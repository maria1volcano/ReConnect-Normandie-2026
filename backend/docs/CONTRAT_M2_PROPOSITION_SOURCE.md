# Proposition de contrat M2 → M4 — `m2-m4.proposal-1`

Ce jalon fournit deux FeatureCollections liées, leurs schémas JSON Schema Draft
2020-12 et des exemples **SYNTHÉTIQUES**. Il ne publie aucune donnée territoriale.
Le PRD complet n'est pas présent dans ce dépôt : les noms obligatoires reprennent
la demande V6.1. Cette proposition doit être confirmée avec M4 avant de devenir
un contrat de production. Elle ne remplace aucun contrat M4 existant en silence.

## Fichiers et usage

- [Schéma des mailles](schema_mailles.json).
- [Schéma des conflits](schema_conflits.json).
- [Mailles synthétiques](../tests/fixtures/m2/synthetic_mailles.geojson).
- [Conflits synthétiques](../tests/fixtures/m2/synthetic_conflits.geojson).
- Préparation et validation : `analysis/export_m2_contract.py`.

```python
from analysis.export_m2_contract import prepare_m2_contract, validate_m2_contract

# result est un ConflictAggregation synthétique contrôlé.
mailles, conflits = prepare_m2_contract(
    result,
    versions={"grid_version": None, "method_version": result.cells.method_version.iloc[0],
              "dataset_version": None},
    test_data=True,
)
validation = validate_m2_contract(mailles, conflits)
```

La version de méthode doit être celle de la détection et des mailles. Pour des objets
relus depuis un lot GPKG, appeler d'abord `verify_conflict_bundle` et reprendre les
versions et le `run_id` du rapport vérifié. Le convertisseur n'ouvre aucun chemin
de production et n'écrit aucun fichier. `test_data=False` est bloqué. `test_data=True`
est une déclaration de l'appelant, dont il doit garantir l'exactitude.

## Enveloppe commune

Les deux collections ont les membres obligatoires suivants :

```json
{
  "type": "FeatureCollection",
  "contract_version": "m2-m4.proposal-1",
  "test_data": true,
  "statut_diffusion": "synthetique_uniquement",
  "provenance": {
    "run_id": "RUN-SYNTHETIQUE-M2-M4",
    "grid_version": "GRILLE-SYNTHETIQUE",
    "method_version": "METHODE-SYNTHETIQUE-TEST",
    "dataset_version": null
  },
  "resume": {
    "analyse_effectuee": true,
    "evenements_distincts_observes": 4,
    "relations_spatiales": 5
  },
  "features": []
}
```

Ce fragment montre l'enveloppe ; les quatre événements et cinq liens sont ceux
des fixtures complètes. Une collection vide avec ce résumé ne serait pas valide
selon le validateur croisé. Les membres métier de l'enveloppe sont des membres
étrangers GeoJSON. Aucun membre `crs` n'est admis. Les deux enveloppes doivent
porter les mêmes métadonnées. Les versions inconnues restent `null`, sans valeur
fictive. Le résumé ne somme jamais les effectifs locaux.

## Structure d'une Feature maille

`geometry` est un Polygon ou MultiPolygon en longitude/latitude, ou `null` pour
une maille hors territoire. Les propriétés autorisées sont :

| Propriété | Type / sens | Correspondance interne |
| --- | --- | --- |
| `maille_id` | Chaîne non vide ou entier ; conserver le type | `maille_id` |
| `grid_version`, `method_version`, `dataset_version` | Chaîne ou `null` | Rapport du lot, sans imputation |
| `statut_analyse` | `analyse_effectuee`, `absence_analyse`, `hors_territoire` | `etat_analyse` |
| `priorite_examen` | `{ "etat": "non_calculee", "valeur": null }` produit à ce jalon | Aucune priorité calculée |
| `diagnostics` | Tableau de codes, jamais texte JSON | `[diagnostic]` |
| `indicateurs` | Objet de trois comptages entiers nullables | Voir ci-dessous |
| `qualite` | Objet typé de complétude, couverture validée et fiabilité | Champs internes homologues |
| `conflit_ids` | Tableau de chaînes uniques | Décodage de `conflit_ids` GPKG |
| `action_ids` | Tableau vide pour l'instant | Actions non calculées |
| `etat_actions` | `non_calculees` | État explicite de la liste vide |

`indicateurs` contient exclusivement `nb_evenements_observes`, `nb_evenements` et
`nb_evenements_exclusifs_observes`. Un zéro observé signifie analyse effectuée
sans événement observé ; un zéro de `nb_evenements` exige les deux couvertures
validées sur la maille. Sans analyse, les trois valeurs sont `null`.

`qualite` contient `routes_completude` / `corridors_completude` (`unknown`,
`declared`, `validated`), `routes_couverture_validee` /
`corridors_couverture_validee` (booléens portant sur la maille), et `fiabilite`.
Une validation documentaire peut être partielle spatialement : le statut de la
source peut être `validated` sans couvrir la maille entière.

Les cinq codes de diagnostic sont `hors_territoire`, `absence_analyse`,
`croisements_observes`, `absence_croisement_confirmee`,
`absence_observation_couverture_non_validee`. Ils décrivent des observations
géométriques et la couverture, sans inférer un état écologique.

Le schéma réserve aussi `priorite_examen.etat = indeterminee` : ce serait le
résultat d'un examen de priorisation effectivement tenté et insuffisamment
étayé. Le convertisseur ne l'assigne jamais ici. `non_calculee` signifie que cette
étape n'est pas développée. Aucune valeur de priorité, indicateur de pression,
action ou règle R1–R4 n'est inventé.

## Structure d'une Feature conflit

`geometry` est un membre de la Feature, **pas une propriété dupliquée**. Le schéma
admet Point, LineString, Polygon et leurs types multiples, ou `null`. Les événements
bruts sont des parties simples ; la généralisation contrôlée peut produire un
autre type compatible.

| Propriété | Type / sens | Correspondance interne |
| --- | --- | --- |
| `conflit_id` | Chaîne unique | `conflit_id` |
| `type` | `route_corridor` | `type` |
| `evidence_level` | `geometrie_2d`, `criteres_examen_documentes`, `preuve_externe_documentee`, `regle_contextuelle_documentee` | Champ homologue |
| `statut` | `croisement_detecte`, `conflit_potentiel`, `obstacle_confirme`, `non_concluant` | Qualification, distincte de la détection |
| `source_ids` | Tableau structuré `{ "role": "routes" ou "corridors", "id": chaîne ou entier }` | Transformation explicite de l'objet interne |
| `maille_ids` | Tableau d'identifiants uniques, non vide | Décodage de `maille_ids` GPKG |
| `precision_affichage` | Code de localisation initial ou `localisation_masquee` / `localisation_generalisee` | État effectif de l'affichage |
| `limites` | Tableau de textes publics autorisés | Textes contrôlés du convertisseur ; aucun texte libre interne |
| `method_version` | Chaîne ou `null` | Rapport/détection concordants |
| `territory_relation` | `interieur`, `frontiere`, `interieur_et_frontiere` | Relation au territoire, indépendante des mailles |
| `diffusion` | Géométrie, autorisation des identifiants sources, état de décision | Politique explicite de diffusion |

Transformation proposée pour `source_ids`, uniquement si leur diffusion est
explicitement autorisée :

```json
{"routes": ["R1"], "corridors": ["C1", "C2"]}
```

devient :

```json
[
  {"id": "C1", "role": "corridors"},
  {"id": "C2", "role": "corridors"},
  {"id": "R1", "role": "routes"}
]
```

Le format interne GPKG reste inchangé. Le tableau préserve les rôles et types
d'identifiants. Il ne restitue pas les paires réellement observées : ne pas en
déduire un produit cartésien de relations documentaires. Une éventuelle extension
avec espace de noms documentaire devra être convenue avec M4.

## Géographie, relations et sérialisation

Le profil suit [RFC 7946](https://www.rfc-editor.org/rfc/rfc7946) : WGS84/CRS84,
ordre **longitude, latitude**, degrés décimaux. Les calculs et liens sont établis
en EPSG:2154, avant conversion. Le convertisseur force XY, oriente les anneaux
extérieurs dans le sens antihoraire et les trous dans le sens horaire. Il n'arrondit
pas les coordonnées. Il ne recalcule pas les liens depuis des géométries publiques
masquées ou généralisées.

Les deux [JSON Schemas Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-validation)
contrôlent les types, propriétés autorisées, tableaux réels, coordonnées finies
dans les domaines longitude/latitude, nombre de sommets et décisions de masquage.
Le validateur Python complète ces contrôles : validité topologique, fermeture des
anneaux, absence de segments régionaux non découpés à l'antiméridien, unicité des
identifiants, existence et réciprocité des références, versions et comptages.
La plage numérique ne prouve pas que le CRS initial a été correctement déclaré,
ni que l'emprise correspond au terrain : les contrôles M1 restent nécessaires.

Les identifiants sont uniques par collection ; ils peuvent apparaître dans
plusieurs listes de relations. Chaque conflit partagé conserve **une seule
Feature**. `maille_ids` et `conflit_ids` définissent exactement la même relation
plusieurs-à-plusieurs. Les relations sont calculées même pour un contact sur la
frontière commune de deux mailles. Le propriétaire canonique préfère l'intérieur,
puis le plus petit identifiant selon son JSON canonique ; il sert seulement au
comptage exclusif. Le total global compte les événements distincts.

Tri déterministe : Features mailles et listes d'identifiants selon le JSON canonique
de leur identifiant ; Features conflits selon `conflit_id` ; `source_ids` selon le
JSON canonique de chaque objet ; limites publiques dans l'ordre lexicographique.
`canonical_json` trie les clés, emploie UTF-8, des séparateurs constants et refuse
NaN/Infinity. Les identifiants entier `1` et chaîne `"1"` restent distincts. Le
validateur accepte les ordres équivalents ; le convertisseur produit l'ordre canonique.

## Confidentialité et diffusion

Les schémas refusent les propriétés supplémentaires à tous les niveaux. Le
convertisseur construit chaque propriété explicitement. Il ne recopie jamais les
attributs sources complets, observations naturalistes, `observations`, `preuves`,
références privées ou textes libres de `limites`. Les versions, identifiants de
run et codes autorisés doivent eux aussi être revus avant une future diffusion.

Sans `ConflictDisclosure` : `geometry = null`, `source_ids = []`,
`precision_affichage = localisation_masquee`. L'identité et les relations restent
présentes. Pour une géométrie exacte ou des identifiants sources, une référence
d'autorisation déclarée est obligatoire. Pour `generalisee`, l'appelant fournit
aussi une géométrie et son CRS ; aucun rayon ou déplacement n'est inventé.
La référence d'autorisation reste interne. L'outil ne l'authentifie pas.
L'appelant doit archiver cette décision et sa référence dans son dossier interne,
liées au `run_id` et au `conflit_id`, pour pouvoir justifier une généralisation ou
une autorisation. La copie destinée à M4 contient seulement l'état de décision.

Le masquage d'un point conserve une localisation indirecte par ses mailles et ses
relations. Cette possibilité doit être examinée lors de la future revue des droits,
y compris pour les géométries des mailles. Ce jalon ne certifie aucune anonymisation
et ne permet pas la diffusion de production. La validité SIG n'établit aucun droit.
Ne pas créer `data/public/mailles.geojson` ni `data/public/conflits.geojson`.

## Prérequis M1 et décisions à confirmer avec M4

M1 doit fournir les couches et identifiants stables, dictionnaires de catégories,
sous-trames et ouvrages/niveaux, millésimes, CRS et emprises validées, précision
et aptitude à la localisation, complétude sur les emprises concernées, licences
et restrictions de diffusion. Toute preuve d'obstacle doit viser l'événement et
résoudre son éventuelle incertitude de localisation avec une référence vérifiable.

M4 doit confirmer la version de contrat et son alignement avec le PRD réel,
le tableau `source_ids` structuré, les types d'identifiants, les états de priorité
et d'actions, les codes de diagnostics/qualité, les géométries nulles et généralisées,
les membres étrangers de l'enveloppe et les règles de comptage. Toute modification
incompatible exigera une nouvelle version convenue du contrat.

La priorité scientifique réelle reste bloquée par l'absence de règles validées,
de données M1 inspectées, de validation de fonctionnalité écologique et de preuves
localisées suffisantes. Un comptage de croisements ou une translation ne constitue
ni une pression écologique, ni une probabilité d'erreur, ni une priorité d'action.
