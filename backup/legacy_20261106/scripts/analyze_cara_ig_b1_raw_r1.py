"""CPU sidecar: raw hidden-space oracles from saved B1 assets only.

These are explanatory teacher diagnostics, never deployable coefficients.
Time slices bound temporary FP64 allocations on the real BTHWD grid.
"""
import argparse,json,sys,time
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.innovation_gain_assets_r1 import load_state
from wcomr.innovation_gain_r1 import project_spatial_blocks
from wcomr.innovation_gain_fit_r1 import box_quadratic

def moments(payload):
 G=np.zeros((2,2));b=np.zeros(2);c=0.;n=0
 for branch in (0,1):
  old,last=payload['anchors'][branch];current=payload['current'][branch]
  ratio=(payload['xi']-last['xi'])/(last['xi']-old['xi'])
  shape=current['probe'].shape
  for t in range(shape[1]):
   def sl(x):return x[:,t:t+1].double()
   full=sl(last['residual'])+ratio*(sl(last['residual'])-sl(old['residual']))
   nu=sl(current['probe'])-sl(current['original'])-sl(last['probe'])-ratio*(sl(last['probe'])-sl(old['probe']))
   target=sl(payload['teacher_hidden'][branch])-sl(current['original'])
   low=project_spatial_blocks(nu);basis=(low,nu-low);e=full-target
   for i in range(2):
    b[i]-=float((e*basis[i]).sum())
    for j in range(2):G[i,j]+=float((basis[i]*basis[j]).sum())
   c+=float(e.square().sum());n+=e.numel()
 return G/n,b/n,c/n

def fit(G,b,c):
 d=np.ones(2);den=float(d@G@d);num=float(b@d)
 scalar=num/den if den>0 else 0.;band=np.linalg.lstsq(G,b,rcond=None)[0]
 boxed=box_quadratic(G,b);ks=float(np.clip(scalar,0,1))
 def loss(k):return float(c-2*b@k+k@G@k)
 return dict(unconstrained_scalar=scalar,unconstrained_band=band.tolist(),boxed_scalar=ks,boxed_band=boxed.tolist(),
  FULL_MSE=c,DEEP_MSE=loss(d),oracle_scalar_MSE=loss(np.ones(2)*ks),oracle_band_MSE=loss(boxed),
  raw_orthogonality_cross=float(G[0,1]),band_energy=np.diag(G).tolist(),
  identifiable_rank=int(np.linalg.matrix_rank(G)),teacher_oracle_only=True)

def main():
 p=argparse.ArgumentParser();p.add_argument('--assets',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists();torch.set_num_threads(2)
 manifest=json.loads((a.assets/'manifest.json').read_text());assert len(manifest['states'])==12
 rows=[];start=time.monotonic()
 for row in manifest['states']:
  payload=load_state(a.assets,row['artifact']);G,b,c=moments(payload);del payload
  rows.append(dict(prompt=row['prompt'],step=row['step'],G=G.tolist(),b=b.tolist(),c=c,oracle=fit(G,b,c)))
 G=np.mean([r['G'] for r in rows],axis=0);b=np.mean([r['b'] for r in rows],axis=0);c=float(np.mean([r['c'] for r in rows]))
 result=dict(status='B1_CPU_RAW_ORACLE_DIAGNOSTIC_NOT_DEPLOYMENT',rows=rows,pooled=fit(G,b,c),
  CPU_wall_seconds=time.monotonic()-start,GPU_submissions=0,real_model_rerun=False,
  precision='FP64 diagnostic algebra on saved tensors; not bitwise implementation replay')
 with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
 print(json.dumps({k:result[k] for k in ('status','CPU_wall_seconds')}))
if __name__=='__main__':main()
