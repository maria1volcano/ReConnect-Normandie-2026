# ReConnect Normandie — interface compacte et carte fiable

## Correction livrée

L’introduction de la carte est ramenée d’environ 242 à 158 px sur desktop. Les statistiques sont de petits indicateurs et la notice de provenance reste accessible dans un volet repliable. La recherche et la sélection partagent une ligne sur desktop, avec labels conservés, puis s’empilent sur mobile. La recherche occupe environ 83 px contre 173 px avant correction ; la carte commence vers 388 px au lieu de 690 px sur une fenêtre de 1440 × 900. La carte conserve ses dimensions utiles, avec une colonne de fiche à côté et l’ordre recherche → carte → fiche sur mobile.

Les motifs hexagonaux forestiers restent dans les marges. La topographie est masquée au centre et décalée sous l’introduction ; les motifs ne traversent plus le titre. Le logo, les couleurs de priorité, les icônes, le relief léger, les contenus scientifiques, les fiches et les données sont conservés. Aucune nouvelle illustration ni dépendance.

## Carte vide : reproduction et correction

Le premier diagnostic du build public a montré des routes et des mailles en réseau normal et en cas de tuiles refusées. Le défaut a ensuite été reproduit avec des tuiles lentes : après trois secondes, le style existait mais aucune source ni couche de mailles n’était montée. Le parcours attendait l’événement global `load`, dépendant du chargement du fond distant.

Le montage des couches territoriales se fait désormais dès `style.load`, indépendamment des tuiles. Le composant de grille attend aussi un style prêt, réinstalle ses couches après changement de style, conserve ses états de sélection et signale les erreurs. Un double envoi initial des mêmes données GeoJSON au worker a été supprimé. Un indicateur reste affiché jusqu’au premier rendu effectif des secteurs.

Un problème de tuiles ne masque plus toutes les tuiles déjà reçues et ne remplace pas le style territorial. Le bouton de reprise recharge seulement la source raster existante. Un échec d’initialisation ou de contexte WebGL possède son propre message, sans prétendre que la carte est utilisable, et permet de réessayer. Le fournisseur demeure OpenStreetMap avec son attribution ; aucun fournisseur ajouté.

Les tests inspectent les sources, l’ordre et la visibilité des couches, les opacités, le cadrage et le canvas, puis sélectionnent réellement une maille rendue. Les 101 géométries sont présentes dans la source ; le rendu de la grille est non vide. Les scénarios tuiles lentes et absentes passent sans attendre leur disponibilité. Une recharge de style conserve la sélection ; une initialisation WebGL refusée puis rétablie revient à un seul canvas fonctionnel.

## Parcours et sécurité

`Root.tsx`, `App.tsx` et `LocalReview.tsx` conduisent déjà aux composants communs de Carte, Catalogue et Méthode. Le composant historique `ApplicationLayout.tsx` n’a pas été réactivé. Les corrections utilisent ces composants partagés pour les deux sources.

- Public statique : 101 secteurs, 165 pistes historiques ; aucun backend nécessaire et aucune proposition V2 publiée.
- Local V2 : 101 secteurs, 205 propositions ; A/B/C = 93/45/67.
- Catalogue : quatre familles, icônes, filtres, conditions et liens conservés.
- Méthode : trois formules et douze références conservées, avec limites et distinctions scientifiques.
- Légende compacte : rouge/orange/jaune/gris et explication scientifique repliable conservés.

## Vérification et preuves

La recette locale détaillée est dans `data/derived/recette_finale_interface_20261116/reprise_compacte/`. `comparatif.html` rassemble le rendu avant/après et les captures finales, y compris les fiches à plusieurs propositions. Les JSON contiennent les résultats exécutés, sans substitution de données ni faux fond cartographique.

Contrôles : build TypeScript/Vite ; sécurité du build public (15 ressources publiques identiques, aucun contenu expérimental embarqué) ; contrat public ; catalogue avec 140 combinaisons de filtres et lecture de la V2 réelle ; parcours navigateur public/local à 390, 768 et 1440 px ; recherche, sélection, navigation, catalogue, méthode, légende, débordement, erreurs JavaScript, contrastes et focus ; résilience réseau et WebGL de la carte publique.

Les avertissements de taille de chunk MapLibre restent ceux du build existant. Aucun calcul scientifique M2 relancé, aucun fichier du worktree M2 modifié. Le serveur V2 lit les lots existants avec les protections de développement et de loopback.

## Préparation Git

Worktree : `reconnect-actions-ui`. Branche conservée : `feat/integration-actions-ui`. HEAD inchangé : `08ad65011eeca458d974913b8608508bd1979114`.

Le dernier `origin/main` a été récupéré : `25336e6`, fusion de la PR #5. Il a un commit d’avance sur HEAD, et leurs arbres de fichiers sont identiques. Il n’y a donc aucun ancien changement committé à rejouer ; seules les modifications locales sélectionnées forment la prochaine intégration.

La future PR devra partir d’une nouvelle branche basée sur `origin/main`, après validation des captures, en conservant les modifications locales. La branche historique n’a pas été changée. Le titre et le corps proposés sont dans `PR_PROPOSEE.md` dans la recette ; la liste exacte des chemins est dans `fichiers_a_committer.txt`. Aucune PR distante n’est créée sans les nouveaux commits, lesquels ne sont pas autorisés à cette étape.

Le lockfile local ne diffère de main que par quatre indicateurs `peer`, sans changement de version, résolution ou intégrité. Il est préservé et exclu de la sélection proposée. Le SVG de l’ancienne illustration, désormais sans référence, est également préservé mais exclu. Les sorties, captures, lots, caches, environnements et sauvegardes restent ignorés. Les dépendances installées satisfont le manifeste.

Aucun commit, push, merge ou déploiement.

## Aperçus locaux

- Build public corrigé : `http://127.0.0.1:5190/`.
- Revue V2 locale : `http://127.0.0.1:5184/`.
- Catalogue et Méthode : `/catalogue` et `/methode` sur chacun des deux aperçus.

L’ancien aperçu public sur 5188 reste une référence antérieure, pas la version corrigée.

### Résultats finaux

- 18 configurations de pages et largeurs : réussite sur les deux sources.
- Cartes finales desktop à 1440 × 900 et mobiles à 390 px : fond routier, mailles et attribution visibles.
- Résilience : source de 101 géométries, rendu vérifié et clic réel, réseau lent/absent, reprise des requêtes, recharge de style et reprise WebGL réussis ; aucun appel API public.
- Contrastes des textes ciblés : minimum mesuré 4,78:1 avec approximation conservatrice des surfaces dégradées ; focus visible de 3 px.
- Sélection proposée : 45 chemins, deux exclusions préservées ; aucun payload privé ni secret détecté par le contrôle ciblé. Aucun fichier ajouté à l’index.
- Les sept fichiers existants modifiés pendant cette reprise sont listés dans `integrite_reprise.json` ; les 38 autres fichiers sauvegardés sont identiques. Deux fichiers supplémentaires : test de résilience et présent rapport.
