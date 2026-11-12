"""Régression numérique M1 figée ; sources d'enjeux/conflits SYNTHÉTIQUES.

Les contacts d'arête, doublons géométriques et lacunes du prototype sont déjà
couverts par test_m2_inputs.py. Les autres cas et les protections supplémentaires
sont contrôlés ici sur le véritable validateur, sans dépendre du prototype.
"""

import hashlib
from importlib import util
import json
import math
from pathlib import Path

import geopandas as gpd
import pytest
from shapely import union_all
from shapely.affinity import translate
from shapely.geometry import LineString, MultiPolygon, Point, Polygon, box

from analysis import validate_inputs as validation
from analysis.aggregate_conflicts import aggregate_conflicts
from analysis.detect_conflicts import SourceFields, detect_route_corridor_conflicts
from analysis.indicateurs_enjeux import compute_enjeux
from analysis.run_conflicts import load_config as load_conflicts_config
from analysis.run_enjeux import load_config as load_enjeux_config

FIXTURES = Path(__file__).parent / "fixtures" / "m1_grid_v61"
X, Y = 461_000.0, 6_905_000.0


def frame(geometries, **columns):
    return gpd.GeoDataFrame(columns, geometry=geometries, crs=2154)


def check(grid, territory=None):
    if territory is None:
        territory = frame([union_all(grid.geometry.to_numpy())])
    report = validation.ValidationReport()
    validation.validate_spatial_coverage(grid, territory, report)
    # Le rapport doit rester sérialisable même pour des entrées bloquées.
    json.dumps(report.as_dict(), allow_nan=False)
    return report


def error_codes(report):
    return {issue.code for issue in report.issues if issue.severity == "error"}


def overlap_issue(report):
    return next(issue for issue in report.issues if issue.code == "grid_overlap")


@pytest.fixture(scope="module")
def m1_grids():
    provenance = json.loads((FIXTURES / "provenance.json").read_text())
    for name, metadata in provenance["files"].items():
        assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == metadata["sha256"]
    spec = util.spec_from_file_location("m1_grid_regression", FIXTURES / "generate_hex_grid.py")
    generator = util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    regenerated, _, pilot = generator.generate_grid()  # fonction pure ; aucun main() ni export
    delivered = gpd.read_file(FIXTURES / "grille_pilote_wgs84.geojson").to_crs(2154)
    return {"geojson": delivered, "regenerated": regenerated}, frame([pilot])


@pytest.mark.parametrize("representation", ["geojson", "regenerated"])
@pytest.mark.parametrize("reverse", [False, True])
def test_m1_grid_passes_with_explicit_residue_without_mutation(m1_grids, representation, reverse):
    grids, territory = m1_grids
    grid = grids[representation].iloc[::-1].copy() if reverse else grids[representation].copy()
    before, before_territory = grid.copy(deep=True), territory.copy(deep=True)
    report = check(grid, territory)
    assert report.ok
    issue = next(i for i in report.issues if i.code == "grid_overlap_numerical_residue")
    assert issue.severity == "warning"
    assert issue.details["positive_pair_count"] > 0
    assert 0 < issue.details["max_pair_area_m2"] <= validation.AREA_TOLERANCE_M2
    assert issue.details["rejected_pairs"] == [] and not issue.details["error"]
    assert len(grid) == 43 and grid.maille_id.is_unique
    assert grid.equals(before) and territory.equals(before_territory)
    assert grid.geometry.to_wkb().tolist() == before.geometry.to_wkb().tolist()


@pytest.mark.parametrize("kind", ["vertex", "disjoint"])
def test_surface_free_relations_have_no_overlap_warning(kind):
    second = box(X+10, Y+10, X+20, Y+20) if kind == "vertex" else box(X+20, Y, X+30, Y+10)
    report = check(frame([box(X, Y, X+10, Y+10), second]))
    assert report.ok
    assert not any(i.code.startswith("grid_overlap") for i in report.issues)


def true_overlap_cases():
    cell = box(X, Y, X+10, Y+10)
    compact = box(X, Y, X+0.0001, Y+0.0001)
    many = [box(X+i, Y, X+i+0.0001, Y+0.0001) for i in range(8) for _ in range(2)]
    return [
        pytest.param([cell, box(X+9.999, Y, X+20, Y+10)], id="millimetre"),
        pytest.param([cell, box(X+1, Y+1, X+2, Y+2)], id="containment"),
        pytest.param([cell]*3, id="triple"),
        pytest.param([box(X, Y, X+5, Y+5), box(X+5-1e-7, Y, X+10, Y+5)], id="tiny-strip"),
        pytest.param([compact, compact], id="tiny-compact"),
        pytest.param(many, id="many-tiny-compacts"),
    ]


@pytest.mark.parametrize("geometries", true_overlap_cases())
def test_true_overlaps_are_rejected_without_ids(geometries):
    grid = frame(geometries)
    grid.index = [99]*len(grid)  # positions, pas labels d'index ni maille_id obligatoires
    before = grid.copy(deep=True)
    report = check(grid)
    assert "grid_overlap" in error_codes(report)
    pairs = overlap_issue(report).details["rejected_pairs"]
    assert pairs and all(p["left_position"] < p["right_position"] for p in pairs)
    assert all("left" not in p and "right" not in p for p in pairs)
    assert grid.equals(before)


def test_one_millimetre_displacement_of_m1_cell_is_rejected(m1_grids):
    grids, territory = m1_grids
    grid = grids["regenerated"].copy()
    position = grid.index[~grid.is_boundary][0]
    grid.at[position, "geometry"] = translate(grid.loc[position].geometry, xoff=0.001)
    report = check(grid, territory)
    assert "grid_overlap" in error_codes(report)
    assert overlap_issue(report).details["rejected_pairs"]


def test_local_rejection_wins_even_when_global_budget_is_satisfied():
    compact = box(X, Y, X+0.0001, Y+0.0001)
    grid = frame([compact, compact, box(X+100, Y+100, X+1100, Y+1100)], maille_id=["A", "B", "C"])
    report = check(grid)
    issue = overlap_issue(report)
    assert issue.details["compensated_overlap_m2"] <= issue.details["global_numeric_budget_m2"]
    pair = issue.details["rejected_pairs"][0]
    assert pair["left"] == "A" and pair["right"] == "B"
    assert pair["numeric_budget_m2"] < pair["area_m2"] < validation.AREA_TOLERANCE_M2


def test_existing_area_cap_cannot_be_relaxed_by_large_coordinate_ulp():
    x = float(2**45)  # scénario arithmétique SYNTHÉTIQUE, pas emprise source plausible
    grid = frame([box(x, Y, x+1, Y+10), box(x+1-math.ulp(x), Y, x+2, Y+10)])
    pair = overlap_issue(check(grid)).details["rejected_pairs"][0]
    assert validation.AREA_TOLERANCE_M2 < pair["area_m2"] <= pair["numeric_budget_m2"]


def test_global_guard_still_rejects_unexplained_union_area_deficit():
    cell = box(X, Y, X+10, Y+10)
    result = validation._grid_overlap_diagnostic(frame([cell]), cell.buffer(-0.01))
    assert result["positive_pair_count"] == 0
    assert result["compensated_overlap_m2"] > result["global_numeric_budget_m2"]
    assert result["error"]


def test_multipolygon_overlap_is_rejected():
    cell = box(X, Y, X+10, Y+10)
    remote = box(X+20, Y, X+30, Y+10)
    assert "grid_overlap" in error_codes(check(frame([MultiPolygon([cell, remote]), cell])))


def test_collection_contacts_do_not_inflate_the_surface_budget():
    grid = frame([
        MultiPolygon([box(X, Y, X+1, Y+1), box(X+10, Y, X+20, Y+10)]),
        MultiPolygon([box(X+0.5, Y+0.5, X+1.5, Y+1.5), box(X+20, Y, X+30, Y+10)]),
    ])
    assert grid.geometry.iloc[0].intersection(grid.geometry.iloc[1]).geom_type == "GeometryCollection"
    issue = overlap_issue(check(grid))
    pair = issue.details["rejected_pairs"][0]
    delta = issue.details["coordinate_ulp_diagonal_m"]
    assert pair["area_m2"] == 0.25
    # Périmètre du carré de côté 0,5 m ; le contact linéaire de 10 m est exclu.
    assert pair["numeric_budget_m2"] == pytest.approx(delta*2 + math.pi*delta**2, rel=1e-12, abs=0)


def test_public_coverage_projects_geographic_input_without_relabelling_sources():
    source = frame([box(X, Y, X+10, Y+10)]).to_crs(4326)
    before = source.copy(deep=True)
    assert check(source).ok
    assert source.crs.to_epsg() == 4326 and source.equals(before)


INVALID_GEOMETRIES = [
    pytest.param(None, "null_geometry", id="null"),
    pytest.param(Polygon(), "empty_geometry", id="empty"),
    pytest.param(Polygon([(X, Y), (X+1, Y+1), (X+1, Y), (X, Y+1), (X, Y)]), "invalid_geometry", id="bowtie"),
    pytest.param(Point(X, Y), "geometry_type", id="point"),
    pytest.param(Polygon([(X, Y), (X+1, Y), (math.inf, Y+1), (X, Y)]), "invalid_geometry", id="infinity"),
    pytest.param(Polygon([(X, Y), (X+1, Y), (math.nan, Y+1), (X, Y)]), "invalid_geometry", id="nan"),
    pytest.param(box(0, 0, 1e200, 1e200), "nonfinite_metrics", id="metric-overflow"),
]


@pytest.mark.parametrize("geometry,code", INVALID_GEOMETRIES)
@pytest.mark.parametrize("role", ["grid", "territory"])
def test_direct_coverage_calls_reject_unvalidated_geometry(geometry, code, role):
    valid = frame([box(X, Y, X+10, Y+10)])
    invalid = frame([geometry])
    report = check(invalid if role == "grid" else valid, invalid if role == "territory" else valid)
    assert not report.ok and code in error_codes(report)
    assert not any(i.code == "grid_overlap_numerical_residue" for i in report.issues)


@pytest.mark.parametrize("role", ["grid", "territory"])
def test_direct_coverage_calls_reject_empty_layer_and_missing_crs(role):
    valid = frame([box(X, Y, X+10, Y+10)])
    for invalid, code in [(frame([]), "empty_layer"), (valid.set_crs(None, allow_override=True), "missing_crs")]:
        report = check(invalid if role == "grid" else valid, invalid if role == "territory" else valid)
        assert not report.ok and code in error_codes(report)


@pytest.mark.parametrize("fault", ["delta-nan", "delta-inf", "delta-zero", "global-budget", "sum-overflow",
                                   "local-nan", "local-inf", "local-negative"])
def test_invalid_computed_budgets_never_accept_silently(monkeypatch, fault):
    grid = frame([box(X, Y, X+10, Y+10), box(X+9.999, Y, X+20, Y+10)])
    if fault.startswith("delta-"):
        monkeypatch.setattr(validation.math, "hypot", lambda *args: {"delta-nan": math.nan, "delta-inf": math.inf, "delta-zero": 0}[fault])
    elif fault == "global-budget":
        original = math.ulp
        monkeypatch.setattr(validation.math, "ulp", lambda value: math.inf if value < 1000 else original(value))
    elif fault == "sum-overflow":
        def overflow(values):
            raise OverflowError("Débordement simulé de l'accumulation")
        monkeypatch.setattr(validation.math, "fsum", overflow)
    else:
        monkeypatch.setattr(validation.math, "pi", {"local-nan": math.nan, "local-inf": math.inf, "local-negative": -1e300}[fault])
    report = check(grid, frame([box(X, Y, X+20, Y+10)]))
    assert "invalid_coverage_numeric" in error_codes(report)
    assert not any(i.code == "grid_overlap_numerical_residue" for i in report.issues)


@pytest.mark.parametrize("geometry", [Point(math.inf, 0), Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)])])
def test_invalid_overlay_geometry_is_not_ignored(monkeypatch, geometry):
    original = validation.union_all
    def invalid_union(values):
        invalid_union.calls += 1
        return geometry if invalid_union.calls == 1 else original(values)
    invalid_union.calls = 0
    monkeypatch.setattr(validation, "union_all", invalid_union)
    grid = frame([box(X, Y, X+10, Y+10)])
    assert "invalid_coverage_numeric" in error_codes(check(grid, grid))


@pytest.mark.parametrize("representation", ["geojson", "regenerated"])
def test_m1_grid_works_in_enjeux_and_conflict_aggregation(m1_grids, representation):
    grids, territory = m1_grids
    grid = grids[representation].copy()
    cell = grid.loc[~grid.is_boundary].geometry.iloc[0]
    center = cell.representative_point()
    sources = frame([box(center.x-1, center.y-1, center.x+1, center.y+1)])
    before = grid.copy(deep=True)
    enjeux = compute_enjeux(grid, territory, sources, sources)
    assert enjeux.report.ok and len(enjeux.cells) == 43
    assert enjeux.cells.enj_01_pct.isna().all()  # aucune complétude inventée
    assert enjeux.cells.enj_02_presence.fillna(False).any()
    detection = detect_route_corridor_conflicts(
        frame([LineString([(center.x-1, center.y), (center.x+1, center.y)])], rid=["SYNTHETIC-R"]),
        frame([LineString([(center.x, center.y-1), (center.x, center.y+1)])], cid=["SYNTHETIC-C"]),
        territory, route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"),
        method_version="SYNTHETIC-GRID-REGRESSION",
    )
    result = aggregate_conflicts(grid, territory, detection)
    assert result.report.ok and len(result.cells) == 43 and len(result.events) == 1
    assert result.summary["distinct_events_observed"] == result.links.canonical_owner.sum() == 1
    assert result.cells.nb_evenements.isna().all()
    assert result.events.statut.tolist() == ["croisement_detecte"]
    assert grid.equals(before)


def test_initial_m1_configurations_are_accepted(tmp_path):
    # Contrats documentés M1, indépendants des fichiers de travail non suivis docs/.
    enjeux = {"grid": {"id_column": "maille_id", "expected_crs": "EPSG:2154"},
              "territory": {"expected_crs": "EPSG:2154"},
              "reservoirs": {"coverage": {"status": "unknown", "source_id": "TVB_RES_NORM"}},
              "corridors": {"coverage": {"status": "unknown", "source_id": "TVB_COR_BN"}}}
    conflicts = {"grid": enjeux["grid"], "territory": enjeux["territory"],
                 "routes": {"id_column": "route_id", "category_column": "categorie", "coverage": {"status": "unknown"}},
                 "corridors": {"id_column": "objet_id", "category_column": "classe_corridor", "coverage": {"status": "unknown"}}}
    for name, config, loader in [("enjeux", enjeux, load_enjeux_config), ("conflits", conflicts, load_conflicts_config)]:
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(config))
        assert loader(path) == config
