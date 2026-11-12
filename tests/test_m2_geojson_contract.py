"""Contrats M4 et exemples exclusivement SYNTHÉTIQUES, sans diagnostic territorial."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sqlite3

import geopandas as gpd
from jsonschema import ValidationError
import pandas as pd
import pytest
from shapely.geometry import LineString, Point, Polygon, box

from analysis.aggregate_conflicts import aggregate_conflicts
from analysis.detect_conflicts import SourceFields, canonical_json, detect_route_corridor_conflicts
from analysis.export_m2_contract import (
    ConflictDisclosure, prepare_m2_contract, validate_m2_contract,
)
from test_m2_conflicts import X, Y, METHOD, aggregate, coverage, detect, frame, synthetic_cli, bundle_paths
from analysis import run_conflicts

FIXTURES = Path(__file__).parent / "fixtures/m2"
VERSIONS = {"grid_version": "GRILLE-SYNTHETIQUE", "method_version": METHOD, "dataset_version": None}


def synthetic_contract():
    """Quatre mailles, quatre événements dont un partagé, un contact et un masqué."""
    cells = frame([box(X + i*1000, Y, X + (i+1)*1000, Y + 1000) for i in range(4)],
                  maille_id=["H1", "H2", "H3", "H4"])
    territory = frame([box(X, Y, X + 4000, Y + 1000)])
    complete_area = frame([box(X, Y, X + 3000, Y + 1000)])
    centers = [(300, 300), (1000, 500), (1400, 800), (1700, 300)]
    roads = frame([LineString([(X+x-100, Y+y), (X+x+100, Y+y)]) for x, y in centers],
                  rid=["R-SYNTH-1", "R-SYNTH-2", "R-SYNTH-3", "R-SYNTH-4"],
                  secret=["DONNÉE PRIVÉE SYNTHÉTIQUE"]*4)
    corridors = frame([LineString([(X+x, Y+y if i == 2 else Y+y-100), (X+x, Y+y+100)])
                       for i, (x, y) in enumerate(centers)], cid=[f"C-SYNTH-{i}" for i in range(4)])
    detection = detect_route_corridor_conflicts(roads, corridors, territory,
        route_fields=SourceFields("rid"), corridor_fields=SourceFields("cid"), method_version=METHOD,
        route_coverage=coverage("routes", territory, complete_area),
        corridor_coverage=coverage("corridors", territory, complete_area))
    result = aggregate_conflicts(cells, territory, detection)
    policies = {event.conflit_id: ConflictDisclosure("exacte", "AUTORISATION SYNTHÉTIQUE", source_ids_allowed=True)
                for event in result.events.itertuples() if event.geometry.x != X + 1700}
    return result, policies


def proposed_pair():
    result, policies = synthetic_contract()
    return prepare_m2_contract(result, versions=VERSIONS, test_data=True,
                               run_id="RUN-SYNTHETIQUE-M2-M4", disclosure=policies)


def fixture_pair():
    return tuple(json.loads((FIXTURES / f"synthetic_{name}.geojson").read_text(encoding="utf-8"))
                 for name in ("mailles", "conflits"))


def test_fixtures_satisfy_both_schemas_geography_and_reciprocal_links():
    mailles, conflits = fixture_pair()
    assert validate_m2_contract(mailles, conflits) == {"mailles": 4, "evenements_distincts_observes": 4, "relations_spatiales": 5}
    assert (mailles, conflits) == proposed_pair()
    assert mailles["test_data"] is conflits["test_data"] is True


def test_examples_cover_all_requested_cases_and_no_priority_is_invented():
    mailles, conflits = fixture_pair()
    cells = {f["properties"]["maille_id"]: f["properties"] for f in mailles["features"]}
    assert len(cells["H1"]["conflit_ids"]) == 2
    assert cells["H3"]["conflit_ids"] == [] and cells["H3"]["indicateurs"]["nb_evenements"] == 0
    assert cells["H4"]["indicateurs"]["nb_evenements"] is None
    assert cells["H4"]["qualite"]["fiabilite"] == "observations_completude_non_etablie"
    assert all(c["priorite_examen"] == {"etat": "non_calculee", "valeur": None} for c in cells.values())
    assert any(f["properties"]["statut"] == "non_concluant" for f in conflits["features"])
    assert any(f["geometry"] is None for f in conflits["features"])
    assert sum(c["indicateurs"]["nb_evenements_observes"] for c in cells.values()) == 5
    assert len(conflits["features"]) == 4


def test_default_disclosure_hides_geometry_source_ids_and_all_private_text():
    result, _ = synthetic_contract()
    result.events["limites"] = '["SECRET INTERNE SYNTHÉTIQUE"]'
    result.events["preuves"] = '[{"reference":"SECRET INTERNE SYNTHÉTIQUE"}]'
    mailles, conflits = prepare_m2_contract(result, versions=VERSIONS, test_data=True)
    assert all(f["geometry"] is None and f["properties"]["source_ids"] == [] for f in conflits["features"])
    serialized = canonical_json([mailles, conflits])
    for private in ("DONNÉE PRIVÉE", "SECRET INTERNE", '"secret"', '"observations"', '"source_objects"', '"preuves"'):
        assert private not in serialized


def test_projection_has_longitude_first_and_preserves_metric_inputs():
    result, policies = synthetic_contract()
    before = result.events.copy(deep=True)
    mailles, conflits = prepare_m2_contract(result, versions=VERSIONS, test_data=True, disclosure=policies)
    exact = next(f for f in conflits["features"] if f["geometry"] is not None)
    original = result.events.loc[result.events.conflit_id == exact["properties"]["conflit_id"]]
    expected = original.to_crs("OGC:CRS84").geometry.iloc[0]
    assert exact["geometry"]["coordinates"] == [expected.x, expected.y]
    assert -2 < expected.x < 3 and 48 < expected.y < 51
    pd.testing.assert_frame_equal(result.events, before)
    assert "crs" not in mailles and "crs" not in conflits


def test_source_object_mapping_becomes_structured_array():
    result, policies = synthetic_contract()
    _, conflits = prepare_m2_contract(result, versions=VERSIONS, test_data=True, disclosure=policies)
    for f in conflits["features"]:
        if f["properties"]["source_ids"]:
            assert {item["role"] for item in f["properties"]["source_ids"]} == {"routes", "corridors"}
            assert all(set(item) == {"role", "id"} for item in f["properties"]["source_ids"])


def test_explicit_generalized_geometry_requires_reference_and_crs():
    result, _ = synthetic_contract()
    identity = result.events.conflit_id.iloc[0]
    generalized = box(X + 200, Y + 200, X + 800, Y + 800)
    policy = ConflictDisclosure("generalisee", "DÉCISION SYNTHÉTIQUE", generalized, "EPSG:2154")
    mailles, conflits = prepare_m2_contract(result, versions=VERSIONS, test_data=True, disclosure={identity: policy})
    event = next(f for f in conflits["features"] if f["properties"]["conflit_id"] == identity)
    assert event["geometry"]["type"] == "Polygon"
    assert event["properties"]["precision_affichage"] == "localisation_generalisee"
    for invalid in (replace(policy, crs=None), replace(policy, reference=None), replace(policy, geometry=None)):
        with pytest.raises(ValueError):
            prepare_m2_contract(result, versions=VERSIONS, test_data=True, disclosure={identity: invalid})


@pytest.mark.parametrize("policy", [ConflictDisclosure("exacte"), ConflictDisclosure("masquee", source_ids_allowed=True),
                                   ConflictDisclosure("inconnu")])
def test_disclosure_needs_explicit_valid_decision(policy):
    result, _ = synthetic_contract()
    with pytest.raises(ValueError):
        prepare_m2_contract(result, versions=VERSIONS, test_data=True,
                            disclosure={result.events.conflit_id.iloc[0]: policy})


def test_production_export_is_disabled_and_no_file_is_written(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result, _ = synthetic_contract()
    with pytest.raises(ValueError, match="production désactivé"):
        prepare_m2_contract(result, versions=VERSIONS, test_data=False)
    prepare_m2_contract(result, versions=VERSIONS, test_data=True)
    assert list(tmp_path.iterdir()) == []


def test_reordered_input_rows_have_identical_canonical_serialization():
    result, policies = synthetic_contract()
    pair = prepare_m2_contract(result, versions=VERSIONS, test_data=True, disclosure=policies)
    result.events = result.events.iloc[::-1]
    result.cells = result.cells.iloc[::-1]
    result.links = result.links.iloc[::-1]
    assert canonical_json(pair) == canonical_json(prepare_m2_contract(result, versions=VERSIONS, test_data=True, disclosure=policies))


@pytest.mark.parametrize("field", ["conflit_ids", "action_ids", "diagnostics"])
def test_stringified_arrays_are_rejected_on_cells(field):
    mailles, conflits = fixture_pair()
    p = mailles["features"][0]["properties"]
    p[field] = json.dumps(p[field])
    with pytest.raises(ValidationError):
        validate_m2_contract(mailles, conflits)


@pytest.mark.parametrize("field", ["maille_ids", "source_ids", "limites"])
def test_stringified_arrays_are_rejected_on_events(field):
    mailles, conflits = fixture_pair()
    p = conflits["features"][0]["properties"]
    p[field] = json.dumps(p[field])
    with pytest.raises(ValidationError):
        validate_m2_contract(mailles, conflits)


@pytest.mark.parametrize("mutation", ["missing_event", "missing_cell", "reciprocal", "duplicate_cell", "duplicate_event", "duplicate_link", "wrong_total", "local_sum_total", "wrong_method", "private_property"])
def test_invalid_contract_or_cross_references_are_rejected(mutation):
    mailles, conflits = fixture_pair()
    if mutation == "missing_event":
        mailles["features"][0]["properties"]["conflit_ids"][0] = "ABSENT-SYNTHETIQUE"
    elif mutation == "missing_cell":
        conflits["features"][0]["properties"]["maille_ids"].append("ABSENT-SYNTHETIQUE")
    elif mutation == "reciprocal":
        shared = next(f for f in conflits["features"] if len(f["properties"]["maille_ids"]) == 2)
        shared["properties"]["maille_ids"].pop()
    elif mutation.startswith("duplicate_"):
        if mutation == "duplicate_link":
            ids = conflits["features"][0]["properties"]["maille_ids"]
            ids.append(ids[0])
        else:
            features = (mailles if mutation == "duplicate_cell" else conflits)["features"]
            features.append(deepcopy(features[0]))
    elif mutation in {"wrong_total", "local_sum_total"}:
        for payload in (mailles, conflits):
            payload["resume"]["evenements_distincts_observes"] = 999 if mutation == "wrong_total" else 5
    elif mutation == "wrong_method":
        conflits["features"][0]["properties"]["method_version"] = "AUTRE TEST"
    else:
        conflits["features"][0]["properties"]["observations"] = "SECRET TEST"
    with pytest.raises((ValueError, ValidationError)):
        validate_m2_contract(mailles, conflits)


@pytest.mark.parametrize("geometry", [
    {"type": "Point", "coordinates": [500000, 6900000]},
    {"type": "Point", "coordinates": [1, 49, 3]},
    {"type": "Point", "coordinates": [float("nan"), 49]},
    {"type": "Polygon", "coordinates": [[[1,49],[2,50],[1,50],[2,49],[1,49]]]},
    {"type": "Polygon", "coordinates": [[[1,49],[2,49],[2,50],[1,50]]]},
])
def test_invalid_or_non_geographic_geometries_are_rejected(geometry):
    mailles, conflits = fixture_pair()
    event = next(f for f in conflits["features"] if f["geometry"] is not None)
    event["geometry"] = geometry
    with pytest.raises((ValueError, ValidationError)):
        validate_m2_contract(mailles, conflits)


def test_schema_preserves_non_calculated_and_indeterminate_priority_states():
    mailles, conflits = fixture_pair()
    mailles["features"][0]["properties"]["priorite_examen"]["etat"] = "indeterminee"
    validate_m2_contract(mailles, conflits)
    mailles["features"][0]["properties"]["priorite_examen"]["valeur"] = 1
    with pytest.raises(ValidationError):
        validate_m2_contract(mailles, conflits)


def test_geojson_preparation_after_verified_geopackage_roundtrip(tmp_path, monkeypatch):
    args, _ = synthetic_cli(tmp_path, monkeypatch)
    assert run_conflicts.main(args) == 0
    payload = run_conflicts.verify_conflict_bundle(*bundle_paths(tmp_path))
    result = aggregate(detect())
    events_path, cells_path, _ = bundle_paths(tmp_path)
    result.events = gpd.read_file(events_path, layer="conflits_candidates")
    result.cells = gpd.read_file(cells_path, layer="mailles_conflits")
    result.summary = payload["run"]["summary"]
    mailles, conflits = prepare_m2_contract(result, versions={k: payload["run"][k] for k in VERSIONS}, test_data=True)
    assert isinstance(mailles["features"][0]["properties"]["conflit_ids"], list)
    assert isinstance(conflits["features"][0]["properties"]["maille_ids"], list)


def test_no_analysis_and_empty_events_keep_null_counts():
    result = aggregate_conflicts(frame([box(X, Y, X+1000, Y+1000)], maille_id=[1]),
                                 frame([box(X, Y, X+1000, Y+1000)]), None)
    mailles, conflits = prepare_m2_contract(result, versions={k:None for k in VERSIONS}, test_data=True)
    assert conflits["features"] == []
    assert mailles["features"][0]["properties"]["indicateurs"]["nb_evenements_observes"] is None
    assert mailles["resume"]["evenements_distincts_observes"] is None


@pytest.mark.parametrize("mutation", ["invalid_owner", "wrong_owner", "wrong_relation"])
def test_bundle_checks_spatial_relations_even_with_updated_hash(tmp_path, mutation):
    result, _ = synthetic_contract()
    paths = {"events":tmp_path / "events.gpkg", "cells":tmp_path / "cells.gpkg", "report":tmp_path / "report.json"}
    run_conflicts.publish_conflict_bundle(result, {"run_id":"TEST SYNTHÉTIQUE", **VERSIONS}, paths)
    with sqlite3.connect(paths["cells"]) as connection:
        if mutation == "invalid_owner":
            connection.execute("UPDATE liens_mailles_conflits SET canonical_owner=2 WHERE canonical_owner=1")
        elif mutation == "wrong_owner":
            shared = result.links.groupby("conflit_id").size().loc[lambda s:s == 2].index[0]
            connection.execute("UPDATE liens_mailles_conflits SET canonical_owner=1-canonical_owner WHERE conflit_id=?", (shared,))
        else:
            connection.execute("UPDATE liens_mailles_conflits SET relation_spatiale='frontiere' WHERE relation_spatiale='interieur'")
    payload = json.loads(paths["report"].read_text())
    payload["run"]["output_sha256"]["cells"] = run_conflicts._sha256(paths["cells"])
    paths["report"].write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError):
        run_conflicts.verify_conflict_bundle(paths["events"], paths["cells"], paths["report"])


def test_masked_geometry_cannot_be_accidentally_exposed():
    mailles, conflits = fixture_pair()
    masked = next(f for f in conflits["features"] if f["geometry"] is None)
    masked["geometry"] = {"type":"Point", "coordinates":[1,49]}
    with pytest.raises(ValidationError):
        validate_m2_contract(mailles, conflits)


def test_null_and_integer_grid_identifiers_are_preserved_without_stringification():
    result = aggregate(detect(), frame([box(X, Y, X+1000, Y+1000)], maille_id=[42]))
    mailles, conflits = prepare_m2_contract(result, versions=VERSIONS, test_data=True)
    assert mailles["features"][0]["properties"]["maille_id"] == 42
    assert conflits["features"][0]["properties"]["maille_ids"] == [42]
    assert mailles["features"][0]["properties"]["dataset_version"] is None


def test_multipolygon_cell_and_clipped_outside_cell_are_supported():
    from shapely.geometry import MultiPolygon
    first = box(X,Y,X+400,Y+1000)
    second = box(X+600,Y,X+1000,Y+1000)
    territory = frame([MultiPolygon([first, second])])
    detection = detect(territory=territory, roads=[], corridors=[])
    result = aggregate(detection, frame([territory.geometry.iloc[0], box(X+2000,Y,X+3000,Y+1000)], maille_id=["H1","H2"]), territory)
    mailles, conflits = prepare_m2_contract(result, versions=VERSIONS, test_data=True)
    assert mailles["features"][0]["geometry"]["type"] == "MultiPolygon"
    assert mailles["features"][1]["geometry"] is None
    assert mailles["features"][1]["properties"]["statut_analyse"] == "hors_territoire"
