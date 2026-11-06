"""Read the original isolated CPU stage; hashes and full receipts, no mutations."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
HOST = ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15',
    '-o','ClearAllForwardings=yes','gkd_minchen']


def main():
    p=argparse.ArgumentParser(); p.add_argument('--suffix',default='r1')
    args=p.parse_args()
    launch=ROOT/('reports/wc_teacher_first_velocity_cpu_'+args.suffix+'_launch_20261013.json')
    bound=json.loads(launch.read_text())
    code='S='+repr(bound['stage'])+'\nP='+repr(bound['CPU_pid'])+'\n'+r'''import pathlib,json,hashlib,time
s=pathlib.Path(S); sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
reg=json.loads((s/'registration.json').read_text())
r={'stage':str(s),'observed_unix':time.time(),'CPU_pid':P,
 'CPU_pid_live':pathlib.Path('/proc',str(P)).exists(),
 'source_revision':reg['source_revision'],'registration_sha256':sha(s/'registration.json'),
 'payload_files':len(reg['payload_sha256']),
 'payload_all_verified':all(sha(s/n)==h for n,h in reg['payload_sha256'].items()),
 'CPU_log_sha256':sha(s/'CPU.log'),'CPU_log_tail':'\n'.join((s/'CPU.log').read_text(errors='replace').splitlines()[-12:])}
for key,name in [('result','CPU-result.json'),('failure','CPU-result.failure.json')]:
 f=s/name
 if f.exists():r[key]=json.loads(f.read_text());r[key+'_sha256']=sha(f)
print(json.dumps(r,allow_nan=False))
'''
    compile(code,'readonly_CPU_receipt','exec')
    value=json.loads(subprocess.check_output(HOST+['python3 -'],input=code,text=True))
    assert value['source_revision']==bound['source_revision'] and value['payload_all_verified']
    raw=ROOT/'.sync'/('wc_teacher_first_velocity_CPU_'+args.suffix+'_full_20261013.json')
    raw.parent.mkdir(exist_ok=True)
    raw.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    result=value.pop('result',None)
    receipt=dict(value,full_local_ref=str(raw),
        full_local_sha256=hashlib.sha256(raw.read_bytes()).hexdigest(),
        GPU_submissions=0,ledger_written=False)
    if result is not None:
        assert result['GPU_submissions']==0 and not result['CUDA_initialized']
        checks=result['checks']
        assert result['actual_CPU_parents']==24 and result['endpoint_suffixes']==32 and result['teacher_pairs']==8
        assert {c['flow'] for c in checks}=={False,True} and len(checks)==2
        rows=[r for c in checks for r in c['checks']]
        assert len(rows)==8 and all(c['ordinary_initial_state_restored'] and c['four_cells'] for c in checks)
        keys=('ordinary_and_old_and_new_parent_complete_equal','new_C_and_original_C_full_suffix_equal',
            'teacher_first_guided_raw_exact','teacher_not_committed','one_teacher_pair_and_one_velocity_injection')
        assert all(all(r[k] for k in keys) for r in rows)
        receipt.update(status=result['status'],CPU_wall_seconds=result['CPU_wall_seconds'],
            CUDA_initialized=result['CUDA_initialized'],actual_CPU_parents=24,
            endpoint_suffixes=32,teacher_pairs=8,all_parent_C_teacher_controls_passed=True,
            flows=[{'flow':c['flow'],'complete_CPU_parents':c['complete_CPU_parents'],
                'endpoint_suffixes':c['endpoint_suffixes'],
                'points':[{'point':r['point'],'actual_diagnostic_pairs':r['actual_diagnostic_pairs'],
                    **{k:r[k] for k in keys}} for r in c['checks']]} for c in checks])
    else:
        receipt['status']='CPU_FAILED_NOT_GPU' if value.get('failure') else 'CPU_RUNNING_NOT_GPU'
    out=ROOT/('reports/wc_teacher_first_velocity_cpu_'+args.suffix+'_receipt_20261013.json')
    out.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:receipt.get(k) for k in ('status','CPU_pid_live','CPU_wall_seconds',
        'payload_files','GPU_submissions','actual_CPU_parents','endpoint_suffixes','teacher_pairs')}))


if __name__=='__main__':
    main()
