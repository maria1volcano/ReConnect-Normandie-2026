import assert from 'node:assert/strict'
import { readdir, readFile } from 'node:fs/promises'
import {
  ECOLOGICAL_PRIORITY,
  PRIORITY_GRID_VERSION,
  applyEcologicalPriorities,
  resolveEcologicalPriority,
} from '../src/integrations/priorityAdapter.ts'
import {
  DEFAULT_REAL_GRID_DATASET,
  TEST_GRID_DATASET,
  prepareGridDataset,
} from '../src/integrations/gridDatasets.ts'
import { matchesGridVersion } from '../src/integrations/geojsonAdapter.ts'
import { M2UnavailableError, parseM2CellSummary } from '../src/integrations/m2Adapter.ts'

const publicDataPath = new URL('../public/data/', import.meta.url)
const grid = JSON.parse(await readFile(new URL('grille_pilote_wgs84.geojson', publicDataPath), 'utf8'))

assert.equal(grid.features.length, 43, 'La grille réelle doit contenir exactement 43 mailles')
assert.equal(new Set(grid.features.map((feature) => feature.properties.maille_id)).size, 43)
assert.ok(grid.features.every((feature) => feature.properties.grid_version === PRIORITY_GRID_VERSION))

const currentGrid = applyEcologicalPriorities(grid, [])
assert.ok(
  currentGrid.features.every((feature) => feature.properties.priority_category === 'INDETERMINATE'),
  'Toutes les mailles réelles doivent rester indéterminées sans priorité validée',
)

const testGrid = prepareGridDataset(grid, TEST_GRID_DATASET, 'TEST')
assert.equal(testGrid.featureCollection.features.length, 43)
assert.deepEqual(
  testGrid.featureCollection.features.map((feature) => feature.geometry),
  grid.features.map((feature) => feature.geometry),
  'TEST doit réutiliser exactement les géométries du pilote M1',
)
assert.deepEqual(
  testGrid.featureCollection.features.map((feature) => [
    feature.properties.maille_id,
    feature.properties.grid_version,
  ]),
  grid.features.map((feature) => [feature.properties.maille_id, feature.properties.grid_version]),
  'TEST doit conserver les maille_id et grid_version d’origine',
)
assert.deepEqual(
  new Set(testGrid.featureCollection.features.map((feature) => feature.properties.priority_category)),
  new Set(['HIGH', 'MODERATE', 'LOW', 'INDETERMINATE']),
  'TEST doit afficher les quatre couleurs synthétiques',
)

const syntheticExpandedDefinition = {
  key: 'fixture-expanded-real',
  label: 'Fixture REAL étendue',
  fileName: 'fixture-not-public.geojson',
  gridVersion: 'M1-EXPANDED-FIXTURE-V2',
  bounds: [[-0.3, 49.1], [-0.1, 49.3]],
}
const syntheticExpandedGrid = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { maille_id: 'EXPANDED-001', grid_version: 'M1-EXPANDED-FIXTURE-V2' },
      geometry: { type: 'Polygon', coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]] },
    },
    {
      type: 'Feature',
      properties: { maille_id: 'EXPANDED-002', grid_version: 'M1-EXPANDED-FIXTURE-V2' },
      geometry: { type: 'Polygon', coordinates: [[[1, 0], [2, 0], [2, 1], [1, 1], [1, 0]]] },
    },
  ],
}
const expandedReal = prepareGridDataset(syntheticExpandedGrid, syntheticExpandedDefinition, 'REAL')
assert.equal(expandedReal.featureCollection.features.length, 2)
assert.equal(testGrid.featureCollection.features.length, 43, 'La configuration REAL ne modifie pas TEST')
assert.throws(
  () => prepareGridDataset(syntheticExpandedGrid, DEFAULT_REAL_GRID_DATASET, 'REAL'),
  /incompatible/,
)
assert.equal(matchesGridVersion({ grid_version: PRIORITY_GRID_VERSION }, PRIORITY_GRID_VERSION), true)
assert.equal(matchesGridVersion({ grid_version: 'INCOMPATIBLE' }, PRIORITY_GRID_VERSION), false)

const baseRecord = {
  maille_id: grid.features[0].properties.maille_id,
  grid_version: PRIORITY_GRID_VERSION,
  category: 'HIGH',
  scientific_validation: 'VALIDATED',
  method_version: 'test-method',
  justification: 'Fixture de validation technique.',
  reliability: {
    level: 'SUFFICIENT',
    uncertainty: null,
    limitations: [],
  },
  provenance: ['fixture-technique'],
}

assert.equal(
  resolveEcologicalPriority(baseRecord.maille_id, PRIORITY_GRID_VERSION, baseRecord).category,
  'HIGH',
)
assert.equal(
  resolveEcologicalPriority(baseRecord.maille_id, PRIORITY_GRID_VERSION, {
    ...baseRecord,
    scientific_validation: 'PENDING',
  }).category,
  'INDETERMINATE',
)
const mismatchedPriority = resolveEcologicalPriority(baseRecord.maille_id, PRIORITY_GRID_VERSION, {
    ...baseRecord,
    grid_version: 'INCOMPATIBLE',
  })
assert.equal(mismatchedPriority.category, 'INDETERMINATE')
assert.equal(mismatchedPriority.scientific_validation, 'UNKNOWN')
assert.equal(mismatchedPriority.resolution_reason, 'grid_version_mismatch')
assert.equal(
  resolveEcologicalPriority(baseRecord.maille_id, PRIORITY_GRID_VERSION, null).category,
  'INDETERMINATE',
)

const m2Fixture = {
  schemaVersion: 'm2-m4.internal-cell-summary-1',
  dataNature: 'reelle',
  diffusion: 'interne_revue_uniquement',
  cellId: baseRecord.maille_id,
  gridVersion: PRIORITY_GRID_VERSION,
  observations: {
    status: 'geometric_detection',
    qualification: 'geometrie_2d',
    distinctEventCount: 0,
    relationshipCount: 0,
    canonicalOwnerCount: 0,
  },
  indicators: {
    enj01: { availability: 'unknown', value: null, status: 'unknown' },
    enj02: { availability: 'unknown', value: null, status: 'unknown' },
  },
  coverage: { routes: 'unknown', corridors: 'unknown', completeness: 'unknown' },
  science: {
    priority: 'not_calculated',
    actions: 'not_calculated',
    validation: 'pending',
    limitations: [],
  },
}
assert.equal(
  parseM2CellSummary(m2Fixture, baseRecord.maille_id, PRIORITY_GRID_VERSION).gridVersion,
  PRIORITY_GRID_VERSION,
)
assert.throws(
  () => parseM2CellSummary(m2Fixture, baseRecord.maille_id, 'INCOMPATIBLE'),
  M2UnavailableError,
)

assert.deepEqual(
  Object.fromEntries(Object.entries(ECOLOGICAL_PRIORITY).map(([key, value]) => [key, value.color])),
  {
    HIGH: '#D9534F',
    MODERATE: '#F29A48',
    LOW: '#E6C65B',
    INDETERMINATE: '#89938F',
  },
)

const publicFiles = await readdir(publicDataPath, { recursive: true })
assert.ok(publicFiles.every((file) => !file.toLowerCase().endsWith('.gpkg')))
for (const file of publicFiles.filter((entry) => entry.endsWith('.json') || entry.endsWith('.geojson'))) {
  const content = await readFile(new URL(file, publicDataPath), 'utf8')
  assert.ok(!content.includes('branche_mailles.gpkg'), `Référence M2 interne publiée dans ${file}`)
  assert.ok(!content.includes('liens_mailles_conflits'), `Schéma M2 interne publié dans ${file}`)
}

console.log('PASS: modes TEST/REAL séparés, géométrie 43 mailles stable, versions M1/M2 sécurisées, aucun GeoPackage M2 public')
