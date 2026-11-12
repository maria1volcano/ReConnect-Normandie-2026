"""Tables D/S proposal-2 : fonctions pures, sans export ni moteur d'actions."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from itertools import combinations
from typing import Callable, Mapping

from analysis.detect_conflicts import canonical_json
from analysis.prepare_priority_inputs import (
    POSITIVE_SIGNALS, PreparedPriorityInputs, PriorityInputError,
    validate_diagnostic_inputs,
)


@dataclass(frozen=True)
class DiagnosticRule:
    code: str
    matches: Callable[[Mapping], bool]
    signal: str
    reason: Callable[[Mapping], str]


def _constant(reason):
    return lambda d: reason


# L'ordre de cette table est normatif. Plusieurs prédicats peuvent être vrais.
D_RULES = (
    DiagnosticRule("D0", lambda d: d["applicabilite"] == "non_applicable_documentee", "hors_champ",
                   _constant("non_applicabilite_documentee")),
    DiagnosticRule("D1", lambda d: d["contradiction_bloquante"] is True or d["applicabilite"] == "inconnue", "indetermine",
                   lambda d: "donnees_contradictoires" if d["contradiction_bloquante"] is True else "applicabilite_inconnue"),
    DiagnosticRule("D2", lambda d: d["enjeu_classe"] == "inconnu" or d["enjeu_methode_id"] is None, "indetermine",
                   lambda d: "enjeu_non_documente" if d["enjeu_classe"] == "inconnu" else "methode_enjeu_absente"),
    DiagnosticRule("D3", lambda d: d["signal_pression"] in {"non_evalue", "non_concluant"}, "indetermine",
                   lambda d: "pression_non_evaluee" if d["signal_pression"] == "non_evalue" else "preuve_non_concluante"),
    DiagnosticRule("D4", lambda d: d["signal_pression"] in POSITIVE_SIGNALS and not d["validite_positive"], "indetermine",
                   _constant("preuve_positive_non_validee")),
    DiagnosticRule("D5", lambda d: d["enjeu_classe"] == "fort" and d["signal_pression"] in {"obstacle_confirme", "conflit_potentiel"}
                   and d["validite_positive"], "eleve", _constant("conflit_etaye_enjeu_fort")),
    DiagnosticRule("D6", lambda d: d["enjeu_classe"] == "fort" and d["signal_pression"] == "croisement_detecte"
                   and d["validite_positive"], "modere", _constant("croisement_non_qualifie_enjeu_fort")),
    DiagnosticRule("D7", lambda d: d["enjeu_classe"] == "moyen" and d["signal_pression"] in POSITIVE_SIGNALS
                   and d["validite_positive"], "modere", _constant("pression_observee_enjeu_moyen")),
    DiagnosticRule("D8", lambda d: d["enjeu_classe"] == "faible" and d["signal_pression"] in {"obstacle_confirme", "conflit_potentiel"}
                   and d["validite_positive"], "modere", _constant("conflit_etaye_enjeu_faible")),
    DiagnosticRule("D9", lambda d: d["signal_pression"] == "absence_validee" and d["validite_absence"]
                   and d["enjeu_classe"] != "inconnu" and d["enjeu_methode_id"] is not None,
                   "faible", _constant("absence_pression_validee")),
    DiagnosticRule("D10a", lambda d: d["enjeu_classe"] == "faible" and d["signal_pression"] == "croisement_detecte"
                   and d["validite_positive"], "indetermine", _constant("signal_non_qualifie")),
)


def normalize_diagnostics_by_family(prepared: PreparedPriorityInputs) -> dict[str, list[dict]]:
    """Regroupe les diagnostics contrôlés, sans les fusionner ni créer des absents."""
    families = {family: [] for family in prepared.pilot["familles_attendues"]}
    for diagnostic in prepared.diagnostics:
        families[diagnostic["famille_id"]].append(deepcopy(diagnostic))
    return families


def _evaluate_diagnostic(diagnostic: dict, pilot: dict) -> dict:
    rule = next((rule for rule in D_RULES if rule.matches(diagnostic)), None)
    if rule is None:
        raise PriorityInputError("E_TABLE_NON_TOTALE", "diagnostic", "Aucune règle D n'admet cette combinaison valide.")
    reason = rule.reason(diagnostic)
    limitations = set(diagnostic["motifs_qualite"])
    if rule.signal == "indetermine":
        limitations.add(reason)
    control = diagnostic.get("controle_contradictions")
    incomplete_control = bool(control and control["contradiction_bloquante"] is None
                              and control["cible"] != "autre_affirmation"
                              and diagnostic["applicabilite"] != "non_applicable_documentee")
    # Les entrées historiques ne qualifient pas la portée des contradictions.
    # D0 reste prioritaire, mais ne peut certifier une couverture suffisante ici.
    ambiguous_scope = (rule.code == "D0" and diagnostic["contradiction_bloquante"] is True and control is None)
    if ambiguous_scope:
        limitations.add("portee_contradiction_non_documentee")
    if rule.code == "D0" and control and control["contradiction_bloquante"] is True:
        limitations.add("contradiction_hors_applicabilite")
    if control and control["contradiction_bloquante"] is None:
        limitations.add("controle_contradiction_non_evalue")
    method_ids = [diagnostic["methode_famille_id"], diagnostic["enjeu_methode_id"]]
    references = {key: deepcopy(pilot["references_methodes"][key]) for key in sorted(set(k for k in method_ids if k))}
    return {"diagnostic_id": diagnostic["diagnostic_id"], "famille_id": diagnostic["famille_id"],
            "signal_diagnostic": rule.signal, "regle_D": rule.code, "motif_principal": reason,
            "motifs_qualite": list(diagnostic["motifs_qualite"]), "motifs_limites": sorted(limitations),
            "deficit_decisionnel": (rule.signal == "indetermine" and reason != "signal_non_qualifie")
                                   or incomplete_control or ambiguous_scope,
            "controle_contradictions": deepcopy(control),
            "references_methodologiques": references, "preuve_ids": list(diagnostic["preuve_ids"]),
            "source_objects": deepcopy(diagnostic["source_objects"]), "phenomene_id": diagnostic["phenomene_id"],
            "periode_reference": deepcopy(diagnostic["periode_reference"]), "entree": deepcopy(diagnostic)}


def _diagnostic_links(diagnostics):
    links = []
    for left, right in combinations(diagnostics, 2):
        identities = [left["diagnostic_id"], right["diagnostic_id"]]
        source_sets = [{canonical_json(source) for source in d["source_objects"]} for d in (left, right)]
        if source_sets[0] & source_sets[1]:
            links.append({"diagnostic_ids": identities, "raison": "source_partagee"})
        if left["phenomene_id"] is not None and canonical_json(left["phenomene_id"]) == canonical_json(right["phenomene_id"]):
            links.append({"diagnostic_ids": identities, "raison": "phenomene_partage"})
    return sorted(links, key=canonical_json)


def evaluate_priorities(cell: Mapping, pilot: Mapping) -> dict:
    """Valide puis décide D0–D10a et S0–S4, indépendamment de l'ordre des données.

    Les booléens de capacité sont des entrées QA contrôlées, jamais déduites d'une
    couleur ou d'une absence de source. Cette fonction ne qualifie pas le terrain.
    """
    prepared = validate_diagnostic_inputs(cell, pilot)
    cell, pilot = prepared.cell, prepared.pilot
    result = {"maille_id": cell["maille_id"], "priority_method_version": pilot["priority_method_version"],
              "territory_id": cell["territory_id"], "grid_version": cell["grid_version"],
              "dataset_version": cell["dataset_version"], "familles_attendues": list(pilot["familles_attendues"]),
              "motifs_tracabilite": sorted(set(pilot["motifs_versions_inconnues"])),
              "diagnostic_ids_justificatifs": [], "diagnostic_ids_non_evalues": [],
              "familles_manquantes": [], "regles_diagnostics": {}, "motifs_principaux_diagnostics": {},
              "diagnostics": [], "liens_diagnostics": [], "relation_diagnostics": "relation_non_etablie",
              "decision_pilote": deepcopy(pilot["decision"])}
    if cell["study_area_m2"] == 0:
        return {**result, "priorite_examen": None, "couverture_synthese": None, "regle_appliquee": "S0",
                "etat_calcul_priorite": "hors_territoire",
                "statut_analyse": "hors_territoire", "motifs_limites": ["hors_territoire"]}
    groups = normalize_diagnostics_by_family(prepared)
    missing = [family for family, diagnostics in groups.items() if not diagnostics]
    details = [_evaluate_diagnostic(d, pilot) for d in prepared.diagnostics]
    limitations = set(pilot["limites_applicabilite"]) | {reason for d in details for reason in d["motifs_limites"]}
    if missing:
        limitations.add("famille_attendue_absente")
    partial = bool(missing or any(d["deficit_decisionnel"] for d in details))
    by_signal = {signal: [d["diagnostic_id"] for d in details if d["signal_diagnostic"] == signal]
                 for signal in ("eleve", "modere", "faible", "indetermine", "hors_champ")}
    if by_signal["eleve"]:
        rule, priority, selected = "S1", "elevee", by_signal["eleve"]
    elif by_signal["modere"]:
        rule, priority, selected = "S2", "moderee", by_signal["modere"]
    elif by_signal["faible"] and not partial and all(d["signal_diagnostic"] in {"faible", "hors_champ"} for d in details):
        rule, priority, selected = "S3", "faible", by_signal["faible"]
    else:
        rule, priority, selected = "S4", "indeterminee", []
        if details and not missing and all(d["signal_diagnostic"] == "hors_champ" for d in details):
            limitations.add("aucune_famille_applicable")
    links = _diagnostic_links(details)
    return {**result, "priorite_examen": priority, "regle_appliquee": rule,
            "statut_analyse": cell.get("statut_analyse"),
            "etat_calcul_priorite": "indeterminee" if priority == "indeterminee" else "calculee",
            "couverture_synthese": "partielle" if partial else "complete",
            "diagnostic_ids_justificatifs": selected, "diagnostic_ids_non_evalues": by_signal["indetermine"],
            "familles_manquantes": missing, "motifs_limites": sorted(limitations),
            "regles_diagnostics": {d["diagnostic_id"]: d["regle_D"] for d in details},
            "motifs_principaux_diagnostics": {d["diagnostic_id"]: d["motif_principal"] for d in details},
            "diagnostics": details, "liens_diagnostics": links,
            "relation_diagnostics": "liens_documentes" if links else "relation_non_etablie"}
