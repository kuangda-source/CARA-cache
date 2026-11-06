"""Exercise unchanged source/global compiler guards on local AST modules."""
import ast,hashlib,importlib.util,json,types
from enum import Enum
from pathlib import Path
import numpy as np
import torch
from einops import rearrange
from wcomr.cfg_guided_w1_forward import compile_collection
from wcomr.cfg_paired_probe_velocity import compile_velocity

def check(runtime):
    runtime=Path(runtime)
    spec=importlib.util.spec_from_file_location('local_origin_full_fixture',Path(__file__).with_name('check_full_sampling.py'))
    full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)
    class DataType(str,Enum):VIDEO='video';IMAGE='image'
    wc=types.ModuleType('local_CPU_source_exact_wc')
    vars(wc).update(torch=torch,np=np,rearrange=rearrange,amp=torch.amp,F=torch.nn.functional,DataType=DataType,
        log=types.SimpleNamespace(**{n:lambda *a,**kw:None for n in ('info','debug','warning','error')}))
    wcpath=runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py'
    full.load_functions(wcpath,['compute_optimal_gamma','estimate_optical_flow','warp_feature','compute_saliency_map','worldcache_mini_train_dit_forward','apply_worldcache'],vars(wc))
    rfpath=runtime/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
    nodes=[n for n in ast.parse(rfpath.read_text()).body if isinstance(n,ast.ClassDef) and n.name=='Video2WorldModelRectifiedFlow'];assert len(nodes)==1
    rf=types.ModuleType('local_CPU_source_exact_rf')
    vars(rf).update(torch=torch,Text2WorldModelRectifiedFlow=object,DataType=DataType,parallel_state=types.SimpleNamespace(is_initialized=lambda:False),NUM_CONDITIONAL_FRAMES_KEY='num_conditional_frames')
    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future,*nodes],type_ignores=[])),str(rfpath),'exec'),vars(rf))
    class Collector:
        def prewarp(self,*a,**kw):raise AssertionError('Compile-only check executed model hook')
        hidden=prewarp;output=prewarp
    collector=Collector();refusals=[]
    try:compile_collection(runtime,wc,rf,collector)
    except AttributeError:refusals.append('MISSING_LOCAL_SOURCE_METADATA')
    else:raise AssertionError('Missing metadata accepted')
    wc.__file__=str(wcpath);rf.__file__=str(rfpath)
    assert Path(wc.worldcache_mini_train_dit_forward.__code__.co_filename).resolve()==wcpath.resolve()
    assert Path(rf.Video2WorldModelRectifiedFlow.denoise.__code__.co_filename).resolve()==rfpath.resolve()
    _,_,proof=compile_collection(runtime,wc,rf,collector)
    model=types.SimpleNamespace(net=object())
    def no_pair(*a,**kw):raise AssertionError('Compile-only check executed a model pair')
    executor=types.SimpleNamespace(model=model,net=model.net,pair=no_pair)
    _,velocity_proof=compile_velocity(runtime,rf,executor,no_pair)
    rf.__file__=str(Path(__file__))
    try:compile_collection(runtime,wc,rf,collector)
    except ValueError:refusals.append('FOREIGN_SOURCE_METADATA')
    else:raise AssertionError('Foreign module filename accepted')
    assert not torch.cuda.is_initialized()
    return dict(status='W3_LOCAL_R2_UNCHANGED_ORIGIN_AND_GLOBAL_GUARDS_COMPILE_PASS_NOT_SAMPLING',
        refusals=refusals,compiler_proof=dict(proof),velocity_compiler_proof=dict(velocity_proof),source_body_and_namespace_identity_checked=True,
        model_forwards=0,weights_loaded=0,GPU_submissions=0,SSH_queries=0,production_import_claim=False)
