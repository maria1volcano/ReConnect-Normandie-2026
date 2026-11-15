import { SiteHeader } from '../components/layout/SiteHeader'
import { linkClickHandler } from '../app/router'
import { isHistoricalReview } from '../integrations/historicalReview'
import { HistoricalMethodePage } from './HistoricalMethodePage'
import { ScientificFoundations, ScientificCitations, MeshDistinction, FormulaProvenance, ScientificBibliography } from '../components/method/ScientificBasis'

export function MethodePage() {
  if(isHistoricalReview())return <HistoricalMethodePage/>
  return <div className="application-shell"><SiteHeader/>
    <main className="doc-page" id="main-content">
      <section className="doc-hero"><p className="context-label">Comprendre les données publiées</p><h1>Méthode — du croisement cartographique aux actions à étudier</h1>
        <p className="doc-lede">ReConnect Normandie croise des données sur les milieux et les activités humaines pour repérer des relations spatiales et poser des questions d’étude. Cette page décrit l’export actuellement autorisé ; le nouveau parcours multi-actions reste distinct, en revue locale.</p>
        <a className="analysis-jump" href="/" onClick={linkClickHandler('/')}>Retour à la carte</a>
      </section>
      <ScientificFoundations/>
      <section className="doc-section"><h2>Le territoire et les données</h2><p>Le pilote couvre Caen, Bénouville, Blainville-sur-Orne, Colombelles, Hérouville-Saint-Clair et Ouistreham. Il ne couvre pas l’ensemble de la Normandie.</p>
        <ul><li><a href="https://www.data.gouv.fr/datasets/bd-topo-r">IGN, BD TOPO</a> : voies, haies et plans d’eau observés ; les dates et la qualité varient selon les objets.</li>
          <li><a href="https://www.normandie.developpement-durable.gouv.fr/les-schemas-regionaux-de-coherence-ecologique-srce-a3638.html">DREAL Normandie, schéma régional des continuités écologiques</a> : espaces et réservoirs, référence 2014.</li>
          <li><a href="https://www.data.gouv.fr/datasets/zones-humides-normandie">DREAL, inventaires de milieux humides</a> et <a href="https://www.data.gouv.fr/datasets/sites-references-dans-cartofriches">Cerema, Cartofriches</a> : localisation et contexte, à actualiser.</li>
          <li>IGN, limites administratives et occupation du sol : emprise des communes et contexte du sol. La végétation cartographiée ne démontre pas une continuité fonctionnelle.</li></ul><p>Le cadrage régional au 1/100 000 ne gagne pas de précision lorsqu’on le découpe en petits secteurs.</p><ScientificCitations ids={['srce']}/>
      </section>
      <section className="doc-section"><h2>Des opérations géographiques reproductibles</h2><p>Les calculs utilisent Lambert-93, un système métrique. Des hexagones de 1 km² avant découpe sont intersectés avec le territoire ; les 101 secteurs conservent leur surface réelle, y compris en bordure.</p><MeshDistinction/>
        <p><code>Sᵢ = aire(Hᵢ ∩ T)</code> : la surface étudiée est celle de l’hexagone Hᵢ à l’intérieur du territoire T.</p><FormulaProvenance kind="area"/>
        <p><code>pᵢ = 100 × aire((Hᵢ ∩ T) ∩ union(Rⱼ)) / Sᵢ</code> : les surfaces des réservoirs Rⱼ sont réunies avant mesure pour éviter les doubles comptes. Cette proportion n’est qualifiée que si la complétude écologique est validée ; sinon elle reste inconnue.</p><FormulaProvenance kind="reservoir"/>
        <p><code>somme des comptes exclusifs = 5 336</code> : chaque relation admise est comptée dans un seul secteur. Les rattachements locaux peuvent être partagés et totalisent 5 759 associations.</p><FormulaProvenance kind="exclusive"/>
        <p>Les intersections entre lignes et surfaces sont distinguées des simples contacts de frontière. Les sources et géométries normalisées sont dédoublonnées. Une des 5 337 relations détectées reste en quarantaine et n’entre pas dans les comptes admis.</p>
      </section>
      <section className="doc-section"><h2>Comprendre les couleurs</h2><p>La couleur donne un ordre indicatif d’examen centré sur les interfaces routières. Elle ne mesure ni une urgence de travaux ni l’ensemble des enjeux écologiques.</p>
        <ul><li><strong>Secteur à examiner en priorité :</strong> voie carrossable en service au sol rencontrant une matrice fragile, avec une surface de réservoir dans le secteur.</li>
          <li><strong>Priorité d’examen élevée :</strong> autre croisement linéaire documenté entre voie et espace de continuité.</li>
          <li><strong>Priorité d’examen modérée :</strong> espace régional présent sans croisement routier retenu ; sa préservation reste à examiner.</li>
          <li><strong>Informations insuffisantes :</strong> les indices de cette méthode ne sont pas réunis. Cela ne démontre pas une faible valeur écologique.</li></ul>
        <p>Aucune classe verte n’est attribuée sans méthode permettant de justifier une faible priorité d’examen. Les couleurs ne sont pas déduites du nombre de solutions. Les conditions et la palette sont des choix méthodologiques de l’équipe ; aucune publication retrouvée ne prescrit ce classement.</p><ScientificCitations ids={['srce','obstacles']}/>
      </section>
      <section className="doc-section"><h2>Des observations aux pistes d’action</h2><p>Les passages pour la faune, les haies, les friches et les milieux humides sont examinés séparément. La localisation d’un élément peut motiver une étude ; elle ne confirme pas une dégradation ni la nécessité d’un aménagement.</p>
        <p>L’export public conserve 404 examens de familles, dont 165 pistes historiques à étudier. Les nouvelles catégories de justification du parcours multi-actions local ne sont pas reconstituées à partir de cet ancien export.</p>
        <p>Une observation commune à plusieurs pistes ne constitue pas plusieurs preuves indépendantes. Les diagnostics et les observations exactes sont conservés pour permettre la vérification.</p>
        <details className="scientific-families"><summary>Fondements propres aux quatre familles</summary>
          <h3>Franchissements pour la faune</h3><p>Les croisements géographiques motivent l’examen des ouvrages et des déplacements réels ; ils ne suffisent pas à confirmer un obstacle.</p><ScientificCitations ids={['passages','obstacles']}/>
          <h3>Haies</h3><p>Une haie localisée appelle d’abord un examen de son état et de sa gestion. Le projet ne calcule pas un déficit de haies.</p><ScientificCitations ids={['haies']}/>
          <h3>Milieux humides</h3><p>Les présences et recouvrements inventoriés appellent un diagnostic hydrologique. Aucun réseau déficitaire de mares n’est déduit.</p><ScientificCitations ids={['tvb','mares','srce']}/>
          <h3>Friches</h3><p>La relation cartographique permet d’interroger le devenir d’un site ; ses habitats, ses sols et les projets connus restent à vérifier.</p><ScientificCitations ids={['renaturation','friches']}/>
        </details>
      </section>
      <section className="doc-section"><h2>Un exemple vérifiable</h2><p className="scientific-numeric-example">La découpe d’un secteur de Caen produit une surface Sᵢ de 727 382,81 m² : 727 382,81 ÷ 1 000 000 ≈ 0,727383 km², au lieu de 1 km² pour l’hexagone complet. Ce calcul formalise l’intersection géographique décrite plus haut ; il ne mesure pas une connectivité fonctionnelle.</p><ScientificCitations ids={['intersection','srce']}/><p>Dans un secteur de Caen, 88 couples voie–espace de continuité sont documentés, dont 45 associent une voie en service au sol à une matrice fragile. Une surface de réservoir est aussi observée : ces conditions expliquent le premier groupe d’examen.</p>
        <p>Ces couples ne représentent pas 88 obstacles ou projets de travaux. La fiche conserve 89 relations locales et les sources associées ; une relation peut avoir plusieurs rattachements. L’identifiant de l’exemple et les commandes de vérification sont disponibles dans la documentation de l’équipe.</p>
      </section>
      <section className="doc-section"><h2>Limites et vérifications</h2><p>La géométrie ne mesure pas le passage réel de la faune, l’efficacité des travaux ou leur urgence. Les inventaires peuvent être incomplets et les tracés anciens ; l’absence d’un objet observé ne prouve pas son absence réelle.</p><p>Les priorités écologiques historiques restent indéterminées. Les calculs géographiques et les règles documentaires sont opérationnels ; les décisions de réalisation demandent une confirmation écologique et technique locale.</p></section>
      <section className="doc-section"><h2>Références et reproduction</h2><p>Les scripts de découpage, d’indicateurs, de détection et d’agrégation sont testés séparément des règles d’étude. Les sources, identifiants et versions exactes restent conservés dans la documentation technique de l’équipe.</p>
        <ScientificBibliography/>
      </section>
    </main>
  </div>
}
