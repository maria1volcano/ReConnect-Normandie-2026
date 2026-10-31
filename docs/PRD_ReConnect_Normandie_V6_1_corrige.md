## DOCUMENT DE RÉFÉRENCE DU PROJET / PRD V6.1

## ReConnect Normandie

PRODUCT REQUIREMENTS DOCUMENT — V6.1 | 30 octobre 2026

Datathon Normandie 2026 — Biodiversité et activités humaines

Statut : version finale proposée à l’équipe pour exécution, sous réserve de la vérification des données et des règles

Équipe : cinq membres | PRODUIT ET ÉCRIT TERMINÉS : 11 novembre 2026 au plus tard | ENVOI DE L’ÉCRIT : 12 novembre 2026 |

JURY : 23 novembre 2026

Promesse produit. ReConnect Normandie rend visibles et compréhensibles les secteurs où des continuités écologiques cartographiées rencontrent des pressions humaines, qualifie les conflits potentiels et propose une liste argumentée de pistes d'action à examiner, sans prédire leur efficacité biologique ni désigner une solution unique optimale.

## Fiche de décision — engagements de la V6.1

Règle absolue de calendrier : la version à rendre est prête, testée, relue et assemblée le mercredi 11 novembre au plus tard. Le jeudi 12 novembre ne comporte aucun développement ni rédaction substantielle : M5 envoie l'écrit officiel, conserve la preuve de dépôt et avertit l'équipe. Le 11 novembre étant férié, les travaux indispensables sont en pratique clos le mardi 10 novembre à 18 h ; le 11 sert uniquement au contrôle de complétude, à la génération finale des fichiers et à la marge de sécurité.

| Objet | Décision commune | Limite et responsabilité |
| --- | --- | --- |
| Concept | Fragmentation des continuités | Aucun effet écologique simulé ou |
|   | écologiques, prédiagnostic explicable | rendement annoncé |
|   | et pistes de reconnexion |   |
| Carte | Normandie visible ; diagnostics réels | Hors pilote : « non analysé », jamais « |
|   | et vérifiés d'abord sur un pilote choisi | faible priorité » |
|   | selon les données |   |
| Géométrie | Grille hexagonale régulière, cible | M1 construit, M2 valide ; pas de |
|   | initiale ~1 km² en Lambert-93 ; | fausse précision |
|   | événements de conflits stockés |   |
|   | séparément |   |
| Analyse | Enjeux écologiques, | M2 spécifie ; M1 fournit les sous- |
|   | fragmentation/conflits potentiels, | mesures géographiques réutilisables |
|   | pressions humaines, fiabilité |   |
| Priorité | Une couleur par maille, classe | Table de règles, pas score de |
|   | synthétique de priorité d'examen | performance, urgence temporelle |
|   | expliquée au clic | distincte |
| Conflits | Croisement géométrique ≠ conflit | Terminologie et limites visibles, |
|   | potentiel qualifié ≠ obstacle confirmé | approche inspirée du Cerema |
| Actions | 12 fiches homogènes, groupées par | Une maille peut recevoir zéro, une ou |
|   | catégories ; 4 règles automatiques | plusieurs pistes ; ne jamais prétendre |
|   | MVP (faune, haies, friches, mares) | avoir évalué les 12 automatiquement |
| Implémentation | M2 définit et contrôle les règles ; M4 | M4 ne modifie pas les hypothèses |
|   | code le moteur générique | scientifiques sans accord M2 |
|   | d'application/présentation des règles |   |
| M5 | Responsable de l'écrit, de | Contribution rédactionnelle et tests |
|   | l'intégration des fiches et de la | répartis sur toute l'équipe |
|   | recette ; développe un module React |   |
|   | autonome « Catalogue / Méthode » |   |
| Technique | Python/GeoPandas, | Export statique complet et démo de |
|   | GeoPackage/Parquet, GeoJSON, | secours obligatoires |
|   | React/MapLibre ; FastAPI légère si |   |
|   | déjà opérationnelle |   |


| Objet | Décision commune | Limite et responsabilité |
| --- | --- | --- |
| Contrôles | Cinq campagnes qualité compactes et | Pas de dispositif de CI ou |
|   | un contrat JSON/GeoJSON unique | versionnement complexe pour un |
|   |   | MVP de deux semaines |
| Numérique responsable | Mesures de volume, temps de | Valeurs relevées avant diffusion, pas |
|   | chargement, requêtes, accès et | de « gain carbone » inventé |
|   | sobriété du traitement |   |
| Dates | 10/11 18 h : gel ; 11/11 : paquet final | M5 contrôle la remise officielle ; |
|   | prêt ; 12/11 : envoi écrit ; 23/11 : | l'écrit n'attend pas la démo du 23 |
|   | pitch |   |

## 1. Problème et opportunité

## 1.1 Constat

Les continuités écologiques relient des réservoirs et des habitats. Les routes, l'urbanisation, l'artificialisation, certaines transformations agricoles, des ouvrages hydrauliques ou l'éclairage peuvent engendrer des pressions différentes selon les milieux et les espèces. Les données utiles existent, mais sont dispersées et hétérogènes. Une commune sans moyens SIG peut difficilement passer d'une carte à une liste compréhensible de points de vigilance et d'études possibles.

La détection cartographique ne constitue ni une preuve de collision, ni une mesure directe de fonctionnalité écologique, ni une autorisation de travaux. La V6 traite les résultats comme des prédiagnostics soumis à vérification locale.

## 1.2 Question centrale

Parmi les secteurs normands documentés, lesquels méritent une vérification en priorité au regard des continuités écologiques et des pressions humaines observables, et quelles familles d'actions pourraient être étudiées pour chacun ?

## 1.3 Utilisateurs et bénéficiaires

- Utilisateur principal : technicien de commune ou intercommunalité chargé d’environnement, d’aménagement ou de continuités écologiques.

- Utilisateur secondaire : élu local, association, gestionnaire d'espace naturel, bureau d'études.

- Bénéficiaires finaux : habitants et biodiversité normands, par une meilleure préparation des décisions publiques.

## 1.4 Proposition de valeur, par ordre

- Repérer des zones nécessitant un examen plus approfondi.

- Consulter plusieurs actions potentielles, les conditions qui justifient leur affichage et les informations manquantes.

- Identifier quelles données et quelles pressions expliquent le signal.

- Visualiser une priorité de vérification synthétique, avec justification au clic.

- Exporter ou communiquer un diagnostic traçable ; ne jamais remplacer une étude de terrain.

## 1.5 Succès observable

Un élu sans expertise SIG peut ouvrir la carte, distinguer les zones analysées, cliquer sur une maille, comprendre en moins d'une minute pourquoi celle-ci est signalée et voir des pistes à étudier. Un technicien peut retrouver les couches, dates, méthodes et limites ayant produit le diagnostic.

## 2. Périmètre fonctionnel et feuille de route

## 2.1 P0 — MVP prêt au plus tard le 11 novembre (travaux essentiels clos le 10)

- Carte affichant toute la Normandie et signalant clairement le pilote réellement calculé.

- novembre. Pilote choisi selon couverture, cohérence des échelles et capacité à tester les quatre règles ; choix documenté le 2

- distincts des mailles. Grille hexagonale stable (~1 km² initialement) ; cartes et fiches liées à des identifiants pérennes ; événements de conflit

- nécessaires aux règles disponibles ou état « non évaluable » justifié. Sources réelles de base : trame verte et bleue, réseau routier, occupation des sols ; couches métier haies, friches, mares


- Quatre familles d'indicateurs ; valeurs numériques et unités conservées lorsqu'elles existent ; null explicite sinon.

- aux mailles. Croisements détectés sur les géométries d'origine ; qualification prudente inspirée des étapes du Cerema ; rattachement

- temporelle (si donnée) et fiabilité visibles au clic. Classe de priorité d'examen unique pour la carte, fondée sur règles documentées, avec enjeux, pressions, menace

- plusieurs pistes lorsque les conditions sont satisfaites ; aucune comparaison d'efficacité. Catalogue de douze fiches de même qualité éditoriale ; moteur évaluant quatre familles automatiquement et listant

- limites. Parcours complet sur données réelles : carte → secteur → justification → actions conditionnelles/étayées → sources et

- même structure. React + MapLibre ; service FastAPI si le code existant est opérationnel et léger ; exports statiques de secours avec la

- questions, relu et finalisé. Module « Catalogue / Méthode » développé par M5, intégré par M3 ; texte de l'écrit officiel répondant aux cinq

- secours. Cinq campagnes de tests et mesures de sobriété, guide de démarrage, jeux diffusables/licences et vidéo ou captures de

- assemblé. Jeudi 12 : envoi de l'écrit officiel sans production supplémentaire. Mardi 10 novembre, 18 h : gel fonctionnel et copie candidate prête. Mercredi 11 : dernière vérification et paquet final

Clause de preuve : une automatisation est « livrée » lorsque la règle existe, traite les données présentes, peut retourner étayée,

conditionnelle, non retenue ou non évaluable, et passe les tests positifs/négatifs/manquants. Si le territoire n'a pas de données métier exploitables, aucune fausse recommandation n'est fabriquée : le manque est signalé et l'objectif des quatre cas réels est qualifié. Toutes les règles doivent néanmoins être testables sur des jeux d'essai explicitement marqués TEST.

## 2.2 P1 — Améliorations après remise de l’écrit, du 13 au 20 novembre

Amélioration de la qualité, tests utilisateurs, extension contrôlée à un autre secteur pilote ou à plusieurs départements, enrichissement des couches, amélioration de performances, filtres thématiques, exports utiles, consultation assistée de professionnels. Aucune extension ne doit compromettre la version gelée et démontrable.

## 2.3 P2 — Après le Datathon

Calcul régional exhaustif, automatisation scientifique des douze familles, modèles par espèces ou groupes écologiques, intégration de données terrain et de trafic, comparaison d'effets avant/après validés, analyse économique et foncière, suivi dans le temps, intégration pérenne aux systèmes territoriaux.

## 2.4 Exclusions explicites du MVP

Aucune prédiction chiffrée de retour d'espèces, aucun pourcentage de bénéfice écologique, aucun classement prétendument optimal d'aménagements, aucune localisation d'espèce sensible diffusée, aucun avis réglementaire ni travaux préconisés sans étude de faisabilité.

## 3. Territoire pilote, choix des mailles et couverture

## 3.1 Sélection du pilote — décision datée au 2 novembre

Un pilote n'est pas choisi sur le nombre brut de fichiers. M1 et M2 examinent plusieurs candidats normands (dont, sans priorité automatique, l'estuaire de l'Orne) sur la couverture TVB, la présence de routes, la finesse des sols, la disponibilité de couches fiables pour haies, friches et mares, la diversité des cas, les années de référence et la possibilité de contrôle manuel.

Conditions minimales : continuités et pressions superposables ; types de géométrie et licences compris ; quatre règles testables sur un ou plusieurs secteurs de l'emprise de démonstration ; aucun défaut majeur de résolution ignoré. Si un seul périmètre compact ne fournit pas quatre cas robustes, documenter une zone pilote élargie ou plusieurs sites d'essai identifiés, sans présenter l'ensemble comme un diagnostic régional.

Livrable de décision : docs/pilote_decision.md avec candidats, justification, limites, emprise, date, avis GO/NO-GO et

responsable.

## 3.2 Grille hexagonale et représentativité

- précision écologique. Grille régulière construite en Lambert-93 (EPSG:2154) ; surface nominale cible environ 1 km², non assimilée à une


- orientation, méthode de découpe et version documentées. Identifiant maille_id déterministe et invariant tant que version de grille, emprise et taille ne changent pas ; origine,

- ratios sont normalisés sur la surface effectivement étudiée ; ne pas compter les portions hors territoire. Hexagones en bordure découpés pour l'affichage, avec surface réelle de couverture et méthode de calcul conservées. Les

- autre résolution ou à un décalage de grille si faisable. M1 construit et versionne la géométrie ; M2 valide la taille au regard des échelles des sources et teste la sensibilité à une

- exclusives. Une maille peut présenter plusieurs pressions et plusieurs conflits ; ses étiquettes ne doivent pas être mutuellement

- exportées en longitude-latitude WGS84/CRS84 (EPSG:4326 en pratique) pour la carte. Les calculs de surfaces et distances se font en mètres (EPSG:2154). Les sorties GeoJSON compatibles RFC 7946 sont

## 3.3 Trois objets géographiques différents

- Sources réelles : routes, corridors linéaires ou surfaciques, haies, habitats, sols, mares, friches.

- 1. 2. géométrie peut être un point ou un segment représentatif, pas nécessairement une rupture avérée. Événements candidats : géométries de croisements ou de proximité, conflit_id, sources et statut d'évidence ; la

- 3. Mailles de diagnostic : maille_id, indicateurs agrégés, priorité, qualité et liste des conflits liés.

Le moteur ne conclut jamais à un croisement à partir de la seule coprésence de deux objets dans une maille. Il teste leurs géométries originales, puis rattache le résultat à une ou plusieurs mailles. Une règle stable de comptage des événements traversant plusieurs hexagones évite les doublons.

## 3.4 Portée publique des résultats

Affichage régional de navigation ne signifie pas couverture régionale du calcul. En dehors du pilote, montrer clairement « analyse non réalisée ». À l'intérieur, distinguer « calculé », « données insuffisantes » et « aucun conflit identifié selon les règles ». Pas d'illusion de précision supérieure à l'échelle d'utilisation des couches TVB.

## 4. Données et stratégie d'accès — responsabilité M1, validation M2

| Groupe | Référentiels candidats | Usage prioritaire | Contrôle obligatoire |
| --- | --- | --- | --- |
| P0 commun | DREAL TVB / SRCE- | Réservoirs, corridors, sous- | Échelle d'emploi, |
|   | SRADDET | trames | millésime, géométrie, sens |
|   |   |   | des attributs |
| P0 commun | IGN BD TOPO | Routes, classes de voies, | Type, géométrie, doublons, |
|   |   | franchissements potentiels | année, ouvrages existants |
|   |   |   | si connus |
| P0 commun | IGN OCS GE | Sol couvert, usages et | Nomenclature, millésime |
|   |   | artificialisation | et couverture ; CORINE |
|   |   |   | seulement en repli |
| Requis R1 | SIPAF si exploitable ; BD | Passages à faune existants, | Couverture incomplète ≠ |
|   | TOPO | statut d'ouvrage | absence d'ouvrage |
| Requis R2 | BD Haie / bocage + sols | Continuités bocagères et | Dates, précision, topologie, |
|   |   | lacunes candidates | interprétation prudente |
|   |   |   | des « vides » |
| Requis R3 | Observatoire EPFN des | Friches candidates proches | Accès réel, qualité de |
|   | friches + sols | de continuités | localisation, statut inconnu |
|   |   |   | du foncier |
| Requis R4 | PRAM / CEN / eau / zones | Mares ou réseaux | Accès réel, géométrie, |
|   | humides | d'habitats humides | exhaustivité et conditions |
|   |   |   | hydrologiques |
| Enrichissement | BD Forêt, INPN/Natura | Contexte et pressions | Ne pas confondre zonage, |
|   | 2000, RPG, ODIN, éclairage | supplémentaires | présence réelle d'espèce et |
|   |   |   | fragmentation |


Règle contractuelle : M1 tient inventaire_sources.csv (identifiant, producteur, URL, licence, version, année, emprise, géométrie, attributs, CRS, restrictions, taille, statut téléchargé/vérifié). Les jeux présents dans un catalogue mais non téléchargés et testés restent marqués candidat.

Les données sensibles restent non diffusées ; les données d'observations naturalistes ne sont pas exportées sous forme de points sensibles. Aucune donnée manquante n'est transformée silencieusement en zéro. Un fichier source brut n'est jamais écrasé.

## 5. Méthode de prédiagnostic — responsabilité scientifique M2

## 5.1 Chaîne de calcul, sans formalisme mathématique lourd dans le PRD

M1 inventorie et harmonise → M2 contrôle les couches reçues et calcule sur les géométries sources → détecte des événements candidats → associe des informations aux mailles → qualifie les indicateurs et leur fiabilité → classe la priorité d'examen → évalue les règles d'actions → exporte les objets normalisés → M4 sert les objets → M3 les affiche et les explique.

Le détail des formules, paramètres, seuils, analyses de sensibilité, bibliographie et éventuelle étude de la taille effective de maille du SDES appartient au dossier méthodologique séparé de M2. Le PRD impose uniquement les entrées, sorties, garanties de transparence et tests.

## 5.2 Quatre familles d'indicateurs

| Famille | Sorties attendues | Interprétation autorisée |
| --- | --- | --- |
| Enjeux écologiques documentés | Présence/part de réservoirs, | Présence d'enjeux cartographiés, pas |
|   | corridors, habitats et statuts si | abondance réelle d'espèces |
|   | disponibles ; sous-trame |   |
| Fragmentation et conflits | Croisements distincts, contexte | Conflits potentiels cartographiques, |
|   | d'infrastructure, continuités | pas rupture fonctionnelle confirmée |
|   | potentiellement interrompues, types |   |
|   | d'événements |   |
| Pressions humaines | Routes, part d'occupation | Conditions de pression, pas causalité |
|   | artificialisée, usages et autres | biologique automatique |
|   | pressions géolocalisables si |   |
|   | interprétables |   |
| Fiabilité | Couverture, années, échelle d'usage, | Capacité du jeu de données à |
|   | licences, champs manquants, qualité | supporter le diagnostic |
|   | des géométries, statut des couches |   |

Les indicateurs bruts gardent leur unité et la règle exacte dans docs/methode_m2.md. Aucune combinaison n'est autorisée

sans justification. Les observations naturalistes sous-échantillonnées ne produisent pas de « zéro biodiversité ».

## 5.3 Niveaux de conflit inspirés de la démarche Cerema

| Statut | Conditions générales | Texte utilisateur |
| --- | --- | --- |
| croisement_detecte | Intersection géométrique réelle de | « Croisement cartographique détecté |
|   | couches compatibles | » |
| conflit_potentiel | Intersection + éléments disponibles | « Conflit potentiel à vérifier » |
|   | susceptibles d'indiquer une gêne |   |
|   | (type d'axe, sous-trame, contexte, |   |
|   | ouvrage recensé, etc.) |   |
| obstacle_confirme | Preuve externe ou expertise | « Obstacle documenté » |
|   | explicitement référencée |   |
| non_concluant | Source manquante, échelle | « Données insuffisantes pour |
|   | inadéquate ou situation indécidable | conclure » |

Une absence de passage à faune dans SIPAF ne confirme pas son inexistence. Des routes différentes, des voies ferrées ou ouvrages hydrauliques ne doivent pas recevoir le même statut par défaut. Les critères réellement disponibles restent déclarés dans les données.


## 5.4 Une couleur principale, des critères détaillés au clic

La carte affiche une seule classe synthétique priorite_examen : elevee, moderee, faible, indeterminee. Elle traduit la priorité d'une vérification préparatoire à l'action, pas une obligation d'investissement ou de travaux. La fiche détaille les trois dimensions : (1) enjeux écologiques documentés, (2) pressions et conflits, (3) menace ou urgence temporelle seulement si une donnée datée l'étaye. La fiabilité est une condition de classement indépendante : si les sources essentielles sont insuffisantes, la classe reste indeterminee, même en présence d'une pression apparente. Le moteur utilise une table de règles explicites, pas un score global pondéré prétendu scientifique. Des classes peuvent être attribuées lorsque critères et seuils documentés sont satisfaits ; les tests doivent inclure l'analyse de sensibilité. La structure de la table de décision est figée le 3 novembre ; les seuils numériques, qui exigent les distributions réelles, sont calibrés le 5 et gelés au plus tard le 6 novembre. Le 9 n’autorise que la correction d’erreurs démontrées. Les règles et limites sont publiées dans la note M2 sans détailler toute la recherche mathématique dans le PRD. Règle anti-circularité : la « priorité d'examen » est un résultat, jamais une variable utilisée pour se calculer elle-même. L'absence

de menace temporelle documentée ne signifie pas « urgence faible » mais « non évaluée ».

## 5.5 Diagnostics multiples et état des données

Un secteur peut avoir diagnostics=["croisement_routier", "interface_artificialisee"] en même temps. La qualité des données est affichée à part (suffisante, partielle, insuffisante). Pas d'étiquette exclusive effaçant les pressions concurrentes.

Les données partielles ne déclenchent une règle que si le sous-ensemble indispensable est valide.

## 6. Catalogue des douze familles et moteur de pertinence

## 6.1 Deux objets à ne jamais confondre

- **Catalogue :** douze fiches détaillées, toutes structurées avec le même niveau d'information, indépendamment du territoire consulté.
- **Moteur local :** quatre règles automatiques MVP examinant la pertinence géographique de certaines familles pour une maille donnée. Une maille peut recevoir zéro, une ou plusieurs pistes ; les huit autres familles restent consultables, mais non évaluées automatiquement.

Aucune action n'est annoncée comme « la plus performante ». Les actions évaluables sont regroupées par statut de pertinence : `etayee_pour_examen`, `conditionnelle`, `non_retenue_par_regle`, `non_evaluable`. `non_retenue` et `non_evaluable` ont des sens différents et ne doivent pas être mélangés.

## 6.2 Quatre familles automatiquement évaluées dans le MVP

R1 — Franchissement routier de la faune. Entrée : intersection réelle route/corridor, type de corridor et type de route si disponibles ; renseignement SIPAF/ouvrages si disponible. Déclencheur : conflit routier candidat documenté ; sortie : étudier la franchissabilité et, le cas échéant, un aménagement. Contre-exemples : aucun croisement ; géométries incompatibles. Réserves : ouvrage déjà présent, trafic et espèces non connus. R2 — Restauration de haies. Entrée : réseau de haies daté, paysage bocager et occupation des sols, sous-trame pertinente. Déclencheur : lacune documentée dans une continuité bocagère à étudier, pas simple « faible densité = besoin de planter ». Contre-exemples : réseau déjà continu, couche incomplète, contexte incompatible. Réserves : propriété, contraintes agronomiques, nature et qualité écologique des haies. R3 — Renaturation de friches. Entrée : géométries fiables de friches, voisinage d'un réservoir/corridor et contexte de sol. Déclencheur : site recensé susceptible d'être étudié pour restaurer une continuité. Contre-exemples : site non reconnu, statut imprécis, éloignement selon règle non satisfaite. Réserves : pollution, usages, foncier, valeur écologique actuelle d'une friche. R4 — Mares / zones humides. Entrée : inventaire géolocalisé de mares et habitats humides, continuités de la trame bleue, contexte hydrologique dans la limite des données disponibles. Déclencheur : lacune ou isolement potentiel documenté d'un réseau d'habitats humides ; piste : étude de conservation, restauration ou création conditionnelle, sans désigner l'emplacement exact. Contre-exemples : données non exhaustives ; absence de justification hydrologique. Réserves : hydrologie, espèces, qualité de l'eau, risque de création inadaptée. Pour chaque R1–R4, M2 livre la spécification métier (données nécessaires, règle explicite, déclencheurs et états, contre-exemples, limites). M4 implémente le moteur d’évaluation, vérifie les quatre familles sur des exemples TEST positifs, négatifs et non évaluables, puis l’exécute sur les résultats réels de M2 ; M2 contrôle le comportement scientifique. Les exemples réels ne sont

revendiqués que lorsqu’ils existent dans les sources effectivement ouvertes.


## 6.3 Fiches homogènes pour les douze familles

Chaque fiche catalogue comporte les onze champs obligatoires : code, nom, catégorie, problème ciblé, objectif écologique hypothétique, signes géographiques, données nécessaires, conditions d'examen, contraintes/contre-indications, vérifications professionnelles et sources, statut d'évaluation MVP. Il n'est pas nécessaire de rédiger un traité scientifique par fiche, mais aucune famille ne reçoit une fiche « vide ».

| Code | Famille | Catégorie | Indice pouvant | Statut MVP |
| --- | --- | --- | --- | --- |
|   |   |   | justifier son examen |   |
| A01 | Haies / continuités | Restauration physique Lacune bocagère |   | Automatique R2 |
|   | bocagères |   | documentée sur |   |
|   |   |   | continuité pertinente |   |
| A02 | Mares / réseaux de | Restauration physique Discontinuité |   | Automatique R4 |
|   | mares |   | potentielle de réseau |   |
|   |   |   | humide documentée |   |
| A03 | Renaturation de | Restauration physique Friche localisée à |   | Automatique R3 |
|   | friches |   | proximité d'une |   |
|   |   |   | continuité |   |
| A04 | Passages à faune / | Restauration physique Croisement route- |   | Automatique R1 |
|   | ouvrages |   | corridor qualifié, |   |
|   |   |   | franchissement à |   |
|   |   |   | vérifier |   |
| A05 | Ripisylves et bandes | Restauration physique Cours d'eau et déficit |   | Documentation |
|   | tampons |   | documenté de |   |
|   |   |   | végétation riveraine |   |
| A06 | Restauration de zones | Restauration physique Zone humide |   | Documentation |
|   | humides |   | dégradée et |   |
|   |   |   | fonctionnement |   |
|   |   |   | hydrologique à |   |
|   |   |   | expertiser |   |
| A07 | Reconnexion des | Restauration physique Boisements isolés et |   | Documentation |
|   | boisements |   | interface de continuité |   |
|   |   |   | plausible |   |
| A08 | Prairies et pratiques | Prévention et gestion Usages agricoles sur |   | Documentation |
|   | agricoles favorables |   | continuité |   |
|   |   |   | documentée |   |
| A09 | Trame noire / | Prévention et gestion | Corridors nocturnes et | Documentation |
|   | réduction d'éclairage |   | éclairage caractérisé |   |
| A10 | Protection | Prévention et gestion | Enjeux écologiques et | Documentation |
|   | réglementaire et |   | cadres de |   |
|   | urbanisme |   | protection/planificatio |   |
|   |   |   | n |   |
| A11 | Évitement de | Prévention et gestion | Continuité confrontée | Documentation |
|   | l'artificialisation |   | à changement |   |
|   |   |   | d'usage/projet |   |
|   |   |   | documenté |   |
| A12 | Reconnexion de deux | Action combinée | Plusieurs actions | Documentation |
|   | habitats (combinaison) |   | nécessaires entre |   |
|   |   |   | habitats identifiés |   |

Ne pas inférer : une friche ne vaut pas autorisation de renaturer ; un zonage ne prouve pas une espèce ; un « vide » dans une couche n'établit pas l'absence réelle d'un habitat ; l'éclairage satellitaire n'est pas un luxmètre au sol.

## 6.4 Ordre de présentation des pistes au clic

- 1. etayee_pour_examen si règle R1–R4 satisfaite et sources suffisantes.

- 2. conditionnelle si des signaux existent mais que des informations importantes manquent.

- 3. Catalogue complémentaire, explicitement intitulé « Autres familles d'action — non évaluées pour ce secteur ».


Une liste peut contenir plusieurs actions sans ordre d'efficacité. L'utilisateur peut filtrer par restauration, prévention/gestion ou action combinée ; les interventions peuvent être complémentaires. La date/urgence documentée d'une menace est affichée distinctement, pas convertie en classement de rendement.

## 7. Parcours utilisateur, interfaces et critères d'acceptation

## 7.1 Parcours principal — démo en moins de cinq minutes

Normandie visible → pilote identifié → mailles colorées → clic → priorité et explications → conflits potentiels qualifiés → plusieurs pistes pertinentes + documents → sources et limites.

L'élu voit d'abord l'essentiel : une légende claire et une fiche brève. Le technicien peut déplier les indicateurs, données, échelles, dates et règles. Aucun jargon non expliqué au premier niveau.

## 7.2 États de l'interface obligatoires

| État | Comportement exigé |
| --- | --- |
| analyse_non_realisee | Hors pilote : zone neutre, pas de priorité attribuée |
| indeterminee | Données insuffisantes : pas de fausse couleur rassurante |
| faible/moderee/elevee | Une couleur accessible + label textuel + règles |
|   | consultables |
| conflit_potentiel | Cause et géométrie à la précision permise, avertissement |
| aucun_signal | Aucun conflit selon règles, pas « absence de danger » |
| actions_multiples | Plusieurs actions listées ; justification indépendante pour |
|   | chacune |
| action_non_evaluable | Fiche catalogue disponible mais pas de recommandation |
|   | locale |
| erreur_chargement/404 | Message intelligible, possibilité de revenir à la carte |

## 7.3 Exigences fonctionnelles priorisées

| ID | Exigence vérifiable | Priorité |
| --- | --- | --- |
| F01 | Carte régionale, pilote clairement | P0 |
|   | délimité, hexagones sélectionnables |   |
| F02 | Au moins trois couches P0 réelles, | P0 |
|   | légendes et source/date visibles |   |
| F03 | Détection et export de conflits | P0 |
|   | potentiels distincts des mailles |   |
| F04 | Quatre familles d'indicateurs, valeurs | P0 |
|   | disponibles et null explicite |   |
| F05 | Priorité synthétique unique et | P0 |
|   | décomposition/fiabilité au clic |   |
| F06 | Catalogue homogène de douze | P0 |
|   | fiches, organisé en catégories |   |
| F07 | Quatre règles automatiques R1–R4 | P0, sous réserve des sources validées |
|   | avec tests et transparence |   |
| F08 | Fiche de maille et liste de pistes | P0 |
|   | applicables/conditionnelles/non |   |
|   | évaluables |   |
| F09 | API documentée, contrat stable, états | P0 |
|   | d'erreur et tests |   |


| ID | Exigence vérifiable | Priorité |
| --- | --- | --- |
| F10 | Sources, licences, méthode et limites | P0 |
|   | consultables |   |
| F11 | Filtres multicritères et recherche de | P1 |
|   | maille/commune |   |
| F12 | Export PDF/CSV et extension | P1 |
|   | géographique |   |
| F13 | Modélisation chiffrée, score de | Hors MVP |
|   | rendement, automatisation des |   |
|   | douze familles |   |

## 7.4 Exigences non fonctionnelles

- Rigueur : origine, année, échelle, unité, limites et méthode visibles ; pas de « faiblesse écologique » déduite d'un null.

- Accessibilité : priorité lisible aussi en texte ; contraste, légendes, navigation clavier, messages de statut compréhensibles.

- interdit la diffusion. Sécurité et données : ne jamais exposer les points d'espèces sensibles, secrets, jetons API ou fichiers dont la licence

- version gelée des fichiers finaux. Reproductibilité pragmatique : dépendances indiquées, un README, un script de préparation, un contrat d'échange, une

## 7.5 Numérique responsable — plan mesurable et propriétaires

La sobriété n'est pas un slogan. M4 mesure, M3 optimise l'affichage, M1/M2 limitent les exports aux données nécessaires, M5 publie les résultats.

| Mesure | Périmètre et méthode | Objectif provisoire pour le | Preuve / propriétaire |
| --- | --- | --- | --- |
|   |   | pilote |   |
| Transfert initial | Navigateur, cache | Viser ≤ 3 Mo hors tuiles du | Capture réseau M3/M4 |
|   | désactivé, application + | fond, ajuster après mesure |   |
|   | données pilote ; fond | et le dire |   |
|   | externe compté à part |   |   |
| Temps jusqu'à carte | Machine de | Viser ≤ 5 s en local ; | Mesures M3 |
| utilisable | démonstration, démarrage | documenter toute |   |
|   | froid ; cinq essais et valeur | exception |   |
|   | médiane |   |   |
| Taille d'une fiche | Réponse JSON d'une | Viser ≤ 100 Ko par fiche | Test M4 |
|   | maille, hors fonds | sans répétition des gros |   |
|   | cartographiques | polygones |   |
| Nombre de requêtes | Ouverture de carte, | Mesurer et éliminer les | Journal réseau M4/M3 |
|   | sélection d'une maille, | appels redondants |   |
|   | ouverture d'une action |   |   |
| Pré-calcul | Opérations SIG lourdes | 100 % des intersections | Revue code M2/M4 |
|   | faites hors navigateur ; | précalculées pour le pilote |   |
|   | aucune intersection |   |   |
|   | recalculée au clic |   |   |
| Services | Comparer API légère | Maintenir une version | README + test M4 |
|   | existante et export | statique démontrable ; ne |   |
|   | JSON/GeoJSON statique | pas imposer une |   |
|   |   | infrastructure superflue |   |
| Accessibilité | Contraste, texte pour les | Aucun chemin principal | Contrôle M3/M5 |
|   | couleurs, clavier, sources et | dépendant uniquement |   |
|   | limites | d'une couleur |   |

Important : ces plafonds sont des budgets internes de conception, non des résultats ou des seuils officiels. Une dérogation mesurée et expliquée vaut mieux qu'une performance annoncée sans preuve. Aucune économie d'énergie ou d'émissions de CO₂ n'est affirmée sans mesure adaptée.


## 8. Architecture et contrats d'interface

## 8.1 Stack retenue

Données : Python, Pandas, GeoPandas, Shapely, PyProj ; QGIS pour les contrôles. Stockage calcul : GeoPackage/GeoParquet en EPSG:2154. Export web : GeoJSON RFC 7946 en longitude-latitude ; JSON pour les fiches et sources. Service : FastAPI avec résultats précalculés, documentation OpenAPI. Interface : React + MapLibre (Leaflet seulement si prototype existant stabilisé). Collaboration : Git, PR et revue.

## 8.2 Arborescence commune (contrat)

```text
reconnect-normandie/
├── data/
│   ├── raw/          # local, non modifié et hors dépôt si volumineux
│   ├── processed/    # SIG harmonisé et grille (M1)
│   ├── derived/      # conflits, mailles, diagnostics (M2)
│   └── public/       # exports autorisés, anonymisés (M2 + M1)
├── analysis/          # scripts et tests M2
├── backend/           # API M4
├── frontend/          # React/MapLibre M3
├── catalogue/         # 12 fiches source de vérité (M5 + M2)
├── docs/              # PRD, décisions, méthode, sources, licences
├── tests/             # tests de contrat, qualité et bout en bout
└── README.md
```

## 8.3 Contrat des fichiers produits par M1 → M2

- grille_pilote.gpkg : maille_id, grid_version, area_m2, geometry ; CRS 2154.

- geometry (dès que disponibles). corridors.gpkg, reservoirs.gpkg : source_id, objet_id, sous_trame, millesime, precision_source,

- routes.gpkg : route_id, categorie, ouvrage_connu si fourni, source_id, millesime, geometry.

- sols.gpkg : sol_id, nomenclatures couverture/usage, source_id, millesime, geometry.

- réellement disponibles ; les champs non disponibles ne sont pas inventés. haies.gpkg, friches.gpkg, mares.gpkg : au minimum identifiant, source, année, géométrie, champs utiles

- couverture, géométries invalides, règles de nettoyage. inventaire_sources.csv + sources.json : provenance et restrictions par couche ; quality_report.md : trous de

Les noms exacts des champs source sont mappés dans un dictionnaire d'harmonisation validé M1/M2 le 3 novembre ; toute modification du schéma après gel exige revue de M2 et M4.

## 8.4 Contrat M2 → M4/M3 : trois sorties distinctes

- A. mailles.geojson, FeatureCollection de polygones (un Feature par maille) : maille_id, grid_version, statut_analyse, priorite_examen, diagnostics[], indicateurs, qualite, conflit_ids[], action_ids[], method_version. geometry en WGS84/CRS84.

- B. conflits.geojson, FeatureCollection d'événements de conflit potentiels : conflit_id, type, evidence_level, source_ids[], maille_ids[], precision_affichage, limites[], geometry généralisée ou omise si diffusion risquée. Les objets d'origine restent dans le stockage interne.

- C. fiches_zones.json (M2) : diagnostics détaillés, indicateurs, périodes, fiabilité et associations d’actions calculées. D. catalogue_actions.json (M5, revue M2/M1) : douze fiches homogènes au format validé par M3/M4. Ces deux objets doivent partager les mêmes action_id.

Exemple minimal fictif, limité à un secteur et non représentatif d'un résultat réel :

```json
{
  "maille_id": "NORM-G1-00042",
  "statut_analyse": "calculee",
  "priorite_examen": "moderee",
  "dimensions": {
    "enjeu_ecologique": "documente",
    "pressions": ["croisement_routier", "artificialisation"],
    "urgence_temporelle": "non_evaluee"
  },
  "qualite": {"niveau": "partielle", "sources_valides": ["TVB", "BD_TOPO"]},
  "conflit_ids": ["CF-104"],
  "actions": [
    {
      "action_id": "A04",
      "regle_id": "R1",
      "statut": "conditionnelle",
      "motif": "Croisement route-corridor documente ; franchissabilite a verifier"
    }
  ],
  "method_version": "m2-v1.0",
  "test_data": true
}
```

Le champ test_data ne doit jamais être true pour une donnée présentée comme réelle, et les exemples fictifs ne sont pas intégrés aux exports de production.

## 8.5 API — propriétaire M4

| Méthode et route | Résultat | Consommateur |
| --- | --- | --- |
| GET /health | État du service + version de jeu de | M3, tests, jury |
|   | données |   |
| GET /zones?bbox=... | Mailles du pilote/viewport | M3 — carte |
|   | (FeatureCollection) |   |
| GET /zones/{maille_id} | Fiche détaillée et action_ids associés M3 — fiche |   |
| GET /conflits?maille_id=... | Conflits liés, géométrie si diffusable M3 — détails |   |
| GET /actions | Catalogue des 12 fiches | M3 — catalogue |
| GET /actions/{action_id} | Fiche complète avec statuts et | M3 |
|   | précautions |   |
| GET /sources | Sources, dates, licences et méthode | M3, documentation |
|   | référencée |   |

Convention pluriel /zones adoptée dans cette V6 pour le jeu de collections ; si la branche M4 existante fonctionne déjà en /zone, ne pas casser le code : choisir au jalon du 3 novembre un nom canonique, documenter les alias éventuels et l'écrire dans api_contract.md. Échecs : 404 pour identifiant absent, 422 pour requête malformée, JSON valide, pagination ou découpe BBOX pour gros volumes.

## 8.6 Contrat stable sans surprocédure

Un seul fichier docs/contrat_donnees.md fait foi dès le 3 novembre : champs, types, identifiants, valeurs absentes, liste des

statuts et routes API. Trois labels simples (grid_version, method_version, dataset_version) suffisent pour retrouver la

source d'un résultat ; aucun système complexe de migration n'est demandé. La validation automatisée minimale teste JSON/GeoJSON, identifiants, codes de priorité, géométries et données manquantes. Un changement incompatible passe par un message écrit dans le tableau commun, l'accord du fournisseur et du consommateur, puis un test d'intégration.

## 9. Organisation : responsabilités et dépendances

## 9.1 Responsabilités équilibrées — un propriétaire par livrable

| Livrable | Responsable principal | Contributeurs | Destinataire / validation |
| --- | --- | --- | --- |
| Sources, métadonnées, | M1 | M2 précise ses besoins | M2 confirme |
| licences et échantillons |   |   | exploitabilité ; M5 reprend |
|   |   |   | les sources pour l'écrit |
| Génération des hexagones | M1 | M2 valide méthode et taille M2 reçoit une base |   |
| et sous-mesures SIG (aires, |   |   | d'indicateurs prête à |
| longueurs, occupation) |   |   | enrichir |
| Spécification des 4 familles, | M2 | M1 + validation facultative | M4 utilise la table, M3 les |
| catégories de conflit, |   | d'experts ; M5 reformule | libellés |
| priorités |   | en langage clair |   |
| Détection géométrique, | M2 | M1 aide aux contrôles sur | M4 consomme les exports ; |
| association conflits ↔ |   | fichiers sources | M3 affiche |
| mailles, résultats |   |   |   |
| scientifiques |   |   |   |


| Livrable | Responsable principal | Contributeurs | Destinataire / validation |
| --- | --- | --- | --- |
| Codage du moteur | M4 | M2 fournit tests et | M2 valide la logique, M3 |
| générique R1–R4 à partir |   | conditions ; M1 prépare | affiche les listes |
| des règles définies |   | couches métier |   |
| Douze fiches et | M5 | M1 renseigne | M4 expose |
| bibliographie homogène | (coordination/assemblage) | données/limites ; M2 | catalogue_actions.json, |
|   |   | explique | M3/M5 affichent |
|   |   | conditions/contre- |   |
|   |   | exemples ; M3 vérifie UX |   |
| Carte régionale, | M3 | M4 intègre l'API ; M2 valide | M5 vérifie le parcours élu |
| hexagones, fiche, |   | la compréhension |   |
| interactions |   |   |   |
| Module React « Catalogue | M5 (développement limité) M3 fournit design system ; |   | M3 intègre le module dans |
| + Méthode » |   | M4 fournit données | le frontend |
| API, export statique, | M4 | M3 pour usages, M2 pour | M3 et M5 effectuent le test |
| démarrage, performance |   | contrats | externe |
| Écrit du 12 novembre, | M5 | Les quatre membres | Relecture collective le 10, |
| recette finale et pitch |   | fournissent contributions | envoi M5 le 12 |
|   |   | écrites et preuves |   |

Principe anti-goulot : M2 décide des significations écologiques mais ne doit pas rédiger seul le catalogue, développer le moteur d'application, fabriquer la grille et corriger l'API. Les quatre autres membres doivent pouvoir avancer avec les contrats TEST même lorsque les résultats réels ne sont pas prêts.

## 9.2 Passages de relais datés et critères de réception

| Flux | Livrable accepté par le | Date ferme | Si bloqué |
| --- | --- | --- | --- |
|   | destinataire |   |   |
| M2 → M1 | Liste des champs requis | 30/10 | M1 signale immédiatement |
|   | pour indicateurs/R1–R4, |   | l'absence d'un champ |
|   | sous-trames et précision |   |   |
|   | attendue |   |   |
| M1 → M2 | Échantillon vrai TVB + | 02/11 | GO/NO-GO et choix d'un |
|   | routes + sols, plus état des |   | autre pilote |
|   | données |   |   |
|   | haies/friches/mares |   |   |
| M1 → M2 | Grille, SIG harmonisé, | 04/11 matin | M2 utilise l'échantillon ; |
|   | densités/aires réutilisables, |   | limite explicite dans le MVP |
|   | sources et qualité |   |   |
| M2 → M3/M4 | Contrat JSON/GeoJSON | 03/11 | Pas de changement |
|   | TEST, statuts, légendes, |   | silencieux après cette date |
|   | table de règles structurelle |   |   |
| M4 → M3 | API simulée + jeu TEST + | 03/11 | Fichiers statiques TEST |
|   | consignes d'erreur |   | fournis pour travail |
|   |   |   | autonome |
| M2 → M4 | Premiers exports réels de | 05/11 ; règles gelées 06/11 | Version précédente |
|   | mailles et conflits, |   | conservée et écart |
|   | méthode et table calibrée |   | documenté |
| M2 → M4 | R1–R4 détaillées avec | 05/11 | M4 implémente sur |
|   | exemples TEST positifs, |   | données de test puis |
|   | négatifs, manquants |   | produit réel |
| M4 → M3 | Endpoints réels + moteur | 06/11, stabilisés 09/11 | M3 utilise la même |
|   | évaluant R1–R4 ; statuts |   | structure statique |
|   | cohérents |   |   |


| Flux | Livrable accepté par le | Date ferme | Si bloqué |
| --- | --- | --- | --- |
|   | destinataire |   |   |
| M1/M2 → M5 | Références, méthodes | 06/11 | M5 ne reprend que des |
|   | courtes, hypothèses, |   | résultats vérifiés |
|   | chiffres autorisés pour |   |   |
|   | l'écrit |   |   |
| M5 → M3/M4 | catalogue_actions.json | 09/11 matin | M3 peut afficher le |
|   | complet (12 fiches), |   | catalogue par JSON sans |
|   | module React autonome |   | module supplémentaire |
| Tous → M5 | Captures, tests, sources, | 09/11 18 h | M5 active le plan B au lieu |
|   | texte du dossier, README, |   | de promettre des éléments |
|   | licences |   | absents |
| M5 → Tous | Écrit final relu et paquet de | 10/11 18 h ; vérification | Corrections documentaires |
|   | rendu prêt | 11/11 | mineures seulement |
| M5 → organisateurs | ÉCRIT OFFICIEL ENVOYÉ, | 12/11 (heure à confirmer, | Plan de secours de dépôt |
|   | accusé conservé | envoi anticipé | confirmé avant le 10 |
|   |   | recommandé) |   |

## 9.3 Collaboration légère

- Point quotidien 10 à 15 minutes, une ligne par personne : fait / prochain / blocage.

- Un tableau partagé : tâche, propriétaire, date, statut, lien vers preuve. Pas d'autres tableaux obligatoires.

- validité des données critiques. Une branche Git par fonctionnalité, une relecture avant fusion ; le pipeline automatique ne vérifie que démarrage et

- conventions redondantes. Une seule méthode de versionner les résultats (grid_version, method_version, dataset_version) ; éviter les

- Un blocage technique est signalé dès qu'il menace le jalon suivant, sans attendre vingt-quatre heures.

- M5 arbitre la portée produit, pas la validité scientifique : si M2 signale une limite avérée, elle est affichée.

## 10. Livrables détaillés par membre

## 10.1 M1 — Sources, qualité, sous-mesures SIG et maillage

Mission : assurer que M2 reçoit tôt des couches réelles compatibles ; produire la grille et les statistiques géométriques élémentaires pour lui éviter de tout recalculer.

Développement / outils : Python, Pandas, GeoPandas, Shapely, PyProj, QGIS ; scripts de chargement, découpe, reprojection, validation des géométries, création des identifiants de mailles, intersections simples d'occupation du sol pour surfaces et linéaires. Contrôler les sources P0 (TVB, réseau routier, sols) et les couches nécessaires aux règles R1–R4 (haies, friches, mares/humides, ouvrages si disponibles).

Livrables : inventaire_sources.csv, grille_pilote.gpkg, data/processed/, sources.json, quality_report.md,

sub_indicateurs.csv ou GeoPackage, scripts reproductibles et vérification des licences. Un échantillon réel est transmis le 2, la version harmonisée le 4 au matin.

Interactions : M2 spécifie les champs nécessaires dès le 30 ; M1 fournit un état d'accès au plus tard le 2 ; M4 reçoit les ordres de grandeur de fichiers ; M5 reçoit les références utilisables dans l'écrit ; M3 reçoit des géométries TEST/validées pour l'affichage.

Terminé lorsque : fichiers lisibles sur une autre machine, CRS et millésimes explicités, IDs uniques, données absentes explicites, et aucun jeu non autorisé diffusé.

## 10.2 M2 — Méthode scientifique, conflits et classification

Mission : définir les critères de détection, de qualification des conflits et de priorité d'examen ; vérifier que les sorties sont scientifiquement prudentes et explicables.

Développement / outils : GeoPandas/Shapely et QGIS ; décisions sur taille et usage du maillage ; détection des croisements sur géométries sources ; dédoublonnage et rattachement aux mailles ; qualification des signaux inspirée de la progression Cerema ; contrôle des quatre familles d'indicateurs ; table explicite de priorités, avec état indéterminé ; définition scientifique de R1–R4 (sans coder seul le moteur d'application).


Livrables : methode_v0.md le 30, docs/contrat_donnees.md le 3 avec M3/M4, conflits.geojson, mailles.geojson, fiches_zones.json, rules_actions.json ou YAML, tests_analyse.md. La revue scientifique détaillée (dont SDES et taille

effective de maille) reste dans le dossier personnel M2, pas dans ce PRD.

Interactions : M1 prépare grille et sous-mesures ; M2 transmet les règles à M4 au plus tard le 5 pour implémentation ; M3 reçoit les textes de la légende et les limites ; M5 reçoit une page de synthèse scientifique et effectue la relecture en langage non technique.

Terminé lorsque : trois secteurs réels contrastés et un cas sans données contrôlés ; structure de règles figée le 3, seuils calibrés sur données le 5, gelés le 6 ; M4 dispose de cas TEST positif, négatif et non évaluable pour R1–R4 ; aucune rupture « confirmée » inventée.

## 10.3 M3 — Carte, sélection et UX du diagnostic

Mission : rendre le résultat compréhensible par un élu, tout en donnant accès à la provenance et aux limites pour les techniciens.

Développement / outils : React, MapLibre, composants RegionMap, HexGridLayer, PriorityLegend, ZoneDetail,

ConflictsPanel, ActionSuggestions ; états non_analyse, indetermine, chargement, erreur ; affichage textuel et

coloré ; gestion de plusieurs pressions/actions ; responsive, clavier, légende et sources.

Livrables : carte Normandie et emprise pilote au 30–2, sélection hexagone le 4, fiche réelle connectée le 6, parcours élu stable et captures au 9–10.

Interactions : le 3, M3 valide les champs avec M2/M4 ; M4 expose endpoints ou fichiers statiques ; M5 produit un module React indépendant Catalogue / Méthode, que M3 intègre sans coder le contenu des 12 fiches à sa place.

Terminé lorsque : un évaluateur peut atteindre « carte → pourquoi → plusieurs actions → sources » sans aide ; hors pilote non classé ; les couleurs ne sont jamais le seul moyen de comprendre la priorité.

## 10.4 M4 — Backend, moteur de règles et fiabilité technique

Mission : transformer les exports calculés en un produit consultable, sans inventer ni recalculer les conclusions écologiques.

Développement / outils : FastAPI légère déjà commencée, contrats de GET /zone/GET /zones selon décision commune du 3,

endpoints de conflits, actions, sources, tests 200/404/422, CORS local ; moteur générique R1–R4 exécutant la table métier fournie par M2 ; export JSON/GeoJSON statique identique en secours ; README, mesures de transfert et performance.

Livrables : API TEST le 30, contrat API partagé le 3, API réelle le 5, moteur R1–R4 branché au plus tard le 9, démarrage reproduit le 10, export statique disponible avant le gel.

Interactions : M2 décide des conditions, M4 les implémente et les teste ; M1 lui communique volumes et contraintes ; M3 reçoit le contrat dès le 3 ; M5 reçoit README, résultats de tests et chiffres de sobriété pour l'écrit.

Terminé lorsque : une autre personne démarre le backend ; les quatre règles répondent correctement aux exemples TEST et aux données réelles évaluables ; absence de sources => non_evaluable, pas de recommandation fictive ; le parcours de secours est démontrable.

## 10.5 M5 — Produit, coordination, développement autonome et remise de l'écrit

Mission : coordonner une livraison qui raconte la même histoire dans le code, les données, l'écrit et le pitch, tout en développant réellement un module.

Développement / outils : React (module ActionCatalogue + page MethodAndSources) consommant

catalogue_actions.json et sources.json; filtres par catégorie, statut documentaire, liens vers sources ; composants conçus

avec M3 pour éviter les collisions de fichiers. M5 ne prend pas en charge la carte principale ni l'API.

Contenus : définir un modèle uniforme ; distribuer les 12 fiches à toute l'équipe (M1 = données/limites, M2 = règles/vérifications, M3 = langage utilisateur, M4 = schéma) ; éditer, harmoniser, relire. Préparer l'écrit officiel avec les cinq questions : problème, solution, impacts, équipe, besoins pour changer d'échelle.

Livrables : plan de travail et trame écrit le 30, brouillon V1 le 5, douze fiches harmonisées + module React au 9, écrit relu et final + archive à 18 h le 10, contrôle paquet du 11, envoi de l'écrit le 12 avec preuve de dépôt, pitch final le 23.

Interactions : M1 fournit sources/licences, M2 définitions et réserves, M3 intégration du module et captures, M4 lancement/performances ; la relecture de l'écrit est répartie entre les cinq personnes le 9 et le 10.

Terminé lorsque : paquet complet prêt au 11, aucune dépendance à un développement le 12, module intégré, douze fiches homogènes, références vérifiées, accusé de remise archivé.


## 11. Calendrier commun, individuel et gel final

## 11.1 Jalons collectifs — aucun rendu en fabrication le 12

| Date | Résultat concret de fin de journée | Validation / prochaine dépendance |
| --- | --- | --- |
| Ven. 30 octobre | PRD V6.1 approuvé, besoins M2 | Tous ; M5 consigne les désaccords |
|   | transmis à M1, inventaire P0, | bloquants |
|   | maquette carte, API TEST, trame des |   |
|   | cinq questions |   |
| Lun. 2 novembre | GO/NO-GO pilote sur données | M1 + M2, arbitré M5 ; M3/M4 |
|   | ouvertes ; échantillon vrai | avancent en parallèle |
|   | TVB/routes/sols ; état des données |   |
|   | métier R1–R4 ; maillage candidat |   |
| Mar. 3 novembre | Contrat et table structurelle des | M2 + M4 + M3, revue M5 |
|   | règles GELÉS : identifiants, GeoJSON |   |
|   | TEST, statuts, endpoints, champs |   |
|   | manquants, catalogue JSON |   |
| Mer. 4 novembre | Grille et SIG harmonisés dès le | M1 → M2 ; M3 affiche TEST, M4 |
|   | matin ; premiers conflits ; carte pilote | prépare réception |
|   | cliquable ; extrait d'écrit en cours |   |
| Jeu. 5 novembre | Export réel M2 v1 et fiche accessible ; | M2 → M4 → M3 ; M5 relecture |
|   | calibration préliminaire des seuils ; | initiale |
|   | brouillon complet de l'écrit ; règles |   |
|   | scientifiques R1–R4 remises à M4 |   |
| Ven. 6 novembre | Parcours réel de bout en bout ; | Test collectif et décision de repli si |
|   | TABLE DES SEUILS GELÉE ; premières | une source manque |
|   | règles automatiques connectées ; |   |
|   | note méthode et limites fournie à M5 |   |
| Lun. 9 novembre | Quatre règles exécutables et testées, | Cinq campagnes QA, corrections |
|   | cas réels uniquement lorsque | critiques ouvertes |
|   | données disponibles ; 12 fiches |   |
|   | harmonisées ; module React M5 |   |
|   | intégré ; écrit final V2 relu |   |
| Mar. 10 novembre, 18 h | GEL DU MVP ET DE L'ÉCRIT ; PR | M5 rassemble une archive candidate |
|   | relues fusionnées ; tests, README, | complète, aucune fonction nouvelle |
|   | sources, captures, vidéo ou mode |   |
|   | statique ; écrit relu par l'équipe |   |
| Mer. 11 novembre, avant fin de | VERSION FINALE PRÊTE : dossier, | Jour férié : aucune fonction |
| journée | écrit, code, données autorisées, PDF, | essentielle planifiée ; contrôle de |
|   | sauvegarde, procédure de dépôt | complétude et marge de sécurité |
|   | vérifiés |   |
| Jeu. 12 novembre | ENVOI DE L'ÉCRIT OFFICIEL | M5 responsable, autre membre |
|   | UNIQUEMENT et sauvegarde de | vérifie confirmation ; heure officielle |
|   | l'accusé/confirmation ; ne pas rédiger | à confirmer |
|   | ni développer ce jour-là |   |
| 13–20 novembre | Qualité du pitch, retours experts, | Toute version enrichie doit repasser |
|   | extension régionale facultative sur | les tests |
|   | branche séparée, sans toucher à la |   |
|   | V6.1 rendue |   |
| 21–22 novembre | Répétitions, vérification des supports | M5 gère la logistique, M3/M4 |
|   | et des conditions de dépôt de | sécurisent la démo |
|   | démo/code s'il y a lieu |   |
| Lun. 23 novembre | Pitch de cinq minutes, démonstration | Jury ; version stable de secours |
|   | et réponses du groupe | disponible |


Important : le 11 novembre est férié. Pour ne dépendre d'aucun travail indispensable ce jour-là, l'équipe doit avoir réellement terminé le 10 à 18 h. Le 11 constitue la date butoir de disponibilité du paquet final ; le 12 est réservé à son envoi officiel. Si l'heure de clôture du formulaire du 12 est inconnue, M5 la confirme avant le 2 novembre et prépare l'envoi anticipé si autorisé.

## 11.2 Répartition synthétique des charges par créneau

| Membre | 30/10–02/11 | 03–06/11 | 09–10/11 | 11–12/11 |
| --- | --- | --- | --- | --- |
| M1 | Inventaire, | Nettoyage, grille | QA données, licence, | Aide à contrôler |
|   | échantillon, choix | finale, métriques de | copie finalisée | paquet ; aucun |
|   | pilote, première grille | base, jeux R1–R4 |   | nouveau nettoyage |
| M2 | Spécification | Détection, | Validation des quatre | Contrôle des résultats |
|   | scientifique, pilotage | qualification, mailles, | règles et tests SIG, | diffusés seulement |
|   | maille, règle | calibrage 5, gel règles | note scientifique finale |   |
|   | structurelle | 6 |   |   |
| M3 | Maquette, carte, | Intégration carte et | Intègre module M5, | Pas de nouvelle |
|   | données TEST | vraie fiche, légendes | UX, captures, | fonctionnalité |
|   |   | et erreurs | contrôles |   |
| M4 | API TEST, contrat et | API réelle, moteur | Tests 200/404, | Contrôle fichier final / |
|   | format statique | générique R1–R4, | performance, | dispositif de dépôt |
|   |   | intégration front | README, secours | seulement |
| M5 | Cadrage, écrit, | Catalogue/module, | Fiches + module | 11 : paquet prêt. 12 : |
|   | distribution fiches, | écrit V1, suivi et revue | intégrés, écrit relu et | envoi écrit + accusé |
|   | module React préparé | scientifique | final 10/11 |   |

## 11.3 Gestion des changements après le 12

La remise écrite du 12 est un instantané vérifiable. Une éventuelle extension de calculs à toute la Normandie avant le 23 se fait dans une branche ou un paquet distinct ; elle ne peut pas modifier rétroactivement les chiffres et affirmations de l'écrit déjà rendu. Les nouveaux résultats ne sont présentés au jury qu'avec une méthode et un statut de validation explicites.

## 12. Recette courte : cinq campagnes obligatoires

| Campagne | Pilote | Vérifications essentielles | Preuve signée |
| --- | --- | --- | --- |
| Q1. Sources et géométrie | M1 avec M2 | Licences, années, CRS, IDs | Rapport de 1 page et |
|   |   | uniques, géométries | capture QGIS |
|   |   | valides, grille et surfaces, |   |
|   |   | trous de couverture |   |
| Q2. Détection et priorité | M2 avec M1 | Intersection réelle vs | Trois secteurs réels + un |
|   |   | même maille sans | cas sans données |
|   |   | croisement ; |   |
|   |   | dédoublonnage multi- |   |
|   |   | maille ; règle de priorité |   |
|   |   | reproductible ; null ≠ 0 ; |   |
|   |   | obstacle « confirmé » |   |
|   |   | uniquement sourcé |   |
| Q3. Quatre associations | M4 avec validation M2 | Chaque règle R1–R4 passe | Tableau de 12 cas TEST + |
| d'actions |   | un TEST positif, négatif et | captures réelles |
|   |   | non évaluable ; les pistes | lorsqu'elles existent |
|   |   | multiples ont une |   |
|   |   | justification ; données |   |
|   |   | insuffisantes ≠ |   |
|   |   | recommandation |   |
| Q4. Application, | M3 + M4 | Parcours élu, 200/404, API | Test sur une autre machine |
| performance et sécurité |   | ou statique, catalogue 12, | + mesures |
|   |   | clavier/contraste, fichiers |   |
|   |   | interdits absents ; relever |   |
|   |   | poids/temps/requêtes |   |


| Campagne | Pilote | Vérifications essentielles | Preuve signée |
| --- | --- | --- | --- |
| Q5. Livraison et écrit | M5 + relecteur tournant | Cinq réponses de l'écrit, | 10/11 paquet candidat ; |
|   |   | sources vérifiées, code et | 11/11 prêt ; 12/11 accusé |
|   |   | récit cohérents, licence, | de remise |
|   |   | README, archive, |   |
|   |   | vidéo/capture secours, |   |
|   |   | procédure d'envoi |   |

La checklist est courte, mais les cas dangereux ne sont pas supprimés. Pas de collecte de métriques factices, pas de fausse précision et pas d'action présentée comme supérieure biologiquement aux autres. Les problèmes bloquants découvert le 9 ou le 10 donnent lieu à une correction ou à un retrait transparent de la fonction concernée.

## 13. Principaux risques, seuils d'alerte et repli

| Risque | Signal d'alerte | Responsable | Réponse validable |
| --- | --- | --- | --- |
| Un pilote sans données | Donnée mare/friche/haie | M1+M2+M5 | Étendre/changer pilote, |
| pour R1–R4 | inutilisable au 2/11 |   | qualifier une règle non |
|   |   |   | évaluée, signaler l'écart si |
|   |   |   | persistant |
| Échelle TVB inadaptée | Précision d'intersection | M2 | Afficher secteur, non |
|   | supérieure à précision |   | emplacement de travaux ; |
|   | source |   | réduire prétention |
| Faux positifs routiers | Ouvrages connus, simple | M2 | Dédoublonner, qualifier et |
|   | tangence, multi-segments |   | afficher niveaux d'évidence |
| Priorité contestable | Seuil arbitraire ou donnée | M2+M5 | Publication des règles, |
|   | manquante |   | tests de sensibilité, classe |
|   |   |   | indéterminée |
| Catalogue interprété | Une action de | M3+M5 | Badges de statut, |
| comme recommandations | documentation apparaît « |   | avertissements et absence |
| fermes | applicable » |   | de classement de |
|   |   |   | rendement |
| Retard dépendances | M1 livre après 4/11 ou | M5 | Échantillon, format TEST |
|   | schéma change après 3/11 |   | stable, décision de repli |
|   |   |   | écrite |
| Performance régionale | GeoJSON trop volumineux M4+M3 |   | Charger pilote/BBOX, |
|   |   |   | simplifier, tuiles si |
|   |   |   | nécessaire |
| Donnée non diffusable | Restrictions/licence | M1 | Garder local, exporter |
|   | incertaines |   | indicateurs agrégés |
|   |   |   | autorisés seulement |
| Pitch ou API indisponible | Lancement non | M4+M5 | Export statique et |
|   | reproductible |   | vidéo/captures de secours |

## 14. Pitch, preuves et changement d'échelle

0:00–0:45 — Problème : données dispersées, continuités et pressions difficiles à exploiter.

0:45–1:15 — Promesse : carte, diagnostic explicable, priorité d'examen et plusieurs pistes à étudier.

1:15–3:40 — Démo : Normandie → pilote → maille → conflits et fiabilité → plusieurs actions → source et condition.

3:40–4:20 — Méthode : données ouvertes, croisements sur géométries sources, mailles, règles transparentes, aucune prédiction.

4:20–5:00 — Impacts attendus, limites, consultation d'experts, extension régionale et sobriété.

L'équipe doit montrer un exemple réel d'intersection qualifiée, une fiche avec plusieurs pistes possibles si les règles se

déclenchent, une autre maille avec décision différente et le traitement honnête d'un cas de données insuffisantes. Le cas « quatre automatisations » est démontré par plusieurs secteurs si nécessaire, pas artificiellement condensé dans une seule maille.


Le changement d'échelle implique validation écologique locale, sources plus fines, contrôles espèces/ouvrages/traffic, calibration des seuils, suivi de versions, mesures de performance et mise à jour régulière. Aucune de ces perspectives ne constitue un résultat déjà démontré.

## 15. Points à confirmer avant le gel de méthode

| Décision indispensable | Responsable | Date limite |
| --- | --- | --- |
| Canal, format et heure exacte de | M5 | 30 octobre / vérification immédiate |
| l'envoi de l'écrit du 12 novembre |   |   |
| (consigne communiquée à l'équipe, |   |   |
| non déduite de la page publique) |   |   |
| Territoire pilote selon compatibilité | M1 + M2 + M5 | 2 novembre |
| des trois sources et données métier |   |   |
| R1–R4 |   |   |
| Taille, origine de grille et emprise | M1 construit, M2 valide | 2 novembre |
| réelle |   |   |
| Routes API au singulier /zone ou au | M4 + M3 | 3 novembre |
| pluriel /zones ; aucune refonte |   |   |
| gratuite du code existant |   |   |
| Structure de la table de priorité, | M2, validation fonctionnelle M3/M4 | 3 novembre |
| statuts, gestion null et sources |   |   |
| Seuils numériques mesurables après | M2, revue M1/M5 | Calibration 5 ; gel 6 novembre |
| inspection réelle ; version stable |   |   |
| Données réellement disponibles pour | M1 + M2 + M4 | 2 pour faisabilité ; 6 pour |
| quatre automatisations et limites |   | confirmation |
| d'usage |   |   |
| Module M5 + douze fiches et liens | M5 + M3 | 9 novembre |
| IDs |   |   |
| Premières mesures de sobriété et | M4 + M3 + M5 | 9 novembre |
| choix API/statique |   |   |
| Écrit et archive finalisés | Tous, M5 pilote | 10 novembre 18 h, vérification 11 |
| Soumission officielle de l'écrit, | M5 | 12 novembre |
| accusé conservé |   |   |

## 16. Références institutionnelles et scientifiques

Ces références éclairent le cadre et les limites ; elles ne prouvent pas que les jeux ont été téléchargés ou que les algorithmes sont validés. Chaque fichier réellement utilisé devra posséder sa propre entrée d'inventaire.

- 1. transparence des infrastructures, ouvrages existants et croisement avec TVB. https://www.cerema.fr/fr/actualites/identification-priorisation-obstacles-aux-continuites Cerema (9 janvier 2026). Identification et priorisation des obstacles aux continuités écologiques terrestres. Méthode de

- 2. selon les départements (jusqu'au 1/10 000 en Eure/Seine-Maritime, 1/50 000 en Calvados/Manche/Orne). https://www.normandie.developpement-durable.gouv.fr/la-trame-verte-et-bleue-en-normandie-a3621.html DREAL Normandie. La trame verte et bleue en Normandie. Référentiels téléchargeables et précision d'usage variable

- 3. https://www.ign.fr/institut/occupation-du-sol-francais IGN. OCS GE, référentiel d'occupation du sol à grande échelle. Nomenclatures et millésimes.

- [IGN. BD TOPO. https://www.data.gouv.fr/datasets/bd-topo-r](https://www.data.gouv.fr/datasets/bd-topo-r)

- 4. 5. https://passagesfaune.fr/ SIPAF. Système d'information sur les passages à faune, données SIG et ouvertes (couverture à vérifier).

- 6. (recherche approfondie hors PRD, dossier M2). https://www.statistiques.developpement-durable.gouv.fr/la-fragmentation-des- milieux-naturels-terrestres-en-france-definitions-cadre-conceptuel SDES (2026). La fragmentation des milieux naturels terrestres en France et méthode de « taille effective de maille »

- 7. INPN. Zonages et référentiels Natura 2000. https://inpn.mnhn.fr/referentiels-donnees


- 8. https://www.datanormandie.fr/actualites/inscriptions-au-datathon-normandie-2026 DataNormandie. Inscriptions au Datathon Normandie 2026 et ressources du concours.

- 9. normandie-2026/ ANBDD. Datathon Normandie 2026 : thématique et clôture du 23 novembre. https://www.anbdd.fr/datathon-

- 10. RFC 7946 (IETF). The GeoJSON Format : coordonnées WGS84/longitude-latitude, format d'échange. https://www.rfc- editor.org/info/rfc7946/ [URL 🔗](https://www.rfc-editor.org/info/rfc7946/)

Décision de cadrage proposée aux cinq membres : approuver cette V6.1 comme contrat commun de réalisation, sous réserve des décisions ouvertes listées en section 15. Tout résultat automatique reste un prédiagnostic argumenté. La qualité scientifique et la cohérence de la démonstration priment sur un nombre fictif de secteurs ou d'actions recommandées.

## ANNEXE A — Fiches de référence des douze familles d'actions

Mode de lecture. Les douze fiches ci-dessous sont de même profondeur structurelle. Les « indices » décrivent des conditions de mise à l'étude et non une assurance d'efficacité. Une fiche étiquetée « documentation » n'est pas automatiquement recommandée dans un hexagone. Les référentiels et autorisations nécessaires restent à vérifier par M1/M2.

## A01 — Plantations et restauration de haies

- Catégorie / statut : restauration physique ; R2 automatisée dans le MVP.

- Problème ciblé : discontinuité potentielle d'un réseau bocager et perte de relais végétaux entre habitats.

- Objectif à examiner : rétablir ou renforcer un maillage de haies adapté au contexte écologique et agricole.

- occupation du sol compatible. Indices géographiques : segments de haies datés, lacune vérifiable entre ensembles cohérents, corridor bocager,

- ultérieure. Données nécessaires : BD Haie / données bocagères, TVB par sous-trame, OCS GE ; propriétés et servitudes en expertise

- Déclencheur local : lacune documentée selon une règle R2 explicite et non simple faible densité des haies.

- agricoles et foncières. Contraintes et contre-indications : continuité déjà présente, inventaire incomplet, enjeux de milieux ouverts, contraintes

- Vérifications terrain : cartographie récente, nature des haies, essences, gestion, exploitation, accord des propriétaires.

- Message public : « Étudier une restauration ciblée des haies ; pertinence et localisation à confirmer sur le terrain. »

- Sources à documenter : IGN BD Haie, DREAL TVB, documents de gestion bocagère régionaux.

## A02 — Mares et réseaux de mares

- Catégorie / statut : restauration physique ; R4 automatisée dans le MVP.

- Problème ciblé : isolement possible d'habitats humides de petite taille et discontinuité d'un réseau de mares.

- Objectif à examiner : maintien, restauration ou étude de création de relais humides lorsque le contexte s'y prête.

- concernée. Indices géographiques : mares cartographiées, habitats humides proches, éventuelle lacune du réseau et sous-trame

- Données nécessaires : inventaire PRAM/CEN ou équivalent, trame bleue, OCS GE, eau et zones humides compatibles.

- incomplète. Déclencheur local : règle R4 fondée sur une configuration humide documentée, non sur l'absence de point dans une base

- Contraintes et contre-indications : hydrologie, qualité de l'eau, usages, risques pour d'autres habitats, statut foncier.

- Vérifications terrain : saisonnalité, alimentation en eau, espèces et gestion, avis hydrologique/naturaliste.

- Message public : « Étudier le fonctionnement du réseau de mares et les possibilités de restauration. »

- locales. Sources à documenter : PRAM Normandie / Conservatoire d'espaces naturels, DREAL trame bleue, données d'eau

## A03 — Renaturation de friches

- Catégorie / statut : restauration physique ; R3 automatisée dans le MVP.

- Problème ciblé : discontinuité ou manque de relais écologiques au sein de secteurs artificialisés ou délaissés.

- pertinente. Objectif à examiner : Indices géographiques : friche géolocalisée, voisinage documenté de corridors ou réservoirs, occupation des sols

- apprécier l'intérêt d'une reconversion écologique d'un site réellement recensé.


Données nécessaires : observatoire EPFN ou autre inventaire qualifié, TVB, OCS GE. Déclencheur local : règle R3 de proximité/contextualisation avec emprise fiable et critères contrôlés. Contraintes et contre-indications : contamination, sécurité, droit du sol, propriété, fonctions écologiques déjà présentes. Vérifications terrain : diagnostic historique et pollution, disponibilité foncière, inventaire écologique, faisabilité. Message public : « Étudier la contribution possible de cette friche à une continuité écologique. »

- Sources à documenter : EPFN/observatoire des friches, IGN OCS GE, DREAL TVB.

## A04 — Franchissement de la faune et ouvrages

Catégorie / statut : restauration physique ; R1 automatisée dans le MVP. Problème ciblé : croisement potentiellement problématique entre infrastructure linéaire et continuité écologique. Objectif à examiner : analyser la franchissabilité et une éventuelle amélioration d'ouvrage ou de gestion. Indices géographiques : intersection géométrique réelle, type de route, type de continuité, ouvrages recensés. Données nécessaires : DREAL TVB, IGN BD TOPO, SIPAF si disponible ; trafic et faune seulement si fiables. Déclencheur local : règle R1 : croisement qualifié, sans conclure automatiquement à un ouvrage à construire. Contraintes et contre-indications : pont/buse déjà fonctionnels, trafic non documenté, faux positifs de représentation. Vérifications terrain : état des ouvrages, passages réels, espèces, collisions, sécurité et faisabilité technique. Message public : « Vérifier la perméabilité de l'infrastructure et les options d'amélioration. » Sources à documenter : Cerema (méthode 2026), DREAL, IGN, SIPAF.

## A05 — Bandes tampons et ripisylves

Catégorie / statut : restauration physique ; documentation uniquement dans le MVP. Problème ciblé : rupture ou affaiblissement potentiel de la végétation associée aux cours d'eau. Objectif à examiner : améliorer la continuité rivulaire et les fonctions de protection des milieux aquatiques. Indices géographiques : cours d'eau identifié, végétation riveraine cartographiée, segment déficitaire documenté. Données nécessaires : hydrographie, BD Haie/forêt, bandes tampons et cartographie des sols. Déclencheur local futur : mise en correspondance des rives, végétation et exigences réglementaires locales. Contraintes et contre-indications : gestion hydraulique, contraintes agricoles, entretien, statuts locaux. Vérifications terrain : état des berges, régime hydrologique, espèces, largeur adaptée et réglementation. Message public : « Examiner la restauration de la continuité végétale des berges. »

- Sources à documenter : agences de l'eau, IGN hydrographie, DREAL/OFB.

## A06 — Restauration de zones humides

Catégorie / statut : restauration physique ; documentation uniquement dans le MVP. Problème ciblé : zone humide potentiellement altérée ou isolée de la trame bleue. Objectif à examiner : restaurer le fonctionnement hydrologique et écologique d'une zone humide. Indices géographiques : zone humide recensée, drainage/ouvrages connus, continuités hydrologiques. Données nécessaires : inventaires zones humides, eau, TVB, occupation du sol et pressions hydrauliques. Déclencheur local futur : diagnostic hydrologique documenté, pas uniquement superposition de deux polygones. Contraintes et contre-indications : niveau de nappe, risques, fonctions existantes, droits et usages. Vérifications terrain : hydrologie, sols, habitats, objectifs réglementaires, propriétaires/gestionnaires. Message public : « Étudier le fonctionnement et les possibilités de restauration de la zone humide. »

- Sources à documenter : DREAL, OFB, agences de l'eau, inventaires territoriaux.

## A07 — Reconnexion de boisements

Catégorie / statut : restauration physique ; documentation uniquement dans le MVP. Problème ciblé : isolement structurel possible entre boisements et réservoirs forestiers. Objectif à examiner : renforcer une continuité boisée ou des habitats relais. Indices géographiques : massifs/boisements, distances et obstacles cartographiés, sous-trame forestière. Données nécessaires : BD Forêt, TVB, OCS GE, haies et éventuellement foncier. Déclencheur local futur : habitat isolé et espace intermédiaire compatible, avec justification écologique.

Contraintes et contre-indications : gestion forestière, foncier, milieux ouverts à préserver, espèces concernées.


- Vérifications terrain : composition forestière, connexions effectives, propriétés, enjeux agricoles. Message public : « Examiner des habitats relais entre boisements identifiés. »

- Sources à documenter : IGN BD Forêt, ONF/DataIFN, DREAL TVB.

## A08 — Prairies et pratiques agricoles favorables

Catégorie / statut : prévention et gestion ; documentation uniquement dans le MVP. Problème ciblé : pratiques et usages agricoles pouvant affecter certains habitats et continuités. Objectif à examiner : étudier des modes de gestion favorables aux corridors et espaces ouverts. Indices géographiques : parcelles RPG, continuités identifiées, bordures et occupation du sol. Données nécessaires : RPG, OCS GE, TVB, contexte d'exploitation à obtenir localement. Déclencheur local futur : lien entre milieu/pression observée et levier de gestion documenté. Contraintes et contre-indications : objectifs agricoles, contraintes réglementaires, faisabilité économique. Vérifications terrain : échanges avec exploitants, biodiversité ciblée, entretien, contractualisation. Message public : « Étudier des pratiques de gestion compatibles avec la continuité concernée. »

- Sources à documenter : IGN/RPG, Agreste, collectivités, OFB.

## A09 — Trame noire / éclairage nocturne

Catégorie / statut : prévention et gestion ; documentation uniquement dans le MVP. Problème ciblé : lumière artificielle susceptible d'affecter des déplacements nocturnes. Objectif à examiner : mieux caractériser l'éclairage et envisager son adaptation. Indices géographiques : éclairage documenté, corridor pertinent, infrastructures lumineuses connues. Données nécessaires : sources locales d'éclairage, trame noire, éventuellement VIIRS/Cerema avec prudence d'échelle. Déclencheur local futur : superposition pertinente et vérifiée, non simple pixel nocturne « brillant ». Contraintes et contre-indications : sécurité, horaires, usages, normes, présence réelle d'espèces sensibles. Vérifications terrain : inventaire de luminaires, mesures d'exposition, acteurs locaux, espèces cibles. Message public : « Étudier les adaptations de l'éclairage sur les continuités nocturnes. »

Sources à documenter : Cerema, données territoriales d'éclairage, OFB trame noire.

## A10 — Protection et urbanisme

Catégorie / statut : prévention et gestion ; documentation uniquement dans le MVP. Problème ciblé : continuités d'intérêt potentiellement insuffisamment prises en compte dans l'aménagement. Objectif à examiner : examiner des leviers de planification ou préservation adaptés au territoire. Indices géographiques : réservoirs/corridors, zonages, documents de planification compatibles. Données nécessaires : GPU, INPN, TVB, documents locaux et statuts effectifs. Déclencheur local futur : enjeu documenté + levier juridique identifiable, pas « zone sans statut = à protéger ». Contraintes et contre-indications : compétence institutionnelle, procédures, proportionnalité et droit applicable. Vérifications terrain : lecture PLU(i)/SCoT, consultation services compétents et juristes. Message public : « Examiner les outils de préservation et de planification mobilisables. »

Sources à documenter : Géoportail de l'urbanisme, INPN, DREAL.

## A11 — Éviter l'artificialisation

Catégorie / statut : prévention et gestion ; documentation uniquement dans le MVP. Problème ciblé : risque de perte future d'une continuité du fait d'une transformation de l'occupation du sol. Objectif à examiner : favoriser l'évitement ou la réduction d'une artificialisation incompatible. Indices géographiques : évolution OCS GE, projets ou zonages d'urbanisation documentés, continuités concernées. Données nécessaires : OCS GE multi-millésimes, CCF, GPU, TVB, projets publics documentés. Déclencheur local futur : pression temporelle corroborée par une source datée, sans inférer l'avenir depuis une seule

carte.

Contraintes et contre-indications : programmation urbaine, contraintes foncières, décisions d'aménagement. Vérifications terrain : nature des projets, alternatives, séquence éviter-réduire-compenser. Message public : « Examiner en amont les risques sur les continuités avant tout projet. »


- Sources à documenter : IGN OCS GE, GPU, CCF, documents d'urbanisme.

## A12 — Reconnexion combinée de deux habitats

- Catégorie / statut : action combinée ; documentation uniquement dans le MVP.

- Problème ciblé : continuité entre deux habitats nécessitant plusieurs leviers complémentaires.

- Objectif à examiner : organiser une démarche d'étude multi-actions, sans calcul de gain ni tracé « optimal ».

- Indices géographiques : habitats identifiés, obstacles multiples, pistes déjà reconnues comme étudiables.

- Données nécessaires : TVB, routes, sols, haies, zones humides, études locales, interventions retenues.

- Déclencheur local futur : connaissance suffisante d'un ensemble de discontinuités et de scénarios cohérents.

- Contraintes et contre-indications : compatibilité intermilieux, foncier, espèces, coût, ingénierie, temporalités.

- Vérifications terrain : expertise multi-espèces, priorisation des sites, échanges institutionnels.

- Message public : « Préparer une étude de reconnexion combinant plusieurs leviers. »

- Sources à documenter : DREAL/OFB, Cerema, études territoriales, résultats des familles A01–A11.

## ANNEXE B — Calendriers individuels détaillés et preuves de livraison

*B1 — M1 : Data, qualité, maillage et sous-indicateurs géométriques*

| Échéance | Livrable / tâche | Transmission attendue |
| --- | --- | --- |
| 30/10 | inventaire_sources.csv + premiers | Communique disponibilité à M2/M5 |
|   | accès P0 et données R1–R4 ; reçoit |   |
|   | liste des besoins M2 |   |
| 02/11 | Extraits SIG réels de candidats, note | Débloque début du pipeline M2 |
|   | d'échelle/format/année ; GO/NO-GO |   |
|   | avec M2 |   |
| 03/11 | Grille v1 et ID déterministes, | Contrat M2/M4/M3 |
|   | dictionnaire des champs |   |
| 04/11 matin | Données pilote harmonisées et sous- | Remise M2 sur fichier réel |
|   | mesures de surface/linéaire ; sources |   |
|   | et trous |   |
| 05–06/11 | Compléments haies/friches/mares, | M4/M2 évaluent R1–R4 |
|   | ouvrages si disponibles ; second |   |
|   | contrôle d'accès |   |
| 09/11 | Sources/licences/millésimes | M5 reçoit références à citer dans |
|   | contrôlés, support de la campagne | l'écrit |
|   | Q1 |   |
| 10/11 | Données autorisées et catalogue des | M2/M4 utilisent exactement ce |
|   | sources GELÉS, script de | paquet |
|   | reconstruction lisible |   |
| 11–12/11 | Contrôle d'archive si sollicité, aucun | M5 envoie l'écrit le 12 |
|   | traitement bloquant |   |

## B2 — M2 : Analyse scientifique, conflits et priorité

| Échéance | Livrable / tâche | Transmission attendue |
| --- | --- | --- |
| 30/10 | methode_v0.md : sous-trames, | M1 démarre recherche ciblée |
|   | indicateurs, niveaux de preuve, liste |   |
|   | de besoins R1–R4 |   |
| 02/11 | Croisement sur échantillon vrai + | M1/M5, choix pilote |
|   | validation taille maille ; GO/NO-GO |   |
| 03/11 | Structure de priorité, définitions des | M4/M3 fixent contrat |
|   | diagnostics, champs/valeurs |   |
|   | manquantes, jeux TEST |   |
| 04/11 | Intersections géométriques et | M4 reçoit premier export TEST/réel |
|   | rattachement aux mailles, cas de |   |
|   | contrôle |   |


| Échéance | Livrable / tâche | Transmission attendue |
| --- | --- | --- |
| 05/11 | Mailles/conflits réels v1 ; paramètres | M4 implémente moteur, M3 affiche |
|   | de priorité provisoires ; R1–R4 |   |
|   | spécifiées scientifiquement |   |
| 06/11 | SEUILS GELÉS après calibration et | M4/M3 disposent de règles stables |
|   | test, note de méthode publiée |   |
| 09/11 | Campagnes Q2/Q3, trois secteurs et | M5 finalise rédaction |
|   | un manquant, revue pistes et limites, |   |
|   | texte scientifique pour écrit |   |
| 10/11 | Dernière correction scientifique, | M4/M5 emballent final |
|   | exports et notes GELÉS à 18 h |   |
| 11–12/11 | Contrôle ponctuel de conformité ; | Envoi écrit M5 |
|   | aucun nouvel algorithme |   |

## B3 — M3 : Carte et interface principale

| Échéance | Livrable / tâche | Transmission attendue |
| --- | --- | --- |
| 30/10 | Maquettes carte/pilote/maille/fiche ; | Feedback M5/M2 |
|   | architecture composants React |   |
| 02/11 | Carte Normandie et couches TEST, | Données visuelles sans bloquer M1 |
|   | gestion « non analysé » |   |
| 03/11 | Validation champs GeoJSON, statuts | Contrat partagé M2/M4 |
|   | et libellés ; légende cohérente |   |
| 04/11 | Mailles cliquables, délimitation pilote | Passage M1/M2 |
|   | et cases de données manquantes |   |
| 05–06/11 | Fiche réelle via M4, action | Démo collective le 6 |
|   | multiple/conditionnelle, source et |   |
|   | justification |   |
| 09/11 | Intègre module Catalogue/Méthode | Test élu M5 |
|   | développé par M5 ; accessibilité et |   |
|   | captures Q4 |   |
| 10/11 | UX corrigée, branche fusionnée, | Paquet rendu M5 |
|   | démo figée à 18 h |   |
| 11–12/11 | Aucun développement bloquant ; | Écrit M5 |
|   | test de lecture du PDF si besoin |   |

## B4 — M4 : API, moteur R1–R4 et sobriété mesurée

| Échéance | Livrable / tâche | Transmission attendue |
| --- | --- | --- |
| 30/10 | API TEST, README, .gitignore, | M3 peut se connecter |
|   | démarrage et /health |   |
| 02–03/11 | Canon API au singulier/pluriel décidé | M2/M3 signent contrat |
|   | une fois ; tests JSON/GeoJSON |   |
| 04–05/11 | Lit exports M2, endpoints réels ; | M3 affiche données et fiches |
|   | premier moteur générique alimenté |   |
|   | par R1–R4 |   |
| 06/11 | Démo réelle + implémentation des | Test collectif |
|   | règles, statuts de défaut et |   |
|   | explications |   |
| 09/11 | Quatre règles exécutables, campagne | M2 vérifie la logique, M5 documente |
|   | Q3, README, sortie statique, | chiffres |
|   | mesures Q4 |   |
| 10/11 | Test sur autre ordinateur, | M5 assemble paquet |
|   | 200/404/422, archive serveur et |   |
|   | secours final, gel 18 h |   |
| 11–12/11 | Vérification de disponibilité, pas de | M5 remet écrit |
|   | refonte serveur |   |


## B5 — M5 : coordination, écrit, douze fiches et développement React

| Échéance | Livrable / tâche | Transmission attendue |
| --- | --- | --- |
| 30/10 | Confirme modalités/heure d'envoi du | Tous savent leur tâche |
|   | 12 ; PRD, tableau équipe, trame des 5 |   |
|   | réponses, partage fiches |   |
| 02/11 | Décision pilote, contacts experts non | Appui M1/M2/M3 |
|   | bloquants, initialise module React |   |
|   | Catalogue |   |
| 03/11 | Catalogue JSON modèle, page | M1/M2 enrichissent fiches |
|   | Méthode, contrat validé avec M3/M4 |   |
| 05/11 | ÉCRIT V1 COMPLET, premières fiches | Retours M1/M2 sur exactitude |
|   | harmonisées, module React en |   |
|   | développement |   |
| 06/11 | Relecture démonstration, texte | M3 prépare intégration |
|   | méthode et limites, progression du |   |
|   | module |   |
| 09/11 | 12 fiches complètes + composant | Documents prêts à finaliser |
|   | intégré ; ÉCRIT V2 RE-LU par |   |
|   | l'équipe ; collecte captures/mesures |   |
| 10/11 18 h | ÉCRIT FINAL, PDF/format officiel, | Paquet candidat complet |
|   | annexes, archive, démo et relecture |   |
|   | collective ; gel |   |
| 11/11 | PAQUET FINAL PRÊT, dernière | Prêt à déposer le lendemain |
|   | vérification et secours ; aucun |   |
|   | développement |   |
| 12/11 | ENVOI DE L'ÉCRIT OFFICIEL, accusé | Clôture du rendu écrit |
|   | de réception et information |   |
|   | immédiate du groupe |   |
| 13–23/11 | Amélioration facultative | Ne modifie pas l'écrit remis |
|   | démonstration, retours mentors, |   |
|   | répétitions et pitch |   |

## ANNEXE C — Règles de collaboration et engagements de preuve

- Aucun passage de relais sans contrôle d'acceptation : un fichier livré mais illisible par le destinataire n'est pas « terminé ».

- Aucun indicateur non documenté : méthode et unités sont accessibles à M5 et à l'utilisateur technicien.

- calculée non affichée comme faible. Aucun résultat illusoire : données TEST non présentées comme réelles, données absentes non remplacées par zéro, classe non

- Aucune « action optimale » inventée : la liste propose les familles à examiner, pas une promesse écologique ou financière.

- géographie originale. Aucune confusion entre géométries et affichage : hexagone = unité d'agrégation, événement = conflit potentiel, source =

- Aucun changement silencieux de contrat : modification versionnée et approuvée par le fournisseur et le consommateur.

- Aucune personnalisation non vérifiée du jury : la démo est vraie, courte, accessible et dispose d'un plan B.
