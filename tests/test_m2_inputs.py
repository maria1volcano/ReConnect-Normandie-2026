"""Contrôles techniques sur des fichiers temporaires et géométries SYNTHÉTIQUES."""

import geopandas as gpd
import pytest
from shapely.geometry import LineString, Point, Polygon, box

from analysis.validate_inputs import (
    LayerSpec, POLYGONS, SpatialExpectation, ValidationReport, read_layer,
    validate_geodataframe, validate_spatial_coverage, validate_spatial_plausibility,
)

GRID = LayerSpec("grid", POLYGONS, ("maille_id",), ("maille_id",))
CELL = box(500_000, 6_900_000, 501_000, 6_901_000)


def frame(geometries=None, **columns):
    return gpd.GeoDataFrame(columns, geometry=[CELL] if geometries is None else geometries, crs=2154)


def codes(report):
    return {issue.code for issue in report.issues if issue.severity == "error"}


def test_valid_grid_does_not_mutate_input():
    source = frame(maille_id=["SYNTHETIC-H1"])
    original = source.copy()
    report = validate_geodataframe(source, GRID)
    assert report.ok
    assert source.equals(original)
    assert report.as_dict()["errors"] == []


@pytest.mark.parametrize("values, expected", [
    ({}, "missing_column"),
    ({"maille_id": [None]}, "null_attribute"),
    ({"maille_id": ["H1", "H1"]}, "duplicate_id"),
])
def test_required_unique_ids(values, expected):
    geometries = [CELL] * (len(values["maille_id"]) if values else 1)
    assert expected in codes(validate_geodataframe(frame(geometries, **values), GRID))


def test_missing_crs_is_blocking():
    source = gpd.GeoDataFrame({"maille_id": ["H1"]}, geometry=[CELL])
    assert "missing_crs" in codes(validate_geodataframe(source, GRID))


def test_wrong_crs_against_explicit_contract():
    report = validate_geodataframe(frame(), LayerSpec("source", POLYGONS, expected_crs="EPSG:4326"))
    assert "unexpected_crs" in codes(report)


def test_incorrect_geographic_label_cannot_be_projected():
    mislabeled = frame().set_crs(4326, allow_override=True)
    assert "reprojection_failed" in codes(validate_geodataframe(mislabeled, LayerSpec("source", POLYGONS)))


def test_legitimate_other_crs_can_be_reprojected():
    geographic = frame(maille_id=["H1"]).to_crs(4326)
    assert validate_geodataframe(geographic, GRID).ok
    assert geographic.crs.to_epsg() == 4326


@pytest.mark.parametrize("geometry, expected", [
    (None, "null_geometry"),
    (Polygon(), "empty_geometry"),
    (Polygon([(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]), "invalid_geometry"),
    (Point(500_000, 6_900_000), "geometry_type"),
    (LineString([(500_000, 6_900_000), (501_000, 6_901_000)]), "geometry_type"),
])
def test_unusable_geometry(geometry, expected):
    report = validate_geodataframe(frame([geometry], maille_id=["H1"]), GRID)
    assert expected in codes(report)
    if expected == "invalid_geometry":
        issue = next(i for i in report.issues if i.code == expected)
        assert issue.details["examples"]


def test_empty_observation_layer_allowed_but_not_grid():
    empty = frame([], maille_id=[])
    assert validate_geodataframe(empty, LayerSpec("reservoirs", POLYGONS, allow_empty=True)).ok
    assert "empty_layer" in codes(validate_geodataframe(empty, GRID))


def test_missing_input_file(tmp_path):
    report = ValidationReport()
    assert read_layer(tmp_path / "ABSENT_SYNTHETIC.gpkg", GRID, report) is None
    assert "missing_file" in codes(report)


def test_unreadable_file(tmp_path):
    path = tmp_path / "BROKEN_SYNTHETIC.gpkg"
    path.write_text("not a GeoPackage", encoding="utf-8")
    report = ValidationReport()
    assert read_layer(path, GRID, report) is None
    assert "unreadable_file" in codes(report)


@pytest.mark.parametrize("suffix", [".gpkg", ".geojson"])
def test_read_supported_formats(tmp_path, suffix):
    path = tmp_path / f"SYNTHETIC_grid{suffix}"
    frame(maille_id=["H1"]).to_file(path, driver="GPKG" if suffix == ".gpkg" else "GeoJSON", index=False)
    report = ValidationReport()
    loaded = read_layer(path, GRID, report)
    assert report.ok
    assert loaded.maille_id.tolist() == ["H1"]


def test_multilayer_requires_explicit_selection(tmp_path):
    path = tmp_path / "SYNTHETIC_multi.gpkg"
    source = frame(maille_id=["H1"])
    source.to_file(path, layer="a", driver="GPKG", index=False)
    source.to_file(path, layer="b", driver="GPKG", index=False)
    report = ValidationReport()
    assert read_layer(path, GRID, report) is None
    assert "ambiguous_layer" in codes(report)
    report = ValidationReport()
    assert read_layer(path, GRID, report, layer="b") is not None
    assert report.ok
    report = ValidationReport()
    assert read_layer(path, GRID, report, layer="absent") is None
    assert "missing_layer" in codes(report)


def test_grid_coverage_gap_is_blocking():
    report = ValidationReport()
    validate_spatial_coverage(frame(), frame([box(500_000, 6_900_000, 502_000, 6_901_000)]), report)
    assert "grid_coverage_gap" in codes(report)


def test_duplicated_cell_geometry_is_blocking_even_with_distinct_ids():
    report = ValidationReport()
    validate_spatial_coverage(frame([CELL, CELL], maille_id=["H1", "H2"]), frame(), report)
    assert "grid_overlap" in codes(report)


def test_partial_cell_overlap_is_blocking():
    second = box(500_500, 6_900_000, 501_500, 6_901_000)
    report = ValidationReport()
    validate_spatial_coverage(frame([CELL, second]), frame([CELL, second]), report)
    assert "grid_overlap" in codes(report)


def test_adjacent_cell_boundary_is_not_overlap():
    second = box(501_000, 6_900_000, 502_000, 6_901_000)
    report = ValidationReport()
    validate_spatial_coverage(frame([CELL, second]), frame([CELL, second]), report)
    assert report.ok


def test_internal_grid_hole_is_blocking():
    hole = box(500_400, 6_900_400, 500_600, 6_900_600)
    report = ValidationReport()
    validate_spatial_coverage(frame([CELL.difference(hole)]), frame(), report)
    assert "grid_coverage_gap" in codes(report)


def test_finite_but_wrong_crs_is_detected_by_official_extent():
    # Degrés étiquetés L93 : transformation identité finie mais lieu incohérent.
    wrong = frame([box(0, 49, 0.01, 49.01)])
    assert validate_geodataframe(wrong, LayerSpec("source", POLYGONS)).ok
    report = ValidationReport()
    expectation = SpatialExpectation(frame(), "Emprise officielle SYNTHÉTIQUE", "M1 SYNTHÉTIQUE")
    validate_spatial_plausibility({"reservoirs": wrong, "territory": frame()}, frame(), report, expectation)
    assert "outside_plausible_extent" in codes(report)
    assert any(i.code == "layer_disjoint_from_territory" for i in report.issues)


def test_plausible_extent_checks_each_feature_not_only_layer_overlap():
    source = frame([CELL, box(1e9, 1e9, 1e9 + 10, 1e9 + 10)])
    report = ValidationReport()
    expectation = SpatialExpectation(frame(), "SYNTHÉTIQUE", "M1 SYNTHÉTIQUE")
    validate_spatial_plausibility({"reservoirs": source}, frame(), report, expectation)
    assert "outside_plausible_extent" in codes(report)


def test_plausible_extent_margin_is_configurable_and_traced():
    source = frame([CELL.buffer(2)])
    report = ValidationReport()
    expectation = SpatialExpectation(frame(), "Marge SYNTHÉTIQUE documentée", "M1 SYNTHÉTIQUE", margin_m=3)
    validate_spatial_plausibility({"reservoirs": source}, frame(), report, expectation)
    assert report.ok
    assert report.layers["plausible_extent"]["margin_m"] == 3


def test_plausible_extent_requires_reference_and_validator():
    report = ValidationReport()
    validate_spatial_plausibility({"territory": frame()}, frame(), report, SpatialExpectation(frame(), "", ""))
    assert "unvalidated_plausible_extent" in codes(report)
