import { render, screen, waitFor } from '@testing-library/react'
import App from './App'
import type { WeatherPayload } from './types'

function mockPayload(overrides?: Partial<WeatherPayload>): WeatherPayload {
  return {
    location: {
      name: 'Walla Walla, WA',
      latitude: 46.0646,
      longitude: -118.343,
      timezone: 'America/Los_Angeles',
    },
    current: {
      observed_at: '2026-07-18T18:00:00Z',
      temperature_f: 82,
      feels_like_f: 82,
      relative_humidity_percent: 25,
      wind_speed_mph: 9,
      wind_gust_mph: 14,
      wind_direction: 'SW',
      conditions: 'Mostly Sunny',
      icon_url: null,
    },
    hourly: [],
    daily: [],
    alerts: [],
    recommendations: {
      golf: {
        score: 85,
        label: 'Excellent',
        best_window: {
          start: '2026-07-18T21:00:00Z',
          end: '2026-07-18T23:00:00Z',
        },
        summary: 'Great weather window for a round of golf.',
        reasons: ['Low rain probability'],
        limited_data: false,
      },
      lawn: {
        recommendation: 'Optional',
        confidence: 'low',
        suggested_time: 'Early morning',
        summary: 'Conditions are moderate.',
        reasons: ['No strong signal'],
        disclaimer: 'Estimate only',
      },
    },
    metadata: {
      source: 'National Weather Service',
      generated_at: '2026-07-18T18:00:00Z',
      last_successful_refresh: '2026-07-18T18:00:00Z',
      stale: false,
      cache_age_seconds: 12,
      status_message: null,
    },
    ...overrides,
  }
}

describe('App', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders no active alerts state', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () => mockPayload(),
    } as Response)

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('No active alerts')).toBeInTheDocument()
    })
  })

  it('shows stale data warning when payload is stale', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: true,
      json: async () =>
        mockPayload({
          metadata: {
            source: 'National Weather Service',
            generated_at: '2026-07-18T18:00:00Z',
            last_successful_refresh: '2026-07-18T17:00:00Z',
            stale: true,
            cache_age_seconds: 1200,
            status_message: 'Serving stale data',
          },
        }),
    } as Response)

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText(/Stale data:/)).toBeInTheDocument()
    })
  })
})
