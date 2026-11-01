/**
 * GeoJSON adapter for loading M2/M4 data
 * Handles static GeoJSON files and future API integration
 */

import type { FeatureCollection, Geometry } from 'geojson'
import type {
  HexagonFeatureProperties,
  PilotBoundaryProperties,
  StatutAnalyse,
  PriorityExamen,
  DiagnosticDetail,
  PotentialConflict,
  RelatedDataState,
  RestorationActionSuggestion,
  ZoneDiagnosticBundle,
} from '../types/hexagon'

export interface HexagonData {
  featureCollection: FeatureCollection<Geometry, HexagonFeatureProperties>
  gridVersion: string
  isTestData: boolean
  loadingError?: string
}

export interface PilotData {
  featureCollection: FeatureCollection<Geometry, PilotBoundaryProperties>
  statut: 'valide' | 'en_attente'
  isTestData: boolean
  loadingError?: string
}

export interface ZoneDetailData {
  maille_id: string
  statut_analyse: StatutAnalyse
  priorite_examen?: PriorityExamen
  dimensions: {
    enjeu_ecologique: string
    pressions: string[]
    urgence_temporelle: string
  }
  qualite: {
    niveau: 'suffisante' | 'partielle' | 'insuffisante'
    sources_valides: string[]
  }
  conflit_ids: string[]
  actions: Array<{
    action_id: string
    statut: string
    motif: string
  }>
  method_version: string
  test_data?: boolean
}

function dataUrl(fileName: string): string {
  return new URL(`${import.meta.env.BASE_URL}data/${fileName}`, window.location.href).href
}

/**
 * Load hexagonal grid GeoJSON
 * Gracefully handles missing or malformed data
 */
export async function loadHexagonGrid(): Promise<HexagonData> {
  try {
    const response = await fetch(dataUrl('mailles.geojson'))
    if (!response.ok) {
      if (response.status === 404) {
        return {
          featureCollection: { type: 'FeatureCollection', features: [] },
          gridVersion: 'none',
          isTestData: false,
          loadingError: 'Données de mailles non disponibles',
        }
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const geojson: FeatureCollection<Geometry, HexagonFeatureProperties> = await response.json()

    if (!geojson || geojson.type !== 'FeatureCollection' || !Array.isArray(geojson.features)) {
      throw new Error('Format GeoJSON invalide')
    }

    const firstFeature = geojson.features[0]
    const gridVersion = firstFeature?.properties?.grid_version || 'unknown'
    const isTestData = firstFeature?.properties?.test_data === true

    return {
      featureCollection: geojson,
      gridVersion,
      isTestData,
    }
  } catch (error) {
    console.error('[geojsonAdapter] Erreur chargement mailles:', error)
    return {
      featureCollection: { type: 'FeatureCollection', features: [] },
      gridVersion: 'error',
      isTestData: false,
      loadingError: error instanceof Error ? error.message : 'Erreur inconnue',
    }
  }
}

/**
 * Load pilot boundary GeoJSON
 * Returns pending state if not validated
 */
export async function loadPilotBoundary(): Promise<PilotData> {
  try {
    const response = await fetch(dataUrl('pilot-boundary.geojson'))
    if (!response.ok) {
      if (response.status === 404) {
        return {
          featureCollection: { type: 'FeatureCollection', features: [] },
          statut: 'en_attente',
          isTestData: false,
          loadingError: 'Zone pilote en attente de validation',
        }
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const geojson: FeatureCollection<Geometry, PilotBoundaryProperties> = await response.json()

    if (!geojson || geojson.type !== 'FeatureCollection' || !Array.isArray(geojson.features)) {
      throw new Error('Format GeoJSON invalide')
    }

    const firstFeature = geojson.features[0]
    const statut = firstFeature?.properties?.statut || 'en_attente'
    const isTestData = firstFeature?.properties?.test_data === true

    return {
      featureCollection: geojson,
      statut,
      isTestData,
    }
  } catch (error) {
    console.error('[geojsonAdapter] Erreur chargement pilote:', error)
    return {
      featureCollection: { type: 'FeatureCollection', features: [] },
      statut: 'en_attente',
      isTestData: false,
      loadingError: error instanceof Error ? error.message : 'Erreur inconnue',
    }
  }
}

/**
 * Load detailed zone diagnostic information
 * First tries TEST fixture, then real data when available
 */
interface TestRelatedDataFixture {
  test_data: true
  conflicts: Record<string, PotentialConflict>
  actions: Record<string, RestorationActionSuggestion>
  zones: Record<
    string,
    {
      conflit_ids: string[]
      action_ids: string[]
      conflict_state: RelatedDataState
      action_state: RelatedDataState
      test_data: true
    }
  >
}

function resolveFixtureRecords<T extends { test_data?: boolean }>(
  ids: string[],
  records: Record<string, T>,
  recordType: string,
): T[] {
  return ids.flatMap((id) => {
    const record = records[id]
    if (!record) {
      console.warn(`[geojsonAdapter] ${recordType} TEST introuvable : ${id}`)
      return []
    }
    if (record.test_data !== true) {
      console.warn(`[geojsonAdapter] ${recordType} TEST sans marqueur test_data : ${id}`)
      return []
    }
    return [record]
  })
}

export async function loadZoneDiagnostic(
  maille_id: string,
  isTestMode: boolean,
): Promise<ZoneDiagnosticBundle | null> {
  try {
    // In TEST mode, load from TEST fixture
    if (isTestMode) {
      const [diagnosticResponse, relatedResponse] = await Promise.all([
        fetch(dataUrl('diagnostics-test.json')),
        fetch(dataUrl('conflicts-actions-test.json')),
      ])
      if (!diagnosticResponse.ok) {
        throw new Error(`Diagnostics TEST indisponibles (HTTP ${diagnosticResponse.status})`)
      }
      if (!relatedResponse.ok) {
        throw new Error(`Conflits/actions TEST indisponibles (HTTP ${relatedResponse.status})`)
      }

      const testData: Record<string, DiagnosticDetail> = await diagnosticResponse.json()
      const relatedData: TestRelatedDataFixture = await relatedResponse.json()
      const diagnostic = testData[maille_id]

      if (!diagnostic) {
        console.warn(`[geojsonAdapter] Diagnostic non trouvé pour ${maille_id} dans les données TEST`)
        return null
      }

      if (diagnostic.test_data !== true || relatedData.test_data !== true) {
        throw new Error('Fixture TEST sans marqueur test_data')
      }

      const zoneRelations = relatedData.zones[maille_id]
      if (!zoneRelations || zoneRelations.test_data !== true) {
        throw new Error(`Relations TEST non disponibles pour ${maille_id}`)
      }

      const conflitIds = diagnostic.conflit_ids ?? zoneRelations.conflit_ids
      const actionIds = diagnostic.action_ids ?? zoneRelations.action_ids

      return {
        diagnostic,
        conflicts: resolveFixtureRecords(conflitIds, relatedData.conflicts, 'Conflit'),
        actions: resolveFixtureRecords(actionIds, relatedData.actions, 'Action'),
        conflictState: zoneRelations.conflict_state,
        actionState: zoneRelations.action_state,
      }
    }

    // In normal mode, try to load from real data (M4 API or static export)
    // For now, return null - this will be implemented when M4 delivers data
    console.log(`[geojsonAdapter] Chargement diagnostic réel pour ${maille_id} - en attente M4`)
    return null
  } catch (error) {
    console.error('[geojsonAdapter] Erreur chargement diagnostic zone:', error)
    throw error
  }
}

/**
 * Load detailed zone information (legacy interface, preserved for compatibility)
 * This will connect to M4 API in the future
 */
export async function loadZoneDetail(maille_id: string): Promise<ZoneDetailData | null> {
  try {
    const response = await fetch(dataUrl(`zone-${maille_id}.json`))
    if (!response.ok) {
      if (response.status === 404) {
        return null
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const data: ZoneDetailData = await response.json()
    return data
  } catch (error) {
    console.error('[geojsonAdapter] Erreur chargement détail zone:', error)
    return null
  }
}

/**
 * Get priority color for MapLibre style
 * Matches PriorityLegend colors
 */
export function getPriorityColor(priority?: PriorityExamen): string {
  switch (priority) {
    case 'elevee':
      return '#D65A5A'
    case 'moderee':
      return '#E8A87C'
    case 'faible':
      return '#C4D4A0'
    case 'indeterminee':
      return '#8B9D83'
    default:
      return '#B8B8B8'
  }
}

/**
 * Get analysis status color
 */
export function getAnalysisStatusColor(statut: StatutAnalyse): string {
  switch (statut) {
    case 'calculee':
      return '#C4D4A0'
    case 'donnees_insuffisantes':
      return '#E8A87C'
    case 'analyse_non_realisee':
      return '#B8B8B8'
    default:
      return '#B8B8B8'
  }
}
