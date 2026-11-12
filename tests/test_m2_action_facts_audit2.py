"""Contre-exemples audit-2 : contrat uniquement, sans moteur ni preuve réelle.

Les exemples positifs ne prouvent que l'acceptabilité de structures SYNTHÉTIQUES.
Les tests REF_* exposent volontairement les limites de JSON Schema : accepter une
référence bien typée ne valide ni son existence ni sa pertinence scientifique.
"""

from copy import deepcopy
import hashlib
import json

import pytest
from jsonschema import Draft202012Validator, ValidationError

from test_m2_action_rule_contract import (
    CONTRACT, MAPPING, ROOT, SCHEMA, normalized_example, pending_example, validator,
)


COUNTEREXAMPLES = [
    ("R1", "sous_trame_documentee"), ("R2", "analyse_lacune_documentee"),
    ("R3", "lien_geometrique_continuite"), ("R4", "analyse_isolement_documentee"),
]
# Attentes indépendantes des contraintes de valeur du schéma.
FAMILY_FACTS = {
    "R1": ["evenement_route_corridor_reference", "statut_croisement", "validite_positive",
           "sous_trame_documentee", "route_source_versionnee", "emprise_reliee"],
    "R2": ["haies_inventaire_date", "sous_trame_bocagere", "continuite_reseau_referencee",
           "analyse_lacune_documentee", "couverture_thematique", "emprise_reliee"],
    "R3": ["friche_id_et_statut", "friche_source_datee", "lien_geometrique_continuite",
           "methode_voisinage_documentee", "contexte_sol", "emprise_reliee"],
    "R4": ["inventaire_mares_date", "sous_trame_humide", "reseau_habitats_reference",
           "analyse_isolement_documentee", "contexte_hydrologique", "emprise_reliee"],
}
NAMED_FACTS = sorted({f for facts in FAMILY_FACTS.values() for f in facts})


def example_for_fact(name):
    family = next(r for r, facts in FAMILY_FACTS.items() if name in facts)
    return normalized_example(family)["family_evidence"]["faits"][name]


def all_errors(errors):
    for error in errors:
        yield error
        yield from all_errors(error.context)


@pytest.mark.parametrize("family,fact", COUNTEREXAMPLES)
@pytest.mark.parametrize("value", [False, None, "VALEUR-SYNTHETIQUE"])
def test_original_family_counterexamples_fail_at_the_offending_value(family, fact, value):
    data = normalized_example(family)
    validator("normalizedInput").validate(data)  # Contrôle non vacu : structure seule.
    data["family_evidence"]["faits"][fact]["valeur"] = value
    errors = list(all_errors(validator("normalizedInput").iter_errors(data)))
    target = ["family_evidence", "faits", fact, "valeur"]
    assert any(list(e.absolute_path) == target for e in errors)


@pytest.mark.parametrize("fact", NAMED_FACTS)
def test_each_named_fact_accepts_its_structured_sample_but_not_documented_null(fact):
    data = example_for_fact(fact)
    v = validator("fact_" + fact)
    v.validate(data)
    data["valeur"] = None
    with pytest.raises(ValidationError):
        v.validate(data)


@pytest.mark.parametrize("fact", [f for f in NAMED_FACTS if f != "validite_positive"])
def test_boolean_cannot_replace_a_categorical_geometrical_or_structured_fact(fact):
    data = example_for_fact(fact)
    data["valeur"] = False
    assert not validator("fact_" + fact).is_valid(data)


@pytest.mark.parametrize("fact", NAMED_FACTS + ["absence_declencheur"])
@pytest.mark.parametrize("state", ["inconnu", "non_applicable_documentee"])
def test_unknown_and_documented_nonapplicability_use_null_without_positive_claim(fact, state):
    data = {"etat": state, "valeur": None,
            "preuve_ids": ["DOMAINE-SYNTHETIQUE"] if state != "inconnu" else [],
            "reference": "DOMAINE-SYNTHETIQUE" if state != "inconnu" else None}
    v = validator("fact_" + fact)
    v.validate(data)
    data["valeur"] = False
    assert not v.is_valid(data)
    if state == "non_applicable_documentee":
        data.update(valeur=None, preuve_ids=[], reference=None)
        assert not v.is_valid(data)


@pytest.mark.parametrize("family,fact", COUNTEREXAMPLES[1:])
@pytest.mark.parametrize("conclusion", ["indice_documente", "declencheur_absent", "indetermine"])
def test_documented_analysis_is_not_necessarily_a_satisfied_trigger(family, fact, conclusion):
    data = normalized_example(family)
    f = data["family_evidence"]["faits"][fact]
    f["valeur"]["conclusion"] = conclusion
    validator("fact_" + fact).validate(f)  # Résultat documentaire admissible.
    assert not validator("normalizedInput").is_valid(data)  # Ne peut étayer.


@pytest.mark.parametrize("family,fact,field,value", [
    ("R1", "sous_trame_documentee", "pertinence", "inconnue"),
    ("R2", "sous_trame_bocagere", "pertinence", "non_etablie"),
    ("R2", "couverture_thematique", "conclusion", "incomplete"),
    ("R3", "friche_id_et_statut", "eligibilite_etude", "non_etablie"),
    ("R4", "sous_trame_humide", "pertinence", "inconnue"),
    ("R4", "contexte_hydrologique", "adequation_etude", "non_etablie"),
    ("R1", "emprise_reliee", "relation", "frontiere_seule"),
    ("R2", "emprise_reliee", "relation", "hors_emprise"),
])
def test_documented_context_does_not_automatically_support_an_action(family, fact, field, value):
    data = normalized_example(family)
    f = data["family_evidence"]["faits"][fact]
    f["valeur"][field] = value
    validator("fact_" + fact).validate(f)
    assert not validator("normalizedInput").is_valid(data)


def absence_example(family="R2"):
    data = normalized_example(family)
    data.update(signal="absence_documentee", preuve_ids=[], preuve_absence_ids=["ABSENCE-SYNTHETIQUE"])
    e = data["family_evidence"]
    e.update(qualification="absence_documentee", preuve_ids=["ABSENCE-SYNTHETIQUE"],
             faits={"absence_declencheur": {"etat": "absence_documentee", "valeur": True,
                    "preuve_ids": ["ABSENCE-SYNTHETIQUE"], "reference": "ABSENCE-SYNTHETIQUE"}})
    return data


@pytest.mark.parametrize("family", list(MAPPING))
def test_negative_attestation_has_an_accepting_structural_path_for_each_family(family):
    validator("normalizedInput").validate(absence_example(family))


@pytest.mark.parametrize("mutation", ["false", "null", "numeric_one", "no_proof", "no_fact_proof",
                                    "no_method", "no_coverage", "coverage_unknown", "no_reference"])
def test_absence_requires_a_true_assertion_and_keeps_previous_negative_guards(mutation):
    data = absence_example()
    e = data["family_evidence"]
    f = e["faits"]["absence_declencheur"]
    if mutation in {"false", "null", "numeric_one"}:
        f["valeur"] = {"false": False, "null": None, "numeric_one": 1}[mutation]
    elif mutation == "no_proof": data["preuve_absence_ids"] = []
    elif mutation == "no_fact_proof": f["preuve_ids"] = []
    elif mutation == "no_method": data.update(methode_validee=False, methode_reference=None)
    elif mutation == "no_coverage": data["couverture_essentielle"] = "insuffisante"
    elif mutation == "coverage_unknown": e["couvertures"][0]["statut"] = "unknown"
    else: f["reference"] = None
    assert not validator("normalizedInput").is_valid(data)


def test_false_absence_is_a_documented_non_conclusion_never_a_negative_attestation():
    f = {"etat": "documente", "valeur": False, "preuve_ids": ["REVUE-SYNTHETIQUE"], "reference": "REVUE-SYNTHETIQUE"}
    validator("fact_absence_declencheur").validate(f)
    data = absence_example()
    data["family_evidence"]["faits"]["absence_declencheur"] = f
    assert not validator("normalizedInput").is_valid(data)


# Chacun de ces cas reste structurellement valide : il doit BLOQUER le futur M4
# lors du contrôle référentiel. Ce test n'est pas l'implémentation de ce contrôle.
@pytest.mark.parametrize("mismatch,check", [
    ("maille_type", "REF_MAILLE"), ("diagnostic", "REF_DIAGNOSTICS"),
    ("fact_proof", "REF_PREUVES"), ("input_proof", "REF_PREUVES"),
    ("phenomenon", "REF_OBJETS_PHENOMENES"), ("object", "REF_OBJETS_PHENOMENES"),
    ("event", "REF_OBJETS_PHENOMENES"), ("method_version", "REF_METHODES"),
    ("submethod", "REF_METHODES"), ("source_version", "REF_OBJETS_PHENOMENES"),
    ("analysis_method_version", "REF_METHODES"), ("analysis_method_reference", "REF_METHODES"),
    ("analysis_object", "REF_OBJETS_PHENOMENES"), ("event_binding", "REF_OBJETS_PHENOMENES"),
    ("network_subframe", "REF_OBJETS_PHENOMENES"),
    ("extent", "REF_EMPRISES"), ("coverage_extent", "REF_EMPRISES"),
    ("period_reversed", "REF_PERIODES"), ("period_disjoint", "REF_PERIODES"),
    ("thematic_gap", "REF_COUVERTURES"), ("evidence_family", "REF_FAMILLE"),
])
def test_well_typed_cross_object_mismatches_are_explicit_blocking_m4_obligations(mismatch, check):
    # Le passage JSON évite les alias Python entre périodes/sources du helper.
    family = ("R3" if mismatch.startswith("analysis_") else "R2"
              if mismatch in {"thematic_gap", "network_subframe"} else "R1")
    data = json.loads(json.dumps(normalized_example(family)))
    e = data["family_evidence"]
    if mismatch == "maille_type": e["maille_id"] = "42"
    elif mismatch == "diagnostic": e["diagnostic_ids"] = ["AUTRE-DIAGNOSTIC-SYNTHETIQUE"]
    elif mismatch == "fact_proof": next(iter(e["faits"].values()))["preuve_ids"] = ["PREUVE-NON-RESOLUE-SYNTHETIQUE"]
    elif mismatch == "input_proof": data["preuve_ids"] = ["AUTRE-PREUVE-SYNTHETIQUE"]
    elif mismatch == "phenomenon": e["phenomene_id"] = "PHENOMENE-AUTRE-FAMILLE-SYNTHETIQUE"
    elif mismatch == "object": e["source_objects"][0]["id"] = "AUTRE-OBJET-SYNTHETIQUE"
    elif mismatch == "event": e["liaison_evenement"]["conflit_id"] = "AUTRE-CONFLIT-SYNTHETIQUE"
    elif mismatch == "method_version": e["methode_version"] = "VERSION-NON-APPROUVEE-SYNTHETIQUE"
    elif mismatch == "submethod": e["methode_id"] = "AUTRE-METHODE-SYNTHETIQUE"
    elif mismatch == "source_version": e["source_objects"][0]["dataset_version"] = "AUTRE-VERSION-SYNTHETIQUE"
    elif mismatch == "analysis_method_version": e["faits"]["lien_geometrique_continuite"]["valeur"]["methode_version"] = "VERSION-DISCORDANTE-SYNTHETIQUE"
    elif mismatch == "analysis_method_reference": e["faits"]["methode_voisinage_documentee"]["valeur"]["reference"] = "REFERENCE-DISCORDANTE-SYNTHETIQUE"
    elif mismatch == "analysis_object": e["faits"]["lien_geometrique_continuite"]["valeur"]["friche_id"] = "AUTRE-FRICHE-SYNTHETIQUE"
    elif mismatch == "event_binding": e["liaison_evenement"]["event_binding_sha256"] = "1" * 64
    elif mismatch == "network_subframe": e["faits"]["continuite_reseau_referencee"]["valeur"]["sous_trame_code"] = "AUTRE-SOUS-TRAME-SYNTHETIQUE"
    elif mismatch == "extent": e["faits"]["emprise_reliee"]["valeur"]["emprise_reference"] = "AUTRE-EMPRISE-SYNTHETIQUE"
    elif mismatch == "coverage_extent": e["couvertures"][0]["emprise_reference"] = "EMPRISE-DISJOINTE-SYNTHETIQUE"
    elif mismatch == "period_reversed": e["periode_reference"].update(debut="2027-01-01", fin="2026-01-01")
    elif mismatch == "period_disjoint": e["source_objects"][0]["periode_reference"].update(debut="2000-01-01", fin="2000-12-31")
    elif mismatch == "thematic_gap": e["faits"]["couverture_thematique"]["valeur"]["categories_couvertes"] = []
    else: e["preuve_ids"] = ["PREUVE-FAMILLE-ETRANGERE-SYNTHETIQUE"]
    if mismatch == "period_disjoint":
        assert e["periode_reference"]["debut"] > e["source_objects"][0]["periode_reference"]["fin"]
    if mismatch == "analysis_method_version":
        assert e["methode_version"] != e["faits"]["lien_geometrique_continuite"]["valeur"]["methode_version"]
    validator("normalizedInput").validate(data)
    obligation = next(c for c in CONTRACT["interobject_checks"] if c["id"] == check)
    assert obligation["blocking_for_real_data"] is True
    assert obligation["schema_support"] in {"non", "partiel"}
    assert obligation["control"] and obligation["failure_code"]


@pytest.mark.parametrize("mutation", ["family", "foreign_fact", "null_method_version", "blank_reference", "bad_date"])
def test_schema_does_reject_local_family_type_and_format_errors(mutation):
    data = normalized_example("R3")
    e = data["family_evidence"]
    if mutation == "family": e["rule_id"] = "R2"
    elif mutation == "foreign_fact": e["faits"]["analyse_isolement_documentee"] = example_for_fact("analyse_isolement_documentee")
    elif mutation == "null_method_version": e["methode_version"] = None
    elif mutation == "blank_reference": e["methode_reference"] = "  "
    else: e["periode_reference"]["debut"] = "2026-02-30"
    assert not validator("normalizedInput").is_valid(data)


def result_example(family="R1"):
    """Résultat non évaluable : aucune déclaration de preuve ni de contrôle accompli."""
    return {
        "maille_id": 42, "diagnostic_ids": [1, "1"], "phenomene_ids": [], "rule_id": family,
        "action_id": MAPPING[family], "rule_version": "m2-actions.spec-proposal-1",
        "ruleset_version": "m2-actions.spec-proposal-1", "contract_revision": "audit-2",
        "statut": "non_evaluable", "regle_decision": "A8", "motif_principal": "non_qualifiable_sans_inventer",
        "justification_courte": "EXEMPLE-SYNTHETIQUE : signal inconnu, aucun avis écologique.",
        "preuve_ids": [], "preuve_absence_ids": [], "attestation_ids": [], "conflit_ids": [],
        "applicabilite_reference": None, "contradiction_references": [],
        "limites": ["sources_M1_non_livrees"], "prerequis_a_verifier": ["methode_M1_M2_a_approuver"],
        "methode": None, "qualite": {"couverture_essentielle": "insuffisante", "methode_validee": False,
                                   "couverture_references": []},
        "etat_validation": "structure_seule", "validation_reference": None, "authentifie_par_logiciel": False,
    }


@pytest.mark.parametrize("family", list(MAPPING))
def test_internal_result_preserves_typed_ids_and_each_provisional_pair(family):
    data = result_example(family)
    validator("actionResult").validate(data)
    assert json.loads(json.dumps(data))["diagnostic_ids"] == [1, "1"]
    data["action_id"] = "A02" if family != "R4" else "A04"
    assert not validator("actionResult").is_valid(data)


@pytest.mark.parametrize("field,value", [
    ("maille_id", True), ("diagnostic_ids", [True]), ("diagnostic_ids", [1, 1]),
    ("phenomene_ids", {"1": "PHENOMENE"}), ("conflit_ids", [None]),
    ("rule_version", "VERSION-INCONNUE"), ("ruleset_version", "VERSION-INCONNUE"),
    ("contract_revision", "audit-1"), ("regle_decision", "V0"), ("statut", "ERREUR"),
    ("motif_principal", "declencheur_etaye"), ("limites", []),
    ("etat_validation", "controle_referentiel_documente"), ("authentifie_par_logiciel", True),
])
def test_output_refuses_collisions_invalid_statuses_and_unsupported_validation_claims(field, value):
    data = result_example()
    data[field] = value
    assert not validator("actionResult").is_valid(data)


@pytest.mark.parametrize("code,status,reason", [
    ("A0", "non_evaluable", "contradiction_bloquante"),
    ("A1", "non_retenue_par_regle", "hors_domaine_documente"),
    ("A2", "non_evaluable", "domaine_methode_ou_donnees_insuffisants"),
    ("A3", "non_evaluable", "controle_contradiction_non_evalue"),
    ("A4", "etayee_pour_examen", "declencheur_etaye"),
    ("A5", "conditionnelle", "etayage_avec_controle_incomplet"),
    ("A6", "conditionnelle", "indice_documente_a_verifier"),
    ("A7", "non_retenue_par_regle", "absence_declencheur_documentee"),
    ("A8", "non_evaluable", "non_qualifiable_sans_inventer"),
])
def test_each_output_binding_rejects_another_status_or_reason(code, status, reason):
    # Test isolé de la liaison déclarative, sans exécuter ni déduire une décision.
    bindings = [b for b in SCHEMA["$defs"]["actionResult"]["allOf"]
                if b.get("if", {}).get("properties", {}).get("regle_decision") == {"const": code}
                and "motif_principal" in b.get("then", {}).get("properties", {})]
    assert len(bindings) == 1
    v = Draft202012Validator(bindings[0])
    v.validate({"regle_decision": code, "statut": status, "motif_principal": reason})
    assert not v.is_valid({"regle_decision": code, "statut": "ERREUR", "motif_principal": reason})
    assert not v.is_valid({"regle_decision": code, "statut": status, "motif_principal": "MOTIF-ETRANGER"})


@pytest.mark.parametrize("code,status,reason", [
    ("A4", "etayee_pour_examen", "declencheur_etaye"),
    ("A6", "conditionnelle", "indice_documente_a_verifier"),
    ("A7", "non_retenue_par_regle", "absence_declencheur_documentee"),
])
def test_schema_success_alone_cannot_support_positive_or_negative_results(code, status, reason):
    data = result_example()
    data.update(regle_decision=code, statut=status, motif_principal=reason)
    assert not validator("actionResult").is_valid(data)


def test_domain_result_can_keep_unvalidated_ecological_method_because_a1_precedes_a2():
    data = result_example()
    data.update(regle_decision="A1", statut="non_retenue_par_regle", motif_principal="hors_domaine_documente",
                etat_validation="controle_referentiel_documente", validation_reference="DOMAINE-SYNTHETIQUE",
                attestation_ids=["DOMAINE-SYNTHETIQUE"], preuve_ids=["DOMAINE-SYNTHETIQUE"],
                applicabilite_reference="DOMAINE-SYNTHETIQUE")
    validator("actionResult").validate(data)  # Déclaration synthétique de contrôle du domaine uniquement.


def declared_result(code="A4"):
    """Déclarations de forme SYNTHÉTIQUES : aucun registre ni contrôle M4 exécuté."""
    data = result_example()
    negative = code == "A7"
    data.update(regle_decision=code,
                statut="non_retenue_par_regle" if negative else "etayee_pour_examen",
                motif_principal="absence_declencheur_documentee" if negative else "declencheur_etaye",
                preuve_ids=[] if negative else ["PREUVE-SYNTHETIQUE"],
                preuve_absence_ids=["ABSENCE-SYNTHETIQUE"] if negative else [],
                attestation_ids=["ATTESTATION-SYNTHETIQUE"], phenomene_ids=[1, "1"], conflit_ids=[1, "1"],
                etat_validation="controle_referentiel_documente", validation_reference="REVUE-SYNTHETIQUE-NON-VERIFIEE",
                methode={"methode_id":"METHODE-SYNTHETIQUE", "version":"VERSION-SYNTHETIQUE", "reference":"REFERENCE-SYNTHETIQUE"},
                qualite={"couverture_essentielle":"suffisante", "methode_validee":True,
                         "couverture_references":["COUVERTURE-SYNTHETIQUE"]})
    return data


@pytest.mark.parametrize("code", ["A4", "A7"])
def test_declared_output_has_a_structural_accepting_path_without_authenticating_the_claim(code):
    data = declared_result(code)
    validator("actionResult").validate(data)
    assert data["authentifie_par_logiciel"] is False
    assert next(c for c in CONTRACT["interobject_checks"] if c["id"] == "REF_RESULTAT")["blocking_for_real_data"]


@pytest.mark.parametrize("code,field,value", [
    ("A4", "preuve_ids", []), ("A4", "conflit_ids", []), ("A4", "diagnostic_ids", []),
    ("A4", "phenomene_ids", []), ("A4", "prerequis_a_verifier", []),
    ("A7", "preuve_absence_ids", []), ("A7", "attestation_ids", []),
    ("A7", "validation_reference", None), ("A7", "methode", None),
])
def test_completed_declarations_cannot_drop_the_required_evidence_or_trace(code, field, value):
    data = declared_result(code)
    validator("actionResult").validate(data)
    data[field] = value
    assert not validator("actionResult").is_valid(data)


@pytest.mark.parametrize("field,value", [("couverture_essentielle", "partielle"),
                                         ("methode_validee", False), ("couverture_references", [])])
def test_negative_result_keeps_all_coverage_and_method_guards(field, value):
    data = declared_result("A7")
    data["qualite"][field] = value
    assert not validator("actionResult").is_valid(data)


@pytest.mark.parametrize("code,reason", [("A5", "etayage_avec_controle_incomplet"),
                                       ("A6", "indice_documente_a_verifier")])
def test_conditional_result_quality_remains_consistent_with_the_declared_a_code(code, reason):
    data = declared_result()
    data.update(regle_decision=code, statut="conditionnelle", motif_principal=reason)
    validator("actionResult").validate(data)
    data["qualite"]["couverture_essentielle"] = "partielle"
    assert validator("actionResult").is_valid(data) is (code == "A6")
    data["qualite"]["couverture_essentielle"] = "insuffisante"
    assert not validator("actionResult").is_valid(data)


def public_example():
    data = result_example()
    return {k: deepcopy(data[k]) for k in ["maille_id", "rule_id", "action_id", "rule_version", "ruleset_version",
            "contract_revision", "statut", "regle_decision", "motif_principal", "justification_courte"]} | {
                "limites_publiques": ["evaluation_incomplete"], "prerequis_publics": ["expertise_requise"],
                "diffusion": {"etat": "autorisee_apres_revue", "policy_version": "POLITIQUE-SYNTHETIQUE"}}


@pytest.mark.parametrize("field", ["preuve_ids", "preuve_absence_ids", "family_evidence", "geometry",
                                   "validation_reference", "attestation_ids", "source_objects", "methode"])
def test_public_projection_has_no_private_field_escape_hatch(field):
    data = public_example()
    validator("actionPublicProjection").validate(data)
    data[field] = "REFERENCE-PRIVEE-SYNTHETIQUE"
    assert not validator("actionPublicProjection").is_valid(data)


def test_internal_results_cannot_be_published_directly_and_text_still_requires_human_review():
    assert not validator("actionPublicProjection").is_valid(result_example())
    data = public_example()
    data["justification_courte"] = "REFERENCE-PRIVEE-SYNTHETIQUE"
    validator("actionPublicProjection").validate(data)  # Le schéma ne classe pas la confidentialité d'un texte.
    assert next(c for c in CONTRACT["interobject_checks"] if c["id"] == "REF_DIFFUSION")["blocking_for_real_data"]
    assert set(data) == set(CONTRACT["public_display_allowlist"])


def test_validation_errors_are_disjoint_from_action_results():
    error = {"type": "validation_error", "maille_id": None, "rule_id": None,
             "code": "E_ACTION_INPUT_INVALIDE", "details": [{"field": "maille_id", "code": "E_ACTION_TYPE_INVALIDE"}]}
    validator("actionValidationError").validate(error)
    assert not validator("actionResult").is_valid(error)
    assert not validator("actionPublicProjection").is_valid(error)
    error["statut"] = "non_evaluable"
    assert not validator("actionValidationError").is_valid(error)


def test_pending_profile_remains_valid_with_no_invented_diagnostic_or_evidence():
    data = pending_example()
    validator("normalizedInput").validate(data)
    assert not data["diagnostic_ids"] and "source_objects" not in data["family_evidence"]


def test_unchanged_oracles_and_decision_table_have_stable_independent_digests():
    fixture = (ROOT / "tests/fixtures/m2/action_rule_cases.json").read_bytes()
    assert hashlib.sha256(fixture).hexdigest() == "df13d94ed790308231dd9f75b64771ea7101300c4d9b427671b7c9ddc1a890e9"
    table = json.dumps(CONTRACT["shared_precedence"], ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    assert hashlib.sha256(table).hexdigest() == "0a5242c4a95daab3974542174c82a6db9d265cf54178ba3925e8d94cfc76504e"
