import copy,importlib.util,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('local_acceptor',R/'scripts/analyze_wc_drop1_full18_r1.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
c=json.loads((R/m.CONFIG).read_text());scenes=[q['name'] for q in c['requests']]
rows=[]
for repeat in (1,2):
 for method in m.METHODS if repeat==1 else m.METHODS[::-1]:rows.append(dict(id=f'warm_{repeat}_{method}',scene=scenes[0],method=method,section='WARMUP',round=repeat))
for i,scene in enumerate(scenes):
 for method in m.METHODS if i%2==0 else m.METHODS[::-1]:rows.append(dict(id=f'timed_{i}_{method}',scene=scene,method=method,section='TIMED',round=1))
for r in rows:
 plan=c['plans'][r['method']]
 r.update(status='COMPLETE',semantic_plan=plan,actions=['DD' if a=='D' else 'CC' for a in plan],solver_steps=36,guided_pairs=36,online_teacher_calls=0,in_timing_hashes=0,research_checkpoints=0,in_timing_guided_copies=36 if r['section']=='WARMUP' else 0,endpoint_audit='PASS',decoded_video={'frames':93},core_seconds=100.,write_deferred_after_main_timer=True,
  source_history=[dict(A_readout=dict(readout_action=a,teacher_calls=0,shared_alpha=1 if a=='A' else 0,extra_heads=1 if a=='A' else 0),teacher_calls=0,true_D_before=1,true_D_after=1) for a in plan],LPIPS={'frame_distances':[.25]*93,'frames':93,'mean_LPIPS':.25},counts={'DD':plan.count('D'),'A':plan.count('A'),'C_plain':plan.count('C')})
launch=dict(registration_sha256='reg',config_sha256='config',source_revision='revision',supervisor_pid=12,gpu_uuid='UUID',run_id=c['run_id'],scope_counts=c['scope_counts'])
v=dict(mode='terminal',launch=launch,payload_verified={'source':True},runtime_verified={'runtime':True},registration={'payload_sha256':{'source':'sha'}},registration_sha256='reg',production_CPU=dict(status='DROP1_FULL18_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU',config_sha256='config',registration_sha256='reg',source_revision='revision'),numeric_CPU=dict(status='DROP1_FULL56_TWO_FLOW_NUMERICAL_CPU_PASS_NOT_GPU',actual_CPU_paths=56,new_complete_paths=48,old_control_paths=8,GPU_submissions=0,CUDA_initialized=False,payload_sha256={'source':'sha'}),CPU_bundle=dict(status='DROP1_COMPLETE_CPU_ACCEPTED_NOT_GPU',commands=[dict(exit_code=0)]*4),supervisor=dict(source_revision='revision',child_exit_code=0,child_pid=13),runner=dict(source_revision='revision',runs=copy.deepcopy(rows)),post_exit=dict(exit_code=0),original_processes={'supervisor':dict(state=None)},own_UUID_lock_free=True,compute_apps='',billing=dict(run_id=c['run_id'],actual_GPUh=1.,wall_seconds=3600),pool=dict(cap_gpu_hours=226,jobs={c['run_id']:dict(job_id=c['run_id'],status='SETTLED',actual_GPUh=1.)}),
 final=dict(rows=rows,scope_counts=c['scope_counts'],status='DROP1_FULL12_SCIENCE_ALL18_AUDITED_93FRAME_SCORED',original_baseline_controls=[dict(status='PASS',scene=s) for s in scenes],warm_guided_controls=[dict(status='PASS',outputs_per_arm=36)]*3,warm_repeat_controls=[dict(warm_repeats_outputs_actions_RGB_equal=True,same_scene_formal_repeat_equal=True)]*3,request_memory_records=[dict(owners_alive_after=0)]*18))
assert m.analyze(v,c)['accepted']
mutations=[lambda x:x['payload_verified'].update(source=False),lambda x:x['runtime_verified'].clear(),lambda x:x['final']['rows'].pop(),lambda x:x['final']['rows'][0].update(scene='foreign'),lambda x:x['final']['rows'][0]['decoded_video'].update(frames=92),lambda x:x['final']['rows'][-1]['LPIPS'].update(frame_distances=[.25]*92),lambda x:x['numeric_CPU'].update(actual_CPU_paths=48),lambda x:x['production_CPU'].update(config_sha256='foreign'),lambda x:x['final']['original_baseline_controls'].pop(),lambda x:x['billing'].update(actual_GPUh=.5),lambda x:x['post_exit'].update(exit_code=1),lambda x:next(q for q in x['final']['rows'] if q['method']=='S25-A' and q['section']=='TIMED')['source_history'][20]['A_readout'].update(shared_alpha=.5)]
for mutation in mutations:
 x=copy.deepcopy(v);mutation(x)
 try:r=m.analyze(x,c)
 except (AssertionError,KeyError,ValueError,TypeError):continue
 assert not r['accepted'],mutation
result=dict(status='DROP1_ACCEPTOR_POSITIVE_AND12_FAILURE_CONTROLS_PASS',positive=1,negative=12,GPU_submissions=0,SSH_queries=0,control_script_ref=str(Path(__file__).resolve().relative_to(R)),control_script_sha256=__import__('hashlib').sha256(Path(__file__).read_bytes()).hexdigest(),acceptor_sha256=__import__('hashlib').sha256((R/'scripts/analyze_wc_drop1_full18_r1.py').read_bytes()).hexdigest())
dest=R/'reports/wc_drop1_local_acceptor_controls_v2_20261017.json'
assert not dest.exists()
dest.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
