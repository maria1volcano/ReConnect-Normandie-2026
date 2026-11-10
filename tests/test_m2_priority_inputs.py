"""Validation amont sur sources et attestations exclusivement SYNTHÉTIQUES."""

from copy import deepcopy
from dataclasses import replace
import json

import pytest
from shapely.geometry import LineString, box

from analysis.detect_conflicts import EventEvidence, IntersectionPrecision, geometry_key, qualify_events
from analysis.evaluate_priorities import evaluate_priorities, normalize_diagnostics_by_family
from analysis.prepare_priority_inputs import (
    PriorityInputError, classify_ecological_stakes, derive_absence_evidence, derive_applicability,
    derive_positive_evidence, detect_assertion_conflicts, validate_diagnostic_inputs,
)
from m2_priority_helpers import PERIOD, diagnostic, inputs, review
from test_m2_conflicts import CELL, X, Y, coverage, detect, frame


@pytest.mark.parametrize("field,value,code", [
    ("diagnostic_id",True,"E_TYPE_INVALIDE"), ("diagnostic_id",False,"E_TYPE_INVALIDE"),
    ("diagnostic_id",float("nan"),"E_TYPE_INVALIDE"), ("diagnostic_id",float("inf"),"E_TYPE_INVALIDE"),
    ("diagnostic_id",1.0,"E_TYPE_INVALIDE"), ("diagnostic_id"," ","E_TYPE_INVALIDE"),
    ("enjeu_classe","tres_fort","E_TYPE_INVALIDE"), ("enjeu_classe",None,"E_TYPE_INVALIDE"),
    ("signal_pression",[],"E_TYPE_INVALIDE"), ("signal_pression","pression_forte","E_TYPE_INVALIDE"),
    ("validite_positive",1,"E_TYPE_INVALIDE"), ("validite_absence","false","E_TYPE_INVALIDE"),
    ("contradiction_bloquante",0,"E_TYPE_INVALIDE"), ("preuve_ids",'[]',"E_TYPE_INVALIDE"),
    ("source_objects",{},"E_TYPE_INVALIDE"), ("motifs_qualite",[None],"E_TYPE_INVALIDE"),
    ("applicabilite","non_applicable","E_TYPE_INVALIDE"), ("phenomene_id",True,"E_TYPE_INVALIDE"),
    ("methode_famille_id","METHODE-INVENTEE","E_METHODE_NON_AUTORISEE"),
    ("enjeu_methode_id","METHODE-INVENTEE","E_METHODE_NON_AUTORISEE"),
    ("preuve_ids",[],"E_PROUVE_POSITIVE_SANS_SOURCE"),
    ("preuve_ids",["ABSENT"],"E_REFERENCE_PREUVE_INVALIDE"),
    ("contradiction_reference",False,"E_TYPE_INVALIDE"),
    ("periode_reference",{"debut":"2026-12-31","fin":"2026-01-01"},"E_PERIODE_INVALIDE"),
    ("periode_reference",{"debut":"hier","fin":"demain"},"E_PERIODE_INVALIDE"),
    ("periode_reference","2026","E_PERIODE_INVALIDE"),
])
def test_malformed_diagnostics_block_with_stable_codes(field,value,code):
    cell,pilot = inputs()
    cell["diagnostics"][0][field] = value
    with pytest.raises(PriorityInputError) as error:
        validate_diagnostic_inputs(cell,pilot)
    assert error.value.code == code


@pytest.mark.parametrize("area", [-1,float("nan"),float("inf"),-float("inf"),True,None,"1000"])
def test_nonfinite_negative_or_non_numeric_surfaces_block(area):
    with pytest.raises(PriorityInputError) as error:
        validate_diagnostic_inputs(*inputs(study_area_m2=area))
    assert error.value.code == "E_SURFACE_INVALIDE"


@pytest.mark.parametrize("mutation,code", [
    ("missing_config","E_PERIMETRE_INVALIDE"), ("duplicate_family","E_PERIMETRE_INVALIDE"),
    ("empty_scope","E_PERIMETRE_INVALIDE"), ("unknown_version","E_PERIMETRE_INVALIDE"),
    ("unreferenced_method","E_PERIMETRE_INVALIDE"), ("missing_diagnostic_field","E_TYPE_INVALIDE"),
    ("unknown_proof","E_REFERENCE_PREUVE_INVALIDE"), ("unreferenced_contradiction","E_CONTRADICTION_SANS_REFERENCE"),
    ("positive_non_applicable","E_NON_APPLICABILITE_INCOHERENTE"),
    ("unvalidated_absence","E_ABSENCE_INCOHERENTE"), ("missing_area","E_TYPE_INVALIDE"),
    ("nan_metadata","E_TYPE_INVALIDE"),
])
def test_configuration_and_cross_field_invariants(mutation,code):
    cell,pilot = inputs()
    d = cell["diagnostics"][0]
    if mutation == "missing_config":
        pilot.pop("decision")
    elif mutation == "duplicate_family":
        pilot["familles_attendues"] *= 2
    elif mutation == "empty_scope":
        pilot["familles_attendues"] = []
    elif mutation == "unknown_version":
        pilot["priority_method_version"] = "INCONNUE"
    elif mutation == "unreferenced_method":
        pilot["references_methodes"].pop(d["methode_famille_id"])
    elif mutation == "missing_diagnostic_field":
        d.pop("periode_reference")
    elif mutation == "unknown_proof":
        pilot["preuves"] = {}
    elif mutation == "unreferenced_contradiction":
        d["contradiction_bloquante"] = True
    elif mutation == "positive_non_applicable":
        d["applicabilite"] = "non_applicable_documentee"
        d["applicabilite_reference"] = "REFERENCE-SYNTHETIQUE"
    elif mutation == "unvalidated_absence":
        d["signal_pression"] = "absence_validee"
    elif mutation == "nan_metadata":
        cell["metadonnees"] = {"erreur":float("nan")}
    else:
        cell.pop("study_area_m2")
    with pytest.raises(PriorityInputError) as error:
        evaluate_priorities(cell,pilot)
    assert error.value.code == code


def test_unknown_versions_need_a_trace_reason_and_are_not_fabricated():
    cell,pilot = inputs()
    cell["dataset_version"] = pilot["dataset_version"] = None
    with pytest.raises(PriorityInputError) as error:
        validate_diagnostic_inputs(cell,pilot)
    assert error.value.code == "E_PERIMETRE_INVALIDE"
    pilot["motifs_versions_inconnues"] = ["version_donnees_non_fournie"]
    assert evaluate_priorities(cell,pilot)["dataset_version"] is None


@pytest.mark.parametrize("mutation", ["missing", "duplicate_reference", "duplicate_registry", "bool_id", "period"])
def test_source_registry_references_uniqueness_and_periods(mutation):
    source = {"namespace":"SOURCE-SYNTHETIQUE", "id":1}
    cell,pilot = inputs([diagnostic(source_objects=[source])])
    if mutation == "missing":
        pilot["sources"] = []
    elif mutation == "duplicate_reference":
        cell["diagnostics"][0]["source_objects"].append(source)
    elif mutation == "duplicate_registry":
        pilot["sources"] *= 2
    elif mutation == "bool_id":
        cell["diagnostics"][0]["source_objects"][0]["id"] = True
    else:
        cell["diagnostics"][0]["periode_reference"] = dict(PERIOD)
        pilot["sources"][0]["periode_reference"] = {"debut":"2025-01-01","fin":"2025-12-31"}
    with pytest.raises(PriorityInputError) as error:
        validate_diagnostic_inputs(cell,pilot)
    assert error.value.code == ("E_PERIODE_INCOMPATIBLE" if mutation == "period" else "E_TYPE_INVALIDE" if mutation == "bool_id" else "E_REFERENCE_SOURCE_INVALIDE")


def test_normalization_preserves_multiple_diagnostics_per_family_and_missing_families():
    cell,pilot = inputs([diagnostic(diagnostic_id="B"),diagnostic()], families=["route_corridor","bocage"])
    groups = normalize_diagnostics_by_family(validate_diagnostic_inputs(cell,pilot))
    assert groups["bocage"] == []
    assert [d["diagnostic_id"] for d in groups["route_corridor"]] == ["A","B"]
    assert len(cell["diagnostics"]) == 2


def positive_review(event, **changes):
    return review(conflit_id=event.conflit_id, source_links_verified=True, scale_adequate=True,
                  localization_resolved=True, **changes)


def test_positive_qa_is_inactive_without_a_documented_review_and_never_promotes_2d():
    detection = detect(precision=IntersectionPrecision(1,"PRECISION-SYNTHETIQUE",True))
    event = detection.events.iloc[0]
    assert not derive_positive_evidence(event, crs=2154)["validite_positive"]
    result = derive_positive_evidence(event, crs=2154, review=positive_review(event))
    assert result["validite_positive"] and result["signal_pression"] == "croisement_detecte"
    assert not result["authors_authenticated_by_software"]


@pytest.mark.parametrize("status", ["conflit_potentiel","obstacle_confirme"])
def test_positive_qa_requires_real_qualification_structure_for_promoted_signals(status):
    detection = detect(precision=IntersectionPrecision(1,"PRECISION-SYNTHETIQUE",True))
    event = detection.events.iloc[0].copy()
    event["statut"] = status
    assert not derive_positive_evidence(event, crs=2154, review=positive_review(event))["validite_positive"]
    evidence = EventEvidence(event.conflit_id,status,"PREUVE-SYNTHETIQUE","CRITERE-SYNTHETIQUE","EXPERT-SYNTHETIQUE","2026-11-03")
    qualified = qualify_events(detection.events,[evidence]).iloc[0]
    assert derive_positive_evidence(qualified, crs=2154, review=positive_review(qualified))["validite_positive"]


def test_unknown_or_insufficient_precision_is_not_erased_by_a_review():
    for precision in (None,IntersectionPrecision(1,"PRECISION-SYNTHETIQUE",False)):
        event = detect(precision=precision).events.iloc[0]
        result = derive_positive_evidence(event, crs=2154, review=positive_review(event))
        assert not result["validite_positive"]
        assert "precision_localisation_insuffisante" in result["motifs_qualite"]


def test_external_resolution_preserves_original_location_limits():
    detection = detect(precision=IntersectionPrecision(1,"PRECISION-SYNTHETIQUE",False))
    event = detection.events.iloc[0]
    evidence = EventEvidence(event.conflit_id,"obstacle_confirme","PREUVE-SYNTHETIQUE","CRITERE-SYNTHETIQUE","EXPERT-SYNTHETIQUE","2026-11-03",
                             localization_resolution_reference="RESOLUTION-SYNTHETIQUE", localization_validated_by="EXPERT-SYNTHETIQUE",
                             localization_validated_at="2026-11-03")
    qualified = qualify_events(detection.events,[evidence]).iloc[0]
    result = derive_positive_evidence(qualified, crs=2154, review=positive_review(qualified))
    assert result["validite_positive"] and qualified.precision_affichage == "localisation_a_confirmer"
    stale = qualified.copy()
    proof = json.loads(stale.preuves)[0]
    proof["conflit_id"] = "AUTRE-EVENEMENT-SYNTHETIQUE"
    stale["preuves"] = json.dumps([proof])
    assert not derive_positive_evidence(stale, crs=2154, review=positive_review(stale))["validite_positive"]


def test_contextual_rule_trace_can_support_potential_but_never_confirms_an_obstacle():
    from analysis.detect_conflicts import PotentialConflictRule, apply_potential_conflict_rules
    detection = detect(precision=IntersectionPrecision(1,"PRECISION-SYNTHETIQUE",True))
    events = detection.events.copy()
    observations = json.loads(events.observations.iloc[0])
    observations["routes"]["context"]["category"] = "CATEGORIE-SYNTHETIQUE"
    events["observations"] = json.dumps(observations)
    rule = PotentialConflictRule("REGLE-SYNTHETIQUE","VERSION-SYNTHETIQUE","REFERENCE-SYNTHETIQUE","CRITERE-SYNTHETIQUE",
                                 "EXPERT-SYNTHETIQUE","2026-11-03",{"routes.context.category":"CATEGORIE-SYNTHETIQUE"})
    event = apply_potential_conflict_rules(events,[rule]).iloc[0]
    assert event.statut == "conflit_potentiel"
    assert derive_positive_evidence(event, crs=2154, review=positive_review(event))["validite_positive"]


def test_positive_review_for_another_event_blocks():
    event = detect().events.iloc[0]
    document = positive_review(event)
    document["conflit_id"] = "AUTRE-SYNTHETIQUE"
    with pytest.raises(PriorityInputError) as error:
        derive_positive_evidence(event, crs=2154, review=document)
    assert error.value.code == "E_REFERENCE_PREUVE_INVALIDE"


@pytest.mark.parametrize("mutation", ["geometry", "territory_boundary", "crs", "source_link", "scale", "period", "precision_contract"])
def test_positive_geometry_provenance_and_scale_limits(mutation):
    event = detect(precision=IntersectionPrecision(1,"PRECISION-SYNTHETIQUE",True)).events.iloc[0].copy()
    document = positive_review(event)
    crs = 2154
    if mutation == "geometry":
        event["geometry"] = None
    elif mutation == "territory_boundary":
        event["territory_relation"] = "frontiere"
    elif mutation == "crs":
        crs = None
    elif mutation == "source_link":
        document["source_links_verified"] = False
    elif mutation == "scale":
        document["scale_adequate"] = False
    elif mutation == "period":
        document["periode_reference"] = None
    else:
        event["precision_reference"] = None
    result = derive_positive_evidence(event, crs=crs, review=document)
    assert not result["validite_positive"] and result["motifs_qualite"]


def absence_review(geometry=CELL):
    return review(scope_geometry_key=geometry_key(geometry),categories_covered=True, subframes_covered=True,
                  covered_categories=["CATEGORIE-SYNTHETIQUE"],covered_subframes=["SOUS-TRAME-SYNTHETIQUE"],
                  source_ids={"routes":"SOURCE-SYNTHETIQUE-routes","corridors":"SOURCE-SYNTHETIQUE-corridors"},
                  source_periods={"routes":dict(PERIOD),"corridors":dict(PERIOD)})


def absence(detection, **changes):
    kwargs = {"crs":2154, "required_sources":{"routes":"SOURCE-SYNTHETIQUE-routes","corridors":"SOURCE-SYNTHETIQUE-corridors"},
              "required_categories":["CATEGORIE-SYNTHETIQUE"],"required_subframes":["SOUS-TRAME-SYNTHETIQUE"],
              "domain_review":absence_review(), "territory":frame([CELL])}
    kwargs.update(changes)
    return derive_absence_evidence(detection, CELL, **kwargs)


def test_validated_spatial_thematic_and_temporal_absence_is_possible():
    detection = detect(roads=[],corridors=[],route_coverage=coverage("routes"),corridor_coverage=coverage("corridors"))
    result = absence(detection)
    assert result["validite_absence"] and result["absence_etablie"]
    assert result["signal_pression"] == "absence_validee" and result["nb_evenements_observes"] == 0


def test_positive_and_negative_capacities_can_coexist_without_asserting_absence():
    detection = detect(precision=IntersectionPrecision(1,"PRECISION-SYNTHETIQUE",True),
                       route_coverage=coverage("routes"),corridor_coverage=coverage("corridors"))
    event = detection.events.iloc[0]
    assert derive_positive_evidence(event,crs=2154,review=positive_review(event))["validite_positive"]
    result = absence(detection)
    assert result["validite_absence"] and not result["absence_etablie"]
    assert result["signal_pression"] is None and result["nb_evenements_observes"] == 1


@pytest.mark.parametrize("problem", ["no_analysis","unknown","partial","theme","subframes","period","no_review","wrong_scope","wrong_sources","no_territory","category_code","subframe_code","missing_domain"])
def test_missing_conditions_never_become_a_validated_absence(problem):
    detection = detect(roads=[],corridors=[],route_coverage=coverage("routes"),corridor_coverage=coverage("corridors"))
    document = absence_review()
    options = {}
    if problem == "no_analysis":
        detection.analysis_performed = False
    elif problem == "unknown":
        from analysis.indicateurs_enjeux import CoverageEvidence
        detection.route_coverage = CoverageEvidence()
    elif problem == "partial":
        detection.route_coverage = coverage("routes", footprint=frame([box(X,Y,X+500,Y+1000)]))
    elif problem in {"theme","subframes"}:
        document["categories_covered" if problem == "theme" else "subframes_covered"] = False
    elif problem == "period":
        document["source_periods"]["routes"] = {"debut":"2025-01-01","fin":"2025-12-31"}
    elif problem == "wrong_scope":
        document["scope_geometry_key"] = geometry_key(box(X,Y,X+500,Y+1000))
    elif problem == "wrong_sources":
        document["source_ids"]["routes"] = "AUTRE-SOURCE-SYNTHETIQUE"
    elif problem == "no_territory":
        options["territory"] = None
    elif problem == "category_code":
        document["covered_categories"] = []
    elif problem == "subframe_code":
        document["covered_subframes"] = []
    elif problem == "missing_domain":
        options["required_categories"] = None
    result = absence(detection,domain_review=None if problem == "no_review" else document,**options)
    assert not result["validite_absence"] and not result["absence_etablie"]
    assert result["signal_pression"] == "non_evalue"
    assert "absence_non_demontree" in result["motifs_qualite"]


def test_coverage_metadata_is_rechecked_and_not_just_trusted_from_previous_flags():
    detection = detect(roads=[],corridors=[],route_coverage=coverage("routes"),corridor_coverage=coverage("corridors"))
    detection.route_coverage = replace(detection.route_coverage,territory_sha256="AUTRE-TERRITOIRE-SYNTHETIQUE")
    with pytest.raises(PriorityInputError) as error:
        absence(detection)
    assert error.value.code == "E_PREUVE_INVALIDE"


def test_coverage_global_confirmation_cannot_be_reused_outside_territory():
    detection = detect(roads=[],corridors=[],route_coverage=coverage("routes"),corridor_coverage=coverage("corridors"))
    outside = box(X+2000,Y,X+3000,Y+1000)
    with pytest.raises(PriorityInputError) as error:
        derive_absence_evidence(detection,outside,crs=2154,required_sources=absence_review()["source_ids"],
                                domain_review=absence_review(outside),territory=frame([CELL]))
    assert error.value.code == "E_PERIMETRE_INVALIDE"


def assertion(identity, conclusion, **changes):
    result = {"assertion_id":identity,"propriete":"FRANCHISSEMENT-SYNTHETIQUE","objet_id":"OBJET-SYNTHETIQUE",
              "emprise_id":"EMPRISE-SYNTHETIQUE","periode_reference":dict(PERIOD),"reference":f"REF-SYNTHETIQUE-{identity}",
              "validee":True,"conclusion":conclusion}
    result.update(changes)
    return result


def test_only_documented_comparable_incompatible_assertions_produce_a_contradiction():
    claims = [assertion("A","presence"),assertion("B","absence")]
    with pytest.raises(PriorityInputError) as error:
        detect_assertion_conflicts(claims)
    assert error.value.code == "E_CONTRADICTION_SANS_REFERENCE"
    result = detect_assertion_conflicts(claims,decision_reference="DECISION-SYNTHETIQUE")
    assert result["contradiction_bloquante"] is True and result["contradiction_reference"] == "DECISION-SYNTHETIQUE"
    assert result == detect_assertion_conflicts(claims[::-1],decision_reference="DECISION-SYNTHETIQUE")


@pytest.mark.parametrize("field,value", [("propriete","AUTRE-SYNTHETIQUE"),("objet_id","AUTRE-SYNTHETIQUE"),
    ("emprise_id","AUTRE-SYNTHETIQUE"),("conclusion","presence"),
    ("periode_reference",{"debut":"2025-01-01","fin":"2025-12-31"})])
def test_distinct_assertions_or_periods_are_not_contradictions(field,value):
    claims = [assertion("A","presence"),assertion("B","absence",**{field:value})] if field != "conclusion" else [assertion("A","presence"),assertion("B",value)]
    result = detect_assertion_conflicts(claims)
    assert result["contradiction_bloquante"] is False


@pytest.mark.parametrize("missing", ["propriete","objet_id","emprise_id","periode_reference","reference"])
def test_insufficient_assertion_metadata_never_claims_no_contradiction(missing):
    claims = [assertion("A","presence"),assertion("B","absence")]
    claims[0][missing] = None
    result = detect_assertion_conflicts(claims)
    assert result["contradiction_bloquante"] is None and result["etat_controle"] == "non_evalue"


def test_overlapping_but_different_periods_require_documented_comparability():
    result = detect_assertion_conflicts([assertion("A","presence"),assertion("B","absence",
        periode_reference={"debut":"2026-03-01","fin":"2026-08-31"})])
    assert result["contradiction_bloquante"] is None
    assert detect_assertion_conflicts([])["contradiction_bloquante"] is None


def test_stakes_and_applicability_interfaces_do_not_infer_real_classes():
    assert derive_applicability()["applicabilite"] == "inconnue"
    assert classify_ecological_stakes()["enjeu_classe"] == "inconnu"
    assert derive_applicability(review(valeur="non_applicable_documentee"))["applicabilite_reference"] == "REFERENCE-SYNTHETIQUE"
    assert classify_ecological_stakes(review(valeur="fort"))["enjeu_methode_id"] == "METHODE-SYNTHETIQUE"
    with pytest.raises(PriorityInputError):
        classify_ecological_stakes(review(valeur="reservoir"))
    with pytest.raises(PriorityInputError):
        derive_applicability({"valeur":"non_applicable_documentee"})


def test_end_to_end_synthetic_qa_to_ds_without_export_or_action_engine():
    detection = detect(roads=[],corridors=[],route_coverage=coverage("routes"),corridor_coverage=coverage("corridors"))
    qa = absence(detection)
    d = diagnostic(signal_pression=qa["signal_pression"],validite_positive=False,validite_absence=qa["validite_absence"],
                   preuve_ids=[],motifs_qualite=qa["motifs_qualite"])
    result = evaluate_priorities(*inputs([d]))
    assert result["regles_diagnostics"] == {"A":"D9"} and result["regle_appliquee"] == "S3"
    assert result["priorite_examen"] == "faible"  # Convention synthétique, pas diagnostic réel.
