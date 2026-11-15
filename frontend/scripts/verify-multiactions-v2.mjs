import assert from 'node:assert/strict'
import {validateV2Cell, V2_SCOPE, V2_MANIFEST, isV2Enabled} from '../src/integrations/multiActionsV2Adapter.ts'
assert.equal(isV2Enabled(), false, 'No V2 activation outside the Vite development runtime')
const action = {action_id:'A01', rule_id:'R2', name:'Étudier les haies', level:'C', level_status:'piste_exploratoire',
  solution:'Étudier la préservation', question:'Quel rôle local ?', deliverable:'Diagnostic', reason:'Haie observée', rank:1,
  observations:['Présence réelle, lien incertain'], uncertainties:['Fonctionnalité inconnue'], checks_before_works:['Validation humaine'],
  next_steps:['Vérifier sur place'], works_validated:false, works_need_demonstrated:false, presence_only:true,
  scientific_status:'non_evaluable', scientific_decision_rule:'A2', precision_qualified:false}
const fixture = {...V2_SCOPE, mode:'local_experimental', test_data:false, publication_authorized:false,
  territorial_priority:{version:'caen6-priorites-etude-actions-20261112-1',presentation_version:'caen6-examen-multiactions-presentation-20261115-1',color:'gris',color_hex:'#9098A4',rank:null,status:'non_evaluable',scope:'interfaces_routieres_et_continuites',global_ecological_priority:false,works_urgency:null},
  maille_id:'SYNTHETIQUE', manifest_sha256:V2_MANIFEST, main_action:null, validated_recommendations:[], actions:[action],
  not_selected:['A02','A03','A04'].map(action_id=>({action_id,reason:'Données insuffisantes',scientific_status:'non_evaluable'})), comparisons:[],
  DS:{priorite_ecologique:{conclusion:'indeterminee'}, method_version:null,priorite_examen:{etat:'non_calculee',valeur:null}}}
assert.doesNotThrow(()=>validateV2Cell(fixture,'SYNTHETIQUE'))
for (const mutate of [c=>{c.actions[0].works_validated=true},c=>{c.actions[0].scientific_status='etayee_pour_examen'},
  c=>{c.actions[0].presence_only=false},c=>{c.actions[0].observations=[]},c=>{c.actions[0].rank=2},c=>{c.main_action=action},
  c=>{c.dataset_version='wrong'},c=>{c.decision_version='wrong'},c=>{c.publication_authorized=true},c=>{c.test_data=true},
  c=>{c.territorial_priority.color='vert'},c=>{c.territorial_priority.global_ecological_priority=true},c=>{c.territorial_priority.works_urgency='urgent'},
  c=>{c.territorial_priority.rank=1},c=>{c.DS.priorite_ecologique.conclusion='validee'},c=>{c.not_selected=[]}]) {
  const bad=structuredClone(fixture);mutate(bad);assert.throws(()=>validateV2Cell(bad,'SYNTHETIQUE'))
}
if (process.env.RECONNECT_V2_API_URL) {
  const base=new URL(process.env.RECONNECT_V2_API_URL)
  assert.ok(['127.0.0.1','localhost'].includes(base.hostname))
  const query=new URLSearchParams(V2_SCOPE).toString()
  const get=async path=>{const r=await fetch(`${base.origin}/api/internal/caen/multiactions-v2/${path}?${query}`);assert.equal(r.status,200);return r.json()}
  const grid=await get('grid');const meta=await get('metadata');assert.equal(grid.features.length,101)
  let total=0,withProposals=0,multiple=0,none=0;const levels={A:0,B:0,C:0}
  for(let i=0;i<grid.features.length;i+=4) for(const cell of await Promise.all(grid.features.slice(i,i+4).map(f=>get('cells/'+encodeURIComponent(f.properties.maille_id))))) {
    validateV2Cell(cell,cell.maille_id);total+=cell.actions.length
    withProposals+=!!cell.actions.length;multiple+=cell.actions.length>1;none+=!cell.actions.length
    for(const a of cell.actions)levels[a.level]++
  }
  assert.deepEqual([total,withProposals,multiple,none],[205,88,61,13]);assert.deepEqual(levels,{A:93,B:45,C:67})
  assert.equal(meta.c_only_cells,25)
}
console.log('PASS V2 : niveaux, justification, versions et verrous ; tests antérieurs conservés.')
