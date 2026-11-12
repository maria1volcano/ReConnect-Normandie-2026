"""Rejeu documentaire depuis le seul lot extrait ; aucun événement M2 recalculé."""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True


def replay(lot):
    lot=Path(lot).resolve()
    sys.path.insert(0,str(lot/'provenance/code'))
    import geopandas as gpd
    from analysis.triage_documentaire_v2 import classify
    grid=gpd.read_file(lot/'donnees/grille.gpkg',layer='mailles').set_index('maille_id')
    sources={'ocsge':gpd.read_file(lot/'donnees/ocsge_complement.gpkg',layer='ocsge')}
    sources.update({k:gpd.read_file(lot/'donnees/sources_consultables.gpkg',layer=k)for k in ['haies','plans_eau']})
    assert all(s.is_valid.all()and s.crs.to_epsg()==2154 for s in sources.values())
    fiches=json.loads((lot/'demo_interne/fiches_zones.json').read_text())['fiches']
    gray=set(json.loads((lot/'reference_v1/bilan.json').read_text())['mailles_grises_techniques'])
    out=[]
    for f in fiches:
        mid=f['maille_id'];cell=grid.loc[mid].geometry;evidence=[]
        for kind,source in sources.items():
            for pos in source.sindex.query(cell,predicate='intersects'):
                r=source.iloc[pos];clipped=r.geometry.intersection(cell)
                measure=clipped.length if kind=='haies'else clipped.area
                if measure<=0:continue
                e={'couche':kind,'objet_id':r.objet_id,'mesure':measure,'unite':'m'if kind=='haies'else'm2',
                    'dans_maille':True,'source_statut':'acquise_geometrie_valide'}
                if kind=='ocsge':e.update(code_cs=r.code_cs,code_us=r.code_us)
                evidence.append(e)
        result=classify(f['triage_documentaire_reference_v1'],evidence,mid in gray)
        assert (result['niveau'],result['regle'])==(f['triage_documentaire']['niveau'],f['triage_documentaire']['regle']),mid
        out.append({'maille_id':mid,'grid_version':f['grid_version'],'territory_id':f['territory_id'],'niveau':result['niveau'],'regle':result['regle']})
    return {'ok':True,'source':'Intersection recalculée des géométries fournies avec chaque maille, sans reprendre les témoins JSON comme preuve',
        'evenements_M2_recalcules':False,'regles_D_S_R1_R4_executees':False,'classes':dict(Counter(r['niveau']for r in out)),'mailles':out}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--lot',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.resolve().is_relative_to(args.lot.resolve()),'Écrire le résultat hors du lot scellé'
    result=replay(args.lot)
    with args.output.open('x',encoding='utf-8')as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'ok':True,'mailles':len(result['mailles']),'classes':result['classes']},ensure_ascii=False))
