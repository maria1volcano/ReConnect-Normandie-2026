import { useEffect, useState } from 'react'
import { SiteHeader } from '../layout/SiteHeader'
import { linkClickHandler } from '../../app/router'
import { loadMethodology, type V2Methodology, LEVEL_NAMES } from '../../integrations/multiActionsV2Adapter'
import { actionFamilyVisual } from '../../integrations/actionFamilyVisuals'
import { JustificationLevels } from './JustificationLevels'
import { PRIORITY_LABELS } from '../../integrations/territorialPresentation'
import { ScientificFoundations, ScientificCitations, MeshDistinction, FormulaProvenance, ScientificBibliography } from '../method/ScientificBasis'
import type { ScientificReferenceId } from '../../integrations/scientificReferences'
import './multiActionsV2.css'

const SOURCES = [
  {name:'BD TOPO', producer:'IGN', vintage:'Millésime écologique non attesté', count:'17 335 tronçons routiers, 879 haies, 5 plans d’eau', role:'Localiser les voies, leur catégorie et leur niveau, les haies et les plans d’eau.', url:'https://www.data.gouv.fr/datasets/bd-topo-r'},
  {name:'Continuités du schéma régional', producer:'DREAL Normandie', vintage:'Référence 2014', count:'40 espaces de continuité et 41 réservoirs', role:'Décrire les espaces régionaux et leur classe documentaire ; leur fonctionnement actuel reste à vérifier.', url:'https://www.normandie.developpement-durable.gouv.fr/les-schemas-regionaux-de-coherence-ecologique-srce-a3638.html'},
  {name:'Inventaires des milieux humides', producer:'DREAL Normandie', vintage:'Périodes et méthodes variables', count:'172 éléments retenus', role:'Localiser des milieux inventoriés, en conservant leur typologie et leur méthode de diagnostic.', url:'https://www.data.gouv.fr/datasets/zones-humides-normandie'},
  {name:'Cartofriches', producer:'Cerema', vintage:'Statuts et dates à actualiser', count:'77 sites recensés, dont des sites reconvertis', role:'Identifier des sites et les projets connus, sans supposer leur disponibilité ni une dégradation écologique.', url:'https://www.data.gouv.fr/datasets/sites-references-dans-cartofriches'},
  {name:'Occupation du sol à grande échelle', producer:'IGN', vintage:'2023', count:'Couverture du sol et artificialisation', role:'Enrichir le contexte territorial. Cette source ne produit pas à elle seule une piste, un habitat humide ou une continuité fonctionnelle.', url:'https://geoservices.ign.fr/ocsge'},
  {name:'ADMIN EXPRESS', producer:'IGN', vintage:'Limites acquises en novembre 2026', count:'6 communes', role:'Délimiter le territoire et associer les communes aux secteurs par recouvrement de surface.', url:'https://geoservices.ign.fr/adminexpress'},
]
const FAMILY_RULES = [
  ['Haies','Une rencontre haie–voie au sol peut ancrer une étude précise ; une relation au réseau régional appelle un approfondissement. Une haie seulement localisée ouvre une exploration.','Vérifier la continuité réelle, les habitats et les pratiques de gestion.'],
  ['Milieux humides','Un plan d’eau identifié et typé, en relation avec le réseau régional ou un inventaire, peut ancrer une étude. Les autres recouvrements sont à approfondir ; une présence seule est à explorer.','Identifier le milieu et son alimentation en eau ; aucun déficit de mares n’est déduit.'],
  ['Friches','Un site typé, non reconverti selon la source et recouvrant le réseau régional peut ancrer une étude. Un type manquant conduit à approfondir ; une présence admissible seule reste à explorer.','Actualiser le statut, relever les habitats existants et examiner les sols et projets.'],
  ['Franchissements pour la faune','Une voie carrossable en service au sol croisant un espace de continuité permet une étude précise. Les autres croisements sont à approfondir ; une simple présence commune reste à explorer.','Examiner les ouvrages, les déplacements des espèces et la perméabilité réelle.'],
]
const FAMILY_REFERENCES: readonly (readonly ScientificReferenceId[])[] = [['haies'],['tvb','mares','srce'],['renaturation','friches'],['passages','obstacles']]
const fmt=(n:number,digits=0)=>n.toLocaleString('fr-FR',{maximumFractionDigits:digits})

export function MultiActionsMethodPage() {
  const [data,setData]=useState<V2Methodology|null>(null),[error,setError]=useState(false),[retry,setRetry]=useState(0)
  useEffect(()=>{
    const control=new AbortController();setError(false)
    void loadMethodology(control.signal).then(d=>{if(!control.signal.aborted)setData(d)}).catch(()=>{if(!control.signal.aborted)setError(true)})
    return()=>control.abort()
  },[retry])
  const example=data?.example
  return <div className="application-shell"><SiteHeader experimental/>
    <main id="main-content" className="doc-page v2-method-page">
      <section className="doc-hero"><p className="context-label">Des données aux questions d’étude</p><h1>Méthode et sources</h1>
        <p>Un traitement géographique reproductible repère des relations entre milieux et activités humaines. Des règles explicites transforment ces observations en pistes d’étude, avec leurs limites.</p>
        <a className="v2-method-link" href="/" onClick={linkClickHandler('/')}>Retour à la carte</a>
      </section>
      <ScientificFoundations/>
      <nav className="v2-method-nav" aria-label="Sommaire de la méthode">{[['objectif','Objectif'],['donnees','Données'],['calculs','Calculs'],['regles','Solutions'],['priorite','Couleurs'],['exemple','Exemple réel'],['references','Références']].map(([id,label])=><a key={id} href={'#'+id}>{label}</a>)}</nav>
      <section id="objectif" className="doc-section"><h2>1. Quel problème examinons-nous ?</h2>
        <p>Les voies et l’évolution des usages du sol peuvent affecter les déplacements des espèces entre leurs habitats. Le pilote examine les interfaces routières, les haies, les milieux humides et les friches susceptibles de participer aux continuités écologiques.</p>
        <p>Nous détectons des relations géographiques et formulons des questions d’étude. Un croisement de tracés ne démontre pas un obstacle ; la présence d’un site ne démontre pas un besoin de travaux.</p><ScientificCitations ids={['tvb','passages']}/>
      </section>
      <section id="donnees" className="doc-section"><h2>2. Quelles données sont réellement utilisées ?</h2>
        <p>Le périmètre couvre Caen, Bénouville, Blainville-sur-Orne, Colombelles, Hérouville-Saint-Clair et Ouistreham. Les sources ont été acquises ou enrichies en novembre 2026 ; leurs dates écologiques restent distinctes.</p>
        <div className="v2-source-grid">{SOURCES.map(s=><article key={s.name}><h3><a href={s.url} target="_blank" rel="noreferrer">{s.name}</a></h3><p className="v2-small-note">{s.producer} · {s.vintage}</p><p><strong>{s.count}.</strong> {s.role}</p></article>)}</div>
        <p>Les inventaires exhaustifs de mares, le trafic mesuré, les espèces sensibles et une qualification de terrain de la perméabilité ne sont pas intégrés. La couverture géométrique d’un fichier ne garantit pas son exhaustivité écologique. Le document régional décrit un cadrage au 1/100 000 : le découpage en secteurs ne lui ajoute pas de précision locale.</p><ScientificCitations ids={['srce']}/>
      </section>
      <section className="doc-section"><h2>3. Comment le territoire est-il découpé ?</h2>
        <p>Le maillage hexagonal fournit des unités régulières à six voisins, sans privilégier une direction de lecture horizontale ou verticale. Il s’agit d’un choix de découpage du projet, sans frontière écologique présumée. Les hexagones ont une surface de 1 km² avant découpe et sont construits en Lambert-93, le système de coordonnées métriques utilisé pour les calculs. Les hexagones sont intersectés avec l’union des six communes : 101 secteurs, dont 67 partiels, couvrent environ 65,21 km².</p>
        <p>Les objets sont associés par une intersection réelle avec la maille ; un contact limité à sa frontière reste distingué d’une relation intérieure. Une maille de bordure peut être très petite. Elle conserve sa surface réelle et ses relations locales ; elle ne doit pas être comparée comme s’il s’agissait d’un hexagone complet.</p>
      </section>
      <section className="doc-section"><h2>Quelle différence avec une mesure de fragmentation ?</h2><MeshDistinction/></section>
      <section id="calculs" className="doc-section"><h2>4. Quels calculs géographiques effectuons-nous ?</h2>
        <p>Les couches sont contrôlées puis projetées en Lambert-93. Le traitement calcule les intersections entre lignes et surfaces, mesure les longueurs ou aires selon la dimension obtenue et distingue une relation intérieure d’un contact sur la frontière. Il ne déplace pas les objets pour créer une relation.</p>
        <div className="v2-equation"><code>Sᵢ = aire(Hᵢ ∩ T)</code><p>Hᵢ est l’hexagone initial, T le territoire et Sᵢ la surface effectivement étudiée. Les morceaux extérieurs au territoire ne participent pas aux mesures.</p><FormulaProvenance kind="area"/></div>
        <div className="v2-equation"><code>pᵢ = 100 × aire((Hᵢ ∩ T) ∩ ⋃ Rⱼ) / Sᵢ</code><p>Rⱼ représente chaque réservoir cartographié. Leur union évite de compter deux fois une surface superposée. Cet indicateur de proportion n’est qualifié que si la complétude écologique est validée ; sinon il reste inconnu, même si une aire observée peut être mesurée.</p><FormulaProvenance kind="reservoir"/></div>
        <div className="v2-equation"><code>Σᵢ Nᵢ exclusif = |E| = 5 336</code><p>E est l’ensemble des relations géométriques admises. Chaque relation reçoit un secteur de comptage unique, choisi par la clé stable parmi les mailles admissibles, en privilégiant une relation intérieure. Les comptes locaux partagés totalisent 5 759 rattachements ; seuls les comptes exclusifs s’additionnent sans doublon.</p><FormulaProvenance kind="exclusive"/></div>
        <p>Les intersections normalisées et leurs sources sont dédoublonnées avant agrégation. Une même relation qui touche deux secteurs est visible dans les deux fiches, mais n’est comptée qu’une fois dans le total exclusif ; le rattachement choisi est déterministe et vérifiable. Les identifiants sources et géométries d’origine restent traçables. Parmi 5 337 relations détectées, une est conservée en quarantaine pour un échec de contrôle territorial ; elle n’entre pas dans les 5 336 admises.</p>
        <details><summary>Précision et contrôles numériques</summary><p>Les budgets numériques servent à détecter des résidus de calcul, sans constituer des seuils écologiques. La précision annoncée des haies est de 3 m ; celle des tracés régionaux est non renseignée. Aucun buffer de tolérance écologique ou seuil de micro-recouvrement n’est ajouté pour promouvoir une proposition.</p><p>Les contacts de frontière et les très petits recouvrements restent signalés. Les géométries invalides sont refusées, sans réparation automatique destinée à faire passer les contrôles.</p></details>
      </section>
      <section id="regles" className="doc-section"><h2>5. Comment une observation devient-elle une solution à étudier ?</h2>
        <p>La chaîne est explicite : observation localisée → hypothèse écologique → conditions propres à la famille → question d’étude. Pour chaque famille, le moteur retient le niveau d’ancrage satisfait, sans quota ni comparaison de bénéfice entre familles. Les trois niveaux de justification sont des heuristiques conçues par notre équipe ; aucune publication retrouvée ne prescrit ces sélecteurs.</p>
        <JustificationLevels/>
        <div className="v2-rule-grid">{FAMILY_RULES.map(([name,rule,check],index)=><article key={name}><h3>{name}</h3><p>{rule}</p><p className="v2-small-note">{check}</p><ScientificCitations ids={FAMILY_REFERENCES[index]}/></article>)}</div>
        <p>Le pilote produit 205 pistes sur 88 secteurs : 93 études étayées, 45 pistes à approfondir et 67 à explorer. 61 secteurs ont plusieurs pistes et 13 restent sans proposition. Une famille peut rester sans proposition faute d’objet admissible localisable, ou lorsque le statut connu contredit l’intervention envisagée, par exemple un site déjà reconverti. Ce résultat ne conclut pas à une absence écologique. Les observations communes sont signalées ; elles ne multiplient pas la force de preuve. Les familles restent non départagées et aucune action principale n’est imposée.</p>
      </section>
      <section id="priorite" className="doc-section"><h2>6. Que signifie la couleur d’une maille ?</h2>
        <p>La carte réutilise une politique M2 d’examen déjà calculée et versionnée, indépendante des solutions. Elle privilégie l’examen des interfaces routières ; elle n’est pas une mesure globale des quatre enjeux. Les conditions et la palette sont propres au projet. Le document régional fournit les objets et leurs attributs, pas cette règle de classement.</p><ScientificCitations ids={['srce','obstacles']}/>
        <ol className="v2-priority-rules"><li><strong>Secteur à examiner en priorité — 27 secteurs.</strong> Une route carrossable en service au sol rencontre une matrice régionale qualifiée de fragile et un réservoir présente une surface positive dans la maille.</li>
          <li><strong>Priorité d’examen élevée — 33 secteurs.</strong> Un croisement linéaire local route–espace de continuité est documenté, sans réunir tous les critères du premier groupe.</li>
          <li><strong>Priorité d’examen modérée — 9 secteurs.</strong> Des espaces régionaux présentent une surface positive, sans croisement routier retenu. Il s’agit d’un examen de préservation, sans preuve d’absence de fragmentation.</li>
          <li><strong>Informations insuffisantes — 32 secteurs.</strong> Les indices de cette politique ne sont pas réunis. D’autres pistes peuvent néanmoins être proposées à partir des haies, des friches ou des milieux humides.</li></ol>
        <p>Les règles utilisent la présence et la nature des relations, sans somme pondérée, quota, meilleur niveau de solution ou seuil sur le nombre d’intersections. Les vérifications contradictoires et les champs inconnus restent à résoudre : cette politique ne qualifie pas le fonctionnement écologique actuel.</p>
        <p><strong>Aucune classe verte n’est attribuée.</strong> Une faible priorité écologique n’est pas démontrée. Un véritable classement global multi-enjeux demanderait des méthodes d’enjeu adaptées, une qualification des pressions, la couverture des sources et des preuves comparables, puis une validation distincte. Les résultats historiques de priorité écologique restent indéterminés.</p>
      </section>
      <section id="exemple" className="doc-section"><h2>7. Un exemple réel, de la donnée aux quatre pistes</h2>
        {example?<div className="v2-real-example" data-example-sector={example.sector.number}>
          <h3>{example.sector.label}</h3>
          <ol><li><strong>Données localisées.</strong> Le secteur couvre {fmt(example.area_m2,2)} m² après découpe. Les inventaires y décrivent notamment {fmt(example.hedge_length_m,2)} m de haies et {fmt(example.wetland_area_m2,2)} m² de milieux humides inventoriés.</li>
            <li><strong>Relations contrôlées.</strong> {example.priority.evidence.nombre_paires_route_corridor_2d} couples distincts voie–espace régional sont retenus, dont {example.priority.evidence.paires_route_matrice_fragile_en_service_au_sol} réunissent les attributs de voie carrossable en service au sol et de matrice fragile. Ces couples ne sont pas des obstacles confirmés.</li>
            <li><strong>Couleur de la maille.</strong> L’examen est classé « {PRIORITY_LABELS[example.priority.color].toLocaleLowerCase('fr')} » : aucun réservoir n’y présente de surface positive dans les observations, donc tous les critères du premier groupe ne sont pas réunis.</li>
            <li><strong>Solutions indépendantes.</strong> {example.actions.map(a=>`${actionFamilyVisual(a.action_id).label} : ${LEVEL_NAMES[a.level].toLocaleLowerCase('fr')}`).join(' ; ')}. Leur niveau repose sur les preuves propres à chaque famille.</li>
          </ol><p className="scientific-numeric-example"><strong>Calcul de surface.</strong> L’intersection de l’hexagone et du territoire donne Sᵢ = {fmt(example.area_m2,2)} m², soit {fmt(example.area_m2/1_000_000,6)} km² (division par 1 000 000). C’est une mesure de découpe géographique ; les petites différences d’arrondi ne sont pas une précision écologique.</p><ScientificCitations ids={['intersection','srce']}/><a className="v2-method-link" href={'/?maille='+encodeURIComponent(example.maille_id)} onClick={linkClickHandler('/?maille='+encodeURIComponent(example.maille_id))}>Ouvrir la fiche de cet exemple</a>
        </div>:<><p role={error?'alert':'status'}>{error?'L’exemple réel est temporairement indisponible.':'Chargement de l’exemple depuis les données vérifiées…'}</p>{error&&<button onClick={()=>setRetry(v=>v+1)}>Réessayer l’exemple</button>}</>}
      </section>
      <section className="doc-section"><h2>8. Ce que les résultats permettent de conclure</h2>
        <p>Le traitement est opérationnel pour localiser des relations, conserver leurs sources et produire des questions d’étude reproductibles. Il ne mesure pas l’efficacité d’un futur aménagement, la mortalité de la faune ou l’urgence temporelle de travaux.</p>
        <p>Avant une réalisation, il faut actualiser les observations, préciser les habitats et les espèces, examiner les ouvrages, l’hydrologie, les usages et le foncier selon la solution, puis confirmer le besoin et la faisabilité avec les responsables écologiques et techniques.</p>
      </section>
      <section id="references" className="doc-section"><h2>9. Références d’appui vérifiées</h2>
        <ScientificBibliography/>
      </section>
      <details className="doc-section v2-method-technical"><summary>Traçabilité et reproduction pour l’équipe</summary>
        <p>Les fichiers scellés conservent les données exactes, les versions, les identifiants, les résultats historiques et les empreintes. Ils restent accessibles à l’équipe dans ses ressources internes, sous les restrictions de diffusion existantes.</p>
        <p>Les équations correspondent aux fonctions de découpage et d’indicateurs, de détection et d’agrégation du code M2. Les règles familiales et leur vérificateur sont testés séparément de la politique d’examen territorial. La matrice docs/TRACABILITE_SCIENTIFIQUE_20261115.md relie chaque indicateur et famille au code, aux données et aux références, distingue les méthodes non appliquées et décrit un calcul réel reproductible, sans publier les lots.</p>
        <p>Cette version reste réservée à la revue locale ; elle n’autorise pas la publication des données internes.</p>
      </details>
    </main>
  </div>
}
