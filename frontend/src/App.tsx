import { useEffect, useMemo, useState } from 'react'
import { fetchWeather } from './api'
import './App.css'
import type { ForecastPeriod, WeatherPayload } from './types'

function App() {
  const [payload, setPayload] = useState<WeatherPayload | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  async function loadWeather(showRefreshing: boolean) {
    if (showRefreshing) {
      setRefreshing(true)
    } else {
      setLoading(true)
    }

    try {
      const nextPayload = await fetchWeather()
      setPayload(nextPayload)
      setError(null)
    } catch {
      setError('Unable to load weather data right now.')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    loadWeather(false)
    const timer = window.setInterval(() => {
      loadWeather(true)
    }, 10 * 60 * 1000)
    return () => window.clearInterval(timer)
  }, [])

  const locationName = payload?.location.name ?? 'Weather'
  const timezone = payload?.location.timezone ?? 'America/Los_Angeles'
  const lastRefresh = useMemo(() => {
    const timestamp = payload?.metadata.last_successful_refresh
    if (!timestamp) {
      return 'No successful refresh yet'
    }
    return formatDateTime(timestamp, timezone)
  }, [payload?.metadata.last_successful_refresh, timezone])

  if (loading) {
    return <main className="app-shell">Loading weather dashboard…</main>
  }

  if (error || payload === null) {
    return (
      <main className="app-shell">
        <h1>Weather dashboard</h1>
        <p role="alert">{error ?? 'No weather data available.'}</p>
        <button type="button" onClick={() => loadWeather(true)}>
          Retry
        </button>
      </main>
    )
  }

  return (
    <main className="app-shell">
      <header className="header">
        <div>
          <h1>{locationName}</h1>
          <p>Last refresh: {lastRefresh}</p>
        </div>
        <button
          type="button"
          className="refresh-button"
          onClick={() => loadWeather(true)}
          disabled={refreshing}
        >
          {refreshing ? 'Refreshing…' : 'Refresh'}
        </button>
      </header>

      {payload.metadata.stale && (
        <section className="warning" role="status">
          <strong>Stale data:</strong> {payload.metadata.status_message ?? 'Showing last known weather data.'}
        </section>
      )}

      <section className="grid">
        <article className="card">
          <h2>Current conditions</h2>
          <p>{payload.current.conditions ?? 'No condition text available'}</p>
          <p>Temp: {formatMaybeNumber(payload.current.temperature_f, '°F')}</p>
          <p>Feels like: {formatMaybeNumber(payload.current.feels_like_f, '°F')}</p>
          <p>Humidity: {formatMaybeNumber(payload.current.relative_humidity_percent, '%')}</p>
          <p>
            Wind: {formatMaybeNumber(payload.current.wind_speed_mph, ' mph')}
            {payload.current.wind_direction ? ` ${payload.current.wind_direction}` : ''}
          </p>
        </article>

        <article className="card">
          <h2>Golf conditions</h2>
          <p>
            Score: {payload.recommendations.golf.score} ({payload.recommendations.golf.label})
          </p>
          <p>{payload.recommendations.golf.summary}</p>
          <ul>
            {payload.recommendations.golf.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </article>

        <article className="card">
          <h2>Lawn recommendation</h2>
          <p>{payload.recommendations.lawn.recommendation}</p>
          <p>{payload.recommendations.lawn.summary}</p>
          <ul>
            {payload.recommendations.lawn.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
          <p className="muted">{payload.recommendations.lawn.disclaimer}</p>
        </article>

        <article className="card">
          <h2>Alerts</h2>
          {payload.alerts.length === 0 ? (
            <p>No active alerts</p>
          ) : (
            <ul>
              {payload.alerts.map((alert) => (
                <li key={alert.id}>
                  <strong>{alert.event ?? 'Alert'}</strong> {alert.headline ?? ''}
                </li>
              ))}
            </ul>
          )}
        </article>
      </section>

      <section className="hourly">
        <h2>Hourly forecast (24h)</h2>
        <div className="hourly-scroll">
          {payload.hourly.slice(0, 24).map((period) => (
            <ForecastCard key={`${period.start}-${period.end}`} period={period} timezone={timezone} />
          ))}
        </div>
      </section>

      <section className="daily">
        <h2>7-day forecast</h2>
        <ul>
          {payload.daily.slice(0, 7).map((period) => (
            <li key={`${period.start}-${period.end}`}>
              <strong>{period.name ?? formatDateTime(period.start, timezone)}</strong> —{' '}
              {period.conditions ?? 'No forecast text'} ({formatMaybeNumber(period.temperature_f, '°F')})
            </li>
          ))}
        </ul>
      </section>

      <footer className="footer">
        <p>Source: {payload.metadata.source}</p>
        <p>Cache age: {payload.metadata.cache_age_seconds}s</p>
      </footer>
    </main>
  )
}

function ForecastCard({ period, timezone }: { period: ForecastPeriod; timezone: string }) {
  return (
    <article className="forecast-card">
      <h3>{formatTime(period.start, timezone)}</h3>
      <p>{period.conditions ?? 'No details'}</p>
      <p>{formatMaybeNumber(period.temperature_f, '°F')}</p>
      <p>Rain: {formatMaybeNumber(period.precip_probability_percent, '%')}</p>
      <p>Wind: {formatMaybeNumber(period.wind_speed_mph, ' mph')}</p>
    </article>
  )
}

function formatMaybeNumber(value: number | null, suffix: string): string {
  if (value === null) {
    return 'N/A'
  }
  return `${Math.round(value)}${suffix}`
}

function formatDateTime(value: string, timezone: string): string {
  return new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function formatTime(value: string, timezone: string): string {
  return new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value))
}

export default App
