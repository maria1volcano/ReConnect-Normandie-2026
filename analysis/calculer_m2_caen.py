"""Chaîne M2 existante appliquée au nouveau territoire, refus conservés en quarantaine."""
from __future__ import annotations
from dataclasses import replace
import json
import math
import sqlite3

import geopandas as gpd
from shapely import get_coordinates, union_all

from analysis import run_enjeux, run_conflicts
from analysis.aggregate_conflicts import aggregate_conflicts, _territory_membership
from analysis.detect_conflicts import detect_route_corridor_conflicts, SourceFields
from analysis.indicateurs_enjeux import CoverageEvidence
from analysis.preparer_caen_et_nord import ROOT, PROC, OUT, GRID, TERRITORY, DATASET, sha, write


def main():
    target = OUT / "calculs_m2"
    target.mkdir(exist_ok=False)
    config_enj = {"grid": {"id_column": "maille_id", "expected_crs": "EPSG:2154"},
                  "territory": {"expected_crs": "EPSG:2154"}}
    for name, sid in (("reservoirs", "TVB_RES_NORM"), ("corridors", "TVB_COR_BN")):
        config_enj[name] = {"expected_crs": "EPSG:2154", "coverage": {"status": "unknown", "source_id": sid, "producer": "DREAL Normandie", "vintage": "2014"}}
    config_rc = {k: config_enj[k].copy() for k in ("grid", "territory", "corridors")}
    config_rc["corridors"].update(id_column="objet_id", category_column="classe_corridor")
    config_rc["routes"] = {"id_column": "route_id", "category_column": "categorie", "expected_crs": "EPSG:2154",
                           "coverage": {"status": "unknown", "source_id": "BDTOPO_ROUTES", "producer": "IGN"}}
    write(target / "config_enjeux.json", config_enj);write(target / "config_conflits.json", config_rc)
    paths = {"grid": (PROC / "grille.gpkg", "mailles"), "territory": (PROC / "territoire.gpkg", "territoire"),
             "routes": (PROC / "routes.gpkg", "routes"), "corridors": (PROC / "corridors.gpkg", "corridors"),
             "reservoirs": (PROC / "reservoirs.gpkg", "reservoirs")}
    def args(names):
        result = []
        for name in names:
            result += ["--" + name, str(paths[name][0]), "--" + name + "-layer", paths[name][1]]
        return result + ["--grid-version", GRID, "--dataset-version", DATASET]
    commands = []
    enj_args = args(("grid", "territory", "reservoirs", "corridors")) + ["--config", str(target / "config_enjeux.json"), "--output", str(target / "enjeux.gpkg"), "--report", str(target / "enjeux.validation.json")]
    commands.append(["analysis.run_enjeux", *enj_args])
    assert run_enjeux.main(enj_args) == 0
    rc_args = args(("grid", "territory", "routes", "corridors")) + ["--config", str(target / "config_conflits.json"),
        "--output-events", str(target / "evenements.gpkg"), "--output-cells", str(target / "mailles.gpkg"), "--report", str(target / "strict.validation.json")]
    commands.append(["analysis.run_conflicts", *rc_args])
    status = run_conflicts.main(rc_args)
    frames = {name: gpd.read_file(file, layer=layer) for name, (file, layer) in paths.items()}
    detection = detect_route_corridor_conflicts(frames["routes"], frames["corridors"], frames["territory"],
        route_fields=SourceFields("route_id", "categorie"), corridor_fields=SourceFields("objet_id", "classe_corridor"),
        route_coverage=CoverageEvidence(**config_rc["routes"]["coverage"]), corridor_coverage=CoverageEvidence(**config_rc["corridors"]["coverage"]))
    raw_events = detection.events.copy()
    study = union_all(frames["territory"].geometry.to_numpy())
    rejected = {row.conflit_id for row in raw_events.itertuples() if not _territory_membership(row.geometry, study)[0]}
    strict = json.loads((target / "strict.validation.json").read_text())
    if status:
        assert strict["errors"] and {e["code"] for e in strict["errors"]} == {"event_outside_territory"}, strict["errors"]
        assert rejected == {cid for err in strict["errors"] for cid in err["details"]["conflit_ids"]}
        aggregation = aggregate_conflicts(frames["grid"], frames["territory"], replace(detection, events=detection.events.loc[~detection.events.conflit_id.isin(rejected)].copy()))
        aggregation.report.add("warning", "events_quarantined", "events", "Événements refusés conservés hors rattachement ; tolérance inchangée.", conflit_ids=sorted(rejected))
        metadata = strict["run"].copy();metadata.update(territory_id=TERRITORY, processing_scope="accepted_events_only_with_explicit_quarantine")
        run_conflicts.publish_conflict_bundle(aggregation, metadata, {"events": target / "evenements.gpkg", "cells": target / "mailles.gpkg", "report": target / "admis.validation.json"})
        report = target / "admis.validation.json"
    else:
        assert not rejected
        report = target / "strict.validation.json"
    run_enjeux.verify_artifact_pair(target / "enjeux.gpkg", target / "enjeux.validation.json")
    run_conflicts.verify_conflict_bundle(target / "evenements.gpkg", target / "mailles.gpkg", report)
    accepted = gpd.read_file(target / "evenements.gpkg", layer="conflits_candidates")
    raw_events.to_file(target / "evenements_detectes.gpkg", layer="evenements_detectes", engine="pyogrio")
    quarantine = raw_events.loc[raw_events.conflit_id.isin(rejected)].copy()
    if len(quarantine):
        quarantine.to_file(target / "quarantaine.gpkg", layer="quarantaine", engine="pyogrio")
    measures = []
    for row in quarantine.itertuples():
        xy = get_coordinates(row.geometry)
        delta = math.hypot(max(math.ulp(float(v)) for v in xy[:, 0]), max(math.ulp(float(v)) for v in xy[:, 1]))
        measures.append({"conflit_id": row.conflit_id, "source_pairs": json.loads(row.source_pairs),
            "wkb_hex": row.geometry.wkb_hex, "outside_length_m": row.geometry.difference(study).length,
            "hausdorff_m": row.geometry.hausdorff_distance(row.geometry.intersection(study)), "delta_m": delta,
            "de9im": row.geometry.relate(study), "reason": "event_outside_territory"})
    write(target / "quarantaine.validation.json", {"count": len(quarantine), "events": measures, "geometry_changed": False, "tolerance_changed": False})
    with sqlite3.connect((target / "mailles.gpkg").as_uri() + "?mode=ro", uri=True) as db:
        links = db.execute("SELECT conflit_id,maille_id,relation_spatiale,canonical_owner FROM liens_mailles_conflits ORDER BY conflit_id,maille_id").fetchall()
    # Un second passage API vérifie les objets et rattachements sans écraser le lot.
    repeat = aggregate_conflicts(frames["grid"], frames["territory"], replace(detection, events=detection.events.loc[~detection.events.conflit_id.isin(rejected)].copy()))
    assert sorted(zip(accepted.conflit_id, accepted.geometry.map(lambda g: g.wkb_hex))) == sorted(zip(repeat.events.conflit_id, repeat.events.geometry.map(lambda g: g.wkb_hex)))
    assert links == list(repeat.links.sort_values(["conflit_id", "maille_id"]).itertuples(index=False, name=None))
    cells = repeat.cells
    result = {"territory_id": TERRITORY, "grid_version": GRID, "dataset_version": DATASET, "method_version": None,
        "mailles": len(cells), "evenements_detectes": len(raw_events), "evenements_agreges": len(accepted),
        "evenements_en_quarantaine": len(quarantine), "paires_sources": len({tuple(p) for value in raw_events.source_pairs for p in json.loads(value)}),
        "routes_concernees": len({r for value in raw_events.source_pairs for r, _ in json.loads(value)}),
        "liens": len(links), "proprietaires": int(repeat.links.canonical_owner.sum()),
        "mailles_avec_evenements": int(cells.nb_evenements_observes.gt(0).sum()),
        "mailles_sans_evenement": int(cells.nb_evenements_observes.eq(0).sum()),
        "active_report": str(report.relative_to(ROOT)), "strict_success": status == 0,
        "repeat_geometry_and_links_identical": True, "original_rules_unchanged": True}
    write(target / "resultats.json", result);write(target / "commandes.json", commands)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
