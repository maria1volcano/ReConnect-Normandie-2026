"""Événements route–corridor : géométrie 2D, contexte et preuves séparés."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Iterable, Literal

import geopandas as gpd
import pandas as pd
from shapely import force_2d, line_merge, normalize, union_all
from shapely.affinity import translate
from shapely.geometry.base import BaseGeometry

from analysis.indicateurs_enjeux import (
    CoverageEvidence, SubframeMapping, _check_mapping, _coverage_geometry,
    territory_geometry_sha256,
)
from analysis.validate_inputs import (
    AREA_TOLERANCE_M2, CORRIDORS, LENGTH_TOLERANCE_M, METRIC_CRS, POLYGONS,
    InputValidationError, LayerSpec, SpatialExpectation, ValidationReport,
    validate_geodataframe, validate_spatial_plausibility,
)

STATUSES = ("croisement_detecte", "conflit_potentiel", "obstacle_confirme", "non_concluant")
EVENT_COLUMNS = [
    "conflit_id", "type", "statut", "detection_status", "intersection_dimension",
    "intersection_relation", "territory_relation", "evidence_level", "source_ids", "source_pairs", "maille_ids",
    "observations", "preuves", "precision_affichage", "precision_m", "precision_reference",
    "precision_sensitive", "precision_sensitivity_scope", "numeric_residue", "limites", "method_version", "length_m", "area_m2",
]


@dataclass(frozen=True)
class SourceFields:
    """Champs réellement présents ; seules les colonnes configurées sont interprétées."""

    id_column: str
    category_column: str | None = None
    structure_column: str | None = None
    level_column: str | None = None
    context_reference: str | None = None
    subframes: SubframeMapping | None = None


@dataclass(frozen=True)
class IntersectionPrecision:
    """Scénario de translation relative documenté, sans tampon ni déplacement brut."""

    distance_m: float
    reference: str
    localization_adequate: bool | None = None


@dataclass(frozen=True)
class EventEvidence:
    """Qualification humaine d'un événement exact, pas règle de décision automatique."""

    conflit_id: str
    target_status: Literal["conflit_potentiel", "obstacle_confirme", "non_concluant"]
    reference: str
    criteria: str
    validated_by: str
    validated_at: str
    observations: str | None = None
    localization_resolution_reference: str | None = None
    localization_validated_by: str | None = None
    localization_validated_at: str | None = None


@dataclass(frozen=True)
class PotentialConflictRule:
    """Interface opt-in de correspondance exacte ; aucune règle de production fournie.

    Les chemins de ``context_equals`` visent les observations, par exemple
    ``routes.context.category``. Les codes doivent avoir une référence officielle.
    """

    rule_id: str
    version: str
    reference: str
    criteria: str
    validated_by: str
    validated_at: str
    context_equals: dict[str, Any]


def apply_potential_conflict_rules(
    events: gpd.GeoDataFrame, rules: Iterable[PotentialConflictRule] = (),
) -> gpd.GeoDataFrame:
    """Seuls les croisements localisables peuvent être proposés à l'examen.

    Une valeur manquante ne satisfait jamais un critère. Les validations sont des
    déclarations tracées, sans authentification de leurs auteurs par le logiciel.
    """
    result = events.copy()
    identities = set()
    for rule in sorted(rules, key=lambda r: (r.rule_id, r.version)):
        if any(not isinstance(getattr(rule, key), str) or not getattr(rule, key).strip()
               for key in ("rule_id", "version", "reference", "criteria", "validated_by", "validated_at")):
            raise ValueError("Règle : identité, version, référence, critères et validation requis.")
        datetime.fromisoformat(rule.validated_at.replace("Z", "+00:00"))
        if (not isinstance(rule.context_equals, dict) or not rule.context_equals
                or any(not isinstance(k, str) or not k.strip() or v is None for k, v in rule.context_equals.items())):
            raise ValueError("Règle : critères contextuels explicites non nuls requis.")
        identity = (rule.rule_id, rule.version)
        if identity in identities:
            raise ValueError("Règle dupliquée : identifiant/version doivent être uniques.")
        identities.add(identity)
        for position, event in enumerate(result.itertuples(index=False)):
            if event.statut != "croisement_detecte" or event.precision_affichage != "localisation_validee":
                continue
            observed = json.loads(event.observations)
            def matches(path, expected):
                value = observed
                for key in path.split("."):
                    if not isinstance(value, dict) or key not in value:
                        return False
                    value = value[key]
                return value is not None and canonical_json(value) == canonical_json(expected)
            if not all(matches(path, value) for path, value in rule.context_equals.items()):
                continue
            result.iloc[position, result.columns.get_loc("statut")] = "conflit_potentiel"
            result.iloc[position, result.columns.get_loc("evidence_level")] = "regle_contextuelle_documentee"
            history = json.loads(event.preuves)
            history.append({"kind": "context_rule", **asdict(rule), "conflit_id": event.conflit_id,
                            "authors_authenticated_by_software": False})
            result.iloc[position, result.columns.get_loc("preuves")] = canonical_json(history)
    return result


@dataclass
class ConflictDetection:
    events: gpd.GeoDataFrame
    report: ValidationReport
    analysis_performed: bool
    territory_sha256: str
    route_coverage: CoverageEvidence = field(default_factory=CoverageEvidence)
    corridor_coverage: CoverageEvidence = field(default_factory=CoverageEvidence)
    route_footprint: BaseGeometry | None = None
    corridor_footprint: BaseGeometry | None = None
    method_version: str | None = None


def json_value(value: Any) -> Any:
    """Normalise les scalaires d'attributs pour des JSON déterministes et sans NaN."""
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if hasattr(value, "item"):
        value = value.item()
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, (datetime, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): json_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(v) for v in value]
    raise ValueError(f"Attribut non sérialisable sans conversion implicite : {type(value).__name__}.")


def canonical_json(value: Any) -> str:
    return json.dumps(json_value(value), sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def identifier(value: Any) -> str | int:
    value = json_value(value)
    if isinstance(value, bool) or not isinstance(value, (str, int)) or (isinstance(value, str) and not value.strip()):
        raise ValueError("Un identifiant doit être un entier ou une chaîne non vide, sans imputation.")
    return value


def geometry_key(geometry: BaseGeometry) -> str:
    return normalize(force_2d(geometry)).wkb_hex


def empty_events() -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame({name: pd.Series(dtype="object") for name in EVENT_COLUMNS},
                            geometry=gpd.GeoSeries([], crs=METRIC_CRS), crs=METRIC_CRS)


def _parts(geometry: BaseGeometry) -> Iterable[BaseGeometry]:
    if geometry.is_empty:
        return
    if geometry.geom_type == "MultiLineString":
        merged = line_merge(geometry)
        if merged.geom_type == "LineString":
            yield merged
            return
        geometry = merged
    if geometry.geom_type.startswith("Multi") or geometry.geom_type == "GeometryCollection":
        for part in geometry.geoms:
            yield from _parts(part)
    else:
        yield geometry


def _intersection(left: BaseGeometry, right: BaseGeometry) -> BaseGeometry:
    # Préserve aussi les objets minuscules entièrement contenus (limite d'overlay GEOS).
    if left.covers(right):
        return right
    if right.covers(left):
        return left
    return left.intersection(right)


def _merged_event(previous: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    """Même emprise candidate et mêmes attributs : unir les liens, pas les inventer."""
    previous_ids, current_ids = json.loads(previous["source_ids"]), json.loads(current["source_ids"])
    for role in ("routes", "corridors"):
        previous_ids[role] = [v for _, v in sorted({canonical_json(v): v for v in (
            *previous_ids[role], *current_ids[role])}.items())]
    previous["source_ids"] = canonical_json(previous_ids)
    previous["source_pairs"] = canonical_json([json.loads(v) for v in sorted(set(
        canonical_json(p) for p in (*json.loads(previous["source_pairs"]), *json.loads(current["source_pairs"]))
    ))])
    observations, incoming = json.loads(previous["observations"]), json.loads(current["observations"])
    for role in ("routes", "corridors"):
        records = observations[role]["source_objects"] + incoming[role]["source_objects"]
        observations[role]["source_objects"] = [json.loads(v) for v in sorted({canonical_json(v) for v in records})]
    observations["pair_intersections"] = [json.loads(v) for v in sorted({canonical_json(v) for v in (
        *observations["pair_intersections"], *incoming["pair_intersections"])})]
    previous["observations"] = canonical_json(observations)
    previous["limites"] = canonical_json(sorted(set(json.loads(previous["limites"]) + json.loads(current["limites"]))))
    if current["statut"] == "non_concluant":
        previous["statut"] = "non_concluant"
    if current["intersection_relation"] != previous["intersection_relation"]:
        previous["intersection_relation"] = "relations_multiples_documentees"
    if current["detection_status"] == "intersection_detectee":
        previous["detection_status"] = "intersection_detectee"
    previous["precision_sensitive"] = (True if previous["precision_sensitive"] or current["precision_sensitive"] else
                                       False if previous["precision_sensitive"] is False and current["precision_sensitive"] is False else None)
    return previous


def _source_groups(
    frame: gpd.GeoDataFrame, fields: SourceFields, name: str, report: ValidationReport,
) -> gpd.GeoDataFrame:
    columns = [fields.id_column, fields.category_column, fields.structure_column, fields.level_column]
    required = tuple(dict.fromkeys(c for c in columns if c))
    validate_geodataframe(frame, LayerSpec(name, CORRIDORS, (fields.id_column,), allow_empty=True), report)
    # Les attributs contextuels manquants sont une lacune, pas une valeur inventée.
    for column in required:
        if column != fields.id_column:
            if column not in frame:
                report.add("error", "missing_context_column", name, "Colonne contextuelle configurée absente.", column=column)
            elif frame[column].isna().any():
                report.add("warning", "missing_source_context", name, "Attribut contextuel manquant conservé null.", column=column)
    if (fields.structure_column or fields.level_column) and not (
        fields.context_reference and fields.context_reference.strip()
    ):
        report.add("error", "undocumented_source_context", name,
                   "Ouvrages/niveaux configurés : référence décrivant les champs nécessaire.")
    if name == "corridors" or fields.subframes is not None:
        _check_mapping(frame, fields.subframes, name, report)
    if not report.ok:
        return gpd.GeoDataFrame(geometry=[], crs=METRIC_CRS)
    projected = frame.to_crs(METRIC_CRS)
    groups: dict[str, dict[str, Any]] = {}
    ids: dict[str, str] = {}
    for _, row in projected.iterrows():
        source_id = identifier(row[fields.id_column])
        attributes = {str(c): json_value(row[c]) for c in projected.columns
                      if c not in {projected.geometry.name, fields.id_column}}
        original = row[projected.geometry.name]
        geometry = force_2d(original)
        key = canonical_json({"geometry": normalize(original).wkb_hex, "attributes": attributes})
        id_key = canonical_json(source_id)
        if id_key in ids and ids[id_key] != key:
            report.add("error", "source_id_reused", name,
                       "Un identifiant source désigne des objets différents.", source_id=source_id)
        ids[id_key] = key
        if key not in groups:
            context = {
                "category": json_value(row[fields.category_column]) if fields.category_column else None,
                "structure": json_value(row[fields.structure_column]) if fields.structure_column else None,
                "level": json_value(row[fields.level_column]) if fields.level_column else None,
                "context_reference": fields.context_reference,
                "source_geometry_has_z": bool(original.has_z),
                "subframe": json_value(row[fields.subframes.column]) if fields.subframes else None,
                "subframe_meaning": fields.subframes.meanings.get(str(row[fields.subframes.column]))
                if fields.subframes and pd.notna(row[fields.subframes.column]) else None,
            }
            groups[key] = {"key": key, "ids": {}, "attributes": attributes, "context": context, "geometry": geometry}
        groups[key]["ids"][id_key] = source_id
    records = []
    for key in sorted(groups):
        record = groups[key]
        record["ids"] = [v for _, v in sorted(record["ids"].items())]
        records.append(record)
    if len(records) < len(frame):
        report.add("info", "duplicate_sources_collapsed", name,
                   "Sources identiques en géométrie et attributs regroupées ; identifiants conservés.",
                   input_count=len(frame), distinct_objects=len(records))
    if frame.geometry.has_z.any():
        report.add("warning", "planar_analysis", name,
                   "Coordonnées Z présentes : analyse explicitement en XY, sans inférence de niveau physique.")
    return gpd.GeoDataFrame(records, geometry="geometry", crs=METRIC_CRS) if records else gpd.GeoDataFrame(
        {"key": [], "ids": [], "attributes": [], "context": []}, geometry=[], crs=METRIC_CRS)


def detect_route_corridor_conflicts(
    routes: gpd.GeoDataFrame | None, corridors: gpd.GeoDataFrame | None,
    territory: gpd.GeoDataFrame, *, route_fields: SourceFields, corridor_fields: SourceFields,
    route_coverage: CoverageEvidence | None = None, corridor_coverage: CoverageEvidence | None = None,
    method_version: str | None = None, spatial_expectation: SpatialExpectation | None = None,
    precision: IntersectionPrecision | None = None,
) -> ConflictDetection:
    """Intersections exactes avant rattachement aux mailles, sans tampon ni score."""
    report = ValidationReport()
    if method_version is not None and (not isinstance(method_version, str) or not method_version.strip()):
        report.add("error", "invalid_method_version", "conflicts", "Version de méthode non vide ou null attendue.")
    validate_geodataframe(territory, LayerSpec("territory", POLYGONS), report)
    if not report.ok:
        raise InputValidationError(report)
    territory_hash = territory_geometry_sha256(territory)
    report.layers["territory"]["geometry_sha256"] = territory_hash
    road_evidence, corridor_evidence = route_coverage or CoverageEvidence(), corridor_coverage or CoverageEvidence()
    road_footprint = _coverage_geometry(road_evidence, "routes", report, territory_hash)
    corridor_footprint = _coverage_geometry(corridor_evidence, "corridors", report, territory_hash)
    if precision is not None and (
        not isinstance(precision.distance_m, (int, float)) or isinstance(precision.distance_m, bool)
        or not math.isfinite(precision.distance_m) or precision.distance_m <= 0
        or not isinstance(precision.reference, str) or not precision.reference.strip()
        or (precision.localization_adequate is not None and type(precision.localization_adequate) is not bool)
    ):
        report.add("error", "invalid_intersection_precision", "conflicts",
                   "La précision exige une distance positive finie, une référence et un avis de localisation booléen ou null.")
    if not report.ok:
        raise InputValidationError(report)
    report.layers["conflicts"] = {"method_version": method_version,
                                 "precision": asdict(precision) if precision else None,
                                 "identity": "sha256_canonical_geometry_attributes_mappings_method"}
    if precision is None:
        report.add("warning", "intersection_precision_unknown", "conflicts",
                   "Précision des intersections non documentée : aucune aptitude à la localisation n'est certifiée.")
    result = ConflictDetection(empty_events(), report, False, territory_hash, road_evidence,
                               corridor_evidence, road_footprint, corridor_footprint, method_version)
    if routes is None or corridors is None:
        report.add("warning", "analysis_not_performed", "conflicts",
                   "Source absente : absence d'analyse, sans événement localisé artificiel.")
        return result
    roads = _source_groups(routes, route_fields, "routes", report)
    paths = _source_groups(corridors, corridor_fields, "corridors", report)
    if not report.ok:
        raise InputValidationError(report)
    frames = {"routes": routes, "corridors": corridors, "territory": territory}
    for name, evidence in (("routes_coverage", road_evidence), ("corridors_coverage", corridor_evidence)):
        if evidence.footprint is not None:
            frames[name] = evidence.footprint
    validate_spatial_plausibility(frames, territory, report, spatial_expectation)
    if not report.ok:
        raise InputValidationError(report)
    if method_version is None:
        report.add("warning", "method_version_missing", "conflicts",
                   "Version de méthode inconnue : null conservé ; identité liée aussi au code de détection.")
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    study = union_all(territory.to_crs(METRIC_CRS).geometry.map(force_2d).to_numpy())
    events: dict[str, dict[str, Any]] = {}
    for _, road in roads.iterrows():
        for position in paths.sindex.query(road.geometry, predicate="intersects"):
            corridor = paths.iloc[position]
            candidate = _intersection(_intersection(road.geometry, corridor.geometry), study)
            if candidate.is_empty:
                continue
            touch = road.geometry.touches(corridor.geometry)
            sensitive = None
            if precision is not None:
                d = precision.distance_m
                sensitive = any(not _intersection(translate(road.geometry, xoff=dx, yoff=dy),
                                                 corridor.geometry).intersects(study)
                                for dx, dy in ((d, 0), (-d, 0), (0, d), (0, -d)))
            parts = list(_parts(candidate))
            for part in parts:
                boundary_only = study.boundary.covers(part)
                territory_relation = ("frontiere" if boundary_only else "interieur_et_frontiere"
                                      if part.intersects(study.boundary) else "interieur")
                dimension = {"Point": "ponctuelle", "LineString": "lineaire", "Polygon": "surfacique"}[part.geom_type]
                residue = ((dimension == "lineaire" and 0 < part.length <= LENGTH_TOLERANCE_M)
                           or (dimension == "surfacique" and 0 < part.area <= AREA_TOLERANCE_M2))
                payload = {
                    "contract": "reconnect.route_corridor.intersection", "method_version": method_version,
                    "unversioned_code_sha256": code_hash if method_version is None else None,
                    "source_namespaces": [road_evidence.source_id, corridor_evidence.source_id],
                    "route_attributes": road["attributes"], "corridor_attributes": corridor["attributes"],
                    "z_source_context": [road["key"] if road["context"]["source_geometry_has_z"] else None,
                                         corridor["key"] if corridor["context"]["source_geometry_has_z"] else None],
                    "geometry": geometry_key(part),
                    "mappings": [asdict(route_fields), asdict(corridor_fields)],
                }
                conflict_id = "rc_" + hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()
                limits = ["Intersection cartographique en plan ; obstruction physique et fonctionnalité écologique non établies.",
                          "Ponts, tunnels, niveaux et ouvrages à vérifier ; aucune absence d'ouvrage n'est déduite."]
                if precision is None:
                    limits.append("Précision spatiale non documentée ; aptitude à la localisation non validée.")
                elif precision.localization_adequate is not True:
                    limits.append("Aptitude à la localisation non validée ou insuffisante selon le contrat de précision.")
                if sensitive:
                    limits.append("Présence de l'intersection sensible aux translations documentées de la paire source.")
                if boundary_only:
                    limits.append("Contact uniquement sur la frontière du territoire ; aucun conflit interne établi.")
                if residue:
                    limits.append("Intersection à l'échelle de la tolérance numérique, conservée sans suppression.")
                # Une disparition globale démontre la perte d'un événement unique seulement.
                # Pour plusieurs composantes, aucune correspondance locale n'est démontrée.
                inconclusive = (touch or boundary_only or residue or (len(parts) == 1 and bool(sensitive))
                                or (precision is not None and precision.localization_adequate is False))
                relation = "contact_frontiere" if touch else "croisement_transversal" if road.geometry.crosses(corridor.geometry) else "intersection_ou_superposition"
                event_row = {
                    "conflit_id": conflict_id, "type": "route_corridor", "statut": "non_concluant" if inconclusive else "croisement_detecte",
                    "detection_status": "contact_detecte" if touch or boundary_only else "intersection_detectee",
                    "intersection_dimension": dimension, "intersection_relation": relation,
                    "territory_relation": territory_relation,
                    "evidence_level": "geometrie_2d", "source_ids": canonical_json({"routes": road["ids"], "corridors": corridor["ids"]}),
                    "source_pairs": canonical_json([[r, c] for r in road["ids"] for c in corridor["ids"]]),
                    "maille_ids": "[]", "observations": canonical_json({
                        "routes": {"attributes": road["attributes"], "context": road["context"], "source_objects": [{
                            "source_ids": road["ids"], "source_object_sha256": hashlib.sha256(road["key"].encode()).hexdigest()}]},
                        "corridors": {"attributes": corridor["attributes"], "context": corridor["context"], "source_objects": [{
                            "source_ids": corridor["ids"], "source_object_sha256": hashlib.sha256(corridor["key"].encode()).hexdigest()}]},
                        "pair_intersections": [{"source_pairs": [[r, c] for r in road["ids"] for c in corridor["ids"]],
                                                "relation": relation, "precision_sensitive": sensitive}],
                    }), "preuves": "[]", "precision_affichage": "precision_non_documentee" if precision is None
                    else "localisation_validee" if precision.localization_adequate is True else "localisation_a_confirmer",
                    "precision_m": precision.distance_m if precision else None,
                    "precision_reference": precision.reference if precision else None,
                    "precision_sensitive": sensitive, "precision_sensitivity_scope": "source_pair" if precision else None,
                    "numeric_residue": residue, "limites": canonical_json(limits),
                    "method_version": method_version, "length_m": float(part.length) if dimension == "lineaire" else None,
                    "area_m2": float(part.area) if dimension == "surfacique" else None,
                    "geometry": normalize(force_2d(part)),
                }
                events[conflict_id] = _merged_event(events[conflict_id], event_row) if conflict_id in events else event_row
    result.analysis_performed = True
    if events:
        result.events = gpd.GeoDataFrame([events[k] for k in sorted(events)], geometry="geometry", crs=METRIC_CRS)
        result.events["precision_sensitive"] = pd.array(result.events.precision_sensitive, dtype="boolean")
    report.add("info", "candidate_events_detected", "conflicts", "Intersections des sources originales, avant agrégation.",
               count=len(result.events), analysis_performed=True,
               inconclusive=int(result.events.statut.eq("non_concluant").sum()))
    return result


def qualify_events(events: gpd.GeoDataFrame, evidence: Iterable[EventEvidence]) -> gpd.GeoDataFrame:
    """Applique uniquement des qualifications externes explicites liées à conflit_id."""
    result = events.copy()
    report = ValidationReport()
    positions = {value: i for i, value in enumerate(result.conflit_id)}
    seen: dict[str, str] = {}
    for item in evidence:
        serialized = canonical_json(item.__dict__)
        if item.conflit_id in seen:
            if seen[item.conflit_id] != serialized:
                report.add("error", "conflicting_event_evidence", "evidence", "Qualifications divergentes pour le même événement.")
            continue
        seen[item.conflit_id] = serialized
        if item.conflit_id not in positions:
            report.add("error", "stale_event_evidence", "evidence", "Preuve sans événement correspondant dans cette exécution.", conflit_id=item.conflit_id)
            continue
        if item.target_status not in STATUSES[1:] or any(not isinstance(getattr(item, key), str) or not getattr(item, key).strip()
            for key in ("reference", "criteria", "validated_by", "validated_at")):
            report.add("error", "undocumented_event_qualification", "evidence", "Qualification sans critères, preuve identifiable et validation explicites.")
            continue
        try:
            datetime.fromisoformat(item.validated_at.replace("Z", "+00:00"))
        except ValueError:
            report.add("error", "invalid_event_evidence_date", "evidence", "Date de validation ISO 8601 attendue.")
            continue
        position = positions[item.conflit_id]
        event = result.iloc[position]
        promotion = item.target_status in {"conflit_potentiel", "obstacle_confirme"}
        if promotion and event.get("territory_relation") == "frontiere":
            report.add("error", "territory_boundary_qualification", "evidence",
                       "Un contact uniquement sur la frontière ne qualifie pas un conflit interne.")
            continue
        needs_resolution = promotion and (event.statut == "non_concluant" or (
            item.target_status == "obstacle_confirme" and event.precision_affichage != "localisation_validee"))
        if needs_resolution:
            required = ("localization_resolution_reference", "localization_validated_by", "localization_validated_at")
            if any(not isinstance(getattr(item, key), str) or not getattr(item, key).strip() for key in required):
                report.add("error", "unresolved_event_localization", "evidence",
                           "La promotion exige une résolution de localisation documentée pour cet événement.")
                continue
            try:
                datetime.fromisoformat(item.localization_validated_at.replace("Z", "+00:00"))
            except ValueError:
                report.add("error", "invalid_localization_date", "evidence", "Date de résolution ISO 8601 attendue.")
                continue
        result.iloc[position, result.columns.get_loc("statut")] = item.target_status
        result.iloc[position, result.columns.get_loc("evidence_level")] = (
            "preuve_externe_documentee" if item.target_status == "obstacle_confirme" else "criteres_examen_documentes")
        history = json.loads(event.preuves)
        record = {**item.__dict__, "previous_status": event.statut,
                  "authors_authenticated_by_software": False}
        if not any(all(previous.get(key) == value for key, value in item.__dict__.items()) for previous in history):
            history.append(record)
        result.iloc[position, result.columns.get_loc("preuves")] = canonical_json(history)
    if not report.ok:
        raise InputValidationError(report)
    return result
