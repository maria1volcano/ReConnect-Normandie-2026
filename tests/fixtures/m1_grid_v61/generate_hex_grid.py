"""Generate the deterministic candidate hexagonal grid for the provisional M1 pilot."""

from __future__ import annotations

import hashlib
import json
import math
import platform
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
from pyproj import Transformer
from shapely import normalize, to_wkb, transform as shapely_transform, union_all
from shapely.geometry import Polygon, box


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUTPUT = PROCESSED / "grille_pilote.gpkg"
REPORT = PROCESSED / "m1_grid_report.json"

PILOT_BBOX_WGS84 = (-0.28, 49.20, -0.22, 49.26)
TARGET_CRS = "EPSG:2154"
TARGET_AREA_M2 = 1_000_000.0
SIDE_M = math.sqrt(2.0 * TARGET_AREA_M2 / (3.0 * math.sqrt(3.0)))
ORIENTATION = "flat_top"
ORIGIN_X = 0.0
ORIGIN_Y = 0.0
X_SPACING_M = 1.5 * SIDE_M
Y_SPACING_M = math.sqrt(3.0) * SIDE_M
GRID_VERSION = "M1-CAND-1KM2-FLAT-L93-O0-V1"
AREA_TOLERANCE_M2 = 1e-4


def pilot_geometry():
    transformer = Transformer.from_crs("EPSG:4326", TARGET_CRS, always_xy=True)
    return shapely_transform(
        box(*PILOT_BBOX_WGS84), transformer.transform, interleaved=False
    )


def regular_hexagon(center_x: float, center_y: float) -> Polygon:
    vertices = [
        (
            center_x + SIDE_M * math.cos(math.radians(60 * vertex)),
            center_y + SIDE_M * math.sin(math.radians(60 * vertex)),
        )
        for vertex in range(6)
    ]
    return Polygon(vertices)


def cell_id(row: int, column: int) -> str:
    return f"NORM-G1K-FLAT-R{row:+07d}-C{column:+07d}"


def semantic_digest(frame: gpd.GeoDataFrame) -> str:
    digest = hashlib.sha256()
    attributes = sorted(column for column in frame.columns if column != "geometry")
    for _, row in frame.sort_values("maille_id", kind="stable").iterrows():
        values = {
            column: None if pd.isna(row[column]) else str(row[column])
            for column in attributes
        }
        digest.update(json.dumps(values, sort_keys=True).encode("utf-8"))
        digest.update(to_wkb(normalize(row.geometry), hex=False, include_srid=False))
    return digest.hexdigest().upper()


def generate_grid() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, object]:
    pilot = pilot_geometry()
    min_x, min_y, max_x, max_y = pilot.bounds

    minimum_column = math.floor((min_x - SIDE_M - ORIGIN_X) / X_SPACING_M) - 1
    maximum_column = math.ceil((max_x + SIDE_M - ORIGIN_X) / X_SPACING_M) + 1

    records = []
    for column in range(minimum_column, maximum_column + 1):
        center_x = ORIGIN_X + column * X_SPACING_M
        column_offset = 0.5 if column % 2 else 0.0
        minimum_row = math.floor(
            (min_y - math.sqrt(3.0) * SIDE_M / 2.0 - ORIGIN_Y) / Y_SPACING_M
            - column_offset
        ) - 1
        maximum_row = math.ceil(
            (max_y + math.sqrt(3.0) * SIDE_M / 2.0 - ORIGIN_Y) / Y_SPACING_M
            - column_offset
        ) + 1
        for row in range(minimum_row, maximum_row + 1):
            center_y = ORIGIN_Y + (row + column_offset) * Y_SPACING_M
            full_geometry = regular_hexagon(center_x, center_y)
            clipped_geometry = full_geometry.intersection(pilot)
            if clipped_geometry.is_empty or clipped_geometry.area <= AREA_TOLERANCE_M2:
                continue
            clipped_area = float(clipped_geometry.area)
            full_area = float(full_geometry.area)
            records.append(
                {
                    "maille_id": cell_id(row, column),
                    "grid_version": GRID_VERSION,
                    "grid_row": row,
                    "grid_col": column,
                    "center_x": center_x,
                    "center_y": center_y,
                    "full_area_m2": full_area,
                    "clipped_area_m2": clipped_area,
                    "area_m2": clipped_area,
                    "pilot_fraction": clipped_area / full_area,
                    "is_boundary": not full_geometry.within(pilot),
                    "full_geometry": full_geometry,
                    "geometry": clipped_geometry,
                }
            )

    records.sort(key=lambda item: (item["grid_row"], item["grid_col"]))
    clipped = gpd.GeoDataFrame(records, geometry="geometry", crs=TARGET_CRS)
    full = gpd.GeoDataFrame(
        clipped.drop(columns="geometry").rename(columns={"full_geometry": "geometry"}),
        geometry="geometry",
        crs=TARGET_CRS,
    )
    clipped = clipped.drop(columns="full_geometry")
    return clipped, full, pilot


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    clipped, full, pilot = generate_grid()

    if OUTPUT.exists():
        OUTPUT.unlink()
    clipped.to_file(OUTPUT, layer="grille_pilote", driver="GPKG", engine="pyogrio", index=False)
    full.to_file(
        OUTPUT,
        layer="hexagones_complets",
        driver="GPKG",
        engine="pyogrio",
        index=False,
        mode="a",
    )

    reopened = gpd.read_file(OUTPUT, layer="grille_pilote", engine="pyogrio")
    reopened_full = gpd.read_file(OUTPUT, layer="hexagones_complets", engine="pyogrio")
    coverage = union_all(reopened.geometry.array)
    missing_area = float(pilot.difference(coverage).area)
    excess_area = float(coverage.difference(pilot).area)

    report = {
        "status": "candidate_awaiting_m2_validation",
        "grid_version": GRID_VERSION,
        "target_crs": TARGET_CRS,
        "pilot_bbox_wgs84": PILOT_BBOX_WGS84,
        "pilot_area_m2": float(pilot.area),
        "target_hexagon_area_m2": TARGET_AREA_M2,
        "calculated_side_m": SIDE_M,
        "orientation": ORIENTATION,
        "origin_m": [ORIGIN_X, ORIGIN_Y],
        "spacing_m": [X_SPACING_M, Y_SPACING_M],
        "cell_count": int(len(reopened)),
        "interior_cell_count": int((~reopened["is_boundary"]).sum()),
        "boundary_cell_count": int(reopened["is_boundary"].sum()),
        "clipped_area_sum_m2": float(reopened["area_m2"].sum()),
        "minimum_clipped_area_m2": float(reopened["area_m2"].min()),
        "maximum_clipped_area_m2": float(reopened["area_m2"].max()),
        "missing_coverage_area_m2": missing_area,
        "excess_coverage_area_m2": excess_area,
        "all_clipped_valid": bool(reopened.geometry.is_valid.all()),
        "all_full_valid": bool(reopened_full.geometry.is_valid.all()),
        "duplicate_ids": int(reopened["maille_id"].duplicated().sum()),
        "clipped_semantic_sha256": semantic_digest(reopened),
        "full_semantic_sha256": semantic_digest(reopened_full),
        "libraries": {
            "python": platform.python_version(),
            "geopandas": gpd.__version__,
            "shapely": shapely.__version__,
        },
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("cell_count", "interior_cell_count", "boundary_cell_count")}))


if __name__ == "__main__":
    main()
