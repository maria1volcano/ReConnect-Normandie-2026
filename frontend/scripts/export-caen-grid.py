"""Export the validated Caen Nord M1 grid as a minimal public GeoJSON.

The source GeoPackage remains in the internal M1 delivery.  This export keeps
only geometry and cell-level grid metadata needed by the M3 map.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import geopandas as gpd


EXPECTED_COUNT = 66
EXPECTED_CRS = "EPSG:2154"
EXPECTED_VERSION = "M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1"
PUBLIC_COLUMNS = [
    "maille_id",
    "grid_version",
    "area_m2",
    "full_area_m2",
    "pilot_fraction",
    "is_boundary",
    "geometry",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--territory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    grid = gpd.read_file(args.input, layer="grille_caen_nord")
    if str(grid.crs).upper() != EXPECTED_CRS:
        raise ValueError(f"CRS source inattendu: {grid.crs}")
    if len(grid) != EXPECTED_COUNT:
        raise ValueError(f"Nombre de mailles inattendu: {len(grid)}")
    if grid.maille_id.isna().any() or not grid.maille_id.is_unique:
        raise ValueError("Les maille_id doivent être renseignés et uniques")
    if set(grid.grid_version) != {EXPECTED_VERSION}:
        raise ValueError("grid_version inattendue")
    if grid.geometry.isna().any() or grid.geometry.is_empty.any() or not grid.geometry.is_valid.all():
        raise ValueError("La grille contient une géométrie vide ou invalide")

    grid_union = grid.geometry.union_all()
    overlap_area = float(grid.geometry.area.sum() - grid_union.area)
    if overlap_area > 0.1:
        raise ValueError(f"Chevauchements inattendus entre cellules: {overlap_area:.3f} m²")

    territory = gpd.read_file(args.territory, layer="territoire_cible").to_crs(grid.crs)
    territory_union = territory.geometry.union_all()
    coverage_difference = float(grid_union.symmetric_difference(territory_union).area)
    if coverage_difference > 0.1:
        raise ValueError(f"Écart de couverture avec le territoire: {coverage_difference:.3f} m²")

    public_grid = grid[PUBLIC_COLUMNS].to_crs("EPSG:4326")
    payload = json.loads(public_grid.to_json(drop_id=True))
    payload.update(
        {
            "name": "Grille M1 Caen Nord — 5 communes",
            "grid_version": EXPECTED_VERSION,
            "source": "Livraison interne M1 m1_m2_caen_nord_v1",
            "source_sha256": sha256(args.input),
            "source_crs": EXPECTED_CRS,
            "license": "Licence Ouverte / Open Licence 2.0 — géométrie dérivée de limites administratives IGN",
        }
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )

    bounds = [round(value, 8) for value in public_grid.total_bounds.tolist()]
    print(json.dumps({"features": len(public_grid), "bounds_wgs84": bounds}, ensure_ascii=False))


if __name__ == "__main__":
    main()
