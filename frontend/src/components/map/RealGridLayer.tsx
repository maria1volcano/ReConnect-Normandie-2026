/**
 * RealGridLayer - MapLibre layer for M1 real candidate hexagonal grid
 * Renders the 43 real hexagons from M1 using validated priority properties.
 * The priority adapter currently resolves every real cell to INDETERMINATE.
 */

import { useEffect, useRef, useCallback } from 'react'
import type { ExpressionSpecification, Map as MapLibreMap } from 'maplibre-gl'
import type { FeatureCollection, Geometry } from 'geojson'
import type { RealGridFeatureProperties } from '../../integrations/priorityAdapter'

const REAL_GRID_SOURCE = 'real-grid-source'
const REAL_GRID_FILL_LAYER = 'real-grid-fill'
const REAL_GRID_LINE_LAYER = 'real-grid-line'

interface RealGridLayerProps {
  map: MapLibreMap | undefined
  realGridData: FeatureCollection<Geometry, RealGridFeatureProperties>
  selectedRealHexagonId: string | null
  hoveredRealHexagonId: string | null
  onSelectRealHexagon: (id: string | null) => void
  onHoverRealHexagon: (id: string | null) => void
  showRealGrid: boolean
}

export function RealGridLayer({
  map,
  realGridData,
  selectedRealHexagonId,
  hoveredRealHexagonId,
  onSelectRealHexagon,
  onHoverRealHexagon,
  showRealGrid,
}: RealGridLayerProps) {
  const isInitializedRef = useRef(false)
  const selectRef = useRef(onSelectRealHexagon)
  const hoverRef = useRef(onHoverRealHexagon)

  useEffect(() => {
    selectRef.current = onSelectRealHexagon
    hoverRef.current = onHoverRealHexagon
  }, [onSelectRealHexagon, onHoverRealHexagon])

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
          'fill-color': [
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
          ] as ExpressionSpecification,
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.68,
            ['boolean', ['feature-state', 'hover'], false],
            0.6,
            0.5,
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
            '#3E4B47',
          ] as ExpressionSpecification,
          'line-opacity': 0.95,
          'line-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            3,
            ['boolean', ['feature-state', 'hover'], false],
            2.4,
            1.2,
          ],
        },
      })

      ;(map as any).on('mousemove', REAL_GRID_FILL_LAYER, (event: any) => {
        const mailleId = event.features?.[0]?.properties?.maille_id
        if (mailleId && typeof mailleId === 'string') {
          map.getCanvas().style.cursor = 'pointer'
          hoverRef.current(mailleId)
        }
      })

      ;(map as any).on('mouseleave', REAL_GRID_FILL_LAYER, () => {
        map.getCanvas().style.cursor = ''
        hoverRef.current(null)
      })

      ;(map as any).on('click', REAL_GRID_FILL_LAYER, (event: any) => {
        const mailleId = event.features?.[0]?.properties?.maille_id
        if (mailleId && typeof mailleId === 'string') {
          selectRef.current(mailleId)
        }
      })

      isInitializedRef.current = true
    } catch (error) {
      console.error('[RealGridLayer] Erreur initialisation:', error)
    }
  }, [map, realGridData])

  const cleanupLayer = useCallback(() => {
    if (!map) return

    try {
      ;(map as any).off('mousemove', REAL_GRID_FILL_LAYER)
      ;(map as any).off('mouseleave', REAL_GRID_FILL_LAYER)
      ;(map as any).off('click', REAL_GRID_FILL_LAYER)

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
  }, [map, realGridData, selectedRealHexagonId, hoveredRealHexagonId])

  return null
}
