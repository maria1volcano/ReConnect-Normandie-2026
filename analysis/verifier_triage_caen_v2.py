"""Vérificateur autonome supplémentaire du ZIP V2 ; bibliothèque standard."""
from __future__ import annotations
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True


def verify(root):
    root=Path(root).resolve()
    spec=importlib.util.spec_from_file_location('verifier_lot_v1',root/'verifier_lot.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    result=mod.verify(root)
    read=lambda p:json.loads(p.read_text())
    original=read(root/'reference_v1/manifest.json')
    previous={f['properties']['maille_id']:f for f in read(root/'reference_v1/mailles.geojson')['features']}
    proposed=read(root/'demo_interne/mailles.geojson')['features']
    comparisons=read(root/'rapports/comparaison_101.json')['mailles']
    fiches=read(root/'demo_interne/fiches_zones.json')['fiches']
    assert len(previous)==len(proposed)==len(comparisons)==len(fiches)==101
    assert len({(r['territory_id'],r['grid_version'],r['maille_id'])for r in comparisons})==101
    assert {r['maille_id']for r in comparisons}==set(previous)
    count=0
    for f in proposed:
        p=f['properties'];old=previous[p['maille_id']]
        assert f['geometry']==old['geometry']
        if p['triage_verification']!=old['properties']['triage_verification']:
            assert old['properties']['triage_verification']=='gris'and p['triage_verification']=='jaune'and p['triage_regle']=='V3b';count+=1
    for f in fiches:
        t=f['triage_documentaire']
        if t['regle']=='V3b':
            assert f['triage_documentaire_reference_v1']['niveau']=='gris'and t['justificatifs_supplementaires']
            for e in t['justificatifs_supplementaires']:
                assert e['dans_maille']and e['mesure']>0 and e['couche']in{'haies','plans_eau','ocsge'}
        assert not f['recommandations_validees'] and f['priorite_ecologique']['conclusion']=='indeterminee'
    protected=['demo_interne/conflits.geojson','demo_interne/actions_resultats.json','donnees/grille.gpkg','donnees/territoire.gpkg','rapports/evenements.gpkg','rapports/quarantaine.gpkg','rapports/mailles.gpkg']
    assert all(hashlib.sha256((root/p).read_bytes()).hexdigest()==original['files_sha256'][p]for p in protected)
    assert len(read(root/'rapports/audit_grises_32.json')['mailles'])==32
    result.update(version_triage='caen6-triage-documentaire-2.0-20261112',classes=dict(Counter(f['properties']['triage_verification']for f in proposed)),
        changements_gris_jaune=count,evenements_et_actions_inchanges=True,classification_D_S_independante=True)
    return result


if __name__=='__main__':
    print(json.dumps(verify(Path(sys.argv[1])if len(sys.argv)>1 else Path(__file__).resolve().parent),ensure_ascii=False,indent=2))
