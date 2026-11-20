# Extension des mailles — Caen et 21 communes voisines (v2, 20/11/2026)

## Ce que la carte affiche maintenant

| | Lot historique (référence) | Grille unique affichée |
|---|---|---|
| Territoire | Caen + 5 communes | Caen + 21 communes |
| Secteurs (mailles) | 101 | **185** |
| Examens R1–R4 | 404 | 740 |
| Pistes « à étudier » | 165 | **284** (R1 106 · R2 102 · R3 52 · R4 24) |
| V1 rouge / V2 orange / V3 jaune / V4 gris | 27 / 33 / 9 / 32 | 37 / 69 / 14 / 65 |
| Événements route × corridor admis | 5 336 | 7 926 |

Communes ajoutées : Anisy, Biéville-Beuville, Cambes-en-Plaine,
Colleville-Montgomery, Cuverville, Démouville, Épron, Escoville, Giberville,
Hérouvillette, Mathieu, Mondeville, Périers-sur-le-Dan, Plumetot, Ranville,
Saint-Aubin-d'Arquenay.

## Pourquoi une grille unique (et plus « base + extension »)

La v1 du 19/11 ajoutait un second fichier à côté du lot historique. À la
limite entre les deux, un même hexagone était coupé en deux secteurs (le
fragment de l'extension était suffixé `-EXT`). Par ailleurs, les limites
communales simplifiées de l'extension ne collaient pas aux limites exactes de
la base : on voyait des lanières et des contours qui semblaient superposés.

La v2 corrige les deux causes :

1. **Limites exactes** : les 22 communes viennent d'ADMIN EXPRESS COG (IGN,
   `ADMINEXPRESS-COG.LATEST:commune`, Licence Ouverte 2.0), la même source que
   le lot historique. Les 6 communes d'origine sont identiques au mètre carré
   près à `communes_6_source.geojson`. Le fichier est versionné dans
   `analysis/territoires/communes_adminexpress_22.geojson`.
2. **Un seul jeu de données** : la grille est construite une seule fois sur
   les 22 communes. Chaque hexagone est un seul secteur, entier.

Contrôles automatiques : 0 m² de superposition, aucun identifiant `-EXT`, la
grille ne déborde pas des communes (`tests/test_grille_22communes.py`).

## Ce qui ne change pas

- `frontend/public/data/caen-6com/` reste **octet pour octet identique**. Il
  sert de référence de contrôle et de repli : si la grille 22 communes est
  absente ou non conforme, le site affiche le lot historique seul (jamais un
  mélange des deux).
- **62 des 101 secteurs historiques** (ceux qui ne touchent pas les nouvelles
  communes) sont strictement identiques dans la grille unique : surface,
  couleur, pistes. Les 39 autres étaient des fragments en bordure ; ils
  deviennent des hexagones entiers recalculés : 31 gardent leur couleur, 8
  changent parce que la partie ajoutée contient d'autres croisements ou
  réservoirs (gris → orange ×3, orange → rouge ×3, jaune → orange ×2).

## Méthode : la même chaîne, rejouée

`analysis/etendre_mailles.py` rejoue, pour n'importe quel territoire :

1. **M1** : même réseau d'hexagones (1 km², Lambert-93, flat-top, origine 0,0)
   et même harmonisation des couches que `preparer_caen_et_nord.py` ;
2. **M2** : les moteurs existants `run_enjeux` et `run_conflicts` ;
3. **Fiches** : table V1–V4, gris technique et pistes R1–R4 de
   `livrer_caen_et_nord.py` ;
4. **Export** : au format public minimisé de `export_public_release.py`.

Aucune règle, aucun seuil n'a été modifié.

### Contrôle de fidélité

Lancé sur les 6 communes d'origine, le script redonne le lot publié :
couleurs et règles 101/101, statuts des 404 examens, 5 336 événements admis,
tous identiques (`analysis/comparer_reference.py`, 0 écart critique). Seul
écart : ± 1 à 2 sites Cartofriches dans 6 mailles, dû à la reprojection de 6
polygones selon la version de PROJ/GEOS ; aucune couleur ni piste ne change.

## Limites

- Routes, haies, plans d'eau et zones humides n'ont été acquis que sur
  l'emprise du 11/11. La grille est découpée sur cette emprise pour qu'aucune
  maille ne soit calculée avec une source manquante : 4,4 % de Mondeville,
  3,6 % d'Anisy et 1,2 % de Colleville-Montgomery ne sont pas couverts.
- 4 secteurs font moins de 1 ha (fragments de bordure), comme dans le lot
  historique.
- Les mêmes limites scientifiques s'appliquent : couleurs = ordre de
  vérification documentaire, pas des priorités écologiques validées.

## Frontend

- `PUBLIC_DISPLAY_DATASET` (`src/integrations/publicDataPolicy.ts`) :
  dossier `data/caen-22com/`, empreintes SHA-256, effectifs attendus ;
- `publicJourneyAdapter.ts` charge ce jeu, et se replie sur le lot historique
  en cas d'erreur ;
- les pistes affichent « Piste calculée · justification non qualifiée ».

Tests : `npm run typecheck`, `npm run test:public-journey`,
`npm run test:catalogue`, `npm run build`, `npm run test:production-safety`,
`pytest tests/test_grille_22communes.py`.

## Reproduire

```bash
python -m analysis.etendre_mailles reference --out data/derived/reference_rejouee
python -m analysis.comparer_reference data/derived/reference_rejouee
python -m analysis.etendre_mailles perimetre22 --out frontend/public/data/caen-22com
```

Après un recalcul, reporter les empreintes de `manifest.json` dans
`PUBLIC_DISPLAY_DATASET`. Calcul : environ 1 min 30.

## Aller plus loin

Pour couvrir toute Caen la Mer ou le Calvados : acquérir routes, haies, plans
d'eau et zones humides sur une emprise plus large
(`acquerir_caen_et_nord.py`), ajouter les communes ADMIN EXPRESS dans
`analysis/territoires/` et une entrée dans `TERRITORIES`, puis relancer.
