# Déblocage opérationnel M1 → M2 — 8 novembre 2026

**État : prêt à préparer l'intégration isolée dès réception des couches ; correctif numérique proposé, non appliqué.** Aucun fichier préexistant modifié. Les calculs enjeux/conflits réels et l'intégration Git n'ont pas été lancés. L'audit A–J, les statistiques CSV et les scénarios de résolution ne sont pas repris.

**V** = observation exécutée/lue ; **R** = recommandation ; **H** = interprétation ou décision restant à valider. Les preuves ciblées et le prototype sont dans [le diagnostic JSON](diagnostic_paires.json) et [le script](diagnostiquer_paires.py).

## 1. Diagnostic exact de `grid_overlap`

**V.** Après `git fetch origin`, M1 pointe toujours sur `fc76d6230994af9aef27f42bb42e0374cd0c8251` : **aucune évolution depuis la revue**. Les deux entrées utilisées ont été comparées octet par octet avec ce commit. Toutes les **903 paires distinctes** sont intersectées sans arrondi, snap, tampon ni seuil de filtrage.

| Mesure en EPSG:2154 | GeoJSON livré reprojeté | Grille régénérée en mémoire |
| --- | ---: | ---: |
| Paires disjointes | 806 | 806 |
| Contacts sans surface, tous LineString | 76 | 75 |
| Paires d'aire strictement positive, toutes Polygon | **21** | **22** |
| Aire maximale d'intersection | **8,6669331333 × 10⁻⁷ m²** | **5,7779554222 × 10⁻⁷ m²** |
| Somme des aires d'intersection | **4,8447351432 × 10⁻⁶ m²** | **4,7423968688 × 10⁻⁶ m²** |
| `somme(aires) − aire(union)` dans M2 | **4,8391520977 × 10⁻⁶ m²** | **4,5113265514 × 10⁻⁶ m²** |

**V.** La tolérance M2 est `10⁻⁶ m²` : chaque intersection est en dessous, leur cumul et la différence globale au-dessus. `math.fsum` ne supprime pas le rejet. Les sommes d'intersections et l'excès global ne sont pas numériquement identiques ; les calculs d'overlay/aire interviennent séparément. En général, les recouvrements triples empêchent aussi d'assimiler ces deux mesures.

**V.** L'espacement des flottants est de `5,8207661 × 10⁻¹¹ m` en X et `9,3132257 × 10⁻¹⁰ m` en Y. Pour les rubans positifs, la largeur équivalente `2A/P` maximale vaut environ **1,397 × 10⁻⁹ m** sur le GeoJSON et **9,313 × 10⁻¹⁰ m** sur la génération. C'est un indicateur d'épaisseur, pas une largeur maximale géométriquement garantie.

**H, fortement étayée.** Il s'agit de **micro-chevauchements topologiques dans les coordonnées flottantes**, présents dès la génération, d'ordre nanométrique ; le passage GeoJSON ajoute une variation numérique. Dire « aucun chevauchement » ou « simple erreur de soustraction » serait faux. Aucun défaut de pavage d'une ampleur supérieure à ces résidus n'est mis en évidence ici. Les limites connues de l'arithmétique GEOS expliquent ce mécanisme, sans fournir de borne universelle d'erreur. [FAQ officielle GEOS](https://libgeos.org/usage/faq/).

## 2. Correctif recommandé et non-régression

**R.** Limiter le changement futur à `validate_spatial_coverage()` et un helper : conserver les géométries, `grid_overlap`, la constante `AREA_TOLERANCE_M2`, la garde de lacune et les contrôles existants. Ajouter un diagnostic par paire et une garde locale **plus restrictive** ; ne pas remplacer simplement `1e-6` par une constante plus grande. Le [diff proposé](grid_overlap.proposition.patch) est concret et non appliqué ; `git apply --check` réussit sans écrire les modifications.

Proposition concrète, exécutée uniquement comme prototype dans l'annexe :

```text
δ = hypot(max(ULP des X), max(ULP des Y))
B_ij = δ × périmètre polygonal de l'intersection + πδ²
B_global = δ × somme(périmètres des mailles)
           + somme(ULP des aires des mailles) + ULP(aire de l'union)
grid_overlap si une aire d'intersection > min(1e-6, B_ij)
             ou si excès global > max(1e-6, B_global)
sinon : avertissement explicite si intersections positives / excès résiduel
```

**R/H.** Ces budgets sont calculés à partir de la résolution machine et de la géométrie, sans distance écologique ni coefficient ajusté au résultat. La forme `δP + πδ²` représente une bande numérique autour d'un contour. C'est une **convention d'ingénierie à approuver**, pas une borne d'erreur certifiée de GEOS. Elle ne démontre ni la précision cartographique des sources ni une topologie mathématiquement exacte. Son adoption doit rester explicite et traçable ; une autre géométrie pathologique pourrait nécessiter un examen supplémentaire.

**V.** Ici `δ = 9,3313979 × 10⁻¹⁰ m` et `B_global ≈ 1,1828212 × 10⁻⁴ m²`. Ce budget global ne suffit **jamais** à autoriser une paire : elle doit aussi respecter le plafond inchangé `1e-6` et son budget local. Les deux grilles passent le prototype **avec avertissement**, tout en restant refusées par le code M2 actuel. Aucun arrondi automatique n'est proposé ; `set_precision` peut déplacer ou faire disparaître des éléments. [Documentation Shapely 2.1.2](https://shapely.readthedocs.io/en/2.1.2/reference/shapely.set_precision.html).

**V. 16 contrôles ciblés réussis**, sans réexécuter les audits antérieurs : deux grilles M1, ordre inversé, contacts arête/sommet, disjonction, chevauchement millimétrique, duplication géométrique avec IDs distincts, contenance, recouvrement triple, ruban non numérique sous `1e-6 m²`, petit recouvrement compact sous ce plafond, plusieurs petits recouvrements, déplacement d'une maille M1 de 1 mm, garde de lacune existante et acceptation des deux configurations. Tous les chevauchements non numériques de ces contre-exemples restent refusés. Les décisions ont également été comparées à l'exécution du **validateur exact du diff proposé dans une copie temporaire**, avec garde de lacune et avertissement vérifiés : [preuve ciblée](verification_correctif.json). Avant activation, intégrer ces cas à la suite de non-régression et lancer les tests SIG concernés, notamment frontières et rattachements ; cette vérification de l'intégration future reste à faire.

## 3. Paquets à obtenir de M1

**V.** Les six GPKG restent absents de la branche et du projet local. Cela ne renseigne pas leur présence sur l'ordinateur de M1. Aucun téléchargement actualisé n'a été substitué au snapshot.

| Paquet minimal pour démarrer | Paquet complémentaire pour la validation complète |
| --- | --- |
| `reservoirs.gpkg`, couche `reservoirs` | `sols.gpkg` / `sols` et `zones_construites.gpkg` / `zones_construites` |
| `corridors.gpkg`, couche `corridors` | Bruts ou extraits figés effectivement utilisés par les mesures, avec leurs empreintes |
| `routes.gpkg`, couche `routes` | Haies, SIPAF, Cartofriches, zones humides : objets/attributs nécessaires et transmissibles |
| `grille_pilote.gpkg`, couches `grille_pilote` et `hexagones_complets`, **ou** génération pure du commit audité, exportée ultérieurement dans le checkout isolé | Registres de couverture par thème/emprise/période, dictionnaires des codes TVB et métadonnées du produit haies réellement utilisé |
| Contour exact du pilote ; récupérable par `pilot` retourné par `generate_grid()`, sans densifier ni reconstruire un autre rectangle | Notices/licences particulières aux compléments lorsque la diffusion est restreinte |
| Manifeste des fichiers reçus : tailles/SHA-256, couches, CRS, champs/types, version liée au commit, droits applicables ; compléter les métadonnées déjà livrées seulement où elles manquent | PRAM et EPFN ne sont pas requis pour démarrer ; ne pas demander à M1 une donnée déclarée indisponible comme préalable général |

**R.** La procédure alternative de grille est : importer le module du commit figé, appeler `generate_grid()`, vérifier les deux empreintes déjà auditées, écrire les deux couches dans un **nouveau** GPKG et écrire `pilot` dans un fichier distinct. Nom proposé M2 pour ce dernier : `pilote_contour.gpkg`, couche `pilote_contour` ; ce nom ne prétend pas désigner un livrable M1 existant. Aucun de ces exports n'est effectué maintenant.

## 4. Configurations et plan d'exécution interne

**V.** Les deux configurations nouvelles passent les véritables `load_config()` de M2 : [enjeux](config_enjeux.proposition.json), [conflits](config_conflits.proposition.json). Les champs correspondent au code/schéma documenté de M1 ; leur présence et leur type dans les GPKG doivent encore être contrôlés à réception.

| Entrée | Mapping préparé | Contrôles à réception |
| --- | --- | --- |
| Grille | `maille_id`, EPSG:2154 | Couche découpée, 43 IDs uniques, versions, aires et diagnostic par paire |
| Réservoirs | Polygones, source `TVB_RES_NORM` | `objet_id`, types/CRS/géométries, valeurs réellement présentes |
| Routes | `route_id`, `categorie`, source `BDTOPO_ROUTES` | IDs non nuls, types linéaires et attributs ; aucun niveau/ouvrage inventé |
| Corridors | `objet_id`, `classe_corridor`, source `TVB_COR_BN` | Polygones/multipolygones, IDs et codes ; aucune fonctionnalité actuelle inférée |
| Territoire | Polygon/MultiPolygon, EPSG:2154 | Contour exact, empreinte géométrique identique pour enjeux/détection/agrégation |

**R.** Les configurations conservent `coverage.status="unknown"`. Aucun `--*-coverage-confirmed`, mapping de sous-trames, distance de précision, règle de qualification ou faux validateur n'est ajouté. L'emprise plausible doit être une référence effectivement approuvée si elle est fournie ; sinon M2 garde son avertissement. `M1-V1` désigne le paquet déclaré, à relier aux SHA-256 et au commit par le manifeste ; ce n'est pas une nouvelle preuve de millésime.

**Commandes préparées, à ne lancer qu'après réception, validation des entrées et application approuvée du correctif, dans le checkout isolé** :

```sh
python -m analysis.run_enjeux \
  --grid data/processed/grille_pilote.gpkg --grid-layer grille_pilote \
  --territory data/processed/pilote_contour.gpkg --territory-layer pilote_contour \
  --reservoirs data/processed/reservoirs.gpkg --reservoirs-layer reservoirs \
  --corridors data/processed/corridors.gpkg --corridors-layer corridors \
  --config docs/deblocage_m1_m2_v61/config_enjeux.proposition.json \
  --grid-version M1-CAND-1KM2-FLAT-L93-O0-V1 --dataset-version M1-V1 \
  --output data/derived/premier_m1_enjeux.gpkg --report data/derived/premier_m1_enjeux.validation.json

python -m analysis.run_conflicts \
  --grid data/processed/grille_pilote.gpkg --grid-layer grille_pilote \
  --territory data/processed/pilote_contour.gpkg --territory-layer pilote_contour \
  --routes data/processed/routes.gpkg --routes-layer routes \
  --corridors data/processed/corridors.gpkg --corridors-layer corridors \
  --config docs/deblocage_m1_m2_v61/config_conflits.proposition.json \
  --grid-version M1-CAND-1KM2-FLAT-L93-O0-V1 --dataset-version M1-V1 \
  --output-events data/derived/premier_m1_conflits.gpkg \
  --output-cells data/derived/premier_m1_mailles.gpkg --report data/derived/premier_m1_conflits.validation.json
```

La version de méthode est volontairement omise jusqu'à sa désignation : M2 conserve NULL, son avertissement et les empreintes du code. Tous les chemins de sortie doivent être libres ; les CLI refusent l'écrasement.

**R. Contrôles de sortie à exécuter ensuite**, sans recalculer maintenant les statistiques M1 :

- Vérifier le couple enjeux avec `verify_artifact_pair()` et le lot conflits avec `verify_conflict_bundle()`. Les validations d'entrées sont déjà intégrées aux CLI ; elles ne réparent pas les sources.
- Comparer par `maille_id` : `study_area_m2 ↔ cell_area_m2`, `reservoir_observed_area_m2 ↔ reservoir_area_m2`, `corridor_observed_area_m2 ↔ corridor_area_m2`. Les corridors polygonaux n'ont pas à fournir une longueur de corridor depuis le CSV. Expliquer les écarts par l'arrondi à six décimales (demi-unité de dernière décimale), les calculs et les versions, sans choisir un nouveau seuil écologique.
- Garder `enj_01_pct=NULL` sans complétude validée ; ENJ-02 peut constater une présence cartographique positive, mais ses absences restent inconnues. Les autres mesures CSV ne deviennent pas des résultats de conflits.
- Conserver `liens_mailles_conflits` dans le GPKG des mailles : une relation par paire événement–maille, toutes les frontières conservées, un propriétaire canonique par événement. Vérifier références réciproques, couverture du territoire, somme des propriétaires = nombre d'événements distincts. Ne jamais comparer `nb_evenements` au nombre de routes, ni additionner les comptes locaux comme total global.
- Examiner les contacts exclusivement sur le bord, les segments traversant plusieurs mailles et les portions minuscules. `croisement_detecte`/`non_concluant` restent des observations géométriques ; absence d'observation ≠ absence écologique.

## 5. Travaux M2 réalisables immédiatement

**V, réalisés ici :** diagnostic des paires, prototype non activé et contre-exemples, configurations vérifiées par leurs parseurs, commandes et critères de réception préparés. **R, après validation du correctif :** modifier seulement le contrôle numérique et ses tests ciblés dans l'environnement isolé, préparer les imports et le contour. Les calculs réels attendent les trois couches sources et la grille/son export. Aucune activation artificielle de R2/R4, de priorité ou d'action n'est nécessaire pour démarrer les observations internes.

## 6. Décisions restant à M2 ou à l'équipe

**H/Décisions :** accepter le critère numérique proposé et sa portée ; confirmer le contour/version du pilote ; identifier la méthode géométrique ; approuver les dictionnaires et les preuves de complétude lorsqu'elles existent. Les classes d'enjeu et priorités restent inconnues sans méthode approuvée. La qualification écologique des croisements, les familles décisionnelles et les méthodes R2/R4 demandent leurs propres preuves ; ces décisions ne bloquent pas le descriptif géométrique interne. Le contrat public M4 et la garde `test_data=False` restent inchangés ; aucune donnée réelle ne sera étiquetée synthétique.

## 7. Sauvegarde et intégration Git sécurisées — procédure non exécutée

**V.** Branche courante `feat/diagnostics-ecologiques`, HEAD `9a5fe89193a394dc457b070cae5436e25d60f139`. Deux fichiers suivis restent modifiés : `analysis/detect_conflicts.py` et `docs/methode_m2.md` (**257 ajouts, 16 suppressions**). Les trois modules de priorité, documents et tests non suivis sont présents. Les caches ignorés sont aussi présents. Un manifeste temporaire contrôle les empreintes des **86 fichiers préexistants**, ignorés compris, sans réaliser la sauvegarde proposée.

**V.** Aucun chemin modifié dans les commits n'est commun aux deux branches depuis leur ancêtre ; aucun chemin M1 suivi n'entre en collision avec les fichiers M2 actuellement non suivis. Cela réduit les collisions attendues, sans constituer un essai de fusion ni garantir la compatibilité fonctionnelle. Les chemins/couches M1 cadrent avec les configurations proposées. Les dépendances restent incompatibles si installées ensemble : M1 exige `pandas==3.1.0`, M2 `pandas>=2,<3` ; le handoff annonce Python 3.14+ alors que les rapports M1 déclarent Python 3.12.

**R. Séquence future, à autoriser et exécuter séparément :**

1. Suspendre les écritures de l'éditeur ; créer une archive complète du répertoire, **avec `.git`, fichiers suivis, non suivis, ignorés et fichiers cachés** ; préserver permissions/liens. Vérifier liste, empreintes et restitution dans un répertoire de contrôle. Un patch ou un bundle Git seul ne sauvegarde pas tous les travaux. **Aucune archive créée ici.**
2. Créer un clone/checkout indépendant à HEAD M2, avec références M1 figées. Préparer l'intégration M1 uniquement dans cette copie, après autorisation de l'opération ; conserver l'archive et le répertoire actuel intacts.
3. Rejouer dans la copie les modifications locales à partir de la sauvegarde vérifiée, **sans remplacer son `.git`** ; copier aussi les non suivis/ignorés et traiter les éventuelles suppressions enregistrées. Comparer tous les fichiers de travail au manifeste, puis examiner les différences introduites par M1. Recontrôler les collisions si M1 ou M2 a changé entre-temps.
4. Utiliser un environnement M2 séparé pour les calculs et un environnement M1 séparé si sa chaîne doit être reproduite. Ne pas installer ses pins au-dessus de M2. Appliquer seulement le correctif approuvé, recevoir les fichiers géographiques avec manifeste, puis lancer les validations ciblées et les commandes internes.
5. Revoir le diff et les résultats avant toute décision de report sur la branche principale de travail. La réversibilité vient du maintien de l'original et de la sauvegarde ; aucun reset/clean/stash n'est nécessaire. **Aucun clone, worktree, merge, commit ou push effectué pendant cette préparation.**

## 8. Proposition de message à M1 — non envoyé

> Bonjour, la revue porte toujours sur `fc76d6230994af9aef27f42bb42e0374cd0c8251`. Pour lancer M2, peux-tu nous transmettre les fichiers figés `reservoirs.gpkg`, `corridors.gpkg` et `routes.gpkg`, avec noms des couches, champs/types, CRS et manifeste tailles/SHA-256 lié à cette livraison ? Ils ne sont pas accessibles dans Git ou notre copie locale ; nous ne présumons pas de leur absence chez toi.
>
> Pour la grille, ton GPKG à deux couches convient ; sinon nous pouvons le produire à partir du générateur figé, ainsi que le contour exact du pilote. Merci de signaler toute différence de contour ou de version et de compléter seulement les informations de droits propres aux fichiers transférés.
>
> En complément, pour vérifier toutes les mesures : sols/zones construites et bruts ou extraits figés effectivement utilisés, notamment haies, SIPAF, Cartofriches et zones humides lorsque transmissibles, plus les dictionnaires TVB et les éventuelles preuves de couverture par source/emprise/période non déjà livrées. PRAM/EPFN ne bloquent pas ce premier lancement. Aucun nouveau téléchargement actualisé n'est requis pour remplacer ces fichiers.

**Prochain point de passage : réception du paquet minimal et approbation du correctif numérique ; ensuite, premiers calculs internes dans la copie isolée.**
