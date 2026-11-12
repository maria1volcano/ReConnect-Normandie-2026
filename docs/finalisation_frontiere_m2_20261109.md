# Finalisation du contrôle de frontière M2 — 9 novembre 2026

**Verdict : correctif validé et intégré à `feat/diagnostics-ecologiques`, sans commit.** Les décisions A/B sont appliquées, les contre-exemples sont refusés et les résultats réels sont identiques à la référence. Aucun merge, reset, clean, stash, checkout, commit ou push.

## État initial et reproduction obligatoire

Le fichier de la branche `analysis/aggregate_conflicts.py` était encore identique octet par octet à `execution/aggregate_conflicts.original.py` de la première exécution réelle : SHA-256 `5bbebbbca99abf680a8d5b20861baf7780acb9ffd02e927bc7f0e3a8426a1516`. Il ne contenait pas le correctif local.

Avant toute modification de la branche, une nouvelle copie isolée a reçu les scripts M2 courants et les entrées/configurations figées de `m2_reel_20261109_01`. La grille n'a pas été régénérée. Le lancement initial a retourné **2**, avec **`event_outside_territory`**, sans publier de lot. Une nouvelle détection a identifié les **mêmes 17 `conflit_id`** que `diagnostic_frontieres.json` ; aucun identifiant ajouté ou manquant. [Reproduction](../data/derived/m2_frontiere_20261109_01/execution/reproduction_echec.json), [liste comparée](../data/derived/m2_frontiere_20261109_01/execution/liste_rejetee_initiale.json).

Les comptes 1 069/1 184 n'ont pas été considérés comme déjà consolidés sur la branche : ils ont servi uniquement de référence à la comparaison après validation du correctif.

## Règle finale effectivement appliquée

Le [diff exact de la branche](../data/derived/m2_frontiere_20261109_01/execution/correctif_frontiere_branche.diff) est limité à `aggregate_conflicts.py` : 64 lignes ajoutées, 3 supprimées.

1. Refus des géométries nulles, vides, invalides ou à coordonnées non finies, et d'un territoire invalide. Sur les entrées valides, **`study.covers(geometry)` conserve l'acceptation historique**, y compris pour une ligne entièrement sur la frontière.
2. En cas d'échec de `covers`, seule une **LineString** satisfaisant **`geometry.relate_pattern(study, "1********")`** peut bénéficier d'une exception. Une portion de l'intérieur de la ligne doit rencontrer l'intérieur du territoire en dimension 1 : un contact ponctuel ou un trajet sur la frontière ne suffit pas.
3. Si `difference(study)` est vide, acceptation par la branche spécifique `difference_vide_malgre_predicat`, sans budget ou marges artificiels.
4. Sinon, la différence doit être une LineString/MultiLineString valide ; l'intersection doit être non vide et valide. **Une ou plusieurs composantes extérieures** sont possibles. Leur **longueur cumulée** vérifie `0 < outside.length <= delta`, et la distance de Hausdorff à l'intersection vérifie simultanément `0 <= distance <= delta`.
5. La formule reste exactement celle du patch initial : `hypot(max ULP(X), max ULP(Y))`, calculée sur les coordonnées XY de l'événement. Aucun multiplicateur, élargissement de type ou budget supplémentaire. Valeurs calculées non finies/non admissibles et échecs topologiques sont refusés.

Le budget ULP reste une **convention d'ingénierie, pas une borne certifiée de précision GEOS**. L'événement original n'est jamais remplacé par son intersection, déplacé ou découpé. `event_outside_territory` est conservé pour les refus ; `event_territory_numerical_residue` est conservé pour les exceptions tracées. Le mode numérique est désormais nommé `residus_lineaires_resolution_machine`, pour ne pas prétendre limiter l'exception à une seule extrémité.

## Analyse individuelle des 17 événements

Le [tableau complet](../data/derived/m2_frontiere_20261109_01/execution/evenements_frontiere_17.md) fournit pour chaque identifiant : type, `covers`, type/longueur de différence, type d'intersection, longueur linéaire intérieure, prédicat DE-9IM, Hausdorff, delta, deux marges, décision et règle. [Version JSON](../data/derived/m2_frontiere_20261109_01/execution/evenements_frontiere_17.json).

| Branche de décision | Cas | Portion intérieure linéaire | Décision |
| --- | ---: | --- | --- |
| Différence vide malgré `covers=False` | 14 | Prédicat dimension 1 vrai et longueur intérieure positive | 14 admis |
| Résidus extérieurs linéaires non vides | 3 | Prédicat dimension 1 vrai et longueur intérieure positive | 3 admis sous les deux contrôles ULP |

Dans les 14 premiers cas, **delta et marges sont N/A**, car non utilisés par cette branche. La distance de Hausdorff, mesurée indépendamment, est nulle.

Pour les trois autres, `delta = 9,331397911231848e-10 m` ; longueurs extérieures et distances de Hausdorff valent respectivement `5,820766091346741e-11`, `5,820766091346741e-11` et `1,7462298274040222e-10 m`. Les deux marges sont positives. Les 17 admissions résultent des critères ; aucun événement n'a été supprimé ou forcé à passer.

## Non-régression et cas adversariaux

**59 nouveaux cas permanents**, dont les 17 géométries réelles figées, complètent les 75 tests conflits existants. Ils vérifient notamment :

- Acceptation historique des lignes intérieures et des lignes couvertes sur la frontière.
- Refus d'une ligne extérieure touchant seulement un point et d'une ligne de frontière prolongée d'un résidu pourtant sous budget : le prédicat topologique est discriminant.
- Acceptation d'un résidu avec portion intérieure et de deux résidus dont la somme reste sous budget ; refus lorsque chaque résidu est petit mais que leur somme dépasse `delta`.
- Contrôle indépendant de Hausdorff, refus des valeurs non finies/négatives et d'un delta invalide ; refus des types non admissibles à l'exception et des géométries invalides.
- Absence de mutation WKB, conservation des liens de frontière de maille, du propriétaire canonique, des comptes observés/exclusifs et des codes d'avertissement/erreur.

Le test isolant la garde de Hausdorff injecte explicitement une valeur calculée hors budget : il ne prétend pas qu'une ligne connexe présente naturellement une distance supérieure à toute sa longueur extérieure.

| Exécution réellement effectuée | Exécutés | Réussis | Échecs | Erreurs | Ignorés |
| --- | ---: | ---: | ---: | ---: | ---: |
| Première série ciblée isolée, doublure Hausdorff incorrecte | 134 | 130 | 4 | 0 | 0 |
| Ciblés isolés après correction de la doublure | 134 | 134 | 0 | 0 | 0 |
| Suite M2 complète isolée, avant report | 1 415 | 1 415 | 0 | 0 | 0 |
| Ciblés sur la branche après report | 134 | 134 | 0 | 0 | 0 |
| Suite M2 complète sur la branche après report | **1 415** | **1 415** | **0** | **0** | **0** |

Les quatre échecs initiaux provenaient d'une doublure renvoyant un `float` Python au lieu du scalaire NumPy attendu par Shapely. **Seule la doublure a été corrigée ; aucun assouplissement de la règle n'a servi à les faire passer.** Les XML de toutes les exécutions sont conservés dans le [manifeste de validation](../data/derived/m2_frontiere_20261109_01/VALIDATION.json). Les suites complètes ont émis 40 avertissements : 38 dépréciations pyproj et 2 débordements volontairement testés dans la validation des entrées. Les 134 ciblés sont inclus dans les 1 415 ; ces passages ne représentent pas des tests distincts supplémentaires.

## Comparaison réelle après intégration

Après le report, le pipeline conflits a été relancé sur les mêmes entrées figées, avec des chemins nouveaux, dans une copie isolée dont **tous les fichiers Python de calcul sont identiques à ceux de la branche**. Le code retour est **0**, le lot est vérifié et l'empreinte d'`aggregate_conflicts.py` enregistrée dans le rapport est celle de la branche.

| Invariant | Référence isolée initiale | Version intégrée |
| --- | ---: | ---: |
| Couples route–corridor | 1 047 | 1 047 |
| Routes distinctes | 789 | 789 |
| Événements géométriques | 1 069 | 1 069 |
| Mailles avec événements observés | 29 | 29 |
| Relations événement–maille | 1 184 | 1 184 |
| Propriétaires canoniques | 1 069 | 1 069 |

La comparaison est **exacte** pour les 1 069 identifiants, WKB et toutes les propriétés des événements, dont IDs sources et statuts ; pour les géométries/propriétés des 43 mailles ; pour les relations, frontières, propriétaires et comptes locaux/exclusifs. Les codes et multiplicités d'avertissements sont également conservés. Les seules évolutions de la trace numérique documentent la règle renforcée/plurielle et la nouvelle provenance de calcul. [Preuve de comparaison](../data/derived/m2_frontiere_20261109_01/execution/comparaison_branche_reference.json).

Nouveaux résultats : [événements](../data/derived/m2_frontiere_20261109_01/data/derived/branche_conflits.gpkg), [mailles et relations](../data/derived/m2_frontiere_20261109_01/data/derived/branche_mailles.gpkg), [rapport du lot](../data/derived/m2_frontiere_20261109_01/data/derived/branche.validation.json). Les premiers résultats `m2_reel_20261109_01` restent inchangés.

## Fichiers et préservation

- **Modifié :** [analysis/aggregate_conflicts.py](../analysis/aggregate_conflicts.py), uniquement après validation isolée des tests et invariants.
- **Créés :** [tests/test_m2_territory_membership.py](../tests/test_m2_territory_membership.py), [fixture des 17 cas](../tests/fixtures/m2/territory_boundary_real_cases.json), le présent rapport, et le dossier nouveau `data/derived/m2_frontiere_20261109_01/` contenant copie isolée, journaux, sorties, diff et preuves.
- L'[inventaire initial](../data/derived/m2_frontiere_20261109_01/execution/inventaire_initial.json) conserve statut Git, non suivis, ignorés et empreintes. Parmi les **165 fichiers préexistants**, seul le validateur d'agrégation autorisé a changé. Tous les autres, y compris GeoPackages M1, anciens résultats, détecteur, correctif `grid_overlap`, travaux D/S et R1–R4, contrats publics et modifications locales précédentes, sont identiques octet par octet. Branche et HEAD inchangés.

**Conclusion : la correction technique de frontière est intégrée et reproductible.** La qualification écologique et les conditions de diffusion restent inchangées : ces événements sont des candidats géométriques, pas des obstacles confirmés ; les priorités et actions ne sont pas validées par ces tests. Le travail peut passer à la qualification scientifique ciblée et à l'intégration interne M4, sans réouvrir les audits antérieurs ni modifier le gel annoncé du 10 novembre 2026 à 18 h (Europe/Paris).
