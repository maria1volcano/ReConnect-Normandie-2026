import { SCIENTIFIC_REFERENCES, type ScientificReferenceId } from '../../integrations/scientificReferences'

function Reference({ id }: { id: ScientificReferenceId }) {
  const r = SCIENTIFIC_REFERENCES[id]
  return <><a href={r.url} target="_blank" rel="noreferrer">{r.title}</a><p>{r.author} · {r.year}. {r.use}</p></>
}

export function ScientificCitations({ ids }: { ids: readonly ScientificReferenceId[] }) {
  return <details className="scientific-citations"><summary>Fondements documentaires ({ids.length})</summary><ul>{ids.map(id=><li key={id}><Reference id={id}/></li>)}</ul></details>
}

export function ScientificFoundations() {
  return <section className="doc-section scientific-foundations"><h2>Une méthode fondée sur des travaux scientifiques et des données publiques</h2>
    <p>ReConnect Normandie mobilise les référentiels publics de l’IGN, de la DREAL et du Cerema, ainsi que des travaux sur les continuités écologiques. Notre équipe d’élèves ingénieurs a programmé des traitements géographiques et défini des règles pour repérer des secteurs et des pistes à étudier.</p>
    <p>Les principes écologiques éclairent les questions posées. Les intersections et mesures décrivent les objets cartographiés ; les catégories d’examen sont des choix du projet. L’interprétation fonctionnelle et le choix d’une intervention demandent une expertise écologique de terrain. Les organismes cités n’ont pas validé nos résultats, nos couleurs ou nos propositions.</p>
    <ScientificCitations ids={['tvb','srce']}/>
  </section>
}

export function MeshDistinction() {
  return <div className="scientific-mesh"><p>Le choix d’hexagones de 1 km² est une convention de découpage de l’équipe. Leur taille ne correspond pas à la « taille effective de maille » de Jaeger ou du SDES, qui caractérise des fragments d’habitats. Les indices de division, de découpage et de taille effective ne sont pas calculés ici.</p><ScientificCitations ids={['sdes','jaeger']}/></div>
}

const FORMULAS = {
  area: { origin: 'Formalisation d’une opération SIG standard', units: 'Hᵢ et T sont des polygones valides projetés en Lambert-93 ; Sᵢ est une aire en m². Seule la partie polygonale à l’intérieur du territoire est mesurée.', code: 'analysis/indicateurs_enjeux.py → compute_enjeux(), _polygonal_part() ; construction : analysis/preparer_caen_et_nord.py → grid().', ids: ['intersection'] },
  reservoir: { origin: 'Ratio géométrique standard, avec une condition de qualification propre au projet', units: 'Rⱼ désigne un réservoir cartographié ; numérateur et dénominateur sont en m², pᵢ en %. Sᵢ doit être strictement positif. L’union évite les superpositions ; sans preuve de complétude écologique validée, la proportion qualifiée reste inconnue.', code: 'analysis/indicateurs_enjeux.py → compute_enjeux(), _checked_proportion(), _fully_covered(). Les seuls ajustements admis portent sur l’arrondi numérique, sans seuil écologique.', ids: ['union','intersection','srce'] },
  exclusive: { origin: 'Convention de comptage déterministe de l’équipe', units: 'E contient les événements géométriques distincts admis ; Nᵢ est leur nombre attribué exclusivement au secteur i, sans unité physique. Chaque événement possède un seul secteur de comptage. Le nombre de rattachements locaux partagés est différent.', code: 'analysis/aggregate_conflicts.py → aggregate_conflicts(), _interior_relation(). Le propriétaire est choisi par la plus petite clé canonique parmi les mailles intersectées, en privilégiant les relations intérieures. Aucune source scientifique retrouvée ne prescrit cette convention.', ids: ['intersection'] },
} as const

export function FormulaProvenance({ kind }: { kind: keyof typeof FORMULAS }) {
  const f=FORMULAS[kind]
  return <div className="scientific-formula" data-formula-origin={kind}><p><strong>Origine : {f.origin}.</strong> {f.units}</p><details><summary>Retrouver le calcul et ses fondements</summary><p><code>{f.code}</code></p><p>Aucune de ces équations n’est une formule d’indice de fragmentation empruntée à une publication.</p><ScientificCitations ids={f.ids}/></details></div>
}

export function ScientificBibliography() {
  const entries=Object.entries(SCIENTIFIC_REFERENCES) as [ScientificReferenceId, (typeof SCIENTIFIC_REFERENCES)[ScientificReferenceId]][]
  return <div className="scientific-bibliography"><p>Les références déjà citées dans les règles ou la méthode du projet sont distinguées des compléments vérifiés pour cet audit. Une référence documentaire ne prouve pas qu’une méthode a été implémentée.</p>
    <ul className="v2-reference-list">{entries.map(([id,r])=><li id={'reference-'+id} key={id} data-reference-id={id}><Reference id={id}/><small>{r.provenance==='existing'?'Appui déjà cité dans les règles ou la méthode du projet':r.provenance==='data'?'Référentiel régional utilisé ; documentation précisée à l’audit':r.provenance==='context-existing'?'Comparaison déjà citée dans la méthode du projet ; méthode non appliquée':r.provenance==='context'?'Comparaison documentaire ajoutée à l’audit ; méthode non appliquée':'Complément documentaire vérifié à l’audit'}</small></li>)}</ul>
    <p>Liens, titres et dates vérifiés le 15 novembre 2026. Les pages OFB sans date explicite restent indiquées comme telles. La matrice complète de l’équipe est conservée dans <code>docs/TRACABILITE_SCIENTIFIQUE_20261115.md</code>.</p>
  </div>
}
