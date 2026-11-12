import type { FeatureCollection, Geometry } from 'geojson'
import type { RealGridFeatureProperties } from './priorityAdapter'

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
  validated_recommendations: []
}

export class M4UnavailableError extends Error {}

function staticDataUrl(fileName: string): string {
  return new URL(`${import.meta.env.BASE_URL}data/caen-6com/${fileName}`, window.location.href).href
}

let staticCellsPromise: Promise<Record<string, M4CellBundle>> | null = null

export function loadStaticCells(signal?: AbortSignal): Promise<Record<string, M4CellBundle>> {
  staticCellsPromise ??= fetchJson<Record<string, M4CellBundle>>(staticDataUrl('cells.json'), signal).catch((error) => {
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
  const response = await fetch(url, { signal, headers: { Accept: 'application/json' } })
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
  if (features.length !== 101 || features.some((feature) => feature.properties.grid_version !== gridVersion || feature.properties.territory_id !== territoryId)) {
    throw new M4UnavailableError('Réponse M4 incompatible avec la grille demandée')
  }
  return bundle
}
