import type { FeatureCollection, Geometry } from 'geojson'
import type { RealGridFeatureProperties } from './priorityAdapter'
import type { ActionPresentation } from './actionPresentation'

/** Presentation values only. No contract, selection or scientific decision is inferred here. */
export const LEVEL_NAMES = { A: 'Étude étayée', B: 'À approfondir', C: 'À explorer' } as const
export const TERRITORIAL_PALETTE = {rouge:'#D64545', orange:'#EF9229', jaune:'#E8C84A', gris:'#9098A4'} as const
export interface Sector { number: number; municipalities: string[]; label: string }
export interface JourneyPriority {
  color: keyof typeof TERRITORIAL_PALETTE; color_hex: string; rank: 1 | 2 | 3 | null
  evidence: {nombre_paires_route_corridor_2d: number; paires_route_matrice_fragile_en_service_au_sol: number; reservoir_presence_surface_positive: boolean; corridor_presence_surface_positive: boolean}
}
export type JourneyAction = {action_id: string; name: string; copy: ActionPresentation} & (
  {source: 'historical_public'; level?: never; origin?: 'extension'} | {source: 'local_experimental'; level: keyof typeof LEVEL_NAMES}
)
export interface JourneyCell {
  maille_id: string; sector: Sector; municipalities: string[]; territorial_priority: JourneyPriority
  actions: JourneyAction[]; not_selected: Array<{action_id: string; explanation: string}>
  linkedObservations: boolean
  observations: Record<string, {nombre_objets_observes: number | null; mesure_observee: number | null; unite?: string}>
  local_event_count: number; canonical_event_count: number
}
export type JourneyGridProperties = RealGridFeatureProperties & {sector: Sector; territorial_priority: JourneyPriority; study_color: string}
export interface JourneyData {grid: FeatureCollection<Geometry, JourneyGridProperties>; metadata: {cells: number; proposals: number}}
export interface JourneyExample {
  maille_id: string; sector: Sector; area_m2: number; priority: JourneyPriority
  hedge_length_m: number | null; wetland_area_m2: number | null; actions: Array<{action_id: string; justification: string}>
}
export interface JourneySource {
  kind: 'historical_public' | 'local_experimental'
  notice: string; footer: string
  load: (signal?: AbortSignal) => Promise<JourneyData>
  loadCell: (id: string, signal?: AbortSignal) => Promise<JourneyCell>
  loadExample: (signal?: AbortSignal) => Promise<JourneyExample>
  method: {sourceCounts?: readonly string[]; intro: string; families: readonly (readonly string[])[]; summary: string; levels: boolean}
}
