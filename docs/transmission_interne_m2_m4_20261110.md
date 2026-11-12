# M2 → M4 — Proposition d'ingestion interne des observations réelles

**10 novembre 2026 — consultation et démonstration internes uniquement.** Les données sont réelles, de version `M1-V1`, sur la grille `M1-CAND-1KM2-FLAT-L93-O0-V1`. Le format documentaire associé est `m2-descriptif-interne-1`, `method_version=null`. Cette proposition ne modifie pas le [contrat public](api_contract_m2_m4.md), encore limité aux exemples synthétiques. Aucun appel à l'exporteur public ni contournement de `test_data=False` ; aucun envoi réalisé.

## Lot à lire et conserver ensemble

Tous les chemins ci-dessous partent de la racine du dépôt. Le [manifeste d'ingestion](../data/derived/m2_diagnostics_20261110_01/manifest_ingestion_interne.json) donne les SHA-256 complets, les types SQLite de **tous** les champs et les runs d'origine. Les couches spatiales sont en **EPSG:2154**, mètres et mètres carrés. Reprojeter en longitude/latitude uniquement dans la vue cartographique, sans réécrire les sources.

| Chemin | Couche / table | Rôle et clé |
| --- | --- | --- |
| `data/derived/m2_frontiere_20261109_01/data/derived/branche_conflits.gpkg` | `conflits_candidates`, 1 069 LineString | Clé `conflit_id` ; géométrie de l'événement d'origine |
| `data/derived/m2_frontiere_20261109_01/data/derived/branche_mailles.gpkg` | `mailles_conflits`, 43 Polygon | Clé `maille_id` ; observations locales et complétude |
| Même GeoPackage mailles | `liens_mailles_conflits`, 1 184 lignes non spatiales | Clé composée `conflit_id, maille_id` ; `relation_spatiale`, `canonical_owner` |
| `data/derived/m2_reel_20261109_01/data/derived/enjeux_m1_reels.gpkg` | `indicateurs_enjeux`, 43 Polygon | Jointure 1:1 `maille_id` avec les mailles de conflits |
| `data/derived/m2_frontiere_20261109_01/data/processed/grille_pilote.gpkg` | `grille_pilote`, 43 Polygon | `maille_id`, `is_boundary`, `pilot_fraction` ; conserver la convention de grille |
| `data/derived/m2_frontiere_20261109_01/data/processed/pilote_contour.gpkg` | `pilote_contour`, 1 Polygon | Emprise d'étude ; distincte d'une preuve de couverture source |
| `data/derived/m2_frontiere_20261109_01/data/processed/routes.gpkg` | `routes`, 1 924 MultiLineString Z | Contexte source `route_id`, `categorie`, attributs routiers ; Z ne qualifie pas un ouvrage |
| `data/derived/m2_frontiere_20261109_01/data/processed/corridors.gpkg` | `corridors`, 16 MultiPolygon | `objet_id`, `classe_corridor`, `sous_trame`, millésime ; matrices SRCE surfaciques |
| `data/derived/m2_frontiere_20261109_01/data/processed/reservoirs.gpkg` | `reservoirs`, 40 Polygon | Contexte de réservoir, sans classement d'enjeu automatique |

Compagnons obligatoires :

- `data/derived/m2_frontiere_20261109_01/data/derived/branche.validation.json` ; run conflits `36e70e86-3cdd-4afb-b5c8-6ff37438b607`.
- `data/derived/m2_reel_20261109_01/data/derived/enjeux_m1_reels.validation.json` ; run enjeux `7e5430a6-d6d9-48c1-b522-36dea974c457`.
- `data/derived/m2_frontiere_20261109_01/VALIDATION.json` et `execution/comparaison_branche_reference.json` dans ce même dossier ; validation déjà acquise de l'intégration.
- `data/derived/m2_reel_20261109_01/run_manifest.json`, `execution/resultats_verifies.json` et `m1_reference/sources.json` ; historique M1 et du calcul initial.
- Les quatre JSON de `data/derived/m2_diagnostics_20261110_01/` et le [compte rendu scientifique](diagnostics_ecologiques_reels_m2_20261110.md).

Les rapports existants contiennent des chemins absolus et des chemins relatifs à leurs copies de travail. Conserver l'arborescence des lots ; en cas de transport, résoudre les chemins via le nouveau manifeste sans modifier les rapports historiques. `ok=true` atteste les contrôles techniques du lot, pas sa qualification écologique. L'ancien `RESULTATS.md` décrit le correctif local à sa date ; pour l'état intégré, consulter les documents de finalisation du 9/10 novembre, sans réécrire cet historique.

## Jointures, champs et types à conserver

Lire les IDs comme des chaînes intactes, y compris les `+` des `maille_id`. Les FID SQLite sont techniques : ne pas les employer comme identifiants métier. Utiliser une connexion SQLite en lecture seule pour la table des liens ; elle n'est pas une couche cartographique supplémentaire.

| Objet | Champs utiles à la vue | Traitement |
| --- | --- | --- |
| Événement | `conflit_id`, `statut`, `type`, `detection_status`, `intersection_relation`, `intersection_dimension`, `territory_relation`, `evidence_level`, `length_m` | Conserver `croisement_detecte`, `geometrie_2d` et la relation brute ; longueur descriptive, pas importance écologique |
| Références événement | `source_ids`, `source_pairs`, `maille_ids`, `observations`, `preuves`, `limites` | Textes JSON à décoder explicitement ; tableaux/objets, pas libellés bruts à concaténer. `preuves=[]` n'est pas une preuve d'absence |
| Qualité événement | `precision_affichage`, `precision_m`, `precision_reference`, `precision_sensitive`, `numeric_residue`, `method_version` | Précision non documentée, inconnues NULL conservées. Un résidu numérique admissible ne prouve aucune précision cartographique |
| Maille | `conflit_ids`, `nb_evenements_observes`, `nb_evenements_exclusifs_observes`, `nb_evenements`, `etat_analyse`, `diagnostic`, `fiabilite` | Décoder la liste d'IDs ; distinguer compte observé, propriétaire exclusif et compte complet inconnu |
| Couverture maille | `routes_coverage_confirmed`, `corridors_coverage_confirmed`, `routes_completeness_status`, `corridors_completeness_status` | Booléens de confirmation et statuts `unknown` conservés ; `false` n'est pas une absence d'objet |
| Enjeux | `study_area_m2`, `reservoir_observed_area_m2`, `corridor_observed_area_m2`, `enj_01_pct`, `enj_01_status`, `enj_02_presence`, `enj_02_status`, champs de couverture | ENJ-01 NULL partout ; ENJ-02 30 présences observées, 13 inconnues. En GPKG relu, `enj_02_presence` peut être float nullable : `1.0→true`, NULL reste inconnu, ne pas appliquer `bool(NaN)` |
| Lien | `conflit_id`, `maille_id`, `relation_spatiale`, `canonical_owner` | Une ligne par relation ; propriétaire entier SQLite 0/1. Les 1 184 relations sont toutes `interieur`, sans préjuger de la relation événement/frontière du pilote |

Un filtre maille utilise les liens pour sélectionner des événements **distincts par `conflit_id`**. La vue locale peut montrer un événement entier dépassant cette maille ; conserver sa géométrie et ses autres rattachements. Les sources routières sont des objets M1 distincts des géométries d'événements. Le regroupement `groupe_geometrie_id` est un SHA-256 de WKB XY normalisé, lié aux IDs dans `situations_geometriques.json` ; ce n'est ni un nouveau conflit, ni un identifiant de phénomène écologique.

Comptes à afficher :

- Global : 1 069 événements distincts ; 789 tronçons sources ; 953 géométries exactes ; 1 184 liens.
- Local : `nb_evenements_observes`, pouvant inclure des observations présentes ailleurs ; somme des mailles = 1 184.
- Agrégation exclusive : `nb_evenements_exclusifs_observes`, somme = 1 069 ; propriétaire canonique utilisé uniquement pour ce comptage.
- Nombre complet `nb_evenements` : NULL sur 43 mailles. Zéro observé dans 14 mailles ne devient pas absence validée.

## Vue cartographique proposée

Libellé principal : **« Observations cartographiques routes–matrices SRCE ; qualification écologique non évaluée »**. Afficher routes et matrices comme contexte, avec catégories brutes filtrables ; distinguer transversal/superposition par style de ligne. Une sélection ouvre les objets sources, la liste des mailles, les limites et le groupe de géométrie partagée. Ne pas juxtaposer deux géométries identiques comme deux obstacles distincts ; une sélection du groupe doit rendre accessibles tous les IDs techniques.

La fiche maille peut afficher aire réellement étudiée, observations locales, ENJ-02 et aire de réservoir observée. Toujours accompagner les NULL d'une explication. Mentionner « priorité non calculée », « actions non calculées », « couverture non attestée ». Aucun vert rassurant pour zéro observé, aucune légende fort/faible dérivée des classes de matrices, aucun rang de danger fondé sur les comptes ou catégories. Les mailles partielles sont identifiées ; pas de comparaison directe de comptes bruts sur des aires différentes. La précision inconnue doit rester visible à l'échelle de consultation ; aucune localisation d'ouvrage précis n'est validée.

## Exemples réels immédiatement utilisables

[secteurs_demonstration.json](../data/derived/m2_diagnostics_20261110_01/secteurs_demonstration.json) fournit S1 à S4 : quatre IDs complets de maille, leurs faits et textes, et 20 objets d'exemple (5/9/6/0) avec `conflit_id`, `source_pairs`, attributs sources, rattachements, propriétaire et SHA-256 WKB. Ce sont des sélections du lot, pas une nouvelle couche ni un échantillon représentatif pour estimer une fréquence. La couche d'origine fournit les géométries.

Exemple de lecture locale, sans conversion publique ni moteur scientifique :

```python
import json
import sqlite3
from pathlib import Path
import geopandas as gpd
import pandas as pd

root = Path.cwd()
lot = root / "data/derived/m2_frontiere_20261109_01/data/derived"
demo = json.loads((root / "data/derived/m2_diagnostics_20261110_01/secteurs_demonstration.json").read_text())
case = demo["secteurs"][0]
maille_id = case["maille"]["maille_id"]
with sqlite3.connect((lot / "branche_mailles.gpkg").as_uri() + "?mode=ro", uri=True) as db:
    liens = pd.read_sql_query(
        "SELECT * FROM liens_mailles_conflits WHERE maille_id = ?", db,
        params=[maille_id],
    )
evenements = gpd.read_file(lot / "branche_conflits.gpkg", layer="conflits_candidates")
selection = evenements[evenements.conflit_id.isin(liens.conflit_id)].copy()
# selection contient les événements originaux ; consulter en EPSG:2154
# ou selection.to_crs(4326) dans la vue, sans écriture sur les fichiers sources.
```

## Texte prêt à transmettre — brouillon non envoyé

> M4, le lot réel M2 est prêt pour une ingestion interne de démonstration. Les GeoPackages consolidés contiennent 43 mailles, 1 069 événements routes–matrices et 1 184 liens, avec un propriétaire canonique par événement. Le manifeste `data/derived/m2_diagnostics_20261110_01/manifest_ingestion_interne.json` référence couches, champs, empreintes, versions et compagnons. Les quatre secteurs S1–S4 et 20 exemples sont dans `secteurs_demonstration.json`. Merci d'afficher ces données comme observations géométriques non qualifiées, de conserver inconnues et couverture non attestée, et de distinguer événements et liens locaux. Priorités et actions restent non calculées ; zéro observé ne prouve pas une absence. Cette transmission concerne la consultation interne : le contrat public et son blocage de l'export réel restent inchangés. Merci de confirmer la lecture du lot et cette sémantique avant toute diffusion.
