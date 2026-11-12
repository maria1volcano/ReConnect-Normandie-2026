"""Relation événements–mailles et quantités brutes, sans score de fragmentation."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import json
import math
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely import get_coordinates, union_all
from shapely.errors import GEOSException
from shapely.geometry.base import BaseGeometry

from analysis.detect_conflicts import (
    STATUSES, ConflictDetection, canonical_json, empty_events, identifier,
)
from analysis.indicateurs_enjeux import _fully_covered, _polygonal_part, territory_geometry_sha256
from analysis.validate_inputs import (
    METRIC_CRS, POLYGONS, InputValidationError, LayerSpec, ValidationReport,
    validate_geodataframe, validate_spatial_coverage,
)


@dataclass
class ConflictAggregation:
    events: gpd.GeoDataFrame
    cells: gpd.GeoDataFrame
    links: pd.DataFrame
    report: ValidationReport
    summary: dict[str, Any]


def _interior_relation(event, cell) -> bool:
    if event.geom_type == "Point":
        return cell.contains(event)
    overlap = event if cell.covers(event) else event.intersection(cell)
    if event.geom_type in ("LineString", "MultiLineString"):
        return (overlap.difference(cell.boundary).length if overlap.intersects(cell.boundary) else overlap.length) > 0
    return overlap.area > 0


def _territory_membership(geometry, study):
    """Appartenance XY sans mutation, avec exception numérique tracée.

    Une géométrie valide entièrement couverte garde le comportement historique,
    même sur la frontière. Sinon seule une LineString dont l'intérieur rencontre
    l'intérieur du territoire en dimension 1 peut bénéficier de l'exception.
    Une différence vide est distinguée des résidus linéaires non vides. Une ou
    plusieurs composantes extérieures sont admises uniquement si leur longueur
    cumulée ET la distance de Hausdorff à l'intersection respectent la même
    diagonale d'ULP. Aucun déplacement ni découpage n'est appliqué à l'événement.
    Ce budget est une convention d'ingénierie, pas une borne certifiée de GEOS.
    """
    def usable(value):
        return (isinstance(value, BaseGeometry) and not value.is_empty and value.is_valid
                and all(math.isfinite(float(v)) for v in
                        get_coordinates(value, include_z=value.has_z).flat))

    try:
        if not usable(geometry) or not usable(study) or study.geom_type not in POLYGONS:
            return False, None
        if study.covers(geometry):
            return True, None
        if geometry.geom_type != "LineString" or not geometry.relate_pattern(study, "1********"):
            return False, None
        outside = geometry.difference(study)
        if outside.is_empty:
            return True, {"mode": "difference_vide_malgre_predicat", "outside_length_m": 0.0}
        if outside.geom_type not in {"LineString", "MultiLineString"} or not usable(outside):
            return False, None
        clipped = geometry.intersection(study)
        if not usable(clipped):
            return False, None
        coordinates = get_coordinates(geometry)
        delta = math.hypot(max(math.ulp(float(v)) for v in coordinates[:, 0]),
                           max(math.ulp(float(v)) for v in coordinates[:, 1]))
        length, distance = float(outside.length), float(geometry.hausdorff_distance(clipped))
        if (not all(math.isfinite(v) for v in (delta, length, distance)) or delta <= 0
                or not (0 < length <= delta) or not (0 <= distance <= delta)):
            return False, None
        return True, {"mode": "residus_lineaires_resolution_machine", "outside_length_m": length,
                      "hausdorff_to_intersection_m": distance, "coordinate_ulp_diagonal_m": delta,
                      "outside_component_count": len(outside.geoms) if outside.geom_type == "MultiLineString" else 1}
    except (GEOSException, ValueError, ArithmeticError):
        return False, None


def aggregate_conflicts(
    grid: gpd.GeoDataFrame, territory: gpd.GeoDataFrame,
    detection: ConflictDetection | None,
) -> ConflictAggregation:
    """Toutes les relations spatiales sont conservées ; un propriétaire canonique par événement.

    ``nb_evenements`` exige deux sources complètes validées sur la maille.
    ``nb_evenements_observes`` est un inventaire observé, jamais un nombre d'obstacles.
    """
    report = deepcopy(detection.report) if detection is not None else ValidationReport()
    validate_geodataframe(grid, LayerSpec("grid", POLYGONS, ("maille_id",), ("maille_id",)), report)
    validate_geodataframe(territory, LayerSpec("territory", POLYGONS), report)
    if not report.ok:
        raise InputValidationError(report)
    validate_spatial_coverage(grid, territory, report)
    if detection is not None and detection.territory_sha256 != territory_geometry_sha256(territory):
        report.add("error", "detection_territory_mismatch", "conflicts",
                   "La détection et l'agrégation ne portent pas sur le même territoire.")
    events = detection.events.copy() if detection is not None else empty_events()
    validate_geodataframe(events, LayerSpec("events", ("Point", "LineString", "Polygon"),
                                          ("conflit_id", "statut"), ("conflit_id",), allow_empty=True), report)
    if "statut" in events and not events.statut.isin(STATUSES).all():
        report.add("error", "invalid_event_status", "conflicts", "Statut d'événement non reconnu.")
    if not report.ok:
        raise InputValidationError(report)
    # La validation contrôle la reprojection possible ; elle ne transforme pas les entrées.
    events = events.to_crs(METRIC_CRS).reset_index(drop=True).copy()
    grid = grid.to_crs(METRIC_CRS).reset_index(drop=True).copy()
    id_types = {type(identifier(value)) for value in grid.maille_id}
    if len(id_types) > 1:
        report.add("error", "mixed_grid_id_types", "grid", "Un seul type d'identifiant par colonne pour préserver les liens à l'export.")
        raise InputValidationError(report)
    study = union_all(territory.to_crs(METRIC_CRS).geometry.to_numpy())
    outside_ids, numerical_memberships = [], []
    for event in events.itertuples(index=False):
        inside, numerical = _territory_membership(event.geometry, study)
        if not inside:
            outside_ids.append(event.conflit_id)
        elif numerical is not None:
            numerical_memberships.append({"conflit_id": event.conflit_id, **numerical})
    if outside_ids:
        report.add("error", "event_outside_territory", "events",
                   "Événement hors emprise : le rattachement ne doit ni déplacer ni découper une détection.",
                   conflit_ids=outside_ids)
        raise InputValidationError(report)
    if numerical_memberships:
        report.add("warning", "event_territory_numerical_residue", "events",
                   "Appartenance contrôlée par différence/ULP ; géométries originales conservées.",
                   count=len(numerical_memberships), events=numerical_memberships)
    effective = grid.geometry.intersection(study).apply(_polygonal_part)
    indexed = gpd.GeoDataFrame({"position": range(len(grid))}, geometry=effective, crs=METRIC_CRS)
    link_rows = []
    for event_position, event in events.iterrows():
        candidates = []
        for position in indexed.sindex.query(event.geometry, predicate="intersects"):
            if effective.iloc[position].area <= 0:
                continue
            candidates.append((position, _interior_relation(event.geometry, effective.iloc[position])))
        if not candidates:
            report.add("error", "unassigned_candidate_event", "conflicts",
                       "Événement sans maille : aucune affectation par proximité ou centroïde n'est autorisée.",
                       conflit_id=event.conflit_id)
            continue
        eligible = [p for p, interior in candidates if interior] or [p for p, _ in candidates]
        owner = min(eligible, key=lambda p: canonical_json(identifier(grid.iloc[p].maille_id)))
        maille_ids = sorted((identifier(grid.iloc[p].maille_id) for p, _ in candidates), key=canonical_json)
        events.at[event_position, "maille_ids"] = canonical_json(maille_ids)
        for position, interior in candidates:
            link_rows.append({"conflit_id": event.conflit_id, "maille_id": identifier(grid.iloc[position].maille_id),
                              "relation_spatiale": "interieur" if interior else "frontiere",
                              "canonical_owner": position == owner})
    if not report.ok:
        raise InputValidationError(report)
    links = pd.DataFrame(link_rows, columns=["conflit_id", "maille_id", "relation_spatiale", "canonical_owner"])
    performed = detection is not None and detection.analysis_performed
    if not performed:
        report.add("warning", "analysis_not_performed", "diagnostic", "Aucun comptage d'absence sans analyse effectuée.")
    status_by_id = dict(zip(events.conflit_id, events.statut))
    cell_rows = []
    for position, cell in enumerate(effective):
        maille_id = identifier(grid.iloc[position].maille_id)
        inside = cell.area > 0
        analyzed = performed and inside
        selected = links.loc[links.maille_id.map(canonical_json) == canonical_json(maille_id)] if not links.empty else links
        conflicts = sorted(set(selected.conflit_id))
        road_complete = bool(analyzed and _fully_covered(cell, detection.route_coverage, detection.route_footprint))
        corridor_complete = bool(analyzed and _fully_covered(cell, detection.corridor_coverage, detection.corridor_footprint))
        complete = road_complete and corridor_complete
        observed = len(conflicts) if analyzed else None
        exclusive = int(selected.canonical_owner.sum()) if analyzed else None
        diagnostic = "hors_territoire" if not inside else "absence_analyse" if not analyzed else (
            "croisements_observes" if conflicts else "absence_croisement_confirmee" if complete
            else "absence_observation_couverture_non_validee")
        cell_rows.append({
            "maille_id": maille_id, "study_area_m2": float(cell.area), "conflit_ids": canonical_json(conflicts),
            "nb_evenements_observes": observed, "nb_evenements": observed if complete else None,
            "nb_evenements_exclusifs_observes": exclusive,
            "routes_coverage_confirmed": road_complete, "corridors_coverage_confirmed": corridor_complete,
            "routes_completeness_status": detection.route_coverage.effective_status if detection else "unknown",
            "corridors_completeness_status": detection.corridor_coverage.effective_status if detection else "unknown",
            "etat_analyse": "hors_territoire" if not inside else "analyse_effectuee" if analyzed else "absence_analyse",
            "diagnostic": diagnostic, "fiabilite": "hors_territoire" if not inside else "absence_analyse" if not analyzed
            else "completude_validee" if complete else "observations_completude_non_etablie",
            "method_version": detection.method_version if detection else None,
            **{f"nb_{status}_observes": sum(status_by_id[c] == status for c in conflicts) if analyzed else None
               for status in STATUSES},
        })
    cells = gpd.GeoDataFrame(cell_rows, geometry=effective, crs=METRIC_CRS)
    cells.loc[cells.study_area_m2 <= 0, "geometry"] = None
    for column in cells.columns:
        if column.startswith("nb_"):
            cells[column] = pd.array(cells[column], dtype="Int64")
    whole_coverage = bool(performed and _fully_covered(study, detection.route_coverage, detection.route_footprint)
                          and _fully_covered(study, detection.corridor_coverage, detection.corridor_footprint))
    summary = {
        "analysis_performed": performed,
        "distinct_events_observed": len(events) if performed else None,
        "distinct_events": len(events) if whole_coverage else None,
        "canonical_owner_count": int(links.canonical_owner.sum()) if performed else None,
        "both_sources_complete_on_territory": whole_coverage,
        "spatial_link_count": len(links), "unit": "evenement_geometrique_route_corridor",
    }
    if performed and summary["canonical_owner_count"] != len(events):
        report.add("error", "nonexclusive_event_ownership", "diagnostic", "Chaque événement doit avoir exactement un propriétaire canonique.")
        raise InputValidationError(report)
    report.add("info", "conflicts_aggregated", "diagnostic",
               "Comptages d'événements distincts ; somme des relations locales non utilisée comme total global.", **summary)
    return ConflictAggregation(events, cells, links, report, summary)
