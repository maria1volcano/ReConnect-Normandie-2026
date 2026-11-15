import assert from 'node:assert/strict'
import {territorialSummary,PRIORITY_LABELS} from '../src/integrations/territorialPresentation.ts'
import {presentAction,localIndicators,readableNonSelection} from '../src/integrations/actionPresentation.ts'
import {validateV2Cell,V2_SCOPE} from '../src/integrations/multiActionsV2Adapter.ts'

const jargon=/\b(?:XY|D\/S|R[1-4]|A0[1-4]|SRCE|V[1-4])\b|référence\(s\)|objet\(s\)/u
const fake=(id,level,relation)=>({action_id:id,level,spatial_relations:relation?[relation]:[],source_context:{},observations:[]})
for(const id of ['A01','A02','A03','A04'])for(const level of ['A','B','C']){
 const p=presentAction(fake(id,level))
 assert.ok(p.why.length>=2&&p.why.length<=3);assert.ok(p.intervention.length>=1&&p.intervention.length<=2)
 assert.equal(p.checks.length,3);assert.ok(!jargon.test([...p.why,...p.intervention,...p.interpretation,...p.checks].join(' ')))
}
const measured={...fake('A01','B','Haie recoupant SRCE'),observations:['Haie recoupant SRCE : 6 référence(s) locale(s).','Haies : 3 objet(s) référencé(s) dans cette question.','Présence non chiffrée'],source_context:{precision_haie_m:[3],precision_srce:[null]}}
assert.deepEqual(localIndicators(measured).map(v=>v.value),[6,3])
assert.match(presentAction(measured).interpretation.join(' '),/3 m/)
assert.match(presentAction({...fake('A02','C'),source_context:{typo:['Remblais']}}).why.join(' '),/remblai/)
assert.ok(!jargon.test(readableNonSelection('Aucun plan d’eau/objet ZH ni relation humide documenté permettant cette piste ; absence écologique non démontrée')))
const wetland=presentAction(fake('A02','B','Inventaire humide recouvrant un réservoir humide'))
assert.match(wetland.why[0],/réservoirs de biodiversité/)
assert.doesNotMatch(wetland.why[0],/plans d’eau/,'Ne pas suggérer une autre relation que celle du lot')
const basin=presentAction({...fake('A02','A'),spatial_relations:['Plan d’eau recouvrant SRCE','Plan d’eau recouvrant un inventaire humide'],source_context:{nature:['Réservoir-bassin']}})
assert.match(basin.why[0],/régional et un inventaire/)
assert.match(basin.interpretation.join(' '),/Réservoir-bassin/)
assert.match(wetland.interpretation.join(' '),/recouvrement très faible/)
const brownfield=presentAction({...fake('A03','A','Site Cartofriches recouvrant SRCE'),source_context:{statut_source:['friche avec projet'],date_actualisation:[],site_actu_date:[null],precision_srce:[null]}})
assert.match(brownfield.interpretation.join(' '),/friche avec projet/)
assert.match(brownfield.interpretation.join(' '),/date d’actualisation n’est pas renseignée/)
assert.match(brownfield.interpretation.join(' '),/précision du tracé régional n’est pas renseignée/)

if(process.env.RECONNECT_V2_API_URL){
 const base=new URL(process.env.RECONNECT_V2_API_URL);assert.ok(['localhost','127.0.0.1'].includes(base.hostname))
 const query=new URLSearchParams(V2_SCOPE).toString()
 const get=async route=>{const r=await fetch(`${base.origin}/api/internal/caen/multiactions-v2/${route}?${query}`);assert.equal(r.status,200);return r.json()}
 const grid=await get('grid');assert.equal(grid.features.length,101)
 const families={A01:{A:0,B:0,C:0},A02:{A:0,B:0,C:0},A03:{A:0,B:0,C:0},A04:{A:0,B:0,C:0}};
 const metrics={cells:0,actions:0,withActions:0,multiple:0,empty:0,A:0,B:0,C:0};let maxWords=0
 for(let i=0;i<101;i+=4)for(const cell of await Promise.all(grid.features.slice(i,i+4).map(f=>get('cells/'+encodeURIComponent(f.properties.maille_id))))){
  validateV2Cell(cell,cell.maille_id);const before=JSON.stringify(cell);const summary=territorialSummary(cell);assert.ok(summary.length>120&&!jargon.test(summary));if(['rouge','orange'].includes(cell.territorial_priority.color))assert.ok(summary.includes(cell.territorial_priority.evidence.nombre_paires_route_corridor_2d.toLocaleString('fr-FR')))
  metrics.cells++;metrics.withActions+=!!cell.actions.length;metrics.multiple+=cell.actions.length>1;metrics.empty+=!cell.actions.length
  for(const a of cell.actions){
   const p=presentAction(a);metrics.actions++;metrics[a.level]++;families[a.action_id][a.level]++
   assert.ok(p.why.length>=2&&p.why.length<=3);assert.ok(p.intervention.length>=1&&p.intervention.length<=2)
   assert.equal(p.checks.length,3);assert.ok(p.indicators.length>0,'Indicateurs précis conservés pour chaque piste')
   assert.ok(p.interpretation.length>0);assert.ok(p.highlights.length>0&&p.highlights.length<=2);assert.ok(p.keyLimit.length>30&&p.keyLimit.split(/\s+/).length<=35)
   assert.ok(!jargon.test([...p.why,...p.intervention,...p.interpretation,...p.checks,...p.indicators.map(i=>i.label)].join(' ')))
   const words=[...p.why,...p.intervention].join(' ').split(/\s+/).length;maxWords=Math.max(maxWords,words)
   assert.ok(words>=35&&words<=160,'Fiche explicative, sans liste principale interminable')
   assert.equal(a.works_validated,false);assert.equal(a.scientific_status,'non_evaluable')
   if(a.action_id==='A02'&&a.level==='B')assert.match(p.why[0],/réservoirs de biodiversité/)
   if(a.action_id==='A02'&&a.level==='A')assert.match(p.why[0],/régional et un inventaire/)
   if(a.action_id==='A03'&&a.source_context.statut_source?.includes('friche avec projet'))assert.match(p.interpretation.join(' '),/friche avec projet/)
  }
  for(const a of cell.not_selected)assert.ok(!jargon.test(readableNonSelection(a.reason)))
  assert.equal(JSON.stringify(cell),before,'La projection éditoriale ne modifie pas les données reçues')
 }
 assert.deepEqual(metrics,{cells:101,actions:205,withActions:88,multiple:61,empty:13,A:93,B:45,C:67})
 assert.deepEqual(families,{A01:{A:18,B:27,C:17},A02:{A:4,B:15,C:23},A03:{A:14,B:0,C:21},A04:{A:57,B:3,C:6}});assert.equal(PRIORITY_LABELS.rouge,'Secteur à examiner en priorité');
 console.log('PASS : 101 fiches, 205 présentations sans mutation, 13 états sans proposition ;',maxWords,'mots au maximum par lecture principale.')
}
console.log('PASS : explications en 2–3 phrases, solutions concrètes, trois vérifications spécifiques et indicateurs sans notations internes.')
