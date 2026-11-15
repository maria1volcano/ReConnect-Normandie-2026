"""A candidate is deliberately not a publication authorization or served release."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from prepare_v2_public_candidate import prepare_candidate, validate_output
from test_multiactions_v2_local import stores


def test_only_new_internal_output_is_allowed(tmp_path):
    for suffix in ('frontend/public/candidate','frontend/dist/candidate','backend/data/candidate','other/candidate'):
        with pytest.raises(ValueError):validate_output(tmp_path/suffix,tmp_path)
    output=tmp_path/'data/derived/candidate'
    assert validate_output(output,tmp_path)==output
    output.mkdir(parents=True)
    with pytest.raises(ValueError,match='existante'):validate_output(output,tmp_path)


def test_symlink_into_public_is_refused(tmp_path):
    public=tmp_path/'frontend/public';public.mkdir(parents=True)
    internal=tmp_path/'data/derived';internal.mkdir(parents=True)
    (internal/'alias').symlink_to(public,target_is_directory=True)
    with pytest.raises(ValueError):validate_output(internal/'alias/candidate',tmp_path)


def test_candidate_preserves_all_actions_but_never_grants_publication(stores,tmp_path):
    canonical,store=stores
    original=deepcopy(store.sheets)
    output=tmp_path/'data/derived/candidate'
    manifest=prepare_candidate(store,output,root=tmp_path)
    assert manifest['publication_authorized'] is False
    assert manifest['approved_by'] is None and manifest['approved_at'] is None
    assert manifest['source_archive_sha256']==canonical.source_sha256
    assert manifest['counts']['actions']==205 and manifest['counts']['cells']==101
    assert manifest['counts']['families']=={'A01':{'A':18,'B':27,'C':17},'A02':{'A':4,'B':15,'C':23},'A03':{'A':14,'C':21},'A04':{'A':57,'B':3,'C':6}}
    for name,h in manifest['files_sha256'].items():
        assert hashlib.sha256((output/name).read_bytes()).hexdigest()==h
    cells=json.loads((output/'cells.json').read_text())
    for mid,c in cells.items():
        source=store.cell(mid)
        assert c['actions']==source['actions']
        assert c['DS']==source['DS'] and c['territorial_priority']==source['territorial_priority']
        assert c['main_action'] is None and c['publication_authorized'] is False
        assert c['validated_recommendations']==[]
        for observation in c['observations'].values():
            assert set(observation)=={'nombre_objets_observes','mesure_observee','unite'}
    assert store.sheets==original
    assert 'historical' not in next(iter(cells.values()))
    with pytest.raises(ValueError):prepare_candidate(store,output,root=tmp_path)
