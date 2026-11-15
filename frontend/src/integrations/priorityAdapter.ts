import type { FeatureCollection, Geometry } from 'geojson'

export const PRIORITY_GRID_VERSION = 'M1-CAND-1KM2-FLAT-L93-O0-V1' as const

export const ECOLOGICAL_PRIORITY = {
  HIGH: { color: '#D9534F', label: 'Priorité écologique élevée' },
  MODERATE: { color: '#F29A48', label: 'Priorité écologique modérée' },
  LOW: { color: '#E6C65B', label: 'Priorité écologique faible' },
  INDETERMINATE: { color: '#89938F', label: 'Priorité indéterminée' },
} as const

export type EcologicalPriorityCategory = keyof typeof ECOLOGICAL_PRIORITY
export type ScientificValidationStatus = 'VALIDATED' | 'PENDING' | 'REJECTED' | 'UNKNOWN'
export type ReliabilityLevel = 'SUFFICIENT' | 'PARTIAL' | 'INSUFFICIENT' | 'UNKNOWN'

export interface EcologicalPriorityRecord {
  maille_id: string
  grid_version: string
  category: EcologicalPriorityCategory
  scientific_validation: ScientificValidationStatus
  method_version: string | null
  justification: string | null
  reliability: {
    level: ReliabilityLevel
    uncertainty: string | null
    limitations: string[]
  }
  provenance: string[]
}

export type PriorityResolutionReason =
  | 'validated'
  | 'missing_priority'
  | 'grid_version_mismatch'
  | 'scientific_validation_pending'
  | 'synthetic_demo'

export interface ResolvedEcologicalPriority extends EcologicalPriorityRecord {
  category: EcologicalPriorityCategory
  resolution_reason: PriorityResolutionReason
}

export interface RealGridFeatureProperties {
  study_priority?: import('./m4Adapter').M4StudyPriority
  study_color?: string
  territory_id?: string
  documentary_level?: 'rouge' | 'orange' | 'jaune' | 'gris'
  documentary_rule?: 'V1' | 'V2' | 'V3' | 'V4'
  documentary_color?: '#D9534F' | '#F29A48' | '#E6C65B' | '#89938F'
  maille_id: string
  grid_version: string
  grid_row?: number
  grid_col?: number
  center_x?: number
  center_y?: number
  full_area_m2?: number
  clipped_area_m2?: number
  area_m2?: number
  pilot_fraction?: number
  is_boundary?: boolean
  priority_category: EcologicalPriorityCategory
  priority_validation_status: ScientificValidationStatus
  priority_method_version: string | null
  priority_justification: string | null
  priority_reliability: ReliabilityLevel
  priority_uncertainty: string | null
  priority_limitations: string[]
  priority_provenance: string[]
  priority_resolution_reason: PriorityResolutionReason
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === 'string')
}

function isNullableString(value: unknown): value is string | null {
  return value === null || typeof value === 'string'
}

export function parsePriorityRecord(value: unknown): EcologicalPriorityRecord | null {
  if (!isRecord(value) || !isRecord(value.reliability)) return null

  const category = value.category
  const validation = value.scientific_validation
  const reliabilityLevel = value.reliability.level
  if (
    typeof value.maille_id !== 'string' ||
    typeof value.grid_version !== 'string' ||
    !Object.hasOwn(ECOLOGICAL_PRIORITY, String(category)) ||
    !['VALIDATED', 'PENDING', 'REJECTED', 'UNKNOWN'].includes(String(validation)) ||
    !isNullableString(value.method_version) ||
    !isNullableString(value.justification) ||
    !['SUFFICIENT', 'PARTIAL', 'INSUFFICIENT', 'UNKNOWN'].includes(String(reliabilityLevel)) ||
    !isNullableString(value.reliability.uncertainty) ||
    !isStringArray(value.reliability.limitations) ||
    !isStringArray(value.provenance)
  ) {
    return null
  }

  return value as unknown as EcologicalPriorityRecord
}

export function resolveEcologicalPriority(
  mailleId: string,
  expectedGridVersion: string,
  input?: unknown,
): ResolvedEcologicalPriority {
  const record = parsePriorityRecord(input)
  const fallback: ResolvedEcologicalPriority = {
    maille_id: mailleId,
    grid_version: expectedGridVersion,
    category: 'INDETERMINATE',
    scientific_validation: record?.scientific_validation ?? 'UNKNOWN',
    method_version: record?.method_version ?? null,
    justification: record?.justification ?? 'Méthode scientifique en attente de validation.',
    reliability: record?.reliability ?? {
      level: 'UNKNOWN',
      uncertainty: 'Priorité scientifique non disponible ou non validée.',
      limitations: ['Aucune classification écologique validée n’est disponible pour cette maille.'],
    },
    provenance: record?.provenance ?? [],
    resolution_reason: 'missing_priority',
  }

  if (!record || record.maille_id !== mailleId) return fallback
  if (record.grid_version !== expectedGridVersion) {
    return {
      ...fallback,
      scientific_validation: 'UNKNOWN',
      method_version: null,
      justification: 'Priorité rejetée : version de grille incompatible.',
      reliability: {
        level: 'UNKNOWN',
        uncertainty: 'L’enregistrement ne correspond pas à la version de la grille affichée.',
        limitations: ['Aucune catégorie reçue pour une autre version de grille ne peut être affichée.'],
      },
      provenance: [],
      resolution_reason: 'grid_version_mismatch',
    }
  }
  if (record.scientific_validation !== 'VALIDATED') {
    return { ...fallback, resolution_reason: 'scientific_validation_pending' }
  }

  return { ...record, resolution_reason: 'validated' }
}

export function applyEcologicalPriorities(
  grid: FeatureCollection<Geometry>,
  priorityRecords: readonly unknown[],
): FeatureCollection<Geometry, RealGridFeatureProperties> {
  const recordsByCell = new Map<string, unknown>()
  for (const candidate of priorityRecords) {
    const parsed = parsePriorityRecord(candidate)
    if (parsed) recordsByCell.set(`${parsed.grid_version}::${parsed.maille_id}`, candidate)
  }

  return {
    type: 'FeatureCollection',
    features: grid.features.map((feature) => {
      const properties = feature.properties ?? {}
      const mailleId = typeof properties.maille_id === 'string' ? properties.maille_id : ''
      const gridVersion = typeof properties.grid_version === 'string' ? properties.grid_version : ''
      const priority = resolveEcologicalPriority(
        mailleId,
        gridVersion,
        recordsByCell.get(`${gridVersion}::${mailleId}`),
      )

      return {
        ...feature,
        properties: {
          ...properties,
          maille_id: mailleId,
          grid_version: gridVersion,
          priority_category: priority.category,
          priority_validation_status: priority.scientific_validation,
          priority_method_version: priority.method_version,
          priority_justification: priority.justification,
          priority_reliability: priority.reliability.level,
          priority_uncertainty: priority.reliability.uncertainty,
          priority_limitations: priority.reliability.limitations,
          priority_provenance: priority.provenance,
          priority_resolution_reason: priority.resolution_reason,
        } as RealGridFeatureProperties,
      }
    }),
  }
}

export function priorityFromFeature(
  properties: RealGridFeatureProperties,
): ResolvedEcologicalPriority {
  return {
    maille_id: properties.maille_id,
    grid_version: properties.grid_version,
    category: properties.priority_category,
    scientific_validation: properties.priority_validation_status,
    method_version: properties.priority_method_version,
    justification: properties.priority_justification,
    reliability: {
      level: properties.priority_reliability,
      uncertainty: properties.priority_uncertainty,
      limitations: properties.priority_limitations,
    },
    provenance: properties.priority_provenance,
    resolution_reason: properties.priority_resolution_reason,
  }
}
