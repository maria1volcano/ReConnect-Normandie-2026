"""Grille M1 commune entière de Caen + cinq communes, sources et versions isolées."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import geopandas as gpd
import pandas as pd
from shapely import force_2d, normalize, union_all
from shapely.geometry import MultiLineString, MultiPolygon

from analysis.detect_conflicts import json_value
from analysis.validate_inputs import ValidationReport, validate_spatial_coverage, AREA_TOLERANCE_M2

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data/raw/caen_et_nord_20261111_v1"
PROC = ROOT / "data/processed/caen_et_nord/M1_CAEN6_20261111_V1"
OUT = ROOT / "data/derived/caen_et_nord_20261111_01"
GRID = "M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1"
TERRITORY = "caen_et_nord_6communes"
DATASET = "M1-CAEN-ET-NORD-20261111-V1"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, payload):
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write("\n")


def dimension(geometry, kind):
    found, stack = [], [geometry]
    while stack:
        g = stack.pop()
        if g.is_empty:
            continue
        if g.geom_type.startswith("Multi") or g.geom_type == "GeometryCollection":
            stack.extend(g.geoms)
        elif (kind == "line" and g.geom_type == "LineString" and g.length > 0) or (kind == "polygon" and g.geom_type == "Polygon" and g.area > 0):
            found.append(g)
    if not found:
        return None
    return MultiLineString(found) if kind == "line" else MultiPolygon(found)


def grid():
    PROC.mkdir(parents=True, exist_ok=False)
    communes = gpd.read_file(RAW / "communes_6_source.geojson")
    assert communes.crs.to_epsg() == 2154 and communes.is_valid.all()
    study = union_all(communes.geometry.to_numpy())
    caen = communes.loc[communes.code_insee.eq("14118")].geometry.iloc[0]
    territory = gpd.GeoDataFrame({"territory_id": [TERRITORY], "nom": ["Caen et cinq communes du nord"], "dataset_version": [DATASET]}, geometry=[study], crs=2154)
    territory.to_file(PROC / "territoire.gpkg", layer="territoire", engine="pyogrio")
    communes.to_file(PROC / "territoire.gpkg", layer="communes", engine="pyogrio")
    gpd.GeoDataFrame({"territory_id": ["CAEN_COMMUNE"], "code_insee": ["14118"]}, geometry=[caen], crs=2154).to_file(PROC / "territoire.gpkg", layer="caen_commune", engine="pyogrio")
    spec = importlib.util.spec_from_file_location("convention_m1", ROOT / "tests/fixtures/m1_grid_v61/generate_hex_grid.py")
    convention = importlib.util.module_from_spec(spec); spec.loader.exec_module(convention)
    x0, y0, x1, y1 = study.bounds
    records, full_records = [], []
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
            communal = [{"code_insee": c.code_insee, "nom": c.nom_officiel,
                         "area_m2": float(clipped.intersection(c.geometry).area)}
                        for c in communes.itertuples() if clipped.intersection(c.geometry).area > 0]
            attrs = {"maille_id": convention.cell_id(row, col), "grid_version": GRID, "territory_id": TERRITORY,
                "dataset_version": DATASET, "grid_row": row, "grid_col": col, "center_x": cx, "center_y": cy,
                "full_area_m2": full.area, "clipped_area_m2": clipped.area, "area_m2": clipped.area,
                "pilot_fraction": clipped.area / full.area, "is_boundary": not study.covers(full),
                "caen_area_m2": float(clipped.intersection(caen).area), "communes": json.dumps(communal, ensure_ascii=False)}
            records.append({**attrs, "geometry": clipped});full_records.append({**attrs, "geometry": full})
    cells = gpd.GeoDataFrame(records, crs=2154).sort_values("maille_id").reset_index(drop=True)
    full = gpd.GeoDataFrame(full_records, crs=2154).sort_values("maille_id").reset_index(drop=True)
    report = ValidationReport();validate_spatial_coverage(cells, territory, report)
    assert report.ok, report.as_dict()
    covered = union_all(cells.geometry.to_numpy())
    missing = caen.difference(covered).area
    assert missing <= AREA_TOLERANCE_M2
    old = gpd.read_file(ROOT / "data/processed/caen_nord_5communes/M1-M2-CAEN-NORD-V1/m2_caen_nord_20261111_02/m1_m2_caen_nord_v1/grille_caen_nord.gpkg", layer="hexagones_complets").set_index("maille_id")
    shared = cells.loc[cells.maille_id.isin(old.index)]
    assert all(c.center_x == old.loc[c.maille_id].center_x and c.center_y == old.loc[c.maille_id].center_y for c in shared.itertuples())
    cells.to_file(PROC / "grille.gpkg", layer="mailles", engine="pyogrio")
    full.to_file(PROC / "grille.gpkg", layer="hexagones_complets", engine="pyogrio")
    write(OUT / "grille.validation.json", {**report.as_dict(), "grid_version": GRID, "territory_id": TERRITORY,
        "dataset_version": DATASET, "mailles": len(cells), "caen_commune_area_m2": caen.area,
        "territory_area_m2": study.area, "caen_missing_area_m2": missing,
        "territory_excess_area_m2": covered.difference(study).area,
        "sum_cell_area_m2": float(cells.area.sum()), "partial_cells": int(cells.is_boundary.sum()),
        "mailles_avec_surface_caen": int(cells.caen_area_m2.gt(0).sum()),
        "old_lattice_shared_ids": shared.maille_id.tolist(), "centers_identical": True,
        "lattice_source_sha256": sha(ROOT / "tests/fixtures/m1_grid_v61/generate_hex_grid.py"),
        "origin": [0, 0], "orientation": "flat_top", "nominal_area_m2": 1000000,
        "municipality_source": "ADMINEXPRESS-COG.LATEST:commune", "source_date": "retrieved_2026-11-11_COG_LATEST",
        "caen_commune_logical_extent": "territoire.gpkg:caen_commune",
        "analysis_extent": TERRITORY})
    print("Grille validée", len(cells), "mailles ; Caen entière couverte", flush=True)


def layers():
    acquisition = json.loads((RAW / "acquisition.json").read_text())
    if (RAW / "routes_reprise.json").exists():
        acquisition["sources"]["routes"] = json.loads((RAW / "routes_reprise.json").read_text())
    study = gpd.read_file(PROC / "territoire.gpkg", layer="territoire").geometry.iloc[0]
    processing, refused = {}, []
    for kind, info in acquisition["sources"].items():
        if kind == "communes":
            continue
        if info["status"] != "acquired":
            processing[kind] = info; continue
        if "pages" in info:
            feats = [f for p in info["pages"] for f in json.loads((ROOT / p["file"]).read_text())["features"]]
            source = gpd.GeoDataFrame.from_features(feats, crs=2154)
            if "cleabs" not in source:
                raise ValueError("Identifiant IGN absent")
        else:
            vector = ROOT / info["vector_file"]
            # Les shapefiles SRCE/ZH sont en L93 ; GPKG Cartofriches : adapter BBOX au CRS déclaré.
            meta = gpd.read_file(vector, rows=1)
            if meta.crs is None:
                processing[kind] = {"status": "unusable", "reason": "CRS absent"};continue
            from pyproj import Transformer
            bounds = Transformer.from_crs(2154, meta.crs, always_xy=True).transform_bounds(*study.bounds, densify_pts=21)
            source = gpd.read_file(vector, bbox=bounds).to_crs(2154)
        rows = []
        for i, obj in source.iterrows():
            original = obj.geometry
            if original is None or original.is_empty or not original.is_valid:
                refused.append({"layer": kind, "source_index": str(i), "reason": "invalid_or_empty_source_geometry"});continue
            if not original.intersects(study):
                continue
            geom = dimension(original.intersection(study), "line" if kind in {"routes", "haies"} else "polygon")
            if geom is None:
                continue
            attrs = {str(k): json_value(obj[k]) for k in source.columns if k != "geometry"}
            if kind == "routes":
                mapping = {"route_id": "cleabs", "categorie": "nature", "importance": "importance", "position_sol": "position_par_rapport_au_sol",
                    "statut_objet": "etat_de_l_objet", "nombre_voies": "nombre_de_voies", "largeur_chaussee": "largeur_de_chaussee",
                    "contexte_urbain": "urbain", "precision_planimetrique_m": "precision_planimetrique", "vitesse_moyenne_vl_source": "vitesse_moyenne_vl",
                    "date_modification": "date_modification", "acces_vehicule_leger": "acces_vehicule_leger"}
                attrs = {k: attrs.get(v) for k, v in mapping.items()}
                attrs.update(source_id="BDTOPO_ROUTES", ouvrage_connu=None, millesime=None)
            elif kind in {"corridors", "reservoirs"}:
                source_hash = hashlib.sha256(normalize(force_2d(original)).wkb + json.dumps(attrs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:20].upper()
                attrs = {"source_id": "TVB_COR_BN" if kind == "corridors" else "TVB_RES_NORM",
                    "objet_id": "TVB-COR-" + source_hash if kind == "corridors" else str(attrs.get("ID_RESV") or "TVB-RES-" + source_hash),
                    "objet_source_id": attrs.get("ID_SRCE"), "sous_trame": attrs.get("MILMAJ_REG"),
                    "millesime": "2014", "precision_source": None,
                    **({"classe_corridor": attrs.get("CLASS_CORR"), "libelle_source": attrs.get("ID_CORR")} if kind == "corridors" else {"nom": attrs.get("NOM_RESV")})}
            else:
                identifier = attrs.get("cleabs") or attrs.get("site_id") or attrs.get("id") or attrs.get("id_friche")
                if identifier is None:
                    identifier = hashlib.sha256(normalize(force_2d(original)).wkb + json.dumps(attrs, sort_keys=True).encode()).hexdigest()
                attrs["objet_id"] = str(identifier)
                # Garder les listes et dictionnaires sources en texte JSON dans le GPKG.
                attrs = {k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v for k, v in attrs.items()}
            rows.append({**attrs, "geometry": geom})
        if rows:
            frame = gpd.GeoDataFrame(rows, crs=2154)
            id_col = "route_id" if kind == "routes" else "objet_id"
            assert frame[id_col].notna().all() and frame[id_col].is_unique, (kind, "IDs dupliqués")
            assert frame.is_valid.all()
            frame.to_file(PROC / (kind + ".gpkg"), layer=kind, engine="pyogrio")
            processing[kind] = {**info, "status": "processed", "features": len(frame),
                "crs": "EPSG:2154", "file": str((PROC / (kind + ".gpkg")).relative_to(ROOT)), "layer": kind,
                "id_column": id_col, "sha256": sha(PROC / (kind + ".gpkg")),
                "fields": list(frame.columns), "null_counts": {k: int(frame[k].isna().sum()) for k in frame.columns if k != "geometry"}}
        else:
            processing[kind] = {**info, "status": "no_observed_objects", "features": 0}
        print("Couche", kind, processing[kind]["status"], processing[kind].get("features"), flush=True)
    write(OUT / "sources_preparees.json", {"territory_id": TERRITORY, "grid_version": GRID, "dataset_version": DATASET,
        "sources": processing, "source_geometries_refused": refused, "ecological_completeness_validated": False})


if __name__ == "__main__":
    p = argparse.ArgumentParser();p.add_argument("stage", choices=["grid", "layers"])
    args = p.parse_args();grid() if args.stage == "grid" else layers()
