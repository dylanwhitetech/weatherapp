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
    map_panel: {
      default_layer_id: 'temperature',
      cycle_seconds: 8,
      zoom: 6,
      overlay_opacity: 0.65,
      layers: [
        {
          id: 'temperature',
          label: 'Temp',
          kind: 'observation-points',
          description: 'Observed station temperatures near the configured location',
          enabled: true,
          unavailable_reason: null,
          tile_url: null,
          data_url: '/api/v1/maps/observations/temperature',
          source: 'National Weather Service Observations',
          attribution: 'Observation data © NOAA/NWS',
          updated_at: '2026-07-18T18:00:00Z',
          legend: {
            title: 'Temperature',
            units: '°F',
            entries: [
              { label: 'Cool', color: '#3b82f6' },
              { label: 'Warm', color: '#f59e0b' },
            ],
            note: 'Point markers are station observations, not a continuous heatmap.',
          },
        },
        {
          id: 'wind',
          label: 'Wind',
          kind: 'observation-points',
          description: 'Observed station wind speed near the configured location',
          enabled: true,
          unavailable_reason: null,
          tile_url: null,
          data_url: '/api/v1/maps/observations/wind',
          source: 'National Weather Service Observations',
          attribution: 'Observation data © NOAA/NWS',
          updated_at: '2026-07-18T18:00:00Z',
          legend: {
            title: 'Wind',
            units: 'mph',
            entries: [
              { label: 'Light', color: '#60a5fa' },
              { label: 'Strong', color: '#dc2626' },
            ],
            note: 'Point markers are station observations, not a continuous wind field.',
          },
        },
        {
          id: 'precipitation',
          label: 'Precip',
          kind: 'tile',
          description: 'Observed radar precipitation',
          enabled: true,
          unavailable_reason: null,
          tile_url: '/api/v1/maps/tiles/precipitation/{z}/{x}/{y}.png',
          data_url: null,
          source: 'RainViewer Radar',
          attribution: 'Radar tiles © RainViewer',
          updated_at: '2026-07-18T18:00:00Z',
          legend: {
            title: 'Precipitation',
            units: 'Reflectivity intensity',
            entries: [
              { label: 'Light rain/snow', color: '#60a5fa' },
              { label: 'Heavy precipitation', color: '#ef4444' },
            ],
            note: 'Observed radar, not forecast model precipitation.',
          },
        },
        {
          id: 'fires',
          label: 'Fires',
          kind: 'fires',
          description: 'Recent active-fire detections',
          enabled: true,
          unavailable_reason: null,
          tile_url: null,
          data_url: '/api/v1/maps/fires',
          source: 'NASA FIRMS',
          attribution: 'Fire detections © NASA FIRMS',
          updated_at: '2026-07-18T18:00:00Z',
          legend: {
            title: 'Active fires',
            units: 'km',
            entries: [{ label: 'Recent detection', color: '#f97316' }],
            note: 'Points represent detections, not perimeters.',
          },
        },
        {
          id: 'air-quality',
          label: 'Air Quality',
          kind: 'air-quality',
          description: 'Observed AQI stations near the configured location',
          enabled: true,
          unavailable_reason: null,
          tile_url: null,
          data_url: '/api/v1/maps/air-quality',
          source: 'US EPA AirNow API',
          attribution: 'Air quality data © US EPA AirNow',
          updated_at: '2026-07-18T18:00:00Z',
          legend: {
            title: 'US AQI',
            units: 'AQI',
            entries: [{ label: 'Good (0-50)', color: '#22c55e' }],
            note: 'Station observations, not a continuous heatmap.',
          },
        },
      ],
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

  it('renders the map panel before other dashboard cards', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(successResponse(mockPayload()))

    render(<App />)

    const headings = await screen.findAllByRole('heading', { level: 2 })
    expect(headings[0]).toHaveTextContent('Weather map')
    expect(screen.getByRole('tab', { name: 'Temp' })).toBeInTheDocument()
  })

  it('pauses cycling when a layer is manually selected', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(successResponse(mockPayload()))
    const user = userEvent.setup()

    render(<App />)

    await screen.findByText('No active alerts')
    await user.click(screen.getByRole('tab', { name: 'Wind' }))

    expect(screen.getByRole('button', { name: 'Resume cycle' })).toBeInTheDocument()
  })

  it('updates legend notes when switching layers', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(successResponse(mockPayload()))
    const user = userEvent.setup()

    render(<App />)

    await screen.findByText('No active alerts')
    await user.click(screen.getByRole('tab', { name: 'Precip' }))

    expect(screen.getByText('Observed radar, not forecast model precipitation.')).toBeInTheDocument()
  })

  it('keeps unavailable layers selectable and shows configuration guidance', async () => {
    const payload = mockPayload({
      map_panel: {
        ...mockPayload().map_panel,
        layers: mockPayload().map_panel.layers.map((layer) =>
          layer.id === 'air-quality'
            ? {
                ...layer,
                unavailable_reason: 'AIRNOW_API_KEY is not configured',
              }
            : layer,
        ),
      },
    })
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(successResponse(payload))
    const user = userEvent.setup()

    render(<App />)

    await screen.findByText('No active alerts')
    const aqTab = screen.getByRole('tab', { name: 'Air Quality' })
    expect(aqTab).toBeEnabled()
    await user.click(aqTab)

    expect(screen.getByText('Layer unavailable: AIRNOW_API_KEY is not configured')).toBeInTheDocument()
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
    const weatherResponses: Array<Promise<Response> | Response> = [
      successResponse(mockPayload()),
      refreshResponse.promise,
    ]
    fetchSpy.mockImplementation((input) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/api/v1/weather')) {
        const next = weatherResponses.shift()
        return Promise.resolve(next ?? successResponse(mockPayload()))
      }
      return Promise.resolve(successJsonResponse({ points: [], observations: [] }))
    })
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
    let weatherRequests = 0
    fetchSpy.mockImplementation((input) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/api/v1/weather')) {
        weatherRequests += 1
        if (weatherRequests === 1) {
          return Promise.resolve(successResponse(mockPayload()))
        }
        return Promise.reject(new Error('network down'))
      }
      return Promise.resolve(successJsonResponse({ points: [], observations: [] }))
    })
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
  return successJsonResponse(payload)
}

function successJsonResponse(payload: unknown): Response {
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
