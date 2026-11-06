"""Consolidate explicitly approved completed tensor groups; retain every alias.

No GPU/ledger/environment changes. Journal and original metadata permit recovery.
The fixed production caller supplies only reviewed completed-run groups.
"""
import hashlib,json,os,stat,time,subprocess,fcntl
from pathlib import Path

ROOT=Path('/data20t/gaokuangda/worldcache_workspace')
RUNS={'wc-policy-interval-assets-cal4-full1624-ada-r2','wc-policy-price-refresh-cal4-full1624-ada-r1','wc-scout-dev6-paired-native-full24-ada-r2'}

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 return h.hexdigest()

def ident(p):
 s=Path(p).lstat()
 assert stat.S_ISREG(s.st_mode) and s.st_uid==os.getuid(),'Owned regular file required'
 return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,mode=stat.S_IMODE(s.st_mode),uid=s.st_uid,nlink=s.st_nlink,allocated=s.st_blocks*512)

def stable(a,b):
 return all(a[k]==b[k] for k in ('device','inode','bytes','mtime_ns','uid'))

def durable_json(path,value):
 with Path(path).open('x') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())

def syncdir(p):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
 try:os.fsync(fd)
 finally:os.close(fd)

def open_hits(keys):
 hits=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   if proc.stat().st_uid!=os.getuid():continue
   for fd in (proc/'fd').iterdir():
    try:
     s=fd.stat()
     if (s.st_dev,s.st_ino) in keys:hits.append(dict(pid=int(proc.name),fd=fd.name))
    except OSError:pass
  except OSError:pass
 return hits

def protect(p):
 stage=Path(p['P1_stage']);reg=stage/'registration.json'
 assert sha(reg)==p['P1_registration_sha256']
 registration=json.loads(reg.read_text());payload=registration['payload_sha256']
 for name,h in payload.items():assert sha(stage/name)==h,'P1 payload differs: '+name
 pid=p['P1_pid'];proc=Path('/proc')/str(pid)
 state=json.loads(subprocess.check_output(['docker','inspect',p['P1_container'],'--format','{{json .State}}'],text=True))
 if p.get('P1_terminal_state'):
  expected=p['P1_terminal_state'];assert not state['Running'] and state['ExitCode']==0
  assert state['StartedAt']==expected['StartedAt'] and state['FinishedAt']==expected['FinishedAt']
  assert not proc.exists(),'Original runner PID now exists; recheck identity'
  ticks=None
 else:
  ticks=int((proc/'stat').read_text().rsplit(')',1)[1].split()[19]);assert ticks==p['P1_start_ticks'] and state['Running']
 active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
 assert not any(('full1624' in x or 'full24' in x) for x in active),'Completed source container is active'
 return dict(observed_unix=time.time(),pid=pid,start_ticks=ticks,container_state=state,registration_sha256=sha(reg),payload_count=len(payload),all_registered_payload_hashes_match=True)

def consolidate(groups,control,guard,allow):
 """Production allowlist/guard are injected; tests use isolated temporary files."""
 control=Path(control);control.mkdir(mode=0o700,exist_ok=True)
 with (control/'maintenance.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  return _consolidate_locked(groups,control,guard,allow)

def _consolidate_locked(groups,control,guard,allow):
 plan_hash=hashlib.sha256(json.dumps(groups,sort_keys=True).encode()).hexdigest()
 receipt=control/'committed.json'
 if receipt.exists():
  old=json.loads(receipt.read_text());assert old['plan_sha256']==plan_hash
  return old
 assert not (control/'verified.json').exists(),'Existing unfinished verification: recover original journal before continuation'
 before=guard();rows=[];cache={}
 for g in groups:
  originals=[]
  for entry in g['files']:
   p=Path(entry['path']);allow(p);s=ident(p)
   assert s['bytes']==g['bytes'] and s['inode']==entry['inode'] and s['device']==entry['dev'] and s['mtime_ns']==entry['mtime_ns']
   key=(s['device'],s['inode'])
   if key not in cache:cache[key]=sha(p)
   assert cache[key]==g['sha256'] and stable(s,ident(p)),'Changed bytes during verification'
   originals.append(dict(path=str(p),identity=s))
  assert len({r['identity']['device'] for r in originals})==1
  canonical=max(originals,key=lambda r:r['identity']['nlink'])
  rows.append(dict(sha256=g['sha256'],bytes=g['bytes'],canonical=canonical['path'],originals=originals))
 keys={(r['identity']['device'],r['identity']['inode']) for g in rows for r in g['originals']}
 assert not open_hits(keys),'Selected tensor inode open by owned process'
 verified=dict(plan_sha256=plan_hash,verified_unix=time.time(),groups=rows,P1_before=before)
 durable_json(control/'verified.json',verified)
 objdir=control/'objects';objdir.mkdir(mode=0o700,exist_ok=True);replaced=[];freed={}
 guard()
 for g in rows:
  canonical=Path(g['canonical']);obj=objdir/(g['sha256']+'.pt')
  assert all(stable(r['identity'],ident(r['path'])) for r in g['originals'])
  assert not open_hits({(r['identity']['device'],r['identity']['inode']) for r in g['originals']})
  if not obj.exists():os.link(canonical,obj);syncdir(objdir)
  assert os.path.samefile(canonical,obj)
  os.chmod(obj,0o444)
  for r in g['originals']:
   target=Path(r['path'])
   if os.path.samefile(target,obj):continue
   assert stable(r['identity'],ident(target))
   temp=target.with_name(target.name+'.dedup-r2-tmp');assert not temp.exists()
   os.link(obj,temp);os.replace(temp,target);syncdir(target.parent)
   event=dict(path=str(target),object=str(obj),sha256=g['sha256'],original_metadata=r['identity'],time_unix=time.time())
   with (control/'commit.jsonl').open('a') as f:f.write(json.dumps(event)+'\n');f.flush();os.fsync(f.fileno())
   replaced.append(event);freed[(r['identity']['device'],r['identity']['inode'])]=r['identity']
  for r in g['originals']:
   assert os.path.samefile(r['path'],obj) and ident(r['path'])['mode']&0o222==0
  assert sha(obj)==g['sha256']
 after=guard()
 value=dict(status='COMPLETED_TENSORS_MERGED_ALL_ORIGINAL_PATHS_RETAINED',plan_sha256=plan_hash,groups=rows,replaced=replaced,newly_replaced_paths=len(replaced),retired_distinct_inodes=len(freed),duplicate_logical_bytes=sum(s['bytes'] for s in freed.values()),duplicate_allocated_bytes=sum(s['allocated'] for s in freed.values()),P1_before=before,P1_after=after,all_original_paths_present=True,all_hashes_match=True,all_shared_objects_readonly=True,completed_unix=time.time(),restore='Copy the SHA object to a new independent inode, verify SHA, restore recorded mode/mtime, then atomic replace only that alias. Never write through or chmod shared hardlinks.')
 durable_json(receipt,value);syncdir(control)
 return value

def main():
 import sys
 os.nice(19);subprocess.run(['ionice','-c','3','-p',str(os.getpid())],capture_output=True)
 p=json.load(sys.stdin);groups=p['groups'];assert len(groups)==9
 control=ROOT/'.sync/cara-cold-archive-r2-20261024'
 def allow(path):
  assert path.resolve()==path.absolute(),'No symlink paths'
  rel=path.relative_to(ROOT)
  assert (rel.parts[0]=='outputs' and rel.parts[1] in RUNS) or (rel.parts[:3]==('.sync','cara-cold-archive-20261023','objects'))
  assert path.suffix=='.pt' and 'pg-p1' not in str(path).lower()
 print(json.dumps(consolidate(groups,control,lambda:protect(p),allow)))
if __name__=='__main__':main()
