"""Validate M3 GeoJSON exports."""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "data/public"
PROCESSED = ROOT / "data/processed"


def main() -> None:
    # Verify grid export
    grid_geojson = PUBLIC / "grille_pilote_wgs84.geojson"
    assert grid_geojson.exists(), f"Grid GeoJSON not found: {grid_geojson}"

    # Load and validate GeoJSON structure
    with grid_geojson.open("r", encoding="utf-8") as f:
        geojson_data = json.load(f)

    assert geojson_data["type"] == "FeatureCollection", "Not a FeatureCollection"
    assert len(geojson_data["features"]) == 43, f"Expected 43 features, got {len(geojson_data['features'])}"

    # Load with GeoPandas to verify CRS and geometry
    grid_gdf = gpd.read_file(grid_geojson, engine="pyogrio")
    assert grid_gdf.crs == "EPSG:4326", f"Expected EPSG:4326, got {grid_gdf.crs}"
    assert grid_gdf.geometry.is_valid.all(), "Invalid geometries found"
    assert grid_gdf.geometry.notna().all(), "Null geometries found"

    # Verify maille_id consistency with original grid
    original_grid = gpd.read_file(PROCESSED / "grille_pilote.gpkg", layer="grille_pilote", engine="pyogrio")
    assert set(grid_gdf["maille_id"]) == set(original_grid["maille_id"]), "maille_id mismatch"
    assert grid_gdf["grid_version"].eq(original_grid["grid_version"].iloc[0]).all(), "grid_version mismatch"

    print("PASS: M3 GeoJSON export validated (FeatureCollection, 43 features, EPSG:4326, valid geometries, consistent IDs)")


if __name__ == "__main__":
    main()
