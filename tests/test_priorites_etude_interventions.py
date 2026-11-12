"""Décisions indicatives d'étude : préconditions, non-promotion et traçabilité."""
from copy import deepcopy
import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from analysis.prioriser_etudes_interventions import decide, PAIRING, FRAGILE, NOTE


def case(color):
    crossing=color in {'rouge','orange'}
    pair={'route_id':'route_synthetique','corridor_id':'matrice_synthetique','categorie':'Route à 1 chaussée',
          'statut_objet':'En service','position_sol':'0','classe_corridor':FRAGILE,'conflit_ids':['evt_synthetique']}
    obs={'routes':{'nombre_objets_observes':1,'mesure_observee':20},'corridors':{'nombre_objets_observes':int(color!='gris'),'mesure_observee':30 if color!='gris'else 0},
         'reservoirs':{'nombre_objets_observes':int(color=='rouge'),'mesure_observee':10 if color=='rouge'else 0},
         'haies':{'nombre_objets_observes':1,'mesure_observee':100},'plans_eau':{'nombre_objets_observes':1,'mesure_observee':200},
         'friches':{'nombre_objets_observes':1,'mesure_observee':300}}
    ref={'niveau':color,'regle':{'rouge':'V1','orange':'V2','jaune':'V3','gris':'V4'}[color],
         'observations_justificatives':{'nombre_paires_route_corridor_2d':int(crossing),'paires_route_matrice_fragile_en_service_au_sol':int(crossing),
             'reservoir_presence_surface_positive':color=='rouge','corridor_presence_surface_positive':color!='gris'},
         'paires_justificatives':[pair]if crossing else [],'conflit_ids_justificatifs':['evt_synthetique']if crossing else [],'reservoir_ids':['res_synthetique']if color=='rouge'else[]}
    actions=[{'regle_id':r,'action_id':a,'titre':'Étude synthétique '+r,'piste_investigation':'a_etudier',
              'conditions_manquantes':['Méthode propre et validation manquantes'],'sources':{},'travaux_preconises':False}for r,a in PAIRING.items()]
    f={'maille_id':'MAILLE_SYNTHETIQUE','grid_version':'GRILLE_TEST','territory_id':'TERRITOIRE_TEST','triage_documentaire':ref,'actions':actions,
       'diagnostic_techniciens':{'conflit_ids':['evt_synthetique']if crossing else[],'observations':obs,'sites_friches_statut_actif':1,'mares_referencees':0},
       'priorite_ecologique':{'conclusion':'indeterminee'},'priorite_examen':{'etat':'non_calculee','valeur':None}}
    science={r:{'action_id':a,'statut':'non_evaluable','regle_decision':'A2'}for r,a in PAIRING.items()}
    return f,science


@pytest.mark.parametrize('color,level',[('rouge',1),('orange',2),('jaune',3),('gris',None)])
def test_levels_are_indicative_and_never_change_science(color,level):
    f,s=case(color);before=deepcopy((f,s));d=decide(f,s)
    assert d['priorite_etude_interventions']['niveau']==level
    assert d['priorite_etude_interventions']['validation_ecologique']is False
    assert d['priorite_etude_interventions']['note']==NOTE
    assert d['D_S']['priorite_ecologique']==f['priorite_ecologique']and d['D_S']['priorite_examen']==f['priorite_examen']
    Draft202012Validator(json.loads((Path(__file__).parents[1]/'docs/schema_instruction_actions_caen.json').read_text())).validate(d)
    assert not d['recommandations_travaux_validees']and d['probleme_ecologique_confirme']is None
    assert (f,s)==before


@pytest.mark.parametrize('color',['rouge','orange'])
def test_main_action_is_only_an_A04_study(color):
    f,s=case(color);d=decide(f,s);a=d['action_principale']
    assert a['action_id']=='A04'and a['regle_id']=='R1'and a['statut_instruction']=='a_instruire_indicatif'
    assert a['statut_scientifique']=='non_evaluable'and a['activation_regle_scientifique']is False
    assert a['justificatifs']['conflit_ids']==['evt_synthetique']and not a['travaux_valides']
    assert a['prochaines_etapes']and a['conditions_manquantes']


def test_yellow_has_preservation_orientation_without_automatic_restoration():
    f,s=case('jaune');d=decide(f,s)
    assert d['action_principale']is None and 'préservation'in d['orientation']
    assert d['motif_absence_action_principale']and not d['actions_complementaires']
    assert all(a['statut_instruction']!='a_instruire_indicatif'for a in d['options_actions'])


def test_gray_stays_non_evaluable_despite_presence_and_legacy_pistes():
    f,s=case('gris');f['triage_documentaire_reference_v1']=deepcopy(f['triage_documentaire'])
    f['triage_documentaire']={'niveau':'jaune','regle':'V3b'}
    f['diagnostic_techniciens']['observations']['ocsge']={'surface_polygones_vegetalises_m2':999999}
    d=decide(f,s)
    assert d['priorite_etude_interventions']['couleur']=='gris'and d['priorite_etude_interventions']['statut']=='non_evaluable'
    assert d['action_principale']is None and not d['actions_complementaires']
    assert len(d['pistes_existantes_ids'])==4
    assert all(a['statut_instruction']=='non_selectionnable_donnees_insuffisantes'for a in d['options_actions'])


@pytest.mark.parametrize('rule',['R2','R3','R4'])
def test_hedge_friche_or_water_presence_does_not_activate_restoration(rule):
    f,s=case('rouge');d=decide(f,s);a=next(a for a in d['options_actions']if a['regle_id']==rule)
    assert a['piste_existante_id']and a['statut_instruction']=='qualification_prealable_seulement'
    assert not a['restauration_selectionnee']and not a['activation_regle_scientifique']and not a['travaux_valides']


@pytest.mark.parametrize('change',['missing_event','out_of_cell','no_fragile','underground','not_service','no_reservoir'])
def test_red_color_without_documented_local_preconditions_is_rejected(change):
    f,s=case('rouge');r=f['triage_documentaire'];p=r['paires_justificatives'][0]
    if change=='missing_event':r['conflit_ids_justificatifs']=[]
    elif change=='out_of_cell':p['conflit_ids']=['evt_uniquement_voisin']
    elif change=='no_fragile':p['classe_corridor']='Autre classe'
    elif change=='underground':p['position_sol']='-1'
    elif change=='not_service':p['statut_objet']='En projet'
    elif change=='no_reservoir':f['diagnostic_techniciens']['observations']['reservoirs']['mesure_observee']=0
    with pytest.raises(AssertionError):decide(f,s)


def test_orange_context_may_include_an_elevated_segment_without_constructing():
    f,s=case('orange');f['triage_documentaire']['paires_justificatives'][0]['position_sol']='1'
    d=decide(f,s)
    assert d['action_principale']['justificatifs']['contexte_routier']['position_sol']=={'1':1}
    assert not d['action_principale']['travaux_valides']


def test_new_scientific_results_require_review_of_this_versioned_policy():
    f,s=case('rouge');s['R2']['statut']='etayee_pour_examen'
    with pytest.raises(AssertionError):decide(f,s)


@pytest.mark.parametrize('sealed_by',['archive','manifest'])
def test_documentation_cannot_rewrite_an_already_sealed_delivery(tmp_path,monkeypatch,sealed_by):
    from analysis import sceller_priorites_actions_caen as sealer
    bundle=tmp_path/'lot';bundle.mkdir()
    original=bundle/'README.md';original.write_text('Livraison historique à préserver')
    if sealed_by=='archive':(tmp_path/'lot.zip').write_bytes(b'archive historique')
    else:(bundle/'manifest.json').write_text('{}')
    monkeypatch.setattr(sealer,'OUT',tmp_path)
    monkeypatch.setattr(sealer,'BUNDLE',bundle)
    with pytest.raises(AssertionError,match='déjà scellé'):sealer.document()
    assert original.read_text()=='Livraison historique à préserver'
