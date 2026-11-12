"""Loopback-only M4 adapter for the immutable internal M2 demonstration ZIP."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse


EXPECTED_SHA256 = "F1878207F370DC2A424898CF2DE89DB540D6EABAB43BD7E5F6C93BBF3C2FD3B4"
PREFIX = "RECONNECT_CAEN_ET_NORD_M2_DEMO_INTERNE_20261111_V1/"
GRID_VERSION = "M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1"
TERRITORY_ID = "caen_et_nord_6communes"
ACTIONS_SHA256 = "F509ABEBD41741F5133949D53B4A88C8DB52F34094F99EE00E9B0217EEE41927"
ACTIONS_PREFIX = "RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1/"
ACTIONS_VERSION = "caen6-priorites-etude-actions-20261112-1"

TRIAGE_COLORS = {"rouge": "#D9534F", "orange": "#F29A48", "jaune": "#E6C65B", "gris": "#89938F"}


class ScopeError(ValueError):
    pass


class M2Store:
    def __init__(self, zip_path: Path):
        self.zip_path = zip_path.resolve()
        digest = hashlib.sha256(self.zip_path.read_bytes()).hexdigest().upper()
        if digest not in {EXPECTED_SHA256, ACTIONS_SHA256}:
            raise ValueError("Empreinte du lot M2 incompatible")
        self.actions_release = digest == ACTIONS_SHA256
        self.source_sha256 = digest.lower()
        self.prefix = ACTIONS_PREFIX if self.actions_release else PREFIX
        with zipfile.ZipFile(self.zip_path) as archive:
            self.grid = self._read(archive, "demo_interne/mailles.geojson")
            sheets = self._read(archive, "demo_interne/fiches_zones.json")
            self.manifest = self._read(archive, "manifest.json")
            self.summary = self._read(archive, "rapports/bilan_actions.json" if self.actions_release else "rapports/bilan.json")
            self.native_counts = self._read(archive, "reference_historique/manifest.json")["counts"] if self.actions_release else self.manifest["counts"]
            self.trace = self._read(archive, "demo_interne/pistes_investigation_trace.json")["pistes"] if self.actions_release else []
        self.sheets = {sheet["maille_id"]: sheet for sheet in sheets["fiches"]}
        self._validate()

    def _read(self, archive: zipfile.ZipFile, relative: str):
        return json.loads(archive.read(self.prefix + relative).decode("utf-8"))

    def _validate(self) -> None:
        scope = self.grid.get("scope", {})
        if scope.get("grid_version") != GRID_VERSION or scope.get("territory_id") != TERRITORY_ID:
            raise ValueError("Portée du lot M2 incompatible")
        features = self.grid.get("features", [])
        if len(features) != 101 or len(self.sheets) != 101:
            raise ValueError("Le lot M2 doit contenir 101 mailles et 101 fiches")
        ids = [feature["properties"]["maille_id"] for feature in features]
        if len(ids) != len(set(ids)) or set(ids) != set(self.sheets):
            raise ValueError("Identifiants M2 non uniques ou fiches orphelines")

        if self.actions_release:
            if (self.manifest.get("version_priorisation_etudes") != ACTIONS_VERSION
                    or self.manifest.get("classification_defaut") != "priorites_etude_interventions"
                    or self.manifest.get("test_data") is not False
                    or self.manifest.get("publication_autorisee") is not False):
                raise ValueError("Version ou restrictions du lot d'actions incompatibles")
            if len(self.trace) != 165 or len({p["piste_id"] for p in self.trace}) != 165:
                raise ValueError("Trace des pistes incohérente")
            for key, sheet in self.sheets.items():
                d = sheet["decision_interventions"]
                if any(d.get(k) != v for k, v in {"maille_id": key, "grid_version": GRID_VERSION,
                        "territory_id": TERRITORY_ID, "version": ACTIONS_VERSION}.items()):
                    raise ValueError("Jointure de décision incompatible")
                if d["D_S"]["priorite_ecologique"] != sheet["priorite_ecologique"]:
                    raise ValueError("Priorité scientifique incohérente")

    @staticmethod
    def check_scope(territory_id: str, grid_version: str) -> None:
        if territory_id != TERRITORY_ID or grid_version != GRID_VERSION:
            raise ScopeError("Version de grille ou territoire incompatible")

    def minimal_grid(self) -> dict:
        features = []
        for source in self.grid["features"]:
            props = source["properties"]
            level = props["triage_verification"]
            features.append({
                "type": "Feature",
                "geometry": source["geometry"],
                "properties": {
                    "territory_id": TERRITORY_ID,
                    "grid_version": GRID_VERSION,
                    "maille_id": props["maille_id"],
                    "area_m2": props["area_m2"],
                    "is_boundary": props["is_boundary"],
                    "pilot_fraction": props["pilot_fraction"],
                    "documentary_level": level,
                    "documentary_rule": props["triage_regle"],
                    "documentary_color": TRIAGE_COLORS[level],
                    **({"study_priority": self.sheets[props["maille_id"]]["priorite_etude_interventions"]}
                       if self.actions_release else {}),
                    "priority_category": "INDETERMINATE",
                    "priority_validation_status": "PENDING",
                },
            })
        return {"type": "FeatureCollection", "scope": self.grid["scope"], "features": features,
                "decision_version": ACTIONS_VERSION if self.actions_release else None}

    def metadata(self) -> dict:
        counts = self.native_counts
        return {
            "territory_id": TERRITORY_ID,
            "grid_version": GRID_VERSION,
            "dataset_version": self.grid["scope"]["dataset_version"],
            "diffusion": "interne_revue_uniquement",
            "publication_authorized": False,
            "cells": 101,
            "diagnostic_sheets": 101,
            "events_detected": counts["evenements_detectes"],
            "events_admitted": counts["evenements_agreges"],
            "events_quarantined": counts["evenements_en_quarantaine"],
            "cell_event_relations": counts["liens"],
            "cells_with_events": counts["mailles_avec_evenements"],
            "documentary_counts": self.summary["couleurs"] if self.actions_release else self.summary["classifications_exploratoires"],
            "documentary_leads": self.summary["pistes_par_famille"] if self.actions_release else self.summary["pistes_investigation"],
            "decision_version": ACTIONS_VERSION if self.actions_release else None,
            "source_zip_sha256": self.source_sha256,
            "test_data": False,
            "validated_recommendations": 0,
        }

    def cell(self, maille_id: str, territory_id: str, grid_version: str) -> dict:
        self.check_scope(territory_id, grid_version)
        sheet = self.sheets.get(maille_id)
        if sheet is None:
            raise KeyError(maille_id)
        triage = sheet["triage_documentaire"]
        observations = sheet["diagnostic_techniciens"]
        return {
            "territory_id": TERRITORY_ID,
            "grid_version": GRID_VERSION,
            "dataset_version": sheet["dataset_version"],
            "maille_id": maille_id,
            "municipalities": sheet["communes"],
            "area_m2": sheet["surface_m2"],
            "is_boundary": sheet["maille_partielle"],
            "documentary": {
                "level": triage["niveau"],
                "rule": triage["regle"],
                "title": triage["titre"],
                "reason": triage["motif"],
                "color": TRIAGE_COLORS[triage["niveau"]],
                "observations": triage["observations_justificatives"],
            },
            "ecological_priority": {
                "category": "INDETERMINATE",
                "scientific_validation": "PENDING",
                "method_version": None,
            },
            "geometric_observations": {
                "local_event_count": observations["nb_evenements_observes"],
                "canonical_event_count": observations["nb_evenements_exclusifs_observes"],
                "source_observations": observations["observations"],
                "enj": observations["ENJ"],
            },
            "investigations": [{
                "action_id": item["action_id"],
                "rule_id": item["regle_id"],
                "title": item["titre"],
                "status": item["statut_regle_m2"],
                "lead_status": item["piste_investigation"],
                "evidence": item["observations_justificatives"],
                "reason": item["motif"],
                "missing_conditions": item["conditions_manquantes"],
                "validation_level": item["niveau_de_validation"],
                "works_recommended": False,
            } for item in sheet["actions"]],
            "limitations": sheet["limites"],
            "validated_recommendations": [],
            **self._instruction(sheet),
        }

    def _instruction(self, sheet: dict) -> dict:
        if not self.actions_release:
            return {}
        d = sheet["decision_interventions"]
        # Explicit allowlist: no raw source objects, event IDs, geometry or local paths.
        option_keys = ("action_id", "regle_id", "statut_instruction", "statut_scientifique",
                       "regle_decision_scientifique", "justification", "observations",
                       "conditions_manquantes", "piste_existante_id", "piste_existante_statut",
                       "restauration_selectionnee", "travaux_valides", "activation_regle_scientifique",
                       "prochaines_etapes")
        def option(value):
            return {k: value[k] for k in option_keys if k in value} if value else None
        return {
            "study_priority": d["priorite_etude_interventions"],
            "instruction": {
                "version": d["version"],
                "diagnostic": d["diagnostic_territorial"],
                "main_action": option(d["action_principale"]),
                "no_main_reason": d["motif_absence_action_principale"],
                "complementary_actions": [option(a) for a in d["actions_complementaires"]],
                "no_complementary_reason": d["motif_absence_complementaires"],
                "options": [option(a) for a in d["options_actions"]],
                "orientation": d["orientation"],
                "conditions_before_works": d["conditions_validation_avant_travaux"],
                "DS": d["D_S"],
                "historical_lead_ids": d["pistes_existantes_ids"],
                "road_context": (d["action_principale"] or {}).get("justificatifs", {}).get("contexte_routier"),
            },
            "provenance": {"source_zip_sha256": self.source_sha256,
                           "decision_version": ACTIONS_VERSION, "dataset_version": sheet["dataset_version"],
                           "test_data": False, "publication_authorized": False},
        }


def make_handler(store: M2Store, allowed_origin: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "ReConnectLocalM4/1.0"

        def _headers(self, status: int) -> None:
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store, private")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            origin = self.headers.get("Origin")
            if origin == allowed_origin:
                self.send_header("Access-Control-Allow-Origin", allowed_origin)
                self.send_header("Vary", "Origin")
            self.end_headers()

        def _send(self, status: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            self._headers(status)
            self.wfile.write(body)

        def _request_allowed(self) -> bool:
            host = self.headers.get("Host", "").split(":", 1)[0]
            remote = self.client_address[0]
            forwarded = self.headers.get("Forwarded") or self.headers.get("X-Forwarded-For")
            return host in {"127.0.0.1", "localhost"} and remote in {"127.0.0.1", "::1"} and not forwarded

        def do_OPTIONS(self) -> None:
            if not self._request_allowed() or self.headers.get("Origin") != allowed_origin:
                return self._send(403, {"error": "local_demo_only"})
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Accept")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

        def do_GET(self) -> None:
            if not self._request_allowed():
                return self._send(403, {"error": "local_demo_only"})
            parsed = urlparse(self.path)
            if parsed.path == "/health":
                return self._send(200, {"status": "ok", "mode": "local_internal_demo"})
            if parsed.path == "/api/internal/caen/metadata":
                return self._send(200, store.metadata())
            if parsed.path == "/api/internal/caen/grid":
                query = parse_qs(parsed.query)
                try:
                    store.check_scope(
                        query.get("territory_id", [""])[0],
                        query.get("grid_version", [""])[0],
                    )
                    return self._send(200, store.minimal_grid())
                except ScopeError as error:
                    return self._send(409, {"error": "scope_mismatch", "detail": str(error)})
            match = re.fullmatch(r"/api/internal/caen/cells/([^/]+)", parsed.path)
            if match:
                query = parse_qs(parsed.query)
                try:
                    payload = store.cell(
                        unquote(match.group(1)),
                        query.get("territory_id", [""])[0],
                        query.get("grid_version", [""])[0],
                    )
                    return self._send(200, payload)
                except ScopeError as error:
                    return self._send(409, {"error": "scope_mismatch", "detail": str(error)})
                except KeyError:
                    return self._send(404, {"error": "cell_not_found"})
            return self._send(404, {"error": "route_not_found"})

        def log_message(self, fmt: str, *args) -> None:
            sys.stderr.write("[m4-local] " + fmt % args + "\n")

    return Handler


def main() -> None:
    zip_value = os.environ.get("RECONNECT_M2_ZIP")
    if not zip_value:
        raise SystemExit("RECONNECT_M2_ZIP doit pointer vers le ZIP M2 audité")
    port = int(os.environ.get("RECONNECT_M4_PORT", "8765"))
    origin = os.environ.get("RECONNECT_FRONTEND_ORIGIN", "http://127.0.0.1:5173")
    store = M2Store(Path(zip_value))
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(store, origin))
    print(f"M4 local interne prêt sur http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
