"""Découpe des livraisons IGN : observations, nomenclature et couverture effective."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import geopandas as gpd
from shapely import union_all
from analysis.preparer_caen_et_nord import dimension, sha
from analysis.auditer_mailles_grises_caen import ROOT, BASE, OUT
from analysis.validate_inputs import AREA_TOLERANCE_M2

RAW = ROOT / "data/raw/ocsge_caen_20261112_v1"
PROC = ROOT / "data/processed/caen_et_nord/OCSGE_2023_20261112_V1"


def prepare(kind):
    PROC.mkdir(parents=True, exist_ok=True)
    paths = list((RAW / ("extrait_ocsge" if kind == "ocsge" else "extrait_artif")).rglob("OCCUPATION_SOL.gpkg" if kind == "ocsge" else "*.gpkg"))
    assert len(paths) == 1
    path = paths[0]
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
        assert db.execute("PRAGMA quick_check").fetchone()[0] == "ok"
    study = gpd.read_file(BASE / "donnees/territoire.gpkg", layer="territoire").geometry.iloc[0]
    cells = gpd.read_file(BASE / "donnees/grille.gpkg", layer="mailles")
    source = gpd.read_file(path, bbox=study.bounds)
    assert source.crs.to_epsg() == 2154
    assert source.id.notna().all() and source.id.is_unique
    valid = source.geometry.notna() & ~source.geometry.is_empty & source.geometry.is_valid
    refused = [{"id": str(row.id), "motif": "geometrie_source_invalide_ou_vide", "geometry_repaired": False}
               for row in source.loc[~valid].itertuples()]
    selected = source.loc[valid & source.geometry.intersects(study)].copy()
    clipped = selected.geometry.intersection(study).map(lambda g: dimension(g, "polygon"))
    selected = selected.loc[clipped.notna()].copy(); selected.geometry = clipped.loc[selected.index]
    assert selected.is_valid.all()
    assert set(selected.millesime.astype(str)) == {"2023"}
    selected["objet_id"] = selected.id.astype(str)
    target = PROC / (kind + ".gpkg")
    assert not target.exists()
    selected.to_file(target, layer=kind, engine="pyogrio")
    covered = union_all(selected.geometry.to_numpy())
    coverage = []
    for c in cells.itertuples():
        gap = c.geometry.difference(covered).area
        coverage.append({"maille_id": c.maille_id, "grid_version": c.grid_version, "territory_id": c.territory_id,
            "surface_maille_m2": c.geometry.area, "surface_couverte_m2": c.geometry.intersection(covered).area,
            "surface_non_couverte_m2": gap, "couverture_geometrique": "complete_dans_budget_numerique_existant" if gap <= AREA_TOLERANCE_M2 else "partielle",
            "budget_numerique_m2": AREA_TOLERANCE_M2, "completude_ecologique": "non_validee"})
    report = {"layer": kind, "source_file": str(path.relative_to(ROOT)), "source_sha256": sha(path),
        "processed_file": str(target.relative_to(ROOT)), "processed_sha256": sha(target), "crs": "EPSG:2154", "millésime": "2023",
        "source_features_bbox": len(source), "retained_features": len(selected), "refus_geometries_bbox": refused,
        "geometry_repaired": False, "id_duplicates": 0, "codes_cs": dict(Counter(selected.code_cs)),
        "codes_us": dict(Counter(selected.code_us)), "champs": list(selected.columns),
        "valeurs_artif": dict(Counter(selected.artif)) if "artif" in selected else None,
        "surface_territoire_m2": study.area, "surface_union_couverte_m2": covered.area,
        "surface_non_couverte_m2": study.difference(covered).area,
        "somme_surfaces_moins_union_m2": float(selected.area.sum() - covered.area),
        "couverture_par_maille": coverage, "ecological_completeness_validated": False,
        "precision_source": {"description": "Positionnement métrique, échelle d'utilisation 1:5000 selon DC_OCSGE_NG juin 2026 ; aucune précision numérique par objet fournie",
                             "valeur_m": None, "reference": "https://data.geopf.fr/annexes/ressources/documentation/DC_OCSGE_NG.pdf"}}
    (OUT / (kind + ".validation.json")).write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k:v for k,v in report.items() if k not in {"couverture_par_maille", "champs", "codes_us"}}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser();parser.add_argument("kind", choices=["ocsge", "artificialisation"])
    prepare(parser.parse_args().kind)
