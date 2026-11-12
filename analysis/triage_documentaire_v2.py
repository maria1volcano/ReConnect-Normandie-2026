"""Extension documentaire V3b : présence locale observée, sans priorité écologique.

V1/V2/V3 sont conservées. Ni route, ni artificialisation, ni voisin seul ne
déclenchent V3b. La végétation cultivée/ornementale reste une couverture observée,
jamais une preuve d'habitat naturel ou de continuité fonctionnelle.
"""
from __future__ import annotations
from copy import deepcopy
from math import isfinite
from analysis.validate_inputs import AREA_TOLERANCE_M2, LENGTH_TOLERANCE_M

VERSION = "caen6-triage-documentaire-2.0-20261112"
VEGETATION_CS = {"CS2.1.1.1", "CS2.1.1.2", "CS2.1.1.3", "CS2.1.2", "CS2.1.3", "CS2.2.1", "CS2.2.2"}
AQUATIC_CS = {"CS1.2.2"}


def admissible(e):
    if not e.get("dans_maille") or e.get("source_statut") != "acquise_geometrie_valide":
        return False
    if not e.get("objet_id") or not isinstance(e.get("mesure"), (float, int)) or not isfinite(e["mesure"]):
        return False
    if e["couche"] == "haies":
        return e["unite"] == "m" and e["mesure"] > LENGTH_TOLERANCE_M
    if e["couche"] == "plans_eau":
        return e["unite"] == "m2" and e["mesure"] > AREA_TOLERANCE_M2
    if e["couche"] == "ocsge":
        return e.get("code_cs") in VEGETATION_CS | AQUATIC_CS and e["unite"] == "m2" and e["mesure"] > AREA_TOLERANCE_M2
    return False


def classify(original, evidence, critical_uncertainty=False):
    result = deepcopy(original)
    witnesses = [deepcopy(e) for e in evidence if admissible(e)]
    if original["niveau"] == "gris" and not critical_uncertainty and witnesses:
        result.update(niveau="jaune", regle="V3b", couleur_hex="#E8C84A",
            titre="Éléments végétalisés ou aquatiques cartographiés à documenter",
            motif="Présence locale documentée de haie, de couverture végétalisée OCS GE ou de surface en eau ; aucun croisement SRCE retenu par V1/V2. Ni habitat naturel, ni continuité fonctionnelle, ni besoin de travaux démontré.")
    result.update(application_version=VERSION, definition_version=VERSION, validation_ecologique=False,
        justificatifs_supplementaires=witnesses if result.get("regle") == "V3b" else [],
        critere_positif="présence locale dans une source acquise et géométrie valide ; complétude écologique non attestée",
        budgets_numeriques={"aire_m2": AREA_TOLERANCE_M2, "longueur_m": LENGTH_TOLERANCE_M,
            "usage": "Exclusion des seuls résidus numériques selon constantes M2 existantes ; aucun seuil écologique"})
    result["sources"] = list(dict.fromkeys(result.get("sources", []) + ["provenance/table_triage_exploratoire_v2.json"]))
    if result.get("regle") == "V3b":
        result["sources"].append("donnees/ocsge_complement.gpkg")
    return result
