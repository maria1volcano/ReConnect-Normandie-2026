# Audit correctif du moteur de priorité M2

Branche : `feat/diagnostics-ecologiques`. Conventions : `m2-priorites.proposal-2`.
Les géométries, règles contextuelles, attestations et diagnostics de tests sont
**exclusivement SYNTHÉTIQUES**. Leur réussite n'est pas une validation scientifique
de terrain. Les modifications locales présentes au début de l'audit sont conservées.

## Vérifications exécutées

La suite a été exécutée avant modification, puis après toutes les corrections :

| Exécution | Réussis | Échecs | Erreurs | Ignorés | Avertissements |
| --- | --- | --- | --- | --- | --- |
| Avant audit | 948 | 0 | 0 | 0 | 38 |
| Après audit | 1 007 | 0 | 0 | 0 | 38 |

Durées pytest : 12,85 s avant, 14,69 s après. Environnement isolé existant
`/private/tmp/reconnect-m2-venv`, sans dépendance ajoutée. Les avertissements sont
les dépréciations pyproj/NumPy déjà observées : 6 dans les conflits et 32 dans les
contrats GeoJSON. Aucun avertissement n'est masqué.

```sh
/private/tmp/reconnect-m2-venv/bin/python -m pytest -q tests/ --junitxml=/private/tmp/m2-audit-after.xml
```

Les 948 tests antérieurs, leurs sources et le helper synthétique sont inchangés.
Les 38 scénarios ont les mêmes oracles : 34 décisions et 4 erreurs attendues.
L'énumération conserve **576 combinaisons : 432 admises, 144 rejetées, 0 admissible
non couverte**. Les empreintes avant/après des tests existants, des fixtures et des
quatre fichiers du contrat GeoJSON proposal-1 ont été comparées.

## Problèmes confirmés et corrections

### 1. Contradictions non évaluées

Le détecteur produisait null alors que l'entrée D/S exigeait un booléen strict.
`integrate_assertion_control()` fournit maintenant le passage explicite, en
conservant le contrôle trivalent, la portée et sa référence, le diagnostic visé
et la trace des valeurs avant intégration. Une entrée null sans contrôle structuré
reste refusée : aucune conversion implicite vers false.

| Situation | Traitement |
| --- | --- |
| Contradiction confirmée sur la pression | État true conservé, D1 selon la précédence existante |
| Contrôle négatif effectivement réalisé | État false / `controle` conservé, signal évalué normalement |
| Contrôle inconnu, conclusion dépendante | Conclusion de pression mise en attente `non_evalue`, D3 si enjeu connu ; état initial et null conservés |
| Contrôle inconnu, preuve fiable indépendante documentée | Signal préservé ; couverture partielle si le contrôle affecte la décision |
| Contrôle inconnu sur l'applicabilité affirmative | Applicabilité inconnue, traitement D1 existant |
| Contrôle portant sur une autre affirmation | Limite conservée ; pas de déficit décisionnel inventé du seul fait de ce contrôle |

L'indépendance est déclarée par références et IDs de preuves déjà présents dans le
diagnostic. Le logiciel ne la mesure pas, ne la déduit pas de fichiers différents
et n'authentifie pas le signataire de l'attestation.

### 2. Portée de D0/D1

Le risque était confirmé : une contradiction portant sur la justification même
de non-applicabilité n'était pas distinguée d'une autre contradiction.

Deux options sont documentées : inverser D0/D1 globalement, ou garder la table et
contrôler la portée avant décision. L'inversion requiert un arbitrage scientifique
et modifierait les oracles : **elle n'est pas appliquée**. D0 reste avant D1.

Une justification de non-applicabilité explicitement contestée est désormais
refusée par `E_APPLICABILITE_CONTRADICTOIRE`, au lieu de laisser D0 la masquer.
Une contradiction explicitement extérieure à cette justification conserve D0,
avec sa limite et sa référence visibles. Les anciennes entrées sans portée gardent
leur règle D0 ; le motif `portee_contradiction_non_documentee` rend la couverture
partielle et empêche de certifier S3 avec un autre diagnostic faible. S3 exige
explicitement la couverture suffisante déjà prévue par sa définition.

Aucune nouvelle formule ou classe de priorité n'est introduite. Les arbitrages
sur le domaine écologique restent à M1/M2 ; l'erreur exige leur réexamen.

### 3. Qualifications contextuelles et preuves périmées

La QA acceptait une trace structurée sans la confronter à une règle approuvée ni
aux observations actuelles. Le prédicat exact existant a été extrait et réutilisé,
sans règle scientifique de production ajoutée.

La définition approuvée provient désormais d'un registre distinct fourni par
l'appelant. Les règles explicitement passées à `apply_potential_conflict_rules()`
sont copiées en attribut pandas local ; après relecture GPKG/JSON ou conversion en
dictionnaire, fournir `approved_context_rules`. La preuve ne peut pas servir de
registre à elle seule. Une liste vide explicite retire les autorisations.

Identité, version, critères, référence, validation déclarée, `conflit_id`, statut
autorisé et correspondance au contexte courant sont vérifiés. Une trace
contextuelle ne peut pas se faire passer pour une expertise confirmant un obstacle.

Les traces contextuelles et humaines enregistrent `event_binding_sha256`, une
empreinte des observations, sources, géométrie, méthode et informations de précision
examinées. Une modification les rend périmées. Les anciennes traces sans empreinte
exigent un nouveau contrôle et renouvellement, jamais un ajout rétroactif aveugle.
L'empreinte n'authentifie pas un auteur. Le transport numérique de précision
`1` → `1.0` en GPKG est testé sans perte de validité ; changer une sensibilité ou
un attribut réel n'est pas traité comme un simple changement de transport.

### 4. Sources et chaîne de préparation

`prepare_route_corridor_diagnostic()` vérifie les sources déclarées contre celles
de l'événement, avec espaces de noms explicites, puis construit les champs de QA,
références et `conflit_ids` à partir de l'événement effectivement examiné. Une revue
fournissant `source_ids` doit elle aussi correspondre. Les discordances déclenchent
`E_REFERENCE_SOURCE_INVALIDE`. Les méthodes d'enjeu/applicabilité ne sont pas
inventées par cet adaptateur. Les registres du pilote restent contrôlés avant D/S.

### 5. JSON et identifiants mixtes

Les index Python étaient corrects en mémoire ; leur sérialisation naïve pouvait
confondre 1 et "1". Ils restent inchangés dans l'API interne.
`prepare_priority_result_json()` produit une copie dont les index sont des tableaux
d'objets à `diagnostic_id` typé, triés selon le JSON canonique. Les tests effectuent
un véritable `json.dumps` / `json.loads` et reconstruisent les deux index sans perte.
Les autres objets à clés non textuelles et les valeurs non finies sont refusés.
La fonction ne publie rien et n'active aucun nouveau contrat GeoJSON.

### 6. États SIG et priorité

Le moteur D/S attribuait systématiquement `statut_analyse=analyse_effectuee` à une
surface positive, même sans diagnostic. Désormais l'état SIG est repris de l'entrée
ou conservé null s'il est inconnu ; il n'est pas inféré du calcul de priorité.
`etat_calcul_priorite` indique séparément `calculee`, `indeterminee` ou
`hors_territoire`. `couverture_synthese` reste la complétude décisionnelle.
Sans diagnostic sur une surface positive : S4 / indéterminée / partielle, sans
analyse SIG inventée. S0 conserve état hors territoire et couverture null.

## Risques examinés ne nécessitant pas de réécriture

- La table D était totale sur son domaine admissible : les 576 oracles et la
  précédence D0/D1 sont conservés, sans règle résiduelle ajoutée.
- Les règles de synthèse ne promeuvent pas deux modérés et conservent un élevé
  indépendant avec une autre famille non évaluable : garanties maintenues.
- Les identifiants entiers/chaînes sont déjà distincts dans Python : les index
  internes ne sont pas remplacés, seul le passage JSON manquant est ajouté.
- La distinction entre capacité d'absence et absence effectivement observée est
  déjà correcte ; aucune nouvelle règle écologique d'absence n'est ajoutée.
- Les garanties SIG de détection/agrégation, CRS et relations plusieurs-à-plusieurs
  restent réutilisées. `analysis/aggregate_conflicts.py` n'a pas été modifié.
- Les contrats proposal-1 n'avaient pas besoin d'être modifiés pour cet audit.

## Fichiers créés ou modifiés

Créés :

- `analysis/export_priority_results.py`
- `tests/test_m2_priority_audit.py`
- `docs/audit_correctif_priorite_m2.md`

Modifiés :

- `analysis/detect_conflicts.py` : validation/matching réutilisables, registre local,
  empreintes des preuves nouvelles.
- `analysis/prepare_priority_inputs.py` : intégration des contrôles, QA contextuelle,
  liaison sources/événement/diagnostic et validation de l'état SIG.
- `analysis/evaluate_priorities.py` : lecture explicite du contrôle, limites de
  couverture et séparation des états ; table scientifique D inchangée.
- `docs/contrat_qualite_amont_m2.md`
- `docs/notes_contrat_m3_m4_proposal2.md`
- `docs/methode_m2.md`

Aucun fichier de test préexistant, oracle, schéma proposal-1, export public,
remote, commit, push, règle d'action ou catalogue M5 n'a été modifié/créé.

## Nouveaux tests et intégration

Les **59 nouveaux tests** couvrent les trois états de contradiction ; les preuves
indépendantes ; la couverture réellement affectée ; les contre-exemples D0/D1 ;
les états invalides et l'absence de réparation silencieuse d'entrées mal formées ;
les règles approuvées, versions erronées, traces fabriquées, attributs ou sources
modifiés ; le transport GPKG ; les preuves externes périmées ; l'aller-retour JSON
des IDs mixtes ; les états SIG/ priorité / couverture distincts.

La chaîne complète est testée pour croisement brut, conflit potentiel documenté
et obstacle documenté : détection réelle d'un croisement synthétique → qualification
éventuelle → QA positive → sources/preuves enregistrées → diagnostic → D6 ou D5 →
S2 ou S1 avec une seconde famille D3 non évaluable. Les justifications, limites,
couverture partielle et null du contrôle sont vérifiés jusqu'au JSON. La même
chaîne n'écrit aucun fichier. Un test séparé confirme que zéro événement avec
couverture inconnue reste D3 / non évalué, jamais une absence validée.

## Compatibilité et prérequis avant une chaîne réelle

`m2-m4.proposal-1` reste inchangé : schémas, convertisseur et contrat API ont les
mêmes empreintes. Le format interne proposé `m2-priorites.internal-json-1` n'est
pas un GeoJSON approuvé. Pour proposal-2, M3/M4 doivent confirmer la forme tableau
des index, le null d'état SIG, l'état de calcul de priorité et l'exposition des
contrôles QA. Les notes de coordination décrivent ces adaptations explicitement.

Les anciennes qualifications sans empreinte et les registres contextuels perdus
lors d'une relecture exigent respectivement un nouvel examen et une configuration
d'approbation explicite. Aucun échec de validation ne doit être contourné par une
constante, un faux document ou une conversion de null en false.

M1 doit fournir couches officielles inspectées, IDs et espaces de noms stables,
dictionnaires, CRS, précision, périodes, couvertures, emprises, versions et droits.
M1/M2 doivent approuver les classes d'enjeu, l'applicabilité, les règles
contextuelles et la portée/indépendance des preuves. Au moins trois secteurs réels
contrastés restent à examiner avant usage décisionnel. Une chaîne réelle demande
également la vérification des lots, le réexamen des preuves et la revue des droits
et champs publics. Aucun seuil écologique, urgence, efficacité d'action ou moteur
R1–R4 n'est développé dans cet audit.
