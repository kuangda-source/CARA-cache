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
    launch = json.loads(Path('reports/wc_ra_calibration_sampling_cpu_'+args.attempt+'_launch_20261010.json').read_text())
    remote = 'L='+repr(launch)+'\n'+r'''
import base64,gzip,hashlib,json,pathlib,time
s=pathlib.Path(L['stage']);root=s.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((s/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_RA_CAL_BATCH_CPU_RUNNING','live_pids':live,'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
reg=json.loads((s/'ra-calibration-sampling-preregistration.json').read_text())
assert sha(s/'ra-calibration-sampling-preregistration.json')==L['registration_sha256']
assert r['payload_after_sha256']==reg['payload_sha256']=={n:sha(s/n) for n in reg['payload_sha256']}
assert r['runtime_after_sha256']==reg['runtime_source_sha256']=={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}
assert r['planned_scope']==reg['CPU_scope']==L['CPU_scope']
names=['receipt.json','core.log','driver.log','launch.json','ra-calibration-sampling-preregistration.json']
names += [n for n in ('result.json','result.failure.json') if (s/n).exists()]
native={}
for n in names:
 raw=(s/n).read_bytes();packed=gzip.compress(raw,mtime=0)
 native[n]={'path':str(s/n),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
  'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
capture={'status':'RA_CAL_BATCH_ORIGINAL_CPU_TERMINAL_SUCCESS' if r['exit_code']==0 else 'RA_CAL_BATCH_ORIGINAL_CPU_FAILURE_COMPLETE_SCOPE_RETAINED',
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
    prefix = 'reports/wc_ra_calibration_sampling_cpu_'+args.attempt+'_terminal_20261010_'
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
            r, core, reg = (objects[n] for n in ('receipt.json','result.json','ra-calibration-sampling-preregistration.json'))
            assert r['exit_code']==r['child_exit_code']==0
            assert r['status']==core['status']=='RA_CALIBRATION_SAMPLING_CPU_NOT_REAL_MODEL'
            assert core['planned_scope']==reg['CPU_scope'] and core['payload_sha256']==reg['payload_sha256']
            assert r['result_sha256']==proof['files']['result.json']['sha256']
            assert not core['CUDA_initialized'] and core['GPU_submissions']==0
            assert (core['solver_updates'],core['net_calls'],core['actual_guided_tensors_reloaded'],
                core['actual_final_latents_reloaded'],core['actual_child_tensors_reloaded'])==(1248,2496,288,8,96)
            assert len(core['checks'])==4 and {(x['flow'],x['scenario']) for x in core['checks']}=={
                (f,s) for f in (False,True) for s in ('complete','last_vector_writer_failure')}
            actual = {x['path']: x for x in proof['actual_tensor_files']}
            recorded = set()
            assert len(actual)==62
            def bind(art):
                raw = actual[art['path']]
                assert raw['bytes']==art['bytes'] and raw['sha256']==art['sha256']
                recorded.add(art['path'])
            for check in core['checks']:
                state = check['receipt']
                assert state['planned_parent_paths']==4 and state['planned_child_arms']==12
                assert state['initial_state_restored'] and len(state['requests'])==2
                for request in state['requests']:
                    assert len(request['paths'])==2 and [p['collect'] for p in request['paths']]==[False,True]
                    for row in request['paths']:
                        assert len(row['guided_sha256'])==len(row['solver_returns'])==36
                        assert row['counters']==list(range(0,70,2))+[0]
                        assert len(row['origins'])==(3 if row['collect'] else 0)
                        if 'vector_artifact' in row:
                            bind(row['vector_artifact'])
                        for origin in row['origins']:
                            t=origin['target_step'];arms=origin['arms']
                            assert t in (13,23,33) and len(arms)==2 and [a['mode'] for a in arms]==['CC','DD']
                            assert all(arms[0][k]==arms[1][k] for k in ('origin_components','origin_fingerprint',
                                'origin_own_fingerprint','origin_own_history','current_input_sha256'))
                            for arm in arms:
                                bind(arm['artifact'])
                                assert arm['status']=='COMPLETE_SAME_STATE_DENSE_SUFFIX_CALIBRATION'
                                assert arm['parent_restored'] and arm['own_shared_history_restored']
                                assert arm['first_velocity_reused_without_extra_net_pair']
                                assert [h['step'] for h in arm['suffix_history']]==list(range(t,37))
                                assert [h['action'] for h in arm['suffix_history']]==[arm['mode']]+['DD']*(36-t)
                if check['scenario']=='complete':
                    assert check['status']=='PASS' and len(check['semantic_mutation_refusals'])==8
                    audit=check['actual_tensor_audit']
                    assert audit['full36_parent_OFF_ON_direct_equal'] and len(audit['files'])==16
                    assert audit['actual_parent_guided_tensors_reloaded']==144
                    assert audit['actual_parent_latents_reloaded']==4 and audit['actual_child_tensors_reloaded']==48
                    assert check['actual_child_truncation_refused']
                    table=dict(audit['table']);fingerprint=table.pop('fingerprint')
                    assert hashlib.sha256(json.dumps(table,sort_keys=True,allow_nan=False).encode()).hexdigest()==fingerprint
                    assert table['toy_only_not_Cosmos_calibration'] and len(table['observed_rows'])==6
                else:
                    assert check['status']=='EXPECTED_FAILURE' and check['complete_scope_retained']
                    last=state['requests'][-1]['paths'][-1]
                    assert last['status']=='CALIBRATION_PARENT_FAILED_COMPLETE_SCOPE_RETAINED'
                    assert 'vector_artifact' not in last and check['initial_full_state_restored']
            assert recorded==set(actual)
            proof.update(complete_executed_parent_paths=16,complete_child_arms_including_last_writer_failure=48,
                full_guarded_batch_complete_scope_reconstructed=True,actual_parent_guided_reloaded=288,
                actual_parent_latents_reloaded=8,actual_child_tensors_reloaded=96,
                semantic_mutation_refusals=16,actual_child_truncation_refusals=2,last_writer_failure_controls=2,
                actual_retained_Toy_tensor_file_size_and_hash_bindings=62,
                real_model_or_video_or_quality_or_speed_claim=False)
    except BaseException as error:
        proof['independent_check_failure'] = {'type':type(error).__name__,'error':str(error)}
        target.write_text(json.dumps(proof,indent=2)+'\n')
        raise
    target.write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({k:v for k,v in proof.items() if k!='files'}))
    return proof['exit_code']


if __name__=='__main__':
    raise SystemExit(main())
