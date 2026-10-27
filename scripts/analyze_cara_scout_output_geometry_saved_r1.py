"""Locate raw-to-output reversals using saved branch/component outputs only."""
import argparse,hashlib,json,os,resource,time
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import torch
from wcomr.policy_interval_readout_r1 import guided
from analyze_cara_scout_mechanism_saved_r1 import output_delta

def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def mse(a,b):return float((a.double()-b.double()).square().mean())
def errors(pair,teacher):
 e=[a.double()-b.double() for a,b in zip(pair,teacher)]
 mc=float(e[0].square().mean());mu=float(e[1].square().mean());cov=float((e[0]*e[1]).mean())
 # FP64 algebra has slightly different rounding from canonical FP32 guidance.
 exact=float((8*e[0]-7*e[1]).square().mean())
 assert abs(exact-(64*mc+49*mu-112*cov))<1e-8
 return dict(branch_c_MSE=mc,branch_u_MSE=mu,cross_covariance=cov,
   weighted_branch_norms=64*mc+49*mu,cfg_cross=-112*cov,guided_FP64_error=exact,
   canonical_guided_MSE=mse(guided(pair),guided(teacher)))
def run(assets,manifest_sha):
 assert sha(assets/'manifest.json')==manifest_sha
 manifest=json.loads((assets/'manifest.json').read_text());rows=[]
 for row in manifest['states']:
  ref=row['artifact'];f=assets/ref['name'];assert f.resolve().parent==assets.resolve() and sha(f)==ref['sha256'] and f.stat().st_size==ref['bytes']
  v=torch.load(f,map_location='cpu',weights_only=True);teacher=v['teacher'];out={};delta={}
  for label in ('WC_C','A_PHASE','R4_GLOBAL','R4_LONG','FULL','DCTA'):
   rd=v['readouts'][label];out[label]={}
   for key in ('component_outputs','outputs'):
    out[label][key]=errors(rd[key],teacher)
   assert abs(out[label]['outputs']['canonical_guided_MSE']-v['summary'][label]['MSE'])<1e-12
  for key in ('component_outputs','outputs'):
   A=v['readouts']['A_PHASE'][key];R=v['readouts']['R4_GLOBAL'][key]
   delta[key]=dict(branches=[output_delta(a,r,t) for a,r,t in zip(A,R,teacher)],
      guided=output_delta(guided(A),guided(R),guided(teacher)))
  rows.append(dict(prompt=row['prompt'],step=row['step'],alpha=v['readouts']['A_PHASE']['alpha'],errors=out,R4_vs_A=delta))
  del v
  print(json.dumps(dict(completed_states=len(rows),total_states=12)),flush=True)
 assert len(rows)==12
 return dict(status='SAVED_OUTPUT_CONVERSION_CFG_PHASE_DIAGNOSTIC',rows=rows,manifest_sha256=manifest_sha,
   new_GPU_submissions=0,IG_reopened=False,fitted=False,head_replayed=False,
   caveat='Component outputs already include warp/head/RF. Cannot separate those three without a new controlled replay.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--manifest-sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 assert os.environ.get('CUDA_VISIBLE_DEVICES','')=='';torch.set_num_threads(2)
 def forbid(*a,**kw):raise RuntimeError('CUDA forbidden')
 torch.cuda._lazy_init=forbid;start=time.monotonic();r=run(a.assets,a.manifest_sha256);assert not torch.cuda.is_initialized()
 r.update(CPU_wall_seconds=time.monotonic()-start,peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,CUDA_initialized=False)
 with a.output.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
