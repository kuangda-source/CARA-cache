"""Reuse the accepted image/venv as a private native control interpreter."""
import argparse,base64,hashlib,json,subprocess
from pathlib import Path
from wc_four_card_resource_cpu_r4 import ssh,write

CODE=r'''
import base64,hashlib,json,os,resource,subprocess,time
from pathlib import Path
d=json.load(__import__('sys').stdin);root=Path('/data20t/gaokuangda/worldcache_workspace');job=root/'bootstrap/wc-fourcard-native-control-python310-r1-20261022'
assert not job.exists(),'Recover the original native-control setup instead of replay'
stage=root/'.sync/wc-bank24-fourcard-full-execution-r2-20261022'
assert (stage/'stage-preparation-complete.json').is_file()
assert not (stage/'scout-GPU-dispatch-fence.json').exists() and not (stage/'scout-GPU-launch.json').exists()
pool=json.loads((root/'reports/gpu-budget-v2.json').read_text());assert 'wc-scout-dev6-paired-native-full24-r1' not in pool['jobs']
resource.setrlimit(resource.RLIMIT_AS,(16*(1<<30),16*(1<<30)));os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:2]))
job.mkdir(mode=0o700);(job/'usr-local').mkdir();(job/'lib').mkdir();(job/'bin').mkdir()
(job/'manifest.json').write_text(json.dumps(d['manifest'],indent=2)+'\n')
name='wc4-native-control-export-r1-20261022'
create=subprocess.run(['docker','create','--name',name,'--network','none','--read-only','--entrypoint','/bin/true',d['image']],capture_output=True,text=True,timeout=20)
assert create.returncode==0,create.stderr[-600:]
try:
 for source,target in [('/usr/local/.',job/'usr-local'),('/lib/x86_64-linux-gnu/.',job/'lib')]:
  q=subprocess.run(['docker','cp',name+':'+source,str(target)],capture_output=True,text=True,timeout=90);assert q.returncode==0,q.stderr[-600:]
finally:
 subprocess.run(['docker','rm',name],capture_output=True,timeout=20,check=True)
loader=job/'lib/ld-linux-x86-64.so.2';python=job/'usr-local/bin/python3.10'
assert loader.is_file() and python.is_file()
site=root/'envs/wc-cosmos-py310-cu128-r3/lib/python3.10/site-packages'
libs=[str(job/'lib'),str(job/'usr-local/lib'),str(site/'torch/lib')]+[str(p) for p in (site/'nvidia').glob('*/lib')]
script='#!/bin/sh\nexport PYTHONHOME='+str(job/'usr-local')+'\nexport PYTHONPATH='+str(site)+'${PYTHONPATH:+:$PYTHONPATH}\nexec '+str(loader)+' --library-path '+':'.join(libs)+' '+str(python)+' "$@"\n'
wrapper=job/'bin/python3';wrapper.write_text(script);wrapper.chmod(0o700)
env=dict(os.environ,PATH=str(job/'bin')+':'+os.environ['PATH'],CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void',USER='gaokuangda',LOGNAME='gaokuangda',PYTHONDONTWRITEBYTECODE='1')
env.pop('LD_PRELOAD',None)
probe="""import json,sys,torch\nfrom pathlib import Path\nsys.path.insert(0,STAGE)\nfrom four_card_bank24_execution_tools_r1 import validate_authorization\nauth=json.loads(Path(AUTH).read_text())\nreg,meta,quote,handoff=validate_authorization(ROOT,STAGE,auth)\nassert not torch.cuda.is_initialized()\nprint(json.dumps(dict(status='ACTUAL_NATIVE_PY310_TORCH_AND_ORIGINAL_FULL_AUTHORIZATION_CPU_PASS',python=sys.version.split()[0],torch=torch.__version__,CUDA_initialized=False,original_registration_sha256=auth['registration_sha256'],handoff=handoff,scope_counts=meta['scope_counts'])))\n"""
(job/'authorization.json').write_text(json.dumps(d['authorization'],indent=2)+'\n')
probe='STAGE='+repr(str(stage))+'\nROOT='+repr(str(root))+'\nAUTH='+repr(str(job/'authorization.json'))+'\n'+probe
q=subprocess.run([str(wrapper),'-c',probe],env=env,capture_output=True,text=True,timeout=120)
(job/'probe.stdout').write_text(q.stdout);(job/'probe.stderr').write_text(q.stderr)
result=dict(status='NATIVE_CONTROL_PYTHON_CPU_PASS' if q.returncode==0 else 'NATIVE_CONTROL_PYTHON_CPU_FAILED_RETAINED',observed_unix=time.time(),job=str(job),source_revision=d['manifest']['source_revision'],
 manifest_sha256=hashlib.sha256((job/'manifest.json').read_bytes()).hexdigest(),wrapper_sha256=hashlib.sha256(wrapper.read_bytes()).hexdigest(),
 python_sha256=hashlib.sha256(python.read_bytes()).hexdigest(),loader_sha256=hashlib.sha256(loader.read_bytes()).hexdigest(),
 exit_code=q.returncode,probe=json.loads(q.stdout) if q.returncode==0 else None,bounded_error=q.stderr[-5000:],
 container_export_removed=True,existing_image_and_venv_reused=True,host_shared_python_changed=False,GPU_submissions=0,CUDA_initialized=False,ledger_written=False)
(job/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
'''

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True,type=Path);a=p.parse_args();assert not a.output.exists()
 source=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
 l=json.loads(Path('reports/wc_four_card_BANK24_full24_GPU_R2_transport_launch_20261022.json').read_text())
 recipe=json.loads(Path('manifests/wc_four_card_bank24_full_execution_cpu_r2_20261022.json').read_text())
 m=dict(source_revision=source,existing_CPU_source='6d9cd4941d5b88aa01e87e5947a0a0d65fce7dad',existing_image=recipe['container_image_id'],control_only=True,GPU_submissions=0)
 r=ssh(CODE,dict(manifest=m,image=recipe['container_image_id'],authorization=l['authorization']),timeout=300);write(a.output,r)
 print(json.dumps(r))
if __name__=='__main__':main()
