"""Tests avec GeoPackage SQLite factice ; aucun résultat scientifique réel embarqué."""
import hashlib
import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app
from services.contract import ContractError
from services.internal_m2 import InternalM2Lot

TOKEN = "test-access-token-over-20-characters"
SCOPE = {"territory_id": "test_portee", "grid_version": "TEST-V1", "dataset_version": "TEST-LOT"}
COUNTS = {"mailles": 2, "enjeux": 2, "evenements": 2,
          "liens_mailles_evenements": 3, "quarantaine": 0}


def make_fake_gpkg(path: Path):
    with sqlite3.connect(path) as db:
        db.executescript('''
        CREATE TABLE mailles (maille_id TEXT, territory_id TEXT, grid_version TEXT,
          dataset_version TEXT, method_version TEXT, etat_analyse TEXT,
          nb_evenements_observes INTEGER, nb_evenements_exclusifs_observes INTEGER,
          nb_evenements INTEGER, priorite_etat TEXT, priorite_valeur TEXT, actions_etat TEXT,
          geometry BLOB);
        CREATE TABLE enjeux (maille_id TEXT, enj_01_pct REAL, enj_01_status TEXT,
          enj_02_presence REAL, enj_02_status TEXT);
        CREATE TABLE evenements (conflit_id TEXT, territory_id TEXT, grid_version TEXT,
          dataset_version TEXT, method_version TEXT, statut TEXT, geometry BLOB);
        CREATE TABLE liens_mailles_evenements (maille_id TEXT, conflit_id TEXT, canonical_owner INTEGER);
        CREATE TABLE quarantaine (conflit_id TEXT);
        ''')
        for mid, observed, exclusive in [('A', 2, 1), ('B', 1, 1)]:
            db.execute('INSERT INTO mailles VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',
                (mid, *SCOPE.values(), None, 'analyse_effectuee', observed, exclusive,
                 None, 'non_calculee', None, 'non_calculees', b'PRIVATE-GEOMETRY'))
        db.executemany('INSERT INTO enjeux VALUES(?,?,?,?,?)',
            [('A', None, 'unknown', 1.0, 'observed'),
             ('B', None, 'unknown', None, 'unknown')])
        for cid in ['C1', 'C2']:
            db.execute('INSERT INTO evenements VALUES (?,?,?,?,?,?,?)',
                 (cid, *SCOPE.values(), None, 'croisement_detecte', b'PRIVATE-COORDINATES'))
        db.executemany('INSERT INTO liens_mailles_evenements VALUES(?,?,?)',
                       [('A', 'C1', 1), ('A', 'C2', 0), ('B', 'C2', 1)])


def fake_client(tmp_path):
    path = tmp_path / 'fake.gpkg'
    make_fake_gpkg(path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    api = create_app(real_gpkg_path=path, internal_token=TOKEN,
                     real_expected_sha256=digest,
                     real_expected_counts=COUNTS, real_expected_scope=SCOPE)
    return TestClient(api, base_url='http://127.0.0.1', client=('127.0.0.1', 50000)), path, digest


def test_demo_and_state_are_not_confused(tmp_path):
    client, _, _ = fake_client(tmp_path)
    assert client.get('/health').json()['test_data'] is True
    status = client.get('/etat-integration').json()
    assert status['m2_caen_nord_66'] == 'charge_interne_uniquement'
    assert client.get('/zones').json()['test_data'] is True
    assert client.get('/internal/m2/health').status_code == 404
    assert client.get('/internal/m2/health', headers={'X-Internal-Token': 'wrong'}).status_code == 404
    assert client.get('/internal/m2/health', headers={'X-Internal-Token': TOKEN}).json()['counts']['relations_spatiales'] == 3


def test_internal_scope_and_no_sensitive_geometry(tmp_path):
    client, _, _ = fake_client(tmp_path)
    header = {'X-Internal-Token': TOKEN}
    a = client.get('/internal/m2/mailles/A', headers=header)
    assert a.status_code == 200
    body = a.json()
    assert body['conflit_ids'] == ['C1', 'C2']
    assert body['priorite_examen'] == {'etat': 'non_calculee', 'valeur': None}
    assert body['enjeux']['enj_01_pct'] is None
    assert body['enjeux']['enj_02_presence'] is True
    assert body['geometrie'] is None
    assert b'PRIVATE' not in a.content
    b = client.get('/internal/m2/mailles/B', headers=header).json()
    assert b['enjeux']['enj_02_presence'] is None
    assert client.get('/internal/m2/mailles/Z', headers=header).status_code == 404
    assert client.get('/internal/m2/mailles/A/conflits', headers=header).json()['total'] == 2
    event = client.get('/internal/m2/conflits/C2', headers=header)
    assert event.status_code == 200 and b'PRIVATE' not in event.content
    assert event.headers['cache-control'] == 'no-store, private'
    assert client.get('/internal/m2/mailles', params={'limit': -4}, headers=header).status_code == 422


def test_refuses_bad_hash_and_unapproved_scopes(tmp_path):
    client, path, digest = fake_client(tmp_path)
    with pytest.raises(ContractError):
        InternalM2Lot(path, expected_sha256='0' * 64, expected_counts=COUNTS,
                      expected_scope=SCOPE)
    with pytest.raises(ContractError):
        InternalM2Lot(path, expected_sha256=digest, expected_counts=COUNTS,
                      expected_scope={**SCOPE, 'grid_version': 'WRONG'})


def test_rejects_missing_owner(tmp_path):
    client, path, digest = fake_client(tmp_path)
    with sqlite3.connect(path) as db:
        db.execute("UPDATE liens_mailles_evenements SET canonical_owner=0 WHERE conflit_id='C2'")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ContractError):
        InternalM2Lot(path, expected_sha256=digest, expected_counts=COUNTS,
                      expected_scope=SCOPE)


def test_no_internal_paths_without_explicit_configuration():
    client = TestClient(create_app(), base_url='http://127.0.0.1')
    assert client.get('/internal/m2/health').status_code == 404
    assert client.get('/etat-integration').json()['m2_caen_nord_66'] == 'lot_non_fourni'
