# Dictionnaire des faits familiaux d’actions — audit-2

Spécification interne proposée à M4. Les codes officiels, méthodes et domaines doivent être approuvés sur les données M1. Aucun seuil, mesure ou preuve de terrain n’est créé ici.

## Enveloppe commune

Chaque fait porte `etat`, `valeur`, `preuve_ids` et `reference`. `documente` signifie traçable, pas « déclencheur satisfait ». Un résultat documenté peut conclure à l’absence du déclencheur ou rester indéterminé.

- `inconnu` : `valeur=null` ; aucune conclusion positive ou négative.
- `non_applicable_documentee` : `valeur=null`, preuves et référence de domaine requises.
- `documente` : valeur non nulle du type propre au fait, preuve et référence requises.
- `absence_documentee` : réservé à `absence_declencheur`, strictement `true`, preuves négatives et méthode contrôlées. `false` ne prouve pas la présence ; il ne soutient aucune absence.

Pour `signal=etaye`, les six faits requis sont documentés et les contraintes positives ci-dessous s’appliquent. Les faits de contexte ou de provenance ne suffisent jamais à eux seuls. Pour une indication partielle, les inconnues restent explicites et la méthode de famille doit justifier le signal ; aucun champ booléen ne remplace une analyse.

## Valeurs par fait

Les noms de types renvoient aux `$defs` du [schéma](schema_actions_m2.json). Le JSON [rules_actions](rules_actions.json), champ `fact_semantics`, contient la même sémantique et les références exactes.

| Fait | Familles | Type et sens | Condition supplémentaire pour étayage | Contrôle externe obligatoire |
| --- | --- | --- | --- | --- |
| `evenement_route_corridor_reference` | R1 | `eventReferenceValue` — Références de l’intersection M2, de sa géométrie et de ses deux sources. | Structure complète et références contrôlées ; ne constitue pas seul un déclencheur. | Résoudre le conflit et les sources, vérifier intersection réelle, géométrie courante et empreinte ; aucune gêne n’est inférée de XY. |
| `statut_croisement` | R1 | `crossingStatusValue` — Qualification M2 de l’événement, distincte de la simple détection. | `{"enum":["conflit_potentiel","obstacle_confirme"]}` | Rejouer le contrôle QA et vérifier règle contextuelle approuvée ou expertise externe pertinente ; localisation résolue. |
| `validite_positive` | R1 | `positiveValidityValue` — Assertion de capacité positive QA pour cette observation précise, sans qualification automatique. | `{"const":true}` | Vérifier les résultats de derive_positive_evidence, l’identité de l’événement et la portée exacte de la revue. |
| `sous_trame_documentee` | R1 | `subframeValue` — Sous-trame réellement référencée et pertinence pour le phénomène routier. | `{"properties":{"pertinence":{"const":"etablie"}}}` | Vérifier le code/version dans le dictionnaire M1 et la pertinence déclarée selon une méthode M2 approuvée. |
| `route_source_versionnee` | R1 | `routeSourcesValue` — Identités et versions des objets routiers réellement utilisés. | Structure complète et références contrôlées ; ne constitue pas seul un déclencheur. | Résoudre chaque objet dans les sources, comparer les versions et le lien à l’événement ; pas seulement un nom de fichier. |
| `emprise_reliee` | R1, R2, R3, R4 | `extentRelationValue` — Lien géométrique des objets concernés à l’emprise étudiée. | `{"properties":{"relation":{"enum":["interieur","interieur_et_frontiere"]}}}` | Vérifier les géométries référencées et la relation ; frontiere_seule n’établit pas un fait intérieur au pilote. |
| `haies_inventaire_date` | R2 | `inventoryValue` — Provenance et période de l’inventaire de haies utilisé, pas une densité. | Structure complète et références contrôlées ; ne constitue pas seul un déclencheur. | Vérifier source/millésime, précision et compatibilité de période ; ne pas déduire une lacune de la densité. |
| `sous_trame_bocagere` | R2 | `subframeValue` — Sous-trame dont le contexte bocager est identifié par la nomenclature M1. | `{"properties":{"pertinence":{"const":"etablie"}}}` | Contrôler le sens officiel du code et la pertinence bocagère ; aucune classe n’est inférée de son libellé. |
| `continuite_reseau_referencee` | R2 | `networkValue` — Réseau et objets de haies/habitats effectivement analysés. | Structure complète et références contrôlées ; ne constitue pas seul un déclencheur. | Résoudre réseau, géométrie et sous-trame ; la présence d’un réseau ne prouve pas sa fonctionnalité ou une lacune. |
| `analyse_lacune_documentee` | R2 | `externalEvaluationValue` — Résultat d’une analyse de lacune, pouvant aussi conclure à son absence ou rester indéterminé. | `{"properties":{"conclusion":{"const":"declencheur_etabli"}}}` | Méthode de lacune/topologie approuvée, domaine et paramètres justifiés, données et rapport contrôlés. Aucun seuil de densité ou connectivité par défaut ; bloquant sans méthode M1/M2. |
| `couverture_thematique` | R2 | `thematicCoverageValue` — Portée des catégories et sous-trames nécessaires à la conclusion. | `{"properties":{"conclusion":{"const":"suffisante_pour_faits_requis"}}}` | Comparer ensembles requis/couverts et exigences du registre de méthode ; une liste requise vide doit être justifiée. Ne pas confondre couverture des faits et exhaustivité SIG. |
| `friche_id_et_statut` | R3 | `brownfieldValue` — Site recensé, statut source et admissibilité à une étude de continuité. | `{"properties":{"eligibilite_etude":{"const":"etablie"}}}` | Résoudre l’identifiant, la nomenclature du statut et son interprétation approuvée ; ne pas déduire disponibilité foncière ou absence de valeur écologique. |
| `friche_source_datee` | R3 | `inventoryValue` — Sources et périodes de l’inventaire de friches réellement exploité. | Structure complète et références contrôlées ; ne constitue pas seul un déclencheur. | Vérifier le statut temporel du site et la compatibilité des millésimes ; aucune péremption arbitraire en nombre d’années. |
| `lien_geometrique_continuite` | R3 | `spatialLinkValue` — Résultat d’une relation géométrique entre une friche et une continuité identifiées. | `{"properties":{"conclusion":{"const":"declencheur_etabli"}}}` | Résoudre les deux objets et le calcul référencé ; vérifier la méthode de voisinage approuvée et ses paramètres. Aucun rayon par défaut ; bloquant sans méthode M1/M2. |
| `methode_voisinage_documentee` | R3 | `methodValue` — Définition et domaine de la méthode de voisinage, pas une mesure de distance. | Structure complète et références contrôlées ; ne constitue pas seul un déclencheur. | Vérifier registre approuvé et méthode effectivement utilisée dans le résultat ; des sous-méthodes distinctes sont possibles si autorisées, jamais assimilées par simple égalité de texte. |
| `contexte_sol` | R3 | `soilContextValue` — Codes d’occupation des sols observés avec leur nomenclature et interprétation. | Structure complète et références contrôlées ; ne constitue pas seul un déclencheur. | Vérifier codes, source et période ; ce contexte n’atteste ni dépollution, ni faisabilité, ni efficacité de renaturation. |
| `inventaire_mares_date` | R4 | `inventoryValue` — Provenance et période de l’inventaire des mares/habitats humides. | Structure complète et références contrôlées ; ne constitue pas seul un déclencheur. | Vérifier inventaire, saisonnalité pertinente et complétude pour les assertions négatives ; zéro point ne signifie pas zéro mare. |
| `sous_trame_humide` | R4 | `subframeValue` — Sous-trame pertinente pour les habitats humides, selon référentiel identifié. | `{"properties":{"pertinence":{"const":"etablie"}}}` | Vérifier nomenclature et pertinence pour les milieux concernés ; ne pas utiliser une distance de dispersion universelle. |
| `reseau_habitats_reference` | R4 | `networkValue` — Réseau d’habitats humides et objets réellement étudiés. | Structure complète et références contrôlées ; ne constitue pas seul un déclencheur. | Résoudre habitats, géométries, sous-trame et période ; ne pas assimiler connectivité structurelle et fonctionnement biologique. |
| `analyse_isolement_documentee` | R4 | `externalEvaluationValue` — Conclusion d’une analyse d’isolement/lacune du réseau humide. | `{"properties":{"conclusion":{"const":"declencheur_etabli"}}}` | Contrôler méthode adaptée, domaine écologique, données et rapport. Aucun critère universel d’isolement ; bloquant sans méthode M1/M2. |
| `contexte_hydrologique` | R4 | `hydrologicalContextValue` — Analyse référencée de l’adéquation hydrologique à une étude, pas une autorisation de créer une mare. | `{"properties":{"adequation_etude":{"const":"etablie"}}}` | Contrôler méthode, saison/période et revue hydrologique compétente ; une donnée manquante reste inconnue. Bloquant pour étayage sans méthode M1/M2. |
| `absence_declencheur` | R1, R2, R3, R4 | `absenceValue` — True affirme que l’absence du déclencheur est établie dans le périmètre/méthode/période ; false ne prouve ni absence ni présence. | Pour une absence : booléen strict true ; jamais false/null. | Vérifier analyse effectuée, preuves négatives, méthode approuvée, couvertures thématique/spatiale/temporelle et absence d’observation pertinente ; ne pas inférer depuis une liste vide. |

## Lecture des types et conclusions

`eventReferenceValue` conserve conflit, sources route/corridor, géométrie référencée et empreinte. `sourceVersionValue` et `inventoryValue` conservent des identités/version et périodes, sans transformer un inventaire en mesure de densité. `networkValue` référence réseau, objets, géométrie et sous-trame sans déclarer une fonctionnalité biologique.

`subframeValue` associe code/référentiel/version et pertinence (`etablie`, `non_etablie`, `inconnue`). Le code n’est pas inventé par M2 : M4 doit vérifier le dictionnaire M1 et son interprétation approuvée.

`externalEvaluationValue` et `spatialLinkValue` portent une conclusion : `declencheur_etabli`, `indice_documente`, `declencheur_absent`, `indetermine`. Ce sont des états de restitution de la méthode externe, pas des critères écologiques ajoutés. Seul `declencheur_etabli` soutient un étayage. La méthode doit fournir domaine, paramètres justifiés, sources, versions et rapport reproductible ; si elle manque, utiliser l’attente M1/M2.

`extentRelationValue` distingue intérieur, intérieur avec frontière, frontière seule, hors emprise et relation indéterminée. Une présence seulement frontalière ne devient pas un fait intérieur. `thematicCoverageValue` distingue couverture des faits nécessaires et complétude globale : les ensembles requis/couverts doivent être comparés par M4 selon la méthode autorisée.

`brownfieldValue` n’assimile pas site recensé à terrain disponible. `soilContextValue` conserve des codes observés, pas un gain attendu ou une dépollution acquise. `hydrologicalContextValue` porte une adéquation à une étude, sans autorisation de travaux ni implantation précise.

### Structure des valeurs admissibles

Chaque objet ci-dessous exige tous les champs nommés et refuse les propriétés
supplémentaires. Les références, codes et versions sont des chaînes non vides ;
les IDs sont des chaînes ou entiers, jamais des booléens. Une référence ne vaut
pas résolution dans le registre M1/M2. Les géométries sont référencées, pas
fabriquées dans ce contrat.

| Type | Champs et domaine |
| --- | --- |
| `sourceIdentityValue` | `namespace`, `id` : identité dans un registre source, sans collision entre espaces de noms. |
| `sourceVersionValue` | Identité précédente et `dataset_version` : version du jeu effectivement utilisé. |
| `eventReferenceValue` | `conflit_id`, `route_sources`, `corridor_sources` non vides, `geometry_reference`, `event_binding_sha256` de 64 caractères hexadécimaux minuscules. M4 compare l'empreinte à `event_evidence_binding` existant pour l'événement courant ; une empreinte bien formée n'est pas une signature. |
| `crossingStatusValue` | `croisement_detecte`, `conflit_potentiel`, `obstacle_confirme`, `non_concluant` : qualification transportée, à contrôler contre l'événement. |
| `positiveValidityValue` | Booléen strict de capacité QA : `false` est documentable, mais interdit pour R1 positive/indicative. `true` exige la revue QA de l'événement. |
| `subframeValue` | `code`, `referentiel`, `version`, `pertinence` : `etablie`, `non_etablie`, `inconnue`. Pas de déduction depuis le nom d'un code. |
| `routeSourcesValue` | Tableau non vide d'objets `sourceVersionValue`, sans doublon exact. La résolution des identités et versions reste externe. |
| `extentRelationValue` | `emprise_reference`, `objet_ids` non vides, `relation` : `interieur`, `interieur_et_frontiere`, `frontiere_seule`, `hors_emprise`, `indeterminee`. La frontière vise le pilote étudié, pas une suppression des relations entre mailles adjacentes. |
| `inventoryValue` | `source_objects` versionnés non vides, `periode_reference` : provenance de l'inventaire, sans exigence automatique d'exhaustivité positive. |
| `networkValue` | `reseau_id`, `objet_ids` non vides, `geometry_reference`, `sous_trame_code` : réseau réellement soumis à l'analyse, pas connectivité biologique déclarée acquise. |
| `externalEvaluationValue` | `evaluation_id`, `methode_id`, `methode_version`, `methode_reference`, `conclusion` (les quatre états définis plus haut), `rapport_reference`. La méthode et le rapport externe doivent expliciter domaine et paramètres reproductibles. |
| `thematicCoverageValue` | `categories_requises`, `sous_trames_requises`, `categories_couvertes`, `sous_trames_couvertes`, `validation_reference`, `conclusion` : `suffisante_pour_faits_requis`, `incomplete`, `inconnue`. Les quatre listes contiennent des codes sans doublon. Le schéma ne compare pas leurs ensembles ; une liste requise vide exige justification de méthode. |
| `brownfieldValue` | `friche_id`, `statut_source`, `referentiel_statut`, `version_referentiel`, `eligibilite_etude` : `etablie`, `non_etablie`, `inconnue`. L'éligibilité concerne l'étude de continuité, pas les travaux. |
| `spatialLinkValue` | `friche_id`, `continuite_id`, `relation_reference`, `methode_id`, `methode_version`, `methode_reference`, `conclusion` (les quatre états). La référence de relation doit résoudre calcul, géométries et rapport, sans rayon inventé. |
| `methodValue` | `methode_id`, `version`, `reference`, `domaine_reference` : définition versionnée et domaine d'usage, distincts du résultat d'application. |
| `soilContextValue` | `source_reference`, `nomenclature_reference`, `codes_observes` non vides, `interpretation_reference` : occupation du sol et interprétation externe contrôlée. Aucun paramètre physicochimique fictif n'est ajouté. |
| `hydrologicalContextValue` | `analyse_reference`, `methode_id`, `methode_version`, `methode_reference`, `adequation_etude` : `etablie`, `non_etablie`, `inconnue`. La référence d'analyse doit résoudre le rapport et la revue hydrologique. |
| `absenceValue` | Booléen strict : `true` affirme l'absence établie ; `false` signifie que cette absence n'est pas établie. Seul l'état `absence_documentee` avec `true` peut porter l'affirmation négative. |

Une `periode_reference` exige `debut`, `fin` au format date ISO et `reference`.
L'ordre des dates, leur lien aux périodes d'observation et leur compatibilité
saisonnière relèvent du contrôle M4 selon les méthodes approuvées. Les références
de couverture, de revue et les preuves de l'enveloppe restent exigées même quand
une valeur structurée porte déjà sa propre référence.

## Limites du schéma et blocages réels

Les propriétés et valeurs sont contrôlables structurellement. L’identité des objets, l’ordre/compatibilité des périodes, l’inclusion des emprises, les versions effectivement appliquées et la vérité des rapports ne sont pas déduits du schéma. Les contrôles `REF_*` de `interobject_checks` sont obligatoires pour M4 avant données réelles. Une validation de schéma ne suffit pas à autoriser un résultat d’action ou sa diffusion.

Sans méthode familiale approuvée et données M1 adaptées, les analyses R2/R3/R4 restent bloquées pour l’étayage. Les profils d’attente permettent de signaler les manquants sans inventer une attestation positive. Les 52 oracles abstraits et les deux multiproblèmes ne sont pas des exemples de preuves scientifiques contrôlées.

La traduction d'une conclusion externe en signal indicatif ou étayé doit être
approuvée par famille. Le schéma ne peut pas inventer cette méthode ni prouver le
signal indicatif à partir de faits tous inconnus. L'absence documentée exige en
plus une recherche négative réalisée et contrôlée ; elle ne résulte pas du seul
libellé `declencheur_absent` d'un rapport. En l'absence de ces prérequis, M4 doit
refuser la promotion vers un résultat favorable ou négatif réel et conserver
l'attente/non-évaluation, ou une erreur de contrat si l'entrée affirme une preuve
incohérente. Les contrôles de décision restent ceux de A0–A8 après validation.
