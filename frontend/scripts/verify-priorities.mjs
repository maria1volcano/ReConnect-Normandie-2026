import assert from 'node:assert/strict'
import { readdir, readFile } from 'node:fs/promises'
import {
  ECOLOGICAL_PRIORITY,
  PRIORITY_GRID_VERSION,
  applyEcologicalPriorities,
  resolveEcologicalPriority,
} from '../src/integrations/priorityAdapter.ts'

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

console.log('PASS: 43 mailles grises, validation/version sécurisées, palette V6.1, aucun GeoPackage M2 public')
