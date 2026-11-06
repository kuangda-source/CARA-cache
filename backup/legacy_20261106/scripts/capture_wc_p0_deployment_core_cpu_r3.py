#!/usr/bin/env python3
"""Read the original P0 CPU handles and independently reload all26 files.

No dispatch, remote writes, GPU lock, real weights or metric execution. Native
receipts/logs are retained locally; Toy tensor files remain on the server.
"""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    launch_ref = 'reports/wc_p0_deployment_core_cpu_r3_launch_20261010.json'
    L = json.loads(Path(launch_ref).read_text())
    code = 'L='+repr(L)+'\n'+r'''
import base64,gzip,hashlib,json,os,pathlib,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_P0_CPU_HANDLES_STILL_LIVE','live_PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert sha(stage/'driver.py')==L['driver_sha256'] and sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text())
assert {n:sha(stage/n) for n in reg['payload_sha256']}==reg['payload_sha256']==r['payload_after_sha256']
assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
assert r['GPU_submissions']==0 and not r['ledger_written'] and not r['GPU_lock_acquired']
assert r['budget_before_sha256']==r['budget_after_sha256']==sha(root/'reports/budget.json')
artifacts=[];tensor_checks={}
if r['exit_code']==0:
 assert r['child_exit_code']==0 and sha(stage/'result.json')==r['result_sha256']
 v=json.loads((stage/'result.json').read_text());assert len(v['complete_paths'])==26
 os.environ['CUDA_VISIBLE_DEVICES']=''
 import torch
 assert not torch.cuda.is_initialized()
 def forbidden(*a,**kw):raise RuntimeError('P0 capture forbids CUDA')
 torch.cuda._lazy_init=forbidden
 def tensor_hash(t):
  h=hashlib.sha256(str((list(t.shape),str(t.dtype))).encode())
  h.update(t.detach().contiguous().reshape(-1).view(torch.uint8).numpy().tobytes());return h.hexdigest()
 loaded={}
 for row in v['complete_paths']:
  path=pathlib.Path(row['path']).resolve();assert path.parent==(stage/'controlled-artifacts').resolve()
  assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256']
  x=torch.load(path,map_location='cpu',weights_only=True)
  assert set(x)=={'guided','final_latent'} and len(x['guided'])==36
  assert all(tuple(t.shape)==(1,8,2,8,8) and t.dtype==torch.float32 and t.device.type=='cpu' and bool(torch.isfinite(t).all()) for t in x['guided']+[x['final_latent']])
  assert [tensor_hash(t) for t in x['guided']]==row['guided_sha256'] and tensor_hash(x['final_latent'])==row['final_latent_sha256']
  key=(row['flow'],row['method'],row['independent_reference']);assert key not in loaded;loaded[key]=x
  artifacts.append({'recorded_path':row['path'],'resolved_path':str(path),'bytes':row['bytes'],'sha256':row['sha256'],'actual_reloaded_tensors':37})
 assert len(list((stage/'controlled-artifacts').glob('*.pt')))==26
 for flow in (False,True):
  source=loaded[(flow,'SOURCE_BASE',False)];full=loaded[(flow,'TRUE_D_REFERENCE',False)]
  for method in ('OFF','DENSE_CONTROL','FULL_P_DECLARED_P'):
   expected=full if method=='FULL_P_DECLARED_P' else source;actual=loaded[(flow,method,False)]
   assert all(torch.equal(a,b) for a,b in zip(actual['guided'],expected['guided'])) and torch.equal(actual['final_latent'],expected['final_latent'])
  for method in ('ROTATION_050','RANDOM_050','ROTATION_075','RANDOM_075'):
   actual=loaded[(flow,method,False)];reference=loaded[(flow,method,True)]
   for a,b in zip(actual['guided'],reference['guided']):torch.testing.assert_close(a,b,rtol=1e-5,atol=2e-6)
   torch.testing.assert_close(actual['final_latent'],reference['final_latent'],rtol=1e-5,atol=2e-6)
 assert not torch.cuda.is_initialized()
 tensor_checks={'actual_independent_reloaded_tensors':962,'all26_shapes_bytes_and_output_hashes_verified':True,'both_flow_source_and_full_P_controls_direct_equal':True,'all8_partial_complete_trajectory_independent_reference_close':True,'registered_CPU_reference_rtol':1e-5,'registered_CPU_reference_atol':2e-6,'CUDA_initialized':False}
 assert sha(root/'reports/budget.json')==r['budget_after_sha256']
files=['receipt.json','registration.json','launch.json','driver.py','driver.log','test.log']
if (stage/'result.json').exists():files.append('result.json')
native={}
for n in files:
 raw=(stage/n).read_bytes();packed=gzip.compress(raw,mtime=0)
 native[n]={'path':str(stage/n),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'gzip_base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':{'status':'ORIGINAL_P0_DEPLOYMENT_CPU_R3_TERMINAL','source_revision':L['source_revision'],'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],'budget_unchanged':True,'GPU_submissions':0,'actual_artifact_bindings':artifacts,'independent_tensor_reload':tensor_checks,'observed_unix':time.time()},'native':native}))
'''
    call = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=15',
        'gkd_minchen', '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -'],
        input=code, text=True, capture_output=True, timeout=55)
    if call.returncode:
        raise RuntimeError(call.stderr[-4000:])
    value = json.loads(call.stdout)
    if not value['native']:
        print(json.dumps(value['capture']))
        return 2
    prefix = 'reports/wc_p0_deployment_core_cpu_r3_terminal_20261010_'
    target = Path(prefix+'capture.json')
    assert not target.exists()
    proof = value['capture']; proof['files'] = {}; objects = {}
    for name, item in value['native'].items():
        packed = base64.b64decode(item['gzip_base64'], validate=True)
        raw = gzip.decompress(packed)
        assert len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256']
        path = Path(prefix+name+'.native.gz'); assert not path.exists(); path.write_bytes(packed)
        proof['files'][name] = {k: v for k, v in item.items() if k != 'gzip_base64'}
        proof['files'][name]['local_path'] = str(path)
        if name.endswith('.json'):
            objects[name] = json.loads(raw)
    try:
        reg_ref = 'manifests/wc_p0_deployment_core_cpu_r3_preregistration_20261010.json'
        assert objects['launch.json'] == L
        committed_reg = subprocess.check_output(['git', 'show', L['source_revision']+':'+reg_ref])
        assert hashlib.sha256(committed_reg).hexdigest() == L['registration_sha256']
        assert json.loads(committed_reg) == objects['registration.json']
        for name, digest in objects['registration.json']['payload_sha256'].items():
            raw = subprocess.check_output(['git', 'show', L['source_revision']+':'+name])
            assert hashlib.sha256(raw).hexdigest() == digest
        deploy = subprocess.check_output(['git', 'show', L['source_revision']+':scripts/deploy_wc_p0_deployment_core_cpu_r3.py'])
        driver = [n.value for n in ast.parse(deploy).body if isinstance(n, ast.Assign)
                  and any(isinstance(t, ast.Name) and t.id == 'DRIVER' for t in n.targets)]
        assert len(driver) == 1 and hashlib.sha256(ast.literal_eval(driver[0]).encode()).hexdigest() == L['driver_sha256']
        if proof['exit_code'] == 0:
            v = objects['result.json']
            assert v['status'] == 'P0_DEPLOYMENT_FULL36_PINNED_BLOCK_CPU_PASS_NOT_UNIPC_OR_VIDEO'
            assert (len(v['complete_paths']), v['actual_complete_pairs'],
                    v['actual_normal_net_calls'], v['actual_tensors_reloaded']) == (26, 936, 1872, 962)
            assert len(proof['actual_artifact_bindings']) == 26
            assert proof['independent_tensor_reload']['actual_independent_reloaded_tensors'] == 962
            D = list(range(1, 8))+[13, 19, 25, 31, 36]; P = [12, 18, 24, 30]
            expected_methods = ['SOURCE_BASE', 'TRUE_D_REFERENCE', 'OFF', 'DENSE_CONTROL',
                'ROTATION_050', 'ROTATION_050', 'RANDOM_050', 'RANDOM_050',
                'ROTATION_075', 'ROTATION_075', 'RANDOM_075', 'RANDOM_075', 'FULL_P_DECLARED_P']
            for flow in (False, True):
                rows = [x for x in v['complete_paths'] if x['flow'] == flow]
                assert [x['method'] for x in rows] == expected_methods
                for row in rows:
                    assert row['completed_pairs'] == 36 and row['actual_tensors_reloaded'] == 37
                    method = row['method']; partial = method not in ('SOURCE_BASE', 'OFF', 'DENSE_CONTROL')
                    deep = D+(P if partial else [])
                    observations = row['actual_Linear_input_rows']
                    assert len(observations) == len(deep)*16
                    assert sorted(set(x[0] for x in observations)) == sorted(deep)
                    assert len(set(tuple(x[:4]) for x in observations)) == len(observations)
                    for step, slot, layer, linear, count in observations:
                        assert slot in (0, 1) and layer in (4, 10, 16, 22) and linear in ('layer1', 'layer2')
                        expected = (64 if method.endswith('050') else 96) if (
                            step in P and not row['independent_reference']
                            and method not in ('TRUE_D_REFERENCE', 'FULL_P_DECLARED_P')) else 128
                        assert count == expected
                    summary = row['summary']
                    if summary is None:
                        continue
                    assert summary['completed_pairs'] == 36 and len(summary['history']) == 36
                    assert summary['teacher_calls'] == summary['extra_candidate_heads'] == 0
                    assert not summary['source_risk_RA_policy_implemented']
                    for h in summary['history']:
                        step = h['step']; kind = 'D' if step in D else 'P' if partial and step in P else 'C'
                        assert h['action'] == kind*2 and h['physical_continuation'] == ('CC' if kind == 'C' else 'DD')
                        assert not h['P_updates_true_D_or_zero_risk_RA_anchor']
                        if kind != 'D':
                            assert h['true_D_after'] == h['true_D_before']
                        if kind == 'P':
                            assert h['working_source_ages'] == [0, 0]
                            assert all(x['kind'] == 'P' and x['creation_error'] == 'UNKNOWN_NOT_ZERO'
                                and not x['RA_zero_risk_reset_allowed'] for x in h['working_sources'])
            failures = v['registered_both_flow_second_branch_failures']
            assert [f['flow'] for f in failures] == [False, True]
            assert all(f['planned_pairs'] == 36 and f['completed_pairs'] == 29
                and f['failure_step'] == 30 and f['failure_slot'] == 1
                and f['projection_cache_transaction_rolled_back'] and f['working_and_D_ledger_not_committed']
                and f['poisoned_no_resume'] and not f['whole_WC_or_solver_fault_rollback_claim'] for f in failures)
            assert not v['CUDA_initialized'] and v['GPU_submissions'] == 0
            assert not v['actual_UniPC_or_Cosmos_weights_or_video_or_quality_or_latency_claim']
        proof['independent_committed_sources_all_scope_and_actual_tensor_bindings_verified'] = True
    except BaseException as error:
        proof['independent_check_error'] = {'type': type(error).__name__, 'message': str(error)}
        target.write_text(json.dumps(proof, indent=2)+'\n')
        raise
    target.write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps({k: v for k, v in proof.items() if k not in ('files', 'actual_artifact_bindings')}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
