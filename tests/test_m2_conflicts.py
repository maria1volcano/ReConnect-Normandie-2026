"""Sources, preuves et territoires exclusivement SYNTHÉTIQUES : aucun diagnostic réel."""

from dataclasses import replace
import json
import math
import sqlite3

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import LineString, MultiLineString, Point, Polygon, box

from analysis.aggregate_conflicts import aggregate_conflicts
from analysis.detect_conflicts import (
    EventEvidence, IntersectionPrecision, PotentialConflictRule, SourceFields,
    apply_potential_conflict_rules, detect_route_corridor_conflicts, qualify_events,
)
from analysis.indicateurs_enjeux import CoverageEvidence, SubframeMapping, territory_geometry_sha256
from analysis import run_conflicts
from analysis.validate_inputs import InputValidationError

X, Y = 500_000, 6_900_000
CELL = box(X, Y, X + 1000, Y + 1000)
ROAD = LineString([(X, Y + 500), (X + 1000, Y + 500)])
CORRIDOR = LineString([(X + 500, Y), (X + 500, Y + 1000)])
METHOD = "METHODE-SYNTHETIQUE-TEST"


def frame(geometries, **columns):
    return gpd.GeoDataFrame(columns, geometry=geometries, crs=2154)


def detect(roads=None, corridors=None, territory=None, **kwargs):
    return detect_route_corridor_conflicts(
        frame([ROAD] if roads is None else roads, rid=[f"R{i}" for i in range(1 if roads is None else len(roads))]),
        frame([CORRIDOR] if corridors is None else corridors, cid=[f"C{i}" for i in range(1 if corridors is None else len(corridors))]),
        frame([CELL]) if territory is None else territory,
        route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"), method_version=METHOD, **kwargs,
    )


def coverage(theme, territory=None, footprint=None):
    return CoverageEvidence(
        confirmed=footprint is None, footprint=footprint, status="validated", source_id=f"SOURCE-SYNTHETIQUE-{theme}",
        producer="PRODUCTEUR SYNTHÉTIQUE", vintage="MILLÉSIME SYNTHÉTIQUE", validity_extent="EMPRISE SYNTHÉTIQUE",
        theme=theme, document_reference="PREUVE SYNTHÉTIQUE", validated_by="M1/M2 SYNTHÉTIQUES",
        validated_at="2026-10-30T12:00:00+01:00",
        territory_sha256=territory_geometry_sha256(frame([CELL]) if territory is None else territory),
    )


def aggregate(detection, cells=None, territory=None):
    return aggregate_conflicts(frame([CELL], maille_id=["H1"]) if cells is None else cells,
                               frame([CELL]) if territory is None else territory, detection)


class TestSourceIntersections:
    def test_linear_route_and_corridor_cross_at_one_real_point(self):
        result = detect()
        assert len(result.events) == 1
        event = result.events.iloc[0]
        assert event.geometry.equals(Point(X + 500, Y + 500))
        assert event.intersection_dimension == "ponctuelle"
        assert event.statut == "croisement_detecte" and event.evidence_level == "geometrie_2d"
        assert event.source_ids == '{"corridors":["C0"],"routes":["R0"]}'
        assert pd.isna(event.length_m) and pd.isna(event.area_m2)

    def test_route_crosses_areal_corridor_with_measured_segment(self):
        result = detect(corridors=[box(X + 400, Y + 400, X + 600, Y + 600)])
        assert len(result.events) == 1
        event = result.events.iloc[0]
        assert event.intersection_dimension == "lineaire" and event.length_m == 200
        assert pd.isna(event.area_m2)

    def test_two_surfaces_produce_area_not_a_fictitious_length(self):
        result = detect(roads=[box(X + 400, Y, X + 600, Y + 1000)],
                        corridors=[box(X + 450, Y + 400, X + 550, Y + 600)])
        event = result.events.iloc[0]
        assert event.intersection_dimension == "surfacique" and event.area_m2 == 20_000
        assert pd.isna(event.length_m)

    def test_copresence_without_intersection_never_creates_event(self):
        result = detect(roads=[LineString([(X, Y + 100), (X + 1000, Y + 100)])],
                        corridors=[LineString([(X, Y + 200), (X + 1000, Y + 200)])])
        assert result.analysis_performed and result.events.empty
        diagnostic = aggregate(result).cells.iloc[0]
        assert diagnostic.nb_evenements_observes == 0
        assert pd.isna(diagnostic.nb_evenements)

    @pytest.mark.parametrize("corridor", [
        LineString([(X + 1000, Y + 500), (X + 1000, Y + 800)]),
        box(X + 400, Y + 500, X + 600, Y + 700),
    ])
    def test_point_or_boundary_contact_is_kept_but_inconclusive(self, corridor):
        event = detect(corridors=[corridor]).events.iloc[0]
        assert event.statut == "non_concluant"
        assert event.detection_status == "contact_detecte"
        assert event.intersection_relation == "contact_frontiere"

    def test_superposed_segments_are_one_geometric_event(self):
        result = detect(corridors=[LineString([(X + 400, Y + 500), (X + 600, Y + 500)])])
        assert len(result.events) == 1
        assert result.events.length_m.iloc[0] == 200
        assert result.events.statut.iloc[0] != "obstacle_confirme"

    def test_disconnected_crossings_remain_two_events_in_one_cell(self):
        lines = MultiLineString([[(X + 300, Y), (X + 300, Y + 1000)],
                                 [(X + 700, Y), (X + 700, Y + 1000)]])
        result = aggregate(detect(corridors=[lines]))
        assert len(result.events) == 2 and result.events.conflit_id.nunique() == 2
        assert result.cells.nb_evenements_observes.iloc[0] == 2
        assert result.summary["distinct_events_observed"] == 2

    def test_source_intersection_outside_territory_creates_no_local_event(self):
        result = detect(roads=[LineString([(X + 2000, Y + 500), (X + 3000, Y + 500)])],
                        corridors=[LineString([(X + 2500, Y), (X + 2500, Y + 1000)])])
        assert result.events.empty

    def test_source_crs_absent_is_blocking(self):
        roads = gpd.GeoDataFrame({"rid": ["R"]}, geometry=[ROAD])
        with pytest.raises(InputValidationError, match="CRS absent"):
            detect_route_corridor_conflicts(roads, frame([CORRIDOR], cid=["C"]), frame([CELL]),
                                           route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"))


class TestDuplicateAndIdentityRules:
    def test_identical_candidate_from_split_sources_is_not_counted_twice(self):
        left = LineString([(X, Y + 500), (X + 500, Y + 500)])
        right = LineString([(X + 500, Y + 500), (X + 1000, Y + 500)])
        result = detect(roads=[left, right])
        assert len(result.events) == 1
        assert json.loads(result.events.source_ids.iloc[0])["routes"] == ["R0", "R1"]
        observed = json.loads(result.events.observations.iloc[0])
        assert len(observed["routes"]["source_objects"]) == 2
        assert len(observed["pair_intersections"]) == 2

    def test_duplicate_geometries_keep_alias_ids_without_duplicate_event(self):
        result = detect(roads=[ROAD, ROAD], corridors=[CORRIDOR, CORRIDOR])
        assert len(result.events) == 1
        ids = json.loads(result.events.source_ids.iloc[0])
        assert ids == {"routes": ["R0", "R1"], "corridors": ["C0", "C1"]}
        assert len(json.loads(result.events.source_pairs.iloc[0])) == 4
        assert result.events.conflit_id.iloc[0] == detect().events.conflit_id.iloc[0]

    def test_duplicate_rows_with_same_id_are_collapsed(self):
        result = detect_route_corridor_conflicts(frame([ROAD, ROAD], rid=["R", "R"]),
            frame([CORRIDOR], cid=["C"]), frame([CELL]), route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"))
        assert len(result.events) == 1 and json.loads(result.events.source_ids.iloc[0])["routes"] == ["R"]

    def test_same_id_for_distinct_source_features_is_blocking(self):
        with pytest.raises(InputValidationError, match="objets différents"):
            detect_route_corridor_conflicts(frame([ROAD, CORRIDOR], rid=["R", "R"]),
                frame([CORRIDOR], cid=["C"]), frame([CELL]), route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"))

    def test_different_contexts_are_not_collapsed_at_same_geometry(self):
        result = detect_route_corridor_conflicts(frame([ROAD, ROAD], rid=["R1", "R2"], category=["A", "B"]),
            frame([CORRIDOR], cid=["C"]), frame([CELL]), route_fields=SourceFields("rid", category_column="category"),
            corridor_fields=SourceFields("cid"))
        assert len(result.events) == 2

    def test_identifiers_are_independent_of_order_orientation_and_index(self):
        roads = frame([ROAD, LineString([(X, Y + 300), (X + 1000, Y + 300)])], rid=["R1", "R2"])
        paths = frame([CORRIDOR], cid=["C"])
        def execute(r, c):
            return detect_route_corridor_conflicts(r, c, frame([CELL]), route_fields=SourceFields("rid"),
                                                  corridor_fields=SourceFields("cid"), method_version=METHOD)
        original = execute(roads, paths)
        reordered = roads.iloc[::-1].copy()
        reordered.geometry = reordered.geometry.map(lambda g: LineString(list(g.coords)[::-1]))
        reversed_paths = paths.copy()
        reversed_paths.geometry = reversed_paths.geometry.map(lambda g: LineString(list(g.coords)[::-1]))
        assert original.events.conflit_id.tolist() == execute(reordered, reversed_paths).events.conflit_id.tolist()

    def test_method_change_changes_identifiers(self):
        initial = detect().events.conflit_id.iloc[0]
        other = detect_route_corridor_conflicts(frame([ROAD], rid=["R0"]), frame([CORRIDOR], cid=["C0"]),
            frame([CELL]), route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"), method_version="AUTRE-METHODE-SYNTHETIQUE")
        assert initial != other.events.conflit_id.iloc[0]

    def test_subframes_and_road_context_are_preserved(self):
        roads = frame([ROAD], rid=["R"], cat=["CAT-TEST"], ouvrage=["PONT-TEST"], niveau=["NIV-TEST"])
        paths = frame([CORRIDOR], cid=["C"], trame=["A"])
        result = detect_route_corridor_conflicts(roads, paths, frame([CELL]),
            route_fields=SourceFields("rid", "cat", "ouvrage", "niveau", "Dictionnaire SYNTHÉTIQUE"),
            corridor_fields=SourceFields("cid", subframes=SubframeMapping("trame", {"A": "SOUS-TRAME SYNTHÉTIQUE"})))
        observed = json.loads(result.events.observations.iloc[0])
        assert observed["routes"]["context"]["structure"] == "PONT-TEST"
        assert observed["routes"]["context"]["category"] == "CAT-TEST"
        assert observed["corridors"]["context"]["subframe_meaning"] == "SOUS-TRAME SYNTHÉTIQUE"
        assert result.events.statut.iloc[0] == "croisement_detecte"

    def test_z_levels_are_not_collapsed_or_interpreted_as_barriers(self):
        roads = frame([LineString([(X, Y + 500, 1), (X + 1000, Y + 500, 1)]),
                       LineString([(X, Y + 500, 10), (X + 1000, Y + 500, 10)])], rid=["R1", "R2"])
        result = detect_route_corridor_conflicts(roads, frame([CORRIDOR], cid=["C"]), frame([CELL]),
                                                route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"))
        assert len(result.events) == 2
        assert set(result.events.statut) == {"croisement_detecte"}
        assert not result.events.geometry.has_z.any()

    def test_unknown_method_is_null_with_deterministic_code_bound_identity(self):
        def execute():
            return detect_route_corridor_conflicts(frame([ROAD], rid=["R"]), frame([CORRIDOR], cid=["C"]),
                frame([CELL]), route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"))
        first, second = execute(), execute()
        assert first.events.method_version.iloc[0] is None
        assert first.events.conflit_id.tolist() == second.events.conflit_id.tolist()

    def test_distinct_documented_subframes_at_same_geometry_remain_distinct(self):
        result = detect_route_corridor_conflicts(frame([ROAD], rid=["R"]),
            frame([CORRIDOR, CORRIDOR], cid=["C1", "C2"], trame=["A", "B"]), frame([CELL]),
            route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid", subframes=SubframeMapping(
                "trame", {"A": "SOUS-TRAME A SYNTHÉTIQUE", "B": "SOUS-TRAME B SYNTHÉTIQUE"})))
        assert len(result.events) == 2


class TestQualificationAndPrecision:
    def test_conflicting_external_qualifications_are_blocking(self):
        events = detect().events
        item = EventEvidence(events.conflit_id.iloc[0], "conflit_potentiel", "REF SYNTHÉTIQUE", "CRITÈRE SYNTHÉTIQUE", "M2", "2026-10-30")
        with pytest.raises(InputValidationError, match="divergentes"):
            qualify_events(events, [item, replace(item, target_status="obstacle_confirme")])

    @pytest.mark.parametrize("distance, reference", [(0, "TEST"), (-1, "TEST"), (float("nan"), "TEST"), (1, "")])
    def test_invalid_precision_contract_is_blocking(self, distance, reference):
        with pytest.raises(InputValidationError, match="précision"):
            detect(precision=IntersectionPrecision(distance, reference))

    def test_numeric_residue_is_kept_and_never_promoted(self):
        line = LineString([(X + 100, Y + 100), (X + 100 + 5e-10, Y + 100)])
        event = detect(roads=[line], corridors=[line]).events.iloc[0]
        assert event.length_m > 0 and event.numeric_residue
        assert event.statut == "non_concluant"

    @pytest.mark.parametrize("status", ["conflit_potentiel", "obstacle_confirme", "non_concluant"])
    def test_external_documented_evidence_can_qualify_exact_event(self, status):
        events = detect().events
        evidence = EventEvidence(events.conflit_id.iloc[0], status, "DOCUMENT EXTERNE SYNTHÉTIQUE", "CRITÈRES SYNTHÉTIQUES",
                                 "VALIDATEUR SYNTHÉTIQUE", "2026-10-30", "OBSERVATION SYNTHÉTIQUE",
                                 "LOCALISATION SYNTHÉTIQUE RÉSOLUE", "EXPERT SYNTHÉTIQUE", "2026-10-30")
        qualified = qualify_events(events, [evidence])
        assert qualified.statut.iloc[0] == status
        assert qualified.geometry.iloc[0].equals(events.geometry.iloc[0])
        assert qualified.detection_status.iloc[0] == events.detection_status.iloc[0]
        assert events.statut.iloc[0] == "croisement_detecte"
        assert len(json.loads(qualified.preuves.iloc[0])) == 1

    @pytest.mark.parametrize("missing", ["reference", "criteria", "validated_by", "validated_at"])
    def test_undocumented_promotion_is_blocking(self, missing):
        events = detect().events
        evidence = EventEvidence(events.conflit_id.iloc[0], "obstacle_confirme", "REF SYNTHÉTIQUE", "CRITÈRE SYNTHÉTIQUE",
                                 "M2 SYNTHÉTIQUE", "2026-10-30")
        with pytest.raises(InputValidationError):
            qualify_events(events, [replace(evidence, **{missing: ""})])

    def test_stale_evidence_never_applies_to_another_event(self):
        evidence = EventEvidence("ABSENT-SYNTHETIC-ID", "obstacle_confirme", "REF", "CRITÈRE", "M2", "2026-10-30")
        with pytest.raises(InputValidationError, match="correspondant"):
            qualify_events(detect().events, [evidence])

    def test_unknown_structure_never_becomes_confirmed_obstacle(self):
        event = detect().events.iloc[0]
        assert event.statut == "croisement_detecte" and json.loads(event.preuves) == []
        assert json.loads(event.observations)["routes"]["context"]["structure"] is None

    def test_precision_insufficient_keeps_event_but_marks_inconclusive(self):
        result = detect(precision=IntersectionPrecision(1, "PRÉCISION SYNTHÉTIQUE", localization_adequate=False))
        event = result.events.iloc[0]
        assert event.statut == "non_concluant" and event.precision_affichage == "localisation_a_confirmer"
        assert event.geometry.equals(Point(X + 500, Y + 500))

    def test_sensitive_intersection_is_flagged_without_buffering_or_new_event(self):
        road = LineString([(X + 499.95, Y + 500), (X + 500.05, Y + 500)])
        raw = detect(roads=[road])
        measured = detect(roads=[road], precision=IntersectionPrecision(1, "SCÉNARIO SYNTHÉTIQUE 1 m", True))
        assert len(measured.events) == 1
        assert measured.events.precision_sensitive.iloc[0]
        assert measured.events.statut.iloc[0] == "non_concluant"
        assert measured.events.geometry.iloc[0].equals(raw.events.geometry.iloc[0])

    def test_unknown_precision_is_not_a_zero_or_a_validated_location(self):
        event = detect().events.iloc[0]
        assert pd.isna(event.precision_sensitive) and pd.isna(event.precision_m)
        assert event.precision_affichage == "precision_non_documentee"


class TestEventCellRelations:
    def test_explicit_qualified_status_counts_do_not_create_score(self):
        detection = detect()
        item = EventEvidence(detection.events.conflit_id.iloc[0], "obstacle_confirme", "REF EXTERNE SYNTHÉTIQUE",
                             "CRITÈRE SYNTHÉTIQUE", "M2 SYNTHÉTIQUE", "2026-10-30",
                             localization_resolution_reference="LOCALISATION SYNTHÉTIQUE RÉSOLUE",
                             localization_validated_by="EXPERT SYNTHÉTIQUE", localization_validated_at="2026-10-30")
        detection.events = qualify_events(detection.events, [item])
        result = aggregate(detection)
        assert result.cells.nb_obstacle_confirme_observes.iloc[0] == 1
        assert result.cells.nb_conflit_potentiel_observes.iloc[0] == 0
        assert not any("score" in column for column in result.cells.columns)

    def test_point_on_shared_border_has_two_links_but_one_global_count(self):
        second = box(X + 1000, Y, X + 2000, Y + 1000)
        territory = frame([CELL, second])
        event = detect(roads=[LineString([(X + 900, Y + 500), (X + 1100, Y + 500)])],
                       corridors=[LineString([(X + 1000, Y), (X + 1000, Y + 1000)])], territory=territory)
        result = aggregate(event, frame([second, CELL], maille_id=["H2", "H1"]), territory)
        assert len(result.links) == 2 and result.links.canonical_owner.sum() == 1
        assert result.links.loc[result.links.canonical_owner, "maille_id"].tolist() == ["H1"]
        assert result.cells.nb_evenements_observes.sum() == 2
        assert result.summary["distinct_events_observed"] == 1
        assert json.loads(result.events.maille_ids.iloc[0]) == ["H1", "H2"]

    def test_owner_prefers_positive_interior_over_incidental_border_contact(self):
        second = box(X + 1000, Y, X + 2000, Y + 1000)
        territory = frame([CELL, second])
        line = LineString([(X + 100, Y + 500), (X + 1000, Y + 500)])
        result = aggregate(detect(roads=[line], corridors=[line], territory=territory),
                           frame([CELL, second], maille_id=["H2", "H1"]), territory)
        assert result.links.loc[result.links.canonical_owner, "maille_id"].tolist() == ["H2"]

    def test_segment_spans_two_regular_hexagons_without_splitting_event(self):
        radius = math.sqrt(2_000_000 / (3 * math.sqrt(3)))
        w = radius * math.sqrt(3) / 2
        shared = X + w
        first = Polygon([(X, Y + radius), (shared, Y + radius / 2), (shared, Y - radius / 2),
                         (X, Y - radius), (X - w, Y - radius / 2), (X - w, Y + radius / 2)])
        second = Polygon([(X + 2*w, Y + radius), (X + 3*w, Y + radius / 2), (X + 3*w, Y - radius / 2),
                          (X + 2*w, Y - radius), (shared, Y - radius / 2), (shared, Y + radius / 2)])
        territory = frame([first, second])
        line = LineString([(X - w, Y), (X + 3*w, Y)])
        result = aggregate(detect(roads=[line], corridors=[box(X - 2000, Y - 2000, X + 3000, Y + 2000)], territory=territory),
                           frame([first, second], maille_id=["HEX1", "HEX2"]), territory)
        assert len(result.events) == 1 and len(result.links) == 2
        assert result.events.length_m.iloc[0] == pytest.approx(line.length)

    def test_validated_absence_is_zero_but_declared_absence_is_unknown(self):
        no_crossing = LineString([(X, Y + 200), (X + 1000, Y + 200)])
        validated = aggregate(detect(corridors=[no_crossing], route_coverage=coverage("routes"), corridor_coverage=coverage("corridors")))
        assert validated.cells.nb_evenements.iloc[0] == 0
        assert validated.cells.diagnostic.iloc[0] == "absence_croisement_confirmee"
        declared = CoverageEvidence(confirmed=True, provenance="DÉCLARATION SYNTHÉTIQUE")
        unknown = aggregate(detect(corridors=[no_crossing], route_coverage=declared, corridor_coverage=declared))
        assert pd.isna(unknown.cells.nb_evenements.iloc[0])
        assert unknown.cells.nb_evenements_observes.iloc[0] == 0
        assert unknown.cells.diagnostic.iloc[0] == "absence_observation_couverture_non_validee"

    @pytest.mark.parametrize("missing_detection", [True, False])
    def test_missing_analysis_creates_no_located_event_or_zero(self, missing_detection):
        detection = None if missing_detection else detect_route_corridor_conflicts(
            None, frame([CORRIDOR], cid=["C"]), frame([CELL]), route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"))
        result = aggregate(detection)
        assert result.events.empty and result.links.empty
        assert result.cells.etat_analyse.iloc[0] == "absence_analyse"
        assert pd.isna(result.cells.nb_evenements_observes.iloc[0])
        assert pd.isna(result.cells.nb_evenements.iloc[0])
        assert result.summary["distinct_events_observed"] is None

    def test_partial_coverage_cannot_authorize_complete_count(self):
        result = aggregate(detect(route_coverage=coverage("routes", footprint=frame([box(X, Y, X + 500, Y + 1000)])),
                                  corridor_coverage=coverage("corridors")))
        assert result.cells.nb_evenements_observes.iloc[0] == 1
        assert pd.isna(result.cells.nb_evenements.iloc[0])
        assert result.summary["distinct_events"] is None


def synthetic_cli(tmp_path, monkeypatch, *, crossing=True, empty_routes=False):
    monkeypatch.setattr(run_conflicts, "PROJECT_ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    processed = tmp_path / "data/processed"
    processed.mkdir(parents=True)
    sources = {"grid": frame([CELL], maille_id=["H1"]), "territory": frame([CELL]),
               "routes": frame([] if empty_routes else [ROAD], rid=[] if empty_routes else ["R"]),
               "corridors": frame([CORRIDOR if crossing else LineString([(X, Y + 200), (X + 1000, Y + 200)])], cid=["C"])}
    args = []
    for name, source in sources.items():
        path = processed / f"SYNTHETIC_{name}.gpkg"
        source.to_file(path, driver="GPKG", index=False)
        args.extend([f"--{name}", str(path)])
    config = tmp_path / "SYNTHETIC_config.json"
    config.write_text(json.dumps({"routes": {"id_column": "rid"}, "corridors": {"id_column": "cid"}}), encoding="utf-8")
    args.extend(["--config", str(config), "--method-version", METHOD])
    return args, processed


def bundle_paths(tmp_path):
    derived = tmp_path / "data/derived"
    return derived / "conflits_candidates.gpkg", derived / "mailles_conflits.gpkg", derived / "conflits_validation.json"


class TestConflictPipeline:
    def test_full_config_with_validated_coverage_and_external_evidence(self, tmp_path, monkeypatch):
        args, processed = synthetic_cli(tmp_path, monkeypatch)
        config_path = tmp_path / "SYNTHETIC_config.json"
        config = json.loads(config_path.read_text())
        for name in ("routes", "corridors"):
            item = coverage(name)
            config[name]["coverage"] = {key: value for key, value in item.__dict__.items()
                                        if key not in {"confirmed", "footprint", "provenance"} and value is not None}
        plausible_path = processed / "SYNTHETIC_extent.gpkg"
        frame([CELL]).to_file(plausible_path, driver="GPKG", index=False)
        config["spatial"] = {"plausible_extent": str(plausible_path), "reference": "EMPRISE OFFICIELLE SYNTHÉTIQUE", "validated_by": "M1 SYNTHÉTIQUE"}
        config["precision"] = {"distance_m": 1, "reference": "SCÉNARIO SYNTHÉTIQUE", "localization_adequate": True}
        config_path.write_text(json.dumps(config), encoding="utf-8")
        # Le calcul préalable retrouve l'identité exacte, sans inventer un conflit_id.
        detection = detect_route_corridor_conflicts(frame([ROAD], rid=["R"]), frame([CORRIDOR], cid=["C"]), frame([CELL]),
            route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"), route_coverage=coverage("routes"),
            corridor_coverage=coverage("corridors"), method_version=METHOD)
        evidence = EventEvidence(detection.events.conflit_id.iloc[0], "conflit_potentiel", "DOCUMENT SYNTHÉTIQUE",
                                 "CRITÈRE SYNTHÉTIQUE", "M1/M2 SYNTHÉTIQUES", "2026-10-30")
        evidence_path = processed / "SYNTHETIC_evidence.json"
        evidence_path.write_text(json.dumps([evidence.__dict__]), encoding="utf-8")
        args.extend(["--route-coverage-confirmed", "--corridor-coverage-confirmed", "--qualifications", str(evidence_path),
                     "--grid-version", "GRILLE-SYNTHETIQUE", "--dataset-version", "DONNEES-SYNTHETIQUES"])
        assert run_conflicts.main(args) == 0
        report = run_conflicts.verify_conflict_bundle(*bundle_paths(tmp_path))
        assert report["run"]["summary"]["distinct_events"] == 1
        events = gpd.read_file(bundle_paths(tmp_path)[0], layer="conflits_candidates")
        assert events.statut.iloc[0] == "conflit_potentiel"
        assert report["run"]["grid_version"] == "GRILLE-SYNTHETIQUE"

    @pytest.mark.parametrize("crossing, empty", [(True, False), (False, False), (True, True)])
    def test_complete_bundle_roundtrip_including_no_observations(self, tmp_path, monkeypatch, crossing, empty):
        args, processed = synthetic_cli(tmp_path, monkeypatch, crossing=crossing, empty_routes=empty)
        before = {str(p): run_conflicts._sha256(p) for p in processed.iterdir()}
        assert run_conflicts.main(args) == 0
        events_path, cells_path, report_path = bundle_paths(tmp_path)
        report = run_conflicts.verify_conflict_bundle(events_path, cells_path, report_path)
        expected = 1 if crossing and not empty else 0
        assert report["run"]["summary"]["distinct_events_observed"] == expected
        assert report["run"]["grid_version"] is None and report["run"]["dataset_version"] is None
        assert report["run"]["method_version"] == METHOD
        assert {str(p): run_conflicts._sha256(p) for p in processed.iterdir()} == before
        assert not (tmp_path / "data/public").exists()
        with sqlite3.connect(cells_path) as connection:
            assert connection.execute("SELECT count(*) FROM liens_mailles_conflits").fetchone()[0] == expected
        assert run_conflicts.main(args) == 2  # aucun écrasement

    def test_missing_file_blocks_without_fictitious_geopackages(self, tmp_path, monkeypatch):
        args, processed = synthetic_cli(tmp_path, monkeypatch)
        args[args.index("--routes") + 1] = str(processed / "ABSENT_SYNTHETIC.gpkg")
        assert run_conflicts.main(args) == 2
        events, cells, report = bundle_paths(tmp_path)
        assert not events.exists() and not cells.exists()
        assert "missing_file" in {i["code"] for i in json.loads(report.read_text())["errors"]}

    def test_public_output_is_forbidden(self, tmp_path, monkeypatch):
        args, _ = synthetic_cli(tmp_path, monkeypatch)
        args.extend(["--output-events", str(tmp_path / "data/public/forbidden.gpkg")])
        assert run_conflicts.main(args) == 2
        assert not (tmp_path / "data/public").exists()

    @pytest.mark.parametrize("role", ["events", "cells", "report"])
    def test_missing_artifact_prevents_bundle_reuse(self, tmp_path, monkeypatch, role):
        args, _ = synthetic_cli(tmp_path, monkeypatch)
        assert run_conflicts.main(args) == 0
        paths = bundle_paths(tmp_path)
        paths[{"events": 0, "cells": 1, "report": 2}[role]].unlink()
        with pytest.raises(ValueError, match="incomplet"):
            run_conflicts.verify_conflict_bundle(*paths)

    def test_json_generation_failure_never_publishes_geopackages(self, tmp_path, monkeypatch):
        args, _ = synthetic_cli(tmp_path, monkeypatch)
        def fail(*args, **kwargs):
            raise OSError("ÉCHEC SYNTHÉTIQUE DU RAPPORT")
        monkeypatch.setattr(run_conflicts, "_write_json", fail)
        assert run_conflicts.main(args) == 2
        events, cells, _ = bundle_paths(tmp_path)
        assert not events.exists() and not cells.exists()

    def test_last_publication_failure_rolls_back_both_geopackages(self, tmp_path, monkeypatch):
        args, _ = synthetic_cli(tmp_path, monkeypatch)
        original = run_conflicts.os.link
        def fail_last(source, target):
            if str(target).endswith("mailles_conflits.gpkg"):
                raise OSError("ÉCHEC SYNTHÉTIQUE DE PUBLICATION")
            return original(source, target)
        monkeypatch.setattr(run_conflicts.os, "link", fail_last)
        assert run_conflicts.main(args) == 2
        events, cells, report = bundle_paths(tmp_path)
        assert not events.exists() and not cells.exists()
        assert json.loads(report.read_text())["run"]["status"] == "blocked"


class TestScientificCorrections:
    @pytest.mark.parametrize("crs", [2154, 4326])
    def test_event_crs_is_explicitly_harmonized_without_mutation(self, crs):
        detection = detect()
        detection.events = detection.events.to_crs(crs)
        original = detection.events.copy(deep=True)
        result = aggregate(detection)
        assert result.events.crs.to_epsg() == 2154
        assert result.events.geometry.iloc[0].distance(Point(X + 500, Y + 500)) < 1e-6
        assert json.loads(result.events.maille_ids.iloc[0]) == ["H1"]
        pd.testing.assert_frame_equal(detection.events, original)

    def test_missing_event_crs_blocks(self):
        detection = detect()
        detection.events = gpd.GeoDataFrame(pd.DataFrame(detection.events.drop(columns="geometry")),
                                            geometry=list(detection.events.geometry))
        with pytest.raises(InputValidationError, match="CRS absent"):
            aggregate(detection)

    @pytest.mark.parametrize("geometry", [Point(X + 3000, Y),
        LineString([(X + 500, Y + 500), (X + 3000, Y + 500)]),
        MultiLineString([[(X, Y), (X + 1, Y + 1)]])])
    def test_outside_or_incompatible_event_blocks(self, geometry):
        detection = detect()
        detection.events.geometry = [geometry]
        with pytest.raises(InputValidationError):
            aggregate(detection)

    @pytest.mark.parametrize("location,relation,status", [(500, "interieur", "croisement_detecte"),
                                                         (0, "frontiere", "non_concluant")])
    def test_territory_boundary_distinct_from_source_crossing(self, location, relation, status):
        detection = detect(roads=[LineString([(X - 100, Y + 500), (X + 1000, Y + 500)])],
                           corridors=[LineString([(X + location, Y + 100), (X + location, Y + 900)])])
        event = detection.events.iloc[0]
        assert event.territory_relation == relation and event.statut == status
        assert event.intersection_relation == "croisement_transversal"
        assert len(aggregate(detection).links) == 1

    def test_shared_cell_boundary_is_inside_territory(self):
        territory = frame([box(X, Y, X + 2000, Y + 1000)])
        detection = detect(roads=[LineString([(X + 900, Y + 500), (X + 1100, Y + 500)])],
                           corridors=[LineString([(X + 1000, Y + 100), (X + 1000, Y + 900)])], territory=territory)
        result = aggregate(detection, frame([CELL, box(X + 1000, Y, X + 2000, Y + 1000)], maille_id=["H1", "H2"]), territory)
        assert result.events.territory_relation.iloc[0] == "interieur"
        assert result.events.statut.iloc[0] == "croisement_detecte"
        assert result.links.relation_spatiale.tolist() == ["frontiere", "frontiere"]
        assert result.summary["distinct_events_observed"] == 1

    def test_event_touching_territory_boundary_but_with_interior_is_distinct(self):
        line = LineString([(X - 100, Y + 500), (X + 500, Y + 500)])
        event = detect(roads=[line], corridors=[line]).events.iloc[0]
        assert event.territory_relation == "interieur_et_frontiere"
        assert event.statut == "croisement_detecte"

    def test_pair_sensitivity_does_not_certify_each_disconnected_event(self):
        roads = MultiLineString([[(X + 200, Y + 200), (X + 800, Y + 200)],
                                 [(X + 499.95, Y + 800), (X + 500.05, Y + 800)]])
        paths = MultiLineString([[(X + 500, Y + 100), (X + 500, Y + 300)],
                                 [(X + 500, Y + 700), (X + 500, Y + 900)]])
        result = detect(roads=[roads], corridors=[paths], precision=IntersectionPrecision(1, "TEST SYNTHÉTIQUE", True))
        assert len(result.events) == 2
        assert not result.events.precision_sensitive.any()  # Le point robuste masque la perte du point fragile.
        assert set(result.events.precision_sensitivity_scope) == {"source_pair"}
        assert set(result.events.statut) == {"croisement_detecte"}
        # Une disparition globale d'une paire multi-événements ne localise pas non plus l'incertitude.
        measured = detect(roads=[roads], corridors=[paths], precision=IntersectionPrecision(1000, "TEST SYNTHÉTIQUE", True))
        assert measured.events.precision_sensitive.all()
        assert set(measured.events.statut) == {"croisement_detecte"}

    @pytest.mark.parametrize("status", ["conflit_potentiel", "obstacle_confirme"])
    def test_inconclusive_event_requires_documented_resolution(self, status):
        events = detect(precision=IntersectionPrecision(1, "TEST", False)).events
        evidence = EventEvidence(events.conflit_id.iloc[0], status, "TEST", "TEST", "TEST", "2026-10-30")
        with pytest.raises(InputValidationError, match="résolution"):
            qualify_events(events, [evidence])
        resolved = replace(evidence, localization_resolution_reference="TEST RÉSOLUTION", localization_validated_by="TEST EXPERT",
                           localization_validated_at="2026-10-30")
        qualified = qualify_events(events, [resolved])
        assert qualified.statut.iloc[0] == status
        assert qualified.precision_affichage.iloc[0] == "localisation_a_confirmer"  # Observation initiale préservée.
        record = json.loads(qualified.preuves.iloc[0])[0]
        assert record["previous_status"] == "non_concluant" and not record["authors_authenticated_by_software"]
        with pytest.raises(InputValidationError, match="Date de résolution"):
            qualify_events(events, [replace(resolved, localization_validated_at="invalide")])

    def test_boundary_contact_cannot_be_promoted_to_internal_obstacle(self):
        events = detect(roads=[LineString([(X - 100, Y + 500), (X + 100, Y + 500)])],
                        corridors=[LineString([(X, Y + 100), (X, Y + 900)])]).events
        evidence = EventEvidence(events.conflit_id.iloc[0], "obstacle_confirme", "TEST", "TEST", "TEST", "2026-10-30",
                                 localization_resolution_reference="TEST", localization_validated_by="TEST", localization_validated_at="2026-10-30")
        with pytest.raises(InputValidationError, match="frontière"):
            qualify_events(events, [evidence])

    def test_unknown_precision_requires_resolution_for_confirmed_obstacle(self):
        events = detect().events
        evidence = EventEvidence(events.conflit_id.iloc[0], "obstacle_confirme", "TEST", "TEST", "TEST", "2026-10-30")
        with pytest.raises(InputValidationError, match="résolution"):
            qualify_events(events, [evidence])

    def test_qualifications_preserve_previous_evidence(self):
        events = detect(precision=IntersectionPrecision(1, "TEST", True)).events
        evidence = EventEvidence(events.conflit_id.iloc[0], "conflit_potentiel", "TEST", "TEST", "TEST", "2026-10-30")
        first = qualify_events(events, [evidence])
        second = qualify_events(first, [replace(evidence, target_status="obstacle_confirme")])
        assert len(json.loads(second.preuves.iloc[0])) == 2

    def test_versioned_rule_interface_is_opt_in_and_has_no_production_rule(self):
        detection = detect(precision=IntersectionPrecision(1, "TEST", True))
        rule = PotentialConflictRule("REGLE-SYNTHETIQUE", "TEST-v1", "REF TEST", "CRITÈRE TEST", "VALIDATEUR TEST",
                                     "2026-10-30", {"routes.context.category": "CATEGORIE TEST"})
        assert apply_potential_conflict_rules(detection.events).equals(detection.events)
        assert apply_potential_conflict_rules(detection.events, [rule]).statut.iloc[0] == "croisement_detecte"
        events = detection.events.copy()
        observations = json.loads(events.observations.iloc[0])
        observations["routes"]["context"]["category"] = "CATEGORIE TEST"
        events["observations"] = json.dumps(observations)
        qualified = apply_potential_conflict_rules(events, [rule])
        assert qualified.statut.iloc[0] == "conflit_potentiel"
        assert json.loads(qualified.preuves.iloc[0])[0]["version"] == "TEST-v1"
        assert events.statut.iloc[0] == "croisement_detecte"
        for precision in ("precision_non_documentee", "localisation_a_confirmer"):
            unknown = events.copy()
            unknown.precision_affichage = precision
            assert apply_potential_conflict_rules(unknown, [rule]).statut.iloc[0] == "croisement_detecte"
        with pytest.raises(ValueError, match="version"):
            apply_potential_conflict_rules(events, [replace(rule, version="")])
        with pytest.raises(ValueError, match="contextuels"):
            apply_potential_conflict_rules(events, [replace(rule, context_equals={})])
        with pytest.raises(ValueError, match="dupliquée"):
            apply_potential_conflict_rules(events, [rule, rule])
