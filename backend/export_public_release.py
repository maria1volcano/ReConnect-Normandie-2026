"""Exports minimisés sans modification des archives M2.

L'ancien export public garde son autorisation historique. Le nouveau lot
ACTIONS_ETUDE reste interne : --output hors des répertoires servis prépare une
candidature ; --authorization lié au SHA-256 exact est requis avant diffusion.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from server import GRID_VERSION, TERRITORY_ID, M2Store  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "frontend" / "public" / "data" / "caen-6com"
MANIFEST_PATH = ROOT / "docs" / "PUBLIC_RELEASE_MANIFEST.json"

# Champs conservés dans chaque source_observations pour l'export public :
# agrégats et statuts uniquement — jamais les listes d'objets sources bruts.
OBSERVATION_SAFE_KEYS = (
    "nombre_objets_observes",
    "mesure_observee",
    "unite",
    "disponibilite",
    "completude_ecologique_validee",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def sanitize_cell(bundle: dict) -> dict:
    bundle = copy.deepcopy(bundle)
    observations = bundle.get("geometric_observations", {}).get("source_observations", {})
    sanitized = {
        name: {key: value for key, value in record.items() if key in OBSERVATION_SAFE_KEYS}
        for name, record in observations.items()
    }
    bundle["geometric_observations"]["source_observations"] = sanitized
    return bundle


def main() -> None:
    parser = argparse.ArgumentParser(description="Export minimisé ; les décisions internes nécessitent une autorisation dédiée.")
    parser.add_argument("--output", type=Path, help="Dossier de candidature hors de frontend/public")
    parser.add_argument("--authorization", type=Path, help="Validation de diffusion liée au SHA-256 exact")
    args = parser.parse_args()
    zip_value = os.environ.get("RECONNECT_M2_ZIP")
    if not zip_value:
        raise SystemExit("RECONNECT_M2_ZIP doit pointer vers le ZIP M2 autorisé")
    zip_path = Path(zip_value).resolve()
    store = M2Store(zip_path)

    grid = store.minimal_grid()
    features = grid["features"]
    if len(features) != 101:
        raise SystemExit(f"Attendu 101 mailles, reçu {len(features)}")

    cells = {}
    for feature in features:
        maille_id = feature["properties"]["maille_id"]
        cells[maille_id] = sanitize_cell(store.cell(maille_id, TERRITORY_ID, GRID_VERSION))
    if len(cells) != 101:
        raise SystemExit(f"Attendu 101 fiches, reçu {len(cells)}")

    leads_total = sum(len(cell["investigations"]) for cell in cells.values())
    leads_a_etudier = sum(
        1 for cell in cells.values() for item in cell["investigations"] if item["lead_status"] == "a_etudier"
    )

    out_dir = (args.output or OUT_DIR).resolve()
    authorized = not store.actions_release
    authorization = None
    if store.actions_release:
        if args.authorization:
            authorization = json.loads(args.authorization.read_text())
            authorized = (authorization.get("publication_authorized") is True
                          and authorization.get("source_zip_sha256", "").lower() == store.source_sha256
                          and authorization.get("scope") == {"territory_id": TERRITORY_ID, "grid_version": GRID_VERSION}
                          and authorization.get("decision_version") == store.metadata()["decision_version"]
                          and bool(authorization.get("approved_by")) and bool(authorization.get("approved_at")))
            if not authorized:
                raise SystemExit("Autorisation incompatible avec ce lot : aucun export écrit")
        served_roots = [(ROOT / p).resolve() for p in ("frontend/public", "frontend/dist")]
        if not authorized and any(out_dir == p or p in out_dir.parents for p in served_roots):
            raise SystemExit("Publication bloquée : fournir une autorisation pour le SHA-256 exact, ou --output hors de frontend/public")
    out_dir.mkdir(parents=True, exist_ok=True)
    grid_path = out_dir / "grid.geojson"
    cells_path = out_dir / "cells.json"
    grid_path.write_text(json.dumps(grid, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    cells_path.write_text(json.dumps(cells, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    manifest = {
        "release": "reconnect-caen-actions-minimise-v1" if store.actions_release else "reconnect-caen-et-nord-public-v1",
        "publication_authorized": authorized,
        "decision_version": store.metadata()["decision_version"],
        "approval": authorization,
        "test_data": False,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "territory_id": TERRITORY_ID,
        "grid_version": GRID_VERSION,
        "source_zip_sha256": sha256_file(zip_path),
        "source_zip_name": zip_path.name,
        "authorization": (("Diffusion du complément d’actions validée par le document lié à cette empreinte." if authorized else "Diffusion du complément d’actions en attente de validation explicite.") if store.actions_release else (
            "Publication des données géographiques requises et des résultats dérivés "
            "du projet autorisée par l'équipe pour la démonstration Datathon. "
            "L'archive M2 source reste immuable (publication_autorisee=false en interne) ; "
            "seul cet export dérivé minimisé est publié."
        )),
        "counts": {
            "cells": len(features),
            "diagnostic_sheets": len(cells),
            "documentary_levels": store.metadata()["documentary_counts"],
            "investigation_leads_total": leads_total,
            "investigation_leads_a_etudier": leads_a_etudier,
            "events_admitted": store.metadata()["events_admitted"],
            "cell_event_relations": store.metadata()["cell_event_relations"],
            "cells_with_events": store.metadata()["cells_with_events"],
            "validated_recommendations": 0,
        },
        "exports": {
            "grid.geojson": {"sha256": sha256_file(grid_path), "description": "101 mailles + catégories documentaires"},
            "cells.json": {"sha256": sha256_file(cells_path), "description": "101 fiches territoriales minimisées"},
        },
        "study_actions": {"main_selections_by_cell": sum(bool(c.get("instruction", {}).get("main_action")) for c in cells.values()),
                          "validated_works": 0},
        "exclusions": [
            "Geometries of raw source-pair events (conflits.geojson)",
            "Per-object source attribute lists (objets IDs) inside observation aggregates",
            "Internal working files, GeoPackages, provenance archives",
            "Any validated ecological priority or restoration recommendation (none exist)",
        ],
        "scientific_limitations": [
            "Geometric 2D crossings are not confirmed ecological conflicts.",
            "Zero observed events does not demonstrate ecological absence.",
            "Study priorities are indicative and distinct from validated ecological D/S priorities." if store.actions_release else "Documentary V1-V4 colors are an exploratory verification order, not validated priorities.",
            "R1-R4 investigation leads are non-evaluable; no works are recommended.",
        ],
        "required_label": "Priorités d'étude des actions écologiques" if store.actions_release else "Indices cartographiques à vérifier — analyse exploratoire",
    }
    manifest_path = out_dir / "release-manifest.json" if args.output else MANIFEST_PATH
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))
    print(f"Export minimisé écrit dans {out_dir} — publication autorisée : {authorized}")


if __name__ == "__main__":
    main()
