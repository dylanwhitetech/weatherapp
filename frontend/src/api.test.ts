import {
  fetchWeather,
  isWeatherRequestError,
  WeatherRequestError,
  WEATHER_REQUEST_TIMEOUT_MS,
} from './api'

describe('fetchWeather', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('throws a typed http error for non-success responses', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue({
      ok: false,
      status: 503,
    } as Response)

    await expect(fetchWeather()).rejects.toEqual(
      expect.objectContaining({
        code: 'http',
        message: 'Weather request failed (503)',
        status: 503,
      }),
    )
  })

  it('maps timed out requests to a timeout error', async () => {
    vi.useFakeTimers()
    mockAbortableFetch()

    const request = fetchWeather()
    const requestExpectation = expect(request).rejects.toEqual(
      expect.objectContaining({
        code: 'timeout',
        message: 'Weather request timed out.',
      }),
    )

    await vi.advanceTimersByTimeAsync(WEATHER_REQUEST_TIMEOUT_MS)

    await requestExpectation
  })

  it('maps externally aborted requests to an aborted error', async () => {
    mockAbortableFetch()
    const controller = new AbortController()
    const request = fetchWeather(controller.signal)

    controller.abort()

    await expect(request).rejects.toEqual(
      expect.objectContaining({
        code: 'aborted',
        message: 'Weather request was cancelled.',
      }),
    )
  })

  it('exposes a type guard for typed fetch errors', () => {
    expect(isWeatherRequestError(new WeatherRequestError('network', 'Weather request failed.'))).toBe(true)
    expect(isWeatherRequestError(new Error('Weather request failed.'))).toBe(false)
  })
})

function mockAbortableFetch(): void {
  vi.spyOn(globalThis, 'fetch').mockImplementation(
    (_input: RequestInfo | URL, init?: RequestInit) =>
      new Promise<Response>((_resolve, reject) => {
        const signal = init?.signal

        if (signal?.aborted) {
          reject(new DOMException('The operation was aborted.', 'AbortError'))
          return
        }

        signal?.addEventListener(
          'abort',
          () => reject(new DOMException('The operation was aborted.', 'AbortError')),
          { once: true },
        )
      }),
  )
}
