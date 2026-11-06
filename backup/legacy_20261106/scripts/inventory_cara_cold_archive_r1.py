"""Remote read-only source inventory; writes only new archive control metadata."""
import pathlib,json,os,time,hashlib,subprocess
os.nice(19)
root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');out=root/'outputs'
raw=out/'wc-policy-interval-assets-cal4-full1624-ada-r2/warm_2_COLLECT/interval-raw'
bank=out/'wc-scout-dev6-paired-native-full24-ada-r2'
selected=sorted(raw.rglob('*.pt'))+sorted(bank.glob('*/scout-step20-21.pt'))+sorted(bank.glob('*/warm-guided.pt'))
assert len(selected)>400
selected_set={str(p) for p in selected};open_hits=[]
for proc in pathlib.Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 try:
  if proc.stat().st_uid!=os.getuid():continue
  for fd in (proc/'fd').iterdir():
   try:
    target=os.readlink(fd)
    if target in selected_set:open_hits.append(dict(pid=int(proc.name),path=target))
   except OSError:pass
 except (OSError,PermissionError):pass
assert not open_hits
active=subprocess.check_output(['docker','ps','--format','{{.Names}}'],text=True).splitlines()
assert not any('full1624' in n or 'full24' in n for n in active)
rows=[]
for p in selected:
 st=p.lstat();assert p.is_file() and not p.is_symlink() and st.st_uid==os.getuid() and st.st_nlink==1
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8<<20),b''):h.update(b)
 after=p.stat();assert (st.st_size,st.st_mtime_ns,st.st_ino)==(after.st_size,after.st_mtime_ns,after.st_ino)
 rows.append(dict(relative=str(p.relative_to(out)),sha256=h.hexdigest(),bytes=st.st_size,mtime_ns=st.st_mtime_ns,inode=st.st_ino,uid=st.st_uid,mode=st.st_mode))
archive=root/'.sync/cara-cold-archive-20261023';archive.mkdir(exist_ok=False,mode=0o700)
value=dict(status='OWNED_COMPLETED_RAW_ARCHIVE_MANIFEST',observed_unix=time.time(),root=str(out),rows=rows,files=len(rows),bytes=sum(r['bytes'] for r in rows),active_containers=active,open_fd_hits=open_hits,protected_P1_stage=str(root/'.sync/cara-pg-p1-full64-ada-r1-20261023'),preserved=['all formal1624 raw','all Native references','videos','final latents','labels/prices','original receipts','runtime/model/cache'],GPU_submissions=0)
(archive/'manifest.json').write_text(json.dumps(value,indent=2)+chr(10))
for group in ('warm1624','bank24'):
 items=[r['relative'] for r in rows if ('warm_2_COLLECT/interval-raw/' in r['relative'])==(group=='warm1624')]
 (archive/(group+'.files')).write_text(chr(10).join(items)+chr(10))
print(json.dumps(value))
