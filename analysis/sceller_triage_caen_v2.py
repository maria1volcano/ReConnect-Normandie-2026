"""Documentation et scellement d'un lot interne V2 ; V1 et science conservées."""
from __future__ import annotations
from collections import Counter
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from analysis.auditer_mailles_grises_caen import ROOT, BASE, OUT
from analysis.enrichir_triage_caen_20261112 import BUNDLE, load, put
from analysis.preparer_ocsge_caen import RAW
from analysis.preparer_caen_et_nord import sha
from analysis.triage_documentaire_v2 import VERSION, VEGETATION_CS, AQUATIC_CS
from analysis.verifier_triage_caen_v2 import verify


def document():
    old=load(BASE/'manifest.json');bilan=load(BUNDLE/'rapports/bilan.json')
    method={"version":VERSION,"objet":"classification_documentaire_exploratoire_SEULEMENT","scientific_validation":False,
        "legend":load(BASE/'provenance/table_triage_exploratoire.json')['legend'],"reference_v1":"provenance/table_triage_exploratoire.json",
        "V1_V2_V3":"Conditions originales et classes conservées, sans nouveau seuil ni nouveau calcul M2",
        "V3b":{"couleur":"jaune","eligible":"Uniquement une maille grise V4 de référence, sans incertitude technique critique",
            "conditions_alternatives":[{"couche":"haies","champ":"objet_id et longueur locale en m","condition":"Haie IGN acquise, valide, avec longueur positive dans la maille"},
                {"couche":"plans_eau","champ":"objet_id et surface locale m2","condition":"Plan d'eau IGN cartographié dans la maille ; pas nécessairement une mare"},
                {"couche":"ocsge","champ":"id, code_cs, code_us, millesime et géométrie","codes_cs_vegetalises":sorted(VEGETATION_CS),"codes_cs_eau":sorted(AQUATIC_CS),
                 "condition":"Surface locale positive d'un polygone de couverture végétalisée ou aquatique OCS GE ; cultures et espaces d'ornement compris"}],
            "sources_qualite":"Acquisition officielle, identifiants et géométries vérifiés ; présence positive suffisante pour une observation documentaire, même si complétude écologique inconnue",
            "conclusion_autorisee":"Un objet ou une couverture est cartographié dans la maille et peut faire l'objet d'une vérification documentaire",
            "conclusions_non_autorisees":["Habitat naturel attesté","Continuité fonctionnelle","Perméabilité","Urgence","Priorité écologique","Besoin de travaux"],
            "motif_jaune":"Présence descriptive sans intersection SRCE V1/V2 ; étend le champ des sources examinées, sans renforcer la preuve écologique",
            "inconnues":"Source indisponible, géométrie invalide, code CS inconnu, contexte seulement voisin ou incertitude technique critique : pas de déclenchement V3b ; V4 conservée sans autre preuve",
            "residus_numeriques":{"surface_m2":1e-6,"longueur_m":1e-9,"origine":"Constantes M2 préexistantes ; pas de seuil écologique ni de seuil de densité"}},
        "non_declencheurs":["Routes seules","Artificialisation seule","Sol nu seul","Présence d'un site Cartofriches seule","Inventaire ZH à typologie/diagnostic ambigus","Voisin seul"],
        "D_S":"101 priorités écologiques indéterminées ; règles et données de décision inchangées",
        "R1_R4":"404 résultats non évaluables et 165 pistes existantes conservés ; aucun recalcul ni activation par OCS GE",
        "statut":"Proposition documentaire vérifiée géométriquement et testée, pas validation écologique ou approbation de travaux"}
    put(BUNDLE/'provenance/table_triage_exploratoire_v2.json',method)
    components={"M2_initial":old['scope']['dataset_version'],"ocsge":"OCS-GE_2-0__GPKG_LAMB93_D014_2023-01-01",
        "artificialisation":"OCS-GE_2-0_ARTIFICIALISATION_GPKG_LAMB93_D014_2023-01-01","triage":VERSION}
    sources=[]
    for kind,file in [('ocsge','acquisition.json'),('artificialisation','acquisition_artif.json')]:
        acquisition=load(RAW/file);report=load(OUT/(kind+'.validation.json'))
        sources.append({"couche":kind,"producer":"IGN","license":"Licence Ouverte 2.0 (lov2)","millésime":"2023","date_acquisition":"2026-11-12",
            "livraison":components[kind],"archive_url":acquisition['url'],"archive_sha256":acquisition['sha256'],"archive_md5_officiel":acquisition['md5'],
            "archive_md5_officiel_verifie":True,"taille_archive_octets":acquisition['bytes'],"source_gpkg_sha256":report['source_sha256'],
            "features_bbox":report['source_features_bbox'],"features_territoire":report['retained_features'],"refus_geometries":report['refus_geometries_bbox'],
            "CRS":"EPSG:2154","source_consultable":"donnees/ocsge_complement.gpkg#"+kind,"surface_non_couverte_globale_m2":report['surface_non_couverte_m2'],
            "ecological_completeness_validated":False,"precision_source":report['precision_source'],
            "metadonnees_officielles":"https://www.data.gouv.fr/datasets/ocs-ge"+('-artificialisation'if kind=='artificialisation'else''),
            "description":"Couvertures et usages dominants"if kind=='ocsge'else"Statut artif/non artif repris de la couche officielle IGN ; aucune reclassification réglementaire locale"})
    put(BUNDLE/'provenance/ocsge_sources.json',{"sources":sources,"component_versions":components,
        "bruts":"Archives originales conservées dans le dépôt producteur ; extractions volumineuses supprimées après découpe contrôlée par manque d'espace. Aucune source antérieure supprimée.",
        "licences_verifiees":"Métadonnées OCS GE et OCS GE Artificialisation : lov2 ; attribution IGN requise",
        "limites":"OCS GE ≠ fonctionnalité écologique ; végétalisé ≠ non artificialisé ; aquatique ≠ mare/zone humide attestée",
        "publication_autorisee":False})
    for file in ['catalogue_calvados.json','catalogue_artif_calvados.json','livraison_2023.json','livraison_artif_2023.json','acquisition.json','acquisition_artif.json','doc_new','doc_artif.pdf']:
        dest=BUNDLE/'provenance/ocsge_documentation'/('DC_OCSGE_NG_202606.pdf' if file=='doc_new' else file);dest.parent.mkdir(exist_ok=True)
        shutil.copyfile(RAW/file,dest)
    for p in [ROOT/'analysis'/name for name in ['acquerir_ocsge_caen.py','auditer_mailles_grises_caen.py','preparer_ocsge_caen.py','triage_documentaire_v2.py','enrichir_triage_caen_20261112.py','valider_triage_caen_v2.py','verifier_triage_caen_v2.py','sceller_triage_caen_v2.py','recalculer_triage_caen_v2.py']]:
        shutil.copyfile(p,BUNDLE/'provenance/code/analysis'/p.name)
    dest=BUNDLE/'provenance/code/tests/test_triage_documentaire_v2.py';dest.parent.mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'tests/test_triage_documentaire_v2.py',dest)
    shutil.copyfile(ROOT/'analysis/verifier_triage_caen_v2.py',BUNDLE/'verifier_triage_v2.py')
    shutil.copyfile(ROOT/'analysis/recalculer_triage_caen_v2.py',BUNDLE/'reproduction/recalculer_triage_v2.py')
    shutil.copyfile(OUT/'preservation_avant.json',BUNDLE/'provenance/empreintes_avant_triage_v2.json')
    shutil.copyfile(OUT/'incident_espace_disque.json',BUNDLE/'rapports/incident_espace_disque.json')
    shutil.copyfile(OUT/'tests_M2_et_triage.log',BUNDLE/'rapports/tests_M2_et_triage.log')
    shutil.copyfile(Path('/private/tmp/reconnect_m3_triage_v2_build_20261112.log'),BUNDLE/'rapports/build_M3_v2.log')
    format_=load(BUNDLE/'FORMAT_GEOPACKAGES.json')
    with sqlite3.connect((BUNDLE/'donnees/ocsge_complement.gpkg').as_uri()+'?mode=ro',uri=True)as db:
        for table in ['ocsge','artificialisation']:
            geom=db.execute('SELECT column_name,geometry_type_name,srs_id,z,m FROM gpkg_geometry_columns WHERE table_name=?',(table,)).fetchone()
            format_['tables'].append({'file':'donnees/ocsge_complement.gpkg','layer_or_table':table,'rows':db.execute('SELECT COUNT(*) FROM '+table).fetchone()[0],
                'geometry':dict(zip(['column','type','srs_id','z','m'],geom)),
                'fields':[{'name':r[1],'type':r[2]}for r in db.execute('PRAGMA table_info('+table+')')]})
    put(BUNDLE/'FORMAT_GEOPACKAGES.json',format_)
    readme='''# Caen et nord — lot interne documentaire V2 — 12 novembre 2026

101 mailles et fiches, mêmes géométries et même grille que V1. Proposition exploratoire : **27 rouges, 33 orange, 41 jaunes, 0 gris documentaire**. Référence V1 conservée : 27/33/9/32. **Les 101 priorités écologiques restent indéterminées** ; 5 336 événements admis, une quarantaine, 404 résultats R1–R4 non évaluables, 165 pistes et zéro recommandation de travaux : inchangés.

## Ingestion M3/M4

1. Extraire ce dossier puis lancer `python3 -B verifier_triage_v2.py` à sa racine. Le contrôle utilise uniquement la bibliothèque standard Python ≥ 3.9, sans recalcul SIG.
2. Si l'application n'a pas encore reçu l'adaptation Caen V1, examiner/appliquer `integration/m3_ingestion_caen.patch` contre le commit M3 indiqué dans `reference_v1/README.md`, avec `git apply --check` préalable. Puis examiner/appliquer **`integration/m3_triage_v2.patch`** : deux fichiers pour la légende V3/V3b, la fiche OCS GE et les limites. Depuis la racine du dépôt frontend d'équipe : préfixes par défaut ; depuis le seul sous-dossier frontend : `-p2`. Les patches ont été testés uniquement dans une copie temporaire, sans modification de branche d'équipe.
3. Depuis frontend, définir `M2_CAEN_LOT_ROOT=/chemin/absolu/vers/ce_dossier` et lancer `npm run dev -- --host 127.0.0.1`. Conserver le mode réel. Le plugin fourni et le routeur FastAPI optionnel sont inchangés. La route de fiche garde les paramètres maille_id/grid_version/territory_id. La vue D/S reste séparée. Aucun build statique ni publication réseau des données n'est autorisé par ce lot.
4. Contrôler le badge 101 mailles, la mention « Indices cartographiques à vérifier — analyse exploratoire », une ancienne maille grise affichée jaune V3b, son détail OCS GE et la vue D/S entièrement indéterminée. Captures et contrôle navigateur : `rapports/`.

Légende jaune V2 : **éléments cartographiés à documenter**, sans continuité fonctionnelle établie. Ne pas garder la seule ancienne légende « continuité cartographiée » pour V3b. Une nouvelle couleur est une extension du périmètre documentaire des sources, pas une preuve écologique supérieure. Les cultures et espaces d'ornement sont compris dans la couverture végétalisée. Végétalisé et artificialisé peuvent se recouper : ne pas additionner ces surfaces. Seuls les champs `triage_*` changent de classification ; `priority_category` reste INDETERMINATE.

## Données et comparaison

`demo_interne/mailles.geojson` et `fiches_zones.json` : données enrichies et classification proposée. `conflits.geojson` et `actions_resultats.json` : strictement inchangés. Jointure : **territory_id + grid_version + maille_id**. Grille conservée `M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1`, territoire `caen_et_nord_6communes`. La version M2 historique ne change pas ; versions des compléments et du triage dans le manifeste.

`rapports/audit_grises_32.csv` et `.json` : audit détaillé des 32, mesures et attributs routiers, haies, eau, SRCE, friches/ZH, couverture, maille partielle, voisinage, distances et précisions. `comparaison_101.csv` et `.json` : avant/après, règles, preuves locales, identifiants, motifs et limites pour les 101 ; `matrice_transition.json` : transition. `reference_v1/mailles.geojson` et le champ `triage_documentaire_reference_v1` de chaque fiche préservent la référence initiale. `donnees/ocsge_complement.gpkg` : deux couches officielles, millésime 2023, EPSG:2154 ; `observations_ocsge_101.json` : mesures par maille.

Les 32 anciennes grises ont une couverture OCS GE positive ; 12 comportaient déjà des haies, deux des objets ZH de typologie ambiguë, 11 des sites Cartofriches. V1–V3 n'utilisaient pas ces sources pour le jaune. La nouvelle condition V3b accepte seulement une présence locale de haie/plan d'eau IGN ou de couverture végétalisée/aquatique OCS GE valide. Routes, artificialisation, sols nus, friches seules ou voisins seuls ne suffisent pas. Les inconnues ne sont pas remplacées par des zéros. Aucun seuil de gravité, densité ou objectif de couleurs. Méthode et cas limites : `provenance/table_triage_exploratoire_v2.json` et `METHODE_TRIAGE_V2.md`.

Les deux produits OCS GE couvrent l'emprise (résidus locaux ≤ 7,79e-8 m², budget numérique existant 1e-6 m²), sans géométrie invalide dans les 38 369 objets de BBOX lus ; 19 231 objets retenus par produit. Ce sont les mêmes objets décrits par deux produits, pas 38 462 objets indépendants. La couverture géométrique n'atteste pas l'exhaustivité écologique. Les zones humides ne sont pas identifiées par l'OCS GE seule. Aucune équivalence automatique entre plan d'eau, mare et habitat humide. Source IGN sous Licence Ouverte 2.0 : attribution requise.

Le voisinage désigne les six voisins du lattice M1 présents dans le territoire ; les distances portent sur les géométries acquises découpées au territoire, pas sur un inventaire exhaustif extérieur. Un objet uniquement voisin ne devient jamais une observation interne. Les haies source portent 3 m de précision ; le SRCE et les autres valeurs inconnues restent NULL. L'OCS GE a une précision globale décrite comme métrique, sans chiffre arbitraire attribué aux objets. Aucun rapprochement n'est une preuve de continuité fonctionnelle.

## Garde-fous

Lot **interne uniquement**, `test_data=False`, publication non autorisée. Exporteur public, règles D/S et R1–R4 inchangés. Pas de faux TEST, de données sensibles d'espèces ou de prescription de travaux. Les huit fiches M5 manquantes ne sont pas inventées ; actions connues conservées. README V1 et ZIP historique des 66 mailles sont archivés séparément. Le ZIP V1 n'a pas été écrasé ; son dossier décomposé correspondait intégralement au manifeste lors de cet audit. Aucun commit, push ou merge.

Les fichiers nécessaires à l'ingestion sont tous dans ce dossier. Les archives départementales sources (138 et 123 Mo) restent chez le producteur avec les MD5 officiels et SHA-256, sans être requises au lancement. L'incident de place disque et la suppression des seules nouvelles extractions intermédiaires sont documentés. Les scripts et tests sont archivés dans provenance/code ; aucun cache, environnement virtuel ou fichier temporaire n'est inclus. Le reçu de vérification après extraction est fourni à côté du ZIP.
'''
    (BUNDLE/'README.md').write_text(readme,encoding='utf-8')
    with (BUNDLE/'README.md').open('a',encoding='utf-8')as f:f.write("\nRejeu documentaire facultatif, sans téléchargement ni détection M2 : `python reproduction/recalculer_triage_v2.py --output /chemin/exterieur/vers/un_nouveau_resultat.json`, avec les dépendances SIG consignées. Les intersections sont recalculées depuis les seules géométries livrées ; les classes des 101 mailles sont comparées aux sorties. Ne pas écrire ce résultat dans le lot scellé.\n")
    (BUNDLE/'MESSAGE_M4_M5.md').write_text('''Le lot documentaire V2 Caen et nord est prêt pour revue interne : 101 fiches, OCS GE et artificialisation IGN 2023 intégrées, audit individuel des 32 anciennes grises et comparaison des 101. Proposition : 27 rouges, 33 orange, 41 jaunes, zéro gris documentaire. Cela décrit des éléments cartographiés à vérifier ; les 101 priorités écologiques D/S restent indéterminées. Les événements, la quarantaine, les 404 résultats R1–R4 et les 165 pistes n'ont pas changé ; aucune recommandation validée.

Extraire le ZIP, lancer python3 -B verifier_triage_v2.py puis suivre README. Configurer M2_CAEN_LOT_ROOT vers ce lot ; appliquer le complément m3_triage_v2.patch après l'adaptation Caen initiale pour afficher la légende adéquate et les observations OCS GE au clic. Vérifié dans une copie isolée de M3, sans changement de votre branche. Conserver la référence V1, les clés de portée, les NULL et la vue D/S séparée. Données internes : aucune diffusion publique autorisée, verrou test_data=False inchangé.
''',encoding='utf-8')
    with (BUNDLE/'FORMAT_JSON.md').open('a',encoding='utf-8')as f:f.write('''

## Complément V2 du 12 novembre

Le schéma interne de base est conservé ; champs additionnels documentés, sans changement de contrat public : `triage_version`, `triage_reference_v1`, `triage_regle_reference_v1`, surfaces OCS GE/artificialisation dans les propriétés GeoJSON. Chaque fiche a `triage_documentaire_reference_v1` et `enrichissement_20261112` avec `observations_dans_maille`, `contexte_voisinage`, `distance_source`, `precision_source`, `couvertures` et statut d'audit. Le voisinage détaillé est audité pour les 32 anciennes grises ; pour les autres, [] signifie non audité selon le statut, pas absence de voisins.

`diagnostic_techniciens.observations.ocsge` et `.artificialisation` ajoutent nombre d'objets, mesures m², objets/ids, codes CS/US, millésime, surfaces par code et statut IGN, couverture effective et limites. Le champ `surface_humide_m2=NULL` signifie non déterminable par l'OCS GE seule. Les surfaces végétalisées désignent les polygones de ces classes dominantes, pas un taux de couvert végétal pur. Les surfaces par CS et par US décrivent les mêmes polygones selon deux dimensions ; ne pas les additionner. Les deux produits OCS GE partagent les identifiants des objets : joindre par couche/produit et objet_id dans la portée du lot, sans addition de leurs comptes.

La nouvelle règle `V3b` concerne uniquement les anciennes grises, sans modifier V1/V2/V3. Le jaune de la nouvelle légende signifie « éléments cartographiés à documenter » ; n'affirmer aucune fonctionnalité. `justificatifs_supplementaires` contient pour chaque témoin couche, objet_id, mesure/unité, dans_maille, statut, précision (éventuellement NULL), références et codes OCS GE. Les champs de décision D/S, recommandations et actions sont conservés. `component_versions` du manifeste distingue le socle M2 du complément OCS GE 2023 et de la nouvelle méthode documentaire.
''')
    method_text='''# Méthode documentaire V2 — décision du 12 novembre 2026

Le changement est défendable comme **élargissement des observations documentaires**, à ce seul niveau. Il ne constitue ni une méthode écologique validée ni une réduction de l'indétermination D/S. Les définitions des rouges et orange restent strictement celles de V1/V2. Les jaunes V3 d'origine restent inchangés ; V3b reconnaît des observations locales supplémentaires, avec une légende élargie et une référence V1 complète.

Une maille auparavant V4, sans incertitude technique critique, devient V3b jaune si au moins un objet valide dans son emprise satisfait l'une des trois conditions : haie IGN de longueur observée positive, plan d'eau IGN de surface observée positive, ou polygone OCS GE de code végétalisé CS2.1.1.1/2/3, CS2.1.2, CS2.1.3, CS2.2.1, CS2.2.2 ou eau CS1.2.2, avec surface locale positive. Les codes réels et leurs libellés sont contrôlés contre la nomenclature de la livraison officielle. Le code d'usage est conservé, notamment pour distinguer cultures, espaces d'ornement et usages sans préjuger d'un habitat naturel.

Une présence cartographique positive dans un inventaire non exhaustif demeure une observation ; un zéro ne démontre pas une absence. Un objet seulement voisin, une source indisponible, une géométrie invalide, un code inconnu, la seule présence de routes/artificialisation/friche ou un objet ZH ambigu ne constituent pas cette preuve locale. Sans autre condition satisfaite, V4 est conservée. Une incertitude critique géométrique/attributaire interdit la promotion. Les seuls filtres numériques sont les constantes M2 existantes (1e-6 m² / 1e-9 m), sans seuil de densité, de nombre d'objets ou de fonctionnalité. Aucun nombre de couleurs n'a été fixé comme cible.

Cette définition reconnaît aussi la végétation cultivée et ornementale. Ce choix est explicite : le résultat dit « couverture végétalisée à documenter » et jamais « milieu naturel fonctionnel ». Sept des 32 cas nouveaux n'ont que des polygones herbacés parmi les classes végétales. Les surfaces classées végétalisées des 32 vont d'au moins 986,27 m² à des valeurs plus grandes, indépendamment de la proportion de maille découpée ; elles ne sont pas pondérées pour produire une gravité. Les deux observations ZH de mailles grises comportent des typologies ambiguës ou de cultures/friches issues de photo-interprétation : elles ne sont pas transformées en habitat humide confirmé.

L'OCS GE représente la couverture et l'usage dominants. Sa généralisation et sa précision métrique limitent l'interprétation au voisinage des frontières. Il n'existe pas ici de précision numérique validée par objet OCS GE : NULL est conservé. Les objets ZH restent une source séparée ; aucune surface humide n'est calculée depuis CS seul. L'artificialisation est reprise du champ `artif` officiel (valeurs observées `artif` / `non artif`) et n'alimente jamais V3b. Les classes CS/US et l'artificialisation peuvent se recouper : ce ne sont pas trois surfaces à sommer.

Le voisinage est défini par la parité de colonne du lattice flat-top M1 : les six voisins sont identifiés sans distance tampon choisie. Pour les voisins conservés dans le territoire, objets partagés, objets uniquement voisins, distances géométriques et précisions disponibles sont archivés séparément. Les distances sont des minima parmi les sources acquises découpées à l'emprise, sans garantie de minimum dans un inventaire extérieur non acquis. Une géométrie partagée indique une continuité de dessin cartographique, pas une connexion écologique. Aucun objet voisin n'est ajouté au compte de la maille.

Les comptes canoniques, la quarantaine, la grille, R1–R4 et les décisions D/S sont conservés octet pour octet quand ils sont des fichiers. Pour les fiches enrichies, les champs de décision et observations initiales sont contrôlés individuellement. Les 1 708 justificatifs de changement ont été recalculés par intersection des géométries fournies et des mailles, sans relancer le détecteur routes–matrices. La méthode est testée sur les cas d'inconnues, données invalides, voisins seuls, routes seules, artificialisation seule, végétation cultivée, résidus numériques et conservation de V1/V2/V3.

Les travaux futurs nécessaires pour une priorité écologique restent des validations d'habitats, sous-trames, espèces, continuités, ouvrages/perméabilité et méthodes approuvées. Aucun effectif de végétation, aucune couleur documentaire et aucune mesure d'artificialisation ne remplace ces préconditions.
'''
    (BUNDLE/'METHODE_TRIAGE_V2.md').write_text(method_text,encoding='utf-8')
    write_report()
    return old,bilan,components,sources


def write_report():
    rows=load(BUNDLE/'rapports/audit_grises_32.json')['mailles'];bilan=load(BUNDLE/'rapports/bilan.json')
    report='''# Audit des 32 mailles grises et triage documentaire V2 — 12 novembre 2026

La proposition V2 conserve les 101 mailles et toutes les décisions scientifiques : **27 rouges, 33 orange, 41 jaunes, zéro gris documentaire**, contre 27/33/9/32 initialement. **Les 101 priorités écologiques restent indéterminées.** La disparition du gris exploratoire décrit une présence cartographique mieux documentée, pas une qualification écologique acquise.

Le nouveau lot est `data/derived/caen_et_nord_triage_20261112_01/RECONNECT_CAEN_ET_NORD_TRIAGE_DOCUMENTAIRE_V2_20261112.zip`, avec `.zip.sha256` et `validation_extraction_v2.json`. Il reste interne et ne remplace pas V1. Le README, les règles versionnées et les vérificateurs sont intégrés au ZIP.

## Diagnostic initial et comparaison

Les 32 anciennes V4 n'ont aucune paire linéaire route–matrice retenue et aucune surface positive SRCE de matrice/réservoir dans leur propre emprise. V1–V3 ne mobilisaient donc aucun signal suffisant. Pourtant **12 ont déjà des haies**, deux de ces 12 des objets de l'inventaire ZH, et 11 ont des sites Cartofriches. Trente contiennent des routes ; deux n'en ont aucune observation. Vingt ne comportent aucun objet haie/eau/ZH dans les sources initiales : cela ne démontre aucune absence écologique. **25 des 32 sont partielles**. Les données et géométries proviennent des six communes réellement acquises ; l'exhaustivité des haies sur Caen n'est pas supposée.

Les motifs V4 exacts, catégories/attributs/longueurs routières, haies, eau, SRCE, ZH, friches, couverture, voisins, distances, précision et données nécessaires figurent dans `rapports/audit_grises_32.csv` et `.json`. La comparaison des 101, les objets justificatifs et limites sont dans `comparaison_101.csv` et `.json`. Aucune observation attestant une absence n'a été créée.

| Initiale → proposée | Rouge | Orange | Jaune | Gris |
| --- | ---: | ---: | ---: | ---: |
| Rouge (27) | 27 | 0 | 0 | 0 |
| Orange (33) | 0 | 33 | 0 | 0 |
| Jaune (9) | 0 | 0 | 9 | 0 |
| Gris (32) | 0 | 0 | 32 | 0 |

## Sources nouvelles et mesures

Deux livraisons officielles IGN ont été récupérées : **OCS GE 2023** et **OCS GE Artificialisation 2023**, département 014, EPSG:2154, Licence Ouverte 2.0. Chaque archive a la taille annoncée et le MD5 officiel : respectivement 138 290 682 et 122 971 095 octets. SHA-256 et provenance dans `provenance/ocsge_sources.json`. Le catalogue officiel distingue les couches complètes des différentiels ; le millésime choisi est 2023, pas la date de publication 2025 ou de téléchargement 2026.

Pour chaque produit : 38 369 objets lus dans la BBOX, **19 231 retenus** sur le territoire, identifiants uniques, **aucune géométrie invalide** dans la sélection source et aucune réparation. Les deux produits décrivent les mêmes objets ; leurs comptes ne sont pas additionnés. Toute l'emprise est couverte ; les résidus locaux sont ≤ 7,79e-8 m², inférieurs au budget M2 préexistant de 1e-6 m². Les codes et usages sont vérifiés avec la nomenclature CSV de la livraison. Cette couverture géométrique n'atteste aucune complétude écologique.

Les **101 mailles** ont de nouvelles observations de polygones végétalisés/aquatiques ; **les 32 anciennes grises ont chacune une couverture végétalisée OCS GE positive**. Sont fournis : surfaces en m² par code CS et US, classes arborées/arbustives/herbacées/aquatiques et statuts officiels artif/non artif. Aucune surface humide n'est déduite de l'OCS GE ; ce champ reste NULL. Les surfaces végétalisées désignent des polygones de classe dominante, pas une mesure de couvert végétal pur. Elles comprennent cultures et espaces d'ornement ; sept cas nouveaux sont exclusivement herbacés parmi les classes végétales. Végétalisé et artificialisé peuvent se recouper et ne doivent pas être additionnés.

Références primaires : [métadonnées IGN OCS GE](https://www.data.gouv.fr/datasets/ocs-ge), [métadonnées IGN Artificialisation](https://www.data.gouv.fr/datasets/ocs-ge-artificialisation), [API de téléchargement IGN](https://cartes.gouv.fr/aide/fr/guides-utilisateur/utiliser-les-services-de-la-geoplateforme/telechargement/). Les descriptifs officiels et la nomenclature sont conservés dans le lot ; leurs concepts décrivent le sol et ses usages, sans attestation de fonctionnalité.

## Évolution proposée, portée scientifique et voisinage

**V1/V2/V3 sont conservées. V3b est réservée aux anciennes V4**, sans incertitude technique critique, avec présence locale valide de haie IGN, plan d'eau IGN ou polygone OCS GE végétalisé/aquatique. Les classes CS et les conditions exactes sont dans `METHODE_TRIAGE_V2.md` et `provenance/table_triage_exploratoire_v2.json`. Routes, artificialisation, sols nus, friches seules, objets ZH ambigus et voisins seuls ne déclenchent pas V3b. Les constantes numériques M2 existantes excluent seulement les résidus ; aucun seuil écologique, de densité, de nombre d'objets ou cible de couleurs n'a été introduit.

Cette extension est défendable **au niveau documentaire uniquement**, avec une légende jaune élargie « éléments cartographiés à documenter ». Elle ne valide ni habitat naturel, ni continuité fonctionnelle, ni valeur écologique, ni urgence. Les 32 changements sont soutenus par **1 708 justificatifs locaux** recalculés contre les géométries fournies. Les données ne permettent toujours pas de calculer une priorité D/S.

Les six voisines du lattice M1 sont recherchées pour les 32, sans tampon choisi. Les objets partagés et uniquement voisins sont séparés ; les distances sont mesurées parmi les objets acquis découpés au territoire, avec leurs précisions ou NULL. Une présence uniquement voisine n'est jamais reportée dans la maille. Un minimum nul peut être un simple contact de frontière. Une continuité de dessin cartographique n'établit pas une continuité fonctionnelle. L'OCS GE a une précision globale décrite comme métrique, sans chiffre inventé par objet ; les haies portent 3 m, les autres inconnues restent NULL.

## Détail des 32 changements

Tous passent de V4/gris à V3b/jaune par présence locale OCS GE végétalisée. Les 12 haies préexistantes contribuent aussi lorsque présentes. Colonnes de surfaces/longueurs ci-dessous arrondies pour lecture ; valeurs exactes, usages et identifiants dans les CSV/JSON. Les suffixes désignent les identifiants complets `NORM-G1K-FLAT-R+…-C+…`.

| Maille | Surface m² | Fraction | Routes m | Haies m | Végétalisé OCS m² | Arboré m² | ZH observés |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
'''
    for r in rows:
        o=r['observations_dans_maille'];n=r['ocsge']['ocsge'];mid=r['maille_id'].replace('NORM-G1K-FLAT-','')
        report+=f"| {mid} | {r['area_m2']:.0f} | {r['pilot_fraction']:.4f} | {o['routes']['mesure_observee']:.0f} | {o['haies']['mesure_observee']:.0f} | {n['surface_polygones_vegetalises_m2']:.0f} | {n['surface_polygones_arbores_m2']:.0f} | {o['zones_humides']['nombre_objets_observes']} |\n"
    report+='''
Les ZH de R+006430-C+000495 sont des friches/cultures photo-interprétées ; celles de R+006431-C+000494 ont typologie et qualité non définies. Elles ne sont pas traitées comme des habitats humides confirmés. Les plans d'eau et mares initialement non observés dans les 32 ne deviennent pas artificiellement présents. Les données OCS GE aquatiques restent distinctes.

## Invariants, livraison et contrôles

Les géométries et clés des 101 mailles sont identiques. **5 336 événements admis, une quarantaine, 60 mailles avec événements / 41 sans, 404 résultats R1–R4 non évaluables, 165 pistes, zéro recommandation : inchangés.** Aucun détecteur routes–matrices ni règle scientifique n'a été relancé ou modifié. Les anciens champs de décision et observations des fiches sont contrôlés individuellement ; les fichiers canoniques et actions sont inchangés par SHA-256.

**1 437 tests réussis**, dont 19 contrôles de la nouvelle condition documentaire ; 40 avertissements existants consignés. Build TypeScript/Vite réussi dans une copie temporaire de M3. Navigation Chrome vérifiée sur une ancienne grise de Caen : jaune V3b, détail OCS GE ouvert, vue D/S séparée, erreur de portée refusée, aucune erreur JavaScript. Captures et rapports dans `rapports/`. Le ZIP final est extrait dans un dossier neuf et vérifié avec le script autonome ; reçu `validation_extraction_v2.json` à côté du ZIP.

M4 peut ingérer les mêmes quatre fichiers internes, complétés par les nouveaux champs, avec les mêmes jointures `(territory_id, grid_version, maille_id)`. La version de grille reste `M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1`. Les versions du socle M2, du complément 2023 et du triage V2 sont distinctes dans le manifeste. Une adaptation additionnelle de deux fichiers M3 met à jour la légende et les observations au clic ; elle s'applique après le patch Caen initial. Instructions exactes : `README.md` du ZIP. Aucun frontend d'équipe n'a été modifié ni déployé.

Les **300 fichiers préexistants protégés** restent identiques à l'état observé au début de cette tâche. L'archive V1 annoncée n'était plus présente à son chemin lors de cet audit ; les 92 fichiers de son dossier décomposé correspondent tous au manifeste V1 et n'ont pas été modifiés. La classification V1 est conservée explicitement dans la nouvelle version. Aucun ZIP antérieur n'a été écrasé. L'incident de place disque a été résolu en traitant les couches successivement et en supprimant les seules nouvelles extractions/écritures partielles ; les archives officielles vérifiées et tous les travaux antérieurs sont conservés.

Le lot est **interne uniquement** : licences et attributions conservées, aucun inventaire de coordonnées d'espèces sensibles acquis, aucun attribut de propriétaire/contact ajouté. Le verrou `test_data=False`, les contrats publics et règles D/S/R1–R4 sont inchangés. Aucun commit, push ou merge. L'absence de gris documentaire ne supprime **aucune des 101 indéterminations écologiques** ni les validations humaines/méthodes encore nécessaires.

Rejeu documentaire autonome facultatif, avec les dépendances SIG déjà consignées : `python reproduction/recalculer_triage_v2.py --output /chemin/vers/un_nouveau_resultat.json` depuis la racine extraite. Ce script recalcule les intersections des seules couches haies/eau/OCS GE avec les 101 mailles et vérifie les classes, sans recalculer les événements M2 ni exécuter D/S ou R1–R4.
'''
    p=ROOT/'docs/audit_grises_et_triage_caen_v2_20261112.md';p.write_text(report,encoding='utf-8')
    (BUNDLE/'rapports/compte_rendu_v2.md').write_text(report,encoding='utf-8')


def seal(old,bilan,components,sources):
    archive=OUT/(BUNDLE.name+'.zip');assert not archive.exists()
    manifest={k:v for k,v in old.items()if k!='files_sha256'}
    manifest.update(format_version='reconnect.caen6.lot-interne-2',created_date='2026-11-12',triage_version=VERSION,
        component_versions=components,controls='rapports/acceptation.json',verification='verifier_triage_v2.py',
        reference_v1='reference_v1/manifest.json',new_sources=sources,publication_autorisee=False,test_data=False)
    manifest['counts']={**manifest['counts'],'triage_documentaire':bilan['classifications_exploratoires'],'changements_gris_jaune':len(bilan['mailles_changees'])}
    files=sorted(p for p in BUNDLE.rglob('*')if p.is_file())
    assert all(not set(p.relative_to(BUNDLE).parts)&{'__pycache__','node_modules','.venv','.DS_Store','.pytest_cache'}for p in files)
    manifest['files_sha256']={p.relative_to(BUNDLE).as_posix():sha(p)for p in files}
    put(BUNDLE/'manifest.json',manifest)
    (BUNDLE/'SHA256SUMS').write_text(''.join(h+'  '+n+'\n'for n,h in sorted({**manifest['files_sha256'],'manifest.json':sha(BUNDLE/'manifest.json')}.items())))
    verify(BUNDLE)
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for p in sorted(BUNDLE.rglob('*')):
            if p.is_file():z.write(p,BUNDLE.name+'/'+p.relative_to(BUNDLE).as_posix())
    fingerprint=sha(archive)
    archive.with_suffix('.zip.sha256').write_text(fingerprint+'  '+archive.name+'\n')
    with tempfile.TemporaryDirectory(prefix='reconnect_triage_v2_extraction_')as temp:
        with zipfile.ZipFile(archive)as z:
            assert z.testzip()is None
            assert all((Path(temp)/n).resolve().is_relative_to(Path(temp).resolve())for n in z.namelist())
            z.extractall(temp)
        result=subprocess.run([sys.executable,'-B',str(Path(temp)/BUNDLE.name/'verifier_triage_v2.py')],capture_output=True,text=True,check=True)
        receipt=json.loads(result.stdout)
    put(OUT/'validation_extraction_v2.json',{'ok':True,'archive':archive.name,'sha256':fingerprint,'bytes':archive.stat().st_size,'verification_apres_extraction_neuve':receipt})
    print(json.dumps({'zip':str(archive.relative_to(ROOT)),'sha256':fingerprint,'bytes':archive.stat().st_size,'extraction_ok':True},ensure_ascii=False,indent=2))


if __name__=='__main__':seal(*document())
