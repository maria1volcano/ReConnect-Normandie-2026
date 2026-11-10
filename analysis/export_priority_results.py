"""Représentation JSON interne des résultats D/S, sans collision d'identifiants.

Cette fonction pure ne publie rien et ne modifie aucun contrat GeoJSON. Les
preuves et références privées restent internes ; une diffusion M4 exige sa revue.
"""

from __future__ import annotations

from copy import deepcopy
import math
from numbers import Real
from typing import Mapping

from analysis.detect_conflicts import canonical_json, identifier
from analysis.prepare_priority_inputs import PriorityInputError


def _json_value(value):
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, Real) and not math.isfinite(value):
        raise PriorityInputError("E_SERIALISATION_PRIORITE", "resultat", "NaN/Infinity interdit ; aucun remplacement par null.")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise PriorityInputError("E_SERIALISATION_PRIORITE", "resultat", "Clé non textuelle hors des index adaptés.")
        return {key: _json_value(child) for key, child in sorted(value.items())}
    if isinstance(value, (list, tuple)):
        return [_json_value(child) for child in value]
    raise PriorityInputError("E_SERIALISATION_PRIORITE", "resultat", "Valeur sans représentation JSON explicite.")


def prepare_priority_result_json(result: Mapping) -> dict:
    """Convertit les deux index Python en tableaux typés, sans modifier l'entrée.

    La priorité devient l'objet proposé {etat,valeur}. Le format déclaré est
    interne : sa structure proposée reste à approuver pour M3/M4, hors GeoJSON.
    """
    if not isinstance(result, Mapping):
        raise PriorityInputError("E_SERIALISATION_PRIORITE", "resultat", "Résultat D/S structuré requis.")
    payload = deepcopy(dict(result))
    for field, value_key in (("regles_diagnostics", "regle_D"), ("motifs_principaux_diagnostics", "motif_principal")):
        index = payload.get(field)
        if not isinstance(index, Mapping):
            raise PriorityInputError("E_SERIALISATION_PRIORITE", field, "Index Python de diagnostics requis.")
        records = []
        for diagnostic_id, value in sorted(index.items(), key=lambda pair: canonical_json(pair[0])):
            try:
                diagnostic_id = identifier(diagnostic_id)
            except (ValueError, TypeError):
                raise PriorityInputError("E_SERIALISATION_PRIORITE", field, "Identifiant chaîne/entier requis.") from None
            records.append({"diagnostic_id": diagnostic_id, value_key: value})
        payload[field] = records
    priority, state = payload.get("priorite_examen"), payload.get("etat_calcul_priorite")
    valid = ((state == "calculee" and isinstance(priority, str) and priority in {"elevee", "moderee", "faible"})
             or (state == "indeterminee" and priority == "indeterminee")
             or (state == "hors_territoire" and priority is None))
    if not valid:
        raise PriorityInputError("E_SERIALISATION_PRIORITE", "priorite_examen", "État et valeur de priorité discordants.")
    payload["priorite_examen"] = {"etat": state, "valeur": priority if state == "calculee" else None}
    payload["priority_result_format_version"] = "m2-priorites.internal-json-1"
    return _json_value(payload)
