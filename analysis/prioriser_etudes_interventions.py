"""Priorités indicatives d'étude, distinctes des décisions scientifiques D/S et R1–R4.

Politique explicitement demandée le 12 novembre 2026 : retour à V1 et étude A04
pour les rouges/orange. Une ancienne piste n'active pas une restauration.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy

VERSION = "caen6-priorites-etude-actions-20261112-1"
TITLE = "Priorités d'étude des actions écologiques"
NOTE = "Classement indicatif fondé sur les données cartographiques. Les aménagements nécessitent une validation écologique et technique avant réalisation."
PALETTE = {"rouge":"#D64545", "orange":"#EF9229", "jaune":"#E8C84A", "gris":"#9098A4"}
LEVELS = {"rouge":1, "orange":2, "jaune":3, "gris":None}
LABELS = {
    "rouge":"priorité 1 — action à examiner en premier",
    "orange":"priorité 2 — intervention potentielle à évaluer",
    "jaune":"priorité 3 — préservation ou amélioration à examiner",
    "gris":"décision non évaluable",
}
PAIRING = {"R1":"A04", "R2":"A01", "R3":"A03", "R4":"A02"}
CARROSSABLES = {"Route à 1 chaussée", "Route à 2 chaussées", "Type autoroutier", "Bretelle", "Rond-point"}
FRAGILE = "Matrice fragile, fortement sensible à la fragmentation"
BEFORE_WORKS = [
    "Confirmer sur le terrain les enjeux, habitats/espèces et la fonctionnalité écologique concernés",
    "Vérifier la localisation, l'actualité des données et les ouvrages ou aménagements existants",
    "Valider la faisabilité technique, les contraintes de gestion, les usages et le contexte foncier",
    "Documenter les préconditions de la famille d'action et appliquer une méthode approuvée",
    "Faire valider le besoin et le choix d'aménagement par les responsables écologiques et techniques",
]


def piste_id(fiche, action):
    return ":".join(["piste", fiche["territory_id"], fiche["grid_version"], fiche["maille_id"], action["regle_id"], action["action_id"]])


def _reference(fiche):
    return fiche.get("triage_documentaire_reference_v1", fiche["triage_documentaire"])


def validate_reference(fiche):
    """Contrôle les justificatifs existants sans recalcul de géométrie ni D/S."""
    ref = _reference(fiche);color=ref["niveau"];obs=ref["observations_justificatives"]
    assert color in LEVELS and ref["regle"] == {"rouge":"V1","orange":"V2","jaune":"V3","gris":"V4"}[color]
    pairs=ref["paires_justificatives"]
    assert len(pairs)==obs["nombre_paires_route_corridor_2d"]
    assert len({(p["route_id"],p["corridor_id"])for p in pairs})==len(pairs)
    local_ids=set(fiche["diagnostic_techniciens"]["conflit_ids"])
    assert set(ref["conflit_ids_justificatifs"])<=local_ids
    assert all(set(p["conflit_ids"])<=local_ids for p in pairs)
    if color in {"rouge","orange"}:
        assert pairs and ref["conflit_ids_justificatifs"]
    else:
        assert not pairs
    if color=="rouge":
        eligible=[p for p in pairs if p["categorie"]in CARROSSABLES and p["statut_objet"]=="En service" and str(p["position_sol"])=="0" and p["classe_corridor"]==FRAGILE]
        assert eligible and len(eligible)==obs["paires_route_matrice_fragile_en_service_au_sol"]
        assert obs["reservoir_presence_surface_positive"] and fiche["diagnostic_techniciens"]["observations"]["reservoirs"]["mesure_observee"]>0
    if color=="jaune":assert obs["reservoir_presence_surface_positive"]or obs["corridor_presence_surface_positive"]
    if color=="gris":assert not obs["reservoir_presence_surface_positive"]and not obs["corridor_presence_surface_positive"]
    return ref


def territorial_problem(fiche, ref):
    o=fiche["diagnostic_techniciens"]["observations"];pairs=ref["observations_justificatives"]["nombre_paires_route_corridor_2d"]
    if ref["niveau"]=="rouge":
        return (f"{ref['observations_justificatives']['paires_route_matrice_fragile_en_service_au_sol']} paires route carrossable en service au sol–matrice fragile sont documentées, avec une surface de réservoir dans la maille. "
                "Ces indices de fragmentation potentielle justifient d'instruire la perméabilité, sans obstacle écologique confirmé.")
    if ref["niveau"]=="orange":
        return (f"{pairs} paires linéaires routes–matrices sont observées. Leur contexte ne réunit pas tous les indices V1 ; "
                "il faut évaluer la pertinence d'une étude de franchissement après vérification des catégories, niveaux et ouvrages.")
    if ref["niveau"]=="jaune":
        return (f"{o['corridors']['nombre_objets_observes']} matrices et {o['reservoirs']['nombre_objets_observes']} réservoirs sont cartographiés, sans croisement linéaire route–matrice retenu. "
                "Examiner leur préservation et leur état ; une restauration exige ses propres préconditions. L'absence de croisement observé ne démontre pas l'absence de fragmentation.")
    return (f"Les indices V1–V3 ne sont pas réunis. {o['haies']['nombre_objets_observes']} haies et {o['friches']['nombre_objets_observes']} sites Cartofriches sont observés, "
            "mais les données ne permettent pas encore de choisir une intervention. La végétation OCS GE ne suffit pas à démontrer une continuité écologique.")


def _factual_action_context(fiche, rule):
    o=fiche["diagnostic_techniciens"]["observations"]
    if rule=="R1":
        return f"{_reference(fiche)['observations_justificatives']['nombre_paires_route_corridor_2d']} paires linéaires documentées ; ouvrages, gêne et perméabilité non qualifiés."
    if rule=="R2":
        return f"{o['haies']['nombre_objets_observes']} haies, {o['haies']['mesure_observee']:.1f} m observés ; aucune lacune fonctionnelle ou topologique validée fournie."
    if rule=="R3":
        return (f"{o['friches']['nombre_objets_observes']} sites Cartofriches, dont {fiche['diagnostic_techniciens']['sites_friches_statut_actif']} au statut source friche ; "
                "la relation à une continuité, l'éligibilité écologique et le statut actuel restent à qualifier.")
    return (f"{o['plans_eau']['nombre_objets_observes']} plans d'eau, {fiche['diagnostic_techniciens']['mares_referencees']} mares explicitement référencées ; "
            "ce zéro n'atteste aucune absence. Aucun déficit de réseau humide et contexte hydrologique validés fournis.")


def decide(fiche, scientific_results):
    """Sélection d'étude A04 autorisée ; jamais promotion d'un statut R1–R4."""
    ref=validate_reference(fiche);color=ref["niveau"];actions={a["regle_id"]:a for a in fiche["actions"]}
    assert set(actions)==set(PAIRING)==set(scientific_results)
    for rule, aid in PAIRING.items():
        assert actions[rule]["action_id"]==scientific_results[rule]["action_id"]==aid
        # Ce lot n'a aucune qualification scientifique positive à interpréter.
        assert scientific_results[rule]["statut"]=="non_evaluable"
        assert not actions[rule]["travaux_preconises"]
    priority={"intitule":TITLE,"niveau":LEVELS[color],"couleur":color,"couleur_hex":PALETTE[color],"libelle":LABELS[color],
        "statut":"indicative"if color!="gris"else"non_evaluable","regle_source":ref["regle"],"version":VERSION,
        "validation_ecologique":False,"urgence_travaux":None,"note":NOTE}
    options=[];primary=None
    for rule, aid in PAIRING.items():
        original=actions[rule];scientific=scientific_results[rule]
        has_piste=original["piste_investigation"]=="a_etudier"
        selected=rule=="R1"and color in {"rouge","orange"}
        if selected:
            status="a_instruire_indicatif"
            reason=territorial_problem(fiche,ref)
        elif color=="gris":
            status="non_selectionnable_donnees_insuffisantes"
            reason="Aucune intervention choisie dans une maille V4 ; une piste documentaire ancienne n'est pas une activation de règle."
        else:
            status="qualification_prealable_seulement"if has_piste else"non_selectionnable_preconditions_manquantes"
            reason="Les préconditions propres à cette action ne sont pas documentées ; la présence d'objets ou une couleur ne suffit pas à la sélectionner."
        option={"action_id":aid,"regle_id":rule,"titre":original["titre"],"statut_instruction":status,"statut_scientifique":scientific["statut"],
            "regle_decision_scientifique":scientific["regle_decision"],"justification":reason,"observations":_factual_action_context(fiche,rule),
            "conditions_manquantes":deepcopy(original["conditions_manquantes"]),
            "sources":{k:deepcopy(original['sources'].get(k,[]))for k in {
                'R1':['routes','corridors','reservoirs'],'R2':['haies','corridors','reservoirs'],
                'R3':['friches','corridors','reservoirs'],'R4':['plans_eau','zones_humides','reservoirs']}[rule]},
            "piste_existante_id":piste_id(fiche,original)if has_piste else None,"piste_existante_statut":original["piste_investigation"],
            "restauration_selectionnee":False,"travaux_valides":False,"activation_regle_scientifique":False}
        if selected:
            option["titre_etude"]="Étudier la perméabilité et les possibilités de franchissement"if color=="rouge"else"Évaluer les croisements pour une éventuelle étude de franchissement"
            option["justificatifs"]={"regle_V1":ref["regle"],"conflit_ids":deepcopy(ref["conflit_ids_justificatifs"]),
                "route_ids":sorted({p["route_id"]for p in ref["paires_justificatives"]}),
                "corridor_ids":sorted({p["corridor_id"]for p in ref["paires_justificatives"]}),"reservoir_ids":deepcopy(ref["reservoir_ids"]),
                "contexte_routier":{k:dict(Counter(str(p[k])for p in ref["paires_justificatives"]))for k in["categorie","statut_objet","position_sol"]}}
            option["prochaines_etapes"]=["Examiner les segments d'intersection et leur précision cartographique",
                "Vérifier sur site les ouvrages existants, le niveau des tronçons et leur franchissabilité",
                "Qualifier les espèces, sous-trames et déplacements concernés avec un écologue",
                "Comparer les options de perméabilité avec le gestionnaire avant toute prescription"]
            primary=deepcopy(option)
        options.append(option)
    if color=="jaune":
        orientation="Examiner la préservation des éléments SRCE cartographiés ; qualifier leur état avant d'envisager une amélioration."
        absent="Orientation de préservation justifiée ; aucune action de restauration A01–A04 n'a ses propres préconditions documentées."
    elif color=="gris":
        orientation="Décision non évaluable : les données ne permettent pas encore de choisir une intervention."
        absent="Aucun choix d'intervention justifié ; conserver les pistes historiques comme éléments à qualifier, sans les activer."
    else:
        orientation="Instruire d'abord l'étude A04, sans présumer un besoin de construction ni un bénéfice comparé."
        absent=None
    return {"maille_id":fiche["maille_id"],"grid_version":fiche["grid_version"],"territory_id":fiche["territory_id"],
        "version":VERSION,"priorite_etude_interventions":priority,"diagnostic_territorial":territorial_problem(fiche,ref),
        "probleme_ecologique_confirme":None,"statut_probleme_ecologique":"non_confirme","action_principale":primary,"motif_absence_action_principale":absent,
        "actions_complementaires":[],"motif_absence_complementaires":"Aucune autre famille ne dispose ici des préconditions documentées permettant de sélectionner une restauration.",
        "options_actions":options,"orientation":orientation,"conditions_validation_avant_travaux":deepcopy(BEFORE_WORKS),
        "recommandations_travaux_validees":[],"pistes_existantes_ids":[piste_id(fiche,a)for a in fiche["actions"]if a["piste_investigation"]=="a_etudier"],
        "D_S":{"priorite_ecologique":deepcopy(fiche['priorite_ecologique']),"priorite_examen":deepcopy(fiche['priorite_examen']),
            "method_version":fiche.get('method_version'),"couverture_synthese":fiche.get('couverture_synthese'),"regle_appliquee":fiche.get('regle_appliquee')},
        "priorite_ecologique_reference":"fiche.priorite_ecologique / fiche.priorite_examen : inchangées",
        "catalogue_M5_complet_disponible":False,"classement_benefice":None}
