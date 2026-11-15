/**
 * RealGridLayer - MapLibre layer for M1 real candidate hexagonal grid
 * Renders the active M1 grid using validated priority properties.
 * The priority adapter currently resolves every real cell to INDETERMINATE.
 */

import { useEffect, useRef, useCallback } from 'react'
import type { ExpressionSpecification, Map as MapLibreMap } from 'maplibre-gl'
import type { FeatureCollection, Geometry } from 'geojson'
import type { RealGridFeatureProperties } from '../../integrations/priorityAdapter'

const REAL_GRID_SOURCE = 'real-grid-source'
const REAL_GRID_FILL_LAYER = 'real-grid-fill'
const REAL_GRID_LINE_LAYER = 'real-grid-line'

const DOCUMENTARY_COLOR_EXPRESSION = [
  'match',
  ['get', 'documentary_level'],
  'rouge', '#D9534F',
  'orange', '#F29A48',
  'jaune', '#E6C65B',
  'gris', '#89938F',
  '#89938F',
] as ExpressionSpecification

const ECOLOGICAL_COLOR_EXPRESSION = [
  'match',
  ['get', 'priority_category'],
  'HIGH',
  '#D9534F',
  'MODERATE',
  '#F29A48',
  'LOW',
  '#E6C65B',
  'INDETERMINATE',
  '#89938F',
  '#89938F',
] as ExpressionSpecification

function fillColorExpression(view: 'study' | 'documentary' | 'ecological' | 'neutral'): ExpressionSpecification | string {
  if (view === 'neutral') return '#8fa99f'
  return view === 'study' ? ['get', 'study_color'] as ExpressionSpecification : view === 'documentary' ? DOCUMENTARY_COLOR_EXPRESSION : ECOLOGICAL_COLOR_EXPRESSION
}

interface RealGridLayerProps {
  contextualBasemap?: boolean
  map: MapLibreMap | undefined
  realGridData: FeatureCollection<Geometry, RealGridFeatureProperties>
  selectedRealHexagonId: string | null
  hoveredRealHexagonId: string | null
  onSelectRealHexagon: (id: string | null) => void
  onHoverRealHexagon: (id: string | null) => void
  showRealGrid: boolean
  classificationView?: 'study' | 'documentary' | 'ecological' | 'neutral'
  highlightedMailleIds?: ReadonlySet<string> | null
}

export function RealGridLayer({
  map,
  contextualBasemap = false,
  realGridData,
  selectedRealHexagonId,
  hoveredRealHexagonId,
  onSelectRealHexagon,
  onHoverRealHexagon,
  showRealGrid,
  classificationView = 'ecological',
  highlightedMailleIds = null,
}: RealGridLayerProps) {
  const isInitializedRef = useRef(false)
  const classificationRef = useRef(classificationView)
  const eventHandlersRef = useRef<Record<string, (event: any) => void> | null>(null)
  const selectRef = useRef(onSelectRealHexagon)
  const hoverRef = useRef(onHoverRealHexagon)

  useEffect(() => {
    classificationRef.current = classificationView
    selectRef.current = onSelectRealHexagon
    hoverRef.current = onHoverRealHexagon
  }, [onSelectRealHexagon, onHoverRealHexagon, classificationView])

  const initializeLayer = useCallback(() => {
    if (!map || isInitializedRef.current) return

    try {
      map.addSource(REAL_GRID_SOURCE, {
        type: 'geojson',
        data: realGridData,
        promoteId: 'maille_id',
      })

      map.addLayer({
        id: REAL_GRID_FILL_LAYER,
        type: 'fill',
        source: REAL_GRID_SOURCE,
        paint: {
          'fill-color': fillColorExpression(classificationRef.current),
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            contextualBasemap ? 0.52 : 0.78,
            ['boolean', ['feature-state', 'hover'], false],
            contextualBasemap ? 0.44 : 0.74,
            contextualBasemap ? 0.30 : 0.7,
          ],
          'fill-opacity-transition': { duration: 200 },
        },
      })

      map.addLayer({
        id: REAL_GRID_LINE_LAYER,
        type: 'line',
        source: REAL_GRID_SOURCE,
        layout: { 'line-join': 'round' },
        paint: {
          'line-color': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            '#FFFFFF',
            ['boolean', ['feature-state', 'hover'], false],
            '#E9FFF6',
            ['boolean', ['feature-state', 'highlighted'], false],
            '#6FF5C8',
            '#3E4B47',
          ] as ExpressionSpecification,
          'line-opacity': 0.95,
          'line-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            3,
            ['boolean', ['feature-state', 'hover'], false],
            2.4,
            ['boolean', ['feature-state', 'highlighted'], false],
            2,
            0.75,
          ],
        },
      })

      const handlers: Record<string, (event: any) => void> = {
        mousemove: (event) => {
          const id = event.features?.[0]?.properties?.maille_id
          if (typeof id === 'string') {
            map.getCanvas().style.cursor = 'pointer'
            hoverRef.current(id)
          }
        },
        mouseleave: () => {
          map.getCanvas().style.cursor = ''
          hoverRef.current(null)
        },
        click: (event) => {
          const id = event.features?.[0]?.properties?.maille_id
          if (typeof id === 'string') selectRef.current(id)
        },
      }
      eventHandlersRef.current = handlers
      for (const [type, listener] of Object.entries(handlers)) {
        ;(map as any).on(type, REAL_GRID_FILL_LAYER, listener)
      }

      isInitializedRef.current = true
    } catch (error) {
      console.error('[RealGridLayer] Erreur initialisation:', error)
    }
  }, [map, realGridData, contextualBasemap])

  const cleanupLayer = useCallback(() => {
    if (!map) return

    try {
      for (const [type, listener] of Object.entries(eventHandlersRef.current ?? {})) {
        ;(map as any).off(type, REAL_GRID_FILL_LAYER, listener)
      }
      eventHandlersRef.current = null

      if (map.getLayer(REAL_GRID_LINE_LAYER)) {
        map.removeLayer(REAL_GRID_LINE_LAYER)
      }
      if (map.getLayer(REAL_GRID_FILL_LAYER)) {
        map.removeLayer(REAL_GRID_FILL_LAYER)
      }
      if (map.getSource(REAL_GRID_SOURCE)) {
        map.removeSource(REAL_GRID_SOURCE)
      }

      isInitializedRef.current = false
    } catch (error) {
      console.error('[RealGridLayer] Erreur nettoyage:', error)
    }
  }, [map])

  useEffect(() => {
    if (!map) return

    if (showRealGrid && realGridData.features.length > 0 && !isInitializedRef.current) {
      initializeLayer()
    } else if (!showRealGrid && isInitializedRef.current) {
      cleanupLayer()
    }

    return () => {
      if (isInitializedRef.current) {
        cleanupLayer()
      }
    }
  }, [map, showRealGrid, realGridData, initializeLayer, cleanupLayer])

  useEffect(() => {
    if (!map || !isInitializedRef.current) return
    const source = map.getSource(REAL_GRID_SOURCE) as { setData?: (data: unknown) => void } | undefined
    source?.setData?.(realGridData)
  }, [map, realGridData])

  useEffect(() => {
    if (!map || !isInitializedRef.current) return
    if (!map.getLayer(REAL_GRID_FILL_LAYER)) return
    map.setPaintProperty(REAL_GRID_FILL_LAYER, 'fill-color', fillColorExpression(classificationView))
  }, [map, classificationView])

  useEffect(() => {
    if (!map || !isInitializedRef.current) return

    const applyStates = () => {
      if (!map.getSource(REAL_GRID_SOURCE)) return

      for (const feature of realGridData.features) {
        const mailleId = feature.properties?.maille_id
        if (mailleId) {
          map.setFeatureState(
            { source: REAL_GRID_SOURCE, id: mailleId },
            {
              hover: mailleId === hoveredRealHexagonId,
              selected: mailleId === selectedRealHexagonId,
              highlighted: highlightedMailleIds?.has(mailleId) ?? false,
            },
          )
        }
      }
    }

    if (map.isStyleLoaded()) {
      applyStates()
    }
    map.on('styledata', applyStates)

    return () => {
      map.off('styledata', applyStates)
    }
  }, [map, realGridData, selectedRealHexagonId, hoveredRealHexagonId, highlightedMailleIds])

  return null
}
