"""Prepare incremental P0 identities/counts/quote gaps. Never dispatch or tune."""
import hashlib,json,re,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'plans/cara_wc_time_protocol_p0_20261027'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(name,v):(OUT/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def main():
 OUT.mkdir(exist_ok=True)
 plan=Path('/Users/kuangda_gao/Documents/CARA_WC_Time_Protocol_and_Fair_Control_Experiment_Plan.md')
 if not (OUT/'USER_PLAN_REFERENCE.md').exists():(OUT/'USER_PLAN_REFERENCE.md').write_bytes(plan.read_bytes())
 cal=read('manifests/cara_shared_CAL66_scope_quote_r1_20261025.json');dev=read('manifests/cara_DEV128_scope_r1_20261026.json')
 shared=cal['roles']['SHARED25_C'];assert shared['policy']==dev['roles']['SHARED25_C']['policy']
 samples=read('configs/wc_scout_cal12_production_entry_r1_20261018.json')['requests'];assert [x['name'] for x in samples]==cal['CAL_FIT_members']
 schedule=next(x for x in cal['schedules'] if x['requested_steps']==35)
 ra=read('reports/cara_wc_time_P0_RA_identity_20261027.json')
 settings={k:v for k,v in read('configs/f1_setup.json').items() if k.startswith('worldcache_')}
 mapping={k:dict(local=v,consumer='wc.apply_worldcache -> model.net.'+k) for k,v in settings.items()}
 mapping['worldcache_num_steps'].update(local=35,effective=70,consumer='video2world.generate_vid2world: target_steps=num_steps*2',actual_CFG=72,reset_after=70)
 roles={
 'NATIVE_U36':dict(kind='native',entry='wcomr.policy_generator_r1.p2_native_sampling.execute',cache=False),
 'WC_WRAPPER_ALLD_U36':dict(kind='wc',settings=settings,force_full=True,edit='skip predicate False only; probe/history intact'),
 'WC_README_U36':dict(kind='wc',settings=settings,force_full=False,ATS_base_mult=5),
 'WC_PAPER_PORT_U36':dict(kind='wc',settings={**settings,'worldcache_rel_l1_thresh':.08,'worldcache_saliency_weight':.12,'worldcache_flow_scale':.5},ATS_base_mult=4,ATS_fraction='cnt/70 per CFG; reset unchanged',paper_exact=False),
 'WC_TUNED_U36':dict(kind='selected_shared_tau',base='WC_PAPER_PORT_U36',tau_candidates=[.04,.06],selected_tau=None),
 'RA_LOCAL_U36':dict(kind='local_RA',entry='wcomr.clean_speed20_r1.execute:RA',calibration_fingerprint=ra['calibration_fingerprint'],threshold=ra['RA_spec']['threshold'],RA_spec=ra['RA_spec'],paper_exact=False),
 'CARA_SHARED25_C_U36':dict(kind='frozen_policy',entry='wcomr.policy_generator_r1.production_sampling.execute',policy=shared['policy'],policy_fingerprint=shared['policy']['fingerprint'])}
 for name,r in roles.items():r['identity_fingerprint']=digest(dict(role=name,definition=r,schedule=schedule,seed=0,source=sha(ROOT/'src/wcomr/wc_time_protocol_p0.py')))
 matrix=[]
 def add(section,scene,role,rep=1,**kw):
  row=dict(id=f'{section}:{scene}:{role}:{rep}',section=section,scene=scene,role=role,seed=0,repeat=rep,**kw);matrix.append(row)
 scenes=cal['CAL_FIT_members'];names=list(roles)
 # Phase A: finite calibration and numerical diagnostics; release before scoring.
 for role in names[:3]+['CARA_SHARED25_C_U36','TAU_0.04','TAU_0.06']:
  add('A_WARM',scenes[0],role,eligible_clean_time=False)
 for scene in scenes[:2]:
  for role in names[:3]:
   for on in (False,True):add('A_DIAGNOSTIC',scene,role,1+int(on),timing_enabled=on,eligible_clean_time=False)
 for scene in scenes[:2]:
  for role in ('NATIVE_U36','CARA_SHARED25_C_U36'):add('A_ANCHOR',scene,role,eligible_clean_time=True)
  for tau in (.04,.06):add('A_CALIBRATION',scene,f'TAU_{tau}',tau=tau,eligible_clean_time=True)
 assert len(matrix)==26
 # GPU released, CPU selects and freezes tau. Phase B is a fresh common batch.
 for role in names:add('B_WARM',scenes[0],role,eligible_clean_time=False)
 for i,scene in enumerate(scenes):
  for role in (names if i%2==0 else names[::-1]):add('B_QUALITY',scene,role,eligible_clean_time=True)
 for scene in scenes[:2]:
  for role in [n for n in names[::-1] if n!='WC_WRAPPER_ALLD_U36']:add('B_TIMING_REPEAT',scene,role,2,eligible_clean_time=True)
 assert len(matrix)==73 and len({x['id'] for x in matrix})==73
 counts=dict(physical_paths=73,phase_A=26,phase_B=47,formal_cells=28,calibration_physical_paths=4,calibration_anchor_paths=4,selected_reused_cells=0,warm=13,timing_repeats=12,diagnostic_on_off_three_arm=12,quality_videos=28,quality_positions=112,LPIPS_pairs_per_metric=24,LPIPS_frames_per_metric=2232,LPIPS_metrics=2,selection_Alex_pairs=4,selection_Alex_frames=372,loads=2,automatic_GPU_retries=0)
 card=dict(schema='CARA_WC_TIME_P0_PREREG_R1',source_main=read('reports/cara_wc_time_P0_live_snapshot_20261027.json')['local_HEAD'],user_plan_sha256=sha(plan),request='CPU_PREP_ONLY_NO_GPU',roles=roles,config_mapping=mapping,schedule=schedule,schedule_sha256=digest(schedule),requests=samples,request_sha256={s['name']:digest(s) for s in samples},scope=counts,physical_matrix=matrix,
 execution_dependencies=['physical_matrix is exact sequential order within each phase','Phase A ends with release and settlement, then four CPU Alex scores and immutable tau freeze','Phase B requires fresh admission and load, seven warm paths, all28 same-batch formal cells, then12 reverse repeats','Release Phase B before all quality scoring; no cross-phase formal reuse'],
 selection=dict(CAL=scenes[:2],candidates=[.04,.06],no_adaptive_expansion=True,per_prompt_time_tolerance_fraction=.05,eligible='Both prompts abs(T_DD_tau/T_DD_CARA-1)<=.05',rank=['eligible: lowest mean Alex','otherwise: lowest max relative absolute T_DD mismatch, label UNMATCHED','tie: lower mean Alex','tie: smaller tau'],finite_complete_only=True,selection_if_any_candidate_missing='NO_SELECTION_COMPLETE_DENOMINATOR_REQUIRED',freeze_before_other_two_CAL=True,final16_tuning=False),
 GPU_authorized=False,GPU_dispatch_ready=False,real_GPU_equivalence_passed=False,old_thresholds_unchanged=True,old_T_DD=None,final16='ORIGINAL_PROTECTED_IDENTITY_NOT_READ_FOR_SELECTION',highspeed19D='NO_REGISTERED_LOCAL_ENTRY_FOUND_NOT_MERGED')
 card['budget_increment_permission']={'source':'direct_user_chat_20261027','mainline_only':True,'increment_GPUh':24,'notify_each_increase':True,'applied_now':False,'does_not_authorize_GPU_launch':True}
 card['scope_sha256']=digest(card);write('CONTROL_IDENTITY_MATRIX.yaml',card) # JSON is a YAML 1.2 subset.
 binding=read('reports/cara_CAL66_quality_binding_20261025.json')
 write('SCORING_BINDINGS.json',dict(identity=binding['identity'],required_resources={k:binding['resources'][k] for k in ('MUSIQ_SPAQ','DINO','AMT_S','RAFT_THINGS')},source_ref='reports/cara_CAL66_quality_binding_20261025.json',source_sha256=sha(ROOT/'reports/cara_CAL66_quality_binding_20261025.json'),active_dimensions=['MUSIQ_LONGER512','subject_consistency','motion_smoothness','dynamic_degree'],new_quality_model_execution=False,CPU_proof_reuse='Only unchanged accepted models; full new card scorer/decoder integration pending',LPIPS=dict(Alex='lpips0.1.4 alex v0.1 [-1,1]',VGG='piq0.8.0 default VGG [0,1]',reference='SAME_PROMPT_NEW_NATIVE_U36',frames=93,resolution=[432,768],resize=False)))
 oldtime=read('reports/cara_latency_boundary_audit_r1_20261027.json')['cards'];hosts={}
 for host,source,base,sharedrole in [('two_card','CAL66','NATIVE35','SHARED25_C'),('four_card','C112','NATIVE','SHARED26_C')]:
  groups=oldtime[source]['groups'];native=groups[base]['means']['full_request_seconds'];caratime=groups[sharedrole]['means']['full_request_seconds'] if host=='two_card' else None
  prices={n:dict(T_DD=None,measured_new_request_seconds=None,historical_request_seconds=native if n=='NATIVE_U36' else caratime if n=='CARA_SHARED25_C_U36' else None,complete_quote_seconds=None) for n in names}
  # A dimensional planning scenario, explicitly not a measured upper bound or price approval.
  scenario=(73*native/3600+1.0+.35)*1.25
  hosts[host]=dict(roles=prices,matched_historical_native_ref=source,native_request_seconds=native,all73_at_native_scenario_GPUh=scenario,scenario_is_not_upper_bound=True,whole_validated_quote_GPUh=None,hard_limit_authorized_GPUh=None,quality_GPUh=0,post_release_CPU=dict(cpus=4,memory_GiB=12,planning_wall_hours=6,allocated_vCPUh_cap=24,measured_whole_wall_seconds=None),missing=['AllD probe overhead price','README/PaperPort/tau/RA matched current prices','A/B diagnostic/hash/transfer/telemetry overhead','full new scorer wall/RAM bound','target-host thermal matched confirmation'])
 ledger=read('reports/cara_wc_time_P0_live_snapshot_20261027.json')['hosts']['four_card']['ledger']
 write('COST_AND_RESOURCE_ENVELOPE.json',dict(status='NOT_READY_COMPLETE_MEASURED_QUOTE_MISSING_NO_GPU_AUTHORITY',scope=counts,hosts=hosts,central=dict(used=ledger['used_gpu_hours'],reserved=ledger['reserved_gpu_hours'],available=ledger['available_gpu_hours'],cap=226),old_uncertainty_hold_GPUh=16.5,final16_quote_GPUh=None,reserve_final16_before_development_admission=True,planned_disk_minimum_GiB=30,phase_costs=['load','13 warm','12 diagnostics','28 formal cells','4 calibration anchors and4 tau search cells','12 repeats','checkpoint/hash/write/read','idle while holding GPU','release/failed attempt actual cost','post-release48 formal LPIPS scores plus4 selection Alex scores and112 quality scores'],money_counting='one central envelope; external host mirror is not extra credit'))
 # Hash every immutable input referenced here and every protected prior artifact (no historical edits).
 tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0');tracked=set(filter(None,tracked))
 protected={p for p in tracked if (p.startswith(('reports/','configs/','manifests/','plans/')) and re.search(r'(DEV128|cara_IG_|CAL66|cara_innovation_gain)',p)) or re.match(r'research/(702|716|717|721|722)_',p)}
 refs=protected|{'configs/f1_setup.json','configs/wc_scout_cal12_production_entry_r1_20261018.json','reports/cara_latency_boundary_audit_r1_20261027.json','reports/cara_latency_boundary_audit_verified_r1_20261027.json','reports/wc_native_lpips_historical_protocol_audit_20261027.json','reports/wc_native_lpips_official_rescore_accepted_20261027.json','plans/cara_policy_generator_20261020/NEW_INPUT_POOL48_R1_20261025.json','src/wcomr/clean_speed20_r1.py','src/wcomr/policy_generator_r1/p2_native_sampling.py','src/wcomr/policy_generator_r1/production_sampling.py','src/wcomr/current_birth_real_inputs_r1.py'}
 for n in cal['source_bindings']:refs.add(n)
 for n in refs:
  assert (ROOT/n).exists(),n
 rows={n:sha(ROOT/n) for n in sorted(refs)}
 # Direct explicit source bindings are checked against their recorded SHA.
 checks=[]
 for doc in ['manifests/cara_shared_CAL66_scope_quote_r1_20261025.json','manifests/cara_DEV128_scope_r1_20261026.json','reports/wc_native_lpips_historical_protocol_audit_20261027.json']:
  value=read(doc)
  for k in ('source_bindings','input_bindings','input_sha256'):
   for n,h in value.get(k,{}).items():
    if (ROOT/n).is_file():
     actual=sha(ROOT/n);assert actual==h,(doc,n);rows[n]=actual;checks.append(dict(owner=doc,path=n,sha256=h,match=True))
 assert not subprocess.check_output(['git','diff','HEAD','--',*sorted(protected)],cwd=ROOT)
 write('REFERENCE_SHA_INVENTORY.json',dict(main=card['source_main'],plan_sha256=sha(plan),references=rows,protected_paths=sorted(protected),direct_recorded_SHA_checks=checks,protected_vs_main_unchanged=True,scope='All explicit P0 source refs and protected DEV128/IG/CAL66/702/716/717/721/722 artifacts; not all repository history'))
 print('Prepared',len(matrix),'physical paths;',len(protected),'protected files;',len(rows),'references;',len(checks),'explicit SHA checks')
if __name__=='__main__':main()
