"""Execute all twelve current price diagnostic parents with boundary-only GC.

The normal P_OFF replay and the separately tested ActionPrice16Owner are
called unchanged. No model loading, GPU admission or scientific acceptance.
"""
import copy
from pathlib import Path
import weakref

from . import clean_speed20_r1 as clean
from .math_n2_batch_r1 import execute as original_parent
from .action_price16_collection_r1 import price16_install
from .simple26d_memory_r2 import collect_boundary


class RequestFailure(RuntimeError):
    def __init__(self,error,receipt):
        super().__init__(str(error));self.original_type=type(error).__name__;self.receipt=receipt


def prepare_samples(scope,argument_type):
    if len(scope['requests'])!=4 or len({r['name'] for r in scope['requests']})!=4:
        raise ValueError('Four complete original development requests required')
    result={}
    for row in scope['requests']:
        sample=argument_type(**row)
        if any(sample.model_dump(mode='json').get(k)!=v for k,v in row.items()):
            raise ValueError('Typed original request identity changed')
        result[row['name']]=sample
    return result


def execute_one(inference,sample,planned,*,scope,parameters,checkpoint_reserves,
                restore_request_state,output,**common):
    if (planned not in scope['complete_parent_matrix'] or planned['mode'] not in ('BASELINE','AUDIT','LEAN')
            or sample.name!=planned['scene'] or sample.seed!=0 or sample.num_steps!=35
            or planned['complete_updates']!=36 or planned['gamma']!=parameters['gamma']):
        raise ValueError('Original complete parent, input and frozen readout identity required')
    if (not inference.rank0 or inference.text_guardrail_runner is None
            or inference.video_guardrail_runner is None):
        raise ValueError('Ordinary guardrails required')
    before=collect_boundary();restored=restore_request_state()
    if (restored['original_state_sha256']!=restored['restored_state_sha256']
            or restored['shared_eval_verified'] is not True):
        raise ValueError('Restore the exact healthy request state and shared eval mode')
    holders={};components=[];old_install=clean.install;result={};partial={}
    def install(*a,**kw):
        value=old_install(*a,**kw)
        components.extend(weakref.ref(c) for c in value[1:] if c is not None)
        return value
    try:
        with clean.patched(clean,'install',install):
            if planned['mode']=='BASELINE':
                result,_=original_parent(inference,sample,'P_OFF',parameters=parameters,output=output,audit=True,**common)
                result['diagnostic_points']=[]
                result['actual_pair_computations']=result.get('guided_pairs',0)
            else:
                selected=[r for r in scope['states'] if r['scene']==sample.name]
                if (len(selected)!=4 or sorted(r['chosen']['step'] for r in selected)!=planned['measured_steps']):
                    raise ValueError('All four preregistered natural positions required')
                directory=Path(output)
                def writer(step,payload):
                    import torch
                    from .mid_coverage import tree_digest
                    from .frozen_shared_production_r1 import sha
                    directory.mkdir(parents=True,exist_ok=True)
                    path=directory/('point-'+str(step)+'.pt')
                    with path.open('xb') as handle:torch.save(payload,handle)
                    return dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size,
                        tensor_sha256=tree_digest(payload))
                with price16_install(clean,inference.pipe.model.sample_scheduler,selected,
                        {**checkpoint_reserves,'action_price_observation_mode':planned['mode']},
                        writer,parameters,holders):
                    result=clean.execute(inference,sample,'KEEP_A_P',output=output,audit=True,**common)
                owner=holders.get('owner')
                result['diagnostic_points']=copy.deepcopy(owner.records) if owner is not None else []
                result['source_history']=copy.deepcopy(owner.deployment.history) if owner is not None else []
                result['actual_pair_computations']=owner.actual_pair_computations if owner is not None else 0
                del owner
        if result['status'] in ('COMPLETE','VIDEO_REJECTED'):
            expected=36 if planned['mode']=='BASELINE' else 100
            if (result['solver_steps']!=36 or result['guided_pairs']!=36
                    or len(result.get('guided',[]))!=36 or result['actual_pair_computations']!=expected
                    or len(result['diagnostic_points'])!=(0 if planned['mode']=='BASELINE' else 4)):
                raise ValueError('Full36 parents and every original state/trial must survive')
    except BaseException as error:
        owner=holders.get('owner')
        if owner is not None:
            partial=dict(diagnostic_points=copy.deepcopy(owner.records),
                actual_pair_computations=owner.actual_pair_computations)
        del owner
        raise RequestFailure(error,partial) from error
    finally:
        holders.clear();after=collect_boundary()
    alive=sum(ref() is not None for ref in components)
    if alive:raise ValueError('Completed diagnostic retained a reachable algorithm component')
    result.update(pre_request_state_identity=restored,observation_mode=planned['mode'],
        complete_parent_identity=copy.deepcopy(planned),new_prices_used_in_parent=False,
        request_memory_lifecycle=dict(before=before,after=after,observed_components=len(components),
            components_alive_after=alive,within_request_algorithm_or_guardrails_changed=False),
        timing_claim='N09_SAME_STATE_INCREMENTAL_ACTION_DIAGNOSTIC_NOT_CLEAN_VIDEO')
    return result


def full_rows(rows,scope):
    plan=scope['complete_parent_matrix']
    if len(plan)!=12 or len(rows)>12 or [r['id'] for r in rows]!=[r['id'] for r in plan[:len(rows)]]:
        raise ValueError('Keep the entire registered12 and the original observed prefix')
    for row,expected in zip(rows,plan):
        if any(row.get(k)!=v for k,v in expected.items()):raise ValueError('Original parent position changed')
    return copy.deepcopy(rows)+[{**p,'status':'NOT_REACHED'} for p in plan[len(rows):]]


def archive_output(result,directory,output_root,*,expected_shape):
    from .runtime_profile40_execution_r1 import archive_output as archive
    # Only its finite full36 tensor/file boundary is reused; no profile mode
    # or timing metadata is changed or invented for an action-price path.
    return archive(result,dict(audit_guided=True,component_profile=False),directory,output_root,
        expected_shape=expected_shape)


def run_registered_batch(scope,samples,run_one,*,save=lambda value:None):
    plan=scope['complete_parent_matrix']
    if (len(plan)!=12 or set(samples)!={p['scene'] for p in plan}
            or sum(p['complete_updates'] for p in plan)!=432):
        raise ValueError('All original12 parent positions required')
    result=dict(status='N09_ACTION12_RUNNING_RAW_CPU_PENDING',runs=[],registered_scope=scope['scope_counts'],
        matrix=copy.deepcopy(plan),GPU_submissions=0,new_prices_deployed=False)
    for planned in plan:
        row=copy.deepcopy(planned);result['runs'].append(row)
        try:
            row.update(run_one(planned,samples[planned['scene']]))
            changed={k:row.get(k) for k,v in planned.items() if row.get(k)!=v}
            if changed:
                row['callback_identity_error']=changed;row.update(planned)
                raise ValueError('The callback changed its original parent identity')
            if row['status'] not in ('COMPLETE','TEXT_REJECTED','VIDEO_REJECTED'):
                raise ValueError('A completed callback must preserve a real guarded outcome')
        except BaseException as error:
            row.update(getattr(error,'receipt',{}));row.update(status='TECH_FAILED',
                error_type=getattr(error,'original_type',type(error).__name__),error=str(error))
            result['status']='N09_ACTION12_TECHNICAL_STOP_FULL_SCOPE_RETAINED';save(result);return result
        save(result)
    result['status']='N09_ACTION12_GPU_EXITED_REQUIRES_FULL_RAW_CPU_AUDIT';save(result)
    return result
