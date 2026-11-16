import type { JourneyAction, JourneyCell, JourneyData, JourneySource } from './journeyModel'
import type { ScientificReferenceId } from './scientificReferences'
import { searchText, PRIORITY_LABELS } from './territorialPresentation.ts'

/** Four documented families, adapted from the historical catalogue. No M5 cards
 * or ecological selectors are introduced. References are those already audited. */
export const CATALOGUE_FAMILIES = [
  {id:'A04',label:'Faune',title:'Étudier les franchissements pour la faune',methodIndex:3,
    problem:'Une voie peut gêner les déplacements entre habitats, selon les espèces et les ouvrages présents.',
    solution:'Examiner les ouvrages existants et les possibilités d’améliorer leur perméabilité avant d’envisager un aménagement.',
    indicators:'Tracés routiers, espaces de continuité, position des voies et observations des déplacements de la faune.',
    limit:'Un croisement cartographique ne démontre pas un obstacle. Le trafic, les espèces et les ouvrages doivent être qualifiés sur place.',
    sources:['IGN : routes observées','DREAL : espaces de continuité et réservoirs','Inventaire des passages à faune : complément à consulter, non fourni dans le lot'],references:['passages','obstacles']},
  {id:'A01',label:'Bocage',title:'Préserver les haies et étudier leur continuité',methodIndex:0,
    problem:'L’état et la continuité des haies peuvent influencer les déplacements des espèces et la qualité de leurs habitats.',
    solution:'Étudier la préservation, la gestion et, si un besoin est confirmé, le renforcement des connexions bocagères.',
    indicators:'Haies localisées, état du réseau et relations cartographiques avec les voies et les espaces régionaux.',
    limit:'La présence ou une faible densité de haies ne suffit pas à démontrer une lacune. Une analyse du réseau et du terrain reste nécessaire.',
    sources:['IGN : haies observées, exhaustivité écologique non validée','DREAL : contexte bocager régional'],references:['haies','srce']},
  {id:'A03',label:'Friches',title:'Étudier le devenir écologique des friches',methodIndex:2,
    problem:'Le devenir d’un site peut affecter des habitats existants ou des connexions avec les milieux voisins.',
    solution:'Examiner les habitats, les usages et la faisabilité d’une renaturation compatible avec la valeur écologique déjà présente.',
    indicators:'Sites officiellement recensés, statut actuel, habitats et relations spatiales avec les continuités.',
    limit:'Un site recensé n’est pas nécessairement disponible ni dégradé. Le foncier, les projets et les éventuelles pollutions conditionnent toute intervention.',
    sources:['Cerema : sites Cartofriches','État actuel du site, usages et sols : vérifications complémentaires'],references:['renaturation','friches']},
  {id:'A02',label:'Milieux humides',title:'Préserver et étudier les milieux humides',methodIndex:1,
    problem:'Les déplacements entre habitats humides dépendent de la nature des milieux et de leur fonctionnement hydrologique.',
    solution:'Préciser les milieux présents et leur alimentation en eau pour étudier leur préservation ou une restauration adaptée.',
    indicators:'Plans d’eau typés, inventaires humides, contexte hydrologique et relations avec le réseau régional.',
    limit:'Un plan d’eau n’est pas automatiquement une mare. Un inventaire partiel ne démontre pas un déficit et ne justifie pas une création directe.',
    sources:['IGN : plans d’eau observés, mares non qualifiées','DREAL : inventaires humides de couverture hétérogène','Inventaires de mares : complément à consulter, non fourni dans le lot'],references:['tvb','mares','srce']},
] as const satisfies readonly {id:string;label:string;title:string;methodIndex:number;problem:string;solution:string;indicators:string;limit:string;sources:readonly string[];references:readonly ScientificReferenceId[]}[]
export type CatalogueFamilyId = typeof CATALOGUE_FAMILIES[number]['id']
export interface CatalogueFilters {family:CatalogueFamilyId|'all';commune:string;priority:keyof typeof PRIORITY_LABELS|'all';query:string}
export const EMPTY_CATALOGUE_FILTERS:CatalogueFilters={family:'all',commune:'all',priority:'all',query:''}
export interface CatalogueEntry {cell:JourneyCell;action:JourneyAction}
export interface JourneyCatalogue {data:JourneyData;cells:JourneyCell[];families:Array<{id:CatalogueFamilyId;entries:CatalogueEntry[]}>}

/** Indexes received proposals, without selecting, grading or ranking solutions. */
export function buildJourneyCatalogue(data:JourneyData,cells:JourneyCell[],kind:JourneySource['kind']):JourneyCatalogue {
  const ids=new Set(data.grid.features.map(f=>f.properties.maille_id))
  if(data.grid.features.length!==data.metadata.cells || cells.length!==data.metadata.cells || ids.size!==cells.length || new Set(cells.map(c=>c.maille_id)).size!==ids.size || cells.some(c=>!ids.has(c.maille_id)))throw new Error('Secteurs du catalogue incompatibles')
  const families=CATALOGUE_FAMILIES.map(f=>({id:f.id,entries:cells.flatMap(cell=>cell.actions.filter(a=>a.action_id===f.id).map(action=>({cell,action})))}))
  if(families.reduce((n,f)=>n+f.entries.length,0)!==data.metadata.proposals || cells.some(c=>new Set(c.actions.map(a=>a.action_id)).size!==c.actions.length)
    || families.some(f=>f.entries.some(e=>e.action.source!==kind || (kind==='historical_public' && 'level' in e.action))))throw new Error('Contrat de propositions incompatible')
  return {data,cells,families}
}
const cache=new WeakMap<JourneySource,Promise<JourneyCatalogue>>()
export async function loadJourneyCatalogue(source:JourneySource,signal?:AbortSignal):Promise<JourneyCatalogue> {
  signal?.throwIfAborted()
  let pending=cache.get(source)
  if(!pending){
    pending=(async()=>{
      const data=await source.load(),ids=data.grid.features.map(f=>f.properties.maille_id),cells:JourneyCell[]=new Array(ids.length)
      let cursor=0
      await Promise.all(Array.from({length:Math.min(4,ids.length)},async()=>{
        while(cursor<ids.length){const index=cursor++;cells[index]=await source.loadCell(ids[index])}
      }))
      return buildJourneyCatalogue(data,cells,source.kind)
    })().catch(error=>{cache.delete(source);throw error})
    cache.set(source,pending)
  }
  // A shared source snapshot survives route changes; one subscriber cannot abort another.
  const result=await pending;signal?.throwIfAborted();return result
}
export function readCatalogueFilters(search:string):CatalogueFilters {
  const p=new URLSearchParams(search),old={R1:'A04',R2:'A01',R3:'A03',R4:'A02'} as const
  const raw=p.get('famille')??'all',family=old[raw as keyof typeof old]??raw,priority=p.get('priorite')??'all'
  return {family:CATALOGUE_FAMILIES.some(f=>f.id===family)?family as CatalogueFamilyId:'all',commune:p.get('commune')||'all',priority:Object.hasOwn(PRIORITY_LABELS,priority)?priority as CatalogueFilters['priority']:'all',query:p.get('recherche')??''}
}
export function hasCatalogueFilters(filters:CatalogueFilters):boolean {
  return filters.family!=='all'||filters.commune!=='all'||filters.priority!=='all'||!!filters.query.trim()
}
export function filterCatalogueEntries(catalogue:JourneyCatalogue,id:CatalogueFamilyId,filters:CatalogueFilters):CatalogueEntry[] {
  if(filters.family!=='all'&&filters.family!==id)return []
  const definition=CATALOGUE_FAMILIES.find(f=>f.id===id)!,terms=searchText(filters.query).split(/\s+/).filter(Boolean)
  const familyText=searchText(`${definition.label} ${definition.title} ${definition.problem}`)
  return (catalogue.families.find(f=>f.id===id)?.entries??[]).filter(({cell})=>
    (filters.commune==='all'||cell.municipalities.includes(filters.commune)) && (filters.priority==='all'||cell.territorial_priority.color===filters.priority)
    && terms.every(term=>(familyText+' '+searchText(cell.sector.label)).includes(term)))
}
export function catalogueSectorIds(catalogue:JourneyCatalogue,filters:CatalogueFilters):Set<string> {
  return new Set(CATALOGUE_FAMILIES.flatMap(f=>filterCatalogueEntries(catalogue,f.id,filters).map(e=>e.cell.maille_id)))
}
export function catalogueHref(path:'/'|'/catalogue',filters:CatalogueFilters,maille?:string):string {
  const p=new URLSearchParams()
  if(filters.family!=='all')p.set('famille',filters.family)
  if(filters.commune!=='all')p.set('commune',filters.commune)
  if(filters.priority!=='all')p.set('priorite',filters.priority)
  if(filters.query.trim())p.set('recherche',filters.query)
  if(maille)p.set('maille',maille)
  return path+(p.size?'?'+p.toString():'')
}
