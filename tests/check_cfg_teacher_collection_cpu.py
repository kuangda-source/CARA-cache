"""Pinned sampler/denoise/frozen conditions with Toy weights and writer; not GPU evidence."""
import ast
import copy
from contextlib import nullcontext
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import torch
from wcomr.cfg_teacher_collection import GuidedTeacherFork
from wcomr.cfg_teacher_sampling import run_teacher_batch,vector_artifact,verify_batch
from wcomr.cfg_teacher_metrics import score_four_cells,SPACE,guided
from wcomr.h0_mode import establish_shared_eval


def load(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def exercise(*,inference,samples,wc,settings,inference_module,flow,runtime,artifact_root=None,**unused):
    samples=samples[-1:];model=inference.pipe.model;net=model.net
    old=(net.prepare_embedded_sequence,model.conditioner.get_condition_with_negative_prompt,
         model.get_velocity_fn_from_batch,model.denoise,GuidedTeacherFork.measure,model.get_data_and_condition)
    config_before=dict(vars(model.config))
    net.prepare_embedded_sequence=lambda x,**kw:(x[:,:2048].movedim(1,-1).contiguous(),None,None)
    frozen,class_sha=load('check_rv0_video_actions_cpu').pinned_video_condition(runtime,
        wc.worldcache_mini_train_dit_forward.__globals__['DataType'])
    def conditions(batch):
        return tuple(frozen(crossattn_emb=torch.ones(1,3,4)*(1+slot+.1*(batch['prompt']=='human')),
            fps=batch['fps'],use_video_condition=torch.tensor([True])).set_video_condition(
                torch.zeros(1,2048,2,8,8),0,0,num_conditional_frames=1) for slot in (0,1))
    model.conditioner.get_condition_with_negative_prompt=conditions
    # The base fixture returns RGB directly. This declared Toy encoder supplies
    # the same latent geometry to the unchanged Video2World condition interface.
    model.get_data_and_condition=lambda batch:(None,torch.zeros(1,2048,2,8,8),None)
    source=runtime/'cosmos_predict2/_src/predict2/models/video2world_model_rectified_flow.py'
    assert hashlib.sha256(source.read_bytes()).hexdigest()=='9b53e3f024e5cbb2cb3778819e1a6fd353923c13ad9b868d99602051640a65e8'
    tree=ast.parse(source.read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Video2WorldModelRectifiedFlow')
    nodes=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in ('denoise','get_velocity_fn_from_batch')]
    ns=dict(wc.worldcache_mini_train_dit_forward.__globals__,NUM_CONDITIONAL_FRAMES_KEY='num_conditional_frames',
        parallel_state=types.SimpleNamespace(is_initialized=lambda:False))
    future=ast.ImportFrom(module='__future__',names=[ast.alias(name='annotations')],level=0)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[future,*nodes],type_ignores=[])),str(source),'exec'),ns)
    for name in ('denoise','get_velocity_fn_from_batch'):setattr(model,name,types.MethodType(ns[name],model))
    model.config.conditional_frame_timestep=-1;model.config.denoise_replace_gt_frames=True
    model.config.min_num_conditional_frames=model.config.max_num_conditional_frames=0
    model.config.conditional_frames_probs=None
    mode=establish_shared_eval(net);settings={**settings,'probe_depth':2,'worldcache_rel_l1_thresh':.06}
    config={'sample_names':['human'],'run_id':'CPU_CFG_TEACHER','logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30)}
    contexts=[(config['run_id']+':human','toy_model','condition:human')];checks=[]
    failures=[] if not flow else ['second_CFG','nested_writer','condition_mutation','solver_mutation','nonfinite','mode_mutation']
    try:
        for scenario in ['complete']+failures:
            actual_denoise=types.MethodType(ns['denoise'],model)
            def faulted_denoise(*args,**kwargs):
                value=actual_denoise(*args,**kwargs)
                router=getattr(net,'_wc_rv0_router',None)
                if router is not None and router.plan is not None and router.plan.mode=='DD' and router.calls==46:
                    if scenario=='condition_mutation':args[3].gt_frames.add_(1)
                    if scenario=='solver_mutation':model.sample_scheduler._step_index+=1
                    if scenario=='nonfinite':value=value.clone();value.reshape(-1)[0]=float('nan')
                    if scenario=='mode_mutation':net.blocks[-1].training=True
                return value
            model.denoise=faulted_denoise
            def measurement(fork,label,cell,**kwargs):
                if scenario=='second_CFG' and fork.completed==22 and label=='DD_second':
                    original_decide=fork.router.decide
                    def fail_second(*args):
                        if fork.router.calls==46:raise ValueError('CPU injected second CFG failure')
                        return original_decide(*args)
                    fork.router.decide=fail_second
                    try:return old[4](fork,label,cell,**kwargs)
                    finally:fork.router.decide=original_decide
                return old[4](fork,label,cell,**kwargs)
            GuidedTeacherFork.measure=measurement
            def writer(path,tensors):
                if scenario=='nested_writer' and 'S23_after_DC' in str(path) and path.name=='CD_second.pt':
                    raise ValueError('CPU injected nested vector writer failure')
                return vector_artifact(path,tensors)
            state={};error=None
            if artifact_root is not None:
                target=Path(artifact_root)/('flow_ON' if flow else 'flow_OFF')/scenario
                target.mkdir(parents=True,exist_ok=False)
                storage=nullcontext(str(target))
            else:
                storage=tempfile.TemporaryDirectory(prefix='cfg-teacher-core-')
            with storage as tmp:
                try:
                    run_teacher_batch(inference,samples,wc,settings,state=state,save=lambda:None,output=Path(tmp),
                        inference_module=inference_module,contexts=contexts,mode_setup=mode,runtime=runtime,config=config,writer=writer)
                except BaseException as exc:error=str(exc)
                (Path(tmp)/'complete-scope-receipt.json').write_text(json.dumps(state,indent=2,allow_nan=False)+'\n')
                assert (state['planned_parents'],state['planned_origins'],state['planned_CFG_pairs'],state['planned_videos'])==(2,5,40,2)
                if scenario=='complete':
                    assert error is None,error
                    verdict=verify_batch(state);assert verdict['strict_repeat_groups']==20
                    origins=state['parents'][1]['origins'];metrics=[]
                    for origin in origins:
                        cells={}
                        for record in origin['pairs']:
                            art=record['artifact'];p=Path(art['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==art['sha256']
                            raw=torch.load(p,weights_only=True)
                            assert torch.equal(guided(raw['conditional'],raw['unconditional'],7),raw['guided'])
                            if record['label'].endswith('_first'):cells[record['mode']]={k:raw[k] for k in ('conditional','unconditional')}
                        metrics.append(score_four_cells(cells,guidance=7,measurement_space=SPACE))
                    assert len(list(Path(tmp).rglob('*.pt')))==40
                    refused=[]
                    for name in ['missing_origin','missing_repeat','wrong_pair_output','wrong_condition','wrong_action']:
                        bad=copy.deepcopy(state)
                        if name=='missing_origin':bad['parents'][1]['origins'].pop()
                        elif name=='missing_repeat':bad['parents'][1]['origins'][0]['pairs'].pop()
                        elif name=='wrong_pair_output':bad['parents'][1]['origins'][0]['pairs'][1]['actual_guided_sha256']='0'*64
                        elif name=='wrong_condition':bad['parents'][1]['origins'][0]['pairs'][1]['denoise_arguments'][0]['condition_values']='0'*64
                        elif name=='wrong_action':bad['parents'][1]['origins'][0]['pairs'][0]['action_report']['plan']['mode']='CD'
                        try:verify_batch(bad)
                        except ValueError:refused.append(name)
                        else:raise AssertionError('Incomplete/mutated teacher evidence accepted: '+name)
                    checks.append({'scenario':scenario,'flow':flow,'receipt':state,'CPU_Toy_metrics_not_real_model':metrics,
                        'complete_pair_rows':40,'complete_mock_videos':2,'semantic_mutation_rejections':refused})
                else:
                    assert error and state['parents'][-1]['status']=='TECH_BLOCKED_RETAINED_SCOPE',(scenario,error)
                    origins=state['parents'][-1]['origins'];assert len(origins)==5
                    failed=[r for o in origins for r in o['pairs'] if r['status']=='TECH_BLOCKED_RETAINED_COMPLETE_SCOPE']
                    assert failed and all(r['parent_restored'] for r in failed)
                    checks.append({'scenario':scenario,'flow':flow,'error':error,'receipt':state,
                        'complete_scope_retained':True,'all_failed_forks_restored':True})
            assert all(float(b)==0 for b in net.buffers()) and not any(m.training for m in net.modules())
            assert not hasattr(net,'_wc_rv0_router')
        return checks
    finally:
        net.prepare_embedded_sequence=old[0];model.conditioner.get_condition_with_negative_prompt=old[1]
        model.get_velocity_fn_from_batch=old[2];model.denoise=old[3];GuidedTeacherFork.measure=old[4]
        model.get_data_and_condition=old[5]
        vars(model.config).clear();vars(model.config).update(config_before)


def run(runtime,artifact_root=None):
    result=load('check_full_sampling').run(Path(runtime),exercise=lambda **kwargs:exercise(
        runtime=Path(runtime),artifact_root=artifact_root,**kwargs))
    assert len(result['checks'])==8 and not torch.cuda.is_initialized()
    result.update(status='CFG_TEACHER_COMPLETE_COLLECTOR_CPU_Toy_PASS_NOT_GPU',successful_full_parents=4,
        successful_origins=10,successful_CFG_pairs=80,successful_mock_videos=4,failed_attempts_retained=6,
        strict_repeat_groups=40,source_actual_denoise_and_CFG_closure=True,CUDA_initialized=False,GPU_submissions=0)
    return result
