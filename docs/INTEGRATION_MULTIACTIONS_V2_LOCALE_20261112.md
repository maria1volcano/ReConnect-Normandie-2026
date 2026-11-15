# Intégration locale expérimentale des décisions multi-actions V2

12 novembre 2026 — worktree `reconnect-actions-ui`, branche
`feat/integration-actions-ui`. Aucun commit, push, merge, changement de PR distante
ou déploiement. Le dépôt M2 original reste en lecture seule.

**Verdict : intégration locale fonctionnelle**, limitée à la carte et aux fiches
V2 en mode développement. Les pages Catalogue et Méthode existantes conservent
leur contenu historique ; elles ne deviennent pas le catalogue officiel M5 ni
une présentation des 205 nouvelles pistes. La vue cartographique expérimentale
est la page d'accueil lorsque ses commutateurs sont explicitement activés.

## Résultats contrôlés avant ingestion

Le vérificateur M2 V2 a été exécuté en lecture seule (`python -B`) depuis le
dépôt original : inventaire, empreintes, V1 reproductible, sources canoniques et
égalité des décisions reconstruites vérifiés, sans calcul géométrique. Les trois
documents M2 et les exemples réels ont été consultés. Le backend contrôle aussi
le schéma, chaque jointure, les preuves référencées, les ancrages de présence,
les copies D/S/R1–R4 et la traçabilité des 165 pistes avant de servir la projection.

| Indicateur | Vérifié |
| --- | ---: |
| Fiches / géométries de mailles | 101 / 101 |
| Pistes | 205 |
| Mailles avec propositions / multi-actions | 88 / 61 |
| Sans proposition | 13 |
| Niveaux A / B / C | 93 / 45 / 67 |
| Mailles uniquement C | 25 |
| Mailles avec propositions utilisant des observations liées | 11 |
| Événements canoniques / pistes historiques conservés | 5 336 / 165 |
| Recommandations de travaux validées | 0 |

Le lot demeure `test_data=false`, `publication_autorisee=false`. Empreinte du
manifeste V2 :
`95378d1f13bc94418b813b682f3c7a75572126374cb2e825b9e72da0ea8e6057`.
Aucune anomalie bloquante détectée sur ce lot. Les relations géographiques
incertaines et micro-recouvrements restent des limites, notamment pour les A :
ce niveau qualifie une question d'étude et ne démontre aucun besoin de travaux.

## Adaptations réalisées

### Backend

`backend/multiactions_v2.py` ajoute un lecteur séparé, en lecture seule et lié
à l'empreinte du lot. `backend/server.py` conserve ses routes existantes et ajoute :

- `/api/internal/caen/multiactions-v2/metadata` ;
- `/api/internal/caen/multiactions-v2/grid` ;
- `/api/internal/caen/multiactions-v2/cells/{maille_id}`.

Les quatre paramètres `territory_id`, `grid_version`, `dataset_version`,
`decision_version` sont obligatoires et vérifiés exactement. La clé de maille
est contrôlée dans ce périmètre. Le serveur écoute exclusivement `127.0.0.1`,
refuse les hôtes distants, les origines non autorisées et les en-têtes de proxy.
Sans `RECONNECT_ENV=development` et `RECONNECT_M2_MULTIACTIONS_V2=1`, le nouveau
lot n'est pas chargé et ses routes restent désactivées. Aucune solution de repli
vers les données anciennes n'est employée en cas d'erreur V2.

Seules les géométries **découpées des mailles** sont servies. La projection par
fiche fournit noms, objectifs, niveaux, observations synthétiques, relation
spatiale, incertitudes, conditions, contexte attributaire autorisé et résultats
scientifiques conservés. Les objets sources bruts, IDs d'objets/preuves/événements,
géométries de routes/corridors/haies et chemins locaux ne sont pas transmis.
Les attributs NULL restent NULL dans les détails autorisés. Les empreintes sont
des références de traçabilité, jamais une autorisation de publication.

### Frontend

`multiActionsV2Adapter.ts` contrôle le périmètre, la version, les compteurs, la
présence de justifications et les verrous. La vue expérimentale exige à la fois
le mode Vite **développement**, `VITE_M2_MULTIACTIONS_V2=1` et un hôte local. Son
API doit être une URL HTTP de boucle locale. Le build de production reste sur
les données publiques anciennes, même si le drapeau V2 est fourni au build.

La liste de pistes est de taille variable, y compris zéro. Chaque carte présente
un nom lisible, A/B/C, l'objectif, la possibilité à étudier, l'observation et une
note d'incertitude ; les explications, vérifications et résultats scientifiques
sont repliables. Les familles non sélectionnées restent consultables. Il n'y a
pas d'action principale imposée, de score, de bénéfice comparé ni de travaux validés.
Les observations liées sont signalées sans addition de force de preuve.

La vue V2 utilise une **teinte uniforme de repérage**, sans synthèse globale
calculée à partir des solutions. La légende explique A/B/C ; les vues documentaires
V1–V4 et D/S historiques restent explicitement séparées. Le fond de carte V2
emploie les limites administratives déjà disponibles localement : aucun appel de
page à un service externe pendant la recette V2.

La disposition desktop sépare carte et fiches ; le mobile les empile. Les
attributions et commandes disposent d'une marge de cadrage, sans recouvrir les
mailles à sélectionner. Le délai de secours réservé au fond distant ne réinitialise pas la carte locale.
Dans cette vue V2, le clic de maille ne sélectionne pas un département et
conserve le cadrage sur Caen. Les changements de vue modifient la peinture sans
recréer les abonnements MapLibre ; les callbacks sont désabonnés précisément.
Un défaut de fiche historique périmée lors d'un changement de maille a également
été corrigé : la clé complète doit correspondre avant d'afficher les données.
Les tests historiques n'ont pas été assouplis.

## Services locaux et commandes exactes

Adresse principale : **http://127.0.0.1:5184/**.
Backend : **http://127.0.0.1:8768/health**.
Les services anciens sur 5183/8767 restent préservés. Ne pas utiliser le domaine
Vercel pour cette expérimentation et ne pas rendre ces ports accessibles par proxy.

Les deux services V2 sont démarrés à la livraison. Pour les relancer, ouvrir deux
terminaux, après arrêt de leurs instances précédentes. Depuis le worktree UI :

```bash
# Terminal 1, racine de reconnect-actions-ui
RECONNECT_ENV=development \
RECONNECT_M2_MULTIACTIONS_V2=1 \
RECONNECT_M2_V2_ROOT=../Datathon-normandie-2026/data/derived/m2_multiactions_experimental_v2_20261112_01/lot_experimental_v2 \
RECONNECT_M2_ZIP=../Datathon-normandie-2026/data/derived/caen_et_nord_actions_20261112_01/RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1.zip \
RECONNECT_M4_PORT=8768 \
RECONNECT_FRONTEND_ORIGIN=http://127.0.0.1:5184 \
/private/tmp/reconnect_actions_fastapi_20261112/bin/python -B backend/server.py
```

```bash
# Terminal 2, racine de reconnect-actions-ui
cd frontend
VITE_M2_MULTIACTIONS_V2=1 VITE_M4_API_BASE_URL=http://127.0.0.1:8768 \
  npm run dev -- --host 127.0.0.1 --port 5184 --strictPort
```

Le Python ci-dessus est l'environnement de tests déjà présent sur cette machine,
réutilisé sans modifier le venv M2. Sur une autre machine ou après suppression de
ce dossier temporaire, installer `backend/requirements-dev.txt` dans un venv
local au worktree UI et remplacer cet exécutable par celui du venv. Les dépendances
Node déjà présentes ont été réutilisées ; aucun `npm ci` ni changement du lockfile
n'a été nécessaire.

## Mailles à tester

Le sélecteur et les quatre boutons d'exemples évitent de saisir les IDs. Pour
un lien direct, utiliser `/?maille=` suivi de l'identifiant encodé (`+` → `%2B`).

| Maille | Résultat attendu |
| --- | --- |
| `NORM-G1K-FLAT-R+006423-C+000488` | A01 A, A02 A, A04 A ; observations routières liées signalées |
| `NORM-G1K-FLAT-R+006423-C+000491` | A01 A, A03 A, A04 A |
| `NORM-G1K-FLAT-R+006421-C+000491` | A03 C seule ; lien avec connectivité incertain |
| `NORM-G1K-FLAT-R+006427-C+000495` | A01 B et A02 C ; ZH Remblais conservée comme telle |
| `NORM-G1K-FLAT-R+006421-C+000490` | Aucune proposition, état vide expliqué |
| `NORM-G1K-FLAT-R+006429-C+000492` | A01 B, A02 C, A04 B ; chemin/sentier et niveau routier à vérifier |

## Vérifications et preuves

- **36 tests backend réussis**, comprenant les tests existants et neuf contrôles
  V2 : 101 fiches, comptes, copies scientifiques, absence d'objets privés dans la
  projection, versions, erreur de chargement, absence du mode et refus HTTP.
- Tests frontend de priorités et d'actions historiques : réussis, inchangés.
- Nouveau test frontend V2 : validations négatives, puis lecture réelle des
  101 fiches via l'API avec contrôle des 205/88/61/13 et 93/45/67.
- TypeScript et build statique : réussis. Le build a été réalisé avec le drapeau
  V2 forcé pour vérifier qu'il ne suffit pas à activer l'expérience en production.
- Chrome V2 : six fiches réelles, détails repliables, observations liées,
  A/B/C et absence, carte neutre et vues historiques, largeurs 320/390/768/1024/1440,
  clic réel mobile après bascules/redimensionnements, absence de faux repli du fond local, erreur 503 et réessai,
  version incompatible, build statique sans appel V2, aucune erreur JavaScript.
- Chrome historique : quatre couleurs/fiches, D/S, catalogue/méthode, cinq
  largeurs et clic mobile ; test existant conservé et réussi.
- Accès direct Vite au JSON M2 brut via `/@fs` : HTTP 403. Routes de fichiers
  sources bruts non fournies par le backend.

Les reçus et captures sont conservés sous
`data/derived/multiactions_v2_ui_20261112_03/qa/`, ignoré par Git.
Un avertissement Starlette/httpx et l'avertissement de taille du module MapLibre
restent consignés ; ils ne bloquent pas l'exécution locale.

Commandes de recette, depuis la racine UI (fournir les mêmes chemins privés que
pour le serveur pour les tests backend réels) :

```bash
RECONNECT_M2_V2_ROOT=../Datathon-normandie-2026/data/derived/m2_multiactions_experimental_v2_20261112_01/lot_experimental_v2 \
RECONNECT_M2_ZIP=../Datathon-normandie-2026/data/derived/caen_et_nord_actions_20261112_01/RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1.zip \
PYTHONPATH=backend /private/tmp/reconnect_actions_fastapi_20261112/bin/python -B \
  -m pytest -q -p no:cacheprovider backend/tests backend/test_server.py
```

```bash
cd frontend
npm run test:priorities
npm run test:actions
RECONNECT_V2_API_URL=http://127.0.0.1:8768 npm run test:multiactions-v2
PLAYWRIGHT_MODULE_PATH=/private/tmp/reconnect_browser_test_20261111/node_modules/playwright-core \
  npm run test:browser:multiactions-v2
VITE_M2_MULTIACTIONS_V2=1 VITE_M4_API_BASE_URL=static npm run build
```

Le test navigateur accepte `RECONNECT_V2_PREVIEW_URL` pour contrôler aussi un
serveur `vite preview` local du build statique, ainsi que `RECONNECT_UI_QA_DIR`
et `CHROME_EXECUTABLE_PATH`. Aucun navigateur/dépendance n'a été installé ici.

## Préservation et limites

Les 345 fichiers M2 et l'état Git M2 pris comme référence avant l'intégration
sont contrôlés inchangés. Les 15 fichiers publics UI, le manifeste public existant
et la modification préexistante de `frontend/package-lock.json` sont préservés.
Ce lockfile était déjà modifié avant l'intervention et n'est pas un changement V2.
Les lots, règles et archives M2 ne sont pas modifiés ni copiés dans le frontend.

Le travail porte sur le code local ; il ne fournit aucune validation écologique
de travaux ni autorisation de diffusion. M5 doit toujours confirmer le catalogue,
les experts qualifier les observations et les porteurs examiner la faisabilité.
Les fichiers V2 restent internes ; aucun export public, ajout à Git ou publication
n'est réalisé. La PR #5 distante et `reconnect-normandie.vercel.app` restent inchangés.
