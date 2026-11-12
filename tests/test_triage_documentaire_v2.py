"""Garde-fous de la nouvelle condition documentaire, indépendante des règles D/S."""
from copy import deepcopy
import pytest
from analysis.triage_documentaire_v2 import classify


def witness(**changes):
    return dict(couche="ocsge", objet_id="OCSGE_REEL_DE_TEST", code_cs="CS2.2.1", code_us="US1.1", dans_maille=True,
                source_statut="acquise_geometrie_valide", mesure=50.0, unite="m2", **changes)


@pytest.mark.parametrize("color,rule", [("rouge", "V1"), ("orange", "V2"), ("jaune", "V3")])
def test_existing_classification_never_changes(color, rule):
    old = {"niveau": color, "regle": rule, "motif": "original", "couleur_hex": "original"}
    result = classify(old, [witness()])
    assert all(result[k] == v for k, v in old.items())


@pytest.mark.parametrize("changes", [
    {"couche": "routes"}, {"couche": "artificialisation"}, {"couche": "zones_humides"},
    {"dans_maille": False}, {"source_statut": "inconnue"}, {"code_cs": None},
    {"code_cs": "CS1.1.1.1"}, {"code_cs": "CS1.2.1"}, {"mesure": 0}, {"mesure": 1e-9}, {"objet_id": None},
    {"mesure": float('nan')}, {"mesure": float('inf')},
])
def test_negative_or_ambiguous_evidence_cannot_make_yellow(changes):
    e = witness();e.update(changes)
    assert classify({"niveau": "gris", "regle": "V4"}, [e])["niveau"] == "gris"


def test_local_cultivated_vegetation_is_only_documentary_and_does_not_mutate_inputs():
    old = {"niveau": "gris", "regle": "V4"};e = witness();snapshot = deepcopy((old, e))
    result = classify(old, [e])
    assert result["regle"] == "V3b" and result["validation_ecologique"] is False
    assert "Ni habitat naturel" in result["motif"] and (old, e) == snapshot


def test_technical_uncertainty_keeps_gray_even_with_local_vegetation():
    assert classify({"niveau": "gris", "regle": "V4"}, [witness()], True)["niveau"] == "gris"


def test_no_count_threshold_and_no_gravity_score():
    old = {"niveau": "gris", "regle": "V4"};e = witness()
    a = classify(old, [e]);b = classify(old, [e] * 1000)
    assert a["regle"] == b["regle"] == "V3b" and "score" not in a
