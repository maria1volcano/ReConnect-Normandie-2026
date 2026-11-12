"""Nouvelle livraison d'instruction d'actions : V1 principal, sans calcul SIG."""
from __future__ import annotations
from collections import Counter, defaultdict
from copy import deepcopy
import csv
import hashlib
import json
from pathlib import Path
import shutil

from analysis.prioriser_etudes_interventions import decide, piste_id, VERSION, TITLE, NOTE, LABELS, LEVELS, PALETTE

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'data/derived/caen_et_nord_triage_20261112_01/RECONNECT_CAEN_ET_NORD_TRIAGE_DOCUMENTAIRE_V2_20261112'
OUT=ROOT/'data/derived/caen_et_nord_actions_20261112_01'
BUNDLE=OUT/'RECONNECT_CAEN_ET_NORD_ACTIONS_ETUDE_20261112_V1'


def load(path):return json.loads(Path(path).read_text())


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def digest_json(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def put(path,data):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def build():
    old=load(SOURCE/'manifest.json')
    assert all(sha(SOURCE/name)==h for name,h in old['files_sha256'].items()),'Lot source altéré'
    assert not BUNDLE.exists()
    shutil.copytree(SOURCE,BUNDLE)
    history=BUNDLE/'reference_historique';history.mkdir()
    for name in ['manifest.json','SHA256SUMS','README.md','FORMAT_JSON.md','METHODE_TRIAGE_V2.md','MESSAGE_M4_M5.md','verifier_lot.py','verifier_triage_v2.py']:
        shutil.move(str(BUNDLE/name),str(history/name))
    shutil.move(str(BUNDLE/'integration'),str(history/'integration_v2'))
    shutil.move(str(BUNDLE/'reproduction'),str(history/'reproduction_v2'))
    native={'admis.validation.json','strict.validation.json','enjeux.validation.json','enjeux.gpkg','evenements.gpkg','evenements_detectes.gpkg',
        'quarantaine.gpkg','quarantaine.validation.json','mailles.gpkg','resultats.json','commandes.json','config_enjeux.json','config_conflits.json',
        'grille.validation.json','sources_preparees.json','sources_optionnelles_preparees.json'}
    (history/'rapports_v2').mkdir()
    for p in (BUNDLE/'rapports').iterdir():
        if p.name not in native:shutil.move(str(p),str(history/'rapports_v2'/p.name))
    for name in ['integration','reproduction']:(BUNDLE/name).mkdir()
    doc=load(SOURCE/'demo_interne/fiches_zones.json');geo=load(SOURCE/'demo_interne/mailles.geojson')
    immutable=['priorite_examen','priorite_ecologique','couverture_synthese','regle_appliquee','method_version','diagnostic_ids_justificatifs','diagnostic_ids_non_evalues','motifs_limites']
    put(BUNDLE/'provenance/invariants_avant.json',{'source_manifest_sha256':sha(SOURCE/'manifest.json'),
        'source_fiches_sha256':old['files_sha256']['demo_interne/fiches_zones.json'],
        'mailles':{f['maille_id']:{'DS':{k:deepcopy(f[k])for k in immutable},'actions_sha256':digest_json(f['actions']),
            'diagnostic_techniciens_sha256':digest_json(f['diagnostic_techniciens'])}for f in doc['fiches']}})
    scientific=load(SOURCE/'demo_interne/actions_resultats.json');by_mail=defaultdict(dict)
    for r in scientific['resultats']:by_mail[r['maille_id']][r['rule_id']]=r
    props={f['properties']['maille_id']:f['properties']for f in geo['features']}
    decisions=[];trace=[];colors=Counter();main=Counter();rows=[]
    for index,f in enumerate(doc['fiches']):
        mid=f['maille_id'];d=decide(f,by_mail[mid]);decisions.append(d)
        f['diagnostic_elus_reference_v2']=deepcopy(f['diagnostic_elus'])
        f['triage_documentaire_v3b_historique']=deepcopy(f['triage_documentaire'])
        f['triage_documentaire']=deepcopy(f['triage_documentaire_reference_v1'])
        f['priorite_etude_interventions']=deepcopy(d['priorite_etude_interventions'])
        f['decision_interventions']=d
        f['action_ids_a_etudier_reference_v2']=deepcopy(f['action_ids_a_etudier'])
        f['action_ids_a_etudier']=[d['action_principale']['action_id']]if d['action_principale']else[]
        f['pistes_investigation_ids']=deepcopy(d['pistes_existantes_ids'])
        f['diagnostic_elus']['resume']=f['secteur']+' : '+d['diagnostic_territorial']
        f['diagnostic_elus']['principal_signal']=d['orientation']
        f['diagnostic_elus']['sens_couleur']=d['priorite_etude_interventions']['libelle']+'. '+NOTE
        p=props[mid];ref=f['triage_documentaire'];priority=d['priorite_etude_interventions']
        p['action_ids_pistes_historiques']=deepcopy(p['action_ids'])
        p.update(action_ids=deepcopy(f['action_ids_a_etudier']),triage_verification=ref['niveau'],triage_regle=ref['regle'],triage_couleur=ref['couleur_hex'],triage_motif=ref['motif'],
            triage_version=ref['application_version'],priorite_etude_niveau=priority['niveau'],priorite_etude_statut=priority['statut'],
            priorite_etude_couleur=priority['couleur_hex'],priorite_etude_libelle=priority['libelle'],priorite_etude_version=VERSION,
            action_principale_id=d['action_principale']['action_id']if d['action_principale']else None,actions_complementaires_ids=[],
            description_courte=f['diagnostic_elus']['resume'],intervention_travaux_validee=False)
        for j,a in enumerate(f['actions']):
            if a['piste_investigation']=='a_etudier':
                trace.append({'piste_id':piste_id(f,a),'maille_id':mid,'grid_version':f['grid_version'],'territory_id':f['territory_id'],
                    'action_id':a['action_id'],'regle_id':a['regle_id'],'statut_origine':a['piste_investigation'],'statut_scientifique':a['statut_regle_m2'],
                    'justification_origine':a['observations_justificatives'],'fiche_pointer':f'/fiches/{index}/actions/{j}',
                    'action_origine_sha256':digest_json(a),'source_origine_sha256':old['files_sha256']['demo_interne/fiches_zones.json'],
                    'statut_instruction':next(o['statut_instruction']for o in d['options_actions']if o['regle_id']==a['regle_id']),
                    'role':'principale_a_instruire'if d['action_principale']and d['action_principale']['action_id']==a['action_id']else'piste_ancienne_non_activee'})
        colors[priority['couleur']]+=1
        if d['action_principale']:main[d['action_principale']['action_id']]+=1
        rows.append({'maille_id':mid,'grid_version':f['grid_version'],'territory_id':f['territory_id'],'secteur':f['secteur'],
            'couleur':priority['couleur'],'niveau_etude':priority['niveau'],'statut_etude':priority['statut'],'regle_V1':priority['regle_source'],
            'action_principale':d['action_principale']['action_id']if d['action_principale']else None,
            'statut_action_principale':d['action_principale']['statut_instruction']if d['action_principale']else None,
            'diagnostic':d['diagnostic_territorial'],'orientation':d['orientation'],'absence_action_principale':d['motif_absence_action_principale'],
            'actions_complementaires':[],'pistes_existantes_ids':d['pistes_existantes_ids'],'D_S':'indeterminee','travaux_valides':False})
    assert len(doc['fiches'])==len(decisions)==101 and len(trace)==165
    doc.update(format_version='m2-m4.caen6.actions-etude-interne-1',classification_defaut='priorites_etude_interventions',version_priorisation_etudes=VERSION,mention_obligatoire=NOTE,
        intitule_carte=TITLE,triage_version='caen6-documentaire-20261111-1',publication_autorisee=False)
    geo.update(format_version='reconnect.vue-interne-actions-1',classification_defaut='priorites_etude_interventions',version_priorisation_etudes=VERSION,mention_obligatoire=NOTE)
    put(BUNDLE/'demo_interne/fiches_zones.json',doc);put(BUNDLE/'demo_interne/mailles.geojson',geo)
    put(BUNDLE/'demo_interne/priorites_etude_interventions.json',{'format_version':'m2-m4.instruction-actions-1','scope':doc['scope'],'version':VERSION,
        'intitule':TITLE,'note':NOTE,'publication_autorisee':False,'test_data':False,'mailles':decisions})
    put(BUNDLE/'demo_interne/pistes_investigation_trace.json',{'scope':doc['scope'],'version':VERSION,'pistes':trace,'nombre':len(trace),
        'limite':'Une piste ancienne n’est pas automatiquement une action sélectionnée ou une règle activée.'})
    with(BUNDLE/'rapports/decisions_101.csv').open('w',encoding='utf-8',newline='')as stream:
        w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader()
        for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False)if isinstance(v,(list,dict))else v for k,v in row.items()})
    put(BUNDLE/'provenance/politique_etude_interventions.json',{'version':VERSION,'origine':'Correction explicite utilisateur du 12 novembre 2026',
        'titre':TITLE,'note':NOTE,'legende':{c:{'niveau':LEVELS[c],'libelle':LABELS[c],'couleur_hex':PALETTE[c]}for c in LEVELS},
        'source_classement':'V1 originale conservée ; V3b historique non utilisée pour la vue principale',
        'selection':'Rouge : A04 à instruire en premier ; orange : A04 à évaluer selon les croisements ; jaune : orientation de préservation et aucune restauration sans préconditions propres ; gris : intervention non évaluable',
        'R2_R3_R4':'Aucune activation par la seule présence de haie, friche, plan d’eau ou végétation ; préconditions propres non documentées dans ce lot',
        'statuts_scientifiques':'Inchangés et distincts ; la sélection indicative d’une étude A04 ne requalifie pas R1',
        'DS':'Inchangée, indéterminée sur les 101 mailles','travaux_valides':0,'scientific_validation':False})
    summary={'version':VERSION,'scope':doc['scope'],'mailles':101,'couleurs':dict(colors),'actions_principales_a_instruire':dict(main),
        'unite_comptage_actions_principales':'selection_par_maille','nombre_projets_ou_ouvrages_distincts':None,
        'sans_action_principale':sum(d['action_principale']is None for d in decisions),'orientations_preservation':colors['jaune'],
        'decisions_non_evaluables':colors['gris'],'actions_complementaires_selectionnees':0,'pistes_tracees':len(trace),
        'pistes_par_famille':dict(Counter(p['regle_id']for p in trace)),'pistes_non_activees':sum(p['role']=='piste_ancienne_non_activee'for p in trace),
        'resultats_scientifiques_non_evaluables':len(scientific['resultats']),'priorites_ecologiques_indeterminees':101,
        'evenements_agreges':5336,'evenements_detectes':5337,'evenements_en_quarantaine':1,'recommandations_travaux_validees':0,
        'geometries_recalculees':False,'publication_autorisee':False}
    put(BUNDLE/'rapports/bilan_actions.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':build()
