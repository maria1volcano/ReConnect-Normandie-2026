import { loadV2, loadV2Cell, loadMethodology, LEVEL_NAMES } from './multiActionsV2Adapter'
import { presentAction, readableNonSelection } from './actionPresentation'
import type { JourneySource } from './journeyModel'

const families = [
  ['Haies','Une rencontre haie–voie au sol peut ancrer une étude précise ; une relation au réseau régional appelle un approfondissement. Une haie seulement localisée ouvre une exploration.','Vérifier la continuité réelle, les habitats et les pratiques de gestion.'],
  ['Milieux humides','Un plan d’eau identifié et typé, en relation avec le réseau régional ou un inventaire, peut ancrer une étude. Les autres recouvrements sont à approfondir ; une présence seule est à explorer.','Identifier le milieu et son alimentation en eau ; aucun déficit de mares n’est déduit.'],
  ['Friches','Un site typé, non reconverti selon la source et recouvrant le réseau régional peut ancrer une étude. Un type manquant conduit à approfondir ; une présence admissible seule reste à explorer.','Actualiser le statut, relever les habitats existants et examiner les sols et projets.'],
  ['Franchissements pour la faune','Une voie carrossable en service au sol croisant un espace de continuité permet une étude précise. Les autres croisements sont à approfondir ; une simple présence commune reste à explorer.','Examiner les ouvrages, les déplacements des espèces et la perméabilité réelle.'],
]

/** Reached only through Root's DEV-only lazy import and the unchanged loopback/flag gates. */
export const localJourneySource: JourneySource = {
  kind: 'local_experimental',
  notice: 'Revue locale : données expérimentales internes. Leur diffusion publique n’est pas autorisée.',
  footer: 'Version locale de revue · données internes, diffusion non autorisée.',
  load: loadV2,
  async loadCell(id,signal) {
    const cell=await loadV2Cell(id,signal)
    return {...cell, linkedObservations: cell.comparisons.some(c=>c.observations_liees),
      actions:cell.actions.map(a=>({action_id:a.action_id,name:a.name,source:'local_experimental' as const,level:a.level,copy:presentAction(a)})),
      not_selected:cell.not_selected.map(a=>({action_id:a.action_id,explanation:readableNonSelection(a.reason)}))}
  },
  async loadExample(signal) {
    const {example}=await loadMethodology(signal)
    return {...example, actions:example.actions.map(a=>({action_id:a.action_id,justification:LEVEL_NAMES[a.level].toLocaleLowerCase('fr')}))}
  },
  method: {
    levels: true, families,
    sourceCounts: ['17 335 tronçons routiers, 879 haies, 5 plans d’eau', '40 espaces de continuité et 41 réservoirs', '172 éléments retenus', '77 sites recensés, dont des sites reconvertis', 'Couverture du sol et artificialisation', '6 communes'],
    intro: 'La chaîne est explicite : observation localisée → hypothèse écologique → conditions propres à la famille → question d’étude. Pour chaque famille, le moteur retient le niveau d’ancrage satisfait, sans quota ni comparaison de bénéfice entre familles. Les trois niveaux de justification sont des heuristiques conçues par notre équipe ; aucune publication retrouvée ne prescrit ces sélecteurs.',
    summary: 'Le pilote produit 205 pistes sur 88 secteurs : 93 études étayées, 45 pistes à approfondir et 67 à explorer. 61 secteurs ont plusieurs pistes et 13 restent sans proposition. Une famille peut rester sans proposition faute d’objet admissible localisable, ou lorsque le statut connu contredit l’intervention envisagée, par exemple un site déjà reconverti. Ce résultat ne conclut pas à une absence écologique. Les observations communes sont signalées ; elles ne multiplient pas la force de preuve. Les familles restent non départagées et aucune action principale n’est imposée.'
  }
}
