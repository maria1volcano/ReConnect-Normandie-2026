# M1 — Document de remise à l'équipe (Handoff)

Date : 3 novembre 2026
Statut : **package technique complet, en attente de validation scientifique M2**

## Livrables M1 complets

### Données géographiques

| Fichier | Format | Description | Lignes/Objets | Usage |
|---|---|---|---|---|
| `data/processed/grille_pilote.gpkg` | GeoPackage | Grille hexagonale candidate (2 couches) | 43 mailles | M2: base d'analyse, M3: affichage |
| `data/processed/reservoirs.gpkg` | GeoPackage | Réservoirs SRCE harmonisés | 40 objets | M2: analyse écologique |
| `data/processed/corridors.gpkg` | GeoPackage | Corridors SRCE harmonisés | 16 objets | M2: analyse écologique |
| `data/processed/routes.gpkg` | GeoPackage | Routes BD TOPO harmonisées | 1 924 objets | M2: pressions routières |
| `data/processed/sols.gpkg` | GeoPackage | Occupation du sol OCS GE | 3 358 objets | M2: contexte d'occupation |
| `data/processed/zones_construites.gpkg` | GeoPackage | Zones construites OCS GE | 83 objets | M2: artificialisation |

### Mesures élémentaires

| Fichier | Format | Description | Lignes | Usage |
|---|---|---|---|---|
| `data/processed/sub_indicateurs.csv` | CSV UTF-8 | Une ligne par maille avec toutes les mesures | 43 | M2: entrée pour analyse scientifique |
| `data/processed/sub_indicateurs_ocs.csv` | CSV UTF-8 | Occupation du sol détaillée par maille et catégorie | 227 | M2: analyse fine de l'occupation |

### Métadonnées et rapports

| Fichier | Description |
|---|---|
| `data/processed/sources.json` | Métadonnées complètes des sources (producteur, URL, licence, CRS, champs, restrictions) |
| `data/processed/m1_grid_report.json` | Rapport de génération de grille (paramètres, couverture, empreintes) |
| `data/processed/m1_measurements_report.json` | Rapport de calcul des mesures (comptes, règles, SHA-256) |
| `docs/inventaire_sources.csv` | Inventaire détaillé des sources avec statut d'acquisition |
| `docs/quality_report.md` | Rapport de qualité technique (CRS, géométries, identifiants, limitations) |
| `docs/M1_GRILLE_HEXAGONALE.md` | Documentation de la grille candidate |
| `docs/M1_SOUS_INDICATEURS.md` | Documentation des mesures élémentaires |
| `docs/M1_PIPELINE_SIG.md` | Documentation du pipeline de prétraitement |
| `docs/M1_ETAPE_2_RAPPORT.md` | Rapport Step 2 (acquisition des données) |
| `docs/M1_ETAPE_3_RAPPORT.md` | Rapport Step 3 (prétraitement) |
| `docs/M1_ETAPE_4_RAPPORT.md` | Rapport Step 4 (génération de grille) |
| `docs/M1_ETAPE_5_RAPPORT.md` | Rapport Step 5 (calcul des mesures) |

### Scripts de reproduction

| Script | Description |
|---|---|
| `analysis/prepare_m1.py` | Pipeline de prétraitement SIG (Step 3) |
| `analysis/test_prepare_m1.py` | Tests du pipeline de prétraitement |
| `analysis/generate_hex_grid.py` | Génération de la grille hexagonale (Step 4) |
| `analysis/test_hex_grid.py` | Tests de génération de grille |
| `analysis/calculate_m1_measurements.py` | Calcul des mesures élémentaires (Step 5) |
| `analysis/test_m1_measurements.py` | Tests des mesures élémentaires |

## Schémas de données

### Grille (`grille_pilote.gpkg` - couche `grille_pilote`)

| Champ | Type | Description |
|---|---|---|
| `maille_id` | String | Identifiant unique de maille (ex: `NORM-G1K-FLAT-R+006425-C+000495`) |
| `grid_version` | String | Version de la grille (`M1-CAND-1KM2-FLAT-L93-O0-V1`) |
| `grid_row` | Integer | Indice de ligne (signé) |
| `grid_col` | Integer | Indice de colonne (signé) |
| `center_x` | Float | Coordonnée X du centre en EPSG:2154 |
| `center_y` | Float | Coordonnée Y du centre en EPSG:2154 |
| `full_area_m2` | Float | Aire de l'hexagone complet théorique (1 000 000 m²) |
| `clipped_area_m2` | Float | Aire réelle après découpe sur pilote |
| `area_m2` | Float | Aire effective de la maille (égale à clipped_area_m2) |
| `pilot_fraction` | Float | Fraction de l'hexagone contenue dans le pilote |
| `is_boundary` | Boolean | `true` si la maille est découpée par la bordure |
| `geometry` | Polygon | Géométrie de la maille en EPSG:2154 |

### Mesures par maille (`sub_indicateurs.csv`)

| Champ | Type | Unité | Description |
|---|---|---|---|
| `maille_id` | String | - | Identifiant de maille (clé étrangère vers grille) |
| `grid_version` | String | - | Version de la grille |
| `cell_area_m2` | Float | m² | Aire réelle de la maille |
| `is_boundary` | Boolean | - | `true` si maille de bordure |
| `road_length_m` | Float | m | Longueur totale des routes dans la maille (union des intersections) |
| `road_object_count` | Integer | - | Nombre de routes distinctes intersectant la maille |
| `reservoir_area_m2` | Float | m² | Aire totale des réservoirs dans la maille |
| `reservoir_object_count` | Integer | - | Nombre de réservoirs distincts |
| `corridor_area_m2` | Float | m² | Aire totale des corridors dans la maille |
| `corridor_object_count` | Integer | - | Nombre de corridors distincts |
| `ocs_covered_area_m2` | Float | m² | Aire couverte par OCS GE (union) |
| `ocs_coverage_fraction` | Float | - | Fraction de la maille couverte par OCS GE |
| `constructed_area_m2` | Float | m² | Aire des zones construites OCS GE |
| `hedge_length_m` | Float | m | Longueur totale des haies |
| `hedge_object_count` | Integer | - | Nombre de haies distinctes |
| `sipaf_record_count` | Integer | - | Nombre d'ouvrages SIPAF (0 dans le pilote) |
| `cartofriches_area_m2` | Float | m² | Aire des friches Cartofriches |
| `cartofriches_site_count` | Integer | - | Nombre de sites Cartofriches |
| `wetland_area_m2` | Float | m² | Aire des zones humides DREAL |
| `wetland_record_count` | Integer | - | Nombre d'enregistrements zones humides |
| `pram_pond_count` | Integer | - | NULL (source indisponible) |
| `epfn_site_count` | Integer | - | NULL (source indisponible) |
| `length_unit` | String | - | Unité de longueur (`m`) |
| `area_unit` | String | - | Unité d'aire (`m2`) |
| `measurement_crs` | String | - | CRS des mesures (`EPSG:2154`) |
| `*_coverage_status` | String | - | Statut de couverture par source (voir documentation) |
| `source_ids` | String | - | Identifiants des sources utilisées (séparés par `;`) |

### Occupation du sol détaillée (`sub_indicateurs_ocs.csv`)

| Champ | Type | Unité | Description |
|---|---|---|---|
| `maille_id` | String | - | Identifiant de maille |
| `grid_version` | String | - | Version de la grille |
| `ocs_code_cs` | String | - | Code de couverture OCS GE (conservé tel quel) |
| `ocs_area_m2` | Float | m² | Aire de cette catégorie dans la maille |
| `ocs_fraction_of_cell` | Float | - | Fraction de la maille occupée par cette catégorie |
| `area_unit` | String | - | Unité d'aire (`m2`) |
| `source_id` | String | - | Source (`OCSGE`) |
| `source_year` | String | - | Année de référence (`2023`) |

## Instructions d'exécution

### Prérequis

- Python 3.14+
- Dépendances : voir `analysis/requirements-m1.txt`
  - geopandas==1.2.0
  - pandas==3.1.0
  - pyogrio==0.13.0
  - pyproj==3.8.0
  - shapely==2.2.0

### Installation

```bash
cd migration-reconnect-m1
python -m venv .venv-m1
.venv-m1/Scripts/activate
pip install -r analysis/requirements-m1.txt
```

### Reconstruction complète (si sources brutes disponibles)

```bash
# Step 3: Prétraitement SIG
python analysis/prepare_m1.py
python analysis/test_prepare_m1.py

# Step 4: Génération de grille
python analysis/generate_hex_grid.py
python analysis/test_hex_grid.py

# Step 5: Calcul des mesures
python analysis/calculate_m1_measurements.py
python analysis/test_m1_measurements.py
```

### Reconstruction partielle (si données traitées déjà disponibles)

Si les fichiers dans `data/processed/` sont déjà présents, seule l'étape 5 peut être réexécutée :

```bash
python analysis/calculate_m1_measurements.py
python analysis/test_m1_measurements.py
```

## Contrat M1 → M2

### Ce que M2 reçoit

1. **Grille candidate** : 43 mailles hexagonales en EPSG:2154 avec identifiants stables
2. **Mesures élémentaires** : longueurs, aires, comptes pour chaque maille et chaque source
3. **Couches harmonisées** : réservoirs, corridors, routes, sols, zones construites en GeoPackage
4. **Métadonnées complètes** : provenance, licences, CRS, champs, limitations
5. **Règles de calcul** : union des intersections pour éviter les doubles comptages
6. **Convention NULL vs zéro** : distinction claire entre indisponible et absent

### Ce que M2 doit faire

1. **Valider la grille** : pertinence de la résolution 1 km², orientation, ancrage
2. **Valider les nomenclatures** : sens métier des attributs TVB, classification corridors
3. **Définir les règles de détection** : critères scientifiques des événements de conflit
4. **Qualifier les indicateurs** : interprétation écologique des mesures géométriques
5. **Définir les priorités** : table de règles de priorité d'examen
6. **Spécifier R1–R4** : conditions d'affichage des actions faune, haies, friches, mares
7. **Tester la sensibilité** : éventuel test avec une autre résolution de maille

### Ce que M2 ne doit pas attendre de M1

- Aucune conclusion scientifique (conflit confirmé, priorité, restauration)
- Aucune classification écologique des corridors ou réservoirs
- Aucune règle de priorité ou de recommandation d'action
- Aucune donnée qui n'existe pas dans les sources réelles

## Contrat M1 → M3

### Données d'affichage disponibles

M3 peut utiliser pour l'affichage :

1. **Grille pilote** : `data/processed/grille_pilote.gpkg` (couche `grille_pilote`)
   - Convertir en GeoJSON WGS84/CRS84 pour MapLibre
   - Champs à afficher : `maille_id`, `grid_version`, `is_boundary`
   - Ne pas afficher de priorité ou classement écologique (M2 uniquement)

2. **Sources géographiques** : couches harmonisées pour inspection visuelle
   - Réservoirs, corridors, routes, sols, zones construites
   - Convertir en GeoJSON WGS84/CRS84
   - Fournir attribution dans la légende

### GeoJSON pour M3 (optionnel, à générer par M4 ou M3)

Si M3 a besoin de GeoJSON WGS84, la conversion peut être faite avec :

```python
import geopandas as gpd

grid = gpd.read_file('data/processed/grille_pilote.gpkg', layer='grille_pilote')
grid_wgs84 = grid.to_crs('EPSG:4326')
grid_wgs84.to_file('data/public/grille_pilote_wgs84.geojson', driver='GeoJSON')
```

### Limites pour M3

- Ne pas modifier les données TEST existantes dans M3
- Ne pas afficher de priorité ou classement écologique sans validation M2
- Hors pilote : afficher clairement "analyse non réalisée"
- Respecter les licences des sources dans l'attribution

## Contrat M1 → M4

### Ingestion des données

M4 peut consommer :

1. **GeoPackages** : couches harmonisées via GeoPandas ou pyogrio
2. **CSV** : mesures élémentaires via pandas
3. **JSON** : métadonnées et rapports

### Exemple de chargement (Python)

```python
import geopandas as gpd
import pandas as pd
import json

# Grille
grid = gpd.read_file('data/processed/grille_pilote.gpkg', layer='grille_pilote')

# Mesures
measures = pd.read_csv('data/processed/sub_indicateurs.csv')
ocs_categories = pd.read_csv('data/processed/sub_indicateurs_ocs.csv')

# Couches sources
reservoirs = gpd.read_file('data/processed/reservoirs.gpkg', layer='reservoirs')
corridors = gpd.read_file('data/processed/corridors.gpkg', layer='corridors')
routes = gpd.read_file('data/processed/routes.gpkg', layer='routes')
soils = gpd.read_file('data/processed/sols.gpkg', layer='sols')
constructed = gpd.read_file('data/processed/zones_construites.gpkg', layer='zones_construites')

# Métadonnées
sources = json.load(open('data/processed/sources.json'))
grid_report = json.load(open('data/processed/m1_grid_report.json'))
measurements_report = json.load(open('data/processed/m1_measurements_report.json'))
```

### Schémas attendus par M4

M4 doit s'attendre aux schémas documentés dans ce handoff et dans `sources.json`. Toute modification de schéma après gel exige une revue M2/M4.

## Dépendances manquantes

### Sources indisponibles

- **PRAM_MARES** : extraction autorisée requise, droits de réutilisation non publiés
- **FRICHES_EPFN** : licence non spécifiée, aucune ressource téléchargeable

Ces sources sont marquées NULL dans les mesures. M2 peut décider de les acquérir ultérieurement si nécessaire.

### Validation scientifique requise

M2 doit valider avant toute interprétation :

- Échelle et pertinence de la grille (1 km²)
- Compatibilité échelle-source (SRCE 2014)
- Nomenclatures TVB (attributs et sens métier)
- Fonctionnalité des corridors (vectorisation ≠ fonctionnalité)
- Règles de détection des conflits
- Sensibilité à la résolution de maille

## Limitations connues

### Limitations techniques

- Bbox pilote rectangulaire : fragment minimal de 11,7 m²
- Avertissement CRLF dans Git : conversion automatique, sans impact fonctionnel
- Chemins relatifs : tous les scripts utilisent des chemins relatifs à la racine du projet

### Limitations métier

- Inventaires non exhaustifs : SIPAF, Cartofriches, BD Haie
- Millésimes hétérogènes : zones humides DREAL
- Ancienneté SRCE : 2014
- Résolution SRCE : peut ne pas être adaptée à tous les usages écologiques
- Occupation du sol : OCS GE décrit l'occupation, pas la sensibilité écologique

## Tests de validation

Tous les tests M1 passent :

- `test_prepare_m1.py` : ✅ pipeline de prétraitement
- `test_hex_grid.py` : ✅ génération de grille (reproductibilité, CRS, IDs, géométries, aires, couverture)
- `test_m1_measurements.py` : ✅ mesures élémentaires (sources authentiques, EPSG:2154, non-négatif, NULL vs zéro, déterminisme)

## Statut du pilote et de la grille

Le pilote (estuaire de l'Orne, bbox [-0.28, 49.20, -0.22, 49.26]) et la grille (version `M1-CAND-1KM2-FLAT-L93-O0-V1`) sont **provisoires**. M2 doit valider formellement la pertinence de cette emprise et de cette résolution avant toute généralisation à la Normandie entière.

## Prochaines étapes

1. **M2** : Valider scientifiquement la grille, les nomenclatures et définir les règles de détection
2. **M2** : Produire les analyses scientifiques (conflits, priorités, règles R1–R4)
3. **M3** : Intégrer les données géographiques validées pour l'affichage
4. **M4** : Préparer l'ingestion des données M2 et servir les APIs
5. **M5** : Utiliser les références sources et la documentation pour l'écrit

## Contact pour questions

Pour toute question technique sur les données M1 :
- Consulter `docs/quality_report.md` pour les détails techniques
- Consulter `docs/inventaire_sources.csv` pour les sources
- Consulter `data/processed/sources.json` pour les métadonnées

Pour toute question scientifique sur l'interprétation :
- S'adresser à M2 après validation scientifique

---

**Généré par M1 le 3 novembre 2026**
**Version du package : M1-V1**
**Git branch : feat/m1-donnees-sig-v61**
**Commit le plus récent : 66b8f57 (Step 5)**
