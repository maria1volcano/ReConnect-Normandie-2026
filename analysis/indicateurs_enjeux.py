"""ENJ-01/ENJ-02 : mesures des objets cartographiés, sans interprétation biologique."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import math
from typing import Literal

import geopandas as gpd
import pandas as pd
from shapely import normalize, union_all
from shapely.geometry.base import BaseGeometry

from analysis.validate_inputs import (
    AREA_TOLERANCE_M2, LENGTH_TOLERANCE_M, CORRIDORS, METRIC_CRS, POLYGONS,
    InputValidationError, LayerSpec, SpatialExpectation, ValidationReport,
    validate_geodataframe, validate_spatial_coverage, validate_spatial_plausibility,
)


@dataclass(frozen=True)
class CoverageEvidence:
    """Complétude inconnue, déclarée ou validée et applicable à une emprise.

    Une emprise d'objets observés n'est pas une emprise de complétude.
    ``confirmed`` historique désigne seulement une portée globale déclarée.
    Ni ce booléen ni ``provenance`` ne valent validation M1/M2.
    """

    confirmed: bool = False
    footprint: gpd.GeoDataFrame | None = None
    provenance: str | None = None
    status: Literal["unknown", "declared", "validated"] = "unknown"
    source_id: str | None = None
    producer: str | None = None
    vintage: str | None = None
    validity_extent: str | None = None
    theme: str | None = None
    document_reference: str | None = None
    validated_by: str | None = None
    validated_at: str | None = None
    territory_sha256: str | None = None

    @property
    def effective_status(self) -> str:
        if self.status == "unknown" and (self.confirmed or self.footprint is not None or self.provenance):
            return "declared"
        return self.status


@dataclass(frozen=True)
class CorridorSensitivity:
    """Scénario de précision documentaire, en mètres ; aucune valeur par défaut."""

    distance_m: float
    reference: str


def territory_geometry_sha256(territory: gpd.GeoDataFrame) -> str:
    """Empreinte de l'union normalisée en L93 pour lier une validation globale à T."""
    geometry = normalize(union_all(territory.to_crs(METRIC_CRS).geometry.to_numpy()))
    return hashlib.sha256(geometry.wkb).hexdigest()


@dataclass(frozen=True)
class SubframeMapping:
    """Colonne de sous-trame réellement présente et sens validé de ses valeurs."""

    column: str
    meanings: dict[str, str] = field(default_factory=dict)


@dataclass
class EnjeuxResult:
    cells: gpd.GeoDataFrame
    subframes: pd.DataFrame
    report: ValidationReport


def _coverage_geometry(
    evidence: CoverageEvidence, name: str, report: ValidationReport,
    territory_hash: str | None,
) -> BaseGeometry | None:
    if evidence.confirmed and evidence.footprint is not None:
        report.add("error", "ambiguous_coverage", name,
                   "Choisir une confirmation globale ou une emprise de complétude, pas les deux.")
    if evidence.status not in {"unknown", "declared", "validated"}:
        report.add("error", "invalid_coverage_status", name, "Statut de complétude inconnu.")
    status = evidence.effective_status
    if status == "validated":
        required = ("source_id", "producer", "vintage", "validity_extent", "theme",
                    "document_reference", "validated_by", "validated_at")
        missing = [key for key in required if not (
            isinstance(getattr(evidence, key), str) and getattr(evidence, key).strip()
        )]
        if missing:
            report.add("error", "incomplete_validated_coverage", name,
                       "Métadonnées de validation de complétude incomplètes.", missing=missing)
        if evidence.theme != name:
            report.add("error", "coverage_theme_mismatch", name,
                       "La validation de complétude ne concerne pas le thème calculé.")
        if isinstance(evidence.validated_at, str) and evidence.validated_at:
            try:
                datetime.fromisoformat(evidence.validated_at.replace("Z", "+00:00"))
            except ValueError:
                report.add("error", "invalid_validation_date", name,
                           "La date de validation doit respecter le format ISO 8601.")
        if evidence.footprint is None:
            if not evidence.confirmed:
                report.add("error", "missing_coverage_scope", name,
                           "Une validation exige une portée globale explicite ou une emprise géométrique.")
            if not territory_hash or evidence.territory_sha256 != territory_hash:
                report.add("error", "coverage_territory_mismatch", name,
                           "La validation globale doit viser l'empreinte géométrique exacte du territoire étudié.")
    elif status == "declared":
        report.add("warning", "declared_coverage_unvalidated", name,
                   "Complétude déclarée mais non validée M1/M2 : aucun zéro confirmé n'est autorisé.")
    report.layers.setdefault(name, {})["coverage"] = {
        "mode": "global" if evidence.confirmed else "footprint" if evidence.footprint is not None else "unknown",
        "provenance": evidence.provenance,
        "status": status,
        **{key: getattr(evidence, key) for key in (
            "source_id", "producer", "vintage", "validity_extent", "theme",
            "document_reference", "validated_by", "validated_at", "territory_sha256",
        )},
    }
    if evidence.footprint is not None:
        start = len(report.issues)
        validate_geodataframe(evidence.footprint, LayerSpec(f"{name}_coverage", POLYGONS), report)
        if not any(i.severity == "error" for i in report.issues[start:]):
            return union_all(evidence.footprint.to_crs(METRIC_CRS).geometry.to_numpy())
    elif status == "unknown":
        report.add("warning", "unknown_coverage", name,
                   "Complétude non confirmée : une absence d'observation ne vaut pas zéro.")
    return None


def _check_mapping(
    frame: gpd.GeoDataFrame, mapping: SubframeMapping | None,
    name: str, report: ValidationReport,
) -> None:
    if mapping is None:
        report.add("warning", "subframe_mapping_missing", name,
                   "Sous-trames non interprétées : colonne et signification à valider auprès de M1.")
        return
    if mapping.column not in frame.columns:
        report.add("error", "missing_subframe_column", name,
                   "Colonne de sous-trame configurée absente.", column=mapping.column)
        return
    actual = set(frame[mapping.column].dropna().astype(str))
    undocumented = actual - mapping.meanings.keys()
    if undocumented or not mapping.meanings or any(not v.strip() for v in mapping.meanings.values()):
        report.add("error", "undocumented_subframe", name,
                   "Chaque code de sous-trame doit avoir une signification documentée.",
                   undocumented=sorted(undocumented))
    if frame[mapping.column].isna().any():
        report.add("warning", "null_subframe", name,
                   "Sous-trames manquantes conservées comme inconnues, sans les imputer.")


def _fully_covered(
    geometry: BaseGeometry, evidence: CoverageEvidence,
    footprint: BaseGeometry | None,
) -> bool:
    if geometry.area <= 0 or evidence.effective_status != "validated":
        return False
    return evidence.confirmed or (
        footprint is not None and geometry.difference(footprint).area <= AREA_TOLERANCE_M2
    )


def _checked_proportion(
    observed_area: float, study_area: float, report: ValidationReport, maille_id: object,
) -> float | None:
    """Contrôle l'inégalité d'aires avant toute correction d'arrondi documentée."""
    if not math.isfinite(observed_area) or not (
        -AREA_TOLERANCE_M2 <= observed_area <= study_area + AREA_TOLERANCE_M2
    ):
        report.add("error", "reservoir_area_out_of_bounds", "indicators",
                   "La surface de réservoir mesurée viole 0 ≤ aire ≤ surface étudiée.",
                   maille_id=str(maille_id), observed_area_m2=repr(observed_area), study_area_m2=study_area)
        return None
    corrected = min(study_area, max(0.0, observed_area))
    if corrected != observed_area:
        report.add("info", "numeric_area_adjustment", "indicators",
                   "Ajustement limité à la tolérance numérique ; la mesure brute est conservée.",
                   maille_id=str(maille_id), delta_m2=corrected - observed_area)
    return 100.0 * corrected / study_area


def _observed_corridors(
    geometry: BaseGeometry, corridors: gpd.GeoDataFrame,
) -> tuple[float, float]:
    """Union séparée des lignes et polygones ; les lignes sur la limite sont exclues."""
    if geometry.area <= 0 or corridors.empty:
        return 0.0, 0.0
    hits = corridors.iloc[corridors.sindex.query(geometry, predicate="intersects")]
    lines = hits.loc[hits.geom_type.isin(("LineString", "MultiLineString")), "geometry"]
    polygons = hits.loc[hits.geom_type.isin(POLYGONS), "geometry"]
    # Une ligne coïncidant avec une frontière ne traverse pas l'intérieur de H ∩ T.
    # Éviter un overlay inutile sur un objet entièrement contenu : GEOS peut
    # réduire à vide une ligne très courte aux grandes coordonnées L93.
    clipped_lines = []
    for line in lines:
        clipped = line if geometry.covers(line) else line.intersection(geometry)
        if clipped.intersects(geometry.boundary):
            clipped = clipped.difference(geometry.boundary)
        clipped_lines.append(clipped)
    clipped_polygons = [polygon if geometry.covers(polygon) else polygon.intersection(geometry)
                        for polygon in polygons]
    length = union_all(clipped_lines).length
    area = union_all(clipped_polygons).area
    return float(length), float(area)


def _presence(length: float, area: float, covered: bool, in_territory: bool) -> bool | None:
    if not in_territory:
        return None
    if length > 0 or area > 0:
        return True
    return False if covered else None


def _polygonal_part(geometry: BaseGeometry) -> BaseGeometry:
    """Retire les contacts ponctuels/linéaires du découpage des mailles."""
    if geometry.geom_type in POLYGONS:
        return geometry
    if geometry.geom_type == "GeometryCollection":
        return union_all([_polygonal_part(part) for part in geometry.geoms])
    return union_all([])


def compute_enjeux(
    grid: gpd.GeoDataFrame, territory: gpd.GeoDataFrame,
    reservoirs: gpd.GeoDataFrame, corridors: gpd.GeoDataFrame,
    *, reservoir_coverage: CoverageEvidence | None = None,
    corridor_coverage: CoverageEvidence | None = None,
    reservoir_subframes: SubframeMapping | None = None,
    corridor_subframes: SubframeMapping | None = None,
    spatial_expectation: SpatialExpectation | None = None,
    corridor_sensitivity: CorridorSensitivity | None = None,
) -> EnjeuxResult:
    """Calcule les indicateurs après validation ; les entrées restent inchangées.

    ENJ-01 reste null si la complétude n'est pas établie sur toute la maille
    étudiée, même en présence d'objets observés. ENJ-02 peut être vrai avec une
    couverture inconnue, car une observation positive suffit à établir sa présence.
    """
    report = ValidationReport()
    for frame, spec in (
        (grid, LayerSpec("grid", POLYGONS, ("maille_id",), ("maille_id",))),
        (territory, LayerSpec("territory", POLYGONS)),
        (reservoirs, LayerSpec("reservoirs", POLYGONS, allow_empty=True)),
        (corridors, LayerSpec("corridors", CORRIDORS, allow_empty=True)),
    ):
        validate_geodataframe(frame, spec, report)
    reservoir_coverage = reservoir_coverage or CoverageEvidence()
    corridor_coverage = corridor_coverage or CoverageEvidence()
    territory_hash = territory_geometry_sha256(territory) if report.ok else None
    report.layers.setdefault("territory", {})["geometry_sha256"] = territory_hash
    reservoir_footprint = _coverage_geometry(reservoir_coverage, "reservoirs", report, territory_hash)
    corridor_footprint = _coverage_geometry(corridor_coverage, "corridors", report, territory_hash)
    _check_mapping(reservoirs, reservoir_subframes, "reservoirs", report)
    _check_mapping(corridors, corridor_subframes, "corridors", report)
    if corridor_sensitivity is not None:
        if (not math.isfinite(corridor_sensitivity.distance_m) or corridor_sensitivity.distance_m <= 0
                or not corridor_sensitivity.reference.strip()):
            report.add("error", "invalid_corridor_precision", "corridors",
                       "La sensibilité exige une distance strictement positive et une précision documentée.")
        report.layers.setdefault("corridors", {})["sensitivity"] = {
            "distance_m": corridor_sensitivity.distance_m if math.isfinite(corridor_sensitivity.distance_m)
            else repr(corridor_sensitivity.distance_m), "reference": corridor_sensitivity.reference,
        }
    else:
        report.add("warning", "corridor_precision_unknown", "corridors",
                   "Précision spatiale non documentée : seuls les résidus numériques sont identifiés.")
    if not report.ok:
        raise InputValidationError(report)
    validate_spatial_coverage(grid, territory, report)
    frames = {"grid": grid, "territory": territory, "reservoirs": reservoirs, "corridors": corridors}
    for name, evidence in (("reservoirs_coverage", reservoir_coverage), ("corridors_coverage", corridor_coverage)):
        if evidence.footprint is not None:
            frames[name] = evidence.footprint
    if report.ok:
        validate_spatial_plausibility(frames, territory, report, spatial_expectation)
    if not report.ok:
        raise InputValidationError(report)

    grid = grid.to_crs(METRIC_CRS).reset_index(drop=True)
    territory_union = union_all(territory.to_crs(METRIC_CRS).geometry.to_numpy())
    reservoirs = reservoirs.to_crs(METRIC_CRS)
    corridors = corridors.to_crs(METRIC_CRS)
    if reservoirs.geometry.name != "geometry":
        reservoirs = reservoirs.rename_geometry("geometry")
    if corridors.geometry.name != "geometry":
        corridors = corridors.rename_geometry("geometry")
    reservoir_union = union_all(reservoirs.geometry.to_numpy())
    # Seul H ∩ T entre dans les mesures ; la géométrie de sortie est aussi découpée.
    effective = grid.geometry.intersection(territory_union).apply(_polygonal_part)
    groups: list[tuple[str, str | None, str | None, object]] = []
    for kind, frame, mapping in (
        ("reservoirs", reservoirs, reservoir_subframes),
        ("corridors", corridors, corridor_subframes),
    ):
        if mapping is None:
            continue
        values = frame[mapping.column].astype("string")
        for value in sorted(values.dropna().unique()):
            subset = frame.loc[values.eq(value).fillna(False)]
            item = union_all(subset.geometry.to_numpy()) if kind == "reservoirs" else subset
            groups.append((kind, value, mapping.meanings[value], item))
        if values.isna().any():
            subset = frame.loc[values.isna()]
            item = union_all(subset.geometry.to_numpy()) if kind == "reservoirs" else subset
            groups.append((kind, None, None, item))

    rows: list[dict] = []
    subrows: list[dict] = []
    for position, cell in enumerate(effective):
        maille_id = grid.iloc[position]["maille_id"]
        study_area = float(cell.area)
        inside = study_area > 0
        r_covered = _fully_covered(cell, reservoir_coverage, reservoir_footprint)
        c_covered = _fully_covered(cell, corridor_coverage, corridor_footprint)
        observed_area = float(cell.intersection(reservoir_union).area) if inside else None
        length, area = _observed_corridors(cell, corridors)
        checked = _checked_proportion(observed_area, study_area, report, maille_id) if inside else None
        proportion = checked if r_covered else None
        numerical_residue = (0 < length <= LENGTH_TOLERANCE_M) or (0 < area <= AREA_TOLERANCE_M2)
        sensitivity_values = {
            "corridor_presence_sensitive": None,
            "corridor_sensitivity_length_min_m": None, "corridor_sensitivity_length_max_m": None,
            "corridor_sensitivity_area_min_m2": None, "corridor_sensitivity_area_max_m2": None,
        }
        if corridor_sensitivity is not None and inside:
            distance = corridor_sensitivity.distance_m
            inner = _polygonal_part(cell.buffer(-distance))
            outer = _polygonal_part(cell.buffer(distance).intersection(territory_union))
            low_length, low_area = _observed_corridors(inner, corridors)
            high_length, high_area = _observed_corridors(outer, corridors)
            sensitivity_values = {
                "corridor_presence_sensitive": (low_length > 0 or low_area > 0) != (high_length > 0 or high_area > 0),
                "corridor_sensitivity_length_min_m": low_length,
                "corridor_sensitivity_length_max_m": high_length,
                "corridor_sensitivity_area_min_m2": low_area,
                "corridor_sensitivity_area_max_m2": high_area,
            }
        rows.append({
            "maille_id": maille_id,
            "study_area_m2": study_area,
            "reservoir_observed_area_m2": observed_area,
            "reservoir_coverage_confirmed": r_covered,
            "reservoir_completeness_status": reservoir_coverage.effective_status,
            "enj_01_pct": proportion,
            "enj_01_status": "outside_territory" if not inside else "complete" if r_covered else "unknown_coverage",
            "corridor_observed_length_m": length if inside else None,
            "corridor_observed_area_m2": area if inside else None,
            "corridor_coverage_confirmed": c_covered,
            "corridor_completeness_status": corridor_coverage.effective_status,
            "corridor_numerical_residue": numerical_residue,
            **sensitivity_values,
            "enj_02_presence": _presence(length, area, c_covered, inside),
            "enj_02_status": "outside_territory" if not inside else "observed" if length > 0 or area > 0 else "confirmed_absence" if c_covered else "unknown_coverage",
        })
        for kind, value, meaning, item in groups:
            # La confirmation d'une couche ne garantit pas la complétude de son
            # classement par sous-trame : aucune absence par sous-trame n'est imputée.
            group_area = float(cell.intersection(item).area) if kind == "reservoirs" else None
            group_length, corridor_area = _observed_corridors(cell, item) if kind == "corridors" else (None, None)
            subrows.append({
                "maille_id": maille_id, "source": kind, "source_value": value,
                "meaning": meaning, "study_area_m2": study_area,
                "reservoir_observed_area_m2": group_area if inside else None,
                "corridor_observed_length_m": group_length if inside else None,
                "corridor_observed_area_m2": corridor_area if inside else None,
            })
    if not report.ok:
        raise InputValidationError(report)
    cells = gpd.GeoDataFrame(rows, geometry=effective, crs=METRIC_CRS)
    for column in ("enj_01_pct", "reservoir_observed_area_m2", "corridor_observed_length_m", "corridor_observed_area_m2"):
        cells[column] = pd.array(cells[column], dtype="Float64")
    cells["enj_02_presence"] = pd.array(cells["enj_02_presence"], dtype="boolean")
    cells["corridor_presence_sensitive"] = pd.array(cells["corridor_presence_sensitive"], dtype="boolean")
    # Hors de T : conserver la ligne attributaire avec une géométrie NULL.
    cells.loc[cells.study_area_m2 <= 0, "geometry"] = None
    report.add("info", "computed", "indicators", "Mesures géométriques calculées en Lambert-93.",
               cells=len(cells), unknown_enj_01=int(cells.enj_01_pct.isna().sum()),
               unknown_enj_02=int(cells.enj_02_presence.isna().sum()))
    if cells.corridor_numerical_residue.any():
        report.add("warning", "tiny_corridor_intersection", "indicators",
                   "Intersections positives à l'échelle de la tolérance numérique ; observations conservées.",
                   count=int(cells.corridor_numerical_residue.sum()))
    if cells.corridor_presence_sensitive.fillna(False).any():
        report.add("warning", "corridor_presence_sensitive", "indicators",
                   "Présence observée sensible au scénario de précision documenté ; référence brute conservée.",
                   count=int(cells.corridor_presence_sensitive.fillna(False).sum()))
    return EnjeuxResult(cells, pd.DataFrame(subrows), report)
