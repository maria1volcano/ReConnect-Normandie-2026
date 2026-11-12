import { loadStaticCells, type M4CellBundle } from './m4Adapter'

export type RuleId = 'R1' | 'R2' | 'R3' | 'R4'

export interface CatalogueFamily {
  ruleId: RuleId
  actionId: string
  name: string
  question: string
  declarationEtayee: string
  declarationIndicative: string
  absenceDocumentee: string
  nonEvaluable: string
  aVerifier: string
  sources: string[]
  leadCount: number
  cellCount: number
  cells: Array<{ mailleId: string; municipalities: string[]; documentaryLevel: string }>
}

// Définitions issues de docs/rules_actions.json (règles R1–R4, statut
// « proposition_de_specification_non_approuvee_M4 ») et docs/regles_actions_m2.md
// §5. Aucun intitulé ni seuil n'est inventé ici.
export const CATALOGUE_FAMILY_ORDER: RuleId[] = ['R1', 'R2', 'R3', 'R4']

const FAMILY_META: Record<RuleId, Omit<CatalogueFamily, 'leadCount' | 'cellCount' | 'cells'>> = {
  R1: {
    ruleId: 'R1',
    actionId: 'A04',
    name: 'Franchissement routier de la faune',
    question: 'Croisement route–corridor qualifié, avec examen des ouvrages existants.',
    declarationEtayee:
      'Événement réel route–corridor avec identifiant de conflit, sources route et corridor versionnées, sous-trame pertinente et qualification « conflit_potentiel » ou « obstacle_confirme ».',
    declarationIndicative:
      'Croisement détecté géométriquement de façon fiable, sans qualification de la gêne occasionnée.',
    absenceDocumentee:
      'Pas de croisement pertinent selon une couverture thématique, spatiale et temporelle réellement validée.',
    nonEvaluable:
      'Couche manquante, localisation incertaine ou conflit géométrique non résolu.',
    aVerifier:
      'Ouvrage existant (SIPAF), route ou voie, trafic, espèces concernées et gestionnaire. Une entrée R1 ne recommande jamais de construire directement un passage.',
    sources: ['BD TOPO 3.5 — tronçons de route (IGN)', 'SRCE — corridors et réservoirs 2014 (DREAL Normandie)', 'SIPAF — passages à faune'],
  },
  R2: {
    ruleId: 'R2',
    actionId: 'A01',
    name: 'Restauration de haies et continuités bocagères',
    question: 'Lacune ou discontinuité du réseau de haies sur une sous-trame pertinente.',
    declarationEtayee:
      'Analyse structurale ou topologique du réseau de haies documentant une lacune reliée à une sous-trame pertinente, avec emprise, millésime et couverture valides.',
    declarationIndicative:
      'Vraie rupture cartographiée possible, mais état du réseau ou pertinence à confirmer.',
    absenceDocumentee:
      'Réseau évalué et aucune lacune candidate selon les règles annoncées.',
    nonEvaluable:
      'Simple densité faible, haies non cartographiées ou absence de méthode de connectivité validée.',
    aVerifier:
      'Usages, parcelles, gestion, état actuel et pratiques agricoles avant toute intervention.',
    sources: ['BD Haie V2 (IGN / OFB)', 'SRCE — matrice bocagère 2014 (DREAL Normandie)'],
  },
  R3: {
    ruleId: 'R3',
    actionId: 'A03',
    name: 'Renaturation de friches',
    question: 'Friche officiellement recensée présentant une relation spatiale justifiée avec une continuité.',
    declarationEtayee:
      'Friche identifiée et contrôlée présentant une relation géométrique à une continuité définie par une méthode de voisinage versionnée, avec faits indispensables suffisants pour proposer une étude.',
    declarationIndicative:
      'Friche localisée et élément de relation plausibles mais encore incomplets.',
    absenceDocumentee:
      'Aucune friche candidate selon inventaire et règle de relation entièrement couverts.',
    nonEvaluable:
      'Simple polygone supposé friche, absence de critère de proximité, statut non vérifié.',
    aVerifier:
      'Pollution, valeur écologique préexistante, contraintes foncières et usages — examens de faisabilité, pas un score.',
    sources: ['Cartofriches — sites référencés (Cerema)', "Observatoire des friches EPF Normandie (accès à clarifier)"],
  },
  R4: {
    ruleId: 'R4',
    actionId: 'A02',
    name: 'Mares et réseaux de mares',
    question: 'Discontinuité ou isolement potentiel documenté dans un réseau de milieux humides.',
    declarationEtayee:
      'Isolement ou lacune du réseau d’ habitats humides documenté par une méthode adaptée et un contexte hydrologique pertinent.',
    declarationIndicative:
      'Faiblesse du réseau attestée comme hypothèse, hydrologie ou connectivité à confirmer.',
    absenceDocumentee:
      'Aucun déficit documenté dans le réseau étudié avec inventaire assez complet.',
    nonEvaluable:
      'Simple « absence de points de mares », inventaire partiel, règle de distance arbitraire, aucun contexte hydrologique.',
    aVerifier:
      'Ne pas proposer de point d’implantation ni de création directe ; inventaire et contexte hydrologique d’abord.',
    sources: ['PRAM — base de données zones humides Normandie', 'SRCE — sous-trame bleue 2014 (DREAL Normandie)'],
  },
}

let cache: Promise<CatalogueFamily[]> | null = null

export function loadCatalogueFamilies(): Promise<CatalogueFamily[]> {
  cache ??= loadStaticCells()
    .then((cells) => buildFamilies(cells))
    .catch((error) => {
      cache = null
      throw error
    })
  return cache
}

function buildFamilies(cells: Record<string, M4CellBundle>): CatalogueFamily[] {
  return CATALOGUE_FAMILY_ORDER.map((ruleId) => {
    const familyCells: CatalogueFamily['cells'] = []
    let leadCount = 0
    for (const bundle of Object.values(cells)) {
      const leads = bundle.investigations.filter(
        (inv) => inv.rule_id === ruleId && inv.lead_status === 'a_etudier',
      )
      if (leads.length > 0) {
        leadCount += leads.length
        familyCells.push({
          mailleId: bundle.maille_id,
          municipalities: bundle.municipalities.map((m) => m.nom),
          documentaryLevel: bundle.documentary.level,
        })
      }
    }
    familyCells.sort((a, b) => a.mailleId.localeCompare(b.mailleId))
    return { ...FAMILY_META[ruleId], leadCount, cellCount: familyCells.length, cells: familyCells }
  })
}

export function mailleIdsForRule(cells: Record<string, M4CellBundle>, ruleId: RuleId): Set<string> {
  const ids = new Set<string>()
  for (const bundle of Object.values(cells)) {
    if (bundle.investigations.some((inv) => inv.rule_id === ruleId && inv.lead_status === 'a_etudier')) {
      ids.add(bundle.maille_id)
    }
  }
  return ids
}
