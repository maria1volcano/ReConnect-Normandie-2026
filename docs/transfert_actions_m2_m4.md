# Transfert M2 → M4 / M5 — correspondances d'actions

**Proposition structurelle prête pour revue et implémentation du socle M4 sur
fixtures ; activation scientifique réelle non autorisée.** Version
`m2-actions.spec-proposal-1`, révision technique `audit-2`. Le PRD et le catalogue
M5 ne sont pas présents localement et ne sont pas considérés validés. La référence
PRD déclarée par le pack n'a pas été certifiée. Les IDs suivants restent
provisoires, conformément à l'instruction M2 :

| rule_id | action_id | Famille |
| --- | --- | --- |
| R1 | A04 | Passages à faune / ouvrages |
| R2 | A01 | Haies / continuités bocagères |
| R3 | A03 | Renaturation de friches |
| R4 | A02 | Mares / réseaux de mares |

M5 confirme ces appariements et les douze fiches avant branchement. A05–A12 restent
consultables et documentaires, sans déclenchement automatique ni rang d'efficacité.

## Entrées et exécution

Lire [rules_actions.json](rules_actions.json), [la spécification](regles_actions_m2.md),
le [dictionnaire des 22 faits](dictionnaire_faits_actions_m2.md)
et [schema_actions_m2.json](schema_actions_m2.json). Ce dernier est un schéma
**interne proposé**, sans modification des contrats GeoJSON proposal-1/proposal-2.

- `commonInput` sert uniquement à l'audit des 52 fixtures abstraites : champs
  catégoriels, appariements, références et invariants V0. Une référence textuelle
  `family_evidence` ne devient pas une preuve scientifique.
- `normalizedInput` est proposé pour l'intégration M2/M4 : maille et diagnostics
  typés, `rule_version`, faits familiaux, sources et méthodes versionnées, emprise,
  périodes, couvertures, preuve positive/négative, attestation M2 et limites.
- `pendingEvidence` permet de déclarer les données M1 manquantes, avec un signal
  inconnu et sans source ni diagnostic fictif. `domainEvidence` documente une vraie
  non-applicabilité ; il ne remplace pas une couche absente.

`priorite_examen` est interdite comme entrée de règle. M4 applique V0 puis A0–A8
par première correspondance. A0 protège contre une contradiction pertinente avant
A1. A8 est limitée aux deux cas résiduels explicités, sans « sinon » universel.
Un couple `(maille_id, rule_id)` est unique ; plusieurs preuves peuvent soutenir
une même action, et les quatre actions sont conservées séparément dans une maille.

Avant une sortie favorable, M4 doit vérifier ou recevoir une attestation M2
contrôlée : existence et concordance des sources/preuves, même maille et phénomène,
emprise et périodes compatibles, méthode/version approuvée pour cette famille,
faits effectivement soutenus, couvertures pertinentes, preuve courante. Pour R1,
réutiliser la QA existante, son registre contextuel approuvé et l'empreinte de
l'événement. Le schéma seul ne réalise pas ces contrôles et n'authentifie aucun avis.
Aucun adaptateur scientifique R2–R4 ne doit être déclaré actif sans validation M1/M2.
Une preuve positive locale peut soutenir l'étude sans certifier l'exhaustivité
globale d'un inventaire ; une conclusion négative nécessite les couvertures
validées pertinentes. Ne pas convertir automatiquement un statut SIG en
`couverture_essentielle`.

Les valeurs libres audit-1 ne sont plus admises. `documente` ne signifie pas
« déclencheur satisfait » : les analyses externes portent une conclusion nommée,
les sous-trames une pertinence, et les sources/réseaux/relations une structure.
`absence_declencheur=true` est une affirmation négative ; `false` ou `null` ne
permettent aucune absence documentée. Les faits inconnus restent nuls.

Valider explicitement le profil, avec JSON Schema 2020-12 et un vérificateur de
formats : le `$ref` racine historique désigne `commonInput`, pas l'entrée réelle.
Par exemple, construire un schéma avec les mêmes `$defs` et
`$ref=#/$defs/normalizedInput`. Sélectionner de même les profils de sortie.
Valider seulement `familyEvidence` ne suffit pas : les contraintes par famille
et signal se trouvent aussi dans `normalizedInput`.

### Contrôles référentiels bloquants à implémenter par M4

Les douze obligations `rules_actions.json.interobject_checks` font partie de la
recette, même quand JSON Schema accepte la structure. M4 doit :

- Comparer les mailles et ensembles de diagnostics en conservant leur type,
  résoudre chaque preuve et vérifier ses liens et sa polarité ; contrôler les
  objets, phénomènes et familles réellement concernés.
- Résoudre les méthodes/versions dans le registre approuvé, leur domaine et
  leurs sous-méthodes autorisées. Une chaîne non vide ou une version inconnue
  n'est pas une approbation. Des sous-méthodes différentes ne sont pas interdites
  si leur composition est approuvée.
- Contrôler les géométries, inclusions et emprises, l'ordre et la compatibilité
  des périodes, les catégories/sous-trames requises et couvertes. Ni l'égalité
  textuelle systématique des emprises/périodes ni un tampon ou délai arbitraire
  ne remplace ces contrôles.
- Relier chaque résultat aux entrées contrôlées, appliquer V0 puis la première
  règle A admissible et refuser les doublons typés `(maille_id, rule_id)` du lot.
  Conserver les quatre familles sans classement ni fusion de phénomènes.
- Construire explicitement la projection publique après contrôle des droits,
  de la sensibilité et du contenu des textes.

`schema_support` décrit la comparaison concernée : `non` ne signifie pas que
ses champs n'ont aucun type. Par exemple, les dates ont un format mais leur ordre
et leur compatibilité ne sont pas vérifiés. Les tests audit-2 montrent des
discordances encore acceptées structurellement et les rattachent aux `REF_*` ;
aucun contrôleur M4 opérationnel n'est livré côté M2.

## Sorties

| Statut | Interprétation |
| --- | --- |
| `etayee_pour_examen` | Étude justifiée par un déclencheur vérifié ; aucune autorisation de travaux |
| `conditionnelle` | Piste documentée avec conditions précises restant à vérifier |
| `non_retenue_par_regle` | Non-applicabilité justifiée ou absence du déclencheur prouvée dans le périmètre |
| `non_evaluable` | Données, méthode ou preuves insuffisantes pour conclure |

Conserver `maille_id`, `rule_id`, `action_id`, versions, règle A retenue, motif,
preuves positives **et négatives**, conflits liés, attestation, limites et prérequis.
Les groupes de statuts servent à présenter plusieurs pistes, jamais à classer leur
rendement. Une non-évaluation n'est pas une conclusion négative.

Le profil `actionResult` formalise ces champs. Les identifiants sont des entiers
ou des chaînes non vides, jamais des booléens. Les listes `diagnostic_ids`,
`phenomene_ids`, `conflit_ids`, `preuve_ids`, `preuve_absence_ids` et
`attestation_ids` préservent `1` et `"1"` séparément ; ne pas les transformer en
clés d'objet JSON. M4 doit employer une lecture sans perte pour les grands entiers.
`methode` conserve identité/version/référence ; ses sous-méthodes restent
consultables par les attestations. `qualite` conserve couverture essentielle,
méthode déclarée validée et références de couverture. Les preuves du domaine A1
ne sont pas des preuves d'un déclencheur écologique positif.

`etat_validation=structure_seule` permet de porter un résultat non évaluable.
Les résultats favorables et non retenus exigent
`controle_referentiel_documente`, `validation_reference` et `attestation_ids`.
Ces champs sont déclaratifs : M4 vérifie le contrôle lui-même, pas seulement le
booléen ou la présence d'une référence. `authentifie_par_logiciel` reste faux.
Le couplage A/statut/motif est vérifié par le schéma ; la bonne sélection de A
sur les entrées reste à la charge du moteur M4. A1 n'impose pas une méthode
écologique active, car la non-applicabilité documentée précède A2.

Les erreurs V0 ne produisent pas de statut d'action. Le code global est
`E_ACTION_INPUT_INVALIDE`, détaillé par les codes de `validation_errors` : identité,
type, doublon, référence absente, signal/couverture incohérents, preuve familiale
invalide, discordance source/preuve ou trou de table. `ERREUR` n'est qu'un marqueur
historique d'oracle, pas un cinquième état public.
Le profil distinct `actionValidationError` conserve code et détails par champ,
sans `statut` d'action. Un refus structurel ne calcule pas lui-même le code fin :
la traduction des violations et des contrôles référentiels reste à M4.

## Recette et points ouverts

M4 doit reproduire les **52 cas inchangés** (40 décisions abstraites, 12 V0) et les
**2 cas multiproblèmes** de `tests/fixtures/m2/action_rule_cases.json`. Ces cas sont
SYNTHÉTIQUES : les preuves familiales sont des substituts, pas des observations.
Compléter ultérieurement, après revue M2/M4, les attentes précises de motifs,
limites, preuves et codes d'erreurs ; elles ne figurent pas dans les oracles actuels.
La conformité documentaire des tests M2 ne prouve pas l'exécution du futur moteur.

M1/M2 doivent encore approuver données, catégories/sous-trames, périodes,
couvertures, critères de lacune/voisinage/hydrologie et versions des méthodes.
M5 confirme les IDs et le contenu du catalogue. M4 valide le schéma interne et
implémente les contrôles référentiels puis l'unique moteur. Aucun seuil numérique
ni coefficient d'efficacité n'est livré par défaut.

Pour l'affichage public : IDs règle/action, statut, motif et justification relus,
limites et prérequis publiables, versions et références publiques autorisées.
Les preuves brutes, références privées, localisations sensibles et attributs
sources complets restent internes. Utiliser la liste d'autorisation proposée dans
le JSON après revue des droits ; ne pas publier directement les résultats internes.

`actionPublicProjection` interdit les champs privés par liste fermée, y compris
preuves, attestations, géométries et références internes de validation. La
politique de diffusion et sa revue sont déclarées ; JSON Schema ne contrôle ni
les droits ni la confidentialité d'une phrase libre. Les textes publiables
doivent donc être relus. Aucun export public n'est généré par ce chantier.

## Acceptation d'audit-2

M4 doit accepter les 22 sémantiques de faits et leurs valeurs, les trois profils
de sortie, les états de validation, les douze contrôles `REF_*`, les erreurs et
la politique de projection. La recette d'exécution M4 doit compléter les tests
documentaires M2 avec de vrais registres et des discordances interobjets rejetées.
Les méthodes R2/R3/R4, les dictionnaires et les données M1 restent des prérequis
scientifiques bloquants ; aucun test synthétique ne les approuve. M5 doit encore
confirmer les quatre correspondances provisoires et les fiches catalogue.
