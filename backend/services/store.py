"""Chargement sûr des exports M2 et données M1/M5 ; aucune réécriture scientifique."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contract import ContractError, canonical_id, validate_m2_contract


BASE_DIR = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f"Fichier attendu absent : {path}")

    def reject_constant(value):
        raise ValueError(f"Nombre JSON invalide : {value}")

    def reject_duplicate_keys(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Clé JSON dupliquée : {key}")
            result[key] = value
        return result

    with path.open(encoding="utf-8") as f:
        return json.load(f, parse_constant=reject_constant, object_pairs_hook=reject_duplicate_keys)


@dataclass(frozen=True)
class Store:
    mailles: dict
    conflits: dict
    maille_index: dict[str, dict]
    conflit_index: dict[str, dict]
    sources: list[dict]
    actions: dict[str, dict] | None
    fiches: dict[str, dict] | None
    validation: dict

    @property
    def provenance(self):
        return self.mailles["provenance"]

    @property
    def test_data(self):
        return self.mailles["test_data"]


def load_store(data_dir: Path, sources_file: Path | None = None,
               actions_file: Path | None = None, fiches_file: Path | None = None) -> Store:
    mailles = read_json(data_dir / "mailles.geojson")
    conflits = read_json(data_dir / "conflits.geojson")
    validation = validate_m2_contract(mailles, conflits)

    # Les schémas M2 fournis ne certifient que le lot synthétique et ne doivent
    # pas être contournés pour publier des données réelles non autorisées.
    if mailles["test_data"] is not True or mailles["statut_diffusion"] != "synthetique_uniquement":
        raise ContractError("Publication de données réelles non autorisée par ce contrat provisoire.")

    mi = {canonical_id(f["properties"]["maille_id"]): f for f in mailles["features"]}
    ci = {canonical_id(f["properties"]["conflit_id"]): f for f in conflits["features"]}

    sources = []
    if sources_file is not None and sources_file.is_file():
        with sources_file.open(encoding="utf-8-sig", newline="") as f:
            sources = list(csv.DictReader(f, delimiter=";"))
        if not sources or not {"identifiant", "nom", "producteur", "url", "licence", "statut"}.issubset(sources[0]):
            raise ContractError("Inventaire M1 incomplet ou en-têtes incompatibles.")

    actions = None
    if actions_file is not None and actions_file.is_file():
        payload = read_json(actions_file)
        if isinstance(payload, dict) and isinstance(payload.get("actions"), list):
            payload = payload["actions"]
        if not isinstance(payload, list):
            raise ContractError("catalogue_actions.json doit être une liste ou {actions:[...]}.")
        actions = {}
        for item in payload:
            if not isinstance(item, dict) or "action_id" not in item:
                raise ContractError("Chaque action doit porter action_id.")
            aid = canonical_id(item["action_id"])
            if aid in actions:
                raise ContractError(f"Action dupliquée : {aid}")
            actions[aid] = item

    fiches = None
    if fiches_file is not None and fiches_file.is_file():
        payload = read_json(fiches_file)
        if isinstance(payload, dict) and isinstance(payload.get("fiches"), list):
            payload = payload["fiches"]
        if not isinstance(payload, list):
            raise ContractError("fiches_zones.json doit être une liste ou {fiches:[...]}.")
        fiches = {}
        for fiche in payload:
            if not isinstance(fiche, dict) or "maille_id" not in fiche:
                raise ContractError("Chaque fiche doit porter maille_id.")
            mid = canonical_id(fiche["maille_id"])
            if mid in fiches or mid not in mi:
                raise ContractError(f"Fiche en doublon ou sans maille : {mid}")
            # Le backend ne crée pas de liens ni d'actions scientifiques.
            if "conflit_ids" in fiche and {canonical_id(x) for x in fiche["conflit_ids"]} != {canonical_id(x) for x in mi[mid]["properties"]["conflit_ids"]}:
                raise ContractError(f"Liens de fiche incohérents : {mid}")
            fiches[mid] = fiche

    return Store(mailles, conflits, mi, ci, sources, actions, fiches, validation)
