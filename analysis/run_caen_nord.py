"""Exécution interne isolée de la chaîne M2 existante sur la livraison Caen Nord.

Depuis la racine : .venv/bin/python -m analysis.run_caen_nord --archive <zip>
Une reproduction exige un nouvel --run-id. Aucun résultat existant n'est écrasé.
Les moteurs D/S et R1–R4 ne sont pas activés sans configuration approuvée.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess
import sys
import zipfile

import geopandas as gpd
import pandas as pd
from shapely import force_2d, get_coordinates, normalize, union_all

from analysis import run_conflicts, run_enjeux
from analysis.aggregate_conflicts import _territory_membership, aggregate_conflicts
from analysis.detect_conflicts import SourceFields, detect_route_corridor_conflicts, json_value
from analysis.indicateurs_enjeux import CoverageEvidence
from analysis.validate_inputs import (CORRIDORS, POLYGONS, LayerSpec,
    ValidationReport, validate_geodataframe, validate_spatial_coverage)

ROOT = Path(__file__).resolve().parents[1]
TERRITORY = "caen_nord_5communes"
GRID = "M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1"
DATASET = "M1-M2-CAEN-NORD-V1"
ATTRS = ["categorie", "importance", "nombre_voies", "largeur_chaussee",
         "position_sol", "precision_planimetrique_m", "statut_objet",
         "contexte_urbain", "vitesse_moyenne_vl_source", "ouvrage_connu", "millesime"]
OLD = Path("data/derived/m2_diagnostics_20261110_01/situations_geometriques.json")


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(path, payload):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def key(geometry):
    return hashlib.sha256(normalize(force_2d(geometry)).wkb).hexdigest()


def counts(values):
    return dict(sorted(Counter("NULL" if pd.isna(v) else str(v) for v in values).items()))


def scope():
    return dict(territory_id=TERRITORY, grid_version=GRID,
                dataset_version=DATASET, method_version=None)


def signature_quarantine(frame):
    return sorted((e.conflit_id, key(e.geometry), e.source_pairs, e.statut) for e in frame.itertuples())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--run-id", default="m2_caen_nord_20261111_02")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        raise ValueError("run-id : caractères simples uniquement")
    source = args.archive.expanduser().resolve()
    incoming = ROOT / "data/processed" / TERRITORY / DATASET / args.run_id
    out = ROOT / "data/derived" / TERRITORY / args.run_id
    if incoming.exists() or out.exists():
        raise FileExistsError("Choisir un nouveau run-id ; aucun écrasement autorisé")
    # Inventaire avant toute écriture : toutes les données et tous les documents antérieurs.
    baseline = {str(p.relative_to(ROOT)): sha(p) for base in (ROOT / "data", ROOT / "docs")
                for p in sorted(base.rglob("*")) if p.is_file()}
    for p in (incoming, out):
        check = subprocess.run(["git", "check-ignore", str(p.relative_to(ROOT)) + "/probe.json"],
                               cwd=ROOT, capture_output=True)
        if check.returncode != 0:
            raise ValueError("Dossier de données non ignoré par Git")
    archive_hash = sha(source)
    sidecar = source.with_suffix(source.suffix + ".sha256")
    if not sidecar.is_file() or sidecar.read_text().split()[0].lower() != archive_hash:
        raise ValueError("Empreinte de l'archive absente ou discordante")
    incoming.mkdir(parents=True)
    out.mkdir(parents=True)
    write(out / "preservation_avant.json", baseline)
    with zipfile.ZipFile(source) as z:
        for member in z.infolist():
            target = (incoming / member.filename).resolve()
            if not target.is_relative_to(incoming.resolve()):
                raise ValueError("Chemin ZIP hors dossier d'intégration")
        z.extractall(incoming)
    delivery = incoming / "m1_m2_caen_nord_v1"
    manifest = json.loads((delivery / "manifest.json").read_text())
    if manifest["delivery_id"] != DATASET or manifest["grid_version"] != GRID:
        raise ValueError("Livraison ou grille inattendue")
    for item in manifest["outputs"].values():
        if sha(delivery / item["file"]) != item["sha256"].lower():
            raise ValueError("Empreinte GeoPackage discordante")
    specs = {
        "grid": ("grille_caen_nord.gpkg", "grille_caen_nord", POLYGONS, "maille_id", 66),
        "territory": ("territoire_caen_nord.gpkg", "territoire_cible", POLYGONS, None, 1),
        "routes": ("routes.gpkg", "routes", CORRIDORS, "route_id", 8539),
        "corridors": ("corridors.gpkg", "corridors", POLYGONS, "objet_id", 31),
        "reservoirs": ("reservoirs.gpkg", "reservoirs", POLYGONS, "objet_id", 20),
    }
    frames, report, interfaces = {}, ValidationReport(), {}
    for name, (file, layer, types, id_col, n) in specs.items():
        df = gpd.read_file(delivery / file, layer=layer)
        required = (id_col,) if id_col else ()
        validate_geodataframe(df, LayerSpec(name, types, required, required,
                                           expected_crs="EPSG:2154"), report)
        if len(df) != n:
            raise ValueError(f"Effectif inattendu : {name}")
        frames[name] = df
        interfaces[name] = {"file": str((delivery / file).relative_to(ROOT)), "layer": layer,
            "count": len(df), "geometry_types": counts(df.geom_type),
            "dtypes": {c: str(t) for c, t in df.dtypes.items()},
            "null_counts": {c: int(df[c].isna().sum()) for c in df.columns if c != "geometry"}}
    grid, territory, routes, corridors = (frames[n] for n in ("grid", "territory", "routes", "corridors"))
    if set(grid.grid_version) != {GRID}:
        raise ValueError("Versions de grille mélangées")
    for attr in ATTRS:
        if attr not in routes:
            raise ValueError(f"Attribut routier absent : {attr}")
    validate_spatial_coverage(grid, territory, report)
    study = union_all(territory.geometry.to_numpy())
    full = gpd.read_file(delivery / "grille_caen_nord.gpkg", layer="hexagones_complets")
    clipped = full.set_index("maille_id").loc[grid.maille_id].geometry.intersection(study)
    symmetric = [float(a.symmetric_difference(b).area) for a, b in zip(grid.geometry, clipped)]
    # Réutilise le budget de couverture existant, sans changement de tolérance.
    from analysis.validate_inputs import AREA_TOLERANCE_M2
    write(out / "interfaces.validation.json", {**scope(), **report.as_dict(), "interfaces": interfaces,
        "full_vs_clipped_symmetric_difference_max_m2": max(symmetric),
        "clipped_cells": int((grid.pilot_fraction < 1 - 1e-9).sum()),
        "archive_path": str(source), "archive_sha256": archive_hash})
    if max(symmetric) > AREA_TOLERANCE_M2 or not report.ok:
        raise ValueError("Grille découpée non conforme ; consulter le contrôle des interfaces")
    config_enj = {
        "grid": {"id_column": "maille_id", "expected_crs": "EPSG:2154"},
        "territory": {"expected_crs": "EPSG:2154"},
        "reservoirs": {"expected_crs": "EPSG:2154", "coverage": {"status": "unknown",
            "source_id": "TVB_RES_NORM", "producer": "DREAL Normandie", "vintage": "2014"}},
        "corridors": {"expected_crs": "EPSG:2154", "coverage": {"status": "unknown",
            "source_id": "TVB_COR_BN", "producer": "DREAL Normandie", "vintage": "2014"}},
    }
    config_rc = {k: config_enj[k] for k in ("grid", "territory", "corridors")}
    config_rc["corridors"] = {**config_rc["corridors"], "id_column": "objet_id", "category_column": "classe_corridor"}
    # Pas de promotion des champs bruts en preuve : tous restent présents dans observations.
    config_rc["routes"] = {"id_column": "route_id", "category_column": "categorie",
        "expected_crs": "EPSG:2154", "coverage": {"status": "unknown", "source_id": "BDTOPO_ROUTES", "producer": "IGN"}}
    for name, config in (("enjeux", config_enj), ("conflits", config_rc)):
        write(out / f"config_{name}.json", config)
    commands = []
    def execute(module, selected, target, config, result_args, allow_membership_block=False):
        argv = []
        for name in selected:
            file, layer = specs[name][:2]
            argv += ["--" + name, str(delivery / file), "--" + name + "-layer", layer]
        argv += ["--config", str(out / config), "--grid-version", GRID, "--dataset-version", DATASET]
        argv += result_args
        commands.append([sys.executable, "-m", module.__name__, *argv])
        print("Calcul " + target, flush=True)
        if module.main(argv) != 0:
            if allow_membership_block:
                strict = json.loads(Path(argv[argv.index("--report") + 1]).read_text())
                if strict["errors"] and {e["code"] for e in strict["errors"]} == {"event_outside_territory"}:
                    return strict
            write(out / "commandes.json", commands)
            raise RuntimeError("Chaîne bloquée : " + target)
        return None
    execute(run_enjeux, ("grid", "territory", "reservoirs", "corridors"), "ENJ", "config_enjeux.json",
        ["--output", str(out / "enjeux.gpkg"), "--report", str(out / "enjeux.validation.json")])
    raw_events = None
    quarantined = None
    for prefix in ("", "reproduction_"):
        strict = execute(run_conflicts, ("grid", "territory", "routes", "corridors"), prefix + "conflits", "config_conflits.json",
            ["--output-events", str(out / (prefix + "evenements.gpkg")), "--output-cells", str(out / (prefix + "mailles.gpkg")),
             "--report", str(out / (prefix + "conflits_strict.validation.json"))], allow_membership_block=True)
        if strict is None:
            raise RuntimeError("Ce profil d'exécution documente le blocage de frontière connu ; réviser explicitement le profil si la chaîne stricte réussit")
        # Les règles de frontière restent strictes : isoler les refus, sans mutation ni promotion.
        detection = detect_route_corridor_conflicts(routes, corridors, territory,
            route_fields=SourceFields(id_column="route_id", category_column="categorie"),
            corridor_fields=SourceFields(id_column="objet_id", category_column="classe_corridor"),
            route_coverage=CoverageEvidence(**config_rc["routes"]["coverage"]),
            corridor_coverage=CoverageEvidence(**config_rc["corridors"]["coverage"]))
        rejected = {cid for error in strict["errors"] for cid in error["details"]["conflit_ids"]}
        actual = {e.conflit_id for e in detection.events.itertuples() if not _territory_membership(e.geometry, study)[0]}
        if rejected != actual:
            raise ValueError("Refus strict et diagnostic de quarantaine discordants")
        quarantined_current = detection.events.loc[detection.events.conflit_id.isin(rejected)].copy()
        accepted = detection.events.loc[~detection.events.conflit_id.isin(rejected)].copy()
        aggregation = aggregate_conflicts(grid, territory, replace(detection, events=accepted))
        aggregation.report.add("warning", "events_quarantined", "events",
            "Lot partiel : événements refusés par le contrôle strict conservés séparément, sans rattachement canonique.",
            conflit_ids=sorted(rejected), strict_report=prefix + "conflits_strict.validation.json",
            detected_count=len(detection.events), aggregated_count=len(accepted))
        metadata = strict["run"].copy()
        metadata.update(scope())
        metadata["processing_scope"] = "accepted_events_only_with_explicit_quarantine"
        metadata["strict_run_status"] = "blocked"
        metadata["quarantined_conflit_ids"] = sorted(rejected)
        run_conflicts.publish_conflict_bundle(aggregation, metadata, {
            "events": out / (prefix + "evenements.gpkg"), "cells": out / (prefix + "mailles.gpkg"),
            "report": out / (prefix + "conflits.validation.json")})
        quarantined_current.to_file(out / (prefix + "quarantaine.gpkg"), layer="evenements_refuses", driver="GPKG", engine="pyogrio")
        if not prefix:
            raw_events, quarantined = detection.events.copy(), quarantined_current
        elif signature_quarantine(quarantined) != signature_quarantine(quarantined_current):
            raise ValueError("Quarantaine non reproductible")
    write(out / "commandes.json", commands)
    run_enjeux.verify_artifact_pair(out / "enjeux.gpkg", out / "enjeux.validation.json")
    for prefix in ("", "reproduction_"):
        run_conflicts.verify_conflict_bundle(out / (prefix + "evenements.gpkg"), out / (prefix + "mailles.gpkg"),
                                            out / (prefix + "conflits.validation.json"))
    events = gpd.read_file(out / "evenements.gpkg", layer="conflits_candidates")
    cells = gpd.read_file(out / "mailles.gpkg", layer="mailles_conflits")
    enjeux = gpd.read_file(out / "enjeux.gpkg", layer="indicateurs_enjeux")
    with sqlite3.connect(f"{(out / 'mailles.gpkg').as_uri()}?mode=ro", uri=True) as db:
        links = pd.read_sql_query("SELECT * FROM liens_mailles_conflits", db)
    def signature(df, id_col):
        rows = []
        for _, row in df.sort_values(id_col).iterrows():
            rows.append({c: key(row[c]) if c == "geometry" else json_value(row[c]) for c in df.columns})
        return hashlib.sha256(json.dumps(rows, sort_keys=True, allow_nan=False).encode()).hexdigest()
    repeat_checks = {}
    for name, frame, layer, id_col in (("evenements", events, "conflits_candidates", "conflit_id"),
                                     ("mailles", cells, "mailles_conflits", "maille_id")):
        other = gpd.read_file(out / f"reproduction_{name}.gpkg", layer=layer)
        repeat_checks[name] = signature(frame, id_col) == signature(other, id_col)
    with sqlite3.connect(f"{(out / 'reproduction_mailles.gpkg').as_uri()}?mode=ro", uri=True) as db:
        other_links = pd.read_sql_query("SELECT * FROM liens_mailles_conflits ORDER BY conflit_id, maille_id", db)
    repeat_checks["liens"] = links.sort_values(["conflit_id", "maille_id"]).reset_index(drop=True).equals(other_links)
    if not all(repeat_checks.values()):
        raise ValueError("Reproduction discordante")
    print("Comparaison sans attributs routiers enrichis", flush=True)
    minimal = routes[[c for c in ("route_id", "source_id", "categorie", "ouvrage_connu", "millesime", "geometry")
                      if c in routes]].copy()
    ablation = detect_route_corridor_conflicts(minimal, corridors, territory,
        route_fields=SourceFields(id_column="route_id", category_column="categorie"),
        corridor_fields=SourceFields(id_column="objet_id", category_column="classe_corridor"),
        route_coverage=CoverageEvidence(**config_rc["routes"]["coverage"]),
        corridor_coverage=CoverageEvidence(**config_rc["corridors"]["coverage"]))
    def geometric_signature(frame):
        return sorted((key(e.geometry), e.source_pairs, e.statut, e.intersection_relation, e.territory_relation)
                      for e in frame.itertuples())
    ablation_check = {"attributs_conserves": list(minimal.columns),
        "evenements_sans_enrichissement": len(ablation.events),
        "memes_geometries_paires_statuts_relations": geometric_signature(raw_events) == geometric_signature(ablation.events),
        "comparaison_conflit_id": "non pertinente : les identifiants dépendent aussi des attributs sources",
        "validation": ablation.report.as_dict()}
    write(out / "ablation_attributs.json", {**scope(), **ablation_check})
    # Contrôle géométrique exploratoire calculé indépendamment du découpage des événements.
    raw_pairs = {(routes.iloc[i].route_id, corridor.objet_id)
                 for corridor in corridors.itertuples() for i in routes.sindex.query(corridor.geometry, predicate="intersects")}
    detected_pairs = {tuple(p) for value in raw_events.source_pairs for p in json.loads(value)}
    aggregated_pairs = {tuple(p) for value in events.source_pairs for p in json.loads(value)}
    groups = defaultdict(list)
    for row in events.itertuples():
        groups[key(row.geometry)].append(row.conflit_id)
    roads = routes.set_index("route_id")
    event_rows = []
    event_index = events.set_index("conflit_id")
    quarantine_ids = set(quarantined.conflit_id)
    for e in raw_events.itertuples():
        ids = json.loads(e.source_ids)
        for route_id in ids["routes"]:
            event_rows.append({**scope(), "conflit_id": e.conflit_id, "route_id": route_id,
                "corridor_ids": ids["corridors"], "statut": e.statut,
                "intersection_relation": e.intersection_relation,
                "maille_ids": [] if e.conflit_id in quarantine_ids else json.loads(event_index.loc[e.conflit_id, "maille_ids"]),
                "traitement": "quarantaine" if e.conflit_id in quarantine_ids else "agrege",
                **{attr: json_value(roads.loc[route_id, attr]) for attr in ATTRS}})
    attrs = pd.DataFrame(event_rows)
    associated = routes.loc[routes.route_id.isin(attrs.route_id)].copy()
    distributions = {}
    for attr in ATTRS:
        distributions[attr] = {"routes_livrees": counts(routes[attr]),
            "routes_concernees_distinctes": counts(associated[attr]),
            "relations_evenement_route": counts(attrs[attr]),
            "evenements": {value: int(part.conflit_id.nunique())
                for value, part in attrs.groupby(attrs[attr].map(lambda x: "NULL" if pd.isna(x) else str(x)))},
            "evenements_agreges": {value: int(part.loc[part.traitement.eq("agrege"), "conflit_id"].nunique())
                for value, part in attrs.groupby(attrs[attr].map(lambda x: "NULL" if pd.isna(x) else str(x)))}}
    cross = [{"statut_objet": str(status), "position_sol": json_value(position),
              "evenements": int(part.conflit_id.nunique()), "routes_distinctes": int(part.route_id.nunique()),
              "evenements_agreges": int(part.loc[part.traitement.eq("agrege"), "conflit_id"].nunique())}
             for (status, position), part in attrs.groupby(["statut_objet", "position_sol"], dropna=False)]
    comparisons = []
    for e in events.itertuples():
        inside, numerical = _territory_membership(e.geometry, study)
        if not inside:
            raise ValueError("Événement hors territoire")
        if numerical:
            comparisons.append({"conflit_id": e.conflit_id, **numerical})
    summary = {**scope(), "mailles": len(cells), "evenements": len(events), "liens": len(links),
        "evenements_detectes": len(raw_events), "evenements_agreges": len(events), "evenements_quarantaine": len(quarantined),
        "statuts_tous_detectes": counts(raw_events.statut), "paires_agregees": len(aggregated_pairs),
        "proprietaires_canoniques": int(links.canonical_owner.sum()),
        "mailles_avec_observations": int(cells.nb_evenements_observes.gt(0).sum()),
        "mailles_sans_evenement_observe": int(cells.nb_evenements_observes.eq(0).sum()),
        "mailles_sans_observation_concluante": int(cells.nb_croisement_detecte_observes.eq(0).sum()),
        "mailles_avec_croisement_detecte": int(cells.nb_croisement_detecte_observes.gt(0).sum()),
        "paires_geometriques_exploratoires": len(raw_pairs),
        "routes_geometriques_exploratoires": len({p[0] for p in raw_pairs}),
        "controle_exploratoire_independant": {"paires_annoncees": 3096, "routes_annoncees": 2378,
            "paires_egales": len(raw_pairs) == 3096, "routes_egales": len({p[0] for p in raw_pairs}) == 2378},
        "paires_detectees": len(detected_pairs), "routes_detectees": len(associated),
        "paires_uniquement_exploratoires": sorted(raw_pairs - detected_pairs),
        "paires_uniquement_detecteur": sorted(detected_pairs - raw_pairs),
        "geometries_xy_exactes": len(groups), "groupes_geometries_partagees": sum(len(v) > 1 for v in groups.values()),
        "evenements_dans_groupes_partages": sum(len(v) for v in groups.values() if len(v) > 1),
        "dimensions": counts(events.intersection_dimension), "statuts": counts(events.statut),
        "relations_geometriques": counts(events.intersection_relation),
        "relations_territoire": counts(events.territory_relation), "relations_mailles": counts(links.relation_spatiale),
        "residus_numeriques": int(events.numeric_residue.sum()),
        "enjeux": {"enj_01_valides": int(enjeux.enj_01_pct.notna().sum()),
            "reservoir_aire_positive": int(enjeux.reservoir_observed_area_m2.gt(0).sum()),
            "enj_02_presence": int(enjeux.enj_02_presence.fillna(False).sum()),
            "enj_02_inconnus": int(enjeux.enj_02_presence.isna().sum()),
            "enj_01_statuts": counts(enjeux.enj_01_status), "enj_02_statuts": counts(enjeux.enj_02_status)},
        "reproduction_identique": repeat_checks, "appartenance_numerique": comparisons,
        "ablation_memes_geometries_paires_statuts_relations": ablation_check["memes_geometries_paires_statuts_relations"],
        "moteurs_D_S_R1_R4_executes": False, "priorites_justifiables": 0,
        "priorite": {"etat": "non_calculee", "valeur": None},
        "enjeu_classe": "inconnu", "actions": {"etat": "non_calculees", "action_ids": []}}
    write(out / "resultats.json", summary)
    quarantine_metrics = []
    for e in quarantined.itertuples():
        g = e.geometry
        xy = get_coordinates(g)
        delta = math.hypot(max(math.ulp(float(v)) for v in xy[:, 0]), max(math.ulp(float(v)) for v in xy[:, 1]))
        quarantine_metrics.append({**scope(), "conflit_id": e.conflit_id,
            "source_ids": json.loads(e.source_ids), "geometry_wkb_hex": g.wkb_hex,
            "outside_length_m": float(g.difference(study).length),
            "hausdorff_m": float(g.hausdorff_distance(g.intersection(study))),
            "coordinate_ulp_diagonal_m": delta, "relate": g.relate(study),
            "mailles_intersectees_exploratoires": grid.loc[grid.intersects(g), "maille_id"].tolist(),
            "motif": "event_outside_territory ; budget ULP inchangé, aucun propriétaire attribué"})
    write(out / "quarantaine.validation.json", {**scope(), "evenements": quarantine_metrics,
        "validation_humaine_necessaire": True, "geometries_modifiees": False,
        "strict_reports_preserved": True, "quarantine_reproduction_identical": True})
    write(out / "attributs_routiers.json", {**scope(), "unites": "événements distincts et objets routiers, sans poids de danger",
        "distributions": distributions, "statut_position": cross})
    write(out / "evenements_contexte.json", {**scope(), "evenements_routes": event_rows,
        "groupes_geometries_xy": [{"sha256": k, "conflit_ids": v} for k, v in sorted(groups.items())]})
    # Sélection reproductible de cas, sans classement écologique ni seuil ajouté.
    cases = []
    masks = {f"service_position_{v}": attrs.statut_objet.eq("En service") & attrs.position_sol.eq(v)
             for v in sorted(attrs.position_sol.dropna().unique())}
    masks["autres_statuts"] = ~attrs.statut_objet.eq("En service")
    masks["voies_largeur_manquantes"] = attrs.nombre_voies.isna() | attrs.largeur_chaussee.isna()
    municipalities = gpd.read_file(delivery / "territoire_caen_nord.gpkg", layer="communes_cibles")
    for label, mask in masks.items():
        subset = attrs.loc[mask & attrs.traitement.eq("agrege")].sort_values(["conflit_id", "route_id"]).drop_duplicates("conflit_id")
        for _, row in subset.head(3).iterrows():
            event = event_index.loc[row.conflit_id]
            cases.append({**{c: json_value(row[c]) for c in row.index}, "groupe_selection": label,
                "critere": "trois premiers conflit_id triés du groupe, sans rang écologique",
                "xy_l93_point_sur_evenement": list(event.geometry.representative_point().coords)[0],
                "geometrie_xy_sha256": key(event.geometry),
                "communes_intersectees": [{c: json_value(r[c]) for c in municipalities.columns if c != "geometry"}
                    for _, r in municipalities.loc[municipalities.intersects(event.geometry)].iterrows()],
                "validation_requise": ["Sous-trame et espèces pertinentes", "Localisation et précision bilatérales",
                    "Situation actuelle du franchissement, ouvrages et usages", "Méthode d'enjeu et qualification approuvées"]})
    write(out / "cas_revue_expert.json", {**scope(), "cas": cases,
        "mailles_sans_observation": cells.loc[cells.nb_evenements_observes.eq(0), "maille_id"].tolist()})
    # Paquet distinct pour ingestion interne M4 ; les lots natifs vérifiés restent intacts.
    internal = out / "m4_interne.gpkg"
    for frame, layer in ((events, "evenements"), (cells, "mailles"), (enjeux, "enjeux"), (quarantined, "quarantaine")):
        scoped = frame.copy()
        for k, v in scope().items():
            scoped[k] = v
        if layer == "mailles":
            scoped["priorite_etat"] = "non_calculee"
            scoped["priorite_valeur"] = None
            scoped["enjeu_classe"] = "inconnu"
            scoped["actions_etat"] = "non_calculees"
        scoped.to_file(internal, layer=layer, driver="GPKG", engine="pyogrio")
    with sqlite3.connect(internal) as db:
        scoped_links = links.assign(**scope())
        scoped_links.to_sql("liens_mailles_evenements", db, index=False, if_exists="fail")
        db.execute("CREATE UNIQUE INDEX liens_scopes ON liens_mailles_evenements (territory_id, grid_version, dataset_version, conflit_id, maille_id)")
        db.execute("INSERT INTO gpkg_contents (table_name, data_type, identifier, description, last_change) VALUES ('liens_mailles_evenements', 'attributes', 'liens_mailles_evenements', 'Relations internes avec identité territoriale', strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))")
    for layer in ("evenements", "mailles", "enjeux", "quarantaine"):
        restored = gpd.read_file(internal, layer=layer)
        assert set(restored.territory_id) == {TERRITORY} and set(restored.grid_version) == {GRID}
        assert set(restored.dataset_version) == {DATASET}
    # Conserve les versions exactes des programmes nécessaires à une reproduction future.
    code = out / "code" / "analysis"
    code.mkdir(parents=True)
    for p in (ROOT / "analysis").glob("*.py"):
        shutil.copyfile(p, code / p.name)
    shutil.copyfile(ROOT / "analysis/requirements.txt", code / "requirements.txt")
    lock = subprocess.check_output([sys.executable, "-m", "pip", "freeze"], text=True)
    (out / "requirements.lock.txt").write_text(lock)
    previous_grid = ROOT / "data/derived/m2_frontiere_20261109_01/data/processed/grille_pilote.gpkg"
    overlap = None
    if previous_grid.exists():
        old_grid = gpd.read_file(previous_grid, layer="grille_pilote")
        overlap = sorted(set(old_grid.maille_id) & set(grid.maille_id))
    changed = [p for p, old_hash in baseline.items() if not (ROOT / p).is_file() or sha(ROOT / p) != old_hash]
    if changed:
        raise ValueError("Travaux antérieurs modifiés : " + repr(changed))
    write(out / "preservation.validation.json", {"ok": True, "files_checked": len(baseline),
        "changed": changed, "shared_old_grid_ids": overlap,
        "identity_key": ["territory_id", "grid_version", "dataset_version", "maille_id"]})
    write(out / "manifest_interne.json", {**scope(), "run_id": args.run_id,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "archive": {"path": str(source), "sha256": archive_hash},
        "sources": {str(p.relative_to(ROOT)): sha(p) for p in sorted(delivery.iterdir()) if p.is_file()},
        "outputs": {str(p.relative_to(ROOT)): sha(p) for p in sorted(out.rglob("*")) if p.is_file()},
        "baseline_reference": str(OLD), "baseline_sha256": sha(ROOT / OLD),
        "software": {p: importlib.metadata.version(p) for p in ("geopandas", "shapely", "pandas", "numpy", "pyproj", "pyogrio")},
        "python": sys.version, "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "public_export": False, "scientific_approval": None,
        "strict_pipeline_status": "blocked", "internal_pipeline_status": "partial_with_quarantine",
        "identity_key": ["territory_id", "grid_version", "dataset_version", "maille_id"],
        "limites": ["Contrats publics inchangés", "D/S et R1–R4 non exécutés", "Aucune couleur écologique calculée",
            "Les attributs bruts ne sont pas des preuves de trafic ou de franchissabilité"]})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
