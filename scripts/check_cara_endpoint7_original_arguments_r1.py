"""Read-only original32 file hashes plus accepted asset stamps; no GPU or ledger writes."""
import hashlib,json,os,shlex,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from cara_two_card_transport_r1 import password
OUTPUT=ROOT/'reports/cara_endpoint7_original_arguments_assets_r1_20261101.json'
REMOTE=r'''
import hashlib,json,os,pathlib,signal,time
signal.alarm(65);os.sched_setaffinity(0,{26})
p=json.loads(payload);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');files=[];stamps=[]
for a in p['files']:
 f=pathlib.Path(a['path']);raw=f.read_bytes();h=hashlib.sha256(raw).hexdigest()
 files.append(dict(path=str(f),sha256=h,expected_sha256=a['sha256'],bytes=len(raw),matched=h==a['sha256']))
for a in p['assets']:
 f=root/a['path'];s=f.stat();stamp=[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]
 stamps.append(dict(path=str(f),expected_digest=a['digest'],stamp=stamp,expected_stamp=a['stamp'],unchanged=stamp==a['stamp'],rehash_performed=False))
s=os.statvfs(root)
print(json.dumps(dict(observed_unix=time.time(),host=os.uname().nodename,CPU_affinity=sorted(os.sched_getaffinity(0)),
 files=files,accepted_asset_stamps=stamps,available_disk_bytes=s.f_bavail*s.f_frsize,
 all_original_files_match=all(r['matched'] for r in files),all_accepted_asset_stamps_unchanged=all(r['unchanged'] for r in stamps),
 GPU_submissions=0,ledger_written=False,four_card_accessed=False)))
'''
def main():
 assert not OUTPUT.exists()
 p=json.loads((ROOT/'configs/cara_endpoint_proposal.json').read_text())
 descriptors={r['source']['path']:r['source'] for r in p['reference_sources']}
 descriptors.update({r['source']['path']:r['source'] for r in p['formal_matrix'] if r['mode']=='REUSE_COMPLETE_SCORE'})
 files=[]
 for a in descriptors.values():files.extend([dict(path=a['path'],sha256=a['sha256']),dict(path=str(Path(a['path']).with_suffix('.json')),sha256=a['argument_file_sha256'])])
 source='reports/cara_budget_successor_assets_accepted_r1_20261031.json';raw=(ROOT/source).read_bytes()
 payload=json.dumps(dict(files=files,assets=json.loads(raw)['asset_sha256_and_stamps']))
 secret=password();code='import sys;payload=sys.stdin.read();exec('+repr(REMOTE)+')'
 command="sudo -S -p '' -u gaokuangda -g docker /home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python -c "+shlex.quote(code)
 child=subprocess.Popen(['ssh','-F',str(ROOT/'.sync/cara-fast-mainline-tailscale-20261030/ssh_config.budget_direct.private'),'-o','BatchMode=yes','-o','ConnectTimeout=20','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=3','two_card_lan',command],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
 try:out,err=child.communicate((secret+'\n'+payload).encode(),timeout=90)
 except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);out,err=child.communicate()
 result=json.loads(out) if child.returncode==0 else None
 report=dict(exit_code=child.returncode,result=result,stderr=err.decode(errors='replace').replace(secret,'[REDACTED]'),
  accepted_asset_source=source,accepted_asset_source_sha256=hashlib.sha256(raw).hexdigest(),
  old_model_hash_reused_only_if_all_stamps_unchanged=True,whole_production_admission=False)
 with OUTPUT.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(exit_code=child.returncode,files_match=(result or {}).get('all_original_files_match'),asset_stamps_unchanged=(result or {}).get('all_accepted_asset_stamps_unchanged'))))
if __name__=='__main__':main()
