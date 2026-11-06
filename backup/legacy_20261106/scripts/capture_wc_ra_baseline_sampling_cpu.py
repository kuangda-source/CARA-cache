#!/usr/bin/env python3
"""Read original CPU handles/native evidence; no dispatch, GPU or ledger write."""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--attempt', choices=('r1', 'r2'), default='r1')
    args = parser.parse_args()
    launch = json.loads(Path('reports/wc_ra_baseline_sampling_cpu_'+args.attempt+'_launch_20261010.json').read_text())
    remote = 'L='+repr(launch)+'\n'+r'''
import base64,gzip,hashlib,json,pathlib,time
s=pathlib.Path(L['stage']);root=s.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((s/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_RA_BASELINE_BATCH_CPU_RUNNING','live_pids':live,'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
reg=json.loads((s/'ra-baseline-sampling-preregistration.json').read_text())
assert sha(s/'ra-baseline-sampling-preregistration.json')==L['registration_sha256']
assert r['payload_after_sha256']==reg['payload_sha256']=={n:sha(s/n) for n in reg['payload_sha256']}
assert r['runtime_after_sha256']==reg['runtime_source_sha256']=={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}
assert r['planned_scope']==reg['CPU_scope']==L['CPU_scope']
names=['receipt.json','core.log','driver.log','launch.json','ra-baseline-sampling-preregistration.json']
names += [n for n in ('result.json','result.failure.json') if (s/n).exists()]
native={}
for n in names:
 raw=(s/n).read_bytes();packed=gzip.compress(raw,mtime=0)
 native[n]={'path':str(s/n),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
  'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
capture={'status':'RA_BASELINE_BATCH_ORIGINAL_CPU_TERMINAL_SUCCESS' if r['exit_code']==0 else 'RA_BASELINE_BATCH_ORIGINAL_CPU_FAILURE_COMPLETE_SCOPE_RETAINED',
 'source_revision':r['source_revision'],'exit_code':r['exit_code'],'original_pids_absent':pids,
 'CPU_wall_seconds':r['CPU_wall_seconds'],'planned_scope':reg['CPU_scope'],
 'budget_before_sha256':r['budget_before_sha256'],'budget_after_sha256':r['budget_after_sha256'],
 'current_budget_sha256':sha(root/'reports/budget.json'),'CPU_never_writes_ledger':not r['ledger_written_by_this_driver'],
 'observed_unix':time.time(),'GPU_submissions':0}
capture['actual_tensor_files']=[{'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)}
 for p in sorted((s/'CPU-artifacts').rglob('*.pt'))]
print(json.dumps({'capture':capture,'native':native}))
'''
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        'gkd_minchen', 'python3 -'], input=remote, text=True, capture_output=True, timeout=55)
    if call.returncode:
        raise RuntimeError(call.stderr[-4000:])
    data = json.loads(call.stdout)
    if not data['native']:
        print(json.dumps(data['capture']))
        return 2
    prefix = 'reports/wc_ra_baseline_sampling_cpu_'+args.attempt+'_terminal_20261010_'
    target = Path(prefix+'capture_and_independent_audit.json')
    assert not target.exists()
    proof = data['capture']
    proof['files'] = {}
    objects = {}
    for n, item in data['native'].items():
        packed = base64.b64decode(item['base64'], validate=True)
        raw = gzip.decompress(packed)
        assert hashlib.sha256(packed).hexdigest()==item['compressed_sha256']
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
        path = Path(prefix+n+'.native.gz')
        assert not path.exists()
        path.write_bytes(packed)
        proof['files'][n] = {k: v for k, v in item.items() if k!='base64'}
        proof['files'][n]['local_path'] = str(path)
        if n.endswith('.json'):
            objects[n] = json.loads(raw)
    try:
        if proof['exit_code']==0:
            r, core, reg = (objects[n] for n in ('receipt.json','result.json','ra-baseline-sampling-preregistration.json'))
            assert r['exit_code']==r['child_exit_code']==0
            assert r['status']==core['status']=='RA_BASELINE_SAMPLING_CPU_NOT_REAL_MODEL'
            assert core['planned_scope']==reg['CPU_scope'] and core['payload_sha256']==reg['payload_sha256']
            assert r['result_sha256']==proof['files']['result.json']['sha256']
            assert not core['CUDA_initialized'] and core['GPU_submissions']==0
            import math
            from statistics import median
            assert (core['solver_updates'],core['net_calls'],core['actual_guided_tensors_reloaded'],core['actual_final_latents_reloaded'])==(864,1728,432,12)
            assert len(core['checks'])==4 and {(x['flow'],x['scenario']) for x in core['checks']}=={(f,s) for f in (False,True) for s in ('complete','last_vector_writer_failure')}
            actual={x['path']:x for x in proof['actual_tensor_files']}
            recorded=set()
            assert len(actual)==22
            def bind(art):
                raw=actual[art['path']]
                assert raw['bytes']==art['bytes'] and raw['sha256']==art['sha256']
                recorded.add(art['path'])
            old=json.loads(gzip.decompress(Path(reg['calibration_batch_CPU_result_ref']).read_bytes()))
            for check in core['checks']:
                state=check['receipt']
                assert state['planned_paths']==state['planned_videos']==6 and state['teacher_calls']==0
                assert state['initial_state_restored'] and len(state['requests'])==2
                for request in state['requests']:
                    rows=request['paths']
                    assert len(rows)==3 and [x['method'] for x in rows]==['WC','JOINT_NATIVE','RA']
                    for row in rows:
                        assert len(row['guided_sha256'])==len(row['solver_returns'])==36
                        assert row['counters']==list(range(0,70,2))+[0]
                        assert row['actions'][:7]==['DD']*7 and row['actions'][-1]=='DD'
                        assert len(row['actions'])==len(row['block_visits'])==36
                        assert row['conditions_before']==row['conditions_after']==rows[0]['conditions_before']
                        assert row['first_velocity_input_sha256']==rows[0]['first_velocity_input_sha256']
                        assert row['rng_after']==rows[0]['rng_after']
                        assert [x['step'] for x in row['checkpoints']]==[13,21,33,35,36]
                        assert all(len(x['components'])==50 for x in row['checkpoints'])
                        assert row['all_modules_eval'] and row['parameter_versions_unchanged']
                        for action,visits in zip(row['actions'],row['block_visits']):
                            assert visits==[[1,1]+[int(a=='D')]*(row['layers']-2) for a in action]
                        if row['method']=='WC':assert not row['policy_history'] and not row['prefix_decisions']
                        else:
                            assert [h['step'] for h in row['policy_history']]==list(range(1,37))
                            assert [h['action'] for h in row['policy_history']]==row['actions']
                            assert [d['step'] for d in row['prefix_decisions']]==list(range(8,36))
                            for d in row['prefix_decisions']:
                                t=d['step'];packets=d['paid_probes']
                                assert d['prefix_visits_before_deep']==[[1,1]+[0]*(row['layers']-2)]*2
                                assert [(p['slot'],p['counter']) for p in packets]==[(0,2*(t-1)),(1,2*(t-1)+1)]
                                assert d['action']==row['actions'][t-1]
                                if row['method']=='JOINT_NATIVE':assert d['action']==('CC' if all(p['native_cache'] for p in packets) else 'DD')
                            if row['method']=='RA':assert row['RA_threshold']==state['RA_threshold'] and row['calibration_fingerprint']==state['calibration_fingerprint']
                        if 'vector_artifact' in row:bind(row['vector_artifact'])
                if check['scenario']=='complete':
                    assert check['status']=='PASS' and len(check['semantic_mutation_refusals'])==6
                    audit=check['actual_tensor_audit']
                    assert audit['actual_guided_tensors_reloaded']==216 and audit['actual_final_latents_reloaded']==6
                    assert audit['actual_initial_7_DD_guided_direct_equal'] and len(audit['files'])==6
                    assert check['actual_final_method_truncation_refused']
                    initialized=check['threshold_initialization']
                    assert initialized['rule']=='MEDIAN_EIGHT_COMPLETE_SHARED_D6_INTERVAL_PAID_RISKS'
                    prior=next(x for x in old['checks'] if x['status']=='PASS' and x['flow']==check['flow'])
                    table=prior['actual_tensor_audit']['table']
                    assert table['toy_only_not_Cosmos_calibration'] and initialized['calibration_fingerprint']==table['fingerprint']==state['calibration_fingerprint']
                    totals=[]
                    for request in prior['receipt']['requests']:
                        history=request['paths'][0]['own_history']
                        for anchor,stop in ((7,13),(13,19),(19,25),(25,31)):
                            total=0.
                            for t in range(anchor+1,stop+1):
                                packets=history[t-1]['paid_probes'];a,b=[p['delta_y'] for p in packets]
                                total+=math.sqrt((8*a-7*b)**2+112*a*b*(1-table['rho_prior']))*table['gains'][str(t)]
                            totals.append(total)
                    assert len(initialized['observed_intervals'])==8 and math.isclose(median(totals),state['RA_threshold'],rel_tol=1e-12)
                    assert not initialized['endpoint_quality_used_to_choose_threshold'] and not initialized['matches_actual_RA_time_or_dense_count']
                else:
                    assert check['status']=='EXPECTED_FAILURE' and check['complete_scope_retained']
                    last=state['requests'][-1]['paths'][-1]
                    assert last['status']=='METHOD_FAILED_COMPLETE_SCOPE_RETAINED' and 'vector_artifact' not in last
                    assert check['initial_full_state_restored']
            assert recorded==set(actual)
            proof.update(complete_executed_paths=24,full_guarded_three_method_scope_reconstructed=True,
                actual_guided_reloaded=432,actual_latents_reloaded=12,semantic_mutation_refusals=12,
                actual_last_method_truncation_refusals=2,last_writer_failure_controls=2,
                independently_reconstructed_eight_interval_initial_thresholds=2,
                actual_retained_Toy_tensor_file_size_and_hash_bindings=22,
                real_model_or_video_or_quality_or_speed_claim=False)
    except BaseException as error:
        proof['independent_check_failure'] = {'type':type(error).__name__,'error':str(error)}
        target.write_text(json.dumps(proof,indent=2)+'\n')
        raise
    target.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k not in ('files','actual_tensor_files')}))
    return proof['exit_code']


if __name__=='__main__':
    raise SystemExit(main())
