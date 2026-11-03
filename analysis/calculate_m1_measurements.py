"""Calculate elementary geographic measurements for M2 without interpretation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import make_valid, union_all

from generate_hex_grid import GRID_VERSION, OUTPUT as GRID_OUTPUT, TARGET_CRS


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
OUTPUT = PROCESSED / "sub_indicateurs.csv"
OCS_OUTPUT = PROCESSED / "sub_indicateurs_ocs.csv"
REPORT = PROCESSED / "m1_measurements_report.json"
TOLERANCE_M2 = 0.01


RAW_SOURCES = {
    "TVB_RES_NORM": ROOT / "data/raw/tvb_srce_normandie/reservoirs_srce_normandie_source.zip",
    "TVB_COR_BN": ROOT / "data/raw/tvb_srce_normandie/corridors_basse_normandie/corridors_srce_basse_normandie_source.zip",
    "BDTOPO_ROUTES": ROOT / "data/raw/bdtopo_routes/routes_orne_estuaire_bbox.geojson",
    "OCSGE": ROOT / "data/raw/ocsge_d014_2023/OCS-GE_2-0__GPKG_LAMB93_D014_2023-01-01.7z",
    "BDHAIE": ROOT / "data/raw/bdhaie_pilot/haies_pilot.geojson",
    "SIPAF": ROOT / "data/raw/sipaf/Tous_les_PAF.gpkg",
    "CARTOFRICHES": ROOT / "data/raw/cartofriches/friches-surfaces.gpkg",
    "ZH_DREAL_NORM": ROOT / "data/raw/zones_humides/zones_humides_pilot.gml",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_layer(path: Path, layer: str) -> gpd.GeoDataFrame:
    frame = gpd.read_file(path, layer=layer, engine="pyogrio")
    if frame.crs is None:
        raise RuntimeError(f"Missing CRS: {path}:{layer}")
    frame = frame.to_crs(TARGET_CRS)
    invalid = ~frame.geometry.is_valid
    if invalid.any():
        frame.loc[invalid, "geometry"] = frame.loc[invalid, "geometry"].map(make_valid)
    return frame.loc[frame.geometry.notna() & ~frame.geometry.is_empty].copy()


def spatial_subset(frame: gpd.GeoDataFrame, cell_geometry) -> gpd.GeoDataFrame:
    positions = frame.sindex.query(cell_geometry, predicate="intersects")
    return frame.iloc[positions]


def union_measure(frame: gpd.GeoDataFrame, cell_geometry, measure: str) -> float:
    candidates = spatial_subset(frame, cell_geometry)
    if candidates.empty:
        return 0.0
    intersections = [geometry.intersection(cell_geometry) for geometry in candidates.geometry]
    merged = union_all([geometry for geometry in intersections if not geometry.is_empty])
    return float(getattr(merged, measure)) if not merged.is_empty else 0.0


def object_count(frame: gpd.GeoDataFrame, cell_geometry, identifier: str) -> int:
    candidates = spatial_subset(frame, cell_geometry)
    return int(candidates.loc[candidates.geometry.intersects(cell_geometry), identifier].nunique())


def load_complementary(grid: gpd.GeoDataFrame) -> dict[str, gpd.GeoDataFrame]:
    pilot = union_all(grid.geometry.array)

    hedges = gpd.read_file(RAW_SOURCES["BDHAIE"], engine="pyogrio").to_crs(TARGET_CRS)
    hedges = hedges.loc[hedges.geometry.intersects(pilot)].copy()

    sipaf = gpd.read_file(RAW_SOURCES["SIPAF"], layer="Tous_les_PAF", engine="pyogrio")
    sipaf = sipaf.to_crs(TARGET_CRS)
    sipaf = sipaf.loc[sipaf.geometry.notna() & sipaf.geometry.intersects(pilot)].copy()

    friches = gpd.read_file(
        RAW_SOURCES["CARTOFRICHES"],
        layer="friches_surfaces",
        bbox=(-0.28, 49.20, -0.22, 49.26),
        engine="pyogrio",
    ).to_crs(TARGET_CRS)
    friches = friches.loc[friches.geometry.intersects(pilot)].copy()

    wetlands = gpd.read_file(RAW_SOURCES["ZH_DREAL_NORM"], engine="pyogrio").to_crs(TARGET_CRS)
    wetlands = wetlands.loc[wetlands.geometry.intersects(pilot)].copy()

    for frame in (hedges, sipaf, friches, wetlands):
        invalid = ~frame.geometry.is_valid
        if invalid.any():
            frame.loc[invalid, "geometry"] = frame.loc[invalid, "geometry"].map(make_valid)
    return {"hedges": hedges, "sipaf": sipaf, "friches": friches, "wetlands": wetlands}


def main() -> None:
    raw_before = {source: sha256(path) for source, path in RAW_SOURCES.items()}
    grid = read_layer(GRID_OUTPUT, "grille_pilote").sort_values("maille_id", kind="stable")
    if not grid["grid_version"].eq(GRID_VERSION).all():
        raise RuntimeError("Unexpected grid version")

    reservoirs = read_layer(PROCESSED / "reservoirs.gpkg", "reservoirs")
    corridors = read_layer(PROCESSED / "corridors.gpkg", "corridors")
    roads = read_layer(PROCESSED / "routes.gpkg", "routes")
    soils = read_layer(PROCESSED / "sols.gpkg", "sols")
    constructed = read_layer(PROCESSED / "zones_construites.gpkg", "zones_construites")
    complementary = load_complementary(grid)

    rows: list[dict] = []
    category_rows: list[dict] = []
    for cell in grid.itertuples(index=False):
        geometry = cell.geometry
        cell_area = float(geometry.area)
        soil_candidates = spatial_subset(soils, geometry)
        soil_coverage = union_measure(soils, geometry, "area")

        for code in sorted(soil_candidates["couverture"].dropna().astype(str).unique()):
            category = soil_candidates.loc[soil_candidates["couverture"].astype(str).eq(code)]
            category_area = union_measure(category, geometry, "area")
            if category_area > TOLERANCE_M2:
                category_rows.append(
                    {
                        "maille_id": cell.maille_id,
                        "grid_version": cell.grid_version,
                        "ocs_code_cs": code,
                        "ocs_area_m2": category_area,
                        "ocs_fraction_of_cell": category_area / cell_area,
                        "area_unit": "m2",
                        "source_id": "OCSGE",
                        "source_year": "2023",
                    }
                )

        rows.append(
            {
                "maille_id": cell.maille_id,
                "grid_version": cell.grid_version,
                "cell_area_m2": cell_area,
                "is_boundary": bool(cell.is_boundary),
                "road_length_m": union_measure(roads, geometry, "length"),
                "road_object_count": object_count(roads, geometry, "route_id"),
                "reservoir_area_m2": union_measure(reservoirs, geometry, "area"),
                "reservoir_object_count": object_count(reservoirs, geometry, "objet_id"),
                "corridor_area_m2": union_measure(corridors, geometry, "area"),
                "corridor_object_count": object_count(corridors, geometry, "objet_id"),
                "ocs_covered_area_m2": soil_coverage,
                "ocs_coverage_fraction": soil_coverage / cell_area,
                "constructed_area_m2": union_measure(constructed, geometry, "area"),
                "hedge_length_m": union_measure(complementary["hedges"], geometry, "length"),
                "hedge_object_count": object_count(complementary["hedges"], geometry, "cleabs"),
                "sipaf_record_count": object_count(complementary["sipaf"], geometry, "Identifiant UUID"),
                "cartofriches_area_m2": union_measure(complementary["friches"], geometry, "area"),
                "cartofriches_site_count": object_count(complementary["friches"], geometry, "site_id"),
                "wetland_area_m2": union_measure(complementary["wetlands"], geometry, "area"),
                "wetland_record_count": object_count(complementary["wetlands"], geometry, "pk_zh"),
                "pram_pond_count": pd.NA,
                "epfn_site_count": pd.NA,
                "length_unit": "m",
                "area_unit": "m2",
                "measurement_crs": TARGET_CRS,
                "p0_coverage_status": "complete_for_provisional_pilot",
                "bdhaie_coverage_status": "available_bounded_wfs_non_exhaustive",
                "sipaf_coverage_status": "available_inventory_non_exhaustive",
                "cartofriches_coverage_status": "available_inventory_non_exhaustive",
                "wetland_coverage_status": "available_bounded_wfs_heterogeneous_inventory",
                "pram_coverage_status": "unavailable_authorized_extract_required",
                "epfn_coverage_status": "unavailable_licence_and_resource_unconfirmed",
                "source_ids": "BDTOPO_ROUTES;TVB_RES_NORM;TVB_COR_BN;OCSGE;BDHAIE;SIPAF;CARTOFRICHES;ZH_DREAL_NORM",
            }
        )

    result = pd.DataFrame(rows).sort_values("maille_id", kind="stable")
    categories = pd.DataFrame(category_rows).sort_values(
        ["maille_id", "ocs_code_cs"], kind="stable"
    )
    result.to_csv(OUTPUT, index=False, encoding="utf-8", float_format="%.6f", lineterminator="\n")
    categories.to_csv(
        OCS_OUTPUT, index=False, encoding="utf-8", float_format="%.6f", lineterminator="\n"
    )

    raw_after = {source: sha256(path) for source, path in RAW_SOURCES.items()}
    if raw_before != raw_after:
        raise RuntimeError("A raw source changed during measurement")
    report = {
        "status": "elementary_measurements_only_awaiting_m2_interpretation",
        "grid_version": GRID_VERSION,
        "measurement_crs": TARGET_CRS,
        "grid_row_count": int(len(result)),
        "ocs_category_row_count": int(len(categories)),
        "source_feature_counts_in_pilot": {
            "reservoirs": int(len(reservoirs)),
            "corridors": int(len(corridors)),
            "roads": int(len(roads)),
            "soils": int(len(soils)),
            "constructed_zones": int(len(constructed)),
            "hedges": int(len(complementary["hedges"])),
            "sipaf": int(len(complementary["sipaf"])),
            "cartofriches": int(len(complementary["friches"])),
            "wetlands": int(len(complementary["wetlands"])),
        },
        "raw_sha256_before_and_after": raw_after,
        "output_sha256": {
            "sub_indicateurs.csv": sha256(OUTPUT),
            "sub_indicateurs_ocs.csv": sha256(OCS_OUTPUT),
        },
        "missing_value_rule": "Unavailable source measurements are NULL; zero is used only for no intersecting records in a source covering the pilot.",
        "overlap_rule": "Lengths and areas use unary union of within-cell intersections; overlapping geometries are counted once per measurement/source.",
    }
    REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(result), "ocs_rows": len(categories), **report["source_feature_counts_in_pilot"]}))


if __name__ == "__main__":
    main()
