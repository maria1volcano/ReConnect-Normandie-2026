"""Documenter et sceller un nouveau lot interne, sans modifier ses entrées historiques."""
from __future__ import annotations
from collections import Counter
import importlib.metadata
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile

from analysis.preparer_caen_et_nord import ROOT, OUT, RAW, PROC, sha
from analysis.livrer_caen_et_nord import BUNDLE, SCOPE
from analysis.verifier_lot_caen import verify


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def document():
    read = lambda p: json.loads(p.read_text())
    bilan = read(BUNDLE / "rapports/bilan.json")
    fiches = read(BUNDLE / "demo_interne/fiches_zones.json")["fiches"]
    scope = bilan["scope"]
    assert scope == SCOPE
    rep = BUNDLE / "reproduction"
    rep.mkdir(exist_ok=True)
    for name in ("routes", "corridors", "reservoirs", "grille", "territoire"):
        dest = rep / "entrees_m2" / (name + ".gpkg")
        dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(PROC / (name + ".gpkg"), dest)
    # Entrées exactes : les identifiants canoniques dépendent aussi des attributs sources.
    # Le GeoPackage minimisé de consultation ne doit pas remplacer ces entrées pour un rejeu.
    for source in (ROOT / "analysis").glob("*.py"):
        dest = BUNDLE / "provenance/code/analysis" / source.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    shutil.copyfile(ROOT / "analysis/requirements.txt", BUNDLE / "provenance/code/analysis/requirements.txt")
    fixture = "tests/fixtures/m1_grid_v61/generate_hex_grid.py"
    dest = BUNDLE / "provenance/code" / fixture; dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / fixture, dest)
    for name in ("api_contract_m2_m4.md", "table_decision_m2.md", "regles_actions_m2.md", "dictionnaire_faits_actions_m2.md",
                 "rules_actions.json", "schema_actions_m2.json", "table_triage_exploratoire.json", "schema_conflits.json", "schema_mailles.json"):
        dest = BUNDLE / "provenance/code/docs" / name; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / "docs" / name, dest)
    shutil.copyfile(ROOT / "analysis/verifier_lot_caen.py", BUNDLE / "verifier_lot.py")
    shutil.copyfile(OUT / "audit_branches/branches.json", BUNDLE / "provenance/branches_inspectees.json")
    shutil.copyfile(OUT / "preservation_avant.json", BUNDLE / "provenance/empreintes_travaux_anterieurs.json")
    shutil.copyfile(Path("/private/tmp/reconnect_m2_tests_caen_20261111.log"), BUNDLE / "rapports/tests_M2.log")
    shutil.copyfile(Path("/private/tmp/reconnect_m3_build_20261111_v2.log"), BUNDLE / "rapports/build_M3.log")
    shutil.copyfile(ROOT / "docs/finalisation_cartographique_caen_et_nord_20261111.md", BUNDLE / "rapports/compte_rendu.md")
    put(BUNDLE / "provenance/environnement.json", {"python_scientifique": sys.version,
        "packages": {n: importlib.metadata.version(n) for n in ("geopandas", "shapely", "pyproj", "pyogrio", "pandas", "numpy", "pytest", "jsonschema")},
        "M3_build_node": "22.23.5", "M3_build": "tsc --noEmit && vite build", "M4_test_python": "3.15.2",
        "sources_originales": "Les chemins des rapports historiques désignent le dépôt producteur ; les chemins du manifeste sont relatifs au présent lot."})
    (rep / "requirements-calcul.txt").write_text("".join(n + "==" + importlib.metadata.version(n) + "\n" for n in
        ("geopandas", "shapely", "pyproj", "pyogrio", "pandas", "numpy", "pytest", "jsonschema")), encoding="utf-8")
    effective = read(OUT / "sources_preparees.json")["sources"]
    effective.update({k: v for k, v in read(BUNDLE / "rapports/sources_optionnelles_preparees.json").items() if isinstance(v, dict)})
    source_records = []
    for kind, info in effective.items():
        if info.get("status") != "processed": continue
        meta_path = ROOT / info["metadata"] if "metadata" in info else RAW / "metadata/bd-topo-r.json"
        if "metadata" not in info:
            assert kind == "routes" and info["producer"] == "IGN"
        meta = read(meta_path)
        assert meta["license"] == "lov2", (kind, meta.get("license"))
        references = [{k: p[k] for k in ("file", "url", "sha256", "features") if k in p} for p in info.get("pages", [])]
        if not references:
            references = [{k: info[k] for k in ("url", "vector_file") if k in info}]
            # L'empreinte de préparation porte sur le GPKG transformé ; celle du brut est distincte.
            retry = RAW / (kind + "_reprise.json")
            raw_record = read(retry) if retry.exists() else read(RAW / "acquisition.json")["sources"][kind]
            for key in ("sha256", "file", "url"):
                if key in raw_record: references[0]["raw_" + key] = raw_record[key]
        source_records.append({"layer": kind, "producer": info["producer"], "features": info["features"],
            "source_crs_processing": "EPSG:2154", "license": "Licence Ouverte 2.0 (lov2)",
            "metadata_url": "https://www.data.gouv.fr/api/1/datasets/" + meta["slug"] + "/",
            "metadata_title": meta["title"], "metadata_last_modified": meta.get("last_modified"), "metadata_sha256": sha(meta_path),
            "retrieval_date": "2026-11-11", "ecological_vintage": "2014" if kind in {"reservoirs", "corridors"} else None,
            "upstream_references": references, "processed_original_sha256": info["sha256"],
            "consultation": "donnees/sources_consultables.gpkg#" + kind,
            "exhaustivite_ecologique_validee": False, "refus_geometries_bbox": len(info.get("refused", []))})
    admin = read(RAW / "metadata/admin-express.json"); assert admin["license"] == "lov2"
    source_records.append({"layer": "communes", "producer": "IGN", "features": 6, "license": "Licence Ouverte 2.0 (lov2)",
        "metadata_url": "https://www.data.gouv.fr/api/1/datasets/" + admin["slug"] + "/", "metadata_sha256": sha(RAW / "metadata/admin-express.json"),
        "metadata_last_modified": admin.get("last_modified"), "source": "ADMINEXPRESS-COG.LATEST:commune", "retrieval_date": "2026-11-11",
        "raw_sha256": sha(RAW / "communes_6_source.geojson"), "commune_caen": "14118", "ecological_vintage": None})
    put(BUNDLE / "provenance/sources_licences.json", {"sources": source_records,
        "revue_diffusion": {"publication_autorisee": False, "diffusion": "interne_revue_uniquement",
            "licences": "Métadonnées officielles vérifiées lov2 pour toutes les couches incorporées ; attribution requise.",
            "minimisation": "Aucun propriétaire, contact, nom d'interprète, adresse individuelle ni référence cadastrale dans les couches servies.",
            "inventaires_sensibles": "Aucun inventaire d'espèces, PRAM ou SIPAF acquis/incorporé ; aucune géométrie d'espèce sensible à filtrer dans ce lot.",
            "bruts": "Archives nationales et réponses originales conservées localement, non incorporées au lot d'ingestion.",
            "gate": "Export public test_data=False inchangé et bloquant ; le présent lot n'est pas cet export public."}})
    tables = []
    for path in sorted(BUNDLE.rglob("*.gpkg")):
        with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as db:
            geometries = {r[0]: {"column": r[1], "type": r[2], "srs_id": r[3], "z": r[4], "m": r[5]}
                          for r in db.execute("SELECT table_name,column_name,geometry_type_name,srs_id,z,m FROM gpkg_geometry_columns")}
            for (name,) in db.execute("SELECT table_name FROM gpkg_contents ORDER BY table_name"):
                assert name.replace("_", "").isalnum()
                fields = [{"name": r[1], "type": r[2]} for r in db.execute('PRAGMA table_info("' + name + '")')]
                count = db.execute('SELECT COUNT(*) FROM "' + name + '"').fetchone()[0]
                tables.append({"file": path.relative_to(BUNDLE).as_posix(), "layer_or_table": name, "rows": count,
                    "geometry": geometries.get(name), "fields": fields})
    put(BUNDLE / "FORMAT_GEOPACKAGES.json", {"tables": tables, "join": ["territory_id", "grid_version", "maille_id"],
         "evenements": "conflit_id ; liens relationnels dans rapports/mailles.gpkg:liens_mailles_conflits ; portée du lot obligatoire pour les tables natives sans territory_id",
         "sources": "routes.route_id ; autres couches.objet_id ; donnees/liens_observations.json lie ces objets aux mailles",
         "null": "NULL reste inconnu ; zéro observation ne démontre aucune absence écologique"})
    put(BUNDLE / "rapports/validation_ensemble.json", {"tests_M2": {"passed": 1418, "warnings": 40, "log": "rapports/tests_M2.log"},
        "M3_build": {"ok": True, "log": "rapports/build_M3.log", "isolated_copy": True},
        "M4_router": read(BUNDLE / "rapports/validation_routeur_M4.json"),
        "navigateur": read(BUNDLE / "rapports/validation_navigateur.json"),
        "acceptation_geometrie_science": "rapports/acceptation.json", "extraction": "Vérificateur autonome exécuté sur le ZIP final ; reçu externe à côté du ZIP"})
    write_readme(fiches)
    write_format()
    (rep / "rejouer_m2.py").write_text('''"""Rejeu optionnel ; aucun calcul nécessaire pour ingérer le lot livré."""
import argparse
import json
from pathlib import Path
import sys
p = argparse.ArgumentParser()
p.add_argument("--output", type=Path, required=True, help="Nouveau dossier ; ne doit pas exister")
a = p.parse_args()
lot = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(lot / "provenance/code"))
from analysis import calculer_m2_caen as runner
scope = json.loads((lot / "manifest.json").read_text())["scope"]
a.output = a.output.resolve()
a.output.mkdir(parents=True, exist_ok=False)
runner.ROOT = a.output
runner.OUT = a.output
runner.PROC = lot / "reproduction/entrees_m2"
runner.GRID = scope["grid_version"]
runner.TERRITORY = scope["territory_id"]
runner.DATASET = scope["dataset_version"]
runner.main()
''', encoding="utf-8")
    (rep / "README.md").write_text("""# Reproduction optionnelle

L'ingestion ne nécessite aucun recalcul. Pour vérifier les fichiers : `python3 verifier_lot.py` à la racine extraite.

Pour rejouer ENJ et le détecteur/agrégateur natifs dans un environnement scientifique séparé : installer `provenance/code/analysis/requirements.txt`, puis lancer `python reproduction/rejouer_m2.py --output /chemin/vers/un_nouveau_dossier`. Employer les versions consignées dans `provenance/environnement.json` pour comparer les géométries/identifiants. Le rejeu strict doit refuser un événement ; le script conserve son identifiant et sa géométrie en quarantaine et agrège uniquement les autres, sans nouvelle tolérance.

`entrees_m2/` contient les cinq GeoPackages exacts du calcul, avec les attributs qui participent à l'identité des événements. Ne pas leur substituer la couche routière minimisée de consultation. Les rapports de production sont dans `rapports/`, et les commandes réellement exécutées dans `rapports/commandes.json`. Leurs chemins absolus sont ceux du producteur ; le script ci-dessus résout les chemins de ce lot extrait.

Les scripts d'acquisition et d'enrichissement sont archivés pour audit dans `provenance/code/analysis/`. Les acquisitions en ligne peuvent changer : les réponses brutes originales, refus et reprises restent dans le dépôt producteur `data/raw/caen_et_nord_20261111_v1/`, avec leurs empreintes. Les ZIP nationaux et les données personnelles des bruts ne sont pas nécessaires à l'ingestion et ne sont pas transmis. La grille de référence M1 est archivée avec son générateur. Les observations et leurs liens locaux sont fournis dans `donnees/` ; le JSON final est scellé par SHA-256.

Ne pas exécuter le `main()` historique de `construire_fiches_66.py` : seuls sa liste documentaire de catégories et `color_rule` ont été réutilisés. Ses effectifs historiques et sa sortie TEST ne constituent pas le lot courant.
""", encoding="utf-8")
    return bilan, source_records


def write_readme(fiches):
    text = """# ReConnect — Caen entière et cinq communes du nord — revue interne du 11 novembre 2026

Le lot est prêt pour une démonstration locale de l'application existante : **101 mailles découpées**, 66 identifiants de lattice partagés avec le lot historique, **40 mailles avec une surface dans Caen**. Ce dernier nombre ne désigne pas les mailles avec événements. Périmètre : Caen (14118), Bénouville, Blainville-sur-Orne, Colombelles, Hérouville-Saint-Clair et Ouistreham. Grille : `M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1` ; territoire : `caen_et_nord_6communes` ; données : `M1-CAEN-ET-NORD-20261111-V1`.

## Charger la démonstration existante M3

1. Extraire ce dossier et lancer `python3 verifier_lot.py` depuis sa racine. Aucun paquet Python SIG n'est nécessaire à cette vérification.
2. Dans le travail de M3, examiner `integration/m3_ingestion_caen.patch`, préparé contre `feat/m3-frontend-reconnect-v61` au commit `3e17eaf6e036c036b49c8a061e918528267948e0`. Depuis la racine du dépôt M3 : `git apply --check /chemin/du/lot/integration/m3_ingestion_caen.patch`, puis appliquer le patch après revue par M3. Depuis le seul dossier frontend, utiliser `-p2`. Aucun checkout ni changement de branche n'a été fait par le producteur M2.
3. Dans `frontend/`, après installation des dépendances du verrou existant, définir `M2_CAEN_LOT_ROOT=/chemin/absolu/du/dossier_extrait` puis lancer `npm run dev -- --host 127.0.0.1`. Exemple : `M2_CAEN_LOT_ROOT='/chemin/du/lot' npm run dev -- --host 127.0.0.1`. Node 22.23.5 a servi à la validation. Ouvrir l'adresse locale indiquée par Vite.
4. Vérifier le badge **101 mailles réelles M1 chargées**, la mention « Indices cartographiques à vérifier — analyse exploratoire », une fiche au clic et le sélecteur des deux vues. La capture `rapports/carte_exploratoire.png` montre le résultat vérifié dans Chrome.

Le patch réutilise React/MapLibre, les couches et styles existants. Il fournit le chargement de la nouvelle grille, le cadrage de toute l'emprise, deux légendes séparées et un panneau de fiche au clic. Le plugin interne est actif uniquement dans le serveur de développement ; **un simple `vite build` ne publie pas les données**. La branche existante contient encore un mode TEST distinct : ne pas l'activer pour cette démonstration réelle. Les chemins et anciens territoires restent séparés.

## Raccordement optionnel au backend M4

Branche inspectée : `feat/backend-housin`, commit `466a4a7f331bf06428edbdb8d7c7fe2d9aca68c6`. Les routes `/zones` et `/zones/{zone_id:int}` y servent deux exemples TEST ; elles ne constituent pas un contrat de fiche réelle. Copier `integration/m2_caen_router.py` dans `backend/`, importer `router` dans `main.py` puis appeler `app.include_router(router)`. Pour un lancement `uvicorn main:app` depuis backend, utiliser `from m2_caen_router import router` ; pour un module `backend.main`, utiliser l'import relatif correspondant.

Configurer le même `M2_CAEN_LOT_ROOT` côté backend et servir sur `127.0.0.1`, sans confiance dans des en-têtes proxy externes. Le routeur expose les quatre fichiers sous `/__internal/m2/caen/` ainsi que `/__internal/m2/caen/fiches/{maille_id}?grid_version=...&territory_id=...`. Une mauvaise portée renvoie 409 ; une maille absente 404. Les requêtes non locales et les en-têtes de proxy sont refusés. Les versions exactes de Starlette du backend requièrent Python ≥ 3.11 ; les tests du routeur ont utilisé Python 3.15.2 et FastAPI 0.162.0. Ne pas réutiliser la .venv SIG Python 3.10 pour ces dépendances backend.

Pour la démonstration immédiate, le plugin Vite suffit ; M4 peut ensuite réutiliser les mêmes réponses dans son API interne. Le schéma final M4 et le catalogue officiel de 12 actions M5 doivent encore être confirmés. Ils ne sont pas simulés par ce lot. Les huit fiches M5 manquantes sont absentes ; les quatre références connues A04/R1, A01/R2, A03/R3, A02/R4 restent jointes par `action_id`.

## Sens des deux cartes

Vue par défaut : **ordre de vérification documentaire**, 27 rouges V1, 33 orange V2, neuf jaunes V3 et 32 grises V4. Ce sont des indices cartographiques, sans mesure de risque, gravité, urgence ni efficacité de travaux. Les cinq catégories carrossables documentaires sont Route à 1 chaussée, Route à 2 chaussées, Type autoroutier, Bretelle et Rond-point. Aucune relation de perméabilité n'est déduite de la position au sol. La définition V1–V4 est jointe, et les paires, objets et surfaces justifiant chaque couleur figurent dans chaque fiche.

Vue D/S : **101 priorités indéterminées**, méthode NULL, `priorite_examen={etat: non_calculee, valeur: null}`, aucun enjeu écologique classé à partir de la seule présence de matrices. Les pourcentages/présences ENJ qualifiés restent NULL quand la couverture n'est pas attestée ; les mesures observées sont disponibles séparément. Les couleurs documentaires n'alimentent jamais `priority_category`.

V1 exige une paire linéaire admissible avec route de la convention carrossable, `statut_objet="En service"`, `position_sol="0"`, matrice `Matrice fragile, fortement sensible à la fragmentation`, et une surface positive de réservoir dans la même maille. V2 désigne les autres paires linéaires documentées ; V3 une matrice ou un réservoir de surface positive sans telle paire ; V4 les informations insuffisantes. Les seuls éléments non concluants/frontaliers, en quarantaine, ou attributs critiques manquants rendent la classification incertaine et grise avec motif. Aucun seuil de nombre d'intersections ou de densité n'est employé. Les paires locales et les événements canoniques ont des unités de compte distinctes.

## Comptes, relations et quarantaine

**5 337 détectés = 5 336 agrégés + un en quarantaine** ; 5 250 paires sources, 4 360 routes distinctes concernées. 5 759 liens maille–événement ; chaque événement admis a un propriétaire canonique, soit 5 336 comptes exclusifs. **60 mailles ont des événements admis, 41 n'en ont aucun**. La somme des comptes locaux vaut 5 759 et celle des comptes exclusifs 5 336. Douze événements admis non concluants de frontière sont conservés et identifiés, sans servir de preuve à une couleur V1/V2.

L'événement `rc_d1ac6a3bdcf06eb66226fd8699d2a9ae8f4cb7932fe8c924ba55cdaf4cf459f4`, route `TRONROUT0000002334259154` / matrice `TVB-COR-0AD80F5F1B25C5271D14`, est refusé par `event_outside_territory`. Résidu linéaire extérieur 1.2493837389962852e-9 m ; distance de Hausdorff 1.1301883402599254e-9 m, supérieure au budget ULP 9.331397911231848e-10 m. Le validateur est inchangé. Sa géométrie originale reste dans `rapports/quarantaine.gpkg`, avec WKB et mesures dans `quarantaine.validation.json`. Il n'est ni dans `demo_interne/conflits.geojson` ni dans les liens/comptes canoniques. Les fiches signalent uniquement sa proximité technique ; aucun rattachement n'est créé pour le faire passer.

Les jointures de fiches utilisent **(`territory_id`, `grid_version`, `maille_id`)** ; celles des événements `conflit_id` avec le même contexte de lot. Ne jamais joindre uniquement sur `maille_id` entre pilotes : les mêmes hexagones complets ont légitimement le même identifiant, mais leur découpe et leurs données diffèrent. Dans `actions_resultats.json`, le scope est dans l'en-tête et s'applique à chacun des 404 `actionResult` inchangés ; ne pas ajouter arbitrairement des propriétés interdites par leur schéma existant.

## Sources, investigations et limites

Sources acquises et découpées : 17 335 routes IGN, 40 matrices et 41 réservoirs SRCE, 879 haies dans 62 mailles, cinq plans d'eau dans cinq mailles, 77 sites Cartofriches dans 40 mailles, 172 objets de l'inventaire DREAL de zones humides dans 41 mailles. Ces nombres ne sont pas les nombres du pilote historique. Toutes les couches consultables sont en EPSG:2154 ; seuls les deux GeoJSON cartographiques sont en WGS84 longitude/latitude.

Les cinq plans d'eau sont trois Retenue et deux Réservoir-bassin ; **zéro mare explicitement référencée** par ce filtre, sans preuve d'absence de mares. Le PRAM/exhaustivité des inventaires de mares n'est pas acquis. Cartofriches comprend 35 sites avec projet, 23 sans projet et 19 reconvertis ; ces derniers ne sont pas assimilés à des friches actuelles. Dix-sept géométries Cartofriches et 44 de zones humides invalides dans la BBOX de lecture ont été refusées sans réparation ; ce ne sont pas 61 absences écologiques ni nécessairement 61 objets du territoire. Leurs identifiants et motifs sont conservés dans les rapports. Le ZH est un inventaire hétérogène : remblais, zones non définies, mares/étangs/lacs, prairies, etc., issu majoritairement de photo-interprétation. Ne pas traiter tous ses polygones comme des habitats humides actuels ou des mares.

**165 pistes dans 71 mailles** : R1/A04 60, R2/A01 50, R3/A03 35, R4/A02 20. Ce sont des investigations documentaires justifiées, pas des activations de travaux. R2 requiert des haies observées avec matrice/réservoir dans la maille, sans diagnostiquer une rupture ; R3 ne retient comme signal que les sites de statut source friche avec/sans projet ; R4 signale les plans d'eau/mare explicite ou réservoir de sous-trame humide. Les autres objets de l'inventaire ZH restent consultables et à qualifier, sans conversion automatique en déclencheur R4. Les quatre examens scientifiques par maille restent **404 non évaluables A2**, sans méthode familiale approuvée, preuve d'obstacle/rupture ou validation écologique. **Zéro recommandation validée.**

Métadonnées et licences : `provenance/sources_licences.json` ; précision/NULL/qualité et champs : `FORMAT_GEOPACKAGES.json`, fiches et rapports. Le millésime SRCE est 2014 ; l'acquisition au 11 novembre 2026 n'est pas une actualisation écologique de 2014. Les dates de mise à jour d'objets IGN ne constituent pas un millésime écologique global. `ouvrage_connu` et millésime routier restent NULL ; sous-trames des matrices `-` et précision SRCE NULL. La vitesse source n'est pas une mesure de trafic.

## Diffusion et conservation

Ce lot est **interne, pour revue/démonstration locale**, pas une autorisation de publication. Les couches utilisées relèvent de la Licence Ouverte 2.0, avec attribution IGN / DREAL Normandie / Cerema. Les données de consultation ont été minimisées (sans propriétaires, contacts, noms d'interprètes, adresses individuelles ni références cadastrales) ; les bruts restent chez le producteur. Aucun inventaire de localisation d'espèces sensibles n'a été incorporé. Le verrou d'export public `test_data=False`, les règles scientifiques et les contrats publics restent inchangés. Ne pas contourner ce verrou en étiquetant les données réelles comme TEST, en les copiant dans le répertoire public ni en ouvrant le plugin au réseau. Une diffusion publique exige encore le circuit de validation prévu par le projet.

Le ZIP historique 66 mailles est inclus **scellé et séparé** sous `historique/` avec son empreinte d'origine. Les 433 fichiers préexistants ont été vérifiés inchangés. Aucun commit, push, merge, checkout ou modification des branches de l'équipe n'a été effectué. `rapports/tests_M2.log`, `acceptation.json`, les validations du routeur/navigateur et les captures documentent les vérifications. Le reçu final `validation_extraction.json` est fourni à côté du ZIP et le même contrôle est rejouable sans dépendances avec `verifier_lot.py`.
"""
    (BUNDLE / "README.md").write_text(text, encoding="utf-8")
    (BUNDLE / "MESSAGE_M4_M5.md").write_text("""Le lot Caen entière + les cinq communes du nord est prêt pour revue interne : 101 fiches et deux vues séparées. Le ZIP contient les GeoJSON, fiches, actions, données SIG, règles, provenance, contrôles et un patch ciblé de votre application M3. Vérifier `python3 verifier_lot.py`, appliquer le patch M3 après revue, puis définir `M2_CAEN_LOT_ROOT` vers le dossier extrait et lancer Vite en boucle locale. README : étapes exactes et routeur M4 optionnel.

Vue de démonstration par défaut : 27 rouges, 33 orange, neuf jaunes, 32 grises, explicitement « Indices cartographiques à vérifier — analyse exploratoire ». Vue D/S : toutes les priorités indéterminées. 5 336 événements admis, un quarantainé, 60 mailles avec événements / 41 sans événement observé. 165 pistes documentaires R1–R4, aucune recommandation de travaux validée ; 404 examens scientifiques non évaluables. Merci de conserver ces distinctions, les NULL et la portée de grille/territoire. M5 peut joindre les fiches officielles par A04/R1, A01/R2, A03/R3, A02/R4 dès qu'elles seront disponibles ; les huit autres ne sont pas inventées.

Les adaptations ont été compilées et testées dans une copie temporaire de M3 ; aucune branche d'équipe n'a été modifiée. Le raccordement dans votre branche et une éventuelle diffusion publique restent à valider. Le verrou public test_data=False est inchangé.
""", encoding="utf-8")


def write_format():
    (BUNDLE / "FORMAT_JSON.md").write_text("""# Format interne réellement fourni

Le lot adapte les données à MapLibre/React de la branche M3 inspectée, mais ne se déclare pas conforme à un schéma frontend final inconnu ni à l'export public `m2-m4.proposal-1`. `format_version=reconnect.vue-interne-1` désigne les GeoJSON privés ; `m2-m4.caen6.demonstration-interne-1` désigne le document de fiches. Le manifeste conserve la portée commune ; `method_version=null` est intentionnel.

| Fichier | Structure / champs utiles |
| --- | --- |
| `demo_interne/mailles.geojson` | FeatureCollection 101 Polygon/MultiPolygon WGS84 ; `maille_id`, `grid_version`, `territory_id`, `dataset_version`, `area_m2`, `pilot_fraction`, `is_boundary`, `caen_area_m2`, `triage_verification`, `triage_couleur`, `triage_regle`, `triage_motif`, `validation_ecologique=false`, `description_courte`, `conflit_ids`, `action_ids`, `action_ids_valides=[]`, comptes locaux/exclusifs. `priority_category=INDETERMINATE`, statut PENDING et méthode NULL restent indépendants. |
| `demo_interne/conflits.geojson` | FeatureCollection 5 336 lignes admises WGS84 ; `conflit_id`, scope, `maille_ids`, `source_pairs`, `statut`, `evidence_level=geometrie_2d`, `precision_affichage`, `territory_relation`, `limites`. Aucun objet de quarantaine affiché. |
| `demo_interne/fiches_zones.json` | En-tête `scope`, `classification_defaut`, `mention_obligatoire`, `publication_autorisee=false`, puis `fiches[101]`. Chaque fiche a scope + maille_id, communes/surface, triage avec paires/sources/motif, D/S séparé, `diagnostic_elus`, `diagnostic_techniciens`, `actions[4]`, `action_ids_a_etudier`, `action_ids_valides=[]`, `recommandations_validees=[]`, limites. |
| `demo_interne/actions_resultats.json` | En-tête scope et `profile=actionResult`, puis `resultats[404]` validés avec le profil `actionResult` existant, sans changement de contrat. Clé locale `(maille_id,rule_id)` dans le scope de l'en-tête ; `diagnostic_ids` correspondent aux diagnostics des fiches. A2/non_evaluable ; méthode NULL ; preuves/attestations vides. |
| `donnees/liens_observations.json` | Liste de relations scope + maille_id + source_couche + objet_id + `measure` positive + unité m/m2 ; ne pas sommer les nombres d'objets locaux pour obtenir un total territorial d'objets distincts. |

Pour une fiche, filtrer sur les trois identifiants de portée. Pour ses événements, utiliser `conflit_ids` ou le tableau `maille_ids` des événements, jamais une recherche par centre/proximité. Un événement peut appartenir à plusieurs mailles, mais un seul compte exclusif. `rapports/mailles.gpkg:liens_mailles_conflits` conserve `relation_spatiale` et `canonical_owner` ; ses tables natives héritent du scope du lot. Les valeurs NULL ne deviennent ni zéro, ni faible, ni absence. Les mailles sans événement restent cliquables avec leur fiche, leurs autres observations et le motif de non-évaluation.

`diagnostic_techniciens.observations` comporte les couches routes/corridors/reservoirs/haies/plans_eau/friches/zones_humides : nombre d'objets observés, mesure et unité, objets/attributs minimisés, disponibilité, complétude non attestée et référence de source. Les longueurs locales sont découpées à la maille ; les surfaces sont l'union des observations locales. Les mesures sont descriptives, sans coefficient de danger ni seuil écologique. Les objets et dates sont consultables avec `donnees/sources_consultables.gpkg` ; les licences/millésimes globaux sont dans `provenance/sources_licences.json`. Inventaire exhaustif des tables/champs/géométries/CRS : `FORMAT_GEOPACKAGES.json`.

Chacune des quatre actions de fiche expose `action_id`, `regle_id`, `statut_regle_m2`, `piste_investigation`, `observations_justificatives`, `conditions_satisfaites`, `conditions_manquantes`, `motif`, `sources`, `niveau_de_validation`, `travaux_preconises=false`. `a_etudier` est une piste documentaire, jamais une recommandation validée. Les fiches M5 officielles pourront être associées par action_id sans changer ces diagnostics.

La palette documentaire est fournie dans `provenance/table_triage_exploratoire.json`, et chaque fiche conserve `definition_version`, `application_version`, disponibilité et limites. L'application doit afficher la mention exploratoire près de la carte, utiliser `triage_couleur` pour cette seule vue et `priority_category` pour la vue D/S. Ne pas transmettre le triage au calcul scientifique ni renommer une couleur documentaire « priorité écologique ».
""", encoding="utf-8")


def seal(bilan, sources):
    archive = OUT / (BUNDLE.name + ".zip")
    assert not archive.exists(), "Livraison scellée déjà présente"
    counts = {**{k: v for k, v in bilan["m2"].items() if isinstance(v, int) and not isinstance(v, bool)},
              "fiches": bilan["mailles"], "actions_resultats": bilan["diagnostics_familiaux_non_evaluables"],
              "triage_documentaire": bilan["classifications_exploratoires"], "priorites_ecologiques": bilan["priorites_ecologiques"],
              "pistes_investigation": bilan["pistes_investigation"], "recommandations_validees": 0}
    forbidden = {"__pycache__", "node_modules", ".venv", ".DS_Store", ".pytest_cache"}
    files = sorted(p for p in BUNDLE.rglob("*") if p.is_file() and p.name not in {"manifest.json", "SHA256SUMS"})
    assert all(not forbidden.intersection(p.relative_to(BUNDLE).parts) and p.suffix not in {".pyc", ".tmp"} for p in files)
    manifest = {"format_version": "reconnect.caen6.lot-interne-1", "created_date": "2026-11-11", "scope": SCOPE,
        "publication_autorisee": False, "diffusion": "interne_revue_uniquement", "test_data": False,
        "public_export": False, "public_export_gate": "Inchangé ; aucun export public de données réelles exécuté",
        "default_view": "triage_documentaire", "required_label": "Indices cartographiques à vérifier — analyse exploratoire",
        "extent": {"communes": ["14118", "14060", "14076", "14167", "14327", "14488"], "source_crs": "EPSG:2154",
            "area_m2": 65214583.519504786, "caen_commune_area_m2": 25729815.904390305,
            "analysis": "donnees/territoire.gpkg#territoire", "minimal": "donnees/territoire.gpkg#caen_commune", "display_crs": "OGC:CRS84"},
        "counts": counts, "sources": sources, "controls": "rapports/acceptation.json", "verification": "verifier_lot.py",
        "entrypoints": {"mailles": "demo_interne/mailles.geojson", "conflits": "demo_interne/conflits.geojson",
            "fiches": "demo_interne/fiches_zones.json", "actions": "demo_interne/actions_resultats.json", "readme": "README.md"},
        "historical": {"file": "historique/M2_CAEN_NORD_FINAL_M1_M2_20261111_V1.zip", "sha256": bilan["historical_zip_sha256"],
            "grid_version": "M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1", "mailles": 66, "active": False},
        "files_sha256": {p.relative_to(BUNDLE).as_posix(): sha(p) for p in files}}
    put(BUNDLE / "manifest.json", manifest)
    (BUNDLE / "SHA256SUMS").write_text("".join(h + "  " + n + "\n" for n, h in sorted({**manifest["files_sha256"], "manifest.json": sha(BUNDLE / "manifest.json")}.items())), encoding="utf-8")
    verify(BUNDLE)
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(BUNDLE.rglob("*")):
            if path.is_file(): z.write(path, BUNDLE.name + "/" + path.relative_to(BUNDLE).as_posix())
    digest = sha(archive)
    archive.with_suffix(".zip.sha256").write_text(digest + "  " + archive.name + "\n")
    # Extraction dans un répertoire neuf : ne pas valider uniquement l'arborescence productrice.
    with tempfile.TemporaryDirectory(prefix="reconnect_caen_extraction_") as temp:
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            for name in z.namelist():
                assert (Path(temp) / name).resolve().is_relative_to(Path(temp).resolve())
            z.extractall(temp)
        extracted = Path(temp) / BUNDLE.name
        run = subprocess.run([sys.executable, "-B", str(extracted / "verifier_lot.py")], check=True, capture_output=True, text=True)
        receipt = json.loads(run.stdout)
    put(OUT / "validation_extraction.json", {"critere": 13, "ok": True, "archive": archive.name, "archive_sha256": digest,
         "mode": "ZIP testé, extrait dans un dossier neuf puis vérificateur bibliothèque standard exécuté dans l'extraction", "resultat": receipt})
    print(json.dumps({"zip": str(archive.relative_to(ROOT)), "sha256": digest, "bytes": archive.stat().st_size,
                      "files": len(manifest["files_sha256"]) + 2, "extraction_ok": True}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    seal(*document())
