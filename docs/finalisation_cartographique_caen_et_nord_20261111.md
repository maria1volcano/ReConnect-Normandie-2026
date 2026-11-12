# Livraison cartographique M1–M2 : Caen entière et cinq communes du nord

Le lot couvre réellement la commune entière de **Caen (14118)** et les cinq communes du pilote historique : Bénouville, Blainville-sur-Orne, Colombelles, Hérouville-Saint-Clair, Ouistreham. Il fournit **101 mailles découpées**, une fiche par maille, deux classifications séparées et une adaptation ciblée de l'application M3 existante. Il est destiné à une **revue et démonstration locales**, sans publication autorisée.

ZIP à transmettre :

`data/derived/caen_et_nord_20261111_01/RECONNECT_CAEN_ET_NORD_M2_DEMO_INTERNE_20261111_V1.zip`

Joindre son `.zip.sha256` et le reçu `data/derived/caen_et_nord_20261111_01/validation_extraction.json`. Le ZIP contient son propre vérificateur autonome, son manifeste et les empreintes de chaque fichier. Le message de transmission est `MESSAGE_M4_M5.md` dans le dossier extrait.

## Périmètre et géométrie

La limite officielle IGN ADMIN EXPRESS COG LATEST des six communes a été acquise le 11 novembre 2026 ; les références, dates de métadonnées et empreintes sont archivées. La date de téléchargement ne constitue pas un millésime écologique. La surface territoriale est de **65,2145835195 km²**, dont **25,7298159044 km² pour Caen**. Les limites communales sont conservées ; l'analyse porte sur leur union, sans découpage successif créant des trous.

La grille réutilise le générateur M1 existant : hexagones flat-top, surface nominale de 1 km², origine (0,0), EPSG:2154, identifiants canoniques de ligne/colonne. Son nombre de mailles découle de l'intersection avec le territoire : **101, dont 67 partielles**. Quarante mailles ont une surface positive dans Caen. Ce nombre de quarante n'est pas le compte des mailles avec événements.

Nouvelle portée :

- `territory_id=caen_et_nord_6communes`
- `grid_version=M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1`
- `dataset_version=M1-CAEN-ET-NORD-20261111-V1`
- `method_version=NULL`

La lacune numérique sur Caen est de **6,1623113302e-8 m²**, dans le budget préexistant de 1e-6 m². L'excès territorial est nul. Le résidu de chevauchement, **1,6942620277e-5 m²**, satisfait les budgets locaux et globaux du validateur M2 existant, avec avertissement explicite ; aucune géométrie ni tolérance n'a été modifiée. Les 66 hexagones complets partagés sont exactement identiques aux anciens, à tolérance zéro. Les découpes territoriales et données restent distinctes par version.

## Application existante inspectée

Les références ont été lues dans un clone nu temporaire indépendant. Aucune branche de l'équipe ni modification locale préexistante n'a été changée.

| Module | Branche et commit inspectés | Interface observée |
| --- | --- | --- |
| M3 | `feat/m3-frontend-reconnect-v61` — `3e17eaf6e036c036b49c8a061e918528267948e0` | React, Vite, TypeScript et MapLibre ; GeoJSON statique de 43 mailles, `promoteId=maille_id`, priorité D/S via `priority_category`. La fiche réelle ne consommait pas encore le nouveau JSON territorial. Plugin Vite interne précédent lié à l'ancien périmètre. |
| M4 | `feat/backend-housin` — `466a4a7f331bf06428edbdb8d7c7fe2d9aca68c6` | FastAPI ; `/health`, `/zones`, `/zones/{zone_id:int}` ; deux exemples TEST, sans contrat de fiche réelle pour les identifiants canoniques. |

`docs/api_contract_m2_m4.md` a également été consulté. Il reste inchangé et ne démontre pas à lui seul le schéma effectivement utilisé par le frontend. Le format livré est donc explicitement une vue interne documentée, accompagnée d'une adaptation vérifiée contre le code inspecté ; il ne prétend pas être le contrat frontend définitif ni le contrat public.

Le patch M3 fourni touche huit fichiers : chargement de la grille, plugin local, propriétés complémentaires, couleur documentaire indépendante, cadrage de la nouvelle emprise, état de disponibilité de la carte et fiche au clic. Il réutilise les composants, styles et bibliothèque existants. Un routeur FastAPI optionnel expose les mêmes réponses en lecture seule et boucle locale. Aucune reconstruction du frontend/backend ni application du patch sur les branches de l'équipe n'a été effectuée.

## Sources réellement acquises

| Couche | Objets retenus sur le nouveau territoire | Mailles avec observation locale positive | Limites |
| --- | ---: | ---: | --- |
| Routes IGN BD TOPO | 17 335 | 96 | Attributs documentaires ; aucune mesure de trafic ni de perméabilité. |
| Matrices SRCE | 40 | 65 | 21 fragiles et 19 robustes ; sous-trame `-`, précision NULL ; SRCE 2014. |
| Réservoirs SRCE | 41 | 36 | Sous-trames sources conservées ; aucune qualification écologique actuelle ajoutée. |
| Haies IGN BD TOPO | 879 | 62 | Exhaustivité écologique et fonctionnalité inconnues. |
| Plans d'eau IGN BD TOPO | 5 | 5 | Trois Retenue, deux Réservoir-bassin ; zéro mare explicitement référencée, absence non démontrée. |
| Sites Cartofriches | 77 | 40 | 35 avec projet, 23 sans projet, 19 reconvertis ; tous ne sont pas des friches actuelles. |
| Inventaire DREAL zones humides | 172 | 41 | Typologie et modes de diagnostic hétérogènes ; pas une preuve uniforme d'habitat humide fonctionnel actuel. |

Les sources proviennent des services officiels IGN, DREAL et Cerema. Les licences des métadonnées ont été vérifiées **Licence Ouverte 2.0** et les attributions sont conservées. Références : [Cartofriches](https://www.data.gouv.fr/datasets/sites-references-dans-cartofriches), [matrices SRCE](https://www.data.gouv.fr/datasets/srce-corridors-basse-normandie), [réservoirs SRCE](https://www.data.gouv.fr/datasets/srce-reservoirs-de-biodiversite-normandie), [zones humides](https://www.data.gouv.fr/datasets/zones-humides-normandie). Les URL d'acquisition, empreintes des réponses et métadonnées précises figurent dans `provenance/sources_licences.json` et les rapports de préparation.

Les acquisitions initialement interrompues ont été reprises explicitement : pagination routière bornée avec attributs demandés, Cartofriches par plages HTTP contrôlées, zones humides par WFS borné avec **775 retournés sur 775 annoncés**. Les traces initiales d'échec restent conservées localement. Dix-sept géométries Cartofriches et 44 géométries de zones humides invalides dans la BBOX ont été refusées **sans réparation** ; leurs identifiants/motifs sont documentés. Ces 61 refus ne constituent ni des absences écologiques ni nécessairement 61 objets du territoire final.

L'inventaire PRAM/exhaustif de mares reste indisponible. Aucun inventaire d'espèces sensibles, ni objet fictif de substitution, n'a été ajouté. Les données brutes nationales, attributs de propriétaires, contacts et noms d'interprètes restent chez le producteur ; les couches de consultation transmises utilisent des listes fermées de champs.

## Résultats M2 et quarantaine

| Unité | Nouveau lot Caen et nord |
| --- | ---: |
| Événements détectés | **5 337** |
| Événements agrégés | **5 336** |
| Événements en quarantaine | **1** |
| Paires sources routes–matrices | 5 250 |
| Routes sources distinctes concernées | 4 360 |
| Liens maille–événement | 5 759 |
| Propriétaires canoniques / somme des comptes exclusifs | 5 336 |
| Mailles avec événements admis | **60** |
| Mailles sans événement admis observé | **41** |

Les comptes 60/41 sont calculés à partir des événements effectivement agrégés. Les comptes locaux peuvent se répéter entre mailles ; les comptes exclusifs ne se répètent pas. Tous les événements sont linéaires dans ce lot : 5 324 croisements détectés et 12 non concluants de frontière, conservés comme tels. Ces derniers ne servent pas de preuve aux règles V1/V2.

Le contrôle strict a refusé `rc_d1ac6a3bdcf06eb66226fd8699d2a9ae8f4cb7932fe8c924ba55cdaf4cf459f4`, issu de la route `TRONROUT0000002334259154` et de la matrice `TVB-COR-0AD80F5F1B25C5271D14`. Sa géométrie linéaire présente un résidu extérieur de **1,2493837390e-9 m** et une distance de Hausdorff de **1,1301883403e-9 m**, supérieure au budget ULP inchangé de **9,3313979112e-10 m**. Règle : `event_outside_territory` dans le validateur d'appartenance territoriale de l'agrégateur. La géométrie originale/WKB est conservée dans `quarantaine.gpkg` et son rapport. Elle n'est pas découpée, déplacée, réaffectée par proximité ni incluse dans les comptes/GeoJSON affichables.

Le rapport `strict.validation.json` conserve cet échec ; **`admis.validation.json` est le rapport actif du lot des événements admis**. Les validateurs de paires d'artefacts natifs ont été exécutés. Un second passage API a confirmé les mêmes identifiants, géométries et liens. Aucun événement n'a été modifié pour faire passer la validation.

Répartition des **5 336 événements admis**, sans pondération de danger :

| Attribut routier | Effectifs |
| --- | --- |
| Statut | En service 5 313 ; en projet 18 ; en construction 5 |
| Position | Au sol `0` : 5 203 ; surélevé `1` : 131 ; souterrain `-1` : 2 |
| Catégorie | Route à 1 chaussée 3 349 ; sentier 975 ; route empierrée 388 ; chemin 182 ; rond-point 180 ; route à 2 chaussées 144 ; type autoroutier 52 ; bretelle 40 ; escalier 26 |
| Voies / largeur | Chacun de ces deux attributs est NULL pour 1 623 événements ; autres répartitions dans `acceptation.json`. |
| Contexte urbain | Oui 4 821 ; non 515 |

La position au sol ne démontre pas la perméabilité. `ouvrage_connu` et millésime routier restent NULL ; vitesse source distincte d'un trafic mesuré. ENJ-01/ENJ-02 fournissent les observations et statuts de couverture ; les sorties qualifiées restent NULL lorsque les préconditions de complétude ne sont pas attestées.

## Deux cartes distinctes et règles effectivement appliquées

| Vue | Rouge | Orange | Jaune | Gris |
| --- | ---: | ---: | ---: | ---: |
| **Vérification documentaire V1–V4** | **27** | **33** | **9** | **32** |
| **Priorité écologique D/S** | **0** | **0** | **0** | **101 indéterminées** |

La vue par défaut porte visiblement la mention **« Indices cartographiques à vérifier — analyse exploratoire »**. La vue D/S est disponible séparément avec sa légende. Les captures `rapports/carte_exploratoire.png` et `carte_priorite_ecologique.png` montrent le même secteur dans les deux vues.

Les deux fichiers fournis par l'utilisateur ont été lus et leurs empreintes conservées : `docs/table_triage_exploratoire.json` et `analysis/construire_fiches_66.py`. Seules les constantes documentaires et la fonction `color_rule` du script historique sont réutilisées, jamais son `main()` ni ses effectifs/couleurs ou étiquettes TEST historiques.

- **V1** : paire locale linéaire documentée, route parmi Route à 1 chaussée / Route à 2 chaussées / Type autoroutier / Bretelle / Rond-point, `En service`, `position_sol=0`, classe source `Matrice fragile, fortement sensible à la fragmentation`, et surface positive de réservoir dans la maille.
- **V2** : autre paire route–matrice linéaire documentée.
- **V3** : surface positive de matrice ou réservoir sans telle paire observée.
- **V4** : éléments insuffisants. Des éléments seulement non concluants/frontaliers, quarantainés, une source critique indisponible ou un attribut critique manquant conservent explicitement l'incertitude et le gris. Aucun cas supplémentaire de gris technique n'est apparu dans les données acquises.

Les catégories, valeurs et relations ont été vérifiées contre les objets réellement acquis. Chaque fiche conserve les paires et identifiants d'événements justificatifs, objets réservoirs/matrices, observations de surface, règle, motif, disponibilité, versions et limites. Aucun nombre brut d'intersections, densité ou surface de maille partielle ne devient un score de gravité.

**Aucune synthèse D/S n'a été exécutée faute de préconditions écologiques et méthodes approuvées.** `priorite_examen` reste non calculée, `method_version=NULL`, couverture/synthèse et règle appliquée NULL. La présence de matrice n'a pas été transformée en enjeu moyen.

## Diagnostics et actions

Chaque fiche expose diagnostic élu, diagnostic technique, trois dimensions distinctes (enjeux documentés, activités humaines observées, fiabilité), comptes locaux/exclusifs, objets et attributs routiers, haies/eau/friches/ZH, qualité, sources, limites et préconditions manquantes. Les 41 mailles sans événement restent consultables ; zéro observation ne signifie pas absence de fragmentation ou d'habitat.

| Famille | Référence connue | Pistes documentaires | Statut scientifique |
| --- | --- | ---: | --- |
| R1 | A04 | 60 | Perméabilité et ouvrages à examiner ; aucune prescription de passage à faune. |
| R2 | A01 | 50 | Haies avec matrice/réservoir dans la maille ; ni rupture fonctionnelle ni plantation déduite de la densité. |
| R3 | A03 | 35 | Sites dont le statut source est friche avec/sans projet ; statut actuel, éligibilité et contexte à vérifier. |
| R4 | A02 | 20 | Plans d'eau ou réservoirs de sous-trame humide à qualifier ; aucune conversion automatique des ZH en mares ou création de mare recommandée. |

Total : **165 pistes dans 71 mailles**, **404 examens de préconditions R1–R4 non évaluables A2**, **zéro recommandation validée**. Les références d'actions n'inventent pas le contenu des fiches M5. Les méthodes familiales approuvées, sous-trames pertinentes, localisation adaptée, perméabilité réelle, espèces, continuité fonctionnelle, statut des sites, contexte foncier/pollution ou réseau hydrologique restent à qualifier selon la famille. Une première priorité écologique nécessite des preuves et validations humaines rattachées aux diagnostics, puis les préconditions des règles existantes.

Le catalogue officiel des 12 actions M5 et le contrat final M4 restent attendus. Les huit fiches manquantes ne sont pas créées. Le raccordement ultérieur par `action_id` est prévu et documenté.

## Fichiers, jointures et ingestion

Le ZIP contient notamment :

- `demo_interne/mailles.geojson` et `conflits.geojson` en WGS84, longitude/latitude, 2D, sans membre CRS ancien.
- `demo_interne/fiches_zones.json` : 101 fiches ; `actions_resultats.json` : 404 résultats validés au profil `actionResult` existant.
- `donnees/grille.gpkg`, `territoire.gpkg`, `sources_consultables.gpkg` : sept couches sources minimisées, EPSG:2154 ; `liens_observations.json` pour les relations locales.
- `rapports/` : GeoPackages natifs, quarantaine, rapports strict/admis, ENJ, contrôles et captures.
- `FORMAT_JSON.md` et `FORMAT_GEOPACKAGES.json` : structures, tables, champs, types, CRS et relations exhaustifs.
- `integration/m3_ingestion_caen.patch`, plugin Vite local, panneau de fiche et routeur M4 optionnel.
- `reproduction/` : cinq entrées M2 exactes, dépendances consignées et script de rejeu optionnel dans une nouvelle sortie ; code/règles et empreintes dans `provenance/`.
- `historique/` : ZIP 66 mailles original inchangé et isolé.
- `manifest.json`, `SHA256SUMS`, `verifier_lot.py`, `README.md`, `MESSAGE_M4_M5.md`.

Joindre par **(`territory_id`, `grid_version`, `maille_id`)**, et par `conflit_id` dans le même scope pour les événements. Les tables natives sans territoire hérité doivent être lues dans le scope déclaré du lot. Les `actionResult` gardent leur schéma existant ; leur portée est déclarée par l'en-tête du document. Ne pas joindre les pilotes uniquement sur `maille_id`.

Pour une démonstration immédiate par M3/M4 :

1. Extraire le ZIP ; exécuter `python3 verifier_lot.py` depuis sa racine.
2. Examiner puis appliquer le patch M3 contre le commit indiqué, avec `git apply --check` préalable dans son propre travail.
3. Depuis le frontend, définir `M2_CAEN_LOT_ROOT` vers la racine extraite puis lancer `npm run dev -- --host 127.0.0.1` ; conserver le mode réel.
4. Contrôler le badge 101 mailles, la mention exploratoire, une fiche au clic et la vue D/S distincte. Le README donne aussi les deux lignes d'inclusion du routeur FastAPI si M4 le préfère.

La démonstration locale ne nécessite **aucun recalcul scientifique**. Le plugin Vite ne sert que la liste fermée des quatre ressources internes et refuse les requêtes non locales/proxy. Un `vite build` seul ne déploie pas les données. Les adaptations n'ont pas été appliquées aux branches de l'équipe et aucun déploiement n'est affirmé.

## Vérifications et préservation

- **1 418 tests existants réussis**, 40 avertissements consignés ; aucune modification de tests/règles pour obtenir ce résultat.
- Build TypeScript/Vite réussi sur une copie temporaire de M3 avec son verrou de dépendances ; avertissement de taille de bundles conservé.
- Huit contrôles du routeur M4 réussis : données, fiche, portée, absent, refus proxy/externe et lecture seule. Ses versions de Starlette requièrent Python ≥ 3.11 ; le routeur a été testé sous Python 3.15.2, séparément de la .venv SIG Python 3.10.
- Test Chrome réussi : 101 mailles, mention visible, clic sur une maille de Caen, fiche chargée, deux vues séparées, mauvaise portée refusée et aucune erreur JavaScript.
- Critères d'acceptation 1–12 et 14 vérifiés sur les données réelles dans `rapports/acceptation.json` ; critère 13 vérifié sur une **extraction neuve du ZIP final**, avec manifeste/SHA et jointures, par le vérificateur sans dépendances SIG. Reçu final à côté du ZIP.
- **433 fichiers antérieurs inchangés** par SHA-256, ainsi que les deux fichiers de conventions ajoutés par l'utilisateur. Aucune modification suivie par Git ; aucun commit, push ou merge.

Le ZIP historique 66 mailles conserve l'empreinte **`e9b08b7f3e5879b20e8655850ce1dad783616a18c7eac2c8e96da6aad2726df5`**, ses 3 157/3 156/1 événements et ses comptes 40/26. Les résultats du pilote initial de 43 mailles et les autres travaux préexistants sont également conservés. Les nouveaux résultats ne remplacent ni ne requalifient les anciens.

## Ce qui reste à faire pour le 12 novembre

Les données et la démonstration dans la copie de validation sont prêtes. **M3/M4 doivent intégrer l'adaptation dans leur application et vérifier leur lancement local** ; aucun blocage d'acquisition n'empêche l'affichage du territoire traité. Le catalogue M5 et la confirmation du schéma applicatif final restent nécessaires à l'intégration définitive des fiches officielles, mais n'empêchent pas de consulter les diagnostics et pistes fournis.

Une publication en ligne reste soumise au circuit de validation prévu par le projet. Le verrou public **`test_data=False` demeure inchangé** ; les données réelles n'ont pas été maquillées en TEST et aucun dossier public n'a été alimenté. Le caractère exploratoire, la revue des licences, la minimisation attributaire et les limites sont explicitement conservés. Le lot ne permet toujours pas de recommander des travaux ni d'affirmer une priorité écologique validée.
