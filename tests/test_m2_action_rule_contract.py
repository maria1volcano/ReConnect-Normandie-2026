"""Audit documentaire du contrat d'actions ; aucun moteur M4 n'est exécuté ici.

Les ensembles finis ci-dessous vérifient la partition logique des prédicats
documentés. Les fixtures et attestations sont SYNTHÉTIQUES, sans validation terrain.
"""

from collections import Counter
from copy import deepcopy
from itertools import product
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import pytest

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    def reject(value):
        raise ValueError(f"Constante JSON interdite : {value}")
    return json.loads((ROOT/path).read_text(encoding="utf-8"),parse_constant=reject)


CONTRACT = read_json("docs/rules_actions.json")
FIXTURES = read_json("tests/fixtures/m2/action_rule_cases.json")
SCHEMA = read_json("docs/schema_actions_m2.json")
MAPPING = {"R1":"A04","R2":"A01","R3":"A03","R4":"A02"}  # Provisoire, confirmé par l'instruction M2, pas par M5.
STATUSES = {"etayee_pour_examen","conditionnelle","non_retenue_par_regle","non_evaluable"}
ROWS = {row["code"]:row for row in CONTRACT["shared_precedence"]}
CASES = FIXTURES["cases"]


def validator(profile):
    schema = {**SCHEMA,"$ref":f"#/$defs/{profile}"}
    return Draft202012Validator(schema,format_checker=FormatChecker())


def test_structured_contract_ids_versions_statuses_and_declared_precedence():
    Draft202012Validator.check_schema(SCHEMA)
    assert CONTRACT["ruleset_version"] == FIXTURES["ruleset_version"]
    assert {r["rule_id"]:r["action_id"] for r in CONTRACT["rules"]} == MAPPING
    assert len(CONTRACT["rules"]) == len(set(r["rule_id"] for r in CONTRACT["rules"])) == 4
    assert [r["code"] for r in CONTRACT["shared_precedence"]] == ["V0"]+[f"A{i}" for i in range(9)]
    assert set(CONTRACT["presentation_order"]) == STATUSES
    assert not {"priorite_examen","efficacite","score_gain"} & (set(CONTRACT["decision_inputs"]) | set(CONTRACT["output_contract"]))
    assert CONTRACT["documentary_action_ids"] == [f"A{i:02}" for i in range(5,13)]
    assert all(row["output"] in STATUSES and row["reason"].strip() for code,row in ROWS.items() if code!="V0")
    for rule in CONTRACT["rules"]:
        assert rule["rule_version"] == CONTRACT["ruleset_version"]
        assert rule["required_family_facts"] and rule["professional_checks"] and rule["references_officielles"]
    # Aucune prétendue validation contre un catalogue absent.
    assert "absent" in CONTRACT["catalogue_status"]


@pytest.mark.parametrize("case",CASES,ids=lambda c:c["case_id"])
def test_52_fixture_oracles_are_structurally_consistent_not_engine_results(case):
    expected = case["expected"]
    assert MAPPING[case["inputs"]["rule_id"]] == case["inputs"]["action_id"]
    assert "priorite_examen" not in case["inputs"]
    assert "SYNTHETIQUE" in json.dumps(case["inputs"],ensure_ascii=False)
    if expected["regle_decision"] == "V0":
        assert expected["statut"] == "ERREUR"  # Marqueur d'oracle, jamais un cinquième statut d'action.
        assert not validator("commonInput").is_valid(case["inputs"])
    else:
        validator("commonInput").validate(case["inputs"])
        row = ROWS[expected["regle_decision"]]
        assert expected["statut"] == row["output"]
        # Compatibilité de l'oracle avec son prédicat déclaré et la précédence.
        Draft202012Validator(row["predicate_schema"]).validate(case["inputs"])
        preceding = CONTRACT["shared_precedence"][1:int(expected["regle_decision"][1:])+1]
        assert all(not Draft202012Validator(r["predicate_schema"]).is_valid(case["inputs"]) for r in preceding)


def test_fixture_counts_and_scope_are_honest_about_missing_family_evidence():
    assert len(CASES)==52 and len(FIXTURES["multiproblemes"])==2
    identities=[c["case_id"] for c in CASES+FIXTURES["multiproblemes"]]
    assert len(set(identities))==54
    assert Counter(c["expected"]["statut"] for c in CASES)=={
        "etayee_pour_examen":4,"conditionnelle":8,"non_retenue_par_regle":8,"non_evaluable":20,"ERREUR":12}
    assert CONTRACT["test_fixture_contract"]["test_data"] is True
    assert CONTRACT["test_fixture_contract"]["family_evidence_is_placeholder"] is True
    assert all(not validator("normalizedInput").is_valid(c["inputs"]) for c in CASES)
    # Ces absences d'oracles détaillés sont signalées, pas comblées artificiellement.
    assert CONTRACT["test_fixture_contract"]["missing_expected_fields"] == ["motif_principal","limites","preuve_ids","error_code"]
    assert all("motif_principal" not in c["expected"] for c in CASES)


@pytest.mark.parametrize("multi",FIXTURES["multiproblemes"],ids=lambda c:c["case_id"])
def test_multiple_problem_oracles_keep_all_actions_without_benefit_ranking(multi):
    cases={c["case_id"]:c for c in CASES}
    assert len(set(multi["inputs_case_ids"]))==4
    references=[cases[i] for i in multi["inputs_case_ids"]]
    assert set(c["inputs"]["rule_id"] for c in references)==set(MAPPING)
    assert {c["inputs"]["action_id"]:c["expected"]["statut"] for c in references}==multi["expected"]
    assert len(multi["expected"])==4 and multi["no_benefit_ranking"] is True
    assert sum(s in {"etayee_pour_examen","conditionnelle"} for s in multi["expected"].values())>=2


def test_symbolic_table_partition_is_total_without_a_generic_a8_catch_all():
    # 432 états catégoriels par famille, avec les références synthétiques requises.
    domain=[]
    for app,method,coverage,signal,control,independent in product(
        ("oui","non_applicable_documentee","inconnue"),(False,True),
        ("suffisante","partielle","insuffisante"),("etaye","indicatif","absence_documentee","inconnu"),
        ("exclue","confirmee","non_evaluee"),(False,True)):
        d=deepcopy(CASES[0]["inputs"])
        d.update(applicabilite=app,applicabilite_reference="REFERENCE-SYNTHETIQUE" if app=="non_applicable_documentee" else None,
                 methode_validee=method,methode_reference="REFERENCE-SYNTHETIQUE" if method else None,
                 couverture_essentielle=coverage,signal=signal,controle_contradiction=control,
                 contradiction_references=["REFERENCE-SYNTHETIQUE"] if control=="confirmee" else [],
                 independance_reference="REFERENCE-SYNTHETIQUE" if independent else None,
                 preuve_absence_ids=["ABSENCE-SYNTHETIQUE"] if signal=="absence_documentee" else [])
        domain.append(d)
    admitted={i for i,d in enumerate(domain) if validator("commonInput").is_valid(d)}
    covered=set();partition={"V0":len(domain)-len(admitted)}
    for code,row in list(ROWS.items())[1:]:
        members={i for i in admitted if Draft202012Validator(row["predicate_schema"]).is_valid(domain[i])}
        partition[code]=len(members-covered)
        covered|=members
    assert len(domain)==432 and len(admitted)==240 and covered==admitted
    assert partition=={"V0":192,"A0":80,"A1":32,"A2":104,"A3":6,"A4":2,"A5":1,"A6":6,"A7":2,"A8":7}
    assert ROWS["A8"]["predicate_schema"]!={}
    print("\nAudit logique documentaire : 432 états, 240 admissibles, 192 impossibles, 0 trou ; pas d'exécution du moteur M4.")


@pytest.mark.parametrize("mutation", ["priority","bad_pair","unknown_rule","wrong_rule_version","boolean_id","numeric_bool", "empty_positive_proof",
                                     "absence_no_proof","contradiction_no_reference","nonapp_no_reference"])
def test_common_input_schema_rejects_invalid_claims_and_priority_dependency(mutation):
    data=deepcopy(CASES[0]["inputs"])
    if mutation=="priority": data["priorite_examen"]="elevee"
    elif mutation=="bad_pair": data["action_id"]="A01"
    elif mutation=="unknown_rule": data["rule_id"]="R5"
    elif mutation=="wrong_rule_version": data["rule_version"]="VERSION-INCONNUE"
    elif mutation=="boolean_id": data["maille_id"]=True
    elif mutation=="numeric_bool": data["methode_validee"]=1
    elif mutation=="empty_positive_proof": data["preuve_ids"]=[]
    elif mutation=="absence_no_proof": data["signal"]="absence_documentee"
    elif mutation=="contradiction_no_reference": data["controle_contradiction"]="confirmee"
    else: data.update(applicabilite="non_applicable_documentee",signal="inconnu")
    with pytest.raises(ValidationError): validator("commonInput").validate(data)


def normalized_example(rule_id):
    """Forme SYNTHÉTIQUE pour tester les types, jamais une preuve écologique.

    Audit-2 : les anciennes chaînes génériques sont remplacées par des structures
    explicites. Les déclarations d'approbation ci-dessous ne sont pas vérifiées
    par JSON Schema et n'autorisent aucun usage réel.
    """
    data=deepcopy(next(c["inputs"] for c in CASES if c["case_id"]==f"{rule_id}-positif_etaye"))
    data.update(maille_id=42,diagnostic_ids=[1,"1"],rule_version=CONTRACT["ruleset_version"])
    period={"debut":"2026-01-01","fin":"2026-12-31","reference":"PERIODE-SYNTHETIQUE"}
    rule=next(r for r in CONTRACT["rules"] if r["rule_id"]==rule_id)
    source={"namespace":"SOURCE-SYNTHETIQUE","id":1,"dataset_version":"VERSION-SYNTHETIQUE"}
    subframe={"code":"CODE-SYNTHETIQUE","referentiel":"REFERENTIEL-SYNTHETIQUE",
              "version":"VERSION-SYNTHETIQUE","pertinence":"etablie"}
    inventory={"source_objects":[source],"periode_reference":period}
    network={"reseau_id":"RESEAU-SYNTHETIQUE","objet_ids":[1,"1"],
             "geometry_reference":"GEOMETRIE-SYNTHETIQUE","sous_trame_code":"CODE-SYNTHETIQUE"}
    evaluation={"evaluation_id":"EVALUATION-SYNTHETIQUE","methode_id":"METHODE-SYNTHETIQUE",
                "methode_version":"VERSION-SYNTHETIQUE","methode_reference":"REFERENCE-SYNTHETIQUE",
                "conclusion":"declencheur_etabli","rapport_reference":"RAPPORT-SYNTHETIQUE"}
    values={
        "evenement_route_corridor_reference":{"conflit_id":"CONFLIT-SYNTHETIQUE",
            "route_sources":[{"namespace":"SOURCE-SYNTHETIQUE","id":1}],
            "corridor_sources":[{"namespace":"CORRIDOR-SYNTHETIQUE","id":"1"}],
            "geometry_reference":"GEOMETRIE-SYNTHETIQUE","event_binding_sha256":"0"*64},
        "statut_croisement":"conflit_potentiel", "validite_positive":True,
        "sous_trame_documentee":subframe,"route_source_versionnee":[source],
        "emprise_reliee":{"emprise_reference":"EMPRISE-SYNTHETIQUE","objet_ids":[1,"1"],"relation":"interieur"},
        "haies_inventaire_date":inventory,"sous_trame_bocagere":subframe,
        "continuite_reseau_referencee":network,"analyse_lacune_documentee":evaluation,
        "couverture_thematique":{"categories_requises":["CODE-SYNTHETIQUE"],"sous_trames_requises":["CODE-SYNTHETIQUE"],
            "categories_couvertes":["CODE-SYNTHETIQUE"],"sous_trames_couvertes":["CODE-SYNTHETIQUE"],
            "validation_reference":"REVUE-SYNTHETIQUE","conclusion":"suffisante_pour_faits_requis"},
        "friche_id_et_statut":{"friche_id":1,"statut_source":"STATUT-SYNTHETIQUE",
            "referentiel_statut":"REFERENTIEL-SYNTHETIQUE","version_referentiel":"VERSION-SYNTHETIQUE","eligibilite_etude":"etablie"},
        "friche_source_datee":inventory,
        "lien_geometrique_continuite":{"friche_id":1,"continuite_id":"1","relation_reference":"RELATION-SYNTHETIQUE",
            "methode_id":"METHODE-SYNTHETIQUE","methode_version":"VERSION-SYNTHETIQUE",
            "methode_reference":"REFERENCE-SYNTHETIQUE","conclusion":"declencheur_etabli"},
        "methode_voisinage_documentee":{"methode_id":"METHODE-SYNTHETIQUE","version":"VERSION-SYNTHETIQUE",
            "reference":"REFERENCE-SYNTHETIQUE","domaine_reference":"DOMAINE-SYNTHETIQUE"},
        "contexte_sol":{"source_reference":"REFERENCE-SYNTHETIQUE","nomenclature_reference":"REFERENTIEL-SYNTHETIQUE",
            "codes_observes":["CODE-SYNTHETIQUE"],"interpretation_reference":"INTERPRETATION-SYNTHETIQUE"},
        "inventaire_mares_date":inventory,"sous_trame_humide":subframe,"reseau_habitats_reference":network,
        "analyse_isolement_documentee":evaluation,
        "contexte_hydrologique":{"analyse_reference":"ANALYSE-SYNTHETIQUE","methode_id":"METHODE-SYNTHETIQUE",
            "methode_version":"VERSION-SYNTHETIQUE","methode_reference":"REFERENCE-SYNTHETIQUE","adequation_etude":"etablie"}}
    facts={f:{"etat":"documente","valeur":deepcopy(values[f]),"preuve_ids":["PREUVE-SYNTHETIQUE"],
              "reference":"REFERENCE-SYNTHETIQUE"} for f in rule["required_family_facts"]}
    data["family_evidence"]={
        "attestation_id":"ATTESTATION-SYNTHETIQUE","rule_id":rule_id,"maille_id":42,"diagnostic_ids":[1,"1"],
        "phenomene_id":"PHENOMENE-SYNTHETIQUE","emprise_reference":"EMPRISE-SYNTHETIQUE","periode_reference":period,
        "methode_id":"METHODE-SYNTHETIQUE","methode_version":"VERSION-SYNTHETIQUE","methode_reference":"REFERENCE-SYNTHETIQUE",
        "qualification":"etaye","preuve_ids":["PREUVE-SYNTHETIQUE"],
        "source_objects":[{"namespace":"SOURCE-SYNTHETIQUE","id":1,"dataset_version":"VERSION-SYNTHETIQUE",
                           "reference":"REFERENCE-SYNTHETIQUE","periode_reference":period}],
        "couvertures":[{"theme":"THEME-SYNTHETIQUE","statut":"validated","emprise_reference":"EMPRISE-SYNTHETIQUE",
                         "periode_reference":period,"reference":"REFERENCE-SYNTHETIQUE"}],
        "faits":facts,"validation_m2":{"reference":"REVUE-SYNTHETIQUE","validated_by":"EXPERT-SYNTHETIQUE",
                                         "validated_at":"2026-11-03T12:00:00+01:00","authentifie_par_logiciel":False},
        "limites":["EXEMPLE-SYNTHETIQUE-NON-OPERATIONNEL"],"independance":None,
        "liaison_evenement":{"conflit_id":"CONFLIT-SYNTHETIQUE","event_binding_sha256":"0"*64} if rule_id=="R1" else None}
    return data


@pytest.mark.parametrize("rule_id",list(MAPPING))
def test_proposed_family_attestation_shapes_are_typed_and_preserve_mixed_ids(rule_id):
    data=normalized_example(rule_id)
    validator("normalizedInput").validate(data)
    assert json.loads(json.dumps(data,allow_nan=False))["diagnostic_ids"]==[1,"1"]
    stripped=deepcopy(data);stripped["family_evidence"]={"reference":"SYNTHETIQUE"}
    with pytest.raises(ValidationError): validator("normalizedInput").validate(stripped)


@pytest.mark.parametrize("rule_id",list(MAPPING))
def test_a_supported_flag_without_family_facts_never_satisfies_the_proposed_schema(rule_id):
    data=normalized_example(rule_id)
    fact=CONTRACT["rules"][list(MAPPING).index(rule_id)]["required_family_facts"][0]
    data["family_evidence"]["faits"].pop(fact)
    with pytest.raises(ValidationError): validator("normalizedInput").validate(data)


@pytest.mark.parametrize("mutation", ["unknown_fact","wrong_qualification","wrong_family","wrong_r1_status", "false_positive_qa"])
def test_incoherent_proposed_attestations_are_structurally_rejected(mutation):
    data=normalized_example("R1");e=data["family_evidence"]
    if mutation=="unknown_fact": e["faits"]["sous_trame_documentee"]["etat"]="inconnu"
    elif mutation=="wrong_qualification": e["qualification"]="inconnu"
    elif mutation=="wrong_family": e["rule_id"]="R2"
    elif mutation=="wrong_r1_status": e["faits"]["statut_croisement"]["valeur"]="croisement_detecte"
    else: e["faits"]["validite_positive"]["valeur"]=False
    with pytest.raises(ValidationError): validator("normalizedInput").validate(data)


def test_absence_requires_a_negative_attestation_not_just_no_positive_objects():
    data=normalized_example("R2")
    data.update(signal="absence_documentee",preuve_ids=[],preuve_absence_ids=["ABSENCE-SYNTHETIQUE"])
    data["family_evidence"]["qualification"]="absence_documentee"
    with pytest.raises(ValidationError): validator("normalizedInput").validate(data)
    data["family_evidence"]["faits"]={"absence_declencheur":{"etat":"absence_documentee","valeur":True,
        "preuve_ids":["ABSENCE-SYNTHETIQUE"],"reference":"ABSENCE-SYNTHETIQUE"}}
    data["family_evidence"]["preuve_ids"]=["ABSENCE-SYNTHETIQUE"]
    validator("normalizedInput").validate(data)
    data["family_evidence"]["couvertures"][0]["statut"]="unknown"
    with pytest.raises(ValidationError): validator("normalizedInput").validate(data)


def test_positive_local_evidence_does_not_claim_global_inventory_completeness():
    for status in ("unknown","declared"):
        data=normalized_example("R1")
        data["family_evidence"]["couvertures"][0]["statut"]=status
        validator("normalizedInput").validate(data)
        assert data["couverture_essentielle"]=="suffisante"  # Faits locaux, pas exhaustivité de l'inventaire.


def test_reference_checks_and_public_filter_remain_explicit_m4_obligations():
    # JSON Schema ne prouve ni l'existence d'une source ni la véracité d'un avis.
    assert len(CONTRACT["referential_checks_required"])>=7
    assert "methode_id/version/reference" in CONTRACT["referential_checks_required"][2]
    assert "priorite_examen" not in SCHEMA["$defs"]["commonInput"]["properties"]
    assert not {"family_evidence","preuve_ids","source_objects","geometry","independance_reference"} & set(CONTRACT["public_display_allowlist"])
    assert "E_ACTION_TABLE_NON_TOTALE" in {v["code"] for v in CONTRACT["validation_errors"]}


def pending_example():
    data=deepcopy(next(c["inputs"] for c in CASES if c["case_id"]=="R1-couverture_inconnue"))
    data.update(maille_id=42,diagnostic_ids=[],rule_version=CONTRACT["ruleset_version"],couverture_essentielle="insuffisante")
    data["family_evidence"]={"etat":"en_attente","rule_id":"R1","maille_id":42,"diagnostic_ids":[],
        "qualification":"inconnu","manquants":["sources_M1_non_livrees"],"limites":["absence_non_demontree"],"reference_analyse":None}
    return data


def test_missing_m1_data_have_a_typed_pending_profile_without_fake_sources():
    data=pending_example()
    validator("normalizedInput").validate(data)
    assert data["diagnostic_ids"]==[] and "source_objects" not in data["family_evidence"]
    assert data["signal"]=="inconnu" and data["family_evidence"]["manquants"]


@pytest.mark.parametrize("claim",["etaye","absence_documentee","non_applicable_documentee"])
def test_pending_data_cannot_be_converted_to_a_positive_or_negative_claim(claim):
    data=pending_example()
    data.update(couverture_essentielle="suffisante",preuve_ids=["PREUVE-SYNTHETIQUE"],preuve_absence_ids=["ABSENCE-SYNTHETIQUE"])
    if claim=="non_applicable_documentee":
        data.update(applicabilite=claim,applicabilite_reference="DOMAINE-SYNTHETIQUE")
    else: data["signal"]=claim
    with pytest.raises(ValidationError): validator("normalizedInput").validate(data)


def test_non_applicability_has_a_documented_domain_profile_distinct_from_missing_data():
    data=pending_example()
    data.update(applicabilite="non_applicable_documentee",applicabilite_reference="DOMAINE-SYNTHETIQUE")
    complete=normalized_example("R1")["family_evidence"]
    data["family_evidence"]={
        "etat":"non_applicable_documentee","rule_id":"R1","maille_id":42,"diagnostic_ids":[],
        "qualification":"inconnu","applicabilite_reference":"DOMAINE-SYNTHETIQUE", "methode_id":"DOMAINE-SYNTHETIQUE",
        "methode_version":"VERSION-SYNTHETIQUE","methode_reference":"REFERENCE-SYNTHETIQUE","emprise_reference":"EMPRISE-SYNTHETIQUE",
        "periode_reference":complete["periode_reference"],"preuve_ids":["DOMAINE-SYNTHETIQUE"],
        "validation_m2":complete["validation_m2"],"limites":[]}
    validator("normalizedInput").validate(data)
