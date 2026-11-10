# M2 — Sélection Git finale contrôlée, 10 novembre 2026

**52 chemins proposés ; aucun ajout réel à l'index, commit ou push.** Le patch
`.gitignore` a été examiné et appliqué à l'identique. La sélection est prête à être
approuvée ; `git add --dry-run` annonce exactement les 52 chemins ci-dessous.

## État Git et conservation

Branche `feat/diagnostics-ecologiques`, HEAD
`9a5fe89193a394dc457b070cae5436e25d60f139`, inchangés. Au démarrage : quatre fichiers
suivis modifiés et 234 fichiers non suivis. Après exclusions : **cinq fichiers
suivis modifiés et 47 fichiers non suivis visibles**, tous présents dans la sélection.
Le diff suivi comprend désormais 466 insertions et 29 suppressions : 19 lignes
ajoutées au `.gitignore`, en plus du travail antérieur inchangé.

Les quatre modifications préexistantes sont : `analysis/aggregate_conflicts.py`,
`analysis/detect_conflicts.py`, `analysis/validate_inputs.py` et `docs/methode_m2.md`.
Leur contenu est préservé. Dans cette intervention, seuls `.gitignore` et ce document
sont modifiés ; les calculs, données M1, résultats validés, règles et contrats
restent inchangés. Aucun fichier local supprimé.

Les commandes de lecture demandées ont été exécutées : branche, `git status`,
`git diff --stat`, diff suivi et liste complète des fichiers non suivis.
Les fichiers ont été examinés par familles, contenu textuel, dépendances,
taille et motifs connus d'identifiants sensibles ; pas de test scientifique relancé.

## Classement retenu

| Catégorie | Nombre proposé | Contenu et justification |
| --- | ---: | --- |
| Infrastructure Git | 1 | `.gitignore`, conventions Python conservées, exclusions locales ajoutées |
| Code M2 canonique | 6 | Trois modules modifiés de validation/détection/agrégation ; trois modules QA/triage/export interne encore non suivis |
| Tests Python et helper | 8 | Sept modules de régression et `m2_priority_helpers.py` ; dépendances locales conservées |
| Fixtures | 6 | Générateur M1 figé, grille GeoJSON et provenance ; cas D/S, actions et frontière réelle |
| Documentation, schémas, configurations et annexes méthodologiques | 31 | Méthodes, QA, D/S, R1–R4 proposés, preuves d'audit légères, configs et transmissions M4/M5 |
| **Total** | **52** | Liste explicite ci-dessous ; aucun dossier ajouté globalement |

Les JSON `docs/audit_m1_v61/controles.json`, `docs/deblocage_m1_m2_v61/diagnostic_paires.json`
et `verification_correctif.json` sont retenus comme annexes méthodologiques légères
référencées par les documents. Ils ne contiennent pas de chemins personnels ni
les journaux et manifestes d'exécution interne des lots. Ils ne remplacent pas les
sorties réelles conservées sous `data/`. Les fixtures géographiques réelles portent
leur provenance et une portée de régression technique, sans qualification écologique.
Le code QA et les conventions D/S/R1–R4 sont versionnés dans leur état proposé ;
leur ajout au dépôt ne constitue pas une validation écologique.

**À conserver localement sans versionner : 184 fichiers non suivis initialement sous
`data/`**, dont :

- `data/processed/reservoirs.gpkg`, `data/processed/corridors.gpkg`, `data/processed/routes.gpkg`.
- Tous les fichiers de `data/derived/m2_reel_20261109_01/` : résultats, copies sources,
  manifestes internes, mesures, journaux et scripts de cette copie de travail.
- Tous les fichiers de `data/derived/m2_frontiere_20261109_01/` : résultats et preuves
  de validation, copies de code et entrées figées, rapports d'exécution.
- Tous les fichiers de `data/derived/m2_difference_vide_20261110_01/` : preuves et scripts
  d'exécution ponctuelle.
- Tous les fichiers de `data/derived/m2_diagnostics_20261110_01/` : descriptions réelles,
  secteurs, manifeste et script de préparation locale.
- Le ZIP M4 et son SHA-256, retrouvés hors dépôt dans `/Users/ouissal.c/Documents/` ;
  les contrôles d'assemblage restent sous `/private/tmp/reconnect_normandie_livraison_20261110/`.

**À exclure :** les trois `.DS_Store` visibles au démarrage (`.DS_Store`,
`tests/.DS_Store`, `tests/fixtures/.DS_Store`), caches, environnements virtuels,
configuration `.env*` et archives. Tous restent sur disque. La liste exacte des
234 fichiers non suivis initiaux et leur classement sont conservés hors dépôt dans
`git_final/non_suivis_avant.txt` et `git_final/classement_non_suivis.json`.
Aucun fichier de secret détecté dans les chemins proposés.

## Verdict et effet du patch .gitignore

**Adapté et appliqué**, sans ajustement des règles proposées. Les règles existantes
`__pycache__/`, `*.py[cod]`, `.venv/` sont préservées. Ajouts :

```gitignore
/data/raw/
/data/processed/
/data/derived/
*.gpkg
*.gpkg-*
*.zip
*.zip.sha256
.DS_Store
.pytest_cache/
.mypy_cache/
.ruff_cache/
venv/
.env
.env.*
!.env.example
```

Le contrôle `git check-ignore --no-index -v` a porté sur **tous les 21 fichiers
actuellement suivis** et les **52 chemins proposés** : aucune correspondance
excluante. Ce contrôle évite de se reposer sur le seul fait que Git protège les
fichiers déjà suivis des effets de `.gitignore`. Les scripts, schémas, documents,
fixtures GeoJSON et fichiers `provenance.json` nécessaires sont conservés.

Exemples confirmés par `git check-ignore -v` :

| Chemin contrôlé | Règle racine effective |
| --- | --- |
| `data/processed/routes.gpkg` | `/data/processed/` |
| `data/derived/m2_diagnostics_20261110_01/manifest_ingestion_interne.json` | `/data/derived/` |
| `reconnect_normandie_M2_M4_reel_exploratoire_20261110.zip` | `*.zip` |
| `reconnect_normandie_M2_M4_reel_exploratoire_20261110.zip.sha256` | `*.zip.sha256` |
| `tests/.DS_Store` | `.DS_Store` |
| `.pytest_cache/example` | `.pytest_cache/` |
| `analysis/__pycache__/example.pyc` | `__pycache__/` |
| `.venv/example` | `.venv/` |
| `.env.local` | `.env.*` |

## Liste exacte et commande proposée

**Commande préparée, non exécutée sans `--dry-run` :**

```sh
git add -- \
  .gitignore \
  analysis/aggregate_conflicts.py \
  analysis/detect_conflicts.py \
  analysis/evaluate_priorities.py \
  analysis/export_priority_results.py \
  analysis/prepare_priority_inputs.py \
  analysis/validate_inputs.py \
  docs/audit_actions_m2.md \
  docs/audit_correctif_priorite_m2.md \
  docs/audit_m1_v61/README.md \
  docs/audit_m1_v61/controles.json \
  docs/audit_m1_v61/verifier_livraison.py \
  docs/contrat_qualite_amont_m2.md \
  docs/deblocage_m1_m2_v61/README.md \
  docs/deblocage_m1_m2_v61/config_conflits.proposition.json \
  docs/deblocage_m1_m2_v61/config_enjeux.proposition.json \
  docs/deblocage_m1_m2_v61/diagnostic_paires.json \
  docs/deblocage_m1_m2_v61/diagnostiquer_paires.py \
  docs/deblocage_m1_m2_v61/grid_overlap.proposition.patch \
  docs/deblocage_m1_m2_v61/plan_detaille.md \
  docs/deblocage_m1_m2_v61/verification_correctif.json \
  docs/deblocage_operationnel_m1_m2_v61.md \
  docs/diagnostics_ecologiques_reels_m2_20261110.md \
  docs/dictionnaire_faits_actions_m2.md \
  docs/finalisation_frontiere_m2_20261109.md \
  docs/methode_m2.md \
  docs/notes_contrat_m3_m4_proposal2.md \
  docs/regles_actions_m2.md \
  docs/revue_scientifique_m1_m2_v61.md \
  docs/rules_actions.json \
  docs/schema_actions_m2.json \
  docs/securisation_git_m2_20261110.md \
  docs/synthese_scientifique_m2_m5_20261110.md \
  docs/table_decision_m2.md \
  docs/transfert_actions_m2_m4.md \
  docs/transmission_interne_m2_m4_20261110.md \
  docs/verification_m2_priorites.md \
  docs/verification_spec_m2_v2.md \
  tests/fixtures/m1_grid_v61/generate_hex_grid.py \
  tests/fixtures/m1_grid_v61/grille_pilote_wgs84.geojson \
  tests/fixtures/m1_grid_v61/provenance.json \
  tests/fixtures/m2/action_rule_cases.json \
  tests/fixtures/m2/decision_cases_m2.json \
  tests/fixtures/m2/territory_boundary_real_cases.json \
  tests/m2_priority_helpers.py \
  tests/test_m2_action_facts_audit2.py \
  tests/test_m2_action_rule_contract.py \
  tests/test_m2_grid_overlap.py \
  tests/test_m2_priorities.py \
  tests/test_m2_priority_audit.py \
  tests/test_m2_priority_inputs.py \
  tests/test_m2_territory_membership.py
```

Aucun `git add .` ni `git add -A`. Le contrôle préalable utilise les mêmes arguments
avec `--dry-run`. Il a été exécuté sur une copie identique de l'index dans le dossier
temporaire, via `GIT_INDEX_FILE`, pour garantir que l'index réel reste intact.
Résultat : **code retour 0, 52 chemins annoncés, zéro chemin inattendu, aucun stderr**.
Les noms annoncés correspondent exactement à la liste ci-dessus. L'index réel reste
identique à l'état initial, sans fichier indexé. Les traces sont conservées dans
`git_final/git_add_dry_run.stdout.txt` et `git_add_dry_run.stderr.txt`.

Les 52 fichiers sont textuels, sans lien symbolique, aucun de 1 Mio ou plus ;
ensemble environ **1,08 Mio**. Le plus grand est `docs/schema_actions_m2.json` :
**144 694 octets**. Les motifs de clés privées, jetons GitHub/AWS/API connus,
affectations d'identifiants sensibles et URL avec identifiant/mot de passe n'ont
produit aucune alerte. Ce contrôle ciblé ne constitue pas une garantie universelle
sur tout secret possible ; aucune archive, donnée brute volumineuse ou configuration
locale n'entre dans la sélection.

Les fichiers déjà suivis et inchangés (entrypoints, exigences Python, contrat public,
schémas mailles/conflits et tests historiques) sont déjà dans HEAD et ne requièrent
pas d'ajout. Le contrat public M2/M4 demeure inchangé.

## Message de commit proposé

```text
feat(m2): consolider les contrôles SIG, le triage et la transmission interne

- conserver les correctifs numériques de grille et de frontière et leurs régressions
- versionner la QA amont, les conventions D/S proposées et les contrats d’actions
- préparer les transmissions descriptives M4/M5 sans priorité écologique calculée
- exclure données sources, résultats locaux, archives, caches et configuration locale
```

## Limites restantes avant commit et push

Aucun blocage technique dans la sélection. L'autorisation de commit et de push
reste à donner séparément. Avant un commit autorisé, relire le diff réellement
indexé ; ce contrôle préalable n'a pas indexé les fichiers. Aucun test M2 relancé,
aucune nouvelle qualification écologique : le code de calcul est inchangé dans
cette intervention.

Le futur clone GitHub contiendra le code, les fixtures et la documentation, mais
pas les sorties réelles et preuves d'exécution internes sous `data/`. Les liens
vers ces lots locaux nécessitent le ZIP M4 conservé séparément ; les documents
historiques et propositions datées ne sont pas réécrits comme des décisions actuelles.
Le ZIP M4 a été retrouvé à son emplacement actuel :
`/Users/ouissal.c/Documents/reconnect_normandie_M2_M4_reel_exploratoire_20261110.zip`.
Son empreinte correspond exactement à celle du lot livré (1 141 431 octets, 34 fichiers), SHA-256
`f496fd5561e6aa4d6819af71cbbf6818c784f795e87347fa11970d0f9c1e7091`.

La liste des chemins, tailles et SHA-256 finaux et les traces de contrôle sont sous
`/private/tmp/reconnect_normandie_livraison_20261110/git_final/`.
**Aucun commit, push, merge, reset, clean ou changement de branche effectué.**
