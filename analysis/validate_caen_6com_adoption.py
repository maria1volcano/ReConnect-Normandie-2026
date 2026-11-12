"""Validate the immutable M2 Caen-six-commune grid before formal M1 adoption."""

from __future__ import annotations

import argparse
import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd


EXPECTED_ZIP_SHA256 = "F1878207F370DC2A424898CF2DE89DB540D6EABAB43BD7E5F6C93BBF3C2FD3B4"
EXPECTED_GRID_VERSION = "M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1"
EXPECTED_CODES = {"14118", "14488", "14060", "14076", "14167", "14327"}
PREFIX = "RECONNECT_CAEN_ET_NORD_M2_DEMO_INTERNE_20261111_V1/"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def validate(zip_path: Path, previous_delivery: Path) -> dict[str, object]:
    if digest(zip_path) != EXPECTED_ZIP_SHA256:
        raise ValueError("Empreinte du ZIP M2 inattendue")

    with tempfile.TemporaryDirectory(prefix="m1_caen6_adoption_") as temp_dir:
        temp = Path(temp_dir)
        with zipfile.ZipFile(zip_path) as archive:
            for relative in ("donnees/grille.gpkg", "donnees/territoire.gpkg"):
                member = PREFIX + relative
                target = temp / Path(relative).name
                target.write_bytes(archive.read(member))

        grid = gpd.read_file(temp / "grille.gpkg", layer="mailles")
        full = gpd.read_file(temp / "grille.gpkg", layer="hexagones_complets").set_index("maille_id")
        territory = gpd.read_file(temp / "territoire.gpkg", layer="territoire")
        communes = gpd.read_file(temp / "territoire.gpkg", layer="communes")
        previous = gpd.read_file(previous_delivery / "grille_caen_nord.gpkg", layer="grille_caen_nord").set_index("maille_id")
        previous_full = gpd.read_file(previous_delivery / "grille_caen_nord.gpkg", layer="hexagones_complets").set_index("maille_id")
        previous_territory = gpd.read_file(previous_delivery / "territoire_caen_nord.gpkg", layer="territoire_cible").geometry.union_all()

        assert grid.crs.to_epsg() == full.crs.to_epsg() == territory.crs.to_epsg() == 2154
        assert len(grid) == len(full) == 101
        assert grid.maille_id.is_unique and full.index.is_unique
        assert set(grid.grid_version) == {EXPECTED_GRID_VERSION}
        assert grid.geometry.is_valid.all() and full.geometry.is_valid.all()
        assert set(communes.code_insee.astype(str)) == EXPECTED_CODES
        assert len(communes) == 6 and communes.geometry.is_valid.all()
        assert int(grid.is_boundary.sum()) == 67
        assert len(grid) - int(grid.is_boundary.sum()) == 34
        assert abs(float(grid.geometry.union_all().symmetric_difference(territory.geometry.union_all()).area)) < 0.001
        assert set(previous.index) <= set(grid.maille_id)

        current = grid.set_index("maille_id")
        common = sorted(previous.index)
        assert all(previous_full.loc[cell].geometry.equals_exact(full.loc[cell].geometry, 0) for cell in common)
        clipped_difference = sum(
            previous.loc[cell].geometry.symmetric_difference(
                current.loc[cell].geometry.intersection(previous_territory)
            ).area
            for cell in common
        )
        assert clipped_difference < 0.001
        assert max(abs(full.geometry.area - 1_000_000)) < 0.001

        return {
            "status": "adopted_for_local_integration",
            "zip_sha256": EXPECTED_ZIP_SHA256,
            "grid_version": EXPECTED_GRID_VERSION,
            "territory_id": "caen_et_nord_6communes",
            "crs": "EPSG:2154",
            "cells": len(grid),
            "interior_cells": 34,
            "boundary_cells": 67,
            "municipality_codes": sorted(EXPECTED_CODES),
            "territory_area_m2": float(territory.geometry.area.sum()),
            "shared_previous_ids": len(common),
            "full_hexagons_exactly_equal": len(common),
            "previous_clip_symmetric_difference_m2": clipped_difference,
            "publication_authorized": False,
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--m2-zip", type=Path, required=True)
    parser.add_argument("--previous-delivery", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(validate(args.m2_zip, args.previous_delivery), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
