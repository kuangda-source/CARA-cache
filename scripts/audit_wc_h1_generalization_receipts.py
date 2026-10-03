import pathlib,json,time,subprocess,hashlib,fcntl,statistics,math
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
stage=root/'.sync/wc-h1-generalization-r1';out=root/'outputs/wc-h1-generalization-r1'
def sha(path):
 h=hashlib.sha256()
 with pathlib.Path(path).open('rb') as stream:
  for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
 return h.hexdigest()
s=json.loads((out/'supervisor.json').read_text());r=json.loads((out/'diagnostic/receipt.json').read_text())
d=json.loads((stage/'deploy-r1.json').read_text());c=json.loads((stage/'mid-config.json').read_text())
assert 'ended_unix' in s and 'wall_seconds' in s,'not terminal: inspect SAME handles'
pids=[s['pid'],s['child_pid'],r['pid']]
assert all(not pathlib.Path('/proc/'+str(pid)).exists() for pid in pids)
with (root/'.sync/f1.lock').open('a+') as lock:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
for name,digest in d['payload_sha256'].items():assert sha(stage/name)==digest
budget=json.loads((root/'reports/budget.json').read_text())
assert budget==s['budget_after'] and not any(k.endswith('_inflight') for k in budget)
assert budget['cap_gpu_hours']==12 and budget['gpu_jobs_launched']==s['budget_before']['gpu_jobs_launched']+1
assert abs(budget['used_gpu_hours']-s['budget_before']['used_gpu_hours']-s['wall_seconds']/3600)<1e-12
assert s['wall_seconds']<=6000 and not s['release']['pids'] and s['release']['memory_used_mib']<=1024
monitor=[json.loads(line) for line in (out/'gpu-monitor.jsonl').read_text().splitlines()]
assert any(r['pid'] in row['pids'] for row in monitor) and all(set(row['pids'])<={r['pid']} for row in monitor)
full=r['status']=='H1_REQUESTS2_SOURCE24_LOCAL72_FULL66_NINE_GATE_PASS_REQUIRES_AUDIT'
assert (r['planned_source_denominator'],r['planned_lifetime_denominator'],r['planned_raw_files'])==(24,72,120)
gates={'input_hashes','output_hashes','trace','block_counts','state_fingerprints','sampling','named_inputs','conditions','field_signatures'}
metadata={row['sample']:row['sample_context_sha256'] for row in d['cpu_checks']['sample_metadata']['samples']}
def trace_sha(trace):
 h=hashlib.sha256();h.update(b'list')
 for row in trace:
  for key in sorted(row):h.update(str(key).encode());h.update(repr(row[key]).encode())
 return h.hexdigest()
if full:
 assert s['exit_code']==0 and len(r['requests'])==2
 assert [q['sample_name'] for q in r['requests']]==c['sample_names']
 assert r['h1_coverage']=={'requests':2,'source_arms':24,'future_source_age_cells':72,'all_held_references_immutable':True}
 assert r['mode_setup']['after']['training_modules']==0
 assert r['mode_setup']['all_train_implementations']=='torch.nn.Module.train'
 assert r['mode_setup']['parameter_and_buffer_objects_versions_unchanged']
groups=[];snapshots={};source_rows=[];lifetime_rows=[]
for req in r.get('requests',[]):
 name=req['sample_name'];context=req['reference_context']
 assert context==[c['run_id']+':'+name,'Cosmos-Predict2.5-2B:'+c['f1_setup_sha256'],metadata[name]]
 assert (req['planned_source_denominator'],req['planned_lifetime_denominator'],req['planned_raw_files'])==(12,36,60)
 if full:
  assert req['status']=='H1_REGIONS_SOURCE12_LOCAL36_NINE_GATE_PASS_REQUIRES_AUDIT'
  assert set(req['all_gate_checks'])==gates and all(req['all_gate_checks'].values())
  left,right=req['phases'];assert all(left[k]==right[k] for k in gates)
  assert req['shared_eval_through_both_phases']
  for phase in req['phases']:
   assert phase['solver_steps']==33 and phase['actual_cfg_calls_entered']==66
   assert all(len(phase[k])==66 for k in ['trace','input_hashes','output_hashes','named_inputs','conditions'])
   assert phase['sampling']['actual_schedule_steps']==36 and phase['sampling']['worldcache_horizon']==70
   assert [(p['solver_step'],p['call']) for p in phase['field_signatures']]==[(13,26),(21,42),(33,66)]
   assert all(len(p['components'])==36 for p in phase['field_signatures'])
  assert [(p['solver_step'],p['call'],p['status']) for p in right['roundtrips']]==[(13,26,'ROUNDTRIP_PASS'),(21,42,'ROUNDTRIP_PASS'),(33,66,'ROUNDTRIP_PASS')]
  a,b=req['prepared_input_calls'];assert a['source']=='OFFICIAL_PREPARE_ONCE' and b['source']=='SHARED_OFFICIAL_PREPARED_BATCH'
  assert all(a[k]==b[k] for k in ['request','prepared','rng_before','rng_after'])
 selection=req.get('source_selection');selected={}
 if selection:
  baseline=req['phases'][0]['trace'];assert len(baseline)==66
  assert all(type(p['call']) is int and p['call']==i+1 and type(p['cache_counter_before']) is int and p['cache_counter_before']==i and type(p['deep_executed']) is bool for i,p in enumerate(baseline))
  assert selection['baseline_trace_sha256']==trace_sha(baseline)
  assert selection['rule']==c['source_selection_rule'] and selection['selection_inputs']==c['selection_inputs']
  assert not selection['candidate_errors_used_for_selection']
  assert [q['region'] for q in selection['selected']]==['early','late']
  for q,region in zip(selection['selected'],c['source_regions']):
   lo,hi=region['source_step_bounds'];eligible=[step for step in range(lo,hi+1) if all(p['deep_executed'] and p['cache_counter_before']>=14 for p in baseline[2*(step-1):2*step])]
   assert eligible and q['source_solver_step']==eligible[0] and q['eligible_source_steps']==eligible
   assert q['bounds']==[lo,hi] and q['source_cfg_calls']==[2*eligible[0]-1,2*eligible[0]]
   selected[q['region']]=q
 if full:assert len(req['h1_source_records'])==4 and len(req['h1_records'])==12
 sources={}
 for record in req.get('h1_source_records',[]):
  region=record['region'];q=selected[region];branch=record['cfg_slot']
  assert record['status']=='THREE_HELD_SOURCES_COMPLETE' and record['solver_step']==q['source_solver_step'] and record['call']==q['source_cfg_calls'][branch]
  history=[p['cache_counter_before'] for p in req['phases'][1]['trace'][:record['call']-1] if p['deep_executed'] and p['cache_counter_before']%2==branch][-2:]
  assert record['historical_true_full_counters']==history==q['historical_true_full_counters'][branch] and len(history)==2
  assert req['phases'][1]['trace'][record['call']-1]['deep_executed']
  assert [row['arm'] for row in record['arms']]==['dense','matched_full','sparse']
  assert record['arms'][0]['dense_repeat_bitwise_matches_deployed']
  for row in record['arms']:
   provenance=row['provenance'];identity=provenance['identity']
   assert identity=={'request':context[0],'model':context[1],'condition':context[2]+':'+record['condition_fingerprint'],'cfg_slot':branch,'group':[2,28],'solver_step':q['source_solver_step'],'source_call':record['call'],'source_kind':row['arm']}
   assert provenance['prior_true_dense_counter']==history[-1]
   assert provenance['source_is_approximate']==(row['arm']!='dense')
   assert not provenance['inserted_into_online_cache_or_calibrator'] and not provenance['mask_reused_for_future_attention']
   sources[(region,branch,row['arm'])]=provenance
   assert len(row['wall_ms'])==3 and min(row['wall_ms'])>0 and abs(statistics.median(row['wall_ms'])-row['median_wall_ms'])<1e-9
  arms={row['arm']:row for row in record['arms']}
  source_rows.append({'sample':name,'region':region,'call':record['call'],'cfg_slot':branch,'source_step':record['solver_step'],'D_over_S_group_cost':arms['dense']['median_wall_ms']/arms['sparse']['median_wall_ms'],'arms':{kind:{'ms':row['median_wall_ms'],'velocity_rmse':row['velocity']['relative_rmse'],'residual_rmse':row['postwarp_residual']['relative_rmse']} for kind,row in arms.items()}})
 if full:assert {(p['region'],p['cfg_slot'],p['age']) for p in req['h1_records']}=={(region,b,k) for region in ('early','late') for b in (0,1) for k in (1,2,4)}
 for record in req.get('h1_records',[]):
  region=record['region'];q=selected[region];branch=record['cfg_slot']
  assert record['status']=='THREE_SOURCE_LIFETIME_CELLS_COMPLETE' and record['solver_step']==q['source_solver_step']+record['age']
  assert record['call']==2*(record['solver_step']-1)+branch+1 and record['source_call']==q['source_cfg_calls'][branch]
  assert record['prediction_before_current_shadow_truth'] and record['future_D_double_replay_bitwise_equal']
  skipped=not req['phases'][1]['trace'][record['call']-1]['deep_executed']
  assert record['official_future_skipped']==skipped and record['shadow_D_matches_deployed_full']==(None if skipped else True)
  arms={row['arm']:row for row in record['completed_arms']};assert list(arms)==['dense','matched_full','sparse']
  for kind,row in arms.items():
   assert row['provenance']==sources[(region,branch,kind)]
   assert len(row['wall_ms'])==3 and min(row['wall_ms'])>0 and abs(statistics.median(row['wall_ms'])-row['median_wall_ms'])<1e-9
   lifetime_rows.append({'sample':name,'region':region,'call':record['call'],'cfg_slot':branch,'source_step':q['source_solver_step'],'age':record['age'],'source':kind,'official_future_skipped':skipped,'ms':row['median_wall_ms'],'velocity_rmse':row['velocity']['relative_rmse'],'residual_rmse':row['postwarp_residual']['relative_rmse'],'velocity_excess_over_dense_source':row['velocity']['relative_rmse']-arms['dense']['velocity']['relative_rmse'],'local_five_percent_screen':row['velocity']['relative_rmse']<=.05 and row['postwarp_residual']['relative_rmse']<=.05})
 for scope,attempts,key in [('SOURCE',req.get('h1_source_attempts',[]),'completed_source_arms'),('FUTURE',req.get('h1_attempts',[]),'completed_arms')]:
  for attempt in attempts:
   rows=attempt.get(key,[])
   for row in rows:
    snapshot=row.get('raw_snapshot')
    if snapshot:snapshots[snapshot['path']]=snapshot
   truth=next((row.get('raw_snapshot') for row in rows if row['arm']=='dense'),None) if scope=='SOURCE' else attempt.get('truth_raw_snapshot')
   if truth:
    snapshots[truth['path']]=truth
    groups.append({'sample':name,'region':attempt['region'],'scope':scope,'call':attempt['call'],'cfg_slot':attempt['cfg_slot'],'age':attempt.get('age'),'truth':truth,'arms':rows})
indexed={snap['path'] for group in groups for snap in [group['truth']]+[row['raw_snapshot'] for row in group['arms'] if row.get('raw_snapshot')]}
extra=[snap for path,snap in snapshots.items() if path not in indexed]
code='groups='+repr(groups)+'\nextra_snapshots='+repr(extra)+'\n'+raw_code
process=subprocess.run(['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u','-'],input=code,text=True,capture_output=True,timeout=480,env={'CUDA_VISIBLE_DEVICES':'','OMP_NUM_THREADS':'2','OPENBLAS_NUM_THREADS':'2','PATH':'/usr/bin:/bin'})
(out/'raw-audit-r1.log').write_text(process.stdout+'\n'+process.stderr)
assert process.returncode==0,process.stderr[-4000:]
raw=json.loads(process.stdout.strip().splitlines()[-1])
available={str(path):sha(path) for path in (out/'diagnostic').glob('*/raw-h1/*/*/*.pt')}
raw['available_raw_file_sha256']=available;raw['unindexed_raw_artifacts']=[path for path in available if path not in snapshots]
if full:assert len(available)==len(raw['checked'])==120 and len(raw['recomputed'])==96 and not raw['unindexed_raw_artifacts']
audit={'status':'H1_GENERALIZATION_SOURCE_RAW_ERRORS_NINE_GATES_COST_RELEASE_AUDIT_PASS' if full else 'H1_GENERALIZATION_FAILURE_AVAILABLE_RAW_SOURCE_COST_RELEASE_AUDITED','source_revision':d['source_revision'],'audit_code_sha256':audit_code_sha256,'observed_unix':time.time(),'source_hashes_verified':True,'pids_absent':pids,'global_lock_free':True,'gpu_wall_seconds':s['wall_seconds'],'budget':budget,'raw_output_files_checked':len(raw['checked']),'tensor_raw_hashes_checked':2*len(raw['checked']),'raw_errors_independently_recomputed':len(raw['recomputed']),'raw_checks':raw,'peak_monitor_memory_mib':max(row['memory_used_mib'] for row in monitor),'monitor_samples':len(monitor),'gpu_release':s['release'],'receipt_sha256':{name:sha(out/name) for name in ['supervisor.json','diagnostic/receipt.json','coverage.log','gpu-monitor.jsonl']},'limits':'Two exposed CAL, correlated CFG/windows/ages. Fixed official trajectory, no independently forked rollout or video. Frozen inline reference/truth guards, not independently reconstructed complete probe caches.'}
summary={'status':'H1_GENERALIZATION_LOCAL72_AUDITED_DESCRIPTIVE_ONLY' if full else 'H1_GENERALIZATION_TECH_BLOCKED_NO_COMPLETE_MATRIX','source':d['source_revision'],'error':r.get('error'),'gpu_wall_seconds':s['wall_seconds'],'used_gpu_hours':budget['used_gpu_hours'],'remaining_gpu_hours':12-budget['used_gpu_hours'],'planned_source_arms':24,'planned_lifetime_cells':72,'complete_source_arms':3*len(source_rows),'complete_lifetime_cells':len(lifetime_rows),'source_rows':source_rows,'lifetime_rows':lifetime_rows,'closed_loop_video_independent_confirmation':False,'auto_next_GPU_H2_RV_training':False}
(out/'audit-r1.json').write_text(json.dumps(audit,indent=2)+'\n');(out/'summary-r1.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({'audit':audit,'summary':summary,'supervisor':s,'runner':r}))
