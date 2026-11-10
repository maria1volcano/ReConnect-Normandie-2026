"""Normalisation EXCLUSIVEMENT SYNTHÉTIQUE des fixtures historiques de D/S.

Ce code n'est jamais importé par analysis et ne constitue pas une source M1.
Les résultats attendus ne sont ni lus ni utilisés par ces adaptateurs de tests.
"""

from copy import deepcopy
import json
from pathlib import Path

from analysis.detect_conflicts import canonical_json

METHOD = "m2-priorites.proposal-2"
FIXTURE_PATH = Path(__file__).parent / "fixtures/m2/decision_cases_m2.json"
CASES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]
PERIOD = {"debut":"2026-01-01", "fin":"2026-12-31"}


def diagnostic(**changes):
    result = {"diagnostic_id":"A", "famille_id":"route_corridor", "applicabilite":"oui",
              "applicabilite_reference":None, "enjeu_classe":"fort", "enjeu_methode_id":"METHODE-SYNTHETIQUE",
              "signal_pression":"conflit_potentiel", "validite_positive":True, "validite_absence":False,
              "contradiction_bloquante":False, "contradiction_reference":None, "motifs_qualite":[],
              "preuve_ids":["PREUVE-SYNTHETIQUE-A"], "source_objects":[], "phenomene_id":None,
              "periode_reference":None, "methode_famille_id":"METHODE-FAMILLE-SYNTHETIQUE-route_corridor"}
    result.update(changes)
    return result


def inputs(diagnostics=None, families=None, **changes):
    diagnostics = deepcopy([diagnostic()] if diagnostics is None else diagnostics)
    families = ["route_corridor"] if families is None else list(families)
    # Seul champ facultatif absent des fixtures v2 ; null explicite dans le contrat.
    for d in diagnostics:
        d.setdefault("periode_reference", None)
    family_methods = {f:[f"METHODE-FAMILLE-SYNTHETIQUE-{f}"] for f in families}
    references = {"METHODE-SYNTHETIQUE":{"version":"VERSION-SYNTHETIQUE", "reference":"REF-ENJEU-SYNTHETIQUE"}}
    for methods in family_methods.values():
        references.update({m:{"version":"VERSION-SYNTHETIQUE", "reference":"REF-FAMILLE-SYNTHETIQUE"} for m in methods})
    sources = {canonical_json(s):{**s, "reference":"REF-SOURCE-SYNTHETIQUE", "periode_reference":None}
               for d in diagnostics for s in d["source_objects"]}
    pilot = {"territory_id":"TERRITOIRE-SYNTHETIQUE", "grid_version":"GRILLE-SYNTHETIQUE",
             "dataset_version":"DONNEES-SYNTHETIQUES", "priority_method_version":METHOD,
             "familles_attendues":families, "methodes_familles":family_methods, "references_methodes":references,
             "sources":list(sources.values()),
             "preuves":{p:"DOCUMENT-SYNTHETIQUE-"+p for d in diagnostics for p in d["preuve_ids"]},
             "decision":{"reference":"PERIMETRE-SYNTHETIQUE", "methode_id":METHOD, "version":"SYNTHETIQUE-v2",
                         "validated_by":"APPROBATEUR-SYNTHETIQUE", "validated_at":"2026-11-03"},
             "limites_applicabilite":[], "motifs_versions_inconnues":[]}
    cell = {"maille_id":"MAILLE-SYNTHETIQUE", "study_area_m2":1_000_000, "diagnostics":diagnostics,
            **{k:deepcopy(pilot[k]) for k in ("territory_id", "grid_version", "dataset_version", "priority_method_version", "familles_attendues")}}
    cell.update(changes)
    return cell, pilot


def fixture_inputs(case):
    return inputs(case["diagnostics"], case["familles_attendues"], maille_id=case["case_id"],
                  study_area_m2=case["study_area_m2"], priority_method_version=case["priority_method_version"])


def review(**changes):
    result = {"reference":"REFERENCE-SYNTHETIQUE", "methode_id":"METHODE-SYNTHETIQUE",
              "version":"VERSION-SYNTHETIQUE", "validated_by":"EXPERT-SYNTHETIQUE",
              "validated_at":"2026-11-03", "periode_reference":dict(PERIOD)}
    result.update(changes)
    return result
