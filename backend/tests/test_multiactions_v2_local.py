"""Local V2 remains separate from public routes, data and scientific results."""
from copy import deepcopy
import json
import os
from pathlib import Path
import threading
from http.server import ThreadingHTTPServer
from urllib.request import Request, urlopen
from urllib.error import HTTPError

import pytest

from server import M2Store, make_handler, TERRITORY_ID, GRID_VERSION
from multiactions_v2 import configure, MultiActionsV2Store, VERSION, DATASET, PAIRING


def test_development_switch_is_explicit_and_defaults_off():
    assert configure(None, {}) is None
    assert configure(None, {'RECONNECT_M2_V2_ROOT':'unused'}) is None
    for env in ({'RECONNECT_M2_MULTIACTIONS_V2':'true'},
                {'RECONNECT_M2_MULTIACTIONS_V2':'1','RECONNECT_ENV':'production'},
                {'RECONNECT_M2_MULTIACTIONS_V2':'1','RECONNECT_ENV':'development'},
                {'RECONNECT_M2_MULTIACTIONS_V2':'1','RECONNECT_ENV':'development','RECONNECT_M2_V2_ROOT':'unused','RECONNECT_FRONTEND_ORIGIN':'https://example.org'}):
        with pytest.raises(ValueError):configure(None,env)


@pytest.fixture(scope='module')
def stores():
    if not os.environ.get('RECONNECT_M2_V2_ROOT') or not os.environ.get('RECONNECT_M2_ZIP'):
        pytest.skip('Lot V2 et archive canoniques internes requis')
    canonical = M2Store(Path(os.environ['RECONNECT_M2_ZIP']))
    return canonical, MultiActionsV2Store(Path(os.environ['RECONNECT_M2_V2_ROOT']), canonical)


def test_full_projection_counts_science_and_no_raw_sources(stores):
    canonical, store = stores
    meta = store.metadata()
    assert [meta[k] for k in ('cells','proposals','cells_with_proposals','multi_action_cells','cells_without_proposals','A','B','C','c_only_cells')] == [101,205,88,61,13,93,45,67,25]
    total = leads = 0
    for mid,sheet in store.sheets.items():
        cell = store.cell(mid);total += len(cell['actions']);leads += cell['historical_lead_count']
        assert cell['DS'] == canonical.sheets[mid]['decision_interventions']['D_S']
        assert cell['main_action'] is None and not cell['validated_recommendations']
        assert {a['action_id'] for a in cell['actions']+cell['not_selected']} == set(PAIRING)
        for a in cell['actions']:
            assert a['scientific_status'] == 'non_evaluable' and a['scientific_decision_rule'] == 'A2'
            assert not a['works_validated'] and not a['works_need_demonstrated']
            assert a['observations'] and a['uncertainties'] and a['checks_before_works']
        payload = json.dumps(cell,ensure_ascii=False)
        for forbidden in ('objet_id','TRONROUT','HAIELINE','relation_audit_id','source_gpkg','/Users/','"geometry"','"preuves"'):
            assert forbidden not in payload
    assert (total,leads) == (205,165)
    grid = store.grid()
    assert len(grid['features']) == 101
    assert [f['geometry'] for f in grid['features']] == [f['geometry'] for f in canonical.minimal_grid()['features']]
    assert all('study_priority' not in f['properties'] for f in grid['features'])


def test_c_only_zero_multiple_and_linked_cases(stores):
    _,s=stores
    assert len(s.cell('NORM-G1K-FLAT-R+006423-C+000488')['actions']) == 3
    assert any(c['observations_liees'] for c in s.cell('NORM-G1K-FLAT-R+006423-C+000488')['comparisons'])
    assert not s.cell('NORM-G1K-FLAT-R+006421-C+000490')['actions']
    c=s.cell('NORM-G1K-FLAT-R+006421-C+000491')
    assert [(a['action_id'],a['level']) for a in c['actions']] == [('A03','C')]
    assert c['actions'][0]['presence_only']
    c=s.cell('NORM-G1K-FLAT-R+006427-C+000495')
    assert next(a for a in c['actions'] if a['action_id']=='A02')['source_context']['typo'] == ['Remblais']


@pytest.mark.parametrize('key', ['territory_id','grid_version','dataset_version','decision_version'])
def test_exact_scope_required(key):
    query={k:[v] for k,v in {'territory_id':TERRITORY_ID,'grid_version':GRID_VERSION,'dataset_version':DATASET,'decision_version':VERSION}.items()}
    MultiActionsV2Store.check_scope(query)
    query[key]=['wrong']
    with pytest.raises(ValueError):MultiActionsV2Store.check_scope(query)
    query.pop(key)
    with pytest.raises(ValueError):MultiActionsV2Store.check_scope(query)


def test_altered_or_missing_lot_rejected_without_fallback(stores,tmp_path):
    canonical,_=stores
    with pytest.raises(FileNotFoundError):MultiActionsV2Store(tmp_path,canonical)
    (tmp_path/'manifest.json').write_text('{"format_version":"wrong"}')
    with pytest.raises(ValueError,match='Empreinte'):MultiActionsV2Store(tmp_path,canonical)


@pytest.fixture(scope='module')
def servers(stores):
    old,new=stores
    servers=[ThreadingHTTPServer(('127.0.0.1',0),make_handler(old,'http://127.0.0.1:5184',v)) for v in (None,new)]
    for s in servers:threading.Thread(target=s.serve_forever,daemon=True).start()
    yield servers
    for s in servers:s.shutdown();s.server_close()


def request(server,route,headers=None):
    req=Request(f'http://127.0.0.1:{server.server_port}'+route,headers=headers or {})
    try:
        with urlopen(req) as r:return r.status,dict(r.headers),json.load(r)
    except HTTPError as r:return r.code,dict(r.headers),json.load(r)


def test_http_guards_and_old_routes_preserved(servers):
    old,new=servers
    from urllib.parse import urlencode
    scope=urlencode(dict(territory_id=TERRITORY_ID,grid_version=GRID_VERSION,dataset_version=DATASET,decision_version=VERSION))
    path='/api/internal/caen/multiactions-v2/metadata?'+scope
    assert request(old,path)[0] == 404
    status,headers,body=request(new,path,{'Origin':'http://127.0.0.1:5184'})
    assert status == 200 and body['proposals'] == 205 and headers['Cache-Control']=='no-store, private'
    assert headers['Access-Control-Allow-Origin']=='http://127.0.0.1:5184'
    for h in ({'Origin':'https://example.org'},{'Host':'example.org'},{'Forwarded':'for=8.8.8.8'},
              {'X-Forwarded-For':'8.8.8.8'},{'X-Forwarded-Host':'example.org'},{'X-Forwarded-Proto':'https'},{'Via':'proxy'}):
        assert request(new,path,h)[0] == 403
    assert request(new,'/api/internal/caen/multiactions-v2/grid')[0] == 409
    assert request(new,'/api/internal/caen/multiactions-v2/cells/absent?'+scope)[0] == 404
    assert request(new,'/api/internal/caen/multiactions-v2/provenance.json?'+scope)[0] == 404
    assert request(new,'/api/internal/caen/metadata')[2]['events_admitted'] == 5336
    # The original V1 decision is still available through its original endpoint.
    _,_,cell=request(new,'/api/internal/caen/cells/NORM-G1K-FLAT-R%2B006423-C%2B000488?'+scope)
    assert cell['instruction']['main_action']['action_id'] == 'A04'


def test_territorial_policy_is_exactly_the_sealed_policy_and_not_abc(stores):
    from collections import Counter
    from copy import deepcopy
    canonical, store = stores
    source_before = deepcopy(canonical.sheets)
    counts = Counter()
    for mid in store.sheets:
        p = store.territorial_priority(mid)
        original = canonical.sheets[mid]['decision_interventions']['priorite_etude_interventions']
        assert (p['color'],p['color_hex'],p['rank'],p['version']) == (original['couleur'],original['couleur_hex'],original['niveau'],original['version'])
        assert p['global_ecological_priority'] is False and p['works_urgency'] is None
        assert p['evidence'] == canonical.sheets[mid]['triage_documentaire_reference_v1']['observations_justificatives']
        counts[p['color']] += 1
    assert counts == {'rouge':27,'orange':33,'jaune':9,'gris':32}
    # The territorial policy is independent of the number and grades of V2 proposals.
    mid='NORM-G1K-FLAT-R+006424-C+000493'
    before=store.territorial_priority(mid)
    modified=deepcopy(store.sheets[mid]);original=store.sheets[mid]
    try:
        store.sheets[mid]=modified
        for p in modified['propositions']:
            p['selectionnee']=False;p['niveau_justification']='non_selectionnee'
        assert store.territorial_priority(mid) == before
    finally: store.sheets[mid]=original
    assert canonical.sheets == source_before


def test_geographic_labels_match_real_municipalities(stores):
    canonical,store=stores
    grid=store.grid()
    for index,f in enumerate(grid['features']):
        p=f['properties'];mid=p['maille_id']
        assert p['sector']['municipalities'] == [m['nom'] for m in canonical.sheets[mid]['communes']]
        assert p['sector']['number'] == index+1
        assert all(name in p['sector']['label'] for name in p['sector']['municipalities'])
        assert p['territorial_priority'] == store.cell(mid)['territorial_priority']
        assert p['study_color'] == p['territorial_priority']['color_hex']


def test_methodology_example_is_read_from_real_sources(stores,servers):
    from urllib.parse import urlencode
    canonical,store=stores
    method=store.methodology();example=method['example'];mid=example['maille_id'];sheet=canonical.sheets[mid]
    assert len(example['actions']) == 4
    assert example['area_m2'] == sheet['surface_m2']
    assert example['hedge_length_m'] == sheet['diagnostic_techniciens']['observations']['haies']['mesure_observee']
    assert example['priority']['color']=='orange'
    assert example['priority']['evidence']['nombre_paires_route_corridor_2d']==68
    assert example['priority']['evidence']['paires_route_matrice_fragile_en_service_au_sol']==38
    query=urlencode(dict(territory_id=TERRITORY_ID,grid_version=GRID_VERSION,dataset_version=DATASET,decision_version=VERSION))
    route='/api/internal/caen/multiactions-v2/methodology?'+query
    assert request(servers[0],route)[0] == 404
    assert request(servers[1],route)[2] == method
    assert request(servers[1],route,{'Origin':'https://example.org'})[0] == 403
