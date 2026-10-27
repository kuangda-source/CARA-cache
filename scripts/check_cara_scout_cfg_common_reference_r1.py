"""Pure CPU reference algebra and failure boundaries; no model acceptance."""
import json,sys
from pathlib import Path
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from wcomr.scout_cfg_common_proposal_r1 import common_long_proposal
from wcomr.cfg_guided_w1_outputs import shared_output_fusion

def main():
 g=torch.Generator().manual_seed(720);pair=lambda:tuple(torch.randn((1,2,3,4,5),generator=g) for _ in range(2))
 C,A,R=pair(),pair(),pair();clones=[x.clone() for p in (C,A,R) for x in p]
 for step,anchor in [(22,21),(25,24),(33,30),(35,30),(32,30)]:
  a=1 if step<25 else .5;o=common_long_proposal(C=C,A_component=A,R4_component=R,step=step,anchor_step=anchor)
  if step-anchor<3:
   assert all(torch.equal(x,y) for x,y in zip(o,shared_output_fusion(C,A,a)))
  else:
   m=(R[0]+R[1])/2;d=A[0]-A[1];expected=shared_output_fusion(C,(m+d/2,m-d/2),a)
   assert all(torch.allclose(x,y,atol=1e-6,rtol=1e-6) for x,y in zip(o,expected))
   aa=shared_output_fusion(C,A,a);assert torch.allclose(o[0]-o[1],aa[0]-aa[1],atol=1e-6,rtol=1e-6)
 assert all(torch.equal(x,y) for x,y in zip(clones,[x for p in (C,A,R) for x in p]))
 failures=[]
 for name,kw in [('stale_anchor',dict(anchor_step=27)),('dense_step',dict(step=36)),('future_anchor',dict(anchor_step=34)),('nonfinite',dict(R4_component=(R[0]*float('nan'),R[1]))),('wrong_shape',dict(R4_component=(R[0][:,:,:,:2],R[1]))),('wrong_dtype',dict(A_component=(A[0].double(),A[1].double())))]:
  args=dict(C=C,A_component=A,R4_component=R,step=33,anchor_step=30);args.update(kw)
  try:common_long_proposal(**args)
  except ValueError:failures.append(name)
  else:raise AssertionError('Accepted '+name)
 return dict(status='COMMON_LONG_REFERENCE_CPU_PASS_NOT_PRODUCTION_ACCEPTANCE',identity_cases=5,rejected=failures,
    no_input_mutation=True,teacher_input=False,threshold_fit=False,IG_reopened=False,GPU_submissions=0,latency_measured=False)
if __name__=='__main__':
 p=Path(sys.argv[1]);assert not p.exists()
 with p.open('x') as f:json.dump(main(),f,indent=2);f.write('\n')
 print('COMMON_LONG_REFERENCE_CPU_PASS')
