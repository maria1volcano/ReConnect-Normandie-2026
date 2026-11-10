# ReConnect Normandie V6.1 — Spécification M2 des priorités d'examen

**Identifiant :** `m2-priorites.proposal-2`  
**Date :** 2026-11-03  
**Statut :** proposition de méthode, **non validée sur des données réelles** ; cette version remplace `m2-priorites.proposal-1` pour les tests de développement, pas pour la production.  
**Objet :** décision territoriale explicable ; **ni** efficacité d'action, **ni** urgence temporelle, **ni** score écologique universel.

## 1. Décisions stables du MVP V6.1

1. Une maille, plusieurs diagnostics spécialisés, une seule priorité synthétique (`elevee`, `moderee`, `faible`, `indeterminee`) ; `hors_territoire` n'est **pas** une priorité.
2. Conserver les deux GeoJSON liés (`mailles.geojson`, `conflits.geojson`), plus `fiches_zones.json` M2 et `catalogue_actions.json` M5. Le moteur de règles d'action appartient à M4 ; M2 rédige les règles versionnées R1–R4 ; douze fiches restent dans le catalogue M5. Aucune « meilleure solution » ni rang d'efficacité.
3. Pas de somme, moyenne, pondération ou bonus lié au nombre d'observations : une même route peut étayer plusieurs mesures, mais n'apporte pas deux preuves indépendantes de rupture.
4. Un croisement 2D n'est pas un obstacle écologique confirmé. Aucune absence n'est inférée d'une couche dont la couverture est inconnue.
5. Le mot **faible** signifie : « aucun signal justifiant une priorité d'examen supérieure selon **les familles réellement couvertes par la méthode déclarée** ». Il ne signifie jamais « biodiversité faible », « milieu sans valeur » ou « absence de tous les risques ». L'interface affiche aussi `aucun_signal` lorsque l'absence des signaux étudiés est établie.
6. Priorité et complétude **décisionnelle** sont deux dimensions distinctes : une maille peut être `elevee` avec `couverture_synthese=partielle` ou `indeterminee` avec `couverture_synthese=complete`. **`complete` signifie ici que les diagnostics attendus sont suffisamment qualifiés pour la table D/S ; cela ne certifie pas l'exhaustivité SIG des sources.** Les statuts et emprises de couverture SIG restent stockés dans `qualite` et `fiches_zones.json`.

## 2. Périmètre scientifique : familles attendues et familles exploratoires

- Avant tout calcul territorial, déclarer une **configuration de pilote versionnée** comprenant : `territory_id`, `grid_version`, `priority_method_version`, `familles_attendues`, références des méthodes autorisées par famille, date/approbateur de la décision et limites d'applicabilité.
- `familles_attendues` contient **uniquement les familles dont la méthode de traduction en signal commun a été explicitement validée** ; ce choix est arrêté avant de regarder la distribution des couleurs. On ne retire **jamais** automatiquement une famille attendue parce que ses données manquent dans une maille : cela entraîne une évaluation partielle.
- Les autres familles sont `exploratoires` : elles peuvent alimenter `diagnostics[]` et les fiches de zone, mais **pas** les règles S de couleur. Ne pas les passer artificiellement comme « non applicables ». Leur statut exploratoire doit être visible dans la méthodologie et sur l'interface de portée des résultats.
- La première famille prioritaire à documenter est `route_corridor` ; ce choix de développement ne valide pas automatiquement les autres familles (`pression_route`, `bocage`, `mares`, `friches`). Dans les **fixtures exclusivement synthétiques**, ces autres familles peuvent être activées par configuration pour tester la généricité des règles.
- Une famille attendue est applicable à une maille seulement si une **règle de domaine documentée** le conclut. L'absence de couche n'autorise jamais `non_applicable_documentee`.
- Si le périmètre est limité à `route_corridor`, la carte devra être légendée « priorité d'examen selon les croisements route–corridor étudiés », et non « priorité écologique exhaustive en Normandie ».

## 3. Entrées et provenance

### 3.1 Entrée maille

| Champ | Type / sémantique |
|---|---|
| `maille_id` | chaîne non vide ou entier ; type préservé |
| `study_area_m2` | nombre fini >= 0 ; **0** -> `hors_territoire` (S0) |
| `familles_attendues[]` | liste non vide, unique, issue du périmètre pilote versionné ; pas de déduction d'après les résultats |
| `diagnostics[]` | zéro ou plusieurs diagnostics ; plusieurs diagnostics d'une même famille sont possibles |
| `priority_method_version` | version de la méthode D/S ; distincte des versions des sources SIG |
| `territory_id`, `grid_version`, `dataset_version` | références versionnées, inconnues conservées null avec motif de traçabilité si nécessaire |

### 3.2 Entrée par diagnostic attendu

| Champ | Domaine | Responsable du calcul/contrôle |
|---|---|---|
| `diagnostic_id` | identifiant unique de diagnostic dans la maille | M2 |
| `famille_id` | famille **attendue** dans le périmètre courant | Configuration M2 |
| `applicabilite` | `oui`, `non_applicable_documentee`, `inconnue` | Adaptateur par famille M2 |
| `applicabilite_reference` | chaîne non vide **si** `non_applicable_documentee` ; null sinon | Référence de domaine M1/M2 |
| `enjeu_classe` | `fort`, `moyen`, `faible`, `inconnu` | Méthode d'enjeux M2, à valider sur attributs M1 |
| `enjeu_methode_id` | chaîne non vide si enjeu connu ; null autorisé seulement comme défaut à qualifier D2 | Méthode M2 |
| `signal_pression` | `obstacle_confirme`, `conflit_potentiel`, `croisement_detecte`, `absence_validee`, `non_concluant`, `non_evalue` | Adaptateur de diagnostic M2 |
| `validite_positive` | booléen : **capacité à soutenir une observation positive**, sans présumer que l'événement est observé | QA positif M2 |
| `validite_absence` | booléen : **capacité documentaire à conclure à une absence** dans le périmètre considéré | QA couverture M2 |
| `contradiction_bloquante` | booléen : divergence documentée non résolue sur la **même affirmation**, même objet/emprise et période compatible | Contrôle de cohérence M2 |
| `contradiction_reference` | référence obligatoire lorsque `contradiction_bloquante=true` ; sinon null | Contrôle M2 |
| `motifs_qualite[]` | liste de codes normalisés avec liens vers les preuves ; aucune erreur silencieuse | QA M2 |
| `preuve_ids[]` | références d'événements/documents validés ; obligatoires pour signal positif **exploitable** | QA M2 |
| `phenomene_id` | identifiant de mécanisme, si disponible | Adaptateur M2 |
| `source_objects[]` | couples `namespace`/`id` si disponibles | M1/M2 |
| `periode_reference` | période/référence si pertinente, null sinon avec limite si nécessaire | M1/M2 |
| `methode_famille_id` | méthode versionnée d'adaptation de la famille | M2 |

**Important :** `validite_positive` et `validite_absence` sont des *capacités de preuve*, pas des assertions opposées. Les deux peuvent être `true` pour une source complète ayant effectivement observé un conflit. En revanche `signal_pression=absence_validee` accompagné de `validite_absence=false` est **contradictoire** et doit être bloqué.

### 3.3 Contrôles bloquants (avant D/S)

- `E_ID_DUPLIQUE`, `E_FAMILLE_HORS_PERIMETRE`, `E_TYPE_INVALIDE`, `E_SURFACE_INVALIDE` (négative, NaN, infinie), `E_PERIMETRE_INVALIDE` (configuration absente, listes dupliquées), `E_REFERENCE_NON_APPLICABILITE` (non applicable sans justification), `E_ABSENCE_INCOHERENTE` (`absence_validee` et `validite_absence=false`), `E_CONTRADICTION_SANS_REFERENCE` (booléen vrai sans justification), `E_PROUVE_POSITIVE_SANS_SOURCE` (signal positif *validé* mais aucune preuve identifiable), `E_NON_APPLICABILITE_INCOHERENTE` (signal positif sur diagnostic déclaré non applicable).
- `enjeu_classe` connu mais `enjeu_methode_id=null` n'est **pas** une preuve d'enjeu valide : le diagnostic retourne D2 avec motif `methode_enjeu_absente` ; en production, l'adaptateur doit signaler cette anomalie.
- Si une famille attendue n'a aucun diagnostic, **ne pas créer** de diagnostic fictif et ne pas inventer un identifiant : ajouter `famille_attendue_absente` au motif synthétique et inscrire cette famille dans les `familles_manquantes` de la fiche détaillée.
- Les champs facultatifs manquants dans les anciennes fixtures synthétiques peuvent être normalisés explicitement pour **les tests uniquement**, jamais imputés sur les données réelles. Les sources synthétiques ne prouvent aucune qualification réelle.
- En cas de surface égale à zéro : S0 (`priorite_examen=null`, `couverture_synthese=null`) ; refuser toutefois les identifiants/valeurs mal formés si des diagnostics sont fournis.

## 4. Conditions amont : produire les capacités, pas les inventer

**A. Qualification positive.** Pour `croisement_detecte`, exiger géométrie d'intersection non vide en EPSG:2154, lien source vérifié, adéquation à l'échelle, précision adaptée à l'affirmation et provenance. Un simple croisement ne devient jamais automatiquement `conflit_potentiel`. Pour `conflit_potentiel`, exiger en plus une règle contextuelle versionnée *validée* ou une preuve externe documentée reliée à `conflit_id`. Pour `obstacle_confirme`, exiger une preuve externe pertinente, traçable et une incertitude de localisation résolue. Ce moteur de QA ne doit pas authentifier une expertise humaine par simple présence d'un champ texte.

**B. Absence documentée.** Exiger analyse réalisée, aucune observation pertinente selon la méthode, couches indispensables et sous-trames sélectionnées couvertes, complétude spatiale/thématique `validated` sur `H∩T`, périodes pertinentes. Le zéro `nb_evenements_observes=0` **ne suffit pas**. Si ces conditions ne sont pas réunies, utiliser `non_evalue` avec motif `absence_non_demontree`, jamais `absence_validee`.

**C. Contradiction.** Construire un contrôle M2 qui compare des assertions identifiables : type d'affirmation, objet/événement ou géométrie pertinente, emprise, période, sources et qualification. `contradiction_bloquante=true` seulement pour des assertions incompatibles après harmonisation de ces dimensions. Une couche sans signal n'est pas, à elle seule, une assertion d'absence validée ; la coexistence route dense + croisement n'est pas une contradiction. Conserver les références contradictoires et la règle de détection. Les incohérences non résolues affectent uniquement les diagnostics concernés.

**D. Applicabilité et enjeu.** Une famille n'est pas « non applicable » parce qu'une source manque. `fort/moyen/faible` n'est attribué que selon un mapping M1→M2 identifié par `enjeu_methode_id` ; aucune traduction automatique « réservoir=fort, corridor=moyen » ni seuil universel n'est activée avant validation sur données M1.

**Découpage du code :** le moteur de D/S reçoit des diagnostics **déjà normalisés**. Un adaptateur/validateur M2 distinct produit, justifie et contrôle les capacités ; en absence de données M1, n'implémenter que les contrôles génériques et interfaces avec stubs explicites, jamais de règles de qualification réelle simulées comme étant de production.

## 5. Table D — Décision par diagnostic (première règle applicable)

Les règles D sont exécutées **après** les invariants bloquants. Elles retournent toujours `signal_diagnostic` + `regle_D` + `motif_principal` + `motifs_qualite` conservés. `indetermine` n'est pas un ordre numérique. Les comparaisons d'enjeu portent sur un domaine **catégoriel**, jamais sur un score implicite.

| Précédence | Condition | `signal_diagnostic` | `motif_principal` |
|---|---|---|---|
| `D0` | `applicabilite=non_applicable_documentee` et référence valide | `hors_champ` | `non_applicabilite_documentee` |
| `D1` | `contradiction_bloquante=true` ou `applicabilite=inconnue` | `indetermine` | `donnees_contradictoires` ou `applicabilite_inconnue` (précédence interne : contradiction d'abord) |
| `D2` | `enjeu_classe=inconnu` ou `enjeu_methode_id` absent pour classe connue | `indetermine` | `enjeu_non_documente` ou `methode_enjeu_absente` |
| `D3` | `signal_pression=non_evalue` ou `non_concluant` | `indetermine` | `pression_non_evaluee` ou `preuve_non_concluante` ; conserver aussi `absence_non_demontree` si pertinent |
| `D4` | Signal positif (`obstacle_confirme`, `conflit_potentiel`, `croisement_detecte`) et `validite_positive=false` | `indetermine` | `preuve_positive_non_validee` |
| `D5` | Enjeu `fort` + (`obstacle_confirme` ou `conflit_potentiel`) exploitable | `eleve` | `conflit_etaye_enjeu_fort` |
| `D6` | Enjeu `fort` + `croisement_detecte` exploitable | `modere` | `croisement_non_qualifie_enjeu_fort` |
| `D7` | Enjeu `moyen` + l'un des trois signaux positifs exploitables | `modere` | `pression_observee_enjeu_moyen` |
| `D8` | Enjeu `faible` + (`obstacle_confirme` ou `conflit_potentiel`) exploitable | `modere` | `conflit_etaye_enjeu_faible` |
| `D9` | `absence_validee` + `validite_absence=true` + enjeu documenté | `faible` | `absence_pression_validee` |
| `D10a` | Enjeu `faible` + `croisement_detecte` exploitable | `indetermine` | `signal_non_qualifie` ; **couverture suffisante possible** |

**AUCUN D10 résiduel.** Toute autre combinaison *structurellement valide* non couverte constitue `E_TABLE_NON_TOTALE` : erreur de spécification bloquante (ne pas publier une couleur). Le cas `absence_validee` + `validite_absence=false` n'est **pas** une nouvelle règle D10b : c'est `E_ABSENCE_INCOHERENTE`. Il faut corriger le contrat de l'adaptateur, plutôt que transformer une contradiction formelle en gris.

Pour les motifs `donnees_contradictoires`, `applicabilite_inconnue`, `enjeu_non_documente`, `methode_enjeu_absente`, `pression_non_evaluee`, `preuve_non_concluante`, `preuve_positive_non_validee`, marquer un déficit de preuve/données. `signal_non_qualifie` est **interprétation non conclue à données complètes possibles**, non un déficit de couverture.

Les règles D5–D10a sont des **conventions de triage exploratoires à approuver** ; elles ne constituent pas une classification officielle ou un classement d'efficacité d'intervention.

## 6. Table S — Synthèse par maille, sans promotion

1. Si `study_area_m2=0` : `S0`, `priorite_examen=null`, `statut_analyse=hors_territoire`, `couverture_synthese=null`, listes justificatives vides.
2. Traiter chaque diagnostic attendu, vérifier les familles manquantes, **ignorer `hors_champ` seulement s'il est documenté**. Un diagnostic d'une famille exploratoire ne participe pas à la couleur.
3. `couverture_synthese=partielle` si au moins une famille attendue manque, a une applicabilité inconnue, ou contient un diagnostic indéterminé **pour motif de données, preuve ou méthode** ; sinon `complete`. `signal_non_qualifie` **seul** n'entraîne pas `partielle`. Cette métrique indique la **complétude des conclusions D/S dans le périmètre déclaré**, pas la couverture spatiale exhaustive des couches : un signal positif fiable peut être conclu sur source à couverture partielle, avec les limites de la source visibles séparément. Ne jamais présenter `complete` comme « toutes les données sont complètes ».
4. Appliquer les règles dans l'ordre :

| Rang | Condition | Priorité | Justificatifs |
|---|---|---|---|
| `S1` | >= 1 diagnostic exploitable `eleve` | `elevee` | Tous les `diagnostic_id` `eleve`, triés ; autres non évalués consignés |
| `S2` | Pas d'`eleve` et >= 1 diagnostic exploitable `modere` | `moderee` | Tous les `diagnostic_id` `modere`, triés |
| `S3` | >= 1 diagnostic `faible`, **toutes** les familles attendues représentées, et **tous** les diagnostics attendus applicables sont `faible` ou `hors_champ` documenté | `faible` | Tous les `diagnostic_id` `faible`, triés |
| `S4` | Aucun des cas précédents, y compris toutes les familles non applicables | `indeterminee` | Aucun ; motif explicite, par exemple `aucune_famille_applicable`, `famille_attendue_absente`, `signal_non_qualifie` |

- Plusieurs diagnostics `modere` ne deviennent pas `eleve`. Deux diagnostics d'une même famille dont un est faible et l'autre indéterminé **ne permettent pas S3**.
- `diagnostic_ids_non_evalues` inclut tous les diagnostics `indetermine`, même si le motif est `signal_non_qualifie` avec `couverture_synthese=complete`. Une **famille absente** n'ayant aucun `diagnostic_id`, sa trace est dans `motifs_limites` et `familles_manquantes` (détail M2).
- `motifs_limites` = union triée des motifs principaux et des limites QA affectant la lecture, plus les motifs synthétiques de S. Enregistrer par ailleurs l'association `diagnostic_id→regle_D/motif_principal` dans `fiches_zones.json`.
- Les listes sont triées de façon déterministe, sans conversion implicite des identifiants entiers en chaînes. La couleur exprime une **priorité d'examen**, jamais l'urgence.
- `eleve`/`modere`/`indetermine` appartiennent à la table D ; `elevee`/`moderee`/`indeterminee` à la table S. Le mapping est explicite, sans heuristique de suffixe.

## 7. Diagnostics liés et contradictions

- Conserver toutes les observations et l'intégrité `conflit_ids ↔ maille_ids`. Les relations plusieurs-à-plusieurs restent distinctes du nombre global d'événements.
- En MVP : collecter les `source_objects` et `phenomene_id` quand disponibles. Si deux diagnostics ont la même clé `namespace + id` ou `phenomene_id`, les signaler comme **liés** dans le détail, sans les supprimer et sans changer la couleur. Un recoupement de données seul ne prouve pas l'identité écologique du phénomène.
- Quand la traçabilité est insuffisante, retourner `relation_non_etablie` et non `independants`. L'analyse causale d'indépendance et la promotion multi-pressions sont **hors MVP**.
- Une contradiction porte sur la **même affirmation** à période et emprise compatibles, non sur la simple coexistence de diagnostics différents. Le QA en amont doit produire la référence documentée du conflit et mettre les diagnostics touchés en quarantaine (`D1`) sans affecter les signaux fiables non concernés.

## 8. Validation des tests (avant M1)

### 8.1 Cas synthétiques contractuels

- Utiliser `tests/fixtures/m2/decision_cases_m2.json` (version 2). Tester **toutes** les sorties explicites : règle D par diagnostic, priorité, règle S, couverture, justificatifs, non évalués, familles manquantes et motifs.
- Les cas `expected_error` doivent lever un **type d'erreur et un code stables**, sans publier de résultat partiel.
- Les fixtures sont un oracle de conformité **aux conventions**, non une validation de leur justesse scientifique. Relecture humaine des attentes indispensable.

### 8.2 Exhaustivité de la table D

Pour `enjeu_classe` (4) × `signal_pression` (6) × `validite_positive` (2) × `validite_absence` (2) × `applicabilite` (3) × `contradiction_bloquante` (2) = **576 combinaisons brutes**, compléter les références documentaires synthétiques requises (applicabilité, contradiction, méthode d'enjeu, preuves positives exploitables) **sans rendre valides des incohérences**.

- Pour chaque combinaison, déterminer les invariants bloquants **avant** D, puis vérifier soit un rejet explicite documenté, soit exactement une **règle sélectionnée par précédence**. Plusieurs prédicats peuvent être vrais, c'est la règle prioritaire qui décide.
- Confirmer qu'aucun cas admissible ne tombe dans `E_TABLE_NON_TOTALE`; ne pas utiliser de catch-all indéterminé.
- Compter distinctement : cas admissibles, cas bloqués par invariants, cas non couverts (doivent être 0). Ne pas affirmer que 576 cas représentent toutes les situations spatiales ou documentaires.
- Contrôler l'invariance à l'ordre et à la duplication des entrées, le statut `hors_territoire`, les familles manquantes, le cumul sans bonus, et la cohérence des motifs.
- Monotonie **conditionnelle** : à enjeu/méthode/qualité/applicabilité identiques, `conflit_potentiel → obstacle_confirme` ne diminue pas une priorité connue ; à signal/méthode/qualité identiques, `moyen → fort` ne la diminue pas. **Ne pas** ordonner `indeterminee` vis-à-vis de `faible` ni considérer `croisement_detecte` et `non_concluant` comme une échelle d'intensité.
- Tests d'intégration géométrique : CRS, union d'objets, couverture réelle sur `H∩T`, limites territoriales, preuve d'absence et références aux conflits, une fois couches M1 disponibles.

### 8.3 Validation écologique réelle

Dès réception de M1, vérifier manuellement **au moins trois secteurs réels contrastés**, avec sources et avis méthodologique indépendants des fixtures. Contrôler la distribution des couleurs comme diagnostic descriptif, **sans modifier les règles pour produire une carte artificiellement discriminante**. Enregistrer les décisions, leur date, les conflits de preuve et les versions.

## 9. Interface M3/M4 et livrables V6.1

- Contrat **actuel** `m2-m4.proposal-1` : inchangé, exclusivement données synthétiques, priorité `non_calculee` et `action_ids=[]`.
- Proposer à M3/M4 `m2-m4.proposal-2` (ne pas écraser silencieusement l'ancien) : `priorite_examen` comme objet `{etat, valeur}`, avec `etat` distinct pour `non_calculee`, `calculee`, `indeterminee`, `hors_territoire`, `valeur` = `elevee|moderee|faible|null` compatible ; `couverture_synthese=complete|partielle|null` ; `regle_appliquee` (S0–S4) ; `diagnostic_ids_justificatifs[]` ; `diagnostic_ids_non_evalues[]` ; `motifs_limites[]` de codes publics maîtrisés.
- `fiches_zones.json` : détail par diagnostic, `regle_D`, sources, preuves/règles versionnées, `familles_manquantes`, événements liés, limites, périodes et statut de preuve. Ne pas exposer les références privées dans les GeoJSON publics.
- `conflits.geojson` conserve son contrat géographique et sa politique de masquage ; `catalogue_actions.json` M5 reste à 12 fiches. M2 définit R1–R4 versionnées, M4 exécute une unique implémentation du moteur d'actions ; zéro tri par bénéfice supposé.
- Toute proposition de `proposal-2` implique revue de compatibilité avec M4 et M3, maintien des fixtures `proposal-1` pour non-régression ou migration explicite, puis incrémentation de version **avant** une publication réelle.

## 10. Limites scientifiques non négociables

- **Pas de classes d'enjeu inventées** : leur mapping dépend des attributs M1 (réservoirs, corridors, sous-trames, prescriptions, échelle de représentation, dates et limites) et d'une validation documentée.
- **Pas de `conflit_potentiel` automatique fondé sur un simple croisement** ; fixer des critères contextuels vérifiables. `obstacle_confirme` exige une preuve externe localisée pertinente.
- **Pas de calcul d'urgence** ou de gain écologique chiffré sans données/méthode spécialisées.
- Le calcul `max(D)` est une convention commune de triage, pas un modèle écologique de l'efficacité d'une restauration. Les sous-familles ne sont comparables qu'après validation de leur traduction vers D.
- Sources de cadrage à vérifier et citer correctement dans l'écrit, sans leur attribuer nos seuils : OFB Trame verte et bleue ; Cerema identification/priorisation des obstacles et notice de grille d'aide à la hiérarchisation des points noirs. Les normes scientifiques ne sont **pas** prouvées par les tests de code.
