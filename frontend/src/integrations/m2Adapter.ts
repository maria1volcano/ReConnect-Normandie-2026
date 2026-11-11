export const M2_GRID_VERSION = 'M1-CAND-1KM2-FLAT-L93-O0-V1' as const

export type M2Availability = 'observed' | 'unknown'
export type M2CoverageStatus = 'unknown'

export interface M2IssueIndicator<T> {
  availability: M2Availability
  value: T | null
  status: string
}

export interface M2CellSummary {
  schemaVersion: 'm2-m4.internal-cell-summary-1'
  dataNature: 'reelle'
  diffusion: 'interne_revue_uniquement'
  cellId: string
  gridVersion: string
  observations: {
    status: 'geometric_detection'
    qualification: 'geometrie_2d'
    distinctEventCount: number
    relationshipCount: number
    canonicalOwnerCount: number
  }
  indicators: {
    enj01: M2IssueIndicator<number>
    enj02: M2IssueIndicator<boolean>
  }
  coverage: {
    routes: M2CoverageStatus
    corridors: M2CoverageStatus
    completeness: M2CoverageStatus
  }
  science: {
    priority: 'not_calculated'
    actions: 'not_calculated'
    validation: 'pending'
    limitations: string[]
  }
}

export class M2UnavailableError extends Error {
  constructor(message = 'Données M2 non chargées') {
    super(message)
    this.name = 'M2UnavailableError'
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

function isNonNegativeInteger(value: unknown): value is number {
  return Number.isInteger(value) && Number(value) >= 0
}

export function parseM2CellSummary(
  value: unknown,
  requestedCellId: string,
  expectedGridVersion: string,
): M2CellSummary {
  if (!isRecord(value) || value.schemaVersion !== 'm2-m4.internal-cell-summary-1') {
    throw new M2UnavailableError('Réponse M2 interne incompatible')
  }

  const observations = value.observations
  const indicators = value.indicators
  const coverage = value.coverage
  const science = value.science

  if (
    value.dataNature !== 'reelle' ||
    value.diffusion !== 'interne_revue_uniquement' ||
    value.cellId !== requestedCellId ||
    value.gridVersion !== expectedGridVersion ||
    !isRecord(observations) ||
    observations.status !== 'geometric_detection' ||
    observations.qualification !== 'geometrie_2d' ||
    !isNonNegativeInteger(observations.distinctEventCount) ||
    !isNonNegativeInteger(observations.relationshipCount) ||
    !isNonNegativeInteger(observations.canonicalOwnerCount) ||
    observations.distinctEventCount > observations.relationshipCount ||
    !isRecord(indicators) ||
    !isRecord(indicators.enj01) ||
    !isRecord(indicators.enj02) ||
    !isRecord(coverage) ||
    coverage.routes !== 'unknown' ||
    coverage.corridors !== 'unknown' ||
    coverage.completeness !== 'unknown' ||
    !isRecord(science) ||
    science.priority !== 'not_calculated' ||
    science.actions !== 'not_calculated' ||
    science.validation !== 'pending' ||
    !Array.isArray(science.limitations) ||
    !science.limitations.every((item) => typeof item === 'string')
  ) {
    throw new M2UnavailableError('Réponse M2 interne invalide')
  }

  const enj01 = indicators.enj01
  const enj02 = indicators.enj02
  if (
    enj01.availability !== 'unknown' ||
    enj01.value !== null ||
    typeof enj01.status !== 'string' ||
    !['observed', 'unknown'].includes(String(enj02.availability)) ||
    (enj02.value !== true && enj02.value !== null) ||
    (enj02.availability === 'observed' && enj02.value !== true) ||
    (enj02.availability === 'unknown' && enj02.value !== null) ||
    typeof enj02.status !== 'string'
  ) {
    throw new M2UnavailableError('États d’indicateurs M2 invalides')
  }

  return value as unknown as M2CellSummary
}

export async function loadM2CellSummary(
  cellId: string,
  signal?: AbortSignal,
  expectedGridVersion: string = M2_GRID_VERSION,
): Promise<M2CellSummary> {
  const response = await fetch(`/__internal/m2/cells/${encodeURIComponent(cellId)}`, {
    headers: { Accept: 'application/json' },
    signal,
  })

  if (!response.ok) {
    throw new M2UnavailableError()
  }

  return parseM2CellSummary(await response.json(), cellId, expectedGridVersion)
}
