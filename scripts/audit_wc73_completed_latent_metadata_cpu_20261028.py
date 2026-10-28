import json,zipfile,pickle,io,hashlib,time,resource
from pathlib import Path
class Reader(pickle.Unpickler):
 def persistent_load(self,pid):return ('STORAGE',pid)
 def find_class(self,m,n):
  if m=='collections' and n=='OrderedDict':return dict
  if m=='torch._utils' and n.startswith('_rebuild_tensor'):return lambda *args:('TENSOR',args)
  if m=='torch' and n.endswith('Storage'):return ('DTYPE',n)
  raise ValueError((m,n))
start=time.time();o=Path('/data20t/gaokuangda/worldcache_workspace/outputs/cara-wc73-r1-20261027');d=json.loads((o/'A-runner.json').read_text());out=[]
for r in d['batch']['rows']:
 if r['status']!='COMPLETE':continue
 p=Path(r['tensor_artifact']['path']);iswarm=r['slot']['section']=='A_WARM'
 if iswarm:
  data=p.read_bytes();assert hashlib.sha256(data).hexdigest()==r['tensor_artifact']['sha256'];archive=io.BytesIO(data)
 else:archive=p
 with zipfile.ZipFile(archive) as z:
  prefix=z.namelist()[0].split('/')[0]+'/';meta=Reader(io.BytesIO(z.read(prefix+'data.pkl'))).load();byteorder=z.read(prefix+'byteorder').decode();latent=meta['final_latent'];pid=latent[1][0][1];raw=z.read(prefix+'data/'+pid[2]);guides=len(meta.get('guided',[]));assert guides==(0 if iswarm else 36)
 out.append({'slot':r['slot'],'warm_SHA_verified':iswarm,'guided_count':guides,'byteorder':byteorder,'latent_metadata':latent,'latent_storage_sha256':hashlib.sha256(raw).hexdigest()})
print(json.dumps({'rows':out,'wall_seconds':time.time()-start,'CPU_seconds':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,'GPUh':0}))
