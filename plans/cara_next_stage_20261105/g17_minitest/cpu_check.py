"""Small complete36 CPU paths through the existing SpeedOwner and UniPC fixture."""
import json
import os
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tests')]
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ['NVIDIA_VISIBLE_DEVICES']='void'
import torch
from test_cara_f19_speed190_sampling_r1 import run
from postprocess import interval,summarize

if __name__=='__main__':
    torch.set_num_threads(2)
    def forbidden(*args,**kwargs):raise RuntimeError('CPU preparation forbids CUDA')
    torch.cuda._lazy_init=forbidden
    card=json.loads((HERE/'manifest.json').read_text());checks=[]
    for name,role in card['roles'].items():
        for flow in (False,True):
            result=run(role['policy'],flow,light=role['light_C'])
            assert [r['actual'] for r in result['history']]==role['policy']['actions']
            assert not any(r['fallback_reason'] for r in result['history'])
            assert torch.isfinite(result['latent']).all() and len(result['outputs'])==36
            checks.append(dict(role=name,flow=flow,actual36_actions_match=True,finite=True))
    assert interval([0.,0.,0.,0.])==[0.,0.]
    rows=[dict(slot=s,Alex=.18 if s['role']=='G17' else .20,T_DD=132.63 if s['role']=='G17' else 131.7,mask_matches=True)
        for s in card['matrix'] if s['section']!='warm']
    summary=summarize(card,rows)
    assert abs(summary['contrasts'][0]['mean_delta']+.02)<1e-12
    assert summary['contrasts'][0]['improved']==4 and summary['within_common_budget']['G17']
    value=dict(passed=True,checks=checks,paired_summary_controls_passed=True,CUDA_initialized=torch.cuda.is_initialized(),
        model_weights_loaded=False,scope='Existing pinned cache/RF/UniPC with tiny CPU model; not Linux production admission',GPU_submissions=0,remote_calls=0)
    (HERE/'cpu_check.json').write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps(dict(passed=True,complete36_paths=len(checks),CUDA_initialized=value['CUDA_initialized'])))
