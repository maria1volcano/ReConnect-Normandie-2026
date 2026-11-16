import type { FeatureCollection, Geometry } from 'geojson'
import type { RealGridFeatureProperties } from './priorityAdapter'
import type { M4CellBundle, M4Investigation } from './m4Adapter'
import { TERRITORIAL_PALETTE, type JourneyAction, type JourneyCell, type JourneyData, type JourneyPriority, type JourneySource } from './journeyModel.ts'
import { PUBLIC_DATA_POLICY as policy } from './publicDataPolicy.ts'

const FAMILIES = {
  A01: { keys:['haies','corridors'], why:'Les haies peuvent contribuer aux déplacements des espèces entre habitats ; leur présence cartographiée ne décrit pas leur continuité réelle.', solution:'Une étude de l’état des haies et de leurs connexions pourrait préciser les besoins de gestion ou les possibilités de restauration.', limit:'La présence d’une haie ne démontre ni une lacune du réseau ni un besoin de plantation.' },
  A02: { keys:['plans_eau','zones_humides'], why:'Les milieux aquatiques peuvent participer aux continuités humides ; leur rôle dépend de leur nature, de leur alimentation en eau et des espèces présentes.', solution:'Un inventaire ciblé et une étude du fonctionnement hydrologique pourraient préciser les possibilités de préservation ou de restauration.', limit:'Ces observations ne démontrent ni un déficit de mares ni la nécessité de créer un plan d’eau.' },
  A03: { keys:['friches','corridors'], why:'Certains sites peuvent contribuer aux continuités écologiques, mais les habitats déjà présents et les usages doivent être examinés avant d’envisager leur évolution.', solution:'Une étude du site, de ses habitats et de ses usages pourrait examiner l’intérêt et la faisabilité d’une renaturation.', limit:'Un site recensé dans Cartofriches n’est pas nécessairement disponible ni écologiquement dégradé.' },
  A04: { keys:['routes','corridors'], why:'Une route peut affecter les déplacements des espèces ; une intersection sur la carte ne démontre toutefois pas un obstacle réel.', solution:'Une étude des ouvrages existants et des déplacements de la faune pourrait examiner les possibilités d’amélioration de leur perméabilité.', limit:'Les relations géométriques ne correspondent pas à des obstacles confirmés ni à des emplacements validés de travaux.' },
} as const
const NAMES: Record<string,string> = {haies:'Haies recensées dans le secteur',corridors:'Espaces régionaux de continuité',plans_eau:'Plans d’eau recensés',zones_humides:'Éléments d’inventaire humide',friches:'Sites Cartofriches, tous statuts',routes:'Tronçons routiers recensés'}
const RANK = {rouge:1,orange:2,jaune:3,gris:null} as const

function publicPriority(cell:M4CellBundle):JourneyPriority {
  const color=cell.documentary.level, e=cell.documentary.observations
  if (!(color in TERRITORIAL_PALETTE)
      || !['nombre_paires_route_corridor_2d','paires_route_matrice_fragile_en_service_au_sol'].every(k=>Number.isInteger(e[k]) && Number(e[k])>=0)
      || typeof e.reservoir_presence_surface_positive!=='boolean' || typeof e.corridor_presence_surface_positive!=='boolean') throw new Error('Observations historiques incompatibles')
  // Rename the received documentary category for display, never recalculate it.
  return {color,color_hex:TERRITORIAL_PALETTE[color],rank:RANK[color],evidence:{
    nombre_paires_route_corridor_2d:Number(e.nombre_paires_route_corridor_2d),
    paires_route_matrice_fragile_en_service_au_sol:Number(e.paires_route_matrice_fragile_en_service_au_sol),
    reservoir_presence_surface_positive:e.reservoir_presence_surface_positive,
    corridor_presence_surface_positive:e.corridor_presence_surface_positive}}
}
function actionPresentation(a:M4Investigation,cell:M4CellBundle):JourneyAction {
  const family=FAMILIES[a.action_id as keyof typeof FAMILIES]
  if(!family)throw new Error('Famille historique inconnue')
  const indicators=family.keys.flatMap(key=>{
    const value=cell.geometric_observations.source_observations[key]?.nombre_objets_observes
    return typeof value==='number' ? [{label:NAMES[key],value}] : []
  })
  const evidence=a.evidence.replace('paires linéaires documentaires liées aux événements M2 admis','relations cartographiques entre voies et espaces de continuité').replace('avec matrice ou réservoir dans la maille','dans un secteur comprenant des espaces régionaux de continuité ou des réservoirs de biodiversité')
  return {source:'historical_public',action_id:a.action_id,name:a.title,copy:{
    why:['Les données historiques recensent '+evidence.replace(/\.$/,'')+'.',family.why],intervention:[family.solution],
    indicators,highlights:indicators.slice(0,2),keyLimit:family.limit,
    interpretation:['Cette piste figure dans les données historiques autorisées. Les observations locales ne qualifient pas son efficacité écologique et ne fournissent aucun niveau de justification A/B/C.'],
    checks:[...a.missing_conditions],
  }}
}

/** Pure contract adapter. Does not create V2 actions or change scientific statuses. */
export function adaptPublicSnapshot(cells:Record<string,M4CellBundle>,grid:FeatureCollection<Geometry,RealGridFeatureProperties>):{data:JourneyData;cells:Record<string,JourneyCell>;raw:Record<string,M4CellBundle>} {
  const ids=Object.keys(cells).sort(), mapped:Record<string,JourneyCell>={}
  if(ids.length!==policy.cells || grid.type!=='FeatureCollection' || grid.features.length!==policy.cells || new Set(grid.features.map(f=>f.properties.maille_id)).size!==policy.cells)throw new Error('Périmètre public incomplet')
  let exams=0,leads=0
  for(const [index,id] of ids.entries()) {
    const c=cells[id]
    if(c.territory_id!==policy.territory || c.grid_version!==policy.grid || c.dataset_version!==policy.dataset || c.maille_id!==id
      || 'actions' in c || 'mode' in c || 'decision_version' in c || 'instruction' in c || 'study_priority' in c
      || c.validated_recommendations.length || c.ecological_priority.category!=='INDETERMINATE'
      || c.ecological_priority.scientific_validation!=='PENDING' || c.ecological_priority.method_version!==null
      || c.investigations.length!==4 || new Set(c.investigations.map(a=>a.action_id)).size!==4
      || c.investigations.some(a=>!(a.action_id in FAMILIES)||a.status!=='non_evaluable'||a.works_recommended!==false||!['a_etudier','non_qualifiable'].includes(a.lead_status)))throw new Error('Contrat historique public incompatible')
    const municipalities=c.municipalities.map(m=>m.nom),number=index+1
    const actions=c.investigations.filter(a=>a.lead_status==='a_etudier').map(a=>actionPresentation(a,c))
    exams+=c.investigations.length;leads+=actions.length
    mapped[id]={maille_id:id,sector:{number,municipalities,label:`${municipalities.join(' / ')} — secteur ${number}`},municipalities,territorial_priority:publicPriority(c),actions,
      not_selected:c.investigations.filter(a=>a.lead_status!=='a_etudier').map(a=>({action_id:a.action_id,explanation:'Les observations historiques disponibles ne permettent pas de qualifier une piste pour cette famille. Cela ne démontre pas une absence d’enjeu écologique.'})),
      // The historical contract does not qualify links between family observations.
      linkedObservations:false,observations:c.geometric_observations.source_observations,
      local_event_count:c.geometric_observations.local_event_count,canonical_event_count:c.geometric_observations.canonical_event_count}
  }
  if(exams!==policy.investigations || leads!==policy.leads)throw new Error('Lot historique inattendu')
  const features=grid.features.map(f=>{
    const p=f.properties,cell=mapped[p.maille_id]
    if(!cell || p.territory_id!==policy.territory || p.grid_version!==policy.grid || p.documentary_level!==cell.territorial_priority.color)throw new Error('Grille historique incompatible')
    return {...f,properties:{...p,sector:cell.sector,territorial_priority:cell.territorial_priority,study_color:cell.territorial_priority.color_hex}}
  })
  return {data:{grid:{...grid,features},metadata:{cells:ids.length,proposals:leads}},cells:mapped,raw:cells}
}

async function authorizedJson(file:keyof typeof policy.files):Promise<unknown> {
  const url=new URL(`${import.meta.env.BASE_URL}${policy.directory}${file}`,window.location.href)
  if(url.origin!==window.location.origin)throw new Error('Ressource publique hors origine')
  const response=await fetch(url,{cache:'no-cache',signal:AbortSignal.timeout(20_000)})
  if(!response.ok)throw new Error('Données historiques indisponibles')
  const bytes=await response.arrayBuffer()
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),n=>n.toString(16).padStart(2,'0')).join('')
  if(digest!==policy.files[file])throw new Error('Ressource absente de la sélection publique autorisée')
  return JSON.parse(new TextDecoder().decode(bytes))
}
let snapshot:Promise<ReturnType<typeof adaptPublicSnapshot>>|null=null
async function loadSnapshot(signal?:AbortSignal) {
  // Shared immutable cache: cancelling one subscriber never aborts another one.
  signal?.throwIfAborted()
  snapshot??=Promise.all([authorizedJson('cells.json'),authorizedJson('grid.geojson')]).then(([cells,grid])=>adaptPublicSnapshot(cells as Record<string,M4CellBundle>,grid as JourneyData['grid'])).catch(error=>{snapshot=null;throw error})
  const result=await snapshot;signal?.throwIfAborted();return result
}
export const publicJourneySource:JourneySource={
  kind:'historical_public',
  notice:'Version publique : 165 pistes historiques autorisées sur 101 secteurs. Leurs niveaux de justification ne sont pas qualifiés. Les propositions expérimentales restent réservées à la revue locale.',
  footer:'Données historiques autorisées · aucune proposition expérimentale publiée.',
  load:async signal=>(await loadSnapshot(signal)).data,
  loadCell:async(id,signal)=>{
    const cell=(await loadSnapshot(signal)).cells[id]
    if(!cell)throw new Error('Secteur public introuvable')
    return cell
  },
  loadExample:async signal=>{
    const {cells,raw}=await loadSnapshot(signal),id='NORM-G1K-FLAT-R+006422-C+000487',cell=cells[id]
    // The numeric example comes from the same verified historical snapshot.
    return {maille_id:id,sector:cell.sector,area_m2:raw[id].area_m2,priority:cell.territorial_priority,
      hedge_length_m:cell.observations.haies?.mesure_observee??null,wetland_area_m2:cell.observations.zones_humides?.mesure_observee??null,
      actions:cell.actions.map(a=>({action_id:a.action_id,justification:'piste historique, justification non qualifiée'}))}
  },
  method:{levels:false,
    intro:'La version publique reprend les pistes déjà signalées dans le lot historique autorisé. Les 404 examens familiaux distinguent les pistes à étudier des situations non qualifiables. Le frontend présente ces résultats existants ; il ne recalcule pas leur sélection et n’attribue aucun niveau de justification.',
    families:[
      ['Haies','Une piste historique peut signaler des haies observées dans un secteur où figurent des espaces régionaux. Cette co-présence ne démontre pas une connexion fonctionnelle.','Vérifier la continuité réelle, les habitats et les pratiques de gestion.'],
      ['Milieux humides','Les pistes historiques portent sur la qualification des plans d’eau et du réseau humide recensés. Elles ne démontrent pas un manque de mares.','Identifier le milieu et son alimentation en eau.'],
      ['Friches','Les pistes historiques invitent à examiner le statut des sites et leur relation aux continuités. Le fichier source distingue les sites reconvertis.','Actualiser le statut, relever les habitats existants et examiner les sols et projets.'],
      ['Franchissements pour la faune','Les relations cartographiques entre voies et espaces régionaux motivent une étude des ouvrages existants, sans confirmer un obstacle.','Examiner les ouvrages, les déplacements des espèces et la perméabilité réelle.'],
    ],
    summary:'Le lot public contient 101 secteurs et 404 examens familiaux : 165 pistes historiques à étudier et 239 situations non qualifiables. 71 secteurs présentent au moins une piste et 30 n’en présentent aucune. Les niveaux A/B/C, les relations entre propositions et les nouvelles propositions du lot expérimental ne sont pas disponibles dans ce contrat public. Aucune efficacité ni nécessité de travaux n’est déduite.'
  }
}
