/**
 * HexGridLayer - MapLibre hexagonal diagnostic grid layer
 * Renders hexagonal polygons with hover and selection states
 * Does not create its own map instance - uses existing map reference
 */

import { useEffect, useRef, useCallback } from 'react'
import type { Map as MapLibreMap, ExpressionSpecification } from 'maplibre-gl'
import type { FeatureCollection } from 'geojson'

const HEX_SOURCE = 'hex-grid-source'
const HEX_FILL_LAYER = 'hex-grid-fill'
const HEX_LINE_LAYER = 'hex-grid-line'

interface HexGridLayerProps {
  map: MapLibreMap | undefined
  hexagonData: FeatureCollection
  selectedHexagonId: string | null
  hoveredHexagonId: string | null
  onSelectHexagon: (id: string | null) => void
  onHoverHexagon: (id: string | null) => void
  testModeEnabled?: boolean
}

export function HexGridLayer({
  map,
  hexagonData,
  selectedHexagonId,
  hoveredHexagonId,
  onSelectHexagon,
  onHoverHexagon,
  testModeEnabled = false,
}: HexGridLayerProps) {
  const isInitializedRef = useRef(false)
  const selectRef = useRef(onSelectHexagon)
  const hoverRef = useRef(onHoverHexagon)

  useEffect(() => {
    selectRef.current = onSelectHexagon
    hoverRef.current = onHoverHexagon
  }, [onSelectHexagon, onHoverHexagon])

  const initializeLayer = useCallback(() => {
    if (!map || isInitializedRef.current) return

    try {
      map.addSource(HEX_SOURCE, {
        type: 'geojson',
        data: hexagonData,
      })

      map.addLayer({
        id: HEX_FILL_LAYER,
        type: 'fill',
        source: HEX_SOURCE,
        paint: {
          'fill-color': [
            'match',
            ['get', 'priorite_examen'],
            'elevee',
            '#D9534F',
            'moderee',
            '#F29A48',
            'faible',
            '#E6C65B',
            'indeterminee',
            '#89938F',
            '#89938F',
          ] as ExpressionSpecification,
          'fill-opacity': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            0.8,
            ['boolean', ['feature-state', 'hover'], false],
            0.7,
            0.65,
          ],
          'fill-opacity-transition': { duration: 200 },
        },
      })

      map.addLayer({
        id: HEX_LINE_LAYER,
        type: 'line',
        source: HEX_SOURCE,
        layout: { 'line-join': 'round' },
        paint: {
          'line-color': [
            'match',
            ['get', 'priorite_examen'],
            'elevee',
            '#8F302D',
            'moderee',
            '#A85A18',
            'faible',
            '#897414',
            'indeterminee',
            '#3E4B47',
            '#FFFFFF',
          ] as ExpressionSpecification,
          'line-opacity': 0.9,
          'line-width': [
            'case',
            ['boolean', ['feature-state', 'selected'], false],
            2,
            4,
          ],
        },
      })

      map.addLayer({
        id: 'hex-labels',
        type: 'symbol',
        source: HEX_SOURCE,
        layout: {
          'text-field': ['get', 'maille_id'],
          'text-size': 11,
          'text-anchor': 'center',
          'text-justify': 'center',
        },
        paint: {
          'text-color': '#303726',
          'text-halo-color': '#FFFFFF',
          'text-halo-width': 2,
          'text-opacity': 0.9,
        },
      })

      ;(map as any).on('mousemove', HEX_FILL_LAYER, (event: any) => {
        const mailleId = event.features?.[0]?.properties?.maille_id
        if (mailleId && typeof mailleId === 'string') {
          map.getCanvas().style.cursor = 'pointer'
          hoverRef.current(mailleId)
        }
      })

      ;(map as any).on('mouseleave', HEX_FILL_LAYER, () => {
        map.getCanvas().style.cursor = ''
        hoverRef.current(null)
      })

      ;(map as any).on('click', HEX_FILL_LAYER, (event: any) => {
        const mailleId = event.features?.[0]?.properties?.maille_id
        if (mailleId && typeof mailleId === 'string') {
          selectRef.current(mailleId)
        }
      })

      isInitializedRef.current = true
    } catch (error) {
      console.error('[HexGridLayer] Erreur initialisation:', error)
    }
  }, [map, hexagonData])

  const cleanupLayer = useCallback(() => {
    if (!map) return

    try {
      ;(map as any).off('mousemove', HEX_FILL_LAYER)
      ;(map as any).off('mouseleave', HEX_FILL_LAYER)
      ;(map as any).off('click', HEX_FILL_LAYER)

      if (map.getLayer('hex-labels')) {
        map.removeLayer('hex-labels')
      }
      if (map.getLayer(HEX_LINE_LAYER)) {
        map.removeLayer(HEX_LINE_LAYER)
      }
      if (map.getLayer(HEX_FILL_LAYER)) {
        map.removeLayer(HEX_FILL_LAYER)
      }
      if (map.getSource(HEX_SOURCE)) {
        map.removeSource(HEX_SOURCE)
      }

      isInitializedRef.current = false
    } catch (error) {
      console.error('[HexGridLayer] Erreur nettoyage:', error)
    }
  }, [map])

  useEffect(() => {
    if (!map) return

    if (hexagonData.features.length > 0 && !isInitializedRef.current) {
      initializeLayer()
    } else if (hexagonData.features.length === 0 && isInitializedRef.current) {
      cleanupLayer()
    }

    return () => {
      if (isInitializedRef.current) {
        cleanupLayer()
      }
    }
  }, [map, hexagonData, initializeLayer, cleanupLayer])

  useEffect(() => {
    if (!map || !isInitializedRef.current) return

    const applyStates = () => {
      if (!map.getSource(HEX_SOURCE)) return

      const source = map.getSource(HEX_SOURCE) as any
      const features = source._data?.features || []

      for (const feature of features) {
        const mailleId = feature.properties?.maille_id
        if (mailleId) {
          map.setFeatureState(
            { source: HEX_SOURCE, id: mailleId },
            {
              hover: mailleId === hoveredHexagonId,
              selected: mailleId === selectedHexagonId,
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
  }, [map, selectedHexagonId, hoveredHexagonId])

  useEffect(() => {
    if (!map) return

    if (testModeEnabled && hexagonData.features.length > 0 && !isInitializedRef.current) {
      initializeLayer()
    } else if (!testModeEnabled && isInitializedRef.current) {
      cleanupLayer()
    }

    return () => {
      if (isInitializedRef.current) {
        cleanupLayer()
      }
    }
  }, [map, hexagonData, testModeEnabled, initializeLayer, cleanupLayer])

  return null
}
