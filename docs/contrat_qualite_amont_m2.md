# ReConnect Normandie V6.1 — Contrat de qualité en amont des tables D/S

**Document de travail M2** — 3 novembre 2026 — `m2-qa.proposal-2`  
**À ne pas confondre avec une validation scientifique de production :** M1 n'a pas encore livré/validé les couches réelles exploitées ici.

## 1. Pourquoi ce contrat existe

`validite_positive`, `validite_absence`, `contradiction_bloquante`, `enjeu_classe` et `applicabilite` doivent être calculés ou validés **en amont** de `evaluate_priorities.py` par des fonctions traçables. La table D/S ne doit ni les deviner ni interpréter des attributs M1 inconnus.

## 2. Chaîne de responsabilités

| Fonction proposée (nom adaptable au dépôt) | Données nécessaires | Sortie | Étape sans M1 |
|---|---|---|---|
| `validate_diagnostic_inputs` | Entrée typée, IDs, statut, versions et références | erreurs bloquantes + avertissements | Implémentable maintenant |
| `derive_positive_evidence` | Événements M2, CRS, précision, `statut`, références, méthode contextuelle | capacité `validite_positive`, preuves, limites | Interface/test synthétique ; règles réelles en attente |
| `derive_absence_evidence` | Couverture M1 validée par thème + emprise maille + événements observés | capacité `validite_absence`, preuve d'absence si aucun signal | Réutiliser `_fully_covered` ; tests synthétiques |
| `detect_assertion_conflicts` | Assertions sur la même propriété, emprise, période, événement et sources | `contradiction_bloquante` + références | Implémenter comparaison de structures, pas d'inférence écologique |
| `derive_applicability` | Périmètre famille + sous-trame + règles spatiales/documentaires | `oui`, `non_applicable_documentee`, `inconnue` + référence | Interface en attente de dictionnaires M1 |
| `classify_ecological_stakes` | ENJ-01/02 + catégories, sous-trames et critères approuvés | classe d'enjeu + `enjeu_methode_id` | Interface + état `inconnu` ; aucune classe inventée |

**Attention :** un code d'adaptation par famille peut être un ensemble de fonctions plutôt qu'un unique fichier. Éviter les moteurs autonomes divergents. Les règles d'action R1–R4 restent spécifiées par M2 et exécutées par M4.

## 3. Sémantique normative

- `validite_positive`: « *si* cette observation est retenue, sa preuve est suffisamment localisée/documentée pour soutenir exactement l'affirmation déclarée ». Ce booléen ne transforme pas un croisement géométrique en `conflit_potentiel` ou en `obstacle_confirme`.
- `validite_absence`: « la famille et l'emprise disposent des données nécessaires et complètes pour conclure à l'absence des signaux qu'elle mesure ». Peut être vrai **même si un événement est observé** ; le signal demeure positif et l'absence n'est alors évidemment pas conclue.
- `signal_pression=absence_validee`: assertion d'absence **effectivement établie**, qui impose `validite_absence=true` et aucune observation pertinente incompatible ; le QA refuse les contradictions.
- `contradiction_bloquante=true`: impossibilité de décider pour une **assertion précise**, avec deux références incompatibles sur une même emprise/période comparable. Ce n'est ni la simple superposition de couches ni la différence entre deux diagnostics indépendants.
- `enjeu_classe` connu : exige une méthode de classification versionnée et approuvée. Conserver `inconnu` sans inventer de seuil.
- `applicabilite=non_applicable_documentee`: exige une référence positive de non-applicabilité ; une couche absente ou mauvaise n'est jamais une preuve de non-applicabilité.

## 4. Trace minimale recommandée

Chaque diagnostic doit pouvoir être relié à :

- Ses identifiants `diagnostic_id`, `famille_id`, `source_objects[]`, `phenomene_id` si établi, `conflit_id[]` éventuels.
- Les versions de méthode et de données, la sous-trame, la date/période, la précision et la couverture réellement validée.
- Les preuves de présence et d'absence : `preuve_ids[]`, règles de validation, couverture par thème et emprise.
- La justification de non-applicabilité, si applicable.
- Les assertions contradictoires éventuelles, avec leurs références, zone/période et type de contradiction.
- Les `motifs_qualite[]` normalisés (pas uniquement un booléen final).

L'information brute/privée reste dans les données internes et dans `fiches_zones.json` selon les droits. Les GeoJSON publics reprennent uniquement des champs autorisés.

## 5. Jeux de tests préalables à exiger

1. Croisement 2D réel, mais aucune preuve de franchissabilité : `croisement_detecte` uniquement.
2. Croisement dont la précision est insuffisante ou frontière uniquement : observation conservée, aucune promotion automatique.
3. Croisement + ouvrage indiqué « pont » sans évaluation écologique : pas d'`obstacle_confirme` automatique.
4. Qualification externe avec identifiant périmé ou localisation non résolue : rejet ou non-conclusion tracée.
5. Zéro événement et couverture route/corridor validée sur `H∩T` : `absence_validee` possible.
6. Zéro événement et couverture inconnue/partielle : `non_evalue` ; jamais absence prouvée.
7. Croisement positif avec couverture totale : `validite_positive=true` et `validite_absence=true` possibles ensemble.
8. Une source dit présence, l'autre absence, pour le même objet, zone et période, toutes deux prétendument validées : contradiction avec références.
9. Deux assertions sur objets, périodes ou propriétés distincts : pas de contradiction bloquante.
10. Données bocage manquantes : `applicabilite=inconnue`, pas `non_applicable_documentee`.
11. Enjeu connu sans méthode d'enjeu : D2, jamais passage silencieux à une couleur.
12. Les mêmes données, réordonnées ou indexées différemment : mêmes flags/identifiants/références normalisés.

Ne pas fabriquer des preuves de production par des constantes « test » ; dans les fixtures, toutes les références doivent être explicitement SYNTHÉTIQUES.

## 6. Dépendances externes attendues

M1 : sources officielles préparées, dictionnaires de types de routes/ouvrages/sous-trames, couvertures validées, précision, versions, périodes, droits. M2 : règles de validité et de traduction scientifique en enjeux. M3/M4 : contrat `m2-m4.proposal-2` à confirmer ; ne pas inférer les preuves depuis la couleur.

## 7. Intégration après audit correctif

### Contrôle trivalent et capacités indépendantes

`detect_assertion_conflicts()` conserve trois conclusions : `true` /
`contradiction_documentee`, `false` / `controle`, `null` / `non_evalue`.
`integrate_assertion_control()` est le passage explicite vers D/S. Il exige une
cible (`pression`, `applicabilite`, `autre_affirmation`) et une `portee_reference`
documentant l'affirmation concernée. Le contrôle est relié au `diagnostic_id`,
conservé dans `controle_contradictions` avec ses motifs et `entree_avant_controle`.
Le `null` n'est jamais converti en `false`.

Sans preuve indépendante documentée, une conclusion de pression affectée par un
contrôle inconnu est mise en attente : `signal_pression=non_evalue`, capacités
positives/négatives non revendiquées et état initial conservé. Les règles D/S
existantes traitent ensuite cette entrée. Pour conserver une preuve fiable,
fournir `preuve_ids_independantes` (sous-ensemble des preuves du diagnostic) et
`independance_reference`. Cette indépendance est une déclaration examinée par
M1/M2, jamais inférée d'un fichier différent ou authentifiée par le logiciel.

Un signal élevé indépendant reste visible ; la couverture décisionnelle demeure
partielle si le contrôle inconnu affecte la décision. Un contrôle explicitement
relatif à une autre affirmation peut rester une limite sans déficit décisionnel.
Une applicabilité affirmative affectée par un contrôle inconnu reste `inconnue`.
Une justification de non-applicabilité contestée exige un réexamen et déclenche
`E_APPLICABILITE_CONTRADICTOIRE`.

Les entrées historiques à booléen strict restent acceptées. Le `null` sans contrôle
structuré reste une erreur de type. Une conclusion exploitable affirmée directement
avec un contrôle inconnu dépendant est refusée par
`E_CONTROLE_CONTRADICTION_NON_RESOLU` ; utiliser l'intégrateur et documenter la portée.

### D0/D1 : options et choix provisoire

Deux options ont été examinées : rendre D1 prioritaire sur D0 partout, ou conserver
la précédence existante et contrôler la portée en amont. La première modifierait
les conventions et les 576 oracles sans décision scientifique. **D0 reste donc
avant D1.** La seconde option est implémentée :

- Contradiction ciblant la justification de non-applicabilité : entrée bloquée
  avant D0, sans nouvelle règle de priorité.
- Contradiction documentée sur une autre affirmation : D0 conservée, contradiction
  et référence visibles dans le détail et les limites.
- Ancienne entrée D0 + contradiction sans portée : règle D0 conservée, motif
  `portee_contradiction_non_documentee`, couverture partielle. Cette entrée ne
  permet pas de certifier les conditions de S3 avec un autre diagnostic faible.

S3 exige explicitement une couverture décisionnelle suffisante ; aucun bonus,
seuil écologique ou nouvel ordre D n'est ajouté. Une modification générale de la
précédence reste une décision méthodologique à approuver séparément.

### Qualification contextuelle et péremption

Les règles passées à `apply_potential_conflict_rules()` sont des définitions
explicitement déclarées approuvées par l'appelant. Leur copie est conservée en
mémoire dans les attributs pandas, séparément des traces de preuve. Ce registre
n'est ni un certificat d'identité ni une validation scientifique automatique.
Après lecture GPKG/JSON ou conversion en dictionnaire, fournir explicitement le
registre `approved_context_rules` à `derive_positive_evidence()` ; les traces ne
peuvent pas s'auto-approuver. Une liste vide explicite retire ces autorisations.

La QA exige une correspondance exacte entre trace et définition approuvée :
identité, version, critères, références et validation déclarée. Elle réutilise le
prédicat existant sur les observations actuelles. Une règle contextuelle n'autorise
que `conflit_potentiel`, jamais une confirmation d'obstacle.

Les qualifications contextuelles et humaines portent `event_binding_sha256`,
empreinte de la géométrie, des observations, sources, méthode et informations de
précision au moment de l'examen. Changer ces éléments sans renouveler la preuve
la rend inexploitable. Statut qualifié et listes de mailles sont exclus : une
agrégation ne périme pas la preuve. Le transport numérique `precision_m=1` → `1.0`
en GPKG conserve la même mesure et empreinte. L'empreinte n'est pas une signature
d'auteur. Les anciennes traces sans empreinte exigent un réexamen et un
renouvellement ; elles ne sont pas certifiées a posteriori.

### Liaison sources–événement–diagnostic

`prepare_route_corridor_diagnostic()` reçoit l'enjeu/applicabilité documentés, la
méthode de famille, l'événement et sa revue. Il contrôle les couples `namespace`/`id`
contre les sources de l'événement, applique la QA positive et relie le diagnostic
au `conflit_id` et aux preuves correspondantes. Si la revue fournit `source_ids`,
leur correspondance est également contrôlée. Une discordance lève
`E_REFERENCE_SOURCE_INVALIDE`. Les registres du pilote doivent encore être validés
par `validate_diagnostic_inputs()` avant D/S.

Aucune classification réelle ni publication n'est activée. Le
[bilan de l'audit](audit_correctif_priorite_m2.md) précise les tests et limites.
