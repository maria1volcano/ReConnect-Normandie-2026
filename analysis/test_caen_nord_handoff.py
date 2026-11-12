"""End-to-end validation for the internal Caen-nord M1 -> M2 handoff."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import geopandas as gpd
from shapely import union_all

from generate_caen_nord_handoff import DELIVERY, EXPECTED_COMMUNES, GRID_VERSION, TARGET_CRS


ROOT = Path(__file__).resolve().parents[1]
ZIP_PATH = DELIVERY.parent / "M1_M2_CAEN_NORD_V1.zip"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def manifest() -> dict:
    return json.loads((DELIVERY / "manifest.json").read_text(encoding="utf-8"))


def semantic_hashes(data: dict) -> dict:
    return {
        "territory": data["outputs"]["territory"]["territory_semantic_sha256"],
        "municipalities": data["outputs"]["territory"]["municipalities_semantic_sha256"],
        "grid_clipped": data["outputs"]["grid"]["clipped_semantic_sha256"],
        "grid_full": data["outputs"]["grid"]["full_semantic_sha256"],
        "roads": data["outputs"]["roads"]["semantic_sha256"],
        "corridors": data["outputs"]["corridors"]["semantic_sha256"],
        "reservoirs": data["outputs"]["reservoirs"]["semantic_sha256"],
    }


def main() -> None:
    original_grid_path = ROOT / "data" / "processed" / "grille_pilote.gpkg"
    original_grid_hash = sha256(original_grid_path)
    before = manifest()
    raw_hashes_before = before["provenance"]

    subprocess.run(
        [sys.executable, str(ROOT / "analysis" / "generate_caen_nord_handoff.py")],
        cwd=ROOT,
        check=True,
    )
    after = manifest()

    assert semantic_hashes(after) == semantic_hashes(before), "Delivery changed on deterministic rerun"
    assert after["provenance"] == raw_hashes_before, "Raw source provenance changed"
    assert sha256(original_grid_path) == original_grid_hash, "Original 43-cell grid was modified"

    territory = gpd.read_file(
        DELIVERY / "territoire_caen_nord.gpkg", layer="territoire_cible", engine="pyogrio"
    )
    communes = gpd.read_file(
        DELIVERY / "territoire_caen_nord.gpkg", layer="communes_cibles", engine="pyogrio"
    )
    grid = gpd.read_file(
        DELIVERY / "grille_caen_nord.gpkg", layer="grille_caen_nord", engine="pyogrio"
    )
    full_grid = gpd.read_file(
        DELIVERY / "grille_caen_nord.gpkg", layer="hexagones_complets", engine="pyogrio"
    )
    roads = gpd.read_file(DELIVERY / "routes.gpkg", layer="routes", engine="pyogrio")
    corridors = gpd.read_file(DELIVERY / "corridors.gpkg", layer="corridors", engine="pyogrio")
    reservoirs = gpd.read_file(DELIVERY / "reservoirs.gpkg", layer="reservoirs", engine="pyogrio")
    original_grid = gpd.read_file(original_grid_path, layer="grille_pilote", engine="pyogrio")

    assert dict(zip(communes["code_insee"], communes["nom_officiel"], strict=True)) == EXPECTED_COMMUNES
    assert len(communes) == 5 and len(territory) == 1
    assert territory.geometry.iloc[0].is_valid and territory.geometry.iloc[0].geom_type == "Polygon"
    assert all(frame.crs.to_string() == TARGET_CRS for frame in (
        territory, communes, grid, full_grid, roads, corridors, reservoirs
    ))

    assert len(original_grid) == 43
    assert len(grid) == 66 and grid["maille_id"].is_unique
    assert grid["grid_version"].eq(GRID_VERSION).all()
    assert grid.geometry.notna().all() and grid.geometry.is_valid.all()
    assert full_grid.geometry.notna().all() and full_grid.geometry.is_valid.all()
    assert set(grid["maille_id"]) == set(full_grid["maille_id"])

    coverage = union_all(grid.geometry.array)
    target = territory.geometry.iloc[0]
    assert target.difference(coverage).area < 1e-3
    assert coverage.difference(target).area < 1e-3
    overlap_area = 0.0
    spatial_index = full_grid.sindex
    for index, geometry in enumerate(full_grid.geometry):
        for other_index in spatial_index.query(geometry, predicate="intersects"):
            if other_index > index:
                overlap_area += geometry.intersection(full_grid.geometry.iloc[other_index]).area
    assert overlap_area < 1e-3

    shared = set(original_grid["maille_id"]) & set(grid["maille_id"])
    assert len(shared) == 14
    for maille_id in shared:
        old = original_grid.loc[original_grid["maille_id"] == maille_id].iloc[0]
        new = grid.loc[grid["maille_id"] == maille_id].iloc[0]
        assert old.center_x == new.center_x and old.center_y == new.center_y
        assert old.grid_version != new.grid_version

    required_road_fields = {
        "route_id", "categorie", "importance", "nombre_voies", "largeur_chaussee",
        "position_sol", "precision_planimetrique_m", "methode_acquisition_planimetrique",
        "statut_objet", "contexte_urbain", "vitesse_moyenne_vl_source",
        "acces_vehicule_leger", "acces_pieton", "sens_circulation",
        "classement_administratif", "numero_route", "source_id",
    }
    assert required_road_fields <= set(roads.columns)
    assert len(roads) == 8539 and roads["route_id"].is_unique
    assert len(corridors) == 31 and corridors["objet_id"].is_unique
    assert len(reservoirs) == 20 and reservoirs["objet_id"].is_unique
    assert roads["source_id"].eq("BDTOPO_ROUTES").all()
    assert corridors["source_id"].eq("TVB_COR_BN").all()
    assert reservoirs["source_id"].eq("TVB_RES_NORM").all()
    assert not any("priority" in column.lower() for frame in (grid, roads, corridors, reservoirs) for column in frame.columns)

    validation = json.loads((DELIVERY / "validation_report.json").read_text(encoding="utf-8"))
    assert validation["status"] == "passed"
    assert ZIP_PATH.exists() and ZIP_PATH.stat().st_size > 0
    expected_zip_files = {
        "m1_m2_caen_nord_v1/M1_M2_HANDOFF.md",
        "m1_m2_caen_nord_v1/corridors.gpkg",
        "m1_m2_caen_nord_v1/grille_caen_nord.gpkg",
        "m1_m2_caen_nord_v1/manifest.json",
        "m1_m2_caen_nord_v1/reservoirs.gpkg",
        "m1_m2_caen_nord_v1/routes.gpkg",
        "m1_m2_caen_nord_v1/territoire_caen_nord.gpkg",
        "m1_m2_caen_nord_v1/validation_report.json",
    }
    with zipfile.ZipFile(ZIP_PATH) as archive:
        assert set(archive.namelist()) == expected_zip_files
        assert archive.testzip() is None

    print(
        "PASS: official territory, 66-cell topology, enriched essential layers, "
        "versioned IDs, reproducibility, original pilot preservation, transferable ZIP"
    )


if __name__ == "__main__":
    main()
