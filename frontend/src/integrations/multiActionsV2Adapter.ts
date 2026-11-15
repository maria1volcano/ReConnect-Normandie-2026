import type { FeatureCollection, Geometry } from 'geojson'
import type { RealGridFeatureProperties } from './priorityAdapter'

export const V2_VERSION = 'm2.multiactions.experimental-2.0'
export const V2_SCOPE = {
  territory_id: 'caen_et_nord_6communes', grid_version: 'M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1',
  dataset_version: 'M1-CAEN-ET-NORD-20261111-V1', decision_version: V2_VERSION,
} as const
export const V2_MANIFEST = '95378d1f13bc94418b813b682f3c7a75572126374cb2e825b9e72da0ea8e6057'
export const LEVEL_NAMES = { A: 'Étude étayée', B: 'À approfondir', C: 'À explorer' } as const
export const TERRITORIAL_VERSION = 'caen6-priorites-etude-actions-20261112-1'
export const TERRITORIAL_PALETTE = {rouge:'#D64545', orange:'#EF9229', jaune:'#E8C84A', gris:'#9098A4'} as const
export interface Sector { number: number; municipalities: string[]; label: string }
export interface TerritorialPriority {
  version: string; presentation_version: string; color: keyof typeof TERRITORIAL_PALETTE; color_hex: string
  rank: 1 | 2 | 3 | null; status: 'indicative' | 'non_evaluable'; scope: 'interfaces_routieres_et_continuites'
  global_ecological_priority: false; works_urgency: null
  evidence: {nombre_paires_route_corridor_2d: number; paires_route_matrice_fragile_en_service_au_sol: number; reservoir_presence_surface_positive: boolean; corridor_presence_surface_positive: boolean}
}
export type V2GridProperties = RealGridFeatureProperties & {sector: Sector; territorial_priority: TerritorialPriority; study_color: string}
export type V2ActionId = 'A01' | 'A02' | 'A03' | 'A04'
export interface V2Action {
  action_id: V2ActionId; rule_id: string; name: string; level: 'A' | 'B' | 'C'; level_status: string
  objectives: string[]; solution: string; question: string; deliverable: string; reason: string
  observations: string[]; spatial_relations: string[]; uncertainties: string[]; checks_before_works: string[]
  next_steps: string[]; presence_only: boolean; rank: 1; ranking_reason: string
  scientific_status: 'non_evaluable'; scientific_decision_rule: 'A2'; source_context: Record<string, unknown[]>
  precision_qualified: false; works_validated: false; works_need_demonstrated: false
}
interface Envelope {
  territory_id: string; grid_version: string; dataset_version: string; decision_version: string
  mode: 'local_experimental'; test_data: false; publication_authorized: false
}
export interface V2Cell extends Envelope {
  sector: Sector; territorial_priority: TerritorialPriority
  maille_id: string; municipalities: string[]; diagnostic: string; actions: V2Action[]
  not_selected: Array<{action_id: V2ActionId; name: string; reason: string; scientific_status: 'non_evaluable'}>
  comparisons: Array<{action_a: string; action_b: string; conclusion: 'non_comparables'; motif: string; observations_liees: boolean}>
  observations: Record<string, {nombre_objets_observes: number | null; mesure_observee: number | null; unite: string}>
  local_event_count: number; canonical_event_count: number; historical: {level: string; rule: string}
  DS: {priorite_ecologique: {conclusion: string}; priorite_examen: {etat: string; valeur: null}; method_version: null}
  source_DS_sha256: string; historical_lead_count: number; main_action: null
  validated_recommendations: []; manifest_sha256: string
}
export interface V2Metadata extends Envelope {
  territorial_priority_version: string
  territorial_priority_counts: Record<'rouge'|'orange'|'jaune'|'gris'|'vert', number>
  cells: number; proposals: number; cells_with_proposals: number; multi_action_cells: number
  cells_without_proposals: number; A: number; B: number; C: number; c_only_cells: number
  linked_observation_cells: number; validated_recommendations: 0; manifest_sha256: string
}

export interface V2Methodology extends Envelope {
  example: {maille_id: string; sector: Sector; area_m2: number; local_events: number; exclusive_events: number
    priority: TerritorialPriority; hedge_length_m: number; wetland_area_m2: number; actions: Array<{action_id: V2ActionId; level: V2Action['level']}>}
}

export function validateTerritorialPriority(p: TerritorialPriority): void {
  if (!p || p.version !== TERRITORIAL_VERSION || p.presentation_version !== 'caen6-examen-multiactions-presentation-20261115-1'
    || !Object.hasOwn(TERRITORIAL_PALETTE, p.color) || p.color_hex !== TERRITORIAL_PALETTE[p.color]
    || p.rank !== ({rouge:1, orange:2, jaune:3, gris:null} as const)[p.color]
    || p.status !== (p.color === 'gris' ? 'non_evaluable' : 'indicative')
    || p.scope !== 'interfaces_routieres_et_continuites' || p.global_ecological_priority !== false || p.works_urgency !== null) {
    throw new Error('Priorité d’examen incompatible ; aucun classement de remplacement chargé.')
  }
}

export function isV2Enabled(): boolean {
  return import.meta.env?.DEV === true && import.meta.env.VITE_M2_MULTIACTIONS_V2 === '1'
    && typeof window !== 'undefined' && ['localhost', '127.0.0.1'].includes(window.location.hostname)
}

function envelope(value: Envelope): void {
  if (Object.entries(V2_SCOPE).some(([key, expected]) => value[key as keyof Envelope] !== expected)
      || value.mode !== 'local_experimental' || value.test_data !== false || value.publication_authorized !== false) {
    throw new Error('Version ou portée V2 incompatible ; aucune donnée de remplacement chargée.')
  }
}

export function validateV2Cell(cell: V2Cell, id: string): void {
  envelope(cell)
  validateTerritorialPriority(cell.territorial_priority)
  const pairing = {A01: 'R2', A02: 'R4', A03: 'R3', A04: 'R1'}
  const statuses = {A: 'etude_ciblee_justifiee', B: 'piste_plausible', C: 'piste_exploratoire'}
  if (cell.maille_id !== id || cell.manifest_sha256 !== V2_MANIFEST || !Array.isArray(cell.actions)
      || !Array.isArray(cell.not_selected) || cell.main_action !== null || cell.validated_recommendations.length !== 0
      || cell.DS.priorite_ecologique.conclusion !== 'indeterminee' || cell.DS.method_version !== null
      || cell.DS.priorite_examen.etat !== 'non_calculee' || cell.DS.priorite_examen.valeur !== null) {
    throw new Error('Fiche V2 incohérente ou résultat scientifique modifié.')
  }
  const ids = [...cell.actions, ...cell.not_selected].map(a => a.action_id)
  if (ids.length !== 4 || new Set(ids).size !== 4 || ids.some(id => !Object.hasOwn(pairing, id))) throw new Error('Familles V2 incompatibles.')
  for (const a of cell.actions) {
    if (a.rule_id !== pairing[a.action_id] || !Object.hasOwn(statuses, a.level) || a.level_status !== statuses[a.level]
        || !a.name || !a.question || !a.solution || !a.reason || !a.deliverable || a.rank !== 1
        || a.works_validated !== false || a.works_need_demonstrated !== false || a.scientific_status !== 'non_evaluable'
        || a.scientific_decision_rule !== 'A2' || a.presence_only !== (a.level === 'C') || a.precision_qualified !== false
        || [a.observations, a.uncertainties, a.checks_before_works, a.next_steps].some(v => !Array.isArray(v) || !v.length)) {
      throw new Error('Proposition V2 sans justification ou statut compatible.')
    }
  }
  if (cell.comparisons.length !== cell.actions.length * (cell.actions.length - 1) / 2
      || cell.comparisons.some(c => c.conclusion !== 'non_comparables')
      || cell.not_selected.some(a => !a.reason || a.scientific_status !== 'non_evaluable')) throw new Error('Comparaisons ou non-sélections incompatibles.')
}

function url(route: string): string {
  if (!isV2Enabled()) throw new Error('Le mode multi-actions V2 est désactivé.')
  const base = new URL(import.meta.env.VITE_M4_API_BASE_URL ?? 'http://127.0.0.1:8768')
  if (base.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(base.hostname) || base.username || base.password) {
    throw new Error('La V2 accepte uniquement un serveur HTTP local.')
  }
  const target = new URL(`/api/internal/caen/multiactions-v2/${route}`, base)
  for (const [key, value] of Object.entries(V2_SCOPE)) target.searchParams.set(key, value)
  return target.href
}
async function fetchV2<T>(route: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(url(route), {signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(20000)]) : AbortSignal.timeout(20000),
    cache: 'no-store', headers: {Accept: 'application/json'}})
  if (!response.ok) throw new Error(`Source V2 indisponible (${response.status}) ; vérifiez le mode local et sa version.`)
  return response.json() as Promise<T>
}
export async function loadV2Cell(id: string, signal?: AbortSignal): Promise<V2Cell> {
  const cell = await fetchV2<V2Cell>(`cells/${encodeURIComponent(id)}`, signal)
  validateV2Cell(cell, id)
  return cell
}
export async function loadMethodology(signal?: AbortSignal): Promise<V2Methodology> {
  const data = await fetchV2<V2Methodology>('methodology', signal)
  envelope(data); validateTerritorialPriority(data.example.priority)
  return data
}
export async function loadV2(signal?: AbortSignal): Promise<{metadata: V2Metadata; grid: FeatureCollection<Geometry, V2GridProperties>}> {
  const [metadata, grid] = await Promise.all([fetchV2<V2Metadata>('metadata', signal),
    fetchV2<FeatureCollection<Geometry, V2GridProperties> & Envelope>('grid', signal)])
  envelope(metadata); envelope(grid)
  for (const f of grid.features) {
    validateTerritorialPriority(f.properties.territorial_priority)
    if (f.properties.study_color !== f.properties.territorial_priority.color_hex
      || !f.properties.sector?.municipalities.length || !f.properties.sector.label) throw new Error('Repérage territorial incompatible.')
  }
  if (metadata.territorial_priority_version !== TERRITORIAL_VERSION
    || Object.entries({rouge:27,orange:33,jaune:9,gris:32,vert:0}).some(([color,count]) => metadata.territorial_priority_counts[color as keyof V2Metadata['territorial_priority_counts']] !== count)
    || Object.entries({rouge:27,orange:33,jaune:9,gris:32}).some(([color,count]) => grid.features.filter(f=>f.properties.territorial_priority.color===color).length!==count)) throw new Error('Distribution territoriale incompatible.')
  if (metadata.manifest_sha256 !== V2_MANIFEST || metadata.cells !== 101 || metadata.proposals !== 205
      || metadata.cells_with_proposals !== 88 || metadata.multi_action_cells !== 61 || metadata.cells_without_proposals !== 13
      || metadata.A !== 93 || metadata.B !== 45 || metadata.C !== 67 || metadata.c_only_cells !== 25 || metadata.validated_recommendations !== 0
      || grid.features.length !== 101 || new Set(grid.features.map(f => f.properties.maille_id)).size !== 101
      || grid.features.some(f => Object.entries(V2_SCOPE).some(([key, value]) => (f.properties as unknown as Record<string, unknown>)[key] !== value)
        || f.properties.priority_category !== 'INDETERMINATE')) throw new Error('Comptages ou grille V2 incompatibles.')
  return {metadata, grid}
}
