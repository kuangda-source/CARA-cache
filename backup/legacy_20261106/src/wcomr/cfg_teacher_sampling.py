"""Two complete guarded OFF/ON parents with all five restored CFG teacher origins."""
import copy
import hashlib
from pathlib import Path
import time
import torch

from .cfg_teacher_collection import MODES, TeacherPairRouter, GuidedTeacherFork, verify_origin
from .cfg_teacher_measurement import net_input_witness, solver_return_witness, tensor_witness, validate_net_binding
from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks, synchronize
from .mid_coverage import WC_FIELDS, tree_digest
from .prepared_input import input_signatures
from .rv0_causal import TRACE_KEYS, artifact, model_guardrail_missing, pipeline_hooks
from .rv0_cfg_budget_evaluation import solver_configuration
from .rv0_fork import WC_CONFIGURATION, official_suffix
from .rv0_restore import capture_inventory, capture_gate, cuda_memory_observation

ORIGINS = ('S22', 'S23_after_CC', 'S23_after_DC', 'S23_after_CD', 'S23_after_DD')


def vector_artifact(path, tensors):
    if path.exists() or set(tensors)!={'conditional','unconditional','guided'}:
        raise ValueError('Fresh complete actual branch/guided artifact required')
    path.parent.mkdir(parents=True,exist_ok=True)
    torch.save(tensors,path)
    return {'path':str(path),'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'tensor_sha256':{k:tree_digest(v) for k,v in tensors.items()},
            'shape':{k:list(v.shape) for k,v in tensors.items()},
            'dtype':{k:str(v.dtype) for k,v in tensors.items()},
            'space':'POST_DENOISE_BEFORE_SOLVER'}


def verify_batch(state):
    if (state['planned_parents']!=2 or state['planned_videos']!=2 or state['planned_origins']!=5
            or state['planned_CFG_pairs']!=40 or len(state['parents'])!=2):
        raise ValueError('Complete registered teacher scope required')
    off,on=state['parents']
    parity = {k:off[k]==on[k] for k in tuple(TRACE_KEYS)+('net_measurements','solver_measurements','final_components','final_solver_configuration',
        'sample_return_sha256','final_latent_sha256','flags_before','flags_after','pipeline')}
    parity['video_bytes']=off['artifact']['sha256']==on['artifact']['sha256']
    if not all(parity.values()):
        raise ValueError('Diagnostic changed full parent behavior: '+str(parity))
    origins=on['origins']
    if [o['label'] for o in origins]!=list(ORIGINS) or len(origins)!=5:
        raise ValueError('Missing registered origins; no smaller successful subset')
    origin_checks=[verify_origin(o) for o in origins]
    if any(o['status']!='COMPLETE_LOCAL_ORIGIN' for o in origins):
        raise ValueError('Pending/failed origin retained')
    for row in (off,on):
        if len(row['inputs'])!=72 or len(row['solver_outputs'])!=36 or row['status']!='COMPLETE_PARENT':
            raise ValueError('Incomplete original full parent')
        if len(row.get('net_measurements',[]))!=72 or len(row.get('solver_measurements',[]))!=36:
            raise ValueError('Missing full parent actual measurement spaces')
        for witness,signature in zip(row['net_measurements'],row['inputs']):
            validate_net_binding(witness,signature)
        for witness,raw_sha in zip(row['solver_measurements'],row['solver_outputs']):
            if witness['raw_return_tree_sha256']!=raw_sha:
                raise ValueError('Solver return measurement space binding differs')
    return {'full_parent_parity':parity,'origin_checks':origin_checks,
            'strict_repeat_groups':20,'local_CFG_pairs':40,'diagnostic_net_calls':80,
            'teacher_written_to_original_parent':False,'endpoint_labels':0,'formal_RV_labels':0}


def run_teacher_batch(inference,samples,wc,settings,*,state,save,output,inference_module,
                      contexts,mode_setup,runtime,config,writer=vector_artifact):
    if (len(samples)!=1 or len(contexts)!=1 or [s.name for s in samples]!=config['sample_names']
            or samples[0].num_steps!=35 or inference.pipe.offload_diffusion_model
            or not inference.rank0 or model_guardrail_missing(inference) or state.get('parents')):
        raise ValueError('Independent complete guarded teacher batch required')
    model,net=inference.pipe.model,inference.pipe.model.net
    scheduler=model.sample_scheduler
    suffix=official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));initial_sha=initial.fingerprint()
    original_forward=net.forward
    original_config={k:copy.deepcopy(getattr(net,k)) for k in WC_CONFIGURATION if hasattr(net,k)}
    original_keys={k for k in WC_FIELDS if hasattr(net,k)}
    state.update(planned_parents=2,planned_videos=2,planned_origins=5,planned_CFG_pairs=40,
        planned_diagnostic_net_calls=80,parents=[],teacher_written_to_deployment=False,endpoint_labels=0)
    sample,context=samples[0],contexts[0]
    if context[0]!=config['run_id']+':'+sample.name:
        raise ValueError('Registered teacher request identity differs')
    save()
    try:
        for phase in ('OFF','ON'):
            initial.restore();verify_shared_eval(net,mode_setup)
            wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
            router=TeacherPairRouter(context)
            router.install(net,wc,runtime/'cosmos_predict2/_src/predict2/inference/worldcache_utils.py')
            row={'phase':phase,'status':'STARTED',**{k:[] for k in TRACE_KEYS},'pipeline':[],
                'origins':[],'net_measurements':[],'solver_measurements':[],
                'prepare_calls':0,'flags_before':backend_flags(),'memory_before':cuda_memory_observation()}
            state['parents'].append(row);save()
            hooks,handles=Hooks(),[];capture={'inside':False,'record':None,'branches':[]};count=[0]
            try:
                pipeline_hooks(hooks,model,inference_module,row)
                hooks.wrap(inference.pipe,'_get_data_batch_input',after=lambda v:row.update(prepare_calls=row['prepare_calls']+1))
                hooks.wrap(model,'get_velocity_fn_from_batch',after=lambda v:capture.update(velocity=v))
                def before_denoise(args,kwargs):
                    capture['noise']=args[0]
                    if capture['record'] is not None:
                        if len(args)!=4 or kwargs:
                            raise ValueError('Pinned positional noise/latent/timestep/condition call required')
                        capture['record']['denoise_arguments'].append({
                            'noise':tree_digest(args[0]),'latent':tree_digest(args[1]),'timestep':tree_digest(args[2]),
                            'condition_class':type(args[3]).__module__+'.'+type(args[3]).__name__,
                            'condition_values':tree_digest(args[3].to_dict(skip_underscore=False))})
                def after_denoise(value):
                    if capture['record'] is not None:
                        capture['record']['post_denoise_branch_sha256'].append(tree_digest(value))
                        capture['record']['post_denoise_measurements'].append(tensor_witness(value))
                        capture['branches'].append(value.detach().cpu().clone())
                hooks.wrap(model,'denoise',before=before_denoise,after=after_denoise)
                for block in list(net.blocks)[settings['probe_depth']:]:
                    handles.append(block.register_forward_hook(lambda *a:count.__setitem__(0,count[0]+1)))
                def destination():
                    return capture['record'] if capture['record'] is not None else row
                def before_forward(args,kwargs):
                    destination()['inputs'].append(input_signatures(args,kwargs));count[0]=0
                    destination()['net_measurements'].append(net_input_witness(args,kwargs))
                def after_forward(value):
                    target=destination();target['outputs'].append(tree_digest(value));target['deep'].append(count[0])
                    target['banks'].append(tree_digest({k:getattr(net,k) for k in WC_FIELDS if hasattr(net,k)}))
                hooks.wrap(net,'forward',before=before_forward,after=after_forward)

                def new_fork(latent,origin):
                    inventory=capture_inventory(net,scheduler,latent,capture['noise'],capture['velocity'])
                    origin['capture_gate']=capture_gate(inventory,logical_copy_cap_bytes=config['logical_copy_cap_bytes'],
                        transient_copy_factor=2,workspace_reserve_bytes=config['workspace_reserve_bytes'],
                        available_gpu_bytes=torch.cuda.mem_get_info()[0] if latent.is_cuda else None)
                    origin['status']='STARTED';save()
                    fork=GuidedTeacherFork(model,latent,capture['noise'],capture['generator'],capture['velocity'],
                        suffix,router=router,context=context,capture=capture,
                        writer=lambda label,tensors:writer(output/sample.name/'vectors'/origin['label']/(label+'.pt'),tensors),save=save)
                    origin['pairs']=fork.records;origin['snapshot_storage']=fork.snapshot_storage()
                    origin['condition_classes']=[type(c).__module__+'.'+type(c).__name__ for c in fork.conditions]
                    return fork

                def child_origin(mode,latent):
                    origin=next(o for o in row['origins'] if o['label']=='S23_after_'+mode)
                    fork=new_fork(latent,origin)
                    try:
                        for child_mode in MODES:
                            for repetition in ('first','second'):
                                fork.measure(child_mode+'_'+repetition,child_mode)
                        origin['verification']=verify_origin(origin);origin['status']='COMPLETE_LOCAL_ORIGIN';save()
                    except BaseException as error:
                        origin.update(status='TECH_BLOCKED_RETAINED_ORIGIN',error_type=type(error).__name__,error=str(error));save();raise
                    finally:
                        fork.restore_parent()

                def after_step(value):
                    destination()['solver_outputs'].append(tree_digest(value))
                    destination()['solver_measurements'].append(solver_return_witness(value))
                    if capture['inside']:
                        return
                    latent=value[0].squeeze(0)
                    if scheduler._step_index==36:
                        final=CompleteStateRoundtrip(net,scheduler,latent,[capture['generator']])
                        row.update(final_latent_sha256=tree_digest(latent),final_components=final.components(),
                            final_solver_configuration=solver_configuration(scheduler))
                    if phase!='ON' or scheduler._step_index!=22:
                        return
                    row['origins']=[{'label':label,'status':'PENDING','pairs':[]} for label in ORIGINS]
                    root=row['origins'][0];fork=new_fork(latent,root)
                    capture['inside']=True
                    try:
                        for mode in MODES:
                            fork.measure(mode+'_first',mode,advance=lambda child,m=mode:child_origin(m,child))
                            fork.measure(mode+'_second',mode)
                        root['verification']=verify_origin(root);root['status']='COMPLETE_LOCAL_ORIGIN';save()
                    except BaseException as error:
                        root.update(status='TECH_BLOCKED_RETAINED_ORIGIN',error_type=type(error).__name__,error=str(error));save();raise
                    finally:
                        fork.restore_parent();capture['record']=None;capture['inside']=False
                hooks.wrap(scheduler,'step',before=lambda args,kwargs:capture.update(generator=kwargs['generator']),after=after_step)
                hooks.wrap(model,'generate_samples_from_batch',after=lambda value:row.update(sample_return_sha256=tree_digest(value)))
                synchronize();started=time.perf_counter()
                paths=inference.generate([sample],output_dir=output/sample.name/phase)
                synchronize();row.update(wall_seconds=time.perf_counter()-started,flags_after=backend_flags(),
                    artifact=artifact(paths[0]) if len(paths)==1 else None)
                if row['artifact'] is None or row['prepare_calls']!=1 or net.cnt!=2:
                    raise ValueError('Complete guarded original parent output missing')
                row['status']='COMPLETE_PARENT';save()
            except BaseException as error:
                row.update(status='TECH_BLOCKED_RETAINED_SCOPE',error_type=type(error).__name__,error=str(error));save();raise
            finally:
                hooks.close()
                for handle in handles:handle.remove()
                router.close()
        state['verdict']=verify_batch(state)
        state['status']='CFG_GUIDED_TEACHER_TWO_PARENT_FIVE_ORIGIN_CORE_COMPLETE_REQUIRES_AUDIT';save()
    finally:
        initial.restore();net.forward=original_forward
        for key in set(WC_FIELDS)-original_keys:
            if hasattr(net,key):delattr(net,key)
        for key,value in original_config.items():setattr(net,key,value)
        assert initial.fingerprint()==initial_sha
