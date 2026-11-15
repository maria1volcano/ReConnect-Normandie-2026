import type { FeatureCollection, Geometry } from 'geojson'
import type { RealGridFeatureProperties } from './priorityAdapter'
import { DEFAULT_REAL_GRID_DATASET, CAEN_TERRITORY_ID } from './gridDatasets.ts'

export interface M4Investigation {
  action_id: string
  rule_id: string
  title: string
  status: 'non_evaluable'
  lead_status: 'a_etudier' | 'non_qualifiable'
  evidence: string
  reason: string
  missing_conditions: string[]
  validation_level: string
  works_recommended: false
}

export const ACTIONS_VERSION = 'caen6-priorites-etude-actions-20261112-1'
export interface M4StudyPriority {
  niveau: 1 | 2 | 3 | null
  couleur: 'rouge' | 'orange' | 'jaune' | 'gris'
  couleur_hex: string
  libelle: string
  version: string
  validation_ecologique: false
  note: string
}
export interface M4StudyAction {
  action_id: 'A01' | 'A02' | 'A03' | 'A04'
  regle_id: string
  statut_instruction: string
  statut_scientifique: 'non_evaluable'
  justification: string
  observations: string
  conditions_manquantes: string[]
  travaux_valides: false
  activation_regle_scientifique: false
  prochaines_etapes?: string[]
}
export interface M4Instruction {
  version: string
  diagnostic: string
  main_action: M4StudyAction | null
  no_main_reason: string | null
  complementary_actions: M4StudyAction[]
  no_complementary_reason: string
  options: M4StudyAction[]
  orientation: string
  conditions_before_works: string[]
  historical_lead_ids: string[]
  road_context: Record<string, Record<string, number>> | null
  DS: Record<string, unknown>
}

export interface M4CellBundle {
  territory_id: string
  maille_id: string
  grid_version: string
  dataset_version: string
  municipalities: Array<{ code_insee: string; nom: string; area_m2: number }>
  area_m2: number
  is_boundary: boolean
  documentary: {
    level: 'rouge' | 'orange' | 'jaune' | 'gris'
    rule: 'V1' | 'V2' | 'V3' | 'V4'
    title: string
    reason: string
    color: string
    observations: Record<string, unknown>
  }
  ecological_priority: { category: 'INDETERMINATE'; scientific_validation: 'PENDING'; method_version: null }
  geometric_observations: {
    local_event_count: number
    canonical_event_count: number
    source_observations: Record<string, { nombre_objets_observes: number | null; mesure_observee: number | null; unite?: string }>
    enj: Record<string, unknown>
  }
  investigations: M4Investigation[]
  limitations: string[]
  study_priority?: M4StudyPriority
  instruction?: M4Instruction
  provenance?: { source_zip_sha256: string; decision_version: string; dataset_version: string; test_data: false; publication_authorized: false }
  validated_recommendations: []
}

export class M4UnavailableError extends Error {}

export function validateInstruction(bundle: M4CellBundle): void {
  if (!bundle.instruction && !bundle.study_priority) return // Authorized legacy public release; no decisions inferred.
  const d = bundle.instruction
  const p = bundle.study_priority
  if (!d || !p || d.version !== ACTIONS_VERSION || p.version !== ACTIONS_VERSION
      || p.validation_ecologique !== false || bundle.validated_recommendations.length !== 0
      || bundle.ecological_priority.category !== 'INDETERMINATE' || bundle.ecological_priority.method_version !== null
      || !d.diagnostic || !Array.isArray(d.options) || !Array.isArray(d.conditions_before_works)
      || !['rouge', 'orange', 'jaune', 'gris'].includes(p.couleur)
      || !/^#[0-9a-f]{6}$/i.test(p.couleur_hex)
      || p.niveau !== ({rouge: 1, orange: 2, jaune: 3, gris: null} as const)[p.couleur]) {
    throw new M4UnavailableError('Décision M2 incompatible ou non vérifiable')
  }
  const actions = [...d.options, ...d.complementary_actions, ...(d.main_action ? [d.main_action] : [])]
  if (actions.some((a) => !a.justification || !Array.isArray(a.conditions_manquantes)
      || a.statut_scientifique !== 'non_evaluable' || a.travaux_valides !== false || a.activation_regle_scientifique !== false)
      || ((p.couleur === 'jaune' || p.couleur === 'gris') && d.main_action !== null)
      || (d.main_action && d.main_action.statut_instruction !== 'a_instruire_indicatif')) {
    throw new M4UnavailableError('Action sans justification ou statut scientifique incompatible')
  }
}

function staticDataUrl(fileName: string): string {
  return new URL(`${import.meta.env.BASE_URL}data/caen-6com/${fileName}`, window.location.href).href
}

let staticCellsPromise: Promise<Record<string, M4CellBundle>> | null = null

export function loadStaticCells(_signal?: AbortSignal): Promise<Record<string, M4CellBundle>> {
  staticCellsPromise ??= fetchJson<Record<string, M4CellBundle>>(staticDataUrl('cells.json')).catch((error) => {
    staticCellsPromise = null
    throw error
  })
  return staticCellsPromise
}

export function getM4ApiBaseUrl(): string | null {
  const configured = import.meta.env.VITE_M4_API_BASE_URL?.trim()
  // 'static'/'none'/vide : données publiques exportées sous public/data/caen-6com.
  // Non défini : backend local de démonstration (http://127.0.0.1:8765).
  if (configured === 'static' || configured === 'none' || configured === '') return null
  return (configured ?? 'http://127.0.0.1:8765').replace(/\/$/, '')
}

export function buildM4CellUrl(baseUrl: string, territoryId: string, gridVersion: string, mailleId: string): string {
  const url = new URL(`${baseUrl.replace(/\/$/, '')}/api/internal/caen/cells/${encodeURIComponent(mailleId)}`)
  url.searchParams.set('territory_id', territoryId)
  url.searchParams.set('grid_version', gridVersion)
  return url.toString()
}

async function fetchJson<T>(url: string, signal?: AbortSignal): Promise<T> {
  const deadline = AbortSignal.timeout(15_000)
  const boundedSignal = signal ? AbortSignal.any([signal, deadline]) : deadline
  const response = await fetch(url, { signal: boundedSignal, headers: { Accept: 'application/json' } })
  if (!response.ok) throw new M4UnavailableError(`M4 indisponible (${response.status})`)
  return response.json() as Promise<T>
}

export async function loadM4CellBundle(
  gridVersion: string,
  mailleId: string,
  territoryId: string,
  signal?: AbortSignal,
): Promise<M4CellBundle> {
  const baseUrl = getM4ApiBaseUrl()
  let bundle: M4CellBundle
  if (baseUrl) {
    bundle = await fetchJson<M4CellBundle>(buildM4CellUrl(baseUrl, territoryId, gridVersion, mailleId), signal)
  } else {
    const cells = await loadStaticCells(signal)
    const candidate = cells[mailleId]
    if (!candidate) throw new M4UnavailableError(`Fiche publique absente pour ${mailleId}`)
    bundle = candidate
  }
  if (bundle.territory_id !== territoryId || bundle.grid_version !== gridVersion || bundle.maille_id !== mailleId) {
    throw new M4UnavailableError('Réponse M4 incompatible avec la cellule demandée')
  }
  validateInstruction(bundle)
  return bundle
}

export async function loadM4Grid(gridVersion: string, territoryId: string, signal?: AbortSignal): Promise<FeatureCollection<Geometry, RealGridFeatureProperties>> {
  const baseUrl = getM4ApiBaseUrl()
  let bundle: FeatureCollection<Geometry, RealGridFeatureProperties>
  if (baseUrl) {
    const url = new URL(`${baseUrl}/api/internal/caen/grid`)
    url.searchParams.set('territory_id', territoryId)
    url.searchParams.set('grid_version', gridVersion)
    bundle = await fetchJson<FeatureCollection<Geometry, RealGridFeatureProperties>>(url.toString(), signal)
  } else {
    bundle = await fetchJson<FeatureCollection<Geometry, RealGridFeatureProperties>>(staticDataUrl('grid.geojson'), signal)
  }
  const features = bundle.features ?? []
  if (new Set(features.map((f) => f.properties.maille_id)).size !== 101 || features.length !== 101 || features.some((feature) => feature.properties.grid_version !== gridVersion || feature.properties.territory_id !== territoryId)) {
    throw new M4UnavailableError('Réponse M4 incompatible avec la grille demandée')
  }
  if (features.some((f) => !!f.properties.study_priority) && features.some((f) => !f.properties.study_priority)) {
    throw new M4UnavailableError('Lot incomplet : priorités indicatives manquantes')
  }
  for (const feature of features) {
    const p = feature.properties.study_priority
    if (p && (p.version !== ACTIONS_VERSION || p.validation_ecologique !== false
        || !['rouge', 'orange', 'jaune', 'gris'].includes(p.couleur) || !/^#[0-9a-f]{6}$/i.test(p.couleur_hex))) {
      throw new M4UnavailableError('Priorité indicative incompatible')
    }
    // Vector tiles stringify nested objects. Project the canonical color into a scalar display property.
    if (p) feature.properties.study_color = p.couleur_hex
  }
  return bundle
}

let cellsPromise: Promise<Record<string, M4CellBundle>> | null = null
export function loadCells(): Promise<Record<string, M4CellBundle>> {
  if (!getM4ApiBaseUrl()) return loadStaticCells()
  cellsPromise ??= (async () => {
    const grid = await loadM4Grid(DEFAULT_REAL_GRID_DATASET.gridVersion, CAEN_TERRITORY_ID)
    const cells: Record<string, M4CellBundle> = {}
    for (let i = 0; i < grid.features.length; i += 4) {
      const batch = await Promise.all(grid.features.slice(i, i + 4).map((f) =>
        loadM4CellBundle(f.properties.grid_version, f.properties.maille_id, CAEN_TERRITORY_ID)))
      for (const cell of batch) cells[cell.maille_id] = cell
    }
    return cells
  })().catch((error) => { cellsPromise = null; throw error })
  return cellsPromise
}
