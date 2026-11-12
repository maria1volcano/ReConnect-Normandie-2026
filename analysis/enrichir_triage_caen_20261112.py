"""Enrichir 101 fiches et comparer le triage documentaire, sans recalcul M2."""
from __future__ import annotations
from collections import Counter, defaultdict
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import shutil

import geopandas as gpd
from shapely import union_all

from analysis.auditer_mailles_grises_caen import ROOT, BASE, OUT
from analysis.preparer_ocsge_caen import PROC, RAW
from analysis.preparer_caen_et_nord import sha
from analysis.triage_documentaire_v2 import VERSION, VEGETATION_CS, AQUATIC_CS, classify

BUNDLE = OUT / "RECONNECT_CAEN_ET_NORD_TRIAGE_DOCUMENTAIRE_V2_20261112"


def load(p): return json.loads(Path(p).read_text())


def put(p, d):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def summarize(frame, cell, labels, kind):
    objects, parts = [], []
    classes = defaultdict(float);uses = defaultdict(float);artif = defaultdict(float)
    for pos in frame.sindex.query(cell, predicate="intersects"):
        r = frame.iloc[pos];piece = r.geometry.intersection(cell);area = float(piece.area)
        if area <= 0: continue
        parts.append(piece);classes[r.code_cs] += area;uses[r.code_us] += area
        obj = {"objet_id": r.objet_id, "code_cs": r.code_cs, "code_us": r.code_us, "millesime": str(r.millesime), "surface_locale_m2": area,
               "libelle_cs": labels.get(r.code_cs), "libelle_us": labels.get(r.code_us)}
        if kind == "artificialisation": obj["artif"] = r.artif;artif[str(r.artif)] += area
        objects.append(obj)
    objects.sort(key=lambda x: x["objet_id"])
    return {"nombre_objets_observes": len(objects), "mesure_observee": float(union_all(parts).area) if parts else 0.0,
        "unite": "m2", "objets": objects, "surface_par_code_cs_m2": dict(classes), "surface_par_code_us_m2": dict(uses),
        "surface_par_statut_artif_m2": dict(artif), "surface_polygones_vegetalises_m2": sum(a for k,a in classes.items() if k in VEGETATION_CS),
        "surface_polygones_arbores_m2": sum(a for k,a in classes.items() if k.startswith("CS2.1.1.")),
        "surface_polygones_arbustifs_m2": classes.get("CS2.1.2", 0.0), "surface_polygones_herbaces_m2": classes.get("CS2.2.1", 0.0),
        "surface_polygones_aquatiques_m2": sum(a for k,a in classes.items() if k in AQUATIC_CS), "surface_humide_m2": None,
        "statut_milieux_humides": "non_identifiables_par_la_nomenclature_OCS_GE_seule", "absence_ecologique_attestee": False,
        "completude_ecologique_validee": False, "millésime": "2023", "precision_source_m": None,
        "precision_source_description": "Métrique selon la spécification IGN ; aucune valeur numérique par objet",
        "disponibilite": "observee" if objects else "aucun_objet_observe_absence_non_demontree",
        "source_reference": "donnees/ocsge_complement.gpkg#" + kind,
        "limites": ["Surfaces de polygones de couverture dominante, pas une mesure de couvert végétal pur", "Végétation cultivée et ornementale incluse, sans inférence d'habitat naturel",
                    "Aucun corridor fonctionnel, mare ou zone humide confirmé par l'OCS GE seule", "Statut artif IGN décrit le sol, pas sa valeur écologique"]}


def main():
    observation_links={k:defaultdict(list)for k in ("haies","plans_eau")}
    for link in load(BASE / "donnees/liens_observations.json"):
        if link["source_couche"] in observation_links:observation_links[link["source_couche"]][link["maille_id"]].append(link)
    assert not BUNDLE.exists()
    # L'intégralité des fichiers du lot V1 décomposé a été vérifiée avant enrichissement.
    previous = load(BASE / "manifest.json")
    assert all(sha(BASE/n) == h for n,h in previous["files_sha256"].items())
    shutil.copytree(BASE, BUNDLE)
    ref = BUNDLE / "reference_v1";ref.mkdir()
    for name in ("manifest.json", "SHA256SUMS"):
        shutil.move(str(BUNDLE / name), str(ref / name))
    shutil.copyfile(BASE / "demo_interne/mailles.geojson", ref / "mailles.geojson")
    for name in ("README.md", "MESSAGE_M4_M5.md", "FORMAT_JSON.md"):
        shutil.copyfile(BASE / name, ref / name)
    for name in ("bilan.json", "acceptation.json", "validation_ensemble.json", "validation_navigateur.json", "compte_rendu.md"):
        shutil.move(str(BUNDLE / "rapports" / name), str(ref / name))
    for name in ("carte_exploratoire.png", "carte_priorite_ecologique.png"):
        shutil.move(str(BUNDLE / "rapports" / name), str(ref / name))
    for k in ("ocsge", "artificialisation"):
        frame = gpd.read_file(PROC / (k + ".gpkg"), layer=k)
        # Source physique exacte, sans noms de personnes ni autre attribut privé.
        frame.to_file(BUNDLE / "donnees/ocsge_complement.gpkg", layer=k, engine="pyogrio")
        shutil.copyfile(OUT / (k + ".validation.json"), BUNDLE / "rapports" / (k + ".validation.json"))
    with (RAW / "NomenclatureOCSGE.csv").open(encoding="utf-8-sig") as stream:
        labels = {r["CODE"]: r["LIBELLE"] for r in csv.DictReader(stream, delimiter=";")}
    shutil.copyfile(RAW / "NomenclatureOCSGE.csv", BUNDLE / "provenance/NomenclatureOCSGE.csv")
    sources = {k:gpd.read_file(PROC / (k + ".gpkg"), layer=k) for k in ("ocsge", "artificialisation")}
    coverage = {k:{r["maille_id"]:r for r in load(OUT/(k+".validation.json"))["couverture_par_maille"]} for k in sources}
    grid = gpd.read_file(BASE / "donnees/grille.gpkg", layer="mailles").set_index("maille_id")
    fiches_doc = load(BASE / "demo_interne/fiches_zones.json");cells = load(BASE / "demo_interne/mailles.geojson")
    audit = {r["maille_id"]:r for r in load(OUT / "audit_grises_v1.json")["mailles"]}
    technical_gray = set(load(BASE / "rapports/bilan.json")["mailles_grises_techniques"])
    cell_index = {f["properties"]["maille_id"]:f["properties"] for f in cells["features"]}
    transitions = []; colors = Counter(); allobs = []; enhanced_gray = []
    for f in fiches_doc["fiches"]:
        mid = f["maille_id"];geom = grid.loc[mid].geometry
        original = deepcopy(f["triage_documentaire"]);evidence = []
        local = {k:summarize(source, geom, labels, k) for k,source in sources.items()}
        for k in local:
            local[k]["couverture_geometrique"] = coverage[k][mid]
            allobs.append({"maille_id":mid,"grid_version":f["grid_version"],"territory_id":f["territory_id"],"couche":k,**local[k]})
        for k in ("haies", "plans_eau"):
            obs = f["diagnostic_techniciens"]["observations"][k]
            # La mesure par objet est obtenue dans les liens SIG existants, pas attribuée au voisin.
            ids = {o["objet_id"] for o in obs["objets"]}
            for link in observation_links[k].get(mid, []):
                assert link["objet_id"] in ids
                evidence.append({"couche":k,"objet_id":link["objet_id"],"mesure":link["measure"],"unite":link["unit"],
                    "dans_maille":True,"source_statut":"acquise_geometrie_valide","precision_source_m":3 if k=="haies" else None,
                    "source_reference":"donnees/sources_consultables.gpkg#"+k,"completude_ecologique_validee":False})
        for o in local["ocsge"]["objets"]:
            evidence.append({"couche":"ocsge","objet_id":o["objet_id"],"mesure":o["surface_locale_m2"],"unite":"m2","dans_maille":True,
                "source_statut":"acquise_geometrie_valide","code_cs":o["code_cs"],"code_us":o["code_us"],"millesime":"2023",
                "precision_source_m":None,"source_reference":"donnees/ocsge_complement.gpkg#ocsge","completude_ecologique_validee":False})
        proposed = classify(original, evidence, mid in technical_gray)
        f["triage_documentaire_reference_v1"] = original
        f["triage_documentaire"] = proposed
        f["enrichissement_20261112"] = {"observations_dans_maille":local,
            "contexte_voisinage":audit[mid]["contexte_voisinage"] if mid in audit else [],
            "distance_source":audit[mid]["distance_source"] if mid in audit else None,
            "precision_source":audit[mid]["precision_source"] if mid in audit else None,
            "statut_audit_voisinage":"audite_car_gris_V1" if mid in audit else "non_audite_dans_cet_examen_des_gris",
            "couvertures": {k:coverage[k][mid] for k in local}, "version":VERSION}
        f["diagnostic_techniciens"]["observations"].update(local)
        f["diagnostic_elus"]["resume"] = (f["secteur"] + " : " + proposed["titre"] + ". " +
            str(f["diagnostic_techniciens"]["nb_evenements_observes"]) + " événements XY locaux, sans obstacle confirmé. Priorité écologique indéterminée.")
        f["diagnostic_elus"]["sens_couleur"] = proposed["motif"]
        f["diagnostic_elus"]["principal_signal"] = proposed["titre"]
        existing_obs = f["diagnostic_techniciens"]["observations"]
        f["diagnostic_elus"]["trois_dimensions"]["enjeux_documentes"] = (
            f"{existing_obs['corridors']['nombre_objets_observes']} matrices et {existing_obs['reservoirs']['nombre_objets_observes']} réservoirs SRCE observés ; "
            f"{local['ocsge']['surface_polygones_vegetalises_m2']:.0f} m² de polygones classés végétalisés OCS GE 2023. Fonctionnalité et niveau d'enjeu écologique non qualifiés.")
        f["diagnostic_elus"]["trois_dimensions"]["fiabilite"] += "; OCS GE 2023 : couvertures et usages cartographiques, pas fonctionnalité écologique"
        p = cell_index[mid]
        p.update(triage_verification=proposed["niveau"],triage_couleur=proposed["couleur_hex"],triage_regle=proposed["regle"],triage_motif=proposed["motif"],
            triage_version=VERSION,triage_reference_v1=original["niveau"],triage_regle_reference_v1=original["regle"], description_courte=f["diagnostic_elus"]["resume"],
            surface_polygones_vegetalises_ocsge_m2=local["ocsge"]["surface_polygones_vegetalises_m2"],
            surface_artificialisee_ign_m2=local["artificialisation"]["surface_par_statut_artif_m2"].get("artif",0.0),
            surface_non_artificialisee_ign_m2=local["artificialisation"]["surface_par_statut_artif_m2"].get("non artif",0.0))
        assert set(local["artificialisation"]["surface_par_statut_artif_m2"]) <= {"artif","non artif"}
        changed = original["niveau"] != proposed["niveau"]
        record = {"maille_id":mid,"grid_version":f["grid_version"],"territory_id":f["territory_id"],"communes":f["communes"],
            "couleur_initiale":original["niveau"],"couleur_proposee":proposed["niveau"],"regle_initiale":original["regle"],"regle_proposee":proposed["regle"],
            "changement":changed,"justification":proposed["motif"] if changed else "Classe V1–V4 de référence conservée",
            "observations_supplementaires_utilisees":proposed["justificatifs_supplementaires"],"priorite_ecologique":"indeterminee",
            "limites":["Présence cartographique seulement ; aucune priorité écologique ou urgence", "La végétation OCS GE inclut cultures et espaces d'ornement",
                "Pas d'absence écologique attestée ni de transfert depuis les voisins", "R1–R4 et recommandations inchangées"]}
        transitions.append(record);colors[proposed["niveau"]] += 1
        if mid in audit:
            row = deepcopy(audit[mid]); row.update(ocsge=local, comparaison=record)
            enhanced_gray.append(row)
    complete_neighborhood(fiches_doc['fiches'], enhanced_gray)
    fiches_doc["triage_version"] = VERSION
    fiches_doc["sources_complementaires"] = ["provenance/ocsge_sources.json", "provenance/table_triage_exploratoire_v2.json"]
    put(BUNDLE / "demo_interne/fiches_zones.json", fiches_doc)
    put(BUNDLE / "demo_interne/mailles.geojson", cells)
    put(BUNDLE / "donnees/observations_ocsge_101.json", allobs)
    put(BUNDLE / "rapports/audit_grises_32.json", {"mailles":enhanced_gray,"completude_ecologique":False})
    put(BUNDLE / "rapports/comparaison_101.json", {"version":VERSION,"mailles":transitions})
    matrix = {a:{b:sum(r["couleur_initiale"]==a and r["couleur_proposee"]==b for r in transitions) for b in ("rouge","orange","jaune","gris")} for a in ("rouge","orange","jaune","gris")}
    put(BUNDLE / "rapports/matrice_transition.json", matrix)
    comparison_csv(transitions)
    audit_csv(enhanced_gray)
    bilan = load(BASE / "rapports/bilan.json")
    bilan.update(triage_version=VERSION,classifications_exploratoires= {c:colors[c]for c in ("rouge","orange","jaune","gris")},classifications_reference_v1=load(BASE/"rapports/bilan.json")["classifications_exploratoires"],
        matrice_transition=matrix,mailles_changees=[r["maille_id"]for r in transitions if r["changement"]],
        grises_avec_observation_ecologique_preexistante=sum(bool(r["sources_ecologiques_non_mobilisees_par_V1_V3"]) for r in audit.values()),
        grises_avec_vegetation_ocsge=sum(r["ocsge"]["ocsge"]["surface_polygones_vegetalises_m2"]>0 for r in enhanced_gray),
        nouvelles_sources={k:len(s)for k,s in sources.items()}, priorites_ecologiques={"indeterminee":101},
        observations_supplementaires_101=sum(bool(r["surface_polygones_vegetalises_m2"] or r["surface_polygones_aquatiques_m2"]) for r in allobs if r["couche"]=="ocsge"))
    put(BUNDLE / "rapports/bilan.json", bilan)
    print(json.dumps({k:bilan[k] for k in ["classifications_exploratoires","grises_avec_observation_ecologique_preexistante","grises_avec_vegetation_ocsge","nouvelles_sources","observations_supplementaires_101"]},ensure_ascii=False,indent=2))


def comparison_csv(records):
    fields = ["maille_id","grid_version","territory_id","couleur_initiale","couleur_proposee","regle_initiale","regle_proposee","changement","justification","observations_supplementaires_utilisees","limites"]
    write_csv(BUNDLE / "rapports/comparaison_101.csv", fields, records)


def complete_neighborhood(fiches, audit_rows):
    """Décrire aussi les objets OCS des voisins, sans alimenter le classifieur."""
    index={f['maille_id']:f for f in fiches}
    audits={r['maille_id']:r for r in audit_rows}
    for mid,r in audits.items():
        f=index[mid];local=f['enrichissement_20261112']['observations_dans_maille']
        r['observations_dans_maille'].update(local)
        for kind in local:
            f['enrichissement_20261112']['distance_source'][kind]={
                'distance_source_m':0.0 if local[kind]['objets'] else None,
                'definition':'Intersection surfacique positive locale des polygones acquis ; ne mesure pas une connexion écologique',
                'objets_les_plus_proches':[{'objet_id':o['objet_id'],'precision_source_m':None}for o in local[kind]['objets']],
                'absence_attestee':False}
            r['distance_source'][kind]=f['enrichissement_20261112']['distance_source'][kind]
        for n in r['contexte_voisinage']:
            neighbour=index[n['maille_id']]['enrichissement_20261112']['observations_dans_maille']
            for kind in local:
                ours={o['objet_id']for o in local[kind]['objets']};theirs={o['objet_id']for o in neighbour[kind]['objets']}
                n['observations_dans_voisin'][kind]={'objets_observes_voisin':len(theirs),'objet_ids_uniquement_voisin':sorted(theirs-ours),
                    'objet_ids_partages':sorted(theirs&ours),'mesure_locale_voisin':neighbour[kind]['mesure_observee'],'unite':'m2',
                    'presence_dans_maille_courante_deduite':False}
        f['enrichissement_20261112']['contexte_voisinage']=r['contexte_voisinage']


def audit_csv(records):
    rows = []
    for r in records:
        obs = r["observations_dans_maille"];o=r["ocsge"]["ocsge"];a=r["ocsge"]["artificialisation"]
        row = {k:r[k]for k in ("maille_id","grid_version","territory_id","area_m2","pilot_fraction","maille_partielle","motif_v4_exact","diagnostic_information")}
        row.update(communes=r["communes"],categories_routes=r["attributs_routes"],
            sources_non_mobilisees_V1=r["sources_ecologiques_non_mobilisees_par_V1_V3"],voisins=[x["maille_id"]for x in r["contexte_voisinage"]],
            distance_source=r["distance_source"],precision_source=r["precision_source"],couvertures_sources=r["couverture_sources"],
            surface_vegetalisee_ocsge_m2=o["surface_polygones_vegetalises_m2"],surface_arbores_ocsge_m2=o["surface_polygones_arbores_m2"],
            surface_herbacee_ocsge_m2=o["surface_polygones_herbaces_m2"],surface_eau_ocsge_m2=o["surface_polygones_aquatiques_m2"],
            surface_artif_ign_m2=a["surface_par_statut_artif_m2"].get("artif",0),surface_non_artif_ign_m2=a["surface_par_statut_artif_m2"].get("non artif",0),
            couverture_ocsge=o["couverture_geometrique"],couleur_proposee=r["comparaison"]["couleur_proposee"],regle_proposee=r["comparaison"]["regle_proposee"],
            donnees_susceptibles_de_qualifier=r["donnees_susceptibles_de_qualifier"])
        for kind in obs:
            row[kind+"_nombre_objets"] = obs[kind]["nombre_objets_observes"]
            row[kind+"_mesure_observee"] = obs[kind]["mesure_observee"]
            row[kind+"_unite"] = obs[kind]["unite"]
        rows.append(row)
    write_csv(BUNDLE/"rapports/audit_grises_32.csv", list(rows[0]),rows)


def write_csv(path, fields, records):
    with path.open("w",encoding="utf-8",newline="")as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction="ignore");writer.writeheader()
        for r in records:writer.writerow({k:json.dumps(v,ensure_ascii=False)if isinstance(v,(dict,list))else v for k,v in r.items()if k in fields})


if __name__ == "__main__":
    main()
