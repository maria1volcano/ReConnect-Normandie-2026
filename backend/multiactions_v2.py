"""Read-only, loopback development adapter for a pinned experimental M2 V2 lot.

No export, geometry calculation, official action evaluation or public fallback.
Only the clipped grid and a small per-cell presentation projection are served.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import zipfile
from urllib.parse import urlparse

VERSION = 'm2.multiactions.experimental-2.0'
DATASET = 'M1-CAEN-ET-NORD-20261111-V1'
GRID = 'M1-CAEN-6COM-1KM2-FLAT-L93-O0-V1'
TERRITORY = 'caen_et_nord_6communes'
MANIFEST_SHA256 = '95378d1f13bc94418b813b682f3c7a75572126374cb2e825b9e72da0ea8e6057'
TERRITORIAL_VERSION = 'caen6-priorites-etude-actions-20261112-1'
PRESENTATION_VERSION = 'caen6-examen-multiactions-presentation-20261115-1'
PRIORITY_PALETTE = {'rouge': '#D64545', 'orange': '#EF9229', 'jaune': '#E8C84A', 'gris': '#9098A4'}
PAIRING = {'A01': 'R2', 'A02': 'R4', 'A03': 'R3', 'A04': 'R1'}
LEVELS = ('etude_ciblee_justifiee', 'piste_plausible', 'piste_exploratoire')
NAMES = {'A01': 'Préserver les haies et étudier leur renforcement', 'A02': 'Préserver et étudier les milieux humides',
         'A03': 'Étudier le devenir écologique des friches', 'A04': 'Étudier les passages et la perméabilité pour la faune'}
RELATIONS = {'route_corridor': 'Croisement cartographique route–corridor', 'haie_route_contact': 'Contact XY haie–route',
             'haie_route_srce_contact': 'Contact XY haie–route situé dans SRCE', 'haie_srce': 'Haie recoupant SRCE',
             'friche_srce': 'Site Cartofriches recouvrant SRCE', 'eau_srce': 'Plan d’eau recouvrant SRCE',
             'eau_zone_humide': 'Plan d’eau recouvrant un inventaire humide',
             'zone_humide_reservoir_humide': 'Inventaire humide recouvrant un réservoir humide',
             'presence_cartographique': 'Présence dans la maille ; aucune connexion fonctionnelle établie'}
LAYERS = {'routes': 'Tronçons routiers', 'corridors': 'Matrices et corridors SRCE', 'reservoirs': 'Réservoirs SRCE',
          'haies': 'Haies', 'friches': 'Sites Cartofriches', 'plans_eau': 'Plans d’eau', 'zones_humides': 'Milieux humides inventoriés'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def configure(canonical, env):
    flag = env.get('RECONNECT_M2_MULTIACTIONS_V2', '0')
    require(flag in {'0', '1'}, 'Commutateur V2 invalide')
    if flag == '0':
        return None
    require(env.get('RECONNECT_ENV') == 'development', 'V2 réservée au développement local explicite')
    require(bool(env.get('RECONNECT_M2_V2_ROOT')), 'Dossier interne V2 requis')
    origin = urlparse(env.get('RECONNECT_FRONTEND_ORIGIN', 'http://127.0.0.1:5173'))
    require(origin.scheme == 'http' and origin.hostname in {'127.0.0.1', 'localhost'}, 'Origine frontend V2 locale requise')
    return MultiActionsV2Store(Path(env['RECONNECT_M2_V2_ROOT']), canonical)


class MultiActionsV2Store:
    def __init__(self, root, canonical):
        from jsonschema import Draft202012Validator
        self.root, self.canonical = Path(root).resolve(), canonical
        require(canonical.actions_release, 'Le lot canonique ACTIONS_ETUDE est requis pour la jointure V2')
        require(sha(self.root / 'manifest.json') == MANIFEST_SHA256, 'Empreinte du lot expérimental V2 incompatible')
        self.manifest = json.loads((self.root / 'manifest.json').read_text())
        for name, h in self.manifest['fichiers_sha256'].items():
            require(name == Path(name).name and sha(self.root / name) == h, 'Fichier V2 altéré')
        doc = json.loads((self.root / 'fiches_multiactions_v2.json').read_text())
        require(doc['format_version'] == VERSION and doc['publication_autorisee'] is False and doc['test_data'] is False, 'Enveloppe V2 incompatible')
        require(doc['scope'] == canonical.manifest['scope'], 'Portée/version de données V2 incompatible')
        self.scope = doc['scope']
        validator = Draft202012Validator(json.loads((self.root / 'schema.json').read_text()))
        self.sheets = {}
        with zipfile.ZipFile(canonical.zip_path) as archive:
            science = canonical._read(archive, 'demo_interne/actions_resultats.json')['resultats']
        science = {(r['maille_id'], r['action_id']): r for r in science}
        for sheet in doc['fiches']:
            validator.validate(sheet)
            mid = sheet['maille_id']
            require(mid not in self.sheets and mid in canonical.sheets, 'Maille V2 dupliquée/orpheline')
            original = canonical.sheets[mid]
            require(sheet['scope'] == self.scope and sheet['D_S'] == original['decision_interventions']['D_S'], 'Jointure/D-S V2 incohérents')
            require(sheet['source_D_S_sha256'] == digest(sheet['D_S']), 'Empreinte D/S incohérente')
            require(sheet['reference_documentaire_historique'] == original['triage_documentaire_reference_v1'], 'Classification historique modifiée')
            expected_trace = [p for p in canonical.trace if p['maille_id'] == mid]
            require(sheet['pistes_historiques'] == expected_trace, 'Pistes historiques modifiées')
            proofs = {p['preuve_id']: p for p in sheet['preuves']}
            require(len(proofs) == len(sheet['preuves']), 'Preuve V2 dupliquée')
            for proof in proofs.values():
                for obj in proof['objets']:
                    require(obj['fichier_sha256'] == canonical.manifest['files_sha256'][obj['fichier']], 'Provenance objet incompatible')
                if proof['type'] == 'presence_cartographique':
                    a = proof['ancrage_canonique']; layer = a['couche']
                    require(a['maille_id'] == mid and a['sha256'] == canonical.manifest['files_sha256'][a['fichier']], 'Ancrage de présence incompatible')
                    objects = original['diagnostic_techniciens']['observations'][layer]['objets']
                    field = 'route_id' if layer == 'routes' else 'objet_id'
                    require(any(str(o.get(field)) == a['objet_id'] and o == proof['attributs'] for o in objects), 'Présence non résolue dans la fiche canonique')
            props = {p['action_id']: p for p in sheet['propositions']}
            require(len(props) == len(sheet['propositions']) and set(props) == set(PAIRING), 'Familles V2 incompatibles')
            for aid, p in props.items():
                require(p['rule_id'] == PAIRING[aid] and p['resultat_scientifique'] == science[mid, aid], 'Résultat scientifique modifié')
                require(p['resultat_scientifique_sha256'] == digest(p['resultat_scientifique']), 'Empreinte scientifique incohérente')
                require(p['travaux_valides'] is False and p['besoin_travaux_demontre'] is False, 'Travaux artificiellement validés')
                require(set(p['observations_motivantes']) <= proofs.keys(), 'Preuves V2 non résolues')
                require(p['selectionnee'] == (p['niveau_justification'] in LEVELS), 'Sélection/niveau incohérents')
                if p['niveau_justification'] in LEVELS[:2]:
                    require(any(proofs[r]['type'] != 'presence_cartographique' and proofs[r]['fait_local_positif'] for r in p['observations_motivantes']), 'Promotion depuis une présence seule')
            require(set(sheet['pistes_selectionnees']) == {a for a,p in props.items() if p['selectionnee']}, 'Liste de pistes incohérente')
            self.sheets[mid] = sheet
        require(len(self.sheets) == 101 and set(self.sheets) == set(canonical.sheets), '101 jointures V2 requises')
        self.counts = self._counts()
        require(self.counts == {'cells':101, 'proposals':205, 'cells_with_proposals':88, 'multi_action_cells':61,
                               'cells_without_proposals':13, 'A':93, 'B':45, 'C':67, 'c_only_cells':25,
                               'linked_observation_cells':11}, 'Comptages V2 incompatibles')
        self.sector_numbers = {f['properties']['maille_id']: i + 1 for i, f in enumerate(canonical.grid['features'])}
        # Read the already sealed M2 policy; no score or new ecological ranking.
        for mid in self.sheets:
            self.territorial_priority(mid)
        require(dict(Counter(self.territorial_priority(mid)['color'] for mid in self.sheets))
                == {'rouge': 27, 'orange': 33, 'jaune': 9, 'gris': 32}, 'Priorités d’examen incompatibles')

    def territorial_priority(self, mid):
        old = self.canonical.sheets[mid]
        p = old['decision_interventions']['priorite_etude_interventions']
        color = p['couleur']
        require(p['version'] == TERRITORIAL_VERSION and color in PRIORITY_PALETTE
                and p['couleur_hex'] == PRIORITY_PALETTE[color]
                and p['validation_ecologique'] is False and p['urgence_travaux'] is None
                and p['niveau'] == {'rouge': 1, 'orange': 2, 'jaune': 3, 'gris': None}[color],
                'Classement territorial source incompatible')
        return {'version': TERRITORIAL_VERSION, 'presentation_version': PRESENTATION_VERSION,
                'color': color, 'color_hex': p['couleur_hex'], 'rank': p['niveau'],
                'status': p['statut'], 'scope': 'interfaces_routieres_et_continuites',
                'global_ecological_priority': False, 'works_urgency': None,
                'evidence': deepcopy(old['triage_documentaire_reference_v1']['observations_justificatives'])}

    def sector(self, mid):
        municipalities = [m['nom'] for m in self.canonical.sheets[mid]['communes']]
        number = self.sector_numbers[mid]
        return {'number': number, 'municipalities': municipalities,
                'label': f'{" / ".join(municipalities)} — secteur {number}'}

    def _counts(self):
        selected = [p for s in self.sheets.values() for p in s['propositions'] if p['selectionnee']]
        counts = Counter(p['niveau_justification'] for p in selected)
        return {'cells':len(self.sheets), 'proposals':len(selected),
                'cells_with_proposals':sum(bool(s['pistes_selectionnees']) for s in self.sheets.values()),
                'multi_action_cells':sum(len(s['pistes_selectionnees'])>1 for s in self.sheets.values()),
                'cells_without_proposals':sum(not s['pistes_selectionnees'] for s in self.sheets.values()),
                **{letter:counts[lv] for letter,lv in zip('ABC',LEVELS)},
                'c_only_cells':sum(bool(s['pistes_selectionnees']) and all(p['niveau_justification']==LEVELS[2] for p in s['propositions'] if p['selectionnee']) for s in self.sheets.values()),
                'linked_observation_cells':sum(any(c['observations_liees'] for c in s['comparaisons']) for s in self.sheets.values())}

    @staticmethod
    def check_scope(query):
        for key, value in {'territory_id':TERRITORY, 'grid_version':GRID, 'dataset_version':DATASET, 'decision_version':VERSION}.items():
            require(query.get(key) == [value], 'Portée ou version des décisions incompatible')

    def metadata(self):
        return {**self.counts, **self.scope, 'decision_version':VERSION, 'mode':'local_experimental',
                'test_data':False, 'publication_authorized':False, 'validated_recommendations':0,
                'manifest_sha256':MANIFEST_SHA256, 'families':NAMES,
                'territorial_priority_version': TERRITORIAL_VERSION,
                'territorial_priority_counts': {'rouge':27, 'orange':33, 'jaune':9, 'gris':32, 'vert':0}}

    def grid(self):
        grid = self.canonical.minimal_grid()
        for f in grid['features']:
            f['properties'].pop('study_priority', None)
            mid = f['properties']['maille_id']
            priority = self.territorial_priority(mid)
            f['properties'].update(dataset_version=DATASET, decision_version=VERSION,
                                   sector=self.sector(mid), territorial_priority=priority,
                                   study_color=priority['color_hex'])
        return {**grid, **self.scope, 'decision_version':VERSION, 'dataset_version':DATASET,
                'test_data':False, 'publication_authorized':False, 'mode':'local_experimental'}

    def methodology(self):
        """Allowlisted, read-only example from sealed sources, never a raw export."""
        mid = 'NORM-G1K-FLAT-R+006424-C+000493'
        old = self.canonical.sheets[mid]
        cell = self.cell(mid)
        t = old['diagnostic_techniciens']
        return {**self.scope, 'decision_version':VERSION, 'mode':'local_experimental',
                'test_data':False, 'publication_authorized':False,
                'example': {'maille_id':mid, 'sector':self.sector(mid), 'area_m2':old['surface_m2'],
                            'local_events':cell['local_event_count'], 'exclusive_events':cell['canonical_event_count'],
                            'priority':self.territorial_priority(mid),
                            'hedge_length_m':t['observations']['haies']['mesure_observee'],
                            'wetland_area_m2':t['observations']['zones_humides']['mesure_observee'],
                            'actions':[{'action_id':a['action_id'], 'level':a['level']} for a in cell['actions']]}}

    def cell(self, mid):
        s = self.sheets[mid]; old = self.canonical.sheets[mid]
        proofs = {p['preuve_id']:p for p in s['preuves']}
        selected, excluded = [], []
        for p in s['propositions']:
            if not p['selectionnee']:
                excluded.append({'action_id':p['action_id'], 'name':NAMES[p['action_id']], 'reason':p['justification'],
                                 'scientific_status':p['resultat_scientifique']['statut']})
                continue
            used = [proofs[r] for r in p['observations_motivantes']]
            attrs = [r['attributs'] for r in used]
            relations = Counter(RELATIONS[r['type']] for r in used)
            # Explicit allowlist; no raw object IDs, paths, proof IDs or source geometry.
            context = {}
            for key in ('categorie','position_sol','statut_objet','nature','nature_plan_eau','site_type','statut_source','site_statut','typo_zh','typo','diag_zh','diag','qualite_zh','qualite','precision_haie_m','precision_route_m','precision_srce','precision_planimetrique','date_actualisation','site_actu_date','date_modification'):
                values = [a[key] for a in attrs if key in a]
                if values:
                    context[key] = list({json.dumps(v,ensure_ascii=False):v for v in values}.values())
            observations = [f'{name} : {count} référence(s) locale(s).' for name,count in sorted(relations.items())]
            for layer in sorted({o['couche'] for r in used for o in r['objets']}):
                ids = {o['objet_id'] for r in used for o in r['objets'] if o['couche'] == layer}
                observations.append(f'{LAYERS[layer]} : {len(ids)} objet(s) référencé(s) dans cette question.')
            if p['cree_uniquement_sur_presence']:
                observations.append('Présence cartographique ; lien de connectivité incertain. Aucune connexion déduite.')
            selected.append({'action_id':p['action_id'], 'rule_id':p['rule_id'], 'name':NAMES[p['action_id']],
                             'level':dict(zip(LEVELS,'ABC'))[p['niveau_justification']], 'level_status':p['niveau_justification'],
                             'objectives':p['objectif_ecologique'], 'solution':p['type_intervention_envisageable'],
                             'question':p['question_locale'], 'deliverable':p['livrable_etude'], 'reason':p['justification'],
                             'observations':observations, 'spatial_relations':[RELATIONS[k] for k in p['lien_spatial_etabli']],
                             'uncertainties':p['incertitudes'], 'checks_before_works':p['donnees_manquantes_avant_travaux'],
                             'next_steps':p['etapes_verification_opportunite'], 'presence_only':p['cree_uniquement_sur_presence'],
                             'rank':p['classement']['rang'], 'ranking_reason':p['classement']['motif'],
                             'scientific_status':p['resultat_scientifique']['statut'], 'scientific_decision_rule':p['resultat_scientifique']['regle_decision'],
                             'source_context':context, 'precision_qualified':p['precision_relation_qualifiee'],
                             'works_validated':False, 'works_need_demonstrated':False})
        return {'mode':'local_experimental', 'decision_version':VERSION, **self.scope, 'maille_id':mid,
                'municipalities':[m['nom'] for m in old['communes']], 'diagnostic':s['diagnostic'],
                'sector':self.sector(mid), 'territorial_priority':self.territorial_priority(mid),
                'actions':selected, 'not_selected':excluded, 'main_action':None,
                'comparisons':[{k:c[k] for k in ('action_a','action_b','conclusion','motif','observations_liees')} for c in s['comparaisons']],
                'observations':deepcopy(s['observations_historiques']),
                'local_event_count':s['evenements_locaux'], 'canonical_event_count':s['evenements_exclusifs'],
                'historical':{'level':s['reference_documentaire_historique']['niveau'], 'rule':s['reference_documentaire_historique']['regle']},
                'DS':deepcopy(s['D_S']), 'source_DS_sha256':s['source_D_S_sha256'], 'historical_lead_count':len(s['pistes_historiques']),
                'test_data':False, 'publication_authorized':False, 'validated_recommendations':[], 'manifest_sha256':MANIFEST_SHA256}
