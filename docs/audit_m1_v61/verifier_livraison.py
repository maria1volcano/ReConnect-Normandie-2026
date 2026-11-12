"""Read-only audit: M1 snapshot and current M2, no M1 entrypoint executed."""
import sys, pathlib, json, hashlib, importlib.util, importlib.metadata, math, collections, subprocess
import geopandas as gpd
import pandas as pd
from shapely import union_all
from shapely.geometry import box
from pyproj import Transformer
from shapely.ops import transform
root=pathlib.Path.cwd()
snapshot=pathlib.Path(sys.argv[1])
initial_paths=subprocess.check_output(['git','ls-files','-z','--cached','--others','--exclude-standard'],text=True).split('\0')
baseline_at_start={'files':{p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in initial_paths if p and (root/p).is_file()}, 'status':subprocess.check_output(['git','status','--porcelain=v1','-uall'],text=True),'head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch':subprocess.check_output(['git','branch','--show-current'],text=True).strip()}
sys.path.insert(0,str(root))
spec=importlib.util.spec_from_file_location('m1_grid_audit',snapshot/'analysis/generate_hex_grid.py')
gen=importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)
from analysis.validate_inputs import ValidationReport,validate_spatial_coverage,validate_geodataframe,LayerSpec,POLYGONS
from analysis.prepare_priority_inputs import classify_ecological_stakes,derive_applicability
from analysis.export_m2_contract import prepare_m2_contract
out={'scope':'Delivered GeoJSON/CSV checked; absent GPKGs and raw data NOT independently verified',
     'm1_commit':subprocess.check_output(['git','rev-parse','origin/feat/m1-donnees-sig-v61'],text=True).strip(),
     'm2_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
     'python':sys.version,
     'software':{p:importlib.metadata.version(p) for p in ['geopandas','shapely','pandas','numpy','pyproj','pyogrio']}}
files=sorted(p for p in snapshot.rglob('*') if p.is_file())
out['inventory']=[{'path':p.relative_to(snapshot).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]
out['missing_handoff_gpkgs']=[name for name in ['grille_pilote','reservoirs','corridors','routes','sols','zones_construites'] if not (snapshot/f'data/processed/{name}.gpkg').exists()]
measure_report=json.loads((snapshot/'data/processed/m1_measurements_report.json').read_text())
out['csv_hashes']={name:{'expected':sha,'observed':hashlib.sha256((snapshot/'data/processed'/name).read_bytes()).hexdigest().upper(),'observed_lf':hashlib.sha256((snapshot/'data/processed'/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest().upper()} for name,sha in measure_report['output_sha256'].items()}
m=pd.read_csv(snapshot/'data/processed/sub_indicateurs.csv')
o=pd.read_csv(snapshot/'data/processed/sub_indicateurs_ocs.csv',dtype={'ocs_code_cs':str})
g=gpd.read_file(snapshot/'data/public/grille_pilote_wgs84.geojson')
l93=g.to_crs(2154)
a,b,pilot=gen.generate_grid()
a2,b2,_=gen.generate_grid()
def geometry_report(frame):
 u=union_all(frame.geometry.array)
 r=ValidationReport()
 territory=gpd.GeoDataFrame(geometry=[pilot],crs=2154)
 validate_spatial_coverage(frame,territory,r)
 return {'count':len(frame),'crs':str(frame.crs),'geometry_types':frame.geom_type.value_counts().to_dict(),
 'invalid':int((~frame.is_valid).sum()),'empty':int(frame.is_empty.sum()),'duplicate_ids':int(frame.maille_id.duplicated().sum()),
 'sum_area_m2':float(frame.area.sum()),'union_area_m2':u.area,'overlap_sum_minus_union_m2':float(frame.area.sum()-u.area),
 'missing_pilot_area_m2':pilot.difference(u).area,'outside_pilot_area_m2':u.difference(pilot).area,
 'bbox_l93':list(frame.total_bounds),'min_area_m2':float(frame.area.min()),'max_area_m2':float(frame.area.max()),
 'm2_validation':r.as_dict()}
out['delivered_geojson']={'original_crs':str(g.crs),'bbox_wgs84':list(g.total_bounds),'properties':g.columns.tolist(),**geometry_report(l93)}
out['regenerated_grid_in_memory']={**geometry_report(a),'full_area_min':float(b.area.min()),'full_area_max':float(b.area.max()),
 'full_hash':gen.semantic_digest(b),'clipped_hash':gen.semantic_digest(a),'repeat_hash_equal':gen.semantic_digest(a)==gen.semantic_digest(a2) and gen.semantic_digest(b)==gen.semantic_digest(b2)}
x=l93.set_index('maille_id'); y=a.set_index('maille_id')
out['grid_comparison']={'same_ids':set(x.index)==set(y.index),'maximum_hausdorff_m':max(x.loc[i].geometry.hausdorff_distance(y.loc[i].geometry) for i in x.index),'maximum_symmetric_difference_m2':max(x.loc[i].geometry.symmetric_difference(y.loc[i].geometry).area for i in x.index),
 'csv_ids_equal':set(m.maille_id)==set(g.maille_id),'ocs_ids_subset':set(o.maille_id)<=set(g.maille_id),
 'max_csv_vs_regenerated_area_m2':max(abs(m.set_index('maille_id').loc[i].cell_area_m2-y.loc[i].geometry.area) for i in y.index),
 'max_geojson_property_vs_geometry_area_m2':float((l93.area-l93.area_m2).abs().max())}
q=m.set_index('maille_id').join(g.set_index('maille_id')[['pilot_fraction']])
small=q.sort_values('cell_area_m2').head(8).copy()
small['road_density_m_per_km2']=small.road_length_m/small.cell_area_m2*1e6
out['small_cells']=small[['cell_area_m2','pilot_fraction','road_length_m','road_density_m_per_km2','hedge_length_m','reservoir_area_m2','corridor_area_m2','ocs_coverage_fraction','constructed_area_m2']].reset_index().to_dict('records')
numeric=m.select_dtypes('number')
out['csv']={'rows':len(m),'columns':m.columns.tolist(),'duplicate_ids':int(m.maille_id.duplicated().sum()),'null_counts':m.isna().sum().to_dict(),'negative_counts':(numeric<0).sum().to_dict(),
 'nonfinite_nonnull':int(((~numeric.isna()) & ~numeric.map(math.isfinite)).sum().sum()),'boundary_counts':m.is_boundary.value_counts().to_dict(),
 'constant_fields':{c:m[c].drop_duplicates().tolist() for c in m.columns if m[c].nunique(dropna=False)==1 and not m[c].isna().all()},
 'numeric_ranges':{c:{'min':float(m[c].min()),'max':float(m[c].max()),'sum':float(m[c].sum()),'zeros':int(m[c].eq(0).sum())} for c in numeric if not m[c].isna().all()},
 'area_over_cell_max_m2':{c:float((m[c]-m.cell_area_m2).max()) for c in ['reservoir_area_m2','corridor_area_m2','ocs_covered_area_m2','constructed_area_m2','cartofriches_area_m2','wetland_area_m2']}}
area=o.groupby('maille_id').ocs_area_m2.sum().reindex(m.maille_id,fill_value=0).to_numpy()
frac=o.merge(m[['maille_id','cell_area_m2']],on='maille_id',validate='many_to_one')
out['csv_semantic_checks']={'count_columns_integral':all(m[c].dropna().map(float.is_integer).all() if m[c].dtype.kind=='f' else True for c in m if c.endswith('_count')), 'boundary_flags_match':bool(m.set_index('maille_id').is_boundary.eq(g.set_index('maille_id').is_boundary.reindex(m.maille_id)).all()), 'ocs_versions_match':bool(o.grid_version.eq(gen.GRID_VERSION).all()),'ocs_source_ids_match':bool(o.source_id.eq('OCSGE').all()),'ocs_source_year_match':bool(o.source_year.eq(2023).all()),'main_versions_match':bool(m.grid_version.eq(gen.GRID_VERSION).all())}
out['ocs']={'rows':len(o),'columns':o.columns.tolist(),'null_counts':o.isna().sum().to_dict(),'duplicate_keys':int(o.duplicated(['maille_id','ocs_code_cs']).sum()),'codes':sorted(o.ocs_code_cs.unique()),
 'max_area_sum_minus_union_m2':float(max(area-m.ocs_covered_area_m2.to_numpy())),
 'min_area_sum_minus_union_m2':float(min(area-m.ocs_covered_area_m2.to_numpy())),
 'max_fraction_formula_error':float((frac.ocs_fraction_of_cell-frac.ocs_area_m2/frac.cell_area_m2).abs().max()),
 'max_coverage_fraction_error':float((m.ocs_coverage_fraction-m.ocs_covered_area_m2/m.cell_area_m2).abs().max()),
 'area_by_code_m2':o.groupby('ocs_code_cs').ocs_area_m2.sum().to_dict()}
out['m2_missing_decisions']={'classify_ecological_stakes':classify_ecological_stakes(),'derive_applicability':derive_applicability()}
try: prepare_m2_contract(None,versions={},test_data=False)
except Exception as e: out['m2_production_export_guard']={'exception':type(e).__name__,'message':str(e)}
# Technical sensitivity, no ecological thresholds: half/double area, half-step origin.
scenarios=[]
for area,shift in [(500000,False),(1000000,True),(2000000,False)]:
 gen.TARGET_AREA_M2=area; gen.SIDE_M=math.sqrt(2*area/(3*math.sqrt(3)))
 gen.X_SPACING_M=1.5*gen.SIDE_M; gen.Y_SPACING_M=math.sqrt(3)*gen.SIDE_M
 gen.ORIGIN_X=gen.X_SPACING_M/2 if shift else 0; gen.ORIGIN_Y=gen.Y_SPACING_M/2 if shift else 0
 z,_,_=gen.generate_grid()
 scenarios.append({'target_area_m2':area,'origin_shift_half_step':shift,'cell_count':len(z),'interior_cells':int((~z.is_boundary).sum()),'boundary_cells':int(z.is_boundary.sum()),'min_clipped_area_m2':float(z.area.min()),'union_area_m2':union_all(z.geometry.array).area})
out['technical_grid_sensitivity_only']=scenarios
# Boundary construction: densification is a numerical experiment, not a new pilot.
from shapely.geometry import Polygon
corners=[(-.28,49.2),(-.22,49.2),(-.22,49.26),(-.28,49.26)]
coords=[(u[0]+(v[0]-u[0])*i/1000,u[1]+(v[1]-u[1])*i/1000) for u,v in zip(corners,corners[1:]+corners[:1]) for i in range(1000)]
dense=transform(Transformer.from_crs(4326,2154,always_xy=True).transform,Polygon(coords))
out['bbox_projection_sensitivity']={'method':'1000 subdivisions per geographic bbox edge; diagnostic only','dense_bbox_area_m2':dense.area,'pilot_outside_dense_bbox_m2':pilot.difference(dense).area,'dense_bbox_outside_pilot_m2':dense.difference(pilot).area,'boundary_max_distance_m':pilot.hausdorff_distance(dense)}
baseline=json.loads(pathlib.Path(sys.argv[3]).read_text()) if len(sys.argv)>3 else baseline_at_start
out['m2_initial_status']=baseline['status']
out['m2_audited_code_sha256']={p:h for p,h in baseline['files'].items() if p.startswith('analysis/') and p.endswith('.py')}
out['preservation']={'changed_preexisting_files':[p for p,h in baseline['files'].items() if not (root/p).is_file() or hashlib.sha256((root/p).read_bytes()).hexdigest()!=h], 'head_unchanged':baseline['head']==subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'branch_unchanged':baseline['branch']==subprocess.check_output(['git','branch','--show-current'],text=True).strip()}
pathlib.Path(sys.argv[2]).write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in out.items() if k not in ['inventory','csv','ocs']},ensure_ascii=False,indent=2))
print(json.dumps({'csv':out['csv'],'ocs':out['ocs']},ensure_ascii=False,indent=2))
