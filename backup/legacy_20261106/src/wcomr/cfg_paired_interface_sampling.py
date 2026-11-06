"""Two complete guarded native WC parents and one restored local interface.

No full counterfactual suffix, candidate routing policy or endpoint label.
All sixteen same-origin pair rows are required; every tensor is retained.
"""
import copy
from pathlib import Path
import time
import torch

from .cfg_paired_local_interface import PairedLocalInterface, verify_comparisons
from .cfg_teacher_sampling import vector_artifact
from .cfg_teacher_measurement import net_input_witness, solver_return_witness, origin_witness
from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .h0_mode import verify_shared_eval
from .light_sampling import Hooks,synchronize
from .mid_coverage import WC_FIELDS,tree_digest
from .prepared_input import input_signatures
from .rv0_causal import TRACE_KEYS,artifact,model_guardrail_missing,pipeline_hooks
from .rv0_cfg_budget_evaluation import solver_configuration
from .rv0_fork import WC_CONFIGURATION,official_suffix,object_state
from .rv0_restore import capture_inventory,capture_gate,cuda_memory_observation


def verify_batch(state):
    if (state['planned_parents'],state['planned_videos'],state['planned_local_pairs'])!=(2,2,16) or len(state['parents'])!=2:
        raise ValueError('Complete two-parent/sixteen-pair interface scope required')
    off,on=state['parents']
    keys=tuple(TRACE_KEYS)+('net_measurements','solver_measurements','final_components','final_solver_configuration',
        'sample_return_sha256','final_latent_sha256','flags_before','flags_after','pipeline')
    parity={k:off[k]==on[k] for k in keys}
    parity['video_bytes']=off['artifact']['sha256']==on['artifact']['sha256']
    if not all(parity.values()):raise ValueError('Local interface changed native full parent: '+str(parity))
    for row in (off,on):
        if row['status']!='COMPLETE_PARENT' or len(row['inputs'])!=72 or len(row['solver_outputs'])!=36:
            raise ValueError('Complete native parent missing')
        if len(row['net_measurements'])!=72 or len(row['solver_measurements'])!=36:
            raise ValueError('Full parent measurement coverage missing')
    origin=on['origin']
    if off['origin'] is not None or origin['status']!='COMPLETE_INTERFACE_ORIGIN':
        raise ValueError('Single actual completed S22 origin required')
    result=verify_comparisons(origin['pairs'])
    for row in origin['pairs']:
        if set(row['artifact']['tensor_sha256'])!={'conditional','unconditional','guided'}:
            raise ValueError('All actual branch/guided tensor artifacts required')
        if [row['artifact']['tensor_sha256'][k] for k in ('conditional','unconditional')]!=row['branch_sha256'] or row['artifact']['tensor_sha256']['guided']!=row['guided_sha256']:
            raise ValueError('Actual output artifact binding differs')
    return {**result,'full_parent_parity':parity,'actual_state_origins':1,'raw_tensor_count':48,
            'observer_net_events':32,'candidate_full_sampler_policy':False}


def run_interface_batch(inference,samples,wc,settings,*,state,save,output,inference_module,
        contexts,mode_setup,runtime,config,rf_module,writer=vector_artifact):
    if (len(samples)!=1 or len(contexts)!=1 or [s.name for s in samples]!=config['sample_names']
            or samples[0].num_steps!=35 or inference.pipe.offload_diffusion_model or not inference.rank0
            or model_guardrail_missing(inference) or state.get('parents')):
        raise ValueError('Independent complete guarded interface batch required')
    model,net=inference.pipe.model,inference.pipe.model.net;scheduler=model.sample_scheduler
    suffix=official_suffix(runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py')
    initial=CompleteStateRoundtrip(net,scheduler,torch.zeros(1));initial_sha=initial.fingerprint()
    old_forward=net.forward
    old_config={k:copy.deepcopy(getattr(net,k)) for k in WC_CONFIGURATION if hasattr(net,k)}
    old_keys={k for k in WC_FIELDS if hasattr(net,k)}
    sample,context=samples[0],contexts[0]
    if context[0]!=config['run_id']+':'+sample.name:raise ValueError('Interface request identity differs')
    state.update(planned_parents=2,planned_videos=2,planned_local_pairs=16,planned_comparisons=8,
        parents=[],endpoint_labels=0,future_cost_labels=0,teacher_written_to_parent=False)
    save()
    try:
        for phase in ('OFF','ON'):
            initial.restore();verify_shared_eval(net,mode_setup)
            wc.apply_worldcache(net,**{k.removeprefix('worldcache_'):v for k,v in settings.items()})
            row={'phase':phase,'status':'STARTED',**{k:[] for k in TRACE_KEYS},'pipeline':[],
                'origin':None,'net_measurements':[],'solver_measurements':[],'prepare_calls':0,
                'flags_before':backend_flags(),'memory_before':cuda_memory_observation()}
            state['parents'].append(row);save()
            hooks,handles=Hooks(),[];capture={};deep=[0]
            try:
                pipeline_hooks(hooks,model,inference_module,row)
                hooks.wrap(inference.pipe,'_get_data_batch_input',after=lambda v:row.update(prepare_calls=row['prepare_calls']+1))
                hooks.wrap(model,'get_velocity_fn_from_batch',after=lambda v:capture.update(velocity=v))
                hooks.wrap(model,'denoise',before=lambda a,k:capture.update(noise=a[0]))
                for block in list(net.blocks)[settings['probe_depth']:]:
                    handles.append(block.register_forward_hook(lambda *a:deep.__setitem__(0,deep[0]+1)))
                def before_forward(args,kwargs):
                    row['inputs'].append(input_signatures(args,kwargs));deep[0]=0
                    row['net_measurements'].append(net_input_witness(args,kwargs))
                def after_forward(value):
                    row['outputs'].append(tree_digest(value));row['deep'].append(deep[0])
                    row['banks'].append(tree_digest({k:getattr(net,k) for k in WC_FIELDS if hasattr(net,k)}))
                hooks.wrap(net,'forward',before=before_forward,after=after_forward)
                def after_step(value):
                    row['solver_outputs'].append(tree_digest(value));row['solver_measurements'].append(solver_return_witness(value))
                    latent=value[0].squeeze(0)
                    if scheduler._step_index==36:
                        final=CompleteStateRoundtrip(net,scheduler,latent,[capture['generator']])
                        row.update(final_latent_sha256=tree_digest(latent),final_components=final.components(),
                            final_solver_configuration=solver_configuration(scheduler))
                    if phase!='ON' or scheduler._step_index!=22:return
                    inventory=capture_inventory(net,scheduler,latent,capture['noise'],capture['velocity'])
                    reserve=config['workspace_reserve_bytes']+config['paired_prefix_reserve_bytes']
                    gate=capture_gate(inventory,logical_copy_cap_bytes=config['logical_copy_cap_bytes'],
                        transient_copy_factor=2,workspace_reserve_bytes=reserve,
                        available_gpu_bytes=torch.cuda.mem_get_info()[0] if latent.is_cuda else None)
                    origin={'label':'S22','status':'STARTED','pairs':[],'capture_inventory':inventory,'capture_gate':gate,
                        'origin_measurement':origin_witness(latent,capture['noise'])}
                    row['origin']=origin;save()
                    fork=PairedLocalInterface(model,latent,capture['noise'],capture['generator'],capture['velocity'],suffix,
                        context=context,runtime=runtime,wc_module=wc,rf_module=rf_module)
                    origin['pairs']=fork.records;origin['origin_components']=fork.snapshot.components()
                    origin['frozen_condition_values_sha256']=tree_digest([object_state(c) for c in fork.conditions])
                    if len(origin['origin_components'])!=config['expected_components'] or list(latent.shape)!=config['expected_shape']:
                        raise ValueError('Actual interface snapshot component/shape differs from admission')
                    try:
                        for action in ('CC','DD'):
                            for observers in (False,True):
                                for repetition in ('first','second'):
                                    for order in ('ORIGINAL','PAIRED'):
                                        label='_'.join((action,'OBS_ON' if observers else 'OBS_OFF',repetition,order))
                                        save();pair=fork.measure(label,action,order,observers);pair['repetition']=repetition
                                        pair['artifact']=writer(output/sample.name/'vectors'/(label+'.pt'),fork.last_tensors)
                                        save()
                        origin.update(verification=verify_comparisons(origin['pairs']),status='COMPLETE_INTERFACE_ORIGIN');save()
                    except BaseException as error:
                        origin.update(status='INTERFACE_TECH_BLOCKED_COMPLETE_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));save();raise
                    finally:fork.restore_parent()
                hooks.wrap(scheduler,'step',before=lambda a,k:capture.update(generator=k['generator']),after=after_step)
                hooks.wrap(model,'generate_samples_from_batch',after=lambda v:row.update(sample_return_sha256=tree_digest(v)))
                synchronize();started=time.perf_counter();paths=inference.generate([sample],output_dir=output/sample.name/phase)
                synchronize();row.update(wall_seconds=time.perf_counter()-started,flags_after=backend_flags(),
                    artifact=artifact(paths[0]) if len(paths)==1 else None)
                if row['artifact'] is None or row['prepare_calls']!=1 or net.cnt!=2:raise ValueError('Complete native parent output missing')
                row['status']='COMPLETE_PARENT';save()
            except BaseException as error:
                row.update(status='INTERFACE_PARENT_TECH_BLOCKED_COMPLETE_SCOPE_RETAINED',error_type=type(error).__name__,error=str(error));save();raise
            finally:
                hooks.close()
                for handle in handles:handle.remove()
        state.update(verdict=verify_batch(state),status='REAL_PAIRED_INTERFACE_CORE_COMPLETE_REQUIRES_RAW_CPU_AUDIT');save()
    finally:
        initial.restore();net.forward=old_forward
        for key in set(WC_FIELDS)-old_keys:
            if hasattr(net,key):delattr(net,key)
        for key,value in old_config.items():setattr(net,key,value)
        assert initial.fingerprint()==initial_sha
