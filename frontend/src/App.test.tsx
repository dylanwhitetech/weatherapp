import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
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

  it('renders the initial loading state while the first request is pending', () => {
    const pendingResponse = deferred<Response>()
    vi.spyOn(globalThis, 'fetch').mockReturnValue(pendingResponse.promise)

    render(<App />)

    expect(screen.getByText('Loading weather dashboard…')).toBeInTheDocument()
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

  it('retries successfully after an initial load failure', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    fetchSpy.mockRejectedValueOnce(new Error('network down'))
    fetchSpy.mockResolvedValueOnce(successResponse(mockPayload()))
    const user = userEvent.setup()

    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to load weather data right now.')

    await user.click(screen.getByRole('button', { name: 'Retry' }))

    await waitFor(() => {
      expect(screen.getByText('No active alerts')).toBeInTheDocument()
    })
  })

  it('shows a refreshing state during a manual refresh', async () => {
    const refreshResponse = deferred<Response>()
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    fetchSpy.mockResolvedValueOnce(successResponse(mockPayload()))
    fetchSpy.mockReturnValueOnce(refreshResponse.promise)
    const user = userEvent.setup()

    render(<App />)

    await screen.findByText('No active alerts')

    await user.click(screen.getByRole('button', { name: 'Refresh' }))

    expect(screen.getByRole('button', { name: 'Refreshing…' })).toBeDisabled()

    refreshResponse.resolve(successResponse(mockPayload()))

    await waitFor(() => {
      expect(screen.getByRole('button', { name: 'Refresh' })).toBeEnabled()
    })
  })

  it('returns to the blocking error state when a refresh fails', async () => {
    const fetchSpy = vi.spyOn(globalThis, 'fetch')
    fetchSpy.mockResolvedValueOnce(successResponse(mockPayload()))
    fetchSpy.mockRejectedValueOnce(new Error('network down'))
    const user = userEvent.setup()

    render(<App />)

    await screen.findByText('No active alerts')

    await user.click(screen.getByRole('button', { name: 'Refresh' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to load weather data right now.')
    expect(screen.getByRole('heading', { name: 'Weather dashboard' })).toBeInTheDocument()
    expect(screen.queryByText('No active alerts')).not.toBeInTheDocument()
  })
})

function successResponse(payload: WeatherPayload): Response {
  return {
    ok: true,
    json: async () => payload,
  } as Response
}

function deferred<T>(): {
  promise: Promise<T>
  resolve: (value: T) => void
  reject: (reason?: unknown) => void
} {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((nextResolve, nextReject) => {
    resolve = nextResolve
    reject = nextReject
  })

  return { promise, resolve, reject }
}
