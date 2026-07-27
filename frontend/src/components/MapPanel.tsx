import { useEffect, useMemo, useState } from 'react'
import './MapPanel.css'
import type {
  AirQualityObservation,
  AirQualityOverlayPayload,
  FirePoint,
  FiresOverlayPayload,
  MapLayer,
  MapPanel as MapPanelConfig,
  ObservationOverlayPayload,
  ObservationPoint,
} from '../types'

const TILE_SIZE = 256
const GRID_SPAN = 3
const GRID_SIZE = TILE_SIZE * GRID_SPAN

interface MapPanelProps {
  location: {
    name: string
    latitude: number
    longitude: number
  }
  timezone: string
  mapPanel: MapPanelConfig
}

interface FireState {
  loading: boolean
  error: string | null
  payload: FiresOverlayPayload | null
}

interface AirQualityState {
  loading: boolean
  error: string | null
  payload: AirQualityOverlayPayload | null
}

interface ObservationState {
  loading: boolean
  error: string | null
  payload: ObservationOverlayPayload | null
}

function pickDefaultLayer(layers: MapLayer[], fallbackId: string): string {
  const configured = layers.find((layer) => layer.id === fallbackId && layer.enabled)
  if (configured) {
    return configured.id
  }

  const firstEnabled = layers.find((layer) => layer.enabled)
  return firstEnabled?.id ?? fallbackId
}

export function MapPanel({ location, timezone, mapPanel }: MapPanelProps) {
  const [activeLayerId, setActiveLayerId] = useState(() =>
    pickDefaultLayer(mapPanel.layers, mapPanel.default_layer_id),
  )
  const [isCycling, setIsCycling] = useState(true)
  const [fires, setFires] = useState<FireState>({
    loading: false,
    error: null,
    payload: null,
  })
  const [airQuality, setAirQuality] = useState<AirQualityState>({
    loading: false,
    error: null,
    payload: null,
  })
  const [observations, setObservations] = useState<ObservationState>({
    loading: false,
    error: null,
    payload: null,
  })

  const enabledLayers = useMemo(
    () => mapPanel.layers.filter((layer) => layer.enabled),
    [mapPanel.layers],
  )

  const activeLayer = useMemo(
    () => mapPanel.layers.find((layer) => layer.id === activeLayerId) ?? mapPanel.layers[0] ?? null,
    [activeLayerId, mapPanel.layers],
  )

  useEffect(() => {
    const nextId = pickDefaultLayer(mapPanel.layers, mapPanel.default_layer_id)
    const activeLayerStillAvailable = mapPanel.layers.some(
      (layer) => layer.id === activeLayerId && layer.enabled,
    )

    if (!activeLayerStillAvailable) {
      setActiveLayerId(nextId)
    }
  }, [activeLayerId, mapPanel.default_layer_id, mapPanel.layers])

  useEffect(() => {
    if (!isCycling || enabledLayers.length <= 1) {
      return
    }

    const intervalMs = Math.max(3, mapPanel.cycle_seconds) * 1000
    const timer = window.setInterval(() => {
      setActiveLayerId((currentId) => {
        const currentIndex = enabledLayers.findIndex((layer) => layer.id === currentId)
        const nextIndex = currentIndex < 0 ? 0 : (currentIndex + 1) % enabledLayers.length
        return enabledLayers[nextIndex].id
      })
    }, intervalMs)

    return () => window.clearInterval(timer)
  }, [enabledLayers, isCycling, mapPanel.cycle_seconds])

  useEffect(() => {
    if (!activeLayer || activeLayer.kind !== 'fires' || !activeLayer.enabled || !activeLayer.data_url) {
      setFires({ loading: false, error: null, payload: null })
      return
    }
    const dataUrl = activeLayer.data_url

    const controller = new AbortController()
    setFires({ loading: true, error: null, payload: null })

    void (async () => {
      try {
        const response = await fetch(dataUrl, { signal: controller.signal })
        if (!response.ok) {
          throw new Error(`Fire layer request failed (${response.status})`)
        }
        const payload = normalizeFiresPayload(await response.json())
        setFires({ loading: false, error: null, payload })
      } catch (error) {
        if (controller.signal.aborted) {
          return
        }
        setFires({
          loading: false,
          error: error instanceof Error ? error.message : 'Failed to load fire detections.',
          payload: null,
        })
      }
    })()

    return () => controller.abort()
  }, [activeLayer])

  useEffect(() => {
    if (!activeLayer || activeLayer.kind !== 'air-quality' || !activeLayer.data_url) {
      setAirQuality({ loading: false, error: null, payload: null })
      return
    }
    const dataUrl = activeLayer.data_url

    const controller = new AbortController()
    setAirQuality({ loading: true, error: null, payload: null })

    void (async () => {
      try {
        const response = await fetch(dataUrl, { signal: controller.signal })
        if (!response.ok) {
          throw new Error(`Air quality request failed (${response.status})`)
        }
        const payload = normalizeAirQualityPayload(await response.json())
        setAirQuality({ loading: false, error: null, payload })
      } catch (error) {
        if (controller.signal.aborted) {
          return
        }
        setAirQuality({
          loading: false,
          error: error instanceof Error ? error.message : 'Failed to load air quality observations.',
          payload: null,
        })
      }
    })()

    return () => controller.abort()
  }, [activeLayer])

  useEffect(() => {
    if (!activeLayer || activeLayer.kind !== 'observation-points' || !activeLayer.data_url) {
      setObservations({ loading: false, error: null, payload: null })
      return
    }
    const dataUrl = activeLayer.data_url

    const controller = new AbortController()
    setObservations({ loading: true, error: null, payload: null })

    void (async () => {
      try {
        const response = await fetch(dataUrl, { signal: controller.signal })
        if (!response.ok) {
          throw new Error(`Observation request failed (${response.status})`)
        }
        const payload = normalizeObservationPayload(await response.json(), activeLayer.id)
        setObservations({ loading: false, error: null, payload })
      } catch (error) {
        if (controller.signal.aborted) {
          return
        }
        setObservations({
          loading: false,
          error: error instanceof Error ? error.message : 'Failed to load weather observations.',
          payload: null,
        })
      }
    })()

    return () => controller.abort()
  }, [activeLayer])

  const tiles = useMemo(() => {
    const zoom = Math.max(0, Math.floor(mapPanel.zoom))
    const tileCount = 2 ** zoom
    const centerTileX = lonToTile(location.longitude, zoom)
    const centerTileY = latToTile(location.latitude, zoom)
    const baseTileX = Math.floor(centerTileX) - 1
    const baseTileY = Math.floor(centerTileY) - 1

    const nextTiles: Array<{ id: string; x: number; y: number; row: number; col: number }> = []
    for (let row = 0; row < GRID_SPAN; row += 1) {
      for (let col = 0; col < GRID_SPAN; col += 1) {
        const rawX = baseTileX + col
        const rawY = baseTileY + row
        const wrappedX = mod(rawX, tileCount)
        const clampedY = Math.max(0, Math.min(tileCount - 1, rawY))
        nextTiles.push({ id: `${wrappedX}-${clampedY}-${row}-${col}`, x: wrappedX, y: clampedY, row, col })
      }
    }

    return { zoom, baseTileX, baseTileY, tileCount, tiles: nextTiles }
  }, [location.latitude, location.longitude, mapPanel.zoom])

  const fireMarkers = useMemo(() => {
    if (activeLayer?.kind !== 'fires' || !fires.payload) {
      return []
    }
    return projectMarkers(
      fires.payload.points,
      tiles.zoom,
      tiles.baseTileX * TILE_SIZE,
      tiles.baseTileY * TILE_SIZE,
      tiles.tileCount * TILE_SIZE,
    )
  }, [activeLayer?.kind, fires.payload, tiles.baseTileX, tiles.baseTileY, tiles.tileCount, tiles.zoom])

  const airQualityMarkers = useMemo(() => {
    if (activeLayer?.kind !== 'air-quality' || !airQuality.payload) {
      return []
    }
    return projectAirQualityMarkers(
      airQuality.payload.observations,
      tiles.zoom,
      tiles.baseTileX * TILE_SIZE,
      tiles.baseTileY * TILE_SIZE,
      tiles.tileCount * TILE_SIZE,
    )
  }, [activeLayer?.kind, airQuality.payload, tiles.baseTileX, tiles.baseTileY, tiles.tileCount, tiles.zoom])

  const observationMarkers = useMemo(() => {
    if (activeLayer?.kind !== 'observation-points' || !observations.payload) {
      return []
    }
    return projectObservationMarkers(
      observations.payload.points,
      observations.payload.metric,
      tiles.zoom,
      tiles.baseTileX * TILE_SIZE,
      tiles.baseTileY * TILE_SIZE,
      tiles.tileCount * TILE_SIZE,
    )
  }, [activeLayer?.kind, observations.payload, tiles.baseTileX, tiles.baseTileY, tiles.tileCount, tiles.zoom])

  if (!activeLayer) {
    return null
  }
  const activeTileUrl = activeLayer.kind === 'tile' ? activeLayer.tile_url : null

  return (
    <section className="map-panel" aria-label="Weather map panel">
      <header className="map-panel-header">
        <div>
          <h2>Weather map</h2>
          <p className="muted">
            {location.name} · {activeLayer.description}
          </p>
        </div>
        <button type="button" className="refresh-button" onClick={() => setIsCycling((value) => !value)}>
          {isCycling ? 'Pause cycle' : 'Resume cycle'}
        </button>
      </header>

      <div className="map-layer-controls" role="tablist" aria-label="Map layers">
        {mapPanel.layers.map((layer) => {
          const selected = layer.id === activeLayer.id
          return (
            <button
              key={layer.id}
              type="button"
              role="tab"
              aria-selected={selected}
              disabled={!layer.enabled}
              className={`map-layer-button${selected ? ' is-active' : ''}`}
              onClick={() => {
                setActiveLayerId(layer.id)
                setIsCycling(false)
              }}
            >
              {layer.label}
            </button>
          )
        })}
      </div>

      <div className="map-stage" role="img" aria-label={`${activeLayer.label} map`}>
        <div className="map-grid">
          {tiles.tiles.map((tile) => (
            <img
              key={`base-${tile.id}`}
              className="map-tile"
              loading="lazy"
              src={`https://tile.openstreetmap.org/${tiles.zoom}/${tile.x}/${tile.y}.png`}
              alt=""
            />
          ))}
        </div>

        {activeLayer.kind === 'tile' && activeTileUrl && (
          <div className="map-grid map-overlay" style={{ opacity: mapPanel.overlay_opacity }}>
            {tiles.tiles.map((tile) => (
              <img
                key={`overlay-${tile.id}`}
                className="map-tile"
                loading="lazy"
                src={buildTileUrl(activeTileUrl, tiles.zoom, tile.x, tile.y)}
                alt=""
              />
            ))}
          </div>
        )}

        {activeLayer.kind === 'fires' && (
          <div className="map-fires-layer">
            {fires.loading && <div className="map-state-chip">Loading fire detections…</div>}
            {fires.error && <div className="map-state-chip map-state-chip-error">{fires.error}</div>}
            {fireMarkers.map((marker) => (
              <div
                key={marker.id}
                className="fire-marker"
                title={marker.title}
                style={{ left: `${marker.xPercent}%`, top: `${marker.yPercent}%` }}
              />
            ))}
          </div>
        )}

        {activeLayer.kind === 'air-quality' && (
          <div className="map-fires-layer">
            {airQuality.loading && <div className="map-state-chip">Loading air quality observations…</div>}
            {airQuality.error && <div className="map-state-chip map-state-chip-error">{airQuality.error}</div>}
            {airQualityMarkers.map((marker) => (
              <div
                key={marker.id}
                className={`aq-marker ${marker.levelClass}`}
                title={marker.title}
                style={{ left: `${marker.xPercent}%`, top: `${marker.yPercent}%` }}
              />
            ))}
          </div>
        )}

        {activeLayer.kind === 'observation-points' && (
          <div className="map-fires-layer">
            {observations.loading && <div className="map-state-chip">Loading weather observations…</div>}
            {observations.error && <div className="map-state-chip map-state-chip-error">{observations.error}</div>}
            {observationMarkers.map((marker) => (
              <div
                key={marker.id}
                className={`obs-marker ${marker.levelClass}`}
                title={marker.title}
                style={{ left: `${marker.xPercent}%`, top: `${marker.yPercent}%` }}
              >
                <span className="obs-marker-label">{marker.valueLabel}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {activeLayer.unavailable_reason && (
        <p className="muted map-unavailable">
          Layer unavailable: {activeLayer.unavailable_reason}
        </p>
      )}

      <section className="map-legend" aria-label="Map legend">
        <h3>Legend</h3>
        <p className="muted">
          {activeLayer.legend.title}
          {activeLayer.legend.units ? ` · ${activeLayer.legend.units}` : ''}
        </p>
        <ul className="map-legend-list">
          {activeLayer.legend.entries.map((entry) => (
            <li key={entry.label} className="map-legend-item">
              <span className="map-legend-swatch" style={{ backgroundColor: entry.color }} aria-hidden="true" />
              <span>{entry.label}</span>
            </li>
          ))}
        </ul>
        {activeLayer.legend.note && <p className="muted">{activeLayer.legend.note}</p>}
        <p className="muted">
          Source: {activeLayer.source} · Updated:{' '}
          {formatTimestamp(
            activeLayer.updated_at ??
              fires.payload?.updated_at ??
              airQuality.payload?.updated_at ??
              observations.payload?.updated_at ??
              null,
            timezone,
          )}
        </p>
        <p className="muted">Attribution: {activeLayer.attribution}; basemap © OpenStreetMap contributors.</p>
      </section>
    </section>
  )
}

function buildTileUrl(template: string, z: number, x: number, y: number): string {
  return template.replace('{z}', String(z)).replace('{x}', String(x)).replace('{y}', String(y))
}

function lonToTile(lon: number, zoom: number): number {
  return ((lon + 180) / 360) * 2 ** zoom
}

function latToTile(lat: number, zoom: number): number {
  const radians = (lat * Math.PI) / 180
  return (((1 - Math.log(Math.tan(radians) + 1 / Math.cos(radians)) / Math.PI) / 2) * 2 ** zoom)
}

function lonToWorldPixel(lon: number, zoom: number): number {
  return ((lon + 180) / 360) * (2 ** zoom) * TILE_SIZE
}

function latToWorldPixel(lat: number, zoom: number): number {
  const radians = (lat * Math.PI) / 180
  return (
    ((1 - Math.log(Math.tan(radians) + 1 / Math.cos(radians)) / Math.PI) / 2) *
    (2 ** zoom) *
    TILE_SIZE
  )
}

function mod(value: number, base: number): number {
  return ((value % base) + base) % base
}

function projectMarkers(
  points: FirePoint[],
  zoom: number,
  topLeftX: number,
  topLeftY: number,
  worldSizePx: number,
): Array<{ id: string; xPercent: number; yPercent: number; title: string }> {
  const projected: Array<{ id: string; xPercent: number; yPercent: number; title: string }> = []
  for (const point of points) {
    const worldX = lonToWorldPixel(point.longitude, zoom)
    const worldY = latToWorldPixel(point.latitude, zoom)

    let deltaX = worldX - topLeftX
    while (deltaX < 0) {
      deltaX += worldSizePx
    }
    while (deltaX > worldSizePx) {
      deltaX -= worldSizePx
    }

    const deltaY = worldY - topLeftY
    if (deltaX < 0 || deltaX > GRID_SIZE || deltaY < 0 || deltaY > GRID_SIZE) {
      continue
    }

    projected.push({
      id: `${point.latitude}-${point.longitude}-${point.acquired_at ?? 'na'}`,
      xPercent: (deltaX / GRID_SIZE) * 100,
      yPercent: (deltaY / GRID_SIZE) * 100,
      title: `${point.satellite ?? 'Satellite'} detection · ${point.distance_km} km`,
    })
  }
  return projected
}

function projectAirQualityMarkers(
  observations: AirQualityObservation[],
  zoom: number,
  topLeftX: number,
  topLeftY: number,
  worldSizePx: number,
): Array<{ id: string; xPercent: number; yPercent: number; title: string; levelClass: string }> {
  const projected: Array<{ id: string; xPercent: number; yPercent: number; title: string; levelClass: string }> = []
  for (const observation of observations) {
    const worldX = lonToWorldPixel(observation.longitude, zoom)
    const worldY = latToWorldPixel(observation.latitude, zoom)

    let deltaX = worldX - topLeftX
    while (deltaX < 0) {
      deltaX += worldSizePx
    }
    while (deltaX > worldSizePx) {
      deltaX -= worldSizePx
    }

    const deltaY = worldY - topLeftY
    if (deltaX < 0 || deltaX > GRID_SIZE || deltaY < 0 || deltaY > GRID_SIZE) {
      continue
    }

    projected.push({
      id: `${observation.latitude}-${observation.longitude}-${observation.pollutant}-${observation.aqi}`,
      xPercent: (deltaX / GRID_SIZE) * 100,
      yPercent: (deltaY / GRID_SIZE) * 100,
      title: `${observation.reporting_area}: AQI ${observation.aqi} (${observation.category})`,
      levelClass: getAqiLevelClass(observation.aqi),
    })
  }
  return projected
}

function projectObservationMarkers(
  points: ObservationPoint[],
  metric: 'temperature' | 'wind',
  zoom: number,
  topLeftX: number,
  topLeftY: number,
  worldSizePx: number,
): Array<{ id: string; xPercent: number; yPercent: number; title: string; levelClass: string; valueLabel: string }> {
  const projected: Array<{
    id: string
    xPercent: number
    yPercent: number
    title: string
    levelClass: string
    valueLabel: string
  }> = []
  for (const point of points) {
    const worldX = lonToWorldPixel(point.longitude, zoom)
    const worldY = latToWorldPixel(point.latitude, zoom)

    let deltaX = worldX - topLeftX
    while (deltaX < 0) {
      deltaX += worldSizePx
    }
    while (deltaX > worldSizePx) {
      deltaX -= worldSizePx
    }

    const deltaY = worldY - topLeftY
    if (deltaX < 0 || deltaX > GRID_SIZE || deltaY < 0 || deltaY > GRID_SIZE) {
      continue
    }

    const roundedValue = Math.round(point.value)
    const valueLabel = `${roundedValue}`
    const directionText = point.wind_direction ? ` ${point.wind_direction}` : ''
    projected.push({
      id: `${point.station_id}-${point.latitude}-${point.longitude}`,
      xPercent: (deltaX / GRID_SIZE) * 100,
      yPercent: (deltaY / GRID_SIZE) * 100,
      title: `${point.station_name ?? point.station_id}: ${roundedValue}${point.unit}${directionText}`,
      levelClass: getObservationLevelClass(metric, point.value),
      valueLabel,
    })
  }
  return projected
}

function getObservationLevelClass(metric: 'temperature' | 'wind', value: number): string {
  if (metric === 'temperature') {
    if (value < 45) {
      return 'obs-cold'
    }
    if (value < 70) {
      return 'obs-mild'
    }
    if (value < 85) {
      return 'obs-warm'
    }
    return 'obs-hot'
  }

  if (value < 10) {
    return 'obs-calm'
  }
  if (value < 20) {
    return 'obs-breezy'
  }
  if (value < 30) {
    return 'obs-windy'
  }
  return 'obs-strong'
}

function getAqiLevelClass(aqi: number): string {
  if (aqi <= 50) {
    return 'aq-good'
  }
  if (aqi <= 100) {
    return 'aq-moderate'
  }
  if (aqi <= 150) {
    return 'aq-usg'
  }
  return 'aq-unhealthy'
}

function formatTimestamp(value: string | null, timezone: string): string {
  if (!value) {
    return 'Unknown'
  }
  return new Intl.DateTimeFormat('en-US', {
    timeZone: timezone,
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function normalizeFiresPayload(raw: unknown): FiresOverlayPayload {
  const payload = typeof raw === 'object' && raw !== null ? (raw as Record<string, unknown>) : {}
  return {
    source: typeof payload.source === 'string' ? payload.source : 'Unknown source',
    fetched_at: typeof payload.fetched_at === 'string' ? payload.fetched_at : new Date().toISOString(),
    updated_at: typeof payload.updated_at === 'string' ? payload.updated_at : null,
    points: Array.isArray(payload.points) ? (payload.points as FirePoint[]) : [],
  }
}

function normalizeAirQualityPayload(raw: unknown): AirQualityOverlayPayload {
  const payload = typeof raw === 'object' && raw !== null ? (raw as Record<string, unknown>) : {}
  return {
    source: typeof payload.source === 'string' ? payload.source : 'Unknown source',
    fetched_at: typeof payload.fetched_at === 'string' ? payload.fetched_at : new Date().toISOString(),
    updated_at: typeof payload.updated_at === 'string' ? payload.updated_at : null,
    observations: Array.isArray(payload.observations) ? (payload.observations as AirQualityObservation[]) : [],
  }
}

function normalizeObservationPayload(raw: unknown, layerId: string): ObservationOverlayPayload {
  const payload = typeof raw === 'object' && raw !== null ? (raw as Record<string, unknown>) : {}
  const metric = layerId === 'wind' ? 'wind' : 'temperature'
  return {
    metric,
    source: typeof payload.source === 'string' ? payload.source : 'National Weather Service Observations',
    fetched_at: typeof payload.fetched_at === 'string' ? payload.fetched_at : new Date().toISOString(),
    updated_at: typeof payload.updated_at === 'string' ? payload.updated_at : null,
    points: Array.isArray(payload.points) ? (payload.points as ObservationPoint[]) : [],
  }
}
