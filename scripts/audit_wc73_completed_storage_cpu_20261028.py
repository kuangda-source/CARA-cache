
import json,zipfile,pickle,hashlib,io,time,resource
from pathlib import Path
import os,signal
signal.alarm(1800)
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
progress=Path('/tmp/wc73-output-audit-progress-r2.json')
def report(**kw):
 progress.write_text(json.dumps(dict(at=time.time(),pid=os.getpid(),**kw)))
report(step='starting')
start=time.time();o=Path('/data20t/gaokuangda/worldcache_workspace/outputs/cara-wc73-r1-20261027');d=json.loads((o/'A-runner.json').read_text());rows=[r for r in d['batch']['rows'] if r['status']=='COMPLETE' and r['slot']['section']=='A_DIAGNOSTIC'];results=[];idx={}
class Reader(pickle.Unpickler):
 def persistent_load(self,pid):return ('STORAGE',pid)
 def find_class(self,m,n):
  if m=='collections' and n=='OrderedDict':return dict
  if m=='torch._utils' and n.startswith('_rebuild_tensor'):return lambda *args:('TENSOR',args)
  if m=='torch' and n.endswith('Storage'):return ('DTYPE',n)
  raise ValueError((m,n))
def hd(f):
 h=hashlib.sha256()
 while True:
  b=f.read(1024*1024)
  if not b:break
  h.update(b)
 return h.hexdigest()
for r in rows:
 p=Path(r['tensor_artifact']['path'])
 report(step='single_disk_read',path=str(p));
 data=p.read_bytes();actual=hashlib.sha256(data).hexdigest()
 assert actual==r['tensor_artifact']['sha256']
 report(step='zip_tensor_read',path=str(p));
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  prefix=z.namelist()[0].split('/')[0]+'/';meta=Reader(io.BytesIO(z.read(prefix+'data.pkl'))).load();stor={}
  for n in z.namelist():
   k=n[len(prefix):]
   if k.startswith('data/'):
    with z.open(n) as f:stor[k]=hd(f)
 record={'meta':meta,'storage':stor,'inputs_RNG':r['diagnostic_inputs']};key=(r['slot']['role'],r['slot']['timing_enabled']);idx[key]=record;results.append({'slot':r['slot'],'file_sha_verified':True,'storage_count':len(stor),'video':r['result']['video_path']})
 del data
 Path('/tmp/wc73-output-audit-partial-r2.json').write_text(json.dumps({'files':results}))
checks=[]
for a,b in [(('NATIVE_U36',False),('NATIVE_U36',True)),(('WC_WRAPPER_ALLD_U36',False),('WC_WRAPPER_ALLD_U36',True)),(('NATIVE_U36',True),('WC_WRAPPER_ALLD_U36',True))]:checks.append({'left':a,'right':b,'tensor_metadata_equal':idx[a]['meta']==idx[b]['meta'],'tensor_storage_bytes_equal':idx[a]['storage']==idx[b]['storage'],'inputs_RNG_equal':idx[a]['inputs_RNG']==idx[b]['inputs_RNG']})
report(step='complete');print(json.dumps({'checks':checks,'files':results,'wall_seconds':time.time()-start,'CPU_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'RGB_comparison':'NOT_EXECUTED','no_CUDA':True}))
