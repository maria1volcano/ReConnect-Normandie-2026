"""Audit d'intégration M2 : géométries, preuves et décisions SYNTHÉTIQUES seulement."""

from copy import deepcopy
from dataclasses import asdict, replace
import json

import geopandas as gpd
import pandas as pd
import pytest
from shapely.affinity import translate

from analysis.detect_conflicts import (
    EventEvidence, IntersectionPrecision, PotentialConflictRule, apply_potential_conflict_rules,
    event_evidence_binding, qualify_events,
)
from analysis.evaluate_priorities import evaluate_priorities
from analysis.export_priority_results import prepare_priority_result_json
from analysis.prepare_priority_inputs import (
    PriorityInputError, derive_positive_evidence, detect_assertion_conflicts,
    integrate_assertion_control, prepare_route_corridor_diagnostic,
)
from m2_priority_helpers import diagnostic, inputs
from test_m2_conflicts import aggregate, detect
from test_m2_priority_inputs import absence, assertion, positive_review


def unknown_control():
    return detect_assertion_conflicts([])


def negative_control():
    return detect_assertion_conflicts([assertion("A","presence"), assertion("B","presence")])


def confirmed_control():
    return detect_assertion_conflicts([assertion("A","presence"), assertion("B","absence")],
                                     decision_reference="DECISION-CONTRADICTION-SYNTHETIQUE")


def integrate(d, control, *, cible="pression", independent=False):
    return integrate_assertion_control(d, control, cible=cible, portee_reference="PORTEE-SYNTHETIQUE",
        preuve_ids_independantes=list(d["preuve_ids"]) if independent else [],
        independance_reference="EXAMEN-INDEPENDANCE-SYNTHETIQUE" if independent else None)


def test_unknown_control_is_retained_and_dependent_claim_is_quarantined():
    original = diagnostic()
    before = deepcopy(original)
    d = integrate(original, unknown_control())
    result = evaluate_priorities(*inputs([d]))
    assert original == before
    assert d["contradiction_bloquante"] is None
    assert d["controle_contradictions"]["entree_avant_controle"]["signal_pression"] == "conflit_potentiel"
    assert result["regles_diagnostics"] == {"A":"D3"}
    assert result["priorite_examen"] == "indeterminee" and result["couverture_synthese"] == "partielle"
    assert "controle_contradiction_non_evalue" in result["motifs_limites"]
    assert result["diagnostics"][0]["entree"]["contradiction_bloquante"] is None


def test_independent_reliable_evidence_remains_visible_with_partial_coverage():
    d = integrate(diagnostic(), unknown_control(), independent=True)
    result = evaluate_priorities(*inputs([d]))
    assert result["priorite_examen"] == "elevee" and result["regles_diagnostics"] == {"A":"D5"}
    assert result["couverture_synthese"] == "partielle"
    assert result["diagnostic_ids_justificatifs"] == ["A"]
    assert result["diagnostics"][0]["controle_contradictions"]["contradiction_bloquante"] is None


@pytest.mark.parametrize("control_factory,rule,coverage", [(negative_control,"D5","complete"),
                                                         (confirmed_control,"D1","partielle")])
def test_negative_and_confirmed_controls_integrate_without_changing_d_rules(control_factory,rule,coverage):
    d = integrate(diagnostic(), control_factory())
    result = evaluate_priorities(*inputs([d]))
    assert result["regles_diagnostics"] == {"A":rule} and result["couverture_synthese"] == coverage
    assert d["contradiction_bloquante"] is (rule == "D1")


def test_a_different_unknown_family_does_not_hide_a_reliable_high_signal():
    secondary = diagnostic(diagnostic_id="B", famille_id="bocage",methode_famille_id="METHODE-FAMILLE-SYNTHETIQUE-bocage")
    result = evaluate_priorities(*inputs([diagnostic(),integrate(secondary,unknown_control())],families=["route_corridor","bocage"]))
    assert result["priorite_examen"] == "elevee" and result["diagnostic_ids_non_evalues"] == ["B"]
    assert "controle_contradiction_non_evalue" in result["motifs_limites"]


def test_unknown_control_affecting_absence_cannot_produce_low_priority():
    d = diagnostic(signal_pression="absence_validee",validite_positive=False,validite_absence=True,preuve_ids=[])
    result = evaluate_priorities(*inputs([integrate(d,unknown_control())]))
    assert result["priorite_examen"] == "indeterminee" and result["regles_diagnostics"] == {"A":"D3"}


def test_unknown_applicability_control_is_not_cured_by_pressure_evidence():
    d = integrate(diagnostic(),unknown_control(),cible="applicabilite",independent=True)
    assert d["applicabilite"] == "inconnue"
    result = evaluate_priorities(*inputs([d]))
    assert result["regles_diagnostics"] == {"A":"D1"}
    assert result["motifs_principaux_diagnostics"] == {"A":"applicabilite_inconnue"}


@pytest.mark.parametrize("mutation,code", [
    ("wrong_diagnostic","E_REFERENCE_PREUVE_INVALIDE"), ("wrong_state","E_TYPE_INVALIDE"),
    ("wrong_target","E_TYPE_INVALIDE"), ("no_scope_reference","E_TYPE_INVALIDE"),
    ("unknown_independent_proof","E_REFERENCE_PREUVE_INVALIDE"),
    ("no_independence_reference","E_TYPE_INVALIDE"), ("forged_usable_claim","E_CONTROLE_CONTRADICTION_NON_RESOLU"),
])
def test_invalid_control_integration_cannot_silently_turn_unknown_into_false(mutation,code):
    d = integrate(diagnostic(),unknown_control(),independent=True)
    control = d["controle_contradictions"]
    if mutation == "wrong_diagnostic": control["diagnostic_id"] = "AUTRE-SYNTHETIQUE"
    elif mutation == "wrong_state": control["etat_controle"] = "controle"
    elif mutation == "wrong_target": control["cible"] = []
    elif mutation == "no_scope_reference": control["portee_reference"] = None
    elif mutation == "unknown_independent_proof": control["preuve_ids_independantes"] = ["PREUVE-ABSENTE"]
    elif mutation == "no_independence_reference": control["independance_reference"] = None
    else: control["preuve_ids_independantes"] = []
    with pytest.raises(PriorityInputError) as error:
        evaluate_priorities(*inputs([d]))
    assert error.value.code == code


def non_applicable():
    return diagnostic(diagnostic_id="B",applicabilite="non_applicable_documentee",applicabilite_reference="DOMAINE-SYNTHETIQUE",
                      enjeu_classe="inconnu",enjeu_methode_id=None,signal_pression="non_evalue",validite_positive=False,preuve_ids=[])


@pytest.mark.parametrize("control_factory", [confirmed_control,unknown_control])
def test_disputed_non_applicability_cannot_be_hidden_by_d0(control_factory):
    with pytest.raises(PriorityInputError) as error:
        integrate(non_applicable(),control_factory(),cible="applicabilite")
    assert error.value.code == "E_APPLICABILITE_CONTRADICTOIRE"


def test_documented_contradiction_outside_applicability_preserves_d0():
    d = integrate(non_applicable(),confirmed_control(),cible="autre_affirmation")
    result = evaluate_priorities(*inputs([d]))
    assert result["regles_diagnostics"] == {"B":"D0"}
    assert "contradiction_hors_applicabilite" in result["motifs_limites"]
    assert result["couverture_synthese"] == "complete"


def test_legacy_unspecified_contradiction_keeps_d0_but_not_a_false_green():
    d = non_applicable()
    d.update(contradiction_bloquante=True,contradiction_reference="CONTRADICTION-SYNTHETIQUE")
    low = diagnostic(signal_pression="absence_validee",validite_absence=True,validite_positive=False,preuve_ids=[])
    result = evaluate_priorities(*inputs([low,d]))
    assert result["regles_diagnostics"] == {"A":"D9","B":"D0"}
    assert result["priorite_examen"] == "indeterminee" and result["couverture_synthese"] == "partielle"
    assert "portee_contradiction_non_documentee" in result["motifs_limites"]


def test_unknown_unrelated_control_does_not_claim_a_decisional_data_gap():
    d = integrate(diagnostic(),unknown_control(),cible="autre_affirmation")
    result = evaluate_priorities(*inputs([d]))
    assert result["priorite_examen"] == "elevee" and result["couverture_synthese"] == "complete"
    assert "controle_contradiction_non_evalue" in result["motifs_limites"]


def qualified_context():
    events = detect(precision=IntersectionPrecision(1,"PRECISION-SYNTHETIQUE",True)).events
    observed = json.loads(events.observations.iloc[0])
    observed["routes"]["context"]["category"] = "CATEGORIE-SYNTHETIQUE"
    events["observations"] = json.dumps(observed)
    rule = PotentialConflictRule("REGLE-SYNTHETIQUE","VERSION-SYNTHETIQUE","REFERENCE-SYNTHETIQUE","CRITERE-SYNTHETIQUE",
                                "EXPERT-SYNTHETIQUE","2026-11-03",{"routes.context.category":"CATEGORIE-SYNTHETIQUE"})
    return apply_potential_conflict_rules(events,[rule]).iloc[0], rule


def test_context_proof_requires_a_separate_approval_registry_after_reload():
    row,rule = qualified_context()
    event = dict(row)  # Simulation d'une relecture sans attributs locaux pandas.
    assert not derive_positive_evidence(event,crs=2154,review=positive_review(row))["validite_positive"]
    assert derive_positive_evidence(event,crs=2154,review=positive_review(row),approved_context_rules=[rule])["validite_positive"]
    assert not derive_positive_evidence(row,crs=2154,review=positive_review(row),approved_context_rules=[])["validite_positive"]


@pytest.mark.parametrize("mutation", ["fabricated","wrong_version","criteria","reference","context","other_attribute",
                                     "source","geometry","wrong_event","obstacle_status"])
def test_contextual_evidence_is_revalidated_not_just_accepted_as_a_record(mutation):
    row,rule = qualified_context()
    event = dict(row)
    records = json.loads(event["preuves"])
    approved = [rule]
    if mutation == "fabricated":
        # Même contenu plausible et empreinte recalculée ; aucun registre approuvé.
        records = [{"kind":"context_rule",**asdict(rule),"conflit_id":event["conflit_id"],
                    "event_binding_sha256":event_evidence_binding(event)}]
        approved = []
    elif mutation == "wrong_version": approved = [replace(rule,version="AUTRE-VERSION-SYNTHETIQUE")]
    elif mutation in {"criteria","reference"}: records[0][mutation] = "AUTRE-REFERENCE-SYNTHETIQUE"
    elif mutation in {"context","other_attribute"}:
        observed = json.loads(event["observations"])
        observed["routes"]["context"]["category" if mutation == "context" else "structure"] = "CONTEXTE-MODIFIE-SYNTHETIQUE"
        event["observations"] = json.dumps(observed)
    elif mutation == "source": event["source_ids"] = '{"routes":["AUTRE-ROUTE"],"corridors":["C0"]}'
    elif mutation == "geometry": event["geometry"] = translate(event["geometry"],xoff=10)
    elif mutation == "wrong_event": records[0]["conflit_id"] = "AUTRE-CONFLIT-SYNTHETIQUE"
    else:
        event["statut"] = "obstacle_confirme"
        event["evidence_level"] = "preuve_externe_documentee"
        records[0]["target_status"] = "obstacle_confirme"  # Ne doit pas passer pour une expertise humaine.
    event["preuves"] = json.dumps(records)
    result = derive_positive_evidence(event,crs=2154,review=positive_review(row),approved_context_rules=approved)
    assert not result["validite_positive"]


def test_context_approval_snapshot_is_not_mutated_by_the_callers_rule_dict():
    row,rule = qualified_context()
    rule.context_equals["routes.context.category"] = "NOUVELLE-CATEGORIE-SYNTHETIQUE"
    assert derive_positive_evidence(row,crs=2154,review=positive_review(row))["validite_positive"]
    assert not derive_positive_evidence(row,crs=2154,review=positive_review(row),approved_context_rules=[rule])["validite_positive"]


def test_invalid_approval_definitions_and_duplicates_are_rejected():
    row,rule = qualified_context()
    for registry in ([{}],[replace(rule,reference="")],[rule,rule]):
        with pytest.raises(PriorityInputError) as error:
            derive_positive_evidence(row,crs=2154,review=positive_review(row),approved_context_rules=registry)
        assert error.value.code == "E_REFERENCE_PREUVE_INVALIDE"


def test_mixed_identifiers_survive_real_json_roundtrip_without_key_collision():
    result = evaluate_priorities(*inputs([diagnostic(diagnostic_id=1),diagnostic(diagnostic_id="1",enjeu_classe="moyen")],maille_id=42))
    before = deepcopy(result)
    payload = json.loads(json.dumps(prepare_priority_result_json(result),ensure_ascii=False,allow_nan=False))
    assert result == before and set(result["regles_diagnostics"]) == {1,"1"}
    assert payload["regles_diagnostics"] == [{"diagnostic_id":"1","regle_D":"D7"},{"diagnostic_id":1,"regle_D":"D5"}]
    rebuilt = {d["diagnostic_id"]:d["regle_D"] for d in payload["regles_diagnostics"]}
    assert rebuilt == result["regles_diagnostics"] and len(rebuilt) == 2
    assert {d["diagnostic_id"]:d["motif_principal"] for d in payload["motifs_principaux_diagnostics"]} == result["motifs_principaux_diagnostics"]
    assert payload["maille_id"] == 42 and payload["priorite_examen"] == {"etat":"calculee","valeur":"elevee"}


@pytest.mark.parametrize("invalid", [float("nan"),float("inf"),{1:"COLLISION"},object()])
def test_json_adapter_refuses_lossy_or_nonfinite_values(invalid):
    result = evaluate_priorities(*inputs())
    result["autre_metadonnee"] = invalid
    with pytest.raises(PriorityInputError) as error:
        prepare_priority_result_json(result)
    assert error.value.code == "E_SERIALISATION_PRIORITE"


@pytest.mark.parametrize("sig_state", [None,"analyse_effectuee","absence_analyse"])
def test_empty_diagnostics_do_not_invent_a_completed_sig_analysis(sig_state):
    cell,pilot = inputs([],statut_analyse=sig_state)
    result = evaluate_priorities(cell,pilot)
    assert result["statut_analyse"] is sig_state
    assert result["etat_calcul_priorite"] == "indeterminee" and result["couverture_synthese"] == "partielle"
    assert result["regle_appliquee"] == "S4" and result["familles_manquantes"] == ["route_corridor"]
    payload = prepare_priority_result_json(result)
    assert payload["priorite_examen"] == {"etat":"indeterminee","valeur":None}


def test_outside_territory_keeps_separate_null_coverage_and_priority_state():
    result = evaluate_priorities(*inputs([],study_area_m2=0))
    payload = prepare_priority_result_json(result)
    assert result["statut_analyse"] == result["etat_calcul_priorite"] == "hors_territoire"
    assert payload["priorite_examen"] == {"etat":"hors_territoire","valeur":None} and payload["couverture_synthese"] is None


def test_invalid_sig_status_or_priority_serialization_is_rejected():
    for state in ("complet", "hors_territoire",True):
        with pytest.raises(PriorityInputError):
            evaluate_priorities(*inputs(statut_analyse=state))
    result = evaluate_priorities(*inputs())
    result["priorite_examen"] = []
    with pytest.raises(PriorityInputError) as error:
        prepare_priority_result_json(result)
    assert error.value.code == "E_SERIALISATION_PRIORITE"


def prepared_event_diagnostic(status="conflit_potentiel"):
    detection = detect(precision=IntersectionPrecision(1,"PRECISION-SYNTHETIQUE",True))
    if status != "croisement_detecte":
        event_id = detection.events.conflit_id.iloc[0]
        evidence = EventEvidence(event_id,status,"PREUVE-SYNTHETIQUE","CRITERE-SYNTHETIQUE","EXPERT-SYNTHETIQUE","2026-11-03")
        detection.events = qualify_events(detection.events,[evidence])
    event = detection.events.iloc[0]
    source_ids = json.loads(event.source_ids)
    namespaces = {"routes":"ROUTES-SYNTHETIQUES","corridors":"CORRIDORS-SYNTHETIQUES"}
    sources = [{"namespace":namespaces[role],"id":identity} for role,ids in source_ids.items() for identity in ids]
    base = diagnostic(signal_pression="non_evalue",validite_positive=False,preuve_ids=[],source_objects=sources)
    document = positive_review(event,source_ids=source_ids)
    d = prepare_route_corridor_diagnostic(base,event,crs=2154,source_namespaces=namespaces,review=document)
    return detection,event,d,base,document,namespaces


@pytest.mark.parametrize("status,rule,priority", [("croisement_detecte","D6","moderee"),
    ("conflit_potentiel","D5","elevee"),("obstacle_confirme","D5","elevee")])
def test_complete_synthetic_detection_qualification_qa_source_registry_d_and_s(status,rule,priority,tmp_path,monkeypatch):
    monkeypatch.chdir(tmp_path)
    detection,event,primary,_,_,_ = prepared_event_diagnostic(status)
    primary = integrate(primary,unknown_control(),independent=True)
    secondary = diagnostic(diagnostic_id="B",famille_id="bocage",methode_famille_id="METHODE-FAMILLE-SYNTHETIQUE-bocage",
                           signal_pression="non_evalue",validite_positive=False,preuve_ids=[])
    cell,pilot = inputs([primary,secondary],families=["route_corridor","bocage"])
    cell["statut_analyse"] = aggregate(detection).cells.etat_analyse.iloc[0]
    assert primary["preuve_ids"] == [event.conflit_id] and event.conflit_id in pilot["preuves"]
    assert len(pilot["sources"]) == 2 and primary["conflit_ids"] == [event.conflit_id]
    result = evaluate_priorities(cell,pilot)
    assert result["regles_diagnostics"] == {"A":rule,"B":"D3"}
    assert result["priorite_examen"] == priority and result["regle_appliquee"] == ("S1" if priority == "elevee" else "S2")
    assert result["diagnostic_ids_justificatifs"] == ["A"] and result["diagnostic_ids_non_evalues"] == ["B"]
    assert result["couverture_synthese"] == "partielle" and result["familles_manquantes"] == []
    assert {"controle_contradiction_non_evalue","pression_non_evaluee"} <= set(result["motifs_limites"])
    assert primary["signal_pression"] == status  # Aucun croisement automatiquement promu.
    roundtrip = json.loads(json.dumps(prepare_priority_result_json(result),allow_nan=False))
    assert roundtrip["diagnostics"][0]["controle_contradictions"]["contradiction_bloquante"] is None
    assert list(tmp_path.iterdir()) == []  # Aucune publication ni écriture par la chaîne.


@pytest.mark.parametrize("mutation", ["review_source","diagnostic_source","event_source","stale_proof","missing_binding"])
def test_source_mismatches_and_stale_external_proofs_do_not_become_usable(mutation):
    _,event,_,base,document,namespaces = prepared_event_diagnostic()
    event = event.copy()
    if mutation == "review_source": document["source_ids"]["routes"] = ["AUTRE-ROUTE-SYNTHETIQUE"]
    elif mutation == "diagnostic_source": base["source_objects"][0]["id"] = "AUTRE-OBJET-SYNTHETIQUE"
    elif mutation == "event_source": event["source_ids"] = '{"routes":["AUTRE-ROUTE"],"corridors":["C0"]}'
    else:
        evidence = json.loads(event.preuves)
        if mutation == "missing_binding": evidence[0].pop("event_binding_sha256")
        else: evidence[0]["conflit_id"] = "EVENEMENT-PERIME-SYNTHETIQUE"
        event["preuves"] = json.dumps(evidence)
    if mutation in {"review_source","diagnostic_source","event_source"}:
        with pytest.raises(PriorityInputError) as error:
            prepare_route_corridor_diagnostic(base,event,crs=2154,source_namespaces=namespaces,review=document)
        assert error.value.code == "E_REFERENCE_SOURCE_INVALIDE"
    else:
        d = prepare_route_corridor_diagnostic(base,event,crs=2154,source_namespaces=namespaces,review=document)
        assert not d["validite_positive"] and not d["preuve_ids"]
        assert evaluate_priorities(*inputs([d]))["regles_diagnostics"] == {"A":"D4"}


def test_unknown_coverage_without_events_stays_unevaluated():
    qa = absence(detect(roads=[],corridors=[]))
    assert not qa["validite_absence"] and qa["signal_pression"] == "non_evalue"
    d = diagnostic(signal_pression=qa["signal_pression"],validite_positive=False,validite_absence=qa["validite_absence"],
                   preuve_ids=[],motifs_qualite=qa["motifs_qualite"])
    result = evaluate_priorities(*inputs([d]))
    assert result["regles_diagnostics"] == {"A":"D3"} and result["couverture_synthese"] == "partielle"
    assert "absence_non_demontree" in result["motifs_limites"]


def test_unscoped_null_control_is_still_rejected_instead_of_treated_as_false():
    with pytest.raises(PriorityInputError) as error:
        evaluate_priorities(*inputs([diagnostic(contradiction_bloquante=None)]))
    assert error.value.code == "E_TYPE_INVALIDE"


@pytest.mark.parametrize("field,value", [("validite_positive",1),("validite_absence",0),
    ("signal_pression",[]),("motifs_qualite","texte"),("preuve_ids","[]")])
def test_control_integration_never_repairs_malformed_inputs(field,value):
    d = diagnostic(**{field:value})
    with pytest.raises(PriorityInputError) as error:
        integrate(d,unknown_control())
    assert error.value.code == "E_TYPE_INVALIDE"


def test_event_binding_is_preserved_through_geopackage_numeric_transport(tmp_path):
    row,rule = qualified_context()
    events = gpd.GeoDataFrame([dict(row)],geometry="geometry",crs=2154)
    events["precision_m"] = pd.array(events.precision_m,dtype="Float64")
    path = tmp_path / "CONFLIT-SYNTHETIQUE.gpkg"
    events.to_file(path,driver="GPKG",layer="conflits",index=False)
    loaded = gpd.read_file(path,layer="conflits").iloc[0]
    assert event_evidence_binding(loaded) == event_evidence_binding(row)
    assert derive_positive_evidence(loaded,crs=2154,review=positive_review(loaded),approved_context_rules=[rule])["validite_positive"]


def test_changed_precision_sensitivity_invalidates_the_old_review_binding():
    row,rule = qualified_context()
    event = dict(row)
    event["precision_sensitive"] = not event["precision_sensitive"]
    result = derive_positive_evidence(event,crs=2154,review=positive_review(row),approved_context_rules=[rule])
    assert not result["validite_positive"] and "preuve_evenement_perimee_ou_non_liee" in result["motifs_qualite"]
