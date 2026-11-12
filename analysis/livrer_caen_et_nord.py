"""Vue GeoJSON interne, classification documentaire séparée et fiches territoriales.

N'utilise pas l'exporteur public, ne marque pas des données réelles comme TEST,
ne modifie aucune règle D/S, R1–R4 ou V1–V4. Les sorties restent privées.
"""
from __future__ import annotations
from collections import Counter, defaultdict
import importlib.util
import json
import shutil
import sqlite3

import geopandas as gpd
import pandas as pd
from shapely import force_2d
from shapely.geometry import mapping
from shapely.ops import orient

from analysis.detect_conflicts import json_value
from analysis.integrer_complement_caen_nord import profile
from analysis.preparer_caen_et_nord import ROOT, RAW, PROC, OUT, GRID, TERRITORY, DATASET, write, sha

BUNDLE = OUT / "RECONNECT_CAEN_ET_NORD_M2_DEMO_INTERNE_20261111_V1"
SCOPE = {"territory_id": TERRITORY, "grid_version": GRID, "dataset_version": DATASET, "method_version": None}
LIMITS = ["Indices cartographiques à vérifier — analyse exploratoire", "Une intersection XY n'est pas un obstacle confirmé",
          "La co-présence dans une maille n'établit pas une connexion fonctionnelle", "Inventaires écologiques non exhaustifs et sous-trames de matrices inconnues",
          "Aucune urgence, gravité, efficacité ou prescription de travaux calculée"]


def geojson(frame, properties):
    projected = frame.to_crs("OGC:CRS84")
    return {"type": "FeatureCollection", "format_version": "reconnect.vue-interne-1", "dataNature": "reelle",
            "diffusion": "interne_revue_uniquement", "publication_autorisee": False, "scope": SCOPE,
            "features": [{"type": "Feature", "geometry": mapping(orient(force_2d(g), sign=1.0)), "properties": p}
                         for g, p in zip(projected.geometry, properties)]}


def main():
    BUNDLE.mkdir(exist_ok=False)
    for name in ("demo_interne", "donnees", "rapports", "provenance", "integration"):
        (BUNDLE / name).mkdir()
    work = OUT / "calculs_m2"
    grid = gpd.read_file(PROC / "grille.gpkg", layer="mailles").sort_values("maille_id").reset_index(drop=True)
    cells = gpd.read_file(work / "mailles.gpkg", layer="mailles_conflits").set_index("maille_id")
    enjeux = gpd.read_file(work / "enjeux.gpkg", layer="indicateurs_enjeux").set_index("maille_id")
    events = gpd.read_file(work / "evenements.gpkg", layer="conflits_candidates")
    quarantine = gpd.read_file(work / "quarantaine.gpkg", layer="quarantaine") if (work / "quarantaine.gpkg").exists() else events.iloc[:0].copy()
    metadata = json.loads((OUT / "sources_preparees.json").read_text())["sources"]
    metadata.update(json.loads((OUT / "sources_optionnelles_preparees.json").read_text()))
    sources = {k: gpd.read_file(ROOT / v["file"], layer=k) for k, v in metadata.items() if v["status"] == "processed"}
    with sqlite3.connect((work / "mailles.gpkg").as_uri() + "?mode=ro", uri=True) as db:
        links = pd.read_sql_query("SELECT * FROM liens_mailles_conflits", db)
    assert set(grid.maille_id) == set(cells.index) == set(enjeux.index)
    table = json.loads((ROOT / "docs/table_triage_exploratoire.json").read_text())
    spec = importlib.util.spec_from_file_location("conventions_documentaires", ROOT / "analysis/construire_fiches_66.py")
    conventions = importlib.util.module_from_spec(spec);spec.loader.exec_module(conventions)
    assert conventions.CATEGORIES_CARROSSABLES == {"Route à 1 chaussée", "Route à 2 chaussées", "Type autoroutier", "Bretelle", "Rond-point"}
    assert table["legend"] == conventions.PRIORITE_PALETTE
    assert sources["routes"].categorie.isin(conventions.CATEGORIES_CARROSSABLES).any()
    assert sources["corridors"].classe_corridor.eq(conventions.NATURE_MATRICE_FRAGILE).any()
    for field in ("categorie", "statut_objet", "position_sol"):
        assert field in sources["routes"]
    for f in ("table_triage_exploratoire.json", "rules_actions.json", "schema_actions_m2.json"):
        shutil.copyfile(ROOT / "docs" / f, BUNDLE / "provenance" / f)
    schema = json.loads((ROOT / "docs/schema_actions_m2.json").read_text())
    action_validator = profile(schema, "actionResult")
    rules = json.loads((ROOT / "docs/rules_actions.json").read_text())
    definitions = {r["rule_id"]: r for r in rules["rules"]}
    missing = {
        "R1": ["Sous-trame pertinente et qualité de localisation bilatérale", "Ouvrages, espèces et perméabilité réelle", "Méthode familiale et contrôle des contradictions approuvés"],
        "R2": ["Sous-trame bocagère pertinente", "Analyse de lacune/topologie et état fonctionnel du réseau", "Méthode familiale approuvée"],
        "R3": ["Statut actuel et éligibilité écologique du site", "Relation à une continuité selon une méthode de voisinage approuvée", "Contexte foncier, pollution et méthode familiale approuvée"],
        "R4": ["Inventaire de mares/habitats pertinents et couvertures adaptées", "Analyse de réseau/isolement et contexte hydrologique", "Méthode familiale approuvée"],
    }
    # Listes fermées pour ne pas diffuser les propriétaires, contacts ou noms d'interprètes.
    allowed = {
        "haies": ["objet_id", "cleabs", "hauteur", "largeur", "precision_planimetrique", "date_modification"],
        "plans_eau": ["objet_id", "cleabs", "nature", "statut", "date_modification"],
        "friches": ["objet_id", "site_id", "site_type", "site_statut", "site_actu_date", "nature"],
        "zones_humides": ["objet_id", "pk_zh", "typo", "diag", "qualite", "leg_simpl", "id_source", "id_echelle"],
        "corridors": ["objet_id", "classe_corridor", "sous_trame", "millesime", "precision_source"],
        "reservoirs": ["objet_id", "sous_trame", "millesime", "precision_source"],
        "routes": ["route_id", "categorie", "importance", "nombre_voies", "largeur_chaussee", "position_sol", "statut_objet", "contexte_urbain", "vitesse_moyenne_vl_source", "precision_planimetrique_m", "millesime", "ouvrage_connu"],
    }
    for kind, source in sources.items():
        source[[c for c in allowed[kind] if c in source] + ["geometry"]].to_file(BUNDLE / "donnees/sources_consultables.gpkg", layer=kind, engine="pyogrio")
    for file in ("grille.gpkg", "territoire.gpkg"):
        shutil.copyfile(PROC / file, BUNDLE / "donnees" / file)
    # GeoPackages canoniques indivisibles avec leurs rapports : chemins historiques conservés.
    for path in work.iterdir():
        if path.is_file():
            shutil.copyfile(path, BUNDLE / "rapports" / path.name)
    event_index = events.set_index("conflit_id")
    fiches, props, actions_results, observation_links = [], [], [], []
    colors, investigations, technical_gray = Counter(), Counter(), []
    for cell in grid.itertuples():
        mid = cell.maille_id
        local_ids = sorted(links.loc[links.maille_id == mid, "conflit_id"])
        native = cells.loc[mid];enj = enjeux.loc[mid]
        observations = {}; source_ids = {}
        for kind, source in sources.items():
            objects, clips = [], []
            for position in source.sindex.query(cell.geometry, predicate="intersects"):
                row = source.iloc[position]
                clipped = row.geometry.intersection(cell.geometry)
                value = float(clipped.length if kind in {"haies", "routes"} else clipped.area)
                if value <= 0:
                    continue
                oid = row["route_id"] if kind == "routes" else row["objet_id"]
                objects.append({k: json_value(row[k]) for k in allowed[kind] if k in row.index})
                clips.append(clipped)
                observation_links.append({**SCOPE, "maille_id": mid, "source_couche": kind, "objet_id": oid,
                                          "measure": value, "unit": "m" if kind in {"haies", "routes"} else "m2"})
            measure = sum(g.length for g in clips) if kind in {"haies", "routes"} else float(gpd.GeoSeries(clips, crs=2154).union_all().area) if clips else 0.0
            observations[kind] = {"nombre_objets_observes": len(objects), "mesure_observee": measure,
                "unite": "m" if kind in {"haies", "routes"} else "m2", "objets": objects,
                "disponibilite": "observee" if objects else "aucun_objet_observe_absence_non_demontree",
                "completude_ecologique_validee": False, "source_reference": "donnees/sources_consultables.gpkg#" + kind}
            source_ids[kind] = [o.get("route_id", o.get("objet_id")) for o in objects]
        for kind in allowed:
            if kind not in observations:
                observations[kind] = {"nombre_objets_observes": None, "mesure_observee": None, "objets": [], "disponibilite": "source_non_utilisable", "completude_ecologique_validee": False}
        pairs = {}; eligible_ids = []; nonconclusive = []
        for cid in local_ids:
            event = event_index.loc[cid]
            local_part = event.geometry.intersection(cell.geometry)
            if event.statut == "non_concluant" or event.territory_relation == "frontiere":
                nonconclusive.append(cid);continue
            if local_part.length <= 0 or event.intersection_dimension != "lineaire":
                continue
            info = json.loads(event.observations)
            ra, ca = info["routes"]["attributes"], info["corridors"]["attributes"]
            eligible_ids.append(cid)
            for rid, coid in json.loads(event.source_pairs):
                key = (rid, coid)
                if key not in pairs:
                    pairs[key] = {"route_id": rid, "corridor_id": coid, "conflit_ids": [],
                        "categorie": ra.get("categorie"), "statut_objet": ra.get("statut_objet"), "position_sol": ra.get("position_sol"),
                        "importance": ra.get("importance"), "classe_corridor": ca.get("classe_corridor")}
                pairs[key]["conflit_ids"].append(cid)
        positive_fragile = [p for p in pairs.values() if p["categorie"] in conventions.CATEGORIES_CARROSSABLES and p["statut_objet"] == "En service" and str(p["position_sol"]) == "0" and p["classe_corridor"] == conventions.NATURE_MATRICE_FRAGILE]
        doc_obs = {"nombre_paires_route_corridor_2d": len(pairs), "paires_route_matrice_fragile_en_service_au_sol": len(positive_fragile),
                   "reservoir_presence_surface_positive": observations["reservoirs"]["mesure_observee"] > 0,
                   "corridor_presence_surface_positive": observations["corridors"]["mesure_observee"] > 0}
        ambiguity = bool(nonconclusive and not pairs)
        ambiguity = ambiguity or any(p.get(k) is None for p in pairs.values() for k in ("categorie", "statut_objet", "position_sol", "classe_corridor"))
        q_local = [q.conflit_id for q in quarantine.itertuples() if q.geometry.intersects(cell.geometry)]
        ambiguity = ambiguity or bool(q_local and not pairs)
        relevant_missing = any(observations[k]["disponibilite"] == "source_non_utilisable" for k in ("routes", "reservoirs", "corridors"))
        triage = conventions.color_rule(doc_obs)
        if ambiguity or relevant_missing:
            triage = {"niveau": "gris", "regle": "V4", "titre": "Vérification technique nécessaire", "motif": "Éléments seulement non concluants/en quarantaine ou source critique indisponible ; aucun ordre documentaire attribué par défaut."}
            technical_gray.append(mid)
        triage.update(couleur_hex=table["legend"][triage["niveau"]], validation_ecologique=False,
            definition_version=table["version"], application_version="caen6-documentaire-20261111-1",
            sources=["provenance/table_triage_exploratoire.json", "donnees/sources_consultables.gpkg"],
            disponibilite_donnees="a_revoir" if ambiguity or relevant_missing else "sources_critiques_acquises_completude_ecologique_inconnue",
            limites=LIMITS, observations_justificatives=doc_obs,
            paires_justificatives=list(pairs.values()), conflit_ids_justificatifs=sorted(set(eligible_ids)),
            reservoir_ids=source_ids["reservoirs"], corridor_ids=source_ids["corridors"])
        colors[triage["niveau"]] += 1
        mare_objects = [p for p in observations["plans_eau"]["objets"] if str(p.get("nature", "")).strip().casefold() == "mare"]
        wet_reservoirs = [p for p in observations["reservoirs"]["objets"] if p.get("sous_trame") == "Milieu humide"]
        active_sites = [p for p in observations["friches"]["objets"] if p.get("site_statut") in {"friche avec projet", "friche sans projet"}]
        applicable_investigation = {"R1": bool(pairs), "R2": bool(observations["haies"]["objets"] and (observations["corridors"]["objets"] or observations["reservoirs"]["objets"])),
                                   "R3": bool(active_sites), "R4": bool(mare_objects or observations["plans_eau"]["objets"] or wet_reservoirs)}
        action_details, diagnostics = [], []
        for rule in ("R1", "R2", "R3", "R4"):
            aid = definitions[rule]["action_id"];did = "diag:" + GRID + ":" + mid + ":" + rule
            formal = {"maille_id": mid, "diagnostic_ids": [did], "phenomene_ids": [], "rule_id": rule, "action_id": aid,
                "rule_version": rules["ruleset_version"], "ruleset_version": rules["ruleset_version"], "contract_revision": "audit-2",
                "statut": "non_evaluable", "regle_decision": "A2", "motif_principal": "domaine_methode_ou_donnees_insuffisants",
                "preuve_ids": [], "preuve_absence_ids": [], "attestation_ids": [], "conflit_ids": local_ids if rule == "R1" else [],
                "applicabilite_reference": None, "contradiction_references": [], "limites": LIMITS,
                "prerequis_a_verifier": missing[rule], "methode": None, "qualite": {"couverture_essentielle": "insuffisante", "methode_validee": False, "couverture_references": []},
                "etat_validation": "structure_seule", "validation_reference": None, "authentifie_par_logiciel": False,
                "justification_courte": "; ".join(missing[rule])}
            action_validator.validate(formal);actions_results.append(formal)
            topic = {"R1": "Perméabilité des franchissements et ouvrages existants", "R2": "État et continuités du réseau de haies", "R3": "Statut des sites Cartofriches et relation aux continuités", "R4": "Qualification des plans d'eau et du réseau humide"}[rule]
            justification = {"R1": f"{len(pairs)} paires linéaires documentaires liées aux événements M2 admis", "R2": f"{observations['haies']['nombre_objets_observes']} haies observées, avec matrice ou réservoir dans la maille", "R3": f"{len(active_sites)} sites avec statut source friche, distincts des sites reconvertis", "R4": f"{observations['plans_eau']['nombre_objets_observes']} plans d'eau et {len(wet_reservoirs)} réservoirs de sous-trame humide observés"}[rule]
            action_details.append({"action_id": aid, "regle_id": rule, "titre": topic,
                "statut_regle_m2": "non_evaluable", "piste_investigation": "a_etudier" if applicable_investigation[rule] else "non_qualifiable",
                "observations_justificatives": justification, "conditions_satisfaites": ["Sources et géométries cartographiques disponibles"] if applicable_investigation[rule] else [],
                "conditions_manquantes": missing[rule], "motif": "Préparer une qualification locale ; aucun déclencheur écologique validé" if applicable_investigation[rule] else "Aucune piste locale suffisamment documentée par ces observations",
                "sources": source_ids, "niveau_de_validation": "documentaire_non_valide_ecologiquement", "travaux_preconises": False})
            diagnostics.append({"diagnostic_id": did, "famille": rule, "etat": "non_evaluable_ecologiquement", "observations_cartographiques": justification,
                                "motifs": missing[rule], "problemes_ecologiques_confirmes": None})
            if applicable_investigation[rule]:investigations[rule] += 1
        names = ", ".join(p["nom"] for p in json.loads(cell.communes))
        summary = f"{names} : {triage['titre']}. {len(local_ids)} événements XY locaux, sans obstacle confirmé. Priorité écologique indéterminée."
        fiche = {**SCOPE, "maille_id": mid, "secteur": names, "communes": json.loads(cell.communes), "surface_m2": cell.area_m2,
            "maille_partielle": bool(cell.is_boundary), "pilot_fraction": cell.pilot_fraction,
            "triage_documentaire": triage, "priorite_examen": {"etat": "non_calculee", "valeur": None},
            "priorite_ecologique": {"conclusion": "indeterminee", "couleur": "gris", "category": "INDETERMINATE", "scientific_validation": "PENDING"},
            "couverture_synthese": None, "regle_appliquee": None, "diagnostic_ids_justificatifs": [],
            "diagnostic_ids_non_evalues": [d["diagnostic_id"] for d in diagnostics], "motifs_limites": ["enjeu_ecologique_non_qualifie", "methodes_et_domaines_non_approuves", "absence_non_demontree"],
            "diagnostic_elus": {"resume": summary, "sens_couleur": triage["motif"], "principal_signal": triage["titre"],
                "trois_dimensions": {"enjeux_documentes": "Matrices et réservoirs cartographiés ; aucun niveau d'enjeu écologique attribué",
                    "activites_humaines_observees": f"{observations['routes']['nombre_objets_observes']} tronçons routiers sources observés ; effet écologique non quantifié",
                    "fiabilite": "Couverture non attestée ; sources SRCE 2014 et inventaires hétérogènes"}},
            "diagnostic_techniciens": {"observations": observations, "ENJ": {k: json_value(enj[k]) for k in enjeux.columns if k != "geometry"},
                "nb_evenements_observes": int(native.nb_evenements_observes), "nb_evenements_exclusifs_observes": int(native.nb_evenements_exclusifs_observes),
                "conflit_ids": local_ids, "nb_paires_documentaires_lineaires": len(pairs), "conflit_ids_non_concluants": nonconclusive,
                "quarantaine_a_proximite_technique": q_local, "mares_referencees": len(mare_objects), "absence_mares_demontree": False,
                "sites_friches_statut_actif": len(active_sites), "diagnostics": diagnostics},
            "actions": action_details, "action_ids_a_etudier": [a["action_id"] for a in action_details if a["piste_investigation"] == "a_etudier"],
            "action_ids_valides": [], "recommandations_validees": [], "validation_ecologique": False, "limites": LIMITS}
        fiches.append(fiche)
        props.append({**SCOPE, "maille_id": mid, "area_m2": cell.area_m2, "pilot_fraction": cell.pilot_fraction, "is_boundary": bool(cell.is_boundary),
            "caen_area_m2": cell.caen_area_m2, "triage_verification": triage["niveau"], "triage_couleur": triage["couleur_hex"], "triage_regle": triage["regle"],
            "triage_motif": triage["motif"], "validation_ecologique": False, "description_courte": summary,
            "priorite_examen": {"etat": "non_calculee", "valeur": None}, "priority_category": "INDETERMINATE", "priority_validation_status": "PENDING",
            "priority_method_version": None, "couverture_synthese": None, "regle_appliquee": None,
            "nb_evenements_observes": len(local_ids), "nb_evenements_exclusifs_observes": int(native.nb_evenements_exclusifs_observes),
            "conflit_ids": local_ids, "action_ids": fiche["action_ids_a_etudier"], "action_ids_valides": [], "diffusion": "interne_revue_uniquement"})
    write(BUNDLE / "demo_interne/mailles.geojson", geojson(grid, props))
    event_props = [{**SCOPE, "conflit_id": e.conflit_id, "maille_ids": json.loads(e.maille_ids), "source_pairs": json.loads(e.source_pairs),
                    "statut": e.statut, "evidence_level": e.evidence_level, "precision_affichage": e.precision_affichage,
                    "territory_relation": e.territory_relation, "limites": json.loads(e.limites), "diffusion": "interne_revue_uniquement"} for e in events.itertuples()]
    write(BUNDLE / "demo_interne/conflits.geojson", geojson(events, event_props))
    write(BUNDLE / "demo_interne/fiches_zones.json", {"format_version": "m2-m4.caen6.demonstration-interne-1", "scope": SCOPE,
        "classification_defaut": "triage_documentaire", "mention_obligatoire": LIMITS[0], "publication_autorisee": False, "fiches": fiches})
    write(BUNDLE / "demo_interne/actions_resultats.json", {"profile": "actionResult", "scope": SCOPE, "resultats": actions_results})
    pd.DataFrame(observation_links).to_json(BUNDLE / "donnees/liens_observations.json", orient="records", force_ascii=False, indent=2)
    for path in (OUT / "grille.validation.json", OUT / "sources_preparees.json", OUT / "sources_optionnelles_preparees.json"):
        if path.name == "sources_optionnelles_preparees.json":
            safe_report = json.loads(path.read_text())
            safe_report["zones_humides"].get("values", {}).pop("interpr", None)
            safe_report["privacy_redaction"] = "Les valeurs du nom des interprètes sont omises dans cette copie de consultation ; original conservé localement."
            write(BUNDLE / "rapports" / path.name, safe_report)
        else:
            shutil.copyfile(path, BUNDLE / "rapports" / path.name)
    historical = ROOT / "data/derived/caen_nord_5communes/final_m1_m2_20261111_01/M2_CAEN_NORD_FINAL_M1_M2_20261111_V1.zip"
    (BUNDLE / "historique").mkdir();shutil.copyfile(historical, BUNDLE / "historique" / historical.name)
    result = {"scope": SCOPE, "mailles": len(grid), "mailles_avec_surface_caen": int(grid.caen_area_m2.gt(0).sum()),
        "classifications_exploratoires": dict(colors), "priorites_ecologiques": {"indeterminee": len(grid)},
        "synthese_D_S_executee": False, "diagnostics_familiaux_non_evaluables": len(actions_results), "pistes_investigation": dict(investigations),
        "recommandations_validees": 0, "source_features": {k: len(v) for k, v in sources.items()},
        "mailles_grises_techniques": technical_gray, "historical_zip_sha256": sha(historical),
        "triage_definition_sha256": sha(ROOT / "docs/table_triage_exploratoire.json"),
        "triage_category_definition_sha256": sha(ROOT / "analysis/construire_fiches_66.py"),
        "privacy_fields_removed": ["proprio_nom", "proprio_personne", "source_contact", "interpr", "site_adresse", "long", "lat", "unite_fonciere_refcad"],
        "publication_autorisee": False, "public_export_gate_unchanged": True,
        "m2": json.loads((work / "resultats.json").read_text())}
    write(BUNDLE / "rapports/bilan.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
