"""End-to-end Step 3 checks using the real local data."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import geopandas as gpd


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "analysis" / "prepare_m1.py"
REPORT = ROOT / "data" / "processed" / "m1_processing_report.json"

EXPECTED = {
    "reservoirs": ("reservoirs.gpkg", "reservoirs", "objet_id"),
    "corridors": ("corridors.gpkg", "corridors", "objet_id"),
    "routes": ("routes.gpkg", "routes", "route_id"),
    "sols": ("sols.gpkg", "sols", "sol_id"),
    "zones_construites": ("zones_construites.gpkg", "zones_construites", "zone_id"),
}


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def run_pipeline() -> dict:
    subprocess.run([sys.executable, str(PIPELINE)], cwd=ROOT, check=True)
    return json.loads(REPORT.read_text(encoding="utf-8"))


def main() -> None:
    first = run_pipeline()
    first_digests = {name: value["semantic_sha256"] for name, value in first["layers"].items()}
    raw_hashes = first["raw_sha256_before_and_after"]

    second = run_pipeline()
    second_digests = {name: value["semantic_sha256"] for name, value in second["layers"].items()}
    assert first_digests == second_digests, "Semantic outputs differ after a second run"
    assert raw_hashes == second["raw_sha256_before_and_after"], "Raw hashes differ between runs"

    for name, (filename, layer, id_column) in EXPECTED.items():
        path = ROOT / "data" / "processed" / filename
        assert path.exists() and path.stat().st_size > 0, f"Missing output {path}"
        frame = gpd.read_file(path, layer=layer, engine="pyogrio")
        expected_count = second["layers"][name]["output_features"]
        assert len(frame) == expected_count and expected_count > 0
        assert frame.crs.to_epsg() == 2154
        assert frame.geometry.notna().all() and frame.geometry.is_valid.all()
        assert id_column in frame.columns and frame[id_column].notna().all()
        assert not frame[id_column].duplicated().any()

    for key, expected_hash in raw_hashes.items():
        source_paths = {
            "reservoir_archive": ROOT / "data/raw/tvb_srce_normandie/reservoirs_srce_normandie_source.zip",
            "corridor_archive": ROOT / "data/raw/tvb_srce_normandie/corridors_basse_normandie/corridors_srce_basse_normandie_source.zip",
            "roads_geojson": ROOT / "data/raw/bdtopo_routes/routes_orne_estuaire_bbox.geojson",
            "ocsge_archive": ROOT / "data/raw/ocsge_d014_2023/OCS-GE_2-0__GPKG_LAMB93_D014_2023-01-01.7z",
        }
        assert file_hash(source_paths[key]) == expected_hash

    print("PASS: real-data pipeline, reopen, CRS, validity, IDs, determinism, raw hashes")


if __name__ == "__main__":
    main()
