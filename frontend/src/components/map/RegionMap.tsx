import { useCallback, useEffect, useRef, useState } from 'react'
import type { MutableRefObject } from 'react'
import type {
  ExpressionSpecification,
  LngLatBoundsLike,
  Map as MapLibreMap,
  StyleSpecification,
} from 'maplibre-gl'
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'
import {
  DEPARTMENTS_BY_CODE,
  NORMANDY_DEPARTMENTS,
  isDepartmentCode,
  type DepartmentCode,
} from './normandyDepartments'
import type { FeatureCollection } from 'geojson'
import { loadPilotBoundary } from '../../integrations/geojsonAdapter'

const NORMANDY_BOUNDS: [[number, number], [number, number]] = [
  [-1.9550553, 48.1793863],
  [1.8028556, 50.0722125],
]

function getInitialBoundsPadding(containerWidth: number) {
  if (containerWidth < 680) return 18
  if (containerWidth < 1100) return 24
  return 32
}

function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function dataUrl(fileName: string) {
  return new URL(`${import.meta.env.BASE_URL}data/${fileName}`, window.location.href).href
}

const REGION_BOUNDARY_COLOR = '#127475'
const DEPARTMENTS_SOURCE = 'normandy-departments'
const DEPARTMENTS_FILL_LAYER = 'normandy-departments-fill'
const PILOT_SOURCE = 'pilot-boundary'
const PILOT_FILL_LAYER = 'pilot-boundary-fill'
const PILOT_LINE_LAYER = 'pilot-boundary-line'
const PILOT_LABEL_LAYER = 'pilot-boundary-label'
const IGN_ATTRIBUTION = 'Limites administratives : IGN – ADMIN EXPRESS COG CARTO'
const OSM_TILES = ['https://tile.openstreetmap.org/{z}/{x}/{y}.png']

const departmentColor = [
  'match',
  ['get', 'code_insee'],
  ...NORMANDY_DEPARTMENTS.flatMap((department) => [department.code, department.color]),
  '#8B9D83',
] as unknown as ExpressionSpecification

const administrativeSources: StyleSpecification['sources'] = {
  [DEPARTMENTS_SOURCE]: {
    type: 'geojson',
    data: dataUrl('normandy-departments.geojson'),
    attribution: IGN_ATTRIBUTION,
  },
  'normandy-region': {
    type: 'geojson',
    data: dataUrl('normandy-boundary.geojson'),
    attribution: IGN_ATTRIBUTION,
  },
  [PILOT_SOURCE]: {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  },
}

const administrativeLayers: StyleSpecification['layers'] = [
  {
    id: DEPARTMENTS_FILL_LAYER,
    type: 'fill',
    source: DEPARTMENTS_SOURCE,
    paint: {
      'fill-color': departmentColor,
      'fill-opacity': [
        'case',
        ['boolean', ['feature-state', 'selected'], false],
        0.5,
        ['boolean', ['feature-state', 'hover'], false],
        0.52,
        ['boolean', ['feature-state', 'muted'], false],
        0.06,
        0.32,
      ],
      'fill-opacity-transition': { duration: 300 },
    },
  },
  {
    id: 'normandy-departments-line',
    type: 'line',
    source: DEPARTMENTS_SOURCE,
    layout: { 'line-join': 'round' },
    paint: {
      'line-color': '#FFFFFF',
      'line-opacity': 0.85,
      'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.8, 9, 1.4, 13, 2],
    },
  },
  {
    id: 'normandy-departments-selected-line',
    type: 'line',
    source: DEPARTMENTS_SOURCE,
    layout: { 'line-join': 'round' },
    paint: {
      'line-color': '#303726',
      'line-opacity': ['case', ['boolean', ['feature-state', 'selected'], false], 0.9, 0],
      'line-width': ['interpolate', ['linear'], ['zoom'], 5, 1.5, 9, 2.25, 13, 3],
      'line-opacity-transition': { duration: 300 },
    },
  },
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
  {
    id: PILOT_FILL_LAYER,
    type: 'fill',
    source: PILOT_SOURCE,
    paint: {
      'fill-color': '#8B7355',
      'fill-opacity': 0.12,
    },
  },
  {
    id: PILOT_LINE_LAYER,
    type: 'line',
    source: PILOT_SOURCE,
    layout: { 'line-join': 'round', 'line-cap': 'round' },
    paint: {
      'line-color': '#8B7355',
      'line-opacity': 0.8,
      'line-width': ['interpolate', ['linear'], ['zoom'], 5, 2, 9, 3, 13, 4],
      'line-dasharray': [4, 2],
    },
  },
  {
    id: PILOT_LABEL_LAYER,
    type: 'symbol',
    source: PILOT_SOURCE,
    layout: {
      'text-field': 'Zone TEST (démonstration)',
      'text-size': 11,
      'text-anchor': 'center',
      'text-justify': 'center',
      'text-offset': [0, 0],
    },
    paint: {
      'text-color': '#8B7355',
      'text-halo-color': '#E8DCC7',
      'text-halo-width': 2,
      'text-opacity': 0.9,
    },
  },
]

const basemapStyle: StyleSpecification = {
  version: 8,
  sources: {
    openstreetmap: {
      type: 'raster',
      tiles: OSM_TILES,
      tileSize: 256,
      attribution: '© OpenStreetMap contributors',
    },
    ...administrativeSources,
  },
  layers: [
    { id: 'base-background', type: 'background', paint: { 'background-color': '#b9c8bc' } },
    {
      id: 'openstreetmap',
      type: 'raster',
      source: 'openstreetmap',
    },
    ...administrativeLayers,
  ],
}

const fallbackStyle: StyleSpecification = {
  version: 8,
  sources: { ...administrativeSources },
  layers: [
    {
      id: 'fallback-background',
      type: 'background',
      paint: { 'background-color': '#8B9D83' },
    },
    ...administrativeLayers,
  ],
}

type MapState = 'loading' | 'ready' | 'basemap-error' | 'map-error'

export interface RegionMapProps {
  localOnly?: boolean
  compactControls?: boolean
  selectedDepartment?: DepartmentCode | null
  hoveredDepartment?: DepartmentCode | null
  onSelectDepartment?: (code: DepartmentCode | null) => void
  onHoverDepartment?: (code: DepartmentCode | null) => void
  mapRef?: MutableRefObject<MapLibreMap | undefined>
  hexagonCount?: number
  realGridCount?: number
  isTestData?: boolean
  testModeEnabled?: boolean
  showRealGrid?: boolean
  onZoomToTestZone?: () => void
  onZoomToPilot?: () => void
  onToggleRealGrid?: () => void
  studyAreaBounds?: LngLatBoundsLike | null
  onMapReady?: () => void
}

export function RegionMap({
  localOnly = false,
  compactControls = false,
  selectedDepartment: selectedProp,
  hoveredDepartment: hoveredProp,
  onSelectDepartment,
  onHoverDepartment,
  mapRef: externalMapRef,
  hexagonCount = 0,
  realGridCount = 0,
  isTestData = false,
  testModeEnabled = false,
  showRealGrid = true,
  onZoomToTestZone,
  onZoomToPilot,
  onToggleRealGrid,
  studyAreaBounds = null,
  onMapReady,
}: RegionMapProps = {}) {
  const mapContainerRef = useRef<HTMLDivElement>(null)
  const internalMapRef = useRef<MapLibreMap | undefined>(undefined)
  const activeMapRef = externalMapRef || internalMapRef
  const cameraTargetRef = useRef<LngLatBoundsLike>(studyAreaBounds ?? NORMANDY_BOUNDS)
  const userMovedCameraRef = useRef(false)
  const [mapState, setMapState] = useState<MapState>('loading')
  const [mapAttempt,setMapAttempt] = useState(0)
  const basemapRetryRef = useRef<(() => void) | null>(null)
  const [innerSelected, setInnerSelected] = useState<DepartmentCode | null>(null)
  const [innerHovered, setInnerHovered] = useState<DepartmentCode | null>(null)
  const [pilotData, setPilotData] = useState<FeatureCollection | null>(null)

  const selectedDepartment = selectedProp !== undefined ? selectedProp : innerSelected
  const hoveredDepartment = hoveredProp !== undefined ? hoveredProp : innerHovered

  const selectDepartment = useCallback(
    (code: DepartmentCode | null) => {
      setInnerSelected(code)
      onSelectDepartment?.(code)
    },
    [onSelectDepartment],
  )
  const hoverDepartment = useCallback(
    (code: DepartmentCode | null) => {
      setInnerHovered(code)
      onHoverDepartment?.(code)
    },
    [onHoverDepartment],
  )

  const selectRef = useRef(selectDepartment)
  const hoverRef = useRef(hoverDepartment)
  useEffect(() => {
    selectRef.current = selectDepartment
    hoverRef.current = hoverDepartment
  }, [selectDepartment, hoverDepartment])

  useEffect(() => {
    const container = mapContainerRef.current
    if (!container) return
    const mapContainer: HTMLDivElement = container

    let map: MapLibreMap | undefined
    let cancelled = false
    let basemapFailed = false
    let basemapTimeout: ReturnType<typeof setTimeout> | undefined
    let resizeObserver: ResizeObserver | undefined
    setMapState('loading')
    userMovedCameraRef.current = false

    async function initialiseMap() {
      try {
        const maplibregl = await import('maplibre-gl')
        if (cancelled) return
        maplibregl.setWorkerUrl(maplibreWorkerUrl)

        map = new maplibregl.Map({
          container: mapContainer,
          style: localOnly ? fallbackStyle : basemapStyle,
          bounds: studyAreaBounds ?? NORMANDY_BOUNDS,
          fitBoundsOptions: { padding: getInitialBoundsPadding(mapContainer.clientWidth) },
          minZoom: 5,
          attributionControl: false,
        })
        internalMapRef.current = map
        if (externalMapRef) {
          externalMapRef.current = map
        }

        const fitCameraTarget = () => {
          if (!map || cancelled) return
          const { clientWidth, clientHeight } = mapContainer
          const padding = getInitialBoundsPadding(clientWidth)
          if (clientWidth <= padding * 2 || clientHeight <= padding * 2) return
          map.resize()
          if (userMovedCameraRef.current) return
          map.fitBounds(cameraTargetRef.current, { padding: localOnly ? { top: padding, right: padding, bottom: 100, left: padding } : padding, duration: 0 })
        }

        map.on('movestart', (event) => {
          if (event.originalEvent) userMovedCameraRef.current = true
        })

        resizeObserver = new ResizeObserver(fitCameraTarget)
        resizeObserver.observe(mapContainer)

        map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')
        map.addControl(
          new maplibregl.AttributionControl({ compact: !compactControls, customAttribution: 'Limites : IGN' }),
          'bottom-right',
        )

        map.on('mousemove', DEPARTMENTS_FILL_LAYER, (event) => {
          const code = event.features?.[0]?.properties?.code_insee
          if (!isDepartmentCode(code)) return
          map!.getCanvas().style.cursor = 'pointer'
          hoverRef.current(code)
        })
        map.on('mouseleave', DEPARTMENTS_FILL_LAYER, () => {
          map!.getCanvas().style.cursor = ''
          hoverRef.current(null)
        })
        map.on('click', DEPARTMENTS_FILL_LAYER, (event) => {
          const code = event.features?.[0]?.properties?.code_insee
          if (isDepartmentCode(code)) selectRef.current(code)
        })

        map.on('error', (event) => {
          if (!localOnly && (('sourceId' in event && event.sourceId === 'openstreetmap') || /tile\.openstreetmap\.org/.test(String(event.error)))) {
            showBasemapError()
          } else {
            console.error('[RegionMap] Erreur MapLibre', event.error)
            setMapState('map-error')
          }
        })

        const showBasemapError = () => {
          if (cancelled || basemapFailed) return
          basemapFailed = true
          clearTimeout(basemapTimeout)
          setMapState('basemap-error')
          // A failed raster request must not remove loaded tiles or vector layers.
          fitCameraTarget()
        }

        // style.load is independent of raster tile completion. Mount the local
        // territorial layers now, including when the network is slow or offline.
        const styleReady = () => {
          if (cancelled) return
          fitCameraTarget()
          if (!basemapFailed) setMapState('ready')
          onMapReady?.()
        }
        map.on('style.load', styleReady)
        map.on('sourcedata', event => {
          if (event.sourceId === 'openstreetmap' && event.tile?.state === 'loaded') {
            clearTimeout(basemapTimeout)
          }
        })
        map.on('webglcontextlost', () => { if (!cancelled) setMapState('map-error') })

        basemapRetryRef.current = () => {
          if (!map || cancelled) return
          const raster = map.getSource('openstreetmap') as {setTiles: (tiles:string[])=>void} | undefined
          if (!raster) return
          basemapFailed = false
          setMapState('ready')
          clearTimeout(basemapTimeout)
          // Reload this source alone: preserve the grid, selection and camera.
          raster.setTiles([...OSM_TILES])
          basemapTimeout = setTimeout(showBasemapError,10_000)
        }

        if (!localOnly) basemapTimeout = setTimeout(showBasemapError, 10_000)
      } catch (error) {
        if (!cancelled) {
          if (!map) mapContainer.replaceChildren()
          console.error('[RegionMap] Initialisation impossible',error)
          setMapState('map-error')
        }
      }
    }

    void initialiseMap()

    return () => {
      cancelled = true
      clearTimeout(basemapTimeout)
      resizeObserver?.disconnect()
      basemapRetryRef.current = null
      internalMapRef.current = undefined
      if (externalMapRef) {
        externalMapRef.current = undefined
      }
      map?.remove()
    }
  }, [mapAttempt])

  useEffect(() => {
    const map = activeMapRef.current
    if (!map || mapState === 'loading') return

    const applyStates = () => {
      if (!map.getSource(DEPARTMENTS_SOURCE)) return
      for (const department of NORMANDY_DEPARTMENTS) {
        map.setFeatureState(
          { source: DEPARTMENTS_SOURCE, id: Number(department.code) },
          {
            hover: department.code === hoveredDepartment,
            selected: department.code === selectedDepartment,
            muted: selectedDepartment !== null && department.code !== selectedDepartment,
          },
        )
      }
    }

    if (map.isStyleLoaded()) applyStates()
    map.on('styledata', applyStates)
    return () => {
      map.off('styledata', applyStates)
    }
  }, [mapState, hoveredDepartment, selectedDepartment])

  useEffect(() => {
    const map = activeMapRef.current
    if (!map || mapState === 'loading' || !map.getLayer(DEPARTMENTS_FILL_LAYER)) return
    map.setPaintProperty(
      DEPARTMENTS_FILL_LAYER,
      'fill-opacity',
      compactControls && showRealGrid
        ? 0.045
        : [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.5,
            ['boolean', ['feature-state', 'hover'], false],
            0.52,
            ['boolean', ['feature-state', 'muted'], false],
            0.06,
            0.3,
          ],
    )
    if (map.getLayer('normandy-departments-line')) {
      map.setPaintProperty('normandy-departments-line', 'line-opacity', compactControls && showRealGrid ? 0.32 : 0.82)
    }
  }, [mapState, compactControls, showRealGrid])

  useEffect(() => {
    const map = activeMapRef.current
    if (!map || mapState === 'loading') return

    const target = selectedDepartment
      ? DEPARTMENTS_BY_CODE.get(selectedDepartment)?.bounds ?? NORMANDY_BOUNDS
      : studyAreaBounds ?? NORMANDY_BOUNDS
    if (target === cameraTargetRef.current && !userMovedCameraRef.current) return

    cameraTargetRef.current = target
    userMovedCameraRef.current = false
    const container = map.getContainer()
    map.fitBounds(target, {
      padding: localOnly ? { top: 24, right: 24, bottom: 100, left: 24 } : getInitialBoundsPadding(container.clientWidth) * 2,
      duration: prefersReducedMotion() ? 0 : 900,
    })
  }, [mapState, selectedDepartment, studyAreaBounds])

  useEffect(() => {
    void (async () => {
      const pilotResult = await loadPilotBoundary()
      setPilotData(pilotResult.featureCollection)
    })()
  }, [])

  useEffect(() => {
    const map = activeMapRef.current
    if (!map) return

    if (testModeEnabled && pilotData) {
      const source = map.getSource(PILOT_SOURCE)
      if (source) {
        ;(source as any).setData(pilotData)
      }
      if (map.getLayer(PILOT_LABEL_LAYER)) {
        map.setLayoutProperty(PILOT_LABEL_LAYER, 'visibility', 'visible')
      }
    } else if (!testModeEnabled) {
      const source = map.getSource(PILOT_SOURCE)
      if (source) {
        ;(source as any).setData({ type: 'FeatureCollection', features: [] })
      }
      if (map.getLayer(PILOT_LABEL_LAYER)) {
        map.setLayoutProperty(PILOT_LABEL_LAYER, 'visibility', 'none')
      }
    }
  }, [mapState, pilotData, testModeEnabled])

  const isLoading = mapState === 'loading'
  const hasBasemapError = mapState === 'basemap-error'
  const hasMapError = mapState === 'map-error'
  const hoveredName = hoveredDepartment ? DEPARTMENTS_BY_CODE.get(hoveredDepartment)?.name : null

  return (
    <div
      className={`region-map${compactControls ? ' region-map--compact' : ''}`}
      aria-busy={isLoading}
      onKeyDown={(event) => {
        if (event.key === 'Escape' && selectedDepartment) selectDepartment(null)
      }}
    >
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

      {hasBasemapError || hasMapError ? (
        <div className={compactControls ? 'v2-basemap-status' : 'map-status map-status--error'} role="alert">
          <strong>{hasMapError ? 'La carte ne peut pas être affichée.' : 'Fond routier incomplet ou indisponible.'}</strong>
          <span>{hasMapError ? 'Utilisez la liste des secteurs ou réessayez.' : 'Les secteurs restent sélectionnables.'}</span>
          <button type="button" onClick={()=>{
            if (hasBasemapError && basemapRetryRef.current) basemapRetryRef.current()
            else setMapAttempt(n=>n+1)
          }}>{hasMapError ? 'Réessayer la carte' : 'Réessayer le fond routier'}</button>
        </div>
      ) : null}

      {!isLoading && !hasBasemapError && hoveredName ? (
        <div className="map-readout" aria-hidden="true">
          {hoveredName}
        </div>
      ) : null}

      <div className="layer-placeholders" aria-label="État des couches territoriales">
        {showRealGrid && realGridCount > 0 && (
          <span className="status-badge status-badge--info">
            {realGridCount} {compactControls ? 'secteurs analysés' : `maille${realGridCount > 1 ? 's' : ''} réelle${realGridCount > 1 ? 's' : ''}`}
          </span>
        )}
        {testModeEnabled && isTestData && (
          <span className="status-badge status-badge--warning">
            DONNÉES SYNTHÉTIQUES — DÉMONSTRATION
          </span>
        )}
        {testModeEnabled && hexagonCount > 0 && (
          <span className="status-badge status-badge--success">
            {hexagonCount} maille{hexagonCount > 1 ? 's' : ''} pilote chargée{hexagonCount > 1 ? 's' : ''}
          </span>
        )}
      </div>

      {showRealGrid && realGridCount > 0 && onZoomToPilot && (
        <button
          type="button"
          className="test-zone-button"
          onClick={onZoomToPilot}
          aria-label="Zoomer vers le territoire d’étude Caen et cinq communes"
        >
          {compactControls ? 'Recentrer' : 'Voir la zone d’étude'}
        </button>
      )}

      {testModeEnabled && isTestData && hexagonCount > 0 && onZoomToTestZone && (
        <button
          type="button"
          className="test-zone-button"
          onClick={onZoomToTestZone}
          aria-label="Zoomer vers la zone pilote historique"
        >
          Recentrer le pilote
        </button>
      )}

      <button
        type="button"
        className="test-mode-toggle"
        onClick={onToggleRealGrid}
        aria-pressed={showRealGrid}
      >
        {showRealGrid ? (compactControls ? 'Masquer les mailles' : 'Masquer la grille') : (compactControls ? 'Afficher les mailles' : 'Afficher la grille')}
      </button>

    </div>
  )
}
