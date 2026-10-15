#!/usr/bin/env python3
"""Scoped cache/package metadata via the actual generation Python; no models."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CODE=r'''
import importlib.metadata as md,importlib.util,json,pathlib,sys,time
base=pathlib.Path('/home/gaokuangda/.cache');packages={}
for name in ('torch','torchvision','vbench','pyiqa','decord','opencv-python','av','clip','transformers'):
 try:packages[name]=md.version(name)
 except md.PackageNotFoundError:packages[name]=None
paths=[base/'vbench'/n for n in ('amt_model','raft_model','pyiqa_model','dino_model','clip_model','ViCLIP')]
paths.extend([base/'torch/hub/checkpoints',base/'clip'])
files=[];directories=[]
for directory in paths:
 directories.append(dict(path=str(directory),exists=directory.is_dir()))
 if directory.is_dir():
  for p in sorted(directory.rglob('*')):
   if p.is_file() and p.suffix.lower() in ('.pth','.pt','.safetensors','.yaml','.json'):
    s=p.stat();files.append(dict(path=str(p),bytes=s.st_size,mtime_ns=s.st_mtime_ns,sha256=None))
specs={}
for name in ('vbench','clip','pyiqa'):
 spec=importlib.util.find_spec(name);specs[name]=spec.origin if spec else None
print(json.dumps(dict(status='N10_GENERATION_ENV_STATIC_METADATA_NOT_MODEL_OR_GPU_VALIDATION',observed_unix=time.time(),
 interpreter=sys.executable,python_version=sys.version,packages=packages,import_specs=specs,directories=directories,files=files,
 torch_hub_dino_source_cached=(base/'torch/hub/facebookresearch_dino_main/hubconf.py').is_file(),
 runtime_or_models_imported=False,model_weights_read_or_hashed=False,downloads=False,GPU_queries=False,
 original_N06_or_N05_stage_or_handles_read=False,server_files_written=False,GPU_submissions=0,ledger_written=False,
 scope='Explicit cache paths in the actual Cosmos generation Python. Missing here is not machine-wide absence. Metadata is not resource hash or runtime acceptance.')))
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    command=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(CODE)]
    r=subprocess.run(command,capture_output=True,text=True,timeout=55)
    value=dict(transport_exit_code=r.returncode,stderr=r.stderr,expected_remote_interpreter=PY,
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if r.returncode==0:value['observation']=json.loads(r.stdout)
    else:value['stdout']=r.stdout
    a.output.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(transport_exit_code=r.returncode,receipt=str(a.output),
        packages=value.get('observation',{}).get('packages'),cache_files=len(value.get('observation',{}).get('files',[])))))
    if r.returncode:raise SystemExit(r.returncode)

if __name__=='__main__':main()
