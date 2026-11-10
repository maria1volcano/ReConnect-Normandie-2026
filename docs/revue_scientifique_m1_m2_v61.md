# ReConnect Normandie V6.1 — Première revue scientifique M2 de M1

Date : **8 novembre 2026**. Revue de la **livraison effectivement accessible**, sans fusion ni modification des données ou des méthodes existantes.

**Avis : M1 est intégrable sous conditions pour un MVP exploratoire. La livraison Git seule ne permet pas encore de lancer la chaîne SIG M2 réelle.** Deux obstacles techniques sont vérifiés : les six GeoPackages annoncés sont absents du dépôt distant et local ; la grille livrée/reproduite dépasse la tolérance numérique de chevauchement de M2. Les mesures livrées constituent des observations cartographiques utilisables, pas une validation des priorités, des obstacles ou des actions.

## Périmètre, preuves et préservation

Les mentions suivantes s'appliquent à toutes les sections :

- **[V] Vérifié** : lecture du fichier/code réellement accessible, calcul exécuté ou comparaison Git. Une lecture de rapport vérifie ce qu'il affirme, pas les données sous-jacentes absentes.
- **[M1] Déclaré** : résultat de M1 non reproduit indépendamment faute de couche/source.
- **[EXT] Appui externe** : documentation officielle consultée le 8 novembre 2026 ; ce n'est pas une expertise de terrain sur le pilote.
- **[D] Décision restante** : hypothèse ou choix scientifique à valider, jamais un paramètre activé par cet audit.

Références figées :

| Élément | Référence contrôlée |
| --- | --- |
| Branche de travail | `feat/diagnostics-ecologiques` |
| HEAD M2 | `9a5fe89193a394dc457b070cae5436e25d60f139` |
| Référence M1 après `git fetch origin` | `origin/feat/m1-donnees-sig-v61`, `fc76d6230994af9aef27f42bb42e0374cd0c8251` |
| Ancêtre commun | `36a69bb4e3174f4a067275c303fdcc6ca4448899` |
| Package déclaré | `M1-V1`, daté du 3 novembre 2026 |
| Grille | `M1-CAND-1KM2-FLAT-L93-O0-V1` |

**[V]** Le handoff a été lu intégralement depuis la référence distante. Son « commit le plus récent » `66b8f57` précède le HEAD effectivement revu `fc76d62`. Les deux fichiers suivis déjà modifiés à l'ouverture étaient `analysis/detect_conflicts.py` et `docs/methode_m2.md` ; de nombreux fichiers M2 étaient non suivis, notamment les trois modules de priorité et les documents/tests R1–R4. Ils ont été lus dans leur état local, sans les remplacer par HEAD. Le statut initial détaillé et les empreintes des modules audités figurent dans l'annexe JSON.

**[V]** `fetch` a réussi après autorisation d'écriture de `FETCH_HEAD`. Aucun checkout, merge, commit, push, reset ou stash n'a été effectué. Une archive de la référence M1 a été extraite en répertoire temporaire ; aucun worktree n'était nécessaire puisque les GeoPackages n'étaient pas accessibles. Aucun script M1 `main()` n'a été lancé. La génération a été appelée **en mémoire**, sans écrire de GeoPackage ni remplacer de rapport M1. Aucun GeoJSON existant n'a été modifié.

Preuves de calcul : [résultats détaillés](audit_m1_v61/controles.json) et [script de contrôle](audit_m1_v61/verifier_livraison.py). L'inventaire de l'annexe contient les **44 fichiers** de la référence M1, leurs tailles et leurs SHA-256. Environnement temporaire conforme aux plages M2 : Python 3.10, GeoPandas 1.1.4, Shapely 2.1.2, pandas 2.3.3, NumPy 2.2.6, pyproj 3.7.1, pyogrio 0.13.0.

Les anciens audits R1–R4/D/S et leurs suites synthétiques n'ont pas été relancés. Les exécutions portent sur les données livrées, la génération de grille et les interfaces M2 directement concernées. Les tests M1 qui exigent les sources brutes n'ont pas été annoncés comme réexécutés.

## A. Inventaire vérifié de M1

| Livraison | Contenu réellement accessible [V] | Limite |
| --- | --- | --- |
| Géométries | `data/public/grille_pilote_wgs84.geojson` : 43 polygones avec attributs de grille | Seule couche géographique effectivement livrée dans Git |
| Mesures | `data/processed/sub_indicateurs.csv` : 43 lignes, 33 colonnes ; `sub_indicateurs_ocs.csv` : 227 lignes, 8 colonnes | Agrégats, aucune géométrie source ni liste d'objets par maille |
| Métadonnées | `sources.json`, `m1_grid_report.json`, `m1_measurements_report.json`, `m1_processing_report.json` | Les empreintes des fichiers absents ne prouvent pas leur livraison |
| Traitements | `analysis/prepare_m1.py`, `generate_hex_grid.py`, `calculate_m1_measurements.py`, `export_m3_data.py` | Lecture intégrale ; seule génération pure exécutée |
| Tests M1 | `test_prepare_m1.py`, `test_hex_grid.py`, `test_m1_measurements.py`, `test_export_m3_data.py` | Présents, mais exécution complète impossible sans les entrées |
| Dépendances | `analysis/requirements-m1.txt` | Incompatibilité pandas avec les exigences M2, voir H |
| Documentation | `M1_HANDOFF.md`, `quality_report.md`, `inventaire_sources.csv`, `M1_GRILLE_HEXAGONALE.md`, `M1_SOUS_INDICATEURS.md`, `M1_PIPELINE_SIG.md`, rapports `M1_ETAPE_1` à `6`, `pilote_decision.md`, `plan_acquisition_m1.md`, `data/raw/README.md` | Certaines notices reflètent une étape antérieure aux compléments Step 5 |
| Infrastructure | README et fichiers `.gitkeep`/`.gitignore` | Aucun backend/API M4 livré ici |

**[V] Absents** : `grille_pilote.gpkg` (ses deux couches), `reservoirs.gpkg`, `corridors.gpkg`, `routes.gpkg`, `sols.gpkg`, `zones_construites.gpkg`. Aucun `.gpkg` n'est suivi dans l'arbre M1 ; `data/processed/.gitignore` ignore `*.gpkg`. Aucun GeoPackage n'a été trouvé dans le répertoire de projet local, y compris parmi les fichiers ignorés. Aucun mécanisme de téléchargement du package traité ou pointeur LFS de ces fichiers n'apparaît dans l'arbre inspecté.

**[V]** Les sources brutes TVB, BD TOPO, OCS GE, haies, SIPAF, Cartofriches et zones humides sont aussi absentes et ignorées. Les nombres **40 réservoirs, 16 corridors, 1 924 routes, 3 358 sols, 83 zones construites, 1 181 haies, 0 SIPAF, 3 friches et 156 objets humides** sont donc **[M1]**, même si les CSV sont compatibles avec des observations de ces thèmes. Ils ne constituent pas un comptage indépendant de ces objets.

**[V]** La reconstruction « partielle » annoncée dans le handoff est incomplète : `calculate_m1_measurements.py` calcule d'abord les empreintes de huit sources brutes, puis charge directement les quatre compléments bruts. Recevoir les six GeoPackages ne suffirait pas à réexécuter cette étape sans ces sources ou sans adaptation future explicite.

## B. Pertinence du territoire pilote

**[V]** L'emprise correspond à un rectangle de coordonnées WGS84 `[-0.28, 49.20, -0.22, 49.26]`, projeté par ses quatre sommets puis relié par segments en Lambert-93. Son aire est **29,171588 km²**. La bbox Lambert-93 reproduite est :

`[460989.257242, 6904815.661232, 465631.045140, 6911663.950544]`.

Elle concorde avec `m1_processing_report.json` et `pilote_decision.md`. En revanche, la bbox `[341381.45, 6795383.00, 356532.01, 6817213.40]` du tableau de `quality_report.md` est **erronée pour ce pilote**, et ne doit servir à aucun contrôle de plausibilité M2.

**[V]** Les CSV présentent des réservoirs dans 15 mailles, des corridors surfaciques dans 30, des routes dans 40, des haies dans 37, des friches dans 3 et des zones humides dans 31. Cela établit une diversité de mesures, pas leur bon positionnement ni des relations écologiques entre elles. Les couches manquent pour contrôler les ponts, infrastructures, habitats et sites précis.

**[EXT]** Le Conservatoire du littoral décrit l'estuaire de l'Orne comme un ensemble de milieux littoraux, humides et dunaires sur plusieurs communes. Cette diversité rend le contexte intéressant, sans démontrer sa représentation dans notre rectangle. [Présentation officielle du site](https://www.conservatoire-du-littoral.fr/siteLittoral/147/28-estuaire-de-l-orne-14_calvados.htm).

**[D] Avis territorial : favorable comme secteur technique compact de la basse vallée de l'Orne, provisoire comme pilote écologique.** Le libellé « estuaire de l'Orne » ne vaut pas délimitation de l'ensemble de l'estuaire. Une confrontation cartographique aux limites du site et aux secteurs amont/aval est encore nécessaire. Ne pas transférer au rectangle les habitats ou espèces décrits pour tout l'estuaire. Le territoire n'a pas à démontrer les quatre actions pour être un MVP honnête ; les familles non évaluables doivent rester visibles. Un second site peut être étudié ultérieurement si nécessaire, sans généralisation à toute la Normandie.

## C. Grille hexagonale et frontières

### Résultats exécutés

| Contrôle [V] | Résultat |
| --- | --- |
| Identifiants | 43 chaînes uniques ; mêmes IDs entre GeoJSON, grille régénérée et CSV principal |
| Géométries livrées | 43 Polygon valides, aucun vide ; CRS lu EPSG:4326, reprojection EPSG:2154 réussie |
| Grille reconstituée | 43 mailles ; 15 intérieures, 28 de bordure, soit 65,1 % des mailles découpées |
| Hexagone complet | Côté 620,403239 m ; largeur sommet–sommet 1 240,806479 m ; hauteur 1 074,569932 m ; aire 1 000 000 m² aux erreurs flottantes près |
| Espacement des centres | 930,604859 m en X ; 1 074,569932 m en Y avec décalage alterné des colonnes |
| Aire minimale | 11,7282197377 m², maille `NORM-G1K-FLAT-R+006431-C+000501` |
| Fraction minimale | 0,0000117282 du million de m², soit **0,00117282 %** |
| Cohérence des aires CSV/grille | Écart maximal 0,000000499 m², cohérent avec six décimales d'export |
| Fidélité du GeoJSON reprojeté | Distance de Hausdorff maximale par maille ≈ 2,80 × 10⁻⁹ m par rapport à la grille régénérée |
| Reproductibilité | Deux générations en mémoire identiques ; **les deux empreintes sémantiques sont exactement celles de `m1_grid_report.json`** |
| Lacunes et excès par overlay GEOS | Aires calculées nulles par rapport au polygone pilote M1, pour la grille régénérée et le GeoJSON reprojeté |

Les deux empreintes reproduites sont `9D7C0AE4CD08F3AD6CE233AE59B8F7C777FEBB50BBC1B563933040B726752201` (découpée) et `7CD6CA2479CB0046DFA4090875BB37F79305FAD711C79487751C260DD8E041B0` (complète). Cela valide la génération pure et sa cohérence avec le rapport, **pas la lecture du GeoPackage absent**.

### Incompatibilité numérique effective avec M2

**[V]** `validate_spatial_coverage()` utilise `somme(aires des mailles) − aire(union)` et une tolérance absolue de **10⁻⁶ m²**. Sur la grille régénérée, la différence vaut **4,51132655 × 10⁻⁶ m²** ; sur le GeoJSON reprojeté, **4,83915210 × 10⁻⁶ m²**. Dans les deux cas, M2 retourne **`grid_overlap`**. Même prendre l'union de la grille comme territoire ne retire pas ce rejet.

Ces écarts sont compatibles avec l'arithmétique flottante aux grandes coordonnées Lambert-93 ; ils ne démontrent pas un chevauchement écologique significatif. La différence entre l'aire du pilote et celle de l'union varie elle-même à cette échelle. M1 emploie une tolérance de 10⁻⁴ m² dans son contrôle de grille. **[D]** Il faut convenir d'un contrôle numérique commun et le vérifier sur les couches reçues : inspection des intersections par paires, budget d'erreur lié à l'échelle des coordonnées et aux opérations, puis tolérance numérique documentée ou construction topologique commune. Aucune tolérance n'a été changée pendant la revue. Ce point est bloquant pour les chemins M2 qui valident la grille, même s'il est probablement facile à corriger.

### Le rectangle géographique et sa projection

**[V]** Le GeoJSON a une latitude maximale de **49,2600034799°**, légèrement supérieure à 49,26°. Ce résultat se reproduit : transformer seulement les quatre sommets n'est pas identique à transformer des frontières géographiques densifiées. Un diagnostic à 1 000 subdivisions par côté donne environ **0,415 m** de distance maximale entre les contours, **1 208,316 m²** du pilote M1 hors du rectangle densifié et **1 211,123 m²** dans le sens inverse. Ce scénario est un contrôle de construction géométrique, pas une nouvelle emprise officielle.

**[D]** Conserver pour ce MVP le contour M1 identifié, en le documentant précisément. Vérifier la couverture des extractions WFS fondées sur la bbox géographique avant de déclarer leurs zéros exhaustifs, en particulier dans cette mince bande de bord. Ne pas modifier silencieusement le contour : cela changerait les surfaces et la version du jeu de données.

### Petites mailles : options et recommandation

**[V]** Le fragment minimal ne contient dans le CSV ni route, ni haie, ni réservoir, ni corridor ; OCS le couvre entièrement. Il n'a donc pas produit ici de densité routière extrême. Le risque de comparaison demeure : une autre portion de **8 936,610 m²** porte **181,617 m** de route, soit environ **20 322,84 m/km²** après normalisation. Cette densité n'est pas un seuil de pression validé.

| Option [D] | Intérêt | Limite |
| --- | --- | --- |
| Conserver les portions et utiliser leur surface réelle | Compatible avec `H ∩ T`, IDs inchangés, mesures additives inspectables | Variabilité et forte sensibilité de bord ; ratios à montrer avec surface/fraction |
| Supprimer les petites portions | Affichage simplifié | Perte de couverture ; exige un seuil qui n'est pas justifié ici |
| Fusionner des portions avec des voisines | Réduit certains extrêmes | Casse le support hexagonal et les IDs ; règle de fusion supplémentaire |
| Mesurer les hexagones complets | Supports comparables | Exige des données au-delà du pilote ; ne pas compter l'extérieur inconnu comme zéro |
| Redéfinir le pilote suivant la grille | Réduit le découpage | Change la question territoriale et les acquisitions |

**Recommandation MVP [D] : conserver les 43 portions, les mesures sur leur surface effective et leurs IDs.** Exposer `is_boundary`, `cell_area_m2` et `pilot_fraction` dans le détail de qualité ; garder les mailles complètes comme comparaison descriptive distincte. Ne pas classer les mailles selon les seuls totaux bruts ou densités ; aucune suppression, fusion ou exclusion automatique de priorité n'est décidée ici. Un résumé territorial de proportions utilise le rapport des sommes d'aires, pas la moyenne non pondérée des pourcentages des 43 portions.

### Sensibilité technique exécutée

Les valeurs suivantes sont des **scénarios de grille**, sans seuil écologique et sans calcul d'effets sur les diagnostics faute de couches :

| Aire nominale | Ancrage | Mailles | Intérieures / bordure | Plus petite portion |
| --- | --- | ---: | ---: | ---: |
| 1 km² | M1, origine (0,0) | 43 | 15 / 28 | 11,728 m² |
| 1 km² | Décalage d'un demi-pas en X et Y | 43 | 19 / 24 | 1 463,302 m² |
| 0,5 km² | Origine (0,0) | 78 | 40 / 38 | 982,411 m² |
| 2 km² | Origine (0,0) | 27 | 7 / 20 | 57 156,100 m² |

**[V]** Le découpage et le fragment extrême sont sensibles à l'ancrage. **[D]** Le caractère stable des enjeux, événements et priorités ne peut être affirmé à partir de ces seuls comptes. Conserver 1 km² pour la première intégration technique est défendable, sous validation de son interprétation ; changer l'origine seulement pour faire disparaître le petit fragment serait une optimisation sans justification écologique.

## D. Sources, sous-indicateurs et nomenclatures

### Sources réellement documentées

Dans ce tableau, les comptes et schémas géographiques sont **[M1]** ; leur construction est confirmée par lecture du code **[V]**, mais leurs valeurs individuelles restent inaccessibles. Les licences doivent rester liées au paquet/version réellement reçu.

| Source | Provenance, date, licence documentées | Champs et géométrie préparés / utilisables | Limites pour M2 |
| --- | --- | --- | --- |
| Réservoirs | DREAL Normandie ; SRCE 2014, ressource publiée en 2024 ; Licence Ouverte 2.0 | 40 Polygon, EPSG:2154 ; `objet_id ← ID_RESV`, `objet_source_id ← ID_SRCE`, `nom`, `sous_trame ← MILMAJ_REG`, `millesime`, `precision_source=NULL` | Échelle régionale, catégories et précision non qualifiées ; pas d'inventaire actuel de biodiversité |
| Corridors | DREAL, ex-Basse-Normandie ; SRCE 2014 ; Licence Ouverte 2.0 confirmée sur la fiche officielle | 16 MultiPolygon, EPSG:2154 ; `objet_id` calculé avant découpe, `libelle_source ← ID_CORR`, `classe_corridor ← CLASS_CORR`, `sous_trame ← MILMAJ_REG`, `precision_source=NULL` | Matrices vectorisées, pas des axes de déplacement observés ; décodage des valeurs absent |
| Routes | IGN, WFS `BDTOPO_V3:troncon_de_route`, acquisition annoncée le 03/11/2026 ; Licence Ouverte 2.0 | 1 924 MultiLineString après découpe ; WGS84 → L93 ; `route_id ← cleabs`, `categorie ← nature`, `importance`, `date_modification`, `nombre_voies`, `largeur_chaussee` | `ouvrage_connu` et `millesime` forcés à NULL ; pas de trafic, perméabilité ni niveau physique exploitable transmis |
| Occupation du sol | IGN/DGALN, OCS GE 2.0 D014, 2023, livraison annoncée 2025 ; Licence Ouverte 2.0 | 3 358 MultiPolygon L93 ; `sol_id`, `couverture ← code_cs`, `usage ← code_us`, `millesime`, `source_objet`, `id_origine` | Couverture et usage ne sont pas une classe d'enjeu ; CSV détaillé limité à CS |
| Zones construites | Même paquet OCS GE | 83 MultiPolygon L93 ; `zone_id`, `millesime` | Enveloppe construite ; ne pas nommer sa surface « surface imperméabilisée » ni indice ZAN validé |
| Haies | Attribution M1 à BD Haie V2 mars 2024, images 2020–2022 ; Licence Ouverte 2.0 | 1 181 lignes annoncées, `cleabs` ; fichier brut WFS `BDTOPO_V3:haie` reprojeté en L93, sans export traité | L'identité entre ce flux courant BD TOPO et un paquet BD Haie V2 figé **n'est pas établie** ; vérifier le produit, les champs, le millésime et l'emprise réels |
| SIPAF | Ministère, parcs nationaux, Cerema ; export courant ; licence ouverte pour les données diffusables | 0 objet annoncé ; clé `Identifiant UUID` ; lecture `Tous_les_PAF`, reprojection depuis le CRS déclaré du fichier | CRS source encore « A VERIFIER » dans `sources.json` ; inventaire contributif ; zéro observation ≠ aucun ouvrage |
| Cartofriches | Cerema ; export 07/10/2026 ; Licence Ouverte 2.0 | 3 objets annoncés, `site_id` ; couche `friches_surfaces`, mesures d'aire après reprojection L93 | Sites potentiels, données hétérogènes ; CRS natif non renseigné. Le filtre `bbox` est passé en degrés **avant** reprojection : adéquation au CRS natif à contrôler, pas erreur démontrée |
| Zones humides | DREAL Normandie ; inventaires hétérogènes ; Licence Ouverte 2.0 | 156 objets retenus selon M1 ; clé `pk_zh` ; GML WFS L93 | Ni inventaire des mares ni fonctionnement hydrologique ; types, dates et statuts par objet non livrés |
| PRAM / EPFN | CEN Normandie / EPF Normandie | Sources déclarées indisponibles ; mesures NULL | Accès/réutilisation PRAM et ressource/licence EPFN non résolus d'après M1 ; aucune absence écologique déduite |

**[V]** Les couches principales sont découpées au pilote par `repair_clip`. Les compléments sont sélectionnés par intersection puis mesurés sur chaque maille. Cela permet en principe les croisements en L93, mais la découpe enlève le contexte extérieur nécessaire aux réseaux de haies, à l'isolement et à certains événements routiers. Les `make_valid` et filtrages de types existent dans le code ; l'absence d'objets géographiques empêche de contrôler leurs effets. Le rapport de traitement déclare zéro réparation sur P0. En cas futur de GeometryCollection, le code écarte l'objet de type inattendu au lieu d'en extraire les composantes : compter et examiner toute perte, sans prétendre qu'elle s'est produite ici.

**[EXT]** Le catalogue BD Haie distingue V1 et V2 et leurs méthodes ; il ne certifie pas l'extrait WFS choisi par M1. [Fiche IGN BD Haie](https://www.data.gouv.fr/datasets/bd-haie). SIPAF décrit des données d'ouvrages/observations alimentées par les gestionnaires, avec floutage des données taxonomiques sensibles : licence ouverte et précision publique ne doivent pas être confondues. [Site officiel SIPAF](https://passagesfaune.fr/). Le Cerema confirme l'incomplétude et l'hétérogénéité des champs de Cartofriches. [Fiche producteur Cartofriches](https://www.data.gouv.fr/datasets/sites-references-dans-cartofriches). La DREAL confirme le mélange photo-interprétation/terrain des zones humides. [Fiche producteur zones humides](https://www.data.gouv.fr/datasets/zones-humides-normandie).

### SRCE 2014 : portée défendable

**[EXT]** La fiche producteur confirme la vectorisation des matrices verte et bleue. [Couche corridors DREAL](https://www.data.gouv.fr/datasets/srce-corridors-basse-normandie). Le guide de bon usage décrit une restitution au **1/100 000**, des secteurs potentiellement favorables et la nécessité d'affiner localement les continuités. Cette échelle n'est pas une résolution raster ni une erreur métrique quantifiée ; aucun tampon n'en est déduit. [Guide officiel de bon usage](https://www.normandie.developpement-durable.gouv.fr/IMG/pdf/201404_SRCE_Guide-Usage.pdf) — extrait indexé consulté, téléchargement direct refusé par le serveur. La DREAL date l'adoption bas-normande du 29 juillet 2014. [Présentation DREAL des SRCE](https://www.normandie.developpement-durable.gouv.fr/les-schemas-regionaux-de-coherence-ecologique-srce-a3638.html).

**[EXT]** Le cadre régional actuel présenté par la Région est le SRADDET adopté en mars 2024 et approuvé en mai 2024, qui intègre les anciens schémas. Le fichier SRCE historique ne constitue pas à lui seul une analyse de conformité réglementaire actuelle ou une servitude à la parcelle. [SRADDET — Région Normandie](https://www.normandie.fr/le-sraddet).

**[D]** Usage retenable : contexte de continuités cartographiées historiquement, mesures d'emprise, sélection de secteurs à examiner. Usage non démontré : déplacement effectif d'espèces, obstacle physique actuel, priorité de travaux, état de conservation ou corridor local précis. En 2026, une publication de ressource en 2024 ne rajeunit pas les connaissances de référence 2014. Le croisement avec les routes courantes et OCS 2023 est possible géométriquement mais n'est pas une photographie écologique synchrone.

Les codes réellement présents de `classe_corridor` et `sous_trame` ne sont pas vérifiables sans GeoPackage. **Aucun mapping « réservoir → fort » ou « corridor → moyen » n'est validé.** Les champs `MILASO_*`, `MILMAJ_NAT`, `OBJ_ASSI` ou `DELIMIT` ne sont pas conservés par l'harmonisation actuelle ; leur intérêt doit être examiné dans les bruts sans inventer de valeurs ni redéduire les sous-trames associées.

### Formules et résultats des deux CSV

Avec `C = H ∩ T` (portion réellement analysée), la lecture de `calculate_m1_measurements.py` confirme :

| Groupe [V : formule, cohérence numérique] | Calcul | Interprétation permise |
| --- | --- | --- |
| Routes, haies | `longueur(union(objet ∩ C))`, en m | Linéaire cartographié observé ; pas un déficit de continuité |
| Réservoirs, corridors, OCS, construit, friches, humide | `aire(union(objet ∩ C))`, en m² | Emprise observée du thème ; unions indépendantes par source |
| Comptes d'objets | Nombre d'IDs distincts des objets intersectant C | Occurrences par maille, incluant les contacts de frontière ; pas nécessairement aire/longueur positive |
| Couverture OCS | `ocs_covered_area_m2 / cell_area_m2` | Fraction de surface géométriquement représentée |
| OCS par catégorie | Union par code CS, puis `ocs_area_m2 / cell_area_m2` | Fraction du support étudié ; ce n'est pas une fraction de la seule surface OCS |

**[V] Contrôles satisfaits :** les deux SHA-256 sont exactement ceux du rapport M1 ; 43 IDs principaux uniques ; 227 couples `(maille_id, ocs_code_cs)` uniques ; toutes les références OCS se rattachent à la grille ; aucune mesure négative ou non finie non nulle ; toutes les aires thématiques restent inférieures ou égales à l'aire de la maille dans le CSV. PRAM et EPFN sont vides dans les **43 lignes**, et non remplacés par zéro. Il n'y a pas d'autre valeur manquante dans ces tables.

La somme des aires OCS par code retrouve l'aire d'union de chaque maille à environ **10⁻⁶ m²** près ; l'écart maximal entre fraction publiée et fraction recalculée est **4,99 × 10⁻⁷**, cohérent avec les six décimales. La fraction OCS vaut 1 dans les 43 mailles. Cela confirme la cohérence des CSV ; **cela ne recontrôle pas les recouvrements ni lacunes de la couche OCS absente**.

**[V] Résumés des valeurs livrées**, non recomptage indépendant des sources : 218 793,509 m de routes, 108 859,625 m de haies, 3 502 366,333 m² de réservoirs, 10 860 687,991 m² de corridors, 5 265 376,203 m² de zones construites, 7 344,571 m² de friches et 2 288 687,028 m² de zones humides. Les sommes de comptes routiers (2 158), réservoirs (69), corridors (69), haies (1 301) et zones humides (191) ne sont **pas** des nombres d'objets distincts sur le pilote. Ne pas les opposer comme anomalies aux 1 924 routes ou 40 réservoirs annoncés. Même pour les longueurs, une ligne exactement sur une frontière commune peut être comptée dans deux mailles : un total territorial définitif doit être vérifié par union globale.

**[V]** Le code écarte du CSV OCS détaillé les catégories dont l'aire locale est ≤ **0,01 m²**. C'est une tolérance de sortie M1, pas un seuil écologique. Une catégorie absente de ce CSV peut donc désigner un résidu écarté ; ne pas y substituer automatiquement une absence validée. L'union par code n'empêche pas des chevauchements **entre** codes : vérifier la partition sur la couche livrée avant toute classification.

**[V]** Onze codes CS sont effectivement présents dans le CSV pilote, contre douze annoncés pour le paquet départemental : ce n'est pas une contradiction d'emprise. Leur lecture descriptive est :

| Code | Libellé descriptif |
| --- | --- |
| `CS1.1.1.1` | Zones bâties |
| `CS1.1.1.2` | Zones non bâties imperméables |
| `CS1.1.2.1` | Zones à matériaux minéraux |
| `CS1.2.1` | Sols nus |
| `CS1.2.2` | Surfaces d'eau |
| `CS2.1.1.1` | Peuplements de feuillus |
| `CS2.1.1.2` | Peuplements de conifères |
| `CS2.1.1.3` | Peuplements mixtes |
| `CS2.1.2` | Formations arbustives et sous-arbrisseaux |
| `CS2.1.3` | Autres formations ligneuses |
| `CS2.2.1` | Formations herbacées |

**[EXT]** OCS GE sépare couverture CS et usage US ; le construit englobe le bâti et son environnement. La documentation indique une échelle d'emploi de 1/5 000, une précision métrique et une généralisation avec unités minimales d'intérêt, notamment 500/2 500 m² selon le contexte. Ces spécifications du produit ne sont ni une précision garantie par objet ni une raison de supprimer nos fragments. [Descriptif IGN OCS GE NG, révision juin 2026](https://data.geopf.fr/annexes/ressources/documentation/DC_OCSGE_NG.pdf) ; confronter cette version à la notice du paquet 2023/2025 reçu.

**[D]** La classe herbacée, majoritaire dans le CSV, ne prouve ni prairie permanente ni habitat favorable à une espèce. `CS1.2.2` ne permet pas d'identifier des mares ou leur régime hydrologique. Le CSV ne conserve pas `usage` : il est insuffisant pour distinguer les usages au sein d'une couverture. Les zones construites et CS bâties sont des mesures différentes ; ne pas les additionner.

### NULL, zéro et traçabilité

**[V]** Les statuts non exhaustifs des compléments sont présents. Mais `p0_coverage_status=complete_for_provisional_pilot` est une **constante écrite dans le code**, sans preuve spatiale, contrôle de pagination WFS, validation thématique, date ou validateur par source. Il ne satisfait pas `CoverageEvidence(status='validated', ...)` de M2. Les zéros restent des « zéro objet/mesure observé dans l'extrait », jamais un constat d'absence actuelle d'ouvrage, haie, friche ou habitat.

**[V]** `source_ids` trace huit jeux au niveau de chaque ligne, avec une liste constante. Elle ne donne pas les IDs d'objets, les millésimes individuels, les sous-trames ou les liens route–corridor. Les références croisées sont possibles au niveau des sources, pas reconstituables au niveau des phénomènes. Les documents d'acquisition sont en retard sur Step 5 pour plusieurs statuts ; `sources.json` garde aussi certains CRS « A VERIFIER » malgré le traitement déclaré.

## E. Compatibilité précise avec les fonctions M2

| Fonction ou entrée | Compatibilité réellement constatée | Adaptation / information nécessaire |
| --- | --- | --- |
| `validate_inputs.read_layer` | Lit GPKG/GeoJSON, pas les CSV [V] | Fournir les GPKG ; pour la grille à deux couches, préciser `grille_pilote` |
| GeoJSON grille M1 | Lisible, `maille_id` et version directement compatibles [V] | Se trouve dans `data/public`, refusé par les restrictions de chemins des CLI ; éventuelle copie distincte sous `data/processed`, puis reprojection. Rejet numérique de grille à résoudre |
| CSV principaux et OCS | Consommables directement pour **audit et statistiques descriptives** [V] | Aucun des CLI enjeux/conflits n'ingère ces CSV comme substitut aux géométries ; typage des identifiants en chaînes, booléens et valeurs nulles explicite |
| `compute_enjeux` / `indicateurs_enjeux.py` | Schémas M1 annoncés compatibles pour polygones de réservoirs/corridors [lecture V, couches M1] | `territory` polygonal absent comme livraison séparée ; grille et couches à recevoir ; preuve de complétude pour ENJ-01 ; dictionnaire de sous-trames pour ventilation |
| `run_enjeux.py` | Entrées géographiques sous `data/processed`, sortie interne GPKG + validation JSON [V] | Construire une configuration et un territoire traçables ; ne pas confondre l'union observée des sources avec leur emprise de complétude |
| `detect_route_corridor_conflicts` | Accepte routes linéaires et corridors polygonaux, calcule avant rattachement aux mailles [V] | `SourceFields(id_column='route_id', category_column='categorie')` et `SourceFields(id_column='objet_id', category_column='classe_corridor')` selon le code M1 ; vérifier les colonnes sur les couches reçues |
| `run_conflicts.py` | Configuration obligatoire avec IDs sources ; chemins sous `data/processed` [V] | Pas de configuration réelle livrée ; absence de référence métrique de précision ; ne pas renseigner une distance inventée |
| `aggregate_conflicts` | Relations événement–mailles plusieurs-à-plusieurs, propriétaire canonique, comptes observés/complets séparés [V] | Grille rejetée actuellement ; vérifier les frontières et préserver la table de liens |
| `prepare_priority_inputs.py` | Exige diagnostics, registres de preuves/sources, périmètre pilote, versions, méthodes et contrôles [V] | Ces objets ne sont pas des attributs bruts attendus de M1 : **travail M2 restant** ; absence de mapping scientifique d'enjeu et d'applicabilité |
| `evaluate_priorities.py` | Reçoit des diagnostics normalisés ; n'interprète pas les CSV M1 [V] | Périmètre et méthodes approuvés, enjeu et QA par diagnostic ; ne pas créer ces attestations pour faire fonctionner la table |
| `export_priority_results.py` | Sérialisation JSON **interne**, pas géographique [V] | `prepare_priority_result_json()` ne remplace ni filtre public ni contrat M4 approuvé |
| `export_m2_contract.py` | Deux GeoJSON `m2-m4.proposal-1`, production désactivée [V, garde exécutée] | `test_data=False` lève `ValueError`. Aucune diffusion réelle possible via ce module tel quel ; jamais marquer M1 réel `test_data=True` pour contourner la garde |

### Attributs et conventions qui restent à fournir

**[V]** Les identifiants de maille sont des chaînes stables et ne nécessitent pas de renumérotation. `route_id`, `objet_id`, `sol_id`, `zone_id` sont prévus par le code M1. L'ID corridor est un hash des attributs et de la géométrie source **avant** découpe : il sert de clé technique de cette livraison, mais sa stabilité entre rééditions de source n'est pas acquise. `ID_CORR` est conservé comme libellé, pas arbitrairement réutilisé comme clé unique.

**[V/M1]** Les champs utiles mais manquants ou inconnus comprennent : `precision_source` (NULL), ouvrage et niveau physique des routes, trafic et éléments de franchissabilité, valeurs et dictionnaires des sous-trames/classes, couverture validée par thème et période, contexte extérieur au pilote. Ne pas configurer un `level_column` absent ; toute signification d'ouvrage/niveau demande `context_reference`.

**[D]** Les `diagnostic_id`, `enjeu_classe`, `enjeu_methode_id`, `validite_positive`, `validite_absence`, décisions de contradiction et familles attendues sont à produire par M2 à partir de contrôles documentés. Leur absence dans M1 n'est pas un motif pour inventer des attributs M1 ou modifier R1–R4.

## F. Faisabilité des diagnostics réels et des priorités

| Diagnostic | Ce qui est faisable maintenant [V] | Après livraison des couches | Ce qui ne peut pas être conclu |
| --- | --- | --- | --- |
| Réservoirs / ENJ-01 | Audit de `reservoir_area_m2` et ratios descriptifs sur `cell_area_m2` | Recalcul d'aire observée ; ENJ-01 officiel seulement si complétude réellement validée | `compute_enjeux` conserve `enj_01_pct=NULL` sans cette validation, même si l'aire observée est positive |
| Corridors / ENJ-02 | 30 mesures surfaciques positives dans le CSV | Présence observée possible sans complétude globale ; zéro confirmé seulement sur couverture validée | Fonctionnalité actuelle, flux d'espèces, importance locale |
| Pression routière | Longueurs et occurrences descriptives | Intersections exactes lignes routes × polygones corridors × territoire, souvent **segments dans une matrice**, parfois contacts ponctuels | Nombre de passages bloqués ou nombre d'ouvrages nécessaires |
| Contexte OCS / construit | Fractions et classes descriptives | Croisement CS/US, vérification de la partition et du support construit | Sensibilité écologique, imperméabilisation ou artificialisation réglementaire automatiques |
| Bocage, friches, humide | Mesures géométriques par maille | Inspection d'objets, réseaux/relations sous méthodes explicites | Rupture de haie, potentiel de renaturation ou isolement humide à partir des seuls agrégats |

**[V]** Aucun nombre réel d'événements route–corridor n'a pu être calculé : les deux géométries sources manquent. Une route et un corridor présents dans la même maille ne prouvent même pas leur intersection. Une fois les couches reçues, le détecteur actuel peut conserver `croisement_detecte` ou `non_concluant` ; `conflit_potentiel` demande une règle contextuelle approuvée ou une qualification documentée ; `obstacle_confirme` exige une preuve externe localisée. Les ponts, tunnels, niveaux et ouvrages ne sont pas résolus par une intersection XY, ni par la seule présence de Z.

**[V]** `derive_positive_evidence()` exige une revue liant sources, échelle, localisation et période. Sans précision documentée, la localisation n'est pas automatiquement exploitable ; l'interface demande sa résolution documentée. `classify_ecological_stakes()` sans décision retourne `inconnu` et méthode NULL ; `derive_applicability()` retourne `inconnue` : ces deux comportements ont été exécutés et constatés. Les méthodes D/S existent, mais M1 ne fournit pas les décisions qui les rendent scientifiquement applicables.

### Frontières et dénombrement

**[V, lecture du code]** Un événement peut traverser plusieurs mailles. L'agrégation conserve toutes les relations `interieur`/`frontiere` et attribue un propriétaire canonique déterministe parmi les mailles admissibles. Il ne s'agit pas d'une attribution écologique exclusive. Utiliser le nombre global d'événements distincts ou les propriétaires exclusifs, jamais la somme des comptes locaux. Un contact exclusivement sur le bord du pilote reste `non_concluant` et ne peut être promu comme preuve intérieure.

**[D]** Sur les couches reçues, examiner particulièrement les segments parallèles à une frontière, les événements coupés par l'emprise et le fragment minimal. Les écarts numériques déjà observés justifient une vérification explicite des liens ; aucune affectation par proximité, déplacement ou centroïde n'est autorisée. La convention actuelle est adaptée à l'inspection, sous cette vérification.

### Statut des règles D/S sur la livraison actuelle

Cette matrice vérifie uniquement les **préconditions réelles**, sans réauditer les tables :

| Règles | État actuel | Condition nécessaire |
| --- | --- | --- |
| D0 | Non justifiée par la seule livraison | Non-applicabilité positivement documentée ; source manquante ≠ hors champ |
| D1 | État d'attente possible après construction d'un diagnostic valide | Applicabilité inconnue ; ne pas inventer une contradiction pour exprimer un manque |
| D2 | État d'attente attendu si applicabilité établie mais enjeu inconnu | Mapping d'enjeu/méthode absent ; diagnostic et périmètre structurés requis avant appel |
| D3–D4 | Utilisables pour représenter l'évaluation incomplète | Pression non évaluée/non concluante, ou preuve positive non validée, sans fausse preuve |
| D5 et D8 | Non évaluables actuellement | Enjeu documenté et conflit potentiel/obstacle étayé absents |
| D6 et D7 | Partiellement préparables, pas calculables comme résultats réels ici | Croisements réels, QA positive et classe d'enjeu approuvée |
| D9 | Non évaluable | Complétude spatiale, thématique et temporelle + absence effective des signaux ; les zéros CSV n'y suffisent pas |
| D10a | Non évaluable actuellement | Croisement exploitable et enjeu faible documenté ; aucun faible inventé |
| S0 | Pas de cas hors territoire dans les 43 portions positives | Hors territoire seulement si surface étudiée nulle |
| S1 / S2 | Pas de priorité élevée/modérée réelle démontrable | Diagnostic élevé/modéré valide selon les préconditions précédentes |
| S3 | Non justifiable | Toutes les familles attendues suffisamment conclues ; aucune preuve de ce type livrée |
| S4 | Résultat d'attente possible, après configuration approuvée | Périmètre versionné et diagnostics/familles manquantes explicites ; pas de carte publiée à partir d'un périmètre fictif |

**[D]** Ne pas appeler D/S tant que le périmètre pilote, les méthodes et les registres n'existent pas. Une sortie technique indéterminée ne remplace pas leur approbation. Pour la première expérimentation, une famille route–corridor peut être proposée comme seule famille décisionnelle, avec R2–R4 exploratoires, **si l'équipe approuve explicitement ce périmètre avant calcul**. Ne pas le réduire maille par maille ou pour obtenir des couleurs.

### Transmission à M4 : contrat actuel et évolution

**[V]** Aucun GeoJSON de production M2 n'a été généré. Le GeoJSON de grille M1 ne respecte pas à lui seul le contrat des résultats M2 : il lui manque diagnostics, qualité de preuve, relations aux conflits et états de calcul.

| Support | Champs que prévoit le code/contrat actuel | État réel |
| --- | --- | --- |
| `mailles.geojson` | `maille_id`, trois versions, `statut_analyse`, `priorite_examen={etat,valeur}`, diagnostics, nombres observés/complets/exclusifs, qualité routes/corridors, `conflit_ids`, `action_ids`, `etat_actions` | Export proposal-1 synthétique : priorité `non_calculee`, actions vides ; pas encore les priorités D/S réelles |
| `conflits.geojson` | `conflit_id`, type, niveau de preuve, statut, IDs sources autorisés, `maille_ids`, précision d'affichage, limites publiques, méthode, relation au territoire, décision de diffusion | Géométrie masquée et IDs sources exclus par défaut ; références privées non recopiées |
| Enveloppes des deux collections | `contract_version`, `test_data`, `statut_diffusion`, provenance et résumé cohérents | Exclusivement synthétique actuellement |
| `fiches_zones.json` proposé | Diagnostics détaillés, règles D/S, raisons et limites, familles manquantes, versions, sources et preuves selon droits | À construire avec projection publique filtrée ; sérialisation interne ≠ autorisation de diffusion |
| Compléments à prévoir | Surface effective, fraction de maille, bordure, couvertures par thème, périodes ; table interne de liens événement–maille | Champs présents en M1 mais non tous transmis par la liste d'autorisation actuelle ; évolution de contrat à approuver |
| `catalogue_actions.json` | Catalogue M5, correspondances R1/A04, R2/A01, R3/A03, R4/A02 | Non livré ici ; M4 reste propriétaire du moteur d'actions |

**[D]** Pour de vraies données, convenir avec M3/M4 d'une version de contrat autorisant la production et les états D/S/actions, avec droits et attribution. Ne pas modifier silencieusement `proposal-1` et ne pas exposer le résultat interne complet de `prepare_priority_result_json()`.

## G. Faisabilité des quatre familles d'actions

Le classement ci-dessous est un **avis de faisabilité du projet**, pas un résultat du moteur R1–R4. Aucune attestation familiale réelle n'est produite ici. Les règles et correspondances existantes restent inchangées.

| Règle | Classement sur les éléments disponibles | Information partielle réellement exploitable | Manquants décisifs |
| --- | --- | --- | --- |
| **R1 → A04 — passages à faune** | **Seulement une piste conditionnelle** ; détection géométrique potentiellement suffisante pour démarrer après livraison/contrôles | Totaux routiers et surfaciques TVB ; aucun événement localisé livré ; SIPAF=0 observation, pas absence d'ouvrage | Routes/corridors, sous-trame et pertinence d'échelle, précision, qualification, contexte pont/tunnel/ouvrage et vérification actuelle. Pas de passage à construire recommandé |
| **R2 → A01 — haies** | **Non évaluable avec les données disponibles pour la règle** | 108,860 km de haies annoncées par les mesures ; contexte OCS ; cela permet un descriptif | Géométrie du réseau, identification exacte du produit, couverture et contexte extérieur, méthode de lacune/topologie et relation à la sous-trame. Une densité faible n'est pas une rupture |
| **R3 → A03 — friches** | **Seulement une piste conditionnelle pour examiner les sites**, pas déclenchement de règle établi | 3 mailles avec mesure positive Cartofriches ; EPFN n'est donc pas indispensable à toute poursuite | Géométries/IDs et état actuel des sites, relation à une continuité, méthode de voisinage, enjeux existants et contraintes. Coprésence par maille ≠ relation de voisinage |
| **R4 → A02 — mares** | **Non évaluable avec les données disponibles** | Zones humides et eau OCS fournissent un contexte cartographique | Inventaire de mares/habitats pertinents, réseau et couverture, méthode d'isolement/lacune, contexte hydrologique. Zone humide ≠ mare, eau OCS ≠ inventaire exhaustif |

**[V/M1]** L'inventaire de sources mentionne des mares du Parc Normandie-Maine, limitées à des communes de l'Orne/Sarthe et anciennes (2003–2013), non acquises pour ce pilote du Calvados : ce n'est pas un substitut local disponible à PRAM. Les autres candidats (cours d'eau SRCE, forêt, Natura 2000, RPG) ne sont pas livrés comme couches exploitables ; ne pas les compter comme preuve partielle déjà obtenue.

**[D]** Après récupération des couches, R1 et R3 sont les voies les plus courtes vers une **étude d'opportunité** conditionnelle. Aucune famille n'atteint actuellement « données et méthode potentiellement suffisantes, sous validation » pour une conclusion étayée complète. Cela ne remet pas en cause le contrat R1–R4 : ses tests synthétiques attestent une convention de traitement, pas la disponibilité des faits ni leur vérité sur ces sites.

## H. Anomalies et corrections proposées

**Aucune des corrections ci-dessous n'a été appliquée.** Le caractère bloquant dépend de la sortie visée : un manque de preuve d'action ne bloque pas des statistiques descriptives.

### Bloquants pour les calculs ou sorties concernés

| ID | Constat / preuve | Impact | Correction minimale à préparer |
| --- | --- | --- | --- |
| B1 | Six GPKG absents [V] ; ignorés par Git | Recalcul SIG, croisements et inspection des valeurs sources impossibles | Transfert séparé des six fichiers avec manifeste, couches, tailles et empreintes ; contrôle en lecture seule |
| B2 | `grid_overlap` reproduit sur la grille réelle et régénérée [V] | `compute_enjeux` et agrégation refusent cette grille | Harmoniser le contrôle numérique M1/M2 après diagnostic de précision ; test ciblé sur cette grille, sans seuil écologique |
| B3 | Territoire et configurations M2 non livrés [V] | CLI réels non prêts | Matérialiser ultérieurement le contour exact M1 et les mappings de champs ; distinguer territoire, emprise plausible et couverture source |
| B4 | Couvertures validées, mapping d'enjeu, précision et décisions pilote absents [V/M1] | ENJ-01 validé, absences, priorités concluantes et qualifications d'actions non justifiables | Dossiers de validation ciblés par thème/sortie ; conserver les observations et inconnues jusque-là |
| B5 | Production refusée par `prepare_m2_contract(test_data=False)` [V exécuté] | Livraison publique/API de résultats réels bloquée | Évolution de contrat et revue M2/M3/M4, avant activation de production |
| B6 | Mesures dépendantes des huit bruts, dont quatre compléments non exportés [V] | Reconstruction M1 complète et validation indépendante des mesures impossibles | Livrer les extraits figés et les informations de chargement, ou préparer une adaptation de reproduction explicite ; pas de téléchargement courant présenté comme le même snapshot |

### Corrections importantes, sans bloquer le descriptif initial du MVP

| ID | Constat | Correction / décision |
| --- | --- | --- |
| I1 | Bbox L93 de `quality_report.md` fausse [V] | Aligner la notice sur le contour contrôlé et le rapport de traitement |
| I2 | `p0_coverage_status` constant, non assimilable à `validated` [V] | Métadonnées par source, justification d'emprise/thème/période, pagination et version d'extraction ; ne pas fabriquer un statut validé |
| I3 | Bord géographique versus segments projetés : différence submétrique reproduite [V] | Nommer exactement le contour et vérifier les bandes non couvertes par les extractions ; ne pas changer l'emprise sans version |
| I4 | 28 mailles de bordure ; fragment 11,7 m² [V] | Conserver support réel et métadonnées visibles ; pas de classement brut ou seuil de suppression inventé |
| I5 | Attribution BD Haie V2 d'un flux `BDTOPO_V3:haie` non démontrée [V] | Vérifier identité/version du produit et les métadonnées de l'extrait ; garder l'actualité variable si c'est ce que permet la source |
| I6 | CRS SIPAF/Cartofriches et valeurs TVB non vérifiables [V/M1] | Inspection des schémas/CRS/valeurs reçus ; contrôler le bbox Cartofriches dans le CRS de lecture |
| I7 | Des attributs sources utiles ne sont pas transmis ; `ouvrage_connu=NULL` [V] | Évaluer un complément traçable des bruts si nécessaire ; ne pas reconstituer des niveaux ou ouvrages imaginaires |
| I8 | Exigences M1 `pandas==3.1.0` versus M2 `pandas>=2,<3` [V] | Environnements séparés ou dépendances communes testées ultérieurement. Ne pas installer les deux fichiers d'exigences ensemble |
| I9 | Handoff Python 3.14+ versus rapports Python 3.12 [V documentaire] | Aligner environnement déclaré et environnement effectivement producteur ; ne pas confondre reproduction pure réussie sous Python 3.10 et validation complète du pipeline |
| I10 | Inventaire/statuts et `pilote_decision.md` datent parfois d'avant Step 5 [V] | Réconcilier les étapes ; distinguer acquisition, fichier livré et validation scientifique |
| I11 | Compteurs par maille additifs en apparence, pas d'IDs d'objets dans CSV [V] | Éviter les sommes de nombres d'objets ; transmettre tables de liens internes si nécessaires |
| I12 | Mares, lacunes bocagères, relations friche–TVB et hydrologie non décrites [V] | Laisser R2/R4 non évaluables et R1/R3 à l'état de pistes de travail ; produire les faits avant toute exécution du moteur M4 |

### Améliorations facultatives

- **[D]** Un paquet de reproduction figé, téléchargeable séparément de Git, avec dictionnaires, conditions de réutilisation et contrôle des empreintes simplifierait l'intégration.
- **[D]** Des acquisitions autour du pilote permettraient d'examiner les réseaux et événements coupés ; l'emprise doit découler de la méthode et du contexte, sans rayon écologique choisi par défaut.
- **[D]** Après disponibilité des couches, comparer diagnostics sur les scénarios d'ancrage/résolution et préparer un second site si une famille exige un contexte absent du pilote.

## I. Recommandation d'intégration Git

**Intégrable sous conditions. Pas de fusion immédiate recommandée comme preuve que M2 peut calculer les diagnostics réels.** Les CSV, rapports et scripts apportent une base utile et la génération de grille est reproductible. Les réserves techniques identifiées sont circonscrites ; elles ne justifient pas un rejet global de M1.

**[V]** Par rapport à l'ancêtre commun, M2 a 20 chemins modifiés dans les commits et M1 43 ; leur intersection est vide. Cela suggère une intégration de contenu peu conflictuelle, mais **ce n'est pas une simulation de merge** et cela ne traite pas les modifications locales non commitées. Les suppressions apparentes de modules M2 dans un simple diff entre branches signifient surtout que M1 ne les possède pas ; elles ne prédisent pas leur suppression par un merge à trois voies.

Conditions techniques minimales : recevoir/identifier les fichiers géographiques figés, régler le rejet numérique de grille, préparer territoire/configurations, garder un environnement de dépendances cohérent. Conditions de portée scientifique : autoriser d'abord des mesures observées et des candidats géométriques ; ne pas promettre des absences validées, des priorités qualifiées ou quatre actions avant leurs validations spécifiques. Le développement d'une chaîne interne peut précéder l'évolution du contrat public, dont la production reste bloquée.

**[D]** Une intégration future doit être préparée dans un checkout/worktree isolé, en préservant explicitement les travaux M2 non commitées. Cette revue n'autorise ni commit ni fusion et n'en a effectué aucun.

## J. Plan technique minimal pour les premiers calculs M2

Les étapes ci-dessous sont un plan, **pas des modifications déjà appliquées**.

1. **Recevoir le snapshot géographique.** Les six GPKG sont nécessaires à la revue P0 complète. Pour le premier calcul enjeux/conflits, grille, réservoirs, corridors et routes suffisent avec le territoire ; sols/construit servent au contexte et aux contrôles OCS. Ajouter les compléments bruts ou extraits figés pour les familles correspondantes. Vérifier tailles, SHA-256, listes de couches, CRS, champs, valeurs, validité et couverture. Ne pas substituer silencieusement un WFS actuel aux fichiers du 03/11/2026.
2. **Rendre l'exécution M2 possible.** Convenir du contrôle numérique de grille, puis revalider les couches reçues. Utiliser la couche `grille_pilote` découpée, garder les hexagones complets pour le contrôle du support ; matérialiser le territoire exact M1 et ses versions. Conserver séparément les empreintes des fichiers et l'empreinte géométrique de territoire attendue par M2.
3. **Écrire ultérieurement les configurations explicites.** Grille : `maille_id`, EPSG:2154. Routes : `route_id`/`categorie`. Corridors : `objet_id`/`classe_corridor`. Sous-trames seulement après dictionnaire des valeurs réellement observées. Couvertures d'abord inconnues ou déclarées selon les preuves ; pas de booléen global validé par simple lecture du CSV. Pas de distance de précision sans justification documentaire.
4. **Exécuter ENJ-01/02 en interne.** `python -m analysis.run_enjeux` avec fichiers/couches/configuration identifiés, sorties nouvelles sous `data/derived/`. Conserver les aires observées, ENJ-01 NULL tant que sa complétude n'est pas validée, et les présences de corridors observées sans interprétation fonctionnelle. Vérifier le couple GPKG/rapport, les 43 IDs, les surfaces et la cohérence avec les agrégats M1.
5. **Détecter les candidats route–corridor.** `python -m analysis.run_conflicts`, sans qualification externe inventée ; récupérer événements, mailles et table des liens. Inspecter la géométrie des segments dans les matrices, leurs sources et leur relation au territoire. Vérifier les nombres distincts, propriétaires canoniques, frontières et précision. Les données peuvent être techniquement analysées avec une complétude inconnue ; leurs zéros ne deviennent pas des absences validées.
6. **Revoir trois secteurs réels contrastés.** Les sélectionner après inspection des objets : intersection candidate intérieure, absence d'observation avec couverture à examiner, cas de frontière/petit support. Si le pilote ne présente pas ces cas, le constater au lieu de fabriquer des secteurs. Résoudre l'échelle et la localisation, demander les informations d'ouvrage pertinentes et enregistrer les preuves/date/portée. Ce travail reste à faire ; aucune revue terrain indépendante n'a été simulée.
7. **Décider le périmètre de priorité.** Déclarer familles attendues, méthodes autorisées, versions, registres de sources/preuves et limites. Approuver ou conserver inconnues les classes d'enjeu et l'applicabilité. Construire des diagnostics typés via les interfaces existantes, puis seulement appeler `evaluate_priorities`. Ne pas changer D/S pour obtenir une carte plus discriminante.
8. **Préparer la restitution et les actions.** Conserver R1–R4 inchangées ; produire leurs faits familiaux réels ou leurs manquants explicites. Faire évoluer avec M3/M4 le contrat de production, les champs de qualité de bordure et le filtre de diffusion. Les fiches détaillées portent les limites et les résultats indéterminés ; aucune donnée réelle n'est déguisée en synthétique.

**Décision finale de revue : GO conditionnel pour intégrer M1 et commencer les mesures exploratoires après résolution de B1–B3 ; NO-GO en l'état pour annoncer une chaîne complète de diagnostics, de priorités et d'actions scientifiquement validés.** Les informations supplémentaires de B4/B6 et la validation M2 conditionnent ces conclusions ; B5 conditionne la diffusion par le contrat M4. Le pilote peut servir le MVP sans prétendre représenter toute la Normandie ni rendre les quatre familles évaluables.
