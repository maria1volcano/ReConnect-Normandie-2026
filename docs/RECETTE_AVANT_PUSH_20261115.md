# Dernière recette avant push — 15 novembre 2026

## Verdicts séparés

**Code prêt à être committé et poussé pour revue : OUI**, avec la sélection explicite de 59 chemins ci-dessous. Aucun commit ou push n’est réalisé par cette recette. La fusion de la PR et un déploiement ne sont pas déclarés prêts : ils demandent l’intégration Git future, une nouvelle évaluation GitHub et la résolution du contrôle Vercel existant en échec.

**Autorisation de publier les 205 pistes V2 : NON.** Le build public continue de servir les données historiques déjà autorisées. La candidature V2 n’est ni approuvée, ni raccordée à un lecteur public. Une autorisation de diffusion et une étape distincte d’intégration restent indispensables.

La seule alerte de style est `global.css:2429: new blank line at EOF`. Les mêmes lignes vides sont présentes dans le `main` distant examiné et ont été conservées pour éviter un conflit purement textuel. La simulation à trois versions ne produit aucun marqueur de conflit. Cette alerte est documentée, sans modification du contrôle de whitespace ou masquage par configuration Git.

## Changements ciblés pendant cette recette

La refonte n’a pas été reprise. Trois fichiers sources seulement ont changé par rapport au début de cette vérification :

- `StudyLegend.tsx` : les quatre anciens libellés du parcours historique utilisent désormais les mêmes formulations que la V2 ; le texte précise la portée routière et l’indépendance des niveaux des solutions.
- `TerritorialZoneDetail.tsx` : le badge historique traduit la couleur reçue avec les libellés de présentation, sans réécrire le champ du backend ou calculer une priorité.
- `global.css` : fin de fichier réconciliée avec le main exact. Les règles du nouveau logo sont conservées.

Aucune modification du backend, des calculs M2, contrats, données publiques, lots scientifiques ou protections locales. Le lockfile préexistant est préservé et exclu de la sélection. Les autres changements de cette recette sont les rapports et la liste de fichiers.

## Références scientifiques

Les 12 références affichées ont été rapprochées de leur rôle exact et des sections de la page Méthode. Les 18 liens de références et données affichés répondent en HTTP 200. Les auteurs/organismes, titres et dates sont cohérents avec les pages primaires ; les pages OFB sans date restent signalées comme telles. Pour Jaeger, seule la notice et le résumé ont été consultés, sans prétendre avoir reproduit son texte intégral.

| Élément | Fondement documenté | Ce qui n’est pas attribué à la publication |
| --- | --- | --- |
| Continuités et contexte régional | OFB continuités ; composantes du schéma régional Basse-Normandie 2014, dont limites au 1/100 000. | Fonctionnalité actuelle des objets locaux, précision améliorée par la grille. |
| Franchissements pour la faune | Cerema, guide 2021 et démarche obstacles 2026 : ouvrages, espèces et diagnostic. | Croisement assimilé à un obstacle, score national de transparence, sélection locale A/B/C. |
| Haies | OFB gestion des haies : état, entretien, préservation et plantation à distinguer. | Seuil de lacune ou densité, rupture fonctionnelle inférée d’un contact. |
| Milieux humides | OFB continuités et référentiel régional ; OFB « Restauration de mares » comme exemple de projet seulement. | Protocole général d’implantation, distance entre mares ou déficit local calculé. |
| Friches | Cerema renaturation 2022 et friches/biodiversité 2025 : sols, habitats et projets à étudier. | Notation parisienne transposée ou besoin de travaux démontré sur chaque friche. |
| Intersections et unions | Documentation Shapely 2.1.2 : partie commune et union géométrique. | Méthode écologique validant les résultats. |
| Fragmentation, comparaison bibliographique | Jaeger 2000 et SDES 2026 : indices fondés sur les fragments et taille effective de maille. | Indices effectivement implémentés ; les hexagones nominaux de 1 km² ne sont pas cet indicateur. |
| Règles territoriales, qualification et A/B/C | Conventions explicites de l’équipe ; aucun protocole publié retrouvé prescrivant ces sélecteurs. | Validation Cerema/SDES/OFB, gain écologique, urgence ou priorité de travaux. |

Les trois formules gardent leurs origines, variables, unités, hypothèses et fonctions exactes. Le comptage exclusif reste une convention déterministe du projet. L’exemple réel de découpe déjà documenté est conservé ; aucun nouveau résultat scientifique n’a été produit. La [matrice complète](TRACABILITE_SCIENTIFIQUE_20261115.md) reste le document de référence.

## Priorités territoriales et niveaux des solutions

| Couleur | Libellé de présentation | Secteurs V2 |
| --- | --- | ---: |
| Rouge | Secteur à examiner en priorité | 27 |
| Orange | Priorité d’examen élevée | 33 |
| Jaune | Priorité d’examen modérée | 9 |
| Gris | Informations insuffisantes | 32 |

Vérification des légendes, options de recherche/catalogue, fiches, badges et pages Méthode des parcours concernés. Les anciennes formulations de la légende historique et du badge reçu ont été corrigées uniquement à l’affichage. Les valeurs M2 et leurs libellés d’origine restent dans les données. Le mode historique de contrôle reste accessible uniquement sous son drapeau de développement local explicite ; les résultats écologiques historiques ne sont pas renommés en priorités de travaux.

Aucune classe verte ajoutée. Le vert de l’identité visuelle et de la famille haies ne constitue pas une classe territoriale. L’ordre d’examen est indicatif et principalement routier. Les niveaux A/B/C restent indépendants de la couleur et ne sont pas recalculés : 93/45/67, soit 205 pistes, sur 88 secteurs ; 61 secteurs à plusieurs pistes, 13 sans proposition, 15 avec quatre pistes. Les états sans proposition ne concluent pas à une absence écologique.

## Git et compatibilité avec main

| Référence inspectée en lecture seule | Valeur |
| --- | --- |
| Branche applicative | `feat/integration-actions-ui` |
| HEAD applicatif inchangé | `b2c72871ed49a575cc0a4306a28f586afc7d9fbc` |
| `origin/main` local, non rafraîchi | `cb6856fbc40b9377b36ade8de0176a4c87f2d66b` |
| `main` GitHub consulté | `14f6c7fc0d62f930ef8f7d1997b7618f546878c1` |
| Divergence des commits distants | 2 en avance / 2 en retard ; base commune `cb6856f` |
| PR #5 | Ouverte, non fusionnée, tête `b2c7287`, `mergeable=false` pour l’ancien contenu distant. |
| Statut Vercel de cette tête | `failure`, « Deployment was blocked », daté du 12 novembre. |

Le contrôle « Vercel Preview Comments » est réussi ; il indique l’absence de commentaires non résolus, pas la réussite d’un déploiement. La description distante mentionne un ancien blocage de vérification d’auteur Git ; la recette ne modifie ni identité Git, ni configuration Vercel et ne prétend pas avoir résolu ce blocage.

Le nouveau main n’a modifié que `Root.tsx`, `CataloguePage.tsx`, `doc-pages.css` et `global.css` depuis la base commune. Leurs octets ont été relus depuis GitHub. `git merge-file -p`, appliqué à des copies temporaires avec la base commune, donne zéro conflit pour les trois fichiers existants et produit exactement les fichiers de travail. Le fichier documentaire ajouté des deux côtés est identique octet pour octet. Le logo et les corrections locales sont conservés. **Aucun conflit de contenu restant détecté pour ce main précis.** Le statut de la PR distante ne peut pas refléter des changements non committés ; il sera à réévaluer après une future intégration autorisée. Les branches et index n’ont pas été déplacés.

L’écart de lignes vides en fin de CSS produisait un conflit de whitespace lors de la première comparaison. Les fins de fichier de main ont été conservées ; `git diff --check` signale donc l’alerte héritée précisée au début. Une première copie temporaire de `Root.tsx` comportait aussi une ligne finale ajoutée par la sérialisation de l’outil : la comparaison finale a été refaite depuis les octets exacts du contenu distant, sans modifier Root.

Sources distantes : [main examiné](https://github.com/maria1volcano/ReConnect-Normandie-2026/commit/14f6c7fc0d62f930ef8f7d1997b7618f546878c1), [PR #5](https://github.com/maria1volcano/ReConnect-Normandie-2026/pull/5). Le reçu technique conserve les SHA, la divergence et les statuts consultés.

## Liste exacte à committer et exclusions

La liste exécutable à revoir est [COMMIT_APPLICATIF_MVP_20261115.txt](COMMIT_APPLICATIF_MVP_20261115.txt) : **59 chemins**, dont 58 fichiers présents et une suppression intentionnelle. Elle couvre les changements applicatifs existants et les compléments de recette, sans inclure le dépôt scientifique voisin.

Le nouveau `frontend/public/assets/reconnect-normandie-symbole.png` y figure explicitement, ainsi que la suppression de `frontend/public/images/ecological-emblem.png`. `SiteHeader.tsx` pointe vers le nouveau fichier local, possède un `alt` vide pour éviter la répétition du nom déjà porté par le lien, et conserve textes/navigation. L’image est identique au PNG fourni, avec transparence et proportions conservées, 60 px sur ordinateur et 48 px sur mobile. Les hauteurs initiales de l’en-tête sont conservées à l’arrondi près. Les quatre largeurs 320/390/768/1440 passent, ainsi que les liens au clavier et les navigations Carte/Méthode.

Exclusions impératives :

- `frontend/package-lock.json`, seul changement non ignoré exclu : suppression préexistante de quatre marqueurs `peer`, sans changement de version/intégrité. Aucun écrasement ou restauration de cette modification locale.
- `data/derived/**`, dont candidature V2, captures, reçus et ce dossier de recette ; `data/raw/**` et `data/processed/**`.
- Tous les ZIP, GeoPackages, bases SQLite, données scientifiques brutes, environnements Python, caches, journaux, `node_modules`, `dist`, fichiers `.env*` et clés/secrets ; aucun ajout forcé des fichiers ignorés.
- Tous les fichiers M2 non suivis de `../Datathon-normandie-2026` ; ils restent dans leur worktree et hors de la sélection applicative.
- Répertoires temporaires de contrôle et build dans `/tmp`.

La liste est une autorisation technique de sélection, pas un staging exécuté. Revue des extensions, chemins et motifs de secrets sur les fichiers sélectionnés : aucun lot interne ou secret détecté. Les chemins vers les lots dans le code lecteur et les identifiants de traçabilité des tests/documentations ne copient pas les fichiers sources. Le préparateur de candidature est du code ; ses fichiers de sortie sont exclus. Les 20 fichiers déjà présents dans la PR distante ont aussi été examinés : code, tests et documentation, sans nouvel export de données.

## Résultats des tests exécutés

| Contrôle | Résultat |
| --- | --- |
| TypeScript et build Vite | Réussis, avec les deux drapeaux locaux forcés et l’API de production statique. |
| Tests frontend priorités/actions | Réussis. |
| Contrat V2 et projection éditoriale avec le vrai backend local | 101 fiches et 205 présentations, distributions exactes, 13 états sans proposition, aucune mutation ; 81 mots maximum dans la lecture principale. |
| Backend existant | 42 réussis, 1 avertissement de dépendance existant ; verrous de diffusion, scope et proxy contrôlés. |
| Navigateur V2 | 101 mailles, 205 cartes, 15 secteurs à quatre pistes, cinq largeurs, recherche, détails/clavier, méthode, réessai et repli sans fond de carte réussis. |
| Navigateur public | Carte, méthode, catalogue et fiche réelle ; cinq largeurs, contrastes et navigation sans backend ; zéro requête API. |
| Navigateur historique isolé | Quatre couleurs, clics carte, libellés, ancien catalogue/méthode, séparation du résultat écologique, cinq largeurs et refus proxy réussis. |
| Sources/formules ouvertes | Deux pages, 12 références, trois provenances, détails ouverts sur cinq largeurs, sans débordement. |
| Logo | Quatre largeurs, proportions, canal alpha, texte du lien accessible, navigation clavier et hauteur préservée. Captures inspectées. |
| Sécurité du build | Composants/contenus V2 exclus ; 15 ressources publiques conformes aux fichiers autorisés et au nouveau logo ; aucun ZIP/GPKG/secret/chemin privé embarqué. |
| Intégrité | 1 253 fichiers M2 inchangés ; backend, données publiques, lockfile et autres fichiers applicatifs protégés inchangés, hors les trois corrections de présentation/CSS décrites. |
| Git | Index vide ; HEAD et référence locale origin/main inchangés ; aucune opération de commit, push, fusion ou déploiement. |

Le premier navigateur V2 avait terminé les vérifications de données mais dépassé son délai pendant la capture finale. Le parcours complet a été rejoué seul et a réussi, sans assouplir ses assertions. Le build garde l’avertissement connu de taille de MapLibre. La suite scientifique M2 n’a pas été relancée inutilement : ses 1 538 succès précédents sont documentés dans la recette scientifique, et les fichiers scientifiques ont été protégés par empreintes pendant cette vérification ciblée.

## Différences entre local et production ; autorisations manquantes

| Local V2 protégé | Production actuelle |
| --- | --- |
| 101 mailles, 205 pistes, 93/45/67, quatre familles. | 101 fiches, 404 examens de familles, dont 165 pistes historiques à étudier. |
| Développement, drapeau explicite et hôte loopback ; lecteur interne de lots scellés. | Export statique déjà autorisé, sans dépendance au backend du Mac. |
| Page Méthode et exemple V2 issus des données locales. | Méthode adaptée à l’ancien export, exemple autorisé ; aucune donnée V2 reconstituée. |

Pour rendre les 205 pistes publiques, il faut l’export minimisé comprenant `grid.geojson`, `cells.json`, `metadata.json`, `methodology.json`, accompagné du manifeste, de ses versions et empreintes. La candidature existante reste sous `data/derived/v2_public_candidate_mvp_20261115_01/`, hors des chemins servis ; son manifeste vaut SHA-256 `bf9fbaa28df6b2493b70deb965a7c21c287b7be18164685aad6773452595b8d7`, avec `publication_authorized=false`, `approved_by=null`, `approved_at=null`, inchangés.

Il manque : l’approbation explicite de cette candidature et des droits/usages de diffusion, l’acceptation d’un contrat de distribution statique et de son lecteur public, puis une étape autorisée de raccordement et de recette sans backend. Copier les JSON dans public ou activer les drapeaux locaux en production ne constitue pas une solution autorisée. Les lots scellés ne doivent pas être modifiés pour fabriquer une approbation. Le contrôle Vercel et l’autorisation de déploiement sont des sujets séparés, également non résolus par cette recette. Voir [la procédure de publication](PUBLICATION_MVP_20261115.md).

## Commandes Git futures — proposées, non exécutées

À lancer seulement lors d’une étape ultérieure explicitement autorisée, depuis la racine applicative. Ne pas utiliser `git add .` ou `git add -A`, ni reset/clean/stash automatique ; la modification locale du lockfile doit rester intacte.

```sh
git status --short
git fetch origin
git log --oneline --left-right origin/main...HEAD
git diff --check
git diff -- frontend/src/styles/global.css frontend/src/styles/doc-pages.css frontend/src/styles/integration-actions.css
git add --pathspec-from-file=docs/COMMIT_APPLICATIF_MVP_20261115.txt
git diff --cached --name-status
git diff --cached --stat
git diff --cached --check
git commit -m "feat: finaliser le MVP et documenter les limites scientifiques"
```

Les commandes `diff --check` signaleront la ligne vide héritée de main ; vérifier qu’aucune autre erreur n’a été introduite. Avant commit, contrôler la sélection ligne par ligne contre la liste et vérifier l’identité d’auteur Git ; aucun réglage d’identité n’est proposé automatiquement. La liste explicite inclut la suppression du vieil écusson.

Si l’intégration de main est autorisée après ce commit applicatif et une nouvelle lecture du main distant :

```sh
git merge --no-ff --no-commit origin/main
git diff --cached --name-status
npm --prefix frontend run build
# Après revue et recette de l’intégration, sans conflit restant :
git commit -m "chore: integrer main apres la recette du MVP"
git push origin HEAD:feat/integration-actions-ui
```

Ces commandes ne sont pas lancées ici. Si main diffère du SHA examiné, refaire la comparaison avant la fusion. Si un conflit apparaît, préserver les fichiers locaux et résoudre explicitement ; ne pas exécuter de résolution automatique « ours/theirs ». Le brouillon de PR local peut alors servir à actualiser la description distante lors d’une étape autorisée. Un push vers une branche reliée à Vercel peut déclencher une prévisualisation ; l’accord de cette étape doit en tenir compte. La fusion de la PR et la publication des données restent soumises aux vérifications et autorisations distinctes ci-dessus.

## Preuves locales

Les captures et reçus sont dans `data/derived/recette_avant_push_20261115/`, ignoré par Git et absent du build : `github.json`, `compatibility_main.json`, `selection.json`, `integrity.json`, `tests_backend.xml`, `scientific_links.json`, les validations navigateur locale/publique/historique et les captures d’en-tête. Ils permettent de retrouver les états réellement vérifiés sans ajouter de données internes à la sélection.
