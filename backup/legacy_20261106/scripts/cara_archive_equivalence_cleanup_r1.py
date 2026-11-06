"""Verify every archive member against an existing tree, then unlink one archive.

No extraction and no recursive deletion. Exact fixed archive/root pairs are
supplied by a reviewed plan. An immutable proof/journal precedes each unlink.
"""
import argparse,collections,hashlib,json,os,stat,time,zipfile,tarfile,subprocess
from pathlib import Path,PurePosixPath

def fingerprint(s):
 return dict(dev=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,mode=stat.S_IMODE(s.st_mode),uid=s.st_uid,nlink=s.st_nlink)

def stable(a,b):return all(a[k]==b[k] for k in ('dev','inode','bytes','mtime_ns','ctime_ns'))
def write_new(p,v):
 with Path(p).open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def progress(control,v):
 temp=control/'progress.tmp';temp.write_text(json.dumps(v,ensure_ascii=False)+'\n');os.replace(temp,control/'progress.json')
def safe_target(root,name,strip_root):
 parts=PurePosixPath(name).parts
 if not parts or '..' in parts or PurePosixPath(name).is_absolute():raise ValueError('Unsafe member path')
 if strip_root:
  if parts[0]!=strip_root:raise ValueError('Unexpected member root')
  parts=parts[1:]
 if not parts:raise ValueError('Empty regular member path')
 root=Path(root);variants=[root.joinpath(*parts)]
 try:variants.append(root.joinpath(*(p.encode('cp437').decode('gbk') for p in parts)))
 except UnicodeError:pass
 p=next((p for p in variants if p.is_file()),variants[0])
 if p.resolve()!=p.absolute() or not p.is_relative_to(root):raise ValueError('Symlink or escaped target')
 return p

def compare_stream(stream,target,size):
 s=target.lstat()
 if not stat.S_ISREG(s.st_mode) or s.st_size!=size:raise ValueError('Missing regular file or size mismatch: '+str(target))
 original=fingerprint(s);h=hashlib.sha256();n=0
 fd=os.open(target,os.O_RDONLY|os.O_NOFOLLOW)
 with os.fdopen(fd,'rb') as f:
  if not stable(original,fingerprint(os.fstat(f.fileno()))):raise ValueError('Target changed at open')
  while True:
   a=stream.read(1<<20);b=f.read(len(a)) if a else f.read(1)
   if a!=b:raise ValueError('Content mismatch: '+str(target))
   if not a:break
   h.update(a);n+=len(a)
 if n!=size or not stable(original,fingerprint(target.lstat())):raise ValueError('Target changed during comparison')
 return dict(target=str(target),bytes=n,sha256=h.hexdigest(),target_identity=original)

def visible_open_hits(path):
 s=Path(path).stat();key=(s.st_dev,s.st_ino);hits=[];unreadable=0
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   for fd in (proc/'fd').iterdir():
    try:
     q=fd.stat()
     if (q.st_dev,q.st_ino)==key:hits.append(dict(pid=int(proc.name),fd=fd.name))
    except OSError:pass
  except PermissionError:unreadable+=1
  except OSError:pass
 return dict(hits=hits,unreadable_process_fd_directories=unreadable)

def verify_one(item,control,delete=False):
 archive=Path(item['archive']);root=Path(item['root']);prefix=item.get('strip_root');name=item['id'];out=control/name;out.mkdir(mode=0o700)
 before=fingerprint(archive.lstat());assert stat.S_ISREG(archive.lstat().st_mode)
 assert before['inode']==item['expected_inode'] and before['bytes']==item['expected_bytes'] and before['mtime_ns']==item['expected_mtime_ns']
 rows=[];total=0;started=time.time();last=0
 def record(member,result):
  nonlocal total,last
  row=dict(member=member,**result);rows.append(row);total+=row['bytes']
  with (out/'members.jsonl').open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
  if time.monotonic()-last>10:
   progress(control,dict(status='VERIFYING',archive=str(archive),members=len(rows),bytes_verified=total,started_unix=started,observed_unix=time.time()));last=time.monotonic()
 try:
  if item['format']=='zip':
   with archive.open('rb',buffering=64<<20) as archive_stream, zipfile.ZipFile(archive_stream) as z:
    infos=z.infolist();central=[dict(filename=x.filename,size=x.file_size,CRC=x.CRC,compressed_bytes=x.compress_size,external_attr=x.external_attr,date_time=x.date_time) for x in infos]
    write_new(out/'archive-members.json',central)
    seen=set()
    # Fail cheaply on any missing/different-size member before bulk reads.
    for x in infos:
     if x.is_dir():continue
     mode=x.external_attr>>16
     if stat.S_ISLNK(mode):raise ValueError('Archive symlink retained')
     target=safe_target(root,x.filename,prefix)
     if str(target) in seen:raise ValueError('Duplicate archive target')
     seen.add(str(target));s=target.lstat()
     if not stat.S_ISREG(s.st_mode) or s.st_size!=x.file_size:raise ValueError('Size mismatch: '+str(target))
    for x in infos:
     if x.is_dir():continue
     target=safe_target(root,x.filename,prefix)
     with z.open(x) as stream:record(x.filename,compare_stream(stream,target,x.file_size))
  else:
   with tarfile.open(archive,'r|gz') as t:
    seen=set()
    for x in t:
     if x.isdir():continue
     if not x.isfile():raise ValueError('Nonregular tar member retained')
     target=safe_target(root,x.name,prefix)
     if str(target) in seen:raise ValueError('Duplicate tar target')
     seen.add(str(target))
     with t.extractfile(x) as stream:record(x.name,compare_stream(stream,target,x.size))
  assert rows,'Empty archive cannot authorize deletion'
  assert stable(before,fingerprint(archive.lstat())),'Archive changed during verification'
  for row in rows:assert stable(row['target_identity'],fingerprint(Path(row['target']).lstat())),'Extracted file changed before deletion'
  opened=visible_open_hits(archive);assert not opened['hits'],'Archive is open; retained'
  # fsync proof before destructive action. Contents and every member remain in place.
  with (out/'members.jsonl').open('rb') as f:os.fsync(f.fileno())
  proof=dict(status='ALL_ARCHIVE_MEMBERS_BYTE_EQUAL',archive=str(archive),root=str(root),archive_identity=before,members=len(rows),uncompressed_bytes=total,manifest_sha256=hashlib.sha256((out/'members.jsonl').read_bytes()).hexdigest(),verified_unix=time.time(),visible_open_check=opened,delete_authorized=delete)
  write_new(out/'verified.json',proof)
  if delete:
   assert stable(before,fingerprint(archive.lstat()))
   write_new(out/'delete-intent.json',dict(archive=str(archive),identity=before,proof_sha256=hashlib.sha256((out/'verified.json').read_bytes()).hexdigest(),time_unix=time.time()))
   archive.unlink();fd=os.open(archive.parent,os.O_RDONLY|os.O_DIRECTORY)
   try:os.fsync(fd)
   finally:os.close(fd)
  result=dict(proof,status='VERIFIED_ARCHIVE_REMOVED_EXTRACTED_FILES_RETAINED' if delete else 'VERIFIED_NOT_REMOVED',removed=delete,archive_exists=archive.exists(),completed_unix=time.time())
 except Exception as e:
  result=dict(status='RETAINED_VERIFICATION_FAILED_OR_INCOMPLETE',archive=str(archive),removed=False,archive_exists=archive.exists(),checked_members=len(rows),checked_uncompressed_bytes=total,error=type(e).__name__+': '+str(e),completed_unix=time.time())
 write_new(out/'result.json',result);return result

def main():
 a=argparse.ArgumentParser();a.add_argument('--plan',required=True);a.add_argument('--control',required=True);a.add_argument('--delete-verified',action='store_true');args=a.parse_args()
 os.nice(19);subprocess.run(['ionice','-c','3','-p',str(os.getpid())],capture_output=True)
 if hasattr(os,'sched_getaffinity'):os.sched_setaffinity(0,{max(os.sched_getaffinity(0))})
 plan=json.loads(Path(args.plan).read_text());control=Path(args.control)
 assert control.is_dir() and not (control/'started.json').exists(),'Recover existing worker, never blind restart'
 write_new(control/'started.json',dict(pid=os.getpid(),started_unix=time.time(),delete_verified=args.delete_verified))
 rows=[]
 for item in plan['archives']:
  rows.append(verify_one(item,control,args.delete_verified));progress(control,dict(status='ARCHIVE_FINISHED',archive=item['archive'],last_result=rows[-1],observed_unix=time.time()))
 result=dict(status='ARCHIVE_CHECKS_COMPLETE',rows=rows,deleted_archive_bytes=sum(r['archive_identity']['bytes'] for r in rows if r['removed']),completed_unix=time.time())
 write_new(control/'result.json',result);progress(control,result)
if __name__=='__main__':main()
