#!/usr/bin/env python3
"""ReConnect Normandie: diagnostic documentaire M1 pour les 66 mailles Caen Nord.

NE calcule PAS de priorite ecologique D/S ou de decisions R1-R4 validees.
Construit un ordre de VERIFICATION CARTOGRAPHIQUE distinct, sa provenance et
quatre pistes d'instruction (sans prescription de travaux). Les observations
canoniques du moteur M2 doivent etre jointes separement par M4.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, math, tempfile, zipfile
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import mapping
from pyproj import Transformer
from shapely.ops import transform

GRID_VERSION = 'M1-CAEN-NORD-5COM-1KM2-FLAT-L93-O0-V1'
TERRITORY_ID = 'CAEN-NORD-5COM-V1'
VERSION = 'm2-annotation-documentaire-caen-nord-0.1'
CRS_SOURCE = 'EPSG:2154'
PRIORITE_PALETTE = {'rouge':'#D64545','orange':'#EF9229','jaune':'#E8C84A','gris':'#9098A4'}
CATEGORIES_CARROSSABLES = {'Route à 1 chaussée','Route à 2 chaussées','Type autoroutier','Bretelle','Rond-point'}
NATURE_MATRICE_FRAGILE = 'Matrice fragile, fortement sensible à la fragmentation'
ACTIONS = [
 {'action_id':'A04','regle_id':'R1','titre':'Étude de perméabilité des infrastructures et franchissements de la faune',
  'sujet':'Franchissement routier', 'non_prescription':'Aucun passage à faune à construire sans diagnostic sur le terrain'},
 {'action_id':'A01','regle_id':'R2','titre':'Diagnostic des continuités bocagères et éventuelles restaurations de haies',
  'sujet':'Bocage', 'non_prescription':'Ne pas planter de haie sur seule densité ou présence cartographique'},
 {'action_id':'A03','regle_id':'R3','titre':'Étude de renaturation de friche reliée à une continuité',
  'sujet':'Friches', 'non_prescription':'Ne pas prescrire des travaux sans friche attestée et diagnostic foncier/écologique'},
 {'action_id':'A02','regle_id':'R4','titre':'Diagnostic de connectivité des mares et habitats humides',
  'sujet':'Milieux humides', 'non_prescription':'Ne pas prescrire une création de mare sans inventaire ni contexte hydrologique'}
]

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for x in iter(lambda:f.read(1024*1024),b''):h.update(x)
 return h.hexdigest()

def dump(path,obj):
 path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n',encoding='utf8')

def jnum(n, precision=2):
 if n is None or pd.isna(n): return None
 if not math.isfinite(float(n)):return None
 return round(float(n),precision)

def normalize_str(x):
 if x is None or pd.isna(x):return None
 s=str(x).strip()
 return s if s and s!='-' else None

def color_rule(obs):
 if obs['paires_route_matrice_fragile_en_service_au_sol']>0 and obs['reservoir_presence_surface_positive']:
  return {'niveau':'rouge','regle':'V1','titre':'Plusieurs indices cartographiques à vérifier',
          'motif':'Au moins un croisement route en service au sol–matrice SRCE fragile, et une surface de réservoir cartographiée dans cette maille. Leur coexistence ne démontre pas une rupture écologique.'}
 if obs['nombre_paires_route_corridor_2d']>0:
  return {'niveau':'orange','regle':'V2','titre':'Croisement cartographique à examiner',
          'motif':'Au moins un segment routier a une intersection linéaire positive avec une matrice SRCE, sans preuve suffisante pour classer V1.'}
 if obs['corridor_presence_surface_positive'] or obs['reservoir_presence_surface_positive']:
  return {'niveau':'jaune','regle':'V3','titre':'Continuité cartographiée à documenter',
          'motif':'Présence d’une matrice SRCE ou d’un réservoir, mais aucun croisement linéaire route–matrice observé dans les couches étudiées. Cela n’établit pas une absence de pression.'}
 return {'niveau':'gris','regle':'V4','titre':'Information insuffisante',
         'motif':'Les sources mobilisées ne fournissent ni croisement linéaire observé ni surface positive de corridor/réservoir dans la maille ; les inventaires ne sont pas exhaustifs.'}

def optional_rows(csv, grid):
 if csv is None: return {}, {'statut':'non_fourni','raison':'CSV réel téléchargé sur le Mac non joint à la conversation; aucune mesure de haie ou plan d’eau n’est reconstituée.'}
 df=pd.read_csv(csv,keep_default_na=True)
 required={'maille_id','grid_version'}
 if not required.issubset(df.columns):raise ValueError('CSV complément M1 incomplet: maille_id/grid_version absents')
 if len(df)!=len(grid):raise ValueError(f'Complément M1: {len(df)} lignes, attendu {len(grid)}')
 if df[['maille_id','grid_version']].duplicated().any():raise ValueError('Doublon de clé dans complément M1')
 if set(df.grid_version.astype(str))!={GRID_VERSION}:raise ValueError('Version de grille différente dans complément M1')
 if set(df.maille_id.astype(str))!=set(grid.maille_id.astype(str)):raise ValueError('Mailles du complément différentes de la grille')
 if 'haies_longueur_m_observe' not in df.columns:raise ValueError('Colonne haies_longueur_m_observe manquante')
 return {str(r['maille_id']):r.to_dict() for _,r in df.iterrows()}, {'statut':'joint_sur_66_mailles','fichier':csv.name,'sha256':sha(csv)}

def optional_value(row,kind,metric):
 if row is None:return None
 stat=row.get(kind+'_statut_couverture')
 if stat=='non_evalue' or pd.isna(stat):return None
 return jnum(row.get(kind+'_'+metric))

def build(args):
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory() as t:
  with zipfile.ZipFile(args.m1_zip) as z:
   for m in z.infolist():
    dest=(Path(t)/m.filename).resolve()
    if not dest.is_relative_to(Path(t).resolve()):raise ValueError('Chemin archive dangereux')
   z.extractall(t)
  roots=list(Path(t).rglob('grille_caen_nord.gpkg'))
  if len(roots)!=1:raise ValueError('Grille M1 absente ou ambiguë')
  base=roots[0].parent
  h=gpd.read_file(base/'grille_caen_nord.gpkg',layer='grille_caen_nord').sort_values('maille_id').reset_index(drop=True)
  r=gpd.read_file(base/'routes.gpkg',layer='routes'); c=gpd.read_file(base/'corridors.gpkg',layer='corridors'); v=gpd.read_file(base/'reservoirs.gpkg',layer='reservoirs')
  if len(h)!=66 or len(r)!=8539 or len(c)!=31 or len(v)!=20:raise ValueError('Effectifs M1 incohérents')
  for lbl,df in [('grille',h),('routes',r),('corridors',c),('reservoirs',v)]:
   if df.crs is None or df.crs.to_epsg()!=2154:raise ValueError(f'CRS non conforme {lbl}')
   if not df.geometry.is_valid.all():raise ValueError(f'Géométries invalides: {lbl}')
  if h.maille_id.duplicated().any() or set(h.grid_version)!={GRID_VERSION}:raise ValueError('Grille invalide')
  complements,complement_meta=optional_rows(args.complement_csv,h)

  result={}
  for i,cell in h.iterrows():
   mid=str(cell.maille_id)
   res=[];co=[]
   for k in v.sindex.query(cell.geometry,predicate='intersects'):
    vv=v.iloc[int(k)];inter=cell.geometry.intersection(vv.geometry)
    if inter.area>0:res.append((str(vv.objet_id),normalize_str(vv.sous_trame),inter))
   for k in c.sindex.query(cell.geometry,predicate='intersects'):
    cc=c.iloc[int(k)];inter=cell.geometry.intersection(cc.geometry)
    if inter.area>0:co.append((str(cc.objet_id),str(cc.classe_corridor),inter))
   res_union=unary_union([a[2] for a in res]) if res else None
   co_union=unary_union([a[2] for a in co]) if co else None
   result[mid]={'maille_id':mid,'grid_version':GRID_VERSION,'territory_id':TERRITORY_ID,
       'geometry':cell.geometry,'area_m2':float(cell.clipped_area_m2),'pilot_fraction':float(cell.pilot_fraction),
       'is_boundary':bool(cell.is_boundary),
       'pairs':{}, 'reservoir_ids':sorted({a[0] for a in res}),
       'reservoir_sous_trames':sorted({a[1] for a in res if a[1]}),
       'reservoir_area_m2_union':float(res_union.area) if res_union else 0.,
       'corridor_ids':sorted({a[0] for a in co}),
       'corridor_classes':sorted({a[1] for a in co}),
       'corridor_area_m2_union':float(co_union.area) if co_union else 0.,
       'route_ids':set(),'pair_classes':collections.Counter(),'road_classes':collections.Counter(),
       'pair_frag_on_soil_service':0,'source_dates_corridors':['2014'] if co else []}
  # Identité de la PAIRE, pas identité d'un événement canonique M2.
  pair_intersections=gpd.sjoin(r[['route_id','categorie','importance','statut_objet','position_sol','geometry']],
      c[['objet_id','classe_corridor','geometry']],predicate='intersects',how='inner')
  n_positive_pairs=0; ids_positive=set(); n_links=0
  for _,row in pair_intersections.iterrows():
   geom=row.geometry.intersection(c.geometry.iloc[int(row.index_right)])
   if geom.is_empty or geom.length<=0: continue
   n_positive_pairs+=1
   route_id=str(row.route_id);corridor_id=str(row.objet_id)
   pair_id='M1PAIR-'+hashlib.sha256((route_id+'|'+corridor_id).encode()).hexdigest()[:16].upper()
   ids_positive.add(pair_id)
   is_fragile=str(row.classe_corridor)==NATURE_MATRICE_FRAGILE
   on_soil_service=(str(row.statut_objet)=='En service' and str(row.position_sol)=='0')
   is_carrossable=str(row.categorie) in CATEGORIES_CARROSSABLES
   for j in h.sindex.query(geom,predicate='intersects'):
    cell=h.iloc[int(j)]; within=geom.intersection(cell.geometry)
    if within.is_empty or within.length<=0: continue
    b=result[str(cell.maille_id)]
    if pair_id in b['pairs']:continue
    b['pairs'][pair_id]={'paire_id':pair_id,'route_id':route_id,'corridor_id':corridor_id,
         'categorie_route':str(row.categorie),'classe_corridor':str(row.classe_corridor),
         'route_en_service_au_sol':on_soil_service,'categorie_carrossable':is_carrossable,
         'intersection_2d_longueur_m':round(float(within.length),2)}
    b['route_ids'].add(route_id);b['pair_classes'][str(row.classe_corridor)]+=1
    b['road_classes'][str(row.categorie)]+=1
    if is_fragile and on_soil_service and is_carrossable:b['pair_frag_on_soil_service']+=1
    n_links+=1

  to_crs84=Transformer.from_crs(2154,4326,always_xy=True)
  feats=[];fiches=[];summary=collections.Counter();per_action=collections.Counter()
  for mid,b in result.items():
   p=list(b['pairs'].values()); pc=b['pair_classes']
   complement=complements.get(mid)
   haie_l=optional_value(complement,'haies','longueur_m_observe')
   haie_n=optional_value(complement,'haies','nombre_observe')
   eau_n=optional_value(complement,'plans_eau','nombre_observe')
   eau_s=optional_value(complement,'plans_eau','surface_m2_observe')
   mare_n=optional_value(complement,'mares_referencees','nombre_observe')
   friche_n=optional_value(complement,'friches','nombre_observe')
   humide_n=optional_value(complement,'zones_humides','nombre_observe')
   # Types de contextes observés, pas classes de gravité écologique.
   obs={'nombre_paires_route_corridor_2d':len(p),
        'nombre_routes_distinctes_avec_croisement':len(b['route_ids']),
        'paires_route_matrice_fragile_en_service_au_sol':b['pair_frag_on_soil_service'],
        'paires_matrices_fragiles':pc[NATURE_MATRICE_FRAGILE],
        'paires_matrices_robustes':sum(x for k,x in pc.items() if k!=NATURE_MATRICE_FRAGILE),
        'categories_routes_avec_croisement':dict(sorted(b['road_classes'].items())),
        'reservoir_nombre_objets_cartographies':len(b['reservoir_ids']),
        'reservoir_surface_union_m2':jnum(b['reservoir_area_m2_union']),
        'reservoir_presence_surface_positive':b['reservoir_area_m2_union']>0,
        'reservoir_sous_trames':b['reservoir_sous_trames'],
        'corridor_nombre_objets_cartographies':len(b['corridor_ids']),
        'corridor_surface_union_m2':jnum(b['corridor_area_m2_union']),
        'corridor_presence_surface_positive':b['corridor_area_m2_union']>0,
        'corridor_classes_source':b['corridor_classes'],
        'haies_longueur_observee_m':haie_l,'haies_nombre_objets_observes':haie_n,
        'plans_eau_surface_observee_m2':eau_s,'plans_eau_nombre_observes':eau_n,
        'mares_referencees_nombre_observes':mare_n,
        'friches_nombre_observees':friche_n,
        'zones_humides_nombre_observees':humide_n}
   triage=color_rule(obs);triage['couleur_hex']=PRIORITE_PALETTE[triage['niveau']]
   triage.update({'objet':'triage_de_verification_documentaire','validation_ecologique':False,
           'ne_pas_afficher_comme':'priorite_ecologique_ou_urgence','method_version':VERSION})
   notes=[]
   if b['is_boundary']:notes.append('maille_decoupee_par_limite_territoire; indices sans extrapolation à l’hexagone complet')
   if len(p):notes.extend(['intersections_routes_matrices_uniquement_2d','pas_de_preuve_obstacle_ecologique'])
   else:notes.append('zero_croisement_observe_n_est_pas_absence_validee')
   if b['corridor_ids']:notes.extend(['sous_trame_matrices_non_documentee','SRCE_2014_precision_source_inconnue'])
   notes.append('couverture_inventaires_ecologiques_non_attestee')
   if complement is None:notes.append('complement_m1_haies_plans_eau_non_fourni_ici')
   else:notes.append('complement_m1_couverture_ecologique_non_attestee')
   if b['reservoir_sous_trames'] and 'Milieu humide' in b['reservoir_sous_trames']:
    humide_observe=True
   else: humide_observe=False
   # Etude R1 sur un signal documentaire 2D, jamais une prescription.
   a04=len(p)>0
   a01=haie_l is not None and haie_l>0 and (bool(b['corridor_ids']) or bool(b['reservoir_ids']))
   a02=humide_observe or (eau_n is not None and eau_n>0) or (mare_n is not None and mare_n>0)
   a03=friche_n is not None and friche_n>0
   decisions=[]
   decisions.append({'action_id':'A04','regle_id':'R1','statut_regle_m2':'non_evaluable',
       'piste_investigation':'a_etudier' if a04 else 'non_qualifiable',
       'proposition':'Réaliser un diagnostic de perméabilité au droit des infrastructures et vérifier les ouvrages existants, les espèces concernées et la circulation.' if a04 else 'Compléter les données de franchissabilité et la couverture des corridors avant de conclure à l’absence de problème.',
       'motif':'Croisement routier et matrice écologique observés en 2D, pas obstacle confirmé.' if a04 else 'Aucun croisement routier 2D observé, absence non attestée.',
       'preuves_m1':sorted(b['pairs']), 'conditions_manquantes':['qualification_ecologique_du_corridor','franchissabilite','ouvrages_existants','trafic_et_especes','methodologie_R1_validee'],
       'travaux_preconises':False})
   decisions.append({'action_id':'A01','regle_id':'R2','statut_regle_m2':'non_evaluable',
       'piste_investigation':'a_etudier' if a01 else 'non_qualifiable',
       'proposition':'Étudier la continuité du réseau de haies observé et rechercher une lacune de connexion avant tout projet de plantation.' if a01 else 'Acquérir ou qualifier le réseau de haies et analyser sa continuité fonctionnelle.',
       'motif':f'{int(haie_n or 0)} objets de haies observés, {haie_l:.1f} m cumulés découpés dans cette maille; aucune rupture démontrée.' if a01 else 'Données de haies ou lien de continuité insuffisants pour identifier une rupture.',
       'preuves_m1':['IGN_BDTOPO_HAIES_COMPLEMENT'] if a01 else [],
       'conditions_manquantes':['sous_trame_bocagere','analyse_topologique_reseau','completude_inventaire','foncier_et_usages','methodologie_R2_validee'],
       'travaux_preconises':False})
   decisions.append({'action_id':'A03','regle_id':'R3','statut_regle_m2':'non_evaluable',
       'piste_investigation':'a_etudier' if a03 else 'non_qualifiable',
       'proposition':'Vérifier le statut des friches recensées, leur relation aux continuités et les contraintes avant une éventuelle étude de renaturation.' if a03 else 'Acquérir Cartofriches et vérifier les emprises de friches avant toute sélection de site.',
       'motif':'Présence descriptive de friche(s) dans le complément, sans qualification de potentiel écologique.' if a03 else 'Aucune couche validée de friches disponible pour une conclusion.',
       'preuves_m1':['FRICHES_COMPLEMENT'] if a03 else [],
       'conditions_manquantes':['inventaire_friches_qualifie','relation_spatiale_validee','etat_ecologique','pollution','statut_foncier','methodologie_R3_validee'],
       'travaux_preconises':False})
   decisions.append({'action_id':'A02','regle_id':'R4','statut_regle_m2':'non_evaluable',
       'piste_investigation':'a_etudier' if a02 else 'non_qualifiable',
       'proposition':'Étudier le réseau de mares et les continuités humides, vérifier l’inventaire PRAM et le fonctionnement hydrologique.' if a02 else 'Acquérir l’inventaire des mares et des zones humides avant toute conclusion sur les lacunes du réseau.',
       'motif':'Contexte humide ou plan d’eau réellement cartographié, sans diagnostic hydrologique de lacune.' if a02 else 'Inventaire de mares/réseau humide et analyse de connectivité insuffisants.',
       'preuves_m1':(['TVB_RES_NORM_MILIEU_HUMIDE'] if humide_observe else [])+(['IGN_PLANS_EAU_COMPLEMENT'] if (eau_n or 0)>0 else []),
       'conditions_manquantes':['inventaire_mares_complet','hydrologie','connectivite_zones_humides','especes','methodologie_R4_validee'],
       'travaux_preconises':False})
   for dec in decisions:
    if dec['piste_investigation']=='a_etudier':per_action[dec['action_id']]+=1
   if len(p):resume=f'{len(p)} couple(s) route–matrice écologique cartographié(s) en 2D dans cette maille. Obstacle non confirmé.'
   elif b['reservoir_ids'] or b['corridor_ids']:resume='Continuité écologique cartographiée, sans croisement routier 2D observé dans les données étudiées.'
   else:resume='Aucun croisement ni surface de continuité détecté dans les couches étudiées; couverture non exhaustive.'
   if humide_observe:resume+=' Réservoir de sous-trame humide présent.'
   if haie_l is not None:resume+=f' Haies observées : {haie_l:.0f} m (coupure à la limite de la maille).'
   # Distinction centrale: priorité écologique D/S non calculée, couleur exploratoire secondaire.
   fiche={'maille_id':mid,'grid_version':GRID_VERSION,'territory_id':TERRITORY_ID,
          'method_version':VERSION,'test_data':True,'diffusion_publique_autorisee':False,
          'surface_m2':jnum(b['area_m2']), 'fraction_hexagone':jnum(b['pilot_fraction'],6),'maille_partielle':b['is_boundary'],
          'priorite_examen':{'etat':'non_calculee','valeur':None,'couleur':'gris','couleur_hex':PRIORITE_PALETTE['gris'],
               'regle_D_appliquee':None,'regle_S_appliquee':None,
               'motifs':['enjeu_ecologique_non_qualifie','seuils_et_methode_non_approuves','pression_2d_non_obstacle_confirme']},
          'triage_documentaire':triage,
          'diagnostic':{'resume_elus':resume,
           'resume_techniciens':'Classe exploratoire calculée à partir de la co-présence d’observations sources (routes, matrices, réservoirs), jamais à partir d’un score de gravité. Les tables D/S ne peuvent pas fournir de priorité sur ces données.',
           'observations':obs,'qualite':{'niveau':'partielle','limites':sorted(set(notes))},
           'preuve_source_ids':{'reservoirs':b['reservoir_ids'],'corridors':b['corridor_ids'],
                'routes_avec_croisement':sorted(b['route_ids']),'paires_route_corridor_2d':sorted(b['pairs'])}},
          'actions':decisions,
          'actions_a_etudier_ids':[d['action_id'] for d in decisions if d['piste_investigation']=='a_etudier'],
          'action_ids_valides':[],
          'm2_canonique':{'nombre_evenements_agreges':None,'conflit_ids':[],
             'etat':'a_joindre_depuis_m4_interne_gpkg','attention':'Les paires M1 ne sont pas les événements canoniques M2.'}}
   fiches.append(fiche)
   summary[triage['niveau']]+=1
   # source polygons output in lon/lat for browser display.
   geo=transform(to_crs84.transform,b['geometry'])
   props={ 'maille_id':mid,'grid_version':GRID_VERSION,'territory_id':TERRITORY_ID,
       'couleur':'gris','priorite_examen':None,'priorite_examen_etat':'non_calculee',
       'triage_verification':triage['niveau'],'triage_couleur':triage['couleur_hex'],
       'triage_regle':triage['regle'],'nb_paires_M1_2d':len(p),
       'nb_routes_distinctes_2d':len(b['route_ids']),
       'reservoir_surface_m2':jnum(b['reservoir_area_m2_union']),
       'corridor_surface_m2':jnum(b['corridor_area_m2_union']),
       'haies_longueur_m':haie_l,'plans_eau_nombre':eau_n,
       'maille_partielle':b['is_boundary'],'pilot_fraction':jnum(b['pilot_fraction'],6),
       'actions_a_etudier_ids':fiche['actions_a_etudier_ids'],
       'description_courte':resume,'test_data':True}
   feats.append({'type':'Feature','properties':props,'geometry':mapping(geo)})
  assert len(fiches)==len(feats)==66
  assert len({(x['maille_id'],x['grid_version']) for x in fiches})==66
  assert sum(summary.values())==66
  assert sum(x['properties']['nb_paires_M1_2d']>0 for x in feats)==40,'Attendu: 40 mailles avec intersection route–corridor pour la source M1'
  geojson={'type':'FeatureCollection','name':'caen_nord_66_triage_documentaire','features':feats}
  dump(out/'mailles_diagnostics_documentaires_66.geojson',geojson)
  dump(out/'fiches_zones_66.json',{'version':VERSION,'grid_version':GRID_VERSION,'territory_id':TERRITORY_ID,'fiches':fiches})
  dump(out/'catalogue_4_actions_M2_references.json',{'version':VERSION,'statut':'NON officiel M5; 4 associations connues, huit autres fiches non incluses', 'actions':ACTIONS})
  dump(out/'table_triage_exploratoire.json',{'version':VERSION,'objet':'ordre_de_verification_documentaire_SEULEMENT',
      'scientific_validation':False,'legend':PRIORITE_PALETTE,'rules':[
       {'id':'V1','couleur':'rouge','condition':'route carrossable en service au sol intersecte linéairement une matrice fragile; réservoir de surface positive dans même maille','effet':'priorité de vérification documentaire; aucune gravité écologique déterminée'},
       {'id':'V2','couleur':'orange','condition':'autre intersection linéaire route–matrice documentée'},
       {'id':'V3','couleur':'jaune','condition':'pas de croisement routier 2D observé; surface positive matrice/réservoir'},
       {'id':'V4','couleur':'gris','condition':'aucun signal suffisant dans les sources mobilisées'}],
       'note':'Ne PAS implémenter comme D/S, ni renommer en priorité écologique. Pas de seuil d’événements, pas de score écologique.'})
  manifest={'created_at_utc':datetime.now(timezone.utc).isoformat(),
    'method_version':VERSION,'territory_id':TERRITORY_ID,'grid_version':GRID_VERSION,
    'm1_zip_sha256':sha(args.m1_zip),'m1_complement':complement_meta,
    'sources':{'routes':'IGN BD TOPO (M1 fourni)','corridors':'SRCE 2014 (M1 fourni)','reservoirs':'SRCE 2014 (M1 fourni)'},
    'm1_inputs':{'mailles':66,'routes':8539,'corridors':31,'reservoirs':20},
    'm1_geometric_observations':{'paires_2d_globales':n_positive_pairs,'paires_uniques':len(ids_positive),
                                'liens_paire_maille':n_links,'mailles_avec_paires_2d':40},
    'triage_exploratoire_66':dict(summary),
    'actions_documentaires_a_etudier_66':dict(per_action),
    'm2_canonique_externe_declare_par_utilisateur':{'evenements_detectes':3157,'evenements_agreges':3156,'evenements_quarantaine':1,
           'attention':'Chiffres fournis par Codex, M4 canonical GPKG non accessible dans ce contexte; non inclus dans les 66 fiches.'},
    'scientific_status':{'ecological_priority': 'non_calculee_pour_66',
      'D_S_table_unmodified':True,'R1_R4_validated_recommendations':0,
      'color_interpretation':'triage documentaire, non risque écologique','publication_autorisee':False,
      'test_data':True},'limitations':[
       'Les classes colorées sont une convention de présentation exploratoire proposée, non une méthode écologique validée.',
       'Les comptes de paires M1 ne sont PAS les 3156 événements canoniques M2.',
       'Le croisement est une intersection géométrique 2D, non un conflit/obstacle écologique confirmé.',
       'La co-présence route-corridor et réservoir dans une maille ne prouve pas leur connectivité fonctionnelle.',
       'Matrices SRCE datant de 2014, sous-trame non renseignée, précision source inconnue.',
       'Complétude de la couverture des réservoirs/corridors non validée; absence de géométrie ≠ absence écologique.',
       'Les 48 mailles découpées ne sont pas de surfaces égales; les comptes bruts ne sont pas un score.',
       'Complément haies/plans d’eau joint seulement si fichier CSV réel fourni; ne pas utiliser les fichiers de vérification hors réseau.',
       'Aucune prescription de travaux; seules des pistes d’études sont indiquées.',
       'Ne pas contourner le verrou test_data=False du pipeline M2 officiel.'
    ]}
  for name in ['mailles_diagnostics_documentaires_66.geojson','fiches_zones_66.json','catalogue_4_actions_M2_references.json','table_triage_exploratoire.json']:
   manifest.setdefault('files',{})[name]={'sha256':sha(out/name),'size_bytes':(out/name).stat().st_size}
  dump(out/'manifest.json',manifest)
  return manifest

def main():
 pa=argparse.ArgumentParser()
 pa.add_argument('--m1-zip',type=Path,required=True)
 pa.add_argument('--complement-csv',type=Path)
 pa.add_argument('--output',type=Path,required=True)
 args=pa.parse_args()
 for k in ['m1_zip','complement_csv']:
  if getattr(args,k) is not None and not getattr(args,k).is_file():pa.error(k+' fichier introuvable')
 print(json.dumps(build(args),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
