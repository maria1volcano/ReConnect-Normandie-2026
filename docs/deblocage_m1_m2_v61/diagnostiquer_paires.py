"""Diagnostic ciblé et prototype NON ACTIVÉ ; aucune écriture sur les entrées.

Usage depuis la racine : PYTHONDONTWRITEBYTECODE=1 python <ce script>
    <snapshot M1 extrait> <nouveau JSON de sortie>

Les tests exécutent le validateur existant et une proposition en mémoire.
Le prototype numérique n'est pas une borne garantie de l'erreur GEOS.
"""

from __future__ import annotations

from collections import Counter
from importlib import metadata, util
from itertools import combinations
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

import geopandas as gpd
import shapely
from shapely import get_coordinates, union_all
from shapely.affinity import translate
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from analysis.validate_inputs import (  # noqa: E402
    AREA_TOLERANCE_M2, ValidationReport, validate_spatial_coverage,
)
from analysis.run_enjeux import load_config as load_enjeux_config  # noqa: E402
from analysis.run_conflicts import load_config as load_conflicts_config  # noqa: E402


def polygon_parts(geometry):
    """Ne pas gonfler le périmètre surfacique avec des contacts linéaires."""
    if geometry.geom_type == "Polygon":
        yield geometry
    elif geometry.geom_type in {"MultiPolygon", "GeometryCollection"}:
        for part in geometry.geoms:
            yield from polygon_parts(part)


def analyse_pairs(frame):
    """Toutes les paires i<j, aucun arrondi/snap/réparation ni filtre d'aire."""
    coordinates = get_coordinates(frame.geometry.array)
    ux = max(math.ulp(float(value)) for value in coordinates[:, 0])
    uy = max(math.ulp(float(value)) for value in coordinates[:, 1])
    delta = math.hypot(ux, uy)
    rows = []
    types = Counter()
    disjoint = 0
    for i, j in combinations(range(len(frame)), 2):
        intersection = frame.geometry.iloc[i].intersection(frame.geometry.iloc[j])
        if intersection.is_empty:
            disjoint += 1
            continue
        types[intersection.geom_type] += 1
        parts = list(polygon_parts(intersection))
        area = math.fsum(part.area for part in parts)
        perimeter = math.fsum(part.length for part in parts)
        # Budget dérivé de la résolution machine et du périmètre observé.
        # Le terme pi*delta² traite la fermeture d'une bande autour d'un contour.
        local_budget = delta * perimeter + math.pi * delta**2 if area > 0 else 0.0
        rows.append({
            "left": str(frame.iloc[i].maille_id),
            "right": str(frame.iloc[j].maille_id),
            "intersection_type": intersection.geom_type,
            "area_m2": area,
            "polygon_perimeter_m": perimeter,
            "equivalent_strip_width_m": 2 * area / perimeter if perimeter else None,
            "proposed_local_budget_m2": local_budget,
            "exceeds_existing_area_cap": area > AREA_TOLERANCE_M2,
            "exceeds_proposed_local_budget": area > local_budget,
        })
    areas = frame.geometry.area.tolist()
    union = union_all(frame.geometry.array)
    # fsum réduit l'erreur d'accumulation, sans prétendre corriger l'overlay.
    excess = math.fsum(areas) - union.area
    accumulation_budget = math.fsum(math.ulp(area) for area in areas) + math.ulp(union.area)
    global_budget = delta * math.fsum(frame.length.tolist()) + accumulation_budget
    positive = [row for row in rows if row["area_m2"] > 0]
    # PROPOSITION : contrôle local ET global ; aucune hausse de la constante M2.
    rejected = [row for row in positive if row["exceeds_existing_area_cap"]
                or row["exceeds_proposed_local_budget"]]
    unexplained_global = excess > max(AREA_TOLERANCE_M2, global_budget)
    return {
        "all_distinct_pairs": len(frame) * (len(frame) - 1) // 2,
        "disjoint_pairs": disjoint,
        "nonempty_types": dict(types),
        "boundary_pairs_without_area": sum(row["area_m2"] == 0 for row in rows),
        "positive_area_pairs": len(positive),
        "max_intersection_area_m2": max((row["area_m2"] for row in positive), default=0.0),
        "sum_intersection_areas_m2": math.fsum(row["area_m2"] for row in positive),
        "sum_areas_minus_union_m2": float(frame.area.sum() - union.area),
        "fsum_areas_minus_union_m2": excess,
        "ulp_x_m": ux, "ulp_y_m": uy, "coordinate_ulp_diagonal_m": delta,
        "proposed_global_budget_m2": global_budget,
        "proposed_rejected_pairs": rejected,
        "proposed_grid_overlap_error": bool(rejected or unexplained_global),
        "proposed_numeric_warning": bool(positive or excess > AREA_TOLERANCE_M2),
        "pairs": rows,
    }


def existing_validation(frame, territory=None):
    territory = territory if territory is not None else gpd.GeoDataFrame(
        geometry=[union_all(frame.geometry.array)], crs=frame.crs,
    )
    report = ValidationReport()
    validate_spatial_coverage(frame, territory, report)
    return report.as_dict()


def synthetic_frame(geometries):
    return gpd.GeoDataFrame(
        {"maille_id": [f"SYNTHETIQUE-{i}" for i in range(len(geometries))]},
        geometry=geometries, crs=2154,
    )


def main(snapshot, output):
    output = output.resolve()
    if output.exists():
        raise ValueError("Refus d'écraser une sortie existante.")
    reference = "fc76d6230994af9aef27f42bb42e0374cd0c8251"
    selected = ["analysis/generate_hex_grid.py", "data/public/grille_pilote_wgs84.geojson"]
    hashes = {}
    for relative in selected:
        local = (snapshot / relative).read_bytes()
        git = subprocess.check_output(["git", "show", f"{reference}:{relative}"], cwd=ROOT)
        if local != git:
            raise ValueError(f"Entrée différente du snapshot audité : {relative}")
        hashes[relative] = hashlib.sha256(local).hexdigest()
    spec = util.spec_from_file_location("m1_grid_pairs_only", snapshot / selected[0])
    generator = util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    regenerated, _, _ = generator.generate_grid()  # pas de main(), pas de fichier produit
    delivered = gpd.read_file(snapshot / selected[1]).to_crs(2154)
    out = {
        "m1_commit": reference,
        "current_m1_ref": subprocess.check_output(
            ["git", "rev-parse", "origin/feat/m1-donnees-sig-v61"], cwd=ROOT, text=True,
        ).strip(),
        "selected_input_sha256": hashes,
        "software": {p: metadata.version(p) for p in ["geopandas", "shapely", "pyproj"]},
        "geos": shapely.geos_version_string,
        "prototype_status": "proposition_non_appliquee_budget_non_garanti_par_GEOS",
        "delivered_geojson_l93": analyse_pairs(delivered),
        "regenerated_grid_l93": analyse_pairs(regenerated),
        "existing_validator": {
            "delivered": existing_validation(delivered),
            "regenerated": existing_validation(regenerated),
        },
    }
    tests = []

    def expect(name, frame, rejected):
        before = [geometry.wkb for geometry in frame.geometry]
        result = analyse_pairs(frame)
        assert result["proposed_grid_overlap_error"] is rejected, name
        assert before == [geometry.wkb for geometry in frame.geometry], name
        tests.append({"case": name, "passed": True, "expected_grid_overlap": rejected})

    expect("M1_GeoJSON_residu_numerique_signale", delivered, False)
    expect("M1_regeneree_residu_numerique_signale", regenerated, False)
    expect("M1_ordre_inverse", delivered.iloc[::-1].reset_index(drop=True), False)
    x, y = 461000.0, 6905000.0
    expect("contact_arete", synthetic_frame([box(x, y, x+10, y+10), box(x+10, y, x+20, y+10)]), False)
    expect("contact_sommet", synthetic_frame([box(x, y, x+10, y+10), box(x+10, y+10, x+20, y+20)]), False)
    expect("objets_disjoints", synthetic_frame([box(x, y, x+10, y+10), box(x+20, y, x+30, y+10)]), False)
    expect("vrai_chevauchement_millimetrique", synthetic_frame([box(x, y, x+10, y+10), box(x+9.999, y, x+20, y+10)]), True)
    expect("geometrie_dupliquee_ids_distincts", synthetic_frame([box(x, y, x+10, y+10)]*2), True)
    expect("contenance", synthetic_frame([box(x, y, x+10, y+10), box(x+1, y+1, x+2, y+2)]), True)
    expect("recouvrement_triple", synthetic_frame([box(x, y, x+10, y+10)]*3), True)
    expect("chevauchement_inferieur_au_cap_mais_non_numerique", synthetic_frame([
        box(x, y, x+5, y+5), box(x+5-1e-7, y, x+10, y+5),
    ]), True)
    expect("petit_polygone_compact_sous_1e_6_m2", synthetic_frame([
        box(x, y, x+0.0001, y+0.0001), box(x, y, x+0.0001, y+0.0001),
    ]), True)
    many = []
    for i in range(8):
        tiny = box(x+i, y, x+i+0.0001, y+0.0001)
        many.extend([tiny, tiny])
    expect("plusieurs_petits_chevauchements_non_numeriques", synthetic_frame(many), True)
    perturbed = regenerated.copy()
    position = perturbed.index[~perturbed.is_boundary][0]
    perturbed.at[position, "geometry"] = translate(perturbed.loc[position].geometry, xoff=0.001)
    expect("maille_M1_deplacee_1_mm", perturbed, True)
    # Vérifier que la proposition ne demande aucune modification de la garde de lacune.
    gap = synthetic_frame([box(x, y, x+1, y+1), box(x+2, y, x+3, y+1)])
    territory = gpd.GeoDataFrame(geometry=[box(x, y, x+3, y+1)], crs=2154)
    assert any(e["code"] == "grid_coverage_gap" for e in existing_validation(gap, territory)["errors"])
    tests.append({"case": "garde_lacune_existante_conservee", "passed": True})
    for grid in [delivered, regenerated]:
        assert any(e["code"] == "grid_overlap" for e in existing_validation(grid)["errors"])
        assert analyse_pairs(grid)["proposed_numeric_warning"]
    configs = Path(__file__).parent
    load_enjeux_config(configs / "config_enjeux.proposition.json")
    load_conflicts_config(configs / "config_conflits.proposition.json")
    tests.append({"case": "deux_configurations_acceptees_par_load_config", "passed": True})
    out["targeted_tests"] = tests
    output.write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(f"{len(tests)} contrôles ciblés réussis ; diagnostic : {output}")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve(), Path(sys.argv[2]))
