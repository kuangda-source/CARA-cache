"""Verify and consolidate only completed exact duplicate raw files.

Archive objects are read-only hardlinks on the same filesystem, not an offsite
backup. Both original experiment paths retain exact bytes. No recursive delete.
Input via stdin: plan, action verify|commit. A committed receipt maps every alias
back to its SHA-addressed object and original metadata for independent restore.
"""
import os,json,stat,hashlib,time
from pathlib import Path


def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for block in iter(lambda:f.read(8<<20),b''):h.update(block)
 return h.hexdigest()


def identity(path):
 s=path.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_uid!=os.getuid():raise ValueError('Owned regular original required')
 return dict(inode=s.st_ino,device=s.st_dev,bytes=s.st_size,mtime_ns=s.st_mtime_ns,mode=stat.S_IMODE(s.st_mode),uid=s.st_uid)


def same(a,b):return all(a[k]==b[k] for k in ('inode','device','bytes','mtime_ns','uid'))


def open_hits(paths):
 hits=[]
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   if p.stat().st_uid!=os.getuid():continue
   for fd in (p/'fd').iterdir():
    try:
     if os.readlink(fd) in paths:hits.append(dict(pid=int(p.name),path=os.readlink(fd)))
    except OSError:pass
  except OSError:pass
 return hits


def main():
 import sys,subprocess,shutil
 os.nice(19);incoming=json.load(sys.stdin);plan=incoming['plan'];action=incoming['action']
 root=Path(plan['root']);control=Path(plan['archive_control']);old=root/'wc-policy-interval-assets-cal4-full1624-ada-r2'
 assert root==Path('/data20t/gaokuangda/worldcache_workspace/outputs') and control.name=='cara-cold-archive-20261023'
 assert len(plan['pairs'])==452
 active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
 assert not any('full1624' in n or 'full24' in n for n in active)
 paths=set()
 for r in plan['pairs']:
  for key in ('source','canonical'):
   p=root/r[key];assert p.resolve().is_relative_to(old.resolve()) and not p.is_symlink()
   paths.add(str(p))
 assert not open_hits(paths),'An original is open; defer archive'
 verify_path=control/'duplicate-verified.json';receipt=control/'duplicate-committed.json';journal=control/'duplicate-commit.jsonl'
 if action=='verify':
  assert not verify_path.exists();rows=[];cache={};started=time.time()
  for r in plan['pairs']:
   a=root/r['source'];b=root/r['canonical'];sa=identity(a);sb=identity(b)
   assert sa['device']==sb['device'] and sa['bytes']==sb['bytes']==r['bytes'] and a!=b
   # A fresh previous manifest is usable only while inode, size, mtime and uid
   # are unchanged. Canonical objects are always independently hashed here.
   previous=r.get('source_stat');prior_ok=previous and all(sa[k]==previous[k] for k in ('inode','bytes','mtime_ns','uid'))
   if not prior_ok:assert sha(a)==r['sha256']
   if str(b) not in cache:cache[str(b)]=sha(b)
   assert cache[str(b)]==r['sha256'] and same(sa,identity(a)) and same(sb,identity(b))
   rows.append(dict(r,source_identity=sa,canonical_identity=sb,source_hash_reused_from_unchanged_fresh_manifest=bool(prior_ok)))
  value=dict(status='EXACT_DUPLICATE_ARCHIVE_VERIFIED_NOT_RELEASED',plan_sha256=hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest(),rows=rows,started_unix=started,ended_unix=time.time(),active_containers=active,files=len(rows),bytes=sum(r['bytes'] for r in rows),removed_original_bytes=0)
  with verify_path.open('x') as f:json.dump(value,f,indent=2);f.write(chr(10));f.flush();os.fsync(f.fileno())
  print(json.dumps(value));return
 assert action=='commit';v=json.loads(verify_path.read_text());assert v['plan_sha256']==hashlib.sha256(json.dumps(plan,sort_keys=True).encode()).hexdigest()
 if receipt.exists():print(receipt.read_text());return
 objects=control/'objects';objects.mkdir(exist_ok=True,mode=0o700);before=shutil.disk_usage(root).free;rows=[]
 for r in v['rows']:
  a=root/r['source'];b=root/r['canonical'];obj=objects/(r['sha256']+'.pt');sb=identity(b)
  assert same(sb,r['canonical_identity'])
  if not obj.exists():os.link(b,obj)
  assert os.path.samefile(obj,b)
  if not os.path.samefile(a,obj):
   assert same(identity(a),r['source_identity']) and not open_hits({str(a),str(b)})
   os.chmod(obj,0o444)
   temp=a.with_name(a.name+'.archive-link-tmp');assert not temp.exists();os.link(obj,temp)
   assert os.path.samefile(temp,obj) and temp.stat().st_size==r['bytes']
   os.replace(temp,a)
  assert os.path.samefile(a,b) and os.path.samefile(a,obj) and identity(a)['bytes']==r['bytes']
  os.chmod(obj,0o444)
  row=dict(source=str(a),canonical=str(b),archive_object=str(obj),sha256=r['sha256'],bytes=r['bytes'],source_original_metadata=r['source_identity'],canonical_original_metadata=r['canonical_identity'],original_paths_present=True,one_readonly_inode=True)
  with journal.open('a') as f:f.write(json.dumps(row)+chr(10));f.flush();os.fsync(f.fileno())
  rows.append(row)
 value=dict(status='LOSSLESS_EXACT_DUPLICATE_ARCHIVE_COMMITTED',archive_type='SAME_FILESYSTEM_READONLY_SHA_OBJECTS_WITH_ORIGINAL_HARDLINK_PATHS_NOT_OFFSITE_BACKUP',rows=rows,files=len(rows),duplicate_bytes_released=sum(r['bytes'] for r in rows),disk_free_before=before,disk_free_after=shutil.disk_usage(root).free,completed_unix=time.time(),original_payload_bytes_unchanged=True,P1_stage_modified=False,GPU_submissions=0,ledger_written=False,restore='Copy archive_object to a new temp file, verify SHA256, restore recorded source metadata, then atomic replace original source path; do not write through hardlinks.')
 with receipt.open('x') as f:json.dump(value,f,indent=2);f.write(chr(10));f.flush();os.fsync(f.fileno())
 print(json.dumps(value))

if __name__=='__main__':main()
