#!/usr/bin/env python3
"""New CPU-only zero-mask semantics audit; original GPU bridge remains strict."""
import argparse
import ast
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('project','stage','selected-stage','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists();start=time.monotonic()
    os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    sys.path.insert(0,str(a.selected_stage/'src'))
    import torch
    torch.set_num_threads(2)
    def forbidden(*args,**kwargs):raise RuntimeError('CPU semantic audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_paired_cfg_production import validate
    validate(a.project,a.selected_stage)
    runtime=a.project/'runtime';source=runtime/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
    assert sha(source)=='9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8'
    tree=ast.parse(source.read_text());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Video2WorldModelRectifiedFlow')
    denoise=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='denoise')
    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
    namespace={'torch':torch};exec(compile(ast.fix_missing_locations(ast.Module(body=[future,denoise],type_ignores=[])),str(source)+'#CPU-denoise', 'exec'),namespace)
    wc_source=runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
    assert sha(wc_source)=='b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903'
    wc_func=next(n for n in ast.parse(wc_source.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='worldcache_mini_train_dit_forward')
    kw=wc_func.args.kwarg.arg
    kw_loads=[n for n in ast.walk(wc_func) if isinstance(n,ast.Name) and n.id==kw and isinstance(n.ctx,ast.Load)]
    get_calls=[n for n in ast.walk(wc_func) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id==kw]
    assert len(kw_loads)==len(get_calls)==1 and get_calls[0].func.attr=='get' and get_calls[0].args[0].value=='timestep_scale'
    # Frozen actual condition class; only its base/interface CPU loader is reused.
    helper_path=a.selected_stage/'tests/check_rv0_video_actions_cpu.py'
    spec=importlib.util.spec_from_file_location('gt_condition_cpu_loader',helper_path);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    enum_source=runtime/'cosmos_predict2/_src/predict2/conditioner.py';enum_ast=next(n for n in ast.parse(enum_source.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='DataType')
    from enum import Enum
    enums={'Enum':Enum};exec(compile(ast.fix_missing_locations(ast.Module(body=[enum_ast],type_ignores=[])),str(enum_source)+'#DataType','exec'),enums)
    condition_type,condition_ast_sha=helper.pinned_video_condition(runtime,enums['DataType'])
    checks=[];positive=[]
    class Net:
        def __init__(self):self.inputs=[]
        def __call__(self,x_B_C_T_H_W,timesteps_B_T,**kwargs):
            self.inputs.append((x_B_C_T_H_W.clone(),timesteps_B_T.clone(),{k:tree_digest(v) for k,v in kwargs.items() if k!='gt_frames'}))
            return x_B_C_T_H_W*.125+timesteps_B_T.reshape(1,1,-1,1,1)
    for dtype in (torch.float32,torch.bfloat16):
        noise=torch.arange(96,dtype=dtype).reshape(1,2,3,4,4)/100
        x=noise+.1;t=torch.tensor([[.3]],dtype=dtype)
        gt1=torch.zeros_like(x);gt2=torch.ones_like(x)*.7
        for cond_time in (-1,0):
            for use in (False,True):
                for replace in (False,True):
                    net=Net();model=SimpleNamespace(net=net,tensor_kwargs={'dtype':dtype,'device':'cpu'},config=SimpleNamespace(conditional_frame_timestep=cond_time,denoise_replace_gt_frames=replace))
                    outputs=[]
                    for gt in (gt1,gt2):
                        condition=condition_type(use_video_condition=torch.tensor([use])).edit_data_type(enums['DataType'].VIDEO)
                        condition=condition.set_video_condition(gt,0,0,num_conditional_frames=0)
                        assert not bool(condition.condition_video_input_mask_B_C_T_H_W.any())
                        outputs.append(namespace['denoise'](model,noise,x,t,condition))
                    assert torch.equal(outputs[0],outputs[1]) and torch.equal(net.inputs[0][0],net.inputs[1][0]) and torch.equal(net.inputs[0][1],net.inputs[1][1]) and net.inputs[0][2]==net.inputs[1][2]
                    checks.append({'dtype':str(dtype),'conditional_timestep':cond_time,'use_condition':use,'replace_gt':replace,'zero_mask_prediction_and_active_inputs_identical':True})
            net=Net();model=SimpleNamespace(net=net,tensor_kwargs={'dtype':dtype,'device':'cpu'},config=SimpleNamespace(conditional_frame_timestep=cond_time,denoise_replace_gt_frames=True));outputs=[]
            for gt in (gt1,gt2):
                condition=condition_type(use_video_condition=torch.tensor([True])).edit_data_type(enums['DataType'].VIDEO).set_video_condition(gt,0,0,num_conditional_frames=1)
                outputs.append(namespace['denoise'](model,noise,x,t,condition))
            assert not torch.equal(outputs[0],outputs[1])
            positive.append({'dtype':str(dtype),'conditional_timestep':cond_time,'nonzero_mask_detected_GT_effect':True})
    try:tree_digest(torch.tensor([float('nan')]))
    except ValueError:nonfinite_refused=True
    else:raise AssertionError('Nonfinite GT not refused')
    prefix_path=a.stage/'reports/wc_w3_paired_cfg_parent_prefix_native_20261008.json.gz'
    prefix=json.loads(gzip.decompress(prefix_path.read_bytes()));row=prefix['cases'][0]['WC']['requests'][0]
    actual_masks={x['kwargs']['condition_video_input_mask_B_C_T_H_W'] for x in row['inputs'][:44]};assert len(actual_masks)==1
    mask_candidates={str(dtype):tree_digest(torch.zeros((1,1,24,54,96),dtype=dtype)) for dtype in (torch.float32,torch.bfloat16)}
    matched=[name for name,value in mask_candidates.items() if value==next(iter(actual_masks))];assert len(matched)==1,'Actual recorded mask is not reconstructed all-zero full geometry'
    config_tree=ast.parse((runtime/'cosmos_predict2/config.py').read_text());parsed_property=next(n for n in ast.walk(config_tree) if isinstance(n,ast.FunctionDef) and n.name=='num_input_frames')
    text_case=next(case for match in ast.walk(parsed_property) if isinstance(match,ast.Match) for case in match.cases if isinstance(case.pattern,ast.MatchValue) and isinstance(case.pattern.value,ast.Attribute) and case.pattern.value.attr=='TEXT2WORLD')
    assert len(text_case.body)==1 and isinstance(text_case.body[0],ast.Return) and text_case.body[0].value.value==0
    assert prefix['config']['preregistration']['same_existing_request']['inference_type']=='text2world'
    result={'status':'INACTIVE_GT_ZERO_MASK_REAL_DENOISE_AST_AND_ACTUAL_MASK_CPU_PASS_NOT_REAL_WEIGHTS_OR_GPU_ACCEPTANCE','GPU_submissions':0,'CUDA_initialized':False,
        'CPU_wall_seconds':time.monotonic()-start,'zero_mask_cases':checks,'nonzero_mask_positive_controls':positive,'nonfinite_GT_refused':nonfinite_refused,
        'WC_extra_kwargs_only_lookup':'timestep_scale','gt_frames_never_read_by_WC_forward':True,'real_recorded_mask_hash':next(iter(actual_masks)),
        'full_real_mask_reconstructed_shape':[1,1,24,54,96],'full_real_mask_reconstructed_dtype':matched[0],'real_text2world_num_input_frames_property_zero':True,
        'frozen_denoise_source_sha256':sha(source),'frozen_WC_source_sha256':sha(wc_source),'frozen_condition_AST_sha256':condition_ast_sha,
        'prefix_original_archive_sha256':sha(prefix_path),'real_weights_or_quality':False,'original_strict_historical_input_criterion_unchanged':True,
        'boundary':'Actual frozen denoise/condition AST with Toy network; source shows WC ignores extra gt_frames and actual recorded finite mask hash equals all-zero full geometry; full GPU state/encoding/history still needs separate audit'}
    assert not torch.cuda.is_initialized();a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({k:result[k] for k in ('status','CPU_wall_seconds','full_real_mask_reconstructed_dtype','CUDA_initialized')}))

if __name__=='__main__':main()
