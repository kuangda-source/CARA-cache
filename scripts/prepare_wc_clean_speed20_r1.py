"""Freeze user-requested speed20, warmups, quality controls and whole cost."""
import gzip,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
SCENES=['av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199']
oldproof=json.loads((R/'reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json').read_text())
old=json.loads(gzip.decompress((R/oldproof['files']['runner']['local_path']).read_bytes()))
refs={};dur=[]
for name in SCENES:
 q=next(q for q in old['comparison']['batch']['requests'] if q['sample_name']==name)
 native=next(q for q in old['comparison']['references'] if q['sample_name']==name)
 for method,row in [('NATIVE',native)]+[(m,next(x for x in q['paths'] if x['method']==tag))
     for m,tag in [('WC','WC'),('RA','RA'),('A_NO_P','BETA1_ONE_PHASE')]]:
  refs[name+':'+method]={k:row.get(k) for k in ['final_latent_sha256','vector_artifact','actions','video_artifact','artifact']}
  sec=row.get('instrumented_pipeline_wall_seconds',row.get('pipeline_wall_seconds'))
  dur.append(dict(scene=name,method=method,source_seconds=sec))
cap=json.loads((R/'reports/wc_e3_complete64_terminal_r1_20261011_capture.json').read_text())
def rows_in(x):
 if isinstance(x,dict):
  if x.get('collect')=='A_CPD_BETA1_ONE_PHASE' and x.get('collection_complete',{}).get('deployment',{}).get('working_epoch_strategy')=='WORKING_P_AGE_KEEP_INTERVAL':yield x
  for value in x.values():yield from rows_in(value)
 elif isinstance(x,list):
  for value in x:yield from rows_in(value)
for item in cap['originals'].values():
 if not ('BLOCK_' in item['local_ref'] or 'reuse_receipt' in item['local_ref']):continue
 b=json.loads(gzip.decompress((R/item['local_ref']).read_bytes()))
 for row in rows_in(b):
  name=next((n for n in SCENES if row.get('label','').startswith(n)),None)
  if name is None:continue
  key=name+':KEEP_A_P'
  if key in refs:continue
  refs[key]={k:row[k] for k in ['final_latent_sha256','vector_artifact','actions','video_artifact']}
  accepted=json.loads((R/'reports/wc_e3_complete64_accepted_results_r1_20261012.json').read_text())
  recorded=next(x for x in accepted['per_slot_all64'] if x['strategy']=='WORKING_P_AGE_KEEP_INTERVAL' and x['sample_name']==name and x['method']=='A_CPD_BETA1_ONE_PHASE')
  dur.append(dict(scene=name,method='KEEP_A_P',source_seconds=recorded['recorded_cost']['instrumented_pipeline_wall_seconds']))
assert len(refs)==10 and len(dur)==10
# Four full paths per scene/method: two warmups plus two measured rounds.
envelope=sum(x['source_seconds']*4 for x in dur)
forecast=(envelope*1.30+600+1200)/3600
assert forecast<=8
c={'card':'WC-CLEAN-SPEED20-BETA1-KEEP-R1-20261012-A','run_id':'wc-clean-speed20-beta1-keep-r1',
 'methods':['NATIVE','WC','RA','A_NO_P','KEEP_A_P'],'scenes':SCENES,
 'requests':[next(x for x in json.loads((R/'configs/wc_e3_complete64_production_r1_20261011.json').read_text())['requests'] if x['name']==n) for n in SCENES],
 'A_method':'BETA1_ONE_PHASE','A_boundary':25,'A_strength':[1.,.5],
 'early_head_elision':False,'working_epoch_strategy':'WORKING_P_AGE_KEEP_INTERVAL',
 'timed_runs':20,'warmup_runs':20,'warmups_per_scene_method':2,'total_complete_paths':40,'model_loads':1,
 'round_orders':['forward','reverse'],'main_timing':'Text encoding + denoising + VAE decoding, synchronized boundaries',
 'guardrails_retained_outside_main_timer':True,'video_write_outside_main_timer':True,
 'algorithm_caches_anchors_projection_and_candidate_heads_paid':True,
 'per_step_tensor_copies_hashes_checkpoints_files_in_clean_timer':False,
 'old_audit_endpoint_and_action_bindings':refs,'all93_LPIPS_after_GPU':True,
 'forecast_complete_GPUh':forecast,'cost_source_all10':dur,'prior_40_path_envelope_seconds':envelope,
 'whole_cost_margin_factor':1.30,'model_load_import_allowance_seconds':600,'outside_timer_io_quality_binding_allowance_seconds':1200,
 'automatic_single_job_GPUh':8,'cumulative_cap_GPUh':77.89524658965853,
 'authority_ref':'manifests/wc_current_window_execution_authorization_20261011_8gpuh.json',
 'original_parent_stage':'.sync/wc-e3-complete64-selected-r1-20261011',
 'user_request':'两场景、五配置、正反两轮共20计时，预热另计；固定A版本、计时外核对输出及LPIPS',
 'P_mechanism_full_card_remains_deferred':True,'E2_original_card_unchanged':True,
 'GPU_execution_selected':False,'training':False,'parameter_sweep':False}
write(R/'configs/wc_clean_speed20_r1_20261012.json',c)
print(json.dumps({'complete_paths':40,'timed_runs':20,'warmup_runs':20,'forecast_complete_GPUh':forecast}))
