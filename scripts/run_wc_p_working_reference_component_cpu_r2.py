"""Install seven pinned CPU-only component files in a fresh isolated stage."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    root=Path(__file__).resolve().parents[1]
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    manifest=root/'manifests/wc_p_working_reference_component_cpu_r2_20261011.json'
    reg=json.loads(manifest.read_text());payload={}
    for n,h in reg['payload_sha256'].items():
        raw=(root/n).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==h
        assert raw==subprocess.check_output(['git','show',revision+':'+n],cwd=root)
        payload[n]=base64.b64encode(raw).decode()
    assert manifest.read_bytes()==subprocess.check_output(['git','show',revision+':'+str(manifest.relative_to(root))],cwd=root)
    packet={'registration':reg,'source_revision':revision,'files':payload}
    code='P='+repr(packet)+'\n'+r'''import os,base64,hashlib,json,pathlib,subprocess,time
project=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr');stage=project/'.sync'/P['registration']['stage_name']
assert not stage.exists();stage.mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=sha(project/'reports/budget.json')
for n,b in P['files'].items():
    q=stage/n;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(base64.b64decode(b))
assert {n:sha(stage/n) for n in P['files']}==P['registration']['payload_sha256']
(stage/'registration.json').write_text(json.dumps(P['registration'],indent=2)+'\n')
driver=r"""import sys,torch,json
torch.set_num_threads(2)
def forbidden(*a,**k):raise RuntimeError('P component denies CUDA, weights and download')
torch.cuda._lazy_init=forbidden;torch.load=forbidden;torch.hub.download_url_to_file=forbidden
from check_p_working_reference_residual_cpu_r2 import run
v=run();assert not torch.cuda.is_initialized();print(json.dumps(v))
"""
py='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
started=time.monotonic()
child=subprocess.run([py,'-c',driver],text=True,capture_output=True,
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',
        PYTHONPATH=str(stage/'src')+':'+str(stage/'tests'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1'))
(stage/'CPU.log').write_text(child.stdout+child.stderr)
after={n:sha(stage/n) for n in P['files']}
assert after==P['registration']['payload_sha256'] and sha(project/'reports/budget.json')==before
receipt={'source_revision':P['source_revision'],'supervisor_PID':os.getpid(),'exit_code':child.returncode,
    'CPU_wall_seconds':time.monotonic()-started,'payload_after_sha256':after,
    'budget_before_and_after_sha256':before,'GPU_submissions':0,'ledger_written':False,
    'observed_unix':time.time(),'stage':str(stage)}
if child.returncode==0:
    value=json.loads(child.stdout)
    assert len(value['successful_modes'])==2 and len(value['fallbacks'])==7 and value['foreign_D_refused']
    (stage/'result.json').write_text(json.dumps(value,indent=2)+'\n')
    receipt['result_sha256']=sha(stage/'result.json');receipt['status']='COMPONENT_CPU_PASS_NOT_FULL_SAMPLER'
else:
    value={'retained_original_log':child.stdout+child.stderr};receipt['status']='COMPONENT_CPU_FAILED_RETAINED'
(stage/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({'receipt':receipt,'component':value,'original_log':child.stdout+child.stderr}))
'''
    call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','gkd_minchen','python3 -'],
                        input=code,text=True,capture_output=True)
    if call.returncode:raise RuntimeError(call.stderr[-3500:])
    value=json.loads(call.stdout)
    p=root/'reports/wc_p_working_reference_component_cpu_r2_20261011.json';assert not p.exists()
    p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps(value['receipt']))


if __name__=='__main__':main()
