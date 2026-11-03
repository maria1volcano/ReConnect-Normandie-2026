"""End-to-end validation of the deterministic M1 candidate grid."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
from shapely import union_all

from generate_hex_grid import (
    AREA_TOLERANCE_M2,
    GRID_VERSION,
    OUTPUT,
    REPORT,
    TARGET_AREA_M2,
    pilot_geometry,
)


ROOT = Path(__file__).resolve().parents[1]


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def raw_hashes() -> dict[str, str]:
    paths = {
        "reservoirs": ROOT / "data/raw/tvb_srce_normandie/reservoirs_srce_normandie_source.zip",
        "corridors": ROOT / "data/raw/tvb_srce_normandie/corridors_basse_normandie/corridors_srce_basse_normandie_source.zip",
        "roads": ROOT / "data/raw/bdtopo_routes/routes_orne_estuaire_bbox.geojson",
        "ocsge": ROOT / "data/raw/ocsge_d014_2023/OCS-GE_2-0__GPKG_LAMB93_D014_2023-01-01.7z",
    }
    return {name: file_hash(path) for name, path in paths.items()}


def run_generator() -> dict:
    subprocess.run([sys.executable, str(ROOT / "analysis/generate_hex_grid.py")], cwd=ROOT, check=True)
    return json.loads(REPORT.read_text(encoding="utf-8"))


def main() -> None:
    source_hashes = raw_hashes()
    first = run_generator()
    first_hashes = (first["clipped_semantic_sha256"], first["full_semantic_sha256"])
    second = run_generator()
    second_hashes = (second["clipped_semantic_sha256"], second["full_semantic_sha256"])
    assert first_hashes == second_hashes, "Grid output changed on deterministic rerun"

    clipped = gpd.read_file(OUTPUT, layer="grille_pilote", engine="pyogrio")
    full = gpd.read_file(OUTPUT, layer="hexagones_complets", engine="pyogrio")
    pilot = pilot_geometry()

    assert OUTPUT.exists() and OUTPUT.stat().st_size > 0
    assert clipped.crs.to_epsg() == 2154 and full.crs.to_epsg() == 2154
    assert clipped["maille_id"].notna().all() and clipped["maille_id"].is_unique
    assert clipped["grid_version"].eq(GRID_VERSION).all()
    assert clipped.geometry.notna().all() and (~clipped.geometry.is_empty).all()
    assert clipped.geometry.is_valid.all() and full.geometry.is_valid.all()
    assert clipped.geometry.intersects(pilot).all()
    assert (clipped["area_m2"] - clipped.geometry.area).abs().max() < AREA_TOLERANCE_M2
    assert (clipped["clipped_area_m2"] - clipped["area_m2"]).abs().max() < AREA_TOLERANCE_M2
    assert (full["full_area_m2"] - TARGET_AREA_M2).abs().max() < AREA_TOLERANCE_M2
    assert set(clipped.loc[~clipped["is_boundary"], "area_m2"].round(4)) == {TARGET_AREA_M2}
    assert clipped.loc[clipped["is_boundary"], "area_m2"].lt(TARGET_AREA_M2).all()

    coverage = union_all(clipped.geometry.array)
    assert pilot.difference(coverage).area < AREA_TOLERANCE_M2
    assert coverage.difference(pilot).area < AREA_TOLERANCE_M2
    assert raw_hashes() == source_hashes, "A raw source changed during grid generation"

    print("PASS: reopen, CRS, IDs, geometry, areas, pilot coverage, determinism, raw hashes")


if __name__ == "__main__":
    main()
