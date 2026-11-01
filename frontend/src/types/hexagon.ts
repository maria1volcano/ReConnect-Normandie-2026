/**
 * Type definitions for hexagonal diagnostic grid data
 * Based on PRD V6.1 contract between M2 → M3/M4
 */

export type PriorityExamen = 'elevee' | 'moderee' | 'faible' | 'indeterminee'

export type StatutAnalyse = 'calculee' | 'donnees_insuffisantes' | 'analyse_non_realisee'

export type EvidenceLevel = 'croisement_detecte' | 'conflit_potentiel' | 'obstacle_confirme' | 'non_concluant'

export type ActionStatut = 'etayee_pour_examen' | 'conditionnelle' | 'non_retenue_par_regle' | 'non_evaluable'

export interface DiagnosticResult {
  type: string
  description?: string
  evidence_level?: EvidenceLevel
}

export interface Indicateurs {
  enjeu_ecologique?: string
  pressions?: string[]
  urgence_temporelle?: string
  [key: string]: string | string[] | undefined
}

export interface Qualite {
  niveau: 'suffisante' | 'partielle' | 'insuffisante'
  sources_valides: string[]
  annees?: string[]
  echelle?: string
}

export interface HexagonFeatureProperties {
  maille_id: string
  grid_version: string
  statut_analyse: StatutAnalyse
  priorite_examen?: PriorityExamen
  diagnostics?: DiagnosticResult[]
  indicateurs?: Indicateurs
  qualite?: Qualite
  conflit_ids?: string[]
  action_ids?: string[]
  method_version?: string
  test_data?: boolean
}

export interface HexagonZoneDetail {
  maille_id: string
  statut_analyse: StatutAnalyse
  priorite_examen?: PriorityExamen
  dimensions: {
    enjeu_ecologique: string
    pressions: string[]
    urgence_temporelle: string
  }
  qualite: Qualite
  conflit_ids: string[]
  actions: Array<{
    action_id: string
    regle_id?: string
    statut: ActionStatut
    motif: string
  }>
  method_version: string
  test_data?: boolean
}

export interface DiagnosticDetail {
  maille_id: string
  statut_analyse: StatutAnalyse
  priorite_examen?: PriorityExamen
  priorite_explication?: string
  enjeux_ecologiques: string[]
  pressions_humanis: string[]
  fragmentation_conflits: DiagnosticResult[]
  urgence_temporelle?: string
  indicateurs: {
    enjeu_ecologique?: { valeur: string; unite?: string }
    fragmentation?: { valeur: string; unite?: string }
    pressions?: { valeur: string; unite?: string }
    fiabilite?: { valeur: string; unite?: string }
  }
  qualite: {
    niveau: 'suffisante' | 'partielle' | 'insuffisante'
    couverture: string
    sources: SourceReference[]
    annees?: string[]
    echelle?: string
    champs_manquants?: string[]
  }
  method_version: string
  conflit_ids?: string[]
  action_ids?: string[]
  test_data?: boolean
}

export type RelatedDataState =
  | 'disponible'
  | 'aucun_documente'
  | 'donnees_manquantes'
  | 'analyse_non_realisee'

export interface PotentialConflict {
  conflit_id: string
  type: string
  titre: string
  description: string
  feature_ecologique: string
  pression_humaine: string
  evidence_level: EvidenceLevel
  methode_detection?: string
  qualification: string
  sources: SourceReference[]
  limites: string[]
  test_data?: boolean
}

export interface RestorationActionSuggestion {
  action_id: string
  regle_id: 'R1' | 'R2' | 'R3' | 'R4'
  titre: string
  conflit_ids: string[]
  motif: string
  pertinence: string
  conditions_verification: string[]
  sources: SourceReference[]
  limites: string[]
  statut: ActionStatut
  test_data?: boolean
}

export interface ZoneDiagnosticBundle {
  diagnostic: DiagnosticDetail
  conflicts: PotentialConflict[]
  actions: RestorationActionSuggestion[]
  conflictState: RelatedDataState
  actionState: RelatedDataState
}

export interface SourceReference {
  nom: string
  producteur?: string
  annee?: string
  echelle?: string
  licence?: string
  url?: string
  description?: string
}

export interface PilotBoundaryProperties {
  pilot_id: string
  nom: string
  statut: 'valide' | 'en_attente'
  date_validation?: string
  superficie_km2?: number
  test_data?: boolean
}
