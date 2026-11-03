# M1 — Rapport de l'étape 2

Date : 3 novembre 2026

## Recommandation de pilote

M1 recommande provisoirement un secteur compact de l'estuaire de l'Orne, initialement échantillonné par le bbox WGS84 `[-0.28, 49.20, -0.22, 49.26]`. Le choix est un **GO technique M1**, sous réserve de validation M2/M5. Il n'est pas présenté comme une validation scientifique.

## Vérification géographique locale

Le bbox WGS84 a été transformé en Lambert-93 avec les paramètres EPSG:2154/RGF93 : `[460989.257, 6904815.661, 465631.045, 6911663.951]`. Les comptes ci-dessous résultent de tests d'intersection sur les géométries, après présélection par emprise ou index R-tree ; ils ne sont pas de simples comptes de bounding boxes.

| Couche réelle | Compte total du fichier | Candidats par emprise/index | Intersections géométriques pilote |
|---|---:|---:|---:|
| SRCE réservoirs | 20 404 | non conservé séparément | **40** |
| SRCE corridors Basse-Normandie | 14 534 | non conservé séparément | **17** |
| BD TOPO tronçons de route, extrait WFS | 1 926 | 1 926 | **1 924** |
| OCS GE `OCCUPATION_SOL` | 417 689 | 3 684 | **3 683** |
| OCS GE `ZONE_CONSTRUITE` | 31 340 | 100 | **99** |

Les écarts OCS GE entre candidats R-tree et intersections finales, ainsi que les deux routes hors intersection géométrique, confirment que le contrôle ne s'est pas limité aux enveloppes. Aucune couche n'a une intersection vide. Le secteur possède donc une couverture P0 technique suffisante pour poursuivre, sans préjuger de sa pertinence scientifique.

## Données P0 acquises et inspectées

### TVB — réservoirs SRCE Normandie

- Producteur : DREAL Normandie ; Licence Ouverte 2.0 ; référence scientifique 2014.
- Source réelle : `https://www.data.gouv.fr/api/1/datasets/r/c6e90e56-421d-45b3-9457-1c9a19962633`.
- Archive : 27 080 588 octets ; SHA-256 `12BBABAB26A594363B8F8DCB111AC43745E5829D4DCAEC33F5B475F5127A6E7C`.
- Inspection : Shapefile complet, polygones (type 5), EPSG:2154 confirmé par le PRJ, 20 404 enregistrements, emprise Lambert-93 `341381.45,6795383.00,612532.01,6997213.40`.
- Champs : `ID_RESV`, `ID_SRCE`, `NOM_RESV`, informations de milieux, délimitation et relations interrégionales/internationales.
- Couverture pilote : 40 intersections géométriques sur 20 404 objets régionaux.
- Limite : couche ancienne et régionale ; le statut de réservoir 2014 ne démontre pas un état écologique actuel.

### TVB — corridors SRCE Basse-Normandie

- Producteur : DREAL Normandie ; Licence Ouverte 2.0 ; référence scientifique 2014.
- Source réelle : `https://www.data.gouv.fr/api/1/datasets/r/e9c69c04-02bd-459b-9821-3ffe70360aae`.
- Archive : 19 757 409 octets ; SHA-256 `9F8AB6B025C09163F77EE567E83DF946B68153C463AD26A0D39DDAD84D994AFB`.
- Inspection : Shapefile complet, polygones (type 5), EPSG:2154, 14 534 objets, emprise `343045.40,6778729.75,560540.36,6969750.49`.
- Champs : `ID_CORR`, `ID_SRCE`, `CLASS_CORR`, informations de milieux, délimitation, symbologie et `surf_ha`.
- Couverture pilote : 17 intersections géométriques.
- Limite : vectorisation des matrices verte et bleue du SRCE 2014 ; échelle, classe et fonctionnalité écologique actuelle doivent être validées par M2.

### Routes — BD TOPO V3

- Producteur : IGN ; Licence Ouverte 2.0.
- Source réelle : requête WFS bornée consignée dans `data/raw/README.md`.
- Fichier : GeoJSON, 5 739 817 octets ; SHA-256 `133992B47A34FF4C840FB114B6A21F0EED2D331C55F089B6A45532B8E4A3ADA2`.
- Inspection : FeatureCollection lisible, 1 926 LineString, EPSG:4326 déclaré, aucune géométrie nulle, aucun doublon de `cleabs`.
- Couverture pilote : 1 924 intersections géométriques. Deux objets renvoyés par le filtre WFS n'intersectent pas réellement le rectangle selon le contrôle local.
- Champs utiles : `cleabs`, `nature`, `importance`, état, dates, précision, nombre de voies, largeur, circulation, accès, restrictions, communes et informations d'ouvrages.
- Limite : extrait WFS et non archive millésimée ; dates/actualité varient par objet.

### Sols — OCS GE 2.0 D014 2023

- Producteur : IGN/DGALN ; Licence Ouverte 2.0 ; millésime 2023.
- Source réelle : archive IGN Géoplateforme consignée dans `data/raw/README.md`.
- Archive : 138 290 682 octets ; SHA-256 `F1DA3C0C5978988C536C5ACB5C9173E519D1271BD88EE45CBCEA1F54991D7CAC`.
- Inspection : extraction réussie ; contrôles SQLite `integrity_check=ok` sur les deux GeoPackages.
- `OCCUPATION_SOL.gpkg` : EPSG:2154, 417 689 objets, 12 codes de couverture et 18 codes d'usage, aucun `id`, `code_cs`, `code_us` ou géométrie nul ; emprise `394752.21,6857034.20,513241.30,6937634.10`.
- `ZONE_CONSTRUITE.gpkg` : EPSG:2154, 31 340 objets ; emprise `394903.20,6857073.65,513034.09,6929309.16`.
- Couverture pilote : 3 683 objets `OCCUPATION_SOL` et 99 objets `ZONE_CONSTRUITE` intersectent réellement le rectangle.
- Champs : `id`, `code_cs`, `code_us`, `millesime`, `source`, `ossature`, `id_origine`, `code_or`.
- Limite : 566,6 Mo décompressés pour l'occupation du sol ; le paquet brut reste local et ignoré par Git.

## Faisabilité R1–R4

- **R1 — Evidence available for further investigation.** Routes, corridors et réservoirs ont des intersections locales. Aucun conflit ni ouvrage existant n'a été déduit.
- **R2 — Potentially relevant but not yet verified.** BD Haie V2 est accessible et OCS GE fournit le contexte, mais aucun objet haie local n'est inspecté.
- **R3 — Insufficient data.** Cartofriches est accessible, sans objet local inspecté ; l'EPFN reste bloqué par l'absence de licence/ressource confirmée.
- **R4 — Insufficient data.** Les sources DREAL/PRAM sont identifiées, sans objet mare ou zone humide inspecté dans le bbox.

Une absence de donnée inspectée n'est pas interprétée comme une absence écologique.

## Blocages restants

- PRAM : demande d'extraction et autorisation de réutilisation nécessaires.
- EPFN : licence absente et ressource directe non confirmée.
- M2 doit valider l'échelle et le sens des objets SRCE, l'emprise finale, les champs requis et la capacité du secteur à fournir quatre cas honnêtes.

## Préparation à l'étape 3

Les trois familles P0 disposent de fichiers réels lisibles et d'une couverture pilote non vide. Les transformations de bbox et les intersections ont été exécutées en lecture seule sur les géométries sources ; les GeoPackages ont été présélectionnés par leurs R-tree. Aucun fichier brut n'a été modifié. Après validation M2/M5, les données sont techniquement prêtes pour une harmonisation contrôlée en Step 3. Aucun découpage persistant, nettoyage, grille, conflit ou priorité n'a été produit.
