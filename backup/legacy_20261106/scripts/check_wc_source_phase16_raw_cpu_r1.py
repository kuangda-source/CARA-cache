#!/usr/bin/env python3
"""Independently reload every cal16 Toy tensor and reconstruct CFG losses."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from collections import Counter


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    import torch
    from wcomr.mid_coverage import tree_digest
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    v=json.loads((a.stage/'CPU-result.json').read_text())
    assert v['status']=='SOURCE_PHASE16_TWO_FLOW_FULL16_PARENTS32_STATES_CPU_PASS_NOT_GPU'
    reg=json.loads((a.stage/'registration.json').read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert v['payload_sha256']==reg['payload_sha256']
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    points=[];cells=Counter();files=set();tensors=0
    for flow in v['checks']:
        for parent in flow['checks']:
            assert parent['all36_guided_actions_final_and_video_equal']
            assert parent['all5_pre_action_trials_restored'] and parent['actual_diagnostic_pairs']==56
            for r in parent['records']:
                path=Path(r['artifact']['path']).resolve()
                assert path.is_relative_to((a.stage/'CPU-artifacts').resolve()) and path not in files
                files.add(path);raw=torch.load(path,weights_only=True,map_location='cpu')
                assert tree_digest(raw)==r['artifact']['tensor_sha256']
                assert set(raw)=={'DENSE_SAME_STATE','C','D_REFERENCE_A','FUSION_A','NEW_P','actual_latent','timestep'}
                flat=[t for x in raw.values() for t in (x if isinstance(x,tuple) else (x,))]
                assert len(flat)==12 and all(isinstance(t,torch.Tensor) and bool(torch.isfinite(t).all()) for t in flat)
                tensors+=len(flat);teacher=raw['DENSE_SAME_STATE']
                energy=(8*teacher[0].double()-7*teacher[1].double()).square().mean().item()
                losses={}
                for name in ('C','D_REFERENCE_A','FUSION_A','NEW_P'):
                    pair=raw[name];assert len(pair)==2
                    assert all(t.shape==teacher[b].shape and t.dtype==teacher[b].dtype for b,t in enumerate(pair))
                    ec,eu=(pair[b].double()-teacher[b].double() for b in (0,1))
                    loss=(8*ec-7*eu).square().mean().item()
                    algebra=64*ec.square().mean().item()+49*eu.square().mean().item()-112*(ec*eu).mean().item()
                    assert math.isclose(loss,algebra,rel_tol=1e-9,abs_tol=1e-10)
                    losses[name]={'absolute_guided_MSE':loss,'normalized_guided_MSE':loss/max(energy,1e-12)}
                assert len(r['restores'])==len(r['trial_receipts'])==5
                assert not r['offline_teacher_or_candidates_committed_to_parent']
                point=r['point'];cell=point['source']+'_'+point['phase'];cells[cell]+=1
                if point['source']=='D':
                    assert all(torch.equal(x,y) for x,y in zip(raw['D_REFERENCE_A'],raw['FUSION_A']))
                points.append({'flow':flow['flow'],'scene':parent['scene'],'selection':point,
                    'parent_continues':r['parent_continues'],'teacher_guided_energy':energy,'losses':losses,
                    'raw_sha256':sha(path),'tensor_sha256':r['artifact']['tensor_sha256']})
    assert len(files)==len(points)==32 and tensors==384 and all(cells[k]==8 for k in ('D_EARLY','D_LATE','P_EARLY','P_LATE'))
    out={'status':'SOURCE_PHASE16_ALL32_RAW384_CFG_RECONSTRUCTION_CPU_PASS_NOT_REAL_LABELS',
        'raw_files':32,'raw_tensors':384,'source_phase_cells':dict(cells),'points':points,
        'sampling_result_sha256':sha(a.stage/'CPU-result.json'),'registration_sha256':sha(a.stage/'registration.json'),
        'GPU_submissions':0,'CUDA_initialized':torch.cuda.is_initialized(),'ledger_written':False,
        'all16_CPU_parent_paths_and_natural_pre_P_controls':True}
    assert not out['CUDA_initialized'] and not a.output.exists()
    a.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:out[k] for k in ('status','raw_files','raw_tensors','source_phase_cells','GPU_submissions')}))


if __name__=='__main__':main()
