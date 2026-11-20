"""La grille publique 22 communes ne doit contenir ni superposition ni hexagone fragmenté."""
from pathlib import Path

import geopandas as gpd
import pytest
from shapely import union_all

ROOT = Path(__file__).resolve().parents[1]
GRID = ROOT / "frontend/public/data/caen-22com/grid.geojson"
COMMUNES = ROOT / "analysis/territoires/communes_adminexpress_22.geojson"


@pytest.fixture(scope="module")
def grid():
    return gpd.read_file(GRID).to_crs(2154)


def test_aucune_superposition(grid):
    index = grid.sindex
    overlap = sum(grid.geometry[i].intersection(grid.geometry[j]).area
                  for i in range(len(grid)) for j in index.query(grid.geometry[i], predicate="intersects") if j > i)
    assert overlap < 1e-3


def test_un_seul_fragment_par_hexagone(grid):
    assert grid.maille_id.is_unique
    assert not grid.maille_id.str.endswith("-EXT").any()


def test_couvre_les_communes_dans_l_emprise(grid):
    communes = union_all(gpd.read_file(COMMUNES).to_crs(2154).geometry.to_numpy())
    cells = union_all(grid.geometry.to_numpy())
    assert cells.difference(communes).area < 1.0
    assert len(grid) == 185
