"""Bind the frozen N09 full40 modes to the unchanged inference/profile paths.

This adapter selects no methods, changes no sampler, and grants no GPU access.
Its formal paths diagnose execution overhead; none is a clean timing repeat.
"""
import copy
import json
from pathlib import Path
import time

from .balanced_repeat_execution_r1 import observed_timers, prepare_samples
from .balanced_repeat_timing_r1 import matrix, SLOTS
from .deployment_profile_r1 import RequestProfile, profile_execution
from .frozen_shared_execution_r1 import execute
from .frozen_shared_production_r1 import audit_row as original_outcome_audit, full_rows as original_prefix

COUNTS = dict(requests=2, methods=5, formal_profile_control_paths=30, full_warmup_paths=10,
    total_paths=40, ordinary_pairs=1440, ordinary_CFG_calls=2880, loads=1, online_teacher_pairs=0,
    profiled_paths=20, original_full_audit_formal_paths=10, profile_full_audit_formal_paths=10,
    profile_lean_formal_paths=10, all_guided_parity_pairs=10,
    profile_audit_lean_endpoint_parity_pairs=10, accepted_video_expected_frames=93)
BINDINGS = dict(FULL_NATIVE='NATIVE35', WORLD_CACHE='WC_HALF', RA_CFG_CACHE='RA_DEFAULT',
                GCR_EFFICIENT='A_NO_P', CPA_HIGH_FIDELITY='TABLE_PHASE_H1')
MODES = {0:'ORIGINAL_AUDIT_WARMUP', 1:'ORIGINAL_AUDIT', 2:'PROFILE_AUDIT', 3:'PROFILE_LEAN'}


def plan(bindings):
    result=[]
    for original in matrix():
        row=copy.deepcopy(original); row['id']='n09_runtime_'+row['id']
        row.update(method=bindings[row['slot']],mode=MODES[row['round']],
            audit_guided=row['round']!=3,component_profile=row['round'] in (2,3),actual_solver_updates=36)
        if row['section']!='WARMUP':row['section']='PROFILE_CONTROL'
        result.append(row)
    return result


def bind(scope, protocol, freeze):
    if (scope['status']!='N09_RUNTIME_FULL40_SCOPE_PREREGISTERED_NOT_PRODUCTION_OR_GPU_CARD'
            or scope['scope_counts']!=COUNTS or scope['method_bindings']!=BINDINGS
            or freeze['repeat_timing_bindings']!=BINDINGS
            or freeze['parameters_frozen_from']!='DEVELOPMENT_ONLY' or freeze['final_test_outputs_seen']
            or scope['requests']!=protocol['requests'] or scope['complete_matrix']!=plan(BINDINGS)
            or len(scope['requests'])!=2 or set(BINDINGS)!=set(SLOTS)
            or not set(BINDINGS.values()).issubset(freeze['method_ids'])
            or not scope['old_exposed_CAL_only'] or not scope['original_N08_scope_unchanged']
            or not scope['scope_is_separate_from_clean_repeated_latency']):
        raise ValueError('Keep all frozen five roles, old two requests and original40 profile/control positions')
    for request in scope['requests']:
        if (request['seed']!=0 or request['num_steps']!=35 or request['guidance']!=7
                or request['num_output_frames']!=93 or request['resolution']!='432,768'):
            raise ValueError('The old profile requests retain original seed, steps and video geometry')
    return dict(status='N09_FULL40_EXECUTION_BOUND_NOT_PRODUCTION_CPU_OR_GPU',
        scope_counts=copy.deepcopy(COUNTS),bindings=copy.deepcopy(BINDINGS),
        final_shared_method_ids=copy.deepcopy(freeze['method_ids']),
        requests=copy.deepcopy(scope['requests']),execution_plan=plan(BINDINGS),
        clean_repeated_latency_claim=False,whole_GPU_card_selected=False)


def audit_row(row, planned, bound):
    if (any(row.get(k)!=v for k,v in planned.items())
            or planned not in bound['execution_plan']
            or planned['method']!=bound['bindings'][planned['slot']]):
        raise ValueError('Original profile mode, method, request and order must remain explicit')
    # Reuse only the original per-request numerical/trace audit. A local copy
    # maps its old warm/formal trace boolean; the actual N09 section is retained.
    mapped={**planned,'case_id':planned['scene'],
            'section':'WARMUP' if planned['audit_guided'] else 'TIMED'}
    original_outcome_audit({**row,**mapped},mapped,
        dict(cases=[dict(id=r['name'],seed=r['seed']) for r in bound['requests']]))
    if row['status'] in ('COMPLETE','VIDEO_REJECTED'):
        return observed_timers(row)
    return None


def execute_one(inference, sample, planned, bound, *, restore_request_state,
                inference_module, device='cuda:0', **kwargs):
    if (planned not in bound['execution_plan'] or sample.name!=planned['scene']
            or sample.seed!=0 or sample.num_steps!=35
            or planned['method']!=bound['bindings'][planned['slot']]
            or any(name in kwargs for name in ('audit','profile'))):
        raise ValueError('Use the registered original profile mode and actual sample')
    restored=restore_request_state();origin=restored['original_state_sha256']
    if (not isinstance(origin,str) or len(origin)!=64 or any(c not in '0123456789abcdef' for c in origin)
            or restored['restored_state_sha256']!=origin or restored['shared_eval_verified'] is not True):
        raise ValueError('Restore original request/scheduler/RNG and shared eval before profiling')
    context=(profile_execution(inference,inference_module=inference_module,
        probe_depth=kwargs['settings']['probe_depth'],device=device) if planned['component_profile']
        else RequestProfile(device=device))
    with context as observer:
        result=execute(inference,sample,planned['method'],inference_module=inference_module,
                       audit=planned['audit_guided'],**kwargs)
    summary=observer.summary
    if summary['status']!='PROFILE_COMPLETE':raise ValueError('One original complete request observation required')
    if not planned['component_profile'] and (summary['components'] or summary['intervals']):
        raise ValueError('Original audit controls must not acquire component hooks')
    if result['status'] in ('COMPLETE','VIDEO_REJECTED'):
        guided=result.get('guided')
        if planned['audit_guided']:
            if not isinstance(guided,list) or len(guided)!=36:
                raise ValueError('All36 actual guided tensors required for each registered audit path')
            result['warm_guided_outputs']=len(guided)  # Original numerical audit's trace-count field.
        elif guided is not None:
            raise ValueError('Lean profile must omit research guided copies')
    timers=audit_row({**planned,**result},planned,bound)
    memory={k:copy.deepcopy(summary[k]) for k in ('device','memory_before','memory_after',
        'peak_reset_before_request','request_profile_wall_seconds')}
    return dict(result,timing_intervals=timers,pre_request_state_identity=restored,
        request_memory_observation=memory,component_profile_summary=summary if planned['component_profile'] else None,
        clean_repeated_latency_claim=False,profile_control_mode=planned['mode'])


def archive_output(result, planned, directory, output_root, *, expected_shape):
    """Save original CPU tensors and scalar profile records after request timing."""
    import os
    import torch
    from .mid_coverage import tree_digest
    from .frozen_shared_production_r1 import sha
    directory,output_root=Path(directory).resolve(),Path(output_root).resolve()
    if not directory.is_relative_to(output_root):raise ValueError('Keep all original profile artifacts in their run')
    row=dict(result);guided=row.pop('guided',None);final=row.pop('final_latent',None)
    summary=row.pop('component_profile_summary',None)
    if (summary is not None)!=planned['component_profile']:
        raise ValueError('Every profiled path needs its original scalar record; controls have no component record')
    if row['status']=='TEXT_REJECTED':
        if guided is not None or final is not None:raise ValueError('Text rejection cannot contain model tensors')
    elif row['status'] in ('COMPLETE','VIDEO_REJECTED'):
        def tensor(value):
            return (isinstance(value,torch.Tensor) and value.device.type=='cpu'
                and tuple(value.shape)==tuple(expected_shape) and bool(torch.isfinite(value).all()))
        if (not tensor(final) or (planned['audit_guided'] and
                (not isinstance(guided,list) or len(guided)!=36 or not all(tensor(t) for t in guided)))
                or (not planned['audit_guided'] and guided is not None)):
            raise ValueError('Every actual finite final/full36 audit tensor must match original shape and mode')
    else:raise ValueError('Only actual original generation outcomes can be archived')
    directory.mkdir(parents=True,exist_ok=True)
    def save(name,value,*,scalar=False):
        path=directory/name
        with path.open('xb') as handle:
            if scalar:handle.write((json.dumps(value,ensure_ascii=False,allow_nan=False,indent=2)+'\n').encode())
            else:torch.save(value,handle)
            handle.flush();os.fsync(handle.fileno())
        return dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size)
    if final is not None:
        row.update(final_latent_sha256=tree_digest(final),final_artifact=save('final-latent.pt',{'final_latent':final}))
    if guided is not None:
        row.update(guided_outputs=36,guided_tree_sha256=tree_digest(guided),
                   guided_artifact=save('guided.pt',{'guided':guided}))
    if summary is not None:
        if not planned['component_profile']:raise ValueError('No component profile on original controls')
        row.update(component_profile_artifact=save('profile-scalars.json',summary,scalar=True),
            profile_components=copy.deepcopy(summary['components']))
    if row.get('video_path'):
        video=Path(row['video_path']).resolve()
        if not video.is_relative_to(directory):raise ValueError('Original video belongs to another profile path')
        row['video_path']=str(video)
    return row


def run_registered_batch(bound, samples, run_one, *, save=lambda state:None):
    if (bound['scope_counts']!=COUNTS or bound['bindings']!=BINDINGS
            or bound['execution_plan']!=plan(bound['bindings'])):
        raise ValueError('Keep every original full40 request/control position')
    if set(samples)!={(r['scene'],r['slot']) for r in bound['execution_plan']}:
        raise ValueError('All ten original typed request/role variants required')
    state=dict(status='N09_FULL40_RUNNING',scope_counts=copy.deepcopy(COUNTS),runs=[])
    save(state)
    for planned in bound['execution_plan']:
        row={**planned,'status':'RUNNING','started_unix':time.time()};state['runs'].append(row);save(state)
        try:
            row.update(run_one(planned,samples[(planned['scene'],planned['slot'])]),ended_unix=time.time())
            row['timing_intervals']=audit_row(row,planned,bound);save(state)
        except BaseException as error:
            row.update(original_returned_status=row['status'],status='TECH_FAILED',
                error_type=type(error).__name__,error=str(error),ended_unix=time.time())
            state.update(status='N09_FULL40_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED',error=str(error));save(state);raise
    state['status']='N09_FULL40_GPU_COMPLETE_CPU_AUDIT_PENDING';save(state)
    return state


def full_rows(runs,bound):
    return original_prefix(runs,bound['execution_plan'])
