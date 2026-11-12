# ReConnect Normandie — Backend M4 (FastAPI)

**État : démonstrateur d'intégration M2 → M4, données synthétiques exclusivement.**

Le contrat SIG actuellement fourni est **`m2-m4.proposal-1`**. Il **interdit de considérer les fixtures comme des données réelles** et ne contient **aucune priorité scientifique calculée** ni recommandation d'action. Le backend ne calcule ni score écologique, ni efficacité attendue, ni priorité de travaux.

## Démarrer dans WSL / Ubuntu

Depuis la **racine du dépôt**, si le dossier `backend/` contient ce package :

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pytest -q
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Documentation interactive : http://127.0.0.1:8000/docs

Vérifier la démo :

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/zones
curl http://127.0.0.1:8000/zones/H1
curl 'http://127.0.0.1:8000/conflits?maille_id=H1'
```

## API de démonstration

| Route | Contenu |
|---|---|
| `GET /health` | Disponibilité, version, provenance et comptages globaux sans doublons |
| `GET /metadata` | Enveloppe M2 et avertissement scientifique |
| `GET /zones?bbox=minlon,minlat,maxlon,maxlat&limit=500&offset=0` | FeatureCollection GeoJSON de mailles (filtrage exact d'intersection WGS84) |
| `GET /zones/{maille_id}` | Diagnostic d'une maille avec `null` explicites pour les éléments non fournis |
| `GET /conflits?maille_id=H1` | Événements uniques liés à une maille (géométries masquées conservées) |
| `GET /conflits/{conflit_id}` | Feature du conflit, sans reconstruction de géométrie |
| `GET /zones/{maille_id}/conflits` | Conflits de la maille |
| `GET /sources` | Inventaire candidat M1 et statuts de vérification |
| `GET /actions` | Tableau vide `en_attente_m5` tant que le catalogue n'est pas livré |
| `GET /actions/{action_id}` | Détail de catalogue, ou HTTP 503 si M5 absent |

Alias de compatibilité : `/zone` et `/mailles` pour la collection, `/mailles/{maille_id}` pour le détail. `GET /zones` retourne désormais les mailles du projet écologique, **plus** l'ancien tableau de pollution lumineuse. Ce tableau reste conservé dans `data/legacy_zones_TEST_non_diffuse.json` uniquement pour traçabilité, et n'est pas servi.

Les collections paginées conservent le `resume` du lot M2 **global** et exposent `X-Total-Count`, `X-Limit`, `X-Offset` et `X-Resume-Scope: dataset-global`. Ne pas additionner les comptages locaux ni interpréter `resume` comme le résumé d'une page.

### Identifiants typés

M2 peut fournir `maille_id` entier ou chaîne. Un identifiant entier `1` diffère de la chaîne `"1"`. Dans l'URL, ajouter `?id_type=integer` ou `?id_type=string` si les deux existent ; la résolution automatique renvoie 409 en cas d'ambiguïté.

### Jeux de données

- `data/demo/mailles.geojson` et `data/demo/conflits.geojson` : **fixtures SYNTHÉTIQUES M2**, non représentatives du territoire.
- `schemas/` : JSON Schemas exacts de M2 ; validation au démarrage de **l'ensemble du lot** (géométrie, types, versions, références croisées, comptages).
- `data/inventaire_sources.csv` : inventaire M1 de **sources candidates**. Conserver les mentions « A VERIFIER ».
- `data/catalogue_actions.json` et `data/fiches_zones.json` : **absents** dans les archives reçues. Routes et branchements préparés, sans invention de contenu.

Des variables d'environnement facultatives permettent de choisir les chemins des fichiers (`RECONNECT_DATA_DIR`, `RECONNECT_SOURCES_CSV`, `RECONNECT_ACTIONS_JSON`, `RECONNECT_FICHES_JSON`) et les origines autorisées (`RECONNECT_CORS_ORIGINS`, liste séparée par virgules). Le fichier `.env.example` documente ces valeurs mais n'est pas chargé automatiquement : exporter les variables dans le terminal avant le lancement.

Exemple :

```bash
export RECONNECT_DATA_DIR="$PWD/data/demo"
export RECONNECT_CORS_ORIGINS="http://localhost:5173,http://127.0.0.1:5173"
python -m uvicorn main:app --reload
```

**Publication réelle désactivée** : les schémas M2 imposent `test_data=true` et `statut_diffusion=synthetique_uniquement`. Pour des données réelles, M1/M2/M4 devront valider les droits, définir un contrat de production versionné, et adapter les contrôles avant toute mise en ligne. Ne jamais modifier simplement ces marqueurs pour forcer la diffusion.

## Tests

`python -m pytest -q` teste les routes, les paramètres invalides (HTTP 422), les références croisées, le comptage unique, le masquage des géométries, les origines CORS, l'absence de calculs inventés et le rejet d'un jeu de données invalides.

## Frontend M3

Le frontend fourni consomme **pour l'instant des fichiers statiques** (`frontend/public/data/mailles.geojson`, etc.) et un composant de détail provisoire. Un **projet d'adaptateur** est inclus à part dans `integration_M3/` dans l'archive livrée. Il fournit des requêtes vers cette API et une fiche de mailles TEST. **Ne pas écraser la branche M3 sans accord de son responsable.**

Pour démarrer localement les deux composants, ouvrir deux terminaux : serveur FastAPI (`backend`) et Vite (`frontend`, `npm ci` puis `npm run dev`). Le frontend doit utiliser l'adaptateur proposé ou son propre adaptateur API validé, avec `VITE_RECONNECT_API_URL=http://127.0.0.1:8000`.

## Limitations réelles

1. Aucun export territorial réel M2 n'a été transmis ; seuls les tests synthétiques sont validables.
2. Les schémas M2 actuels forcent `priorite_examen.valeur=null` et `action_ids=[]`. Une nouvelle version commune du contrat est nécessaire pour les règles R1–R4 et les priorités calculées.
3. Aucun `fiches_zones.json` ni `catalogue_actions.json` M5 livré ; leur format n'est donc pas stabilisé. Le backend accepte provisoirement une liste d'objets munis d'identifiants, mais l'intégration définitive nécessite revue de contrat.
4. Le pilote et la grille démo M3 ne sont pas géographiquement alignés sur les fixtures M2. L'adaptateur de démonstration zoome sur l'emprise réelle des fixtures et ne les fait pas passer pour un territoire pilote validé.
5. Le catalogue de sources M1 contient des informations documentaires à confirmer ; il n'autorise aucune diffusion de géométries sensibles.

Ce code est limité au périmètre backend M4. Aucun commit, merge ni push n'est réalisé dans les branches de l'équipe.
