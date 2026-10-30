"""CLI : deux GeoPackages intermédiaires liés et un rapport M2 indivisible à l'usage."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from typing import Any
from uuid import uuid4

import geopandas as gpd
import pandas as pd
from shapely.errors import GEOSException

from analysis.aggregate_conflicts import ConflictAggregation, _interior_relation, aggregate_conflicts
from analysis.detect_conflicts import (
    EVENT_COLUMNS, EventEvidence, IntersectionPrecision, SourceFields, canonical_json,
    detect_route_corridor_conflicts, qualify_events,
)
from analysis.indicateurs_enjeux import CoverageEvidence, SubframeMapping
from analysis.run_enjeux import _gpkg_metadata, _merge_reports, _publish_failure_report, _sha256, _write_json
from analysis.validate_inputs import (
    CORRIDORS, POLYGONS, InputValidationError, LayerSpec, SpatialExpectation, ValidationReport, read_layer,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
VERSION_KEYS = ("grid_version", "method_version", "dataset_version")
LINK_TABLE = "liens_mailles_conflits"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("grid", "territory", "routes", "corridors"):
        parser.add_argument(f"--{name}", type=Path, required=True)
        parser.add_argument(f"--{name}-layer")
    for name in ("route", "corridor"):
        scope = parser.add_mutually_exclusive_group()
        scope.add_argument(f"--{name}-coverage", type=Path)
        scope.add_argument(f"--{name}-coverage-confirmed", action="store_true", help="Portée déclarée, pas validation.")
        parser.add_argument(f"--{name}-coverage-layer")
        parser.add_argument(f"--{name}-coverage-provenance")
    parser.add_argument("--config", type=Path, required=True, help="Identifiants sources et contrats M1 explicites.")
    parser.add_argument("--qualifications", type=Path, help="JSON de qualifications externes liées aux conflit_id.")
    for name in VERSION_KEYS:
        parser.add_argument("--" + name.replace("_", "-"))
    parser.add_argument("--output-events", type=Path, default=Path("data/derived/conflits_candidates.gpkg"))
    parser.add_argument("--output-cells", type=Path, default=Path("data/derived/mailles_conflits.gpkg"))
    parser.add_argument("--report", type=Path, default=Path("data/derived/conflits_validation.json"))
    return parser


def _read_json(path: Path) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"Constante JSON non finie interdite : {value}.")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=reject_constant)


def load_config(path: Path) -> dict[str, Any]:
    config = _read_json(path)
    if not isinstance(config, dict) or set(config) - {"grid", "territory", "routes", "corridors", "spatial", "precision"}:
        raise ValueError("Objet de configuration conflits inconnu.")
    source_keys = {"id_column", "expected_crs", "category_column", "structure_column", "level_column",
                   "context_reference", "subframes", "coverage"}
    allowed = {"grid": {"id_column", "expected_crs"}, "territory": {"expected_crs"},
               "routes": source_keys, "corridors": source_keys,
               "spatial": {"plausible_extent", "plausible_extent_layer", "reference", "validated_by", "margin_m"},
               "precision": {"distance_m", "reference", "localization_adequate"}}
    for name, settings in config.items():
        if not isinstance(settings, dict) or set(settings) - allowed[name]:
            raise ValueError(f"Configuration incorrecte : {name}.")
        for key in allowed[name] - {"subframes", "coverage", "distance_m", "localization_adequate", "margin_m"}:
            if key in settings and (not isinstance(settings[key], str) or not settings[key].strip()):
                raise ValueError(f"{name}.{key} doit être une chaîne non vide.")
        if "subframes" in settings:
            mapping = settings["subframes"]
            if (not isinstance(mapping, dict) or set(mapping) != {"column", "meanings"}
                    or not isinstance(mapping["column"], str) or not mapping["column"].strip()
                    or not isinstance(mapping["meanings"], dict) or not mapping["meanings"]
                    or any(not isinstance(v, str) or not v.strip() for v in mapping["meanings"].values())):
                raise ValueError("Mapping de sous-trame incorrect ou non documenté.")
        if "coverage" in settings:
            evidence = settings["coverage"]
            keys = {"status", "source_id", "producer", "vintage", "validity_extent", "theme",
                    "document_reference", "validated_by", "validated_at", "territory_sha256"}
            if not isinstance(evidence, dict) or set(evidence) - keys or any(
                not isinstance(v, str) or not v.strip() for v in evidence.values()
            ):
                raise ValueError("Métadonnées de complétude incorrectes.")
    for name in ("routes", "corridors"):
        if not config.get(name, {}).get("id_column"):
            raise ValueError(f"{name}.id_column doit identifier le champ réellement fourni par M1.")
    if "spatial" in config and not {"plausible_extent", "reference", "validated_by"} <= config["spatial"].keys():
        raise ValueError("Emprise plausible : chemin, référence et validateur M1 requis.")
    if "spatial" in config:
        margin = config["spatial"].get("margin_m", 0)
        if isinstance(margin, bool) or not isinstance(margin, (int, float)) or not math.isfinite(margin) or margin < 0:
            raise ValueError("Marge d'emprise positive ou nulle, finie et documentée attendue.")
    if "precision" in config and not {"distance_m", "reference"} <= config["precision"].keys():
        raise ValueError("Précision : distance et référence documentaire requises.")
    return config


def _source_fields(settings: dict[str, Any]) -> SourceFields:
    return SourceFields(**{key: SubframeMapping(**value) if key == "subframes" else value
                           for key, value in settings.items() if key not in {"expected_crs", "coverage"}})


def _processed_path(path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to((PROJECT_ROOT / "data/processed").resolve()):
        raise ValueError(f"Entrée géographique hors data/processed/ : {path}.")
    return path


def _output_paths(args: argparse.Namespace) -> dict[str, Path]:
    paths = {"events": args.output_events.resolve(), "cells": args.output_cells.resolve(), "report": args.report.resolve()}
    if len(set(paths.values())) != 3:
        raise ValueError("Les trois chemins de sortie doivent être distincts.")
    for role, path in paths.items():
        if not path.is_relative_to((PROJECT_ROOT / "data/derived").resolve()):
            raise ValueError("Sorties autorisées seulement dans data/derived/.")
        if path.suffix.lower() != (".json" if role == "report" else ".gpkg"):
            raise ValueError("Formats de sortie : deux .gpkg et un .json.")
        if path.exists():
            raise ValueError(f"Refus d'écraser : {path}.")
    for name in VERSION_KEYS:
        if getattr(args, name) is not None and not getattr(args, name).strip():
            raise ValueError(f"{name} : version inconnue à omettre, chaîne vide interdite.")
    return paths


def _write_links(path: Path, links: pd.DataFrame) -> None:
    with sqlite3.connect(path) as connection:
        links.to_sql(LINK_TABLE, connection, index=False, if_exists="fail",
                     dtype={"conflit_id": "TEXT", "canonical_owner": "INTEGER", "relation_spatiale": "TEXT"})
        connection.execute(f"CREATE UNIQUE INDEX unique_event_cell ON {LINK_TABLE} (conflit_id, maille_id)")
        connection.execute(
            "INSERT INTO gpkg_contents (table_name, data_type, identifier, description, last_change) "
            "VALUES (?, 'attributes', ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))",
            (LINK_TABLE, LINK_TABLE, "Relation plusieurs-à-plusieurs, sans double comptage global"),
        )


def verify_conflict_bundle(
    events_path: Path, cells_path: Path, report_path: Path,
    *, expected_paths: dict[str, Path] | None = None,
) -> dict[str, Any]:
    """Refuse les lots incomplets, discordants ou privés de relations vérifiables."""
    paths = {"events": Path(events_path).resolve(), "cells": Path(cells_path).resolve(), "report": Path(report_path).resolve()}
    if not all(path.is_file() for path in paths.values()):
        raise ValueError("Lot conflits incomplet : les deux GeoPackages et le rapport sont obligatoires.")
    try:
        payload = json.loads(paths["report"].read_text(encoding="utf-8"))
        run = payload["run"]
        if payload["ok"] is not True or payload["errors"] or run["status"] != "success":
            raise ValueError("Lot sans rapport de succès valide.")
        expected = {k: str(v) for k, v in (expected_paths or paths).items()}
        if run["artifact_paths"] != expected:
            raise ValueError("Chemins discordants dans le rapport.")
        for role in ("events", "cells"):
            with sqlite3.connect(f"{paths[role].as_uri()}?mode=ro", uri=True) as connection:
                if connection.execute("PRAGMA quick_check").fetchall() != [("ok",)]:
                    raise ValueError("Intégrité SQLite incorrecte.")
            embedded = _gpkg_metadata(paths[role])
            if (embedded["run_id"] != run["run_id"] or embedded["artifact_paths"] != expected
                    or embedded["bundle_required"] is not True or embedded["role"] != role
                    or embedded["feature_counts"] != run["feature_counts"]
                    or any(embedded[key] != run[key] for key in VERSION_KEYS)):
                raise ValueError("Identités, versions ou contrats du lot discordants.")
            if _sha256(paths[role]) != run["output_sha256"][role]:
                raise ValueError(f"Empreinte {role} discordante.")
        events = gpd.read_file(paths["events"], layer="conflits_candidates")
        cells = gpd.read_file(paths["cells"], layer="mailles_conflits")
        for name, frame in (("events", events), ("cells", cells)):
            if len(frame) != run["feature_counts"][name] or frame.crs is None or frame.crs.to_epsg() != 2154:
                raise ValueError("Effectif ou CRS de couche incorrect.")
        if (not set(EVENT_COLUMNS) <= set(events.columns) or events.conflit_id.isna().any()
                or events.conflit_id.duplicated().any() or cells.maille_id.isna().any() or cells.maille_id.duplicated().any()
                or events.geometry.isna().any() or events.geometry.is_empty.any() or not events.geometry.is_valid.all()):
            raise ValueError("Schéma ou identifiants de sortie incorrects.")
        with sqlite3.connect(f"{paths['cells'].as_uri()}?mode=ro", uri=True) as connection:
            links = pd.read_sql_query(f"SELECT * FROM {LINK_TABLE}", connection)
        if len(links) != run["feature_counts"]["links"] or links.duplicated(["conflit_id", "maille_id"]).any():
            raise ValueError("Effectif ou unicité des relations incorrects.")
        if (links.isna().any().any() or not links.canonical_owner.isin([0, 1]).all()
                or not links.relation_spatiale.isin(["interieur", "frontiere"]).all()):
            raise ValueError("Valeurs de relations incorrectes.")
        if not set(links.conflit_id) <= set(events.conflit_id) or not set(links.maille_id.map(canonical_json)) <= set(cells.maille_id.map(canonical_json)):
            raise ValueError("Relation sans événement ou maille correspondante.")
        for _, event in events.iterrows():
            selected = links.loc[links.conflit_id == event.conflit_id]
            if selected.canonical_owner.sum() != 1 or sorted(selected.maille_id.tolist(), key=canonical_json) != json.loads(event.maille_ids):
                raise ValueError("Relations d'événement ou propriétaire canonique incohérents.")
            interior_ids = []
            actual_ids = []
            for cell_position in cells.sindex.query(event.geometry, predicate="intersects"):
                cell = cells.iloc[cell_position]
                actual_ids.append(cell.maille_id)
                interior = _interior_relation(event.geometry, cell.geometry)
                if interior:
                    interior_ids.append(cell.maille_id)
                recorded = selected.loc[selected.maille_id.map(canonical_json) == canonical_json(cell.maille_id)]
                if len(recorded) != 1 or recorded.relation_spatiale.iloc[0] != ("interieur" if interior else "frontiere"):
                    raise ValueError("Relation spatiale discordante avec les géométries.")
            if sorted(actual_ids, key=canonical_json) != json.loads(event.maille_ids):
                raise ValueError("Rattachements spatiaux incomplets.")
            owner = min(interior_ids or actual_ids, key=canonical_json)
            if canonical_json(selected.loc[selected.canonical_owner == 1, "maille_id"].iloc[0]) != canonical_json(owner):
                raise ValueError("Propriétaire canonique non déterministe.")
        for _, cell in cells.iterrows():
            selected = links.loc[links.maille_id.map(canonical_json) == canonical_json(cell.maille_id)]
            if sorted(selected.conflit_id) != json.loads(cell.conflit_ids):
                raise ValueError("Liste d'événements de maille incohérente.")
        return payload
    except (KeyError, TypeError, sqlite3.DatabaseError) as exc:
        raise ValueError(f"Lot conflits non conforme : {exc}") from exc


def publish_conflict_bundle(
    result: ConflictAggregation, metadata: dict[str, Any], paths: dict[str, Path],
) -> None:
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".m2-conflicts-", dir=paths["events"].parent) as temporary:
        staged = {"events": Path(temporary) / "events.gpkg", "cells": Path(temporary) / "cells.gpkg",
                  "report": Path(temporary) / "report.json"}
        events = result.events.copy()
        for name in ("precision_m", "length_m", "area_m2"):
            events[name] = pd.array(events[name], dtype="Float64")
        for name in ("precision_sensitive", "numeric_residue"):
            events[name] = pd.array(events[name], dtype="boolean")
        events.to_file(staged["events"], driver="GPKG", layer="conflits_candidates", engine="pyogrio", index=False)
        result.cells.to_file(staged["cells"], driver="GPKG", layer="mailles_conflits", engine="pyogrio", index=False)
        _write_links(staged["cells"], result.links)
        counts = {"events": len(events), "cells": len(result.cells), "links": len(result.links)}
        path_strings = {k: str(v) for k, v in paths.items()}
        for role in ("events", "cells"):
            embedded = {key: metadata[key] for key in ("run_id", *VERSION_KEYS)}
            embedded.update({"bundle_required": True, "role": role, "artifact_paths": path_strings, "feature_counts": counts})
            with sqlite3.connect(staged[role]) as connection:
                connection.execute("CREATE TABLE m2_run (metadata_json TEXT NOT NULL)")
                connection.execute("INSERT INTO m2_run VALUES (?)", (canonical_json(embedded),))
        metadata.update({"artifact_paths": path_strings, "feature_counts": counts, "summary": result.summary,
                         "output_sha256": {k: _sha256(staged[k]) for k in ("events", "cells")},
                         "status": "success", "finished_at_utc": datetime.now(timezone.utc).isoformat()})
        _write_json(staged["report"], {**result.report.as_dict(), "run": metadata})
        verify_conflict_bundle(staged["events"], staged["cells"], staged["report"], expected_paths=paths)
        published = []
        try:
            for role in ("report", "events", "cells"):
                os.link(staged[role], paths[role])
                published.append(role)
            verify_conflict_bundle(paths["events"], paths["cells"], paths["report"])
        except BaseException:
            for role in reversed(published):
                if paths[role].exists() and os.path.samestat(staged[role].stat(), paths[role].stat()):
                    paths[role].unlink()
            raise


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        paths = _output_paths(args)
        for name in ("grid", "territory", "routes", "corridors", "route_coverage", "corridor_coverage"):
            if getattr(args, name) is not None:
                _processed_path(getattr(args, name))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    report = ValidationReport()
    metadata = {
        "run_id": str(uuid4()), "started_at_utc": datetime.now(timezone.utc).isoformat(),
        **{key: getattr(args, key) for key in VERSION_KEYS}, "python": sys.version,
        "software": {key: version(key) for key in ("geopandas", "shapely", "pandas", "pyproj", "pyogrio")},
        "command_args": {key: str(value) if isinstance(value, Path) else value for key, value in vars(args).items()},
        "source_sha256": {}, "code_sha256": {name: _sha256(Path(__file__).with_name(name)) for name in (
            "detect_conflicts.py", "aggregate_conflicts.py", "run_conflicts.py", "validate_inputs.py", "indicateurs_enjeux.py", "run_enjeux.py")},
    }
    missing = [key for key in VERSION_KEYS if metadata[key] is None]
    if missing:
        report.add("warning", "versions_missing", "pipeline", "Versions inconnues conservées null.", fields=missing)
    result = None
    try:
        config = load_config(args.config)
        metadata["config"] = config
        frames = {}
        for name in ("grid", "territory", "routes", "corridors"):
            id_column = config.get(name, {}).get("id_column", "maille_id" if name == "grid" else None)
            spec = LayerSpec(name, CORRIDORS if name in {"routes", "corridors"} else POLYGONS,
                             (id_column,) if id_column else (), (id_column,) if name == "grid" else (),
                             expected_crs=config.get(name, {}).get("expected_crs"), allow_empty=name in {"routes", "corridors"})
            frames[name] = read_layer(getattr(args, name), spec, report, layer=getattr(args, f"{name}_layer"))
        evidence = {}
        for name in ("route", "corridor"):
            path = getattr(args, f"{name}_coverage")
            footprint = read_layer(path, LayerSpec(f"{name}s_coverage", POLYGONS), report,
                                   layer=getattr(args, f"{name}_coverage_layer")) if path else None
            evidence[name] = CoverageEvidence(confirmed=getattr(args, f"{name}_coverage_confirmed"), footprint=footprint,
                                             provenance=getattr(args, f"{name}_coverage_provenance"),
                                             **config[f"{name}s"].get("coverage", {}))
        spatial = None
        spatial_path = None
        if "spatial" in config:
            settings = config["spatial"]
            spatial_path = _processed_path(Path(settings["plausible_extent"]))
            footprint = read_layer(spatial_path, LayerSpec("plausible_extent", POLYGONS), report,
                                   layer=settings.get("plausible_extent_layer"))
            if footprint is not None:
                spatial = SpatialExpectation(footprint, settings["reference"], settings["validated_by"], settings.get("margin_m", 0))
        for path in [args.config, args.qualifications, spatial_path, *(getattr(args, key) for key in (
            "grid", "territory", "routes", "corridors", "route_coverage", "corridor_coverage"))]:
            if path is not None and path.is_file():
                metadata["source_sha256"][str(path)] = _sha256(path)
        if report.ok:
            id_column = config.get("grid", {}).get("id_column", "maille_id")
            if id_column != "maille_id":
                if "maille_id" in frames["grid"].columns:
                    raise ValueError("Le mapping de grille écraserait maille_id.")
                frames["grid"] = frames["grid"].rename(columns={id_column: "maille_id"})
            detection = detect_route_corridor_conflicts(
                frames["routes"], frames["corridors"], frames["territory"],
                route_fields=_source_fields(config["routes"]), corridor_fields=_source_fields(config["corridors"]),
                route_coverage=evidence["route"], corridor_coverage=evidence["corridor"],
                method_version=args.method_version, spatial_expectation=spatial,
                precision=IntersectionPrecision(**config["precision"]) if "precision" in config else None,
            )
            if args.qualifications:
                records = _read_json(args.qualifications)
                if not isinstance(records, list):
                    raise ValueError("Une liste de qualifications documentées est attendue.")
                detection.events = qualify_events(detection.events, [EventEvidence(**item) for item in records])
            result = aggregate_conflicts(frames["grid"], frames["territory"], detection)
            _merge_reports(report, result.report)
            result.report = report
    except InputValidationError as exc:
        _merge_reports(report, exc.report)
    except (OSError, ValueError, TypeError, GEOSException) as exc:
        report.add("error", "conflicts_pipeline_error", "pipeline", str(exc))
    if result is not None and report.ok:
        try:
            publish_conflict_bundle(result, metadata, paths)
            print(f"Lot conflits vérifié : {paths['events']} ; {paths['cells']} ; {paths['report']}")
            return 0
        except Exception as exc:
            metadata.pop("output_sha256", None)
            report.add("error", "conflicts_export_failed", "pipeline", "Publication du lot interrompue.", reason=str(exc))
    metadata.update({"status": "blocked", "finished_at_utc": datetime.now(timezone.utc).isoformat()})
    for issue in report.issues:
        if issue.severity == "error":
            print(f"[{issue.code}] {issue.layer}: {issue.message}", file=sys.stderr)
    try:
        _publish_failure_report(paths["report"], {**report.as_dict(), "run": metadata})
    except Exception as exc:
        print(f"Rapport non enregistré : {exc}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
