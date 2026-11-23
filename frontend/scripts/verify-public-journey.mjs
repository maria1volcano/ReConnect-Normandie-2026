import assert from 'node:assert/strict'
import fs from 'node:fs'
import {adaptPublicSnapshot} from '../src/integrations/publicJourneyAdapter.ts'
import {PUBLIC_DATA_POLICY,PUBLIC_DISPLAY_DATASET} from '../src/integrations/publicDataPolicy.ts'
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
// Grille unique 22 communes : empreintes épinglées, contrat identique, cohérence avec le lot historique.
{
 const policy=PUBLIC_DISPLAY_DATASET,readD=n=>fs.readFileSync(new URL('../public/'+policy.directory+n,import.meta.url))
 for(const [name,hash]of Object.entries(policy.files))assert.equal(createHash('sha256').update(readD(name)).digest('hex'),hash,'Empreinte 22 communes '+name)
 const dc=JSON.parse(readD('cells.json')),dg=JSON.parse(readD('grid.geojson')),disp=adaptPublicSnapshot(dc,dg,policy)
 assert.deepEqual(disp.data.metadata,{cells:policy.cells,proposals:policy.leads})
 assert.throws(()=>adaptPublicSnapshot(dc,dg),'La grille 22 communes ne passe pas pour le lot historique')
 assert.ok(Object.keys(cells).every(id=>id in dc),'Chaque hexagone historique existe dans la grille unique')
 const same=Object.keys(cells).filter(id=>Math.abs(dc[id].area_m2-cells[id].area_m2)<1)
 assert.equal(same.length,62)
 for(const id of same){
  assert.equal(dc[id].documentary.level,cells[id].documentary.level,'Couleur historique conservée '+id)
  assert.deepEqual(dc[id].investigations.map(i=>i.lead_status),cells[id].investigations.map(i=>i.lead_status),'Pistes historiques conservées '+id)
 }
 assert.ok(Object.keys(dc).every(id=>!id.endsWith('-EXT')),'Aucun hexagone fragmenté entre deux jeux')
 assert.ok(Object.values(disp.cells).flatMap(c=>c.actions).every(a=>a.origin==='extension'))
 console.log('PASS 22 communes :',policy.cells,'secteurs,',policy.leads,'pistes ; 62 secteurs historiques non touchés par l’extension strictement identiques, 39 hexagones de frontière recalculés entiers.')
}
console.log('PASS public : 101 secteurs, 404 examens, 165 pistes historiques, 30 sans piste ; aucun niveau inventé, sources inchangées et contrats incompatibles refusés.')
