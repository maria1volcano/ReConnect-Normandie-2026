import { SiteHeader } from '../components/layout/SiteHeader'
import { linkClickHandler } from '../app/router'

const STAGES = [
  {
    n: '01',
    title: 'Acquisition des données',
    text: 'Collecte des couches publiques : BD TOPO 3.5 (IGN), occupation du sol OCS GE 2.0, SRCE Basse-Normandie (DREAL), inventaires haies, friches et zones humides.',
  },
  {
    n: '02',
    title: 'Reprojection et normalisation',
    text: 'Reprojection en EPSG:2154 (RGF93 / Lambert-93), contrôle des CRS déclarés, harmonisation des attributs et des emprises.',
  },
  {
    n: '03',
    title: 'Génération de la grille géographique',
    text: 'Tessellation hexagonale « flat-top » couvrant les six communes, version M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1, emprise nominale 1 km² par cellule.',
  },
  {
    n: '04',
    title: 'Détection des intersections géométriques',
    text: 'Intersection spatiale entre tronçons routiers et linéaires de matrices écologiques SRCE (croisements 2D), puis association de chaque événement aux mailles concernées.',
  },
  {
    n: '05',
    title: 'Propriété canonique et dédoublonnage',
    text: 'Chaque observation source est rattachée à un événement canonique unique ; les doublons inter-sources sont fusionnés sans supprimer les phénomènes distincts.',
  },
  {
    n: '06',
    title: 'Indicateurs et contrôles qualité',
    text: 'Comptages d’événements locaux et canoniques, mesures observées par source (routes, haies, plans d’eau…), indicateurs ENJ-01/ENJ-02 et vérifications de complétude.',
  },
  {
    n: '07',
    title: 'Classification documentaire',
    text: 'Attribution d’un niveau V1–V4 par maille selon les règles de la table de triage exploratoire (voir section ci-dessous).',
  },
  {
    n: '08',
    title: 'Fiches territoriales',
    text: 'Production d’une fiche par maille : niveau documentaire, motif, observations géométriques, municipalités et limites.',
  },
  {
    n: '09',
    title: 'Pistes d’investigation',
    text: 'Génération des pistes R1–R4 associées à A04/A01/A03/A02 pour les mailles concernées, toutes au statut « à étudier ».',
  },
  {
    n: '10',
    title: 'Restitution cartographique',
    text: 'Export public minimisé (grid.geojson + cells.json) consommé par l’application, conformément au manifeste de publication.',
  },
]

const SOURCES = [
  {
    source: 'SRCE — Réservoirs et corridors de biodiversité, Basse-Normandie',
    producer: 'DREAL Normandie',
    vintage: 'Référentiel 2014, publié 15/11/2024',
    licence: 'Licence Ouverte 2.0',
    limit: 'Données de 2014 ; le tracé ne prouve pas une fonctionnalité actuelle.',
  },
  {
    source: 'BD TOPO 3.5 — tronçons de route',
    producer: 'IGN',
    vintage: 'Livraison M1 du 11/11/2026 ; millésimes objets variables ou NULL',
    licence: 'Licence Ouverte 2.0',
    limit: 'Champ état renseigné inégalement ; la présence d’un tronçon ne vaut pas trafic constaté.',
  },
  {
    source: 'OCS GE 2.0 — occupation du sol',
    producer: 'IGN / DGALN',
    vintage: 'Millésime D014-2023',
    licence: 'Licence Ouverte 2.0',
    limit: 'Occupation du sol, pas une cartographie de sensibilité écologique.',
  },
  {
    source: 'BD TOPO — haies et plans d’eau',
    producer: 'IGN',
    vintage: 'Livraison M1 du 11/11/2026 ; millésimes objets variables ou NULL',
    licence: 'Licence Ouverte 2.0',
    limit: 'Exhaustivité écologique non validée. Les plans d’eau ne sont pas automatiquement des mares ; zéro observation ne démontre pas une absence.',
  },
  {
    source: 'Cartofriches — sites référencés',
    producer: 'Cerema',
    vintage: 'Mise à jour ~trimestrielle',
    licence: 'Licence Ouverte 2.0',
    limit: 'Inventaire non exhaustif ; les sites restent à confirmer.',
  },
  {
    source: 'SIPAF — complément à consulter',
    producer: 'MTE / Cerema / Parcs nationaux',
    vintage: 'Non fourni dans ce lot Caen',
    licence: 'Licence Ouverte 2.0 (données diffusables)',
    limit: 'Aucun ouvrage de ce référentiel n’est utilisé comme observation dans ce lot.',
  },
]

const LIMITS = [
  'Une intersection géométrique route–matrice ne démontre pas une rupture écologique : elle signale un point à vérifier.',
  'Les données SRCE datent de 2014 : l’occupation du sol et les continuités ont pu changer depuis.',
  'Les inventaires (haies, friches, mares, passages à faune) sont nécessairement incomplets.',
  'Les priorités écologiques restent indéterminées : aucune méthode de connectivité n’a été validée sur ce territoire.',
  'Les couleurs V1–V4 orientent les priorités indicatives d’étude lorsque les décisions du nouveau lot sont disponibles ; elles ne valident pas une priorité écologique.',
]

export function MethodePage() {
  return (
    <div className="application-shell">
      <SiteHeader />
      <main className="doc-page" id="main-content">
        <section className="doc-hero">
          <p className="context-label">M1 · M2 · M3 · M4</p>
          <h1>Méthode — du croisement cartographique aux actions à étudier</h1>
          <p className="doc-lede">
            Cette page décrit la chaîne de traitement réellement mise en œuvre pour produire la carte
            des 101 mailles et les fiches de vérification. Elle distingue explicitement ce que le
            pipeline établit — des indices documentaires — de ce qu’il n’établit pas : des
            priorités écologiques validées.
          </p>
          <a className="analysis-jump" href="/" onClick={linkClickHandler('/')}>
            ← Retour à la carte
          </a>
        </section>

        <section className="doc-section">
          <h2>1. Problème et objectif</h2>
          <p>
            Le projet ReConnect Normandie réalise un <strong>prédiagnostic exploratoire des
            continuités écologiques</strong> sur le territoire Caen et nord des six communes. Il
            croise les infrastructures linéaires (routes) avec les trames écologiques cartographiées
            (SRCE, occupation du sol, inventaires thématiques) pour identifier les secteurs où une
            étude d’une action peut être instruite en premier.
          </p>
          <p>
            L’application aide à choisir les premières interventions à étudier : passage de la faune en rouge et orange, préservation à examiner en jaune, décision non évaluable en gris. Le rang d’étude reste indicatif et distinct de la priorité écologique D/S. Aucun aménagement n’est prescrit sans validation écologique et technique.
          </p>
        </section>

        <section className="doc-section">
          <h2>2. Périmètre géographique</h2>
          <ul className="doc-facts">
            <li><strong>Communes :</strong> Caen, Ouistreham, Bénouville, Blainville-sur-Orne, Colombelles, Hérouville-Saint-Clair.</li>
            <li><strong>Grille :</strong> 101 cellules hexagonales « flat-top » jointives, version M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1.</li>
            <li><strong>Projection de calcul :</strong> EPSG:2154 (RGF93 / Lambert-93) ; sorties GeoJSON en CRS84.</li>
            <li><strong>Résolution :</strong> emprise nominale 1 km² par cellule ; les mailles de bordure sont des fragments d’hexagone et leurs surfaces réelles varient.</li>
          </ul>
        </section>

        <section className="doc-section">
          <h2>3. Sources de données</h2>
          <div className="doc-table-wrap">
            <table className="doc-table">
              <thead>
                <tr><th>Source</th><th>Producteur</th><th>Millésime</th><th>Licence</th><th>Limite connue</th></tr>
              </thead>
              <tbody>
                {SOURCES.map((s) => (
                  <tr key={s.source}>
                    <td>{s.source}</td><td>{s.producer}</td><td>{s.vintage}</td>
                    <td>{s.licence}</td><td>{s.limit}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="doc-note">Inventaire complet et vérifications : <code>docs/inventaire_sources.csv</code>.</p>
        </section>

        <section className="doc-section">
          <h2>4. Chaîne de traitement M1 → M2</h2>
          <ol className="doc-stages">
            {STAGES.map((stage) => (
              <li key={stage.n}>
                <span className="stage-num">{stage.n}</span>
                <div><strong>{stage.title}</strong><p>{stage.text}</p></div>
              </li>
            ))}
          </ol>
        </section>

        <section className="doc-section">
          <h2>5. Classification documentaire V1–V4 — règles exactes</h2>
          <p>
            La couleur de chaque maille vient de la table de triage exploratoire
            (<code>docs/table_triage_exploratoire.json</code>, version
            « m2-annotation-documentaire-caen-nord-0.1 »). Il s’agit d’un{' '}
            <strong>classement cartographique utilisé pour orienter les études, distinct de la priorité écologique</strong> : aucun seuil
            d’événements, aucun score écologique, aucune équivalence avec les classes D/S.
          </p>
          <div className="v-rules">
            <div className="v-rule v-rule--rouge">
              <h3>V1 — Rouge : croisement à examiner en priorité</h3>
              <p>Une route carrossable <strong>en service au sol</strong> intersecte linéairement une matrice fragile, et un réservoir de surface positive est présent dans la même maille.</p>
            </div>
            <div className="v-rule v-rule--orange">
              <h3>V2 — Orange : autre croisement route–matrice</h3>
              <p>Intersection linéaire route–matrice documentée qui ne remplit pas la double condition de V1.</p>
            </div>
            <div className="v-rule v-rule--jaune">
              <h3>V3 — Jaune : signal de présence sans croisement routier</h3>
              <p>Aucun croisement routier 2D observé, mais présence positive de matrice ou de réservoir sur la maille.</p>
            </div>
            <div className="v-rule v-rule--gris">
              <h3>V4 — Gris : aucun signal suffisant</h3>
              <p>Aucun des signaux ci-dessus n’est détecté dans les sources mobilisées pour cette maille.</p>
            </div>
          </div>
          <p className="doc-note">
            Comportement en cas de données manquantes : une maille sans observation route–matrice ni
            surface matrice/réservoir bascule en V4 ; la présence d’une couche absente n’est jamais
            interprétée comme une absence prouvée. La règle est évaluée par maille, avec priorité à
            V1, puis V2, V3, V4.
          </p>
        </section>

        <section className="doc-section">
          <h2>6. Exemple traçable — une maille V1 réelle</h2>
          <div className="doc-example">
            <p><strong>Maille :</strong> <code>NORM-G1K-FLAT-R+006422-C+000487</code> (Caen)</p>
            <p><strong>Niveau :</strong> V1 / rouge — « Plusieurs indices cartographiques à vérifier »</p>
            <p><strong>Motif enregistré :</strong> « Au moins un croisement route en service au sol–matrice SRCE fragile, et une surface de réservoir cartographiée dans cette maille. Leur coexistence ne démontre pas une rupture écologique. »</p>
            <p><strong>Observations :</strong> 88 paires de croisement route–corridor en 2D ; 45 paires route–matrice fragile « en service au sol » ; présence de réservoir et de corridor à surface positive ; 89 événements locaux canoniques ; 52 haies et ~6 606 m de routes observés. Cette maille porte les quatre pistes R1–R4.</p>
          </div>
          <p className="doc-note">
            Exemple tiré directement des données publiques (<code>cells.json</code>) — aucune mesure
            n’a été ajoutée ni extrapolée.
          </p>
        </section>

        <section className="doc-section">
          <h2>7. Résultats et comptages</h2>
          <ul className="doc-facts">
            <li><strong>101</strong> cellules géographiques couvertes.</li>
            <li><strong>5 337</strong> événements détectés, dont <strong>5 336</strong> admis et <strong>1</strong> mis en quarantaine.</li>
            <li><strong>5 759</strong> relations maille–événement : un même événement canonique peut concerner plusieurs mailles (bords partagés, recouvrements), d’où un nombre de relations supérieur au nombre d’événements uniques.</li>
            <li><strong>60</strong> mailles avec au moins une observation enregistrée.</li>
            <li><strong>404</strong> évaluations R1–R4 (101 mailles × 4 règles), toutes non évaluables faute de méthode familiale validée.</li>
            <li><strong>165</strong> pistes d’investigation au statut « à étudier » (R1/A04 : 60 · R2/A01 : 50 · R3/A03 : 35 · R4/A02 : 20).</li>
            <li><strong>0</strong> recommandation écologique validée.</li>
          </ul>
          <p className="doc-note">
            Événements uniques ≠ relations maille–événement : la déduplication canonique se fait au
            niveau de l’événement, tandis qu’une maille peut héberger plusieurs événements et un
            événement peut en toucher plusieurs.
          </p>
        </section>

        <section className="doc-section">
          <h2>8. Limites scientifiques</h2>
          <ul className="doc-limits">
            {LIMITS.map((limit) => <li key={limit}>{limit}</li>)}
          </ul>
        </section>

        <section className="doc-section">
          <h2>9. Transparence méthodologique</h2>
          <p>
            Sources de référence dans le dépôt : <code>docs/methode_m2.md</code> (validation SIG et
            niveaux de preuve), <code>docs/regles_actions_m2.md</code> et{' '}
            <code>docs/rules_actions.json</code> (spécification R1–R4, statut « proposition non
            approuvée »), <code>docs/table_triage_exploratoire.json</code> (règles V1–V4),{' '}
            <code>docs/PUBLIC_RELEASE_MANIFEST.json</code> (autorisation et contenu de l’export
            public). Les scripts de traitement M1/M2 sont versionnés dans les branches{' '}
            <code>feat/m1-donnees-sig-v61</code> et <code>feat/diagnostics-ecologiques</code>.
          </p>
          <p>
            <a className="analysis-jump" href="/catalogue" onClick={linkClickHandler('/catalogue')}>
              Consulter le catalogue des pistes d’investigation →
            </a>
          </p>
        </section>
      </main>
    </div>
  )
}
