"""Canonical final M2 import and minimised release gate (no geometric calculations)."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from server import ACTIONS_SHA256, ACTIONS_VERSION, GRID_VERSION, TERRITORY_ID, M2Store, ScopeError
from export_public_release import sanitize_cell


@pytest.fixture(scope='module')
def store():
    archive = os.environ.get('RECONNECT_M2_ZIP')
    if not archive:
        pytest.skip('RECONNECT_M2_ZIP requis pour les contrôles du vrai lot final')
    return M2Store(Path(archive))


def test_real_counts_and_scope(store):
    assert store.actions_release
    m = store.metadata()
    assert m['events_detected'] == 5337
    assert m['events_admitted'] == 5336
    assert m['events_quarantined'] == 1
    assert m['cell_event_relations'] == 5759
    assert m['cells_with_events'] == 60
    assert m['documentary_counts'] == dict(rouge=27, orange=33, jaune=9, gris=32)
    assert sum(m['documentary_leads'].values()) == 165
    assert m['test_data'] is False and m['publication_authorized'] is False
    assert m['decision_version'] == ACTIONS_VERSION


def test_all_canonical_decisions_and_trace(store):
    grid = store.minimal_grid()
    assert len(grid['features']) == 101
    assert [f['geometry'] for f in grid['features']] == [f['geometry'] for f in store.grid['features']]
    total_selected = total_leads = total_exclusive = 0
    for f in grid['features']:
        mid = f['properties']['maille_id']
        c = store.cell(mid, TERRITORY_ID, GRID_VERSION)
        original = store.sheets[mid]['decision_interventions']
        assert c['instruction']['diagnostic'] == original['diagnostic_territorial']
        assert c['instruction']['DS'] == original['D_S']
        assert c['study_priority'] == original['priorite_etude_interventions']
        assert c['ecological_priority']['category'] == 'INDETERMINATE'
        assert c['ecological_priority']['method_version'] is None
        assert len(c['instruction']['options']) == 4
        for action in c['instruction']['options']:
            assert action['statut_scientifique'] == 'non_evaluable'
            assert action['travaux_valides'] is False and action['activation_regle_scientifique'] is False
            assert action['justification'] and action['conditions_manquantes']
        main = c['instruction']['main_action']
        if c['study_priority']['couleur'] in {'rouge', 'orange'}:
            assert main['action_id'] == 'A04' and main['statut_instruction'] == 'a_instruire_indicatif'
            assert main['justification'] == original['action_principale']['justification']
            total_selected += 1
        else:
            assert main is None
        assert not c['instruction']['complementary_actions']
        assert c['validated_recommendations'] == []
        total_exclusive += c['geometric_observations']['canonical_event_count']
        total_leads += len(c['instruction']['historical_lead_ids'])
    assert (total_selected, total_leads, total_exclusive) == (60, 165, 5336)
    assert {x['piste_id'] for x in store.trace} == {id for sheet in store.sheets.values()
            for id in sheet['decision_interventions']['pistes_existantes_ids']}


def test_scope_and_missing_cell(store):
    mid = next(iter(store.sheets))
    for territory, grid in [('wrong', GRID_VERSION), (TERRITORY_ID, 'M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1')]:
        with pytest.raises(ScopeError): store.cell(mid, territory, grid)
    with pytest.raises(KeyError): store.cell('absente', TERRITORY_ID, GRID_VERSION)


def test_sanitisation_does_not_mutate_source(store):
    for mid in store.sheets:
        c = store.cell(mid, TERRITORY_ID, GRID_VERSION)
        before = copy.deepcopy(c)
        public = sanitize_cell(c)
        assert c == before
        for record in public['geometric_observations']['source_observations'].values():
            assert 'objets' not in record and 'source_reference' not in record
        text = json.dumps(public)
        for forbidden in ('TRONROUT', 'TVB-COR-', '.gpkg', '/Users/', 'conflit_ids', 'reservoir_ids'):
            assert forbidden not in text


def test_unrecognised_archive_fails_closed(tmp_path):
    p = tmp_path/'not-a-delivery.zip';p.write_bytes(b'not trusted')
    with pytest.raises(ValueError, match='Empreinte'): M2Store(p)


def test_public_export_requires_bound_approval(store, tmp_path):
    script = Path(__file__).resolve().parents[1]/'export_public_release.py'
    public = script.parents[1]/'frontend/public/data/caen-6com'
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in public.iterdir() if p.is_file()}
    run = subprocess.run([sys.executable, '-B', str(script)], text=True, capture_output=True)
    assert run.returncode != 0 and 'Publication bloquée' in run.stderr
    bad = tmp_path/'approval.json';bad.write_text(json.dumps({'publication_authorized': True, 'source_zip_sha256': 'other'}))
    out = tmp_path/'candidate'
    run = subprocess.run([sys.executable, '-B', str(script), '--authorization', str(bad), '--output', str(out)], text=True, capture_output=True)
    assert run.returncode != 0 and not out.exists()
    run = subprocess.run([sys.executable, '-B', str(script), '--output', str(out)], text=True, capture_output=True)
    assert run.returncode == 0, run.stderr
    manifest = json.loads((out/'release-manifest.json').read_text())
    assert manifest['publication_authorized'] is False
    assert manifest['source_zip_sha256'].lower() == ACTIONS_SHA256.lower()
    assert len(json.loads((out/'cells.json').read_text())) == 101
    assert before == {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in public.iterdir() if p.is_file()}
