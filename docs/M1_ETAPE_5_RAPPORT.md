# M1 — Rapport de l'étape 5

Date : 3 novembre 2026  
Statut : **mesures élémentaires produites, interprétation M2 requise**

## Livrables et couverture

`sub_indicateurs.csv` contient **43 lignes**, une par maille candidate. `sub_indicateurs_ocs.csv` contient **227 lignes** maille/catégorie. Les 43 mailles ont une couverture OCS GE complète dans l'emprise étudiée.

Sources réellement mesurées dans le pilote : 1 924 routes, 40 réservoirs, 16 corridors polygonaux, 3 358 objets OCS, 83 zones construites, 1 181 haies, 3 polygones Cartofriches et 165 zones humides candidates avant découpe final. L'export SIPAF courant contient zéro objet intersectant le pilote ; son inventaire étant non exhaustif, ce zéro n'est pas une preuve d'absence d'ouvrage.

Ordres de grandeur géométriques, sans interprétation :

| Mesure agrégée sur le pilote | Valeur |
|---|---:|
| Longueur routière fusionnée | `218 793,5 m` |
| Aire de réservoirs fusionnée | `3 502 366 m²` |
| Aire de corridors fusionnée | `10 860 690 m²` |
| Aire de zones construites | `5 265 376 m²` |
| Longueur de haies fusionnée | `108 859,6 m` |
| Aire Cartofriches | `7 344,6 m²` |

## Disponibilité R1–R4

- **R1 — SIPAF :** export officiel inspecté, zéro intersection pilote ; donnée non exhaustive, aucune conclusion d'absence.
- **R2 — BD Haie :** extrait WFS officiel borné, 1 181 lignes mesurables.
- **R3 — Cartofriches :** GeoPackage officiel, trois sites/polygones intersectants ; EPFN reste bloqué par la licence et l'absence de ressource confirmée.
- **R4 — zones humides/mares :** extrait WFS DREAL borné disponible en GML et mesuré ; inventaires et millésimes hétérogènes. PRAM exige une extraction autorisée et reste `NULL`.

## Validation

Deux exécutions ont produit des CSV identiques. Les tests confirment : clés de grille exhaustives et uniques, calculs EPSG:2154, valeurs disponibles non négatives, aires OCS et construites inférieures ou égales aux aires de maille, somme des catégories cohérente avec la couverture OCS, fusion des recouvrements, provenance, distinction `NULL`/zéro et empreintes brutes inchangées.

Résultat : `PASS: genuine sources, grid IDs, EPSG:2154 metrics, nonnegative values, overlap rules, NULL-vs-zero, provenance, determinism, raw hashes`.

## Passage à l'étape 6

M2 doit valider la grille, les nomenclatures, l'usage des comptes et les limites d'exhaustivité avant toute qualification scientifique. Restent à résoudre : accès R4, clarification EPFN, validation de l'échelle SRCE et définition scientifique des événements. Aucun conflit, score, priorité ou conseil de restauration n'a été produit.
