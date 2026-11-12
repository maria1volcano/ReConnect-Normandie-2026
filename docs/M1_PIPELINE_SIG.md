# M1 — Pipeline SIG reproductible (étape 3)

Date : 3 novembre 2026

## Objet et périmètre

Ce pipeline prépare les cinq couches P0 réelles du pilote provisoire pour leur examen par M2. Il harmonise, reprojette et découpe les objets sources, sans produire de grille, d'indicateur, de score, de conflit écologique ni de priorisation.

L'emprise provisoire est le rectangle WGS84 `[-0.28, 49.20, -0.22, 49.26]`, soit `[460989.257242, 6904815.661232, 465631.045140, 6911663.950544]` en EPSG:2154. Sa validation scientifique reste à la charge de M2/M5.

## Environnement

Le pipeline a été validé sous Python 3.12 avec les versions épinglées dans `analysis/requirements-m1.txt` : GeoPandas 1.2.0, Pyogrio 0.13.0, PyProj 3.8.0, Shapely 2.2.0 et pandas 3.1.0.

Exemple PowerShell depuis la racine du dépôt :

```powershell
py -3.12 -m venv .venv-m1
.\.venv-m1\Scripts\python.exe -m pip install -r analysis\requirements-m1.txt
.\.venv-m1\Scripts\python.exe analysis\prepare_m1.py
.\.venv-m1\Scripts\python.exe analysis\test_prepare_m1.py
```

Les données brutes décrites dans `data/raw/README.md` doivent être présentes localement. Elles restent ignorées par Git.

## Entrées et traitement

`analysis/prepare_m1.py` localise les deux Shapefiles SRCE, l'extrait GeoJSON BD TOPO et les deux couches GeoPackage OCS GE. Il :

1. calcule les SHA-256 des quatre livrables sources avant traitement ;
2. lit uniquement les candidats de l'emprise lorsque le format et son index spatial le permettent ;
3. reprojette chaque couche en Lambert-93 (`EPSG:2154`) ;
4. applique `make_valid` uniquement aux géométries effectivement invalides ;
5. réalise un véritable découpage géométrique sur le rectangle pilote avec `geopandas.clip` ;
6. écarte explicitement les géométries vides ou de dimension inattendue et en consigne le nombre ;
7. harmonise les attributs, en conservant les identifiants source ;
8. écrit puis rouvre chaque GeoPackage, et produit un rapport JSON contenant comptes, validité, CRS et empreintes sémantiques ;
9. recalcule les SHA-256 des sources et échoue si elles ont changé.

Les valeurs absentes sont conservées comme `NULL` GeoPackage ; elles ne sont jamais remplacées par zéro. Le champ `ID_CORR` des corridors est un libellé répété et non un identifiant. Il est donc conservé dans `libelle_source`, tandis que `objet_id` est une empreinte déterministe de la géométrie source normalisée et de ses attributs. `objet_source_id` conserve `ID_SRCE`.

## Sorties

Les données sont séparées dans `data/processed/` :

| Fichier | Couche | Identifiant contrôlé |
|---|---|---|
| `reservoirs.gpkg` | `reservoirs` | `objet_id` |
| `corridors.gpkg` | `corridors` | `objet_id` |
| `routes.gpkg` | `routes` | `route_id` |
| `sols.gpkg` | `sols` | `sol_id` |
| `zones_construites.gpkg` | `zones_construites` | `zone_id` |

Les GeoPackages, volumineux et reproductibles, sont ignorés par Git. `m1_processing_report.json` est versionnable : il documente les résultats sans embarquer les géométries.

## Vérification

`analysis/test_prepare_m1.py` exécute deux fois le pipeline, compare les empreintes sémantiques, rouvre les cinq fichiers, puis vérifie : sortie non vide, compte attendu, EPSG:2154, géométries non nulles et valides, identifiants non nuls et uniques, et intégrité SHA-256 des sources brutes.

## Limites

Le pilote reste provisoire. Les objets SRCE datent de 2014 et leur échelle ou leur sens écologique n'est pas validé ici. L'extrait routier WFS ne constitue pas une archive globale millésimée. Les données locales nécessaires à R2–R4 restent incomplètes. Le pipeline prépare des preuves géographiques ; il ne conclut ni à la fonctionnalité écologique, ni à l'existence d'un conflit ou d'une opportunité.
