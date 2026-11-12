"""ReConnect Normandie — API M4 (contrat provisoire M2, données TEST)."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from shapely.geometry import box, shape

from services.contract import CONTRACT_VERSION, canonical_id
from services.store import BASE_DIR, Store, load_store
from services.internal_m2 import CAEN_NORD_SHA256, InternalM2Lot
import hmac


IDType = Literal["auto", "string", "integer"]


def _resolve_id(value: str, index: dict[str, dict], id_type: IDType = "auto") -> str:
    """Préserve les IDs JSON typés, même si l'URL n'a que des chaînes."""
    keys = [canonical_id(value)] if id_type in ("auto", "string") else []
    if id_type in ("auto", "integer"):
        try:
            if str(int(value)) == value:
                keys.append(canonical_id(int(value)))
        except ValueError:
            if id_type == "integer":
                raise HTTPException(status_code=422, detail="Identifiant entier attendu.")
    matches = [key for key in keys if key in index]
    if not matches:
        raise HTTPException(status_code=404, detail="Identifiant introuvable.")
    if len(matches) > 1:
        raise HTTPException(status_code=409, detail="Identifiant ambigu : préciser id_type=string ou id_type=integer.")
    return matches[0]


def _parse_bbox(value: str | None):
    if value is None:
        return None
    try:
        parts = [float(part) for part in value.split(",")]
    except ValueError:
        raise HTTPException(status_code=422, detail="bbox attendu : min_lon,min_lat,max_lon,max_lat.")
    if (len(parts) != 4 or any(not math.isfinite(x) for x in parts)
            or not (-180 <= parts[0] < parts[2] <= 180)
            or not (-90 <= parts[1] < parts[3] <= 90)):
        raise HTTPException(status_code=422, detail="bbox invalide : longitude/latitude WGS84, bornes croissantes.")
    return box(*parts)


def _collection_view(original: dict, features: list[dict], response: Response, offset: int, limit: int, total: int) -> dict:
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Offset"] = str(offset)
    response.headers["X-Limit"] = str(limit)
    # Le résumé du contrat concerne TOUJOURS le lot complet M2, pas la page.
    response.headers["X-Resume-Scope"] = "dataset-global"
    return {**original, "features": features[offset:offset + limit]}


def create_app(*, data_dir: Path | None = None, sources_file: Path | None = None,
               actions_file: Path | None = None, fiches_file: Path | None = None,
               real_gpkg_path: Path | None = None, internal_token: str | None = None,
               real_expected_sha256: str | None = None,
               real_expected_counts: dict[str, int] | None = None,
               real_expected_scope: dict[str, str] | None = None) -> FastAPI:
    dataset_path = data_dir or Path(os.getenv("RECONNECT_DATA_DIR", str(BASE_DIR / "data" / "demo")))
    source_path = sources_file if sources_file is not None else Path(os.getenv("RECONNECT_SOURCES_CSV", str(BASE_DIR / "data" / "inventaire_sources.csv")))
    actions_path = actions_file if actions_file is not None else Path(os.getenv("RECONNECT_ACTIONS_JSON", str(BASE_DIR / "data" / "catalogue_actions.json")))
    fiches_path = fiches_file if fiches_file is not None else Path(os.getenv("RECONNECT_FICHES_JSON", str(BASE_DIR / "data" / "fiches_zones.json")))
    store: Store = load_store(dataset_path, source_path, actions_path, fiches_path)
    # Démonstration publique strictement synthétique. Les données réelles, distinctes,
    # ne peuvent être chargées que sur activation explicite d'un accès interne local.
    real_file = real_gpkg_path or (Path(os.environ["RECONNECT_INTERNAL_GPKG"])
                                   if os.getenv("RECONNECT_INTERNAL_GPKG") else None)
    private_token = internal_token or os.getenv("RECONNECT_INTERNAL_TOKEN")
    if real_file is not None and (not private_token or len(private_token) < 20):
        raise RuntimeError("RECONNECT_INTERNAL_TOKEN (20 caractères minimum) requis pour le lot interne.")
    private_lot = (InternalM2Lot(real_file, expected_sha256=real_expected_sha256 or CAEN_NORD_SHA256,
                                expected_counts=real_expected_counts,
                                expected_scope=real_expected_scope)
                   if real_file is not None else None)

    api = FastAPI(
        title="ReConnect Normandie — API M4",
        version="0.1.0-demo",
        description=("API de prédiagnostic territorial. Contrat M2 provisoire "
                     "`m2-m4.proposal-1`. **Données synthétiques uniquement ; "
                     "priorité et actions non calculées.**"),
    )
    api.state.store = store
    default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
    origins = [v.strip() for v in os.getenv("RECONNECT_CORS_ORIGINS", default_origins).split(",") if v.strip()]
    api.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                       allow_methods=["GET"], allow_headers=["*"],
                       expose_headers=["X-Total-Count", "X-Limit", "X-Offset", "X-Resume-Scope"])

    @api.get("/", tags=["service"])
    def welcome():
        return {"projet": "ReConnect Normandie", "api": "/docs", "contrat": CONTRACT_VERSION,
                "avertissement": "Données synthétiques de démonstration ; aucune conclusion territoriale."}

    @api.get("/health", tags=["service"])
    def health():
        return {"status": "ok", "contract_version": store.mailles["contract_version"],
                "test_data": store.test_data, "statut_diffusion": store.mailles["statut_diffusion"],
                "dataset_version": store.provenance["dataset_version"],
                "grid_version": store.provenance["grid_version"],
                "method_version": store.provenance["method_version"],
                "run_id": store.provenance["run_id"],
                "mailles": len(store.maille_index),
                "evenements_distincts_observes": store.validation["evenements_distincts_observes"],
                "relations_spatiales": store.validation["relations_spatiales"],
                "priorites_calculees": False,
                "catalogue_actions_disponible": store.actions is not None,
                "fiches_zones_disponibles": store.fiches is not None}

    @api.get("/metadata", tags=["service"])
    def metadata():
        return {"contract_version": store.mailles["contract_version"],
                "test_data": store.test_data, "statut_diffusion": store.mailles["statut_diffusion"],
                "provenance": store.provenance, "resume_global": store.mailles["resume"],
                "avertissement": "Les croisements 2D ne prouvent pas des obstacles écologiques."}

    @api.get("/zones", tags=["mailles"])
    @api.get("/mailles", include_in_schema=False)
    @api.get("/zone", include_in_schema=False)
    def zones(response: Response, bbox: str | None = Query(default=None, description="min_lon,min_lat,max_lon,max_lat (CRS84)"),
              offset: int = Query(default=0, ge=0), limit: int = Query(default=500, ge=1, le=5000)):
        viewport = _parse_bbox(bbox)
        features = store.mailles["features"]
        if viewport is not None:
            features = [f for f in features if f["geometry"] is not None and shape(f["geometry"]).intersects(viewport)]
        return _collection_view(store.mailles, features, response, offset, limit, len(features))

    @api.get("/zones/{maille_id}", tags=["mailles"])
    @api.get("/mailles/{maille_id}", include_in_schema=False)
    def zone_detail(maille_id: str, id_type: IDType = "auto"):
        key = _resolve_id(maille_id, store.maille_index, id_type)
        feature = store.maille_index[key]
        props = feature["properties"]
        fiche = store.fiches.get(key) if store.fiches is not None else None
        return {
            **props, "geometry": feature["geometry"],
            "test_data": store.test_data, "contract_version": store.mailles["contract_version"],
            "provenance": store.provenance,
            "fiche_detaillee_disponible": fiche is not None,
            "fiche": fiche,  # `null` si M2 n'a pas livré fiches_zones.json
            "dimensions": fiche.get("dimensions") if fiche else None,
            "actions": fiche.get("actions") if fiche else None,
        }

    @api.get("/conflits", tags=["conflits"])
    def conflits(response: Response, maille_id: str | None = None, id_type: IDType = "auto",
                 offset: int = Query(default=0, ge=0), limit: int = Query(default=500, ge=1, le=5000)):
        features = store.conflits["features"]
        if maille_id is not None:
            key = _resolve_id(maille_id, store.maille_index, id_type)
            event_ids = {canonical_id(cid) for cid in store.maille_index[key]["properties"]["conflit_ids"]}
            features = [f for f in features if canonical_id(f["properties"]["conflit_id"]) in event_ids]
        return _collection_view(store.conflits, features, response, offset, limit, len(features))

    @api.get("/conflits/{conflit_id}", tags=["conflits"])
    def conflit_detail(conflit_id: str):
        key = _resolve_id(conflit_id, store.conflit_index, "string")
        # Ne jamais reconstruire la géométrie depuis les données internes.
        return store.conflit_index[key]

    @api.get("/zones/{maille_id}/conflits", tags=["conflits"])
    def conflits_de_zone(maille_id: str, response: Response, id_type: IDType = "auto",
                        offset: int = Query(default=0, ge=0), limit: int = Query(default=500, ge=1, le=5000)):
        key = _resolve_id(maille_id, store.maille_index, id_type)
        event_ids = {canonical_id(cid) for cid in store.maille_index[key]["properties"]["conflit_ids"]}
        features = [f for f in store.conflits["features"] if canonical_id(f["properties"]["conflit_id"]) in event_ids]
        return _collection_view(store.conflits, features, response, offset, limit, len(features))

    @api.get("/actions", tags=["actions"])
    def actions():
        if store.actions is None:
            return {"status": "en_attente_m5", "disponible": False, "count": 0,
                    "actions": [], "test_data": store.test_data,
                    "message": "Catalogue M5 non fourni ; aucune action inventée."}
        return {"status": "disponible", "disponible": True, "count": len(store.actions),
                "actions": list(store.actions.values()), "test_data": store.test_data}

    @api.get("/actions/{action_id}", tags=["actions"])
    def action_detail(action_id: str, id_type: IDType = "auto"):
        if store.actions is None:
            raise HTTPException(status_code=503, detail="Catalogue M5 non encore disponible.")
        key = _resolve_id(action_id, store.actions, id_type)
        return store.actions[key]

    @api.get("/etat-integration", tags=["service"])
    def etat_integration():
        """États documentés, jamais une promesse de résultat scientifique."""
        return {
            "m4": "api_demo_testee",
            "m2_geojson_public": "proposal-1_synthetique_uniquement",
            "m2_priorites_proposal_2": "proposition_non_validee",
            "m2_caen_nord_66": "charge_interne_uniquement" if private_lot else "lot_non_fourni",
            "m2_triage_101": "lot_non_fourni_non_diffusable",
            "m5_actions": "catalogue_present_non_valide" if store.actions else "catalogue_non_fourni",
            "m3_frontend": "adaptateur_frontend_non_valide_sur_la_nouvelle_API",
            "limites": ["Les couleurs du triage documentaire ne sont pas des priorités écologiques.",
                        "Le lot réel et le contrat public proposal-1 sont séparés."],
        }

    if private_lot is not None:
        def _require_internal(request: Request, x_internal_token: str | None = Header(default=None)):
            # Jamais d'accès distant direct, même avec le jeton.
            if (request.client is None or request.client.host not in ("127.0.0.1", "::1")
                    or not x_internal_token or not hmac.compare_digest(x_internal_token, private_token)):
                raise HTTPException(status_code=404, detail="Not Found")

        @api.middleware("http")
        async def private_cache_control(request: Request, call_next):
            response = await call_next(request)
            if request.url.path.startswith("/internal/"):
                response.headers["Cache-Control"] = "no-store, private"
                response.headers["X-Content-Type-Options"] = "nosniff"
            return response

        @api.get("/internal/m2/health", include_in_schema=False)
        def internal_health(request: Request, x_internal_token: str | None = Header(default=None)):
            _require_internal(request, x_internal_token)
            return {"status": "ready_internal_only", "territory": private_lot.scope,
                    "counts": private_lot.counts,
                    "geometries_publiees": False, "priorites_calculees": False,
                    "actions_calculees": False,
                    "avertissement": "Données internes non autorisées à la diffusion publique."}

        @api.get("/internal/m2/mailles", include_in_schema=False)
        def internal_cells(request: Request, x_internal_token: str | None = Header(default=None),
                           offset: int = Query(default=0, ge=0),
                           limit: int = Query(default=50, ge=1, le=500)):
            _require_internal(request, x_internal_token)
            ids = list(private_lot.cells)
            return {"total": len(ids), "offset": offset, "limit": limit,
                    "items": [private_lot.cell_detail(private_lot.cells[key]["maille_id"])
                              for key in ids[offset:offset + limit]]}

        @api.get("/internal/m2/mailles/{maille_id}", include_in_schema=False)
        def internal_cell(maille_id: str, request: Request,
                          x_internal_token: str | None = Header(default=None)):
            _require_internal(request, x_internal_token)
            result = private_lot.cell_detail(maille_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Maille absente de ce lot et de cette version.")
            return result

        @api.get("/internal/m2/mailles/{maille_id}/conflits", include_in_schema=False)
        def internal_cell_events(maille_id: str, request: Request,
                                 x_internal_token: str | None = Header(default=None),
                                 offset: int = Query(default=0, ge=0),
                                 limit: int = Query(default=100, ge=1, le=500)):
            _require_internal(request, x_internal_token)
            key = canonical_id(maille_id)
            if key not in private_lot.cells:
                raise HTTPException(status_code=404, detail="Maille absente.")
            conflicts = private_lot.links[key]
            return {"total": len(conflicts), "offset": offset, "limit": limit,
                    "items": [private_lot.events[c] | {"geometrie": None}
                              for c in conflicts[offset:offset + limit]]}

        @api.get("/internal/m2/conflits/{conflit_id}", include_in_schema=False)
        def internal_conflict(conflit_id: str, request: Request,
                              x_internal_token: str | None = Header(default=None)):
            _require_internal(request, x_internal_token)
            result = private_lot.event_detail(conflit_id)
            if result is None:
                raise HTTPException(status_code=404, detail="Événement absent.")
            return result

    @api.get("/sources", tags=["sources"])
    def sources(offset: int = Query(default=0, ge=0), limit: int = Query(default=500, ge=1, le=2000)):
        return {"count": len(store.sources), "offset": offset, "limit": limit,
                "sources": store.sources[offset:offset + limit],
                "avertissement": "Inventaire de candidats M1 ; les champs A VERIFIER et les statuts ne valent pas validation des licences ou diffusions."}

    return api


app = create_app()
