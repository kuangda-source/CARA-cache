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
    launch = json.loads(Path('reports/wc_ra_calibration_core_cpu_'+args.attempt+'_launch_20261010.json').read_text())
    remote = 'L='+repr(launch)+'\n'+r'''
import base64,gzip,hashlib,json,pathlib,time
s=pathlib.Path(L['stage']);root=s.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((s/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_RA_CAL_CORE_CPU_RUNNING','live_pids':live,'GPU_submissions':0},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
reg=json.loads((s/'ra-coarse-cal-core-preregistration.json').read_text())
assert sha(s/'ra-coarse-cal-core-preregistration.json')==L['registration_sha256']
assert r['payload_after_sha256']==reg['payload_sha256']=={n:sha(s/n) for n in reg['payload_sha256']}
assert r['runtime_after_sha256']==reg['runtime_source_sha256']=={n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}
assert r['planned_scope']==reg['CPU_scope']==L['CPU_scope']
names=['receipt.json','core.log','driver.log','launch.json','ra-coarse-cal-core-preregistration.json']
names += [n for n in ('result.json','result.failure.json') if (s/n).exists()]
native={}
for n in names:
 raw=(s/n).read_bytes();packed=gzip.compress(raw,mtime=0)
 native[n]={'path':str(s/n),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
  'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
capture={'status':'RA_CAL_CORE_ORIGINAL_CPU_TERMINAL_SUCCESS' if r['exit_code']==0 else 'RA_CAL_CORE_ORIGINAL_CPU_FAILURE_COMPLETE_SCOPE_RETAINED',
 'source_revision':r['source_revision'],'exit_code':r['exit_code'],'original_pids_absent':pids,
 'CPU_wall_seconds':r['CPU_wall_seconds'],'planned_scope':reg['CPU_scope'],
 'budget_before_sha256':r['budget_before_sha256'],'budget_after_sha256':r['budget_after_sha256'],
 'current_budget_sha256':sha(root/'reports/budget.json'),'CPU_never_writes_ledger':not r['ledger_written_by_this_driver'],
 'observed_unix':time.time(),'GPU_submissions':0}
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
    prefix = 'reports/wc_ra_calibration_core_cpu_'+args.attempt+'_terminal_20261010_'
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
            r, core, reg = (objects[n] for n in ('receipt.json','result.json','ra-coarse-cal-core-preregistration.json'))
            assert r['exit_code']==r['child_exit_code']==0
            assert r['status']==core['status']=='RA_COARSE_CAL_CORE_PINNED_FULL36_TOY_CPU_NOT_COSMOS'
            assert core['planned_scope']==reg['CPU_scope'] and core['payload_sha256']==reg['payload_sha256']
            assert r['result_sha256']==proof['files']['result.json']['sha256']
            assert not core['CUDA_initialized'] and core['GPU_submissions']==0
            assert (core['complete_parent_paths'],core['same_state_origins'],core['complete_child_arms'],
                    core['solver_updates'],core['net_calls'])==(8,12,24,624,1248)
            assert len(core['checks'])==2 and {c['flow'] for c in core['checks']}=={False,True}
            for c in core['checks']:
                assert (c['actual_solver_updates'],c['actual_net_calls'])==(312,624)
                assert len(c['paths'])==2 and len(c['observed_rows'])==6
                for p in c['paths']:
                    assert p['full36_parent_OFF_ON_actual_equal'] and p['conditions_and_global_RNG_equal']
                    assert len(p['parent_actions'])==36 and len(p['complete_origins'])==3
                    for origin in p['complete_origins']:
                        t = origin['step']; a,b = origin['arms']
                        assert t in (13,23,33) and [a['mode'],b['mode']]==['CC','DD']
                        assert all(a[k]==b[k] for k in ('origin_components','origin_fingerprint',
                            'origin_own_fingerprint','origin_own_history','current_input_sha256'))
                        for arm in (a,b):
                            assert arm['status']=='COMPLETE_SAME_STATE_DENSE_SUFFIX_CALIBRATION'
                            assert arm['parent_restored'] and arm['own_shared_history_restored']
                            assert arm['first_velocity_reused_without_extra_net_pair']
                            assert arm['actual_suffix_solver_updates']==arm['actual_suffix_net_pairs']==37-t
                            assert [h['step'] for h in arm['suffix_history']]==list(range(t,37))
                            assert [h['action'] for h in arm['suffix_history']]==[arm['mode']]+['DD']*(36-t)
                            assert set(arm['artifact']['tensor_sha256'])=={'conditional','unconditional','guided','final_latent'}
                            assert arm['artifact']['tensor_sha256']['guided']==arm['current_guided_sha256']
                            assert arm['artifact']['tensor_sha256']['final_latent']==arm['final_latent_sha256']
                table = dict(c['table']); fingerprint = table.pop('fingerprint')
                assert hashlib.sha256(json.dumps(table,sort_keys=True,allow_nan=False).encode()).hexdigest()==fingerprint
                assert table['toy_only_not_Cosmos_calibration'] and table['maximum_estimated_reuse_age']==6
                assert table['observed_rows']==c['observed_rows']
                assert all(x['estimated_prior_not_observed_cell'] for x in table['rho_at'])
                assert all(x['rejected'] for x in c['refusal_controls']) and len(c['refusal_controls'])==3
            proof.update(full_complete_8_parent_24_suffix_scope_reconstructed=True,
                actual_Toy_post_denoise_and_final_latents_reloaded_in_registered_core=True,
                actual_Toy_files_retained_after_temporary_fixture=False,
                source_bound_full36_parent_equality_and_history_restore_verified=True,
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
