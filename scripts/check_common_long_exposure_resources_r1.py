"""Read-only dual-host metadata inventory and resource snapshot; no admission."""
import argparse,hashlib,json
from pathlib import Path
from cara_two_card_transport_r1 import ssh,four_ssh
ROOT=Path(__file__).resolve().parents[1]
CODE=r'''
import os,json,time,hashlib,subprocess,pathlib
p=json.load(__import__('sys').stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
def command(cmd):
 r=subprocess.run(cmd,text=True,capture_output=True,timeout=45);return dict(exit_code=r.returncode,stdout=r.stdout[:24000],stderr=r.stderr[:1000])
def disk(path):
 s=os.statvfs(path);return dict(path=str(path),available_bytes=s.f_bavail*s.f_frsize,free_inodes=s.f_favail,device=os.stat(path).st_dev)
rows=[];skipped=[];seen=0;digest=hashlib.sha256()
# Only metadata filenames; no tensor/video/scientific-score reads.
allowed={'registration.json','manifest.json','asset-manifest.json','collection-verified.json','B1-assets.json','request.json','runner.json','collection.json','B1-results.json','scout-assets.json'}
for base in (root/'.sync',root/'outputs'):
 for current,dirs,files in os.walk(base,followlinks=False):
  dirs[:]=[d for d in dirs if d not in ('cache','runtime','CPU-caches','CPU-numeric','envs','.git','huggingface','torchinductor','triton') and not (pathlib.Path(current)/d).is_symlink()]
  for name in files:
   if name not in allowed and not name.endswith('-config.json') and 'requests' not in name:continue
   if not name.endswith('.json'):continue
   f=pathlib.Path(current)/name
   try:
    before=f.stat()
    if f.is_symlink():skipped.append(str(f));continue
    if before.st_size>8*2**20:
     hh=hashlib.sha256();hits=set();common=False;carry=b''
     with f.open('rb') as stream:
      for block in iter(lambda:stream.read(2**20),b''):
       hh.update(block);search=carry+block;carry=search[-512:]
       hits.update(n for n in p['names'] if n.encode() in search);common=common or b'R4_COMMON_LONG' in search
     after=f.stat()
     if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):skipped.append(str(f));continue
     h=hh.hexdigest();seen+=1;digest.update((str(f)+h).encode())
     if hits or common:rows.append(dict(path=str(f),sha256=h,target_names=sorted(hits),common_long_mentioned=common,CPU_namespace=('cpu' in str(f).lower()),bytes=before.st_size,streamed_byte_marker_scan=True))
     continue
    raw=f.read_bytes();v=json.loads(raw);after=f.stat()
    if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):skipped.append(str(f));continue
    h=hashlib.sha256(raw).hexdigest();seen+=1;digest.update((str(f)+h).encode())
    hits=[n for n in p['names'] if n.encode() in raw]
    common=b'R4_COMMON_LONG' in raw
    if hits or common:rows.append(dict(path=str(f),sha256=h,target_names=hits,common_long_mentioned=common,CPU_namespace=('cpu' in str(f).lower()),bytes=len(raw)))
   except (OSError,ValueError):skipped.append(str(f))
ledger=root/'reports/gpu-budget-v2.json';v=json.loads(ledger.read_text()) if ledger.exists() else {}
print(json.dumps(dict(host=p['host'],observed_unix=time.time(),metadata_files_checked=seen,inventory_digest=digest.hexdigest(),matches=rows,skipped=skipped,
 exposure_scope='REGISTERED_ISOLATED_WORKSPACE_METADATA_ONLY_NOT_ALL_TENSORS_OR_LEGACY_WORKSPACE',
 complete_global_exposure_claim=False,
 disks=[disk(root),disk(pathlib.Path.home())],
 meminfo={l.split(':')[0]:l.split(':')[1].strip() for l in pathlib.Path('/proc/meminfo').read_text().splitlines() if l.startswith(('MemAvailable:','MemTotal:'))},
 gpu=command(['nvidia-smi','--query-gpu=index,uuid,name,memory.total,memory.used,compute_mode','--format=csv,noheader,nounits']),
 apps=command(['nvidia-smi','--query-compute-apps=gpu_uuid,pid,used_memory','--format=csv,noheader,nounits']),
 ledger=dict(sha256=hashlib.sha256(ledger.read_bytes()).hexdigest() if ledger.exists() else None,totals={k:v.get(k) for k in ('cap_gpu_hours','used_gpu_hours','reserved_gpu_hours','available_gpu_hours')},reserved_jobs=[dict(job_id=k,run_id=j.get('run_id'),kind=j.get('kind'),gpu_uuid=j.get('gpu_uuid')) for k,j in v.get('jobs',{}).items() if j.get('status')=='RESERVED_OR_RUNNING']),
 GPU_submissions=0,ledger_written=False)))
'''
def main():
 a=argparse.ArgumentParser();a.add_argument('--host',choices=['four_card','two_card'],required=True);a.add_argument('--output',type=Path,required=True);a=a.parse_args();assert not a.output.exists()
 m=json.loads((ROOT/'manifests/cara_common_long_newstates_scope_quote_r1_20261027.json').read_text())
 v=(ssh if a.host=='two_card' else four_ssh)(CODE,dict(host=a.host,names=[r['name'] for r in m['requests']]),timeout=180)
 a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v[k] for k in ('host','metadata_files_checked','skipped','disks','meminfo','gpu','apps','ledger')}))
if __name__=='__main__':main()
