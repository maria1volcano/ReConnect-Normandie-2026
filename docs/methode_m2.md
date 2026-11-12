# ReConnect Normandie V6.1 — méthode M2 : validation SIG et enjeux

## Périmètre et état du dépôt

La chaîne implémente les contrôles des entrées, ENJ-01, ENJ-02 et désormais les
événements géométriques route–corridor décrits dans la section dédiée ci-dessous.
À l'inspection initiale du dépôt le 30 octobre 2026, seul un README minimal
était versionné ; aucun PRD V6.1, fichier SIG ni environnement Python configuré
n'était présent. La demande jointe constitue donc le périmètre de travail, sans
présumer du schéma des futures livraisons M1.

Les tests utilisent exclusivement des géométries **synthétiques**. Leurs valeurs ne
constituent aucun diagnostic sur la Normandie. Aucune donnée n'est téléchargée par
le pipeline, aucune source n'est réparée ou écrasée, aucun export public n'est créé.
Les métriques avancées de fragmentation, la modélisation globale des pressions,
les pondérations et les règles R1–R4 restent hors périmètre. Depuis le 3 novembre
2026, les conventions de triage D/S proposal-2 sont implémentées et testées sur
entrées synthétiques ; elles ne constituent pas une priorisation écologique validée.

## Installation et exécution

Python 3.10 ou ultérieur ; environnement isolé conseillé. Depuis la racine du dépôt :

```sh
python3 -m venv /tmp/reconnect-m2-venv
/tmp/reconnect-m2-venv/bin/python -m pip install -r analysis/requirements.txt
/tmp/reconnect-m2-venv/bin/python -m pytest -q tests/test_m2_inputs.py tests/test_m2_enjeux.py
/tmp/reconnect-m2-venv/bin/python -m analysis.run_enjeux --help
```

Exemple de commande à adapter **après livraison des vrais fichiers M1**. Les noms
ci-dessous sont des emplacements d'exemple et ne désignent pas des fichiers présents :

```sh
/tmp/reconnect-m2-venv/bin/python -m analysis.run_enjeux \
  --grid data/processed/grille_m1.gpkg --grid-layer grille \
  --territory data/processed/territoire_m1.gpkg --territory-layer territoire \
  --reservoirs data/processed/reservoirs_m1.gpkg --reservoirs-layer reservoirs \
  --corridors data/processed/corridors_m1.gpkg --corridors-layer corridors \
  --output data/derived/indicateurs_enjeux.gpkg
```

Sans validation de complétude applicable, le calcul conserve les observations mais laisse
les indicateurs indéterminés lorsque la preuve d'absence ou de complétude manque.
Les chemins d'entrée doivent appartenir à `data/processed/`, y compris les emprises
de couverture. Les sorties doivent appartenir à `data/derived/`. Les chemins sont
résolus, y compris les liens symboliques ; tout fichier de sortie existant est
refusé. Choisir un autre nom pour une nouvelle exécution.

Le rapport est enregistré par défaut sous
`data/derived/indicateurs_enjeux.validation.json`. `--report` permet un autre nom dans
`data/derived/`. Code de retour : `0` en cas de succès, `2` en cas de contrôle
bloquant ou d'erreur. Les avertissements seuls n'empêchent pas le calcul. Une erreur
d'entrée produit un rapport sans GeoPackage. Un chemin de sortie interdit ou
existant est refusé avant toute écriture, sans rapport supplémentaire.

### Complétude inconnue, déclarée ou validée

La couverture concerne la **complétude de la cartographie pour le thème considéré**,
sur un millésime et une emprise explicités. Ce n'est ni
l'enveloppe des objets observés, ni la couverture géométrique de la grille, ni la
preuve d'une absence d'habitat dans le monde réel.

Chaque source possède un état indépendant :

| `CoverageEvidence.status` | Conséquence |
| --- | --- |
| `unknown` | Complétude inconnue ; aucune absence confirmée |
| `declared` | Déclaration non validée M1/M2 ; aucune absence confirmée |
| `validated` | Validation documentée ; indicateur complet uniquement là où elle est entièrement applicable |

Une provenance textuelle, une emprise polygonale ou l'ancien `confirmed=True` ne
valent jamais validation. Les anciens paramètres sont acceptés, mais sont reclassés
comme déclarations en l'absence de statut validé. Les observations positives sont
conservées dans tous les états ; ENJ-01 reste `null` sans complétude validée et
applicable. ENJ-02 peut être `true` par observation.

En CLI, indiquer d'abord la **portée globale déclarée**, par exemple :

```sh
--reservoir-coverage-confirmed \
--reservoir-coverage-provenance "Référence de la déclaration à examiner"
```

Pour une complétude limitée spatialement, utiliser à la place :

```sh
--reservoir-coverage data/processed/emprise_completude_reservoirs.gpkg \
--reservoir-coverage-layer completude \
--reservoir-coverage-provenance "Référence M1 validée pour cette emprise"
```

Les options `--corridor-coverage-confirmed`, `--corridor-coverage`,
`--corridor-coverage-layer` et `--corridor-coverage-provenance` fonctionnent de même.
La portée globale et l'emprise sont mutuellement exclusives. Les options seules
n'autorisent plus un zéro confirmé. Ajouter les métadonnées validées dans `--config`.
Schéma à renseigner **sans inventer les valeurs M1** :

```json
{
  "reservoirs": {
    "coverage": {
      "status": "validated",
      "source_id": "<identifiant de source M1>",
      "producer": "<producteur>",
      "vintage": "<millésime applicable>",
      "validity_extent": "<référence de l'emprise de validité>",
      "theme": "reservoirs",
      "document_reference": "<preuve documentaire de complétude>",
      "validated_by": "<responsables M1/M2 de la validation>",
      "validated_at": "<date de validation ISO 8601>",
      "territory_sha256": "<empreinte géométrique exacte de T pour la portée globale>"
    }
  }
}
```

Les huit champs de `source_id` à `validated_at` sont obligatoires pour `validated`.
`theme` doit valoir `reservoirs` ou `corridors` selon la source. Une date invalide,
une portée ambiguë, un thème différent ou des métadonnées manquantes bloquent le
calcul. Pour `declared`, conserver les informations connues sans remplir les champs
inconnus avec des valeurs fictives.

La validation globale est liée à `T` par `territory_sha256`, calculé par
`territory_geometry_sha256(territory)` : SHA-256 de l'union normalisée en EPSG:2154.
Un premier rapport sans validation conserve cette empreinte dans
`layers.territory.geometry_sha256`, à examiner avec M1/M2. Une validation ne peut pas
être réutilisée automatiquement sur un autre territoire. L'empreinte est sensible
aux coordonnées et à la représentation géométrique : une modification exige une
nouvelle vérification. En mode emprise, la couche polygonale limite directement
l'applicabilité spatiale ; l'empreinte globale n'est pas exigée.

Ces métadonnées tracent une validation inscrite dans le contrat d'entrée ; le
programme n'authentifie pas les validateurs et ne certifie pas le contenu de la
preuve documentaire. M1/M2 doivent examiner cette preuve, l'applicabilité temporelle
et la correspondance entre identifiant de source, fichier et millésime.
La totalité de `H ∩ T` doit être couverte pour autoriser une absence confirmée.
Une tolérance numérique absolue de `10⁻⁶ m²` est appliquée à la différence entre
emprise et maille ; elle n'a aucune signification écologique.

### Mapping configurable des champs

Par défaut, seul `maille_id` est exigé dans la grille. Aucun nom de champ de
sous-trame n'est présumé. `--config chemin/config_m1.json` accepte un objet de
configuration restreint. Exemple de **schéma à renseigner**, sans présumer des
champs réellement présents :

```json
{
  "grid": {"id_column": "<champ identifiant validé par M1>", "expected_crs": "EPSG:2154"},
  "territory": {"expected_crs": "EPSG:2154"},
  "reservoirs": {
    "subframes": {
      "column": "<champ source validé>",
      "meanings": {"<code réellement présent>": "<signification documentée par M1>"}
    }
  }
}
```

Omettre les clés non validées ; tous ces réglages sont optionnels. `expected_crs`
exige l'égalité avec le CRS source annoncé par M1 ; ce n'est pas le CRS de sortie.
`corridors` accepte aussi `expected_crs`, `subframes`, `coverage` et `sensitivity`.
Les clés inconnues sont refusées pour éviter les fautes de configuration silencieuses.
Un mapping d'identifiant ne peut pas écraser une colonne `maille_id` déjà présente.

Chaque code de sous-trame observé doit être documenté. Les codes sont représentés
comme des chaînes. Un code sans signification documentée bloque le calcul. Les
sous-trames manquantes restent inconnues et sont signalées. Sans mapping, seuls les
indicateurs agrégés sont produits avec un avertissement ; aucune sous-trame n'est
interprétée. Le rapport archive la configuration utilisée et son empreinte.

### Emprise plausible officielle et précision documentée

Le même JSON accepte les paramètres suivants, à renseigner depuis une référence M1 :

```json
{
  "spatial": {
    "plausible_extent": "data/processed/<emprise_plausible_M1>.gpkg",
    "plausible_extent_layer": "<couche M1>",
    "reference": "<référence officielle M1>",
    "validated_by": "<validateur M1>",
    "margin_m": 0
  },
  "corridors": {
    "sensitivity": {
      "distance_m": "<remplacer par une distance numérique positive documentée>",
      "reference": "<document établissant la précision et le scénario retenu>"
    }
  }
}
```

Cet exemple contient des paramètres à renseigner ; ne pas l'exécuter tel quel.
Omettre entièrement `sensitivity` sans précision documentée. `margin_m`, nulle par
défaut, est une marge de contrôle d'emprise ; une marge positive doit être justifiée
et est archivée. Chaque géométrie, y compris `T` et les emprises de complétude, doit
appartenir à l'emprise plausible éventuellement élargie. Une livraison régionale
plus étendue que le pilote exige une emprise plausible adaptée à cette livraison.
Cette emprise ne désigne ni `T` ni la complétude thématique. Aucune limite du pilote
n'est inventée ou téléchargée.

## Validation avant calcul

`analysis/validate_inputs.py` expose :

| Fonction ou contrat | Rôle |
| --- | --- |
| `LayerSpec` | Types géométriques, colonnes requises, unicité, CRS attendu, couche vide autorisée |
| `read_layer` | Existence, format, lisibilité, choix explicite de couche puis contrôle du contenu |
| `validate_geodataframe` | Contrôles réutilisables sur des données déjà chargées, sans mutation |
| `validate_spatial_coverage` | Couverture du territoire par la grille, trous, chevauchements, mailles hors territoire |
| `SpatialExpectation` / `validate_spatial_plausibility` | Emprise M1, entités hors domaine et incohérences avec T |
| `ValidationReport` | Erreurs bloquantes, avertissements, qualité et métadonnées des couches |
| `InputValidationError` | Arrêt du calcul avec accès au rapport structuré |

Les formats acceptés sont GeoPackage et GeoJSON (`.geojson` ou `.json`). Un GPKG
multicouche nécessite un nom de couche ; aucune première couche n'est choisie
silencieusement. Grille, territoire, réservoirs et emprises de complétude exigent
des `Polygon`/`MultiPolygon`. Les corridors acceptent aussi des
`LineString`/`MultiLineString`. Les `GeometryCollection` sources, points, géométries
nulles, vides ou invalides sont bloquants. Les motifs d'invalidité sont rapportés
avec jusqu'à cinq exemples. Aucune réparation par `buffer(0)` ou `make_valid` n'est
appliquée. Une couche d'observations peut ne contenir aucune entité ; le CRS doit
néanmoins être renseigné. Grille, territoire et emprises ne peuvent pas être vides.
Un corridor ponctuel reçoit en plus le code `point_corridor_business_case` : il
exige une définition métier distincte, sans conversion artificielle en mètres ou m².

Les identifiants de maille sont obligatoires, non nuls et uniques. Aucun identifiant
de réservoir/corridor n'est imposé sans contrat M1 ; `LayerSpec` permet de demander
leur unicité quand elle sera justifiée.

Un CRS absent bloque le calcul. Un CRS connu peut être reprojecté vers
**EPSG:2154 (Lambert-93)** ; un échec, des coordonnées non finies ou des géométries
invalides après transformation sont bloquants. Un contrat `expected_crs` permet
de détecter une étiquette incorrecte par comparaison. La seule réussite d'une
reprojection ne prouve pas la justesse de l'étiquette CRS, l'ordre des axes,
l'exactitude géodésique ou l'emprise attendue : validation M1 indispensable.
Les coordonnées sources non finies, les coordonnées longitude/latitude en degrés
hors domaine et les mesures projetées non finies sont bloquantes. Une étiquette
L93 appliquée à tort à des degrés peut produire une transformation identité finie :
le contrat d'emprise permet de détecter ce cas. Les entités hors emprise plausible
validée sont bloquantes ; une entité correcte ne peut pas masquer un objet aberrant
dans la même couche.

Sans emprise plausible, le rapport signale que ce contrôle n'est pas validé. Une
couche entièrement disjointe de `T` produit un avertissement avec sa distance
minimale à `T` : une source régionale peut légitimement n'avoir aucune observation
locale. Ce cas demande un examen de l'emprise et du CRS, sans correction automatique.

La grille doit couvrir tout `T`, à `10⁻⁶ m²` près. Un trou supérieur à cette tolérance
**bloque** le calcul. Le chevauchement est mesuré par la différence entre la somme
des aires des mailles et l'aire de leur union : une valeur supérieure à `10⁻⁶ m²`
**bloque également** le calcul, y compris pour des identifiants distincts portant une
même géométrie. Un contact normal entre mailles adjacentes a une aire nulle. La
tolérance porte sur des surfaces agrégées et sert uniquement aux arrondis ; elle
n'a aucune signification écologique. La forme régulière et la surface nominale de
la grille officielle restent des contrats à préciser avec M1, sans les imposer
arbitrairement. Les mailles entièrement
hors territoire sont signalées et conservées comme lignes attributaires avec
surface étudiée nulle, indicateurs `null` et géométrie de sortie `NULL`.
Le territoire et les sources surfaciques sont unionnés : leurs superpositions ne
gonflent pas les mesures. La couverture source n'est jamais inférée de leur emprise
d'observation.

## ENJ-01 — proportion de réservoirs écologiques cartographiés

**Définition.** Part de la surface réellement étudiée d'une maille occupée par
l'union des réservoirs cartographiés, lorsque la complétude de la source est confirmée.

\[
S_H = H \cap T, \qquad R = \bigcup_i R_i, \qquad
P(H) = 100\,\frac{\operatorname{Aire}(S_H \cap R)}{\operatorname{Aire}(S_H)}.
\]

`H` désigne le polygone original de la maille, `T` l'union des polygones du territoire
réellement étudié, `R_i` un réservoir observé et `R` leur union géométrique.
Les trous de `T` sont conservés. Les centroïdes ne sont jamais utilisés.
Numérateur et dénominateur sont mesurés en m² après reprojection ; le résultat
`enj_01_pct` est un pourcentage dans `[0, 100]`. La surface mesurée `a_H` doit d'abord
satisfaire `−10⁻⁶ ≤ a_H ≤ Aire(S_H) + 10⁻⁶`, en m². Une violation bloque le calcul,
même sans complétude validée. Aucun bornage ne masque une erreur importante.
Seul un dépassement à l'intérieur de la tolérance peut être ajusté pour le ratio,
avec l'information `numeric_area_adjustment` ; la surface brute reste inchangée.

**Données et hypothèses.** Grille et identifiants validés, limite de `T` explicite,
réservoirs polygonaux, CRS fiables, géométries utilisables et preuve de complétude
par source. La proportion suppose une surface étudiée strictement positive. Une
maille de bordure utilise `Aire(H ∩ T)`, jamais l'aire nominale de sa maille entière.

**Zéro et valeur inconnue.** `0` est autorisé uniquement si la complétude est
validée et applicable à tout `S_H`, `Aire(S_H) > 0`, et l'intersection avec l'union des réservoirs
a une aire nulle. Un simple contact de frontière n'ajoute aucune aire. Si la
complétude est inconnue, simplement déclarée ou partielle, `enj_01_pct = null`, y compris en présence
d'observations positives. La surface observée est conservée séparément et peut
constituer une information partielle, sans être présentée comme un inventaire
complet. Une absence d'observation avec couverture inconnue peut ainsi avoir une
surface **observée** de zéro et un **indicateur** `null`.

**Limites.** La proportion décrit une cartographie et sa complétude documentée. Elle
ne mesure ni qualité d'habitat, ni biodiversité, ni occupation réelle exhaustive.
Des différences de millésime, de résolution ou de définition des réservoirs
limitent les comparaisons. Les sous-trames peuvent se recouvrir : leurs surfaces
ne s'additionnent pas pour retrouver le total unionné.

**Tests.** Maille de 1 km² avec 25 % de réservoirs, union de réservoirs superposés
(75 %, et doublons couvrant 100 %), zéro confirmé, couverture inconnue/partielle,
bordure découpée (50 % sur 0,5 km²), trous du territoire, complétude spatiale par
maille et conservation des sous-trames documentées.

## ENJ-02 — présence de corridors écologiques cartographiés

**Définition.** Existence d'une intersection de dimension positive avec un corridor
cartographié dans la surface étudiée d'une maille. Les lignes et les polygones
sont traités séparément :

\[
L_H = \operatorname{Longueur}\left((S_H \cap \bigcup_i C_i^{lin})
\setminus \partial S_H\right),\qquad
A_H = \operatorname{Aire}\left(S_H \cap \bigcup_j C_j^{surf}\right).
\]

`C_i^{lin}` et `C_j^{surf}` sont respectivement les corridors linéaires et surfaciques ;
`∂S_H` est la frontière de la partie étudiée de la maille. `L_H` est en mètres,
`A_H` en m². Chaque famille est unionnée pour ne pas additionner deux fois les
objets superposés d'une même dimension.

`enj_02_presence` vaut :

| Situation sur une surface étudiée positive | Valeur |
| --- | --- |
| `L_H > 0` ou `A_H > 0` | `true`, même si la couverture est inconnue |
| `L_H = 0` et `A_H = 0`, complétude validée et applicable sur toute la surface étudiée | `false` |
| `L_H = 0` et `A_H = 0`, complétude inconnue/déclarée/partielle | `null` |
| Maille sans surface dans `T` | `null` |

Un contact ponctuel, une ligne située uniquement sur la frontière et un corridor
surfacique touchant seulement le bord ne suffisent pas à établir une présence.
Une ligne située sur une frontière commune n'est donc attribuée à aucune des deux
mailles si elle ne pénètre dans aucun intérieur. La règle s'applique aussi aux
frontières de `T` et aux bords de ses trous. Les contacts isolés issus d'une
intersection polygonale sont retirés de la géométrie de maille en sortie.

**Données et hypothèses.** Grille et territoire validés, corridors de dimension
documentée, précision et millésime connus, et validation indépendante de
complétude pour autoriser `false`. Les mesures utilisent les objets d'origine,
reprojetés et découpés, sans tampon arbitraire.

**Limites.** Une longueur, une surface et une présence sont trois propriétés
géométriques différentes. Les longueurs ne sont jamais converties en surfaces
sans donnée de largeur justifiée ; les surfaces ne sont pas converties en longueurs.
Une ligne et un polygone peuvent décrire un même corridor : leurs mesures restent
séparées et ne doivent pas être additionnées. Aucune mesure ne prouve une
fonctionnalité écologique, un passage d'espèces ou une continuité effective.
Aucun seuil écologique de longueur ou de surface n'est introduit. La présence
positive utilise strictement `> 0` ; les petits résidus topologiques et la précision
des sources demandent un examen M1/M2 avant interprétation.

### Résidus numériques et sensibilité cartographique

Deux contrôles sont distincts :

- **Résidus numériques** : une intersection positive de longueur ≤ `10⁻⁹ m` ou
  d'aire ≤ `10⁻⁶ m²` est signalée par `corridor_numerical_residue` et un avertissement.
  Ces tolérances ne définissent ni précision de source ni seuil écologique. La
  mesure et la présence positive sont conservées. Pour un objet entièrement
  contenu, le calcul évite un overlay inutile susceptible d'effacer des géométries
  extrêmement petites aux grandes coordonnées L93.
- **Sensibilité documentée** : `CorridorSensitivity(distance_m, reference)` ou
  `corridors.sensitivity` définit une distance `d > 0` justifiée par les métadonnées
  de précision. Le programme compare les mesures sur `S⁻ = erosion(S_H, d)` et
  `S⁺ = dilatation(S_H, d) ∩ T`, sans changer les corridors ni la valeur brute de
  référence. Il conserve les longueurs et surfaces de ces deux scénarios et signale
  une différence de présence positive (`corridor_presence_sensitive`).

Le scénario porte sur la fenêtre d'observation ; il ne simule pas toutes les erreurs
possibles. La borne basse exclut aussi une bande près du bord de `T`, et la borne
haute reste dans `T` : ce choix conservateur demande un examen M1/M2. Il peut
identifier un corridor proche d'une frontière ou une présence voisine sans modifier
l'absence de référence. Les valeurs min/max décrivent ces scénarios imbriqués,
pas des intervalles de confiance ni une fonctionnalité écologique. Aucune distance
n'est déduite automatiquement d'une échelle cartographique. Sans précision
documentée, le contrôle de sensibilité est `null` avec avertissement ; seuls les
résidus numériques sont identifiés. Les opérations restent soumises aux limites
arithmétiques de GEOS.

**Tests.** Corridor traversant avec 1 000 m mesurés, doublon linéaire, longueur
et surface mixtes séparées, contacts ponctuels/linéaires/surfaciques de frontière,
présence positive malgré couverture inconnue, absence confirmée et absence
indéterminée, intersection composite à la bordure de `T`.

## Sorties et traçabilité

`compute_enjeux` retourne un `EnjeuxResult` contenant les mailles, les observations
par sous-trame et le rapport. L'API réutilisable accepte des `GeoDataFrame` sans
imposer de chemin disque et ne modifie pas les entrées. Elle refait les contrôles
avant calcul et lève `InputValidationError` en cas d'erreur bloquante.

Le GeoPackage intermédiaire comporte une couche `indicateurs_enjeux`, en EPSG:2154,
dont la géométrie représente `H ∩ T` :

| Champ | Signification / unité |
| --- | --- |
| `maille_id` | Identifiant validé de la maille |
| `study_area_m2` | Dénominateur surfacique effectif, m² |
| `reservoir_observed_area_m2` | Aire de l'union des réservoirs observés dans `H ∩ T`, m² |
| `reservoir_coverage_confirmed` | Complétude confirmée pour cette maille étudiée |
| `reservoir_completeness_status` | `unknown`, `declared` ou `validated` pour la source |
| `enj_01_pct` | Proportion de réservoirs cartographiés, % ou null |
| `enj_01_status` | `complete`, `unknown_coverage` ou `outside_territory` |
| `corridor_observed_length_m` | Longueur unionnée observée hors frontière, m |
| `corridor_observed_area_m2` | Aire unionnée des corridors surfaciques observés, m² |
| `corridor_coverage_confirmed` | Complétude confirmée pour cette maille étudiée |
| `corridor_completeness_status` | État de la preuve de complétude de la source |
| `corridor_numerical_residue` | Intersection positive à l'échelle des tolérances numériques |
| `corridor_presence_sensitive` | Présence différente entre scénarios, ou null si non calculé |
| `corridor_sensitivity_length_min_m`, `corridor_sensitivity_length_max_m` | Longueurs observées des scénarios, m |
| `corridor_sensitivity_area_min_m2`, `corridor_sensitivity_area_max_m2` | Aires observées des scénarios, m² |
| `enj_02_presence` | Booléen nullable de présence cartographique |
| `enj_02_status` | `observed`, `confirmed_absence`, `unknown_coverage` ou `outside_territory` |

Le booléen nullable est préservé comme `NULL` dans le GeoPackage ; selon le lecteur,
les booléens peuvent être exposés comme `0/1/NULL`.

Si un mapping documenté est fourni et que des codes sont observés, une couche
`observations_sous_trames` conserve `maille_id`, la source (`reservoirs` ou `corridors`),
`source_value`, `meaning`, la surface étudiée, et les mesures géométriques observées
de la famille considérée. Les autres mesures sont nulles. Les codes manquants
restent `NULL`. Cette couche ne déduit aucune absence par sous-trame : la complétude
de toute la source ne garantit pas la complétude de son classement thématique.
Les zéros y décrivent uniquement les intersections des objets observés d'un code.

Le rapport JSON contient `errors` (bloquantes), `warnings`, `quality`, les contrats
et métadonnées de couches, déclarations de couverture, configuration, heures UTC,
versions Python et bibliothèques, empreintes SHA-256 des entrées, de la configuration,
des trois modules exécutés et de la sortie. Les valeurs nulles ne sont pas imputées.

Les options `--grid-version`, `--method-version` et `--dataset-version` renseignent
les versions communiquées/validées ; leur absence reste `null`, avec avertissement.
Le nom du projet « V6.1 » n'est pas utilisé comme version de méthode par défaut.
Un identifiant unique d'exécution (`run_id`) relie les artefacts. La table interne
`m2_run` du GeoPackage conserve cet identifiant, les trois versions, le caractère
obligatoire du rapport, les chemins attendus et les effectifs des couches.

### Protocole de publication et réutilisation

1. Écrire le GeoPackage temporaire, puis ses métadonnées de couplage.
2. Calculer son SHA-256 et sérialiser intégralement le rapport temporaire.
3. Vérifier les deux fichiers : intégrité SQLite, lecture du JSON, identité,
   versions, chemins, empreinte, présence des couches, effectifs et CRS de sortie.
4. Publier **le rapport en premier**, puis le GeoPackage, par création exclusive de
   liens sans remplacement ; vérifier à nouveau le couple final.
5. Retourner `0` uniquement après ces contrôles. En cas d'erreur normale, retirer
   les liens créés par cet appel et tenter de publier seulement un rapport `blocked`.

Une erreur de sérialisation du rapport ne publie aucun GeoPackage. Une erreur de
publication du second fichier retire le rapport de succès. Une interruption brutale
entre les deux publications peut laisser un rapport sans GeoPackage, jamais un
GeoPackage publié avant son rapport. Deux fichiers indépendants ne constituent pas
une transaction atomique de système de fichiers ; les consommateurs doivent
**obligatoirement** vérifier le couple, notamment après déplacement, copie ou
suppression manuelle. Aucun verrouillage ou remplacement des fichiers d'autrui
n'est effectué. Les fichiers temporaires sont sous `data/derived/`.

Exemple de contrôle réutilisable depuis Python :

```python
from pathlib import Path
from analysis.run_enjeux import verify_artifact_pair

report = verify_artifact_pair(
    Path("data/derived/indicateurs_enjeux.gpkg"),
    Path("data/derived/indicateurs_enjeux.validation.json"),
)
```

Un rapport absent, bloqué, altéré ou appartenant à une autre exécution interdit la
réutilisation. Les chemins font partie du manifeste : un déplacement arbitraire du
couple nécessite une procédure de reconditionnement qui n'est pas implémentée.
La vérification garantit la cohérence technique du couple, pas une signature
authentifiée ni la validation scientifique des couches réelles. Un rapport bloqué
sans GeoPackage est un compte rendu d'erreur, jamais un résultat complet.

### Compatibilité et migration après audit

Les quatre couches principales, `maille_id`, les options historiques et les deux
indicateurs sont conservés. Les paramètres API `spatial_expectation` et
`corridor_sensitivity`, les métadonnées de complétude et les options de versions
sont ajoutés. Changements de comportement nécessaires :

- Une superposition de grille au-delà de la tolérance est désormais bloquante.
- `CoverageEvidence(confirmed=True, provenance=...)` seul produit `declared` et
  n'autorise plus un zéro/ratio complet ; fournir la validation thématique et son
  emprise applicable. Les anciennes validations par simple texte doivent être revues.
- Les champs `*_coverage_confirmed` signifient désormais **validé et applicable**.
  Les champs `*_completeness_status` conservent l'état de la source. Pour compatibilité,
  `unknown_coverage` reste le statut d'ENJ-01 tant que la complétude applicable manque,
  y compris pour une déclaration ou une validation seulement partielle.
- Un GeoPackage seul n'est plus un résultat complet : vérifier aussi son rapport.
  Les anciens exports sans table `m2_run` doivent être recalculés après validation.

Les bornes de versions de `analysis/requirements.txt` indiquent une compatibilité,
pas un verrouillage bit à bit. Le rapport conserve les versions effectives ; après
stabilisation de l'environnement d'équipe, il faudra figer les dépendances pour
reproduire aussi l'environnement exact. Les opérations géométriques supposent des
couches chargeables en mémoire ; l'union globale des réservoirs peut demander une
optimisation sur les véritables volumes. Les candidats corridors sont recherchés
par index spatial.

## Quatre niveaux de validité à ne pas confondre

| Niveau | Ce que la chaîne établit et ce qu'elle ne permet pas de conclure |
| --- | --- |
| Exactitude mathématique | Union, intersection, unités et dénominateur corrects pour les géométries livrées, à la précision numérique près ; tests synthétiques et invariants d'aires |
| Précision cartographique | Dépend des sources, échelles, dates, géoréférencement, généralisation et erreurs de position ; contrôles d'emprise et scénarios ne remplacent pas leur qualification M1 |
| Interprétation écologique | Une aire, une longueur ou une présence cartographique ne prouve ni déplacement d'espèces, ni qualité d'habitat, ni fonctionnalité ; validation écologique distincte |
| Pertinence décisionnelle | Exige des données locales adaptées, preuves examinées M1/M2, droits et limites de diffusion, expertise et besoins de la collectivité ; aucun score de priorité n'est produit |

Un test mathématique réussi ne valide pas les trois autres niveaux. Un couple
d'artefacts techniquement complet peut contenir des valeurs inconnues et ne constitue
pas une autorisation d'usage décisionnel.

### Sources SRCE au 1/100 000 et hexagones de 1 km²

Le géostandard COVADIS SRCE v1.0 décrit un atlas des éléments régionaux au
1/100 000. Cette référence établit un cadre de représentation, sans qualifier la
précision des futurs fichiers normands livrés par M1. Voir le
[géostandard SRCE, rubrique « Le géostandard en bref »](https://www.geoinformations.developpement-durable.gouv.fr/geostandard-schema-regional-de-coherence-a2775.html).

Le centre de ressources TVB décrit le rôle régional du SRCE et la nécessité d'une
cartographie adaptée aux échelles locales. Il cite des échelles plus fines pour
les SCoT et PLU. Voir la
[FAQ officielle sur la représentation cartographique de la TVB](https://www.trameverteetbleue.fr/presentation-tvb/foire-aux-questions/quelle-representation-cartographique-pour-tvb).

Le guide DREAL Midi-Pyrénées, *La Trame verte et bleue dans les Plans locaux
d'urbanisme* (2012), § 2.1.3 p. 31 et § 2.3.6 p. 45, explique qu'un agrandissement
d'une cartographie régionale exige des compléments et une adaptation locale,
ainsi que des vérifications de terrain pour les continuités identifiées. Le texte
intégral a été consulté via sa
[notice officielle](https://portail.documentation.developpement-durable.gouv.fr/pub/C33OUV00196046-trame-verte-bleue-dans-les-plans-locaux-urbanisme.html).
Ces références historiques sont utilisées pour leur portée méthodologique,
sans affirmer ici l'état actuel du droit de l'urbanisme.

**Conséquences méthodologiques M2**, déduites de cette différence d'échelle : un
hexagone de 1 km² mesure de l'ordre du centimètre sur une carte au 1/100 000. Son
intersection avec un objet généralisé peut être très sensible au tracé des limites.
Une mesure vectorielle exacte à plusieurs décimales n'apporte pas une précision
terrain équivalente. Le découpage en hexagones n'affine ni les données d'origine ni
leur exhaustivité. Les valeurs restent des observations régionales agrégées par
maille, utiles au repérage et à l'examen, sans permettre de définir à elles seules
une limite parcellaire, un corridor fonctionnel ou une intervention locale.

L'échelle seule ne donne pas une erreur métrique, une largeur réelle de corridor
ou une probabilité de présence : aucune conversion universelle n'est implémentée.
M1 doit communiquer les métadonnées effectives de chaque livraison ; M1/M2 doivent
qualifier les variations entre millésimes et sources, documenter les incertitudes
et confronter les secteurs retenus à des données et expertises locales. Les trois
pages officielles ci-dessus ont été consultées pour cet audit ; elles ne valident
aucun résultat territorial du projet.

## Validation encore attendue auprès de M1 et suites

- Chemins, noms de couches, formats, contrats attributaires et identifiant stable
  de maille ; inspection du PRD V6.1 s'il devient disponible.
- Délimitation de `T`, construction et emprise de la grille, éventuels trous et
  chevauchements, précision des frontières et CRS d'origine fiables.
- Emprise plausible officielle de chaque livraison, référence et validateur M1,
  marge métrique éventuelle justifiée ; versions de grille, méthode et jeu de données.
- Définition des réservoirs et corridors, distinction lignes/polygones, millésimes,
  provenance, résolution et limites de chaque source.
- Preuve de complétude spatiale et thématique par source et période ; une simple
  limite administrative ou une emprise de données ne suffit pas.
- Identifiant de source, producteur, millésime, emprise de validité, thème,
  document justificatif, date et responsables de validation M1/M2 ; précision
  spatiale documentée permettant, si pertinent, un scénario de sensibilité.
- Colonnes et dictionnaires des sous-trames, valeurs manquantes, correspondances
  entre sources ; aucun rapprochement automatique de classifications différentes.
- Licence, droits de diffusion, éventuelles restrictions et contrôle conjoint
  avant tout futur export `data/public/` destiné à M3/M4.

La validation des sources réelles et des résultats précède toute interprétation.
La priorisation, la modélisation des pressions, les métriques avancées de fragmentation,
les seuils, les pondérations et les règles R1–R4 feront l'objet d'étapes ultérieures
explicitement validées. Les références officielles vérifiées ci-dessus encadrent les limites
de représentation et de changement d'échelle. Toute autre référence proposée
devra être marquée « à valider » tant qu'elle n'aura pas été vérifiée.

## Vérification de l'implémentation

Avant l'extension route–corridor, les 107 tests synthétiques existants ont été réexécutés
avec succès (0 échec, 0 ignoré), sans modification des modules ENJ-01/ENJ-02, dans
`/private/tmp/reconnect-m2-venv`, sans modifier le Python partagé : Python 3.10.6,
GeoPandas 1.1.4, Shapely 2.1.2, pandas 2.3.3, NumPy 2.2.6, pyproj 3.7.1,
pyogrio 0.13.0 et pytest 9.2.0. La commande `--help` a aussi été exécutée.
Les essais incluent lecture/écriture des fichiers temporaires, rapports JSON,
valeurs `NULL` à l'export, préservation des sources et refus de diffusion publique.
Les classes `TestExactHexagonGeometry`, `TestNumericalRobustness` et
`TestCartographicSensitivity` séparent explicitement les calculs exacts construits,
les tests d'arithmétique et les scénarios de précision cartographique.
`TestCompletenessStates` couvre les défauts de validation ; `TestExportIntegrity`
simule des pannes d'écriture/publication et refuse les rapports absents ou discordants.
Ce constat ne remplace pas la validation future des véritables couches M1.

## Événements candidats route–corridor : trois niveaux distincts

Cette extension distingue les **sources** (routes et corridors), les **événements
cartographiques candidats**, puis les **mailles de diagnostic**. Elle n'infère
jamais une intersection de la présence de deux objets dans un même hexagone.
Les autres habitats et pressions ne sont pas encore croisés. Aucun PRD complet ni
jeu officiel M1 n'est présent dans le dépôt ; les quatre statuts ci-dessous suivent
la demande métier jointe, à confronter ultérieurement au PRD livré.

Les nouveaux modules sont `analysis/detect_conflicts.py`,
`analysis/aggregate_conflicts.py` et `analysis/run_conflicts.py`. Ils réutilisent
`LayerSpec`, les validations SIG, `SpatialExpectation`, `CoverageEvidence`, les
contrôles de complétude et les conventions de versions déjà en place. Les fonctions
internes de complétude et d'export de la phase précédente sont importées, sans
réécrire ses modules ; ces dépendances doivent rester couvertes par les tests.

### Intersections et dimension des observations

Pour une route source `U_i`, un corridor `C_j` et le territoire `T`, tous reprojetés
après contrôle en EPSG:2154, le candidat brut est :

\[
I_{ij} = \bigl(\operatorname{XY}(U_i) \cap \operatorname{XY}(C_j)\bigr) \cap T.
\]

L'index spatial sélectionne les paires réellement intersectantes ; les calculs
utilisent leurs géométries, avant tout rattachement à une maille. Aucun centroïde,
tampon ou distance de proximité implicite n'est utilisé. Une intersection hors
`T` ne produit pas d'événement local. Une couche ponctuelle source est refusée
comme cas métier distinct ; un point **issu d'une intersection** est au contraire
un candidat admissible.

Les géométries multiples/collections résultantes sont décomposées en parties
simples : points, lignes et polygones. Les lignes contiguës de degré 2 sont réunies
par `line_merge` ; les branches restent séparées. Cette convention de décomposition
est propre à ReConnect, pas un modèle de déplacement d'espèces.

| Dimension | Mesure conservée | Interprétation limitée |
| --- | --- | --- |
| Ponctuelle | Géométrie du point ; longueur et aire nulles au sens **non applicables** (`NULL`) | Croisement transversal ou contact à examiner |
| Linéaire | `length_m` en mètres ; `area_m2 = NULL` | Portion commune, sans largeur artificielle |
| Surfacique | `area_m2` en m² ; `length_m = NULL` | Surface commune, sans convertir son périmètre en corridor linéaire |

Un contact ponctuel ou sur la frontière d'un objet est conservé, avec
`intersection_relation = contact_frontiere`, `detection_status = contact_detecte`
et qualification initiale `non_concluant`. Il ne prouve pas un franchissement.
Les superpositions non limitées à la frontière sont distinguées des croisements
transversaux. Les dimensions et relations demeurent consultables.

La frontière du territoire pilote est contrôlée séparément des frontières des
objets sources. `territory_relation` vaut `interieur`, `frontiere` (toute la partie
candidate est couverte par `∂T`) ou `interieur_et_frontiere`. Un croisement transversal
entre sources situé uniquement sur `∂T` est conservé comme `contact_detecte` et
`non_concluant`. Cette règle vaut aussi pour les frontières des trous du territoire.
Il ne peut pas être promu en conflit interne par le mécanisme de qualification.
Une frontière commune de mailles située dans l'intérieur de `T` reste une relation
entre mailles ; elle ne rend pas le croisement territorial non concluant.

Les coordonnées Z éventuelles ne sont pas utilisées pour inférer un niveau physique :
leur présence est signalée, la géométrie d'événement est en XY et les contextes
sources 3D différents ne sont pas fusionnés automatiquement. La connaissance d'un
pont, tunnel, passage inférieur ou autre ouvrage est conservée comme observation
documentée ; sa présence ne démontre ni obstacle ni efficacité écologique.

### Dédoublonnage et identifiants déterministes

Les identifiants M1 sont exigés par mapping explicite ; aucune colonne de route ou
corridor n'est devinée. Ils sont des chaînes non vides ou entiers et sont conservés
dans les JSON. Un identifiant réutilisé pour deux objets géométriquement ou
attributairement différents bloque l'analyse. Une répétition strictement identique
est regroupée. Des objets de même géométrie normalisée et mêmes attributs hors
identifiant sont regroupés avec leurs identifiants alias. Les attributs manquants
restent null ; un champ configuré absent bloque le calcul.

Deux candidats sont dédoublonnés s'ils ont **exactement** la même géométrie XY
normalisée, les mêmes attributs sources hors identifiants, les mêmes mappings et
espaces de noms sources, pour le même contrat de méthode. Cela évite, par exemple,
de compter deux fois un même contact issu de deux segments routiers adjacents.
Les identifiants alias, paires réellement analysées et empreintes des objets sources
sont réunis dans `source_ids`, `source_pairs` et `observations`. Les contextes de
chaque paire restent dans `observations.pair_intersections`. Si l'un est non
concluant, la qualification géométrique fusionnée reste conservatrice.

Deux sous-trames, catégories, niveaux ou autres attributs différents restent
distincts même au même endroit. Une coprésence dans une maille ne déclenche jamais
une fusion. Les empreintes candidates partiellement superposées ne sont pas fusionnées
par proximité. Les objets sources 3D différents sont conservés séparément faute
de modèle validé de niveaux. Le comptage reste celui des événements cartographiques
définis par cette convention, pas celui des obstacles physiques distincts.

L'identifiant vaut :

\[
\texttt{conflit\_id} = \texttt{rc\_} \,\Vert\,
\operatorname{SHA256}\bigl(\operatorname{JSONcanonique}(K)\bigr).
\]

`K` contient le contrat `reconnect.route_corridor.intersection`, `method_version`,
les identifiants de sources documentaires connus (sinon null), la géométrie
candidate normalisée en WKB XY, les attributs hors identifiants, les mappings et,
si nécessaire, le contexte géométrique 3D des sources. Sans version de méthode,
la valeur reste `null` et le SHA-256 du code de détection entre aussi dans `K`, avec
avertissement. Aucune version métier n'est inventée.

Le JSON trie les clés, emploie UTF-8 et des séparateurs constants, sans NaN. Les
géométries sont normalisées sans arrondi ni grille de précision. L'ordre des lignes,
leurs index pandas, l'orientation des lignes, les chemins, les alias identifiants,
les mailles de rattachement et les preuves ajoutées ne déterminent pas l'identité.
Les événements sont triés par identifiant à la sortie.

Une modification de géométrie candidate, d'attribut, de mapping ou de version de
méthode peut changer l'identifiant. Une modification hors de l'emprise candidate
ou d'un alias peut au contraire le laisser inchangé : l'identifiant est une clé
d'événement, **pas un certificat de validité permanente de ses preuves**.
Les preuves doivent être réexaminées après toute nouvelle livraison. Les différences
de reprojection, précision flottante, segmentation et décomposition GEOS peuvent
modifier les événements ; versions de données, code et bibliothèques sont archivées.
La canonisation n'est pas une équivalence topologique générale : une densification
des sommets ou des intersections seulement proches ne sont pas automatiquement
assimilées. M1 doit stabiliser ses objets et leur granularité avant comparaisons.

### Qualification et niveaux de preuve

`detection_status` décrit l'intersection observée ; `statut` décrit la qualification.
Les observations, preuves, limites et précision restent des champs séparés.

| `statut` | Condition d'attribution |
| --- | --- |
| `croisement_detecte` | Intersection géométrique réelle, sans preuve d'obstruction écologique |
| `conflit_potentiel` | Qualification externe visant le `conflit_id`, ou règle contextuelle explicite versionnée ; critères documentés |
| `obstacle_confirme` | Qualification externe visant le `conflit_id`, avec preuve identifiable, critères et validation humaine explicites |
| `non_concluant` | Contact source/territorial, résidu numérique, disparition d'un événement unique sous translation ou précision déclarée insuffisante ; ou qualification externe explicite |

`qualify_events` reçoit des `EventEvidence`. Aucun attribut isolé n'est interprété
comme un obstacle par défaut. Une
preuve doit comporter `conflit_id`, `target_status`, `reference`, `criteria`,
`validated_by`, `validated_at` ISO 8601 et éventuellement `observations`. Des preuves
divergentes pour un même événement, une référence manquante ou un identifiant
absent de l'exécution bloquent l'application. Les répétitions identiques sont
acceptées sans multiplier les événements.

Une promotion de `non_concluant` exige désormais une résolution de localisation
spécifique à l'événement : `localization_resolution_reference`,
`localization_validated_by`, `localization_validated_at` (ISO 8601). La même exigence
s'applique à une confirmation d'obstacle dont la localisation initiale n'était pas
validée, même si le croisement géométrique était observable. Ces champs sont des
attestations déclarées à contrôler par M1/M2 ; le logiciel ne lit pas les documents
ni n'authentifie l'auteur. La localisation brute, ses limites et son état initial
ne sont pas réécrits ; le statut précédent et les preuves successives sont tracés.
Une simple preuve supplémentaire ne peut donc plus effacer silencieusement une
incertitude. Les contacts uniquement sur `∂T` restent hors promotion interne.

`PotentialConflictRule` / `apply_potential_conflict_rules` préparent une interface
optionnelle sans aucune règle de production. Chaque règle exige identifiant,
version, référence, critères, validateur déclaré, date ISO et correspondances
exactes entre chemins d'observations et codes documentés (`context_equals`). Les
valeurs manquantes ne satisfont jamais la règle. Seul `croisement_detecte` avec
`precision_affichage = localisation_validee` peut devenir `conflit_potentiel` ;
aucune règle ne confirme un obstacle ni ne résout une localisation. Le niveau
`regle_contextuelle_documentee` et la règle appliquée sont archivés en preuve.
Les règles sont ordonnées par identifiant/version. Cette interface n'est pas
branchée sur la CLI ; son activation exigera des critères et dictionnaires M1
validés et des cas de tests documentés. Aucun seuil ni coefficient scientifique
n'est fourni par ce développement.

Les niveaux `geometrie_2d`, `criteres_examen_documentes` et
`preuve_externe_documentee` décrivent l'origine de la qualification, pas un score.
Une qualification externe ne modifie ni la géométrie brute ni le statut de détection
ni les limites déjà signalées. L'outil n'authentifie pas ses auteurs et ne vérifie
pas lui-même la véracité du document ; M1/M2 doivent examiner son applicabilité.
`non_concluant` n'est jamais une preuve qu'un obstacle existe.

### Précision des événements

Sans précision documentée : `precision_m = NULL`, `precision_sensitive = NULL`,
`precision_affichage = precision_non_documentee`. L'intersection 2D reste observable,
mais son aptitude à une localisation opérationnelle n'est pas certifiée.

Une longueur positive ≤ `10⁻⁹ m` ou aire positive ≤ `10⁻⁶ m²` est un résidu numérique
signalé et conservé, initialement non concluant. Ces tolérances ne sont pas des
seuils écologiques ou des estimations de précision cartographique.

`IntersectionPrecision(d, reference, localization_adequate)` exige une distance
positive finie et une référence justifiant son sens. Les quatre translations
routières `(d,0)`, `(-d,0)`, `(0,d)`, `(0,-d)`, relativement au corridor fixe, sont
testées sans modifier la géométrie de référence. Si une translation supprime
l'intersection entière dans `T`, la paire est signalée sensible.
`precision_sensitivity_scope = source_pair` explicite cette portée.
Si la paire a un seul événement, cette disparition démontre la perte de son unique
intersection observée et le statut initial est `non_concluant`. Si elle a plusieurs
événements, le champ reste une information de paire et ne modifie pas leurs statuts
locaux. Aucune correspondance des composantes avant/après translation n'est inférée
par une distance arbitraire ; aucun résultat n'est nommé sensibilité locale.
Une paire comportant plusieurs intersections peut en conserver une malgré la
disparition d'une autre : un résultat `false` n'établit donc pas la stabilité de
chaque composante, ni celle de tous les déplacements possibles. Aucun événement
de proximité n'est généré par ces scénarios. Ce contrôle est une adaptation
ReConnect, pas un intervalle de confiance.
Il ne mesure ni une probabilité d'erreur ni une fonctionnalité écologique.

`localization_adequate = false` impose initialement `non_concluant` même si la paire
survit aux quatre translations ; `true` conserve l'avis documenté M1/M2 sans créer
une preuve d'obstacle. Un avis absent reste une localisation à confirmer. Aucune
distance n'est déduite automatiquement de l'échelle SRCE.

### Liens aux mailles et comptages

Pour `S_H = H ∩ T` et un événement géométrique `E_k`, conserver la relation :

\[
\mathcal L = \{(k,H)\;:\;E_k\cap S_H \ne \varnothing,
\operatorname{Aire}(S_H)>0\}.
\]

Toutes les relations sont conservées, y compris un point ou segment situé exactement
sur une frontière commune. `relation_spatiale` distingue l'intérieur (point contenu
strictement, longueur intérieure positive ou aire positive) de la frontière.
Un candidat sans maille est bloquant : aucune affectation au plus proche n'est faite.

L'agrégateur exige un CRS valide pour les événements et effectue explicitement leur
reprojection en EPSG:2154 avant tout test avec les mailles. La validation seule ne
reprojette pas les entrées. Les objets sources restent inchangés ; les événements
reprojetés sont également les événements retournés. Un événement entièrement ou
partiellement hors `T`, nul, vide, invalide ou de type incompatible est bloqué,
sans découpage ou correction implicite. Les différences flottantes d'un aller-retour
de CRS peuvent changer un contact exact : aucune tolérance spatiale métier n'est
inventée pour le restaurer.

Un propriétaire exclusif est choisi parmi les mailles d'intersection intérieure ;
à défaut, parmi toutes les mailles liées. C'est la plus petite sérialisation JSON
canonique de `maille_id`, dans l'ordre lexicographique, indépendamment de l'ordre
des entrées. Cette convention technique n'attribue aucune responsabilité écologique.
La colonne d'identifiants de grille doit avoir un type homogène pour préserver ses
liens dans les fichiers typés.

\[
N_H^{obs}=\#\{k:(k,H)\in\mathcal L\},\qquad
N_{global}^{obs}=\#\{\texttt{conflit\_id distincts}\}.
\]

La somme des comptages locaux peut dépasser le total global ; elle n'est jamais
utilisée comme total. La somme des `canonical_owner` vaut exactement le nombre
global d'événements, avec un propriétaire par événement.

| Situation | `nb_evenements_observes` | `nb_evenements` |
| --- | --- | --- |
| Analyse effectuée, deux complétudes validées sur tout `S_H` | Nombre observé, dont zéro possible | Même nombre |
| Analyse effectuée, complétude inconnue/déclarée/partielle | Nombre observé, dont zéro d'observation possible | `NULL` |
| Source absente / absence d'analyse | `NULL` | `NULL` |
| Maille sans surface étudiée | `NULL` | `NULL` |

Le zéro complet signifie uniquement absence de candidat cartographique dans les
sources complètes pour les thèmes considérés. Les contacts non concluants sont
inclus dans les observations, avec des comptages séparés par `statut`. Aucune
largeur, intensité de trafic, mortalité, espèce ou franchissabilité n'est inventée.
Les lacunes restent dans le rapport et le diagnostic ; elles ne deviennent pas des
points de conflit. L'API accepte une détection absente pour représenter l'absence
d'analyse ; en CLI, un fichier obligatoire absent ou illisible bloque l'exécution
avec rapport seul, sans inventer une couche diagnostique réelle.

### Schéma des sorties et publication

Les sorties intermédiaires forment un lot unique :

- `data/derived/conflits_candidates.gpkg`, couche `conflits_candidates` : événements
  distincts avec les champs obligatoires `conflit_id`, `type`, `evidence_level`,
  `source_ids`, `maille_ids`, `precision_affichage`, `limites`, `method_version`,
  plus statut, détection, dimension/relation, observations, preuves et mesures.
- `data/derived/mailles_conflits.gpkg`, couche `mailles_conflits` : `maille_id`,
  `conflit_ids`, comptages bruts, propriétaires exclusifs observés, états de
  complétude, analyse et fiabilité ; table non spatiale enregistrée dans le GPKG
  `liens_mailles_conflits` (`conflit_id`, `maille_id`, `relation_spatiale`, `canonical_owner`).
- `data/derived/conflits_validation.json` : validation, configuration, preuves
  référencées, sources et code SHA-256, versions, effectifs et total global distinct.

La liaison est donc plusieurs-à-plusieurs :
`mailles.maille_id ← liens_mailles_conflits → conflits.conflit_id`.
Les listes de chaque fichier sont vérifiées contre la table de liens. Les attributs
structurés sont du JSON canonique dans les champs GPKG ; les futurs exports GeoJSON
devront les décoder en listes/objets et reprojecter selon leur contrat de diffusion.
Le contrat [M2 → M4](api_contract_m2_m4.md) fournit maintenant les deux schémas JSON
et un convertisseur de préparation synthétique. Les exports de production restent
désactivés ; les exemples sont uniquement dans `tests/fixtures/m2/`.

Le lot reprend `grid_version`, `method_version`, `dataset_version`, null si inconnus,
et un `run_id` commun dans les deux tables `m2_run` et le rapport. Les trois fichiers
sont préparés et contrôlés avant publication exclusive ; le rapport est publié
d'abord, puis les deux GPKG. Une panne normale retire les liens créés par cet appel
et tente de produire un rapport bloqué. Un arrêt brutal peut laisser un lot partiel :
**la présence d'un seul GPKG ou d'un seul rapport n'autorise jamais sa réutilisation**.
`verify_conflict_bundle(events_path, cells_path, report_path)` est obligatoire en
aval : il vérifie les trois fichiers, l'intégrité SQLite, les empreintes, identités,
versions, CRS, effectifs, liens, listes et propriétaires. Les chemins font partie
du manifeste ; les lots ne sont pas portables par simple renommage. Aucune sortie
existante, source M1 ou sortie ENJ n'est écrasée ; seuls `data/derived/` et les
répertoires temporaires de tests reçoivent des résultats.

### Configuration et exécution

Les chemins suivants sont des **emplacements d'exemple**, sans fichier officiel
présent. Mapping minimal à adapter après inspection M1 :

```json
{
  "routes": {"id_column": "<identifiant routier M1>"},
  "corridors": {"id_column": "<identifiant corridor M1>"}
}
```

Chaque source accepte aussi `expected_crs`, `category_column`, `structure_column`,
`level_column`, `context_reference`, `subframes` et `coverage`. Les colonnes d'ouvrages
ou de niveaux exigent un dictionnaire référencé par `context_reference`. Le sens
des codes de sous-trame suit le mapping documenté de la phase ENJ. Tous les attributs
disponibles sont conservés sans inventer leur signification. `coverage` reprend le
contrat existant avec `theme = routes` ou `corridors`. Les portées sont données par
`--route-coverage-confirmed` / `--route-coverage` et les options homologues corridors ;
elles ne valent jamais validation seules.

La configuration accepte `grid.id_column` (défaut `maille_id`), les CRS attendus,
le même bloc `spatial` d'emprise M1 et le bloc optionnel :

```json
{
  "precision": {
    "distance_m": "<remplacer par un nombre positif documenté>",
    "reference": "<justification documentaire du scénario>",
    "localization_adequate": null
  }
}
```

Omettre ce bloc sans précision documentée. Les qualifications externes sont une
liste JSON d'`EventEvidence`, liée aux véritables identifiants retrouvés au calcul,
passée par `--qualifications chemin/qualifications_validees.json`.

```sh
/tmp/reconnect-m2-venv/bin/python -m analysis.run_conflicts \
  --grid data/processed/grille_m1.gpkg --grid-layer grille \
  --territory data/processed/territoire_m1.gpkg --territory-layer territoire \
  --routes data/processed/routes_m1.gpkg --routes-layer routes \
  --corridors data/processed/corridors_m1.gpkg --corridors-layer corridors \
  --config chemin/config_conflits_m1.json

/tmp/reconnect-m2-venv/bin/python -m pytest -q tests/
```

Les options `--output-events`, `--output-cells`, `--report` permettent d'autres noms
dans `data/derived/`. Les options de versions restent optionnelles ; ne pas remplacer
une version inconnue par une valeur fictive. Retour `0` uniquement pour un lot
techniquement vérifié, `2` pour un blocage. Un succès technique n'est pas une
validation scientifique territoriale.

### Références examinées et portée de cette adaptation

Le [Cerema, « Identification et priorisation des obstacles aux continuités écologiques
terrestres », 9 janvier 2026](https://www.cerema.fr/fr/actualites/identification-priorisation-obstacles-aux-continuites)
présente une démarche combinant classification de transparence des infrastructures,
ouvrages, infrastructures jumelées, notes de sections et croisement avec les TVB
régionales. **Cette méthode complète n'est pas implémentée ici** : aucune note de
transparence, seuil de franchissabilité ou hiérarchie n'est repris sans ses données
et conditions. La distinction entre croisement géométrique, contexte d'ouvrage et
obstacle documenté est une précaution méthodologique de ReConnect.

Le [SDES, « La fragmentation des milieux naturels terrestres en France : définitions,
cadre conceptuel, méthodologie et résultats détaillés »](https://www.statistiques.developpement-durable.gouv.fr/la-fragmentation-des-milieux-naturels-terrestres-en-france-definitions-cadre-conceptuel)
décrit une analyse fondée sur les milieux naturels, les obstacles fragmentants,
leur découpage et la taille effective de maille selon la méthode CBC de Moser.
Notre nombre d'événements n'est pas cette métrique. Aucune taille effective de
maille n'est calculée ; une étude séparée des hypothèses, données et effets de bord
est nécessaire avant toute implémentation.

L'[OFB, « Rétablir les continuités écologiques »](https://ofb.gouv.fr/retablir-les-continuites-ecologiques)
relie les continuités aux déplacements et cycles de vie des espèces dans différents
milieux et présente des obstacles de diverses natures. Ce contexte ne permet pas
d'assimiler une intersection XY à une rupture fonctionnelle. Il justifie la nécessité
de données et d'expertise écologique au-delà de la géométrie.

Les opérations d'intersection sont des mesures géométriques usuelles ; la
décomposition, le dédoublonnage contextuel, les identifiants, les états de preuve,
les scénarios de précision et le propriétaire canonique sont des **conventions
ReConnect à valider**, pas des formules de fragmentation publiées attribuées à ces
organismes. Les trois pages officielles ont été consultées pour cette extension.

### Données nécessaires et étapes avant usage décisionnel

M1 doit fournir routes/corridors officiels, identifiants stables et segmentation
documentée, catégories, niveaux, ponts/tunnels/ouvrages avec leur dictionnaire,
sous-trames, CRS, emprise pilote et plausible, millésimes, licences et trois versions
de suivi. Les preuves de complétude doivent viser les thèmes et emprises effectivement
analysés. Les preuves d'obstacles doivent être externes, localisées et liées aux
événements examinés ; les paramètres de précision doivent avoir une justification.

Avant priorisation ou règles R1–R4 : confronter le schéma au PRD réel, inspecter les
objets et intersections M1, examiner les cas de niveaux et de frontières, valider
la granularité et le dédoublonnage avec M1/M2, vérifier les ouvrages et preuves,
qualifier l'incertitude cartographique, contrôler les droits puis les éventuels
exports publics. Les connaissances d'espèces et de fonctionnalités restent à
acquérir/valider. Aucun événement synthétique ne constitue un diagnostic normand.

### Vérification de l'extension initiale

La phase précédente a passé ses 107 tests avant modification. L'extension dispose
de 58 tests exclusivement synthétiques couvrant intersections de trois dimensions,
coprésence sans intersection, contacts, superpositions, doublons et segmentation,
identité stable, sous-trames et ouvrages, Z, précision, preuves externes, liens sur
frontières et plusieurs hexagones, absence d'analyse, complétude, lecture/écriture
des lots et pannes de publication. Les modules ENJ existants restent inchangés.

Vérification finale dans le même environnement isolé : **165 tests réussis,
0 échec, 0 erreur, 0 ignoré**, en 7,39 secondes, avec `python -m pytest -q tests/`.
Les aides CLI et la syntaxe des nouveaux modules ont aussi été vérifiées. Aucun
fichier de données territorial ni export public n'a été créé dans le dépôt.

### Audit V6.1 : nature des décisions et vérification

| Nature | Décision / limite |
| --- | --- |
| Mathématique | Intersections exactes, intérieur/frontière, union, relation plusieurs-à-plusieurs et cardinal des événements distincts |
| Technique | CRS explicite et harmonisé en EPSG:2154, sérialisation canonique, propriétaire déterministe, schémas JSON, contrôle SQLite/empreintes/liens/géométries |
| Méthodologique ReConnect | Décomposition des événements, frontière pilote non concluante, distinction des statuts, portée de paire des translations, exigences de résolution externe et masquage par défaut |
| Scientifiquement validée | Aucune nouvelle règle territoriale, seuil, coefficient ou relation croisement→obstacle n'est validée par ces tests synthétiques |
| En attente M1 | Couches réelles inspectées, identifiants et dictionnaires officiels, précision, ouvrages/niveaux, sous-trames, complétude, preuves localisées, droits et versions |
| En attente M4 | PRD complet, confirmation de la proposition `m2-m4.proposal-1`, tableau structuré `source_ids`, états d'attente, géométries masquées/généralisées et métadonnées de collection |

La vérification des lots GPKG contrôle aussi l'intégrité SQLite, les valeurs des
liens, leur concordance avec les intersections géométriques et le choix effectif du
propriétaire canonique. Les nouveaux tests couvrent CRS événements 2154/4326/absent,
hors emprise/types incompatibles, frontières du territoire et communes aux mailles,
multi-événements et portée de sensibilité, promotions avec résolution, interface de
règles synthétiques, schémas et géographie des GeoJSON, références réciproques,
masquage/généralisation, confidentialité, comptages et conversion après GPKG.

Les 165 tests initiaux ont été exécutés avec succès avant correction. La suite
étendue a exécuté **223 tests : 223 réussis, 0 échoué, 0 erreur, 0 ignoré**, en
11,37 secondes avec `/private/tmp/reconnect-m2-venv/bin/python -m pytest -q tests/`.
L'environnement isolé utilise Python 3.10, GeoPandas 1.1.4, Shapely 2.1.2,
pandas 2.3.3, NumPy 2.2.6, pyproj 3.7.1, pyogrio 0.13.0, jsonschema 4.26.0
et pytest 9.2.0. Il émet 38 avertissements de dépréciation provenant de pyproj
lors des transformations de tableaux de taille un avec NumPy ; aucun test ne les
masque. Ces avertissements ne constituent pas une validation des versions futures.

Les tests ne valident ni les données réelles ni les conditions scientifiques d'une
priorisation. Les indicateurs de pression, priorité d'examen et règles R1–R4
restent hors de ce jalon. Aucun fichier public ni donnée territoriale n'a été créé.

## Tables D/S et validation amont — 3 novembre 2026

Cette étape implémente [la table de décision proposal-2](table_decision_m2.md) et
[le contrat QA amont](contrat_qualite_amont_m2.md), séparément du contrat GeoJSON
`m2-m4.proposal-1` qui reste inchangé. La priorité D/S est une convention de triage
à approuver, pas une mesure de biodiversité, de gain écologique ou d'urgence.

### Interfaces et entrées

`analysis/prepare_priority_inputs.py` fournit :

| Interface | Entrées / contrôle | Résultat |
| --- | --- | --- |
| `validate_diagnostic_inputs(cell, pilot)` | Maille, diagnostics normalisés, périmètre pilote versionné, méthodes autorisées et registres des preuves/sources | Copie `PreparedPriorityInputs` contrôlée, ou `PriorityInputError` bloquante |
| `derive_positive_evidence(event, crs=..., review=...)` | Événement M2, géométrie métrique, liens sources, précision, qualification et examen documenté visant exactement `conflit_id` | Capacité positive, références et limites ; ne promeut aucun statut |
| `derive_absence_evidence(detection, study_geometry, ...)` | Détection effectuée, territoire lié par empreinte, emprise H∩T, couvertures, catégories/sous-trames requises et revue temporelle/thématique | Capacité négative et, séparément, absence effectivement établie |
| `detect_assertion_conflicts(assertions, decision_reference=...)` | Assertions présence/absence identifiables et documentées | Contradiction documentée, contrôle sans contradiction retenue, ou contrôle non évalué |
| `derive_applicability(decision=None)` | Décision externe versionnée et référencée, facultative | `inconnue` par défaut ; aucune non-applicabilité inférée d'une couche absente |
| `classify_ecological_stakes(decision=None)` | Classe déclarée et méthode documentée, facultatives | `inconnu` par défaut ; aucun seuil automatique |

`analysis/evaluate_priorities.py` fournit la fonction pure
`evaluate_priorities(cell, pilot)` et le regroupement
`normalize_diagnostics_by_family(prepared)`. Ce dernier conserve plusieurs
diagnostics distincts par famille et les familles absentes sans créer de faux
diagnostics. Aucun module n'ouvre de fichier ni ne dépend d'un frontend.

Le pilote doit déclarer explicitement `territory_id`, `grid_version`,
`dataset_version`, `priority_method_version`, `familles_attendues`, les listes de
`methodes_familles` autorisées, leurs `references_methodes` (`version`, `reference`),
la `decision` de périmètre (`methode_id`, `version`, `reference`, `validated_by`,
`validated_at` ISO), les registres `sources` / `preuves`,
`limites_applicabilite` et `motifs_versions_inconnues`. Une version inconnue reste
null avec motif de traçabilité. Les registres documentent les références ; leur
présence n'authentifie ni les auteurs ni le contenu des documents.

La maille reprend les références du pilote, sa surface étudiée et ses diagnostics.
Chaque diagnostic reprend les champs de la table, y compris les null explicites
(`periode_reference`, références non applicables, etc.). Le registre des sources
contient `namespace`, `id`, `reference`, `periode_reference` ; les diagnostics le
référencent par couples `namespace`/`id`. Le registre des preuves associe chaque
`preuve_id` à une référence non vide. Les périodes, lorsqu'elles existent, sont
des objets `{"debut":"AAAA-MM-JJ", "fin":"AAAA-MM-JJ"}` ordonnés. Une période
diagnostique ne peut pas dépasser la portée documentaire connue d'une source.

Les métadonnées absentes des anciennes fixtures sont complétées **uniquement** par
`tests/m2_priority_helpers.py`, avec des références explicitement SYNTHÉTIQUES.
Le code de production ne les importe jamais et ne possède aucune imputation de
source, méthode, référence ou classe d'enjeu à partir d'un scénario.

### Invariants bloquants

Les codes requis sont implémentés : `E_ID_DUPLIQUE`, `E_FAMILLE_HORS_PERIMETRE`,
`E_TYPE_INVALIDE`, `E_SURFACE_INVALIDE`, `E_PERIMETRE_INVALIDE`,
`E_REFERENCE_NON_APPLICABILITE`, `E_ABSENCE_INCOHERENTE`,
`E_CONTRADICTION_SANS_REFERENCE`, `E_PROUVE_POSITIVE_SANS_SOURCE` (orthographe du
contrat conservée), `E_NON_APPLICABILITE_INCOHERENTE`.

S'ajoutent `E_METHODE_NON_AUTORISEE`, `E_REFERENCE_SOURCE_INVALIDE`,
`E_REFERENCE_PREUVE_INVALIDE`, `E_REFERENCE_INVALIDE`, `E_PERIODE_INVALIDE`,
`E_PERIODE_INCOMPATIBLE`, `E_PREUVE_INVALIDE`. Une combinaison admissible non
couverte lève `E_TABLE_NON_TOTALE`, jamais une priorité indéterminée de repli.

Les booléens de capacité sont stricts. Les identifiants booléens, valeurs inconnues,
NaN/Infinity, surfaces négatives, références dupliquées ou sans registre sont
refusés. Les champs facultatifs connus sont fournis explicitement, éventuellement
null ; ils ne sont pas déduits des données disponibles. Les diagnostics fournis
sur une maille hors territoire restent soumis aux contrôles structurels avant S0.
Le périmètre pilote ne peut pas être réduit automatiquement pour masquer une
famille manquante. Les familles exploratoires restent en dehors de l'entrée D/S ;
les passer parmi les diagnostics décisionnels déclenche `E_FAMILLE_HORS_PERIMETRE`.

### Portée des preuves et limites de l'automatisation

Un examen positif doit attester les liens sources, l'adéquation d'échelle et la
localisation pour l'événement précis, avec méthode/version/référence/auteur/date
et période. Sans cet examen, `validite_positive=false`. Une précision déclarée
valide doit avoir distance finie et référence. Les qualifications existantes sont
réutilisées : un conflit potentiel doit avoir une preuve externe ou une trace de
règle contextuelle versionnée ; un obstacle doit avoir une preuve externe.
Après l'audit correctif, une trace contextuelle doit aussi correspondre à un
registre approuvé distinct et satisfaire encore le prédicat sur le contexte
actuel. Les preuves portent une empreinte d'état de l'événement ; une ancienne
trace sans empreinte ou avec des observations modifiées nécessite un nouvel examen.
Les incertitudes initiales nécessitent une résolution référencée. Ni un ouvrage
appelé « pont » ni un simple croisement ne produit une confirmation automatique.
La sensibilité `source_pair` est conservée comme limite sans inférer de précision
locale. Les attestations humaines ne sont pas authentifiées par le logiciel.

Le contrôle négatif réutilise `_coverage_geometry` et `_fully_covered`, y compris
les preuves de complétude thématique `validated` et l'empreinte du territoire. Il
vérifie séparément l'emprise exacte, les sources requises, les codes de catégories
et sous-trames demandés contre ceux couverts par la revue, et les périodes des
deux sources. Les listes de codes doivent être explicitement déclarées ; une
liste vide signifie qu'aucun filtre de ce type n'est requis par la méthode,
jamais que les catégories ou sous-trames sont inconnues. Tous les événements
intersectant H∩T sont retenus par prudence ; aucun filtrage écologique implicite.

`validite_absence=true` exprime une capacité et peut coexister avec un événement
positif. `absence_etablie=true` exige en plus zéro événement pertinent observé.
Si des événements existent, l'adaptateur négatif ne choisit pas arbitrairement un
signal représentatif : `signal_pression=null` impose l'adaptateur positif. Si la
preuve d'absence manque, il renvoie `non_evalue` / `absence_non_demontree`.
La couverture inconnue ne devient donc jamais une absence validée.

Le contrôle de contradictions compare propriété, objet, emprise et périodes
documentaires. Il n'infère aucune contradiction de la seule coexistence des couches.
À ce stade, les périodes doivent être **identiques** pour conclure à une
incompatibilité ; des périodes disjointes sont distinctes et des périodes
recouvrantes différentes restent de comparabilité non établie. Les emprises sont
des identifiants harmonisés en amont, pas une équivalence géométrique devinée.
Un contrôle impossible ou incomplet retourne `contradiction_bloquante=null` avec
`etat_controle=non_evalue` : ne pas le convertir silencieusement en `false` pour
alimenter D/S. Une contradiction retenue exige une référence de décision et garde
les références des assertions incompatibles. `integrate_assertion_control()` lie
explicitement le contrôle à la pression, à l'applicabilité ou à une autre
affirmation, avec référence de portée. Le moteur accepte alors le null structuré
et conserve l'inconnue ; sans ce contrôle, les entrées historiques exigent des
booléens stricts. Une preuve indépendante documentée peut conserver son signal,
avec couverture partielle quand le contrôle inconnu affecte la décision. Il ne
certifie aucune absence universelle de contradiction à partir de false.

### Décision et restitution

Les règles D sont appliquées dans l'ordre D0, D1, D2, D3, D4, D5, D6, D7, D8, D9,
D10a. Plusieurs prédicats peuvent être vrais, seule la première décision gagne.
La synthèse applique S0 avant toute restitution territoriale, puis S1, S2, S3, S4.
Un signal élevé conserve la priorité élevée même avec une autre famille non
évaluable. Plusieurs signaux modérés ne deviennent pas élevés. Une famille absente
ou un diagnostic applicable insuffisamment évalué interdit S3. D10a peut produire
`indeterminee + complete`, distinct de l'indétermination par données manquantes.
`complete` reste la complétude décisionnelle, jamais une certification de couverture SIG.

Les sorties comprennent les dix champs minimaux demandés, les détails par
diagnostic, références méthodologiques, entrées conservées, sources/phénomènes et
liens documentés. Les motifs principaux restent associés à **chaque** diagnostic,
même si une autre famille détermine la couleur. Les limites QA sont conservées.
Les recoupements source/phénomène sont signalés sans fusion ni bonus ; sans lien
explicite, le résultat est `relation_non_etablie`, jamais « indépendants ».

Deux clarifications de spécification sont explicites :

1. Les fixtures excluent de `motifs_limites` les motifs de décision concluante
   D5–D9 et la non-applicabilité D0, malgré la formulation large « union des motifs
   principaux » de la table. Le moteur suit leurs attentes : tous les motifs
   principaux sont dans `motifs_principaux_diagnostics` ; les limites contiennent
   les motifs d'indétermination, motifs QA et limites synthétiques.
2. Les index Python `regles_diagnostics` et `motifs_principaux_diagnostics`
   préservent les clés entières et chaînes. Une sérialisation JSON directe pourrait
   confondre `1` et `"1"`. Les enregistrements de `diagnostics[]` gardent les IDs
   typés sans perte ; M3/M4 doivent privilégier ces enregistrements dans la future
   représentation publique. `prepare_priority_result_json()` convertit désormais
   explicitement les index en tableaux typés dans une copie interne, sans modifier
   les interfaces Python. Aucun export public proposal-2 n'est activé.

Les listes sont triées et dédoublonnées après contrôle des identités et références.
Le tri des identifiants utilise le JSON canonique existant. L'ordre des diagnostics
ou des sources n'affecte pas les sorties. Les fonctions ne modifient pas les entrées.

### Vérifications et conditions avant M1

Le [compte rendu détaillé](verification_m2_priorites.md) consigne les 38 scénarios,
les 576 combinaisons, la monotonie conditionnelle et le bilan pytest local.
Les oracles existants restent inchangés. Aucun seuil, coefficient, classement
d'efficacité, règle d'action ou GeoJSON de production n'est créé.

M1 doit encore fournir les couches officielles préparées, dictionnaires et codes
de catégories/sous-trames/ouvrages, emprises, précision et aptitude de localisation,
périodes, complétudes spatiales/thématiques, versions et droits. M2 doit approuver
les méthodes d'enjeu, d'applicabilité, de qualification contextuelle et la traduction
de chaque famille vers D avant de l'inclure au pilote. L'implémentation ne déclare
aucune de ces méthodes scientifiquement validée par la réussite des tests.
Trois secteurs réels contrastés restent à examiner manuellement après livraison.
La migration de contrat reste à confirmer avec M3/M4 dans
[les notes proposal-2](notes_contrat_m3_m4_proposal2.md). `fiches_zones.json` reste
propriété scientifique M2, `catalogue_actions.json` reste maintenu par M5, et le
moteur R1–R4 reste à M4.

### Audit correctif d'intégration

Le [compte rendu correctif](audit_correctif_priorite_m2.md) complète le bilan
précédent : **1 007 tests réussis, 0 échec, 0 erreur, 0 ignoré, 38 avertissements
pyproj**, dont les 948 antérieurs inchangés et 59 nouveaux tests. Les 38 scénarios
et les 576 oracles D sont conservés. D0 reste avant D1 ; une justification de
non-applicabilité explicitement contestée est bloquée en amont, et une portée de
contradiction manquante empêche de certifier une couverture suffisante pour S3.

Le résultat distingue désormais l'état SIG fourni par l'appelant
(`statut_analyse`, null s'il n'est pas connu), l'état de calcul D/S
(`etat_calcul_priorite`) et la couverture décisionnelle (`couverture_synthese`).
Une maille positive sans diagnostic retourne S4/indéterminée/partielle sans inventer
une analyse SIG effectuée. Les adaptations proposées pour M3/M4 sont décrites dans
les notes proposal-2 ; les contrats GeoJSON proposal-1 restent inchangés.
