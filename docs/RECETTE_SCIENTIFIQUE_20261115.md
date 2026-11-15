# Recette du complément scientifique

15 novembre 2026. Contrôles exécutés après ajout des références et de leur correspondance au code. Le rapport principal est [la matrice scientifique](TRACABILITE_SCIENTIFIQUE_20261115.md).

| Contrôle | Résultat |
| --- | --- |
| Références | 12 notices : titres, organismes/auteur, dates et portée confrontés aux sources primaires ; dates absentes signalées, notice Jaeger distinguée du texte intégral non consulté. |
| Liens affichés | 18/18 URL répondent HTTP 200, redirections suivies ; titres et destinations conservés. Ancien lien régional non confirmable remplacé dans l’interface par la page officielle DREAL. |
| Provenance historique | Cinq références déjà présentes dans les règles ; OFB continuités et SDES déjà présents dans la méthode ; autres compléments identifiés comme tels. Aucun usage rétrospectif inventé. |
| Formules | Trois origines explicites, variables, unités, hypothèses et fonctions ; aucune attribution à un indice publié non calculé. |
| Calcul réel | Intersections recomposées depuis les trois GeoPackage sources, en lecture seule ; surfaces locale et publique concordantes ; unités converties et arrondis contrôlés. Empreintes des entrées dans le reçu numérique. |
| Familles et couleurs | Références propres aux quatre familles ; sélecteurs A/B/C et politique d’examen identifiés comme conventions d’équipe ; protocoles écologiques manquants signalés. |
| M2 | 1 538 tests réussis, 40 avertissements existants. Aucun fichier scientifique modifié. |
| Frontend | TypeScript, tests priorités/actions, contrat V2 et projection éditoriale réussis. |
| Parcours local | 101 mailles, 205 cartes, 15 secteurs à quatre pistes, 13 sans proposition ; distributions A/B/C et couleurs conservées. Recherche, clavier, états d’erreur/réessai et repli cartographique réussis. |
| Méthode, détails ouverts | Local et public, 12 références et 3 provenances ; cinq largeurs 320/390/768/1024/1440 px, sans débordement horizontal. Captures ordinateur et mobile inspectées. |
| Build public final | Compilation réussie avec les deux drapeaux locaux forcés ; aucun contenu/donnée V2 embarqué ; 15 ressources publiques identiques. |
| Navigateur public final | Carte, méthode, catalogue, fiche réelle ; cinq largeurs, contraste documentaire et navigation sans backend réussis ; aucun appel API. |
| Intégrité | 1 268 fichiers scientifiques/publics protégés identiques avant/après ; archives et propositions préservées. HEAD des deux worktrees inchangés, index vides. |

La première tentative de collecte M2 lancée sans dossier explicite a rencontré les copies de tests archivées et des doublons de noms de modules. La commande corrigée cible `tests/` ; les 1 538 tests passent sans supprimer ni modifier les archives. Les URL data.gouv initialement munies d’une barre finale provoquaient une redirection 308 mal suivie par le vérificateur Python ; l’interface utilise maintenant leurs URL canoniques, vérifiées en HTTP 200. Le build conserve l’avertissement existant de taille de MapLibre.

## Pièces de recette locales

Les fichiers de preuve sont conservés dans `data/derived/audit_scientifique_20261115/`, dossier technique ignoré par Git et absent des ressources publiques :

- [Vérification des liens](../data/derived/audit_scientifique_20261115/links.json).
- [Calculs réels et empreintes des entrées](../data/derived/audit_scientifique_20261115/numeric.json).
- [Intégrité avant/après](../data/derived/audit_scientifique_20261115/integrity.json).
- [Résultats M2](../data/derived/audit_scientifique_20261115/tests_m2.xml).
- [Recette des 101 mailles et 205 cartes](../data/derived/audit_scientifique_20261115/local_validation_browser.json).
- [Recette du build public](../data/derived/audit_scientifique_20261115/public_validation_production.json).
- [Détails ouverts sur cinq largeurs](../data/derived/audit_scientifique_20261115/expanded_validation.json).
- [Page Méthode locale](../data/derived/audit_scientifique_20261115/expanded_local_foundations.png) et [formule sur mobile](../data/derived/audit_scientifique_20261115/expanded_local_formula_mobile.png).

## Reproduction

Depuis le dépôt scientifique, avec l’environnement géospatial existant :

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests
```

Depuis la racine applicative, avec les serveurs locaux 5184/8768 et le module Playwright déjà disponible :

```sh
npm --prefix frontend run typecheck
npm --prefix frontend run test:priorities
npm --prefix frontend run test:actions
npm --prefix frontend run test:multiactions-v2
npm --prefix frontend run test:action-presentations
npm --prefix frontend run test:browser:multiactions-v2
VITE_M2_MULTIACTIONS_V2=1 VITE_HISTORICAL_REVIEW=1 VITE_M4_API_BASE_URL=static \
  npm --prefix frontend run build -- --outDir /tmp/reconnect-science-public-build
RECONNECT_BUILD_DIR=/tmp/reconnect-science-public-build npm --prefix frontend run test:production-safety
```

La recette navigateur publique utilise un `vite preview` loopback temporaire sur 5187 et `test:browser:production`, sans backend. `PLAYWRIGHT_MODULE_PATH` doit désigner le module Playwright de l’environnement ; aucun chemin personnel n’est ajouté aux sources.

Aucune commande de staging, commit, push, merge ou déploiement n’a été exécutée. Les modifications préexistantes du worktree sont conservées. Le backend, les contrats et les gardes du mode local n’ont pas été modifiés par ce complément. La liste applicative de revue est complétée avec les deux nouveaux composants/registre et les deux rapports, sans exécuter les commandes Git proposées.
