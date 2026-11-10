"""Règle de frontière A/B : contre-exemples SYNTHÉTIQUES et 17 cas réels figés."""

import json
import math
from pathlib import Path

import geopandas as gpd
import numpy as np
import pytest
import shapely
from shapely import from_wkb, get_coordinates
from shapely.errors import GEOSException
from shapely.geometry import GeometryCollection, LineString, MultiLineString, Point, Polygon, box

from analysis.aggregate_conflicts import _territory_membership, aggregate_conflicts
from analysis.detect_conflicts import SourceFields, detect_route_corridor_conflicts
from analysis.validate_inputs import InputValidationError

X, Y, WIDTH = 461_000.0, 6_905_000.0, 100.0
STUDY = box(X, Y, X+WIDTH, Y+WIDTH)
UX = math.ulp(X)
REAL = json.loads((Path(__file__).parent / "fixtures/m2/territory_boundary_real_cases.json").read_text())


def ulp_delta(geometry):
    coordinates = get_coordinates(geometry)
    return math.hypot(max(math.ulp(float(v)) for v in coordinates[:, 0]),
                      max(math.ulp(float(v)) for v in coordinates[:, 1]))


def segment(left, right):
    return LineString([(left, Y+50), (right, Y+50)])


def assert_membership(geometry, expected, mode=None, study=STUDY):
    before = geometry.wkb if geometry is not None else None
    study_before = study.wkb if study is not None else None
    accepted, evidence = _territory_membership(geometry, study)
    assert accepted is expected
    assert (geometry.wkb if geometry is not None else None) == before
    assert (study.wkb if study is not None else None) == study_before
    if mode is None:
        assert evidence is None
    else:
        assert evidence["mode"] == mode
        json.dumps(evidence, allow_nan=False)
    return evidence


@pytest.mark.parametrize("geometry", [
    segment(X+1, X+99), LineString([(X, Y), (X+WIDTH, Y)]),
    Point(X+1, Y+1), box(X+1, Y+1, X+2, Y+2),
])
def test_covered_geometry_keeps_historical_acceptance(geometry):
    assert STUDY.covers(geometry)
    assert_membership(geometry, True)


def test_boundary_only_covered_line_does_not_need_linear_interior():
    geometry = LineString([(X, Y), (X+WIDTH, Y)])
    assert STUDY.covers(geometry) and not geometry.relate_pattern(STUDY, "1********")
    assert_membership(geometry, True)


@pytest.mark.parametrize("geometry", [
    pytest.param(LineString([(X+10, Y), (X+90, Y)]), id="boundary-line-without-interior"),
    pytest.param(Point(X+50, Y), id="point"),
    pytest.param(MultiLineString([[(X+10, Y), (X+90, Y)]]), id="multiline"),
])
def test_empty_difference_cannot_bypass_type_and_linear_interior_guards(monkeypatch, geometry):
    assert STUDY.covers(geometry)
    assert geometry.difference(STUDY).is_empty
    assert not geometry.relate_pattern(STUDY, "1********")
    assert geometry.intersection(STUDY).difference(STUDY.boundary).length == 0

    original_covers = shapely.covers
    original_difference = shapely.difference
    difference_calls = []

    def discordant_covers(left, right, **kwargs):
        # Simuler uniquement le désaccord de prédicat : les géométries et les
        # opérations de différence/DE-9IM restent réelles et inchangées.
        if left is STUDY and right is geometry:
            return np.bool_(False)
        return original_covers(left, right, **kwargs)

    def track_difference(*args, **kwargs):
        difference_calls.append(True)
        return original_difference(*args, **kwargs)

    monkeypatch.setattr(shapely, "covers", discordant_covers)
    monkeypatch.setattr(shapely, "difference", track_difference)
    assert not STUDY.covers(geometry)
    assert_membership(geometry, False)
    # Le refus doit précéder même le calcul de outside : le retour sur différence
    # vide ne peut contourner ni le type LineString ni la portion intérieure.
    assert difference_calls == []


def test_external_line_touching_one_point_is_refused_despite_tiny_length():
    geometry = LineString([(X-UX, Y), (X, Y)])
    assert geometry.intersection(STUDY).geom_type == "Point"
    assert 0 < geometry.length <= ulp_delta(geometry)
    assert not geometry.relate_pattern(STUDY, "1********")
    assert_membership(geometry, False)


def test_boundary_followed_by_tiny_external_extension_is_refused():
    geometry = LineString([(X+50, Y), (X+WIDTH+UX, Y)])
    outside = geometry.difference(STUDY)
    clipped = geometry.intersection(STUDY)
    assert not STUDY.covers(geometry) and clipped.length > 0
    assert 0 < outside.length <= ulp_delta(geometry)
    assert geometry.hausdorff_distance(clipped) <= ulp_delta(geometry)
    assert not geometry.relate_pattern(STUDY, "1********")
    assert_membership(geometry, False)


@pytest.mark.parametrize("reverse", [False, True])
def test_linear_interior_with_one_small_residue(reverse):
    geometry = segment(X+50, X+WIDTH+UX)
    if reverse:
        geometry = LineString(list(geometry.coords)[::-1])
    assert geometry.relate_pattern(STUDY, "1********")
    evidence = assert_membership(geometry, True, "residus_lineaires_resolution_machine")
    assert evidence["outside_component_count"] == 1
    assert evidence["outside_length_m"] == geometry.difference(STUDY).length
    assert evidence["coordinate_ulp_diagonal_m"] == ulp_delta(geometry)


def test_two_external_components_under_common_budget_are_accepted():
    geometry = segment(X-4*UX, X+WIDTH+4*UX)
    outside = geometry.difference(STUDY)
    assert outside.geom_type == "MultiLineString" and len(outside.geoms) == 2
    assert 0 < outside.length <= ulp_delta(geometry)
    evidence = assert_membership(geometry, True, "residus_lineaires_resolution_machine")
    assert evidence["outside_component_count"] == 2
    assert evidence["outside_length_m"] == sum(part.length for part in outside.geoms)


def test_each_component_under_budget_but_cumulative_length_over_budget_is_refused():
    geometry = segment(X-9*UX, X+WIDTH+9*UX)
    outside = geometry.difference(STUDY)
    delta = ulp_delta(geometry)
    assert len(outside.geoms) == 2 and all(part.length < delta for part in outside.geoms)
    assert outside.length > delta
    assert geometry.hausdorff_distance(geometry.intersection(STUDY)) <= delta
    assert_membership(geometry, False)


def test_hausdorff_guard_is_independent_of_length_guard(monkeypatch):
    geometry = segment(X+50, X+WIDTH+UX)
    delta = ulp_delta(geometry)
    assert geometry.difference(STUDY).length <= delta
    # Injection ciblée d'un résultat numérique incohérent : ne pas prétendre
    # qu'une ligne connexe présente naturellement distance > longueur extérieure.
    monkeypatch.setattr(shapely, "hausdorff_distance", lambda *args, **kwargs: np.float64(2*delta))
    assert_membership(geometry, False)


@pytest.mark.parametrize("geometry", [
    segment(X+50, X+WIDTH+0.001), segment(X-10, X-1),
    LineString([(X-UX, Y+50), (X-UX, Y+50+math.ulp(Y))]),
])
def test_actual_exterior_and_tiny_wholly_exterior_lines_are_refused(geometry):
    assert not STUDY.covers(geometry)
    assert_membership(geometry, False)


@pytest.mark.parametrize("geometry", [
    Point(X-UX, Y+50), box(X-UX, Y+1, X+1, Y+2),
    MultiLineString([[(X+50, Y+50), (X+WIDTH+UX, Y+50)]]),
    GeometryCollection([segment(X+50, X+WIDTH+UX)]),
])
def test_non_linestring_types_cannot_use_the_exception(geometry):
    assert not STUDY.covers(geometry)
    assert_membership(geometry, False)


@pytest.mark.parametrize("geometry", [
    None, LineString(), LineString([(X+1, Y+1), (X+1, Y+1)]),
    LineString([(X+1, Y+1), (math.inf, Y+2)]),
    LineString([(X+1, Y+1), (math.nan, Y+2)]),
    Polygon([(X+1, Y+1), (X+2, Y+2), (X+2, Y+1), (X+1, Y+2), (X+1, Y+1)]),
])
def test_invalid_empty_or_nonfinite_geometry_is_refused(geometry):
    assert_membership(geometry, False)


@pytest.mark.parametrize("study", [None, Polygon(), Point(X, Y),
                                    Polygon([(X, Y), (X+1, Y+1), (X+1, Y), (X, Y+1), (X, Y)])])
def test_invalid_study_is_not_an_acceptance_path(study):
    assert_membership(segment(X+1, X+99), False, study=study)


@pytest.mark.parametrize("distance", [math.nan, math.inf, -1.0])
def test_nonfinite_or_negative_hausdorff_cannot_pass(monkeypatch, distance):
    geometry = segment(X+50, X+WIDTH+UX)
    monkeypatch.setattr(shapely, "hausdorff_distance", lambda *args, **kwargs: np.float64(distance))
    assert_membership(geometry, False)


@pytest.mark.parametrize("delta", [math.nan, math.inf, 0.0])
def test_invalid_ulp_budget_cannot_pass(monkeypatch, delta):
    geometry = segment(X+50, X+WIDTH+UX)
    monkeypatch.setattr(math, "hypot", lambda *args: delta)
    assert_membership(geometry, False)


def test_topology_failure_is_fail_closed(monkeypatch):
    def fail(*args, **kwargs):
        raise GEOSException("Défaillance topologique simulée")
    monkeypatch.setattr(shapely, "relate_pattern", fail)
    assert_membership(segment(X+50, X+WIDTH+UX), False)


@pytest.mark.parametrize("record", REAL["events"], ids=lambda row: row["conflit_id"])
def test_seventeen_real_cases_follow_the_final_criteria(record):
    geometry = from_wkb(bytes.fromhex(record["geometry_wkb_hex"]))
    study = from_wkb(bytes.fromhex(REAL["study_wkb_hex"]))
    assert not study.covers(geometry)
    assert geometry.relate_pattern(study, "1********") is record["expected_linear_interior"]
    assert geometry.intersection(study).difference(study.boundary).length > 0
    assert geometry.difference(study).is_empty is record["outside_is_empty"]
    evidence = assert_membership(geometry, record["expected_acceptance"], record["expected_rule"], study)
    if record["outside_is_empty"]:
        assert "coordinate_ulp_diagonal_m" not in evidence
        assert "hausdorff_to_intersection_m" not in evidence
    else:
        assert 0 < evidence["outside_length_m"] <= evidence["coordinate_ulp_diagonal_m"]
        assert 0 <= evidence["hausdorff_to_intersection_m"] <= evidence["coordinate_ulp_diagonal_m"]


def frame(geometries, **attributes):
    return gpd.GeoDataFrame(attributes, geometry=geometries, crs=2154)


def detection_with_event(geometry, study=STUDY):
    center = study.representative_point()
    placeholder = LineString([(center.x-1, center.y), (center.x+1, center.y)])
    detection = detect_route_corridor_conflicts(
        frame([placeholder], rid=["SYNTHETIC-R"]), frame([placeholder], cid=["SYNTHETIC-C"]),
        frame([study]), route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"),
        method_version="SYNTHETIC-TERRITORY-CONTROL",
    )
    # Artefact d'overlay SYNTHÉTIQUE inséré pour tester l'agrégateur seul.
    detection.events.at[0, "geometry"] = geometry
    return detection


def test_aggregate_warning_retains_geometry_links_and_exclusive_owner():
    geometry = segment(X+50, X+WIDTH+UX)
    detection = detection_with_event(geometry)
    before = detection.events.copy(deep=True)
    result = aggregate_conflicts(frame([STUDY], maille_id=["H"]), frame([STUDY]), detection)
    warning = next(i for i in result.report.issues if i.code == "event_territory_numerical_residue")
    assert warning.severity == "warning" and warning.details["count"] == 1
    assert result.report.ok and result.summary["canonical_owner_count"] == 1
    assert result.events.geometry.iloc[0].wkb == geometry.wkb
    assert result.events.conflit_id.tolist() == before.conflit_id.tolist()
    assert result.links.maille_id.tolist() == ["H"] and result.links.canonical_owner.tolist() == [True]
    assert result.cells.nb_evenements_observes.tolist() == [1]
    assert result.cells.nb_evenements_exclusifs_observes.tolist() == [1]
    assert result.cells.nb_evenements.isna().all()
    assert detection.events.equals(before)


@pytest.mark.parametrize("geometry", [
    LineString([(X+50, Y), (X+WIDTH+UX, Y)]),
    LineString([(X-UX, Y), (X, Y)]), segment(X-9*UX, X+WIDTH+9*UX),
    segment(X+50, X+WIDTH+0.001),
])
def test_aggregate_keeps_error_code_for_outside_events(geometry):
    detection = detection_with_event(geometry)
    before = detection.events.copy(deep=True)
    with pytest.raises(InputValidationError) as exc:
        aggregate_conflicts(frame([STUDY], maille_id=["H"]), frame([STUDY]), detection)
    issue = next(i for i in exc.value.report.issues if i.code == "event_outside_territory")
    assert issue.severity == "error" and issue.details["conflit_ids"] == detection.events.conflit_id.tolist()
    assert detection.events.equals(before)


def test_internal_shared_cell_boundary_preserves_all_links_and_canonical_owner():
    left, right = box(X, Y, X+50, Y+100), box(X+50, Y, X+100, Y+100)
    geometry = LineString([(X+50, Y+10), (X+50, Y+90)])
    detection = detection_with_event(geometry)
    result = aggregate_conflicts(frame([right, left], maille_id=["B", "A"]), frame([STUDY]), detection)
    assert result.report.ok and len(result.events) == 1 and len(result.links) == 2
    assert result.links.relation_spatiale.tolist() == ["frontiere", "frontiere"]
    assert result.links.loc[result.links.canonical_owner, "maille_id"].tolist() == ["A"]
    assert json.loads(result.events.maille_ids.iloc[0]) == ["A", "B"]
    assert result.cells.nb_evenements_observes.sum() == 2
    assert result.cells.nb_evenements_exclusifs_observes.sum() == 1
