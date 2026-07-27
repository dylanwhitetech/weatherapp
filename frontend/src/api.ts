import type { WeatherPayload } from './types'

export const WEATHER_REQUEST_TIMEOUT_MS = 10_000

export type WeatherRequestErrorCode = 'aborted' | 'http' | 'network' | 'timeout'

export class WeatherRequestError extends Error {
  readonly code: WeatherRequestErrorCode
  readonly status?: number

  constructor(code: WeatherRequestErrorCode, message: string, status?: number) {
    super(message)
    this.name = 'WeatherRequestError'
    this.code = code
    this.status = status
  }
}

export function isWeatherRequestError(error: unknown): error is WeatherRequestError {
  return error instanceof WeatherRequestError
}

export async function fetchWeather(signal?: AbortSignal): Promise<WeatherPayload> {
  const request = createWeatherRequest(signal)

  try {
    const response = await fetch('/api/v1/weather', { signal: request.signal })
    if (!response.ok) {
      throw new WeatherRequestError('http', `Weather request failed (${response.status})`, response.status)
    }
    return (await response.json()) as WeatherPayload
  } catch (error) {
    if (request.didTimeout()) {
      throw new WeatherRequestError('timeout', 'Weather request timed out.')
    }

    if (isAbortError(error) || request.signal.aborted) {
      throw new WeatherRequestError('aborted', 'Weather request was cancelled.')
    }

    if (isWeatherRequestError(error)) {
      throw error
    }

    throw new WeatherRequestError('network', 'Weather request failed.')
  } finally {
    request.cleanup()
  }
}

function createWeatherRequest(externalSignal?: AbortSignal): {
  signal: AbortSignal
  cleanup: () => void
  didTimeout: () => boolean
} {
  const controller = new AbortController()
  const cleanupCallbacks: Array<() => void> = []
  let timedOut = false

  const abort = (reason?: unknown) => {
    if (!controller.signal.aborted) {
      controller.abort(reason)
    }
  }

  if (externalSignal) {
    if (externalSignal.aborted) {
      abort(externalSignal.reason)
    } else {
      const onAbort = () => abort(externalSignal.reason)
      externalSignal.addEventListener('abort', onAbort, { once: true })
      cleanupCallbacks.push(() => externalSignal.removeEventListener('abort', onAbort))
    }
  }

  const timeoutId = globalThis.setTimeout(() => {
    timedOut = true
    abort('weather-request-timeout')
  }, WEATHER_REQUEST_TIMEOUT_MS)

  cleanupCallbacks.push(() => globalThis.clearTimeout(timeoutId))

  return {
    signal: controller.signal,
    cleanup: () => {
      for (const callback of cleanupCallbacks) {
        callback()
      }
    },
    didTimeout: () => timedOut,
  }
}

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === 'AbortError'
}
