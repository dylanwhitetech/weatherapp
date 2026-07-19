export type GolfLabel = 'Excellent' | 'Good' | 'Playable' | 'Poor' | 'Avoid'
export type LawnRecommendationType = 'Water' | 'Skip' | 'Delay' | 'Optional'

export interface WeatherPayload {
  location: {
    name: string
    latitude: number
    longitude: number
    timezone: string
  }
  current: {
    observed_at: string | null
    temperature_f: number | null
    feels_like_f: number | null
    relative_humidity_percent: number | null
    wind_speed_mph: number | null
    wind_gust_mph: number | null
    wind_direction: string | null
    conditions: string | null
    icon_url: string | null
  }
  hourly: ForecastPeriod[]
  daily: ForecastPeriod[]
  alerts: AlertMessage[]
  recommendations: {
    golf: {
      score: number
      label: GolfLabel
      best_window: {
        start: string | null
        end: string | null
      }
      summary: string
      reasons: string[]
      limited_data: boolean
    }
    lawn: {
      recommendation: LawnRecommendationType
      confidence: 'low' | 'medium' | 'high'
      suggested_time: string
      summary: string
      reasons: string[]
      disclaimer: string
    }
  }
  metadata: {
    source: string
    generated_at: string
    last_successful_refresh: string | null
    stale: boolean
    cache_age_seconds: number
    status_message: string | null
  }
}

export interface ForecastPeriod {
  start: string
  end: string
  name: string | null
  is_daytime: boolean
  temperature_f: number | null
  wind_speed_mph: number | null
  wind_gust_mph: number | null
  precip_probability_percent: number | null
  conditions: string | null
  icon_url: string | null
}

export interface AlertMessage {
  id: string
  event: string | null
  severity: string | null
  headline: string | null
  description: string | null
  effective: string | null
  expires: string | null
  status: string | null
}
