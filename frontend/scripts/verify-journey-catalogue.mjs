import assert from 'node:assert/strict'
import fs from 'node:fs'
import {adaptPublicSnapshot} from '../src/integrations/publicJourneyAdapter.ts'
import {buildJourneyCatalogue,loadJourneyCatalogue,CATALOGUE_FAMILIES,EMPTY_CATALOGUE_FILTERS,filterCatalogueEntries,catalogueSectorIds,readCatalogueFilters,catalogueHref} from '../src/integrations/journeyCatalogue.ts'
const read=n=>JSON.parse(fs.readFileSync(new URL('../public/data/caen-6com/'+n,import.meta.url)))
const raw=read('cells.json'),grid=read('grid.geojson'),adapted=adaptPublicSnapshot(raw,grid),cells=Object.values(adapted.cells),before=JSON.stringify({raw,grid,cells})
const catalogue=buildJourneyCatalogue(adapted.data,cells,'historical_public')
assert.equal(CATALOGUE_FAMILIES.length,4)
assert.deepEqual(Object.fromEntries(catalogue.families.map(f=>[f.id,f.entries.length])),{A04:60,A01:50,A03:35,A02:20})
assert.equal(catalogueSectorIds(catalogue,EMPTY_CATALOGUE_FILTERS).size,71)
const communes=['all',...new Set(cells.flatMap(c=>c.municipalities))]
let combinations=0
for(const family of CATALOGUE_FAMILIES)for(const commune of communes)for(const priority of ['all','rouge','orange','jaune','gris']){
 const filters={...EMPTY_CATALOGUE_FILTERS,family:family.id,commune,priority}
 const expected=Object.values(raw).filter(c=>c.investigations.some(a=>a.action_id===family.id&&a.lead_status==='a_etudier')&&(commune==='all'||c.municipalities.some(m=>m.nom===commune))&&(priority==='all'||c.documentary.level===priority)).map(c=>c.maille_id).sort()
 const actual=filterCatalogueEntries(catalogue,family.id,filters)
 assert.deepEqual(actual.map(e=>e.cell.maille_id).sort(),expected)
 assert.deepEqual([...catalogueSectorIds(catalogue,filters)].sort(),expected)
 assert.ok(actual.every(e=>!('level'in e.action)))
 assert.deepEqual(readCatalogueFilters(new URL(catalogueHref('/',filters,expected[0]),'https://example.test').search),filters)
 combinations++
}
const query={...EMPTY_CATALOGUE_FILTERS,query:'herouville'}
assert.ok([...catalogueSectorIds(catalogue,query)].every(id=>adapted.cells[id].municipalities.includes('Hérouville-Saint-Clair')))
assert.equal(catalogueSectorIds(catalogue,{...query,query:'introuvable'}).size,0)
assert.equal(readCatalogueFilters('?famille=R1').family,'A04');assert.equal(readCatalogueFilters('?famille=inconnu&priorite=vert').family,'all');assert.equal(readCatalogueFilters('?priorite=vert').priority,'all');assert.equal(readCatalogueFilters('?priorite=constructor').priority,'all')
assert.equal(JSON.stringify({raw,grid,cells}),before,'Aucun résultat scientifique ni donnée modifié')
const changed=structuredClone(cells);changed.find(c=>c.actions.length).actions[0].level='A';assert.throws(()=>buildJourneyCatalogue(adapted.data,changed,'historical_public'))
assert.throws(()=>buildJourneyCatalogue(adapted.data,cells.slice(1),'historical_public'))
assert.throws(()=>buildJourneyCatalogue(adapted.data,cells,'local_experimental'))
let loads=0,cellLoads=0,active=0,max=0
const source={kind:'historical_public',load:async()=>{loads++;return adapted.data},loadCell:async id=>{cellLoads++;active++;max=Math.max(max,active);await new Promise(resolve=>setTimeout(resolve,1));active--;return adapted.cells[id]}}
const [a,b]=await Promise.all([loadJourneyCatalogue(source),loadJourneyCatalogue(source)])
assert.equal(a,b);assert.equal(loads,1);assert.equal(cellLoads,101);assert.ok(max<=4)
const controller=new AbortController();controller.abort();await assert.rejects(loadJourneyCatalogue(source,controller.signal))
let failed=true
const retrySource={...source,load:async()=>{if(failed){failed=false;throw Error('Indisponible')}return adapted.data}}
await assert.rejects(loadJourneyCatalogue(retrySource));assert.equal((await loadJourneyCatalogue(retrySource)).data.metadata.proposals,165)
if(process.env.RECONNECT_V2_API_URL){
 const base=new URL(process.env.RECONNECT_V2_API_URL);assert.ok(['127.0.0.1','localhost'].includes(base.hostname))
 const {V2_SCOPE}=await import('../src/integrations/multiActionsV2Adapter.ts')
 const scope=new URLSearchParams(V2_SCOPE),get=async route=>{const res=await fetch(base.origin+'/api/internal/caen/multiactions-v2/'+route+'?'+scope);assert.equal(res.status,200);return res.json()}
 const vgrid=await get('grid'),metadata=await get('metadata'),vcells=[]
 for(let i=0;i<101;i+=4)for(const cell of await Promise.all(vgrid.features.slice(i,i+4).map(f=>get('cells/'+encodeURIComponent(f.properties.maille_id)))))vcells.push({...cell,actions:cell.actions.map(a=>({...a,source:'local_experimental'}))})
 const cat=buildJourneyCatalogue({grid:vgrid,metadata},vcells,'local_experimental')
 assert.deepEqual(Object.fromEntries(cat.families.map(f=>[f.id,f.entries.length])),{A04:66,A01:62,A03:35,A02:42})
 assert.equal(catalogueSectorIds(cat,EMPTY_CATALOGUE_FILTERS).size,88)
 assert.deepEqual(cat.families.flatMap(f=>f.entries).reduce((n,e)=>(n[e.action.level]++,n),{A:0,B:0,C:0}),{A:93,B:45,C:67})
}
console.log('PASS catalogue : 4 familles, 165 pistes historiques, '+combinations+' combinaisons de filtres, liens exacts, cache isolé et niveaux conservés ; V2 réelle vérifiée si configurée.')
