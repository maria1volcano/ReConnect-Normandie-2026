# Traçabilité scientifique de ReConnect Normandie

Audit du 15 novembre 2026. Complément documentaire à la finalisation du MVP ; aucun résultat, sélecteur, contrat ou lot n’a été modifié. Les pages Méthode du frontend local présentent ces distinctions. Ce document est destiné à l’équipe et au jury ; ses identifiants techniques ne sont pas ajoutés aux cartes d’action.

## Conclusion de l’audit

Le pilote programme des opérations SIG de localisation, intersection, mesure et comptage. Les sources publiques fournissent des objets et leurs attributs. Les publications éclairent l’interprétation écologique et les vérifications à mener. Les règles d’examen territorial et les sélecteurs A/B/C sont des conventions de l’équipe, sans calibration écologique publiée ni validation institutionnelle retrouvée.

Les méthodes de fragmentation de Jaeger (2000), du SDES (2026, correction des limites de Moser), la priorisation nationale du Cerema (2026) et la notation de renaturation du Cerema (2022) **ne sont pas reproduites ni adaptées dans le code audité**. Le réemploi des couches régionales ne constitue pas une reproduction de leur méthode de construction. Un hexagone nominal de 1 km² est une unité d’observation, pas une taille effective de maille.

Le diagnostic repose sur `analysis/indicateurs_enjeux.py`, `detect_conflicts.py`, `aggregate_conflicts.py`, `preparer_caen_et_nord.py`, `livrer_caen_et_nord.py`, `auditer_multiactions_caen.py`, `moteur_multiactions_experimental.py`, `moteur_multiactions_experimental_v2.py`, `construire_fiches_66.py` et `prioriser_etudes_interventions.py`. Les références ont été confrontées à `docs/methode_m2.md` (« Références examinées et portée de cette adaptation »), `docs/regles_actions_m2.md` (§9 et tableau de portée), aux rapports V2, au catalogue scellé des sources et aux lots réellement chargés.

Dans ce document, les chemins `analysis/…`, `tests/…` et les anciens documents M2 se rapportent au dépôt scientifique voisin `../Datathon-normandie-2026`, audité en lecture seule. Les nouveaux fichiers frontend et ce rapport appartiennent exclusivement à `reconnect-actions-ui`. Le frontend n’exécute aucun de ces traitements scientifiques.

## Nature des justifications

| Catégorie demandée | Constat vérifié |
| --- | --- |
| Méthode scientifique reproduite | Aucune des méthodes publiées citées n’est reproduite dans ce pilote. |
| Méthode scientifique adaptée | Aucune adaptation mathématique de ces indices ou scores n’est établie par le code. « S’inspirer d’un principe » n’est pas une adaptation de méthode. |
| Principe scientifique utilisé comme justification | Continuités nécessaires aux cycles de vie ; effets possibles des infrastructures ; intérêt de la gestion des haies, des réseaux humides et des habitats des friches. Voir les références propres à chaque ligne. |
| Choix méthodologique propre à l’équipe | Grille, qualification conditionnelle des observations, comptage exclusif, règles territoriales, hiérarchie des preuves et sélecteurs A/B/C. Les opérations géométriques sous-jacentes sont des opérations SIG standard. |
| Source documentaire encore non retrouvée | Aucun protocole scientifique retrouvé ne prescrit nos seuils logiques de sélection, notre palette, le choix du propriétaire canonique ou ne valide les 205 pistes. Les besoins de validation sont explicités ci-dessous. |

## Matrice indicateur → code → référence → données

Les clés bibliographiques renvoient à la bibliographie complète en fin de document. « Appui de principe » signifie que la référence justifie la question écologique ; elle ne prescrit pas la règle exécutée.

| Élément du projet et phénomène | Méthode implémentée et code | Source scientifique ou méthodologique | Source des données réellement chargées | Adaptation de l’équipe et limites |
| --- | --- | --- | --- | --- |
| Découpage territorial | `preparer_caen_et_nord.grid()` réutilise `regular_hexagon()` du générateur M1 dans `tests/fixtures/m1_grid_v61/generate_hex_grid.py`, puis intersecte l’union des communes ; `compute_enjeux()` conserve la partie polygonale. | `intersection` : documentation SIG ; `sdes`, `jaeger` : comparaison uniquement, indices non appliqués. | IGN ADMIN EXPRESS, six communes, Lambert-93 ; grille nominale de 1 000 000 m². | **Choix d’équipe** : orientation flat-top, origine et dimension ; aucune frontière écologique présumée. 101 secteurs, 67 partiels. Le changement d’échelle n’améliore pas les sources. |
| Aire et proportion de réservoir | `indicateurs_enjeux.compute_enjeux()` : aire de l’intersection avec l’union des réservoirs ; `_checked_proportion()` contrôle le ratio ; `_fully_covered()` conditionne sa qualification. | `union`, `intersection` : opérations techniques standard ; `srce` : sens des réservoirs. Aucun étalonnage de qualité écologique. | 41 réservoirs régionaux DREAL, référence 2014 ; limites et grille IGN. | **SIG standard + choix d’équipe** : union évitant le double compte, aire en m², ratio en %, uniquement si complétude validée. L’aire observée peut être positive alors que la proportion qualifiée reste inconnue. Ce ratio n’est ni une connectivité ni un score de qualité. |
| Présence et mesures de corridors | `_observed_corridors()` : union séparée des lignes et polygones, exclusion des lignes sur la frontière ; `_presence()` : observation positive, absence seulement si couverture validée, sinon inconnu. | `srce` : réservoirs, matrices et cadrage ; `intersection`, `union` : calculs. | 40 objets régionaux DREAL retenus dans le pilote, référence 2014. | **SIG standard + convention d’équipe** : conserver m et m² séparés. Une matrice régionale ne démontre pas un corridor fonctionnel local. Le pilote chargé est polygonal ; le code général accepte aussi des lignes. |
| Relations routières et fragmentation potentielle | `detect_conflicts.detect_route_corridor_conflicts()` : intersections 2D et dimension ; `_source_groups()` normalise géométries/attributs et dédoublonne les sources ; `livrer_caen_et_nord.main()` reconstitue les couples distincts route–matrice associés aux événements admis. | `tvb`, `passages`, `obstacles` : **appui de principe** ; `sdes` et `jaeger` ne fournissent pas le calcul utilisé. `intersection` documente la géométrie. | 17 335 tronçons IGN BD TOPO ; matrices régionales DREAL ; attributs catégorie, statut et position au sol. | **Traitement SIG + conventions d’équipe**. Un couple documentaire, un événement géométrique et un obstacle écologique sont des objets distincts. Sans espèces, trafic et ouvrages qualifiés, aucune fragmentation fonctionnelle ni mortalité n’est mesurée. |
| Relations locales et comptage exclusif | `aggregate_conflicts.aggregate_conflicts()` et `_interior_relation()` : toutes les mailles réellement intersectées sont liées ; un propriétaire déterministe est retenu parmi les relations intérieures, ou à défaut les contacts frontaliers. | `intersection` : technique ; **aucune source scientifique retrouvée** ne prescrit le propriétaire par plus petite clé canonique. | Événements canoniques admis et grille découpée. | **Choix d’équipe** pour l’additivité : 5 336 événements exclusifs, 5 759 associations locales. Une relation détectée sur 5 337 reste en quarantaine. Ni proximité, ni centroïde, ni déplacement ne remplacent une intersection manquante. |
| Mesures locales de haies et autres objets | `livrer_caen_et_nord.main()` : découpe par secteur ; longueur sommée des objets linéaires, aire de l’union pour les polygones ; nombre d’objets à mesure positive. | `intersection`, `union` : calculs ; `haies` : interprétation de gestion. | BD TOPO, DREAL, Cartofriches ; catalogue de chaque couche conservé dans le lot. | **SIG standard + convention d’agrégation**. La longueur des haies de la fiche est une somme des tronçons découpés, pas une mesure de densité de réseau ni une union topologique. Ne pas lui appliquer automatiquement la formule d’union des réservoirs. |
| Franchissements pour la faune | `moteur_multiactions_experimental_v2.choose('routier',…)` : A si couple canonique carrossable, en service, au sol ; B autre couple local ; C coprésence territorialisée de route en service et élément régional. Les preuves sont locales et positives. | `passages` et `obstacles` : **appui de principe** aux études des ouvrages et des espèces ; protocole de sélecteur A/B/C non retrouvé. | Couples canoniques et preuves de présence BD TOPO/DREAL ; `presence_proofs()` et moteur V1 `make_proofs()` assurent les liens aux sources. | **Heuristique d’équipe**, sans note nationale de transparence, choix d’ouvrage ou obstacle confirmé. A n’impose pas la classe « fragile », contrairement au premier groupe territorial. Vérifier ouvrages existants, espèces/déplacements et perméabilité réelle. |
| Continuités bocagères | `auditer_multiactions_caen.audit()` et `local_relation()` : contacts haie–route et intersections haie–élément régional ; `choose('bocager',…)` : A contact haie–route carrossable en service au sol, B autre relation admise, C haie localisée. | `haies` et `srce` : **appui de principe** ; aucun seuil fonctionnel de lacune ou de densité transposé. | 879 haies BD TOPO, routes BD TOPO, matrices/réservoirs DREAL. | **Heuristique d’équipe**. Le régional n’est pas obligatoire pour A. Contact ponctuel intérieur possible, sans prouver une rupture ; précision annoncée des haies 3 m, précision régionale non renseignée. Vérifier structure/continuité réelle, habitats et gestion. |
| Milieux humides | Audit des surfaces communes eau–élément régional, eau–zone humide et zone humide–réservoir typé « Milieu humide » ; `choose('humide',…)` : A plan d’eau typé dans l’une des deux premières relations, B autres recouvrements admis, C présence de plan d’eau ou objet humide. | `tvb`, `srce` : **appui de principe** aux réseaux humides ; `mares` : retour d’expérience seulement. Protocole local de déficit de mares non retrouvé et non appliqué. | 5 plans d’eau BD TOPO ; 172 éléments des inventaires humides DREAL ; réservoirs/matrices DREAL, attributs diagnostic, qualité et typologie conservés. | **Heuristique d’équipe**. Un plan d’eau n’est pas assimilé à une mare ; une zone inventoriée peut être ambiguë ou remblayée. Aucun rayon de dispersion, déficit ou site de création calculé. Vérifier nature du milieu, alimentation en eau et réseau/habitats existants. |
| Friches | Audit des aires friche–élément régional ; `choose('friches',…)` : A site typé, au statut source « friche avec projet » ou « friche sans projet », avec recouvrement local ; B même relation sans type ; C présence au statut admissible ou inconnu. Les sites uniquement reconvertis ne déclenchent pas cette piste. | `renaturation`, `friches` : **appui de principe** aux fonctions des sols, habitats et projets ; notation parisienne non appliquée. | 77 sites Cartofriches Cerema au total, y compris sites reconvertis ; type, statut et date d’actualisation source ; éléments DREAL. | **Heuristique d’équipe**. Ni disponibilité foncière, ni pollution, ni éligibilité, ni besoin de renaturation déduits. Vérifier statut/projet actuel, habitats à conserver et sols/foncier. |
| Priorité territoriale d’examen | `construire_fiches_66.color_rule()` ; appliquée aux observations dans `livrer_caen_et_nord.main()` ; référence conservée et contrôlée par `prioriser_etudes_interventions.validate_reference()` / `decide()`. Rouge : paire admissible avec matrice fragile et réservoir à aire positive ; orange : autre paire linéaire ; jaune : surface régionale positive sans paire ; gris : critères insuffisants. | `srce`, `tvb`, `obstacles` : **appui écologique de principe**, aucune source retrouvée prescrivant cette table ou cette palette. | Paires route/matrice, attributs BD TOPO/DREAL, aires observées de matrices/réservoirs. | **Règle d’équipe** indépendante du meilleur niveau des solutions, sans poids, quota ni seuil de nombre de paires. Répartition 27/33/9/32 ; pas de vert. Ordre d’examen routier, ni urgence, ni priorité de travaux, ni évaluation globale des quatre enjeux. |
| Niveaux de justification A/B/C | `choose()` retient A, sinon B, sinon C, sinon non sélectionnée ; `evaluate()` et `build_cell()` constituent les fiches et gardent les familles non départagées. Le frontend traduit les niveaux en « Étude étayée », « À approfondir », « À explorer ». | **Source documentaire prescrivant ces niveaux non retrouvée**. Les références familiales soutiennent la question, pas la classification. | Preuves d’objets et relations auditées liées aux sources et aux mailles. | **Heuristique d’équipe**, sans probabilité, gain écologique, urgence ou action principale. 205 propositions : 93 A, 45 B, 67 C ; 88 secteurs avec piste, 61 avec plusieurs, 13 sans. Les preuves partagées ne sont pas indépendantes. A ne valide pas des travaux. |
| Occupation du sol et artificialisation | `auditer_multiactions_caen.audit()` conserve les recouvrements de stock artificialisé avec le régional ; les quatre sélecteurs V2 ne sélectionnent pas une action à partir de cette seule relation. | `renaturation` : contexte sur les sols, sans score transposé. | IGN OCS GE, millésime 2023, tables occupation et artificialisation. | **Choix de contexte documentaire**. Ne pas confondre stock et flux, végétation et habitat naturel, recouvrement et cause démontrée. |
| Résultats écologiques historiques | États conservés, aucune activation de règle écologique à partir d’une couleur ou d’un sélecteur exploratoire. | Aucune validation écologique supplémentaire retrouvée. | Résultats M2 historiques scellés. | 101 priorités écologiques indéterminées ; règles historiques non évaluables. Une carte techniquement vérifiée ne valide pas son fonctionnement écologique. |

## Provenance des données et dates

Le fichier scellé `provenance/sources_licences.json` du lot `RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1` donne les producteurs, URL de métadonnées, fichiers amont, licences, dates de récupération et SHA-256. Les sources consultables sont dans `donnees/sources_consultables.gpkg` ; l’occupation du sol est dans `donnees/ocsge_complement.gpkg`. Aucun de ces fichiers n’est ajouté à l’export public.

Les acquisitions/enrichissements datent de novembre 2026 ; ce n’est pas un millésime écologique. Le régional se réfère à 2014, l’OCS GE à 2023 ; les millésimes écologiques des autres couches ne sont pas attestés uniformément. Les états de complétude écologique des observations ne sont pas validés. Les effectifs décrivent le périmètre chargé et filtré, pas les effectifs nationaux.

Les portails IGN BD TOPO, OCS GE, ADMIN EXPRESS, DREAL et Cartofriches affichés dans la page ont été vérifiés. L’ancienne URL de fiche `srce-corridors-basse-normandie` n’a pas pu être confirmée par navigation ; le lien d’interface est remplacé par la page DREAL officielle des schémas, qui donne accès aux documents régionaux. L’URL historique exacte reste conservée dans le catalogue scellé, sans réécriture de sa provenance. Les URL data.gouv affichées utilisent leur forme canonique sans barre finale.

## Les trois formules et leurs hypothèses

1. `Sᵢ = aire(Hᵢ ∩ T)` : **formalisation SIG standard**. Hᵢ, hexagone complet ; T, union du territoire ; Sᵢ, aire polygonale étudiée en m², après projection Lambert-93 et validation géométrique. Code : `compute_enjeux()` / `_polygonal_part()`, et `preparer_caen_et_nord.grid()` pour la construction. Référence technique `intersection`. Aucune formule de fragmentation n’est empruntée.
2. `pᵢ = 100 × aire((Hᵢ ∩ T) ∩ union(Rⱼ)) / Sᵢ` : **ratio géométrique standard** ; Rⱼ, réservoirs valides ; union avant mesure ; Sᵢ > 0 ; pᵢ en %. `compute_enjeux()` appelle `_checked_proportion()` puis ne qualifie le résultat que si `_fully_covered()` valide la preuve de couverture écologique. Les bornes d’aire sont contrôlées ; le clamp éventuel ne corrige que les arrondis dans le budget numérique documenté. Références `union`, `intersection` pour le calcul et `srce` pour le sens des objets. Le calcul brut d’une fraction n’autorise pas sa publication comme proportion écologique qualifiée si la couverture est inconnue.
3. `Σᵢ Nᵢ exclusif = |E| = 5 336` : **invariant d’une convention d’équipe** ; E, événements distincts admis ; Nᵢ, nombre sans unité physique attribué au secteur i. `aggregate_conflicts()` choisit `min(eligible, key=lambda p: canonical_json(identifier(grid.iloc[p].maille_id)))`, parmi les relations intérieures si elles existent, sinon parmi les contacts frontaliers. Il vérifie exactement un propriétaire par événement. Aucun article retrouvé ne prescrit ce choix de clé. Les 5 759 rattachements locaux ne sont pas une somme d’événements uniques.

La documentation Shapely 2.1.2 correspond à la version du Python scientifique de la recette. Les pages décrivent des fonctions logicielles, pas des méthodes écologiques publiées. Les seuils de résidu numérique, les contrôles d’emprise et la précision cartographique ne sont pas des seuils biologiques. Aucun buffer écologique n’a été introduit dans les sélecteurs pour promouvoir une piste.

## Calcul réel recomposé depuis les géométries

Exemple local : `NORM-G1K-FLAT-R+006424-C+000493`, secteur 26, Colombelles / Hérouville-Saint-Clair. La formule de découpe, appliquée en EPSG:2154 aux hexagones complets et à l’union territoriale réellement livrés, donne :

- Aire complète : 1 000 000,0000002142 m² ; aire mesurée hors territoire : 137 770,2028032017 m².
- Aire de l’intersection : **862 229,7971970863 m²**, affichée 862 229,80 m², soit **0,862230 km²** à six décimales. Les différences sous le micro-mètre carré entre décomposition et soustraction proviennent du calcul flottant, pas d’une précision de terrain.
- L’intersection avec l’union des réservoirs mesure 0 m² dans cette maille. La complétude écologique étant inconnue, ne pas conclure à une absence de réservoir réel ni qualifier une proportion écologique nulle.
- 68 couples routiers distincts, dont 38 avec les attributs route carrossable/en service/au sol et matrice fragile. Sans surface positive de réservoir observée, le premier groupe territorial n’est pas satisfait ; la couleur orange est la conséquence d’une règle d’équipe, pas d’un seuil publié.

Exemple de la page publique autorisée : `NORM-G1K-FLAT-R+006422-C+000487`, Caen. Aire recomposée **727 382,8051328657 m²**, soit **0,727383 km²**. Le même lot contient 88 couples, dont 45 admissibles pour le premier groupe, 89 événements locaux et une aire observée de réservoir de 197 269,20463147957 m². La proportion qualifiée reste inconnue faute de complétude. Aucun chiffre privé V2 n’est importé dans la page publique.

Le fondement de ces exemples est l’opération SIG d’intersection (`intersection`) ; le sens et les limites du réservoir/matrice viennent du référentiel régional (`srce`, notamment p. 189–190). Le calcul et la règle de couleur ne sont pas attribués au SDES, à Jaeger ou au Cerema.

Reproduction en lecture seule depuis le dépôt scientifique, avec son Python géospatial :

```python
from pathlib import Path
import geopandas as gpd
from shapely import union_all
p = Path('data/processed/caen_et_nord/M1_CAEN6_20261111_V1')
h = gpd.read_file(p / 'grille.gpkg', layer='hexagones_complets').set_index('maille_id')
t = union_all(gpd.read_file(p / 'territoire.gpkg', layer='territoire').geometry.to_numpy())
r = union_all(gpd.read_file(p / 'reservoirs.gpkg').geometry.to_numpy())
for mid in ['NORM-G1K-FLAT-R+006424-C+000493', 'NORM-G1K-FLAT-R+006422-C+000487']:
    s = h.loc[mid].geometry.intersection(t)
    print(mid, s.area, s.area / 1_000_000, s.intersection(r).area)
```

## Ce qui demande encore une expertise

Les croisements exacts de couches de précisions et de dates différentes restent des indices cartographiques. Le SRCE lui-même (§A.10, p. 189–190) explique les limites de son échelle. L’état des haies, les connexions réellement utilisées, les espèces, les ouvrages, l’hydrologie, les sols et les usages ne sont pas déduits d’une simple intersection. Chaque famille expose deux à trois vérifications avant une décision. Les treize secteurs sans proposition ne sont pas déclarés sans enjeu.

Il reste à construire et valider, pour une évaluation écologique, des méthodes adaptées aux espèces et sous-trames, une couverture comparable, des mesures de pression et des protocoles de terrain. Aucun partenariat ou visa scientifique des organismes cités n’est établi. Le nombre 205 décrit des pistes du moteur ; il n’exprime ni 205 travaux nécessaires ni 205 diagnostics d’écologue.

## Bibliographie vérifiée et rôle dans le projet

Les cinq références de `regles_actions_m2.md` sont des appuis historiques du cadrage. L’OFB continuités et le SDES figurent déjà dans `methode_m2.md`. Les documents régionaux sont précisés ici à partir des données effectivement utilisées. Jaeger, le guide Cerema 2021 et les pages techniques Shapely sont des compléments de cet audit ; ils ne démontrent pas une influence historique sur le moteur.

### tvb

Office français de la biodiversité. **Rétablir les continuités écologiques**. sans date affichée. [Consulter la source](https://ofb.gouv.fr/retablir-les-continuites-ecologiques).

Explique le rôle des réservoirs, corridors et réseaux humides dans les déplacements des espèces. Appui écologique général ; aucune règle de sélection locale n’en est reprise. Déjà cité dans les règles ou la méthode du projet.

### srce

État et Région Basse-Normandie · rédaction Dervenn. **Schéma régional de cohérence écologique de Basse-Normandie — Composantes de la Trame Verte et Bleue régionale**. 2014. [Consulter la source](https://www.normandie.developpement-durable.gouv.fr/IMG/pdf/201404_SRCE_04-Composantes.pdf).

Définit les composantes régionales (p. 165, 168–186) et les limites des cartes au 1/100 000 (p. 189–190). Les couches sont utilisées ; leur méthode de construction n’est pas recalculée. Données régionales utilisées ; document constitutif précisé lors de cet audit.

### passages

Cerema. **Les passages à faune : Préserver et restaurer les continuités écologiques avec les infrastructures linéaires de transport**. 2021. [Consulter la source](https://www.cerema.fr/fr/actualites/passages-faune-guide-complet-du-cerema-creer-entretenir).

La présentation du guide décrit le besoin d’une expertise des espèces, des milieux et des ouvrages avant un aménagement. Elle étaye les vérifications proposées, sans valider nos croisements. Complément vérifié dans cet audit.

### obstacles

Cerema. **Identification et priorisation des obstacles aux continuités écologiques terrestres**. 2026. [Consulter la source](https://www.cerema.fr/fr/actualites/identification-priorisation-obstacles-aux-continuites).

Éclaire l’étude des interfaces avec les infrastructures et des ouvrages. Sa méthode nationale de transparence et de priorisation n’est pas implémentée dans le pilote. Déjà cité dans les règles ou la méthode du projet.

### haies

Office français de la biodiversité. **Gérer durablement ses haies et en créer de nouvelles**. sans date affichée. [Consulter la source](https://ofb.gouv.fr/gerer-durablement-ses-haies-et-en-creer-de-nouvelles).

Distingue gestion, conservation et plantation, selon l’état de la haie. Aucun seuil de lacune ou de densité n’est transposé au moteur. Déjà cité dans les règles ou la méthode du projet.

### renaturation

Cerema. **Comment identifier un potentiel de renaturation à large échelle?**. 2022. [Consulter la source](https://www.cerema.fr/fr/actualites/comment-identifier-potentiel-renaturation-large-echelle).

Éclaire les fonctions des sols et l’étude d’un potentiel de renaturation. La notation développée en contexte parisien n’est pas appliquée aux sites normands. Déjà cité dans les règles ou la méthode du projet.

### friches

Cerema. **Gestion à court et long terme des friches et préservation de la biodiversité : retour sur la conférence technique du 27 novembre 2025**. 2025. [Consulter la source](https://www.cerema.fr/fr/actualites/gestion-court-long-terme-friches-preservation-biodiversite).

Appuie la vérification des habitats déjà présents et des projets avant de choisir le devenir d’une friche. Ce retour d’expérience ne démontre pas le potentiel de chaque site. Déjà cité dans les règles ou la méthode du projet.

### mares

Office français de la biodiversité. **Restauration de mares**. 2024 · mise à jour du 28 octobre. [Consulter la source](https://ofb.gouv.fr/restauration-de-mares).

Décrit un projet du bassin du ru de Vaucresson. Exemple documentaire de réseau de mares, sans protocole général ni distance d’implantation applicable au pilote. Déjà cité dans les règles ou la méthode du projet.

### intersection

Sean Gillies et contributeurs Shapely. **shapely.intersection**. documentation 2.1.2 · copyright 2025. [Consulter la source](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.intersection.html).

Documente l’opération géométrique de partie commune utilisée dans le code. Source technique de calcul, sans interprétation écologique. Complément vérifié dans cet audit.

### union

Sean Gillies et contributeurs Shapely. **shapely.union_all**. documentation 2.1.2 · copyright 2025. [Consulter la source](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.union_all.html).

Documente l’union des géométries utilisée avant mesure pour éviter les doubles comptes de surface. Source technique, sans seuil écologique. Complément vérifié dans cet audit.

### sdes

Service des données et études statistiques (SDES). **La fragmentation des milieux naturels terrestres en France — Définitions, cadre conceptuel, méthodologie et résultats détaillés**. 2026. [Consulter la source](https://www.statistiques.developpement-durable.gouv.fr/la-fragmentation-des-milieux-naturels-terrestres-en-france-definitions-cadre-conceptuel).

Documente la fragmentation et une mesure par taille effective de maille avec correction des limites. Cette mesure n’est pas calculée par ReConnect ; référence de comparaison déjà citée dans la méthode du projet. Déjà cité dans la méthode M2 ; comparaison, méthode non appliquée.

### jaeger

Jochen A. G. Jaeger. **Landscape division, splitting index, and effective mesh size: new measures of landscape fragmentation**. 2000. [Consulter la source](https://link.springer.com/article/10.1023/A:1008129329289).

Landscape Ecology, 15, 115–130. DOI : 10.1023/A:1008129329289. Propose des indices fondés sur la taille des fragments. Ces indices ne sont ni reproduits ni adaptés dans le code audité ; notice et résumé vérifiés, texte intégral sous accès éditeur. Complément de comparaison, méthode non appliquée.

La notice DREAL des schémas a été publiée le 1er mars 2021 ; elle renvoie au schéma Basse-Normandie adopté le 29 juillet 2014. Le volume « Composantes » est la version finale d’avril 2014, rédigée par Vincent Guillemot (Dervenn), avec relecture DREAL/Région. Le lien Cerema 2021 est sa présentation du guide, datée du 8 décembre 2021. La publication SDES est datée du 3 juillet 2026. Le texte intégral de Jaeger n’a pas été consulté derrière l’accès éditeur : auteur, titre, année, pages, DOI et objet des trois indices sont confirmés par la notice et le résumé, sans en reproduire une formule.

Les liens d’interface ont fait l’objet d’un GET en lecture seule ; un HTTP 200 établit leur accessibilité, pas leur validation scientifique. Le reçu JSON conserve l’URL finale et le titre lorsqu’il est disponible. Les descriptions ont été vérifiées sur les pages primaires, et les passages pertinents du volume régional (p. 165, 168–186, 189–190) ainsi que du rapport SDES ont été examinés. Les documents non consultés intégralement ne sont pas présentés comme des protocoles appliqués.
