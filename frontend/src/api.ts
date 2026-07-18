import type { WeatherPayload } from './types'

export async function fetchWeather(signal?: AbortSignal): Promise<WeatherPayload> {
  const response = await fetch('/api/v1/weather', { signal })
  if (!response.ok) {
    throw new Error(`Weather request failed (${response.status})`)
  }
  return (await response.json()) as WeatherPayload
}
