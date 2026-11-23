"""Extension des mailles : calcul M1→M2→fiches publiques dans un JSON séparé.

Rejoue, pour un territoire quelconque, la chaîne existante du lot Caen + 5
communes (préparation M1, moteurs M2 `run_enjeux`/`run_conflicts`, triage
documentaire V1–V4 et pistes R1–R4 de `livrer_caen_et_nord.py`), puis écrit
directement le format public minimisé (`cells.json` + `grid.geojson`).

La base existante n'est jamais modifiée : chaque territoire est écrit dans son
propre dossier (`frontend/public/data/<dossier>/`). Le territoire `perimetre22`
est une grille unique (Caen + 21 communes) : aucun hexagone n'y est coupé entre
deux jeux de données.

Usage, depuis la racine du dépôt :

    python -m analysis.etendre_mailles reference --out data/derived/reference_rejouee
    python -m analysis.etendre_mailles perimetre22 --out frontend/public/data/caen-22com

`reference` recalcule les 101 mailles publiées et sert de contrôle de fidélité
(voir `analysis/comparer_reference.py`).
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import shutil
import sqlite3

import geopandas as gpd
import pandas as pd
from pyproj import Transformer
from shapely import force_2d, normalize, union_all
from shapely.geometry import mapping
from shapely.ops import orient

from analysis import run_conflicts, run_enjeux
from analysis.aggregate_conflicts import _territory_membership, aggregate_conflicts
from analysis.detect_conflicts import SourceFields, detect_route_corridor_conflicts, json_value
from analysis.indicateurs_enjeux import CoverageEvidence
from analysis.preparer_caen_et_nord import dimension

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/caen_et_nord_20261111_v1"
TERRITORIES = {
    "reference": {
        "territory_id": "caen_et_nord_6communes",
        "grid_version": "M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1",
        "dataset_version": "M1-CAEN-ET-NORD-20261111-V1",
        "label": "Caen et cinq communes (référence rejouée)",
        "communes": RAW / "communes_6_source.geojson",
        "clip_to_acquisition": False,
        "limits_note": None,
    },
    "perimetre22": {
        "territory_id": "caen_perimetre_22communes",
        # Même réseau d'hexagones (EPSG:2154, flat-top, origine 0,0, 1 km²) sur un
        # territoire unique : un hexagone n'est jamais coupé entre deux jeux de données.
        "grid_version": "M1-CAEN-22COM-1KM2-FLAT-L93-O0-V1",
        "dataset_version": "M1-CAEN-22COM-20261120-V1",
        "label": "Caen et 21 communes voisines",
        "communes": ROOT / "analysis/territoires/communes_adminexpress_22.geojson",
        "clip_to_acquisition": True,
        "limits_note": None,
    },
}

CARROSSABLES = {"Route à 1 chaussée", "Route à 2 chaussées", "Type autoroutier", "Bretelle", "Rond-point"}
MATRICE_FRAGILE = "Matrice fragile, fortement sensible à la fragmentation"
TRIAGE_COLORS = {"rouge": "#D9534F", "orange": "#F29A48", "jaune": "#E6C65B", "gris": "#89938F"}
LIMITS = ["Indices cartographiques à vérifier — analyse exploratoire", "Une intersection XY n'est pas un obstacle confirmé",
          "La co-présence dans une maille n'établit pas une connexion fonctionnelle", "Inventaires écologiques non exhaustifs et sous-trames de matrices inconnues",
          "Aucune urgence, gravité, efficacité ou prescription de travaux calculée"]
OBSERVATION_SAFE_KEYS = ("nombre_objets_observes", "mesure_observee", "unite", "disponibilite", "completude_ecologique_validee")
ALLOWED = {
    "haies": ["objet_id", "cleabs", "hauteur", "largeur", "precision_planimetrique", "date_modification"],
    "plans_eau": ["objet_id", "cleabs", "nature", "statut", "date_modification"],
    "friches": ["objet_id", "site_id", "site_type", "site_statut", "site_actu_date", "nature"],
    "zones_humides": ["objet_id", "pk_zh", "typo", "diag", "qualite", "leg_simpl", "id_source", "id_echelle"],
    "corridors": ["objet_id", "classe_corridor", "sous_trame", "millesime", "precision_source"],
    "reservoirs": ["objet_id", "sous_trame", "millesime", "precision_source"],
    "routes": ["route_id", "categorie", "importance", "nombre_voies", "largeur_chaussee", "position_sol", "statut_objet", "contexte_urbain", "vitesse_moyenne_vl_source", "precision_planimetrique_m", "millesime", "ouvrage_connu"],
}
MISSING = {
    "R1": ["Sous-trame pertinente et qualité de localisation bilatérale", "Ouvrages, espèces et perméabilité réelle", "Méthode familiale et contrôle des contradictions approuvés"],
    "R2": ["Sous-trame bocagère pertinente", "Analyse de lacune/topologie et état fonctionnel du réseau", "Méthode familiale approuvée"],
    "R3": ["Statut actuel et éligibilité écologique du site", "Relation à une continuité selon une méthode de voisinage approuvée", "Contexte foncier, pollution et méthode familiale approuvée"],
    "R4": ["Inventaire de mares/habitats pertinents et couvertures adaptées", "Analyse de réseau/isolement et contexte hydrologique", "Méthode familiale approuvée"],
}
TOPICS = {"R1": "Perméabilité des franchissements et ouvrages existants", "R2": "État et continuités du réseau de haies",
          "R3": "Statut des sites Cartofriches et relation aux continuités", "R4": "Qualification des plans d'eau et du réseau humide"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def color_rule(obs):
    """Copie conforme de `construire_fiches_66.color_rule` (table V1–V4)."""
    if obs["paires_route_matrice_fragile_en_service_au_sol"] > 0 and obs["reservoir_presence_surface_positive"]:
        return {"niveau": "rouge", "regle": "V1", "titre": "Plusieurs indices cartographiques à vérifier",
                "motif": "Au moins un croisement route en service au sol–matrice SRCE fragile, et une surface de réservoir cartographiée dans cette maille. Leur coexistence ne démontre pas une rupture écologique."}
    if obs["nombre_paires_route_corridor_2d"] > 0:
        return {"niveau": "orange", "regle": "V2", "titre": "Croisement cartographique à examiner",
                "motif": "Au moins un segment routier a une intersection linéaire positive avec une matrice SRCE, sans preuve suffisante pour classer V1."}
    if obs["corridor_presence_surface_positive"] or obs["reservoir_presence_surface_positive"]:
        return {"niveau": "jaune", "regle": "V3", "titre": "Continuité cartographiée à documenter",
                "motif": "Présence d’une matrice SRCE ou d’un réservoir, mais aucun croisement linéaire route–matrice observé dans les couches étudiées. Cela n’établit pas une absence de pression."}
    return {"niveau": "gris", "regle": "V4", "titre": "Information insuffisante",
            "motif": "Les sources mobilisées ne fournissent ni croisement linéaire observé ni surface positive de corridor/réservoir dans la maille ; les inventaires ne sont pas exhaustifs."}


# ---------------------------------------------------------------- territoire

def territory(spec):
    communes = gpd.read_file(spec["communes"]).to_crs(2154)
    communes = communes.loc[communes.geometry.notna()].copy()
    communes["geometry"] = communes.geometry.make_valid().map(lambda g: dimension(g, "polygon"))
    study = union_all(communes.geometry.to_numpy())
    acquisition = json.loads((RAW / "acquisition.json").read_text())
    x0, y0, x1, y1 = acquisition["bbox_epsg2154"]
    from shapely.geometry import box
    bbox = box(x0, y0, x1, y1)
    if spec["clip_to_acquisition"]:
        # Routes, haies, plans d'eau et zones humides n'ont été acquis que sur cette emprise :
        # on ne calcule jamais une maille là où une source manquerait.
        study = dimension(study.intersection(bbox), "polygon")
        communes["geometry"] = communes.geometry.map(lambda g: dimension(g.intersection(study), "polygon"))
        communes = communes.loc[communes.geometry.notna()].copy()
    else:
        assert bbox.covers(study), "Territoire hors emprise d'acquisition"
    reference = None
    return communes.reset_index(drop=True), study, reference


def grid(spec, communes, study):
    conv_spec = importlib.util.spec_from_file_location("convention_m1", ROOT / "tests/fixtures/m1_grid_v61/generate_hex_grid.py")
    convention = importlib.util.module_from_spec(conv_spec)
    conv_spec.loader.exec_module(convention)
    records, _ = _lattice(convention, study, communes)
    for r in records:
        r.update(grid_version=spec["grid_version"], territory_id=spec["territory_id"], dataset_version=spec["dataset_version"])
    cells = gpd.GeoDataFrame(records, crs=2154).sort_values("maille_id").reset_index(drop=True)
    assert cells.maille_id.is_unique
    missing = study.difference(union_all(cells.geometry.to_numpy())).area
    assert missing < 1.0, f"Territoire mal couvert : {missing} m²"
    return cells


def _lattice(convention, study, communes):
    x0, y0, x1, y1 = study.bounds
    records = []
    for col in range(math.floor((x0 - convention.SIDE_M) / convention.X_SPACING_M) - 1,
                     math.ceil((x1 + convention.SIDE_M) / convention.X_SPACING_M) + 2):
        offset = 0.5 if col % 2 else 0.0
        for row in range(math.floor(y0 / convention.Y_SPACING_M - offset) - 2,
                         math.ceil(y1 / convention.Y_SPACING_M - offset) + 3):
            cx, cy = col * convention.X_SPACING_M, (row + offset) * convention.Y_SPACING_M
            full = convention.regular_hexagon(cx, cy)
            clipped = dimension(full.intersection(study), "polygon")
            if clipped is None:
                continue
            communal = [] if communes is None else [
                {"code_insee": c.code_insee, "nom": c.nom_officiel, "area_m2": float(clipped.intersection(c.geometry).area)}
                for c in communes.itertuples() if clipped.intersection(c.geometry).area > 0]
            records.append({"maille_id": convention.cell_id(row, col), "grid_row": row, "grid_col": col,
                            "center_x": cx, "center_y": cy, "full_area_m2": full.area, "area_m2": clipped.area,
                            "pilot_fraction": clipped.area / full.area, "is_boundary": not study.covers(full),
                            "communes": json.dumps(communal, ensure_ascii=False), "geometry": clipped})
    return records, None


# ---------------------------------------------------------------- couches

def raw_sources():
    acquisition = json.loads((RAW / "acquisition.json").read_text())
    sources = acquisition["sources"]
    sources["routes"] = json.loads((RAW / "routes_reprise.json").read_text())
    sources["friches"] = json.loads((RAW / "friches_reprise.json").read_text())
    sources["zones_humides"] = json.loads((RAW / "zones_humides_reprise.json").read_text())
    sources.pop("communes", None)
    return sources


def prepare_layers(study, work):
    """Même harmonisation que `preparer_caen_et_nord.layers`, sur n'importe quelle emprise."""
    processed, refused = {}, []
    for kind, info in raw_sources().items():
        if info.get("status") != "acquired":
            continue
        if "pages" in info:
            feats = [f for p in info["pages"] for f in json.loads((ROOT / p["file"]).read_text())["features"]]
            source = gpd.GeoDataFrame.from_features(feats, crs=2154)
            assert "cleabs" in source
        else:
            vector = ROOT / info["vector_file"]
            meta = gpd.read_file(vector, rows=1)
            bounds = Transformer.from_crs(2154, meta.crs, always_xy=True).transform_bounds(*study.bounds, densify_pts=21)
            # Même règle que la livraison d'origine : reprojection puis refus des géométries invalides, sans réparation.
            source = gpd.read_file(vector, bbox=bounds).to_crs(2154)
        rows = []
        for i, obj in source.iterrows():
            original = obj.geometry
            if original is None or original.is_empty or not original.is_valid:
                refused.append({"layer": kind, "source_index": str(i)})
                continue
            if not original.intersects(study):
                continue
            geom = dimension(original.intersection(study), "line" if kind in {"routes", "haies"} else "polygon")
            if geom is None:
                continue
            attrs = {str(k): json_value(obj[k]) for k in source.columns if k != "geometry"}
            if kind == "routes":
                mapping_ = {"route_id": "cleabs", "categorie": "nature", "importance": "importance", "position_sol": "position_par_rapport_au_sol",
                            "statut_objet": "etat_de_l_objet", "nombre_voies": "nombre_de_voies", "largeur_chaussee": "largeur_de_chaussee",
                            "contexte_urbain": "urbain", "precision_planimetrique_m": "precision_planimetrique", "vitesse_moyenne_vl_source": "vitesse_moyenne_vl",
                            "date_modification": "date_modification", "acces_vehicule_leger": "acces_vehicule_leger"}
                attrs = {k: attrs.get(v) for k, v in mapping_.items()}
                attrs.update(source_id="BDTOPO_ROUTES", ouvrage_connu=None, millesime=None)
            elif kind in {"corridors", "reservoirs"}:
                h = hashlib.sha256(normalize(force_2d(original)).wkb + json.dumps(attrs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20].upper()
                attrs = {"source_id": "TVB_COR_BN" if kind == "corridors" else "TVB_RES_NORM",
                         "objet_id": "TVB-COR-" + h if kind == "corridors" else str(attrs.get("ID_RESV") or "TVB-RES-" + h),
                         "objet_source_id": attrs.get("ID_SRCE"), "sous_trame": attrs.get("MILMAJ_REG"),
                         "millesime": "2014", "precision_source": None,
                         **({"classe_corridor": attrs.get("CLASS_CORR"), "libelle_source": attrs.get("ID_CORR")} if kind == "corridors" else {"nom": attrs.get("NOM_RESV")})}
            else:
                identifier = attrs.get("cleabs") or attrs.get("site_id") or attrs.get("id") or attrs.get("id_friche") or attrs.get("pk_zh")
                if identifier is None:
                    identifier = hashlib.sha256(normalize(force_2d(original)).wkb + json.dumps(attrs, sort_keys=True).encode()).hexdigest()
                attrs["objet_id"] = str(identifier)
                attrs = {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in attrs.items()}
            rows.append({**attrs, "geometry": geom})
        if not rows:
            processed[kind] = None
            continue
        frame = gpd.GeoDataFrame(rows, crs=2154)
        id_col = "route_id" if kind == "routes" else "objet_id"
        if not frame[id_col].is_unique:
            # Objets multipartites livrés en plusieurs enregistrements : identifiant rendu unique, sans fusion.
            frame[id_col] = frame[id_col] + frame.groupby(id_col).cumcount().map(lambda n: "" if n == 0 else f"#{n}")
        assert frame.is_valid.all()
        frame.to_file(work / f"{kind}.gpkg", layer=kind, engine="pyogrio")
        processed[kind] = frame
        print("Couche", kind, len(frame), flush=True)
    return processed, refused


# ---------------------------------------------------------------- M2

def run_m2(spec, cells, study, layers, work, derived):
    cells.drop(columns=["communes"]).to_file(work / "grille.gpkg", layer="mailles", engine="pyogrio")
    gpd.GeoDataFrame({"territory_id": [spec["territory_id"]]}, geometry=[study], crs=2154).to_file(work / "territoire.gpkg", layer="territoire", engine="pyogrio")
    config_enj = {"grid": {"id_column": "maille_id", "expected_crs": "EPSG:2154"}, "territory": {"expected_crs": "EPSG:2154"}}
    for name, sid in (("reservoirs", "TVB_RES_NORM"), ("corridors", "TVB_COR_BN")):
        config_enj[name] = {"expected_crs": "EPSG:2154", "coverage": {"status": "unknown", "source_id": sid, "producer": "DREAL Normandie", "vintage": "2014"}}
    config_rc = {k: dict(config_enj[k]) for k in ("grid", "territory", "corridors")}
    config_rc["corridors"].update(id_column="objet_id", category_column="classe_corridor")
    config_rc["routes"] = {"id_column": "route_id", "category_column": "categorie", "expected_crs": "EPSG:2154",
                           "coverage": {"status": "unknown", "source_id": "BDTOPO_ROUTES", "producer": "IGN"}}
    (derived / "config_enjeux.json").write_text(json.dumps(config_enj))
    (derived / "config_conflits.json").write_text(json.dumps(config_rc))
    paths = {"grid": (work / "grille.gpkg", "mailles"), "territory": (work / "territoire.gpkg", "territoire"),
             "routes": (work / "routes.gpkg", "routes"), "corridors": (work / "corridors.gpkg", "corridors"),
             "reservoirs": (work / "reservoirs.gpkg", "reservoirs")}

    def args(names):
        out = []
        for n in names:
            out += ["--" + n, str(paths[n][0]), "--" + n + "-layer", paths[n][1]]
        return out + ["--grid-version", spec["grid_version"], "--dataset-version", spec["dataset_version"]]

    assert run_enjeux.main(args(("grid", "territory", "reservoirs", "corridors")) + [
        "--config", str(derived / "config_enjeux.json"), "--output", str(derived / "enjeux.gpkg"), "--report", str(derived / "enjeux.validation.json")]) == 0
    status = run_conflicts.main(args(("grid", "territory", "routes", "corridors")) + [
        "--config", str(derived / "config_conflits.json"), "--output-events", str(derived / "evenements.gpkg"),
        "--output-cells", str(derived / "mailles.gpkg"), "--report", str(derived / "strict.validation.json")])
    frames = {n: gpd.read_file(f, layer=l) for n, (f, l) in paths.items()}
    detection = detect_route_corridor_conflicts(frames["routes"], frames["corridors"], frames["territory"],
        route_fields=SourceFields("route_id", "categorie"), corridor_fields=SourceFields("objet_id", "classe_corridor"),
        route_coverage=CoverageEvidence(**config_rc["routes"]["coverage"]), corridor_coverage=CoverageEvidence(**config_rc["corridors"]["coverage"]))
    rejected = {r.conflit_id for r in detection.events.itertuples() if not _territory_membership(r.geometry, study)[0]}
    if status:
        strict = json.loads((derived / "strict.validation.json").read_text())
        assert {e["code"] for e in strict["errors"]} == {"event_outside_territory"}, strict["errors"]
        aggregation = aggregate_conflicts(frames["grid"], frames["territory"],
                                          replace(detection, events=detection.events.loc[~detection.events.conflit_id.isin(rejected)].copy()))
        aggregation.report.add("warning", "events_quarantined", "events", "Événements refusés conservés hors rattachement ; tolérance inchangée.", conflit_ids=sorted(rejected))
        metadata = strict["run"].copy()
        metadata.update(territory_id=spec["territory_id"], processing_scope="accepted_events_only_with_explicit_quarantine")
        run_conflicts.publish_conflict_bundle(aggregation, metadata, {"events": derived / "evenements.gpkg", "cells": derived / "mailles.gpkg", "report": derived / "admis.validation.json"})
    else:
        assert not rejected
    events = gpd.read_file(derived / "evenements.gpkg", layer="conflits_candidates")
    native = gpd.read_file(derived / "mailles.gpkg", layer="mailles_conflits").set_index("maille_id")
    enjeux = gpd.read_file(derived / "enjeux.gpkg", layer="indicateurs_enjeux").set_index("maille_id")
    with sqlite3.connect((derived / "mailles.gpkg").as_uri() + "?mode=ro", uri=True) as db:
        links = pd.read_sql_query("SELECT * FROM liens_mailles_conflits", db)
    quarantine = detection.events.loc[detection.events.conflit_id.isin(rejected)].copy()
    stats = {"evenements_detectes": len(detection.events), "evenements_agreges": len(events),
             "evenements_en_quarantaine": len(quarantine), "liens": len(links),
             "mailles_avec_evenements": int(native.nb_evenements_observes.gt(0).sum())}
    return events, native, enjeux, links, quarantine, stats


# ---------------------------------------------------------------- fiches

def build_cells(spec, cells, layers, events, native, enjeux, links, quarantine):
    rules = json.loads((ROOT / "docs/rules_actions.json").read_text())
    definitions = {r["rule_id"]: r for r in rules["rules"]}
    sources = {k: v for k, v in layers.items() if v is not None}
    event_index = events.set_index("conflit_id")
    links_by_cell = links.groupby("maille_id").conflit_id.apply(sorted).to_dict()
    limitations = LIMITS + ([spec["limits_note"]] if spec["limits_note"] else [])
    bundles, features, colors, leads = {}, [], Counter(), Counter()
    to84 = cells.to_crs("OGC:CRS84")
    for cell, geom84 in zip(cells.itertuples(), to84.geometry):
        mid = cell.maille_id
        local_ids = links_by_cell.get(mid, [])
        observations, objects_by_kind = {}, {}
        for kind, source in sources.items():
            objects, clips = [], []
            for pos in source.sindex.query(cell.geometry, predicate="intersects"):
                row = source.iloc[pos]
                clipped = row.geometry.intersection(cell.geometry)
                value = float(clipped.length if kind in {"haies", "routes"} else clipped.area)
                if value <= 0:
                    continue
                objects.append({k: json_value(row[k]) for k in ALLOWED[kind] if k in row.index})
                clips.append(clipped)
            measure = sum(g.length for g in clips) if kind in {"haies", "routes"} else float(gpd.GeoSeries(clips, crs=2154).union_all().area) if clips else 0.0
            observations[kind] = {"nombre_objets_observes": len(objects), "mesure_observee": measure,
                                  "unite": "m" if kind in {"haies", "routes"} else "m2",
                                  "disponibilite": "observee" if objects else "aucun_objet_observe_absence_non_demontree",
                                  "completude_ecologique_validee": False}
            objects_by_kind[kind] = objects
        for kind in ALLOWED:
            if kind not in observations:
                observations[kind] = {"nombre_objets_observes": None, "mesure_observee": None, "disponibilite": "source_non_utilisable", "completude_ecologique_validee": False}
                objects_by_kind[kind] = []
        pairs, nonconclusive = {}, []
        for cid in local_ids:
            event = event_index.loc[cid]
            local_part = event.geometry.intersection(cell.geometry)
            if event.statut == "non_concluant" or event.territory_relation == "frontiere":
                nonconclusive.append(cid)
                continue
            if local_part.length <= 0 or event.intersection_dimension != "lineaire":
                continue
            info = json.loads(event.observations)
            ra, ca = info["routes"]["attributes"], info["corridors"]["attributes"]
            for rid, coid in json.loads(event.source_pairs):
                pairs.setdefault((rid, coid), {"categorie": ra.get("categorie"), "statut_objet": ra.get("statut_objet"),
                                               "position_sol": ra.get("position_sol"), "classe_corridor": ca.get("classe_corridor")})
        fragile = [p for p in pairs.values() if p["categorie"] in CARROSSABLES and p["statut_objet"] == "En service"
                   and str(p["position_sol"]) == "0" and p["classe_corridor"] == MATRICE_FRAGILE]
        doc_obs = {"nombre_paires_route_corridor_2d": len(pairs), "paires_route_matrice_fragile_en_service_au_sol": len(fragile),
                   "reservoir_presence_surface_positive": observations["reservoirs"]["mesure_observee"] > 0,
                   "corridor_presence_surface_positive": observations["corridors"]["mesure_observee"] > 0}
        ambiguity = bool(nonconclusive and not pairs) or any(v is None for p in pairs.values() for v in p.values())
        ambiguity = ambiguity or bool(not pairs and any(q.intersects(cell.geometry) for q in quarantine.geometry))
        triage = color_rule(doc_obs)
        if ambiguity or any(observations[k]["disponibilite"] == "source_non_utilisable" for k in ("routes", "reservoirs", "corridors")):
            triage = {"niveau": "gris", "regle": "V4", "titre": "Vérification technique nécessaire",
                      "motif": "Éléments seulement non concluants/en quarantaine ou source critique indisponible ; aucun ordre documentaire attribué par défaut."}
        colors[triage["niveau"]] += 1
        obj = objects_by_kind
        mares = [p for p in obj["plans_eau"] if str(p.get("nature", "")).strip().casefold() == "mare"]
        wet = [p for p in obj["reservoirs"] if p.get("sous_trame") == "Milieu humide"]
        active = [p for p in obj["friches"] if p.get("site_statut") in {"friche avec projet", "friche sans projet"}]
        applicable = {"R1": bool(pairs), "R2": bool(obj["haies"] and (obj["corridors"] or obj["reservoirs"])),
                      "R3": bool(active), "R4": bool(mares or obj["plans_eau"] or wet)}
        evidence = {"R1": f"{len(pairs)} paires linéaires documentaires liées aux événements M2 admis",
                    "R2": f"{observations['haies']['nombre_objets_observes']} haies observées, avec matrice ou réservoir dans la maille",
                    "R3": f"{len(active)} sites avec statut source friche, distincts des sites reconvertis",
                    "R4": f"{observations['plans_eau']['nombre_objets_observes']} plans d'eau et {len(wet)} réservoirs de sous-trame humide observés"}
        investigations = []
        for rule in ("R1", "R2", "R3", "R4"):
            leads[rule] += applicable[rule]
            investigations.append({"action_id": definitions[rule]["action_id"], "rule_id": rule, "title": TOPICS[rule],
                "status": "non_evaluable", "lead_status": "a_etudier" if applicable[rule] else "non_qualifiable",
                "evidence": evidence[rule],
                "reason": "Préparer une qualification locale ; aucun déclencheur écologique validé" if applicable[rule] else "Aucune piste locale suffisamment documentée par ces observations",
                "missing_conditions": MISSING[rule], "validation_level": "documentaire_non_valide_ecologiquement", "works_recommended": False})
        enj = enjeux.loc[mid]
        nat = native.loc[mid]
        bundles[mid] = {
            "territory_id": spec["territory_id"], "grid_version": spec["grid_version"], "dataset_version": spec["dataset_version"],
            "maille_id": mid, "municipalities": json.loads(cell.communes), "area_m2": cell.area_m2, "is_boundary": bool(cell.is_boundary),
            "documentary": {"level": triage["niveau"], "rule": triage["regle"], "title": triage["titre"], "reason": triage["motif"],
                            "color": TRIAGE_COLORS[triage["niveau"]], "observations": doc_obs},
            "ecological_priority": {"category": "INDETERMINATE", "scientific_validation": "PENDING", "method_version": None},
            "geometric_observations": {"local_event_count": int(nat.nb_evenements_observes),
                                       "canonical_event_count": int(nat.nb_evenements_exclusifs_observes),
                                       "source_observations": {k: {a: b for a, b in v.items() if a in OBSERVATION_SAFE_KEYS} for k, v in observations.items()},
                                       "enj": {k: json_value(enj[k]) for k in enjeux.columns if k != "geometry"}},
            "investigations": investigations, "limitations": limitations, "validated_recommendations": []}
        features.append({"type": "Feature", "geometry": mapping(orient(force_2d(geom84), sign=1.0)), "properties": {
            "territory_id": spec["territory_id"], "grid_version": spec["grid_version"], "maille_id": mid,
            "area_m2": cell.area_m2, "is_boundary": bool(cell.is_boundary), "pilot_fraction": cell.pilot_fraction,
            "documentary_level": triage["niveau"], "documentary_rule": triage["regle"], "documentary_color": TRIAGE_COLORS[triage["niveau"]],
            "priority_category": "INDETERMINATE", "priority_validation_status": "PENDING"}})
    scope = {"territory_id": spec["territory_id"], "grid_version": spec["grid_version"], "dataset_version": spec["dataset_version"], "method_version": None}
    return bundles, {"type": "FeatureCollection", "scope": scope, "features": features, "decision_version": None}, colors, leads


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("territoire", choices=sorted(TERRITORIES))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    spec = TERRITORIES[args.territoire]
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    # Entrées M2 dans data/processed, sorties dans data/derived (contrat des moteurs existants, ignorés par Git).
    work = ROOT / "data/processed/etendre_mailles" / args.territoire
    derived = ROOT / "data/derived/etendre_mailles" / args.territoire
    for folder in (work, derived):
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
    communes, study, _ = territory(spec)
    cells = grid(spec, communes, study)
    print("Grille", len(cells), "mailles", flush=True)
    layers, refused = prepare_layers(study, work)
    events, native, enjeux, links, quarantine, stats = run_m2(spec, cells, study, layers, work, derived)
    bundles, grid_fc, colors, leads = build_cells(spec, cells, layers, events, native, enjeux, links, quarantine)
    cells_path, grid_path = out / "cells.json", out / "grid.geojson"
    cells_path.write_text(json.dumps(bundles, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    grid_path.write_text(json.dumps(grid_fc, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    lon, lat = Transformer.from_crs(2154, 4326, always_xy=True).transform_bounds(*study.bounds)[0::2], \
        Transformer.from_crs(2154, 4326, always_xy=True).transform_bounds(*study.bounds)[1::2]
    manifest = {"release": f"reconnect-{args.territoire}-v1", "label": spec["label"], **grid_fc["scope"],
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "bounds_wgs84": [[lon[0], lat[0]], [lon[1], lat[1]]],
                "communes": [{"code_insee": c.code_insee, "nom": c.nom_officiel} for c in communes.itertuples()],
                "counts": {"cells": len(bundles), "documentary_levels": dict(colors), "investigation_leads_a_etudier": sum(leads.values()),
                           "leads_by_rule": dict(leads), "investigations": 4 * len(bundles), **stats,
                           "source_features": {k: (0 if v is None else len(v)) for k, v in layers.items()},
                           "source_geometries_refused": len(refused)},
                "method": "Chaîne M1/M2 existante rejouée (run_enjeux, run_conflicts, triage V1–V4, pistes R1–R4) ; aucune règle modifiée",
                "exports": {"cells.json": {"sha256": sha(cells_path)}, "grid.geojson": {"sha256": sha(grid_path)}},
                "scientific_limitations": ["Documentary V1-V4 colors are an exploratory verification order, not validated priorities.",
                                           "Geometric 2D crossings are not confirmed ecological conflicts.",
                                           "Zero observed events does not demonstrate ecological absence."]}
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
