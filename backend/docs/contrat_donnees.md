# Contrat de données M4 — état d'intégration **provisoire**

Date de référence : 3 novembre 2026. Ce fichier **décrit ce qui est implémenté**, mais il **ne prétend pas être une validation finale de l'équipe**. La version source M2 est `m2-m4.proposal-1` (voir `CONTRAT_M2_PROPOSITION_SOURCE.md`). Les fichiers `schemas/schema_mailles.json` et `schemas/schema_conflits.json` sont reproduits tels que transmis par M2.

## Entrée SIG obligatoire

Une paire complète :
- `mailles.geojson` : FeatureCollection, diagnostiques par maille, identifiants `maille_id`, `conflit_ids[]` ; `statut_analyse`, `priorite_examen`, `diagnostics[]`, `indicateurs`, `qualite`, `action_ids[]`, `etat_actions` ; géométrie Polygon/MultiPolygon ou `null`.
- `conflits.geojson` : FeatureCollection d'événements **uniques**, `conflit_id`, `maille_ids[]`, `statut`, `evidence_level`, `diffusion`, `source_ids[]`, `limites[]` ; géométrie null/explicite selon diffusion.

Le backend valide les deux fichiers *ensemble*, notamment la réciprocité des références, les versions, la topologie et les comptages ; il refuse les fichiers invalides dès le démarrage. Les `maille_id` entiers et chaînes sont deux types distincts. Un conflit lié à deux mailles est renvoyé par les deux filtres locaux mais ne compte qu'une fois dans `/conflits` et `/health`.

## À ne pas confondre

| M2 — données | M3 — ancienne maquette | Décision backend |
|---|---|---|
| `statut_analyse: analyse_effectuee` | `calculee` | Le backend restitue **la valeur M2**, conversion de présentation uniquement via adaptateur M3 |
| `priorite_examen: {"etat":"non_calculee","valeur":null}` | `priorite_examen: "elevee"` | **Aucune priorité inventée** ; M3 doit utiliser un style neutre |
| `diagnostics: ["croisements_observes"]` | `diagnostics: [{type:...}]` | Restitution M2 ; adaptation au frontend seulement |
| `test_data: true` à la racine | `test_data` dans chaque Feature | Restitution M2 ; le frontend propage le label TEST |
| `geometry: null` pour certains conflits | affichage carte | Le backend **conserve null**, sans géolocalisation de remplacement |
| `resume` global du lot | viewport filtré | `resume` est global et `X-Total-Count` porte le total filtré |

## Routes

- `/zones` et `/mailles` : GeoJSON avec `bbox`, `offset`, `limit`. Le paramètre bbox est en **lon/lat CRS84**. `/zone` est un alias de collection transitoire.
- `/zones/{maille_id}` : propriétés M2, géométrie, `test_data`, versions, et `fiche`/`dimensions` à `null` tant que M2 ne transmet pas `fiches_zones.json`.
- `/conflits`, `/conflits/{conflit_id}`, `/zones/{maille_id}/conflits` : événements **sans déduplication erronée**. `maille_id` permet de filtrer.
- `/actions`, `/actions/{action_id}` : routes disponibles ; catalogue en attente M5, sans suggestion fabriquée.
- `/sources` : inventaire candidat M1 ; ne pas confondre avec validation juridique, technique ou scientifique.
- `/health`, `/metadata` : état du backend et provenance.

HTTP `404` pour identifiant absent, `409` si un ID URL numérique est ambigu entre entier et chaîne, `422` pour paramètres malformés, `503` pour le détail d'action quand M5 n'a pas livré de catalogue.

## Documents à obtenir pour stabilisation

- M2 : export territorial réel **avec décision de diffusion documentée**, nouvelle version du contrat intégrant les priorités/états d'actions validés, `fiches_zones.json` final.
- M5 : `catalogue_actions.json` final, dictionnaire des statuts/motifs et liens entre `action_id`.
- M1 : inventaire validé, licence et restrictions confirmées et version des données utilisées par M2.
- M3 : accord sur le mapping des statuts, la bannière synthétique, la localisation du territoire pilote et le rendu des priorités non calculées.

Ce contrat de démonstration **ne publie aucune analyse réelle**. Une migration de `m2-m4.proposal-1` vers un contrat de production devra être revue explicitement et accompagnée de tests d'intégration.
