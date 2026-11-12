"""Export M1 grid and sources to WGS84 GeoJSON for M3 frontend display."""

from __future__ import annotations

from pathlib import Path

import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data/processed"
PUBLIC = ROOT / "data/public"
PUBLIC.mkdir(exist_ok=True)

TARGET_CRS = "EPSG:4326"


def export_to_geojson(gdf: gpd.GeoDataFrame, output_path: Path, target_crs: str = TARGET_CRS) -> None:
    """Export GeoDataFrame to GeoJSON in specified CRS."""
    if gdf.crs is None:
        raise RuntimeError(f"Missing CRS in input GeoDataFrame")
    if gdf.crs != target_crs:
        gdf = gdf.to_crs(target_crs)
    gdf.to_file(output_path, driver="GeoJSON", engine="pyogrio")
    print(f"Exported {len(gdf)} features to {output_path}")


def main() -> None:
    # Export grid for M3 display
    grid = gpd.read_file(PROCESSED / "grille_pilote.gpkg", layer="grille_pilote", engine="pyogrio")
    export_to_geojson(grid, PUBLIC / "grille_pilote_wgs84.geojson")

    # Optionally export key source layers for visual inspection
    # Uncomment if M3 needs these for display
    # reservoirs = gpd.read_file(PROCESSED / "reservoirs.gpkg", layer="reservoirs", engine="pyogrio")
    # export_to_geojson(reservoirs, PUBLIC / "reservoirs_wgs84.geojson")
    #
    # corridors = gpd.read_file(PROCESSED / "corridors.gpkg", layer="corridors", engine="pyogrio")
    # export_to_geojson(corridors, PUBLIC / "corridors_wgs84.geojson")
    #
    # routes = gpd.read_file(PROCESSED / "routes.gpkg", layer="routes", engine="pyogrio")
    # export_to_geojson(routes, PUBLIC / "routes_wgs84.geojson")

    print("M3 data export complete")


if __name__ == "__main__":
    main()
