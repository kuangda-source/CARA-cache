#!/usr/bin/env python3
"""Complete only the two oversized identity files retained by the R1 audit."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

ROOT=Path(__file__).resolve().parents[1]
PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
CODE=r'''
import hashlib,json,pathlib,time
root=pathlib.Path('/home/gaokuangda/data/gkd/worldcache_omr').resolve()/'outputs'
tokens={n:[n.encode(),INPUT['prompt_sha256'][n].encode()] for n in INPUT['names']}
overlap=max(len(t) for ts in tokens.values() for t in ts)-1
rows=[];errors=[];started=time.time()
for name in INPUT['pending']:
 p=pathlib.Path(name)
 try:
  assert not p.is_symlink() and p.resolve().is_relative_to(root)
  assert not p.relative_to(root).parts[0].startswith('wc-paper-n10-')
  before=p.stat();assert before.st_size<=2*(1<<30),'Identity metadata exceeds2GiB bound'
  digest=hashlib.sha256();size=0;tail=b'';hits=set()
  with p.open('rb') as f:
   while True:
    block=f.read(1<<20)
    if not block:break
    assert time.time()-started<90,'Identity completion time bound'
    digest.update(block);size+=len(block);combined=tail+block
    for n,ts in tokens.items():
     if any(t in combined for t in ts):hits.add(n)
    tail=combined[-overlap:]
  after=p.stat();assert before.st_size==after.st_size==size and before.st_mtime_ns==after.st_mtime_ns
  rows.append(dict(path=name,bytes=size,sha256=digest.hexdigest(),identity_hits=sorted(hits)))
 except Exception as e:errors.append(dict(path=name,error_type=type(e).__name__,error=str(e)))
print(json.dumps(dict(status='SCOUT_DEV6_OVERSIZED_IDENTITY_FILES_COMPLETED',rows=rows,errors=errors,
 CPU_wall_seconds=time.time()-started,quality_values_extracted=False,ledger_written=False,GPU_submissions=0)))
'''


def main():
    p=argparse.ArgumentParser();p.add_argument('--R1',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();raw=a.R1.read_bytes();old=json.loads(raw);r=old['result']
    assert old['exit_code']==0 and not r['identity_hits']
    assert len(r['errors'])==2 and all(x['error']=='Metadata exceeds bounded identity audit size' for x in r['errors'])
    manifest=json.loads((ROOT/'plans/scouts_20261018/SCOUT_EXPL_DEV6_INPUTS.json').read_text())
    data=dict(names=r['names'],pending=[x['path'] for x in r['errors']],
        prompt_sha256={x['name']:x['prompt_sha256'] for x in manifest['selected_sources']})
    code='INPUT='+repr(data)+'\n'+CODE
    try:
        call=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',
            PY+' -c '+shlex.quote(code)],capture_output=True,timeout=110)
        result=json.loads(call.stdout) if call.returncode==0 else None
        accepted=(result is not None and not result['errors'] and len(result['rows'])==2
            and {x['path'] for x in result['rows']}==set(data['pending'])
            and all(not x['identity_hits'] for x in result['rows']))
        value=dict(status='SCOUT_DEV6_PROJECT_IDENTITY_AUDIT_R1_PLUS_R2',source_revision=subprocess.check_output(
            ['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),R1_ref=str(a.R1),R1_sha256=hashlib.sha256(raw).hexdigest(),
            input_manifest_sha256=r['input_manifest_sha256'],remote_code_sha256=hashlib.sha256(CODE.encode()).hexdigest(),
            result=result,exit_code=call.returncode,stderr=call.stderr.decode(),project_output_scope_accepted=accepted,
            external_or_unrecorded_exposure_proven=False,GPU_submissions=0,ledger_written=False)
    except (OSError,subprocess.TimeoutExpired,ValueError) as e:
        value=dict(status='SCOUT_DEV6_R2_IDENTITY_OBSERVATION_UNKNOWN',project_output_scope_accepted=False,
            R1_ref=str(a.R1),R1_sha256=hashlib.sha256(raw).hexdigest(),error_type=type(e).__name__,error=str(e),GPU_submissions=0)
    with a.output.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
    print(json.dumps({k:value.get(k) for k in ('status','project_output_scope_accepted','exit_code','GPU_submissions')}))
    raise SystemExit(0 if value['project_output_scope_accepted'] else 1)


if __name__=='__main__':main()
