# M1 — Sous-mesures géographiques transmises à M2

Date : 3 novembre 2026  
Statut : **mesures élémentaires, sans interprétation scientifique**

## Contrat de sortie

`analysis/calculate_m1_measurements.py` produit deux tables UTF-8 déterministes :

- `data/processed/sub_indicateurs.csv` : exactement une ligne par `maille_id` de la grille candidate ;
- `data/processed/sub_indicateurs_ocs.csv` : relation un-à-plusieurs entre maille et code de couverture OCS GE.

Les clés sont `maille_id` et `grid_version`. `measurement_crs=EPSG:2154`, `length_unit=m` et `area_unit=m2` rendent les unités explicites. `source_ids` référence les identifiants de `docs/inventaire_sources.csv`.

## Définitions

| Champ | Définition | Source / année |
|---|---|---|
| `road_length_m` | longueur de l'union des tronçons découpés dans la maille | `BDTOPO_ROUTES`, actualité par objet |
| `road_object_count` | nombre de `route_id` distincts intersectant la maille | `BDTOPO_ROUTES` |
| `reservoir_area_m2` | aire de l'union des réservoirs découpés | `TVB_RES_NORM`, 2014 |
| `reservoir_object_count` | nombre d'objets réservoir distincts | `TVB_RES_NORM`, 2014 |
| `corridor_area_m2` | aire de l'union des corridors polygonaux découpés | `TVB_COR_BN`, 2014 |
| `corridor_object_count` | nombre d'objets corridor distincts | `TVB_COR_BN`, 2014 |
| `ocs_covered_area_m2` | aire couverte par l'union OCS GE | `OCSGE`, 2023 |
| `ocs_coverage_fraction` | aire OCS divisée par l'aire réelle de la maille | `OCSGE`, 2023 |
| `constructed_area_m2` | aire de l'union des zones construites OCS GE | `OCSGE`, 2023 |
| `hedge_length_m` | longueur de l'union des haies découpées | `BDHAIE`, V2/BD TOPO courant |
| `hedge_object_count` | nombre de `cleabs` distincts | `BDHAIE` |
| `sipaf_record_count` | ouvrages SIPAF distincts intersectant la maille | `SIPAF`, export courant |
| `cartofriches_area_m2` | aire de l'union des polygones de friche | `CARTOFRICHES`, export 2026-10-07 |
| `cartofriches_site_count` | sites distincts intersectant la maille | `CARTOFRICHES` |
| `wetland_area_m2` | aire de l'union des zones humides inventoriées | `ZH_DREAL_NORM`, millésimes hétérogènes |
| `wetland_record_count` | objets zones humides distincts | `ZH_DREAL_NORM` |

La table OCS contient `ocs_code_cs`, `ocs_area_m2` et `ocs_fraction_of_cell`. Les codes sont conservés sans interprétation de nomenclature par M1.

## Règles géographiques

Chaque source est en EPSG:2154 avant calcul. Les géométries sont réellement intersectées avec la portion découpée de la maille. Pour chaque mesure et chaque source, les intersections sont fusionnées avant calcul : un recouvrement interne n'est compté qu'une fois. Les cellules de bord utilisent leur aire réelle, pas le million de mètres carrés théorique.

Une valeur `0` signifie qu'aucun objet du jeu couvrant le pilote n'intersecte la maille. Elle ne prouve pas l'absence réelle d'un phénomène lorsque l'inventaire est non exhaustif ou hétérogène. Une source indisponible produit `NULL`, jamais zéro : mares PRAM (extraction autorisée requise) et friches EPFN (licence/ressource non confirmées). Les champs `*_coverage_status` portent cette distinction.

## Exécution

```powershell
.\.venv-m1\Scripts\python.exe analysis\calculate_m1_measurements.py
.\.venv-m1\Scripts\python.exe analysis\test_m1_measurements.py
```

`data/processed/m1_measurements_report.json` consigne comptes, empreintes, conventions et disponibilité. Ces mesures décrivent des faits géométriques. Une route, un corridor ou une friche dans une maille n'est ni un conflit confirmé, ni une priorité, ni une recommandation.
