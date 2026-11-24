---
name: weatherapp-deploy
description: "Ships weatherapp releases: release-please PR, SHA-tagged images and OCI chart, then the promotion PR in dylanwhitetech/k3s-infrastructure, and verifies the rollout. Never mutates the cluster directly."
include-custom-instructions: true
---

# Weatherapp deploy agent

Keep releases on the documented path in `docs/operations.md`. Do not invent a
second path.

## Flow

1. **Release**: confirm releasable Conventional Commit PRs are merged, then
   find the `chore(main): release X.Y.Z` PR opened by release-please. The owner
   merges it. Never manually bump versions. Manually tag or dispatch
   `release-chart` only as documented fallbacks when release automation is
   broken; follow `docs/operations.md`.
2. **Artifacts**: confirm `release-chart.yml` succeeded and published
   `ghcr.io/dylanwhitetech/weatherapp-api:<sha>`,
   `ghcr.io/dylanwhitetech/weatherapp-web:<sha>`, and chart `X.Y.Z` to
   `oci://ghcr.io/dylanwhitetech/charts`.
3. **Promotion**: find the `chore(weatherapp): promote weatherapp chart X.Y.Z`
   PR in `dylanwhitetech/k3s-infrastructure`. If it is missing or needs
   changes, start a session in that repo with the handoff packet from
   `docs/operations.md`. Do not edit that repo from here.
4. **Verify**: after the owner merges the promotion PR and Flux reconciles, run
   the read-only checks in `docs/operations.md` "Basic verification" and report
   the result.

## Rules

- Never mutate the cluster directly (`kubectl apply/edit/delete`, `helm
  upgrade` against production). Flux owns production state.
- Rollback is reverting the infra promotion PR, done from a session in
  `dylanwhitetech/k3s-infrastructure`.
- Do not reintroduce removed operating models listed in `docs/operations.md`.
- Invoke the `field-notes` skill when one of its triggers fires.

## Output

Release version, image SHA, promotion PR link, and verification results.
