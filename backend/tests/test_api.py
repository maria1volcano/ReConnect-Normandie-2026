from copy import deepcopy
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import app
from services.contract import ContractError, canonical_id, validate_m2_contract
from services.store import BASE_DIR, read_json

client = TestClient(app)


def test_health_and_metadata():
    h = client.get('/health')
    assert h.status_code == 200
    data = h.json()
    assert data['status'] == 'ok'
    assert data['contract_version'] == 'm2-m4.proposal-1'
    assert data['test_data'] is True
    assert data['mailles'] == 4
    assert data['evenements_distincts_observes'] == 4
    assert data['relations_spatiales'] == 5
    assert data['priorites_calculees'] is False
    assert client.get('/metadata').json()['resume_global']['evenements_distincts_observes'] == 4


def test_collection_geojson_and_pagination():
    first = client.get('/zones', params={'limit': 2})
    assert first.status_code == 200
    assert first.headers['x-total-count'] == '4'
    assert first.headers['x-resume-scope'] == 'dataset-global'
    assert first.json()['type'] == 'FeatureCollection'
    assert first.json()['test_data'] is True
    assert len(first.json()['features']) == 2
    second = client.get('/zones', params={'offset': 2, 'limit': 2})
    assert len(second.json()['features']) == 2
    assert first.json()['features'][0]['properties']['maille_id'] != second.json()['features'][0]['properties']['maille_id']
    assert client.get('/zone').status_code == 200
    assert client.get('/mailles').json()['features'] == client.get('/zones').json()['features']


def test_bbox_and_invalid_requests():
    response = client.get('/zones', params={'bbox': '0.25,49.16,0.28,49.19'})
    assert response.status_code == 200
    assert 0 < len(response.json()['features']) <= 4
    outside = client.get('/zones', params={'bbox': '-20,20,-19,21'})
    assert outside.json()['features'] == []
    for bbox in ('nan,0,1,1', '1,2,3', '1,5,0,6', '180,0,181,1'):
        assert client.get('/zones', params={'bbox': bbox}).status_code == 422
    assert client.get('/zones', params={'limit': -1}).status_code == 422
    assert client.get('/zones', params={'offset': -2}).status_code == 422


def test_zone_details_no_invented_science():
    data = client.get('/zones/H1').json()
    assert data['maille_id'] == 'H1'
    assert data['priorite_examen'] == {'etat': 'non_calculee', 'valeur': None}
    assert data['etat_actions'] == 'non_calculees'
    assert data['fiche_detaillee_disponible'] is False
    assert data['fiche'] is None
    assert data['dimensions'] is None
    assert client.get('/zones/unknown').status_code == 404


def test_conflicts_unique_and_reciprocal():
    all_events = client.get('/conflits').json()['features']
    assert len(all_events) == 4
    assert len({c['properties']['conflit_id'] for c in all_events}) == 4
    h1 = client.get('/conflits', params={'maille_id': 'H1'}).json()['features']
    h2 = client.get('/zones/H2/conflits').json()['features']
    assert len(h1) == 2
    assert len(h2) == 3
    assert len(set(f['properties']['conflit_id'] for f in h1).intersection(f['properties']['conflit_id'] for f in h2)) == 1
    for event in h1:
        assert 'H1' in event['properties']['maille_ids']
    assert client.get('/conflits', params={'maille_id': 'not-existent'}).status_code == 404
    assert client.get('/conflits/unknown').status_code == 404


def test_sensitive_geometry_stays_masked():
    results = client.get('/conflits').json()['features']
    for result in results:
        p = result['properties']
        if p['diffusion']['geometrie'] == 'masquee':
            assert result['geometry'] is None
            assert p['source_ids'] == []
            assert p['precision_affichage'] == 'localisation_masquee'
    assert any(item['geometry'] is None for item in results)


def test_sources_and_catalogue_pending():
    sources = client.get('/sources').json()
    assert sources['count'] > 0
    assert sources['sources'][0]['statut'] == 'candidat'
    actions = client.get('/actions').json()
    assert actions['status'] == 'en_attente_m5'
    assert actions['actions'] == []
    assert client.get('/actions/A01').status_code == 503


def test_cors_for_vite():
    r = client.get('/health', headers={'Origin': 'http://localhost:5173'})
    assert r.headers['access-control-allow-origin'] == 'http://localhost:5173'
    r = client.get('/health', headers={'Origin': 'https://non-autorise.example'})
    assert 'access-control-allow-origin' not in r.headers


def test_validator_rejects_broken_references():
    mailles = read_json(BASE_DIR / 'data/demo/mailles.geojson')
    conflits = read_json(BASE_DIR / 'data/demo/conflits.geojson')
    altered = deepcopy(mailles)
    altered['features'][0]['properties']['conflit_ids'].append('UNKNOWN')
    with pytest.raises(ContractError):
        validate_m2_contract(altered, conflits)


def test_ids_preserve_types():
    assert canonical_id(1) != canonical_id('1')
    assert canonical_id(0) != canonical_id('0')
    with pytest.raises(ContractError):
        canonical_id(True)


def test_no_public_real_data_by_default():
    # Les schémas proposés M2 imposent test_data = true.
    mailles = read_json(BASE_DIR / 'data/demo/mailles.geojson')
    conflits = read_json(BASE_DIR / 'data/demo/conflits.geojson')
    real = deepcopy(mailles)
    real['test_data'] = False
    with pytest.raises(ContractError):
        validate_m2_contract(real, conflits)


def test_optional_m5_catalogue_and_fiches(tmp_path):
    import json
    from main import create_app
    from services.store import BASE_DIR
    catalogue = tmp_path / 'actions.json'
    catalogue.write_text(json.dumps([{'action_id':'A-TEST', 'statut':'synthetique_non_evaluable'}]), encoding='utf-8')
    fiche = tmp_path / 'fiches.json'
    fiche.write_text(json.dumps([{'maille_id':'H1', 'dimensions': {'enjeu_ecologique': None},
                                 'conflit_ids': read_json(BASE_DIR / 'data/demo/mailles.geojson')['features'][0]['properties']['conflit_ids']}]),encoding='utf-8')
    api = create_app(actions_file=catalogue, fiches_file=fiche)
    test_client = TestClient(api)
    assert test_client.get('/actions').json()['count'] == 1
    assert test_client.get('/actions/A-TEST').status_code == 200
    detail = test_client.get('/zones/H1').json()
    assert detail['fiche_detaillee_disponible'] is True
    assert detail['dimensions'] == {'enjeu_ecologique': None}

def test_error_if_fiches_reference_wrong_conflicts(tmp_path):
    import json
    from main import create_app
    from services.contract import ContractError
    invalid = tmp_path / 'fiches.json'
    invalid.write_text(json.dumps([{'maille_id':'H1', 'conflit_ids':['INVENTE']}]), encoding='utf-8')
    with pytest.raises(ContractError):
        create_app(fiches_file=invalid)
