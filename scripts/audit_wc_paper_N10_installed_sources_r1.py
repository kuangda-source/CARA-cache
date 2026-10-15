#!/usr/bin/env python3
"""Read installed evaluator source hashes without importing evaluators/models."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CODE=r'''
import hashlib,importlib.util,json,pathlib,sys,time
spec=importlib.util.find_spec('vbench');assert spec is not None
root=pathlib.Path(spec.origin).parent
names=('__init__.py','utils.py','subject_consistency.py','temporal_flickering.py','motion_smoothness.py','dynamic_degree.py','overall_consistency.py',
 'third_party/amt/cfgs/AMT-S.yaml','ViCLIP/bpe_simple_vocab_16e6.txt.gz')
files=[]
for name in names:
 p=root/name;row=dict(relative_path=name,path=str(p),exists=p.is_file())
 if p.is_file():
  raw=p.read_bytes();row.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
 files.append(row)
cache=pathlib.Path('/home/gaokuangda/.cache/vbench/ViCLIP')
print(json.dumps(dict(status='N10_INSTALLED_SOURCE_HASHES_ONLY_NOT_RUNTIME_ACCEPTANCE',observed_unix=time.time(),
 interpreter=sys.executable,vbench_root=str(root),files=files,
 ViCLIP_standard_directory_exists=cache.is_dir(),
 ViCLIP_checkpoint_in_standard_path=(cache/'ViClip-InternVid-10M-FLT.pth').is_file(),
 ViCLIP_tokenizer_in_standard_path=(cache/'bpe_simple_vocab_16e6.txt.gz').is_file(),
 models_imported=False,model_weights_read_or_downloaded=False,GPU_queries=False,
 original_N06_or_N05_stage_or_handles_read=False,server_files_written=False,GPU_submissions=0,ledger_written=False)))
'''

def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    r=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',PY+' -c '+shlex.quote(CODE)],capture_output=True,text=True,timeout=55)
    v=dict(transport_exit_code=r.returncode,stderr=r.stderr,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    if r.returncode==0:v['observation']=json.loads(r.stdout)
    else:v['stdout']=r.stdout
    a.output.write_text(json.dumps(v,indent=2)+'\n')
    print(json.dumps(dict(transport_exit_code=r.returncode,receipt=str(a.output),files=len(v.get('observation',{}).get('files',[])))))
    if r.returncode:raise SystemExit(r.returncode)

if __name__=='__main__':main()
