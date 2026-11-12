"""Export public statique du lot M2 Caen-et-Nord (autorisation de publication
équipe obtenue pour la démonstration Datathon).

L'archive M2 source n'est jamais modifiée : ce script produit uniquement des
exports dérivés minimisés dans ``frontend/public/data/caen-6com/`` et un
manifeste de release dans ``docs/``.

Usage :
    RECONNECT_M2_ZIP=<chemin du ZIP M2> py export_public_release.py
"""

from __future__ import annotations

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
    observations = bundle.get("geometric_observations", {}).get("source_observations", {})
    sanitized = {
        name: {key: value for key, value in record.items() if key in OBSERVATION_SAFE_KEYS}
        for name, record in observations.items()
    }
    bundle["geometric_observations"]["source_observations"] = sanitized
    return bundle


def main() -> None:
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

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grid_path = OUT_DIR / "grid.geojson"
    cells_path = OUT_DIR / "cells.json"
    grid_path.write_text(json.dumps(grid, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    cells_path.write_text(json.dumps(cells, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    manifest = {
        "release": "reconnect-caen-et-nord-public-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "territory_id": TERRITORY_ID,
        "grid_version": GRID_VERSION,
        "source_zip_sha256": sha256_file(zip_path),
        "source_zip_name": zip_path.name,
        "authorization": (
            "Publication des données géographiques requises et des résultats dérivés "
            "du projet autorisée par l'équipe pour la démonstration Datathon. "
            "L'archive M2 source reste immuable (publication_autorisee=false en interne) ; "
            "seul cet export dérivé minimisé est publié."
        ),
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
        "exclusions": [
            "Geometries of raw source-pair events (conflits.geojson)",
            "Per-object source attribute lists (objets IDs) inside observation aggregates",
            "Internal working files, GeoPackages, provenance archives",
            "Any validated ecological priority or restoration recommendation (none exist)",
        ],
        "scientific_limitations": [
            "Geometric 2D crossings are not confirmed ecological conflicts.",
            "Zero observed events does not demonstrate ecological absence.",
            "Documentary V1-V4 colors are an exploratory verification order, not validated priorities.",
            "R1-R4 investigation leads are non-evaluable; no works are recommended.",
        ],
        "required_label": "Indices cartographiques à vérifier — analyse exploratoire",
    }
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))
    print(f"Export écrit dans {OUT_DIR} — manifeste : {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
