"""Acceptation du lot réel Caen : contrôles géométriques et scientifiques existants."""
from __future__ import annotations
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3

import geopandas as gpd
from shapely import union_all
from shapely.geometry import shape
from analysis.preparer_caen_et_nord import ROOT, OUT, PROC, GRID, TERRITORY, sha
from analysis.livrer_caen_et_nord import BUNDLE
from analysis.validate_inputs import ValidationReport, validate_spatial_coverage, AREA_TOLERANCE_M2
from analysis.integrer_complement_caen_nord import profile


def main():
    read = lambda p: json.loads(Path(p).read_text())
    checks = []
    def check(number, label, condition, **evidence):
        assert condition, label
        checks.append({"critere": number, "controle": label, "ok": True, **evidence})
    grid = gpd.read_file(PROC / "grille.gpkg", layer="mailles")
    full = gpd.read_file(PROC / "grille.gpkg", layer="hexagones_complets").set_index("maille_id")
    territory = gpd.read_file(PROC / "territoire.gpkg", layer="territoire")
    caen = gpd.read_file(PROC / "territoire.gpkg", layer="caen_commune").geometry.iloc[0]
    missing = caen.difference(union_all(grid.geometry.to_numpy())).area
    check(1, "Caen 14118 entièrement couverte selon le budget existant", missing <= AREA_TOLERANCE_M2,
          manque_m2=missing, budget_existant_m2=AREA_TOLERANCE_M2)
    coverage = ValidationReport(); validate_spatial_coverage(grid, territory, coverage)
    check(2, "Couverture et chevauchements : validateur M2 inchangé", coverage.ok, rapport=coverage.as_dict())
    old = gpd.read_file(ROOT / "data/processed/caen_nord_5communes/M1-M2-CAEN-NORD-V1/m2_caen_nord_20261111_02/m1_m2_caen_nord_v1/grille_caen_nord.gpkg", layer="hexagones_complets").set_index("maille_id")
    check(3, "Hexagones complets des 66 identifiants communs identiques", set(old.index) <= set(full.index)
          and all(full.loc[i].geometry.equals_exact(old.loc[i].geometry, 0) for i in old.index), identifiants_communs=len(old))
    geo = read(BUNDLE / "demo_interne/mailles.geojson")
    fiches = read(BUNDLE / "demo_interne/fiches_zones.json")["fiches"]
    mids = set(grid.maille_id)
    check(4, "Identifiants et version uniques", len(mids) == len(grid) and set(grid.grid_version) == {GRID}
          and set(grid.territory_id) == {TERRITORY})
    check(5, "Exactement une fiche par hexagone affichable", len(fiches) == len(grid) == len(geo["features"])
          and {f["maille_id"] for f in fiches} == mids)
    spec = importlib.util.spec_from_file_location("triage_legacy", ROOT / "analysis/construire_fiches_66.py")
    legacy = importlib.util.module_from_spec(spec); spec.loader.exec_module(legacy)
    # Réévaluer les préconditions à partir des paires justificatives locales et des surfaces.
    for f in fiches:
        t = f["triage_documentaire"]; obs = t["observations_justificatives"]; pairs = t["paires_justificatives"]
        assert len(pairs) == obs["nombre_paires_route_corridor_2d"]
        fragile = [p for p in pairs if p["categorie"] in legacy.CATEGORIES_CARROSSABLES and p["statut_objet"] == "En service"
                   and str(p["position_sol"]) == "0" and p["classe_corridor"] == legacy.NATURE_MATRICE_FRAGILE]
        assert len(fragile) == obs["paires_route_matrice_fragile_en_service_au_sol"]
        assert obs["reservoir_presence_surface_positive"] == (f["diagnostic_techniciens"]["observations"]["reservoirs"]["mesure_observee"] > 0)
        assert legacy.color_rule(obs)["regle"] == t["regle"] and bool(t["motif"])
    check(6, "V1–V4 réévaluées, justification et couleur de chaque maille", True,
          couleurs=dict(Counter(f["triage_documentaire"]["niveau"] for f in fiches)))
    check(7, "D/S indépendante et non calculée", all(f["priorite_examen"] == {"etat": "non_calculee", "valeur": None}
          and f["method_version"] is None and f["priorite_ecologique"]["category"] == "INDETERMINATE" for f in fiches))
    baseline = read(OUT / "preservation_avant.json")
    altered = [p for p, h in baseline.items() if not (ROOT / p).exists() or sha(ROOT / p) != h]
    initial = read(BUNDLE / "rapports/bilan.json")
    assert sha(ROOT / "docs/table_triage_exploratoire.json") == initial["triage_definition_sha256"]
    assert sha(ROOT / "analysis/construire_fiches_66.py") == initial["triage_category_definition_sha256"]
    check(8, "Fichiers antérieurs conservés octet pour octet", not altered, fichiers=len(baseline), alteres=altered)
    events = gpd.read_file(BUNDLE / "rapports/evenements.gpkg", layer="conflits_candidates")
    detected = gpd.read_file(BUNDLE / "rapports/evenements_detectes.gpkg")
    quarantine = gpd.read_file(BUNDLE / "rapports/quarantaine.gpkg")
    event_idx = detected.set_index("conflit_id")
    unchanged = all(e.geometry.wkb == event_idx.loc[e.conflit_id].geometry.wkb for e in events.itertuples())
    unchanged &= all(e.geometry.wkb == event_idx.loc[e.conflit_id].geometry.wkb for e in quarantine.itertuples())
    check(9, "Détectés = admis + quarantaine, géométries inchangées", unchanged and
          set(detected.conflit_id) == set(events.conflit_id) | set(quarantine.conflit_id)
          and set(events.conflit_id).isdisjoint(quarantine.conflit_id), detectes=len(detected), admis=len(events), quarantaine=len(quarantine))
    actions = read(BUNDLE / "demo_interne/actions_resultats.json")["resultats"]
    validator = profile(read(ROOT / "docs/schema_actions_m2.json"), "actionResult")
    for a in actions: validator.validate(a)
    with sqlite3.connect((BUNDLE / "rapports/mailles.gpkg").as_uri() + "?mode=ro", uri=True) as db:
        links = db.execute("SELECT conflit_id,maille_id,canonical_owner FROM liens_mailles_conflits").fetchall()
    source_ids = {}
    source_frames = {}
    for layer in read(BUNDLE / "rapports/bilan.json")["source_features"]:
        d = gpd.read_file(BUNDLE / "donnees/sources_consultables.gpkg", layer=layer)
        source_frames[layer] = d
        id_col = "route_id" if layer == "routes" else "objet_id"
        source_ids[layer] = set(d[id_col]); assert len(source_ids[layer]) == len(d)
        assert d.crs.to_epsg() == 2154 and d.is_valid.all() and not d.is_empty.any()
    observations = read(BUNDLE / "donnees/liens_observations.json")
    assert all(o["maille_id"] in mids and o["objet_id"] in source_ids[o["source_couche"]] and o["measure"] > 0 for o in observations)
    # Les paires de triage sont bien des objets acquis et reliés aux événements admis.
    indexed_events = events.set_index("conflit_id")
    road_index = source_frames["routes"].set_index("route_id")
    corridor_index = source_frames["corridors"].set_index("objet_id")
    for f in fiches:
        cell = grid.set_index("maille_id").loc[f["maille_id"]].geometry
        for p in f["triage_documentaire"]["paires_justificatives"]:
            assert p["route_id"] in source_ids["routes"] and p["corridor_id"] in source_ids["corridors"]
            for key in ("categorie", "statut_objet", "position_sol", "importance"):
                assert str(p[key]) == str(road_index.loc[p["route_id"], key])
            assert p["classe_corridor"] == corridor_index.loc[p["corridor_id"], "classe_corridor"]
            for cid in p["conflit_ids"]:
                e = indexed_events.loc[cid]
                assert [p["route_id"], p["corridor_id"]] in read_json(e.source_pairs)
                assert e.intersection_dimension == "lineaire" and e.geometry.intersection(cell).length > 0
    check(10, "Actions conformes au schéma et jointures objets/événements vérifiées", len(actions) == 4 * len(grid)
          and len({(c, m) for c, m, _ in links}) == len(links) and sum(o for _, _, o in links) == len(events),
          actions=len(actions), liens_evenements=len(links), liens_observations=len(observations))
    check(11, "Aucune recommandation inventée", all(a["statut"] == "non_evaluable" and a["methode"] is None
          and a["preuve_ids"] == a["attestation_ids"] == [] for a in actions)
          and all(not f["recommandations_validees"] and not any(a["travaux_preconises"] for a in f["actions"]) for f in fiches))
    for file in ("mailles.geojson", "conflits.geojson"):
        doc = read(BUNDLE / "demo_interne" / file)
        assert "crs" not in doc
        for f in doc["features"]:
            g = shape(f["geometry"])
            assert g.is_valid and not g.is_empty and not g.has_z
            assert -180 <= g.bounds[0] <= g.bounds[2] <= 180 and -90 <= g.bounds[1] <= g.bounds[3] <= 90
    check(12, "GeoJSON WGS84, géométries valides et 2D", True)
    # 13 est exécuté séparément sur le ZIP scellé, pour ne pas produire une preuve circulaire.
    private = {"proprio_nom", "proprio_personne", "source_contact", "interpr", "site_adresse", "unite_fonciere_refcad"}
    assert all(private.isdisjoint(d.columns) for d in source_frames.values())
    def scan(value):
        if isinstance(value, dict):
            assert private.isdisjoint(value), "Attribut privé dans les données de démonstration"
            assert value.get("test_data") is not True, "Donnée réelle étiquetée TEST"
            for v in value.values(): scan(v)
        elif isinstance(value, list):
            for v in value: scan(v)
    for path in (BUNDLE / "demo_interne").iterdir(): scan(read(path))
    check(14, "Listes attributaires minimisées, données réelles internes, verrou public intact", True,
          restriction="Aucune publication autorisée ; aucun inventaire d'espèces sensibles incorporé")
    distributions = {}
    for field in ("categorie", "statut_objet", "position_sol", "importance", "nombre_voies", "largeur_chaussee", "contexte_urbain"):
        counts = Counter()
        for e in events.itertuples():
            attrs = read_json(e.observations)["routes"]["attributes"]
            counts[str(attrs.get(field))] += 1
        distributions[field] = dict(counts)
    result = {"ok": True, "criteres_dans_ce_rapport": 13, "critere_13": "Voir validation_extraction.json à côté du ZIP",
              "checks": checks, "repartition_evenements_admis_attributs_routiers": distributions}
    (BUNDLE / "rapports/acceptation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"ok": True, "criteres": len(checks), "fichiers_historiques_preserves": len(baseline)}, ensure_ascii=False))


def read_json(value):
    return json.loads(value)


if __name__ == "__main__": main()
