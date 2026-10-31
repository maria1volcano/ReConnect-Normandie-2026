import { useEffect, useRef, useState } from 'react'
import type { Map as MapLibreMap, StyleSpecification } from 'maplibre-gl'
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'

const NORMANDY_BOUNDS: [[number, number], [number, number]] = [
  [-1.9550553, 48.1793863],
  [1.8028556, 50.0722125],
]

function getInitialBoundsPadding(containerWidth: number) {
  if (containerWidth < 680) return 18
  if (containerWidth < 1100) return 24
  return 32
}

const REGION_BOUNDARY_URL = new URL(
  `${import.meta.env.BASE_URL}data/normandy-boundary.geojson`,
  window.location.href,
).href
const REGION_BOUNDARY_COLOR = '#127475'

const regionBoundarySources: StyleSpecification['sources'] = {
  'normandy-region': {
    type: 'geojson',
    data: REGION_BOUNDARY_URL,
    attribution: 'Limite régionale : IGN – ADMIN EXPRESS COG CARTO',
  },
}

const regionBoundaryLayers: StyleSpecification['layers'] = [
  {
    id: 'normandy-region-fill',
    type: 'fill',
    source: 'normandy-region',
    paint: {
      'fill-color': REGION_BOUNDARY_COLOR,
      'fill-opacity': 0.05,
    },
  },
  {
    id: 'normandy-region-halo',
    type: 'line',
    source: 'normandy-region',
    layout: { 'line-join': 'round', 'line-cap': 'round' },
    paint: {
      'line-color': '#FFFFFF',
      'line-opacity': 0.7,
      'line-width': ['interpolate', ['linear'], ['zoom'], 5, 3, 9, 4.5, 13, 6],
    },
  },
  {
    id: 'normandy-region-outline',
    type: 'line',
    source: 'normandy-region',
    layout: { 'line-join': 'round', 'line-cap': 'round' },
    paint: {
      'line-color': REGION_BOUNDARY_COLOR,
      'line-width': ['interpolate', ['linear'], ['zoom'], 5, 1.25, 9, 2, 13, 2.75],
    },
  },
]

const basemapStyle: StyleSpecification = {
  version: 8,
  sources: {
    openstreetmap: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
    ...regionBoundarySources,
  },
  layers: [
    {
      id: 'openstreetmap',
      type: 'raster',
      source: 'openstreetmap',
    },
    ...regionBoundaryLayers,
  ],
}

const fallbackStyle: StyleSpecification = {
  version: 8,
  sources: { ...regionBoundarySources },
  layers: [
    {
      id: 'fallback-background',
      type: 'background',
      paint: { 'background-color': '#8B9D83' },
    },
    ...regionBoundaryLayers,
  ],
}

type MapState = 'loading' | 'ready' | 'basemap-error'

export function RegionMap() {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const [mapState, setMapState] = useState<MapState>('loading')

  useEffect(() => {
    const container = mapContainerRef.current
    if (!container) return
    const mapContainer: HTMLDivElement = container

    let map: MapLibreMap | undefined
    let cancelled = false
    let basemapFailed = false
    let basemapTimeout: ReturnType<typeof setTimeout> | undefined
    let resizeObserver: ResizeObserver | undefined
    let userMovedCamera = false

    async function initialiseMap() {
      try {
        const maplibregl = await import('maplibre-gl')
        if (cancelled) return
        maplibregl.setWorkerUrl(maplibreWorkerUrl)

        map = new maplibregl.Map({
          container: mapContainer,
          style: basemapStyle,
          bounds: NORMANDY_BOUNDS,
          fitBoundsOptions: { padding: getInitialBoundsPadding(mapContainer.clientWidth) },
          minZoom: 5,
          attributionControl: false,
        })

        const fitNormandy = () => {
          if (!map || cancelled || userMovedCamera) return
          const { clientWidth, clientHeight } = mapContainer
          const padding = getInitialBoundsPadding(clientWidth)
          if (clientWidth <= padding * 2 || clientHeight <= padding * 2) return
          map.resize()
          map.fitBounds(NORMANDY_BOUNDS, { padding, duration: 0 })
        }

        map.on('movestart', (event) => {
          if (event.originalEvent) userMovedCamera = true
        })

        resizeObserver = new ResizeObserver(fitNormandy)
        resizeObserver.observe(mapContainer)

        map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
        map.addControl(
          new maplibregl.AttributionControl({ compact: true, customAttribution: 'Fond de carte' }),
          'bottom-right',
        )

        map.on('error', (event) => {
          console.error('[RegionMap] Erreur MapLibre', event.error)
        })

        const showBasemapError = () => {
          if (cancelled || basemapFailed) return
          basemapFailed = true
          setMapState('basemap-error')
          map?.setStyle(fallbackStyle)
        }

        map.once('load', () => {
          if (cancelled || basemapFailed) return
          clearTimeout(basemapTimeout)
          fitNormandy()
          setMapState('ready')
        })

        basemapTimeout = setTimeout(showBasemapError, 10_000)
      } catch {
        if (!cancelled) setMapState('basemap-error')
      }
    }

    void initialiseMap()

    return () => {
      cancelled = true
      clearTimeout(basemapTimeout)
      resizeObserver?.disconnect()
      map?.remove()
    }
  }, [])

  const isLoading = mapState === 'loading'
  const hasBasemapError = mapState === 'basemap-error'

  return (
    <div className="region-map" aria-busy={isLoading}>
      <div
        ref={mapContainerRef}
        className="map-canvas"
        role="region"
        aria-label="Carte interactive de la Normandie"
      />

      {isLoading ? (
        <div className="map-status" role="status">
          <span className="status-pulse" aria-hidden="true" />
          Chargement de la carte…
        </div>
      ) : null}

      {hasBasemapError ? (
        <div className="map-status map-status--error" role="alert">
          <strong>Fond de carte indisponible</strong>
          <span>La structure de la carte reste accessible. Vérifiez la connexion puis rechargez.</span>
        </div>
      ) : null}

      <div className="layer-placeholders" aria-label="État des couches territoriales">
        <span>Limite du pilote à charger</span>
        <span>Mailles de diagnostic à charger</span>
      </div>
    </div>
  )
}

