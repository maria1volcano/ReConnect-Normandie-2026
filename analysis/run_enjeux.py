"""CLI M2 : entrées préparées par M1, résultats intermédiaires exclusivement."""

from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
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
from shapely.errors import GEOSException

from analysis.indicateurs_enjeux import (
    CorridorSensitivity, CoverageEvidence, EnjeuxResult, SubframeMapping, compute_enjeux,
)
from analysis.validate_inputs import (
    CORRIDORS, METRIC_CRS, POLYGONS, InputValidationError, LayerSpec,
    SpatialExpectation, ValidationReport, read_layer,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("grid", "territory", "reservoirs", "corridors"):
        parser.add_argument(f"--{name}", type=Path, required=True, help="Fichier dans data/processed/.")
        parser.add_argument(f"--{name}-layer", help="Nom de couche, obligatoire si le GPKG en contient plusieurs.")
    for name in ("reservoir", "corridor"):
        group = parser.add_mutually_exclusive_group()
        group.add_argument(f"--{name}-coverage-confirmed", action="store_true",
                           help="Portée globale DÉCLARÉE ; métadonnées validées requises pour confirmer les zéros.")
        group.add_argument(f"--{name}-coverage", type=Path,
                           help="Emprise polygonale de complétude validée, dans data/processed/.")
        parser.add_argument(f"--{name}-coverage-layer")
        parser.add_argument(f"--{name}-coverage-provenance", help="Référence justifiant la complétude déclarée.")
    parser.add_argument("--config", type=Path, help="JSON : mappings de champs et CRS attendus validés par M1.")
    for name in ("grid", "method", "dataset"):
        parser.add_argument(f"--{name}-version", help="Version communiquée/validée ; sinon null, sans valeur inventée.")
    parser.add_argument("--output", type=Path, default=Path("data/derived/indicateurs_enjeux.gpkg"))
    parser.add_argument("--report", type=Path, help="Rapport JSON dans data/derived/, défaut : <output>.validation.json.")
    return parser


def load_config(path: Path | None) -> dict[str, dict[str, Any]]:
    """Schéma volontairement restreint ; les clés inconnues sont des erreurs."""
    config = json.loads(path.read_text(encoding="utf-8")) if path else {}
    if not isinstance(config, dict):
        raise ValueError("La configuration doit être un objet JSON.")
    allowed = {
        "grid": {"id_column", "expected_crs"}, "territory": {"expected_crs"},
        "reservoirs": {"expected_crs", "subframes", "coverage"},
        "corridors": {"expected_crs", "subframes", "coverage", "sensitivity"},
        "spatial": {"plausible_extent", "plausible_extent_layer", "reference", "validated_by", "margin_m"},
    }
    for key, item in config.items():
        if key not in allowed or not isinstance(item, dict) or set(item) - allowed[key]:
            raise ValueError(f"Configuration inconnue ou incorrecte : {key}.")
        for text_key in ("id_column", "expected_crs"):
            if text_key in item and (not isinstance(item[text_key], str) or not item[text_key].strip()):
                raise ValueError(f"{key}.{text_key} doit être une chaîne non vide.")
        if "subframes" in item:
            mapping = item["subframes"]
            if not isinstance(mapping, dict) or set(mapping) != {"column", "meanings"}:
                raise ValueError(f"{key}.subframes attend column et meanings.")
            if not isinstance(mapping["column"], str) or not mapping["column"].strip():
                raise ValueError("Le champ source de sous-trame doit être renseigné.")
            if not isinstance(mapping["meanings"], dict) or not mapping["meanings"] or any(
                not isinstance(v, str) or not v.strip() for v in mapping["meanings"].values()
            ):
                raise ValueError("Les codes de sous-trame doivent avoir des significations documentées.")
        if "coverage" in item:
            evidence = item["coverage"]
            keys = {"status", "source_id", "producer", "vintage", "validity_extent", "theme",
                    "document_reference", "validated_by", "validated_at", "territory_sha256"}
            if not isinstance(evidence, dict) or set(evidence) - keys or any(
                not isinstance(v, str) or not v.strip() for v in evidence.values()
            ):
                raise ValueError(f"{key}.coverage : métadonnées textuelles inconnues ou vides.")
        if "sensitivity" in item:
            sensitivity = item["sensitivity"]
            if not isinstance(sensitivity, dict) or set(sensitivity) != {"distance_m", "reference"}:
                raise ValueError("corridors.sensitivity attend distance_m et reference.")
            distance = sensitivity["distance_m"]
            if (isinstance(distance, bool) or not isinstance(distance, (float, int))
                    or not math.isfinite(distance) or distance <= 0
                    or not isinstance(sensitivity["reference"], str) or not sensitivity["reference"].strip()):
                raise ValueError("La sensibilité exige une distance positive finie et une référence documentaire.")
        if key == "spatial":
            for required in ("plausible_extent", "reference", "validated_by"):
                if not isinstance(item.get(required), str) or not item[required].strip():
                    raise ValueError(f"spatial.{required} doit être renseigné depuis une référence M1.")
            margin = item.get("margin_m", 0.0)
            if isinstance(margin, bool) or not isinstance(margin, (float, int)) or not math.isfinite(margin) or margin < 0:
                raise ValueError("spatial.margin_m doit être une distance finie positive ou nulle.")
    return config


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _check_paths(args: argparse.Namespace) -> tuple[Path, Path]:
    processed = (PROJECT_ROOT / "data/processed").resolve()
    derived = (PROJECT_ROOT / "data/derived").resolve()
    for name in ("grid", "territory", "reservoirs", "corridors", "reservoir_coverage", "corridor_coverage"):
        path = getattr(args, name)
        if path is not None and not path.resolve().is_relative_to(processed):
            raise ValueError(f"{name} doit se trouver dans {processed}.")
    output = args.output.resolve()
    report = args.report.resolve() if args.report else output.with_suffix(".validation.json")
    if output.suffix.lower() != ".gpkg" or report.suffix.lower() != ".json":
        raise ValueError("Sortie attendue en .gpkg et rapport en .json.")
    for path in (output, report):
        if not path.is_relative_to(derived):
            raise ValueError(f"Les sorties doivent rester dans {derived} ; aucun export public.")
        if path.exists():
            raise ValueError(f"Refus d'écraser un fichier existant : {path}.")
    return output, report


def _merge_reports(target: ValidationReport, computed: ValidationReport) -> None:
    for name, metadata in computed.layers.items():
        target.layers.setdefault(name, {}).update(metadata)
    seen = {json.dumps(asdict(i), sort_keys=True) for i in target.issues}
    for issue in computed.issues:
        key = json.dumps(asdict(issue), sort_keys=True)
        if key not in seen:
            target.issues.append(issue)
            seen.add(key)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    """Sérialise intégralement avant d'ouvrir le fichier temporaire."""
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8") as destination:
        destination.write(serialized)
        destination.flush()
        os.fsync(destination.fileno())
    json.loads(path.read_text(encoding="utf-8"))


def _gpkg_metadata(path: Path) -> dict[str, Any]:
    with sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True) as connection:
        if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise ValueError("Contrôle d'intégrité SQLite du GeoPackage en échec.")
        rows = connection.execute("SELECT metadata_json FROM m2_run").fetchall()
    if len(rows) != 1:
        raise ValueError("Le GeoPackage doit contenir une seule identité d'exécution M2.")
    return json.loads(rows[0][0])


def verify_artifact_pair(
    output: Path, report_path: Path, *, expected_paths: tuple[Path, Path] | None = None,
) -> dict[str, Any]:
    """Seul un couple complet, lisible et concordant est un résultat réutilisable.

    Les chemins explicites sont destinés au contrôle des fichiers temporaires
    avant publication. Les consommateurs utilisent les deux premiers arguments.
    """
    try:
        return _verify_artifact_pair(output, report_path, expected_paths=expected_paths)
    except (KeyError, TypeError, sqlite3.DatabaseError) as exc:
        raise ValueError(f"Manifeste ou GeoPackage M2 non conforme : {exc}") from exc


def _verify_artifact_pair(
    output: Path, report_path: Path, *, expected_paths: tuple[Path, Path] | None = None,
) -> dict[str, Any]:
    output, report_path = Path(output).resolve(), Path(report_path).resolve()
    if not output.is_file() or not report_path.is_file():
        raise ValueError("Couple M2 incomplet : GeoPackage ou rapport final absent.")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    run = payload["run"]
    if payload["ok"] is not True or payload["errors"] or run["status"] != "success":
        raise ValueError("Le rapport ne valide pas une exécution complète.")
    expected_output, expected_report = expected_paths or (output, report_path)
    embedded = _gpkg_metadata(output)
    if embedded["report_required"] is not True or embedded["run_id"] != run["run_id"]:
        raise ValueError("Identités d'exécution GeoPackage/rapport discordantes.")
    for name, path in (("output", expected_output), ("report", expected_report)):
        if run["artifact_paths"][name] != str(path) or embedded["artifact_paths"][name] != str(path):
            raise ValueError("Les chemins du couple d'artefacts ne correspondent pas au manifeste.")
    for key in ("grid_version", "method_version", "dataset_version"):
        if key not in run or embedded.get(key) != run[key]:
            raise ValueError(f"Version incohérente ou absente du manifeste : {key}.")
    if _sha256(output) != run["output_sha256"]:
        raise ValueError("L'empreinte du GeoPackage diffère de celle du rapport.")
    counts = run["layer_feature_counts"]
    if "indicateurs_enjeux" not in counts or embedded["layer_feature_counts"] != counts:
        raise ValueError("Liste de couches absente ou incohérente dans le couple M2.")
    for layer, count in run["layer_feature_counts"].items():
        frame = gpd.read_file(output, layer=layer)
        if len(frame) != count or frame.crs is None or frame.crs.to_epsg() != 2154:
            raise ValueError(f"Couche exportée non conforme : {layer}.")
    return payload


def _publish_pair(
    result: EnjeuxResult, report: ValidationReport, metadata: dict[str, Any],
    output: Path, report_path: Path,
) -> None:
    """Prépare et vérifie les deux artefacts, publie le rapport d'abord, puis le GPKG.

    Une interruption entre les deux publications laisse au plus un rapport sans
    GPKG. Toute erreur normale retire uniquement les liens créés par cet appel.
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".m2-", dir=output.parent) as temporary:
        staged_output = Path(temporary) / "indicateurs.gpkg"
        staged_report = Path(temporary) / "validation.json"
        result.cells.to_file(staged_output, driver="GPKG", layer="indicateurs_enjeux", index=False, engine="pyogrio")
        counts = {"indicateurs_enjeux": len(result.cells)}
        if not result.subframes.empty:
            subframes = result.subframes.merge(result.cells[["maille_id", "geometry"]], on="maille_id", validate="many_to_one")
            gpd.GeoDataFrame(subframes, geometry="geometry", crs=METRIC_CRS).to_file(
                staged_output, driver="GPKG", layer="observations_sous_trames", index=False, engine="pyogrio",
            )
            counts["observations_sous_trames"] = len(subframes)
        embedded = {key: metadata[key] for key in ("run_id", "grid_version", "method_version", "dataset_version")}
        embedded.update({"report_required": True, "layer_feature_counts": counts,
                         "artifact_paths": {"output": str(output), "report": str(report_path)}})
        with sqlite3.connect(staged_output) as connection:
            connection.execute("CREATE TABLE m2_run (metadata_json TEXT NOT NULL)")
            connection.execute("INSERT INTO m2_run VALUES (?)", (json.dumps(embedded, allow_nan=False),))
        metadata.update({
            "artifact_paths": embedded["artifact_paths"], "layer_feature_counts": counts,
            "output_sha256": _sha256(staged_output), "status": "success",
            "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        _write_json(staged_report, {**report.as_dict(), "run": metadata})
        verify_artifact_pair(staged_output, staged_report, expected_paths=(output, report_path))
        published: list[tuple[Path, Path]] = []
        try:
            for staged, final in ((staged_report, report_path), (staged_output, output)):
                os.link(staged, final)  # création exclusive, jamais de remplacement
                published.append((staged, final))
            verify_artifact_pair(output, report_path)
        except BaseException:
            for staged, final in reversed(published):
                if final.exists() and os.path.samestat(staged.stat(), final.stat()):
                    final.unlink()
            raise


def _publish_failure_report(report_path: Path, payload: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".m2-failure-", dir=report_path.parent) as temporary:
        staged = Path(temporary) / "failure.json"
        _write_json(staged, payload)
        os.link(staged, report_path)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    # Les chemins sont vérifiés avant toute écriture, y compris celle du rapport.
    try:
        output, report_path = _check_paths(args)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    report = ValidationReport()
    metadata: dict[str, Any] = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": str(uuid4()),
        **{f"{name}_version": getattr(args, f"{name}_version") for name in ("grid", "method", "dataset")},
        "command_args": vars(args).copy(),
        "software": {name: version(name) for name in ("geopandas", "shapely", "pandas", "pyproj", "pyogrio")},
        "python": sys.version,
        "source_sha256": {},
        "code_sha256": {name: _sha256(Path(__file__).with_name(name)) for name in (
            "validate_inputs.py", "indicateurs_enjeux.py", "run_enjeux.py",
        )},
    }
    metadata["command_args"] = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}
    result = None
    missing_versions = [key for key in ("grid_version", "method_version", "dataset_version") if metadata[key] is None]
    if missing_versions:
        report.add("warning", "versions_missing", "pipeline",
                   "Versions non communiquées : valeurs null conservées.", fields=missing_versions)
    try:
        config = load_config(args.config)
        metadata["config"] = config
        if args.config:
            metadata["source_sha256"][str(args.config)] = _sha256(args.config)
        frames: dict[str, gpd.GeoDataFrame | None] = {}
        id_column = config.get("grid", {}).get("id_column", "maille_id")
        for name in ("grid", "territory", "reservoirs", "corridors"):
            spec = LayerSpec(
                name, CORRIDORS if name == "corridors" else POLYGONS,
                (id_column,) if name == "grid" else (),
                (id_column,) if name == "grid" else (),
                expected_crs=config.get(name, {}).get("expected_crs"),
                allow_empty=name in {"reservoirs", "corridors"},
            )
            frames[name] = read_layer(getattr(args, name), spec, report, layer=getattr(args, f"{name}_layer"))
        evidence: dict[str, CoverageEvidence] = {}
        for name in ("reservoir", "corridor"):
            path = getattr(args, f"{name}_coverage")
            footprint = read_layer(path, LayerSpec(f"{name}s_coverage", POLYGONS), report,
                                   layer=getattr(args, f"{name}_coverage_layer")) if path else None
            evidence[name] = CoverageEvidence(
                confirmed=getattr(args, f"{name}_coverage_confirmed"), footprint=footprint,
                provenance=getattr(args, f"{name}_coverage_provenance"),
                **config.get(f"{name}s", {}).get("coverage", {}),
            )
        spatial_expectation = None
        spatial = config.get("spatial")
        if spatial:
            spatial_path = Path(spatial["plausible_extent"]).resolve()
            if not spatial_path.is_relative_to((PROJECT_ROOT / "data/processed").resolve()):
                raise ValueError("L'emprise plausible M1 doit se trouver dans data/processed/.")
            spatial_frame = read_layer(spatial_path, LayerSpec("plausible_extent", POLYGONS), report,
                                      layer=spatial.get("plausible_extent_layer"))
            if spatial_frame is not None:
                spatial_expectation = SpatialExpectation(spatial_frame, spatial["reference"], spatial["validated_by"],
                                                         spatial.get("margin_m", 0.0))
                metadata["source_sha256"][str(spatial_path)] = _sha256(spatial_path)
        for name in ("grid", "territory", "reservoirs", "corridors", "reservoir_coverage", "corridor_coverage"):
            path = getattr(args, name)
            if path and path.is_file():
                metadata["source_sha256"][str(path)] = _sha256(path)
        if report.ok:
            if id_column != "maille_id":
                if "maille_id" in frames["grid"].columns:
                    raise ValueError("Le mapping d'identifiant écraserait une colonne maille_id existante.")
                frames["grid"] = frames["grid"].rename(columns={id_column: "maille_id"})
            mappings = {}
            for name in ("reservoirs", "corridors"):
                item = config.get(name, {}).get("subframes")
                mappings[name] = SubframeMapping(**item) if item else None
            result = compute_enjeux(
                frames["grid"], frames["territory"], frames["reservoirs"], frames["corridors"],
                reservoir_coverage=evidence["reservoir"], corridor_coverage=evidence["corridor"],
                reservoir_subframes=mappings["reservoirs"], corridor_subframes=mappings["corridors"],
                spatial_expectation=spatial_expectation,
                corridor_sensitivity=CorridorSensitivity(**config["corridors"]["sensitivity"])
                if "sensitivity" in config.get("corridors", {}) else None,
            )
            _merge_reports(report, result.report)
    except InputValidationError as exc:
        _merge_reports(report, exc.report)
    except (OSError, ValueError, TypeError, GEOSException) as exc:
        report.add("error", "pipeline_error", "pipeline", str(exc))

    if result is not None and report.ok:
        try:
            _publish_pair(result, report, metadata, output, report_path)
            print(f"Couple intermédiaire vérifié : {output} ; {report_path}")
            return 0
        except Exception as exc:
            metadata.pop("output_sha256", None)
            report.add("error", "export_failed", "output", "Export du couple GeoPackage/rapport interrompu.", reason=str(exc))
    metadata["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    metadata["status"] = "success" if report.ok else "blocked"
    payload = {**report.as_dict(), "run": metadata}
    try:
        _publish_failure_report(report_path, payload)
    except Exception as exc:
        print(f"Rapport non enregistré : {exc}", file=sys.stderr)
        return 2
    print(f"Rapport : {report_path}")
    if not report.ok:
        for issue in report.issues:
            if issue.severity == "error":
                print(f"[{issue.code}] {issue.layer}: {issue.message}", file=sys.stderr)
        return 2
    print(f"Résultats intermédiaires : {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
