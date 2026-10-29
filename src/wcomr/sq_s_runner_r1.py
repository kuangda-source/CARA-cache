"""Run the complete admitted S matrix and restore the original request state.

This entry consumes an existing inference context. Loading, GPU authority,
allocation billing and final release remain separate caller obligations.
"""
import copy
from pathlib import Path
import time

from .sq_s_batch_r1 import require
from .sq_s_physical_r1 import PhysicalRequests,collect
from .sq_s_resource_guard_r1 import ResourceCheckedRequests


def run_matrix(*,request_kwargs,physical_scope,execution_identity_sha256,
               resource_contract,store,output,initial,before_request,verify_mode,
               save_matrix,save_health,witness=None,CPU_decode_fixture=None):
    """One complete matrix; no retry, model reload or partial scientific choice."""
    require(all(callable(fn) for fn in (before_request,verify_mode,save_matrix,save_health)),
        'Original storage, mode and receipt callbacks required')
    require(request_kwargs['sink'] is store,'The same bounded streaming store must receive every S row')
    require(not getattr(store,'_s_runner_consumed',False) and not Path(output).exists(),
        'Original S runner attempt exists; recover without retry')
    store._s_runner_consumed=True
    scope=request_kwargs['scope'];host=physical_scope['host']
    model=request_kwargs['inference'].pipe.model;net=model.net
    parameters=[(name,value,value._version,str(value.dtype)) for name,value in net.named_parameters()]
    origin=initial.fingerprint();started=time.monotonic()
    health=dict(status='S_MATRIX_PREPARING',host=host,CPU_fixture=scope['CPU_fixture_only'],
        upper_scope_sha256=scope['scope_sha256'],physical_scope_sha256=physical_scope['physical_scope_sha256'],
        execution_identity_sha256=execution_identity_sha256,
        resource_contract_sha256=resource_contract['contract_sha256'],attempted_new_role_ids=[],
        original_state_restored=False,parameters_and_precision_unchanged=False,
        actual_scientific_labels_accepted=False,GPU_released=False,central_cost_settled=False)
    save_health(copy.deepcopy(health))

    def unchanged():
        require(all(value._version==version and str(value.dtype)==dtype
                    for _,value,version,dtype in parameters),'S changed original model parameters or precision')
        verify_mode()

    def before(slot):
        # Consume the original role before any callback/forward. A failed role
        # remains attempted in the durable operational receipt.
        health['attempted_new_role_ids'].append(slot['id'])
        health.update(status='S_MATRIX_ROLE_ATTEMPTED',current_role=slot['id'])
        save_health(copy.deepcopy(health))
        before_request(slot)
        initial.restore()
        require(initial.fingerprint()==origin,'S request reset differs from the original full state')
        unchanged()

    matrix=None
    try:
        base=ResourceCheckedRequests(resource_contract=resource_contract,**request_kwargs)
        adapter=PhysicalRequests(base,physical_scope,execution_identity_sha256,witness=witness,
            CPU_decode_fixture=CPU_decode_fixture,production_context=request_kwargs.get('production_context'))
        matrix=collect(adapter,output,before_request=before,storage=store,save=save_matrix)
        expected=[slot['id'] for slot in physical_scope['physical_slots']]
        require(health['attempted_new_role_ids']==expected and base.seen==set(expected)
            and adapter.seen=={slot['id'] for slot in scope['slots']},
            'Complete physical and logical S role denominator required')
        require(len(base.resource_checks)==108 and len(matrix['OFF_ON_controls'])==4
            and (matrix['storage']['measured_rows'],matrix['storage']['raw_states'],
                 matrix['storage']['unique_anchor_files'])==(108,8,24),
            'Complete108 guards, four OFF/ON controls and eight raw/24 anchors required')
        health.update(status='S_MATRIX_DATA_COMPLETE_AWAITING_RESET')
    except BaseException as error:
        health.update(status='S_MATRIX_FAILED_RETAINED_NO_RETRY',error_type=type(error).__name__,error=str(error))
        raise
    finally:
        try:
            initial.restore()
            require(initial.fingerprint()==origin,'S final complete-state restoration failed')
            unchanged()
            health.update(original_state_restored=True,parameters_and_precision_unchanged=True)
        except BaseException as error:
            health.update(status='S_MATRIX_FAILED_RETAINED_NO_RETRY',
                restoration_error_type=type(error).__name__,restoration_error=str(error))
            raise
        finally:
            health.update(matrix_wall_seconds=time.monotonic()-started)
            save_health(copy.deepcopy(health))
    result=dict(status='S_COMPLETE_MATRIX_AWAITING_MODEL_CLEANUP_AND_ALLOCATION_TERMINAL',
        CPU_fixture=scope['CPU_fixture_only'],host=host,matrix=matrix,
        upper_scope_sha256=scope['scope_sha256'],physical_scope_sha256=physical_scope['physical_scope_sha256'],
        execution_identity_sha256=execution_identity_sha256,
        resource_contract_sha256=resource_contract['contract_sha256'],
        resource_checks=copy.deepcopy(base.resource_checks),
        attempted_new_role_ids=list(health['attempted_new_role_ids']),
        original_state_restored=True,parameters_and_precision_unchanged=True,
        actual_scientific_labels_accepted=False,GPU_released=False,central_cost_settled=False)
    health.update(status=result['status']);save_health(copy.deepcopy(health))
    return result


def check_complete_matrix(result,upper,physical,identity_sha256,contract_sha256,*,CPU_fixture=False):
    """Accept only this entry's full data cohort, never original GPU release."""
    require(type(CPU_fixture) is bool and result['CPU_fixture']==upper['CPU_fixture_only']==CPU_fixture,
        'S real/CPU evidence boundary differs')
    require(result['status']=='S_COMPLETE_MATRIX_AWAITING_MODEL_CLEANUP_AND_ALLOCATION_TERMINAL'
        and result['host']==physical['host']
        and result['upper_scope_sha256']==upper['scope_sha256']
        and result['physical_scope_sha256']==physical['physical_scope_sha256']
        and result['execution_identity_sha256']==identity_sha256
        and result['resource_contract_sha256']==contract_sha256,
        'Original S matrix entry or scope binding differs')
    matrix=result['matrix'];counts=physical['counts'];execution=matrix['physical_execution']
    require(matrix['status']=='COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE'
        and matrix['scope_sha256']==upper['scope_sha256'] and matrix['counts']==upper['counts']
        and len(matrix['rows'])==counts['logical_paths']==10
        and execution['scope']==physical and execution['actual_new_paths']==counts['new_paths']
        and execution['actual_imported_OFF']==counts['reused_OFF_paths']
        and result['attempted_new_role_ids']==[s['id'] for s in physical['physical_slots']],
        'Full logical/physical S role cohort differs')
    from .sq_risk_r1 import TARGETS
    from .sq_s_sources_r1 import PARENTS
    witnesses={};moments=[]
    for row,slot in zip(matrix['rows'],upper['slots']):
        value=row['result'];policy=upper['policies'][slot['parent']]
        require(row['slot']==slot and row['status']=='COMPLETE' and value['status']=='COMPLETE'
            and value['CPU_fixture']==CPU_fixture and value['solver_steps']==len(value['guided'])==36
            and value['policy_fingerprint']==policy['fingerprint']
            and value['semantic_actions']==policy['actions'],'S role, policy or full36 witness differs')
        selected=list(TARGETS) if slot['enabled'] else []
        require([r['step'] for r in value['S_rows']]==selected
            and all(r['prompt']==slot['prompt'] and r['parent']==slot['parent']
                and r['parent_roundtrip_equal'] is True and r['teacher_writes_parent'] is False
                and r['source']['source_captured_before_parent_pair'] is True
                and r['source']['current_D_in_source'] is False
                and tuple(r['source']['source_anchor_steps'])==tuple(t for t in PARENTS[slot['parent']] if t<r['step'])[-2:]
                for r in value['S_rows']),'S moment source or complete27/zero cohort differs')
        moments.extend(value['S_rows'])
        if slot['purpose']=='CONTROL':
            key=(slot['prompt'],slot['parent'])
            if key in witnesses:
                other=witnesses.pop(key)
                require(all(value[k]==other[k] for k in ('guided','final_latent','RGB','semantic_actions')),
                    'Original complete OFF/ON result bytes differ')
                if 'pre_encoding_RGB' in value and 'pre_encoding_RGB' in other:
                    require(value['pre_encoding_RGB']==other['pre_encoding_RGB'],
                        'Original fresh OFF/ON pre-encoding RGB differs')
            else:witnesses[key]=value
    require(not witnesses and len(moments)==108
        and sum(r['extra_Dense_teacher_pairs'] for r in moments)==56
        and sum(r['extra_C_readout_pairs'] for r in moments)==52
        and sum(r['extra_Dense_hidden_replay_heads'] for r in moments)==0,
        'Original108/56/52 same-state S denominator differs')
    expected={(s['prompt'],s['parent']) for s in upper['slots'] if s['purpose']=='CONTROL'}
    require(len(matrix['OFF_ON_controls'])==len(execution['OFF_ON_controls'])==len(expected)==4
        and {(r['prompt'],r['parent']) for r in matrix['OFF_ON_controls']}==expected
        and all(r['exact'] is True for r in matrix['OFF_ON_controls'])
        and all(r['exact'] is True and (r['pre_encoding_RGB_compared'] or
            (physical['host']=='two_card' and r['retained_OFF_has_no_pre_encoding_pixels']))
            for r in execution['OFF_ON_controls']),'All four full S OFF/ON controls required')
    checks=result['resource_checks']
    selected=[(s['id'],step) for s in upper['slots'] if s['enabled']
              for step in range(8,36) if step!=24]
    require([(r['slot_id'],r['step']) for r in checks]==selected and len(checks)==108
        and all(r['contract_sha256']==contract_sha256 and r['all_eight_groups_checked']
            and not r['tensor_values_read'] and r['tensor_copies_performed']==0 for r in checks),
        'All108 original pre-snapshot guards required')
    require((matrix['storage']['measured_rows'],matrix['storage']['raw_states'],
             matrix['storage']['unique_anchor_files'])==(108,8,24)
        and result['original_state_restored'] is True and result['parameters_and_precision_unchanged'] is True
        and result['actual_scientific_labels_accepted'] is False
        and result['GPU_released'] is False and result['central_cost_settled'] is False,
        'S data completion cannot imply scientific, GPU release or financial acceptance')
    return dict(status='S_COMPLETE_MATRIX_DATA_ACCEPTED_PENDING_ORIGINAL_ALLOCATION',
        logical_paths=10,new_paths=counts['new_paths'],reused_OFF_paths=counts['reused_OFF_paths'],
        complete_same_state_rows=108,raw_states=8,unique_anchor_files=24,CPU_fixture=CPU_fixture,
        original_GPU_release_accepted=False,original_financial_settlement_accepted=False)
