import type { FeatureCollection, Geometry } from 'geojson'
import {
  PRIORITY_GRID_VERSION,
  applyEcologicalPriorities,
  type EcologicalPriorityCategory,
  type RealGridFeatureProperties,
} from './priorityAdapter.ts'

export type GridMode = 'TEST' | 'REAL'

export const CAEN_NORD_GRID_VERSION = 'M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1' as const
export const CAEN_TERRITORY_ID = 'caen_et_nord_6communes' as const

export interface GridDatasetDefinition {
  key: string
  label: string
  fileName: string
  gridVersion: string
  bounds: [[number, number], [number, number]]
}

export interface PreparedGridDataset {
  definition: GridDatasetDefinition
  featureCollection: FeatureCollection<Geometry, RealGridFeatureProperties>
}

export const TEST_GRID_DATASET: GridDatasetDefinition = {
  key: 'm1-pilot-test-v1',
  label: 'Pilote M1 — démonstration TEST',
  fileName: 'grille_pilote_wgs84.geojson',
  gridVersion: PRIORITY_GRID_VERSION,
  bounds: [
    [-0.28, 49.2],
    [-0.22, 49.26],
  ],
}

export const REAL_GRID_DATASETS = {
  'm1-caen-6com-v1': {
    key: 'm1-caen-6com-v1',
    label: 'Territoire M1 Caen et cinq communes',
    fileName: '',
    gridVersion: CAEN_NORD_GRID_VERSION,
    bounds: [
      [-0.41376271, 49.15302147],
      [-0.22723671, 49.29291092],
    ],
  },
} as const satisfies Record<string, GridDatasetDefinition>

export const DEFAULT_REAL_GRID_DATASET = REAL_GRID_DATASETS['m1-caen-6com-v1']

function validateGrid(
  grid: FeatureCollection<Geometry>,
  definition: GridDatasetDefinition,
): void {
  if (grid.type !== 'FeatureCollection' || !Array.isArray(grid.features)) {
    throw new Error(`Dataset ${definition.key} : FeatureCollection GeoJSON invalide`)
  }

  const ids = new Set<string>()
  for (const feature of grid.features) {
    const mailleId = feature.properties?.maille_id
    const gridVersion = feature.properties?.grid_version
    if (typeof mailleId !== 'string' || mailleId.length === 0) {
      throw new Error(`Dataset ${definition.key} : maille_id manquant`)
    }
    if (ids.has(mailleId)) {
      throw new Error(`Dataset ${definition.key} : maille_id dupliqué (${mailleId})`)
    }
    if (gridVersion !== definition.gridVersion) {
      throw new Error(
        `Dataset ${definition.key} : version ${String(gridVersion)} incompatible avec ${definition.gridVersion}`,
      )
    }
    ids.add(mailleId)
  }
}

const SYNTHETIC_CATEGORIES: readonly EcologicalPriorityCategory[] = [
  'HIGH',
  'MODERATE',
  'LOW',
  'INDETERMINATE',
]

export function createSyntheticTestPriorities(
  grid: FeatureCollection<Geometry>,
): Map<string, EcologicalPriorityCategory> {
  const sortedIds = grid.features
    .map((feature) => String(feature.properties?.maille_id ?? ''))
    .sort((left, right) => left.localeCompare(right))

  return new Map(
    sortedIds.map((mailleId, index) => [
      mailleId,
      SYNTHETIC_CATEGORIES[index % SYNTHETIC_CATEGORIES.length],
    ]),
  )
}

export function prepareGridDataset(
  grid: FeatureCollection<Geometry>,
  definition: GridDatasetDefinition,
  mode: GridMode,
  priorityRecords: readonly unknown[] = [],
): PreparedGridDataset {
  validateGrid(grid, definition)

  if (mode === 'TEST' && grid.features.length !== 43) {
    throw new Error('La grille TEST permanente doit contenir exactement 43 mailles')
  }
  if (mode === 'REAL' && grid.features.length !== 101) {
    throw new Error('La grille REAL Caen et cinq communes doit contenir exactement 101 mailles')
  }

  const prepared = applyEcologicalPriorities(grid, mode === 'TEST' ? [] : priorityRecords)

  if (mode === 'TEST') {
    const syntheticPriorities = createSyntheticTestPriorities(grid)
    for (const feature of prepared.features) {
      feature.properties = {
        ...feature.properties,
        priority_category: syntheticPriorities.get(feature.properties.maille_id) ?? 'INDETERMINATE',
        priority_validation_status: 'UNKNOWN',
        priority_method_version: 'synthetic-demo-v1',
        priority_justification: 'Priorité fictive attribuée uniquement pour la démonstration du mode TEST.',
        priority_reliability: 'UNKNOWN',
        priority_uncertainty: 'Donnée synthétique sans valeur scientifique.',
        priority_limitations: ['Ne pas interpréter comme une conclusion écologique validée.'],
        priority_provenance: ['Démonstration synthétique M3'],
        priority_resolution_reason: 'synthetic_demo',
      }
    }
  }

  return {
    definition,
    featureCollection: prepared,
  }
}
