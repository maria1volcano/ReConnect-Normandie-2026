"""Tests scientifiques SYNTHÉTIQUES : aucun diagnostic réel sur la Normandie."""

import json
from dataclasses import replace
import math

import geopandas as gpd
import pandas as pd
import pytest
from shapely.affinity import translate
from shapely.errors import GEOSException
from shapely.geometry import LineString, Point, Polygon, box

from analysis.indicateurs_enjeux import (
    CorridorSensitivity, CoverageEvidence, SubframeMapping, _checked_proportion,
    compute_enjeux, territory_geometry_sha256,
)
from analysis import run_enjeux
from analysis.validate_inputs import AREA_TOLERANCE_M2, InputValidationError, ValidationReport

X, Y = 500_000, 6_900_000
CELL = box(X, Y, X + 1000, Y + 1000)


def frame(geometries, **columns):
    return gpd.GeoDataFrame(columns, geometry=geometries, crs=2154)


def coverage_metadata(theme, territory=None):
    return {
        "status": "validated", "source_id": f"SYNTHETIC-{theme}",
        "producer": "PRODUCTEUR SYNTHÉTIQUE", "vintage": "MILLÉSIME SYNTHÉTIQUE",
        "validity_extent": "EMPRISE SYNTHÉTIQUE", "theme": theme,
        "document_reference": "DOCUMENT DE TEST SYNTHÉTIQUE",
        "validated_by": "M1/M2 SYNTHÉTIQUES", "validated_at": "2026-10-30T12:00:00+01:00",
        "territory_sha256": territory_geometry_sha256(frame([CELL]) if territory is None else territory),
    }


def validated_coverage(theme, territory=None, footprint=None):
    return CoverageEvidence(confirmed=footprint is None, footprint=footprint,
                            **coverage_metadata(theme, territory))


CONFIRMED = validated_coverage("reservoirs")
CORRIDOR_CONFIRMED = validated_coverage("corridors")


def calculate(reservoirs=None, corridors=None, territory=None, grid=None, **kwargs):
    return compute_enjeux(
        frame([CELL], maille_id=["SYNTHETIC-H1"]) if grid is None else grid,
        frame([CELL]) if territory is None else territory,
        frame([] if reservoirs is None else reservoirs),
        frame([] if corridors is None else corridors),
        **kwargs,
    )


def test_one_square_kilometre_25_percent():
    reservoir = box(X, Y, X + 500, Y + 500)
    result = calculate([reservoir], reservoir_coverage=CONFIRMED)
    row = result.cells.iloc[0]
    assert row.study_area_m2 == pytest.approx(1_000_000)
    assert row.reservoir_observed_area_m2 == pytest.approx(250_000)
    assert row.enj_01_pct == pytest.approx(25)
    assert result.cells.crs.to_epsg() == 2154


def test_overlapping_reservoirs_are_unioned():
    reservoirs = [box(X, Y, X + 500, Y + 1000), box(X + 250, Y, X + 750, Y + 1000)]
    result = calculate(reservoirs, reservoir_coverage=CONFIRMED)
    assert result.cells.enj_01_pct.iloc[0] == pytest.approx(75)


def test_complete_reservoir_cover_is_100_percent():
    result = calculate([CELL, CELL], reservoir_coverage=CONFIRMED)
    assert result.cells.enj_01_pct.iloc[0] == pytest.approx(100)


def test_confirmed_absences_can_be_zero_and_false():
    result = calculate(reservoir_coverage=CONFIRMED, corridor_coverage=CORRIDOR_CONFIRMED)
    assert result.cells.enj_01_pct.iloc[0] == 0
    assert not result.cells.enj_02_presence.iloc[0]


def test_unknown_coverage_never_becomes_zero():
    result = calculate()
    assert pd.isna(result.cells.enj_01_pct.iloc[0])
    assert pd.isna(result.cells.enj_02_presence.iloc[0])
    assert result.cells.reservoir_observed_area_m2.iloc[0] == 0  # observation uniquement


def test_positive_observation_with_unknown_coverage():
    result = calculate([CELL], [LineString([(X, Y + 500), (X + 1000, Y + 500)])])
    assert pd.isna(result.cells.enj_01_pct.iloc[0])
    assert result.cells.reservoir_observed_area_m2.iloc[0] == 1_000_000
    assert result.cells.enj_02_presence.iloc[0]


def test_border_cell_uses_actual_territory_area():
    result = calculate(
        [box(X, Y, X + 250, Y + 1000)],
        territory=frame([box(X, Y, X + 500, Y + 1000)]),
        reservoir_coverage=validated_coverage("reservoirs", frame([box(X, Y, X + 500, Y + 1000)])),
    )
    row = result.cells.iloc[0]
    assert row.study_area_m2 == 500_000
    assert row.enj_01_pct == 50
    assert row.geometry.area == 500_000


def test_territory_holes_are_excluded():
    territory = CELL.difference(box(X + 250, Y + 250, X + 750, Y + 750))
    result = calculate([box(X + 250, Y + 250, X + 750, Y + 750)],
                       territory=frame([territory]), reservoir_coverage=validated_coverage("reservoirs", frame([territory])))
    assert result.cells.study_area_m2.iloc[0] == 750_000
    assert result.cells.enj_01_pct.iloc[0] == 0


def test_clipping_discards_isolated_boundary_contact():
    # T coupe une partie de H et touche ailleurs le bord de H : l'intersection
    # brute est une GeometryCollection contenant un polygone et une ligne.
    territory = frame([
        box(X, Y, X + 500, Y + 500),
        box(X + 800, Y + 1000, X + 900, Y + 1100),
    ])
    neighbor = box(X, Y + 1000, X + 1000, Y + 2000)
    result = calculate(
        corridors=[LineString([(X, Y + 250), (X + 500, Y + 250)])],
        territory=territory, grid=frame([CELL, neighbor], maille_id=["H1", "H2"]),
    )
    assert result.cells.iloc[0].geometry.geom_type == "Polygon"
    assert result.cells.corridor_observed_length_m.iloc[0] == 500


def test_spatial_completeness_is_evaluated_per_clipped_cell():
    second = box(X + 1000, Y, X + 2000, Y + 1000)
    coverage = validated_coverage("reservoirs", footprint=frame([CELL]))
    result = calculate(grid=frame([CELL, second], maille_id=["H1", "H2"]),
                       territory=frame([CELL, second]), reservoir_coverage=coverage)
    assert result.cells.enj_01_pct.iloc[0] == 0
    assert pd.isna(result.cells.enj_01_pct.iloc[1])
    clipped = calculate(territory=frame([box(X, Y, X + 500, Y + 1000)]), reservoir_coverage=coverage)
    assert clipped.cells.enj_01_pct.iloc[0] == 0


def test_partial_coverage_does_not_extrapolate():
    footprint = frame([box(X, Y, X + 500, Y + 1000)])
    result = calculate(reservoir_coverage=validated_coverage("reservoirs", footprint=footprint),
                       corridor_coverage=validated_coverage("corridors", footprint=footprint))
    assert pd.isna(result.cells.enj_01_pct.iloc[0])
    assert pd.isna(result.cells.enj_02_presence.iloc[0])


def test_linear_corridor_crosses_positive_interior_length():
    line = LineString([(X - 100, Y + 500), (X + 1100, Y + 500)])
    result = calculate(corridors=[line, line])
    assert result.cells.enj_02_presence.iloc[0]
    assert result.cells.corridor_observed_length_m.iloc[0] == pytest.approx(1000)
    assert result.cells.corridor_observed_area_m2.iloc[0] == 0


@pytest.mark.parametrize("corridor", [
    LineString([(X - 100, Y + 500), (X, Y + 500)]),  # contact ponctuel
    LineString([(X, Y), (X + 1000, Y)]),  # longueur positive sur la frontière
    box(X - 100, Y, X, Y + 1000),  # polygone touchant seulement le bord
])
def test_boundary_only_corridor_is_not_presence(corridor):
    result = calculate(corridors=[corridor], corridor_coverage=CORRIDOR_CONFIRMED)
    assert not result.cells.enj_02_presence.iloc[0]
    assert result.cells.corridor_observed_length_m.iloc[0] == 0
    assert result.cells.corridor_observed_area_m2.iloc[0] == 0


def test_mixed_corridor_dimensions_are_kept_separate():
    corridors = [LineString([(X, Y + 500), (X + 1000, Y + 500)]), box(X, Y, X + 500, Y + 500)]
    result = calculate(corridors=corridors)
    assert result.cells.corridor_observed_length_m.iloc[0] == 1000
    assert result.cells.corridor_observed_area_m2.iloc[0] == 250_000


def test_cell_outside_territory_has_null_indicators_and_geometry():
    other = box(X + 1000, Y, X + 2000, Y + 1000)
    result = calculate(grid=frame([CELL, other], maille_id=["H1", "H2"]),
                       reservoir_coverage=CONFIRMED, corridor_coverage=CORRIDOR_CONFIRMED)
    row = result.cells.iloc[1]
    assert pd.isna(row.enj_01_pct) and pd.isna(row.enj_02_presence)
    assert row.geometry is None
    assert row.enj_01_status == "outside_territory"


def test_validated_coverage_requires_metadata():
    with pytest.raises(InputValidationError, match="Métadonnées"):
        calculate(reservoir_coverage=CoverageEvidence(confirmed=True, status="validated"))


def test_invalid_geometry_stops_calculation():
    invalid = Polygon([(X, Y), (X + 1000, Y + 1000), (X + 1000, Y), (X, Y + 1000), (X, Y)])
    with pytest.raises(InputValidationError, match="invalides"):
        calculate([invalid])


def test_documented_subframes_are_preserved_without_summing_them():
    reservoirs = frame([CELL, CELL], code_source=["A", "B"])
    grid = frame([CELL], maille_id=["H1"])
    result = compute_enjeux(
        grid, frame([CELL]), reservoirs, frame([]), reservoir_coverage=CONFIRMED,
        reservoir_subframes=SubframeMapping("code_source", {"A": "Type A SYNTHÉTIQUE", "B": "Type B SYNTHÉTIQUE"}),
    )
    assert result.cells.enj_01_pct.iloc[0] == 100
    assert result.subframes.source_value.tolist() == ["A", "B"]
    assert result.subframes.reservoir_observed_area_m2.tolist() == [1_000_000, 1_000_000]


def test_undocumented_subframe_is_blocking():
    with pytest.raises(InputValidationError, match="signification"):
        compute_enjeux(frame([CELL], maille_id=["H1"]), frame([CELL]),
                       frame([CELL], code_source=["X"]), frame([]),
                       reservoir_subframes=SubframeMapping("code_source", {"A": "Type A SYNTHÉTIQUE"}))


def synthetic_pipeline(tmp_path, monkeypatch):
    """Tous les fichiers sont créés sous tmp_path, jamais dans les vraies données."""
    monkeypatch.setattr(run_enjeux, "PROJECT_ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    processed = tmp_path / "data/processed"
    processed.mkdir(parents=True)
    sources = {
        "grid": frame([CELL], source_id=["SYNTHETIC-H1"]),
        "territory": frame([CELL]),
        "reservoirs": frame([box(X, Y, X + 500, Y + 500)], code_source=["A"]),
        "corridors": frame([LineString([(X, Y + 500), (X + 1000, Y + 500)])]),
    }
    arguments = []
    for name, source in sources.items():
        path = processed / f"SYNTHETIC_{name}.gpkg"
        source.to_file(path, driver="GPKG", index=False)
        arguments.extend([f"--{name}", str(path)])
    config = tmp_path / "synthetic_config.json"
    config.write_text(json.dumps({
        "grid": {"id_column": "source_id", "expected_crs": "EPSG:2154"},
        "reservoirs": {"subframes": {"column": "code_source", "meanings": {"A": "Type A SYNTHÉTIQUE"}}},
    }), encoding="utf-8")
    arguments.extend(["--config", str(config)])
    return arguments, processed


def test_cli_roundtrip_report_and_source_preservation(tmp_path, monkeypatch):
    arguments, processed = synthetic_pipeline(tmp_path, monkeypatch)
    hashes = {p: run_enjeux._sha256(p) for p in processed.iterdir()}
    arguments.extend(["--reservoir-coverage-confirmed", "--reservoir-coverage-provenance", "Justification SYNTHÉTIQUE"])
    config_path = tmp_path / "synthetic_config.json"
    config = json.loads(config_path.read_text())
    config["reservoirs"]["coverage"] = coverage_metadata("reservoirs")
    config_path.write_text(json.dumps(config), encoding="utf-8")
    assert run_enjeux.main(arguments) == 0
    output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
    cells = gpd.read_file(output, layer="indicateurs_enjeux")
    assert cells.enj_01_pct.iloc[0] == 25
    assert cells.enj_02_presence.iloc[0]
    assert not gpd.read_file(output, layer="observations_sous_trames").empty
    report = json.loads(output.with_suffix(".validation.json").read_text())
    assert report["ok"] and report["run"]["source_sha256"]
    assert report["run"]["output_sha256"] == run_enjeux._sha256(output)
    assert run_enjeux.verify_artifact_pair(output, output.with_suffix(".validation.json"))["ok"]
    assert all(report["run"][key] is None for key in ("grid_version", "method_version", "dataset_version"))
    assert {p: run_enjeux._sha256(p) for p in processed.iterdir()} == hashes
    assert not (tmp_path / "data/public").exists()
    assert run_enjeux.main(arguments) == 2  # refuse tout écrasement


def test_cli_serializes_unknown_as_null(tmp_path, monkeypatch):
    arguments, processed = synthetic_pipeline(tmp_path, monkeypatch)
    outside_corridors = processed / "SYNTHETIC_corridors_outside.gpkg"
    frame([LineString([(X + 2000, Y), (X + 3000, Y)])]).to_file(
        outside_corridors, driver="GPKG", index=False,
    )
    arguments[arguments.index("--corridors") + 1] = str(outside_corridors)
    assert run_enjeux.main(arguments) == 0
    cells = gpd.read_file(tmp_path / "data/derived/indicateurs_enjeux.gpkg", layer="indicateurs_enjeux")
    assert pd.isna(cells.enj_01_pct.iloc[0])
    assert pd.isna(cells.enj_02_presence.iloc[0])


def test_cli_missing_file_reports_error_without_geopackage(tmp_path, monkeypatch):
    arguments, processed = synthetic_pipeline(tmp_path, monkeypatch)
    arguments[1] = str(processed / "ABSENT_SYNTHETIC.gpkg")
    assert run_enjeux.main(arguments) == 2
    output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
    assert not output.exists()
    report = json.loads(output.with_suffix(".validation.json").read_text())
    assert not report["ok"]
    assert "missing_file" in {item["code"] for item in report["errors"]}


def test_cli_refuses_public_output(tmp_path, monkeypatch):
    arguments, _ = synthetic_pipeline(tmp_path, monkeypatch)
    arguments.extend(["--output", str(tmp_path / "data/public/forbidden.gpkg")])
    assert run_enjeux.main(arguments) == 2
    assert not (tmp_path / "data/public").exists()


def hexagons():
    """Deux hexagones réguliers SYNTHÉTIQUES de 1 km², avec sommets partagés exacts."""
    radius = math.sqrt(2_000_000 / (3 * math.sqrt(3)))
    half_width = math.sqrt(3) * radius / 2
    shared = X + half_width
    first = Polygon([
        (X, Y + radius), (shared, Y + radius / 2), (shared, Y - radius / 2),
        (X, Y - radius), (X - half_width, Y - radius / 2), (X - half_width, Y + radius / 2),
    ])
    center = X + 2 * half_width
    second = Polygon([
        (center, Y + radius), (X + 3 * half_width, Y + radius / 2),
        (X + 3 * half_width, Y - radius / 2), (center, Y - radius),
        (shared, Y - radius / 2), (shared, Y + radius / 2),
    ])
    return first, second


class TestExactHexagonGeometry:
    """Calculs exacts par construction, aux arrondis arithmétiques près."""

    def test_regular_one_km2_hexagon_quarter_reservoir(self):
        first, _ = hexagons()
        territory = frame([first])
        result = calculate(
            reservoirs=[box(X - 2000, Y - 2000, X, Y)],
            grid=frame([first], maille_id=["SYNTHETIC-HEX1"]), territory=territory,
            reservoir_coverage=validated_coverage("reservoirs", territory),
        )
        assert first.area == pytest.approx(1_000_000, abs=1e-5)
        assert result.cells.enj_01_pct.iloc[0] == pytest.approx(25, abs=1e-8)

    def test_adjacent_hexagons_have_no_overlap_and_measure_crossing_line(self):
        first, second = hexagons()
        line = LineString([(first.bounds[0], Y), (second.bounds[2], Y)])
        result = calculate(
            corridors=[line], grid=frame([first, second], maille_id=["HEX1", "HEX2"]),
            territory=frame([first, second]),
        )
        assert result.report.ok
        assert first.intersection(second).area == 0
        assert result.cells.enj_02_presence.all()
        assert result.cells.corridor_observed_length_m.sum() == pytest.approx(line.length, abs=1e-7)

    def test_areal_corridor_overlaps_are_unioned(self):
        result = calculate(corridors=[box(X, Y, X + 500, Y + 1000),
                                      box(X + 250, Y, X + 750, Y + 1000)])
        assert result.cells.corridor_observed_area_m2.iloc[0] == 750_000
        assert result.cells.corridor_observed_length_m.iloc[0] == 0

    def test_corridor_on_shared_hexagon_edge_is_not_interior_presence(self):
        first, second = hexagons()
        edge = first.intersection(second)
        assert edge.geom_type == "LineString" and edge.length > 0
        territory = frame([first, second])
        result = calculate(
            corridors=[edge], grid=frame([first, second], maille_id=["HEX1", "HEX2"]), territory=territory,
            corridor_coverage=validated_coverage("corridors", territory),
        )
        assert not result.cells.enj_02_presence.any()
        assert result.cells.corridor_observed_length_m.sum() == 0

    @pytest.mark.parametrize("kind", ["duplicate", "overlap", "shift", "hole"])
    def test_invalid_hexagon_grid_is_blocking(self, kind):
        first, second = hexagons()
        territory = frame([first, second])
        if kind == "duplicate":
            cells = [first, second, first]
        elif kind == "overlap":
            cells = [first, translate(second, xoff=-1)]
        elif kind == "shift":
            cells = [translate(first, xoff=100), translate(second, xoff=100)]
        else:
            cells = [first.difference(box(X - 10, Y - 10, X + 10, Y + 10)), second]
        with pytest.raises(InputValidationError) as captured:
            calculate(grid=frame(cells, maille_id=[f"HEX{i}" for i in range(len(cells))]), territory=territory)
        errors = {i.code for i in captured.value.report.issues if i.severity == "error"}
        assert errors & {"grid_overlap", "grid_coverage_gap"}


class TestCompletenessStates:
    def test_invalid_validation_date_is_blocking(self):
        with pytest.raises(InputValidationError, match="ISO 8601"):
            calculate(reservoir_coverage=replace(CONFIRMED, validated_at="DATE SYNTHÉTIQUE INVALIDE"))

    def test_validation_requires_explicit_geographic_scope(self):
        with pytest.raises(InputValidationError, match="portée globale"):
            calculate(reservoir_coverage=replace(CONFIRMED, confirmed=False))

    @pytest.mark.parametrize("evidence", [
        CoverageEvidence(),
        CoverageEvidence(confirmed=True, provenance="Texte SYNTHÉTIQUE seul"),
        CoverageEvidence(footprint=frame([CELL]), status="declared"),
    ])
    def test_unknown_or_declared_completeness_never_confirms_zero(self, evidence):
        result = calculate(reservoir_coverage=evidence, corridor_coverage=evidence)
        assert pd.isna(result.cells.enj_01_pct.iloc[0])
        assert pd.isna(result.cells.enj_02_presence.iloc[0])
        assert not result.cells.reservoir_coverage_confirmed.iloc[0]

    def test_declared_completeness_preserves_positive_observations(self):
        declared = CoverageEvidence(confirmed=True, provenance="Déclaration SYNTHÉTIQUE")
        result = calculate([CELL], [LineString([(X, Y + 500), (X + 1000, Y + 500)])],
                           reservoir_coverage=declared, corridor_coverage=declared)
        assert pd.isna(result.cells.enj_01_pct.iloc[0])
        assert result.cells.reservoir_observed_area_m2.iloc[0] == 1_000_000
        assert result.cells.enj_02_presence.iloc[0]

    @pytest.mark.parametrize("field", [
        "source_id", "producer", "vintage", "validity_extent", "theme",
        "document_reference", "validated_by", "validated_at",
    ])
    def test_each_validation_metadata_field_is_required(self, field):
        with pytest.raises(InputValidationError) as captured:
            calculate(reservoir_coverage=replace(CONFIRMED, **{field: None}))
        assert any(i.code == "incomplete_validated_coverage" for i in captured.value.report.issues)

    def test_validation_for_another_theme_is_blocking(self):
        with pytest.raises(InputValidationError, match="thème"):
            calculate(reservoir_coverage=CORRIDOR_CONFIRMED)

    def test_global_validation_cannot_be_reused_for_another_territory(self):
        territory = frame([box(X, Y, X + 500, Y + 1000)])
        with pytest.raises(InputValidationError, match="empreinte"):
            calculate(territory=territory, reservoir_coverage=CONFIRMED)

    def test_validated_footprint_can_be_partial_and_preserves_observations(self):
        partial = frame([box(X, Y, X + 500, Y + 1000)])
        result = calculate([CELL], reservoir_coverage=validated_coverage("reservoirs", footprint=partial))
        assert pd.isna(result.cells.enj_01_pct.iloc[0])
        assert result.cells.reservoir_observed_area_m2.iloc[0] == 1_000_000


class TestNumericalRobustness:
    """Tolérances d'arithmétique, indépendantes de toute précision cartographique."""

    @pytest.mark.parametrize("observed", [-1.0, 1_000_001.0, float("nan"), float("inf")])
    def test_large_or_nonfinite_area_errors_are_not_clamped(self, observed):
        report = ValidationReport()
        assert _checked_proportion(observed, 1_000_000, report, "SYNTHETIC-H1") is None
        assert not report.ok

    @pytest.mark.parametrize("observed, expected", [
        (-AREA_TOLERANCE_M2 / 2, 0),
        (1_000_000 + AREA_TOLERANCE_M2 / 2, 100),
    ])
    def test_only_roundoff_corrections_are_allowed_and_reported(self, observed, expected):
        report = ValidationReport()
        assert _checked_proportion(observed, 1_000_000, report, "SYNTHETIC-H1") == expected
        assert report.ok
        assert any(i.code == "numeric_area_adjustment" for i in report.issues)

    @pytest.mark.parametrize("offset", [-1e-10, 1e-10])
    def test_sub_tolerance_grid_residue_is_accepted(self, offset):
        second = box(X + 1000, Y, X + 2000, Y + 1000)
        result = calculate(grid=frame([CELL, translate(second, xoff=offset)], maille_id=["H1", "H2"]),
                           territory=frame([CELL, second]))
        assert result.report.ok

    @pytest.mark.parametrize("corridor", [
        box(X + 100, Y + 100, X + 100 + 1e-9, Y + 200),
        LineString([(X + 100, Y + 100), (X + 100 + 5e-10, Y + 100)]),
    ])
    def test_tiny_positive_corridors_are_flagged_and_kept(self, corridor):
        result = calculate(corridors=[corridor])
        assert result.cells.enj_02_presence.iloc[0]
        assert result.cells.corridor_numerical_residue.iloc[0]
        assert any(i.code == "tiny_corridor_intersection" for i in result.report.issues)


class TestCartographicSensitivity:
    """Scénarios documentés de précision, séparés des valeurs brutes de référence."""

    def test_boundary_near_corridor_has_sensitive_presence_without_changing_reference(self):
        line = LineString([(X + 0.25, Y + 250), (X + 0.25, Y + 750)])
        raw = calculate(corridors=[line])
        scenario = calculate(corridors=[line], corridor_sensitivity=CorridorSensitivity(1, "Précision SYNTHÉTIQUE de 1 m"))
        row = scenario.cells.iloc[0]
        assert row.corridor_observed_length_m == raw.cells.corridor_observed_length_m.iloc[0] == 500
        assert row.enj_02_presence and row.corridor_presence_sensitive
        assert row.corridor_sensitivity_length_min_m == 0
        assert row.corridor_sensitivity_length_max_m == 500

    def test_central_corridor_presence_remains_positive(self):
        line = LineString([(X + 500, Y), (X + 500, Y + 1000)])
        result = calculate(corridors=[line], corridor_sensitivity=CorridorSensitivity(1, "SYNTHÉTIQUE"))
        assert not result.cells.corridor_presence_sensitive.iloc[0]
        assert result.cells.corridor_sensitivity_length_min_m.iloc[0] == pytest.approx(998)

    def test_near_miss_is_flagged_without_inventing_an_observation(self):
        neighbor = box(X - 1000, Y, X, Y + 1000)
        line = LineString([(X - 0.25, Y + 250), (X - 0.25, Y + 750)])
        result = calculate(corridors=[line], grid=frame([CELL, neighbor], maille_id=["H1", "H2"]),
                           territory=frame([CELL, neighbor]),
                           corridor_sensitivity=CorridorSensitivity(1, "SYNTHÉTIQUE"))
        row = result.cells.iloc[0]
        assert row.corridor_observed_length_m == 0
        assert pd.isna(row.enj_02_presence)
        assert row.corridor_presence_sensitive
        assert row.corridor_sensitivity_length_max_m == 500

    def test_missing_precision_does_not_create_sensitivity_scenario(self):
        assert pd.isna(calculate().cells.corridor_presence_sensitive.iloc[0])

    @pytest.mark.parametrize("distance, reference", [(0, "SYNTHÉTIQUE"), (-1, "SYNTHÉTIQUE"), (1, "")])
    def test_undocumented_or_invalid_precision_is_rejected(self, distance, reference):
        with pytest.raises(InputValidationError, match="précision documentée"):
            calculate(corridor_sensitivity=CorridorSensitivity(distance, reference))

    def test_point_corridor_is_identified_as_distinct_business_case(self):
        with pytest.raises(InputValidationError) as captured:
            calculate(corridors=[Point(X + 500, Y + 500)])
        assert any(i.code == "point_corridor_business_case" for i in captured.value.report.issues)


class TestExportIntegrity:
    @pytest.mark.parametrize("scenario", ["complete", "partial", "wrong_crs_label"])
    def test_cli_full_spatial_coverage_and_sensitivity_config(self, tmp_path, monkeypatch, scenario):
        arguments, processed = synthetic_pipeline(tmp_path, monkeypatch)
        plausible_path = processed / "SYNTHETIC_plausible.gpkg"
        frame([CELL.buffer(10)]).to_file(plausible_path, driver="GPKG", index=False)
        coverage_path = processed / "SYNTHETIC_completeness.gpkg"
        footprint = CELL if scenario != "partial" else box(X, Y, X + 500, Y + 1000)
        frame([footprint]).to_file(coverage_path, driver="GPKG", index=False)
        arguments.extend(["--reservoir-coverage", str(coverage_path)])
        config_path = tmp_path / "synthetic_config.json"
        config = json.loads(config_path.read_text())
        config["reservoirs"]["coverage"] = coverage_metadata("reservoirs")
        config["spatial"] = {"plausible_extent": str(plausible_path),
                             "reference": "Emprise officielle SYNTHÉTIQUE", "validated_by": "M1 SYNTHÉTIQUE"}
        config["corridors"] = {"sensitivity": {"distance_m": 1, "reference": "Précision SYNTHÉTIQUE 1 m"}}
        config_path.write_text(json.dumps(config), encoding="utf-8")
        if scenario == "wrong_crs_label":
            path = processed / "SYNTHETIC_wrong_label.gpkg"
            frame([box(0, 49, 0.01, 49.01)], code_source=["A"]).to_file(path, driver="GPKG", index=False)
            arguments[arguments.index("--reservoirs") + 1] = str(path)
        code = run_enjeux.main(arguments)
        output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
        report_path = output.with_suffix(".validation.json")
        if scenario == "wrong_crs_label":
            assert code == 2 and not output.exists()
            report = json.loads(report_path.read_text())
            assert "outside_plausible_extent" in {i["code"] for i in report["errors"]}
        else:
            assert code == 0
            report = run_enjeux.verify_artifact_pair(output, report_path)
            assert report["layers"]["plausible_extent"]["reference"] == "Emprise officielle SYNTHÉTIQUE"
            assert str(plausible_path) in report["run"]["source_sha256"]
            cells = gpd.read_file(output, layer="indicateurs_enjeux")
            assert cells.corridor_observed_length_m.iloc[0] == 1000
            assert cells.corridor_sensitivity_length_min_m.iloc[0] == pytest.approx(998)
            if scenario == "partial":
                assert pd.isna(cells.enj_01_pct.iloc[0])
            else:
                assert cells.enj_01_pct.iloc[0] == 25

    def test_native_geometry_failure_is_reported_without_output(self, tmp_path, monkeypatch):
        arguments, _ = synthetic_pipeline(tmp_path, monkeypatch)
        def fail_geometry(*args, **kwargs):
            raise GEOSException("Échec géométrique SYNTHÉTIQUE")
        monkeypatch.setattr(run_enjeux, "compute_enjeux", fail_geometry)
        assert run_enjeux.main(arguments) == 2
        output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
        assert not output.exists()
        report = json.loads(output.with_suffix(".validation.json").read_text())
        assert "pipeline_error" in {i["code"] for i in report["errors"]}

    def test_report_generation_failure_never_publishes_geopackage(self, tmp_path, monkeypatch):
        arguments, _ = synthetic_pipeline(tmp_path, monkeypatch)
        def fail_report(*args, **kwargs):
            raise OSError("Échec SYNTHÉTIQUE du rapport")
        monkeypatch.setattr(run_enjeux, "_write_json", fail_report)
        assert run_enjeux.main(arguments) == 2
        output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
        assert not output.exists()
        assert not output.with_suffix(".validation.json").exists()

    def test_geopackage_write_failure_produces_only_blocked_report(self, tmp_path, monkeypatch):
        arguments, _ = synthetic_pipeline(tmp_path, monkeypatch)
        def fail_gpkg(*args, **kwargs):
            raise OSError("Échec SYNTHÉTIQUE GeoPackage")
        monkeypatch.setattr(gpd.GeoDataFrame, "to_file", fail_gpkg)
        assert run_enjeux.main(arguments) == 2
        output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
        assert not output.exists()
        report = json.loads(output.with_suffix(".validation.json").read_text())
        assert not report["ok"] and report["run"]["status"] == "blocked"

    def test_failed_second_publication_rolls_back_success_report(self, tmp_path, monkeypatch):
        arguments, _ = synthetic_pipeline(tmp_path, monkeypatch)
        original_link = run_enjeux.os.link
        def fail_second(source, target):
            if str(target).endswith(".gpkg"):
                raise OSError("Échec SYNTHÉTIQUE de publication GPKG")
            return original_link(source, target)
        monkeypatch.setattr(run_enjeux.os, "link", fail_second)
        assert run_enjeux.main(arguments) == 2
        output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
        assert not output.exists()
        report = json.loads(output.with_suffix(".validation.json").read_text())
        assert report["run"]["status"] == "blocked"

    def test_missing_final_report_prevents_reuse(self, tmp_path, monkeypatch):
        arguments, _ = synthetic_pipeline(tmp_path, monkeypatch)
        assert run_enjeux.main(arguments) == 0
        output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
        report = output.with_suffix(".validation.json")
        report.unlink()
        with pytest.raises(ValueError, match="incomplet"):
            run_enjeux.verify_artifact_pair(output, report)

    @pytest.mark.parametrize("field, value", [("run_id", "SYNTHETIC-OTHER-RUN"), ("output_sha256", "0" * 64)])
    def test_mismatched_report_prevents_reuse(self, tmp_path, monkeypatch, field, value):
        arguments, _ = synthetic_pipeline(tmp_path, monkeypatch)
        assert run_enjeux.main(arguments) == 0
        output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
        report_path = output.with_suffix(".validation.json")
        report = json.loads(report_path.read_text())
        report["run"][field] = value
        report_path.write_text(json.dumps(report), encoding="utf-8")
        with pytest.raises(ValueError):
            run_enjeux.verify_artifact_pair(output, report_path)

    def test_explicit_versions_are_preserved_in_both_artifacts(self, tmp_path, monkeypatch):
        arguments, _ = synthetic_pipeline(tmp_path, monkeypatch)
        arguments.extend(["--grid-version", "SYNTHETIC-G", "--method-version", "SYNTHETIC-M", "--dataset-version", "SYNTHETIC-D"])
        assert run_enjeux.main(arguments) == 0
        output = tmp_path / "data/derived/indicateurs_enjeux.gpkg"
        report = run_enjeux.verify_artifact_pair(output, output.with_suffix(".validation.json"))
        assert report["run"]["grid_version"] == "SYNTHETIC-G"
        assert report["run"]["method_version"] == "SYNTHETIC-M"
        assert report["run"]["dataset_version"] == "SYNTHETIC-D"
