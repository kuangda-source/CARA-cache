"""Offline real Alex/PIQ weights on synthetic CPU images; no scientific scores."""
import os,sys,time,json,hashlib,signal
from pathlib import Path
signal.alarm(180);s=Path(sys.argv[1]);sys.path.insert(0,str(s/'site'));os.environ['TORCH_HOME']=str(s/'torch')
import torch,numpy as np,lpips,piq
start=time.time();torch.set_num_threads(1);assert not torch.cuda.is_initialized()
def no_download(*a,**k):raise RuntimeError('Offline bound weights required')
torch.hub.download_url_to_file=no_download
weights={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (s/'torch/hub/checkpoints').iterdir()}
x=torch.linspace(0,1,3*64*64).reshape(1,3,64,64);y=x.flip(-1)
a=lpips.LPIPS(net='alex',version='0.1',verbose=False).cpu().eval();v=piq.LPIPS().cpu().eval()
with torch.inference_mode():
 assert float(a(x*2-1,x*2-1))==0 and float(v(x,x))==0
 aa=float(a(x*2-1,y*2-1));vv=float(v(x,y));assert np.isfinite([aa,vv]).all()
 assert abs(float(v(torch.cat([x,y]),torch.cat([y,x])))-vv)<1e-6
p=Path(lpips.__file__).parent/'weights/v0.1/alex.pth'
r=dict(status='BOUND_ALEX_PIQ_REAL_WEIGHT_SYNTHETIC_CPU_PASS',torch=torch.__version__,piq=piq.__version__,lpips='0.1.4',weights=weights,alex_linear_weights_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),self_zero=True,batch_mean_parity=True,CUDA_initialized=torch.cuda.is_initialized(),GPU_submissions=0,scientific_quality_result=False,CPU_wall_seconds=time.time()-start)
assert not r['CUDA_initialized'];(s/'CPU-proof.json').write_text(json.dumps(r,indent=2)+'\n');print(r['status'])
