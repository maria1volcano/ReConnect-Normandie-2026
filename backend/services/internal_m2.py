"""Accès interne, strictement non public, au lot Caen-Nord M2 du 11/11/2026.

Ce module ne reprojette, ne reconstruit, ni ne publie de géométries.
L'API officielle proposal-1 reste réservée aux fixtures synthétiques.
Pour le lot réel, le manifeste et le vérificateur de M2 doivent être exécutés
avant tout branchement. Aucune attestation écologique n'est produite ici.
"""
from __future__ import annotations

import hashlib
import sqlite3
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from .contract import ContractError, canonical_id

CAEN_NORD_SHA256 = "49f30ecb75288ab68e8d0b536f67bca5294340fa1607b8202df2cb850b5333e4"
EXPECTED_SCOPE = {
    "territory_id": "caen_nord_5communes",
    "grid_version": "M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1",
    "dataset_version": "M1-M2-CAEN-NORD-V1",
}
EXPECTED_COUNTS = {"mailles": 66, "enjeux": 66, "evenements": 3156,
                   "liens_mailles_evenements": 3400, "quarantaine": 1}
SAFE_CELL_FIELDS = (
    "maille_id", "territory_id", "grid_version", "dataset_version", "method_version",
    "etat_analyse", "nb_evenements_observes", "nb_evenements_exclusifs_observes",
    "nb_evenements", "priorite_etat", "priorite_valeur", "actions_etat",
    "routes_completeness_status", "corridors_completeness_status",
    "routes_couverture_validee", "corridors_couverture_validee", "fiabilite",
)
SAFE_ISSUE_FIELDS = ("enj_01_pct", "enj_01_status", "enj_02_presence", "enj_02_status")
SAFE_EVENT_FIELDS = ("conflit_id", "territory_id", "grid_version", "dataset_version",
                     "method_version", "statut", "evidence_level")


def _digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _connect_readonly(path: Path) -> sqlite3.Connection:
    # Ne jamais ouvrir un GeoPackage externe en écriture ; ni charger d'extension SQLite.
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only=ON")
    return connection


def _columns(db: sqlite3.Connection, table: str) -> set[str]:
    # Noms de tables internes fixes et non contrôlés par les requêtes utilisateurs.
    return {item[1] for item in db.execute(f'PRAGMA table_info("{table}")')}


def _select_columns(db: sqlite3.Connection, table: str, fields: tuple[str, ...]) -> list[dict]:
    choices = [name for name in fields if name in _columns(db, table)]
    if not choices:
        raise ContractError(f"Aucun champ exploitable dans {table}.")
    names = ", ".join('"' + name + '"' for name in choices)
    return [dict(row) for row in db.execute(f'SELECT {names} FROM "{table}"')]


@dataclass
class InternalM2Lot:
    """Vue descriptive en lecture seule d'un GeoPackage certifié par M2.

    Les champs d'identité sont scopés ; pas de rapprochement d'autres versions
    par ``maille_id`` seul, ni de publication de géométrie et sources brutes.
    """
    path: Path
    expected_sha256: str = CAEN_NORD_SHA256
    expected_scope: dict[str, str] | None = None
    expected_counts: dict[str, int] | None = None

    def __post_init__(self):
        self.path = Path(self.path).resolve()
        if not self.path.is_file():
            raise ContractError(f"GeoPackage interne absent : {self.path}")
        if not self.expected_sha256 or _digest(self.path).lower() != self.expected_sha256.lower():
            raise ContractError("Empreinte SHA-256 du GeoPackage incompatible avec le lot M2 attendu.")
        self.scope = self.expected_scope if self.expected_scope is not None else EXPECTED_SCOPE
        counts = self.expected_counts if self.expected_counts is not None else EXPECTED_COUNTS
        with _connect_readonly(self.path) as db:
            for table in (*EXPECTED_COUNTS,):
                if not _columns(db, table):
                    raise ContractError(f"Table requise absente : {table}")
            for table, n in counts.items():
                actual = db.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                if actual != n:
                    raise ContractError(f"Compte {table} incohérent : {actual}, attendu {n}.")
            cols = _columns(db, "mailles")
            if not (set(self.scope) | {"maille_id"}) <= cols:
                raise ContractError("Colonnes de portée/identité absentes des mailles.")
            cells = _select_columns(db, "mailles", SAFE_CELL_FIELDS)
            issues = _select_columns(db, "enjeux", ("maille_id", *SAFE_ISSUE_FIELDS))
            events = _select_columns(db, "evenements", SAFE_EVENT_FIELDS)
            link_fields = _columns(db, "liens_mailles_evenements")
            if not {"maille_id", "conflit_id", "canonical_owner"} <= link_fields:
                raise ContractError("Colonnes de relations requises absentes.")
            links = [dict(row) for row in db.execute(
                'SELECT maille_id, conflit_id, canonical_owner FROM "liens_mailles_evenements"'
            )]
        def ensure_scope(row, label):
            for k, value in self.scope.items():
                if row.get(k) != value:
                    raise ContractError(f"Portée incompatible dans {label} ({k}).")
        self.cells: dict[str, dict] = {}
        for cell in cells:
            ensure_scope(cell, "mailles")
            key = canonical_id(cell["maille_id"])
            if key in self.cells:
                raise ContractError("Maille dupliquée.")
            self.cells[key] = cell
        self.events: dict[str, dict] = {}
        for event in events:
            ensure_scope(event, "evenements")
            key = canonical_id(event["conflit_id"])
            if key in self.events:
                raise ContractError("Événement dupliqué.")
            self.events[key] = event
        self.issues: dict[str, dict] = {}
        for issue in issues:
            key = canonical_id(issue["maille_id"])
            if key in self.issues or key not in self.cells:
                raise ContractError("Enjeux absents, dupliqués ou hors portée.")
            # Un 1 peut être vrai; NULL doit rester inconnu, pas False.
            if issue.get("enj_02_presence") is not None:
                if issue["enj_02_presence"] != 1:
                    raise ContractError("Enjeu 02 non conforme aux valeurs déclarées pour le lot.")
                issue["enj_02_presence"] = True
            self.issues[key] = issue
        if set(self.issues) != set(self.cells):
            raise ContractError("Jointure enjeux/mailles incomplète.")
        self.links: dict[str, list[str]] = defaultdict(list)
        seen_pairs: set[tuple[str, str]] = set()
        owners: Counter[str] = Counter()
        cell_owners: Counter[str] = Counter()
        for link in links:
            mid, cid = canonical_id(link["maille_id"]), canonical_id(link["conflit_id"])
            if mid not in self.cells or cid not in self.events or (mid, cid) in seen_pairs:
                raise ContractError("Relation manquante, dupliquée ou hors de portée.")
            if link["canonical_owner"] not in (0, 1):
                raise ContractError("Propriétaire canonique non binaire.")
            seen_pairs.add((mid, cid))
            self.links[mid].append(cid)
            owners[cid] += link["canonical_owner"]
            cell_owners[mid] += link["canonical_owner"]
        if set(owners) != set(self.events) or any(n != 1 for n in owners.values()):
            raise ContractError("Chaque événement doit avoir exactement un propriétaire canonique.")
        for mid, cell in self.cells.items():
            if cell.get("nb_evenements_observes") != len(self.links[mid]):
                raise ContractError("Comptage local discordant.")
            if cell.get("nb_evenements_exclusifs_observes") != cell_owners[mid]:
                raise ContractError("Comptage exclusif discordant.")
            if cell.get("nb_evenements") is not None:
                raise ContractError("Le compte exhaustif doit rester inconnu dans ce lot.")
            if cell.get("priorite_etat") != "non_calculee" or cell.get("priorite_valeur") is not None:
                raise ContractError("Priorité inattendue dans le lot M2 non priorisé.")
            if cell.get("actions_etat") != "non_calculees":
                raise ContractError("Actions inattendues dans le lot M2.")
        self.counts = {"mailles": len(self.cells), "evenements_admis": len(self.events),
                       "relations_spatiales": len(seen_pairs),
                       "mailles_avec_observations": sum(bool(v) for v in self.links.values()),
                       "mailles_sans_evenement_observe": sum(not self.links[mid] for mid in self.cells),
                       "quarantaine": counts.get("quarantaine")}

    def cell_detail(self, maille_id: str) -> dict | None:
        # Les mailles réelles sont des IDs textuels ; pas de coercition automatique.
        key = canonical_id(maille_id)
        if key not in self.cells:
            return None
        return {
            **self.cells[key],
            "enjeux": self.issues[key],
            "conflit_ids": [self.events[c]["conflit_id"] for c in self.links[key]],
            "priorite_examen": {"etat": "non_calculee", "valeur": None},
            "etat_actions": "non_calculees",
            "nature_donnees": "reelles_interne_non_diffusables",
            "geometrie": None,
            "limitations": ["Détections géométriques, pas obstacles confirmés.",
                            "Zéro observé ne démontre pas une absence écologique.",
                            "Aucune priorité ou action calculée."]
        }

    def event_detail(self, conflit_id: str) -> dict | None:
        event = self.events.get(canonical_id(conflit_id))
        return ({**event, "geometrie": None, "nature_donnees": "reelles_interne_non_diffusables"}
                if event is not None else None)
