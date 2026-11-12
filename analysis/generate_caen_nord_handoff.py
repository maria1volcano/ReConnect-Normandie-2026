"""Build the first internal M1 -> M2 handoff for the five Caen-nord municipalities."""

from __future__ import annotations

import hashlib
import json
import math
import zipfile
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import make_valid, union_all

from generate_hex_grid import (
    AREA_TOLERANCE_M2,
    ORIENTATION,
    ORIGIN_X,
    ORIGIN_Y,
    SIDE_M,
    TARGET_AREA_M2,
    TARGET_CRS,
    X_SPACING_M,
    Y_SPACING_M,
    cell_id,
    regular_hexagon,
)
from enrich_priority_readiness import COMPLETENESS_FIELDS, ROAD_FIELD_MAP
from prepare_m1 import geometry_ids, null_column, repair_clip, semantic_digest, text


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
DELIVERY = ROOT / "data" / "deliveries" / "m1_m2_caen_nord_v1"

GRID_VERSION = "M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1"
EXPECTED_COMMUNES = {
    "14060": "Bénouville",
    "14076": "Blainville-sur-Orne",
    "14167": "Colombelles",
    "14327": "Hérouville-Saint-Clair",
    "14488": "Ouistreham",
}

COMMUNES_SOURCE = RAW / "admin_express_caen_nord" / "communes_cibles_adminexpress.geojson"
ROADS_SOURCES = sorted((RAW / "bdtopo_routes").glob("routes_caen_nord_*.geojson"))
RESERVOIR_SOURCE = next(
    (RAW / "tvb_srce_normandie" / "extracted" / "dataset").glob("*.shp")
)
CORRIDOR_SOURCE = next(
    (RAW / "tvb_srce_normandie" / "corridors_basse_normandie" / "extracted" / "dataset").glob("*.shp")
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def write_layer(frame: gpd.GeoDataFrame, path: Path, layer: str, id_column: str) -> dict:
    if path.exists():
        path.unlink()
    frame.to_file(path, layer=layer, driver="GPKG", engine="pyogrio", index=False)
    reopened = gpd.read_file(path, layer=layer, engine="pyogrio")
    return {
        "file": path.name,
        "layer": layer,
        "crs": reopened.crs.to_string(),
        "feature_count": int(len(reopened)),
        "geometry_types": sorted(reopened.geometry.geom_type.unique().tolist()),
        "fields": [column for column in reopened.columns if column != "geometry"],
        "invalid_geometries": int((~reopened.geometry.is_valid).sum()),
        "null_geometries": int(reopened.geometry.isna().sum()),
        "duplicate_ids": int(reopened[id_column].duplicated().sum()),
        "semantic_sha256": semantic_digest(reopened, id_column),
    }


def load_territory() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame, object]:
    communes = gpd.read_file(COMMUNES_SOURCE, engine="pyogrio").to_crs(TARGET_CRS)
    actual = dict(zip(communes["code_insee"], communes["nom_officiel"], strict=True))
    if actual != EXPECTED_COMMUNES:
        raise RuntimeError(f"Unexpected communes: {actual}")
    if not communes.geometry.is_valid.all():
        communes.loc[~communes.geometry.is_valid, "geometry"] = communes.loc[
            ~communes.geometry.is_valid, "geometry"
        ].map(make_valid)

    territory = union_all(communes.geometry.array)
    if territory.geom_type != "Polygon" or not territory.is_valid:
        raise RuntimeError("The five municipalities must form one valid contiguous polygon")

    municipality_layer = communes[["code_insee", "nom_officiel", "geometry"]].copy()
    municipality_layer["source_id"] = "IGN_ADMINEXPRESS_COG_LATEST"
    territory_layer = gpd.GeoDataFrame(
        [{
            "territory_id": "CAEN-NORD-5COM-V1",
            "name": "Ouistreham–Hérouville-Saint-Clair, cinq communes",
            "commune_codes": ";".join(sorted(EXPECTED_COMMUNES)),
            "source_id": "IGN_ADMINEXPRESS_COG_LATEST",
            "area_m2": float(territory.area),
            "geometry": territory,
        }],
        crs=TARGET_CRS,
    )
    return municipality_layer, territory_layer, territory


def generate_grid(territory) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    min_x, min_y, max_x, max_y = territory.bounds
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
            clipped_geometry = full_geometry.intersection(territory)
            if clipped_geometry.is_empty or clipped_geometry.area <= AREA_TOLERANCE_M2:
                continue
            clipped_area = float(clipped_geometry.area)
            records.append({
                "maille_id": cell_id(row, column),
                "grid_version": GRID_VERSION,
                "grid_row": row,
                "grid_col": column,
                "center_x": center_x,
                "center_y": center_y,
                "full_area_m2": float(full_geometry.area),
                "clipped_area_m2": clipped_area,
                "area_m2": clipped_area,
                "pilot_fraction": clipped_area / float(full_geometry.area),
                "is_boundary": not full_geometry.within(territory),
                "full_geometry": full_geometry,
                "geometry": clipped_geometry,
            })

    records.sort(key=lambda item: (item["grid_row"], item["grid_col"]))
    clipped = gpd.GeoDataFrame(records, geometry="geometry", crs=TARGET_CRS)
    full = gpd.GeoDataFrame(
        clipped.drop(columns="geometry").rename(columns={"full_geometry": "geometry"}),
        geometry="geometry",
        crs=TARGET_CRS,
    )
    return clipped.drop(columns="full_geometry"), full


def prepare_roads(territory) -> tuple[gpd.GeoDataFrame, dict]:
    if len(ROADS_SOURCES) != 4:
        raise RuntimeError(f"Expected four paginated road extracts, found {len(ROADS_SOURCES)}")
    pages = [gpd.read_file(path, engine="pyogrio").to_crs(TARGET_CRS) for path in ROADS_SOURCES]
    source = gpd.GeoDataFrame(pd.concat(pages, ignore_index=True), crs=TARGET_CRS)
    if source["cleabs"].duplicated().any():
        raise RuntimeError("Duplicate BD TOPO cleabs across WFS pages")
    clipped, stats = repair_clip(source, territory, "line")
    data: dict[str, object] = {"source_id": "BDTOPO_ROUTES"}
    for source_field, output_field in ROAD_FIELD_MAP.items():
        values = clipped[source_field]
        data[output_field] = text(values) if values.dtype == object else values
    data["ouvrage_connu"] = null_column(clipped.index)
    data["millesime"] = null_column(clipped.index)
    data["attribute_scope"] = "source_attributes_not_ecological_barrier_evidence"
    roads = gpd.GeoDataFrame(data, geometry=clipped.geometry, crs=TARGET_CRS)
    roads = roads.sort_values("route_id", kind="stable").reset_index(drop=True)
    null_counts = {field: int(roads[field].isna().sum()) for field in COMPLETENESS_FIELDS}
    completeness = {
        field: float(roads[field].notna().mean()) if len(roads) else None
        for field in COMPLETENESS_FIELDS
    }
    return roads, {
        **stats,
        "wfs_bbox_features": int(len(source)),
        "enrichment_null_counts": null_counts,
        "enrichment_completeness_fraction": completeness,
    }


def prepare_reservoirs(territory) -> tuple[gpd.GeoDataFrame, dict]:
    source = gpd.read_file(RESERVOIR_SOURCE, bbox=territory.bounds, engine="pyogrio")
    clipped, stats = repair_clip(source, territory, "polygon")
    frame = gpd.GeoDataFrame(
        {
            "source_id": "TVB_RES_NORM",
            "objet_id": text(clipped["ID_RESV"]),
            "objet_source_id": text(clipped["ID_SRCE"]),
            "nom": text(clipped["NOM_RESV"]),
            "sous_trame": text(clipped["MILMAJ_REG"]),
            "millesime": "2014",
            "precision_source": null_column(clipped.index),
        },
        geometry=clipped.geometry,
        crs=TARGET_CRS,
    )
    return frame, stats


def prepare_corridors(territory) -> tuple[gpd.GeoDataFrame, dict]:
    source = gpd.read_file(CORRIDOR_SOURCE, bbox=territory.bounds, engine="pyogrio")
    source["_m1_objet_id"] = geometry_ids(source, "TVB-COR")
    clipped, stats = repair_clip(source, territory, "polygon")
    frame = gpd.GeoDataFrame(
        {
            "source_id": "TVB_COR_BN",
            "objet_id": text(clipped["_m1_objet_id"]),
            "objet_source_id": text(clipped["ID_SRCE"]),
            "libelle_source": text(clipped["ID_CORR"]),
            "classe_corridor": text(clipped["CLASS_CORR"]),
            "sous_trame": text(clipped["MILMAJ_REG"]),
            "millesime": "2014",
            "precision_source": null_column(clipped.index),
        },
        geometry=clipped.geometry,
        crs=TARGET_CRS,
    )
    return frame, stats


def main() -> None:
    DELIVERY.mkdir(parents=True, exist_ok=True)
    communes, territory_frame, territory = load_territory()
    clipped_grid, full_grid = generate_grid(territory)
    roads, road_stats = prepare_roads(territory)
    corridors, corridor_stats = prepare_corridors(territory)
    reservoirs, reservoir_stats = prepare_reservoirs(territory)

    outputs = {}
    territory_path = DELIVERY / "territoire_caen_nord.gpkg"
    if territory_path.exists():
        territory_path.unlink()
    territory_frame.to_file(territory_path, layer="territoire_cible", driver="GPKG", engine="pyogrio", index=False)
    communes.to_file(territory_path, layer="communes_cibles", driver="GPKG", engine="pyogrio", index=False, mode="a")
    outputs["territory"] = {
        "file": territory_path.name,
        "layers": [
            {"layer": "territoire_cible", "feature_count": 1, "geometry_types": ["Polygon"]},
            {"layer": "communes_cibles", "feature_count": 5, "geometry_types": sorted(communes.geometry.geom_type.unique())},
        ],
        "crs": TARGET_CRS,
        "territory_semantic_sha256": semantic_digest(territory_frame, "territory_id"),
        "municipalities_semantic_sha256": semantic_digest(communes, "code_insee"),
    }

    grid_path = DELIVERY / "grille_caen_nord.gpkg"
    if grid_path.exists():
        grid_path.unlink()
    clipped_grid.to_file(grid_path, layer="grille_caen_nord", driver="GPKG", engine="pyogrio", index=False)
    full_grid.to_file(grid_path, layer="hexagones_complets", driver="GPKG", engine="pyogrio", index=False, mode="a")
    outputs["grid"] = {
        "file": grid_path.name,
        "layers": [
            {"layer": "grille_caen_nord", "feature_count": int(len(clipped_grid)), "geometry_types": sorted(clipped_grid.geometry.geom_type.unique())},
            {"layer": "hexagones_complets", "feature_count": int(len(full_grid)), "geometry_types": sorted(full_grid.geometry.geom_type.unique())},
        ],
        "crs": TARGET_CRS,
        "fields": [column for column in clipped_grid.columns if column != "geometry"],
        "clipped_semantic_sha256": semantic_digest(clipped_grid, "maille_id"),
        "full_semantic_sha256": semantic_digest(full_grid, "maille_id"),
    }
    outputs["roads"] = write_layer(roads, DELIVERY / "routes.gpkg", "routes", "route_id")
    outputs["corridors"] = write_layer(corridors, DELIVERY / "corridors.gpkg", "corridors", "objet_id")
    outputs["reservoirs"] = write_layer(reservoirs, DELIVERY / "reservoirs.gpkg", "reservoirs", "objet_id")

    old_grid = gpd.read_file(PROCESSED / "grille_pilote.gpkg", layer="grille_pilote", engine="pyogrio")
    shared_ids = sorted(set(old_grid["maille_id"]) & set(clipped_grid["maille_id"]))
    old_by_id = old_grid.set_index("maille_id")
    new_by_id = clipped_grid.set_index("maille_id")
    stable_centers = all(
        old_by_id.loc[cell_id_value, "center_x"] == new_by_id.loc[cell_id_value, "center_x"]
        and old_by_id.loc[cell_id_value, "center_y"] == new_by_id.loc[cell_id_value, "center_y"]
        for cell_id_value in shared_ids
    )

    coverage = union_all(clipped_grid.geometry.array)
    full_overlap_area = 0.0
    spatial_index = full_grid.sindex
    for index, geometry in enumerate(full_grid.geometry):
        for other_index in spatial_index.query(geometry, predicate="intersects"):
            if other_index <= index:
                continue
            full_overlap_area += geometry.intersection(full_grid.geometry.iloc[other_index]).area

    source_bounds = {
        "reservoirs": tuple(round(value, 3) for value in gpd.read_file(RESERVOIR_SOURCE, engine="pyogrio").total_bounds),
        "corridors": tuple(round(value, 3) for value in gpd.read_file(CORRIDOR_SOURCE, engine="pyogrio").total_bounds),
        "roads_wfs_request": (455210.5, 6902897.105, 465179.0, 6915318.005),
    }
    validation = {
        "territory_valid": bool(territory.is_valid),
        "territory_contiguous": territory.geom_type == "Polygon",
        "grid_valid": bool(clipped_grid.geometry.is_valid.all() and full_grid.geometry.is_valid.all()),
        "grid_unique_ids": bool(clipped_grid["maille_id"].is_unique),
        "grid_missing_coverage_area_m2": float(territory.difference(coverage).area),
        "grid_excess_coverage_area_m2": float(coverage.difference(territory).area),
        "full_hexagon_overlap_area_m2": float(full_overlap_area),
        "all_crs_epsg2154": all(
            frame.crs.to_epsg() == 2154
            for frame in (communes, territory_frame, clipped_grid, full_grid, roads, corridors, reservoirs)
        ),
        "shared_old_grid_ids": len(shared_ids),
        "shared_ids_keep_same_lattice_centers": stable_centers,
        "old_grid_version": str(old_grid["grid_version"].iloc[0]),
        "new_grid_version": GRID_VERSION,
    }

    manifest = {
        "delivery_id": "M1-M2-CAEN-NORD-V1",
        "status": "ready_for_m2_geometric_crossing",
        "grid_version": GRID_VERSION,
        "target_crs": TARGET_CRS,
        "municipalities": [{"code_insee": code, "name": name} for code, name in EXPECTED_COMMUNES.items()],
        "territory_area_m2": float(territory.area),
        "lattice": {
            "orientation": ORIENTATION,
            "origin_m": [ORIGIN_X, ORIGIN_Y],
            "nominal_cell_area_m2": TARGET_AREA_M2,
            "side_m": SIDE_M,
            "spacing_m": [X_SPACING_M, Y_SPACING_M],
            "boundary_rule": "full lattice hexagons intersected with the exact five-commune union",
        },
        "outputs": outputs,
        "source_processing_counts": {
            "roads": road_stats,
            "corridors": corridor_stats,
            "reservoirs": reservoir_stats,
        },
        "source_extents_epsg2154": source_bounds,
        "validation": validation,
        "provenance": {
            "municipal_boundaries": {
                "producer": "IGN",
                "dataset": "ADMINEXPRESS-COG.LATEST:commune",
                "service": "https://data.geopf.fr/wfs/ows",
                "request_crs": TARGET_CRS,
                "cql_filter": "code_insee IN ('14488','14060','14076','14167','14327')",
                "retrieved_on": "2026-11-11",
                "raw_sha256": sha256(COMMUNES_SOURCE),
            },
            "roads": {
                "producer": "IGN",
                "dataset": "BDTOPO_V3:troncon_de_route",
                "service": "https://data.geopf.fr/wfs/ows",
                "request_crs": TARGET_CRS,
                "request_bbox_epsg2154": [455210.5, 6902897.105, 465179.0, 6915318.005],
                "pagination": {"count": 5000, "start_indexes": [0, 5000, 10000, 15000]},
                "retrieved_on": "2026-11-11",
                "raw_pages_sha256": {path.name: sha256(path) for path in ROADS_SOURCES},
            },
            "corridors": {"producer": "DREAL Normandie", "dataset": "SRCE Basse-Normandie", "reference_year": "2014"},
            "reservoirs": {"producer": "DREAL Normandie", "dataset": "SRCE Normandie", "reference_year": "2014"},
        },
        "limitations": [
            "SRCE data are from 2014 and do not prove present-day ecological functionality.",
            "BD TOPO attributes have object-level dates; no single global vintage is inferred.",
            "Boundary cells are fragments clipped to the exact municipal union.",
            "No ecological priority or action category is calculated in this delivery.",
        ],
    }

    for key, metadata in outputs.items():
        metadata["sha256"] = sha256(DELIVERY / metadata["file"])
    (DELIVERY / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    validation_report = {
        "delivery_id": manifest["delivery_id"],
        "status": "passed" if all([
            validation["territory_valid"],
            validation["territory_contiguous"],
            validation["grid_valid"],
            validation["grid_unique_ids"],
            validation["all_crs_epsg2154"],
            validation["shared_ids_keep_same_lattice_centers"],
            validation["grid_missing_coverage_area_m2"] < 1e-3,
            validation["grid_excess_coverage_area_m2"] < 1e-3,
            validation["full_hexagon_overlap_area_m2"] < 1e-3,
        ]) else "failed",
        "validation": validation,
        "required_layer_schemas": {
            key: metadata.get("fields", [])
            for key, metadata in outputs.items()
            if key in {"grid", "roads", "corridors", "reservoirs"}
        },
        "scientific_scope": (
            "Geographic preparation only. No conflict confirmation, ecological priority, "
            "or restoration recommendation is included."
        ),
    }
    (DELIVERY / "validation_report.json").write_text(
        json.dumps(validation_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    handoff_text = f"""# M1 → M2 — Caen nord, cinq communes

Status: **READY FOR GEOMETRIC CROSSING ANALYSIS**

## Scope

Exact union of Ouistreham (14488), Bénouville (14060), Blainville-sur-Orne (14076),
Colombelles (14167), and Hérouville-Saint-Clair (14327), from IGN
`ADMINEXPRESS-COG.LATEST:commune`, processed in EPSG:2154.

## Inputs for M2

- `grille_caen_nord.gpkg`, layer `grille_caen_nord`: {len(clipped_grid)} clipped cells.
- `territoire_caen_nord.gpkg`, layers `territoire_cible` and `communes_cibles`.
- `routes.gpkg`, layer `routes`: {len(roads)} BD TOPO road objects with source attributes.
- `corridors.gpkg`, layer `corridors`: {len(corridors)} SRCE 2014 objects.
- `reservoirs.gpkg`, layer `reservoirs`: {len(reservoirs)} SRCE 2014 objects.
- `manifest.json`: provenance, schemas, counts, source hashes, and output hashes.
- `validation_report.json`: topology, CRS, ID, coverage, and preservation checks.

Grid version: `{GRID_VERSION}`. Join cells using both `maille_id` and `grid_version`.
The original 43-cell grid remains unchanged. {len(shared_ids)} lattice IDs occur in both territories;
their centers are identical, but their clipped geometries and grid versions must not be mixed.

## Boundary and interpretation rules

Boundary cells are exact intersections between the established 1 km² lattice and the municipal union.
Geometric intersections are candidates for M2 review, not confirmed ecological conflicts.
SRCE layers date from 2014. Missing or null attributes remain unknown and are never converted to absence.
No ecological priority category is present in this package.
"""
    (DELIVERY / "M1_M2_HANDOFF.md").write_text(handoff_text, encoding="utf-8")

    zip_path = DELIVERY.parent / "M1_M2_CAEN_NORD_V1.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(DELIVERY.iterdir()):
            if path.is_file():
                archive.write(path, arcname=f"m1_m2_caen_nord_v1/{path.name}")
    (zip_path.with_suffix(".zip.sha256")).write_text(
        f"{sha256(zip_path)}  {zip_path.name}\n", encoding="ascii"
    )
    print(json.dumps({
        "grid_cells": len(clipped_grid),
        "boundary_cells": int(clipped_grid["is_boundary"].sum()),
        "roads": len(roads),
        "corridors": len(corridors),
        "reservoirs": len(reservoirs),
        "shared_old_grid_ids": len(shared_ids),
        "zip": zip_path.relative_to(ROOT).as_posix(),
        "zip_sha256": sha256(zip_path),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
