"""Contrôle autonome après extraction : bibliothèque standard, sans calcul SIG."""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import sqlite3
import sys


def load(path):return json.loads(Path(path).read_text())


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb')as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def verify(root):
    root=Path(root).resolve();manifest=load(root/'manifest.json')
    expected=manifest['files_sha256'];actual={p.relative_to(root).as_posix()for p in root.rglob('*')if p.is_file()}
    assert actual==set(expected)|{'manifest.json','SHA256SUMS'},'Inventaire du lot différent du manifeste'
    for name,h in expected.items():
        path=(root/name).resolve();assert path.is_relative_to(root)and sha(path)==h,name
    sums=dict((line.split('  ',1)[1],line.split('  ',1)[0])for line in(root/'SHA256SUMS').read_text().splitlines())
    assert set(sums)==set(expected)|{'manifest.json'}
    assert all(sha(root/n)==h for n,h in sums.items())
    assert manifest['publication_autorisee']is False and manifest['test_data']is False
    source=load(root/'reference_historique/manifest.json')
    protected=['demo_interne/actions_resultats.json','demo_interne/conflits.geojson','donnees/grille.gpkg','donnees/territoire.gpkg','donnees/liens_observations.json',
        'donnees/sources_consultables.gpkg','donnees/ocsge_complement.gpkg','rapports/evenements.gpkg','rapports/evenements_detectes.gpkg',
        'rapports/quarantaine.gpkg','rapports/mailles.gpkg','rapports/enjeux.gpkg','rapports/admis.validation.json','rapports/strict.validation.json']
    assert all(sha(root/p)==source['files_sha256'][p]for p in protected),'Artefact canonique modifié'
    doc=load(root/'demo_interne/fiches_zones.json');geo=load(root/'demo_interne/mailles.geojson')
    choices=load(root/'demo_interne/priorites_etude_interventions.json')
    records=load(root/'demo_interne/pistes_investigation_trace.json')['pistes']
    science=load(root/'demo_interne/actions_resultats.json')
    scope=manifest['scope'];fiches=doc['fiches'];features=geo['features'];decisions=choices['mailles']
    assert len(fiches)==len(features)==len(decisions)==101
    assert doc['classification_defaut']==geo['classification_defaut']=='priorites_etude_interventions'
    assert doc['scope']==choices['scope']==science['scope']==scope
    assert geo['scope']==scope
    assert all(f['territory_id']==scope['territory_id']and f['grid_version']==scope['grid_version']and f['dataset_version']==scope['dataset_version']for f in fiches)
    assert len({(f['territory_id'],f['grid_version'],f['maille_id'])for f in fiches})==101
    by_id={f['maille_id']:f for f in fiches};by_dec={d['maille_id']:d for d in decisions}
    before=load(root/'provenance/invariants_avant.json')
    assert sha(root/'reference_historique/manifest.json')==before['source_manifest_sha256']
    original_geometry={f['properties']['maille_id']:f['geometry']for f in load(root/'reference_v1/mailles.geojson')['features']}
    colors=Counter();primary=Counter();n_without=0
    levels={'rouge':1,'orange':2,'jaune':3,'gris':None};pairing={'R1':'A04','R2':'A01','R3':'A03','R4':'A02'}
    scientific={(r['maille_id'],r['rule_id']):r for r in science['resultats']}
    assert len(scientific)==404
    for feature in features:
        p=feature['properties'];f=by_id[p['maille_id']];d=by_dec[f['maille_id']];q=d['priorite_etude_interventions']
        assert p['grid_version']==d['grid_version']==f['grid_version']and p['territory_id']==d['territory_id']==f['territory_id']
        assert d==f['decision_interventions']and q==f['priorite_etude_interventions']
        assert f['triage_documentaire']==f['triage_documentaire_reference_v1']
        assert q['couleur']==f['triage_documentaire']['niveau']==p['triage_verification']
        assert q['niveau']==p['priorite_etude_niveau']==levels[q['couleur']]
        assert q['couleur_hex']==p['priorite_etude_couleur']and q['validation_ecologique']is False
        assert feature['geometry']==original_geometry[f['maille_id']]
        assert all(f[k]==v for k,v in before['mailles'][f['maille_id']]['DS'].items())
        assert all(d['D_S'][k]==f[k]for k in ['priorite_ecologique','priorite_examen','method_version','couverture_synthese','regle_appliquee'])
        assert digest(f['actions'])==before['mailles'][f['maille_id']]['actions_sha256']
        assert digest(f['diagnostic_techniciens'])==before['mailles'][f['maille_id']]['diagnostic_techniciens_sha256']
        assert p['priority_category']=='INDETERMINATE'and p['priority_method_version']is None
        assert {a['regle_id']:a['action_id']for a in d['options_actions']}==pairing
        assert not d['actions_complementaires']and not d['recommandations_travaux_validees']
        selected=['A04']if q['couleur']in{'rouge','orange'}else[]
        assert f['action_ids_a_etudier']==p['action_ids']==selected
        assert f['action_ids_a_etudier_reference_v2']==p['action_ids_pistes_historiques']==[a['action_id']for a in f['actions']if a['piste_investigation']=='a_etudier']
        assert d['conditions_validation_avant_travaux']and d['diagnostic_territorial']and d['orientation']
        for a in d['options_actions']:
            assert a['justification']and a['observations']and a['conditions_manquantes']
            assert a['statut_scientifique']==scientific[(f['maille_id'],a['regle_id'])]['statut']=='non_evaluable'
            assert not a['activation_regle_scientifique']and not a['travaux_valides']and not a['restauration_selectionnee']
            if a['regle_id']!='R1':assert a['statut_instruction']!='a_instruire_indicatif'
        if q['couleur']in{'rouge','orange'}:
            a=d['action_principale'];assert a and a['action_id']=='A04'and a['statut_instruction']=='a_instruire_indicatif'
            assert set(a['justificatifs']['conflit_ids'])<=set(f['diagnostic_techniciens']['conflit_ids'])
            assert a['justificatifs']['conflit_ids']and not a['travaux_valides'];primary[a['action_id']]+=1
        else:
            assert d['action_principale']is None and d['motif_absence_action_principale'];n_without+=1
            assert not p['action_principale_id']
            assert all(a['statut_instruction']!='a_instruire_indicatif'for a in d['options_actions'])
        if q['couleur']=='gris':assert q['statut']=='non_evaluable'
        colors[q['couleur']]+=1
    assert colors=={'rouge':27,'orange':33,'jaune':9,'gris':32}and primary=={'A04':60}and n_without==41
    assert len(records)==len({p['piste_id']for p in records})==165
    original_pistes={(f['maille_id'],a['regle_id']):a for f in fiches for a in f['actions']if a['piste_investigation']=='a_etudier'}
    assert len(original_pistes)==165
    assert {(p['maille_id'],p['regle_id'])for p in records}==set(original_pistes)
    for p in records:
        a=original_pistes[(p['maille_id'],p['regle_id'])]
        assert digest(a)==p['action_origine_sha256']and p['statut_origine']=='a_etudier'
        assert p['piste_id']in by_dec[p['maille_id']]['pistes_existantes_ids']
        assert p['grid_version']==scope['grid_version']and p['territory_id']==scope['territory_id']
        pointer=p['fiche_pointer'].split('/')
        pointed_fiche=fiches[int(pointer[2])];pointed_action=pointed_fiche['actions'][int(pointer[4])]
        assert pointed_fiche['maille_id']==p['maille_id']and digest(pointed_action)==p['action_origine_sha256']
    with sqlite3.connect((root/'rapports/mailles.gpkg').as_uri()+'?mode=ro',uri=True)as db:
        links=db.execute('SELECT conflit_id,maille_id,canonical_owner FROM liens_mailles_conflits').fetchall()
    events=load(root/'demo_interne/conflits.geojson')['features'];ids={f['properties']['conflit_id']for f in events}
    assert len(events)==len(ids)==5336 and len(links)==5759 and sum(o for c,m,o in links)==5336
    assert all(c in ids and m in by_id for c,m,o in links)
    quarantine=load(root/'rapports/quarantaine.validation.json')['events'];assert len(quarantine)==1 and ids.isdisjoint(q['conflit_id']for q in quarantine)
    return {'ok':True,'fichiers_verifies':len(sums),'mailles':101,'couleurs':dict(colors),'actions_principales':dict(primary),
        'orientations_preservation':9,'decisions_non_evaluables':32,'sans_action_principale':41,'pistes_tracees':165,
        'priorites_DS_inchangees':101,'resultats_R1_R4_inchanges':404,'evenements_agreges_inchanges':5336,'quarantaine_inchangee':1,
        'geometries_inchangees':True,'travaux_valides':0,'publication_autorisee':False}


if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1])if len(sys.argv)>1 else Path(__file__).resolve().parent),ensure_ascii=False,indent=2))
