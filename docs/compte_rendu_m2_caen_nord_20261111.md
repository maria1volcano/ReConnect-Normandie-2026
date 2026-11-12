# ReConnect Normandie V6.1 — Compte rendu opérationnel M2, Caen Nord

État au **11 novembre 2026**. Livraison `M1-M2-CAEN-NORD-V1`, territoire `caen_nord_5communes`, grille `M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1`.

**Résultat : les 66 mailles ont des résultats SIG réels. La détection produit 3 157 événements candidats ; 3 156 sont agrégés, un reste en quarantaine numérique. Aucune priorité écologique rouge, orange ou jaune n’est justifiable avec les preuves reçues.** Les attributs routiers améliorent nettement la description et la préparation d’une revue locale, sans lever les conditions écologiques et méthodologiques manquantes. La chaîne stricte complète reste bloquée par l’événement isolé ; le lot livré est explicitement **partiel avec quarantaine**, jamais présenté comme une réussite intégrale sans réserve.

Ce document est l’unique compte rendu de cette intervention. Les fichiers liés sont ses données, contrôles et pièces de reproduction. Aucun travail antérieur, contrat public, règle D/S ou R1–R4 n’a été modifié. Aucun commit, merge ou push.

**Intégration et identité des pilotes**

Archive trouvée sur le Mac : `/Users/ouissal.c/Downloads/M1_M2_CAEN_NORD_V1.zip`. SHA-256 : `5f9dab9e27a864a76ef1367c6d821631d864df2aa6500577882eed2181ff2b18`. L’empreinte du fichier `.sha256` voisin et celles des cinq GeoPackages du manifeste ont été revérifiées. Aucune dépendance à un chemin de conteneur ChatGPT.

Extraction conservée sous `data/processed/caen_nord_5communes/M1-M2-CAEN-NORD-V1/m2_caen_nord_20261111_02/m1_m2_caen_nord_v1/`. Sorties sous `data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/`. Les deux racines sont ignorées par Git, contrôle `git check-ignore` exécuté. La tentative initiale `_01`, bloquée par le contrôle strict, est conservée.

Support utilisé : **couche `grille_caen_nord`, 66 mailles découpées**, dont 48 fragments de frontière et 18 mailles entières ; les hexagones complets servent uniquement au contrôle de conformité. La différence symétrique surfacique maximale entre chaque maille reçue et l’intersection hexagone complet–territoire vaut **0 m²**. Aire du territoire : **39 484 767,615 m²**. Lacune de couverture recalculée : **2,546 × 10⁻⁷ m²** ; micro-recouvrement compensé : **1,130 × 10⁻⁵ m²**, accepté par le contrôle numérique existant, sans réparation ni nouveau seuil.

Les 8 539 routes `MultiLineString`, 31 corridors `MultiPolygon`, 20 réservoirs `MultiPolygon` et la grille `Polygon/MultiPolygon` passent les interfaces M2 : géométries valides, non vides, identifiants sources uniques et EPSG:2154. Les attributs enrichis sont conservés avec leurs types et NULL. Les 8 539 géométries routières portent Z ; la détection reste en XY et Z ne démontre pas un niveau de franchissement. Détails : [interfaces et contrôle de grille](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/interfaces.validation.json).

**Quatorze `maille_id` existent aussi dans le pilote initial**, mais leurs géométries découpées diffèrent. Toute jointure utilise `(territory_id, grid_version, dataset_version, maille_id)` ; pour un événement, remplacer la dernière composante par `conflit_id`. Le paquet M4 porte ces champs dans chaque couche et table. Les lots natifs des CLI conservent leur format existant et doivent rester associés à leur manifeste de portée.

Le pilote initial garde `grid_version=M1-CAND-1KM2-FLAT-L93-O0-V1`, `dataset_version=M1-V1`. Son `territory_id` était absent : l’alias **documentaire interne** `estuaire_orne_43_historique` est défini seulement dans [la comparaison des pilotes](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/comparaison_pilotes.json), sans réécrire les sorties anciennes ni prétendre à une validation historique. `method_version=null` reste explicite pour les deux pilotes ; le code et l’environnement sont empreintés, sans inventer de version scientifique approuvée.

**Résultats SIG et portée des comptes**

| Quantité | Résultat Caen Nord | Interprétation |
| --- | ---: | --- |
| Mailles calculées | 66 | Supports découpés du nouveau territoire |
| Mailles avec événements agrégés | 40 | Au moins une observation géométrique |
| Mailles sans événement observé | 26 | Aucune absence écologique démontrée |
| Paires route–corridor intersectées | 3 096 | Calcul exploratoire indépendant et ensemble du détecteur identiques |
| Routes distinctes concernées | 2 378 | Tronçons sources, sans indépendance écologique supposée |
| Événements détectés avant contrôle d’appartenance | 3 157 | 3 150 `croisement_detecte`, 7 `non_concluant` |
| Événements agrégés | 3 156 | 3 149 `croisement_detecte`, 7 `non_concluant` |
| Événement conservé en quarantaine | 1 | Aucun propriétaire canonique ni comptage local attribué |
| Relations événement–maille | 3 400 | 3 391 intérieures, 9 de frontière ; ne pas additionner comme obstacles |
| Propriétaires canoniques | 3 156 | Exactement un par événement agrégé |
| Relations géométriques des événements agrégés | 916 transversaux ; 2 233 intersections/superpositions ; 7 contacts | Catégories topologiques, sans qualification de gêne |
| Géométries XY normalisées exactement distinctes du lot agrégé | 2 813 | 343 groupes partagés, soit 686 événements ; aucune déduplication écologique |
| ENJ-01 | NULL sur 66 mailles | Complétude non attestée ; aire de réservoir observée positive dans 27 mailles |
| ENJ-02 | Présence observée dans 44 mailles ; NULL dans 22 | Aucune absence confirmée ; aucune classe d’enjeu dérivée |

Les valeurs exploratoires de **3 096 paires / 2 378 routes** ont été recalculées par requête spatiale sur les couches sources, sans réglage du détecteur pour les atteindre. Les ensembles de paires coïncident, y compris après quarantaine : la paire de l’événement isolé possède une autre composante admise. Le nombre d’événements diffère du nombre de paires parce que certaines intersections sont multiparties. [Résultats détaillés](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/resultats.json).

« Sans observation concluante » désigne ici les **26 mailles sans observation SIG** ; les 40 autres contiennent au moins un `croisement_detecte`. Sur le plan **écologique**, aucune des 66 mailles ne dispose aujourd’hui d’une priorité démontrée. Zéro événement observé, zéro obstacle confirmé établi et preuve d’absence sont trois affirmations différentes : seul le premier est calculé localement ici. `nb_evenements` validé demeure NULL, contrairement à `nb_evenements_observes`.

**Frontière : réserve précise et contrôles conservés**

La CLI `analysis.run_conflicts` bloque sur `rc_4ce22d4da9ae4d1496dbe7540ad01b39eab1bd5d0665ea8259784f873b243bdc`, route `TRONROUT0000002334259154`, corridor `TVB-COR-5FC3F5285AD4722F9C24`. Le résidu extérieur cumulé vaut **1,249383739 × 10⁻⁹ m**, Hausdorff **1,130188340 × 10⁻⁹ m**, pour un budget inchangé **9,331397911 × 10⁻¹⁰ m**. La portion intérieure existe, mais les deux gardes numériques sont dépassées. Il s’agit d’un blocage informatique à cette résolution, pas d’une preuve de décalage réel du terrain.

Le lanceur isole exactement les refus de la CLI, vérifie leur identité par le même contrôle, conserve la géométrie et les sources dans `quarantaine.gpkg`, puis appelle **les fonctions existantes** de détection, agrégation et publication sur les événements admis. Les rapports stricts `conflits_strict.validation.json` et `reproduction_conflits_strict.validation.json` restent `blocked`. Les rapports du lot agrégé passent avec l’avertissement `events_quarantined`. Aucun budget n’a été élargi, aucun événement déplacé ou redécoupé, aucune source supprimée.

La maille `NORM-G1K-FLAT-R+006425-C+000492` intersecte l’événement refusé à titre exploratoire ; ce lien ne remplace pas un propriétaire validé. Le traitement de cet événement doit faire l’objet d’une revue numérique distincte avant son admission. [Mesures et WKB conservé](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/quarantaine.validation.json).

Les critères existants acceptent en outre **18 exceptions numériques tracées** : 12 différences vides après garde de type et de portion intérieure, 6 résidus linéaires sous le budget existant. Les 7 contacts du lot agrégé sont `non_concluant` et uniquement sur la frontière territoriale ; les autres se répartissent en 3 103 intérieurs et 46 intérieur/frontière. Aucun contact n’est promu en preuve de rupture.

Un second passage reproduit exactement les IDs, attributs, géométries normalisées, mailles et relations ; la quarantaine est identique. Les vérificateurs natifs des lots contrôlent les empreintes, relations spatiales, doublons et propriétaires canoniques. **1 418 tests passent** dans le nouvel environnement avec `.venv/bin/python -m pytest -q tests` ; les 40 avertissements concernent les cas synthétiques de tests. Le lancement sans chemin explicite collectait les copies archivées et a été remplacé par cette commande ciblant le dépôt courant. [Journal des tests](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/tests_execution.log).

**Attributs routiers : apport mesuré sur les événements**

La table suivante porte sur **tous les 3 157 événements détectés**, avant quarantaine, et les 2 378 routes distinctes qui les portent. Les objets en projet ou construction sont gardés dans l’inventaire géométrique ; ils sont séparables des observations sur voies en service. Un événement n’est compté qu’une fois par valeur source dans cette livraison.

| Statut / position source | Routes livrées | Routes distinctes concernées | Événements détectés | Événements agrégés |
| --- | ---: | ---: | ---: | ---: |
| En service, `0` | 8401 | 2318 | 3066 | 3065 |
| En service, `1` | 91 | 49 | 74 | 74 |
| En service, `-1` | 1 | 0 | 0 | 0 |
| En construction, `0` | 2 | 2 | 3 | 3 |
| En construction, `1` | 1 | 1 | 2 | 2 |
| En projet, `0` | 43 | 8 | 12 | 12 |

Codes de position conservés : `0` au sol, `1` en sursol, `-1` sous le sol, suivant le sens des signes documenté par l’[IGN](https://data.ign.fr/def/topo/20140416.htm). Cette référence éclaire les codes ; elle ne valide aucune fonction écologique du tronçon. **3 140 événements, soit 99,46 %, concernent des voies en service**, dont 3 066 au sol et 74 en sursol. L’événement en quarantaine appartient au groupe en service/au sol. Le seul tronçon souterrain du lot, en service, ne rencontre aucun corridor livré : zéro événement souterrain observé, sans conclusion d’innocuité. La présence de 76 événements en sursol ne prouve ni leur innocuité ni leur caractère d’obstacle.

| Attribut brut | Répartition des 3 157 événements détectés | Apport et limite |
| --- | --- | --- |
| `importance` | 1 : 3 ; 2 : 91 ; 3 : 144 ; 4 : 317 ; 5 : 1 938 ; 6 : 664 | Hiérarchie source du réseau ; aucun poids écologique attribué. |
| `nombre_voies` | 1.0 : 637 ; 2.0 : 1 370 ; 3.0 : 3 ; 4.0 : 1 ; NULL : 1 146 | 2 011 événements renseignés ; NULL ne signifie pas zéro voie. |
| `largeur_chaussee` | 1.0 : 4 ; 10.5 : 1 ; 2.0 : 116 ; 3.0 : 509 ; 3.5 : 39 ; 4.0 : 784 ; 5.0 : 294 ; 5.5 : 49 ; 6.0 : 29 ; 7.0 : 183 ; 9.0 : 3 ; NULL : 1 146 | 2 011 événements renseignés ; dimension de chaussée, sans mesure de franchissabilité. |
| `precision_planimetrique_m` | 10.0 : 39 ; 2.5 : 2 627 ; 20.0 : 39 ; 3.0 : 360 ; 5.0 : 92 | Précision source routière, sans précision corridor ni aptitude bilatérale validée. |
| `contexte_urbain` | False : 438 ; True : 2 719 | Contexte source ; aucune conclusion sur les espèces ou les habitats. |
| `vitesse_moyenne_vl_source` | 0 : 1 300 ; 1 : 138 ; 10 : 192 ; 100 : 18 ; 15 : 46 ; 20 : 324 ; 25 : 277 ; 30 : 381 ; 35 : 96 ; 40 : 80 ; 45 : 102 ; 5 : 52 ; 50 : 56 ; 55 : 52 ; 60 : 5 ; 65 : 2 ; 70 : 12 ; 75 : 8 ; 90 : 13 ; 95 : 3 | Valeurs sources conservées ; ni trafic mesuré ni risque de collision déduit. |
| `ouvrage_connu` | NULL : 3 157 | Entièrement NULL ; ne démontre aucune absence d’ouvrage. |
| `millesime` | NULL : 3 157 | Entièrement NULL ; date de récupération ou de modification non substituée à un millésime global. |

Pour `nombre_voies` et `largeur_chaussee`, **1 146 événements (36,30 %) / 813 routes concernées** restent NULL ; ces champs sont aussi NULL sur 2 248 des 8 539 routes livrées. Les huit attributs enrichis cités sont donc présents, mais leur présence n’équivaut pas à une complétude de toutes les valeurs. Les distributions complètes, y compris par routes livrées, routes concernées et événements agrégés, sont dans [attributs_routiers.json](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/attributs_routiers.json).

La vitesse source comporte notamment **1 300 événements à valeur 0** ; cette valeur n’est pas une attestation de trafic nul. La [documentation IGN du calcul d’itinéraire](https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/calcul-itineraire/) décrit des vitesses calculées à partir d’attributs et de pénalités. Nous conservons la valeur livrée sans la traiter comme mesure de fréquentation, vitesse observée sur site ou pression écologique indépendante. De même, importance, voies, largeur, contexte et vitesse ne forment pas cinq preuves indépendantes d’un même mécanisme.

Les 31 corridors conservent `sous_trame="-"`, `precision_source=NULL`, avec une source SRCE 2014. Les ouvrages connus et millésimes routiers sont NULL sur tout le lot. Les dates d’objet et la récupération du 11 novembre 2026 ne certifient pas l’actualité des corridors ni une perméabilité actuelle. Aucune précision d’intersection globale n’a été fabriquée depuis la précision routière seule.

**Comparaison méthodologique avec les 43 mailles**

| Dimension | Pilote initial, résultats préservés | Caen Nord |
| --- | ---: | ---: |
| Mailles / voies livrées / corridors / réservoirs | 43 / 1 924 / 16 / 40 | 66 / 8 539 / 31 / 20 |
| Événements détectés / agrégés / quarantaine | 1 069 / 1 069 / 0 | 3 157 / 3 156 / 1 |
| Couples / routes concernées | 1 047 / 789 | 3 096 / 2 378 |
| Mailles avec / sans événement agrégé | 29 / 14 | 40 / 26 |
| Relations locales / propriétaires | 1 184 / 1 069 | 3 400 / 3 156 |
| ENJ-02 présence / inconnu | 30 / 13 | 44 / 22 |
| ENJ-01 validé | 0 | 0 |
| Positions et statuts routiers utilisables pour filtrage | Non établis dans le bilan initial | Service, construction, projet et niveaux source distinguables |
| Sous-trame, précision corridor, ouvrages, trafic, preuves écologiques | Insuffisants | Toujours insuffisants |
| Priorités et recommandations réelles | Non calculées | Non calculées |

Les différences de volume décrivent deux territoires, découpes et versions de données ; elles ne mesurent aucune hausse de fragmentation ni amélioration de biodiversité. Les comptes bruts ne classent pas les mailles partielles.

L’**expérience de retrait des attributs enrichis sur Caen Nord** conserve seulement route ID, source ID, catégorie, ouvrage connu, millésime et géométrie, avec les mêmes corridors et fonctions de détection. Résultat : **3 157 événements et mêmes géométries, couples sources, statuts et relations**. Les identifiants peuvent changer puisque leur empreinte inclut les attributs. Le gain démontré est donc la capacité à distinguer situations et lacunes avant expertise ; aucun gain de performance de qualification écologique n’est mesurable sans référence experte. [Contrôle d’ablation](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/ablation_attributs.json).

**Ce qui est calculable au regard de D/S et R1–R4**

Références inchangées : [table D/S](table_decision_m2.md), [règles R1–R4](regles_actions_m2.md), [contrat qualité](contrat_qualite_amont_m2.md). Les moteurs décisionnels ne sont pas exécutés : la configuration territoriale approuvée, les familles attendues, leurs méthodes et leur domaine ne sont pas fournis. Aucun numéro de règle n’est attribué artificiellement aux mailles.

| Diagnostic ou décision | Calcul ou progrès réel | Condition non satisfaite / conséquence |
| --- | --- | --- |
| ENJ-01 / ENJ-02 | Mesures et présences observées calculées | Complétude spatiale, thématique et temporelle non attestée ; pourcentage ENJ-01 et absences ENJ-02 non validés |
| Route–corridor | Croisements XY et sources traçables, contexte de service et de niveau consultable | Sous-trame, précision bilatérale adaptée, fonctionnement écologique et qualification locale absents ; aucun `conflit_potentiel` ou `obstacle_confirme` établi |
| Pression routière | Filtrages service/niveau, catégories, dimensions et contexte | Ni trafic, exposition des espèces, mortalité ni méthode de traduction validée ; aucun score ni seuil créé |
| D0–D4 | Lacunes identifiables pour préparer l’entrée : domaine inconnu, enjeu inconnu, preuve non qualifiée | Ne pas transformer une donnée absente en hors-champ. D1/D2 sont des chemins possibles selon leur précédence, pas des résultats ici calculés |
| D5–D10a | Aucun enjeu `fort/moyen/faible` ni QA positive/absence compatible disponible | Aucun triage écologique favorable justifié ; la présence d’un corridor ne devient jamais `enjeu_classe=moyen` |
| S0–S4 | Supports territoriaux positifs sur 66 mailles | Familles attendues et méthodes non approuvées : `priorite.etat=non_calculee`, valeur NULL ; aucun S4 simulé |
| R1 / A04, étude de franchissement | Cas mieux préparés, croisement géométrique indicatif consultable | Sous-trame, qualité adaptée, méthode, contrôle des contradictions et qualification humaine manquants ; aucun statut d’action automatique émis |
| R2 / A01, bocage | Aucun nouveau fait familial reçu | Ni réseau de haies ni lacune structurale/topologique qualifiée ; la route enrichie ne débloque pas R2 |
| R3 / A03, friches | Aucun nouveau fait familial reçu | Ni friche contrôlée et reliée selon une méthode de voisinage approuvée ni preuve de déclencheur ; R3 non évaluable |
| R4 / A02, mares/humides | Aucun nouveau fait familial reçu | Ni réseau d’habitats, hydrologie ou lacune/isolement validés ; R4 non évaluable |

Pour une première priorité, M2 et l’expert doivent déclarer le **domaine de sous-trame et les espèces/fonctions visées**, valider une méthode d’enjeu qui produit réellement une classe, contrôler la localisation et le contexte actuel, puis lier les preuves à l’événement exact, à la période et aux versions sources. Le gestionnaire doit documenter l’ouvrage, les usages et, si le raisonnement le requiert, les flux de trafic ; l’expert qualifie la gêne ou l’incertitude et contrôle les contradictions. La configuration de pilote versionnée, ses familles attendues et son approbateur restent requis avant les règles S.

Une preuve positive locale contrôlée peut suffire pour examiner un cas, même si la complétude globale de l’inventaire reste inconnue ; elle doit couvrir les faits essentiels à la décision. Une conclusion négative exige au contraire les couvertures et preuves d’absence adaptées. Il ne faut donc ni attendre une exhaustivité universelle pour toute revue locale, ni utiliser un inventaire partiel pour justifier le jaune.

**Cas locaux proposés à la revue**

| Cas local | Route source / maille(s) | Objet de la revue |
| --- | --- | --- |
| C1 — Colombelles | `TRONROUT0000000014320943` / `NORM-G1K-FLAT-R+006426-C+000493` | Au sol : confirmer la continuité et les espèces, l’usage routier et le franchissement réel. |
| C2 — Hérouville-Saint-Clair | `TRONROUT0000000014315728` / `NORM-G1K-FLAT-R+006427-C+000493`, `NORM-G1K-FLAT-R+006428-C+000492` | Sursol, type autoroutier : examiner l’ouvrage et le passage sous la voie ; aucun obstacle déduit du seul polygone SRCE. |
| C3 — Blainville-sur-Orne | `TRONROUT0000000014317019` / `NORM-G1K-FLAT-R+006428-C+000494` | Sursol : vérifier le rapport réel entre niveau routier et habitat concerné. |
| C4 — Hérouville-Saint-Clair | `TRONROUT0000002502079802` / `NORM-G1K-FLAT-R+006426-C+000493` | Hors service : vérifier l’état actuel et distinguer exposition présente et évolution future. |
| C5 — Ouistreham | `TRONROUT0000000014294415` / `NORM-G1K-FLAT-R+006435-C+000496` | Voies et largeur NULL : compléter les données avant toute interprétation de pression. |

La sélection complète contient **12 fiches de contexte portant sur 11 événements uniques**, avec IDs complets, sources corridor, communes réellement intersectées, mailles, point sur l’événement en Lambert-93 et empreinte géométrique. Les groupes se recouvrent volontairement ; les fiches ne sont pas un total d’obstacles. Critère reproductible : trois premiers IDs triés par groupe de contexte, sans rang écologique. [Cas pour expert](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/cas_revue_expert.json). La quarantaine fait l’objet d’une revue technique séparée.

La revue utile peut comparer un cas au sol et un cas en sursol, puis vérifier un statut projet/construction et une lacune de largeur/voies. Une inspection de l’ouvrage, des habitats de part et d’autre et des usages actuels doit précéder toute promotion du signal ; aucune construction de passage n’est recommandée automatiquement.

**Conséquences pour la carte et données M4**

| Couleur envisagée | Condition des règles existantes | État sur Caen Nord |
| --- | --- | --- |
| Rouge | Enjeu fort documenté + conflit potentiel/obstacle qualifié exploitable, puis synthèse approuvée | Non justifiable |
| Orange | Par exemple enjeu fort + croisement exploitable (D6), ou autres conditions D7/D8 | Non justifiable : enjeu et QA manquants ; aucun transfert automatique depuis service/au sol |
| Jaune | Absence validée avec enjeu documenté, et conditions S3 sur toutes les familles attendues | Non justifiable : aucune absence validée |
| Gris | Restitution transparente de l’indétermination ou de la non-évaluation | Les 66 mailles restent sans couleur de priorité justifiée ; si affichées en gris, libeller **« priorité non calculée »**, sans prétendre à un résultat S4 |

Les observations peuvent être affichées séparément et consultées sur les 40 mailles concernées ; les 26 autres gardent « aucune observation sur ces couches, absence non démontrée ». L’événement isolé doit apparaître comme réserve technique, sans augmenter les compteurs ni devenir un obstacle confirmé. Aucune capacité de priorisation supplémentaire n’est revendiquée depuis l’enrichissement routier seul.

Paquet **interne** disponible pour M4 :

- [m4_interne.gpkg](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/m4_interne.gpkg) : couches `evenements` (3 156), `mailles` (66), `enjeux` (66), `quarantaine` (1), table `liens_mailles_evenements` (3 400). Identités territoriales explicites, statuts et observations sources ; priorité NULL/non calculée et actions non calculées.
- [evenements_contexte.json](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/evenements_contexte.json) : contexte des **3 157** candidats, état `agrege/quarantaine`, IDs et groupes exacts du lot agrégé ; pas de propriétaire pour le candidat refusé.
- [attributs_routiers.json](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/attributs_routiers.json), [cas_revue_expert.json](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/cas_revue_expert.json) et [resultats.json](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/resultats.json) : filtres, fiches de revue et comptes avec unités explicites.
- Lots natifs `enjeux.gpkg` + `enjeux.validation.json`, `evenements.gpkg` + `mailles.gpkg` + `conflits.validation.json` ; chaque lot est indivisible à l’usage. Les rapports stricts bloqués et la quarantaine accompagnent obligatoirement la transmission.
- [manifest_interne.json](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/manifest_interne.json) : chemins, empreintes sources/sorties/code, versions et référence historique. [preservation.validation.json](../data/derived/caen_nord_5communes/m2_caen_nord_20261111_02/preservation.validation.json) : **247 fichiers préexistants contrôlés, aucun modifié**, dont les travaux du pilote initial.

Ces fichiers ne sont pas un nouveau contrat public. Aucun GeoJSON public de priorités ni résultat R1–R4 favorable n’est exporté. M4 conserve ses contrôles de droits et sa projection publique ; il ne doit convertir ni les champs NULL en absence, ni le statut de service en preuve de gêne, ni la réussite du lot admis en réussite intégrale de la chaîne stricte.

**Reproduction et environnement**

Le lanceur ajouté est [analysis/run_caen_nord.py](../analysis/run_caen_nord.py). Il utilise les scripts et fonctions M2 existants sans les modifier, isole explicitement la réserve de frontière de cette livraison et refuse les dossiers déjà existants. Le code réellement exécuté est copié sous `code/analysis/` dans le lot. Les commandes exactes des CLI sont dans `commandes.json` ; la branche de quarantaine est dans le lanceur copié.

```sh
.venv/bin/python -m analysis.run_caen_nord \
  --archive /Users/ouissal.c/Downloads/M1_M2_CAEN_NORD_V1.zip \
  --run-id m2_caen_nord_20261111_03
```

L’ID `_03` est un exemple de nouveau dossier pour une reproduction future ; il n’est pas présenté comme une exécution déjà faite. Les résultats présents proviennent de `_02`, avec deux détections/agrégations et le contrôle de retrait des attributs. Lancer depuis la racine du dépôt ; les répertoires `_01` et `_02` sont préservés.

Python **3.10.6**, GeoPandas **1.1.4**, Shapely **2.1.2**, pandas **2.3.3**, NumPy **2.2.6**, pyproj **3.7.1**, pyogrio **0.13.0**. Les dépendances déclarées ont été installées dans le `.venv` local ; `requirements.lock.txt` conserve les versions exactes. Les fichiers `manifest_restitution.json` et `verification_finale.json` ajoutent les empreintes du présent compte rendu, des journaux et les contrôles finaux, sans réécrire le manifeste d’exécution.
