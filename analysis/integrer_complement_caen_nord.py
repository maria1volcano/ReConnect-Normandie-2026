"""Fiches internes provisoires M1/M2, sans relance du détecteur ni export public.

Les profils d'actions viennent du schéma existant. Les pistes documentaires sont
séparées des sorties A0–A8 et ne valident ni méthode ni recommandation de travaux.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3

import geopandas as gpd
from jsonschema import Draft202012Validator, FormatChecker
import pandas as pd

from analysis.detect_conflicts import json_value

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/derived/caen_nord_5communes/transfert_m4_20261111_01/M2_CAEN_NORD_M4_INTERNE_20261111_V1"
RAW = ROOT / "data/raw/m1_complement_caen_nord_20261111"
SCOPE = {"territory_id": "caen_nord_5communes", "grid_version": "M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1",
         "dataset_version": "M1-M2-CAEN-NORD-V1", "method_version": None}
COMPLEMENT = "m1-caen-nord-complement-1"
FORMAT = "m2-caen-nord-fiches-provisoires-1"
FAMILIES = {"R1": "route_corridor", "R2": "bocage", "R3": "friches", "R4": "reseau_humide"}
MISSING = {
    "R1": ["Sous-trame et pertinence écologique non documentées", "Qualité de localisation bilatérale et qualification de perméabilité non validées", "Méthode familiale approuvée et contrôle des contradictions non fournis"],
    "R2": ["Analyse de lacune ou de discontinuité non fournie", "Sous-trame bocagère et fonctionnement biologique non établis", "Méthode familiale approuvée et couvertures des faits essentiels non fournies"],
    "R3": ["Inventaire de friches non chargé", "Statut des sites et lien à une continuité non documentés", "Méthode de voisinage approuvée non fournie"],
    "R4": ["Plans d'eau non qualifiés comme mares ou habitats pertinents", "Analyse de réseau, isolement et hydrologie non fournie", "Zones humides non chargées et méthode familiale approuvée non fournie"],
}
LIMITS = ["Observation cartographique sans preuve de rupture fonctionnelle", "Une non-détection ne démontre pas une absence écologique", "Pistes documentaires distinctes des statuts d'action et des travaux", "Catalogue M5 et schéma applicatif M4 non fournis ; identifiants connus conservés"]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, payload):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(payload, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def object_record(row):
    return {k: json_value(row[k]) for k in row.index if k != "geometry"}


def profile(schema, name):
    return Draft202012Validator({"$schema": schema["$schema"], "$defs": schema["$defs"],
                                "$ref": "#/$defs/" + name}, format_checker=FormatChecker())


def local_source_context(bundle, cells):
    """IDs de contexte, sans recalcul des événements ni indicateur de pression."""
    result = defaultdict(dict)
    for file, layer, identifier, dimension in (
        ("routes.gpkg", "routes", "route_id", "length"),
        ("corridors.gpkg", "corridors", "objet_id", "area"),
        ("reservoirs.gpkg", "reservoirs", "objet_id", "area"),
    ):
        frame = gpd.read_file(bundle / "donnees" / file, layer=layer)
        for cell in cells.itertuples():
            ids = sorted(frame.iloc[i][identifier] for i in frame.sindex.query(cell.geometry, predicate="intersects")
                         if getattr(frame.geometry.iloc[i].intersection(cell.geometry), dimension) > 0)
            result[cell.maille_id][layer] = {"objet_ids": ids, "nombre_objets_locaux_observes": len(ids),
                "source_reference": "donnees/" + file + "#" + layer,
                "critere_geometrique": "portion de longueur positive" if dimension == "length" else "portion de surface positive",
                "completude_ecologique_validee": False,
                "interpretation": "contexte cartographique ; aucun signal écologique dérivé du compte"}
    return result


def build(out):
    bundle = out / "M2_CAEN_NORD_FINAL_M1_M2_20261111_V1"
    bundle.mkdir(exist_ok=False)
    for name in ("donnees", "rapports", "provenance", "outils", "specification"):
        (bundle / name).mkdir()
    # Le lot SIG connu de M4 est copié sans réécriture, ainsi que ses preuves.
    for folder in ("donnees", "rapports", "provenance"):
        for p in (BASE / folder).iterdir():
            if p.is_file():
                shutil.copyfile(p, bundle / folder / p.name)
    shutil.copyfile(BASE / "FORMAT.md", bundle / "FORMAT_SIG_M2.md")
    shutil.copyfile(BASE / "outils/verifier_lot.py", bundle / "outils/verifier_lot_sig.py")
    shutil.copyfile(BASE / "outils/lire_fiche.py", bundle / "outils/lire_fiche_sig.py")
    raw_dest = bundle / "provenance/complement_M1"
    shutil.copytree(RAW, raw_dest)
    for p in ("couches_m1_complement.gpkg", "indicateurs_complement_66_mailles.csv"):
        # Les données ont un emplacement unique ; garder le manifeste et les pages brutes à part.
        (raw_dest / p).rename(bundle / "donnees" / p)
    for name in ("rules_actions.json", "schema_actions_m2.json", "regles_actions_m2.md", "dictionnaire_faits_actions_m2.md", "api_contract_m2_m4.md"):
        shutil.copyfile(ROOT / "docs" / name, bundle / "specification" / name)
    mf = json.loads((RAW / "manifest_m1_complement.json").read_text())
    assert mf["version"] == COMPLEMENT and mf["grid_features"] == 66 and mf["grid_version"] == SCOPE["grid_version"]
    assert mf["crs"] == "EPSG:2154" and mf["scientific_qualification"] == "non_evaluee"
    assert sha(RAW / mf["outputs"]["gpkg"]) == mf["outputs"]["gpkg_sha256"]
    assert sha(RAW / mf["outputs"]["indicateurs_csv"]) == mf["outputs"]["indicateurs_csv_sha256"]
    reference = json.loads((BASE / "provenance/manifest_execution_original.json").read_text())
    assert mf["source_zip_sha256"] == reference["archive"]["sha256"]
    raw_audit = []
    for kind, info in mf["sources"].items():
        seen = set()
        for raw in info.get("raw_pages", []):
            p = RAW / "raw_wfs" / Path(raw["file"]).name
            assert sha(p) == raw["sha256"]
            payload = json.loads(p.read_text())
            assert payload["type"] == "FeatureCollection" and len(payload["features"]) == raw["features"]
            assert payload["crs"]["properties"]["name"].endswith("2154")
            ids = [f["id"] for f in payload["features"]]
            assert len(set(ids)) == len(ids) and not seen.intersection(ids)
            seen.update(ids)
            raw_audit.append({"file": p.name, "kind": kind, "count": len(ids), "sha256": sha(p)})
    csv = pd.read_csv(RAW / "indicateurs_complement_66_mailles.csv")
    assert len(csv) == 66 and not csv.duplicated(["grid_version", "maille_id"]).any()
    assert set(csv.grid_version) == {SCOPE["grid_version"]}
    data = bundle / "donnees/m4_interne.gpkg"
    cells = gpd.read_file(data, layer="mailles").sort_values("maille_id").reset_index(drop=True)
    enjeux = gpd.read_file(data, layer="enjeux").set_index("maille_id")
    events = gpd.read_file(data, layer="evenements")
    quarantine = gpd.read_file(data, layer="quarantaine")
    with sqlite3.connect(data.as_uri() + "?mode=ro", uri=True) as db:
        links = pd.read_sql_query("SELECT * FROM liens_mailles_evenements", db)
    assert (len(cells), len(events), len(quarantine), len(links)) == (66, 3156, 1, 3400)
    assert set(csv.maille_id) == set(cells.maille_id)
    assert not set(quarantine.conflit_id).intersection(links.conflit_id)
    for frame in (cells, events, quarantine):
        for key in ("territory_id", "grid_version", "dataset_version"):
            assert set(frame[key]) == {SCOPE[key]}
    local = links.groupby("maille_id").conflit_id.nunique().reindex(cells.maille_id, fill_value=0)
    assert local.tolist() == cells.nb_evenements_observes.tolist()
    assert (int(local.gt(0).sum()), int(local.eq(0).sum())) == (40, 26)
    csv = csv.set_index("maille_id").loc[cells.maille_id].reset_index()
    # CSV écrit par M1 avec %.6f : vérification à sa résolution d'arrondi,
    # sans seuil écologique ni modification des tolérances de frontière M2.
    assert all(abs(a - b) <= 0.5001e-6 for a, b in zip(csv.clipped_area_m2, cells.study_area_m2))
    layer_specs = {"haies": ("length", "haies_longueur_m_observe", "haies_nombre_observe", 733),
                   "plans_eau": ("area", "plans_eau_surface_m2_observe", "plans_eau_nombre_observe", 4)}
    observed_objects, object_links, comparisons, geometry_audit = {}, [], [], {}
    for kind, (measure, metric, counter, expected) in layer_specs.items():
        frame = gpd.read_file(RAW / "couches_m1_complement.gpkg", layer=kind)
        assert len(frame) == expected and frame.crs.to_epsg() == 2154
        assert frame.geometry.notna().all() and not frame.is_empty.any() and frame.is_valid.all()
        assert frame.source_id_m1_complement.notna().all() and frame.source_id_m1_complement.is_unique and frame.cleabs.is_unique
        observed_objects[kind] = frame.set_index("source_id_m1_complement")
        geometry_audit[kind] = {"count": len(frame), "crs": "EPSG:2154", "types": frame.geom_type.value_counts().to_dict(),
                               "nulls": {k: int(frame[k].isna().sum()) for k in frame.columns if k != "geometry"}}
        for _, cell in cells.iterrows():
            n, measured = 0, 0.0
            for position in frame.sindex.query(cell.geometry, predicate="intersects"):
                source = frame.iloc[position]
                overlap = source.geometry.intersection(cell.geometry)
                value = float(getattr(overlap, measure))
                if value <= 0:
                    continue
                n += 1
                measured += value
                object_links.append({**SCOPE, "complement_dataset_version": COMPLEMENT, "maille_id": cell.maille_id,
                    "source_couche": kind, "source_id_m1_complement": source.source_id_m1_complement,
                    "cleabs": source.cleabs, "length_m": value if measure == "length" else None,
                    "area_m2": value if measure == "area" else None})
            row = csv.loc[csv.maille_id == cell.maille_id].iloc[0]
            assert n == row[counter], (kind, cell.maille_id, n, row[counter])
            difference = abs(measured - row[metric])
            assert difference <= 0.5001e-6, (kind, cell.maille_id, difference)
            comparisons.append({"maille_id": cell.maille_id, "source_couche": kind,
                                "count": n, "csv_count": int(row[counter]), "metric_recomputed": measured,
                                "metric_csv": float(row[metric]), "absolute_difference": difference})
    for kind in ("haies", "plans_eau", "mares_referencees"):
        assert set(csv[kind + "_statut_couverture"]) == {"presence_observee_non_exhaustive"}
        assert mf["sources"][kind]["completeness_validated"] is False
    for kind in ("friches", "zones_humides"):
        assert mf["sources"][kind]["status"] == "non_charge"
        assert csv[[kind + "_surface_m2_observe", kind + "_nombre_observe"]].isna().all().all()
    assert csv[["priorite_ecologique", "method_version"]].isna().all().all()
    plans = observed_objects["plans_eau"]
    assert not plans.nature.str.strip().str.casefold().eq("mare").any()
    assert csv.mares_referencees_nombre_observe.eq(0).all()
    # Une extension séparée, aucune modification du GeoPackage M4 d'origine.
    extension = cells[["maille_id", "geometry"]].merge(csv, on="maille_id", validate="one_to_one")
    for key, value in {**SCOPE, "complement_dataset_version": COMPLEMENT}.items():
        extension[key] = value
    extension.to_file(bundle / "donnees/complement_mailles.gpkg", layer="mailles_complement", driver="GPKG", engine="pyogrio")
    objlinks = pd.DataFrame(object_links)
    with sqlite3.connect(bundle / "donnees/complement_mailles.gpkg") as db:
        objlinks.to_sql("liens_mailles_objets", db, index=False, if_exists="fail")
        db.execute("CREATE UNIQUE INDEX objets_uniques ON liens_mailles_objets (territory_id,grid_version,dataset_version,complement_dataset_version,maille_id,source_couche,source_id_m1_complement)")
        db.execute("INSERT INTO gpkg_contents (table_name,data_type,identifier,description,last_change) VALUES ('liens_mailles_objets','attributes','liens_mailles_objets','Relations descriptives aux objets M1, sans propriétaire écologique',strftime('%Y-%m-%dT%H:%M:%fZ','now'))")
    by_cell = defaultdict(lambda: defaultdict(list))
    for row in object_links:
        by_cell[row["maille_id"]][row["source_couche"]].append(row)
    event_index = events.set_index("conflit_id")
    rules = json.loads((ROOT / "docs/rules_actions.json").read_text())
    schema = json.loads((ROOT / "docs/schema_actions_m2.json").read_text())
    input_validator, output_validator = profile(schema, "normalizedInput"), profile(schema, "actionResult")
    rules_index = {r["rule_id"]: r for r in rules["rules"]}
    rows, action_inputs, action_results = [], [], []
    source_context = local_source_context(bundle, cells)
    for _, cell in cells.iterrows():
        mid = cell.maille_id
        c = csv.loc[csv.maille_id == mid].iloc[0]
        e = enjeux.loc[mid]
        cell_links = links.loc[links.maille_id == mid]
        ids = sorted(cell_links.conflit_id)
        selected = event_index.loc[ids] if ids else events.iloc[:0].set_index("conflit_id")
        service_candidates, road_context = [], []
        for cid, event in selected.iterrows():
            attrs = json.loads(event.observations)["routes"]["attributes"]
            road_context.append({"conflit_id": cid, "statut": event.statut, "territory_relation": event.territory_relation,
                                 **{k: attrs.get(k) for k in ("categorie", "importance", "nombre_voies", "largeur_chaussee", "position_sol", "precision_planimetrique_m", "statut_objet", "contexte_urbain", "vitesse_moyenne_vl_source", "ouvrage_connu", "millesime")}})
            if event.statut == "croisement_detecte" and event.territory_relation != "frontiere" and attrs.get("statut_objet") == "En service":
                service_candidates.append(cid)
        observations = {"contexte_sources": source_context[mid], "routes_corridors": {"etat": "observations_geometriques" if ids else "aucun_evenement_observe_absence_non_demontree",
            "nb_evenements_observes": int(cell.nb_evenements_observes),
            "nb_evenements_exclusifs_observes": int(cell.nb_evenements_exclusifs_observes), "nb_evenements": None,
            "conflit_ids": ids, "nb_candidats_en_service_a_revoir": len(service_candidates), "contexte_routier": road_context},
            "reservoirs_corridors": object_record(e.drop(labels=["geometry"], errors="ignore"))}
        for kind, (_, metric, counter, _) in layer_specs.items():
            referenced = by_cell[mid][kind]
            observations[kind] = {"etat": "presence_observee" if referenced else "aucune_observation_absence_non_demontree",
                "nombre_observe": int(c[counter]), "mesure_observee": float(c[metric]),
                "unite": "m" if kind == "haies" else "m2", "statut_couverture": c[kind + "_statut_couverture"],
                "completude_ecologique_validee": False,
                "objets": [{**r, "attributs_source": object_record(observed_objects[kind].loc[r["source_id_m1_complement"]])} for r in referenced],
                "source_reference": "donnees/couches_m1_complement.gpkg#" + kind}
        observations["mares_referencees"] = {"nombre_observe": 0, "etat": "aucun_objet_selon_filtre_nature_Mare_absence_non_demontree", "filtre": mf["sources"]["mares_referencees"]["rule"], "completude_ecologique_validee": False}
        for kind in ("friches", "zones_humides"):
            observations[kind] = {"etat": "non_charge", "nombre_observe": None, "surface_m2_observe": None, "statut_couverture": "non_evalue"}
        diagnostics, pistes, results_local = [], [], []
        for rule, family in FAMILIES.items():
            definition = rules_index[rule]
            diagnostic_id = "diag:" + mid + ":" + rule
            diagnostics.append({"diagnostic_id": diagnostic_id, "famille": family,
                "qualification_ecologique": "non_evaluable", "faits_disponibles": "observations." + ({"R1": "routes_corridors", "R2": "haies", "R3": "friches", "R4": "plans_eau"}[rule]),
                "conditions_manquantes": MISSING[rule], "problemes_ecologiques_confirmes": {"etat": "non_evalue", "objets": []}})
            inp = {"maille_id": mid, "diagnostic_ids": [diagnostic_id], "rule_id": rule, "action_id": definition["action_id"],
                "rule_version": definition["rule_version"], "applicabilite": "inconnue", "applicabilite_reference": None,
                "methode_validee": False, "methode_reference": None, "couverture_essentielle": "insuffisante",
                "signal": "inconnu", "preuve_ids": [], "preuve_absence_ids": [], "controle_contradiction": "non_evaluee",
                "contradiction_references": [], "independance_reference": None, "limites": LIMITS,
                "family_evidence": {"etat": "en_attente", "rule_id": rule, "maille_id": mid, "diagnostic_ids": [diagnostic_id],
                    "qualification": "inconnu", "manquants": MISSING[rule], "limites": LIMITS,
                    "reference_analyse": "fiches_zones.json#" + mid}}
            input_validator.validate(inp)
            # Contrôle de précédence uniquement sur les prérequis présents :
            # aucun déclencheur positif ou négatif familial n'est fabriqué.
            predicates = [node for node in rules["shared_precedence"] if node.get("code") in ("A0", "A1", "A2")]
            first = next(node for node in predicates if Draft202012Validator(node["predicate_schema"]).is_valid(inp))
            assert first["code"] == "A2"
            result = {"maille_id": mid, "diagnostic_ids": [diagnostic_id], "phenomene_ids": [],
                "rule_id": rule, "action_id": definition["action_id"], "rule_version": definition["rule_version"],
                "ruleset_version": rules["ruleset_version"], "contract_revision": rules["contract_revision"],
                "statut": first["output"], "regle_decision": first["code"], "motif_principal": first["reason"],
                "preuve_ids": [], "preuve_absence_ids": [], "attestation_ids": [], "conflit_ids": ids if rule == "R1" else [],
                "applicabilite_reference": None, "contradiction_references": [], "limites": LIMITS,
                "prerequis_a_verifier": MISSING[rule], "methode": None,
                "qualite": {"couverture_essentielle": "insuffisante", "methode_validee": False, "couverture_references": []},
                "etat_validation": "structure_seule", "validation_reference": None, "authentifie_par_logiciel": False,
                "justification_courte": "Préconditions de qualification non satisfaites : " + "; ".join(MISSING[rule])}
            output_validator.validate(result)
            action_inputs.append(inp); action_results.append(result); results_local.append(result)
            justified = bool(service_candidates) if rule == "R1" else bool(by_cell[mid]["haies"]) if rule == "R2" else bool(by_cell[mid]["plans_eau"]) if rule == "R4" else False
            if justified:
                title = {"R1": "Préparer une investigation locale de perméabilité sur les candidats en service", "R2": "Qualifier le contexte et l'état des haies cartographiées avant toute recherche de lacune", "R4": "Qualifier les plans d'eau et leur contexte hydrologique, sans les assimiler à des mares"}[rule]
                pistes.append({"rule_id": rule, "action_id_reference": definition["action_id"],
                    "nature": "preparation_investigation_documentaire", "titre": title,
                    "justification": f"{len(service_candidates)} candidats XY sur voies en service" if rule == "R1" else f"{int(c['haies_nombre_observe'])} objets de haies observés" if rule == "R2" else f"{int(c['plans_eau_nombre_observe'])} plans d'eau observés, nature source à conserver",
                    "conflit_ids_exemples": service_candidates[:3] if rule == "R1" else [],
                    "conditions": MISSING[rule], "statut_action_associee": "non_evaluable",
                    "qualification_A6": False, "recommandation_travaux": False})
        rows.append({**SCOPE, "complement_dataset_version": COMPLEMENT, "fiche_id": "fiche:" + cell.maille_id,
            "maille_id": mid, "support": {"study_area_m2": float(cell.study_area_m2), "is_boundary": bool(c.is_boundary)},
            "diagnostic_synthetique": f"{len(ids)} événements XY locaux ({int(cell.nb_evenements_exclusifs_observes)} exclusifs), {int(c.haies_nombre_observe)} haies et {int(c.plans_eau_nombre_observe)} plans d'eau observés ; fonctionnalité écologique non qualifiée.",
            "observations": observations, "diagnostics": diagnostics, "actions": results_local,
            "pistes_investigation": pistes, "recommandations_validees": [],
            "etat_recommandations": "aucune_validation_fournie_pas_de_travaux_prescrits",
            "priorite_ecologique": {"conclusion": "indeterminee", "valeur": None, "motifs": ["enjeu_categoriel_non_documente", "methodes_et_configuration_pilote_non_approuvees", "qualification_ecologique_insuffisante"]},
            "priorite_examen": {"etat": "non_calculee", "valeur": None}, "regle_synthese": None,
            "sources": {"sig": "provenance/manifest_execution_original.json", "complement": "provenance/complement_M1/manifest_m1_complement.json", "regles": "specification/rules_actions.json"},
            "qualite": {"qualification_ecologique": "non_evaluee", "completude_ecologique_complement_validee": False,
                "source_m1_territory_id": "CAEN-NORD-5COM-V1", "quarantaine_incluse_dans_comptes": False}, "limites": LIMITS})
    assert len(rows) == 66 and len({r["maille_id"] for r in rows}) == 66
    assert len(action_inputs) == len(action_results) == 264
    assert sha(data) == sha(BASE / "donnees/m4_interne.gpkg")
    envelope = {"format_version": FORMAT, "usage": "interne_provisoire_independant_frontend",
                "scope": SCOPE, "complement_dataset_version": COMPLEMENT, "public_export": False,
                "catalogue_M5_disponible": False, "schema_M4_confirme": False}
    write(bundle / "fiches_zones.json", {**envelope, "fiches": rows})
    write(bundle / "actions_entrees.json", {**envelope, "profile": "normalizedInput", "entrees": action_inputs})
    write(bundle / "actions_resultats.json", {**envelope, "profile": "actionResult", "portee": "controle_des_prerequis_A2_seulement", "resultats": action_results})
    write(bundle / "references_actions.json", {"source": "specification/rules_actions.json", "catalogue_officiel_M5": None,
        "appariements_connus": [{"rule_id": r["rule_id"], "action_id": r["action_id"], "nom_specification": r["name"]} for r in rules["rules"]],
        "contenus_des_12_fiches_M5": "non_fournis_non_inventes"})
    pistes_count = Counter(p["rule_id"] for r in rows for p in r["pistes_investigation"])
    summary = {"scope": SCOPE, "complement_dataset_version": COMPLEMENT, "fiches": 66,
        "evenements_detectes": 3157, "evenements_agreges": 3156, "evenements_en_quarantaine": 1,
        "mailles_avec_evenements": 40, "mailles_sans_evenement": 26,
        "haies_objets": 733, "haies_liens_mailles": sum(r["source_couche"] == "haies" for r in object_links),
        "haies_mailles_presence": int(csv.haies_nombre_observe.gt(0).sum()), "haies_mailles_zero_observe": int(csv.haies_nombre_observe.eq(0).sum()),
        "haies_longueur_csv_m": float(csv.haies_longueur_m_observe.sum()),
        "plans_eau_objets": 4, "plans_eau_liens_mailles": sum(r["source_couche"] == "plans_eau" for r in object_links),
        "plans_eau_mailles_presence": int(csv.plans_eau_nombre_observe.gt(0).sum()),
        "plans_eau_natures": plans.nature.value_counts().to_dict(), "plans_eau_surface_csv_m2": float(csv.plans_eau_surface_m2_observe.sum()),
        "mares_referencees": 0, "absence_ecologique_mares_demontree": False, "friches_chargees": False, "zones_humides_chargees": False,
        "evaluations_actions": 264, "resultats_actions": dict(Counter(a["statut"] for a in action_results)),
        "recommandations_etayees": 0, "actions_conditionnelles": 0, "travaux_recommandes": 0,
        "pistes_documentaires": dict(pistes_count), "total_pistes_documentaires": sum(pistes_count.values()),
        "mailles_avec_piste_documentaire": sum(bool(r["pistes_investigation"]) for r in rows),
        "priorites_ecologiques_indeterminees": 66, "synthese_D_S_executee": False,
        "sig_routes_corridors_relance": False, "M4_GPKG_original_sha256": sha(data)}
    write(bundle / "rapports/bilan_final.json", summary)
    write(bundle / "rapports/validation_complement.json", {"ok": True, "scope": SCOPE,
        "csv_rows": 66, "join_keys": ["grid_version", "maille_id"], "bijective_join": True,
        "raw_pages": raw_audit, "interfaces": geometry_audit, "geometric_comparisons": comparisons,
        "csv_rounding_resolution": "six décimales dans le CSV M1 ; vérification à 0,5001e-6 unité, sans portée écologique",
        "source_csv_preserved": True, "source_gpkg_preserved": True,
        "old_event_counts_unchanged": True, "normalizedInputs_validated": 264, "actionResults_validated": 264,
        "action_precedence_checked": "A0 et A1 ne correspondent pas ; première règle A2 sur tous les dossiers",
        "catalogue_M5_contents_invented": False, "frontend_contract_invented": False})
    return bundle, summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "data/derived/caen_nord_5communes/final_m1_m2_20261111_01")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    bundle, summary = build(args.output.resolve())
    print(json.dumps({"bundle": str(bundle), **summary}, ensure_ascii=False, indent=2))
