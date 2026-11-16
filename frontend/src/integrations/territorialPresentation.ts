import type { JourneyPriority, JourneyCell } from './journeyModel'

export const PRIORITY_LABELS = {
  rouge: 'Secteur à examiner en priorité', orange: 'Priorité d’examen élevée', jaune: 'Priorité d’examen modérée', gris: 'Informations insuffisantes',
} as const
export function prioritySymbol(priority: JourneyPriority): string {
  return priority.rank === null ? '?' : String(priority.rank)
}
export function searchText(text: string): string {
  return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('fr').replace(/[–—]/g, '-').trim()
}

/** Describes received measurements only; never computes a territorial grade. */
export function territorialSummary(cell: Pick<JourneyCell, 'territorial_priority' | 'observations'>): string {
  const priority=cell.territorial_priority, e=priority.evidence
  const count=(key:string)=>cell.observations[key]?.nombre_objets_observes?.toLocaleString('fr-FR') ?? 'nombre non renseigné'
  const pairs=e.nombre_paires_route_corridor_2d.toLocaleString('fr-FR')
  if(priority.color==='rouge')return `${pairs} couples distincts voie–espace de continuité sont cartographiés, dont ${e.paires_route_matrice_fragile_en_service_au_sol.toLocaleString('fr-FR')} associent une voie carrossable en service au sol à une matrice régionale fragile. La surface de réservoir observée dans ce secteur complète les indices qui motivent son examen en priorité.`
  if(priority.color==='orange')return `${pairs} couples distincts voie–espace de continuité sont cartographiés dans ce secteur. ${e.reservoir_presence_surface_positive ? 'Le contexte des voies et des matrices ne réunit pas tous les critères du premier groupe' : 'Aucun réservoir avec une surface positive n’est observé dans la maille, donc tous les critères du premier groupe ne sont pas réunis'} ; les passages et leur fonctionnement restent à examiner.`
  if(priority.color==='jaune')return `${count('corridors')} espaces de continuité et ${count('reservoirs')} réservoirs de biodiversité sont recensés dans ce secteur, sans croisement routier retenu par cette méthode. Leur état et leur préservation restent à examiner, sans déduire de ce résultat une absence de fragmentation.`
  return `Les inventaires recensent ici ${count('haies')} haies, ${count('friches')} sites de friches et ${count('zones_humides')} éléments d’inventaire humide. Les indices routiers nécessaires au classement ne sont pas réunis ; ces comptes ne prouvent ni une absence écologique ni une faible priorité d’examen.`
}
