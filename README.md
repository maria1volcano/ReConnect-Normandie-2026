# ReConnect Normandie — Datathon 2026

Prédiagnostic territorial des continuités écologiques en Normandie.
Intégration finale des chantiers **M1** (données SIG), **M2** (diagnostics),
**M3** (frontend) et **M4** (backend).

## Architecture

| Brique | Branche | Contenu |
|---|---|---|
| M1 | `feat/m1-donnees-sig-v61` | Pipeline SIG reproductible, grille hexagonale pilote, mesures élémentaires, adoption de la grille 6 communes |
| M2 | `feat/diagnostics-ecologiques` | Méthode de croisement géométrique, schémas de contrat, triage documentaire V1–V4, suite de tests |
| M3 | `feat/m3-frontend-reconnect-v61` | Application React + TypeScript + Vite + MapLibre GL |
| M4 | `feat/backend-housin` | API FastAPI de contrat `m2-m4.proposal-1` (données synthétiques / lot interne dédié) |

Branche d'intégration : `integration/final-datathon`.

## Application M3 (frontend)

- **Mode REAL (unique interface publique)** : 101 cellules géographiques
  (`territory_id = caen_et_nord_6communes`,
  `grid_version = M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1`), couvrant Caen et cinq
  communes voisines, affichées avec la classification exploratoire
  documentaire M2 (V1 rouge ×27, V2 orange ×33, V3 jaune ×9, V4 gris ×32).
- **Ces couleurs sont un ordre de vérification documentaire exploratoire**,
  pas des priorités écologiques validées. Les priorités écologiques restent
  indéterminées.
- Clic sur une cellule : fiche territoriale M2 (observations géométriques,
  pistes d'investigation R1–R4 non évaluables, limites, provenance).
- Le mode TEST historique (43 mailles pilotes Orne, données synthétiques)
  est conservé dans le code et les données mais masqué de l'interface
  (`TEST_MODE_UI_ENABLED` dans `frontend/src/components/layout/ApplicationLayout.tsx`).

## Backend actif : `backend/server.py` (adaptateur local M4)

Le backend de démonstration actif est **`backend/server.py`**, un adaptateur
loopback-only qui sert le lot M2 interne certifié (SHA-256 épinglé,
`diffusion = interne_revue_uniquement`, `publication_autorisee = false`) :

```powershell
cd backend
$env:RECONNECT_M2_ZIP='C:\chemin\vers\RECONNECT_CAEN_ET_NORD_M2_DEMO_INTERNE_20261111_V1.zip'
$env:RECONNECT_FRONTEND_ORIGIN='http://127.0.0.1:5173'
py server.py   # http://127.0.0.1:8765
```

Endpoints : `/health`, `/api/internal/caen/metadata`,
`/api/internal/caen/grid`, `/api/internal/caen/cells/{maille_id}`.
Accès refusé hors loopback et hors origine frontend autorisée.

## Backend M4 contractuel : `backend/main.py` (FastAPI)

L'implémentation M4 d'origine (`main.py`, `services/`, `schemas/`,
`tests/`) est conservée pour le contrat `m2-m4.proposal-1`. Elle est conçue
pour les fixtures synthétiques et l'ancien lot interne 66 mailles
(`RECONNECT_INTERNAL_GPKG` + `RECONNECT_INTERNAL_TOKEN`, loopback-only,
géométries non publiées). **Elle n'est pas le backend de la démonstration
101 mailles** — voir `backend/README.md`.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest -q
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Frontend

```powershell
cd frontend
npm ci
npm run dev     # http://127.0.0.1:5173
```

Tests : `npm run typecheck`, `npm run test:priorities`, `npm run build`.

## Données et restrictions

- Le ZIP M2 final est **interne uniquement** : il n'est pas dans le dépôt et
  ne doit pas être publié. La carte REAL nécessite le backend local
  `server.py` + le ZIP autorisé (`RECONNECT_M2_ZIP`).
- `data/deliveries/` (GeoPackages, archives M1→M2) est ignoré par Git.
- Aucun `.env` peuplé n'est versionné ; voir `.env.example`.
- Limites scientifiques : croisements 2D ≠ obstacles confirmés ; zéro
  observation ≠ absence ; aucune priorité ni recommandation de travaux
  validée ; catalogue M5 absent.

Voir `docs/LOCAL_DEMO_RUNBOOK.md` pour le parcours de démonstration.
