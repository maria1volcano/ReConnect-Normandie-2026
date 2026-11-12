# M1 — Rapport de l'étape 3

Date : 3 novembre 2026

## Résultat

Le pipeline SIG reproductible a été exécuté sur les données P0 réelles. Cinq GeoPackages séparés ont été produits en EPSG:2154 et découpés sur l'emprise pilote provisoire.

| Couche produite | Candidats lus | Objets après découpage | Géométries invalides en sortie | Identifiants dupliqués |
|---|---:|---:|---:|---:|
| Réservoirs SRCE | 40 | **40** | 0 | 0 |
| Corridors SRCE | 17 | **16** | 0 | 0 |
| Routes BD TOPO | 1 924 | **1 924** | 0 | 0 |
| OCS GE occupation du sol | 3 683 | **3 358** | 0 | 0 |
| OCS GE zones construites | 99 | **83** | 0 | 0 |

Aucune géométrie source ou découpée n'était invalide : aucun appel réparateur à `make_valid` n'a donc été nécessaire. Aucun objet vide ni objet de dimension inattendue n'a été conservé.

## Correction des comptes de l'étape 2

Les comptes robustes de cette étape remplacent les estimations locales de l'étape 2 pour les corridors et l'OCS GE. Le contrôle léger précédent annonçait 17 corridors, 3 683 occupations du sol et 99 zones construites. Le découpage GeoPandas/Shapely complet confirme que ces valeurs étaient des candidats ou des résultats d'un test géométrique approximatif : les comptes effectivement persistés sont respectivement 16, 3 358 et 83. Les comptes des réservoirs et des routes sont inchangés.

Cette correction ne change pas la conclusion technique : les cinq couches ont une couverture non vide. Elle évite toutefois d'utiliser les anciens comptes comme résultats d'analyse.

## Identifiants et attributs

Les identifiants métier des réservoirs, routes et couches OCS GE sont conservés. Pour les corridors, `ID_CORR` contient un libellé répété (« corridor bleu ») et ne peut garantir l'unicité. Il est conservé comme `libelle_source`; `ID_SRCE` est conservé comme `objet_source_id`; un `objet_id` déterministe est construit à partir de la géométrie source normalisée et des attributs. Les cinq identifiants contrôlés sont non nuls et uniques.

Les valeurs absentes restent `NULL` et ne sont pas assimilées à zéro.

## Contrôles exécutés

Le test de bout en bout a :

- exécuté deux fois le pipeline sur les données réelles ;
- comparé les empreintes sémantiques des cinq couches entre les deux exécutions ;
- rouvert chaque GeoPackage et vérifié son compte, son CRS EPSG:2154, la validité de ses géométries et l'unicité de ses identifiants ;
- recalculé les SHA-256 des quatre sources brutes.

Résultat : `PASS: real-data pipeline, reopen, CRS, validity, IDs, determinism, raw hashes`.

Les empreintes brutes restent : réservoirs `12BB…A6E7C`, corridors `9F8A…94AFB`, routes `1339…3ADA2`, OCS GE `F1DA…D7CAC`. Le détail complet et les empreintes sémantiques figurent dans `data/processed/m1_processing_report.json`.

## Limites et passage à M2

- L'emprise est un pilote technique provisoire ; M2/M5 doivent valider sa pertinence scientifique.
- M2 doit valider l'échelle, la signification et l'usage permis des objets SRCE 2014.
- L'extrait routier WFS n'a pas de millésime global homogène.
- Les preuves locales nécessaires à R2, R3 et R4 restent insuffisantes ou non acquises.
- Aucun manque de donnée n'est interprété comme une absence écologique.

Cette étape ne produit volontairement ni grille, ni sous-indicateur, ni score, ni classement. Les sorties sont des entrées techniques auditables pour la suite, pas une conclusion scientifique.
