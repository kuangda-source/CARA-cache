#!/usr/bin/env python3
"""Independently reconstruct preserved CPU tensors, actions and complete scope; never run sampling."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import torch

MODES=('CC','DC','CD','DD')
ORIGINS=('S22','S23_after_CC','S23_after_DC','S23_after_CD','S23_after_DD')
TRACE=('inputs','outputs','deep','banks','solver_outputs')


def digest(value):
    h=hashlib.sha256()
    def add(x):
        if isinstance(x,torch.Tensor):
            assert torch.isfinite(x).all()
            h.update(str((str(x.dtype),list(x.shape))).encode())
            h.update(memoryview(x.detach().contiguous().reshape(-1).view(torch.uint8).numpy()))
        elif isinstance(x,dict):
            for key in sorted(x):h.update(str(key).encode());add(x[key])
        elif isinstance(x,(tuple,list)):
            h.update(type(x).__name__.encode())
            for item in x:add(item)
        elif x is None or type(x) in (int,float,str,bool):h.update(repr(x).encode())
        else:raise TypeError(type(x))
    add(value);return h.hexdigest()


def mean_square(x):return float(x.double().square().mean())


def audit(stage):
    assert not torch.cuda.is_initialized()
    receipt=json.loads((stage/'receipt.json').read_text());reg=json.loads((stage/'collector-preregistration.json').read_text())
    result=json.loads((stage/'result.json').read_text());checks=result['checks']
    assert receipt['exit_code']==0 and len(checks)==8
    assert receipt['budget_before_sha256']==receipt['budget_after_sha256']
    assert receipt['payload_after_sha256']==reg['payload_sha256'] and receipt['runtime_after_sha256']==reg['runtime_source_sha256']
    for name,expected in reg['payload_sha256'].items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==expected
    complete=[];failed=[];tensor_count=0
    for case in checks:
        state=case['receipt']
        assert (state['planned_parents'],state['planned_origins'],state['planned_CFG_pairs'],state['planned_videos'])==(2,5,40,2)
        if case['scenario']!='complete':
            assert state['parents'][-1]['status']=='TECH_BLOCKED_RETAINED_SCOPE'
            origins=state['parents'][-1]['origins'];assert len(origins)==5
            failures=[r for o in origins for r in o['pairs'] if r['status']=='TECH_BLOCKED_RETAINED_COMPLETE_SCOPE']
            assert failures and all(r['parent_restored'] for r in failures)
            failed.append({'scenario':case['scenario'],'error':case['error'],'planned_CFG_pairs':40,
                'rows_retained':sum(len(o['pairs']) for o in origins),'five_origins_retained':True})
            continue
        off,on=state['parents']
        for k in TRACE+('final_components','final_solver_configuration','sample_return_sha256','final_latent_sha256','flags_before','flags_after','pipeline'):
            assert off[k]==on[k],k
        assert len(off['inputs'])==72 and len(off['solver_outputs'])==36
        assert off['artifact']['sha256']==on['artifact']['sha256']
        for parent in (off,on):
            p=Path(parent['artifact']['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==parent['artifact']['sha256']
            assert parent['status']=='COMPLETE_PARENT'
        assert [o['label'] for o in on['origins']]==list(ORIGINS)
        for index,origin in enumerate(on['origins']):
            assert origin['status']=='COMPLETE_LOCAL_ORIGIN' and len(origin['pairs'])==8
            rows=origin['pairs'];assert [r['label'] for r in rows]==[m+'_'+rep for m in MODES for rep in ('first','second')]
            actual={}
            for row in rows:
                assert row['origin_completed_updates']==(22 if index==0 else 23) and row['parent_restored']
                assert row['status']=='COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT'
                assert row['origin_fingerprint']==digest(row['origin_components'])
                assert row['pair_end_fingerprint']==digest(row['pair_end_components'])
                assert row['origin_components']==rows[0]['origin_components'] and row['inputs']==rows[0]['inputs']
                assert row['origin_solver_configuration']==row['pair_end_solver_configuration']
                for k in ('inputs','outputs','deep','banks','post_denoise_branch_sha256','denoise_arguments'):assert len(row[k])==2
                expected=copy.deepcopy(row['origin_own_history']);events=row['action_report']['events']
                assert row['action_report']['plan']['mode']==row['mode'] and len(events)==2
                step=row['origin_completed_updates']+1
                for slot,event in enumerate(events):
                    assert event['call']==2*(step-1)+slot+1 and event['cfg_slot']==slot
                    assert event['actual_action']==row['mode'][slot] and event['requested']==row['mode'][slot]
                    assert event['paid_probe'] and not event['current_deep_truth_used']
                    assert event['age_solver_steps']==step-expected[slot][-1]
                    assert len(expected[slot])==2 and 1<=event['age_solver_steps']<=32
                    if row['mode'][slot]=='D':expected[slot]=(expected[slot]+[step])[-2:]
                    assert event['true_full_history']==expected
                art=row['artifact'];p=Path(art['path']);raw=p.read_bytes()
                assert len(raw)==art['bytes'] and hashlib.sha256(raw).hexdigest()==art['sha256']
                tensors=torch.load(p,map_location='cpu',weights_only=True)
                assert set(tensors)=={'conditional','unconditional','guided'} and art['space']=='POST_DENOISE_BEFORE_SOLVER'
                for name,tensor in tensors.items():
                    assert tensor.device.type=='cpu' and tensor.dtype==torch.float32 and tensor.ndim==5 and torch.isfinite(tensor).all()
                    assert digest(tensor)==art['tensor_sha256'][name] and list(tensor.shape)==art['shape'][name]
                    tensor_count+=1
                assert row['post_denoise_branch_sha256']==[digest(tensors[k]) for k in ('conditional','unconditional')]
                assert row['actual_guided_sha256']==digest(tensors['guided'])
                assert torch.equal(tensors['guided'],tensors['conditional']+7*(tensors['conditional']-tensors['unconditional']))
                actual[row['label']]=tensors
            for mode in MODES:
                first,second=[r for r in rows if r['mode']==mode]
                skip={'label','wall_seconds','artifact','solver_outputs','child_latent_sha256','solver_step_reused_measured_velocity_without_net_call'}
                assert {k:v for k,v in first.items() if k not in skip}=={k:v for k,v in second.items() if k not in skip}
                for name in ('conditional','unconditional','guided'):assert torch.equal(actual[mode+'_first'][name],actual[mode+'_second'][name])
                if index==0:
                    assert first['solver_step_reused_measured_velocity_without_net_call'] and len(first['solver_outputs'])==1 and not second['solver_outputs']
                    child=next(o for o in on['origins'] if o['label']=='S23_after_'+mode)
                    assert all(r['origin_components']['output']==first['child_latent_sha256'] for r in child['pairs'])
                else:assert all(not r['solver_outputs'] for r in (first,second))
            teacher=actual['DD_first']['guided'].double()
            mse={mode:mean_square(actual[mode+'_first']['guided'].double()-teacher) for mode in MODES}
            reported=case['CPU_Toy_metrics_not_real_model'][index]
            assert all(math.isclose(mse[m],reported['cells'][m]['guided_velocity_MSE_to_DD'],rel_tol=1e-12,abs_tol=1e-12) for m in MODES)
            e0=actual['CC_first']['conditional'].double()-actual['DD_first']['conditional'].double()
            e1=actual['CC_first']['unconditional'].double()-actual['DD_first']['unconditional'].double()
            a,b,dot=mean_square(e0),mean_square(e1),float((e0*e1).mean())
            energy=64*a+49*b-112*dot;direct=mean_square(8*e0-7*e1)
            assert math.isclose(energy,direct,rel_tol=1e-10,abs_tol=1e-10)
            assert math.isclose(direct,reported['CC_error_geometry']['ideal_float64_guided_MSE'],rel_tol=1e-12,abs_tol=1e-12)
            complete.append({'flow':case['flow'],'origin':origin['label'],'pairs':8,'raw_tensor_SHA_and_exact_FP32_guided_verified':True,'Toy_signed_energy_reconstructed':True})
    assert len(complete)==10 and len(failed)==6 and tensor_count==240
    assert not torch.cuda.is_initialized()
    return {'status':'COLLECTOR_CPU_INDEPENDENT_RAW_TENSORS_COMPLETE_SCOPE_AND_ACTION_AUDIT_PASS_NOT_GPU',
        'complete_origins':complete,'failed_attempts_retained':failed,'raw_tensors_reconstructed':240,
        'full_parent_pairs':2,'successful_CFG_pairs':80,'strict_repeat_groups':40,'CUDA_initialized':False,
        'real_model_vectors':0,'GPU_submissions':0,'result_sha256':hashlib.sha256((stage/'result.json').read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--stage',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(audit(args.stage),allow_nan=False))


if __name__=='__main__':main()
