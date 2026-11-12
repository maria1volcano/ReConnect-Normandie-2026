"""Rejouer les décisions indicatives depuis le lot, sans SIG et sans moteur D/S."""
from collections import defaultdict
import argparse
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True


def replay(lot):
    lot=Path(lot).resolve();sys.path.insert(0,str(lot/'provenance/code'))
    from analysis.prioriser_etudes_interventions import decide
    doc=json.loads((lot/'demo_interne/fiches_zones.json').read_text())
    expected={d['maille_id']:d for d in json.loads((lot/'demo_interne/priorites_etude_interventions.json').read_text())['mailles']}
    scientific=defaultdict(dict)
    for r in json.loads((lot/'demo_interne/actions_resultats.json').read_text())['resultats']:scientific[r['maille_id']][r['rule_id']]=r
    decisions=[decide(f,scientific[f['maille_id']])for f in doc['fiches']]
    assert all(d==expected[d['maille_id']]for d in decisions)
    return {'ok':True,'scope':doc['scope'],'decisions':decisions,'calcul_SIG_execute':False,'regles_scientifiques_executees':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--lot',type=Path,default=Path(__file__).resolve().parents[1]);parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args();assert not a.output.resolve().is_relative_to(a.lot.resolve()),'Écrire le résultat hors du lot scellé'
    result=replay(a.lot)
    with a.output.open('x',encoding='utf-8')as f:json.dump(result,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'ok':True,'decisions_confirmees':len(result['decisions']),'calcul_SIG_execute':False},ensure_ascii=False))
