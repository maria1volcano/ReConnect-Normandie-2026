"""Validate Step 5 elementary measurements and deterministic outputs."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

from calculate_m1_measurements import GRID_OUTPUT, OCS_OUTPUT, OUTPUT, RAW_SOURCES, REPORT, sha256


ROOT = Path(__file__).resolve().parents[1]
TOLERANCE_M2 = 0.1


def run_measurements() -> tuple[dict, bytes, bytes]:
    subprocess.run(
        [sys.executable, str(ROOT / "analysis/calculate_m1_measurements.py")],
        cwd=ROOT,
        check=True,
    )
    return (
        json.loads(REPORT.read_text(encoding="utf-8")),
        OUTPUT.read_bytes(),
        OCS_OUTPUT.read_bytes(),
    )


def main() -> None:
    raw_before = {source: sha256(path) for source, path in RAW_SOURCES.items()}
    first_report, first_main, first_ocs = run_measurements()
    second_report, second_main, second_ocs = run_measurements()
    assert first_main == second_main and first_ocs == second_ocs
    assert first_report["output_sha256"] == second_report["output_sha256"]

    grid = gpd.read_file(GRID_OUTPUT, layer="grille_pilote", engine="pyogrio")
    result = pd.read_csv(OUTPUT)
    categories = pd.read_csv(OCS_OUTPUT)

    assert len(result) == len(grid) == 43 and result["maille_id"].is_unique
    assert set(result["maille_id"]) == set(grid["maille_id"])
    assert result["grid_version"].eq(grid["grid_version"].iloc[0]).all()
    assert result["measurement_crs"].eq("EPSG:2154").all()

    measured = [column for column in result if column.endswith(("_m", "_m2", "_count"))]
    unavailable = {"pram_pond_count", "epfn_site_count"}
    for column in measured:
        if column in unavailable:
            assert result[column].isna().all(), column
        else:
            assert result[column].notna().all() and result[column].ge(0).all(), column

    assert result["ocs_covered_area_m2"].le(result["cell_area_m2"] + TOLERANCE_M2).all()
    assert result["constructed_area_m2"].le(result["cell_area_m2"] + TOLERANCE_M2).all()
    assert categories["ocs_area_m2"].ge(0).all()
    category_totals = categories.groupby("maille_id")["ocs_area_m2"].sum()
    coverage = result.set_index("maille_id")["ocs_covered_area_m2"]
    assert (category_totals - coverage.reindex(category_totals.index)).abs().max() < TOLERANCE_M2

    assert result["p0_coverage_status"].eq("complete_for_provisional_pilot").all()
    assert result["wetland_coverage_status"].eq("available_bounded_wfs_heterogeneous_inventory").all()
    assert result["source_ids"].str.contains("OCSGE").all()
    assert result["hedge_length_m"].eq(0).any(), "Expected genuine zero hedge measurements"
    assert raw_before == {source: sha256(path) for source, path in RAW_SOURCES.items()}

    print("PASS: genuine sources, grid IDs, EPSG:2154 metrics, nonnegative values, overlap rules, NULL-vs-zero, provenance, determinism, raw hashes")


if __name__ == "__main__":
    main()
