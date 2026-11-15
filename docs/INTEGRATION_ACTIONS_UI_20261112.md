# Intégration réelle des décisions d’action M3/M4 — 12 novembre 2026

L’intégration est réalisée dans **`feat/integration-actions-ui`**, worktree
`reconnect-actions-ui/`. Sa base est
`origin/main` au commit `cb6856fbc40b9377b36ade8de0176a4c87f2d66b`.
La branche M2, ses fichiers non commités, les archives scellées et les sources
historiques sont conservés. Cette note décrit la préparation avant le commit
d’intégration ; elle n’autorise ni fusion ni publication du nouveau complément.
La branche locale `main` est plus ancienne ; les comparaisons emploient
`origin/main`, sans réinitialisation de branche.

## Ce qui est intégré

Le site existant React/MapLibre/Vite et son adaptateur M4 sont conservés. Le patch
M2 visait `94eef5b8…` ; il a été lu et adapté au code actuel, sans application aveugle.
Les routes actuelles `/api/internal/caen/grid`, `/cells/{maille_id}` et `/metadata`
suffisent ; aucune nouvelle API n’est introduite. Le backend de démonstration
`server.py` accepte l’ancienne livraison et le ZIP final, avec une empreinte attendue
pour chacun. Le backend FastAPI `main.py` et les contrats publics restent inchangés.

Le nouveau lot est reconnu par SHA-256 :
`f509abebd41741f5133949d53b4a88c8db52f34094f99ee00e9b0217eee41927`.
Le diagnostic et les sélections sont lus dans `decision_interventions`, jamais
recalculés à partir d’un nombre d’événements. Les données s’associent exactement
par `(territory_id, grid_version, maille_id)`. Les mauvaises portées sont refusées.
Les statuts scientifiques, NULL et `test_data=False` sont préservés.

| Résultat canonique conservé | Effectif |
| --- | ---: |
| Mailles et fiches | 101 |
| Événements détectés / agrégés / quarantaine | 5 337 / 5 336 / 1 |
| Relations maille–événement / comptes exclusifs | 5 759 / 5 336 |
| Rouge / orange / jaune / gris | 27 / 33 / 9 / 32 |
| Sélections principales A04 par maille | 60 |
| Orientations de préservation / décisions non évaluables | 9 / 32 |
| Pistes historiques conservées | 165 |
| Priorités D/S indéterminées | 101 |
| Recommandations de travaux validées | 0 |

Les 60 sélections sont par maille, sans affirmation de 60 projets indépendants.
Les 105 pistes historiques hors R1 ne deviennent pas des restaurations sélectionnées.
Les géométries des événements ne sont pas remplacées par des calculs frontend ;
elles restent dans l’archive interne. Les comptes présentés proviennent du M2 canonique.

La fiche suit l’ordre territoire/rang d’étude, diagnostic, observations, action
principale, autres actions, préconditions avant travaux, puis D/S et détails.
Les titres compréhensibles remplacent les codes dans la lecture principale. Les
codes, pistes, identifiants, versions et sources restent dans le volet technique.
Les familles non sélectionnées sont distinctes des actions proposées ; en gris,
aucune intervention n’est choisie, y compris lorsqu’une piste historique existe.
Le rang d’étude et D/S ont des vues cartographiques séparées. Les sources indiquent les haies/plans d’eau BD TOPO effectivement acquis ; SIPAF et PRAM sont signalés comme compléments non fournis, sans leur attribuer des observations.

L’en-tête commun ne se chevauche plus. Les contrôles de carte sont séparés du zoom
et des sources ; la légende d’étude est sous la carte. La couleur canonique est projetée vers un attribut scalaire pour MapLibre, qui sérialise les objets imbriqués dans ses tuiles. Le cadrage initial reste sur
Caen au lieu d’être écrasé par le cadrage régional. Les erreurs de fiche sont
visibles et les décisions absentes ne sont pas fabriquées depuis l’ancien export.

## Champs complémentaires

Ces champs étendent la réponse locale existante ; ils ne changent pas la science.

| Champ | Usage |
| --- | --- |
| `study_priority` | Niveau indicatif, couleur exacte du lot, libellé, version et note |
| `instruction.diagnostic` | Diagnostic territorial canonique |
| `instruction.main_action` | Étude principale ou NULL, justification et statut |
| `instruction.complementary_actions` | Compléments réellement sélectionnés, ici [] |
| `instruction.options` | Familles non sélectionnées, motifs et préconditions |
| `instruction.conditions_before_works` | Validations écologiques et techniques requises |
| `instruction.historical_lead_ids` | Traçabilité des 165 pistes sans activation automatique |
| `instruction.DS` | Copie exacte des résultats officiels distincts |
| `provenance` | Empreinte, versions et restrictions du lot source |

Le chargement catalogue utilise la même source que la carte, statique ou backend
local, avec au plus quatre requêtes simultanées et un délai maximal par requête. Cela évite de saturer la file de connexions du serveur local et rend un défaut de réponse visible. Il distingue sélections
courantes et inventaire des pistes historiques. Le cache des fiches statiques
n’est plus annulé par le démontage d’un seul composant.

## Exécution locale du nouveau lot

Dans le worktree d’intégration, avec Python et Node disponibles sur PATH :

```bash
export RECONNECT_M2_ZIP='/chemin/prive/RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1.zip'
RECONNECT_M4_PORT=8767 RECONNECT_FRONTEND_ORIGIN=http://127.0.0.1:5183 python3 -B backend/server.py
```

Dans un autre terminal :

```bash
cd /chemin/du/depot/reconnect-actions-ui/frontend
npm ci
VITE_M4_API_BASE_URL=http://127.0.0.1:8767 npm run dev -- --host 127.0.0.1 --port 5183 --strictPort
```

Les deux services sont locaux, sans reverse proxy public. Les GeoPackages, ZIP et
chemins sources ne sont pas servis. Les requêtes avec en-tête de proxy sont refusées.
Les serveurs de vérification ne sont pas des services de production ; ces
commandes permettent de les lancer localement.

## Vérifications effectuées

- **27 tests backend passent** : API FastAPI existante, ancien test de store et
  import réel du lot final, 101 jointures/décisions, 165 pistes, 5 336 comptes
  exclusifs, NULL, statuts et refus de diffusion sans autorisation liée.
- `npm run test:priorities` et `npm run test:actions` passent. Le deuxième contrôle
  vérifie aussi les 101 fiches de la candidature lorsqu’on lui donne son dossier.
- `VITE_M4_API_BASE_URL=static npm run build` passe avec les dépendances verrouillées.
- Chrome : clics réels sur les quatre couleurs, étude de passage en rouge/orange,
  préservation en jaune, aucune sélection en gris, D/S séparée, provenance au clic,
  catalogue/méthode/carte, largeurs 320/390/768/1024/1440 et clic réel mobile.
  Aucun chevauchement d’en-tête ni débordement horizontal, aucune erreur JavaScript. Les quatre couleurs sont vérifiées dans les propriétés rendues et les avertissements de couleur MapLibre sont contrôlés.
- Build statique : ancien export public inchangé, aucune API interne appelée et
  aucune nouvelle décision déduite. Les nouveaux JSON ne sont pas inclus dans le build.
- `git diff --check` passe. Aucun gros ZIP/GeoPackage dans les changements Git.

Un avertissement Starlette/httpx de l’environnement de test et l’avertissement
Vite de taille du module MapLibre sont consignés ; aucun échec n’est masqué.
Les preuves, journaux et captures sont dans
`data/derived/actions_ui_review_20261112_01/qa/` (ignoré par Git).

Pour reproduire les tests :

```bash
RECONNECT_M2_ZIP="$RECONNECT_M2_ZIP" PYTHONPATH=backend python3 -m pytest -q backend/tests backend/test_server.py
cd frontend
npm run test:priorities
M2_ACTIONS_CANDIDATE_ROOT=../data/derived/actions_ui_review_20261112_01/public_candidate npm run test:actions
VITE_M4_API_BASE_URL=static npm run build
```

Installer préalablement les dépendances `backend/requirements-dev.txt` dans un
venv adapté. Le smoke navigateur fourni requiert `playwright-core` et Chrome ;
`PLAYWRIGHT_MODULE_PATH` et `CHROME_EXECUTABLE_PATH` permettent de désigner leurs
installations. Avec les deux services locaux ci-dessus : `npm run test:browser:actions`.
`RECONNECT_UI_QA_DIR` peut définir son dossier de preuves hors des fichiers publics.

## Publication : blocage précis et candidature prête

**Le domaine Vercel n’a pas été modifié.** L’autorisation historique de
`docs/PUBLIC_RELEASE_MANIFEST.json` concerne un ancien ZIP. Le complément
ACTIONS_ETUDE porte `publication_autorisee=false` ; aucune autorisation de diffusion
liée à cette nouvelle empreinte n’a été fournie. Aucun fichier du lot interne n’a
été placé dans `frontend/public`. L’ancien manifeste et ses deux fichiers publics
restent strictement inchangés.

Une candidature minimisée a été générée **hors des répertoires servis** :
`data/derived/actions_ui_review_20261112_01/public_candidate/`.
Elle contient les deux fichiers adaptés aux chemins statiques déjà employés par
Vercel (`grid.geojson`, `cells.json`), un manifeste, une note et un modèle
d’autorisation non validé. Les listes d’objets sources, géométries d’événements,
GeoPackages et chemins locaux sont exclus ; les sources/limites et les statuts restent.

ZIP de revue :
`data/derived/actions_ui_review_20261112_01/RECONNECT_CAEN_ACTIONS_CANDIDATURE_MINIMISEE_20261112_V1.zip`.
Il est **non publiable en l’état de l’autorisation**, même s’il est minimisé et testé.
Son SHA-256 est `577037b56ad593442eb9e1361b05d5b5eabd8efd0b5ffe84738b89e8b1de535e` (`104756` octets).
L’archive source M2 scellée n’est jamais modifiée ni ajoutée à Git.

Pour terminer la publication, faire valider précisément cette candidature et son
périmètre de diffusion, puis renseigner `authorization.template.json` dans une
copie : `publication_authorized=true`, auteur et date d’approbation, version et
empreinte exactes. Aucun auteur ou accord n’est prérempli. Lancer ensuite, après
cette validation seulement :

```bash
RECONNECT_M2_ZIP="$RECONNECT_M2_ZIP" python3 -B backend/export_public_release.py --authorization /chemin/autorisation_validee.json
```

Cette opération explicite produit l’export public minimisé et son nouveau
manifeste. L’archive interne garde ses restrictions, `test_data=False` et toutes
ses empreintes. Refaire build et contrôles de diffusion avant commit/push validés.
Le frontend Vercel continue d’utiliser `VITE_M4_API_BASE_URL=static` : il n’a pas
besoin d’un nouveau domaine ni d’une API locale accessible publiquement.

## Fichiers modifiés et préparation Git

- `backend/README.md`
- `backend/export_public_release.py`
- `backend/server.py`
- `backend/tests/test_actions_delivery.py`
- `docs/INTEGRATION_ACTIONS_UI_20261112.md`
- `docs/PR_INTEGRATION_ACTIONS_UI.md`
- `frontend/package.json`
- `frontend/scripts/smoke-actions-ui.cjs`
- `frontend/scripts/verify-actions.mjs`
- `frontend/src/components/layout/ApplicationLayout.tsx`
- `frontend/src/components/legend/StudyLegend.tsx`
- `frontend/src/components/map/RealGridLayer.tsx`
- `frontend/src/components/map/RegionMap.tsx`
- `frontend/src/components/sector/TerritorialZoneDetail.tsx`
- `frontend/src/integrations/catalogueData.ts`
- `frontend/src/integrations/m4Adapter.ts`
- `frontend/src/integrations/priorityAdapter.ts`
- `frontend/src/pages/CataloguePage.tsx`
- `frontend/src/pages/MethodePage.tsx`
- `frontend/src/styles/global.css`

Les changements incluent le test navigateur et les notes de livraison/PR.
Commandes prévues pour préparer la PR, après revue et validation :

```bash
cd /chemin/du/depot/reconnect-actions-ui
git branch --show-current
git diff --check
git diff --stat origin/main
git add backend/README.md \
  backend/export_public_release.py \
  backend/server.py \
  backend/tests/test_actions_delivery.py \
  docs/INTEGRATION_ACTIONS_UI_20261112.md \
  docs/PR_INTEGRATION_ACTIONS_UI.md \
  frontend/package.json \
  frontend/scripts/smoke-actions-ui.cjs \
  frontend/scripts/verify-actions.mjs \
  frontend/src/components/layout/ApplicationLayout.tsx \
  frontend/src/components/legend/StudyLegend.tsx \
  frontend/src/components/map/RealGridLayer.tsx \
  frontend/src/components/map/RegionMap.tsx \
  frontend/src/components/sector/TerritorialZoneDetail.tsx \
  frontend/src/integrations/catalogueData.ts \
  frontend/src/integrations/m4Adapter.ts \
  frontend/src/integrations/priorityAdapter.ts \
  frontend/src/pages/CataloguePage.tsx \
  frontend/src/pages/MethodePage.tsx \
  frontend/src/styles/global.css
git commit -m "feat: intégrer les décisions d’étude M2 dans l’application"
git push -u origin feat/integration-actions-ui
```

Ces commandes portent sur le code et la documentation. Ne pas ajouter le ZIP de
revue ni les données internes. Si la candidature est autorisée ultérieurement,
examiner et ajouter séparément les deux exports minimisés et leur manifeste.
La Pull Request doit cibler `main` ; son texte est préparé dans
`docs/PR_INTEGRATION_ACTIONS_UI.md`. Aucun merge n’est autorisé implicitement.
