# ReConnect Normandie — livraison du MVP pour revue avant commit/push

État de référence pour la dernière recette, le logo et la sélection exacte : [RECETTE_AVANT_PUSH_20261115.md](RECETTE_AVANT_PUSH_20261115.md). Ce rapport conserve les constats de la phase précédente.

Complément scientifique du 15 novembre : [matrice indicateurs–code–sources](TRACABILITE_SCIENTIFIQUE_20261115.md) et [recette dédiée](RECETTE_SCIENTIFIQUE_20261115.md). Les pages Méthode relient les références à chaque étape, distinguent les méthodes non implémentées et documentent les trois formules.

15 novembre 2026. **A — PRÊT POUR COMMIT/PUSH DU CODE ET REVUE DE PUBLICATION**, dans le périmètre décrit ci-dessous. Aucune action Git d’écriture ni publication n’a été exécutée. La diffusion publique des 205 propositions reste bloquée : ce rapport n’accorde aucune autorisation.

Interface de revue : **http://127.0.0.1:5184/** ; API locale : **http://127.0.0.1:8768/health**.

## Ce qui est finalisé

- Les couleurs territoriales portent les libellés définitifs : « Secteur à examiner en priorité », « Priorité d’examen élevée », « Priorité d’examen modérée », « Informations insuffisantes ». Aucune catégorie verte n’est créée. Les 27/33/9/32 couleurs restent celles du résultat M2 source.
- Le diagnostic territorial cite désormais les observations propres à la maille : nombre de couples cartographiques, contexte de réservoir ou comptes des éléments observés. Il décrit les données reçues ; il ne recalcule pas le classement.
- Recherche par commune ou secteur, communes réelles, clic sur les hexagones et mise en évidence restent synchronisés. Les raccourcis de démonstration ont disparu.
- Les 205 propositions et leurs niveaux A/B/C sont conservés. Toutes les pistes sélectionnées apparaissent, y compris les quatre solutions de quinze secteurs. Les familles ne sont pas départagées artificiellement.
- Les textes principaux restent explicatifs : deux à trois phrases de justification et une à deux sur l’intervention, 81 mots au maximum pour l’ensemble. Les réserves répétées ont été retirées lorsque la limite spécifique suffit dans les détails. La limite des haies distingue un contact avec une voie d’un recouvrement régional.
- Une seule réserve commune apparaît dans chaque fiche. Les détails contiennent au plus deux indicateurs utiles, une limite spécifique et trois vérifications. Les comptes complets restent dans les ressources rédigées, sans JSON brut.
- Le fond routier OpenStreetMap, ses attributions, les petites commandes et le repli en cas de panne sont conservés. Le périmètre réel est affiché : « Territoire pilote : Caen et cinq communes voisines ».
- La page Méthode locale explique sources, hexagones, Lambert-93, intersections, attribution aux mailles, doublons, trois équations, règles des quatre familles et exemple réel à quatre pistes. Elle explicite aussi les motifs de non-sélection.
- Le parcours public autorisé est également lisible : les modes techniques sont retirés de la navigation normale, les numéros du catalogue sont stables entre filtres, les fiches n’exposent pas les identifiants bruts. La méthode publique explique uniquement l’ancien export effectivement publié.
- Une mention discrète différencie les données publiques autorisées du parcours multi-actions en revue locale. Les écrans techniques historiques sont conservés derrière `VITE_HISTORICAL_REVIEW=1`, seulement en développement sur boucle locale. Le build de production refuse ce mode même si le drapeau est forcé.

## Réconciliation de main, effectivement appliquée

Le `main` distant vérifié est `14f6c7fc0d62f930ef8f7d1997b7618f546878c1`. Ses styles documentaires et son état d’erreur de catalogue ont été repris par modifications ciblées, sans merge, rebase, remplacement aveugle ou déplacement de branche.

- `global.css` et `doc-pages.css` correspondent exactement aux fichiers inspectés de ce `main`.
- Les corrections applicatives précédentes de l’en-tête, du responsive et des commandes cartographiques sont conservées dans `integration-actions.css`, importé après les styles de base.
- L’import documentaire de `Root.tsx` et la séparation du parcours local sont compatibles.
- La simulation textuelle finale contre l’ancêtre commun constate **zéro conflit** sur `global.css`, `Root.tsx` et `CataloguePage.tsx`. La compatibilité visuelle et fonctionnelle a ensuite été testée dans le navigateur.
- Le HEAD et les références locales n’ont pas été déplacés. La PR distante conserve donc son ancien état jusqu’à l’étape Git autorisée ; la résolution est présente dans les fichiers de travail, pas dans un commit déjà poussé.

## Résultats et intégrité

| Indicateur | Résultat conservé |
| --- | ---: |
| Mailles | 101 |
| Propositions | 205 |
| Mailles avec proposition / multi-actions / sans proposition | 88 / 61 / 13 |
| A / B / C | 93 / 45 / 67 |
| Haies A / B / C | 18 / 27 / 17 |
| Milieux humides A / B / C | 4 / 15 / 23 |
| Friches A / B / C | 14 / 0 / 21 |
| Franchissements A / B / C | 57 / 3 / 6 |
| Événements admis / pistes historiques | 5 336 / 165 |
| Rouge / orange / jaune / gris | 27 / 33 / 9 / 32 |

Les fichiers scientifiques, lots scellés, géométries, relations et résultats historiques n’ont pas été modifiés. Les 15 ressources publiques et le lockfile sont inchangés par cette mission. L’état local préexistant est conservé et identifié dans le rapport Git.

## Démonstration scientifique et architecture

La [démonstration documentée lors de la refonte](REFONTE_FINALE_20261115.md#calculs-présentés-et-correspondance-avec-le-code) reste la référence technique pour les équations, les chemins relatifs des fonctions et l’exemple du secteur 26. La page locale présente ces calculs sans demander au lecteur de comprendre les noms de variables du code.

- **M1** fournit géométries, limites et attributs. Les sources réellement intégrées sont IGN BD TOPO et ADMIN EXPRESS, DREAL (schéma régional 2014 et inventaires humides), Cerema Cartofriches et OCS GE pour le contexte effectivement utilisé.
- **M2** découpe et mesure en Lambert-93, détecte et dédoublonne les relations, les attribue aux mailles et applique des règles explicites. Une relation de frontière reste distinguée d’une relation intérieure. Les comptes locaux partagés ne sont pas additionnés comme événements indépendants.
- **M4** vérifie les lots scellés et joint les versions attendues. La projection locale transmet classement, observations et propositions ; elle ne réévalue pas les résultats écologiques.
- **M3** présente les valeurs reçues et traduit les libellés. Les couleurs territoriales, les niveaux de justification et les couleurs de famille restent indépendants.

Les trois équations de la page correspondent à `compute_enjeux` et `aggregate_conflicts` : surface étudiée de l’intersection hexagone–territoire ; proportion d’union des réservoirs sous condition de couverture validée ; somme des comptes exclusifs égale aux 5 336 événements admis. Les tests vérifient les unions, les frontières, les couvertures inconnues et la conservation des relations.

L’exemple local Colombelles / Hérouville-Saint-Clair conserve les valeurs M2 : 862 229,7971970863 m², 68 couples voie–espace régional dont 38 avec les attributs de voie carrossable en service au sol et matrice fragile, sans surface positive de réservoir observée. Il reste orange et porte quatre pistes. L’exemple public de Caen est distinct et utilise les seules données déjà autorisées : 88 couples, 45 avec ces attributs et 89 relations locales ; ces nombres ont été confrontés au JSON public.

Les références Cerema et OFB déjà mobilisées par les documents M2 sont liées dans les pages et le rapport de refonte. Elles soutiennent le cadrage des interfaces, de la gestion des haies, du devenir des friches et des réseaux humides. Elles ne sont pas présentées comme validant nos seuils ou notre politique territoriale. Aucune thèse ou méthode de notation non utilisée n’a été inventée.

La priorité territoriale reste **indicative et principalement routière**. Les fonctions écologiques, les bénéfices et l’urgence de travaux ne sont pas calculés. Les résultats de priorité écologique historiques restent indéterminés, tandis que les opérations géographiques et la sélection des questions d’étude sont opérationnelles et reproductibles.

## Dossier livré

1. Application locale finalisée et démonstration scientifique dans la page Méthode.
2. [Recette, preuves et captures](RECETTE_MVP_20261115.md).
3. [État Git, fichiers et commandes futures](GIT_MVP_20261115.md).
4. [Préparation à la publication et différences local/public](PUBLICATION_MVP_20261115.md).
5. [Description de PR préparée](PR_MVP_FINAL_20261115.md), sans modification distante.

Les rapports des phases précédentes sont conservés comme historiques. Le présent dossier remplace leurs réserves sur le conflit CSS et précise la publication ; il ne remplace aucun contrat scientifique.
