"""Validation du contrat M2 -> M4 `m2-m4.proposal-1` (démonstration).

Aligné sur `analysis/export_m2_contract.py` fourni par M2, sans dépendance
sur geopandas ni accès aux couches SIG de travail.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from shapely.geometry import shape

CONTRACT_VERSION = "m2-m4.proposal-1"
SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"
VERSIONS = ("grid_version", "method_version", "dataset_version")


class ContractError(ValueError):
    """Erreur explicite de contrat : l'API refuse de servir des jeux incohérents."""


def canonical_id(value: Any) -> str:
    """Conserver le type : `1` et `"1"` sont deux identifiants distincts."""
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ContractError("Un identifiant doit être une chaîne ou un entier (pas un booléen).")
    if isinstance(value, str) and not value.strip():
        raise ContractError("Identifiant de chaîne vide.")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _check_geometry(geometry: dict | None) -> None:
    if geometry is None:
        return
    try:
        geom = shape(geometry)
    except (ValueError, TypeError, KeyError) as exc:
        raise ContractError(f"Géométrie invalide : {exc}") from exc
    if geom.is_empty or not geom.is_valid:
        raise ContractError("Géométrie GeoJSON vide ou topologiquement invalide.")
    if geometry["type"] in {"Polygon", "MultiPolygon"}:
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for polygon in polygons:
            for ring in polygon:
                if ring[0] != ring[-1]:
                    raise ContractError("Anneau GeoJSON non fermé.")

    def check_segments(coordinates):
        if not coordinates or not isinstance(coordinates[0], list):
            return
        if coordinates[0] and isinstance(coordinates[0][0], (int, float)):
            if any(abs(a[0] - b[0]) > 180 for a, b in zip(coordinates, coordinates[1:])):
                raise ContractError("Segment non découpé traversant l'antiméridien.")
        else:
            for sub in coordinates:
                check_segments(sub)

    if geometry["type"] != "MultiPoint":
        check_segments(geometry["coordinates"])


def validate_m2_contract(mailles: dict, conflits: dict) -> dict[str, int | None]:
    """Schémas M2 + validité géométrique + réciprocité + comptages cohérents.

    Vérifie les deux FeatureCollections complètes ensemble, jamais des sous-ensembles
    filtrés par l'API.
    """
    try:
        json.dumps([mailles, conflits], allow_nan=False)
        for payload, name in ((mailles, "mailles"), (conflits, "conflits")):
            schema = json.loads((SCHEMAS / f"schema_{name}.json").read_text(encoding="utf-8"))
            Draft202012Validator(schema).validate(payload)
            for feat in payload["features"]:
                _check_geometry(feat["geometry"])

        for key in ("contract_version", "test_data", "statut_diffusion", "provenance", "resume"):
            if mailles[key] != conflits[key]:
                raise ContractError(f"Métadonnées des collections discordantes : {key}")

        def index(collection: dict, id_name: str) -> dict[str, dict]:
            result = {}
            for feature in collection["features"]:
                props = feature["properties"]
                key = canonical_id(props[id_name])
                if key in result:
                    raise ContractError(f"Identifiant dupliqué : {key}")
                result[key] = props
            return result

        cells = index(mailles, "maille_id")
        events = index(conflits, "conflit_id")
        cell_links, event_links = set(), set()
        exclusive_total = 0
        for cell_id, cell in cells.items():
            for version in VERSIONS:
                if cell[version] != mailles["provenance"][version]:
                    raise ContractError("Version des mailles discordante.")
            for cid in cell["conflit_ids"]:
                event_id = canonical_id(cid)
                if event_id not in events:
                    raise ContractError(f"Conflit référencé absent : {event_id}")
                cell_links.add((cell_id, event_id))
            count = cell["indicateurs"]["nb_evenements_observes"]
            analyzed = cell["statut_analyse"] == "analyse_effectuee"
            if (analyzed and count != len(cell["conflit_ids"])) or (not analyzed and (count is not None or cell["conflit_ids"])):
                raise ContractError("Comptage local incompatible avec le statut d'analyse.")
            complete = cell["qualite"]["routes_couverture_validee"] and cell["qualite"]["corridors_couverture_validee"]
            if cell["indicateurs"]["nb_evenements"] != (count if complete and analyzed else None):
                raise ContractError("Comptage complet non justifié par couverture et observation.")
            exclusive = cell["indicateurs"]["nb_evenements_exclusifs_observes"]
            if (analyzed and (exclusive is None or exclusive > count)) or (not analyzed and exclusive is not None):
                raise ContractError("Comptage exclusif invalide.")
            exclusive_total += exclusive or 0

        for event_id, event in events.items():
            if event["method_version"] != conflits["provenance"]["method_version"]:
                raise ContractError("Version d'événement discordante.")
            for mid in event["maille_ids"]:
                cell_id = canonical_id(mid)
                if cell_id not in cells:
                    raise ContractError(f"Maille référencée absente : {cell_id}")
                event_links.add((cell_id, event_id))
        if cell_links != event_links:
            raise ContractError("Relations réciproques mailles-conflits discordantes.")
        observed = len(events) if mailles["resume"]["analyse_effectuee"] else None
        if (not mailles["resume"]["analyse_effectuee"] and (events or any(c["statut_analyse"] == "analyse_effectuee" for c in cells.values()))) or exclusive_total != len(events):
            raise ContractError("État d'analyse global ou comptage des propriétaires exclusifs discordant.")
        if mailles["resume"]["evenements_distincts_observes"] != observed or mailles["resume"]["relations_spatiales"] != len(cell_links):
            raise ContractError("Résumé global incohérent (double comptage possible).")
        return {"mailles": len(cells), "evenements_distincts_observes": observed, "relations_spatiales": len(cell_links)}
    except ContractError:
        raise
    except Exception as exc:
        raise ContractError(f"Contrat M2 invalide : {exc}") from exc
