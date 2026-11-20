# Territoires

`communes_adminexpress_22.geojson` : Caen et 21 communes voisines, limites
exactes ADMIN EXPRESS COG (IGN, couche `ADMINEXPRESS-COG.LATEST:commune`,
Licence Ouverte 2.0), récupérées le 20/11/2026 sur data.geopf.fr en EPSG:2154
(SHA-256 `ce364f71b402f3d20eac4b23fdf85f76367f8a2b86c75cb62c6905c781d71d7b`).
Les 6 communes du lot historique y sont identiques à `communes_6_source.geojson`.

Utilisé par `python -m analysis.etendre_mailles perimetre22`. Le territoire est
découpé sur l'emprise d'acquisition `caen_et_nord_20261111_v1` (BD TOPO, zones
humides) : 4,4 % de Mondeville, 3,6 % d'Anisy et 1,2 % de Colleville-Montgomery
restent hors calcul.
