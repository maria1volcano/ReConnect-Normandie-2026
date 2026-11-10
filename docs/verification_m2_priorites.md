# Vérification locale M2 — QA amont et tables D/S — 3 novembre 2026

Branche contrôlée : `feat/diagnostics-ecologiques`. Version de décision : `m2-priorites.proposal-2`. Sources et attestations de tests exclusivement SYNTHÉTIQUES. Ce bilan démontre une conformité algorithmique aux conventions provisoires, pas leur validité écologique sur la Normandie.

## Dépôt et environnement

La branche et les modifications locales ont été inspectées avant intervention. Les nouvelles spécifications, le JSON des scénarios et les fichiers `.DS_Store` étaient déjà non suivis. Les fichiers M2 suivis étaient sans modification. Aucun changement de branche, remote, commit, push, fichier privé ou composant hors M2. Les contenus locaux préexistants ont été conservés.

Environnement isolé existant : `/private/tmp/reconnect-m2-venv`. Python 3.10, GeoPandas 1.1.4, Shapely 2.1.2, pandas 2.3.3, NumPy 2.2.6, pyproj 3.7.1, pyogrio 0.13.0, jsonschema 4.26.0, pytest 9.2.0. Aucune dépendance ajoutée.

## Fichiers créés et modifiés

Créés :

- `analysis/prepare_priority_inputs.py` : validation structurelle et interfaces QA positives/négatives, assertions, applicabilité et enjeux.
- `analysis/evaluate_priorities.py` : regroupement par famille, table D ordonnée, synthèse S et détails/liens.
- `tests/m2_priority_helpers.py` : complément des métadonnées des fixtures, uniquement synthétique et uniquement dans les tests.
- `tests/test_m2_priority_inputs.py` : 97 tests de validation/QA et chaîne synthétique.
- `tests/test_m2_priorities.py` : 628 tests, dont 38 scénarios et 576 combinaisons catégorielles.
- `docs/verification_m2_priorites.md` : ce compte rendu détaillé.

Modifiés : `docs/methode_m2.md` et `docs/notes_contrat_m3_m4_proposal2.md` (compléments de documentation, contenu préexistant conservé). Aucun test existant supprimé, neutralisé ou modifié.

## Interfaces effectivement disponibles

`validate_diagnostic_inputs(cell, pilot)` bloque les types/valeurs, identifiants, périmètres, versions, méthodes non autorisées, périodes incompatibles, références sans registre et incohérences de capacité. `PriorityInputError` expose `code`, `field`, `message`. Les codes requis, y compris `E_PROUVE_POSITIVE_SANS_SOURCE`, conservent leur orthographe contractuelle. Les erreurs ne deviennent jamais une priorité indéterminée de repli.

`derive_positive_evidence` lit les événements et les traces de qualification déjà existantes. Sans revue documentée visant exactement cet événement, la capacité reste false. Une intersection 2D ne devient pas un conflit potentiel. Une qualification potentielle exige trace contextuelle versionnée ou expertise documentée ; une confirmation exige preuve externe et localisation résolue. Les attestations ne sont pas authentifiées par le logiciel.

`derive_absence_evidence` réutilise `_coverage_geometry` et `_fully_covered`, recontrôle les métadonnées, l’empreinte du territoire et l’emprise H∩T, les sources identifiées, les catégories/sous-trames demandées et les périodes. La capacité négative peut être vraie avec un événement positif ; seule une analyse sans observation pertinente permet `absence_etablie=true`. Sans preuve suffisante : `non_evalue` / `absence_non_demontree`.

`detect_assertion_conflicts` compare assertions documentées sur propriété, objet et emprise identiques. Périodes identiques : comparables ; périodes disjointes : distinctes ; périodes recouvrantes différentes : comparabilité non établie. Un contrôle impossible reste null / `non_evalue`, et toute contradiction retenue exige sa référence de décision.

`derive_applicability` et `classify_ecological_stakes` sont des interfaces déclaratives. Sans décision versionnée et documentée : `inconnue` et `inconnu`. Aucun seuil ou mapping automatique à partir des réservoirs/corridors n’est fourni.

`normalize_diagnostics_by_family` préserve les diagnostics distincts, les sources et les phénomènes. Les familles manquantes restent vides et explicitement signalées, sans diagnostic fictif. `evaluate_priorities` est une fonction pure, sans lecture/écriture, export ou frontend.

## Règles effectivement codées

D0 non-applicabilité documentée ; D1 contradiction avant applicabilité inconnue ; D2 enjeu inconnu avant méthode absente ; D3 pression non évaluée/non concluante ; D4 preuve positive non validée ; D5 conflit étayé/enjeu fort ; D6 croisement/enjeu fort ; D7 pression/enjeu moyen ; D8 conflit/enjeu faible ; D9 absence validée ; D10a croisement/enjeu faible sans qualification. Première règle applicable uniquement. Aucun D10 résiduel ; tout trou admissible produit `E_TABLE_NON_TOTALE`.

S0 hors territoire ; S1 au moins un élevé ; S2 au moins un modéré et aucun élevé ; S3 au moins un faible et toutes les familles/diagnostics suffisamment évalués, les autres étant faibles ou hors champ documenté ; S4 sinon. Ni le nombre de diagnostics ni leurs liens ne produisent de promotion.

Le moteur renvoie les dix champs minimaux, les détails de chaque diagnostic, ses références, sources, phénomène et motifs QA. Les motifs des autres diagnostics ne disparaissent pas quand S1 ou S2 gagne. La complétude décisionnelle reste distincte de la couverture SIG.

## Couverture exhaustive de D

**576 combinaisons exactement : 432 admises, 144 rejetées, 0 admissible non couverte.** Aucun écart avec le contrôle préliminaire.

- 48 rejets `E_ABSENCE_INCOHERENTE` : 4 enjeux × 1 signal absence × 2 capacités positives × 1 capacité négative false × 3 applicabilités × 2 contradictions.
- 96 rejets `E_NON_APPLICABILITE_INCOHERENTE` : 4 enjeux × 3 signaux positifs × 2 capacités positives × 2 capacités négatives × 1 non-applicabilité × 2 contradictions.
- Ces deux ensembles sont disjoints : 576 − 48 − 96 = 432. Les autres références requises sont explicitement synthétiques.

La matrice terminale et les invariants de l’oracle de tests sont indépendants des fonctions et des prédicats de production. Les cas à plusieurs prédicats vrais vérifient la première règle sélectionnée, sans les confondre avec plusieurs décisions.

## Résultats détaillés des 38 scénarios

**38/38 conformes : 34 décisions et 4 erreurs exactes attendues.** Les résultats ci-dessous proviennent du moteur local et sont comparés champ par champ aux attentes inchangées. Les colonnes vides de listes sont des tableaux vides, pas des informations inconnues.

| Cas | Règles D | Motifs principaux par diagnostic | Règle S / priorité / couverture | Justificatifs / non évalués | Familles manquantes | Motifs de limites | Liens documentés |
| --- | --- | --- | --- | --- | --- | --- | --- |
| T01 | `{"A":"D5"}` | `{"A":"conflit_etaye_enjeu_fort"}` | `["S1","elevee","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T02 | `{"A":"D7"}` | `{"A":"pression_observee_enjeu_moyen"}` | `["S2","moderee","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T03 | `{"A":"D6"}` | `{"A":"croisement_non_qualifie_enjeu_fort"}` | `["S2","moderee","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T04 | `{"A":"D9"}` | `{"A":"absence_pression_validee"}` | `["S3","faible","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T05 | `{"A":"D9"}` | `{"A":"absence_pression_validee"}` | `["S3","faible","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T06 | `{"A":"D2"}` | `{"A":"enjeu_non_documente"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["enjeu_non_documente"]` | `[]` |
| T07 | `{"A":"D3"}` | `{"A":"pression_non_evaluee"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["pression_non_evaluee"]` | `[]` |
| T08 | `{"A":"D3"}` | `{"A":"preuve_non_concluante"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["preuve_non_concluante"]` | `[]` |
| T09 | `{"A":"D10a"}` | `{"A":"signal_non_qualifie"}` | `["S4","indeterminee","complete"]` | `[[],["A"]]` | `[]` | `["signal_non_qualifie"]` | `[]` |
| T10 | `{"A":"D8"}` | `{"A":"conflit_etaye_enjeu_faible"}` | `["S2","moderee","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T11 | `{"A":"D4"}` | `{"A":"preuve_positive_non_validee"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["preuve_positive_non_validee"]` | `[]` |
| T12 | `{"A":"D1"}` | `{"A":"donnees_contradictoires"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["donnees_contradictoires"]` | `[]` |
| T13 | `{"A":"D5","B_bocage":"D2"}` | `{"A":"conflit_etaye_enjeu_fort","B_bocage":"enjeu_non_documente"}` | `["S1","elevee","partielle"]` | `[["A"],["B_bocage"]]` | `[]` | `["enjeu_non_documente"]` | `[]` |
| T14 | `{"A":"D7","B_bocage":"D2"}` | `{"A":"pression_observee_enjeu_moyen","B_bocage":"enjeu_non_documente"}` | `["S2","moderee","partielle"]` | `[["A"],["B_bocage"]]` | `[]` | `["enjeu_non_documente"]` | `[]` |
| T15 | `{"A":"D7","B_bocage":"D7"}` | `{"A":"pression_observee_enjeu_moyen","B_bocage":"pression_observee_enjeu_moyen"}` | `["S2","moderee","complete"]` | `[["A","B_bocage"],[]]` | `[]` | `[]` | `[]` |
| T16 | `{"A":"D7","B_pression_route":"D7"}` | `{"A":"pression_observee_enjeu_moyen","B_pression_route":"pression_observee_enjeu_moyen"}` | `["S2","moderee","complete"]` | `[["A","B_pression_route"],[]]` | `[]` | `[]` | `[{"diagnostic_ids":["A","B_pression_route"],"raison":"source_partagee"}]` |
| T17 | `{"A":"D5","B_bocage":"D9"}` | `{"A":"conflit_etaye_enjeu_fort","B_bocage":"absence_pression_validee"}` | `["S1","elevee","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T18 | `{"A":"D5","B_bocage":"D1"}` | `{"A":"conflit_etaye_enjeu_fort","B_bocage":"donnees_contradictoires"}` | `["S1","elevee","partielle"]` | `[["A"],["B_bocage"]]` | `[]` | `["donnees_contradictoires"]` | `[]` |
| T19 | `{"A":"D9","B_bocage":"D2"}` | `{"A":"absence_pression_validee","B_bocage":"enjeu_non_documente"}` | `["S4","indeterminee","partielle"]` | `[[],["B_bocage"]]` | `[]` | `["enjeu_non_documente"]` | `[]` |
| T20 | `{"A":"D9","B_bocage":"D0"}` | `{"A":"absence_pression_validee","B_bocage":"non_applicabilite_documentee"}` | `["S3","faible","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T21 | `{"A":"D3"}` | `{"A":"preuve_non_concluante"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["precision_localisation_insuffisante","preuve_non_concluante"]` | `[]` |
| T22 | `{"A":"D0","B":"D0"}` | `{"A":"non_applicabilite_documentee","B":"non_applicabilite_documentee"}` | `["S4","indeterminee","complete"]` | `[[],[]]` | `[]` | `["aucune_famille_applicable"]` | `[]` |
| T23 | `{"A":"D9"}` | `{"A":"absence_pression_validee"}` | `["S4","indeterminee","partielle"]` | `[[],[]]` | `["bocage"]` | `["famille_attendue_absente"]` | `[]` |
| T24 | `{"A":"D5"}` | `{"A":"conflit_etaye_enjeu_fort"}` | `["S1","elevee","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T25 | `{"A":"D7","B":"D7"}` | `{"A":"pression_observee_enjeu_moyen","B":"pression_observee_enjeu_moyen"}` | `["S2","moderee","complete"]` | `[["A","B"],[]]` | `[]` | `[]` | `[]` |
| T26 | Erreur `E_ABSENCE_INCOHERENTE` conforme | Aucun résultat partiel | — | — | — | — | — |
| T27 | `{"A":"D1"}` | `{"A":"applicabilite_inconnue"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["applicabilite_inconnue"]` | `[]` |
| T28 | Erreur `E_REFERENCE_NON_APPLICABILITE` conforme | Aucun résultat partiel | — | — | — | — | — |
| T29 | `{"A":"D2"}` | `{"A":"methode_enjeu_absente"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["methode_enjeu_absente"]` | `[]` |
| T30 | `{}` | `{}` | `["S0",null,null]` | `[[],[]]` | `[]` | `["hors_territoire"]` | `[]` |
| T31 | Erreur `E_ID_DUPLIQUE` conforme | Aucun résultat partiel | — | — | — | — | — |
| T32 | Erreur `E_FAMILLE_HORS_PERIMETRE` conforme | Aucun résultat partiel | — | — | — | — | — |
| T33 | `{"A":"D9","B":"D3"}` | `{"A":"absence_pression_validee","B":"pression_non_evaluee"}` | `["S4","indeterminee","partielle"]` | `[[],["B"]]` | `[]` | `["pression_non_evaluee"]` | `[]` |
| T34 | `{"A":"D7","B":"D7"}` | `{"A":"pression_observee_enjeu_moyen","B":"pression_observee_enjeu_moyen"}` | `["S2","moderee","complete"]` | `[["A","B"],[]]` | `[]` | `[]` | `[{"diagnostic_ids":["A","B"],"raison":"phenomene_partage"}]` |
| T35 | `{"A":"D5","B":"D1"}` | `{"A":"conflit_etaye_enjeu_fort","B":"applicabilite_inconnue"}` | `["S1","elevee","partielle"]` | `[["A"],["B"]]` | `[]` | `["applicabilite_inconnue"]` | `[]` |
| T36 | `{"A":"D5"}` | `{"A":"conflit_etaye_enjeu_fort"}` | `["S1","elevee","complete"]` | `[["A"],[]]` | `[]` | `[]` | `[]` |
| T37 | `{"A":"D4"}` | `{"A":"preuve_positive_non_validee"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["preuve_positive_non_validee"]` | `[]` |
| T38 | `{"A":"D2"}` | `{"A":"enjeu_non_documente"}` | `["S4","indeterminee","partielle"]` | `[[],["A"]]` | `[]` | `["enjeu_non_documente"]` | `[]` |

## Propriétés et monotonie

Réussies : invariance à l’ordre des diagnostics/sources et conservation des entrées ; rejet des IDs dupliqués ; maintien d’un signal élevé avec famille inconnue ou contradiction indépendante ; impossibilité d’obtenir faible en retirant une famille ; aucune promotion par duplication ou deux modérés ; distinction indéterminée/complète et indéterminée/partielle ; S0 avec validation structurelle maintenue ; non-applicabilité documentée ; coexistence des capacités positive/négative ; refus d’absence non validée ; stabilité des motifs, sources et IDs entiers/chaînes ; protection contre NaN, Infinity, booléens pris pour IDs, valeurs inconnues et champs mal formés.

Les contre-exemples explicites échoueraient si D0/D1/D2/D3 ou S1/S2/S3 étaient inversées. Un test retire volontairement la table D pour vérifier que le trou de spécification lève `E_TABLE_NON_TOTALE` et ne devient pas un gris de repli.

**Monotonie conditionnelle : 6 transitions comparables de qualification** `conflit_potentiel → obstacle_confirme` et **8 transitions comparables d’enjeu** `moyen → fort` entre priorités connues. Toutes respectent la non-diminution à qualité/méthode/applicabilité égales. Les autres combinaisons sont rejetées ou indéterminées et ne sont pas ordonnées numériquement. Aucune échelle de gravité n’est présumée entre non-concluant et croisement.

## Pytest avant et après

Commande finale :

```sh
/private/tmp/reconnect-m2-venv/bin/python -m pytest -q tests/ --junitxml=/private/tmp/m2-priorites-pytest.xml
```

| Exécution | Réussis | Échecs | Erreurs | Ignorés | Avertissements |
| --- | --- | --- | --- | --- | --- |
| Avant modification | 223 | 0 | 0 | 0 | 38 |
| Finale complète | 948 | 0 | 0 | 0 | 38 |

Durée finale pytest : 11,56 s. Les 725 nouveaux tests se répartissent en 628 D/S et 97 QA amont. Les 223 tests antérieurs fonctionnent toujours. Les 38 avertissements sont les dépréciations pyproj/NumPy des transformations de tableaux de taille un (6 dans les conflits, 32 dans les contrats GeoJSON). Aucun avertissement n’a été masqué. Le JUnit temporaire reste hors dépôt.

## Compatibilité et divergences explicites

Empreintes avant/après identiques pour `docs/schema_mailles.json`, `docs/schema_conflits.json`, `analysis/export_m2_contract.py`, `docs/api_contract_m2_m4.md`, ainsi que la table D/S, le contrat QA, la vérification préliminaire et le JSON des scénarios. Les oracles ne sont pas modifiés. Aucun fichier dans `data/public/` n’est créé.

1. **Motifs limitants :** la phrase « union des motifs principaux » est plus large que les fixtures, qui excluent D5–D9 et D0 de `motifs_limites`. Le moteur conserve tous les motifs principaux dans leur index/détails et réserve les limites aux motifs réellement limitants, conformément aux 38 attentes. Cette clarification est documentée, sans changer de règle ni d’oracle.
2. **Métadonnées des fixtures :** elles ne contiennent pas le pilote complet, les registres, certains IDs/versions de maille ou la période optionnelle. Le complément est explicitement localisé dans un helper de tests SYNTHÉTIQUE. La validation de production exige ces champs et ne les fabrique jamais.
3. **Périodes des contradictions :** la comparabilité générique implémentée est volontairement limitée aux périodes identiques. Des périodes recouvrantes non identiques requièrent une future décision documentée spécifique, plutôt qu’une hypothèse écologique.
4. **IDs typés et JSON :** les index Python préservent 1 et "1" séparément ; JSON ne le permettrait pas par simple conversion de clés. Les tableaux détaillés gardent les IDs typés. Une future représentation publique doit être convenue avec M3/M4 ; aucun sérialiseur proposal-2 n’est activé.
5. **Qualification scientifique :** l’admissibilité d’une revue et de sa trace n’authentifie pas son auteur, son document ni sa pertinence scientifique. Les valeurs d’enjeu/applicabilité sont des décisions externes documentées, pas des classifications automatiques opérationnelles.

## Dépendances M1 et risques avant usage réel

M1 doit livrer couches officielles préparées, IDs stables, segmentation et dictionnaires de catégories/ouvrages/sous-trames, CRS et emprises fiables, précision et échelle, périodes, couvertures spatiales/thématiques validées, versions et droits. M2 doit approuver les mappings d’enjeu, les règles d’applicabilité, les critères contextuels et les traductions de familles vers D ; le code ne les invente pas.

Les principaux risques restent la mauvaise attribution de CRS, la précision des sources, les cas frontière, les déclarations de complétude inapplicables, les références périmées ou inadéquates, la comparabilité des périodes/emprises et une légende trop large par rapport au périmètre. Les tests synthétiques n’acceptent aucune donnée réelle ni méthode scientifique à leur place. Trois secteurs réels contrastés doivent encore être relus avec des éléments indépendants après livraison M1.

## Transmission à M3/M4

Confirmer la migration vers `m2-m4.proposal-2`, la conversion explicite catégorie interne → objet `{etat,valeur}`, les états non calculé/indéterminé/hors territoire, les détails typés et les champs publics autorisés. Afficher la portée des familles attendues et le badge de complétude décisionnelle séparément de la couverture SIG. Les sources, preuves privées et motifs techniques internes nécessitent une liste d’autorisation avant diffusion.

Conserver les deux GeoJSON distincts et leurs relations réciproques. `fiches_zones.json` reste scientifique M2 ; `catalogue_actions.json` reste M5. M2 spécifiera R1–R4 et M4 implémentera leur moteur ; cette itération ne crée ni moteur d’actions, ni classement d’efficacité, ni urgence d’intervention.
