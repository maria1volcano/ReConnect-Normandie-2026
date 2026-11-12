"""Oracles fixés et propriétés des conventions provisoires D/S, sans données réelles."""

from copy import deepcopy
from itertools import permutations, product

import pytest

from analysis.evaluate_priorities import evaluate_priorities
from analysis.prepare_priority_inputs import PriorityInputError
from m2_priority_helpers import CASES, diagnostic, fixture_inputs, inputs


@pytest.mark.parametrize("case", CASES, ids=lambda c:c["case_id"])
def test_all_38_contract_scenarios_without_modifying_their_oracles(case):
    if "expected_error" in case:
        with pytest.raises(PriorityInputError) as error:
            evaluate_priorities(*fixture_inputs(case))
        assert error.value.code == case["expected_error"]
    else:
        result = evaluate_priorities(*fixture_inputs(case))
        for key, expected in case["expected"].items():
            assert result[key] == expected, (case["case_id"], key)
        assert result["priority_method_version"] == case["priority_method_version"]


# Domaine recopié de la spécification, indépendant des constantes de production.
STAKES = ("fort", "moyen", "faible", "inconnu")
PRESSURES = ("obstacle_confirme", "conflit_potentiel", "croisement_detecte", "absence_validee", "non_concluant", "non_evalue")
APPLICABILITIES = ("oui", "non_applicable_documentee", "inconnue")
COMBINATIONS = list(product(STAKES, PRESSURES, (False, True), (False, True), APPLICABILITIES, (False, True)))

# Matrice terminale D5–D10a fixée indépendamment du moteur.
TERMINAL = {
    ("fort", "obstacle_confirme"):("D5", "eleve", "conflit_etaye_enjeu_fort"),
    ("fort", "conflit_potentiel"):("D5", "eleve", "conflit_etaye_enjeu_fort"),
    ("fort", "croisement_detecte"):("D6", "modere", "croisement_non_qualifie_enjeu_fort"),
    ("moyen", "obstacle_confirme"):("D7", "modere", "pression_observee_enjeu_moyen"),
    ("moyen", "conflit_potentiel"):("D7", "modere", "pression_observee_enjeu_moyen"),
    ("moyen", "croisement_detecte"):("D7", "modere", "pression_observee_enjeu_moyen"),
    ("faible", "obstacle_confirme"):("D8", "modere", "conflit_etaye_enjeu_faible"),
    ("faible", "conflit_potentiel"):("D8", "modere", "conflit_etaye_enjeu_faible"),
    ("faible", "croisement_detecte"):("D10a", "indetermine", "signal_non_qualifie"),
    **{(stake,"absence_validee"):("D9", "faible", "absence_pression_validee") for stake in STAKES[:3]},
}


def independent_oracle(stake, pressure, positive, absence, applicable, contradiction):
    if pressure == "absence_validee" and not absence:
        return "E_ABSENCE_INCOHERENTE"
    if applicable == "non_applicable_documentee" and pressure in PRESSURES[:3]:
        return "E_NON_APPLICABILITE_INCOHERENTE"
    if applicable == "non_applicable_documentee":
        return "D0", "hors_champ", "non_applicabilite_documentee"
    if contradiction or applicable == "inconnue":
        return "D1", "indetermine", "donnees_contradictoires" if contradiction else "applicabilite_inconnue"
    if stake == "inconnu":
        return "D2", "indetermine", "enjeu_non_documente"
    if pressure in ("non_evalue", "non_concluant"):
        return "D3", "indetermine", "pression_non_evaluee" if pressure == "non_evalue" else "preuve_non_concluante"
    if pressure in PRESSURES[:3] and not positive:
        return "D4", "indetermine", "preuve_positive_non_validee"
    return TERMINAL[stake, pressure]


def combination_inputs(combination):
    stake, pressure, positive, absence, applicable, contradiction = combination
    return inputs([diagnostic(enjeu_classe=stake, signal_pression=pressure, validite_positive=positive,
        validite_absence=absence, applicabilite=applicable, contradiction_bloquante=contradiction,
        enjeu_methode_id=None if stake == "inconnu" else "METHODE-SYNTHETIQUE",
        applicabilite_reference="NON-APPLICABILITE-SYNTHETIQUE" if applicable == "non_applicable_documentee" else None,
        contradiction_reference="CONTRADICTION-SYNTHETIQUE" if contradiction else None)])


@pytest.fixture(scope="module")
def exhaustive_counts():
    counts = {"admis":0, "rejetes":0, "non_couverts":0}
    yield counts
    assert len(COMBINATIONS) == 576
    assert counts == {"admis":432, "rejetes":144, "non_couverts":0}
    print(f"\nD exhaustif : 576 combinaisons ; {counts['admis']} admises, {counts['rejetes']} rejetées, {counts['non_couverts']} non couvertes.")


@pytest.mark.parametrize("combination", COMBINATIONS)
def test_exactly_576_categorical_combinations(combination, exhaustive_counts):
    expected = independent_oracle(*combination)
    try:
        result = evaluate_priorities(*combination_inputs(combination))
    except PriorityInputError as error:
        if error.code == "E_TABLE_NON_TOTALE":
            exhaustive_counts["non_couverts"] += 1
        else:
            exhaustive_counts["rejetes"] += 1
        assert isinstance(expected, str) and expected == error.code
    else:
        exhaustive_counts["admis"] += 1
        assert not isinstance(expected, str)
        detail = result["diagnostics"][0]
        assert (detail["regle_D"], detail["signal_diagnostic"], detail["motif_principal"]) == expected
        assert result["regles_diagnostics"] == {"A":expected[0]}


def test_d_and_s_precedence_counterexamples():
    # D0 gagne sur D1/D2/D3, D1 gagne sur D2, D2 gagne sur D3 et D3 sur D4.
    expectations = [
        (diagnostic(applicabilite="non_applicable_documentee", applicabilite_reference="TEST SYNTHETIQUE",
                    signal_pression="non_evalue", enjeu_classe="inconnu", contradiction_bloquante=True,
                    contradiction_reference="TEST SYNTHETIQUE"), "D0"),
        (diagnostic(enjeu_classe="inconnu", contradiction_bloquante=True, contradiction_reference="TEST SYNTHETIQUE"), "D1"),
        (diagnostic(enjeu_classe="inconnu", signal_pression="non_concluant", validite_positive=False), "D2"),
        (diagnostic(signal_pression="non_concluant", validite_positive=False), "D3"),
    ]
    for d, expected in expectations:
        assert evaluate_priorities(*inputs([d]))["regles_diagnostics"] == {"A":expected}
    ds = [diagnostic(diagnostic_id="E", enjeu_classe="fort"), diagnostic(diagnostic_id="M", enjeu_classe="moyen"),
          diagnostic(diagnostic_id="F", signal_pression="absence_validee", validite_absence=True)]
    for ordered in permutations(ds):
        assert evaluate_priorities(*inputs(list(ordered)))["regle_appliquee"] == "S1"
    assert evaluate_priorities(*inputs(ds[1:]))["regle_appliquee"] == "S2"


def test_no_residual_rule_can_hide_a_table_hole(monkeypatch):
    monkeypatch.setattr("analysis.evaluate_priorities.D_RULES", ())
    with pytest.raises(PriorityInputError) as error:
        evaluate_priorities(*inputs())
    assert error.value.code == "E_TABLE_NON_TOTALE"


def test_diagnostic_and_source_permutations_preserve_every_output_and_inputs():
    sources = [{"namespace":"SOURCE-SYNTHETIQUE", "id":i} for i in (1,2)]
    ds = [diagnostic(diagnostic_id=i, source_objects=sources, phenomene_id="PHENOMENE-SYNTHETIQUE") for i in ("B","A",3)]
    cell, pilot = inputs(ds)
    before = deepcopy((cell,pilot))
    expected = evaluate_priorities(cell,pilot)
    for ordered in permutations(ds):
        candidate, scope = inputs(list(ordered))
        for d in candidate["diagnostics"]:
            d["source_objects"].reverse()
        scope["sources"].reverse()
        assert evaluate_priorities(candidate,scope) == expected
    assert (cell,pilot) == before


def test_duplicating_observations_never_promotes_a_priority():
    moderate = diagnostic(enjeu_classe="moyen")
    assert evaluate_priorities(*inputs([moderate]))["priorite_examen"] == "moderee"
    with pytest.raises(PriorityInputError) as error:
        evaluate_priorities(*inputs([moderate,moderate]))
    assert error.value.code == "E_ID_DUPLIQUE"
    result = evaluate_priorities(*inputs([moderate,{**moderate,"diagnostic_id":"B"}]))
    assert result["priorite_examen"] == "moderee" and result["diagnostic_ids_justificatifs"] == ["A","B"]


@pytest.mark.parametrize("case_id", ["T13", "T18", "T35"])
def test_a_reliable_high_signal_survives_an_independent_data_gap(case_id):
    case = next(c for c in CASES if c["case_id"] == case_id)
    cell,pilot = fixture_inputs(case)
    result = evaluate_priorities(cell,pilot)
    assert result["priorite_examen"] == "elevee" and result["couverture_synthese"] == "partielle"
    cell["diagnostics"] = cell["diagnostics"][:1]
    assert evaluate_priorities(cell,pilot)["priorite_examen"] == "elevee"


def test_cannot_silently_remove_an_expected_family_to_get_green():
    low = diagnostic(signal_pression="absence_validee", validite_absence=True, validite_positive=False)
    cell,pilot = inputs([low], families=["route_corridor","bocage"])
    result = evaluate_priorities(cell,pilot)
    assert result["priorite_examen"] == "indeterminee" and result["familles_manquantes"] == ["bocage"]
    cell["familles_attendues"] = ["route_corridor"]
    with pytest.raises(PriorityInputError) as error:
        evaluate_priorities(cell,pilot)
    assert error.value.code == "E_PERIMETRE_INVALIDE"


def test_undefined_interpretation_is_distinct_from_incomplete_data():
    complete = evaluate_priorities(*fixture_inputs(next(c for c in CASES if c["case_id"] == "T09")))
    partial = evaluate_priorities(*fixture_inputs(next(c for c in CASES if c["case_id"] == "T07")))
    assert complete["priorite_examen"] == partial["priorite_examen"] == "indeterminee"
    assert complete["couverture_synthese"] == "complete" and partial["couverture_synthese"] == "partielle"
    assert complete["diagnostic_ids_non_evalues"] == partial["diagnostic_ids_non_evalues"] == ["A"]


def test_outside_territory_is_s0_but_malformed_diagnostics_still_block():
    cell,pilot = inputs(study_area_m2=0)
    result = evaluate_priorities(cell,pilot)
    assert result["regle_appliquee"] == "S0" and result["priorite_examen"] is None
    assert result["regles_diagnostics"] == {} and result["diagnostic_ids_justificatifs"] == []
    cell["diagnostics"][0]["validite_positive"] = 1
    with pytest.raises(PriorityInputError) as error:
        evaluate_priorities(cell,pilot)
    assert error.value.code == "E_TYPE_INVALIDE"


def test_all_quality_reasons_survive_selection_of_another_diagnostic():
    result = evaluate_priorities(*inputs([diagnostic(),diagnostic(diagnostic_id="B", enjeu_classe="inconnu",
        motifs_qualite=["absence_non_demontree","precision_localisation_insuffisante","absence_non_demontree"])]))
    assert result["motifs_limites"] == ["absence_non_demontree","enjeu_non_documente","precision_localisation_insuffisante"]
    assert result["motifs_principaux_diagnostics"]["B"] == "enjeu_non_documente"


def test_related_diagnostics_are_retained_without_claiming_independence():
    for case_id, reason in (("T16","source_partagee"),("T34","phenomene_partage")):
        result = evaluate_priorities(*fixture_inputs(next(c for c in CASES if c["case_id"] == case_id)))
        assert len(result["diagnostics"]) == 2 and result["liens_diagnostics"][0]["raison"] == reason
        assert result["priorite_examen"] == "moderee"
    unlinked = evaluate_priorities(*inputs([diagnostic(),diagnostic(diagnostic_id="B")]))
    assert unlinked["relation_diagnostics"] == "relation_non_etablie"


def test_integer_identifiers_and_string_identifiers_remain_distinct():
    cell,pilot = inputs([diagnostic(diagnostic_id=1), diagnostic(diagnostic_id="1")], maille_id=42)
    result = evaluate_priorities(cell,pilot)
    assert result["maille_id"] == 42 and result["diagnostic_ids_justificatifs"] == ["1",1]
    assert set(result["regles_diagnostics"]) == {1,"1"}
    assert [d["diagnostic_id"] for d in result["diagnostics"]] == ["1",1]


def test_conditional_monotonicity_only_for_comparable_known_priorities():
    ranks = {"faible":0, "moderee":1, "elevee":2}
    compared = {"qualification":0, "enjeu":0}
    for stake, vp, va, app, contr in product(STAKES,(False,True),(False,True),APPLICABILITIES,(False,True)):
        endpoints = []
        for pressure in ("conflit_potentiel","obstacle_confirme"):
            try:
                endpoints.append(evaluate_priorities(*combination_inputs((stake,pressure,vp,va,app,contr)))["priorite_examen"])
            except PriorityInputError as error:
                assert error.code == "E_NON_APPLICABILITE_INCOHERENTE"
        if len(endpoints) == 2 and all(p in ranks for p in endpoints):
            assert ranks[endpoints[1]] >= ranks[endpoints[0]]
            compared["qualification"] += 1
    for pressure, vp, va, app, contr in product(PRESSURES,(False,True),(False,True),APPLICABILITIES,(False,True)):
        endpoints = []
        for stake in ("moyen","fort"):
            try:
                endpoints.append(evaluate_priorities(*combination_inputs((stake,pressure,vp,va,app,contr)))["priorite_examen"])
            except PriorityInputError as error:
                assert error.code in {"E_NON_APPLICABILITE_INCOHERENTE","E_ABSENCE_INCOHERENTE"}
        if len(endpoints) == 2 and all(p in ranks for p in endpoints):
            assert ranks[endpoints[1]] >= ranks[endpoints[0]]
            compared["enjeu"] += 1
    assert compared == {"qualification":6, "enjeu":8}
    print(f"\nMonotonie comparable : {compared['qualification']} transitions de qualification, {compared['enjeu']} transitions d'enjeu.")
