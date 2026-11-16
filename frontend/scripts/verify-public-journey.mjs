import assert from 'node:assert/strict'
import fs from 'node:fs'
import {adaptPublicSnapshot} from '../src/integrations/publicJourneyAdapter.ts'
import {PUBLIC_DATA_POLICY} from '../src/integrations/publicDataPolicy.ts'
import {createHash} from 'node:crypto'
const read=n=>fs.readFileSync(new URL('../public/data/caen-6com/'+n,import.meta.url))
for(const [name,hash]of Object.entries(PUBLIC_DATA_POLICY.files))assert.equal(createHash('sha256').update(read(name)).digest('hex'),hash)
const cells=JSON.parse(read('cells.json')),grid=JSON.parse(read('grid.geojson')),before=JSON.stringify({cells,grid})
const adapted=adaptPublicSnapshot(cells,grid),all=Object.values(adapted.cells)
assert.deepEqual(adapted.data.metadata,{cells:101,proposals:165})
assert.equal(all.filter(c=>!c.actions.length).length,30)
assert.equal(all.flatMap(c=>c.actions).length,165)
assert.ok(all.flatMap(c=>c.actions).every(a=>a.source==='historical_public'&&!('level'in a)&&a.copy.why.length>=2&&a.copy.why.length<=3&&a.copy.intervention.length>=1&&a.copy.checks.length===3))
for(const c of all)assert.deepEqual(c.actions.map(a=>a.action_id),cells[c.maille_id].investigations.filter(a=>a.lead_status==='a_etudier').map(a=>a.action_id))
assert.equal(JSON.stringify({cells,grid}),before,'Les données et statuts scientifiques restent strictement inchangés')
for(const mutate of [
 c=>{delete c[Object.keys(c)[0]]}, c=>{Object.values(c)[0].mode='local_experimental'},
 c=>{Object.values(c)[0].actions=[]},c=>{Object.values(c)[0].documentary.level='vert'},
 c=>{Object.values(c)[0].validated_recommendations=[{}]},c=>{Object.values(c)[0].investigations[0].works_recommended=true},
 c=>{Object.values(c)[0].dataset_version='autre'},c=>{Object.values(c)[0].ecological_priority.category='HIGH'},
 c=>{Object.values(c)[0].investigations[0].lead_status='a_etudier'},
]){
 const changed=structuredClone(cells);mutate(changed);assert.throws(()=>adaptPublicSnapshot(changed,grid))
}
const badGrid=structuredClone(grid);badGrid.features[0].properties.documentary_level='rouge';assert.throws(()=>adaptPublicSnapshot(cells,badGrid))
console.log('PASS public : 101 secteurs, 404 examens, 165 pistes historiques, 30 sans piste ; aucun niveau inventé, sources inchangées et contrats incompatibles refusés.')
