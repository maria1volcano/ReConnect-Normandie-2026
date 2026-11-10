# M2 — Observations réelles et diagnostics évaluables au 10 novembre 2026

Les sorties réelles permettent une démonstration territoriale descriptive sur **43 mailles**, avec **1 069 événements géométriques candidats** dans 29 mailles. La qualification écologique reste partielle : **aucune priorité ni action automatisée n'est calculée**. Ce livrable prépare la revue humaine et l'ingestion interne, sans modifier les résultats ni les méthodes.

Le dossier [m2_diagnostics_20261110_01](../data/derived/m2_diagnostics_20261110_01/) porte le format documentaire `m2-descriptif-interne-1`, sur les données réelles `M1-V1`, grille `M1-CAND-1KM2-FLAT-L93-O0-V1`. `method_version=null` est conservé. Cette version documentaire n'est pas une approbation scientifique.

## Frontière : sujet technique clos

Les [conclusions du correctif intégré](finalisation_frontiere_m2_20261109.md) et le [contrôle des différences vides](../data/derived/m2_difference_vide_20261110_01/CONTROLE.md) consignent les trois branches : acceptation historique par `study.covers()` ; 14 différences vides acceptées **après** le contrôle `LineString` et DE-9IM `1********` ; trois différences non vides sous budget ULP inchangé. Pour les 14 cas, Hausdorff nul est une mesure indépendante et **delta est non applicable**. Le code actuel et le test permanent de refus sans portion intérieure concordent avec ces conclusions. La convention historique des lignes entièrement couvertes sur la frontière pourra être clarifiée séparément. Aucun correctif, nouveau rapport numérique ou test relancé ici. Les 1 415 tests complets et les 62 tests ciblés sont des résultats antérieurs, pas des exécutions de cette intervention.

## Ce que décrivent les observations

Les comptes proviennent des [sorties consolidées de branche](../data/derived/m2_frontiere_20261109_01/data/derived/branche.validation.json), des [résultats enjeux](../data/derived/m2_reel_20261109_01/data/derived/enjeux_m1_reels.validation.json) et de leur regroupement descriptif dans [situations_geometriques.json](../data/derived/m2_diagnostics_20261110_01/situations_geometriques.json). Les sources initiales ont déjà été réceptionnées : 40 réservoirs, 16 matrices de corridors et 1 924 objets routiers. Le manifeste nouveau conserve leurs empreintes, sans nouvel audit de réception.

| Unité de compte | Observé | Portée et limite |
| --- | ---: | --- |
| Événements techniques, tous `LineString` / `croisement_detecte` | 1 069 | Identifiants de détection ; aucun obstacle confirmé déduit |
| Couples route–matrice sources | 1 047 | 21 couples ont plusieurs composantes, soit 22 événements supplémentaires |
| Tronçons routiers sources concernés | 789 | Segments de base de données, pas 789 axes indépendants |
| Matrices sources concernées | 13 sur 16 | Une même route peut rencontrer plusieurs matrices |
| Géométries XY normalisées exactement distinctes | 953 | WKB normalisé, sans arrondi ; aucune analyse causale d'indépendance |
| Groupes partageant exactement une géométrie | 116, soit 232 événements | 95 groupes entre objets de même classe et 21 entre classes différentes ; conserver tous les IDs |
| Relations événement–maille | 1 184 | Liens locaux, **jamais** total d'obstacles ; un événement peut concerner plusieurs mailles |
| Propriétaires canoniques | 1 069 | Un par événement ; les comptes exclusifs sont additionnables pour retrouver les 1 069 événements |
| Phénomènes écologiques indépendants / obstacles confirmés | Non établi | Ne remplacer cette inconnue ni par 953, ni par 1 069, ni par zéro |

Les répétitions exactes ne traitent pas les superpositions partielles. Les regroupements ne suppriment aucun événement et ne changent aucune géométrie. Les 953 groupes portent chacun les IDs d'événements, routes, matrices et mailles, les catégories brutes, ainsi qu'une référence aux données manquantes et à la qualification commune `qualification_ecologique_non_evaluee`.

| Famille géométrique | Événements | Routes distinctes dans la famille | Interprétation autorisée |
| --- | ---: | ---: | --- |
| `croisement_transversal` | 364 | 285 | Relation topologique au polygone de matrice ; franchissement écologique non établi |
| `intersection_ou_superposition` | 705 | 591 | Portions de voies rencontrant les matrices, souvent incluses dans leurs grands polygones ; pas autant de ruptures |
| Matrice « fragile, fortement sensible à la fragmentation » | 993 | 780 | Libellé source SRCE, **aucune traduction en enjeu fort** |
| Matrice « robuste, mais restant sensible à la fragmentation » | 76 | 73 | Libellé source SRCE, **aucune traduction en enjeu faible** |

Les effectifs de routes des familles ne sont pas additionnables : la même route peut appartenir à plusieurs familles. Les classes SRCE superposées ne constituent pas deux preuves écologiques indépendantes et ne sont pas, à elles seules, une contradiction sur une même affirmation.

| Catégorie routière brute | Événements | Tronçons routiers distincts concernés |
| --- | ---: | ---: |
| Route à 1 chaussée | 581 | 440 |
| Route empierrée | 179 | 131 |
| Chemin | 153 | 96 |
| Sentier | 116 | 95 |
| Rond-point | 27 | 17 |
| Route à 2 chaussées | 10 | 8 |
| Escalier | 3 | 2 |

Ces catégories servent à filtrer les observations, sans coefficient de pression. L'absence de candidat dans une autre catégorie ne démontre pas son innocuité. Les champs `ouvrage_connu` et `millesime` sont manquants sur les 1 924 routes ; Z n'atteste pas un niveau de franchissement. Les 16 corridors portent `sous_trame="-"`, un millésime 2014 et une précision non renseignée.

## Applicabilité scientifique : lecture documentaire, moteurs non exécutés

Références inchangées : [table D/S](table_decision_m2.md), [qualité amont](contrat_qualite_amont_m2.md) et [R1–R4](regles_actions_m2.md). Les formulations ci-dessous décrivent les possibilités actuelles ; elles ne simulent pas une entrée normalisée approuvée ni une sortie du moteur.

| Famille / règles | Entrées et conditions satisfaites | Conditions ou données manquantes | Résultat justifiable maintenant / validation humaine nécessaire |
| --- | --- | --- | --- |
| ENJ-01 | Aires de réservoir observées sur le support `H∩T` ; aire positive dans 15 mailles | Complétude attestée et pertinence temporelle | Aire observée affichable ; `enj_01_pct=NULL` sur 43 mailles. M1/M2 doivent documenter la couverture avant de valider le pourcentage |
| ENJ-02 | Matrices cartographiées et intersection mesurée sur les mailles | Complétude, sous-trame et portée fonctionnelle | Présence cartographique `true` dans 30 mailles, `NULL` dans 13 ; aucune absence confirmée ni continuité fonctionnelle déduite |
| Route–corridor | Événements et objets sources liés ; géométrie 2D et rattachement disponibles | Domaine/sous-trame, précision adaptée, contexte de franchissement, qualification externe | Observation `croisement_detecte` conservée. Ni `conflit_potentiel` ni `obstacle_confirme` promu ; revue locale nécessaire |
| Pression routière | Catégories et longueurs descriptives M1 disponibles | Trafic, exposition, espèces, niveaux et méthode de traduction | Contexte observable ; intensité de pression non évaluée, aucune équivalence sentier/route |
| D0 — hors champ | Sources localisées | Règle de domaine et preuve de non-applicabilité | Applicabilité écologique inconnue ; absence de couche ou de candidat ne justifie pas D0 |
| D1–D4 — insuffisances | Lacunes de preuve identifiées et provenance disponible | Domaine, méthode d'enjeux, QA positif/absence et contrôle de contradictions normalisés | Motifs documentaires : applicabilité inconnue, enjeu inconnu, qualification non évaluée. **Aucun numéro D attribué** faute de configuration de pilote approuvée ; M2/expert doivent construire les entrées réelles |
| D5–D10a — triage | Candidats géométriques disponibles | Enjeu catégoriel et méthode approuvés, preuve positive adaptée ou absence validée | Aucune priorité élevée/modérée/faible justifiée par ces seuls comptes ; validation méthodologique préalable |
| S — synthèse et priorité | 43 supports de surface positive, observations liées | Familles attendues et méthodes autorisées, approbateur, diagnostics et capacités de preuve validés | Priorité `non_calculee`, valeur `NULL`. Évaluation écologique partielle est une annotation documentaire ; aucun S ni `couverture_synthese` calculés |
| R1 / A04 — étude de franchissement | Candidats et couples sources identifiables | Sous-trame, QA, règle contextuelle/expertise, ouvrage et usages | Piste documentaire de revue des franchissements ; aucun statut `conditionnelle` ou `etayee_pour_examen` émis automatiquement |
| R2 / A01 — bocage | Longueurs de haies M1 agrégées, couverture déclarée non exhaustive | Géométrie du réseau reçue par M2, lacune structurale/topologique et méthode validée | Rupture bocagère non évaluable ; une densité ne déclenche pas R2 |
| R3 / A03 — friches | Agrégats Cartofriches descriptifs M1 | Sites et géométries vérifiables, voisinage/continuité pertinent selon méthode approuvée | Lien fonctionnel non évaluable ; co-présence dans une maille insuffisante |
| R4 / A02 — mares / milieux humides | Agrégats d'inventaires de zones humides M1 | Réseau de mares/habitats, couverture, hydrologie et isolement/lacune démontré | Non évaluable ; ni zéro PRAM ni surface d'eau OCS ne justifient création ou restauration automatique |

Les mentions M1 `complete_for_provisional_pilot` et les agrégats OCS ne remplacent pas une attestation de complétude écologique. Aucune règle de non-applicabilité, preuve de terrain ou indépendance n'est inventée. Les sorties documentaires n'attribuent aucun booléen de capacité de preuve aux moteurs.

## Quatre secteurs de démonstration

Les quatre mailles sont distinctes. Les critères de sélection sont géométriques et explicités dans [secteurs_demonstration.json](../data/derived/m2_diagnostics_20261110_01/secteurs_demonstration.json), qui contient le contexte, les textes élu/technicien, les pistes documentaires et **20 exemples réels** avec IDs sources, propriétaire canonique et empreinte WKB. Aucun nom communal n'est inféré du centroïde d'affichage. Les compteurs ci-dessous sont locaux et ne doivent pas être additionnés en total global.

| Secteur / maille_id | Observations / provenance | Explication pour un élu | Limite technicien et suite documentaire |
| --- | --- | --- | --- |
| S1 — `NORM-G1K-FLAT-R+006429-C+000497` | Maille entière ; 180 événements, dont 47 transversaux et 133 superpositions ; 104 tronçons, 134 géométries exactes, 170 propriétaires. Maximum de transversaux parmi les mailles entières | La carte identifie des lieux à examiner ; elle ne démontre pas une gêne pour la faune | Deux objets de matrice de même classe, 46 groupes de géométrie partagée. Examiner quelques ouvrages et le contexte écologique, sans recommandation A04 |
| S2 — `NORM-G1K-FLAT-R+006430-C+000496` | Fraction du support nominal 0,918598 ; 204 événements (62/142), 146 tronçons, 184 géométries ; sept catégories routières et deux classes de matrices | Les différentes voies n'ont pas toutes la même fonction ni le même effet ; la carte les conserve distinctes | Quatre objets de matrice, 20 groupes partagés ; trafic et franchissabilité inconnus. Faire préciser usages, niveaux et sous-trames |
| S3 — `NORM-G1K-FLAT-R+006426-C+000500` | Fraction 0,503952 ; 81 événements (35/46), 61 tronçons, 76 géométries, 80 propriétaires ; cinq événements touchent la frontière du pilote, cinq groupes partagés | Des lignes répétées ou liées à plusieurs mailles ne sont pas plusieurs obstacles | Maille partielle : pas de classement sur compte brut ni densité. Revoir les objets et conserver les liens/canonical owners ; cinq événements de frontière et cinq groupes partagés sont deux comptes distincts |
| S4 — `NORM-G1K-FLAT-R+006426-C+000497` | Maille entière ; zéro événement, ENJ-02 `NULL` ; CSV M1 : 11 objets routiers et 3 660,935459 m de voies | Zéro observation ne veut pas dire zéro risque : des routes existent mais la couverture des continuités n'est pas attestée | Pas de candidat à examiner ici sur ce lot, aucune absence démontrée. Demander couverture et contexte local avant toute conclusion |

Provenance commune : conflits/mailles consolidés `m2_frontiere_20261109_01`, enjeux `m2_reel_20261109_01`, contexte agrégé `m1_reference/sub_indicateurs.csv`. Les IDs complets des observations de chaque maille sont conservés. Les trois premiers secteurs illustrent des observations, le quatrième une absence d'observation ; **les quatre, comme les 43 mailles, restent insuffisamment documentés pour une priorité concluante**. ENJ-01 reste NULL et aucune action automatique n'est calculée pour ces secteurs.

## Transmission et décisions restantes

La [proposition concrète M4](transmission_interne_m2_m4_20261110.md) décrit les GeoPackages, les jointures et les champs affichables. La [synthèse M5](synthese_scientifique_m2_m5_20261110.md) fournit un texte réutilisable. Aucun envoi externe ni export public n'a été effectué ; `test_data=False` reste bloqué dans l'exporteur existant.

Décisions humaines nécessaires : M1/M2 doivent fournir les attestations de couverture et préciser l'actualité/précision des sources ; un expert doit établir les sous-trames, la méthode d'enjeux et la portée des croisements ; l'équipe doit approuver le périmètre et les méthodes du pilote avant D/S ; gestionnaires/expert doivent documenter quelques franchissements ; M4 doit confirmer ce mode d'ingestion interne et l'affichage explicite des inconnues. Les données de réseau bocager, friches, mares et leurs méthodes restent nécessaires pour R2–R4. Ces limites bloquent une conclusion écologique, pas la consultation interne des observations.

## Livraison et vérifications effectuées

Huit fichiers nouveaux, aucun fichier préexistant modifié :

- Ce compte rendu : `docs/diagnostics_ecologiques_reels_m2_20261110.md`.
- `docs/transmission_interne_m2_m4_20261110.md`.
- `docs/synthese_scientifique_m2_m5_20261110.md`.
- `data/derived/m2_diagnostics_20261110_01/situations_geometriques.json` : familles, 953 groupes et qualification documentaire commune.
- `data/derived/m2_diagnostics_20261110_01/mailles_observees.json` : observations et inconnues des 43 mailles.
- `data/derived/m2_diagnostics_20261110_01/secteurs_demonstration.json` : quatre cas et leurs exemples.
- `data/derived/m2_diagnostics_20261110_01/manifest_ingestion_interne.json` : chemins, couches, schémas SQLite, versions, runs, logiciels et SHA-256.
- `data/derived/m2_diagnostics_20261110_01/execution/preparer_diagnostics.py` : préparation descriptive reproductible dans l'environnement M2, sans import du moteur de détection ou D/S ; écrit exclusivement de nouveaux fichiers.

La préparation a été exécutée dans l'environnement SIG M2 isolé, puis les quatre JSON stricts, empreintes, clés et 20 liens documentaires du livrable ont été vérifiés : 43 mailles, 1 069 événements, 1 184 liens, un propriétaire par événement, 953 groupes contenant chacun leurs événements sources. Les 20 exemples correspondent aux IDs, couples sources et empreintes WKB des événements d'origine. Aucune nouvelle analyse d'intersection, aucun lancement de `run_enjeux.py`, `run_conflicts.py` ou des règles de priorité. **Zéro test pytest relancé**, conformément à la demande. Les 281 fichiers préexistants, suivis ou non, sont restés identiques octet par octet ; branche et HEAD inchangés. Aucune opération d'intégration Git.
