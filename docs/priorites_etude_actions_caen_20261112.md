# Correction opérationnelle — priorités d'étude des actions Caen et nord

**12 novembre 2026.** La vue principale repart de V1 et devient **« Priorités d'étude des actions écologiques »** : **27 rouges, 33 orange, 9 jaunes et 32 grises**. L'extension V3b est conservée dans l'historique, sans adoption automatique. L'OCS GE enrichit les observations mais ne démontre ni continuité fonctionnelle ni pertinence d'une restauration.

Le lot autonome corrigé est :

`data/derived/caen_et_nord_actions_20261112_01/RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1.zip`

Son empreinte est dans `.zip.sha256` ; le reçu après extraction neuve dans `validation_extraction_actions.json`. Les versions et résultats précédents sont conservés.

## Décisions territoriales réellement proposées

| Couleur / rang d'étude | Mailles | Action principale / orientation |
| --- | ---: | --- |
| Rouge — priorité 1 | 27 | A04/R1 : étudier en premier la perméabilité et les possibilités de franchissement. Indices V1 : route carrossable en service au sol, matrice fragile et surface de réservoir dans la maille. |
| Orange — priorité 2 | 33 | A04/R1 : évaluer les croisements documentés pour une éventuelle étude de franchissement, en vérifiant catégorie, service, niveau et ouvrages existants. |
| Jaune — priorité 3 | 9 | Examiner la préservation des éléments SRCE et leur état. Aucune restauration de catalogue sélectionnée sans ses propres préconditions. |
| Gris — non évaluable | 32 | Aucune intervention choisie. L'existence de végétation OCS GE, haies ou sites Cartofriches ne lève pas l'indétermination du choix d'intervention. |

**60 études principales A04**, neuf orientations de préservation et 32 décisions non évaluables. Les 41 mailles sans action principale ne sont donc pas toutes « grises » : neuf ont une orientation de préservation mais aucune restauration A01–A04 qualifiable. Aucun bénéfice comparé, niveau de risque confirmé ou urgence de travaux n'est calculé.

La sélection est une **décision indicative d'instruction**, conformément à la correction demandée, pas une qualification positive de R1. Ses indices sont vérifiés dans les justifications V1 existantes et les événements locaux ; le besoin de construction n'est jamais présumé. Les quatre options par maille gardent leur statut scientifique, leur justification, les observations, les sources et les conditions manquantes.

Ce compte d'A04 est **par maille**, pas un nombre de projets indépendants ni d'ouvrages à construire. Les mêmes événements peuvent être partagés ; leurs identifiants et comptes exclusifs restent disponibles pour regrouper les dossiers, sans calcul géométrique ni seuil de regroupement ajouté.

## Préconditions et pistes préservées

Les 165 pistes historiques sont toutes traçables par identifiant stable, maille/grille/territoire, règle/action, pointeur vers l'enregistrement d'origine et empreinte. Elles se répartissent en **60 R1, 50 R2, 35 R3, 20 R4**. Les 60 R1 sont reliées à l'étude principale ; les **105 autres restent à qualifier**, sans activation automatique. Les huit anciennes pistes R3 dans les mailles grises restent consultables mais ne choisissent aucune intervention.

La présence de haies, de friches ou d'eau ne suffit pas. R2/A01 requiert une lacune structurale/topologique et une sous-trame pertinente ; R3/A03 une friche éligible avec relation à une continuité selon une méthode documentée ; R4/A02 un déficit de réseau d'habitats humides et un contexte hydrologique adaptés. Ces préconditions ne sont pas documentées dans ce lot : **aucune restauration complémentaire n'est retenue**. Une orientation de préservation en jaune n'est pas artificiellement rattachée à une fiche M5 manquante.

Chaque fiche expose le rang d'étude, le diagnostic territorial, l'action principale ou son absence motivée, les options complémentaires/non sélectionnées, les justifications, les conditions écologiques et techniques avant travaux, et la priorité D/S distincte. Les étapes d'A04 comprennent la lecture des segments XY, la vérification des ouvrages/niveaux, la qualification des déplacements/espèces et l'examen des options avec le gestionnaire.

## Invariants scientifiques et géographiques

Les **101 mailles et géométries**, **5 336 événements admis**, **une quarantaine**, **60 mailles avec événements / 41 sans**, les diagnostics techniques et observations sont inchangés. Aucun détecteur, agrégateur, calcul ENJ ou D/S de production n'a été relancé. Les résultats scientifiques R1–R4 restent **404 non_evaluable / A2** et les **101 priorités D/S indéterminées**. Méthodes, règles D/S/R1–R4, NULL et contrats publics sont préservés. Aucune recommandation de travaux validée.

Les résumés élus sont réorientés vers l'action, avec conservation du résumé V2 d'origine dans chaque fiche. Les 165 descriptions d'origine restent intactes dans `actions`, mais ce champ ne constitue pas la sélection courante. Les alias actifs `action_ids` / `action_ids_a_etudier` contiennent uniquement les études sélectionnées, A04 pour les 60 rouges/orange et [] ailleurs ; leurs anciennes valeurs sont conservées séparément. Cette distinction évite qu'une vieille piste soit affichée comme intervention recommandée en gris.

## Adaptation M3/M4 et vérification

La branche M3 inspectée est `feat/m3-frontend-reconnect-v61`, commit **94eef5b8f17dc68af22c323603ec2623b2b58ce1**. Une adaptation autonome de huit fichiers est fournie dans `integration/m3_priorites_etude_actions.patch`. Elle conserve l'application React/MapLibre, ajoute la nouvelle légende et la note visible, conserve la vue D/S séparée et affiche les décisions au clic. Elle a été appliquée et compilée dans des copies temporaires ; aucune branche de M3 n'a été modifiée. Ne pas empiler les anciens patches V1/V2.

La légende est celle demandée : rouge priorité 1, orange priorité 2, jaune priorité 3, gris décision non évaluable. La note visible est : « Classement indicatif fondé sur les données cartographiques. Les aménagements nécessitent une validation écologique et technique avant réalisation. » Aucun vocabulaire de risque confirmé ou d'urgence de travaux n'est substitué.

M4 dispose des GeoJSON et fiches habituels, d'un fichier normalisé `priorites_etude_interventions.json`, de `pistes_investigation_trace.json`, d'un CSV des 101 décisions et d'un routeur interne facultatif. Le complément de format est explicitement versionné ; aucun contrat public n'est remplacé. L'ingestion garde les clés `(territory_id, grid_version, maille_id)` et `conflit_id` pour les événements. `test_data=False` reste inchangé ; les serveurs de revue sont limités à la boucle locale, et un ancien lot V3b est refusé comme vue active.

Contrôles de la livraison initiale :

- **1 456 tests Python réussis**, dont 19 cas de priorité d'étude ; 40 avertissements existants consignés.
- Schéma interne validé pour les 101 décisions : chaque action affichable possède un statut et une justification ; aucune restauration/travaux activés artificiellement.
- Build TypeScript/Vite réussi et tests M3 de séparation TEST/réel/versions réussis ; avertissement de taille de bundles conservé.
- Douze contrôles du routeur FastAPI aux versions M4 : 101 mailles/décisions, 165 pistes, cas rouge/gris, erreur de portée, lecture seule, restrictions locales et refus de V3b.
- Navigation Chrome réussie sur les quatre couleurs : A04 en rouge/orange, absence motivée en jaune/gris, note visible et D/S séparée ; aucune erreur JavaScript. Captures dans rapports.
- Vérification autonome du ZIP après extraction dans un dossier neuf ; empreintes, géométries, événements, liens, profils scientifiques, trace des 165 pistes et non-sélections contrôlés sans calcul SIG.

Le ZIP contient un rejeu de décision **sans SIG ni moteur scientifique**, et un vérificateur autonome avec la bibliothèque standard Python. Les sources/versions/licences et observations OCS GE restent disponibles en contexte. Aucun fichier historique, calcul validé ou archive antérieure n'a été écrasé.

## Transmission

Extraire le ZIP et lancer `python3 -B verifier_lot_actions.py`. Suivre ensuite `README.md` et `integration/README.md` pour M3/M4. Un message prêt à transmettre est inclus. Le raccordement à la branche applicative doit encore être réalisé par l'équipe ; aucun déploiement n'est affirmé. Le catalogue M5 complet et les validations écologiques/techniques restent nécessaires avant réalisation de travaux.

La livraison initiale a été produite avant son versionnement. La présente sauvegarde porte uniquement sur les scripts, le schéma, les exemples et ce rapport ; elle n’autorise aucune fusion ni diffusion des données. Le lot demeure interne et ses garde-fous sont conservés.

## Sauvegarde du code M2 et dépendance applicative

Les fichiers sous `integration/m3_m4_caen_actions_20261112/` sont des références
historiques contre le commit M3 `94eef5b8…`, et non des modifications à réappliquer
automatiquement sur l’application actuelle ou sur la PR #5. Le générateur exige
une sortie nouvelle sous `data/derived/` du dépôt M2. Les journaux de validation
du scellement sont configurables via `M2_VALIDATION_LOG_ROOT` ; un lot déjà scellé
est refusé avant toute écriture. Ces protections ne modifient ni les décisions
scientifiques ni les sorties scellées.

La PR #5 possède son adaptation frontend/backend indépendante. La sauvegarde M2
fournit la traçabilité de la politique, des interfaces et de la version
`caen6-priorites-etude-actions-20261112-1` ; elle ne fusionne aucun code applicatif.
L’autorisation des exports minimisés et leur publication distincte restent
nécessaires pour rendre les nouvelles décisions publiques. Le catalogue M5 et
les validations avant travaux demeurent des préconditions séparées.

Contrôle avant sauvegarde Git : **1 458 tests réussis**, dont **21 tests ciblés**
de priorité d’étude et de protection des lots scellés (40 avertissements existants
consignés). Le patch de référence, avec lignes de contexte vides normalisées, a été reproduit à l’identique dans un dossier
ignoré. Les 101 décisions ont été rejouées sans SIG ; les empreintes du lot scellé,
les 5 336 événements admis, la quarantaine, les 165 pistes et les valeurs D/S
restent inchangés. Aucun export public n’est produit par cette sauvegarde.
