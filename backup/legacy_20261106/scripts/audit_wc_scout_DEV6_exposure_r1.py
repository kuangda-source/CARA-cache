#!/usr/bin/env python3
"""Bounded prompt-identity audit only; no model, quality journal or task polling."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CODE=r'''
import hashlib,json,os,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve();output=root/'outputs'
started=time.time();files=[];hits=[];errors=[];skipped=[];visited=0
for directory,subdirs,names in os.walk(output,followlinks=False):
 p=pathlib.Path(directory)
 # N10 only evaluates the already excluded N07 inputs. Do not open its
 # quality journal or runner science here; its original collection is separate.
 if p.parent==output and p.name.startswith('wc-paper-n10-'):
  skipped.append(dict(path=str(p),reason='N10_known_N07_scoring_only_not_new_generation'));subdirs[:]=[];continue
 if time.time()-started>60:
  errors.append(dict(path=str(p),error='BOUNDED_IDENTITY_SCAN_TIME_LIMIT'));break
 visited+=1
 for name in INPUT['names']:
  if name in str(p):hits.append(dict(name=name,path=str(p),location='OUTPUT_PATH'))
 for filename in ('runner.json','receipt.json','supervisor.json'):
  q=p/filename
  if filename not in names:continue
  try:
   if q.is_symlink() or not q.resolve().is_relative_to(output):raise ValueError('Metadata path escapes outputs')
   if q.stat().st_size>32*(1<<20):raise ValueError('Metadata exceeds bounded identity audit size')
   raw=q.read_bytes();text=raw.decode();digest=hashlib.sha256(raw).hexdigest()
   files.append(dict(path=str(q),bytes=len(raw),sha256=digest))
   for name in INPUT['names']:
    if name in text or INPUT['prompt_sha256'][name] in text:
     hits.append(dict(name=name,path=str(q),location='IDENTITY_STRING_ONLY'))
  except Exception as e:errors.append(dict(path=str(q),error_type=type(e).__name__,error=str(e)))
result=dict(status='SCOUT_DEV6_FRESH_PROJECT_OUTPUT_IDENTITY_AUDIT',observed_unix=time.time(),
 names=INPUT['names'],input_manifest_sha256=INPUT['input_manifest_sha256'],metadata_files=files,
 visited_directories=visited,identity_hits=hits,errors=errors,skipped_N10_scoring_only=skipped,
 project_output_scope_accepted=not errors and not hits,external_or_unrecorded_exposure_proven=False,
 quality_scores_read=False,new_GPU_submissions=0,model_loads=0,ledger_written=False,CPU_wall_seconds=time.time()-started)
print(json.dumps(result,allow_nan=False))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists()
    ref='plans/scouts_20261018/SCOUT_EXPL_DEV6_INPUTS.json';raw=(ROOT/ref).read_bytes();value=json.loads(raw)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    assert subprocess.check_output(['git','show',revision+':'+ref],cwd=ROOT)==raw
    inputs=dict(names=[r['name'] for r in value['selected_sources']],input_manifest_sha256=hashlib.sha256(raw).hexdigest(),
        prompt_sha256={r['name']:r['prompt_sha256'] for r in value['selected_sources']})
    for r in value['selected_sources']:
        assert hashlib.sha256((ROOT/r['source_ref']).read_bytes()).hexdigest()==r['source_sha256']
    code='INPUT='+repr(inputs)+'\n'+CODE
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',
            PY+' -c '+shlex.quote(code)],capture_output=True,timeout=90)
        data=json.loads(call.stdout) if call.returncode==0 else None
        result=dict(status='SCOUT_DEV6_FRESH_IDENTITY_RESPONSE',source_revision=revision,exit_code=call.returncode,
            remote_code_sha256=hashlib.sha256(CODE.encode()).hexdigest(),input_manifest_ref=ref,
            input_manifest_sha256=inputs['input_manifest_sha256'],result=data,stderr=call.stderr.decode(),GPU_submissions=0)
    except (OSError,subprocess.TimeoutExpired,ValueError) as e:
        result=dict(status='SCOUT_DEV6_IDENTITY_OBSERVATION_UNKNOWN_NOT_UNEXPOSED',error_type=type(e).__name__,error=str(e),GPU_submissions=0)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    accepted=(result.get('result') or {}).get('project_output_scope_accepted') is True
    print(json.dumps(dict(output=str(a.output),accepted=accepted,GPU_submissions=0)))
    raise SystemExit(0 if accepted else 1)


if __name__=='__main__':main()
