#!/usr/bin/env python3
"""Reload all Toy N1 artifacts independently before using the real entry."""
import argparse
import json
import math
import os
import sys
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True);a=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    from wcomr.mid_coverage import tree_digest
    from wcomr.math_source_fusion_r1 import fusion_risk
    value=json.loads((a.stage/'CPU-result.json').read_text())
    records=[r for flow in value['checks'] for request in flow['checks'] for r in request['records']]
    assert len(records)==12
    tensors=0;P=D=early=late=0
    for r in records:
        path=Path(r['artifact']['path']).resolve();assert path.is_relative_to((a.stage/'CPU-artifacts').resolve())
        raw=torch.load(path,weights_only=True,map_location='cpu');assert tree_digest(raw)==r['artifact']['tensor_sha256']
        teacher=raw['DENSE_SAME_STATE'];errors={}
        for name in ('OFFICIAL_C','D_REFERENCE_UNIT','P_REFERENCE_UNIT','FUSION_HALF_UNIT'):
            c,u=(raw[name][b]-teacher[b] for b in (0,1));eg=(8*c-7*u).double();errors[name]=eg
            actual=eg.square().mean().item()
            assert math.isclose(actual,r['guided_moments'][name]['base_guided_MSE'],rel_tol=2e-5,abs_tol=1e-8)
        x,y=errors['D_REFERENCE_UNIT'],errors['P_REFERENCE_UNIT']
        A=x.square().mean().item();B=y.square().mean().item();C=(x*y).mean().item()
        assert math.isclose(fusion_risk(A,B,C,.5),errors['FUSION_HALF_UNIT'].square().mean().item(),rel_tol=2e-5,abs_tol=1e-8)
        if r['point']['source']=='D':
            D+=1;assert all(torch.equal(x,y) for x,y in zip(raw['D_REFERENCE_UNIT'],raw['P_REFERENCE_UNIT']))
        else:
            P+=1;early+=r['step']<25;late+=r['step']>=25
        tensors+=sum(len(v) if isinstance(v,tuple) else 1 for v in raw.values())
    assert (P,D,tensors)==(8,4,144) and early and late
    result={'status':'N1_BOTH_FLOW_ALL12_RAW144_TENSORS_MOMENTS_PHASES_CPU_PASS',
            'raw_files':12,'raw_tensors':144,'P_states':P,'D_controls':D,
            'early_P_states':early,'late_P_states':late,'GPU_submissions':0,
            'CUDA_initialized':False,'ledger_written':False}
    dest=a.stage/'independent-CPU-raw-audit.json';assert not dest.exists()
    dest.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
