"""Préparation locale du contrat proposé M2→M4 ; diffusion de production désactivée."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

import geopandas as gpd
from jsonschema import Draft202012Validator
from shapely import force_2d
from shapely.geometry import mapping, shape
from shapely.geometry.base import BaseGeometry
from shapely.ops import orient

from analysis.aggregate_conflicts import ConflictAggregation
from analysis.detect_conflicts import canonical_json, identifier, json_value

CONTRACT_VERSION = "m2-m4.proposal-1"
SCHEMA_DIR = Path(__file__).resolve().parents[1] / "docs"
VERSIONS = ("grid_version", "method_version", "dataset_version")


@dataclass(frozen=True)
class ConflictDisclosure:
    """Décision déclarée par événement ; rien n'est autorisé implicitement.

    Une géométrie généralisée doit être fournie avec son CRS et sa justification.
    Le logiciel ne choisit aucun rayon de généralisation et n'authentifie pas la décision.
    """

    mode: str = "masquee"
    reference: str | None = None
    geometry: BaseGeometry | None = None
    crs: str | None = None
    source_ids_allowed: bool = False


def _array(value: Any) -> list:
    decoded = json.loads(value) if isinstance(value, str) else json_value(value)
    if not isinstance(decoded, list):
        raise ValueError("Tableau JSON attendu, sans chaîne JSON dans le contrat public.")
    return decoded


def _sorted_ids(values: list) -> list:
    values = [identifier(v) for v in values]
    if len({canonical_json(v) for v in values}) != len(values):
        raise ValueError("Identifiant dupliqué dans une relation.")
    return sorted(values, key=canonical_json)


def _geometry(geometry: BaseGeometry | None) -> dict | None:
    if geometry is None:
        return None
    return json_value(mapping(orient(force_2d(geometry), sign=1.0)))


def _public_event_geometry(event, policy: ConflictDisclosure, source_crs):
    if policy.mode not in {"masquee", "exacte", "generalisee"} or type(policy.source_ids_allowed) is not bool:
        raise ValueError("Décision de diffusion inconnue.")
    if (policy.mode != "masquee" or policy.source_ids_allowed) and not (
        isinstance(policy.reference, str) and policy.reference.strip()
    ):
        raise ValueError("Une autorisation déclarée et référencée de diffusion est nécessaire.")
    if policy.mode != "generalisee" and (policy.geometry is not None or policy.crs is not None):
        raise ValueError("Une géométrie de remplacement exige le mode generalisee.")
    if policy.mode == "masquee":
        return None, "localisation_masquee"
    geometry, crs = event.geometry, source_crs
    if policy.mode == "generalisee":
        if policy.geometry is None or not policy.crs:
            raise ValueError("Généralisation : géométrie et CRS explicites requis.")
        geometry, crs = policy.geometry, policy.crs
    projected = gpd.GeoSeries([geometry], crs=crs).to_crs("OGC:CRS84").iloc[0]
    return _geometry(projected), "localisation_generalisee" if policy.mode == "generalisee" else event.precision_affichage


def prepare_m2_contract(
    result: ConflictAggregation, *, versions: dict[str, str | None],
    test_data: bool, run_id: str | None = None,
    disclosure: dict[str, ConflictDisclosure] | None = None,
) -> tuple[dict, dict]:
    """Retourne deux objets validés, sans écriture ni publication.

    ``test_data=True`` est une déclaration de l'appelant, pas une détection de
    données synthétiques. Aucun chemin de production n'est activé à ce jalon.
    Les propriétés sont construites champ par champ (liste d'autorisation).
    """
    if test_data is not True:
        raise ValueError("Export de production désactivé : données et droits à valider M1/M2/M4.")
    if not result.report.ok:
        raise ValueError("Résultat M2 bloqué : transformation refusée.")
    if set(versions) != set(VERSIONS):
        raise ValueError("Les trois versions, éventuellement nulles, sont obligatoires.")
    if result.events.crs is None or result.cells.crs is None:
        raise ValueError("CRS explicite requis avant conversion en CRS84.")
    policies = disclosure or {}
    if set(policies) - set(result.events.conflit_id):
        raise ValueError("Décision de diffusion sans événement correspondant.")
    provenance = {"run_id": run_id, **versions}
    def collection(features):
        return {"type": "FeatureCollection", "contract_version": CONTRACT_VERSION,
                "test_data": True, "statut_diffusion": "synthetique_uniquement",
                "provenance": provenance.copy(), "resume": {
                    "analyse_effectuee": bool(result.summary["analysis_performed"]),
                    "evenements_distincts_observes": result.summary["distinct_events_observed"],
                    "relations_spatiales": len(result.links)}, "features": features}
    events = []
    for event in result.events.sort_values("conflit_id").itertuples(index=False):
        if json_value(event.method_version) != versions["method_version"]:
            raise ValueError("Version de méthode discordante entre détection et contrat.")
        policy = policies.get(event.conflit_id, ConflictDisclosure())
        geometry, precision = _public_event_geometry(event, policy, result.events.crs)
        sources = []
        if policy.source_ids_allowed:
            internal = json.loads(event.source_ids) if isinstance(event.source_ids, str) else event.source_ids
            if not isinstance(internal, dict) or set(internal) != {"routes", "corridors"}:
                raise ValueError("source_ids interne : objet routes/corridors attendu.")
            sources = [{"role": role, "id": value} for role in sorted(internal)
                       for value in _sorted_ids(_array(internal[role]))]
        # Ne pas recopier les textes libres des preuves, observations ou limites internes.
        limits = ["Intersection 2D ; fonctionnalité écologique non établie.",
                  "Qualifications humaines déclarées ; auteurs non authentifiés par le logiciel.",
                  "Détails et preuves internes non diffusés."]
        if json_value(event.precision_sensitive) is True:
            limits.append("Sensibilité de paire ; stabilité locale non démontrée pour chaque composante.")
        if policy.mode == "masquee":
            limits.append("Localisation publique masquée.")
        if not policy.source_ids_allowed:
            limits.append("Identifiants sources non diffusés.")
        events.append({"type": "Feature", "geometry": geometry, "properties": {
            "conflit_id": event.conflit_id, "type": event.type, "evidence_level": event.evidence_level,
            "statut": event.statut, "source_ids": sorted(sources, key=canonical_json),
            "maille_ids": _sorted_ids(_array(event.maille_ids)), "precision_affichage": precision,
            "limites": sorted(limits), "method_version": versions["method_version"],
            "territory_relation": event.territory_relation, "diffusion": {
                "geometrie": policy.mode, "source_ids_autorises": policy.source_ids_allowed,
                # Références de décision conservées en interne, jamais copiées ici.
                "decision": "masquage_par_defaut" if policy.reference is None else "decision_declaree"}}})
    cells = []
    projected_cells = result.cells.to_crs("OGC:CRS84")
    for cell in sorted(projected_cells.itertuples(index=False), key=lambda c: canonical_json(c.maille_id)):
        cells.append({"type": "Feature", "geometry": _geometry(cell.geometry), "properties": {
            "maille_id": identifier(cell.maille_id), **versions, "statut_analyse": cell.etat_analyse,
            "priorite_examen": {"etat": "non_calculee", "valeur": None},
            "diagnostics": [cell.diagnostic], "indicateurs": {
                "nb_evenements_observes": json_value(cell.nb_evenements_observes),
                "nb_evenements": json_value(cell.nb_evenements),
                "nb_evenements_exclusifs_observes": json_value(cell.nb_evenements_exclusifs_observes)},
            "qualite": {"routes_completude": cell.routes_completeness_status,
                        "corridors_completude": cell.corridors_completeness_status,
                        "routes_couverture_validee": bool(cell.routes_coverage_confirmed),
                        "corridors_couverture_validee": bool(cell.corridors_coverage_confirmed),
                        "fiabilite": cell.fiabilite},
            "conflit_ids": _sorted_ids(_array(cell.conflit_ids)), "action_ids": [],
            "etat_actions": "non_calculees"}})
    mailles, conflits = collection(cells), collection(events)
    validate_m2_contract(mailles, conflits)
    return mailles, conflits


def _check_geometry(geometry: dict | None) -> None:
    if geometry is None:
        return
    geom = shape(geometry)
    if geom.is_empty or not geom.is_valid:
        raise ValueError("Géométrie GeoJSON vide ou invalide.")
    if geometry["type"] in {"Polygon", "MultiPolygon"}:
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        for polygon in polygons:
            for ring in polygon:
                if ring[0] != ring[-1]:
                    raise ValueError("Anneau GeoJSON non fermé.")
    # Profil régional : refuser des segments traversant l'antiméridien sans découpage.
    def check_segments(coordinates):
        if not coordinates or not isinstance(coordinates[0], list):
            return
        if coordinates[0] and isinstance(coordinates[0][0], (int, float)):
            if any(abs(left[0] - right[0]) > 180 for left, right in zip(coordinates, coordinates[1:])):
                raise ValueError("Segment traversant l'antiméridien : découpage explicite requis.")
        else:
            for part in coordinates:
                check_segments(part)
    if geometry["type"] != "MultiPoint":
        check_segments(geometry["coordinates"])


def validate_m2_contract(mailles: dict, conflits: dict) -> dict[str, int | None]:
    """Schémas locaux, validité SIG et références réciproques ; aucun accès réseau."""
    # Refuse aussi les NaN/Infinity acceptés par certains parseurs JSON.
    json.dumps([mailles, conflits], allow_nan=False)
    for payload, name in ((mailles, "mailles"), (conflits, "conflits")):
        schema = json.loads((SCHEMA_DIR / f"schema_{name}.json").read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(schema).validate(payload)
        for feature in payload["features"]:
            _check_geometry(feature["geometry"])
    for key in ("contract_version", "test_data", "statut_diffusion", "provenance", "resume"):
        if mailles[key] != conflits[key]:
            raise ValueError(f"Métadonnées de collections discordantes : {key}.")
    def index(payload, key):
        records = {}
        for feature in payload["features"]:
            properties = feature["properties"]
            identity = canonical_json(identifier(properties[key]))
            if identity in records:
                raise ValueError("Identifiant de Feature dupliqué.")
            records[identity] = properties
        return records
    cells, events = index(mailles, "maille_id"), index(conflits, "conflit_id")
    cell_links, event_links = set(), set()
    exclusive_total = 0
    for cell_id, cell in cells.items():
        for version in VERSIONS:
            if cell[version] != mailles["provenance"][version]:
                raise ValueError("Version de maille discordante.")
        for value in cell["conflit_ids"]:
            event_id = canonical_json(value)
            if event_id not in events:
                raise ValueError("Conflit référencé absent.")
            cell_links.add((cell_id, event_id))
        count = cell["indicateurs"]["nb_evenements_observes"]
        analyzed = cell["statut_analyse"] == "analyse_effectuee"
        if (analyzed and count != len(cell["conflit_ids"])) or (not analyzed and (count is not None or cell["conflit_ids"])):
            raise ValueError("Comptage local incompatible avec l'état d'analyse.")
        complete = cell["qualite"]["routes_couverture_validee"] and cell["qualite"]["corridors_couverture_validee"]
        if cell["indicateurs"]["nb_evenements"] != (count if complete and analyzed else None):
            raise ValueError("Comptage complet sans couverture validée ou effectif discordant.")
        exclusive = cell["indicateurs"]["nb_evenements_exclusifs_observes"]
        if (analyzed and (exclusive is None or exclusive > count)) or (not analyzed and exclusive is not None):
            raise ValueError("Comptage exclusif local discordant.")
        exclusive_total += exclusive or 0
    for event_id, event in events.items():
        if event["method_version"] != conflits["provenance"]["method_version"]:
            raise ValueError("Version d'événement discordante.")
        for value in event["maille_ids"]:
            cell_id = canonical_json(value)
            if cell_id not in cells:
                raise ValueError("Maille référencée absente.")
            event_links.add((cell_id, event_id))
    if cell_links != event_links:
        raise ValueError("Relations réciproques discordantes.")
    observed = len(events) if mailles["resume"]["analyse_effectuee"] else None
    if (not mailles["resume"]["analyse_effectuee"] and (events or any(c["statut_analyse"] == "analyse_effectuee" for c in cells.values()))) or exclusive_total != len(events):
        raise ValueError("État global d'analyse ou somme des propriétaires exclusifs discordante.")
    if mailles["resume"]["evenements_distincts_observes"] != observed or mailles["resume"]["relations_spatiales"] != len(cell_links):
        raise ValueError("Résumé global discordant ; ne pas sommer les comptages locaux.")
    return {"mailles": len(cells), "evenements_distincts_observes": observed, "relations_spatiales": len(cell_links)}
