"""Contrôles SIG sans réparation implicite ni modification des sources."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

import geopandas as gpd
import numpy as np
from pyproj import CRS
from shapely import get_coordinates, union_all
from shapely.validation import explain_validity

METRIC_CRS = "EPSG:2154"
# Tolérance numérique absolue, en m² ; ce n'est pas un seuil écologique.
AREA_TOLERANCE_M2 = 1e-6
LENGTH_TOLERANCE_M = 1e-9
POLYGONS = ("Polygon", "MultiPolygon")
CORRIDORS = ("LineString", "MultiLineString", *POLYGONS)


@dataclass(frozen=True)
class LayerSpec:
    """Contrat explicite d'une couche ; aucun champ source n'est deviné."""

    name: str
    geometry_types: tuple[str, ...]
    required_columns: tuple[str, ...] = ()
    unique_columns: tuple[str, ...] = ()
    expected_crs: str | None = None
    allow_empty: bool = False


@dataclass(frozen=True)
class SpatialExpectation:
    """Emprise plausible officielle fournie/validée par M1, jamais inférée."""

    footprint: gpd.GeoDataFrame
    reference: str
    validated_by: str
    margin_m: float = 0.0


@dataclass(frozen=True)
class ValidationIssue:
    severity: Literal["error", "warning", "info"]
    code: str
    layer: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationReport:
    """Rapport sérialisable : erreurs bloquantes, avertissements et qualité."""

    issues: list[ValidationIssue] = field(default_factory=list)
    layers: dict[str, dict[str, Any]] = field(default_factory=dict)

    def add(
        self, severity: Literal["error", "warning", "info"], code: str,
        layer: str, message: str, **details: Any,
    ) -> None:
        self.issues.append(ValidationIssue(severity, code, layer, message, details))

    @property
    def ok(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "metric_crs": METRIC_CRS,
            "layers": self.layers,
            "errors": [asdict(i) for i in self.issues if i.severity == "error"],
            "warnings": [asdict(i) for i in self.issues if i.severity == "warning"],
            "quality": [asdict(i) for i in self.issues if i.severity == "info"],
        }


class InputValidationError(ValueError):
    """Une erreur scientifique ou technique interdit le calcul."""

    def __init__(self, report: ValidationReport):
        self.report = report
        messages = [f"{i.layer}: {i.message}" for i in report.issues if i.severity == "error"]
        super().__init__("; ".join(messages))


def validate_geodataframe(
    frame: gpd.GeoDataFrame, spec: LayerSpec,
    report: ValidationReport | None = None,
) -> ValidationReport:
    """Inspecte attributs, géométries et reprojection, sans modifier ``frame``."""
    if report is None:
        report = ValidationReport()
    name = spec.name
    report.layers.setdefault(name, {}).update({"feature_count": len(frame)})
    report.layers[name].setdefault("validation_contract", asdict(spec))
    for column in dict.fromkeys((*spec.required_columns, *spec.unique_columns)):
        if column not in frame.columns:
            report.add("error", "missing_column", name, f"Colonne requise absente : {column}.")
        elif frame[column].isna().any():
            report.add("error", "null_attribute", name, f"Valeurs nulles dans {column}.",
                       count=int(frame[column].isna().sum()))
    for column in spec.unique_columns:
        if column in frame and frame[column].duplicated().any():
            report.add("error", "duplicate_id", name, f"Identifiants non uniques : {column}.",
                       count=int(frame[column].duplicated(keep=False).sum()))
    if frame.empty:
        report.add("info" if spec.allow_empty else "error", "empty_layer", name,
                   "Couche sans entité ; l'absence ne prouve pas la couverture de la source.")
    try:
        geometry = frame.geometry
    except (AttributeError, ValueError):
        report.add("error", "missing_geometry", name, "Colonne géométrique active absente.")
        return report

    nulls = geometry.isna()
    empties = geometry.is_empty
    invalid = ~geometry.is_valid & ~nulls & ~empties
    for mask, code, message in (
        (nulls, "null_geometry", "Géométries nulles."),
        (empties, "empty_geometry", "Géométries vides."),
        (invalid, "invalid_geometry", "Géométries invalides ; aucune réparation automatique."),
    ):
        if mask.any():
            details: dict[str, Any] = {"count": int(mask.sum())}
            if code == "invalid_geometry":
                details["examples"] = [explain_validity(g) for g in geometry[mask].head(5)]
            report.add("error", code, name, message, **details)
    wrong_type = ~geometry.geom_type.isin(spec.geometry_types) & ~nulls & ~empties
    if wrong_type.any():
        report.add("error", "geometry_type", name, "Types géométriques incompatibles.",
                   found=sorted(geometry[wrong_type].geom_type.unique().tolist()),
                   expected=list(spec.geometry_types))
    report.layers[name]["geometry_types"] = sorted(geometry.geom_type.dropna().unique().tolist())
    if name == "corridors" and geometry.geom_type.isin(("Point", "MultiPoint")).any():
        report.add("error", "point_corridor_business_case", name,
                   "Corridors ponctuels : cas métier distinct à définir, sans conversion en longueur ou surface.")
    coordinates = get_coordinates(geometry.to_numpy())
    if coordinates.size and not np.isfinite(coordinates).all():
        report.add("error", "nonfinite_coordinates", name, "Coordonnées non finies dans les géométries sources.")

    if frame.crs is None:
        report.add("error", "missing_crs", name, "CRS absent : son attribution doit être validée par M1.")
        return report
    try:
        crs = CRS.from_user_input(frame.crs)
        report.layers[name]["source_crs"] = crs.to_string()
        degree_axes = crs.axis_info and all(axis.unit_name == "degree" for axis in crs.axis_info[:2])
        if crs.is_geographic and degree_axes and coordinates.size and (
            (np.abs(coordinates[:, 0]) > 180).any() or (np.abs(coordinates[:, 1]) > 90).any()
        ):
            report.add("error", "aberrant_geographic_coordinates", name,
                       "Coordonnées hors domaine longitude/latitude ; déclaration de CRS probablement incorrecte.")
        if spec.expected_crs and crs != CRS.from_user_input(spec.expected_crs):
            report.add("error", "unexpected_crs", name, "Le CRS diffère du contrat explicite.",
                       expected=spec.expected_crs, found=crs.to_string())
        projected = frame.to_crs(METRIC_CRS)
        usable = projected.geometry[~nulls & ~empties]
        if len(usable) and not np.isfinite(usable.bounds.to_numpy()).all():
            report.add("error", "reprojection_failed", name,
                       "La reprojection produit des coordonnées non finies ; vérifier le CRS déclaré.")
        elif len(usable) and not usable.is_valid.all():
            report.add("error", "invalid_projected_geometry", name,
                       "Géométries invalides après reprojection.")
        elif len(usable) and (not np.isfinite(usable.area).all() or not np.isfinite(usable.length).all()):
            report.add("error", "nonfinite_metrics", name,
                       "Surfaces ou longueurs non finies : coordonnées manifestement aberrantes.")
        else:
            report.add("info", "reprojection_ok", name, "Reprojection possible en EPSG:2154.")
    except (ValueError, TypeError, RuntimeError) as exc:
        report.add("error", "reprojection_failed", name, "CRS ou reprojection non utilisable.",
                   reason=str(exc))
    return report


def read_layer(
    path: str | Path, spec: LayerSpec, report: ValidationReport,
    *, layer: str | None = None,
) -> gpd.GeoDataFrame | None:
    """Lit une couche GPKG/GeoJSON et consigne tous les problèmes attendus."""
    path = Path(path)
    report.layers.setdefault(spec.name, {}).update({"path": str(path), "layer": layer})
    if not path.is_file():
        report.add("error", "missing_file", spec.name, "Fichier d'entrée absent.", path=str(path))
        return None
    if path.suffix.lower() not in {".gpkg", ".geojson", ".json"}:
        report.add("error", "unsupported_format", spec.name, "Formats acceptés : GeoPackage et GeoJSON.")
        return None
    try:
        available = gpd.list_layers(path)
        names = available["name"].tolist()
        if layer is None and len(names) != 1:
            report.add("error", "ambiguous_layer", spec.name,
                       "Préciser la couche du conteneur.", available=names)
            return None
        selected = layer if layer is not None else names[0]
        if selected not in names:
            report.add("error", "missing_layer", spec.name,
                       "Couche demandée absente du conteneur.", requested=selected, available=names)
            return None
        frame = gpd.read_file(path, layer=selected)
    except Exception as exc:  # GDAL/pyogrio : conserver aussi les erreurs de lecture natives.
        report.add("error", "unreadable_file", spec.name, "Lecture du fichier impossible.", reason=str(exc))
        return None
    validate_geodataframe(frame, spec, report)
    return frame


def validate_spatial_coverage(
    grid: gpd.GeoDataFrame, territory: gpd.GeoDataFrame,
    report: ValidationReport,
) -> None:
    """Contrôle la couverture géométrique de T ; ne déduit aucune couverture source."""
    grid_union = union_all(grid.to_crs(METRIC_CRS).geometry.to_numpy())
    study_union = union_all(territory.to_crs(METRIC_CRS).geometry.to_numpy())
    uncovered = float(study_union.difference(grid_union).area)
    overlapping = float(grid.to_crs(METRIC_CRS).geometry.area.sum() - grid_union.area)
    report.add("info", "territory_coverage", "grid", "Couverture géométrique de la grille.",
               territory_area_m2=float(study_union.area), uncovered_area_m2=uncovered,
               overlap_area_m2=max(0.0, overlapping))
    if study_union.area <= 0:
        report.add("error", "zero_territory_area", "territory", "Le territoire n'a pas de surface positive.")
    if uncovered > AREA_TOLERANCE_M2:
        report.add("error", "grid_coverage_gap", "grid", "La grille ne couvre pas tout le territoire étudié.",
                   uncovered_area_m2=uncovered)
    if overlapping > AREA_TOLERANCE_M2:
        report.add("error", "grid_overlap", "grid",
                   "Chevauchement surfacique de mailles : la grille officielle ne doit pas compter deux fois des surfaces.",
                   overlap_area_m2=overlapping)
    outside = grid.to_crs(METRIC_CRS).geometry.intersection(study_union).area <= 0
    if outside.any():
        report.add("warning", "cells_outside_territory", "grid",
                   "Certaines mailles n'ont aucune surface dans T ; leurs indicateurs seront null.",
                   count=int(outside.sum()))


def validate_spatial_plausibility(
    frames: dict[str, gpd.GeoDataFrame], territory: gpd.GeoDataFrame,
    report: ValidationReport, expectation: SpatialExpectation | None = None,
) -> None:
    """Compare les sources à T et, si disponible, à une emprise M1 explicite.

    Une source régionale peut légitimement ne pas rencontrer le pilote : cette
    incohérence relative est signalée. Sortir de l'emprise plausible contractuelle
    est en revanche bloquant. Aucun rectangle normand n'est codé en dur.
    Les entrées doivent avoir passé les contrôles géométriques/CRS préalables.
    """
    study = union_all(territory.to_crs(METRIC_CRS).geometry.to_numpy())
    plausible = None
    if expectation is None:
        report.add("warning", "plausible_extent_missing", "spatial",
                   "Emprise plausible M1 non fournie : la cohérence géographique n'est pas validée.")
    else:
        if not expectation.reference.strip() or not expectation.validated_by.strip():
            report.add("error", "unvalidated_plausible_extent", "spatial",
                       "L'emprise plausible nécessite une référence officielle et un validateur M1.")
        if not np.isfinite(expectation.margin_m) or expectation.margin_m < 0:
            report.add("error", "invalid_spatial_margin", "spatial", "La marge métrique doit être finie et positive ou nulle.")
        start = len(report.issues)
        validate_geodataframe(expectation.footprint, LayerSpec("plausible_extent", POLYGONS), report)
        if not any(i.severity == "error" for i in report.issues[start:]) and report.ok:
            plausible = union_all(expectation.footprint.to_crs(METRIC_CRS).geometry.to_numpy())
            if expectation.margin_m:
                plausible = plausible.buffer(expectation.margin_m)
        report.layers.setdefault("plausible_extent", {}).update({
            "reference": expectation.reference, "validated_by": expectation.validated_by,
            "margin_m": expectation.margin_m,
        })
    for name, frame in frames.items():
        projected = frame.to_crs(METRIC_CRS)
        if projected.empty:
            continue
        intersects = projected.geometry.intersects(study)
        if not intersects.any():
            distance = float(projected.geometry.distance(study).min())
            report.add("warning", "layer_disjoint_from_territory", name,
                       "Couche sans contact avec T : contrôler emprise, coordonnées et déclaration de CRS.",
                       minimum_distance_m=distance)
        if plausible is not None:
            # Contrôle de chaque objet : une entité correcte ne masque pas un point aberrant éloigné.
            outside = ~projected.geometry.map(plausible.covers)
            if outside.any():
                report.add("error", "outside_plausible_extent", name,
                           "Entités hors emprise plausible validée M1 ; erreur d'emprise ou de CRS possible.",
                           count=int(outside.sum()))
