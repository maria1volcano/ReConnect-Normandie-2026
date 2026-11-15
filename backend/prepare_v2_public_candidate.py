"""Prepare a minimized, UNAUTHORIZED V2 candidate in a non-served local directory.

This command cannot publish, approve, alter M2, or reuse the historical approval.
The candidate is a review artifact, not a new accepted public-data contract.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path

from server import M2Store
from multiactions_v2 import MultiActionsV2Store, VERSION, TERRITORIAL_VERSION

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_VERSION = 'reconnect.public-candidate.multiactions-1'
CELL_FIELDS = ('territory_id','grid_version','dataset_version','decision_version','mode','test_data',
               'publication_authorized','maille_id','municipalities','sector','territorial_priority',
               'actions','not_selected','comparisons','observations','local_event_count','canonical_event_count',
               'DS','main_action','validated_recommendations','manifest_sha256')


def validate_output(output: Path, root: Path = ROOT) -> Path:
    output = output.resolve()
    # Resolve existing symlinks before comparing. No location inside the frontend
    # or backend may ever be used, even when an authorization file is supplied.
    protected = [(root / name).resolve() for name in ('frontend','backend')]
    if any(output == p or p in output.parents for p in protected):
        raise ValueError('Candidature interne uniquement : destination applicative ou servie interdite')
    internal=(root/'data/derived').resolve()
    if internal not in output.parents:
        raise ValueError('La candidature doit rester sous data/derived, hors des répertoires servis')
    if output.exists():
        raise ValueError('Destination existante : refus d’écraser une candidature')
    return output


def prepare_candidate(store: MultiActionsV2Store, output: Path, *, root: Path = ROOT) -> dict:
    output = validate_output(output, root)
    cells = {}
    for feature in store.canonical.grid['features']:
        mid = feature['properties']['maille_id']
        source = store.cell(mid)
        cell = {key:deepcopy(source[key]) for key in CELL_FIELDS}
        # Object-level observations never belong in a public candidate.
        cell['observations'] = {key:{field:record.get(field) for field in
            ('nombre_objets_observes','mesure_observee','unite')} for key,record in source['observations'].items()}
        cells[mid] = cell
    selected = [a for cell in cells.values() for a in cell['actions']]
    counts = {'cells':len(cells),'actions':len(selected),
              'with_proposals':sum(bool(c['actions']) for c in cells.values()),
              'multi_action':sum(len(c['actions'])>1 for c in cells.values()),
              'without_proposals':sum(not c['actions'] for c in cells.values()),
              'levels':dict(Counter(a['level'] for a in selected)),
              'families':{aid:dict(Counter(a['level'] for a in selected if a['action_id']==aid))
                          for aid in ('A01','A02','A03','A04')}}
    expected={'cells':101,'actions':205,'with_proposals':88,'multi_action':61,'without_proposals':13,
              'levels':{'A':93,'B':45,'C':67},'families':{'A01':{'A':18,'B':27,'C':17},
                'A02':{'A':4,'B':15,'C':23},'A03':{'A':14,'C':21},'A04':{'A':57,'B':3,'C':6}}}
    if counts != expected:
        raise ValueError('Distribution incompatible : candidature non écrite')
    payloads = {'grid.geojson':store.grid(), 'cells.json':cells,
                'metadata.json':store.metadata(), 'methodology.json':store.methodology()}
    encoded = {name:json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
               for name,value in payloads.items()}
    for data in encoded.values():
        text=data.decode()
        if any(token in text for token in ('/Users/', 'TRONROUT', 'HAIELINE', '.gpkg', 'objet_id', 'preuve_id', 'source_reference')):
            raise ValueError('Champ source privé détecté : candidature non écrite')
    manifest = {'candidate_version':CANDIDATE_VERSION, 'publication_authorized':False,
                'approved_by':None, 'approved_at':None, 'status':'candidate_not_for_publication',
                'scope':deepcopy(store.scope), 'decision_version':VERSION,
                'territorial_version':TERRITORIAL_VERSION,
                'source_manifest_sha256':store.metadata()['manifest_sha256'],
                'source_archive_sha256':store.canonical.source_sha256,
                'counts':counts,
                'files_sha256':{name:hashlib.sha256(data).hexdigest() for name,data in encoded.items()},
                'limits':['Priorité indicative centrée sur les interfaces routières, sans urgence de travaux.',
                          'Les niveaux des solutions ne valident ni nécessité ni efficacité des travaux.',
                          'Les autorisations historiques ne couvrent pas cette candidature.',
                          'Une autorisation liée aux empreintes et un lecteur statique validé sont requis avant diffusion.']}
    output.mkdir(parents=True,exist_ok=False)
    for name,data in encoded.items():
        (output/name).write_bytes(data)
    (output/'candidate-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    return manifest


def main() -> None:
    parser=argparse.ArgumentParser(description='Préparer une candidature V2 minimisée ; aucune publication possible.')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        output=validate_output(args.output)
        canonical=M2Store(Path(os.environ['RECONNECT_M2_ZIP']))
        store=MultiActionsV2Store(Path(os.environ['RECONNECT_M2_V2_ROOT']),canonical)
        manifest=prepare_candidate(store,output)
    except (KeyError,ValueError) as error:
        raise SystemExit(str(error))
    print(json.dumps({'candidate_version':manifest['candidate_version'],'counts':manifest['counts'],
                      'publication_authorized':False},ensure_ascii=False))


if __name__=='__main__':
    main()
