"""Validate M1 priority-readiness enrichments without assigning priorities."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import geopandas as gpd
import pandas as pd

from enrich_priority_readiness import (
    GRID,
    GRID_VERSION,
    QUALITY_OUTPUT,
    ROAD_ATTRIBUTES_OUTPUT,
    REPORT_OUTPUT,
    ROADS_OUTPUT,
    SIPAF_OUTPUT,
    semantic_digest,
)


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "analysis" / "enrich_priority_readiness.py"


def run_pipeline() -> tuple[dict, bytes, bytes]:
    subprocess.run([sys.executable, str(PIPELINE)], cwd=ROOT, check=True)
    return (
        json.loads(REPORT_OUTPUT.read_text(encoding="utf-8")),
        QUALITY_OUTPUT.read_bytes(),
        SIPAF_OUTPUT.read_bytes(),
    )


def main() -> None:
    grid_before = gpd.read_file(GRID, layer="grille_pilote", engine="pyogrio")
    grid_digest_before = semantic_digest(grid_before, "maille_id")

    first_report, first_quality, first_sipaf = run_pipeline()
    second_report, second_quality, second_sipaf = run_pipeline()
    assert first_quality == second_quality
    assert first_sipaf == second_sipaf
    assert first_report["roads"]["semantic_sha256"] == second_report["roads"]["semantic_sha256"]

    grid_after = gpd.read_file(GRID, layer="grille_pilote", engine="pyogrio")
    assert semantic_digest(grid_after, "maille_id") == grid_digest_before
    assert len(grid_after) == 43 and grid_after["maille_id"].is_unique
    assert set(grid_after["grid_version"]) == {GRID_VERSION}
    assert grid_after.crs.to_epsg() == 2154

    roads = gpd.read_file(ROADS_OUTPUT, layer="routes_enriched", engine="pyogrio")
    assert len(roads) == 1924 and roads["route_id"].is_unique
    assert roads.crs.to_epsg() == 2154
    required_road_fields = {
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
    }
    assert required_road_fields <= set(roads.columns)
    assert roads["categorie"].notna().all() and roads["importance"].notna().all()
    assert roads["nombre_voies"].isna().any(), "Source NULL values must remain NULL"
    road_attributes = pd.read_csv(ROAD_ATTRIBUTES_OUTPUT)
    assert len(road_attributes) == len(roads)
    assert road_attributes["route_id"].is_unique
    assert set(road_attributes["route_id"]) == set(roads["route_id"])

    quality = pd.read_csv(QUALITY_OUTPUT)
    assert len(quality) == 43 and quality["maille_id"].is_unique
    assert set(quality["maille_id"]) == set(grid_after["maille_id"])
    assert quality["grid_version"].eq(GRID_VERSION).all()
    assert quality["srce_reference_year"].eq(2014).all()
    assert quality["inventory_completeness_conclusion"].eq(
        "unknown_not_suitable_for_absence_inference"
    ).all()
    no_road = quality["road_object_count"].eq(0)
    completeness = quality.filter(like="_completeness_fraction")
    assert completeness.loc[no_road].isna().all(axis=None)
    assert ((completeness.dropna() >= 0) & (completeness.dropna() <= 1)).all(axis=None)
    assert quality.loc[quality["corridor_object_count"].gt(0), "corridor_subtrames"].isna().all()

    sipaf = json.loads(SIPAF_OUTPUT.read_text(encoding="utf-8"))
    assert sipaf["crs"] == "EPSG:2154"
    assert sipaf["pilot_registered_record_count"] == 0
    assert sipaf["inventory_completeness"] == "non_exhaustive"
    assert not sipaf["public_export_created"] and not sipaf["sensitive_record_data_in_output"]

    assert first_report["status"] == "quality_evidence_only_no_priority_classification"
    assert first_report["roads"]["attribute_table_sha256"] == second_report["roads"]["attribute_table_sha256"]
    assert first_report["grid_semantic_sha256_before"] == first_report["grid_semantic_sha256_after"]
    print("PASS: 43 stable grid IDs, enriched roads, NULL handling, joins, CRS, SIPAF context, determinism")


if __name__ == "__main__":
    main()
