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
import type { RealGridFeatureProperties } from './priorityAdapter'
import {
  DEFAULT_REAL_GRID_DATASET,
  TEST_GRID_DATASET,
  prepareGridDataset,
  type GridDatasetDefinition,
} from './gridDatasets.ts'

export interface HexagonData {
  featureCollection: FeatureCollection<Geometry, HexagonFeatureProperties>
  gridVersion: string
  isTestData: boolean
  loadingError?: string
}

export interface RealGridData {
  featureCollection: FeatureCollection<Geometry, RealGridFeatureProperties>
  gridVersion: string
  dataset: GridDatasetDefinition
  loadingError?: string
}

export interface M1Measurements {
  maille_id: string
  grid_version: string
  cell_area_m2: number
  is_boundary: boolean
  road_length_m: number
  road_object_count: number
  reservoir_area_m2: number
  reservoir_object_count: number
  corridor_area_m2: number
  corridor_object_count: number
  ocs_covered_area_m2: number
  ocs_coverage_fraction: number
  constructed_area_m2: number
  hedge_length_m: number
  hedge_object_count: number
  sipaf_record_count: number | null
  cartofriches_area_m2: number
  cartofriches_site_count: number
  wetland_area_m2: number
  wetland_record_count: number
  pram_pond_count: null
  epfn_site_count: null
  length_unit: string
  area_unit: string
  measurement_crs: string
  p0_coverage_status: string
  bdhaie_coverage_status: string
  sipaf_coverage_status: string
  cartofriches_coverage_status: string
  wetland_coverage_status: string
  pram_coverage_status: string
  epfn_coverage_status: string
  source_ids: string
}

export interface OCSMeasurement {
  maille_id: string
  grid_version: string
  ocs_code_cs: string
  ocs_area_m2: number
  ocs_fraction_of_cell: number
  area_unit: string
  source_id: string
  source_year: string
}

export interface M1SourceMetadata {
  source_id: string
  name: string
  producer: string
  reference_year: string | null
  version: string | null
  official_url: string | null
  license: string | null
  license_url: string | null
  geographic_coverage: string | null
  restrictions: string | null
  status: string
}

export interface M1SourceCatalog {
  version: string
  generated_from: string
  sources: Record<string, M1SourceMetadata>
  unavailable_sources: Record<string, M1SourceMetadata>
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

export function matchesGridVersion(
  record: { grid_version: string },
  expectedGridVersion?: string,
): boolean {
  return !expectedGridVersion || record.grid_version === expectedGridVersion
}

/**
 * Load M1 geographic measurements for a specific hexagon
 */
export async function loadM1Measurements(
  maille_id: string,
  expectedGridVersion?: string,
): Promise<M1Measurements | null> {
  try {
    const response = await fetch(dataUrl('sub_indicateurs.json'))
    if (!response.ok) {
      console.error('[geojsonAdapter] Erreur chargement mesures M1:', response.status)
      return null
    }

    const data: Record<string, M1Measurements> = await response.json()
    const measurement = data[maille_id] || null
    return measurement && matchesGridVersion(measurement, expectedGridVersion)
      ? measurement
      : null
  } catch (error) {
    console.error('[geojsonAdapter] Erreur chargement mesures M1:', error)
    return null
  }
}

/**
 * Load OCS land cover measurements for a specific hexagon
 */
export async function loadOCSMeasurements(
  maille_id: string,
  expectedGridVersion?: string,
): Promise<OCSMeasurement[]> {
  try {
    const response = await fetch(dataUrl('sub_indicateurs_ocs.json'))
    if (!response.ok) {
      console.error('[geojsonAdapter] Erreur chargement OCS:', response.status)
      return []
    }

    const data: Record<string, OCSMeasurement[]> = await response.json()
    const measurements = data[maille_id] || []
    return expectedGridVersion
      ? measurements.filter((measurement) => matchesGridVersion(measurement, expectedGridVersion))
      : measurements
  } catch (error) {
    console.error('[geojsonAdapter] Erreur chargement OCS:', error)
    return []
  }
}

/** Load the lightweight provenance export derived from M1 sources.json. */
export async function loadM1SourceCatalog(): Promise<M1SourceCatalog | null> {
  try {
    const response = await fetch(dataUrl('sources-m1.json'))
    if (!response.ok) {
      console.error('[geojsonAdapter] Erreur chargement sources M1:', response.status)
      return null
    }

    const catalog: M1SourceCatalog = await response.json()
    if (!catalog.sources || !catalog.unavailable_sources) {
      throw new Error('Catalogue de sources M1 invalide')
    }
    return catalog
  } catch (error) {
    console.error('[geojsonAdapter] Erreur chargement sources M1:', error)
    return null
  }
}

async function loadGridDataset(
  dataset: GridDatasetDefinition,
  mode: 'TEST' | 'REAL',
  priorityRecords: readonly unknown[] = [],
): Promise<RealGridData> {
  try {
    const response = await fetch(dataUrl(dataset.fileName))
    if (!response.ok) {
      if (response.status === 404) {
        return {
          featureCollection: { type: 'FeatureCollection', features: [] },
          gridVersion: dataset.gridVersion,
          dataset,
          loadingError: `Grille ${dataset.label} non disponible`,
        }
      }
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }

    const geojson: FeatureCollection = await response.json()

    if (!geojson || geojson.type !== 'FeatureCollection' || !Array.isArray(geojson.features)) {
      throw new Error('Format GeoJSON invalide')
    }

    const prepared = prepareGridDataset(geojson, dataset, mode, priorityRecords)

    return {
      featureCollection: prepared.featureCollection,
      gridVersion: dataset.gridVersion,
      dataset,
    }
  } catch (error) {
    console.error(`[geojsonAdapter] Erreur chargement grille ${dataset.key}:`, error)
    return {
      featureCollection: { type: 'FeatureCollection', features: [] },
      gridVersion: dataset.gridVersion,
      dataset,
      loadingError: error instanceof Error ? error.message : 'Erreur inconnue',
    }
  }
}

/** Fixed 43-cell M1 pilot used exclusively for synthetic demonstration. */
export function loadTestGrid(): Promise<RealGridData> {
  return loadGridDataset(TEST_GRID_DATASET, 'TEST')
}

/** Configurable REAL dataset; future grids must provide their own versioned definition. */
export function loadRealGrid(
  dataset: GridDatasetDefinition = DEFAULT_REAL_GRID_DATASET,
  priorityRecords: readonly unknown[] = [],
): Promise<RealGridData> {
  return loadGridDataset(dataset, 'REAL', priorityRecords)
}

/**
 * Load hexagonal grid GeoJSON (TEST data)
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
