#!/usr/bin/env python3
"""Source-bound CPU mathematical checks before any real four-cell teacher collection."""
import argparse
import ast
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import types


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    started = time.time()
    sys.path.insert(0, str(args.stage/'src'))
    import torch
    from wcomr.cfg_teacher_metrics import score_four_cells, SPACE, guided
    torch.set_num_threads(2)
    assert not torch.cuda.is_initialized()
    torch.cuda._lazy_init = lambda *a, **k: (_ for _ in ()).throw(RuntimeError('CUDA forbidden in CPU metric checks'))
    reg = json.loads((args.stage/'metric-preregistration.json').read_text())
    for name, sha in reg['payload_sha256'].items():
        assert hashlib.sha256((args.stage/name).read_bytes()).hexdigest() == sha, name
    for name, sha in reg['runtime_source_sha256'].items():
        assert hashlib.sha256((args.runtime/name).read_bytes()).hexdigest() == sha, name
    source = args.runtime/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
    tree = ast.parse(source.read_text())
    cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name=='Video2WorldModelRectifiedFlow')
    closure = next(n for n in ast.walk(cls) if isinstance(n, ast.FunctionDef) and n.name=='velocity_fn')
    signature = ast.dump(closure, include_attributes=False)
    assignment = next(n for n in closure.body if isinstance(n, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='velocity_pred' for t in n.targets))
    assert ast.dump(assignment.value, include_attributes=False) == ast.dump(ast.parse('cond_v + guidance * (cond_v - uncond_v)', mode='eval').body, include_attributes=False)
    assert [n.value.func.attr for n in closure.body[:2]]==['denoise','denoise']
    assert [n.value.args[-1].id for n in closure.body[:2]]==['condition','uncondition']

    def compile_function(node, namespace):
        node=copy.deepcopy(node);node.decorator_list=[];node.returns=None
        for arg in node.args.args:arg.annotation=None
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(source),'exec'),namespace)
        return namespace[node.name]

    def tensor(values):return torch.tensor(values,dtype=torch.float32).reshape(1,1,2,1,1)
    def cells(e0,e1,teacher0=None,teacher1=None):
        d0=tensor([0,0]) if teacher0 is None else teacher0
        d1=tensor([0,0]) if teacher1 is None else teacher1
        return {'CC':{'conditional':d0+e0,'unconditional':d1+e1},
                'DC':{'conditional':d0.clone(),'unconditional':d1+e1},
                'CD':{'conditional':d0+e0,'unconditional':d1.clone()},
                'DD':{'conditional':d0.clone(),'unconditional':d1.clone()}}
    checks=[]
    def score(c):return score_four_cells(c,guidance=7,measurement_space=SPACE)
    aligned=cells(tensor([7,7]),tensor([8,8]));r=score(aligned)
    assert r['cells']['CC']['guided_velocity_MSE_to_DD']==0
    assert r['cells']['DC']['guided_velocity_MSE_to_DD']==3136 and r['cells']['CD']['guided_velocity_MSE_to_DD']==3136
    assert r['CC_error_geometry']['branch_error_cosine']==1 and r['CC_zero_error_reference']
    checks.append({'name':'aligned_branch_errors_cancel_but_single_refresh_worsens','CC_MSE':0,'DC_CD_MSE':3136})
    opposed=score(cells(tensor([1,1]),tensor([-1,-1])))
    assert opposed['cells']['CC']['guided_velocity_MSE_to_DD']==225
    assert opposed['cells']['DC']['guided_velocity_MSE_to_DD']==49 and opposed['cells']['CD']['guided_velocity_MSE_to_DD']==64
    assert opposed['CC_error_geometry']['branch_error_cosine']==-1
    checks.append({'name':'opposed_error_single_refresh_improves','CC_MSE':225,'DC_MSE':49,'CD_MSE':64})
    orthogonal=score(cells(tensor([1,0]),tensor([0,1])))
    assert orthogonal['CC_error_geometry']['signed_cross_term']==0
    assert orthogonal['cells']['CC']['guided_velocity_MSE_to_DD']==56.5
    checks.append({'name':'orthogonal_error_has_no_cross_energy','CC_MSE':56.5})
    for guidance in [0,1,7]:
        namespace={'torch':torch,'guidance':guidance,'condition':'cond','uncondition':'uncond',
            'self':types.SimpleNamespace(denoise=lambda noise,x,t,condition: aligned['CC']['conditional' if condition=='cond' else 'unconditional'])}
        official=compile_function(closure,namespace)(None,None,None)
        assert torch.equal(official,guided(aligned['CC']['conditional'],aligned['CC']['unconditional'],guidance))
    checks.append({'name':'actual_pinned_closure_order_and_operation_exact','guidance_values':[0,1,7]})
    denoise=compile_function(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='denoise'),{'torch':torch})
    mask=tensor([1,0]);gt=tensor([4,4]);noise=tensor([10,10]);x=tensor([3,3])
    condition=types.SimpleNamespace(is_video=True,gt_frames=gt,use_video_condition=True,
        condition_video_input_mask_B_C_T_H_W=mask,to_dict=lambda:{})
    owner=types.SimpleNamespace(config=types.SimpleNamespace(conditional_frame_timestep=-1,denoise_replace_gt_frames=True),
        tensor_kwargs={},net=lambda **kwargs:tensor([100,2]))
    projected=denoise(owner,noise,x,torch.tensor([.5]),condition)
    assert torch.equal(projected,tensor([6,2]))
    checks.append({'name':'actual_pinned_denoise_replaces_conditioned_frame_before_guidance','post_denoise':[6,2]})
    raw=cells(tensor([100,1]),tensor([-100,1]))
    projected_cells={n:{b:tensor([6,float(v.reshape(-1)[1])]) for b,v in pair.items()} for n,pair in raw.items()}
    assert score(raw)['cells']['CC']['guided_velocity_MSE_to_DD']>1000000
    assert score(projected_cells)['cells']['CC']['guided_velocity_MSE_to_DD']==.5
    checks.append({'name':'raw_network_error_and_post_denoise_error_are_not_interchangeable'})
    asymmetric=copy.deepcopy(aligned);asymmetric['CD']['unconditional'].add_(1)
    assert score(asymmetric)['same_branch_output_factorization']['CD_unconditional_equals_DD'] is False
    checks.append({'name':'context_dependent_branch_outputs_measured_not_assumed_factorized'})
    rng=torch.get_rng_state().clone();before=copy.deepcopy(aligned)
    score(aligned)
    assert torch.equal(rng,torch.get_rng_state())
    assert all(torch.equal(before[n][b],v) for n,pair in aligned.items() for b,v in pair.items())
    checks.append({'name':'CPU_metric_does_not_mutate_input_or_consume_RNG'})
    bad=[]
    missing=copy.deepcopy(aligned);missing.pop('CD');bad.append(('missing_cell',missing,SPACE,7))
    nonfinite=copy.deepcopy(aligned);nonfinite['CC']['conditional'].fill_(float('nan'));bad.append(('nonfinite',nonfinite,SPACE,7))
    dtype=copy.deepcopy(aligned);dtype['DD']['unconditional']=dtype['DD']['unconditional'].double();bad.append(('wrong_output_dtype',dtype,SPACE,7))
    shape=copy.deepcopy(aligned);shape['CD']['conditional']=torch.ones(1,1,3,1,1);bad.append(('different_geometry',shape,SPACE,7))
    bad.extend([('raw_net_space',aligned,'RAW_NETWORK',7),('invalid_guidance',aligned,SPACE,float('inf'))])
    for name,c,space,guidance in bad:
        try:score_four_cells(c,guidance=guidance,measurement_space=space)
        except ValueError:pass
        else:raise AssertionError('Invalid metric input accepted: '+name)
    assert not torch.cuda.is_initialized()
    out={'status':'CFG_TEACHER_SOURCE_BOUND_MATHEMATICAL_CPU_PASS_NOT_COLLECTOR_NOT_GPU','pid':__import__('os').getpid(),
        'registered_scope':reg['identity'],'checks':checks,'invalid_contracts_rejected':[b[0] for b in bad],
        'source_closure_AST_sha256':hashlib.sha256(signature.encode()).hexdigest(),
        'runtime_source_sha256':reg['runtime_source_sha256'],'payload_sha256':reg['payload_sha256'],
        'actual_branch_order':['conditional','unconditional'],'actual_guidance7_ideal_weights':[8,-7],
        'score_space':'actual denoise outputs after conditional-frame replacement, before original solver',
        'real_model_teacher_vectors_collected':0,'CUDA_initialized':False,'GPU_submissions':0,
        'started_unix':started,'ended_unix':time.time()}
    with args.receipt.open('x') as f:f.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':out['status'],'checks':len(checks),'rejected':len(bad),'CUDA_initialized':False}))


if __name__=='__main__':main()
