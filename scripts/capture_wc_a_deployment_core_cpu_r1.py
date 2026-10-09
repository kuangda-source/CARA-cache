#!/usr/bin/env python3
"""Read original A CPU handles and bind the complete native result; no dispatch."""
import ast
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    L=json.loads(Path('reports/wc_a_deployment_core_cpu_r1_launch_20261010.json').read_text())
    code='L='+repr(L)+'\n'+r'''
import base64,gzip,hashlib,json,pathlib,time
stage=pathlib.Path(L['stage']);root=stage.parent.parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((stage/'receipt.json').read_text());pids=[r['pid'],r.get('child_pid')]
live=[p for p in pids if p and pathlib.Path('/proc/'+str(p)).exists()]
if live:
 print(json.dumps({'capture':{'status':'ORIGINAL_A_DEPLOYMENT_CORE_CPU_STILL_LIVE','PIDs':live},'native':{}}));raise SystemExit(0)
assert r['pid']==L['supervisor_pid'] and r['source_revision']==L['source_revision']
assert sha(stage/'driver.py')==L['driver_sha256'] and sha(stage/'registration.json')==L['registration_sha256']
reg=json.loads((stage/'registration.json').read_text())
assert {n:sha(stage/n) for n in reg['payload_sha256']}==r['payload_after_sha256']==reg['payload_sha256']
assert {n:sha(root/'runtime'/n) for n in reg['runtime_source_sha256']}==reg['runtime_source_sha256']
assert r['GPU_submissions']==0 and not r['ledger_written'] and not r['GPU_lock_acquired']
files=['receipt.json','registration.json','launch.json','driver.py','driver.log','test.log']
if (stage/'result.json').exists():files.append('result.json')
files.extend(str(p.relative_to(stage)) for p in sorted((stage/'controlled-artifacts').rglob('*.pt')))
native={}
for n in files:
 p=stage/n;raw=p.read_bytes();packed=gzip.compress(raw,mtime=0)
 native[n]={'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'compressed_sha256':hashlib.sha256(packed).hexdigest(),'base64':base64.b64encode(packed).decode()}
print(json.dumps({'capture':{'status':'A_DEPLOYMENT_CORE_ORIGINAL_NATIVE_CPU_TERMINAL','source_revision':L['source_revision'],
 'original_PIDs_absent':pids,'exit_code':r['exit_code'],'CPU_wall_seconds':r['CPU_wall_seconds'],
 'GPU_submissions':0,'ledger_written':False,'observed_unix':time.time()},'native':native}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=code,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-3000:])
    value=json.loads(call.stdout)
    if not value['native']:print(json.dumps(value['capture']));return 2
    prefix='reports/wc_a_deployment_core_cpu_r1_terminal_20261010_';dest=Path(prefix+'capture.json');assert not dest.exists()
    proof=value['capture'];proof['files']={};objects={}
    for n,item in value['native'].items():
        packed=base64.b64decode(item['base64'],validate=True);raw=gzip.decompress(packed)
        assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256'] and hashlib.sha256(packed).hexdigest()==item['compressed_sha256']
        p=Path(prefix+n.replace('/','__')+'.native.gz');assert not p.exists();p.write_bytes(packed)
        proof['files'][n]={k:v for k,v in item.items() if k!='base64'};proof['files'][n]['local_path']=str(p)
        if n.endswith('.json'):objects[n]=json.loads(raw)
    try:
        assert objects['launch.json']==L
        gitreg=subprocess.check_output(['git','show',L['source_revision']+':manifests/wc_a_deployment_core_cpu_r1_preregistration_20261010.json'])
        assert hashlib.sha256(gitreg).hexdigest()==L['registration_sha256'] and json.loads(gitreg)==objects['registration.json']
        for n,digest in objects['registration.json']['payload_sha256'].items():
            raw=subprocess.check_output(['git','show',L['source_revision']+':'+n]);assert hashlib.sha256(raw).hexdigest()==digest
        deploy=subprocess.check_output(['git','show',L['source_revision']+':scripts/deploy_wc_a_deployment_core_cpu_r1.py'])
        driver=[n.value for n in ast.parse(deploy).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='DRIVER' for t in n.targets)]
        assert len(driver)==1 and hashlib.sha256(ast.literal_eval(driver[0]).encode()).hexdigest()==L['driver_sha256']
        if proof['exit_code']==0:
            r=objects['receipt.json'];v=objects['result.json']
            assert r['child_exit_code']==0 and proof['files']['result.json']['sha256']==r['result_sha256']
            assert v['status']=='A_DEPLOYMENT_FULL36_CONTROLLED_CPU_PASS_NOT_UNIPC_OR_VIDEO'
            assert len(v['complete_paths'])==16 and v['actual_tensors_reloaded']==592
            assert (v['actual_complete_pairs'],v['actual_normal_net_calls'])==(576,1152)
            assert v['both_flow_OFF_direct_source_parity'] and v['RA_prior_is_explicit_Toy_not_real_CAL']
            assert len(v['invalid_method_horizon_refused'])==4 and v['registered_second_branch_failure']['completed_pairs']==29
            assert v['registered_second_branch_failure']['poisoned_no_resume'] and v['registered_second_branch_failure']['complete_scope_retained']
            for flow in (False,True):
                rows=[x for x in v['complete_paths'] if x['flow']==flow]
                assert len(rows)==8
                methods=['SOURCE_BASE','OFF','W1_GLOBAL_1','BETA1_GLOBAL_1','W1_ONE_PHASE','BETA1_ONE_PHASE','OFF','W1_ONE_PHASE']
                assert [x['method'] for x in rows]==methods and [x['selector'] for x in rows]==['D6']*6+['RA_TOY_PRIOR']*2
                assert rows[0]['guided_sha256']==rows[1]['guided_sha256'] and rows[0]['final_latent_sha256']==rows[1]['final_latent_sha256']
                for row in rows:
                    assert row['completed_pairs']==36 and row['actual_tensors_reloaded']==37
                    item=proof['files']['controlled-artifacts/'+Path(row['path']).name]
                    assert item['sha256']==row['sha256'] and item['bytes']==row['bytes']
                    if row['summary'] is not None:
                        assert row['summary']['teacher_calls']==row['summary']['extra_candidate_deep_blocks']==0
                        assert len(row['summary']['history'])==len(row['actual_post_RF_checks'])==36
                        for h in row['summary']['history']:
                            expected=0 if row['method']=='OFF' else (.5 if row['method'].endswith('ONE_PHASE') and h['step']>=25 else 1)
                            assert h['shared_alpha']==expected and h['post_RF_fusion'] and not h['C_readout_updates_D_anchor']
                            assert h['teacher_calls']==h['extra_deep_blocks']==0
                            assert all(all(a<=h['step'] if h['action']=='DD' else a<h['step'] for a in history) for history in h['past_D_steps'])
            assert not v['CUDA_initialized'] and v['GPU_submissions']==0 and not v['actual_UniPC_or_Cosmos_weights_or_video_or_quality_or_latency_claim']
        proof['independent_source_and_complete_result_verified']=True
    except BaseException as e:
        proof['independent_check_error']={'type':type(e).__name__,'message':str(e)};dest.write_text(json.dumps(proof,indent=2)+'\n');raise
    dest.write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='files'}));return 0


if __name__=='__main__':raise SystemExit(main())
