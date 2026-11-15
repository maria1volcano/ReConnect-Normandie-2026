# ReConnect Normandie — refonte finale locale

> Rapport historique de la phase précédente. État final et corrections : [dossier MVP](FINALISATION_MVP_20261115.md).

15 novembre 2026. **Verdict : prête sous réserves pour la revue finale avant push.**

L’interface locale est fonctionnelle, testée et plus explicite. Trois points restent à traiter avant une publication : la portée limitée du classement territorial, le conflit avec le nouveau `main` distant et l’autorisation de diffusion des données. Aucun commit, push, merge, changement de PR ou déploiement n’a été effectué.

Accès de revue : **http://127.0.0.1:5184/**. API de revue : **http://127.0.0.1:8768/health**. Le site publié conserve son parcours et ses ressources publiques antérieurs.

## Résultat livré

- Carte unique colorée, fond OpenStreetMap avec routes et noms de lieux, mailles semi-transparentes, sélection soulignée et légende numérotée. Couverture affichée : « Territoire pilote : Caen et cinq communes voisines ».
- Recherche par commune ou numéro de secteur, insensible aux accents, et un seul sélecteur filtré. Les communes proviennent des associations réelles M2. Les identifiants longs ne sont pas affichés dans le parcours.
- Suppression des quatre boutons de démonstration. Le clic reste le parcours principal ; le sélecteur recadre la carte et la fiche s’actualise. Sur mobile, la sélection amène à la fiche.
- En-tête territorial avec communes, numéro court, priorité d’examen, résumé de deux phrases et nombre de solutions. Toutes les pistes sélectionnées sont affichées, y compris quatre, sans action principale imposée.
- Libellés des solutions : A → **Étude étayée**, B → **À approfondir**, C → **À explorer**. Les valeurs et statuts M2 restent inchangés.
- Explications principales conservées : deux à trois phrases sur les observations, une à deux sur l’intervention. Les détails présentent au plus deux indicateurs utiles, une limite spécifique et trois vérifications.
- Indicateurs complets et limites consultables dans des ressources rédigées ; aucun bloc JSON brut dans la fiche ou la méthode. Les réponses API et les lots exacts restent internes et protégés.
- Page Méthode structurée autour des sources réellement utilisées, de la grille, de trois équations, des règles de chaque famille, des couleurs, d’un exemple réel à quatre solutions, des limites et des références vérifiées.
- Identité conservée : thème vert sombre, Lucide, quatre couleurs de familles centralisées dans `actionFamilyVisuals.ts`, fonds de cartes d’action neutres.

## Audit de la priorité territoriale

### Politique réutilisée, sans nouveau score

Le lot scellé contient déjà une politique M2 indépendante des propositions multi-actions : `caen6-priorites-etude-actions-20261112-1`, calculée par `analysis/prioriser_etudes_interventions.py`. La projection la lit depuis `decision_interventions.priorite_etude_interventions`. Le frontend ne calcule aucun score, poids ou niveau territorial.

| Groupe | Effectif | Critère effectivement documenté |
| --- | ---: | --- |
| Rouge · examen très élevé | 27 | Paire locale linéaire : voie carrossable en service au sol, matrice régionale qualifiée de fragile, plus surface positive de réservoir dans la maille |
| Orange · examen élevé | 33 | Croisement linéaire local voie–matrice retenu, sans réunir tous les critères du premier groupe |
| Jaune · examen modéré | 9 | Surface positive de corridor ou réservoir, sans croisement routier retenu par cette politique |
| Gris · informations insuffisantes | 32 | Les indices de cette politique ne sont pas réunis ; d’autres solutions peuvent néanmoins être envisagées |
| Vert · examen faible | 0 | Aucune condition documentée ne permet de l’attribuer |

Cette politique est un **ordre d’examen indicatif centré sur les interfaces routières et les continuités**. Elle ne compare pas globalement les quatre enjeux, la gravité écologique, la rentabilité, l’efficacité ou l’urgence temporelle de travaux. Le nombre de pistes, leur meilleur niveau et le nombre brut de croisements ne déterminent pas la couleur.

Les enjeux de haies, milieux humides et friches sont réellement exploités pour les solutions. Ils ne sont pas artificiellement additionnés au classement territorial. Une maille grise peut avoir des pistes ; l’absence d’observation n’est pas interprétée comme une faible priorité écologique.

### Ce qui bloque encore un classement global multi-enjeux

Les méthodes d’enjeu pertinentes, la fonctionnalité des habitats, la pression et la perméabilité réelles, les observations de terrain, l’adéquation de précision et l’exhaustivité écologique ne sont pas toutes qualifiées. Des sous-trames et dates restent inconnues. Les observations partagées empêchent aussi de traiter chaque relation comme une confirmation indépendante.

La résolution demande une qualification par famille des enjeux et pressions, des preuves comparables, une gestion explicite des données manquantes et contradictions, puis une méthode de combinaison revue et versionnée séparément dans M2, avec tests et nouvel export interne. Aucun poids ou seuil n’est proposé arbitrairement ici. Les résultats historiques D/S et R1–R4 restent intégralement conservés.

## Calculs présentés et correspondance avec le code

Les fonctions et leurs tests ont été lus avant rédaction. Le dépôt scientifique est resté inchangé.

| Présentation | Implémentation M2 consultée | Vérification |
| --- | --- | --- |
| Surface étudiée `Sᵢ = aire(Hᵢ ∩ T)` | `analysis/indicateurs_enjeux.py`, `compute_enjeux`, découpage puis partie polygonale | Tests de territoire, de frontière et d’indicateurs |
| Proportion des réservoirs `100 × aire((Hᵢ ∩ T) ∩ union(Rⱼ)) / Sᵢ` | `compute_enjeux`, `_checked_proportion`, union des réservoirs ; qualification seulement si couverture écologique validée | `tests/test_m2_enjeux.py`, dont union des surfaces superposées et couverture inconnue conservée inconnue |
| Comptage exclusif `somme(Nᵢ exclusif) = nombre(E)` | `analysis/aggregate_conflicts.py`, `aggregate_conflicts` ; propriétaire unique par clé stable parmi les rattachements admissibles, priorité aux relations intérieures | `tests/test_m2_conflicts.py`, contrôles de frontière et d’appartenance |
| Intersections et dédoublonnage | `analysis/detect_conflicts.py`, `detect_route_corridor_conflicts`, normalisation des géométries et attributs sources ; `analysis/auditer_multiactions_caen.py`, `local_relation` | Tests de détection, de dimension et de conservation des sources |
| Niveaux des quatre solutions | `analysis/moteur_multiactions_experimental_v2.py`, `choose`, et vérificateur V2 | Tests du moteur et des 101 fiches réelles |
| Couleurs territoriales | `analysis/prioriser_etudes_interventions.py`, `validate_reference` et `decide` | Tests existants M2 ; nouveaux tests applicatifs comparant chaque sortie au lot scellé |

La grille nominale est de 1 km² en Lambert-93, découpée sur les six communes : 101 mailles, 67 partielles, environ 65,2146 km². Les objets source invalides et les résultats en quarantaine ne sont pas réparés ou déplacés pour produire une décision.

Les 5 337 relations détectées comprennent 5 336 admises et une quarantaine. Les rattachements locaux sont au nombre de 5 759, tandis que les comptes exclusifs totalisent 5 336. Ces unités ne sont ni des obstacles confirmés ni des travaux à programmer.

### Exemple réel de la page Méthode

Identifiant technique : `NORM-G1K-FLAT-R+006424-C+000493`, secteur 26, Colombelles / Hérouville-Saint-Clair. La page lit l’exemple dans l’API, sans embarquer une copie des données dans le bundle.

- Surface découpée : **862 229,7971970863 m²**.
- Haies observées : **1 377,3896962570077 m**.
- Milieux humides inventoriés : **8 758,854675022496 m²**.
- **68 couples distincts** voie–espace régional, dont **38** avec les attributs voie carrossable en service au sol et matrice fragile.
- Aucun réservoir avec une surface positive observée dans la maille : classement d’examen **orange**, malgré les 38 couples. Aucun seuil de nombre de couples n’est appliqué.
- Quatre pistes, dont les niveaux exacts sont lus dans la réponse V2 et vérifiés par les tests. Les données sources, objets et preuves restent vérifiables dans les lots internes.

## Sources et références

Les sources effectives ont été vérifiées dans `provenance/sources_licences.json` du lot canonique et dans les rapports M2 : IGN BD TOPO (routes, haies, plans d’eau), DREAL (matrices et réservoirs régionaux, inventaires humides), Cerema Cartofriches, IGN ADMIN EXPRESS pour l’emprise, OCS GE 2023 et artificialisation pour le contexte. L’inventaire exhaustif de mares, le trafic mesuré et les inventaires d’espèces sensibles ne sont pas prétendus intégrés.

Les cinq références suivantes figurent déjà dans `docs/regles_actions_m2.md`. Leurs pages ont été vérifiées pour la refonte :

| Référence | Usage exact et limite |
| --- | --- |
| Cerema, 2026, [Identification et priorisation des obstacles aux continuités écologiques terrestres](https://www.cerema.fr/fr/actualites/identification-priorisation-obstacles-aux-continuites) | Cadrage infrastructures–continuités et ouvrages. La note nationale de transparence n’est pas implémentée dans le pilote. |
| OFB, date non affichée, [Gérer durablement ses haies et en créer de nouvelles](https://ofb.gouv.fr/gerer-durablement-ses-haies-et-en-creer-de-nouvelles) | Préservation, gestion et plantation distinguées. Aucun seuil de lacune n’en est déduit. |
| Cerema, 2022, [Comment identifier un potentiel de renaturation à large échelle ?](https://www.cerema.fr/fr/actualites/comment-identifier-potentiel-renaturation-large-echelle) | Cadrage du potentiel et des fonctions des sols. La notation de cette étude n’est pas appliquée à nos mailles. |
| Cerema, 2025, [Gestion à court et long terme des friches et préservation de la biodiversité](https://www.cerema.fr/fr/actualites/gestion-court-long-terme-friches-preservation-biodiversite) | Biodiversité existante et projets à vérifier avant renaturation. |
| OFB, 2024, [Restauration de mares](https://ofb.gouv.fr/restauration-de-mares) | Retour d’expérience de réseau humide ; ni guide de seuils ni règle locale d’implantation. |

Les règles de sélection et d’ordre d’examen sont des conventions d’ingénierie du projet. Les publications ne sont pas présentées comme validant nos niveaux ou nos couleurs. Aucune bibliographie de thèses ou d’articles non mobilisés n’a été ajoutée.

## Projection applicative interne

Le contrat public et les lots ne changent pas. La projection locale ajoute :

- Une propriété `sector` : numéro, communes et libellé provenant des communes réelles associées à chaque maille.
- Une propriété `territorial_priority` conservant version M2, rang, couleur, statut, portée et observations justificatives du classement scellé. La présentation est identifiée séparément par `caen6-examen-multiactions-presentation-20261115-1` ; ce n’est pas un nouveau score.
- `study_color` dans la grille, copié de la priorité source ; le frontend transmet cette couleur au calque MapLibre.
- Les compteurs du classement dans les métadonnées.
- Une route interne `methodology`, sous les mêmes contrôles de portée, version, hôte, origine et absence de proxy, contenant uniquement l’exemple autorisé par la projection.

Les tests vérifient l’identité des couleurs avec les sources scellées, l’indépendance vis-à-vis des solutions et l’absence de mutation. L’application refuse une projection incompatible ; elle ne revient pas silencieusement à un ancien classement.

## Fond de carte et protections

Le fond uniforme provenait du choix `localOnly` de la vue précédente, qui utilisait volontairement le style administratif de secours. La vue de revue utilise désormais le fond raster OpenStreetMap, sans service payant ni clé. Les opacités permettent de lire les routes et noms de lieux. Seules les tuiles du fond de repérage sont demandées à l’extérieur ; les données M2 restent sur les routes de boucle locale protégées.

Le chargement se fait directement sur le territoire pilote. Une panne de tuiles masque le raster tout en conservant les calques, les identifiants de sélection et les interactions. Le message de repli ne masque pas les attributions. Les commandes sont plus petites ; la grille peut être masquée et le territoire recentré.

Le chargement des composants de revue est conditionné au développement, au drapeau explicite et à l’hôte local. Les imports des composants sont aussi supprimés du build de production : leurs textes, l’exemple et la version expérimentale ne sont pas inclus dans le bundle public. Les 15 ressources publiques sont recopiées à l’identique. Aucun lot, JSON brut source, GeoPackage, ZIP ou chemin personnel n’est ajouté au build.

## Validation exécutée

| Contrôle final | Résultat |
| --- | --- |
| Suite scientifique M2 complète | **1 538 tests réussis**, 40 avertissements existants |
| Suite backend complète, Python 3.10 | **39 tests réussis**, un avertissement Starlette/httpx |
| Tests frontend de priorités et d’actions historiques | Réussis |
| Contrat V2 et présentations réelles | 101 mailles, 205 pistes, 88 avec proposition, 61 multi-actions, 13 sans proposition, A/B/C = 93/45/67, sans mutation |
| Navigateur V2 final | 101 mailles et 205 cartes réellement parcourues, dont 15 secteurs à quatre pistes et 13 sans proposition |
| Distribution et cohérence des couleurs | 27 rouges, 33 orange, 9 jaunes, 32 grises ; légende et fiches cohérentes avec l’API |
| Recherche | Commune avec ou sans accent, numéro de secteur, aucun résultat |
| Détails | Ouverture/fermeture et clavier, une limite spécifique, au plus deux indicateurs, trois vérifications ; aucun JSON brut |
| Responsive | 320, 390, 768, 1024, 1440 px, détails ouverts ; aucun débordement ni chevauchement détecté |
| Carte et chargements | Clic réel mobile, sélection synchronisée, erreur de fiche et réessai, panne de tuiles avec grille utilisable |
| Fond OSM, dernière recette V2 | 142 tuiles reçues, aucune réponse de tuile en erreur |
| Contraste des repères numérotés | Minimum **4,80:1** |
| Erreurs JavaScript / requêtes externes inattendues | **0 / 0** |
| Méthode | Trois équations, cinq références, exemple réel à quatre pistes, liens et affichage mobile |
| Production | Build et TypeScript réussis, aucun appel V2 en production malgré le drapeau, contenus de revue exclus du bundle |
| Sécurité | Mauvaises versions et origines refusées, mode désactivé conservé, accès direct au fichier M2 brut par le frontend : **403** |
| Navigateur historique existant, sans modification du test | Réussi : quatre couleurs, clic mobile, catalogue, méthode, D/S séparé, cinq largeurs, refus proxy |

L’essai initial de la suite backend dans un ancien environnement Python 3.9 ne pouvait pas collecter les annotations Python 3.10. Il a été remplacé par un venv temporaire Python 3.10, sans modification du code pour contourner l’erreur. Les dépendances et le lockfile du projet n’ont pas été changés.

Le build conserve l’avertissement de taille du module MapLibre. Il ne bloque pas la compilation.

### Reproduction

Depuis la racine applicative, utiliser un environnement Python 3.10 ou plus avec `backend/requirements-dev.txt`, un module Playwright et Chrome. Les services restent exclusivement en boucle locale. Les chemins des lots sont relatifs au worktree.

```sh
RECONNECT_M2_V2_ROOT=../Datathon-normandie-2026/data/derived/m2_multiactions_experimental_v2_20261112_01/lot_experimental_v2 \
RECONNECT_M2_ZIP=../Datathon-normandie-2026/data/derived/caen_et_nord_actions_20261112_01/RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1.zip \
PYTHONPATH=backend "$QA_PYTHON" -B -m pytest -q -p no:cacheprovider backend/tests backend/test_server.py
```

Depuis `frontend/` :

```sh
npm run test:priorities
npm run test:actions
RECONNECT_V2_API_URL=http://127.0.0.1:8768 npm run test:multiactions-v2
RECONNECT_V2_API_URL=http://127.0.0.1:8768 npm run test:action-presentations
RECONNECT_V2_PREVIEW_URL=http://127.0.0.1:5187 npm run test:browser:multiactions-v2
VITE_M2_MULTIACTIONS_V2=1 VITE_M4_API_BASE_URL=static npm run build -- --outDir /tmp/reconnect-final-public-build-20261115
RECONNECT_BUILD_DIR=/tmp/reconnect-final-public-build-20261115 npm run test:production-safety
```

`PLAYWRIGHT_MODULE_PATH`, `CHROME_EXECUTABLE_PATH` et `RECONNECT_UI_QA_DIR` permettent d’utiliser les outils et emplacements locaux. La recette historique conserve ses ports 5183/8767.

## Captures et reçus

Les captures sont conservées hors du répertoire public et ignorées par Git dans `data/derived/refonte_finale_ui_20261115/qa/` :

- [Quatre solutions](../data/derived/refonte_finale_ui_20261115/qa/desktop_four.png)
- [Secteur rouge](../data/derived/refonte_finale_ui_20261115/qa/desktop_red.png)
- [Piste exploratoire seule](../data/derived/refonte_finale_ui_20261115/qa/desktop_exploratory.png)
- [Sans proposition](../data/derived/refonte_finale_ui_20261115/qa/desktop_empty.png)
- [Quatre solutions en mobile](../data/derived/refonte_finale_ui_20261115/qa/mobile_four.png)
- [Détails en mobile](../data/derived/refonte_finale_ui_20261115/qa/mobile_details.png)
- [Méthode sur ordinateur](../data/derived/refonte_finale_ui_20261115/qa/method_1440.png)
- [Méthode sur mobile](../data/derived/refonte_finale_ui_20261115/qa/method_390.png)
- [Repli en cas de panne du fond](../data/derived/refonte_finale_ui_20261115/qa/offline_map.png)

Les reçus navigateur V2 et historique, ainsi que les rapports JUnit, sont conservés au même endroit pour l’équipe. Ils ne sont pas des exports de données autorisés à la publication.

## Revue Git et préparation du futur push

L’état détaillé est fourni dans [ETAT_GIT_REFONTE_20261115.md](ETAT_GIT_REFONTE_20261115.md).

Les branches sont restées `feat/integration-actions-ui` (HEAD `b2c7287`) et `feat/m2-multi-actions` (HEAD `66a4723`). Le contrôle avant/après des 1 605 fichiers existants confirme : aucun fichier M2, contrat, lot scellé, géométrie canonique, donnée publique ou lockfile modifié pendant la refonte. L’index Git reste vide.

### Écart avec le distant

La [PR #5](https://github.com/maria1volcano/ReConnect-Normandie-2026/pull/5) reste ouverte et inchangée. La référence locale `origin/main` est encore `cb6856f`, mais le `main` distant consulté par le connecteur GitHub est `14f6c7f`, avec deux commits supplémentaires. La branche de la PR est deux commits en avance et deux en retard.

Les nouveaux commits distants extraient les styles documentaires vers `frontend/src/styles/doc-pages.css`, ajoutent son import dans `Root.tsx` et modifient le catalogue. La simulation textuelle à trois versions, dans un dossier temporaire, constate :

- **Un conflit dans `frontend/src/styles/global.css`**, déjà présent entre le HEAD applicatif et le `main` distant. Il concerne l’extraction du bloc documentaire et les styles d’intégration situés à sa suite.
- Aucun conflit textuel dans `Root.tsx` ou `CataloguePage.tsx`, y compris avec le fichier de travail actuel. Une vérification fonctionnelle restera nécessaire après réconciliation des styles.
- Le nouveau fichier distant `doc-pages.css` doit être conservé lors de cette étape ; les ajustements d’en-tête et de responsive de la branche applicative devront aussi l’être.

Aucun fetch modifiant les références locales, merge, rebase ou résolution sur les branches n’a été réalisé. La copie de comparaison n’est pas un résultat de fusion appliqué.

La description de la PR mentionne aussi un ancien blocage de prévisualisation lié à l’identité Git. Sa résolution et une prévisualisation à jour restent à vérifier au moment autorisé ; aucune action Vercel n’a été entreprise ici.

### Procédure proposée, à effectuer à l’étape autorisée

1. Examiner les captures, la portée de la priorité d’examen et la terminologie avec l’équipe ; valider les choix pour la démonstration.
2. Sauvegarder et inventorier séparément les changements existants des deux worktrees. Ne pas utiliser d’ajout global de tous les fichiers.
3. Réconcilier avec le `main` distant actuel sur un travail isolé, après autorisation de cette étape. Résoudre le conflit de styles en conservant `doc-pages.css` et les corrections de l’application. Relancer les tests et les contrôles responsive ensuite.
4. Examiner les fichiers de code, tests, licences et documentation par liste explicite. Garder les lots, exports internes, captures, reçus, venvs, secrets et configurations locales hors de l’index.
5. La note historique `frontend/RECETTE_LISIBILITE_20261113.md` contient des chemins locaux personnels : la conserver comme historique local ou la neutraliser avant tout ajout envisagé. Les motifs génériques de détection de chemins dans les tests ne constituent pas un chemin personnel.
6. Examiner la modification préexistante du lockfile : quatre marqueurs `peer` ont été retirés avant cette intervention, sans changement de version ou d’intégrité des dépendances. Elle est préservée, mais ne doit pas être incluse par inadvertance comme changement de refonte.
7. Relancer les suites M2/backend/frontend, le build et `test:production-safety`, puis revoir l’état Git et les différences destinées à la PR. Confirmer que l’index ne contient aucun lot ni chemin privé.
8. Confirmer séparément les droits de publication des nouvelles données, le catalogue M5, les validations écologiques nécessaires et les conditions de prévisualisation. L’état `publication_authorized=false` demeure bloquant pour toute diffusion des données internes.
9. Présenter le résultat à l’utilisateur avant toute autorisation de commit, push, merge ou déploiement. Cette procédure ne les exécute pas.

La refonte est exploitable pour la revue locale et la démonstration du périmètre décrit. Un classement écologique global multi-enjeux et la publication ne sont pas déclarés validés.
