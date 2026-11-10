# Vérification préliminaire de la spécification M2 — 3 novembre 2026

**Portée :** fichiers de spécification et exemples synthétiques préparés hors du dépôt local de l'équipe. **Ce contrôle n'est pas une exécution de la suite pytest du projet**, ni une validation écologique sur la Normandie.

## Vérifications exécutées

- Lecture et sérialisation du JSON avec interdiction de NaN/Infinity : **OK**.
- **38 scénarios** synthétiques avec résultats attendus détaillés : 34 sorties de décision, 4 erreurs bloquantes attendues. **38/38** conformes à un vérificateur de référence isolé.
- Vérification explicite de la règle D, du motif principal, de la règle S, des identifiants justificatifs/non évalués, des familles manquantes, de la priorité et de la complétude décisionnelle.
- Vérification des liens synthétiques des scénarios T16 (source partagée) et T34 (phénomène partagé).
- Énumération des **576 combinaisons** des six paramètres catégoriels déclarés : **432 admissibles**, **144 rejetées explicitement par invariants**, **0 combinaison admissible sans règle** selon la spécification proposée.
- Cas de bord : T09 = indéterminé *et* couverture décisionnelle complète ; T26 = absence incohérente bloquée ; T30 = hors territoire sans priorité ; T22 = toutes familles non applicables sans faux vert ; T23 = famille attendue absente sans faux vert.

## Limites du contrôle

1. Les oracles ont été rédigés à partir de la même convention de décision que la table : leur cohérence ne prouve pas la validité écologique ou la pertinence des catégories de priorité.
2. L'énumération ne couvre **que** 576 combinaisons de six champs. Elle ne couvre pas toutes les géométries, périodes, documents de preuve ni configurations multi-familles.
3. Le code local de l'équipe et les 223 tests déclarés par Codex n'ont pas été exécutés dans cet environnement. Codex devra refaire tous les tests, sur la branche de M2, et signaler tout résultat divergent.
4. Les décisions de classification des enjeux et de qualification des conflits sont volontairement ouvertes jusqu'à inspection des données M1 et validation des critères par l'équipe.
5. `couverture_synthese=complete` signifie **complétude décisionnelle dans le périmètre**, pas couverture SIG exhaustive : conserver séparément les preuves spatiales de couverture.

## Contrôle de livraison attendu de Codex

- Refaire pytest sur l'environnement isolé : ne pas annoncer des tests « réussis » sans les exécuter.
- Tester les 576 combinaisons, les 38 scénarios, la monotonie conditionnelle, l'invariance à l'ordre, les doublons, les familles manquantes, la non-applicabilité et les contradictions.
- Identifier les cas bloquants et les cas résiduels par code.
- Comparer les sorties au contrat M2→M4 existant sans modifier silencieusement `proposal-1`.
- Distinguer la validation algorithmique de l'acceptation méthodologique par M1/M2/M4 et de la vérification manuelle de trois zones réelles.
