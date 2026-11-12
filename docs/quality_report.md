# M1 — Rapport de qualité technique

Date : 3 novembre 2026
Statut : **validation technique terminée, validation scientifique requise**

## Résumé exécutif

Le package M1 fournit une grille hexagonale candidate (43 mailles, 29,17 km²) et des mesures géographiques élémentaires calculées sur 8 sources réelles (réservoirs, corridors, routes, sols, zones construites, haies, friches, zones humides). Tous les calculs sont en EPSG:2154 avec reproductibilité vérifiée. La documentation des sources et des limitations est complète. M2 doit valider la pertinence scientifique de la grille, des nomenclatures et des règles de détection avant toute interprétation écologique.

## Couverture géographique du pilote

| Paramètre | Valeur |
|---|---:|
| Bbox WGS84 (lon/lat) | `[-0.28, 49.20, -0.22, 49.26]` |
| Bbox EPSG:2154 (m) | `[460989.257242, 6904815.661232, 465631.045140, 6911663.950544]` (calculée par le pipeline) |
| Aire du pilote | `29 171 588,4672 m²` ≈ 29,17 km² |
| Aire nominale hexagone | `1 000 000 m²` (1 km²) |
| Côté hexagone calculé | `620,4032394014 m` |
| Mailles intersectant le pilote | 43 |
| Hexagones intérieurs complets | 15 |
| Mailles de bordure découpées | 28 |
| Aire minimale d'un fragment | `11,7282 m²` |
| Aire maximale | `1 000 000,0000 m²` |

Le rectangle pilote est une emprise technique pour l'estuaire de l'Orne, non une limite écologique ou administrative. La résolution de 1 km² est le candidat initial demandé par le PRD ; M2 doit tester la sensibilité à une autre résolution ou un décalage si nécessaire.

**Correction du 10 novembre 2026 :** la bbox Lambert-93 estimée précédemment était erronée. La valeur ci-dessus provient de `data/processed/m1_processing_report.json`, sortie autoritative du pipeline de reprojection. Cette correction documentaire ne modifie ni la grille, ni ses géométries, ni ses identifiants.

## Couches disponibles et manquantes

### Couches P0 (prioritaires) — intégrées

| Source | Statut | Fichiers bruts | Fichiers traités | Objets dans pilote | Problèmes connus |
|---|---|---|---|---|---|
| TVB_RES_NORM | INSPECTED | `reservoirs_srce_normandie_source.zip` | `reservoirs.gpkg` | 40 | Échelle d'emploi et sens métier des attributs à valider avec M2 |
| TVB_COR_BN | INSPECTED | `corridors_srce_basse_normandie_source.zip` | `corridors.gpkg` | 16 | Ne prouve pas un corridor fonctionnel actuel |
| BDTOPO_ROUTES | INSPECTED | `routes_orne_estuaire_bbox.geojson` | `routes.gpkg` | 1 924 | Extrait WFS borné, millésime global non fourni |
| OCSGE | INSPECTED | `OCS-GE_2-0__GPKG_LAMB93_D014_2023-01-01.7z` | `sols.gpkg`, `zones_construites.gpkg` | 3 358 / 83 | Ne décrit pas directement la sensibilité écologique |

### Couches R1–R4 (complémentaires) — intégrées

| Source | Statut | Fichiers bruts | Objets dans pilote | Problèmes connus |
|---|---|---|---|---|
| SIPAF (R1) | INSPECTED | `Tous_les_PAF.gpkg` | 0 | Inventaire non exhaustif, zéro dans pilote ≠ preuve d'absence |
| BDHAIE (R2) | INSPECTED | `haies_pilot.geojson` | 1 181 | V2 méthode différente de V1, vide ≠ preuve d'absence |
| CARTOFRICHES (R3) | INSPECTED | `friches-surfaces.gpkg` | 3 | Inventaire non exhaustif, champs incomplets |
| ZH_DREAL_NORM (R4) | INSPECTED | `zones_humides_pilot.gml` | 156 | Millésimes hétérogènes, ne prouve pas fonctionnement hydrologique |

### Couches indisponibles

| Source | Statut | Raison |
|---|---|---|
| PRAM_MARES (R4) | CANDIDAT | Extraction autorisée requise, droits de réutilisation non publiés |
| FRICHES_EPFN (R3) | CANDIDAT | Licence non spécifiée, aucune ressource téléchargeable |

## Vérification CRS

| Fichier | CRS attendu | CRS constaté | Méthode de vérification |
|---|---|---|---|
| `grille_pilote.gpkg` (grille_pilote) | EPSG:2154 | EPSG:2154 | gpkg_geometry_columns |
| `grille_pilote.gpkg` (hexagones_complets) | EPSG:2154 | EPSG:2154 | gpkg_geometry_columns |
| `reservoirs.gpkg` | EPSG:2154 | EPSG:2154 | Reprojection depuis source |
| `corridors.gpkg` | EPSG:2154 | EPSG:2154 | Reprojection depuis source |
| `routes.gpkg` | EPSG:2154 | EPSG:2154 | Reprojection depuis EPSG:4326 |
| `sols.gpkg` | EPSG:2154 | EPSG:2154 | Source native |
| `zones_construites.gpkg` | EPSG:2154 | EPSG:2154 | Source native |
| BD Haie extract | EPSG:2154 | EPSG:2154 | Reprojection depuis WFS EPSG:4326 |
| ZH DREAL extract | EPSG:2154 | EPSG:2154 | WFS native |

Tous les calculs de métrique (aires, longueurs) utilisent EPSG:2154 pour garantir des valeurs métriques cohérentes.

## Validation des géométries

### Contrôles effectués

- Invalidité : géométries invalides détectées et réparées avec `shapely.make_valid`
- Vide : géométries vides filtrées et exclues
- Auto-intersection : traitée par `make_valid`
- Intersection pilote : toutes les mailles intersectent le pilote

### Résultats

| Source | Géométries totales | Invalides avant réparation | Invalides après réparation | Exclues (vides) |
|---|---|---|---|---|
| Réservoirs | 40 dans pilote | N/A | 0 | 0 |
| Corridors | 16 dans pilote | N/A | 0 | 0 |
| Routes | 1 924 dans pilote | N/A | 0 | 0 |
| Sols OCS | 3 358 dans pilote | N/A | 0 | 0 |
| Zones construites | 83 dans pilote | N/A | 0 | 0 |
| Haies | 1 181 dans pilote | N/A | 0 | 0 |
| Cartofriches | 3 dans pilote | N/A | 0 | 0 |
| Zones humides | 156 dans pilote | N/A | 0 | 0 |

## Contrôle des identifiants uniques

| Table | Colonnes identifiantes | Unicité vérifiée | Doublons détectés |
|---|---|---|---|
| `grille_pilote` | `maille_id` | ✅ 43 uniques | 0 |
| `sub_indicateurs.csv` | `maille_id` | ✅ 43 uniques | 0 |
| `sub_indicateurs_ocs.csv` | `maille_id`, `ocs_code_cs` | ✅ 227 uniques | 0 |
| `reservoirs.gpkg` | `objet_id` | ✅ | 0 |
| `corridors.gpkg` | `objet_id` | ✅ | 0 |
| `routes.gpkg` | `route_id` | ✅ | 0 |
| `sols.gpkg` | `sol_id` | ✅ | 0 |

## Valeurs manquantes et conventions

### Convention NULL vs zéro

- **NULL** : source indisponible ou extraction non autorisée (ex: `pram_pond_count`, `epfn_site_count`)
- **0** : source disponible mais aucun objet intersectant la maille dans l'inventaire couvrant le pilote
- Une valeur zéro ne prouve pas l'absence réelle d'un phénomène lorsque l'inventaire est non exhaustif

### Champs avec NULL explicite

| Champ | Raison |
|---|---|
| `pram_pond_count` | Source PRAM indisponible (extraction autorisée requise) |
| `epfn_site_count` | Source EPFN indisponible (licence et ressource non confirmées) |

## Dates de référence et limitations

| Source | Année/millésime | Limitation |
|---|---|---|
| TVB (réservoirs, corridors) | 2014 | Ancienneté, cohérence entre anciens SRCE à contrôler |
| BD TOPO routes | Variable par objet | Millésime global non fourni par l'extrait WFS |
| OCS GE | 2023 | Départemental D014, ne couvre pas toute la Normandie |
| BD Haie | 2020-2022 (images), produit 2024 | V2 méthode différente de V1 |
| SIPAF | Continu, par objet | Inventaire non exhaustif |
| Cartofriches | 2026-10-07 | Inventaire non exhaustif |
| ZH DREAL | Hétérogène | Mélange d'inventaires différents |

## Opérations de traitement et nettoyage

### Pipeline commun (sources principales)

1. Chargement depuis fichier brut (ZIP, GeoJSON, 7z, GPKG, GML)
2. Vérification CRS et reprojection vers EPSG:2154 si nécessaire
3. Détection et réparation des géométries invalides (`make_valid`)
4. Filtrage des géométries vides
5. Extraction spatiale sur bbox pilote ou géométrie pilote
6. Renommage et harmonisation des champs selon dictionnaire M1
7. Export en GeoPackage (couche unique)

### Pipeline complémentaire (R1–R4)

1. Téléchargement national ou WFS borné
2. Reprojection vers EPSG:2154
3. Réparation géométries invalides
4. Filtrage spatial sur pilote
5. Utilisation directe dans calculs de mesures (pas d'export séparé)

### Règles de fusion des recouvrements

Pour chaque mesure et chaque source, les intersections géométriques avec une maille sont fusionnées par union unaire avant calcul. Un recouvrement interne n'est donc compté qu'une fois. Ceci évite les doubles comptages d'aires ou longueurs.

## Provenance des données

Toutes les sources sont tracées dans `docs/inventaire_sources.csv` et `data/processed/sources.json`. Les empreintes SHA-256 des fichiers bruts sont consignées et vérifiées avant et après traitement pour garantir l'intégrité.

## Incertitudes connues

### Incertitudes techniques

- Bbox pilote rectangulaire : le fragment minimal de 11,7 m² résulte d'un contact réel avec la bordure
- Précision WGS84 → EPSG:2154 : transformation standard, erreur négligeable à l'échelle km²
- Géométries réparées : `make_valid` peut modifier légèrement la géométrie originale

### Incertitudes métier (validation scientifique requise)

- Échelle des sources TVB : la résolution du SRCE 2014 peut ne pas être adaptée à tous les usages écologiques
- Fonctionnalité des corridors : la vectorisation SRCE ne prouve pas un corridor fonctionnel actuel
- Exhaustivité des inventaires : SIPAF, Cartofriches, BD Haie sont non exhaustifs ; un vide ne prouve pas une absence
- Hétérogénéité des millésimes : les zones humides DREAL mélangent des inventaires de dates différentes
- Sensibilité écologique : OCS GE décrit l'occupation du sol, pas la sensibilité écologique

## Licences et contraintes de redistribution

| Source | Licence | Redistribution autorisée | Attribution requise |
|---|---|---|---|
| TVB (réservoirs, corridors) | Licence Ouverte 2.0 | ✅ Oui | ✅ Oui |
| BD TOPO routes | Licence Ouverte 2.0 | ✅ Oui | ✅ Oui |
| OCS GE | Licence Ouverte 2.0 | ✅ Oui | ✅ Oui |
| BD Haie | Licence Ouverte 2.0 | ✅ Oui | ✅ Oui |
| SIPAF | Licence Ouverte 2.0 (données diffusables) | ✅ Oui (données non sensibles) | ✅ Oui |
| Cartofriches | Licence Ouverte 2.0 | ✅ Oui | ✅ Oui |
| ZH DREAL | Licence Ouverte 2.0 | ✅ Oui | ✅ Oui |
| PRAM | Non spécifiée | ❌ Non connue | ? |
| EPFN | Non spécifiée | ❌ Non connue | ? |

Tous les fichiers de sortie générés par M1 respectent les licences des sources originales. Les données sensibles (taxonomiques SIPAF) ne sont pas diffusées en détail.

## Dépendances de validation scientifique

M2 doit valider :

1. **Pertinence de la grille** : résolution 1 km², orientation, ancrage à l'origine (0,0)
2. **Compatibilité échelle-source** : la résolution SRCE 2014 est-elle adaptée à l'analyse ?
3. **Nomenclatures** : sens métier des attributs TVB, classification des corridors
4. **Règles de détection** : définition scientifique des événements de conflit
5. **Sensibilité à la résolution** : test avec une autre taille de maille ou un décalage
6. **Qualification des signaux** : interprétation des mesures en termes de pression écologique
7. **Règles R1–R4** : définition scientifique des conditions d'affichage des actions

M1 ne produit aucune conclusion scientifique, priorité, conflit confirmé ou recommandation de restauration.

## Tests automatisés

### Tests exécutés et réussis

- `test_prepare_m1.py` : validation du pipeline de prétraitement
- `test_hex_grid.py` : validation de la génération de grille (reproductibilité, CRS, IDs, géométries, aires, couverture pilote)
- `test_m1_measurements.py` : validation des mesures élémentaires (sources authentiques, IDs grille, EPSG:2154, valeurs non négatives, règles de recouvrement, NULL vs zéro, provenance, déterminisme, intégrité sources brutes)

### Résultat

```
PASS: genuine sources, grid IDs, EPSG:2154 metrics, nonnegative values, overlap rules, NULL-vs-zero, provenance, determinism, raw hashes
```

## Intégrité des sources brutes

Les empreintes SHA-256 des fichiers sources sont vérifiées avant et après chaque exécution. Aucune modification n'a été détectée pendant le traitement.

## Organisation des fichiers

```
migration-reconnect-m1/
├── data/
│   ├── raw/                    # Sources brutes, exclues de Git par .gitignore
│   │   ├── tvb_srce_normandie/
│   │   ├── bdtopo_routes/
│   │   ├── ocsge_d014_2023/
│   │   ├── bdhaie_pilot/
│   │   ├── sipaf/
│   │   ├── cartofriches/
│   │   └── zones_humides/
│   └── processed/              # Données harmonisées, mesures et métadonnées
│       ├── reservoirs.gpkg
│       ├── corridors.gpkg
│       ├── routes.gpkg
│       ├── sols.gpkg
│       ├── zones_construites.gpkg
│       ├── grille_pilote.gpkg
│       ├── sub_indicateurs.csv
│       ├── sub_indicateurs_ocs.csv
│       ├── m1_measurements_report.json
│       ├── m1_grid_report.json
│       └── sources.json
├── analysis/
│   ├── prepare_m1.py
│   ├── test_prepare_m1.py
│   ├── generate_hex_grid.py
│   ├── test_hex_grid.py
│   ├── calculate_m1_measurements.py
│   └── test_m1_measurements.py
└── docs/
    ├── inventaire_sources.csv
    ├── M1_GRILLE_HEXAGONALE.md
    ├── M1_PIPELINE_SIG.md
    ├── M1_SOUS_INDICATEURS.md
    ├── M1_ETAPE_2_RAPPORT.md
    ├── M1_ETAPE_3_RAPPORT.md
    ├── M1_ETAPE_4_RAPPORT.md
    ├── M1_ETAPE_5_RAPPORT.md
    └── quality_report.md
```

## Conclusion technique

Le package M1 est techniquement complet et reproductible. Toutes les couches prioritaires sont intégrées avec validation CRS, géométrie et identifiants. Les mesures élémentaires sont calculées de manière déterministe en EPSG:2154. La documentation des sources, licences et limitations est exhaustive. Les tests automatisés confirment l'intégrité du pipeline.

Le passage à M2 requiert maintenant une validation scientifique de la grille, des nomenclatures et des règles de détection. Aucune conclusion écologique, priorité ou recommandation de restauration n'a été produite par M1.
