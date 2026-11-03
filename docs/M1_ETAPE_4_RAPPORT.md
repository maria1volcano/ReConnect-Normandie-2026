# M1 — Rapport de l'étape 4

Date : 3 novembre 2026

Statut : **grille candidate, en attente de validation M2**

## Résultats

La grille réelle du pilote provisoire a été générée en EPSG:2154 avec une surface nominale de `1 000 000 m²` par hexagone, un côté calculé de `620,4032394014 m` et la version `M1-CAND-1KM2-FLAT-L93-O0-V1`.

| Mesure | Résultat |
|---|---:|
| Mailles intersectant le pilote | **43** |
| Hexagones intérieurs complets | **15** |
| Mailles de bordure découpées | **28** |
| Aire du pilote | `29 171 588,4672 m²` |
| Somme des aires découpées | `29 171 588,4672 m²` |
| Aire minimale d'un fragment | `11,7282 m²` |
| Aire maximale | `1 000 000,0000 m²` |
| Défaut de couverture | `0,0 m²` |
| Débordement | `0,0 m²` |

Le GeoPackage `data/processed/grille_pilote.gpkg` conserve séparément la couche découpée `grille_pilote` et les géométries régulières `hexagones_complets`. Les identifiants restent identiques entre les deux représentations.

## Validation exécutée

Deux générations successives ont produit les mêmes identifiants, attributs et géométries selon leurs empreintes sémantiques. Le fichier a été rouvert et les contrôles suivants ont réussi :

- CRS EPSG:2154 pour les deux couches ;
- 43 `maille_id` non nuls et uniques, et `grid_version` présente ;
- géométries valides, non vides et intersectant toutes le pilote ;
- aire attributaire égale à l'aire géométrique dans la tolérance `0,0001 m²` ;
- hexagones complets à environ 1 km² et bordures correctement signalées ;
- union des cellules découpées couvrant exactement le pilote dans la tolérance ;
- empreintes des quatre sources brutes inchangées.

Résultat : `PASS: reopen, CRS, IDs, geometry, areas, pilot coverage, determinism, raw hashes`.

## Blocages restants

M2 doit valider la résolution, l'ancrage et l'emprise au regard des échelles des sources, puis conduire le test de sensibilité demandé par le PRD. Le fragment minimal très petit résulte d'un contact réel avec la bordure rectangulaire ; une règle scientifique éventuelle de regroupement ou de seuil relève de M2 et créerait une nouvelle version. Aucun sous-indicateur, conflit, score ou classement n'a été calculé.
