# Recette finale du MVP

État de référence pour la dernière recette, le logo et la sélection exacte : [RECETTE_AVANT_PUSH_20261115.md](RECETTE_AVANT_PUSH_20261115.md). Ce rapport conserve les constats de la phase précédente.

Complément scientifique du 15 novembre : [matrice indicateurs–code–sources](TRACABILITE_SCIENTIFIQUE_20261115.md) et [recette dédiée](RECETTE_SCIENTIFIQUE_20261115.md). Les pages Méthode relient les références à chaque étape, distinguent les méthodes non implémentées et documentent les trois formules.

15 novembre 2026. Les contrôles ci-dessous ont été exécutés ; les résultats des anciennes recettes ne sont pas simplement repris.

| Contrôle | Résultat |
| --- | --- |
| Suite M2 complète | **1 538 réussis**, 40 avertissements existants |
| Suite backend | **42 réussis**, un avertissement Starlette/httpx |
| Tests frontend de priorités, actions, contrat V2 et présentations | Réussis |
| Contrôle des 101 fiches et distributions par famille | 205 propositions, 88/61/13 mailles, A/B/C 93/45/67, sans mutation |
| Navigateur local V2 | 101 mailles, 205 cartes, 15 mailles à quatre pistes, 13 sans proposition |
| Scénarios nommés | Rouge, orange à quatre familles, jaune, gris, exploratoire seule, sans proposition, observations liées, relation incertaine, recherche multimailles et recherche vide |
| Couleurs | Distribution 27/33/9/32 identique aux données ; aucune classe verte ; labels définitifs présents |
| Responsive local et public | 320, 390, 768, 1024 et 1440 px, détails ouverts, sans débordement ni chevauchement détecté |
| Accessibilité | Contrôles nommés, focus visible, détails au clavier, repères numérotés et libellés textuels ; contraste des repères au moins 4,80:1 |
| Fond routier, recette V2 | 184 tuiles reçues, zéro réponse de tuile en erreur ; repli volontairement testé sans perdre la grille |
| Chargement des fiches | Erreur 503 et réessai ; refus des sources incompatibles ; pas de faux repli vers les données publiques |
| Build public | TypeScript et compilation réussis avec les deux drapeaux locaux forcés |
| Navigation du build public | Carte, méthode, catalogue et fiche réelle, sans backend ni requête API ; cinq largeurs et liens SPA/directs |
| Différence public/local | Publiquement : 101 fiches, 404 examens de familles dont 165 pistes historiques à étudier ; aucune proposition V2 exposée |
| Modes historiques | Absents du parcours public normal ; recette historique réussie avec un drapeau local explicite |
| Accès au lot brut | HTTP 403 depuis le serveur frontend |
| Build et fichiers | Composants/contenus V2 exclus ; 15 ressources publiques identiques ; aucun lot interne ou chemin personnel embarqué |
| Dépendances | `npm ci` réussi dans une copie temporaire du manifeste et du lockfile ; versions du projet inchangées |
| Réconciliation CSS | Zéro conflit dans la comparaison à trois versions des fichiers concernés ; tests de navigation après correction |
| Erreurs JavaScript, recettes finales | Zéro |

Le test historique avait une course initiale entre le chargement du fond et le calcul des coordonnées du clic. Il attend maintenant la fin du chargement et du mouvement de carte ; ses assertions de données, couleurs, clics et navigation sont conservées. La première tentative d’installation hors ligne manquait de cache ; l’installation depuis le registre a ensuite réussi dans un dossier temporaire. Aucun verrou n’a été désactivé pour faire passer un contrôle.

Le build conserve l’avertissement de taille de MapLibre. L’installation temporaire signale le script optionnel macOS `fsevents` ; aucune politique d’autorisation des scripts du projet n’a été modifiée. Ces avertissements ne bloquent pas les résultats rapportés.

## Reproduction depuis la racine applicative

`QA_PYTHON` désigne un Python 3.10 ou plus avec `backend/requirements-dev.txt`. `PLAYWRIGHT_MODULE_PATH` désigne un module Playwright installé localement et `CHROME_EXECUTABLE_PATH`, si nécessaire, le navigateur. Aucun chemin de compte personnel n’est requis dans le code.

```sh
RECONNECT_M2_V2_ROOT=../Datathon-normandie-2026/data/derived/m2_multiactions_experimental_v2_20261112_01/lot_experimental_v2 \
RECONNECT_M2_ZIP=../Datathon-normandie-2026/data/derived/caen_et_nord_actions_20261112_01/RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1.zip \
PYTHONPATH=backend "$QA_PYTHON" -B -m pytest -q -p no:cacheprovider backend/tests backend/test_server.py
npm --prefix frontend run test:priorities
npm --prefix frontend run test:actions
RECONNECT_V2_API_URL=http://127.0.0.1:8768 npm --prefix frontend run test:multiactions-v2
RECONNECT_V2_API_URL=http://127.0.0.1:8768 npm --prefix frontend run test:action-presentations
VITE_M2_MULTIACTIONS_V2=1 VITE_HISTORICAL_REVIEW=1 VITE_M4_API_BASE_URL=static \
  npm --prefix frontend run build -- --outDir /tmp/reconnect-mvp-public-build
RECONNECT_BUILD_DIR=/tmp/reconnect-mvp-public-build npm --prefix frontend run test:production-safety
```

Servir le build dans un autre terminal :

```sh
npm --prefix frontend run preview -- --host 127.0.0.1 --port 5187 --strictPort --outDir /tmp/reconnect-mvp-public-build
```

Puis :

```sh
RECONNECT_V2_PREVIEW_URL=http://127.0.0.1:5187 npm --prefix frontend run test:browser:multiactions-v2
RECONNECT_PUBLIC_PREVIEW_URL=http://127.0.0.1:5187 npm --prefix frontend run test:browser:production
```

La recette historique utilise 5183/8767 et exige désormais `VITE_HISTORICAL_REVIEW=1`, `VITE_M2_MULTIACTIONS_V2=0` au démarrage du serveur Vite local. Ses routes et résultats restent séparés de la V2 et de la production. Les tests réels de lots requièrent les ressources internes ; une CI sans ces lots ne doit pas déclarer les avoir vérifiés lorsqu’ils sont ignorés.

## Captures et reçus locaux

Ils sont conservés sous `data/derived/finalisation_mvp_20261115/qa/`, hors du répertoire public et ignorés par Git :

- [Rouge et observations liées](../data/derived/finalisation_mvp_20261115/qa/desktop_linked.png)
- [Quatre pistes](../data/derived/finalisation_mvp_20261115/qa/desktop_four.png)
- [Jaune](../data/derived/finalisation_mvp_20261115/qa/desktop_yellow.png)
- [Gris](../data/derived/finalisation_mvp_20261115/qa/desktop_gray.png)
- [Piste exploratoire seule](../data/derived/finalisation_mvp_20261115/qa/desktop_exploratory.png)
- [Sans proposition](../data/derived/finalisation_mvp_20261115/qa/desktop_empty.png)
- [Relation incertaine](../data/derived/finalisation_mvp_20261115/qa/desktop_uncertain.png)
- [Détails sur mobile](../data/derived/finalisation_mvp_20261115/qa/mobile_details.png)
- [Méthode locale sur ordinateur](../data/derived/finalisation_mvp_20261115/qa/method_1440.png)
- [Méthode locale sur mobile](../data/derived/finalisation_mvp_20261115/qa/method_390.png)
- [Build public : méthode](../data/derived/finalisation_mvp_20261115/qa/public_methode.png)
- [Build public : fiche réelle](../data/derived/finalisation_mvp_20261115/qa/public_fiche.png)

Les trois reçus navigateur, les rapports JUnit M2/backend et le reçu de comparaison CSS sont stockés au même endroit. Ces preuves ne font pas partie des fichiers proposés au commit.
