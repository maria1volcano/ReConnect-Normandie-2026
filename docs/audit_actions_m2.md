# Audit du contrat scientifique d'actions R1–R4

**Révision courante : `audit-2`, 4 novembre 2026.** Les cinq contre-exemples sont
refusés par les faits typés ; les résultats internes, projections publiques et
erreurs ont des profils distincts. Le [bilan de reprise audit-2](#audit-2--reprise-et-consolidation-du-4-novembre-2026)
ci-dessous précise les tests, limites et fichiers à transmettre. Les sections
précédant ce bilan conservent l'historique audit-1 ; leurs nombres et déclarations
de préservation décrivent cette première itération, pas les adaptations audit-2.

**Verdict : proposition techniquement exploitable pour implémenter le socle M4 en
mode TEST ; activation scientifique et diffusion réelle non autorisées.** Les
méthodes familiales, preuves de terrain et correspondances catalogue doivent
encore être approuvées. Le schéma interne proposé doit être accepté par M4.

## Périmètre et références effectivement disponibles

Branche `feat/diagnostics-ecologiques`. Les modifications locales du moteur M2
présentes avant l'audit sont préservées. Aucun module dans `analysis/`, contrat
GeoJSON proposal-1/proposal-2, test antérieur, remote, commit ou push n'est modifié.

Les trois fichiers du pack ont été fournis pendant l'inspection. Avant leur
livraison, ils étaient absents du répertoire de travail ; l'audit a ensuite repris
sur ces fichiers réels. Le PRD déclaré par le pack et le catalogue M5 ne sont pas
présents localement. Une copie de PRD a été aperçue dans une référence Git locale,
sans changement de branche ; conformément à l'instruction M2, elle n'est pas
utilisée comme validation du PRD ni du catalogue.

Les correspondances **provisoires** sont exactement R1→A04, R2→A01, R3→A03,
R4→A02. Aucun conflit d'identifiant avec M5 n'est démontré : aucun catalogue M5
exploitable n'a été fourni pour comparaison. A05–A12 restent documentaires.

## Bilan exact des tests audit-1 — historique

| Vérification | Réussis | Échecs | Erreurs | Ignorés | Avertissements |
| --- | --- | --- | --- | --- | --- |
| Suite initiale | 1 007 | 0 | 0 | 0 | 38 |
| Suite finale complète | 1 095 | 0 | 0 | 0 | 38 |

Commande finale, dans l'environnement isolé existant :

```sh
/private/tmp/reconnect-m2-venv/bin/python -m pytest -q tests/ --junitxml=/private/tmp/m2-actions-final.xml
```

Durée finale : 12,69 s. Les 38 avertissements sont les dépréciations pyproj/NumPy
déjà présentes (6 conflits, 32 GeoJSON), sans nouvel avertissement ni masquage.
Les **88 nouveaux tests** portent sur documents, JSON Schema, IDs, fixtures,
précédence et partition logique finie. Aucun moteur M4 n'est exécuté et aucune
pertinence écologique réelle n'est démontrée par ces tests.

## Constats confirmés et consolidation

| Constat du pack initial | Traitement |
| --- | --- |
| Appariements cohérents avec l'instruction M2, mais PRD/catalogue non vérifiables | Appariements conservés et explicitement provisoires ; confirmation M5 requise |
| `family_evidence` des fixtures ne démontre pas les faits | Profils abstrait et normalisé distingués ; attestation qualifiée, attente M1 et non-applicabilité documentée séparées |
| Types et invariants uniquement en texte | Schéma interne proposé `schema_actions_m2.json`, avec IDs typés, versions, références et catégories contrôlées |
| A8 formulée comme « autres entrées » | Deux cas résiduels explicites ; aucune catégorie inconnue admise ; `E_ACTION_TABLE_NON_TOTALE` documentée |
| Codes V0 précis non définis | Liste `validation_errors` proposée, sans transformer `ERREUR` en statut d'action |
| Attentes de motifs, limites, preuves et codes fins absentes des oracles | Absence signalée et enrichissement proposé pour revue M2/M4 ; aucun oracle réécrit |
| Cas « couverture inconnue » encodés comme `partielle` | Conservés comme abstractions à signal inconnu ; aucune traduction automatique depuis la qualité SIG |
| R1 « croisement 2D non qualifié » pourrait être lu trop largement | Distinguer indice géométrique effectivement contrôlé et simple libellé non assorti de preuve ; oracle A8 conservé |
| Référence OFB R4 potentiellement interprétée comme protocole général | Portée corrigée : fiche d'un projet particulier ; méthode de déclenchement du pilote encore requise |

La [fiche OFB « Restauration de mares »](https://ofb.gouv.fr/restauration-de-mares)
décrit un projet du bassin du ru de Vaucresson, avec mise à jour du 28 octobre
2024. Elle ne fournit pas à elle seule un protocole général de qualification R4.
Les pages Cerema/OFB citées par le pack ont été ouvertes et leur portée décrite dans
la spécification. Aucun seuil, coefficient ou classement d'efficacité n'en est
importé. Les conventions A restent des propositions ReConnect.

## Audit des 52 cas et des deux multiproblèmes

Les 52 IDs de cas et les deux IDs multiproblèmes sont uniques. Les références des
multis existent et leurs quatre actions distinctes concordent avec les cas cités.
Le JSON des fixtures est inchangé par empreinte.

| Groupe d'oracles, répété pour R1–R4 | Nombre | Décision attendue | Statut |
| --- | --- | --- | --- |
| Positif étayé | 4 | A4 | `etayee_pour_examen` |
| Indice positif | 4 | A6 | `conditionnelle` |
| Absence vérifiée | 4 | A7 | `non_retenue_par_regle` |
| Couverture inconnue / signal inconnu | 4 | A8 | `non_evaluable` |
| Méthode non validée | 4 | A2 | `non_evaluable` |
| Non-applicabilité documentée | 4 | A1 | `non_retenue_par_regle` |
| Contradiction confirmée | 4 | A0 | `non_evaluable` |
| Contrôle inconnu sans indépendance | 4 | A3 | `non_evaluable` |
| Contrôle inconnu avec indépendance | 4 | A5 | `conditionnelle` |
| Absence sans preuve | 4 | V0 | Erreur, hors des quatre statuts |
| Non-applicabilité et signal positif | 4 | V0 | Erreur, hors des quatre statuts |
| Étayage et couverture essentielle incomplète | 4 | V0 | Erreur, hors des quatre statuts |
| Fait spécifique insuffisant | 4 | A8 | `non_evaluable` |

Total : **40 décisions abstraites et 12 entrées invalides** ; quatre étayées,
huit conditionnelles, huit non retenues, vingt non évaluables et douze V0.
Les 48 premiers cas ne donnent qu'une référence textuelle de famille ; les quatre
derniers un libellé de fait insuffisant et une source synthétique. Aucun de ces
52 objets n'est une attestation normalisée de production.

`MULTI-01` conserve A04 étayée, A01 conditionnelle, A03 non évaluable, A02 non
retenue. `MULTI-02` conserve A04 non évaluable, A01 et A03 étayées, A02 conditionnelle.
Ces ensembles sont des oracles proposés, pas des résultats calculés par un moteur
d'actions M2. Leur indicateur `no_benefit_ranking=true` est contrôlé.

### Totalité documentaire et précédence

Le produit des domaines applicabilité (3), méthode validée (2), couverture (3),
signal (4), contrôle de contradiction (3) et indépendance (2) donne **432 états
par famille**, hors variantes de documents/géométries/périodes. Les références
exigées sont renseignées explicitement comme SYNTHÉTIQUES pour cet audit logique.

La validation V0 en rejette 192 ; 240 sont admissibles. Les ensembles de
prédicats, après retrait des règles précédentes, donnent :

| V0 | A0 | A1 | A2 | A3 | A4 | A5 | A6 | A7 | A8 | Trou |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 192 | 80 | 32 | 104 | 6 | 2 | 1 | 6 | 2 | 7 | 0 |

Plusieurs prédicats peuvent être vrais : la partition vérifie la première
correspondance, et non leur exclusivité brute. A8 contient six états à signal
inconnu et un à absence non concluante avec contrôle non évalué malgré
indépendance attestée. La précision de sa formulation conserve les 52 oracles.
Ces 432 états d'actions ne sont pas les 576 combinaisons de la table D de priorité.

## Preuves suffisantes et limites de validation

Le schéma proposé n'accepte pas un simple `signal=etaye` et une référence libre
comme attestation normalisée. Les faits propres à R1, R2, R3, R4, leurs preuves,
méthodes, sources, périodes et emprises doivent être présents. Les contrôles
référentiels et scientifiques restent obligatoires : résoudre les IDs et vérifier
la même affirmation, les versions approuvées et les preuves courantes. Le schéma
ne démontre pas la véracité d'une revue humaine.

Les tests distinguent une capacité positive locale d'une complétude globale :
un inventaire incomplet peut contenir une observation positive contrôlée. Il ne
justifie pas une absence documentée. Les périodes doivent être compatibles et les
thèmes/catégories/sous-trames nécessaires couverts pour la conclusion négative.
La priorité d'examen n'est pas admise comme entrée et aucun score de gain n'est
déclaré. Une entrée en attente peut garder des IDs de diagnostic vides et des
manquants explicites, sans fabriquer une couche M1 ou une non-applicabilité.

Les contrôles de structure négatifs couvrent : mauvais appariement, version de
règle inconnue, booléen pris pour ID, références absentes, signal/couverture
incohérents, mauvais faits familiaux, qualification R1 incompatible, absence sans
attestation négative et tentative de promouvoir une attente M1.

## Fichiers créés ou modifiés

Créés :

- `docs/schema_actions_m2.json` : schéma interne proposé, distinct des GeoJSON.
- `tests/test_m2_action_rule_contract.py` : 88 tests documentaires et de contrat.
- `docs/transfert_actions_m2_m4.md` : coordination M4/M5.
- `docs/audit_actions_m2.md` : ce compte rendu.

Modifiés :

- `docs/regles_actions_m2.md` : précautions, profils, audit, portée des références.
- `docs/rules_actions.json` : types, prédicats, gardes, erreurs et contrôle familial proposés.

Le fichier `tests/fixtures/m2/action_rule_cases.json` et tous les fichiers
préexistants au travail initial (dont tout `analysis/` et les contrats GeoJSON)
conservent leurs empreintes. Aucun test préexistant n'a été neutralisé ou modifié.

## Décisions restantes et remise M4 / M5

- **M1/M2** : confirmer champs et dictionnaires, versions et périodes, précision,
  couvertures, catégories et sous-trames ; approuver les méthodes de lacune,
  voisinage et contexte hydrologique sans seuil par défaut. Les adaptations
  scientifiques R2–R4 ne sont pas déclarées actives.
- **M5** : confirmer A04/A01/A03/A02 et les fiches source de vérité ; aucune
  substitution ni validation de catalogue n'a été prétendue.
- **M4** : accepter le schéma proposé, implémenter l'unique moteur et ses contrôles
  référentiels, reproduire les 52 cas et deux multis, puis les compléments de
  preuves et oracles détaillés après revue commune. Les tests M2 ne s'y substituent pas.
- **Diffusion** : revoir la liste d'autorisation publique et les droits. Les preuves
  brutes, avis privés, références internes et géométries sensibles ne sont pas
  recopiés automatiquement. Aucun fichier `data/public/` n'est produit.

La [note de transfert](transfert_actions_m2_m4.md) donne le format, les quatre
statuts, justifications, erreurs et limites nécessaires. Le socle documentaire
est implémentable en TEST ; la recette réelle nécessite les validations ci-dessus.

## Audit-2 — reprise et consolidation du 4 novembre 2026

**Verdict : contrat interne renforcé, proposé à M4 pour implémentation et revue.
Aucune méthode écologique réelle, attestation de production ou diffusion publique
n'est validée.** La version des règles reste `m2-actions.spec-proposal-1`, avec
`contract_revision=audit-2`. Les associations provisoires R1→A04, R2→A01,
R3→A03, R4→A02 restent soumises à M5. Aucun PRD ni catalogue absent n'est validé.

### État vérifié après la coupure

La branche était `feat/diagnostics-ecologiques`. Le script temporaire
`/private/tmp/consolidate_action_facts_audit2.py` existait intégralement, mais sa
syntaxe était invalide : une accolade manquante dans la garde d'absence provoquait
un `SyntaxError` avant toute exécution. Les deux JSON étaient syntaxiquement
valides et identiques aux empreintes enregistrées avant l'interruption ; le
dictionnaire n'existait pas. **Le script n'avait donc pas exécuté les écritures
prévues.** Il a été lu intégralement, corrigé et compilé syntaxiquement avant son
exécution, après sauvegarde des deux JSON audit-1 dans `/private/tmp/`. Il n'a pas
été relancé à l'aveugle.

À la reprise, les six fichiers demandés étaient présents : spécification,
contrat JSON, schéma, transfert, 88 tests et fixtures 52+2. Le compte rendu
audit-1 existait aussi. Les modifications antérieures de détection/priorisation,
les autres documents et tests locaux étaient présents et ont été conservés.
Le travail audit-2 déjà réalisé avant la reprise se limitait à l'inspection,
la reproduction des cinq défauts, la suite de référence à 1 095 tests et la
préparation du script. Aucun des trois documents que ce script devait écrire
n'avait encore changé.

### Défauts confirmés et contraintes terminées après reprise

| Instance avec `valeur=false` | Audit-1 | Audit-2 |
| --- | --- | --- |
| R1 étayée, `sous_trame_documentee` | Acceptée | Refusée : objet sous-trame requis et pertinence établie pour l'étayage |
| R2 étayée, `analyse_lacune_documentee` | Acceptée | Refusée : analyse structurée et conclusion `declencheur_etabli` requises |
| R3 étayée, `lien_geometrique_continuite` | Acceptée | Refusée : objets liés, méthode/référence et conclusion établie requis |
| R4 étayée, `analyse_isolement_documentee` | Acceptée | Refusée : analyse structurée et conclusion établie requises |
| Signal d'absence, `absence_declencheur` | Acceptée | Refusée : affirmation négative strictement vraie requise |

Ces cinq acceptations puis refus ont été reproduits contre les deux versions de
schéma conservées, sur les mêmes objets synthétiques modifiés. Aucun résultat A
attendu n'a été réécrit pour les obtenir.

Le schéma lie désormais 22 noms de faits à leurs types exacts : inventaire daté,
source versionnée, réseau référencé, relation géométrique, méthode, conclusion
externe, sous-trame, contexte des sols/hydrologie ou booléen QA/négatif. Les types
et tous leurs champs admissibles sont décrits dans le
[dictionnaire des faits](dictionnaire_faits_actions_m2.md). Les codes officiels
restent à résoudre dans les dictionnaires M1, jamais inventés ici.

`documente` exprime la traçabilité. Une analyse peut être documentée et conclure
`indice_documente`, `declencheur_absent` ou `indetermine` ; elle n'étaye alors pas
le signal positif. Les inconnues et non-applicabilités de fait sont nulles, ces
dernières avec preuve de domaine. Les faits des autres familles sont refusés.
Les conditions propres à l'étayage complètent les six faits documentés :
qualification et QA R1, pertinence des sous-trames, conclusions de lacune ou
relation établies, adéquation hydrologique et rattachement au pilote. Aucun
seuil numérique ni calcul écologique nouveau n'est introduit.

Une absence demande `absence_declencheur=true` à l'état `absence_documentee`,
preuves négatives, méthode déclarée validée et couvertures validées pertinentes.
`false` signifie que cette absence n'est pas établie ; il ne prouve pas une
présence. `null` demeure une inconnue. Ces gardes portent sur `normalizedInput` :
le profil abstrait des fixtures et les prédicats de la table ne sont pas modifiés.

### Ce qui reste un contrôle M4

Les **douze contrôles `REF_*`** du JSON sont des obligations bloquantes : maille,
diagnostics, preuves, famille, objets/phénomènes, méthodes, emprises, périodes,
résultat, diffusion, couvertures et unicité des décisions. Les tests montrent
notamment que des IDs bien typés mais discordants, une version inconnue, des
références de méthode discordantes, des sources d'une autre période, une
couverture disjointe ou des ensembles thématiques incomplets peuvent rester
acceptés structurellement. Cela constitue une limite explicitement démontrée,
pas un contrôle M4 déjà réalisé.

Le schéma refuse les mauvais types, champs, familles et appariements, dates
invalides avec `FormatChecker`, états et conclusions locales incompatibles.
Il ne compare pas arbitrairement les valeurs de deux objets. M4 doit résoudre
les registres, comparer les identités typées et les liens, vérifier les preuves
et leur polarité, les géométries et l'empreinte courante R1. La compatibilité des
versions/sous-méthodes, périodes et domaines dépend des méthodes approuvées ;
une égalité textuelle imposée partout serait incorrecte. Les références de
couverture plus large sont acceptables seulement si leur portée est suffisante.

### Résultat et diffusion proposés

`actionResult` formalise les IDs en tableaux conservant entiers et chaînes,
versions, règle/action, l'un des quatre statuts, code A, motif principal lié au
code, justification, preuves positives et négatives, attestations, conflits,
limites/prérequis, méthode, qualité et état déclaré de validation. M4 doit
préserver les grands entiers sans perte et l'unicité typée des décisions dans
un lot. Le schéma d'un objet ne contrôle pas ce lot.

Les résultats favorables ou non retenus nécessitent une référence de contrôle
référentiel et une attestation. A7 conserve preuves négatives et qualité
suffisante. A1 conserve les preuves de domaine sans imposer une méthode
écologique active : sa précédence avant A2 est respectée. Un état déclaré de
contrôle ne prouve pas la réalité de la revue et `authentifie_par_logiciel`
reste faux. Le schéma ne sélectionne pas la règle gagnante sur les entrées.

`actionValidationError` est distinct de tous les résultats d'action. V0 et
`ERREUR` ne constituent aucun cinquième statut. M4 doit traduire les violations
en codes et détails, puis exécuter seul la table A sur les entrées admissibles.

`actionPublicProjection` refuse les champs privés par liste d'autorisation
fermée. Elle se construit explicitement après validation interne et revue des
droits/textes. Un texte libre peut encore contenir une référence privée : le
schéma ne détermine pas sa confidentialité, ce que les tests montrent aussi.
Aucun résultat interne, avis privé ou preuve n'est publié automatiquement.

### Tests et non-régression

| Vérification | Réussis | Échecs | Erreurs | Ignorés | Avertissements |
| --- | --- | --- | --- | --- | --- |
| Référence avant audit-2 | 1 095 | 0 | 0 | 0 | 38 |
| Suite finale complète audit-2 | **1 308** | **0** | **0** | **0** | **38** |
| Dont nouveaux tests audit-2 | **213** | 0 | 0 | 0 | 0 |

Commande effectivement exécutée :

```sh
/private/tmp/reconnect-m2-audit2-venv/bin/python -m pytest -q tests/ --junitxml=/private/tmp/m2-actions-audit2-final.xml
```

Durée pytest : **15,21 s**. L'environnement temporaire a été recréé séparément
car l'ancien répertoire n'était plus un environnement virtuel utilisable. Les
38 avertissements restent les dépréciations pyproj/NumPy : 6 dans les tests de
conflits et 32 dans les tests GeoJSON ; aucun avertissement supplémentaire ou
masqué. Aucune erreur, contradiction de test ou régression connue ne reste après
la suite finale. Les contrôles scientifiques/référentiels non implémentés restent
les prérequis M4/M1 explicités, pas des sécurités annoncées opérationnelles.

Les 88 tests audit-1 sont conservés. Seul leur constructeur
`normalized_example` a été adapté : les chaînes génériques sont remplacées par
des objets explicitement SYNTHÉTIQUES correctement typés. Aucune attente de
test antérieure n'est modifiée ou neutralisée. Ces déclarations de forme,
notamment les références d'approbation synthétiques, ne sont ni des preuves
officielles ni des contrôles scientifiques exécutés. Les tests vérifient aussi
qu'une structure correcte peut être acceptée et qu'elle ne suffit pas à prouver
les liens référentiels.

Le nouveau fichier couvre les cinq contre-exemples et nulls, booléens inadmissibles,
faits documentés défavorables, inconnus/non applicables, absences, discordances
interobjets, versions/références, profils de sortie, couplage A/statut/motif,
IDs typés, séparation public/interne et maintien de l'attente M1. Aucun moteur
d'actions, SIG réel ou preuve de terrain n'est exécuté ou créé.

Les empreintes enregistrées avant la coupure confirment la conservation de tout
`analysis/`, des contrats GeoJSON proposal-1/proposal-2, des tables D/S et des
tests antérieurs hors constructeur précisé. Les 52 oracles et deux multis sont
inchangés **octet pour octet** ; la table A est inchangée structurellement.

- SHA-256 fixtures : `df13d94ed790308231dd9f75b64771ea7101300c4d9b427671b7c9ddc1a890e9`.
- SHA-256 table `shared_precedence` en JSON canonique (clés triées, UTF-8,
  séparateurs compacts) : `0a5242c4a95daab3974542174c82a6db9d265cf54178ba3925e8d94cfc76504e`.

### Fichiers de revue et décisions restantes

| Fichier | Changement audit-2 |
| --- | --- |
| [schema_actions_m2.json](schema_actions_m2.json) | Faits nommés typés, contraintes par famille/signal, trois profils de sortie |
| [rules_actions.json](rules_actions.json) | Sémantique des faits, contrôles interobjets, limites, profils et liste publique ; table A conservée |
| [dictionnaire_faits_actions_m2.md](dictionnaire_faits_actions_m2.md) | Nouveau dictionnaire des types, sens, valeurs, acceptation et blocages réels |
| [regles_actions_m2.md](regles_actions_m2.md) | Révision courante, sémantique et portée des validations |
| [transfert_actions_m2_m4.md](transfert_actions_m2_m4.md) | Recette M4, choix des profils, contrôles et diffusion |
| [test_m2_action_rule_contract.py](../tests/test_m2_action_rule_contract.py) | Constructeur synthétique adapté, 88 tests et attentes conservés |
| [test_m2_action_facts_audit2.py](../tests/test_m2_action_facts_audit2.py) | Nouveaux contre-exemples et contrats de sortie |
| [audit_actions_m2.md](audit_actions_m2.md) | Historique audit-1 et présent bilan de reprise |

Transmettre ces huit fichiers et les
[fixtures inchangées](../tests/fixtures/m2/action_rule_cases.json) pour revue
indépendante. Les JSON se valident avec le profil `$defs` concerné ; le `$ref`
racine historique vers `commonInput` ne valide pas l'entrée normalisée réelle.

**M1/M2** doivent encore livrer/valider nomenclatures, sources, millésimes,
précision, emprises et couvertures. Les méthodes de lacune bocagère, voisinage
friche–continuité, isolement et adéquation hydrologique doivent expliciter domaine,
paramètres, périodes et preuves reproductibles. La QA courante R1 et les
recherches négatives doivent être effectivement contrôlées. Sans ces éléments,
l'étayage réel R2–R4 et les absences réelles restent bloqués.

**M4** doit accepter le dictionnaire, les trois profils, versions, états de
validation, erreurs et douze obligations référentielles, puis implémenter seul
le moteur et ses contrôles. Sa recette devra démontrer les refus référentiels
réels et reproduire les 52+2 oracles sans inventer leurs attentes manquantes.
**M5** doit confirmer IDs, fiches et prérequis du catalogue ; rien de cela n'est
prétendu vérifié ici. La politique de diffusion reste à approuver avant usage
public. Aucun commit, push, export public ou changement de remote n'a été réalisé.
