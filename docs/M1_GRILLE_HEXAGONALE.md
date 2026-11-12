# M1 — Grille hexagonale candidate

Date : 3 novembre 2026

Statut : **candidate, en attente de validation M2**

## Définition

`analysis/generate_hex_grid.py` construit une grille régulière sur l'emprise pilote provisoire documentée : bbox WGS84 `[-0.28, 49.20, -0.22, 49.26]`. La géométrie est transformée et tous les calculs sont réalisés en Lambert-93 (`EPSG:2154`). La grille ne couvre pas toute la Normandie.

La surface nominale cible est `1 000 000 m²`. Pour un hexagone régulier,

`A = (3 × sqrt(3) / 2) × s²`, donc `s = sqrt(2A / (3 × sqrt(3))) = 620,4032394014 m`.

Paramètres déterministes :

| Paramètre | Valeur |
|---|---|
| Version | `M1-CAND-1KM2-FLAT-L93-O0-V1` |
| Orientation | sommet plat (`flat_top`) |
| Origine Lambert-93 | `(0, 0) m` |
| Espacement horizontal | `930,6048591021 m` (`1,5 × s`) |
| Espacement vertical | `1 074,5699318235 m` (`sqrt(3) × s`) |
| Ordre | ligne croissante, puis colonne croissante |

Cette origine globale rend l'ancrage indépendant de l'ordre de parcours. Toute modification de surface, orientation, origine, CRS ou convention d'index impose une nouvelle `grid_version`.

## Identifiants et bordures

`maille_id` dérive uniquement des indices signés de ligne et colonne : `NORM-G1K-FLAT-R{row}-C{column}`. Il est attribué à l'hexagone régulier avant découpage et reste identique dans les deux couches.

`data/processed/grille_pilote.gpkg` contient :

- `grille_pilote` : géométrie réellement étudiée, découpée exactement sur le pilote ; `area_m2` est son aire réelle ;
- `hexagones_complets` : hexagones réguliers originaux, conservés pour l'audit de la grille.

Une maille est `is_boundary=true` si son hexagone complet n'est pas contenu dans le pilote. Un fragment de bordure n'est donc jamais présenté comme un hexagone entier.

## Schéma

Les deux couches partagent : `maille_id`, `grid_version`, `grid_row`, `grid_col`, `center_x`, `center_y`, `full_area_m2`, `clipped_area_m2`, `area_m2`, `pilot_fraction`, `is_boundary`, `geometry`. Dans la couche principale, `geometry`, `area_m2` et `clipped_area_m2` décrivent la portion étudiée. Dans la couche d'audit, la géométrie est l'hexagone complet ; les attributs d'aire découpée restent disponibles pour rapprochement.

## Exécution et contrôle

Depuis la racine du dépôt, avec l'environnement de l'étape 3 :

```powershell
.\.venv-m1\Scripts\python.exe analysis\generate_hex_grid.py
.\.venv-m1\Scripts\python.exe analysis\test_hex_grid.py
```

Le générateur écrit également `data/processed/m1_grid_report.json`, avec paramètres, comptes, couverture et empreintes sémantiques. Le test exécute deux générations et contrôle réouverture, CRS, IDs, validité, aires, intersection et couverture du pilote, reproductibilité et intégrité des sources brutes.

## Limites et validation M2

Le rectangle est une emprise technique, non une limite écologique ou administrative. La résolution nominale de 1 km² est celle demandée comme candidat initial par le PRD ; M2 doit encore vérifier sa compatibilité avec les échelles des sources, tester une autre résolution ou un décalage si nécessaire, et valider l'emprise. Aucun indicateur scientifique, conflit ou niveau de priorité n'est calculé ici.
