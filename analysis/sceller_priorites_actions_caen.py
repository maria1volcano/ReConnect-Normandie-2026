"""Sceller la correction opérationnelle sans modifier les versions historiques."""
from pathlib import Path
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile

from analysis.livrer_priorites_actions_caen import ROOT,SOURCE,OUT,BUNDLE,load,put,sha
from analysis.prioriser_etudes_interventions import VERSION,TITLE,NOTE
from analysis.verifier_lot_actions_caen import verify


def document():
    assert not (OUT/(BUNDLE.name+'.zip')).exists() and not (BUNDLE/'manifest.json').exists(), 'Lot déjà scellé : aucune réécriture autorisée'
    validation_logs=Path(os.environ.get('M2_VALIDATION_LOG_ROOT',str(OUT)))
    summary=load(BUNDLE/'rapports/bilan_actions.json');source_manifest=load(SOURCE/'manifest.json')
    for p in Path('integration/m3_m4_caen_actions_20261112').iterdir():
        if p.is_file():shutil.copyfile(p,BUNDLE/'integration'/p.name)
    shutil.copyfile(ROOT/'docs/schema_instruction_actions_caen.json',BUNDLE/'provenance/schema_instruction_actions_caen.json')
    for name in ['prioriser_etudes_interventions.py','livrer_priorites_actions_caen.py','verifier_lot_actions_caen.py','rejouer_instruction_actions_caen.py','sceller_priorites_actions_caen.py']:
        shutil.copyfile(ROOT/'analysis'/name,BUNDLE/'provenance/code/analysis'/name)
    shutil.copyfile(ROOT/'tests/test_priorites_etude_interventions.py',BUNDLE/'provenance/code/tests/test_priorites_etude_interventions.py')
    shutil.copyfile(ROOT/'analysis/verifier_lot_actions_caen.py',BUNDLE/'verifier_lot_actions.py')
    shutil.copyfile(ROOT/'analysis/rejouer_instruction_actions_caen.py',BUNDLE/'reproduction/rejouer_instruction_actions.py')
    shutil.copyfile(OUT/'preservation_avant.json',BUNDLE/'provenance/empreintes_avant_correction.json')
    shutil.copyfile(OUT/'snapshot_M3.json',BUNDLE/'provenance/snapshot_M3_actions.json')
    shutil.copyfile(OUT/'tests.log',BUNDLE/'rapports/tests_actions.log')
    shutil.copyfile(validation_logs/'build_M3_actions.log',BUNDLE/'rapports/build_M3_actions.log')
    shutil.copyfile(validation_logs/'tests_M3_priorities.log',BUNDLE/'rapports/tests_M3_priorities.log')
    fmt=load(BUNDLE/'FORMAT_GEOPACKAGES.json')
    for t in fmt['tables']:
        if t['file'].startswith('reproduction/'):
            t['file']='reference_historique/reproduction_v2/'+t['file'][len('reproduction/'):]
    put(BUNDLE/'FORMAT_GEOPACKAGES.json',fmt)
    write_readme();write_format();write_report(summary)
    return summary,source_manifest


def write_readme():
    text='''# ReConnect — priorités d'étude des actions — correction du 12 novembre 2026

**Vue principale : Priorités d'étude des actions écologiques.** Retour aux classes V1 : **27 rouges, 33 orange, 9 jaunes, 32 grises**. Les 101 mailles et fiches, 5 336 événements admis, une quarantaine, diagnostics et 165 pistes sont conservés. La proposition V3b est archivée et n'est pas adoptée comme classement principal. La végétation OCS GE reste un contexte, sans preuve de continuité écologique.

> Classement indicatif fondé sur les données cartographiques. Les aménagements nécessitent une validation écologique et technique avant réalisation.

| Vue d'étude | Décision actuelle |
| --- | --- |
| Rouge — priorité 1 | A04 : étudier en premier la perméabilité et les possibilités de franchissement, sur les indices V1 documentés. |
| Orange — priorité 2 | A04 : évaluer les croisements et la pertinence d'une éventuelle étude de franchissement. |
| Jaune — priorité 3 | Examiner la préservation des éléments SRCE et leur état. Aucune restauration A01–A04 sélectionnée faute de préconditions propres. |
| Gris — non évaluable | Les données ne permettent pas encore de choisir une intervention. Aucun effet de la végétation OCS GE sur cette couleur. |

Cela donne **60 études principales A04**, neuf orientations de préservation et 32 décisions non évaluables. Les 105 autres pistes historiques restent à qualifier ; aucune restauration complémentaire n'est automatiquement retenue. Les 404 résultats scientifiques R1–R4 restent non_evaluable/A2. La priorité écologique officielle D/S reste indéterminée sur les 101. Une sélection indicative d'étude n'est ni l'activation scientifique de R1 ni une prescription de construction.

Le compte A04 désigne des sélections **par maille**, pas 60 projets ou ouvrages distincts. Les événements partagés gardent leurs identifiants canoniques et comptes exclusifs ; regrouper les dossiers concernés avant de définir les études et leur périmètre, sans inventer ici un nombre de projets.

## Ingestion immédiate

1. Extraire le dossier, puis lancer `python3 -B verifier_lot_actions.py` depuis sa racine. Python ≥ 3.9 suffit ; aucune bibliothèque SIG ou installation backend nécessaire à ce contrôle.
2. Pour M3, lire `integration/README.md` : le patch `m3_priorites_etude_actions.patch` est autonome contre le commit M3 `94eef5b8f17dc68af22c323603ec2623b2b58ce1`. Ces fichiers sont des références historiques M2 : ne pas les réappliquer automatiquement à main ou à la PR #5 ; toute adaptation nécessite une revue M3/M4. **Ne pas empiler les anciens patches V1/V2.** Aucun checkout, merge ou modification d'une branche d'équipe n'a été effectué par M2.
3. Depuis frontend, lancer `M2_CAEN_LOT_ROOT='/chemin/absolu/vers/ce_dossier' npm run dev -- --host 127.0.0.1` dans l'application adaptée. Rester en mode réel. Vérifier le badge 101, la légende demandée, la note visible et les décisions au clic. La vue D/S dispose de son propre sélecteur/légende. Captures des quatre couleurs et D/S dans `rapports/`.
4. M4 peut ingérer les JSON ou inclure le routeur facultatif `integration/m4_caen_actions_router.py` dans son FastAPI. Instructions d'import, versions Python et endpoints dans `integration/README.md`. Le routeur/plugin refuse un ancien lot V3b et une mauvaise portée ; lecture et boucle locale uniquement. Aucun `vite build` statique ni répertoire public n'est alimenté avec les données.

## Fichiers actifs et jointures

- `demo_interne/mailles.geojson` : 101 géométries WGS84 inchangées, couleur V1 restaurée, priorité d'étude et action principale ; champs D/S indépendants.
- `demo_interne/fiches_zones.json` : 101 fiches avec diagnostic territorial, décision, action principale/absence motivée, options et conditions avant travaux. Les observations/diagnostics techniques initiaux restent identiques ; les résumés antérieurs sont archivés dans chaque fiche.
- `demo_interne/priorites_etude_interventions.json` : 101 décisions normalisées, dont la copie exacte des champs D/S sous `D_S`.
- `demo_interne/pistes_investigation_trace.json` : 165 identifiants stables, pointeurs vers les actions d'origine, statuts, empreintes et rôle courant. Les huit anciennes pistes R3 en gris restent traçables mais ne choisissent aucune intervention.
- `demo_interne/conflits.geojson` et `actions_resultats.json` : **strictement inchangés**, tout comme les GeoPackages natifs de `rapports/`. L'événement en quarantaine reste exclu des comptes et de la carte.
- `donnees/` : sources géographiques, observations et OCS GE conservées ; `FORMAT_GEOPACKAGES.json` décrit toutes les couches et champs.
- `rapports/decisions_101.csv` : synthèse opérationnelle par maille ; `provenance/politique_etude_interventions.json` et `schema_instruction_actions_caen.json` : politique et format interne explicites.

Joindre par **(`territory_id`, `grid_version`, `maille_id`)**, jamais par maille_id seul entre pilotes. Grille : `M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1` ; territoire : `caen_et_nord_6communes`. Le socle M2 garde sa version ; seule la décision indicative d'étude reçoit la version `caen6-priorites-etude-actions-20261112-1`.

Les formats complémentaires sont internes et documentés ; ils ne remplacent ni le contrat public ni le catalogue M5 manquant. Les identifiants connus A04/R1, A01/R2, A03/R3, A02/R4 et leurs statuts scientifiques sont conservés. Aucun contenu des huit autres fiches M5 n'est inventé. Une orientation de préservation en jaune n'est pas transformée en action de catalogue non disponible.

## Sélection courante et traces historiques

Consommer **`decision_interventions`** pour les décisions d'action et **`priorite_etude_interventions`** pour la carte principale. `action_ids` des mailles et `action_ids_a_etudier` des fiches désignent uniquement les études sélectionnées : A04 dans les 60 rouges/orange, [] ailleurs. Les anciennes listes sont dans `action_ids_pistes_historiques` et `action_ids_a_etudier_reference_v2`.

Le tableau `actions` des fiches conserve les quatre enregistrements historiques pour preuve et traçabilité. **Il ne constitue pas la liste active des interventions recommandées.** Les champs `pistes_investigation_ids` et le fichier de trace permettent de retrouver les 165 pistes originales. Les options non sélectionnées ont une justification et des conditions manquantes ; leur ordre est technique, sans classement de bénéfice. A01/R2 nécessite une lacune de réseau, A03/R3 une friche éligible reliée à une continuité par une méthode documentée, A02/R4 un déficit de réseau humide et un contexte hydrologique. Leur simple présence ne suffit pas.

Les fichiers et patches V2 sont isolés sous `reference_historique/` et la référence V1 est conservée. Ne pas lancer un ancien export V3b pour l'affichage principal. Les sorties précédentes chez le producteur ne sont pas écrasées. Les licences IGN/DREAL/Cerema et toutes les limites de couverture/précision restent dans provenance et les fiches.

## Contrôles et limites

Les 101 décisions ont un diagnostic, chaque option affichable un statut et une justification, et chaque sélection A04 des événements locaux liés aux justifications V1. Aucun calcul géométrique de production, diagnostic D/S ou moteur R1–R4 n'a été relancé. Les géométries, comptes, propriétaires canoniques, NULL et décisions scientifiques sont vérifiés inchangés. Aucune recommandation de travaux validée.

1 456 tests Python passent, dont 19 cas spécifiques de la nouvelle politique. Build M3 et tests de séparation TEST/réel réussis. Navigation réelle testée sur rouge/orange/jaune/gris puis D/S. Douze contrôles du routeur FastAPI passent, dont mauvaise portée, refus de V3b, lecture seule et restrictions locales. Résultats et captures dans rapports.

Rejeu facultatif **sans SIG**, à écrire hors du lot : `python3 -B reproduction/rejouer_instruction_actions.py --output /chemin/exterieur/nouveau_rejeu.json`. Il reconstruit les décisions depuis les justifications V1 et résultats R1–R4 conservés, puis les compare aux 101 sorties. Il n'exécute aucun calcul géométrique ni règle scientifique.

Lot **interne uniquement**, `test_data=False`, publication non autorisée. Aucun contournement de l'export public, aucun risque confirmé ou urgence de travaux déduit. Aucun commit, push ou merge demandé/exécuté dans cette correction. Le raccordement dans l'application de l'équipe reste à réaliser par M3/M4 après revue du patch fourni.
'''
    (BUNDLE/'README.md').write_text(text,encoding='utf-8')
    (BUNDLE/'MESSAGE_M3_M4.md').write_text('''Correction opérationnelle prête : utiliser le nouveau lot ACTIONS_ETUDE, pas le triage V3b comme vue principale. Retour V1 : 27 rouges, 33 orange, 9 jaunes, 32 grises. Légende « Priorités d'étude des actions écologiques » et note de validation avant travaux fournies.

60 études principales A04 sont proposées de manière indicative ; neuf jaunes orientent vers l'examen de préservation ; 32 grises ne choisissent aucune intervention. Les 165 pistes restent traçables, dont 105 non activées en restauration. D/S reste indéterminée sur les 101, R1–R4 restent non évaluables, et les 5 336 événements/une quarantaine sont inchangés. Aucune construction ni restauration validée.

Extraire le ZIP, lancer python3 -B verifier_lot_actions.py et suivre README/integration/README.md. Le patch M3 autonome est testé contre 94eef5b8f17dc68af22c323603ec2623b2b58ce1 ; ne pas empiler les anciens patches. M4 dispose des 101 décisions normalisées et de la trace des pistes. Configurer M2_CAEN_LOT_ROOT vers le nouveau lot. Livraison et serveurs de revue internes uniquement, test_data=False préservé. Aucun fichier/branche d'équipe modifié ni déploiement effectué par M2.
''',encoding='utf-8')


def write_format():
    (BUNDLE/'FORMAT_JSON.md').write_text('''# Formats actifs : instructions d'étude, sans modification du contrat public

`fiches_zones.json.format_version = m2-m4.caen6.actions-etude-interne-1` ; `mailles.geojson.format_version = reconnect.vue-interne-actions-1` ; `priorites_etude_interventions.json.format_version = m2-m4.instruction-actions-1`. Les formats natifs `actionResult`, événements M2 et géométries ne changent pas. `classification_defaut=priorites_etude_interventions` remplace le défaut documentaire V2.

| Emplacement | Champs / usage |
| --- | --- |
| Fiche `priorite_etude_interventions` | intitule, niveau 1/2/3 ou NULL, couleur/hex, libelle, statut indicative/non_evaluable, regle_source V1–V4, version, note, validation_ecologique=false, urgence_travaux=NULL. |
| Fiche `decision_interventions` | diagnostic_territorial, orientation, action_principale nullable, motif d'absence, actions_complementaires, options_actions, conditions_validation_avant_travaux, pistes_existantes_ids et copie D/S distincte. |
| Action/option | action_id A01–A04, regle_id R1–R4, titre, statut_instruction, statut_scientifique non_evaluable, justification, observations, conditions_manquantes, sources pertinentes, piste_existante_id, activation_regle_scientifique=false, travaux_valides=false. A04 sélectionnée ajoute titre_etude, événements/objets justificatifs et prochaines_etapes. |
| Statuts d'instruction | a_instruire_indicatif pour A04 rouge/orange ; qualification_prealable_seulement pour une piste ancienne à qualifier ; non_selectionnable_preconditions_manquantes ; non_selectionnable_donnees_insuffisantes pour le gris. Ils ne remplacent pas les statuts scientifiques. |
| D/S | `priorite_examen`, `priorite_ecologique`, `couverture_synthese`, `regle_appliquee`, `method_version` restent inchangés dans les fiches et sont recopiés dans la décision sous D_S. Aucun calcul ou renommage de priorité scientifique. |
| GeoJSON | priorite_etude_niveau/statut/couleur/libelle/version, action_principale_id nullable, actions_complementaires_ids, description_courte et action_ids des études sélectionnées. Les champs priority_category/validation/method restent scientifiques, indépendants. |
| Trace des 165 pistes | piste_id, portée, action_id/regle_id, statut_origine, statut_scientifique, justification_origine, fiche_pointer, action_origine_sha256, source_origine_sha256, statut_instruction et rôle actuelle principale/non activée. |

Chaque décision et chaque fiche est unique sur (`territory_id`,`grid_version`,`maille_id`). Dans les GeoJSON, le scope est aussi dans l'en-tête ; `conflit_id` se joint aux événements canoniques dans cette même portée. Les comptes locaux peuvent se répéter entre mailles, les propriétaires exclusifs non. Les 41 mailles sans événement restent cliquables ; neuf sont jaunes SRCE, 32 grises. Aucune absence écologique n'est inférée.

`actions` conserve les quatre descriptions historiques, sans les transformer en sélections actuelles. Les alias actifs `action_ids_a_etudier` et `action_ids` sont limités aux 60 A04 sélectionnées ; les anciennes valeurs restent dans les champs *_reference_v2 / *_pistes_historiques. Les champs historiques V3b et les observations OCS GE restent consultables et ne gouvernent plus la couleur.

Le schéma du complément est `provenance/schema_instruction_actions_caen.json`. Son périmètre est cette version du lot : les 404 résultats R1–R4 sont non évaluables et aucune restauration complémentaire ne dispose des préconditions documentées. Une qualification future exige une nouvelle validation/politique, pas une modification silencieuse des statuts. Toutes les recommandations de travaux restent vides. Le catalogue M5 complet et le schéma final applicatif restent à confirmer ; aucune fiche manquante n'est inventée.

Les géométries des GeoJSON sont WGS84 longitude/latitude ; les GeoPackages sont en EPSG:2154. Leur inventaire exhaustif, types, champs et chemins se trouvent dans FORMAT_GEOPACKAGES.json. Les tables natives sans territory_id héritent du scope du lot. NULL signifie inconnu/non calculé, jamais zéro, faible, absence ou action inutile. Aucun champ documentaire n'alimente D/S ni l'exporteur public.
''',encoding='utf-8')


def write_report(summary):
    report='''# Correction opérationnelle — priorités d'étude des actions Caen et nord

**12 novembre 2026.** La vue principale repart de V1 et devient **« Priorités d'étude des actions écologiques »** : **27 rouges, 33 orange, 9 jaunes et 32 grises**. L'extension V3b est conservée dans l'historique, sans adoption automatique. L'OCS GE enrichit les observations mais ne démontre ni continuité fonctionnelle ni pertinence d'une restauration.

Le lot autonome corrigé est :

`data/derived/caen_et_nord_actions_20261112_01/RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1.zip`

Son empreinte est dans `.zip.sha256` ; le reçu après extraction neuve dans `validation_extraction_actions.json`. Les versions et résultats précédents sont conservés.

## Décisions territoriales réellement proposées

| Couleur / rang d'étude | Mailles | Action principale / orientation |
| --- | ---: | --- |
| Rouge — priorité 1 | 27 | A04/R1 : étudier en premier la perméabilité et les possibilités de franchissement. Indices V1 : route carrossable en service au sol, matrice fragile et surface de réservoir dans la maille. |
| Orange — priorité 2 | 33 | A04/R1 : évaluer les croisements documentés pour une éventuelle étude de franchissement, en vérifiant catégorie, service, niveau et ouvrages existants. |
| Jaune — priorité 3 | 9 | Examiner la préservation des éléments SRCE et leur état. Aucune restauration de catalogue sélectionnée sans ses propres préconditions. |
| Gris — non évaluable | 32 | Aucune intervention choisie. L'existence de végétation OCS GE, haies ou sites Cartofriches ne lève pas l'indétermination du choix d'intervention. |

**60 études principales A04**, neuf orientations de préservation et 32 décisions non évaluables. Les 41 mailles sans action principale ne sont donc pas toutes « grises » : neuf ont une orientation de préservation mais aucune restauration A01–A04 qualifiable. Aucun bénéfice comparé, niveau de risque confirmé ou urgence de travaux n'est calculé.

La sélection est une **décision indicative d'instruction**, conformément à la correction demandée, pas une qualification positive de R1. Ses indices sont vérifiés dans les justifications V1 existantes et les événements locaux ; le besoin de construction n'est jamais présumé. Les quatre options par maille gardent leur statut scientifique, leur justification, les observations, les sources et les conditions manquantes.

Ce compte d'A04 est **par maille**, pas un nombre de projets indépendants ni d'ouvrages à construire. Les mêmes événements peuvent être partagés ; leurs identifiants et comptes exclusifs restent disponibles pour regrouper les dossiers, sans calcul géométrique ni seuil de regroupement ajouté.

## Préconditions et pistes préservées

Les 165 pistes historiques sont toutes traçables par identifiant stable, maille/grille/territoire, règle/action, pointeur vers l'enregistrement d'origine et empreinte. Elles se répartissent en **60 R1, 50 R2, 35 R3, 20 R4**. Les 60 R1 sont reliées à l'étude principale ; les **105 autres restent à qualifier**, sans activation automatique. Les huit anciennes pistes R3 dans les mailles grises restent consultables mais ne choisissent aucune intervention.

La présence de haies, de friches ou d'eau ne suffit pas. R2/A01 requiert une lacune structurale/topologique et une sous-trame pertinente ; R3/A03 une friche éligible avec relation à une continuité selon une méthode documentée ; R4/A02 un déficit de réseau d'habitats humides et un contexte hydrologique adaptés. Ces préconditions ne sont pas documentées dans ce lot : **aucune restauration complémentaire n'est retenue**. Une orientation de préservation en jaune n'est pas artificiellement rattachée à une fiche M5 manquante.

Chaque fiche expose le rang d'étude, le diagnostic territorial, l'action principale ou son absence motivée, les options complémentaires/non sélectionnées, les justifications, les conditions écologiques et techniques avant travaux, et la priorité D/S distincte. Les étapes d'A04 comprennent la lecture des segments XY, la vérification des ouvrages/niveaux, la qualification des déplacements/espèces et l'examen des options avec le gestionnaire.

## Invariants scientifiques et géographiques

Les **101 mailles et géométries**, **5 336 événements admis**, **une quarantaine**, **60 mailles avec événements / 41 sans**, les diagnostics techniques et observations sont inchangés. Aucun détecteur, agrégateur, calcul ENJ ou D/S de production n'a été relancé. Les résultats scientifiques R1–R4 restent **404 non_evaluable / A2** et les **101 priorités D/S indéterminées**. Méthodes, règles D/S/R1–R4, NULL et contrats publics sont préservés. Aucune recommandation de travaux validée.

Les résumés élus sont réorientés vers l'action, avec conservation du résumé V2 d'origine dans chaque fiche. Les 165 descriptions d'origine restent intactes dans `actions`, mais ce champ ne constitue pas la sélection courante. Les alias actifs `action_ids` / `action_ids_a_etudier` contiennent uniquement les études sélectionnées, A04 pour les 60 rouges/orange et [] ailleurs ; leurs anciennes valeurs sont conservées séparément. Cette distinction évite qu'une vieille piste soit affichée comme intervention recommandée en gris.

## Adaptation M3/M4 et vérification

La branche M3 inspectée est `feat/m3-frontend-reconnect-v61`, commit **94eef5b8f17dc68af22c323603ec2623b2b58ce1**. Une adaptation autonome de huit fichiers est fournie dans `integration/m3_priorites_etude_actions.patch`. Elle conserve l'application React/MapLibre, ajoute la nouvelle légende et la note visible, conserve la vue D/S séparée et affiche les décisions au clic. Elle a été appliquée et compilée dans des copies temporaires ; aucune branche de M3 n'a été modifiée. Ne pas empiler les anciens patches V1/V2.

La légende est celle demandée : rouge priorité 1, orange priorité 2, jaune priorité 3, gris décision non évaluable. La note visible est : « Classement indicatif fondé sur les données cartographiques. Les aménagements nécessitent une validation écologique et technique avant réalisation. » Aucun vocabulaire de risque confirmé ou d'urgence de travaux n'est substitué.

M4 dispose des GeoJSON et fiches habituels, d'un fichier normalisé `priorites_etude_interventions.json`, de `pistes_investigation_trace.json`, d'un CSV des 101 décisions et d'un routeur interne facultatif. Le complément de format est explicitement versionné ; aucun contrat public n'est remplacé. L'ingestion garde les clés `(territory_id, grid_version, maille_id)` et `conflit_id` pour les événements. `test_data=False` reste inchangé ; les serveurs de revue sont limités à la boucle locale, et un ancien lot V3b est refusé comme vue active.

Contrôles :

- **1 456 tests Python réussis**, dont 19 cas de priorité d'étude ; 40 avertissements existants consignés.
- Schéma interne validé pour les 101 décisions : chaque action affichable possède un statut et une justification ; aucune restauration/travaux activés artificiellement.
- Build TypeScript/Vite réussi et tests M3 de séparation TEST/réel/versions réussis ; avertissement de taille de bundles conservé.
- Douze contrôles du routeur FastAPI aux versions M4 : 101 mailles/décisions, 165 pistes, cas rouge/gris, erreur de portée, lecture seule, restrictions locales et refus de V3b.
- Navigation Chrome réussie sur les quatre couleurs : A04 en rouge/orange, absence motivée en jaune/gris, note visible et D/S séparée ; aucune erreur JavaScript. Captures dans rapports.
- Vérification autonome du ZIP après extraction dans un dossier neuf ; empreintes, géométries, événements, liens, profils scientifiques, trace des 165 pistes et non-sélections contrôlés sans calcul SIG.

Le ZIP contient un rejeu de décision **sans SIG ni moteur scientifique**, et un vérificateur autonome avec la bibliothèque standard Python. Les sources/versions/licences et observations OCS GE restent disponibles en contexte. Aucun fichier historique, calcul validé ou archive antérieure n'a été écrasé.

## Transmission

Extraire le ZIP et lancer `python3 -B verifier_lot_actions.py`. Suivre ensuite `README.md` et `integration/README.md` pour M3/M4. Un message prêt à transmettre est inclus. Le raccordement à la branche applicative doit encore être réalisé par l'équipe ; aucun déploiement n'est affirmé. Le catalogue M5 complet et les validations écologiques/techniques restent nécessaires avant réalisation de travaux.

**Aucun commit, push ou merge n'a été effectué pour cette correction.** La PR #2 précédemment poussée n'est pas actualisée automatiquement. La présente livraison est interne, avec publication non autorisée et garde-fous publics conservés.
'''
    path=ROOT/'docs/priorites_etude_actions_caen_20261112.md';path.write_text(report,encoding='utf-8')
    (BUNDLE/'rapports/compte_rendu_actions.md').write_text(report,encoding='utf-8')


def seal(summary,source_manifest):
    archive=OUT/(BUNDLE.name+'.zip');assert not archive.exists()
    before=load(OUT/'preservation_avant.json');assert all(sha(ROOT/p)==h for p,h in before.items()),'Fichier antérieur modifié'
    # Relecture contractuelle et comparaison des décisions, pas de calcul géométrique.
    from jsonschema import Draft202012Validator
    validator=Draft202012Validator(load(BUNDLE/'provenance/schema_instruction_actions_caen.json'))
    for d in load(BUNDLE/'demo_interne/priorites_etude_interventions.json')['mailles']:validator.validate(d)
    manifest={'format_version':'reconnect.caen6.actions-etude-interne-1','date':'2026-11-12','scope':source_manifest['scope'],
        'classification_defaut':'priorites_etude_interventions','version_priorisation_etudes':VERSION,'intitule':TITLE,'note':NOTE,
        'component_versions':{**{k:v for k,v in source_manifest.get('component_versions',{}).items()if k!='triage'},
            'triage_affichage':'caen6-documentaire-20261111-1','triage_V3b_historique':source_manifest.get('component_versions',{}).get('triage'),
            'instruction_actions':VERSION},
        'publication_autorisee':False,'test_data':False,'public_export':False,'diffusion':'interne_revue_uniquement',
        'counts':summary,'source_manifest_sha256':sha(SOURCE/'manifest.json'),'reference_source':'reference_historique/manifest.json',
        'sources_et_licences':'provenance/sources_licences.json et provenance/ocsge_sources.json',
        'verification':'verifier_lot_actions.py','entrypoints':{'mailles':'demo_interne/mailles.geojson','fiches':'demo_interne/fiches_zones.json',
            'decisions':'demo_interne/priorites_etude_interventions.json','pistes':'demo_interne/pistes_investigation_trace.json','evenements':'demo_interne/conflits.geojson','resultats_scientifiques':'demo_interne/actions_resultats.json'},
        'geometries_recalculees':False,'priorites_DS_modifiees':False,'regles_R1_R4_modifiees':False,'fichiers_anterieurs_preserves':len(before)}
    files=sorted(p for p in BUNDLE.rglob('*')if p.is_file())
    assert all(not set(p.relative_to(BUNDLE).parts)&{'__pycache__','node_modules','.venv','.DS_Store','.pytest_cache'}for p in files)
    manifest['files_sha256']={p.relative_to(BUNDLE).as_posix():sha(p)for p in files}
    put(BUNDLE/'manifest.json',manifest)
    (BUNDLE/'SHA256SUMS').write_text(''.join(h+'  '+p+'\n'for p,h in sorted({**manifest['files_sha256'],'manifest.json':sha(BUNDLE/'manifest.json')}.items())))
    verify(BUNDLE)
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        for p in sorted(BUNDLE.rglob('*')):
            if p.is_file():z.write(p,BUNDLE.name+'/'+p.relative_to(BUNDLE).as_posix())
    h=sha(archive);archive.with_suffix('.zip.sha256').write_text(h+'  '+archive.name+'\n')
    with tempfile.TemporaryDirectory(prefix='reconnect_actions_extraction_')as temp:
        with zipfile.ZipFile(archive)as z:
            assert z.testzip()is None
            assert all((Path(temp)/p).resolve().is_relative_to(Path(temp).resolve())for p in z.namelist())
            z.extractall(temp)
        run=subprocess.run([sys.executable,'-B',str(Path(temp)/BUNDLE.name/'verifier_lot_actions.py')],text=True,capture_output=True,check=True)
        checked=__import__('json').loads(run.stdout)
    put(OUT/'validation_extraction_actions.json',{'ok':True,'archive':archive.name,'sha256':h,'bytes':archive.stat().st_size,'verification':checked})
    print(__import__('json').dumps({'zip':str(archive.relative_to(ROOT)),'sha256':h,'bytes':archive.stat().st_size,'extraction_ok':True},ensure_ascii=False,indent=2))


if __name__=='__main__':seal(*document())
