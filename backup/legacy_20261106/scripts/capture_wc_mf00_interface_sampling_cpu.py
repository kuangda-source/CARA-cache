#!/usr/bin/env python3
"""Capture native CPU artifacts and reconstruct the complete MF-00 denominator."""
import base64
import gzip
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    launch=json.loads(Path('reports/wc_mf00_interface_sampling_cpu_r1_launch_20261010.json').read_text())
    source='L='+repr(launch)+'\n'+r'''
import base64,gzip,hashlib,json,pathlib,sys
s=pathlib.Path(L['stage']);root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr')
r=json.loads((s/'receipt.json').read_text())
if 'exit_code' not in r:
 live=[r[k] for k in ('pid','child_pid') if k in r and pathlib.Path('/proc/'+str(r[k])).exists()]
 assert live, 'Receipt unfinished and handles missing; inspect without restart'
 print(json.dumps({'status':'VERIFIED_ORIGINAL_CPU_RUNNING','live_pids':live,'stage':str(s)}));sys.exit(0)
assert not any(pathlib.Path('/proc/'+str(r[k])).exists() for k in ('pid','child_pid'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files={}
for n in ('receipt.json','result.json','core.log','driver.log','launch.json','mf00-interface-sampling-preregistration.json'):
 raw=(s/n).read_bytes();files[n]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode()}
artifacts=[]
for p in sorted((s/'CPU-artifacts').rglob('*.pt')):
 artifacts.append({'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)})
print(json.dumps({'files':files,'artifacts':artifacts,'budget_sha256':sha(root/'reports/budget.json'),'original_pids_absent':[r['pid'],r['child_pid']]}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],input=source,text=True,capture_output=True,timeout=55)
    if call.returncode:raise RuntimeError(call.stderr[-4000:])
    captured=json.loads(call.stdout)
    if captured.get('status')=='VERIFIED_ORIGINAL_CPU_RUNNING':
        print(json.dumps(captured));return
    native={};prefix='reports/wc_mf00_interface_sampling_cpu_r1_terminal_20261010_'
    for name,record in captured['files'].items():
        packed=base64.b64decode(record['gzip_base64']);raw=gzip.decompress(packed)
        assert len(raw)==record['bytes'] and hashlib.sha256(raw).hexdigest()==record['sha256']
        Path(prefix+name+'.native.gz').write_bytes(packed)
        native[name]=json.loads(raw) if name.endswith('.json') else raw.decode()
    receipt=native['receipt.json'];result=native['result.json'];reg=native['mf00-interface-sampling-preregistration.json']
    assert receipt['exit_code']==receipt['child_exit_code']==0
    assert receipt['status']==result['status']=='MF00_INTERFACE_SAMPLING_CPU_NOT_REAL_MODEL'
    assert receipt['payload_after_sha256']==reg['payload_sha256']
    assert result['planned_scope']==receipt['planned_scope']==reg['CPU_scope']
    assert receipt['source_revision']==launch['source_revision']
    assert receipt['budget_before_sha256']==receipt['budget_after_sha256']==captured['budget_sha256']
    artifacts={a['path']:a for a in captured['artifacts']}
    successful=0;executed=0;guided=0;latents=0;refused=0;truncated=0;writer_failures=0
    checks=result['checks'];assert len(checks)==4
    assert {(r['flow'],r['scenario']) for r in checks}=={(f,s) for f in (False,True) for s in ('complete','last_vector_writer_failure')}
    for check in checks:
        state=check['receipt'];assert state['planned_paths']==state['planned_videos']==4
        assert state['initial_state_restored'] and len(state['requests'])==2
        for request in state['requests']:
            rows=request['paths'];assert len(rows)==2
            assert {(r['order'],r['observers'],r['repetition']) for r in rows}=={('ORIGINAL',False,'first'),('PAIRED',False,'first')}
            for row in rows:
                assert len(row['guided_sha256'])==len(row['solver_returns'])==len(row['actions'])==36
                assert row['counters']==list(range(0,70,2))+[0]
                assert [c['step'] for c in row['checkpoints']]==[13,21,33,35,36]
                assert not row['net_events']
                executed+=1
                if 'vector_artifact' in row:
                    a=row['vector_artifact'];actual=artifacts[a['path']]
                    assert (actual['bytes'],actual['sha256'])==(a['bytes'],a['sha256'])
            if check['status']=='PASS':
                left,right=rows
                for key in ('guided_sha256','actions','counters','block_visits','checkpoints','final_components','final_latent_sha256','final_solver_sha256','conditions_before','conditions_after','rng_after','sample_return_sha256','pipeline'):
                    assert left[key]==right[key],key
                assert left['video_artifact']['sha256']==right['video_artifact']['sha256']
        if check['status']=='PASS':
            successful+=4;guided+=check['actual_tensor_audit']['actual_guided_tensors_reloaded'];latents+=check['actual_tensor_audit']['actual_final_latents_reloaded']
            assert check['actual_tensor_audit']['all_direct_equal']
            refused+=len(check['semantic_mutation_refusals']);truncated+=int(check['actual_artifact_truncation_refused'])
        else:
            assert check['status']=='EXPECTED_FAILURE' and check['complete_scope_retained']
            assert state['requests'][-1]['paths'][-1]['status']=='TECH_BLOCKED_COMPLETE_SCOPE_RETAINED'
            writer_failures+=1
    assert (successful,executed,guided,latents,refused,truncated,writer_failures)==(8,16,288,8,24,2,2)
    audit={'status':'MF00_I_FULL_CPU_NATIVE_ARTIFACT_AND_DENOMINATOR_VERIFIED',
        'source_revision':launch['source_revision'],'exit_code':0,
        'complete_new_actual_batch_matrix_and_last_writer_failures_verified':True,
        'actual_Toy_guided_tensors_reloaded':guided,'actual_final_latents_reloaded':latents,
        'complete_executed_paths_including_last_writer_failures':executed,'successful_paths':successful,
        'semantic_mutation_refusals':refused,'actual_truncation_refusals':truncated,'last_writer_failures':writer_failures,
        'CPU_wall_seconds':receipt['CPU_wall_seconds'],'budget_sha256_unchanged':captured['budget_sha256'],
        'original_pids_absent':captured['original_pids_absent'],'files':{n:{k:v for k,v in x.items() if k!='gzip_base64'} for n,x in captured['files'].items()},
        'actual_tensor_files':captured['artifacts'],'GPU_submissions':0,'real_model_or_latency_or_endpoint_claim':False}
    Path(prefix+'capture.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('files','actual_tensor_files')}))


if __name__=='__main__':main()
