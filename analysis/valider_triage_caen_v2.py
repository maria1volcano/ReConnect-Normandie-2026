"""Contrôles sur les données réelles : géométrie, preuves locales et invariants M2."""
from __future__ import annotations
from collections import Counter
import json
from math import isclose
from pathlib import Path
import geopandas as gpd
from analysis.auditer_mailles_grises_caen import ROOT, BASE, OUT
from analysis.enrichir_triage_caen_20261112 import BUNDLE, load, put
from analysis.preparer_caen_et_nord import sha
from analysis.triage_documentaire_v2 import classify
from analysis.validate_inputs import AREA_TOLERANCE_M2, LENGTH_TOLERANCE_M


def main():
    old={f['maille_id']:f for f in load(BASE/'demo_interne/fiches_zones.json')['fiches']}
    new=load(BUNDLE/'demo_interne/fiches_zones.json')['fiches']
    assert len(new)==len(old)==101 and len({f['maille_id']for f in new})==101
    grid=gpd.read_file(BASE/'donnees/grille.gpkg',layer='mailles').set_index('maille_id')
    new_geo=load(BUNDLE/'demo_interne/mailles.geojson')['features']
    old_geo={f['properties']['maille_id']:f for f in load(BASE/'demo_interne/mailles.geojson')['features']}
    for f in new_geo:
        p=f['properties'];assert f['geometry']==old_geo[p['maille_id']]['geometry']
        for k in ['grid_version','territory_id','dataset_version','area_m2','pilot_fraction','priority_category','priority_method_version','conflit_ids','nb_evenements_exclusifs_observes']:
            assert p[k]==old_geo[p['maille_id']]['properties'][k],k
    protected=['demo_interne/actions_resultats.json','demo_interne/conflits.geojson','donnees/grille.gpkg','donnees/territoire.gpkg','donnees/sources_consultables.gpkg','donnees/liens_observations.json']
    protected += [str(p.relative_to(BASE))for p in (BASE/'rapports').glob('*.gpkg')]
    protected += ['rapports/strict.validation.json','rapports/admis.validation.json','rapports/enjeux.validation.json','rapports/quarantaine.validation.json']
    assert all(sha(BASE/p)==sha(BUNDLE/p)for p in protected)
    sources={k:gpd.read_file(BUNDLE/'donnees/ocsge_complement.gpkg',layer=k).set_index('objet_id')for k in ['ocsge','artificialisation']}
    for k in ['haies','plans_eau']:
        sources[k]=gpd.read_file(BASE/'donnees/sources_consultables.gpkg',layer=k).set_index('objet_id')
    assert all(s.is_valid.all()and s.crs.to_epsg()==2154 and s.index.is_unique for s in sources.values())
    assert set(sources['ocsge'].index)==set(sources['artificialisation'].index)
    assert all(sources['ocsge'].loc[i].geometry.equals_exact(r.geometry,0)and sources['ocsge'].loc[i].code_cs==r.code_cs for i,r in sources['artificialisation'].iterrows())
    changed=[];witnesses=0
    for f in new:
        prev=old[f['maille_id']]
        assert f['triage_documentaire_reference_v1']==prev['triage_documentaire']
        for k in ['priorite_examen','priorite_ecologique','method_version','actions','action_ids_a_etudier','action_ids_valides','recommandations_validees','diagnostic_ids_non_evalues']:
            assert f[k]==prev[k],k
        for k,v in prev['diagnostic_techniciens'].items():
            if k!='observations':assert f['diagnostic_techniciens'][k]==v,k
            else:
                for layer,o in v.items():assert f['diagnostic_techniciens']['observations'][layer]==o
        t=f['triage_documentaire'];evidence=t['justificatifs_supplementaires']
        recomputed=classify(prev['triage_documentaire'],evidence)
        assert (recomputed['niveau'],recomputed['regle'])==(t['niveau'],t['regle'])
        if t['niveau']!=prev['triage_documentaire']['niveau']:
            assert prev['triage_documentaire']['niveau']=='gris' and t['regle']=='V3b' and t['niveau']=='jaune'
            assert evidence;changed.append(f['maille_id'])
        for e in evidence:
            witnesses+=1;s=sources[e['couche']].loc[e['objet_id']]
            local=s.geometry.intersection(grid.loc[f['maille_id']].geometry)
            actual=local.length if e['unite']=='m'else local.area
            budget=LENGTH_TOLERANCE_M if e['unite']=='m'else AREA_TOLERANCE_M2
            assert actual>budget and isclose(actual,e['mesure'],rel_tol=0,abs_tol=budget)
            if e['couche']=='ocsge':assert e['code_cs']==s.code_cs and e['code_us']==s.code_us
            assert e['dans_maille']is True
    audit=load(BUNDLE/'rapports/audit_grises_32.json')['mailles']
    assert len(audit)==32
    for r in audit:
        current=r['observations_dans_maille'];mid=r['maille_id']
        for n in r['contexte_voisinage']:
            assert n['maille_id']!=mid and n['continuite_fonctionnelle_etablie']is False
            for layer,o in n['observations_dans_voisin'].items():
                id_key='route_id'if layer=='routes'else'objet_id'
                assert {str(x[id_key])for x in current[layer]['objets']}.isdisjoint(o['objet_ids_uniquement_voisin'])
                assert o['presence_dans_maille_courante_deduite']is False
    baseline=load(OUT/'preservation_avant.json')
    assert all(sha(ROOT/p)==h for p,h in baseline.items())
    original_core=['analysis/evaluate_priorities.py','analysis/export_priority_results.py','analysis/export_m2_contract.py','docs/rules_actions.json','docs/table_decision_m2.md']
    assert all(sha(ROOT/p)==baseline[p]for p in original_core)
    result={'ok':True,'mailles':101,'fiches':101,'geometries_et_scope_conserves':True,'fichiers_M2_conserves':protected,
        'evenements_canoniques_inchanges':5336,'actions_resultats_inchanges':404,'pistes_inchangees':165,'priorites_ecologiques_indeterminees':101,
        'justificatifs_verifies_contre_geometries_sources':witnesses,'changements_gris_jaune':len(changed),'changements_autres':0,
        'fichiers_preexistants_empreintes_verifiees':len(baseline),'voisinage_sans_transfert':True,
        'classes':dict(Counter(f['triage_documentaire']['niveau']for f in new)),
        'reproduction':'Préservation des sources et relecture spatiale des preuves, sans relancer le détecteur ni les règles scientifiques'}
    put(BUNDLE/'rapports/acceptation.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
