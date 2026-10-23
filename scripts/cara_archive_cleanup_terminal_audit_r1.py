"""Read-only final audit of the explicitly authorized 2026-10-24 cleanup.

Execute through the existing four-card SSH wrapper after both original checks
terminate. Every removed archive must have complete byte-comparison proofs;
this independently checks their hashes and all retained extracted identities.
"""
import pathlib,json,hashlib,time,os,subprocess
root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')
controls=[(root/'.sync/cara-archive-equality-cleanup-20261024','nuscenes-mini'),(root/'.sync/cara-archive-equality-cleanup-buffered-r2-20261024','kyxz2021')]
rows=[]
for control,name in controls:
 p=control/name
 assert (p/'result.json').is_file(),'Original verification is not terminal: '+name
 result=json.loads((p/'result.json').read_text())
 row=dict(control=str(control),id=name,result=result,proof_files={})
 for n in ('result.json','verified.json','delete-intent.json','members.jsonl','archive-members.json'):
  f=p/n
  if f.exists():
   data=f.read_bytes();row['proof_files'][n]=dict(path=str(f),bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
 archive=pathlib.Path(result['archive']);row['archive_present_now']=archive.exists()
 if result['removed']:
  assert not archive.exists()
  assert result['status']=='VERIFIED_ARCHIVE_REMOVED_EXTRACTED_FILES_RETAINED'
  assert result['archive_identity']['nlink']==1
  proof=json.loads((p/'verified.json').read_text());intent=json.loads((p/'delete-intent.json').read_text())
  assert intent['proof_sha256']==row['proof_files']['verified.json']['sha256']
  assert proof['manifest_sha256']==row['proof_files']['members.jsonl']['sha256']
  count=total=0
  for line in (p/'members.jsonl').open():
   v=json.loads(line);s=pathlib.Path(v['target']).lstat();i=v['target_identity']
   now=dict(dev=s.st_dev,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns)
   assert all(now[k]==i[k] for k in now),'Extracted file changed: '+v['target']
   count+=1;total+=v['bytes']
  assert count==proof['members'] and total==proof['uncompressed_bytes']
  row['independent_manifest_and_all_extracted_identities_pass']=True
  row['members_verified']=count;row['extracted_bytes_verified']=total
 rows.append(row)
retained=[]
for name in ('/data20t/shentong/BeamNG.tech.v0.35.5.0.zip','/data20t/datasets/DIS5K.zip','/data20t/datasets/COD10K-v3.zip'):
 p=pathlib.Path(name);s=p.stat();retained.append(dict(path=name,present=True,inode=s.st_ino,bytes=s.st_size,mtime_ns=s.st_mtime_ns))
worker=[]
for pid,start in ((1173753,955811543),(1174571,955845495)):
 p=pathlib.Path('/proc')/str(pid);same_live=False;state=None;ticks=None
 if p.exists():
  fields=(p/'stat').read_text().rsplit(')',1)[1].split();state=fields[0];ticks=int(fields[19]);same_live=(ticks==start and state not in ('Z','X'))
 assert not same_live,'Owned archive verifier still live'
 worker.append(dict(pid=pid,expected_start_ticks=start,observed_start_ticks=ticks,state=state,original_live=False))
container='cara-pg-p1-full64-ada-r1-20261023-gpu'
p1=json.loads(subprocess.check_output(['docker','inspect',container,'--format','{{json .State}}'],text=True))
assert not p1['Running'] and p1['ExitCode']==0 and p1['FinishedAt']=='2026-10-23T15:02:35.08563664Z'
reg=root/'.sync/cara-pg-p1-full64-ada-r1-20261023/registration.json'
s=os.statvfs('/data20t')
print(json.dumps(dict(status='ARCHIVE_CLEANUP_TERMINAL_INDEPENDENT_METADATA_ACCEPTED',observed_unix=time.time(),rows=rows,retained=retained,owned_verifiers=worker,P1_original_container_state=p1,P1_registration_sha256=hashlib.sha256(reg.read_bytes()).hexdigest(),data20t=dict(total_bytes=s.f_blocks*s.f_frsize,free_bytes=s.f_bfree*s.f_frsize,available_bytes=s.f_bavail*s.f_frsize),no_new_GPU_task=True),ensure_ascii=False))
