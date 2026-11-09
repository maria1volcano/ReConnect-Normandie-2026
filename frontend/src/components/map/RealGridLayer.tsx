/**
 * RealGridLayer - MapLibre layer for M1 real candidate hexagonal grid
 * Renders the 43 real hexagons from M1 with neutral styling
 * Separate from TEST data - no ecological priorities, just geographic display
 */

import { useEffect, useRef, useCallback } from 'react'
import type { Map as MapLibreMap } from 'maplibre-gl'
import type { FeatureCollection } from 'geojson'

const REAL_GRID_SOURCE = 'real-grid-source'
const REAL_GRID_FILL_LAYER = 'real-grid-fill'
const REAL_GRID_LINE_LAYER = 'real-grid-line'

interface RealGridLayerProps {
  map: MapLibreMap | undefined
  realGridData: FeatureCollection
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

      // Neutral teal fill - no ecological priority colors
      map.addLayer({
        id: REAL_GRID_FILL_LAYER,
        type: 'fill',
        source: REAL_GRID_SOURCE,
        paint: {
          'fill-color': '#127475', // Teal - neutral, not a priority color
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.45,
            ['boolean', ['feature-state', 'hover'], false],
            0.35,
            0.25, // Lower opacity to preserve basemap visibility
          ],
          'fill-opacity-transition': { duration: 200 },
        },
      })

      // Subtle outline
      map.addLayer({
        id: REAL_GRID_LINE_LAYER,
        type: 'line',
        source: REAL_GRID_SOURCE,
        layout: { 'line-join': 'round' },
        paint: {
          'line-color': '#0E5E5F', // Darker teal
          'line-opacity': 0.7,
          'line-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            2.5,
            ['boolean', ['feature-state', 'hover'], false],
            2,
            1.5,
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
