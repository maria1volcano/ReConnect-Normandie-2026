import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { validateInstruction, ACTIONS_VERSION } from '../src/integrations/m4Adapter.ts'
const clone = (v) => structuredClone(v)
const option = { action_id: 'A04', regle_id: 'R1', statut_instruction: 'a_instruire_indicatif',
  statut_scientifique: 'non_evaluable', justification: 'Croisements documentés', conditions_manquantes: ['Qualification écologique et technique'],
  travaux_valides: false, activation_regle_scientifique: false }
for (const [couleur, niveau] of [['rouge', 1], ['orange', 2], ['jaune', 3], ['gris', null]]) {
  const fixture = { validated_recommendations: [], ecological_priority: {category: 'INDETERMINATE', method_version: null},
    study_priority: {version: ACTIONS_VERSION, couleur, niveau, couleur_hex: '#9098A4', validation_ecologique: false},
    instruction: {version: ACTIONS_VERSION, diagnostic: 'Diagnostic local', main_action: niveau === 1 || niveau === 2 ? option : null,
      complementary_actions: [], options: [option], conditions_before_works: ['Validation']} }
  assert.doesNotThrow(() => validateInstruction(fixture))
  for (const mutate of [
    (c) => { c.instruction.version = 'ancienne' },
    (c) => { c.instruction.options[0].justification = '' },
    (c) => { c.instruction.options[0].travaux_valides = true },
    (c) => { c.ecological_priority.category = 'HIGH' },
    (c) => { c.study_priority.validation_ecologique = true },
    (c) => { c.study_priority.niveau = 9 },
    (c) => { c.study_priority.couleur_hex = 'red' },
  ]) { const bad = clone(fixture); mutate(bad); assert.throws(() => validateInstruction(bad)) }
  if (couleur === 'gris' || couleur === 'jaune') {
    const bad = clone(fixture); bad.instruction.main_action = option; assert.throws(() => validateInstruction(bad))
  }
}
const oldCells = JSON.parse(await readFile(new URL('../public/data/caen-6com/cells.json', import.meta.url), 'utf8'))
assert.equal(Object.keys(oldCells).length, 101)
for (const cell of Object.values(oldCells)) {
  assert.doesNotThrow(() => validateInstruction(cell))
  assert.equal(cell.instruction, undefined, 'Aucune décision ne doit être inventée dans la livraison publique antérieure')
}
if (process.env.M2_ACTIONS_CANDIDATE_ROOT) {
  const base = process.env.M2_ACTIONS_CANDIDATE_ROOT
  const cells = JSON.parse(await readFile(`${base}/cells.json`, 'utf8'))
  const grid = JSON.parse(await readFile(`${base}/grid.geojson`, 'utf8'))
  assert.equal(Object.keys(cells).length, 101)
  const colors = {}, seen = new Set(); let selected = 0, pistes = 0, exclusive = 0
  for (const feature of grid.features) {
    const id = feature.properties.maille_id, cell = cells[id]
    assert.ok(!seen.has(id)); seen.add(id)
    assert.ok(cell)
    assert.equal(cell.grid_version, feature.properties.grid_version)
    assert.equal(cell.territory_id, feature.properties.territory_id)
    validateInstruction(cell)
    assert.deepEqual(cell.study_priority, feature.properties.study_priority)
    colors[cell.study_priority.couleur] = (colors[cell.study_priority.couleur] ?? 0) + 1
    if (cell.instruction.main_action) { selected++; assert.equal(cell.instruction.main_action.action_id, 'A04') }
    pistes += cell.instruction.historical_lead_ids.length
    exclusive += cell.geometric_observations.canonical_event_count
  }
  assert.deepEqual(colors, {gris: 32, jaune: 9, rouge: 27, orange: 33})
  assert.equal(selected, 60); assert.equal(pistes, 165); assert.equal(exclusive, 5336)
}
console.log('PASS: décisions d’étude séparées de D/S, actions justifiées, refus de travaux artificiels, ancien export sans décisions inventées')
