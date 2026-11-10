# ReConnect Normandie — spécification M2 des correspondances R1–R4

**État : PROPOSITION de spécification** `m2-actions.spec-proposal-1`, révision technique `audit-2` — à faire valider par M2/M5/M4. **Aucune règle écologique de terrain n'est prétendue validée** sans M1 et une revue scientifique. Le [dictionnaire des faits](dictionnaire_faits_actions_m2.md) précise les valeurs des attestations ; la section 11 remplace les ambiguïtés structurelles de l'audit-1.

## 1. Continuité avec le PRD

Référence déclarée par le pack : `PRD_ReConnect_Normandie_V6_FINAL.docx`, sections 6.1–6.4 et 8.4 ; ce fichier et le catalogue M5 ne sont pas présents localement et ne sont pas considérés validés. Sur instruction M2, les correspondances **provisoires à confirmer avec M5** restent : **R1 → A04** (passages à faune), **R2 → A01** (haies), **R3 → A03** (friches), **R4 → A02** (mares). Les huit autres fiches du catalogue M5 ne sont **pas** évaluées automatiquement. Plusieurs pistes peuvent coexister, sans classement de rendement ni estimation du gain écologique.

**Responsabilités** : M2 définit les faits nécessaires, les critères de validité et les contre-exemples ; M1 prépare et documente les couches ; M5 maintient `catalogue_actions.json` et confirme les `action_id` ; M4 exécute ce contrat de règles dans l'API, M3 n'affiche que les statuts et justifications concises.

**Sorties du MVP** : `mailles.geojson`, `conflits.geojson`, `fiches_zones.json` et `catalogue_actions.json` restent distincts. Cette spécification n'est pas un remplacement du contrat GeoJSON `m2-m4.proposal-1` ; elle prépare son évolution approuvée.

## 2. Ne pas confondre priorité de maille et pertinence de solution

`priorite_examen` est calculée exclusivement par les tables D/S. **Elle n'est jamais une entrée de R1–R4** : une maille classée faible peut nécessiter une vérification d'action sur un phénomène particulier, et une maille élevée n'a pas nécessairement de solution automatique démontrée.

Statuts locaux **exactement** :

- `etayee_pour_examen` : déclencheur vérifié, pertinence d'une **étude** justifiée, jamais autorisation de travaux.
- `conditionnelle` : indice réel documenté, mais preuve ou prérequis encore incomplets ; indiquer exactement ce qu'il faut vérifier.
- `non_retenue_par_regle` : non-applicabilité prouvée **ou** déclencheur absent selon une couverture validée dans un périmètre fixé. Ce n'est ni « action inutile » ni « absence générale de problème ».
- `non_evaluable` : impossibilité de conclure de manière fiable ; expliciter la cause. Une absence de couche ne donne jamais `non_retenue_par_regle`.

Les pistes affichées sont **groupées par statut**. Aucun classement `1,2,3` d'efficacité.

## 3. Contrat d'entrée normalisé (M2 → M4, pas une donnée brute)

Le fichier `rules_actions.json` déclare les champs. L'entrée du moteur pour chaque couple `(maille_id, rule_id)` contient :

| Champ | Signification et producteur |
|---|---|
| `rule_id` + `action_id` | Appariement immuable R1/A04, R2/A01, R3/A03, R4/A02, recoupé avec M5 |
| `applicabilite`, `applicabilite_reference` | « oui », « inconnue » ou non-applicabilité documentée dans le contexte écologique ; méthode M2 |
| `methode_validee`, `methode_reference` | Méthode M2 versionnée/approuvée. Une référence en texte ne prouve pas sa qualité à elle seule |
| `couverture_essentielle` | suffisante/partielle/insuffisante pour les **faits essentiels** à la règle et à l'emprise/époque examinée |
| `signal` | étayé/indicatif/absence documentée/inconnu **calculé en amont** selon R1…R4 ; jamais depuis une couleur ou une simple coprésence de géométries |
| `preuve_ids`, `preuve_absence_ids` | Références de preuve réelles, enregistrées et rattachées à la maille et au phénomène (non simplement un registre de chaînes) |
| `controle_contradiction` | exclue/confirmée/non évaluée avec portée de l'affirmation concernée |
| `independance_reference` | Examen indépendant attesté si la contradiction n'a pu être évaluée ; aucune indépendance déduite automatiquement de deux fichiers |
| `family_evidence` | Preuves/mesures et versions propres à R1, R2, R3 ou R4, contrôlées avant passage dans le moteur |
| `limites` | Informations à vérifier et incertitudes ; ne sont pas effacées par une sortie positive |

**Interdiction d'un moteur déclaratif de « validité vraie »** : le fait de renseigner `signal=etaye` ne suffit pas. M2 doit construire un diagnostic par famille et une attestation source/qualité vérifiable. M4 ne doit jamais supposer que des booléens fournis manuellement remplacent une preuve.

## 4. Précédence commune, après validation structurelle V0

| Ordre | Condition | État |
|---|---|---|
| V0 | Combinaison structurellement impossible, références indispensables manquantes, IDs incohérents | **Erreur bloquante**, pas un statut d'action |
| A0 | Contradiction pertinente confirmée | `non_evaluable` |
| A1 | Famille non applicable avec justification | `non_retenue_par_regle` |
| A2 | Applicabilité inconnue, méthode non validée ou couverture indispensable insuffisante | `non_evaluable` |
| A3 | Contrôle des contradictions inconnu, sans preuve indépendante documentée | `non_evaluable` |
| A4 | Signal étayé, couverture essentielle suffisante, méthode validée, contradiction exclue | `etayee_pour_examen` |
| A5 | Signal étayé et preuve indépendante, mais contrôle contradiction inconnu | `conditionnelle` |
| A6 | Signal indicatif réel et documenté, données au moins partielles et contrôle acceptable | `conditionnelle` |
| A7 | Absence du déclencheur démontrée sur périmètre et couverture suffisants | `non_retenue_par_regle` |
| A8 | Après les règles précédentes : signal inconnu, ou absence documentée avec contrôle non évalué et indépendance attestée | `non_evaluable` avec motif explicite |

**Invariant V0** : un signal `etaye` ne peut pas reposer sur une couverture essentielle partielle ; `absence_documentee` exige couverture suffisante + attestation négative ; `non_applicable_documentee` avec indice positif est incohérent ; une contradiction confirmée exige référence. Les règles restent calculables sans attribuer de poids arbitraires.

**A8 n'est pas une autorisation de cacher un trou de conception** : compter ses déclenchements par famille et motif, afficher les cas non prévus et refuser toute traduction silencieuse en vert. Tests métamorphiques : retrait d'une preuve ⇒ jamais de promotion ; permutation des familles ⇒ même ensemble de statuts ; absence de données ⇒ jamais `non_retenue`; ajout d'un nouveau diagnostic indépendant ⇒ les actions déjà étayées restent identiques, sauf contradiction pertinente démontrée.

## 5. Les faits que M2 doit réellement produire

### R1 — A04 : étude de franchissement routier

**Déclencheur étayé** : événement réel route–corridor avec `conflit_id`, source route et corridor versionnées, sous-trame pertinente et qualification `conflit_potentiel` ou `obstacle_confirme` contrôlée par `derive_positive_evidence()` avec preuve approuvée. **Déclencheur indicatif** : `croisement_detecte` valable géométriquement mais sans qualification de gêne. **Absence documentée** : pas de croisement pertinent selon `derive_absence_evidence()` et couverture thématique/spatiale/temporelle réellement validée. **Non évaluée** : manque de couche, localisation incertaine ou conflit géométrique non résolu. **À vérifier** : ouvrage existant, SIPAF incomplet, route/voie, trafic, espèces, gestionnaire. Une entrée R1 ne recommande **jamais** de construire directement un passage.

### R2 — A01 : restauration d'une continuité bocagère

**Étaye** uniquement si une analyse structurale ou topologique du réseau de haies documente une lacune reliée à une sous-trame pertinente, avec emprise, millésime et couverture valides. **Indicatif** : vraie rupture cartographiée possible, mais état du réseau ou pertinence à confirmer. **Absence** : réseau évalué et aucune lacune candidate selon les règles annoncées. **Non évaluée** : simple densité faible, haies non cartographiées ou absence de méthode de connectivité validée. Conditions de travaux : usages, parcelles, gestion, état actuel et pratiques agricoles.

### R3 — A03 : étude de renaturation de friches

**Étaye** si une friche identifiée et contrôlée présente une relation géométrique à une continuité, définie par une **méthode de voisinage versionnée**, et si les faits indispensables à la proposition d'une **étude** sont suffisants. **Indicatif** : friche localisée et élément de relation plausibles mais encore incomplets. **Absence** : aucune friche candidate selon inventaire et règle de relation entièrement couverts. **Non évaluée** : simple polygone supposé friche, absence de critère de proximité, statut non vérifié. Pollution, valeur écologique préexistante, contraintes foncières et usages sont des examens de faisabilité ; on ne les remplace pas par un score.

### R4 — A02 : réseau de mares et zones humides

**Étaye** si un isolement ou une lacune du **réseau d'habitats humides** est documenté par une méthode adaptée et un contexte hydrologique pertinent. **Indicatif** : faiblesse du réseau attestée comme hypothèse, hydrologie ou connectivité à confirmer. **Absence** : aucun déficit documenté dans le réseau étudié avec inventaire assez complet. **Non évaluée** : simple « absence de points de mares », inventaire partiel, règle de distance arbitraire, aucun contexte hydrologique. Ne pas proposer de point d'implantation ou de création directe.

## 6. Multiproblèmes, limites spatiales et contrats

- Évaluer les quatre règles **indépendamment**, pour une maille donnée ; conserver zéro à quatre états/actions et éventuellement plusieurs justificatifs pour une même action. Ne jamais dupliquer la même action par conflit.
- Une action peut être rattachée à plusieurs `conflit_id` ; un même `conflit_id` peut relever de plusieurs mailles. Préserver les références plusieurs-à-plusieurs.
- Un événement situé uniquement sur la frontière du pilote ne doit pas devenir artificiellement une preuve interne ; conserver frontières, couverture et précision. Les calculs SIG restent en EPSG:2154, les sorties géographiques GeoJSON en CRS84.
- Dédupliquer les sources par identité canonique, **pas** les phénomènes distincts simplement proches. Un même objet source utilisé par R1 et R3 n'autorise aucune somme de gains ou ordre d'efficacité.
- Diffusion : M4 reçoit un résultat public **filtré** (action_id, statut, motif synthétique, limites publiables et références autorisées). Les géométries sensibles, preuves brutes et avis privés restent dans les diagnostics internes et/ou `fiches_zones.json` avec contrôle des droits. Ne pas exposer `prepare_priority_result_json()` directement.

## 7. Tests de validation M2 et de conformité M4

`tests/fixtures/m2/action_rule_cases.json` contient **52 cas synthétiques** (40 cas de décision, 12 entrées invalides) et **2 cas multiproblèmes**. Les oracles sont des propositions M2 à faire valider par M5/M4, **pas des observations scientifiques**. Chaque test doit vérifier la règle A, le statut, le motif, la conservation des preuves et la stabilité à l'ordre des actions.

Les cas R1/R2/R3/R4 utilisent le même schéma de sortie, mais leurs **faits de qualification ne sont pas interchangeables**. Un test R2 avec « faible densité seule » doit rester non évaluable ; un test R1 avec un simple croisement 2D ne doit jamais devenir « obstacle confirmé ».

Tester les invariants croisés : une couche manquante ne produit pas de non-retenue ; un texte de preuve sans source/version vérifiée ne suffit pas ; l'applicabilité inconnue ne peut être interprétée comme refus ; un diagnostic de conflit non qualifié ne peut être promu par la priorité élevée de la maille ; une action étayée n'efface pas les autres conditions et limites.

## 8. Décisions à confirmer avant passage « règles approuvées »

1. **M1/M2** : champs exacts de `haies`, `friches`, `mares`, TVB, zones d'étude, et couverture ; règles de distance/voisinage justifiées (pas de distance arbitraire) ; qualification des lacunes des réseaux.
2. **M5** : IDs A04/A01/A03/A02, nom et prérequis associés, exactement comme dans le catalogue source de vérité.
3. **M4** : schéma final de `rules_actions.json`, format des références, sérialisation des IDs, règles d'erreur et filtres de diffusion ; pas de nouveau contrat public implicite.
4. **M3** : quatre statuts affichés en langage courant ; plusieurs actions dans une fiche ; pas de numérotation d'efficacité.

## 9. Références d'appui (les conventions propres au projet restent proposées)

- Cerema, *Identification et priorisation des obstacles aux continuités écologiques terrestres*, 9 janvier 2026 : https://www.cerema.fr/fr/actualites/identification-priorisation-obstacles-aux-continuites
- OFB, *Gérer durablement ses haies et en créer de nouvelles* : https://ofb.gouv.fr/gerer-durablement-ses-haies-et-en-creer-de-nouvelles
- Cerema, *Comment identifier un potentiel de renaturation à large échelle ?* : https://www.cerema.fr/fr/actualites/comment-identifier-potentiel-renaturation-large-echelle
- Cerema, *Gestion à court et long terme des friches et préservation de la biodiversité* : https://www.cerema.fr/fr/actualites/gestion-court-long-terme-friches-preservation-biodiversite
- OFB, *Restauration de mares* : https://ofb.gouv.fr/restauration-de-mares

## 10. Consolidation de contrat — historique `audit-1`

La première consolidation utilisait `m2-actions.spec-proposal-1`, avec
`contract_revision=audit-1`. Les quatre IDs et les 52 oracles ne sont pas changés.
Cette révision a rendu la structure auditable ; elle n'a déclaré aucune méthode
familiale scientifiquement approuvée. M4 reste l'unique propriétaire du moteur.

### Deux niveaux à ne pas confondre

[`schema_actions_m2.json`](schema_actions_m2.json) est un **nouveau schéma interne
proposé**, distinct des contrats GeoJSON existants. Il définit :

- `commonInput` : types et invariants V0 de la table commune. Les fixtures sont
  volontairement abstraites : 48 ont uniquement une référence textuelle dans
  `family_evidence`, et 4 décrivent seulement un fait insuffisant. Leur conformité
  à ce profil n'est pas une qualification écologique.
- `normalizedInput` : entrée proposée à M4 avec maille, IDs typés, version de règle
  et preuve familiale structurée. Une action étayée ne peut pas reposer sur le
  seul champ `signal`. Les données absentes disposent d'un profil d'attente.

Les profils familiaux sont `familyEvidence` (faits positifs/négatifs documentés),
`pendingEvidence` (signal inconnu et manquants explicites, sans source ni diagnostic
fictif), `domainEvidence` (non-applicabilité positivement justifiée). Une attente
M1 ne peut pas être transformée en non-applicabilité ou absence prouvée.

Une attestation qualifiée relie règle, maille, diagnostics, phénomène, emprise,
période, méthode/version/référence, sources versionnées, preuves des faits,
couvertures, contrôle M2 et limites. Les faits obligatoires de chaque règle sont
ceux de `required_family_facts` ; ils ne sont pas interchangeables. Pour R1 étayée,
la qualification est `conflit_potentiel` ou `obstacle_confirme`, la QA positive est
valide et la liaison à l'événement doit être courante. Un simple croisement fiable
peut être un indice, sans démontrer une gêne. Le cas synthétique
`R1-croisement_2d_non_qualifie` ne contient aucune preuve de cette fiabilité et
reste, conformément à son oracle, non évaluable. Cette distinction ne doit pas
devenir « tout croisement non qualifié est inutilisable ».

### Contrôles obligatoires au-delà du schéma

Un schéma JSON contrôle la structure, pas la vérité d'une attestation. M4 devra
résoudre les preuves et sources, vérifier les mêmes maille/objet/emprise/période,
les versions et domaines des méthodes approuvées, les couvertures indispensables,
et l'état courant des preuves. Les obligations sont listées dans
`referential_checks_required`. La présence d'un auteur, d'une URL ou d'un booléen
ne constitue pas une authentification. Les adaptations réelles R2–R4 restent
inactives tant que leurs méthodes et faits M1/M2 ne sont pas contrôlés.

`couverture_essentielle` porte sur les faits nécessaires à la décision, et non sur
l'exhaustivité de tous les inventaires. Une observation positive localisée et
contrôlée peut suffire à l'examen même si la complétude globale de sa source est
inconnue ; elle ne transforme pas ce statut SIG en `validated`. Une conclusion
négative exige au contraire les couvertures validées nécessaires. Les cas nommés
« couverture inconnue » des fixtures emploient la catégorie abstraite `partielle`
avec signal inconnu : leur non-évaluation est conservée, sans en tirer un mapping
automatique des statuts SIG vers la couverture essentielle.

Les périodes doivent être ordonnées et couvrir les observations ou absences
revendiquées. Il faut déclarer les catégories et sous-trames nécessaires, la portée
spatiale des inventaires et leur qualité d'usage. La complétude décisionnelle D/S
n'est pas substituable à ces couvertures. Un ouvrage non inventorié, une faible
densité, une friche localisée ou zéro point de mare ne satisfont pas seuls ces
exigences. Les avis contradictoires gardent leur portée et leurs références.

### Précédence et totalité vérifiées comme document

Les `predicate_schema` de A0–A8 rendent la table auditable sans implémenter de
moteur d'actions M2. Après V0, appliquer exclusivement la première règle. A8 est
bornée : elle ne couvre que le signal inconnu ou l'absence non concluante du fait
d'un contrôle de contradiction non évalué, malgré l'indépendance attestée. Une
catégorie future non prévue est refusée ; elle ne tombe pas dans un « sinon ».

Sur 432 combinaisons des six champs catégoriels communs, avec références
synthétiques requises, l'audit documentaire distingue 192 combinaisons impossibles
V0 et 240 admissibles. La partition par précédence est : A0=80, A1=32, A2=104,
A3=6, A4=2, A5=1, A6=6, A7=2, A8=7 ; aucun trou. Ces effectifs ne mesurent ni des
situations de terrain ni toutes les configurations de preuves et de périodes.

Les erreurs proposées sont détaillées dans `validation_errors`, notamment
`E_ACTION_INPUT_INVALIDE`, `E_ACTION_ABSENCE_NON_DOCUMENTEE`,
`E_ACTION_ETAYAGE_COUVERTURE_INSUFFISANTE`,
`E_ACTION_NON_APPLICABILITE_INCOHERENTE`,
`E_ACTION_ATTESTATION_FAMILLE_INVALIDE` et `E_ACTION_TABLE_NON_TOTALE`.
Le marqueur `ERREUR` des douze cas V0 n'est pas un cinquième statut d'action.
Les oracles ne précisent pas encore les codes fins, motifs, limites et preuves
attendus ; leur enrichissement devra être relu par M2/M4, sans modifier ici les
attentes d'origine.

### Portée des références vérifiées

Les pages d'appui ont été consultées le 3 novembre 2026 :

| Appui | Portée constatée et limite |
| --- | --- |
| Cerema obstacles, 9 janvier 2026 | Démarche combinant infrastructures, ouvrages et TVB ; elle ne valide pas notre règle R1 ni une déduction d'obstacle depuis XY. |
| OFB gestion des haies et bocage, sans date explicite retenue | Fonctionnement et gestion des haies ; aucun seuil de lacune ou de densité n'est importé. |
| Cerema potentiel de renaturation, 30 mai 2022 | Méthode étudiée en contexte francilien ; pas une calibration transférée automatiquement aux friches normandes. |
| Cerema friches/biodiversité, 15 décembre 2025 | Retour d'expérience sur les enjeux des friches ; ne démontre pas le potentiel de chaque site recensé. |
| OFB « Restauration de mares », mise à jour 28 octobre 2024 | Fiche d'un projet du bassin du ru de Vaucresson, pas un protocole général de déclenchement R4. Une méthode adaptée reste à fournir. |

Ces sources cadrent les précautions ; elles ne sont ni des preuves des événements
du pilote ni des versions de méthodes M1/M2 déjà approuvées. Le
[transfert M4](transfert_actions_m2_m4.md) et le [bilan d'audit](audit_actions_m2.md)
précisent la portée effectivement livrée et les décisions restantes.

## 11. Sémantique des faits et résultats — `audit-2`, 4 novembre 2026

Les cinq contre-exemples confirmés montrent que les anciennes valeurs libres
de `fact.valeur` permettaient de confondre traçabilité et satisfaction du
déclencheur. Le [dictionnaire](dictionnaire_faits_actions_m2.md) et
`rules_actions.json.fact_semantics` définissent désormais **22 faits nommés**,
avec types propres, valeurs admissibles, conditions d'étayage et contrôle externe.
Les sous-schémas `fact_<nom>` s'appliquent à chaque fait ; l'entrée complète se
valide avec `normalizedInput`. `familyEvidence` est une enveloppe commune et ne
remplace pas les contraintes conditionnelles de cette entrée.

`etat=documente` affirme la traçabilité, jamais à lui seul un déclencheur.
Les inventaires, réseaux, relations géométriques et méthodes sont structurés ;
ils ne sont pas remplacés par des booléens. Les analyses de lacune, voisinage et
isolement distinguent `declencheur_etabli`, `indice_documente`,
`declencheur_absent` et `indetermine`. Pour `signal=etaye`, les six faits de la
famille sont documentés et les conclusions favorables spécifiques sont exigées.
Une conclusion défavorable reste documentable mais ne peut étayer l'action.
Une inconnue ou non-applicabilité de fait a une valeur nulle ; cette dernière
nécessite une preuve de domaine. Elle n'est pas déduite d'une couche manquante.

`absence_declencheur.valeur=true` affirme que l'absence du déclencheur est
établie dans la méthode, l'emprise et la période contrôlées. `false` signifie que
cette affirmation n'est pas établie ; il ne démontre pas une présence.
`signal=absence_documentee` exige ce fait à l'état `absence_documentee`, avec
valeur strictement vraie, méthode déclarée validée, preuves négatives et
couvertures validées pertinentes. Une valeur nulle ou fausse est refusée. Cette
garde du profil normalisé s'ajoute aux invariants abstraits ; elle ne réécrit
ni `commonInput`, ni les 52 oracles, ni la table A0–A8.

La présence de ces déclarations n'authentifie pas leurs auteurs. Les douze
contrôles `interobject_checks` distinguent les contraintes locales vérifiées des
comparaisons à réaliser par M4 : identité typée des mailles/diagnostics,
résolution et polarité des preuves, objets/phénomènes/familles, versions de
méthodes approuvées, emprises, périodes, couvertures et unicité des décisions.
Une couverture plus vaste peut être valable si elle couvre effectivement le
domaine requis ; les périodes ne doivent pas forcément être textuellement
identiques, mais leur compatibilité doit être justifiée selon la méthode.
JSON Schema ne calcule aucune de ces relations et ne résout aucun registre.

Trois profils de sortie internes sont proposés à M4 :

- `actionResult` conserve les IDs typés en tableaux, versions, statut, règle A,
  motif contrôlé, justification, preuves positives et négatives, attestations,
  conflits, limites, prérequis et état déclaré du contrôle référentiel.
- `actionValidationError` représente V0 ou une erreur de contrat, sans statut
  d'action. `ERREUR` n'est pas un état de restitution.
- `actionPublicProjection` est une liste d'autorisation fermée, distincte du
  résultat interne. M4 la construit après validation et revue des droits/textes.
  Aucun transfert automatique de preuve ou référence interne n'est autorisé.

Le schéma lie A/statut/motif, sans décider quelle règle doit gagner sur une
entrée. Un résultat favorable ou non retenu exige une référence déclarée de
contrôle et une attestation ; M4 doit en vérifier la réalité. A7 garde méthode,
preuves d'absence et couverture suffisantes. A1 reste antérieure à A2 : un
domaine non applicable peut être établi sans méthode écologique active.

M1/M2 doivent encore fournir et approuver les méthodes, leurs domaines,
paramètres, dictionnaires et versions, et contrôler les sources réelles. Aucune
distance, densité ou connectivité par défaut n'est introduite. Sans cela,
l'usage scientifique réel est bloqué. Les exemples de tests structurés sont
explicitement SYNTHÉTIQUES et ne constituent aucune attestation de production.
Les contrats GeoJSON proposal-1/proposal-2 restent inchangés et le moteur reste
exclusivement à implémenter par M4.
