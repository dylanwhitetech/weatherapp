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
  map_panel: MapPanel
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

export interface MapPanel {
  default_layer_id: string
  cycle_seconds: number
  zoom: number
  overlay_opacity: number
  layers: MapLayer[]
}

export interface MapLayer {
  id: string
  label: string
  kind: 'tile' | 'fires' | 'air-quality' | 'observation-points'
  description: string
  enabled: boolean
  unavailable_reason: string | null
  tile_url: string | null
  data_url: string | null
  source: string
  attribution: string
  updated_at: string | null
  legend: MapLayerLegend
}

export interface MapLayerLegend {
  title: string
  units: string | null
  entries: MapLegendEntry[]
  note: string | null
}

export interface MapLegendEntry {
  label: string
  color: string
}

export interface FiresOverlayPayload {
  source: string
  fetched_at: string
  updated_at: string | null
  points: FirePoint[]
}

export interface FirePoint {
  latitude: number
  longitude: number
  distance_km: number
  confidence: string | null
  brightness: number | null
  acquired_at: string | null
  satellite: string | null
}

export interface AirQualityOverlayPayload {
  source: string
  fetched_at: string
  updated_at: string | null
  observations: AirQualityObservation[]
}

export interface AirQualityObservation {
  latitude: number
  longitude: number
  aqi: number
  category: string
  pollutant: string
  reporting_area: string
  state_code: string | null
  distance_miles: number
  observed_at: string | null
}

export interface ObservationOverlayPayload {
  metric: 'temperature' | 'wind'
  source: string
  fetched_at: string
  updated_at: string | null
  points: ObservationPoint[]
}

export interface ObservationPoint {
  latitude: number
  longitude: number
  value: number
  unit: string
  station_id: string
  station_name: string | null
  wind_direction: string | null
  observed_at: string | null
}
