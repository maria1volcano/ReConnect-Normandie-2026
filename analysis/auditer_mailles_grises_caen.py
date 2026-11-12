"""Audit territorial V1, voisinage de lattice explicite, sans transfert d'observations."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import geopandas as gpd

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/derived/caen_et_nord_20261111_01/RECONNECT_CAEN_ET_NORD_M2_DEMO_INTERNE_20261111_V1"
OUT = ROOT / "data/derived/caen_et_nord_triage_20261112_01"


def adjacent_positions(row, col):
    """Six voisins flat-top du lattice M1 : parité de colonne, aucun rayon choisi."""
    shift = 1 if col % 2 else -1
    return {(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1),
            (row + shift, col - 1), (row + shift, col + 1)}


def audit():
    fiches = json.loads((BASE / "demo_interne/fiches_zones.json").read_text())["fiches"]
    index = {f["maille_id"]: f for f in fiches}
    grid = gpd.read_file(BASE / "donnees/grille.gpkg", layer="mailles").set_index("maille_id")
    positions = {(int(c.grid_row), int(c.grid_col)): mid for mid, c in grid.iterrows()}
    sources = {k: gpd.read_file(BASE / "donnees/sources_consultables.gpkg", layer=k)
               for k in fiches[0]["diagnostic_techniciens"]["observations"]}
    results = []
    for f in fiches:
        if f["triage_documentaire"]["niveau"] != "gris": continue
        mid = f["maille_id"]; cell = grid.loc[mid]; obs = f["diagnostic_techniciens"]["observations"]
        neighbours = sorted(positions[p] for p in adjacent_positions(int(cell.grid_row), int(cell.grid_col)) if p in positions)
        nearby = []; nearest = {}
        for kind, source in sources.items():
            oid = "route_id" if kind == "routes" else "objet_id"
            ds = source.geometry.distance(cell.geometry)
            minimum = float(ds.min())
            rows = source.loc[ds.eq(minimum)].sort_values(oid)
            precision_field = "precision_planimetrique_m" if kind == "routes" else "precision_planimetrique" if kind == "haies" else "precision_source"
            nearest[kind] = {"distance_source_m": minimum, "definition": "Distance géométrique minimale entre la maille découpée et les objets acquis de cette couche ; aucun rayon écologique",
                "objets_les_plus_proches": [{"objet_id": str(r[oid]), "precision_source_m": None if precision_field not in r or r[precision_field] is None else float(r[precision_field])}
                                           for _, r in rows.iterrows()], "absence_attestee": False}
        for neighbour in neighbours:
            nf = index[neighbour]
            no = nf["diagnostic_techniciens"]["observations"]
            context = {}
            for kind in obs:
                oid = "route_id" if kind == "routes" else "objet_id"
                current_ids = {str(o[oid]) for o in obs[kind]["objets"]}
                nids = {str(o[oid]) for o in no[kind]["objets"]}
                context[kind] = {"objets_observes_voisin": len(nids), "objet_ids_uniquement_voisin": sorted(nids - current_ids),
                    "objet_ids_partages": sorted(nids & current_ids), "mesure_locale_voisin": no[kind]["mesure_observee"],
                    "unite": no[kind]["unite"], "presence_dans_maille_courante_deduite": False}
            nearby.append({"maille_id": neighbour, "grid_version": f["grid_version"], "territory_id": f["territory_id"],
                "voisinage": "adjacent_sur_lattice_M1", "distance_entre_mailles_decoupees_m": float(cell.geometry.distance(grid.loc[neighbour].geometry)),
                "longueur_frontiere_commune_m": float(cell.geometry.boundary.intersection(grid.loc[neighbour].geometry.boundary).length),
                "observations_dans_voisin": context, "continuite_fonctionnelle_etablie": False})
        additional = [k for k in ("haies", "zones_humides", "plans_eau") if obs[k]["nombre_objets_observes"] > 0]
        poor = not additional
        results.append({"maille_id": mid, "grid_version": f["grid_version"], "territory_id": f["territory_id"],
            "communes": f["communes"], "area_m2": f["surface_m2"], "pilot_fraction": f["pilot_fraction"], "maille_partielle": f["maille_partielle"],
            "classe_initiale": "gris", "regle_initiale": "V4", "motif_v4_exact": f["triage_documentaire"]["motif"],
            "causes_v4": ["aucune_paire_route_matrice_lineaire_documentee", "aucune_surface_positive_matrice_ou_reservoir_SRCE", "V1_V3_ne_mobilisent_pas_les_autres_couches"],
            "observations_dans_maille": obs,
            "attributs_routes": {k: dict(Counter(str(o.get(k)) for o in obs["routes"]["objets"])) for k in
                                 ("categorie", "importance", "statut_objet", "position_sol", "nombre_voies", "largeur_chaussee")},
            "contexte_voisinage": nearby, "distance_source": nearest,
            "precision_source": {"haies": "3 m selon attribut acquis ; non exhaustif écologiquement", "routes": "Attribut par objet, pas de validation de perméabilité",
                "SRCE": None, "zones_humides": None, "plans_eau": None},
            "couverture_sources": {k: {"acquisition": "objets_officiels_acquis_sur_BBOX_des_six_communes_et_decoupes",
                "completude_ecologique": "non_validee", "absence_attestee": False,
                "statut_local": obs[k]["disponibilite"], "refus_geometries_bbox": 17 if k == "friches" else 44 if k == "zones_humides" else 0}
                for k in sources},
            "sources_ecologiques_non_mobilisees_par_V1_V3": additional,
            "diagnostic_information": "aucun_objet_haie_eau_ZH_observe_dans_les_couches_actuelles" if poor else "observations_ecologiques_cartographiques_non_mobilisees_par_V1_V3",
            "donnees_susceptibles_de_qualifier": ["OCS GE : couverture végétale/aquatique et usages à mesurer localement", "Validation locale des habitats et de leur état fonctionnel",
                "Inventaire des mares et complétude thématique attestée", "Voisinage consultable sans transfert d'objet"]})
    return results


if __name__ == "__main__":
    rows = audit()
    assert len(rows) == 32
    (OUT / "audit_grises_v1.json").write_text(json.dumps({"audit_version": "caen6-v4-audit-20261112-1", "mailles": rows}, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"mailles_grises": len(rows), "avec_autres_observations_ecologiques": sum(bool(r["sources_ecologiques_non_mobilisees_par_V1_V3"]) for r in rows)}, ensure_ascii=False))
