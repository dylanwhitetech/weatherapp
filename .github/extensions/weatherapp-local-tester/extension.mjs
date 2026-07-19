import { execFile, spawn } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import {
    existsSync,
    mkdirSync,
    readFileSync,
    writeFileSync,
} from "node:fs";
import { joinSession } from "@github/copilot-sdk/extension";

const execFileAsync = promisify(execFile);
const isWindows = process.platform === "win32";
const npmExecutable = isWindows ? "npm.cmd" : "npm";
const extensionDir = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(extensionDir, "..", "..", "..");
const frontendDir = resolve(repoRoot, "frontend");
const stateDir = resolve(repoRoot, ".copilot-local");
const statePath = resolve(stateDir, "weatherapp-local-test-state.json");
const frontendUrl = "http://localhost:5173";
const backendHealthUrl = "http://localhost:8000/health/live";

/**
 * @typedef {{ frontendPid?: number; frontendUrl?: string; startedAt?: string; }} LocalState
 */

function ensureStateDir() {
    if (!existsSync(stateDir)) {
        mkdirSync(stateDir, { recursive: true });
    }
}

/** @returns {LocalState} */
function readState() {
    if (!existsSync(statePath)) return {};
    try {
        return JSON.parse(readFileSync(statePath, "utf-8"));
    } catch {
        return {};
    }
}

/** @param {LocalState} state */
function writeState(state) {
    ensureStateDir();
    writeFileSync(statePath, JSON.stringify(state, null, 2), "utf-8");
}

function clearState() {
    writeState({});
}

/**
 * @param {string} command
 * @param {string[]} args
 * @param {string} cwd
 * @param {boolean} [allowFailure]
 */
async function runCommand(command, args, cwd, allowFailure = false) {
    try {
        const { stdout = "", stderr = "" } = await execFileAsync(command, args, {
            cwd,
            windowsHide: true,
            maxBuffer: 20 * 1024 * 1024,
        });
        return { code: 0, stdout, stderr };
    } catch (error) {
        const result = {
            code: Number(error?.code ?? 1),
            stdout: String(error?.stdout ?? ""),
            stderr: String(error?.stderr ?? error?.message ?? "Command failed"),
        };
        if (!allowFailure) {
            const details = [result.stderr, result.stdout].filter(Boolean).join("\n");
            throw new Error(
                `Command failed: ${command} ${args.join(" ")}\n` +
                    (details || `exited with code ${result.code}`)
            );
        }
        return result;
    }
}

/** @param {number | undefined} pid */
async function stopFrontendProcess(pid) {
    if (!pid || Number.isNaN(pid)) return;
    if (isWindows) {
        await runCommand("taskkill", ["/PID", String(pid), "/T", "/F"], repoRoot, true);
    } else {
        try { process.kill(-pid, "SIGTERM"); } catch {}
        try { process.kill(pid, "SIGTERM"); } catch {}
    }
}

async function stopBackendServices() {
    await runCommand("docker", ["compose", "down"], repoRoot, true);
}

/**
 * @param {string} url
 * @param {number} timeoutMs
 */
async function waitForUrl(url, timeoutMs) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
        try {
            const res = await fetch(url);
            if (res.ok) return true;
        } catch {}
        await new Promise((r) => setTimeout(r, 1200));
    }
    return false;
}

/** @param {string} url */
async function isHealthy(url) {
    try {
        const res = await fetch(url);
        return res.ok;
    } catch {
        return false;
    }
}

/**
 * @param {{ rebuildBackend?: boolean; installFrontendDeps?: boolean; userAgent?: string; }} args
 * @param {import("@github/copilot-sdk/extension").Session} session
 */
async function startLocalStack(args, session) {
    const rebuildBackend = args.rebuildBackend !== false;
    const installFrontendDeps = args.installFrontendDeps === true;
    const userAgent = args.userAgent || "";

    const priorState = readState();
    await stopFrontendProcess(priorState.frontendPid);
    await stopBackendServices();

    // Backend via docker compose (inherits .env for NWS_USER_AGENT)
    const composeArgs = rebuildBackend
        ? ["compose", "up", "-d", "--build"]
        : ["compose", "up", "-d"];
    if (userAgent) {
        // Override via inline env — prepend env var for the compose call
        // docker compose doesn't accept inline env; pass via process.env injection instead
        process.env.NWS_USER_AGENT = userAgent;
    }
    await session.log(`Starting backend (docker compose up${rebuildBackend ? " --build" : ""}) ...`, { ephemeral: true });
    await runCommand("docker", composeArgs, repoRoot);

    // Frontend deps
    const nodeModulesDir = resolve(frontendDir, "node_modules");
    if (installFrontendDeps || !existsSync(nodeModulesDir)) {
        await session.log("Installing frontend dependencies (npm ci) ...", { ephemeral: true });
        await runCommand(npmExecutable, ["ci"], frontendDir);
    }

    // Start frontend dev server (host-side, proxies /api → localhost:8000)
    await session.log("Starting frontend dev server ...", { ephemeral: true });
    let frontendPid;
    if (isWindows) {
        const frontendDirPs = frontendDir.replace(/'/g, "''");
        const npmExePs = npmExecutable.replace(/'/g, "''");
        const psCmd =
            `$p = Start-Process -FilePath '${npmExePs}' ` +
            `-ArgumentList 'run dev -- --host 0.0.0.0 --port 5173' ` +
            `-WorkingDirectory '${frontendDirPs}' -PassThru; ` +
            "$p.Id";
        const result = await runCommand(
            "powershell",
            ["-NoProfile", "-Command", psCmd],
            repoRoot
        );
        const parsed = Number(result.stdout.trim().split(/\s+/).pop());
        if (Number.isNaN(parsed) || parsed <= 0) {
            throw new Error(`Could not get frontend process ID. Output: ${result.stdout}`);
        }
        frontendPid = parsed;
    } else {
        const proc = spawn(
            npmExecutable,
            ["run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
            { cwd: frontendDir, detached: true, stdio: "ignore" }
        );
        proc.unref();
        frontendPid = proc.pid;
    }

    const backendUp = await waitForUrl(backendHealthUrl, 90000);
    const frontendUp = await waitForUrl(frontendUrl, 90000);

    writeState({ frontendPid, frontendUrl, startedAt: new Date().toISOString() });
    return { backendUp, frontendUp, frontendPid };
}

/** @param {import("@github/copilot-sdk/extension").Session} session */
async function stopLocalStack(session) {
    const state = readState();
    await stopFrontendProcess(state.frontendPid);
    await stopBackendServices();
    clearState();
    await session.log("Stopped local weatherapp services.", { ephemeral: true });
}

let session;
session = await joinSession({
    customAgents: [
        {
            name: "weatherapp-local-preflight",
            displayName: "Weatherapp Local Preflight",
            description:
                "Runs local smoke tests for the current worktree and opens the embedded browser preview.",
            tools: [
                "weatherapp_local_test",
                "weatherapp_local_status",
                "weatherapp_local_stop",
                "open_canvas",
            ],
            prompt:
                "You are the Weatherapp Local Preflight agent. Call weatherapp_local_test first. " +
                "When it succeeds, open the browser canvas to http://localhost:5173 so the user can test visually. " +
                "Report backend/frontend health and any actionable failures.",
        },
    ],
    commands: [
        {
            name: "weather-local-test",
            description: "Start local weatherapp stack and open browser preview.",
            handler: async () => {
                await session.send({
                    prompt:
                        "Use the weatherapp-local-preflight agent to run local smoke testing now. " +
                        "Call weatherapp_local_test with openBrowser true and summarize status.",
                });
            },
        },
        {
            name: "weather-local-stop",
            description: "Stop local weatherapp backend/frontend services.",
            handler: async () => {
                await session.send({
                    prompt: "Use weatherapp_local_stop to stop local weatherapp services and report completion.",
                });
            },
        },
    ],
    hooks: {
        onPostToolUse: async (input) => {
            if (input.toolName !== "weatherapp_local_test") return;
            const v = input.toolArgs?.openBrowser;
            const open = v !== false && v !== "false" && v !== 0 && v !== "0";
            if (!open) return;
            return {
                additionalContext:
                    "The local UI is running at http://localhost:5173. " +
                    'Now call open_canvas with canvasId "browser", instanceId "weatherapp-local-preview", ' +
                    'and input {"url":"http://localhost:5173"} so the user can test in the embedded browser tab.',
            };
        },
    },
    tools: [
        {
            name: "weatherapp_local_test",
            description:
                "Builds/starts the local weatherapp backend and frontend dev server, validates health endpoints, and prepares browser preview.",
            parameters: {
                type: "object",
                properties: {
                    rebuildBackend: {
                        type: "boolean",
                        description: "Rebuild backend Docker image before running (default: true).",
                    },
                    installFrontendDeps: {
                        type: "boolean",
                        description: "Force npm ci before starting frontend dev server (default: false; auto-runs if node_modules is missing).",
                    },
                    userAgent: {
                        type: "string",
                        description: "NWS_USER_AGENT override. Falls back to .env then compose default.",
                    },
                    openBrowser: {
                        type: "boolean",
                        description: "Whether the agent should open browser canvas after startup (default: true).",
                    },
                },
            },
            handler: async (args) => {
                try {
                    const result = await startLocalStack(args || {}, session);
                    if (!result.backendUp || !result.frontendUp) {
                        return {
                            resultType: "failure",
                            textResultForLlm:
                                `Local stack started with issues.\n` +
                                `Backend healthy: ${result.backendUp} — run: docker compose logs api\n` +
                                `Frontend healthy: ${result.frontendUp} — check npm dev server\n` +
                                "Retry with rebuildBackend=true or check docker/npm availability.",
                        };
                    }
                    return (
                        "Local weatherapp stack is ready.\n" +
                        `Backend:  ${backendHealthUrl}\n` +
                        `Frontend: ${frontendUrl}  (PID ${result.frontendPid})\n` +
                        "Use weatherapp_local_stop when finished."
                    );
                } catch (error) {
                    return {
                        resultType: "failure",
                        textResultForLlm:
                            "Unable to start local weatherapp stack.\n" +
                            `Error: ${String(error?.message || error)}\n` +
                            "Check docker compose and npm availability.",
                    };
                }
            },
        },
        {
            name: "weatherapp_local_status",
            description: "Reports whether local backend/frontend services are healthy.",
            parameters: { type: "object", properties: {} },
            handler: async () => {
                const state = readState();
                const backendUp = await isHealthy(backendHealthUrl);
                const frontendUp = await isHealthy(frontendUrl);
                return (
                    "Local weatherapp status:\n" +
                    `Backend healthy:  ${backendUp}\n` +
                    `Frontend healthy: ${frontendUp}\n` +
                    `Frontend PID:     ${state.frontendPid ?? "unknown"}\n` +
                    `Started at:       ${state.startedAt ?? "unknown"}`
                );
            },
        },
        {
            name: "weatherapp_local_stop",
            description: "Stops local weatherapp services (docker compose down + frontend dev server).",
            parameters: { type: "object", properties: {} },
            handler: async () => {
                await stopLocalStack(session);
                return "Stopped local weatherapp services.";
            },
        },
    ],
});

