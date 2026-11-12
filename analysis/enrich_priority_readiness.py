"""Build M1 evidence-quality enrichments for M2 without classifying priorities."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio
import shapely
from shapely import normalize, to_wkb


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
GRID = PROCESSED / "grille_pilote.gpkg"
ROADS_RAW = RAW / "bdtopo_routes" / "routes_orne_estuaire_bbox.geojson"
SIPAF_RAW = RAW / "sipaf" / "Tous_les_PAF.gpkg"
ROADS_OUTPUT = PROCESSED / "routes_enriched.gpkg"
ROAD_ATTRIBUTES_OUTPUT = PROCESSED / "route_attributes_enriched.csv"
QUALITY_OUTPUT = PROCESSED / "cell_data_quality.csv"
SIPAF_OUTPUT = PROCESSED / "sipaf_context.json"
REPORT_OUTPUT = PROCESSED / "priority_enrichment_report.json"
TARGET_CRS = "EPSG:2154"
GRID_VERSION = "M1-CAND-1KM2-FLAT-L93-O0-V1"
SRCE_REFERENCE_YEAR = 2014

ROAD_FIELD_MAP = {
    "cleabs": "route_id",
    "nature": "categorie",
    "importance": "importance",
    "nombre_de_voies": "nombre_voies",
    "largeur_de_chaussee": "largeur_chaussee",
    "position_par_rapport_au_sol": "position_sol",
    "precision_planimetrique": "precision_planimetrique_m",
    "methode_d_acquisition_planimetrique": "methode_acquisition_planimetrique",
    "etat_de_l_objet": "statut_objet",
    "urbain": "contexte_urbain",
    "vitesse_moyenne_vl": "vitesse_moyenne_vl_source",
    "acces_vehicule_leger": "acces_vehicule_leger",
    "acces_pieton": "acces_pieton",
    "sens_de_circulation": "sens_circulation",
    "date_modification": "date_modification",
    "cpx_classement_administratif": "classement_administratif",
    "cpx_numero": "numero_route",
}

COMPLETENESS_FIELDS = [
    "categorie",
    "importance",
    "nombre_voies",
    "largeur_chaussee",
    "position_sol",
    "precision_planimetrique_m",
    "methode_acquisition_planimetrique",
    "statut_objet",
    "contexte_urbain",
    "vitesse_moyenne_vl_source",
    "acces_vehicule_leger",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def text(series: pd.Series) -> pd.Series:
    return series.astype("string").replace({"": pd.NA})


def semantic_digest(frame: gpd.GeoDataFrame, id_column: str) -> str:
    digest = hashlib.sha256()
    columns = sorted(column for column in frame.columns if column != "geometry")
    for _, row in frame.sort_values(id_column, kind="stable").iterrows():
        attrs = {column: None if pd.isna(row[column]) else str(row[column]) for column in columns}
        digest.update(json.dumps(attrs, sort_keys=True, ensure_ascii=False).encode("utf-8"))
        digest.update(to_wkb(normalize(row.geometry), hex=False, include_srid=False))
    return digest.hexdigest().upper()


def joined_values(frame: gpd.GeoDataFrame, field: str, missing_markers: set[str] | None = None) -> object:
    if frame.empty:
        return pd.NA
    values = text(frame[field]).dropna()
    if missing_markers:
        values = values.loc[~values.isin(missing_markers)]
    unique = sorted(values.unique().tolist())
    return "|".join(unique) if unique else pd.NA


def spatial_subset(frame: gpd.GeoDataFrame, geometry) -> gpd.GeoDataFrame:
    if frame.empty:
        return frame
    candidates = frame.iloc[list(frame.sindex.query(geometry, predicate="intersects"))]
    return candidates.loc[candidates.geometry.intersects(geometry)].copy()


def build_roads(grid: gpd.GeoDataFrame) -> tuple[gpd.GeoDataFrame, dict]:
    source = gpd.read_file(ROADS_RAW, engine="pyogrio")
    missing = sorted(set(ROAD_FIELD_MAP) - set(source.columns))
    if missing:
        raise RuntimeError(f"Missing expected BD TOPO fields: {missing}")
    source = source.to_crs(TARGET_CRS)
    pilot = grid.geometry.union_all()
    source = source.loc[source.geometry.notna() & source.geometry.intersects(pilot)].copy()
    source.geometry = source.geometry.intersection(pilot)
    source = source.loc[~source.geometry.is_empty].copy()

    data: dict[str, object] = {"source_id": "BDTOPO_ROUTES"}
    for source_field, output_field in ROAD_FIELD_MAP.items():
        values = source[source_field]
        data[output_field] = text(values) if values.dtype == object else values
    data["attribute_scope"] = "source_attributes_not_ecological_barrier_evidence"
    enriched = gpd.GeoDataFrame(data, geometry=source.geometry, crs=TARGET_CRS)
    enriched = enriched.sort_values("route_id", kind="stable").reset_index(drop=True)

    if ROADS_OUTPUT.exists():
        ROADS_OUTPUT.unlink()
    enriched.to_file(ROADS_OUTPUT, layer="routes_enriched", driver="GPKG", engine="pyogrio", index=False)
    reopened = gpd.read_file(ROADS_OUTPUT, layer="routes_enriched", engine="pyogrio")
    if len(reopened) != len(enriched) or reopened.crs.to_epsg() != 2154:
        raise RuntimeError("Enriched road output failed reopen validation")
    attributes = pd.DataFrame(reopened.drop(columns="geometry"))
    attributes.to_csv(
        ROAD_ATTRIBUTES_OUTPUT,
        index=False,
        encoding="utf-8",
        float_format="%.6f",
        lineterminator="\n",
    )

    report = {
        "feature_count": int(len(reopened)),
        "crs": reopened.crs.to_string(),
        "fields": [column for column in reopened.columns if column != "geometry"],
        "null_counts": {field: int(reopened[field].isna().sum()) for field in COMPLETENESS_FIELDS},
        "semantic_sha256": semantic_digest(reopened, "route_id"),
        "attribute_table_path": ROAD_ATTRIBUTES_OUTPUT.relative_to(ROOT).as_posix(),
        "attribute_table_sha256": sha256(ROAD_ATTRIBUTES_OUTPUT),
        "interpretation_limit": (
            "Road hierarchy and source speed attributes describe the road dataset; "
            "they do not prove ecological barrier severity, traffic intensity, or permeability."
        ),
    }
    return reopened, report


def build_cell_quality(grid: gpd.GeoDataFrame, roads: gpd.GeoDataFrame) -> pd.DataFrame:
    reservoirs = gpd.read_file(PROCESSED / "reservoirs.gpkg", layer="reservoirs", engine="pyogrio")
    corridors = gpd.read_file(PROCESSED / "corridors.gpkg", layer="corridors", engine="pyogrio")
    measures = pd.read_csv(PROCESSED / "sub_indicateurs.csv", dtype={"maille_id": "string"})
    measures = measures.set_index("maille_id")
    if not measures.index.is_unique:
        raise RuntimeError("Duplicate maille_id in elementary measurements")
    rows: list[dict] = []

    for cell in grid.sort_values("maille_id", kind="stable").itertuples():
        cell_roads = spatial_subset(roads, cell.geometry)
        cell_reservoirs = spatial_subset(reservoirs, cell.geometry)
        cell_corridors = spatial_subset(corridors, cell.geometry)
        measure = measures.loc[cell.maille_id]
        road_count = len(cell_roads)

        row: dict[str, object] = {
            "maille_id": cell.maille_id,
            "grid_version": cell.grid_version,
            "cell_area_m2": float(cell.area_m2),
            "full_area_m2": float(cell.full_area_m2),
            "pilot_fraction": float(cell.pilot_fraction),
            "is_boundary": bool(cell.is_boundary),
            "ocs_coverage_fraction": float(measure["ocs_coverage_fraction"]),
            "road_object_count": road_count,
        }
        for field in COMPLETENESS_FIELDS:
            available = int(cell_roads[field].notna().sum())
            row[f"road_{field}_available_count"] = available
            row[f"road_{field}_completeness_fraction"] = available / road_count if road_count else pd.NA

        reservoir_known = text(cell_reservoirs["sous_trame"]).dropna() if not cell_reservoirs.empty else []
        corridor_classes = text(cell_corridors["classe_corridor"]).dropna() if not cell_corridors.empty else []
        corridor_subtrames = (
            text(cell_corridors["sous_trame"]).replace({"-": pd.NA}).dropna()
            if not cell_corridors.empty
            else []
        )
        row.update(
            {
                "srce_reference_year": SRCE_REFERENCE_YEAR,
                "srce_age_status": "legacy_2014_requires_m2_scale_validation",
                "srce_precision_status": "source_precision_not_provided",
                "reservoir_object_count": int(len(cell_reservoirs)),
                "reservoir_subtrame_available_count": int(len(reservoir_known)),
                "reservoir_subtrames": joined_values(cell_reservoirs, "sous_trame"),
                "reservoir_subtrame_status": (
                    "not_applicable_no_mapped_reservoir"
                    if cell_reservoirs.empty
                    else "available"
                    if len(reservoir_known) == len(cell_reservoirs)
                    else "partially_unknown"
                ),
                "corridor_object_count": int(len(cell_corridors)),
                "corridor_class_available_count": int(len(corridor_classes)),
                "corridor_classes": joined_values(cell_corridors, "classe_corridor"),
                "corridor_subtrame_available_count": int(len(corridor_subtrames)),
                "corridor_subtrames": joined_values(cell_corridors, "sous_trame", {"-"}),
                "corridor_subtrame_status": (
                    "not_applicable_no_mapped_corridor"
                    if cell_corridors.empty
                    else "available"
                    if len(corridor_subtrames) == len(cell_corridors)
                    else "unknown_for_one_or_more_corridors"
                ),
                "bdhaie_inventory_status": measure["bdhaie_coverage_status"],
                "sipaf_inventory_status": measure["sipaf_coverage_status"],
                "cartofriches_inventory_status": measure["cartofriches_coverage_status"],
                "wetland_inventory_status": measure["wetland_coverage_status"],
                "pram_inventory_status": measure["pram_coverage_status"],
                "epfn_inventory_status": measure["epfn_coverage_status"],
                "inventory_completeness_conclusion": "unknown_not_suitable_for_absence_inference",
                "provenance_refs": (
                    "BDTOPO_ROUTES;TVB_RES_NORM;TVB_COR_BN;OCSGE;BDHAIE;SIPAF;"
                    "CARTOFRICHES;ZH_DREAL_NORM"
                ),
            }
        )
        rows.append(row)

    result = pd.DataFrame(rows).sort_values("maille_id", kind="stable")
    if len(result) != 43 or not result["maille_id"].is_unique:
        raise RuntimeError("Cell quality output must contain exactly 43 unique cells")
    if set(result["maille_id"]) != set(grid["maille_id"]):
        raise RuntimeError("Cell quality output does not match the original grid IDs")
    result.to_csv(QUALITY_OUTPUT, index=False, encoding="utf-8", float_format="%.6f", lineterminator="\n")
    return result


def build_sipaf_context(grid: gpd.GeoDataFrame) -> dict:
    sipaf = gpd.read_file(SIPAF_RAW, layer="Tous_les_PAF", engine="pyogrio")
    if sipaf.crs is None or sipaf.crs.to_epsg() != 2154:
        raise RuntimeError(f"Unexpected SIPAF CRS: {sipaf.crs}")
    pilot = grid.geometry.union_all()
    local = sipaf.loc[sipaf.geometry.notna() & sipaf.geometry.intersects(pilot)]
    retained = [
        "Identifiant UUID",
        "ID",
        "Nom Passage Faune",
        "Catégorie d'ouvrage",
        "Type d'ouvrage",
        "Spécificité du passage faune",
        "Infrastructure traversée",
        "Ouvrage hydraulique",
        "Positionnement",
        "Date de réalisation",
        "Date de requalification",
        "Largeur ouvrage (m)",
        "Longueur de franchissement (m)",
        "Source",
    ]
    missing = sorted(set(retained) - set(sipaf.columns))
    if missing:
        raise RuntimeError(f"Missing expected SIPAF fields: {missing}")

    return {
        "source_id": "SIPAF",
        "local_path": "data/raw/sipaf/Tous_les_PAF.gpkg",
        "layer": "Tous_les_PAF",
        "crs": "EPSG:2154",
        "geometry_types": sorted(sipaf.geometry.dropna().geom_type.unique().tolist()),
        "national_export_record_count": int(len(sipaf)),
        "pilot_registered_record_count": int(len(local)),
        "pilot_record_status": "no_registered_record_intersects_pilot",
        "inventory_completeness": "non_exhaustive",
        "absence_interpretation": "No registered record is not evidence that no local crossing structure exists.",
        "retained_fields_for_future_internal_analysis": retained,
        "public_export_created": False,
        "sensitive_record_data_in_output": False,
        "raw_sha256": sha256(SIPAF_RAW),
    }


def main() -> None:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    grid = gpd.read_file(GRID, layer="grille_pilote", engine="pyogrio")
    if len(grid) != 43 or grid.crs.to_epsg() != 2154:
        raise RuntimeError("Unexpected pilot grid count or CRS")
    if set(grid["grid_version"]) != {GRID_VERSION} or not grid["maille_id"].is_unique:
        raise RuntimeError("Unexpected grid version or duplicate cell ID")
    grid_semantic_before = semantic_digest(grid, "maille_id")

    roads, road_report = build_roads(grid)
    quality = build_cell_quality(grid, roads)
    sipaf_context = build_sipaf_context(grid)
    SIPAF_OUTPUT.write_text(json.dumps(sipaf_context, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    grid_after = gpd.read_file(GRID, layer="grille_pilote", engine="pyogrio")
    grid_semantic_after = semantic_digest(grid_after, "maille_id")
    if grid_semantic_after != grid_semantic_before:
        raise RuntimeError("Pilot grid changed during enrichment")

    report = {
        "status": "quality_evidence_only_no_priority_classification",
        "pipeline_version": "m1-priority-readiness-v1",
        "grid_version": GRID_VERSION,
        "grid_row_count": 43,
        "grid_semantic_sha256_before": grid_semantic_before,
        "grid_semantic_sha256_after": grid_semantic_after,
        "target_crs": TARGET_CRS,
        "null_rule": "Unknown or unavailable values remain NULL; they are never converted to zero.",
        "roads": road_report,
        "cell_quality": {
            "row_count": int(len(quality)),
            "field_count": int(len(quality.columns)),
            "path": QUALITY_OUTPUT.relative_to(ROOT).as_posix(),
            "sha256": sha256(QUALITY_OUTPUT),
        },
        "sipaf_context": sipaf_context,
        "libraries": {
            "python": platform.python_version(),
            "geopandas": gpd.__version__,
            "pyogrio": pyogrio.__version__,
            "shapely": shapely.__version__,
        },
        "outputs": {
            "enriched_roads": "data/processed/routes_enriched.gpkg",
            "enriched_road_attributes": "data/processed/route_attributes_enriched.csv",
            "cell_quality": "data/processed/cell_data_quality.csv",
            "sipaf_context": "data/processed/sipaf_context.json",
        },
    }
    REPORT_OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"roads": len(roads), "cells": len(quality), "sipaf_in_pilot": 0}))


if __name__ == "__main__":
    main()
