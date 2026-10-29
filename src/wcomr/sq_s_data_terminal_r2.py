"""Torch-free S data acceptance before artifact/release/billing acceptance.

Recompute all scalar FP64 identities and compare the original full witnesses.
This never grants scientific effect, a GPU release, or a free partial cohort.
"""
import hashlib
import json
import math
from pathlib import PurePosixPath

TARGETS=tuple(t for t in range(8,36) if t!=24)
REAL_IDENTITY='2104a9d053fc6e2967de363fa261bb3a514ee5b93a97d7783208bf3f187c32a6'
REAL_RESOURCE='c3f5d742cbd014838104cae6e7d5afc7adfb9b41c01650bf6a311890a500db2b'
EPS64=2.220446049250313e-16


def require(value,message):
    if not value:raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def signature(value):
    return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)


def finite(value):return type(value) in (float,int) and math.isfinite(value)


def check_moments(row):
    m=row['moments'];C,U,K,energy=(m[k] for k in ('C','U','K','teacher_branch_energy'))
    require(all(finite(x) for x in (C,U,K,energy)) and C>=0 and U>=0 and energy>0,
        'Finite S moments and strictly positive common teacher energy required')
    require(m['coefficients']==[8,-7] and m['reduction_dtype']=='FP64'
        and m['normalization']=='MEAN_TEACHER_BRANCH_ENERGY','Original S CFG coefficients/reduction/normalization differ')
    BR=(C+U)/2;DIAG=64*C+49*U;formula=DIAG-112*K
    tolerance=128*EPS64*max(DIAG,abs(-112*K),1e-300)
    require(all(finite(m[k]) for k in ('BR','DIAG','CFG','CFG_formula','identity_abs_error','identity_tolerance'))
        and m['BR']==BR and m['DIAG']==DIAG and m['CFG']>=0 and m['CFG_formula']==formula
        and m['identity_tolerance']==tolerance
        and m['identity_abs_error']==abs(m['CFG']-formula)<=tolerance,
        'Original FP64 S guided identity or cancellation bound differs')
    require(K*K<=C*U+128*EPS64*max(C*U,K*K,1e-300),
        'S cross moment violates its covariance bound')
    require(m['normalized']==dict(BR=BR/energy,DIAG=DIAG/energy,CFG=m['CFG']/energy),
        'Original common teacher-energy normalization differs')


def check_result(result,upper,physical,*,identity_sha256,resource_contract_sha256,
                 expected_shape,new_output_root=None,CPU_fixture=False):
    require(type(CPU_fixture) is bool and upper['CPU_fixture_only']==physical['CPU_fixture_only']==result['CPU_fixture']==CPU_fixture,
        'S real/CPU data boundary differs')
    require(result['actual_CUDA'] is (not CPU_fixture),'A real S CUDA collection cannot use a CPU fixture')
    require(upper['scope_sha256']==digest({k:v for k,v in upper.items() if k!='scope_sha256'})
        and physical['physical_scope_sha256']==digest({k:v for k,v in physical.items() if k!='physical_scope_sha256'})
        and physical['upper_scope_sha256']==upper['scope_sha256']
        and physical['execution_identity_sha256']==identity_sha256,'Original S scope or execution identity differs')
    if not CPU_fixture:
        require(identity_sha256==REAL_IDENTITY and resource_contract_sha256==REAL_RESOURCE
            and expected_shape==[1,16,24,54,96]
            and isinstance(new_output_root,str) and PurePosixPath(new_output_root).is_absolute(),
            'Frozen real S identities and original output root required')
    require(result['status']=='S_COMPLETE_MATRIX_AWAITING_MODEL_CLEANUP_AND_ALLOCATION_TERMINAL'
        and result['host']==physical['host']
        and result['upper_scope_sha256']==upper['scope_sha256']
        and result['physical_scope_sha256']==physical['physical_scope_sha256']
        and result['execution_identity_sha256']==identity_sha256
        and result['resource_contract_sha256']==resource_contract_sha256,
        'Original complete S model/matrix result required')
    model=result['model_entry'];precision=model['precision']
    require(model['status']=='S_MODEL_AND_MATRIX_COMPLETE_AWAITING_ORIGINAL_ALLOCATION_TERMINAL'
        and model['CPU_fixture']==CPU_fixture and model['execution_identity_sha256']==identity_sha256
        and model['physical_scope_sha256']==physical['physical_scope_sha256']
        and model['model_load_attempts']==model['model_loads']==1
        and model['environment_cleanup_attempted'] is True and model['environment_cleanup_accepted'] is True
        and not any(k in model for k in ('error_type','cleanup_error_type'))
        and precision['conditional_frame_timestep']==.1 and precision['use_wan_fp32_strategy'] is True
        and precision['outer_autocast'] is False,'Original single S model load and cleanup are not complete')
    if not CPU_fixture:
        require(precision['model_precision']=='torch.bfloat16' and precision['blocks']==28
            and precision['parameter_tensors']==569 and precision['parameter_dtypes']=={'torch.bfloat16':569}
            and precision['parameter_devices']=={'cuda:0':569},
            'Original real full2B S precision/geometry differs')
    require(all(result[k] is True for k in ('original_state_restored','parameters_and_precision_unchanged'))
        and all(result[k] is False for k in ('actual_scientific_labels_accepted','GPU_released','central_cost_settled'))
        and all(model[k] is False for k in ('actual_scientific_labels_accepted','original_GPU_release_accepted','original_financial_settlement_accepted')),
        'S data cannot substitute for allocation/financial/scientific acceptance')
    matrix=result['matrix'];counts=physical['counts'];execution=matrix['physical_execution']
    require(matrix['status']=='COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE'
        and matrix['scientific_labels_accepted'] is False
        and matrix['scope_sha256']==upper['scope_sha256'] and matrix['counts']==upper['counts']
        and len(matrix['rows'])==len(upper['slots'])==counts['logical_paths']==10
        and execution['scope']==physical and execution['actual_new_paths']==counts['new_paths']
        and execution['actual_imported_OFF']==counts['reused_OFF_paths']
        and execution['actual_GPU_or_scientific_acceptance'] is False
        and result['attempted_new_role_ids']==[s['id'] for s in physical['physical_slots']],
        'Original full S logical/physical denominator differs')
    require(counts['new_paths']+counts['reused_OFF_paths']==10
        and counts['moment_rows']==108 and counts['raw_states']==8 and counts['unique_anchors']==24
        and counts['extra_Dense_teacher_pairs']==56 and counts['extra_C_shadow_pairs']==52,
        'Original S physical target/teacher/shadow scope differs')
    witnesses={};moments=[];raw=[];new_files=[]
    for row,slot in zip(matrix['rows'],upper['slots']):
        value=row['result'];policy=upper['policies'][slot['parent']]
        require(row['slot']==slot and row['status']==value['status']=='COMPLETE'
            and value['CPU_fixture']==CPU_fixture and value['solver_steps']==len(value['guided'])==36
            and value['policy_fingerprint']==policy['fingerprint'] and value['semantic_actions']==policy['actions']
            and value['diagnostic_only_no_clean_clock'] is True,'Original full36 S request/policy differs')
        for tensor in value['guided']+[value['final_latent']]:
            require(tensor['shape']==expected_shape and tensor['dtype'] in ('torch.float32','torch.bfloat16')
                and signature(tensor['sha256']),'Original typed full S guided/latent witness differs')
        require(value['RGB']['frames']==93 and signature(value['RGB']['sha256']),
            'Original complete saved-video RGB witness required')
        selected=TARGETS if slot['enabled'] else ()
        require([m['step'] for m in value['S_rows']]==list(selected),'Original27/zero S row cohort differs')
        dense=tuple(i+1 for i,a in enumerate(policy['actions']) if a=='D')
        for m in value['S_rows']:
            require((m['prompt'],m['parent'])==(slot['prompt'],slot['parent'])
                and m['parent_roundtrip_equal'] is True and m['paid_prefix_equal'] is True
                and m['teacher_writes_parent'] is False and tuple(m['context'])
                and tuple(m['context'])==tuple(m['source']['context'])
                and m['context'][-1]==policy['fingerprint']
                and m['source']['parent']==m['parent'] and m['source']['step']==m['step']
                and m['source']['source_captured_before_parent_pair'] is True
                and m['source']['current_D_in_source'] is False
                and tuple(m['source']['source_anchor_steps'])==tuple(t for t in dense if t<m['step'])[-2:],
                'S moment used a foreign/current-D source or changed its parent')
            is_C=m['step'] not in dense
            chosen=slot['parent']=='F19-C' and m['step'] in (9,22,33,35)
            require(m['extra_Dense_teacher_pairs']==int(is_C) and m['extra_C_readout_pairs']==int(not is_C)
                and m['extra_Dense_hidden_replay_heads']==0 and m['raw_state_selected']==chosen,
                'S per-state teacher/shadow/raw scope differs')
            check_moments(m);moments.append(m)
            if chosen:raw.append((m['prompt'],m['parent'],m['step']))
        if slot['id'] not in physical['reused_slot_ids']:
            pixels=value['pre_encoding_RGB']
            require(signature(pixels['sha256']) and (CPU_fixture or
                (pixels['shape']==[93,432,768,3] and pixels['dtype']=='uint8')),
                'Original fresh S pre-encoding pixel witness required')
            artifact=value['encoded_video'];path=PurePosixPath(artifact['path'])
            require(type(artifact['bytes']) is int and artifact['bytes']>0 and signature(artifact['sha256'])
                and path.is_absolute() and '..' not in path.parts,'Original new S encoded artifact metadata required')
            if new_output_root is not None:
                expected=PurePosixPath(new_output_root)/slot['id']
                require(path.parts[:len(expected.parts)]==expected.parts,'S artifact escaped its original role output')
            new_files.append(artifact['path'])
        if slot['purpose']=='CONTROL':
            key=(slot['prompt'],slot['parent'])
            if key in witnesses:
                other=witnesses.pop(key)
                require(all(value[k]==other[k] for k in ('guided','final_latent','RGB','semantic_actions')),
                    'Original complete S OFF/ON witnesses differ')
                if 'pre_encoding_RGB' in value and 'pre_encoding_RGB' in other:
                    require(value['pre_encoding_RGB']==other['pre_encoding_RGB'],
                        'Fresh S OFF/ON pre-encoding pixels differ')
            else:witnesses[key]=value
    require(not witnesses and len(moments)==108 and len(set(raw))==len(raw)==8
        and len(new_files)==len(set(new_files))==counts['new_paths'],
        'Complete original S data/raw/artifact cohort required')
    controls=matrix['OFF_ON_controls'];pairs={(s['prompt'],s['parent']) for s in upper['slots'] if s['purpose']=='CONTROL'}
    physical_controls=execution['OFF_ON_controls']
    require(len(controls)==len(physical_controls)==4
        and {(c['prompt'],c['parent']) for c in controls}==pairs
        and {(c['prompt'],c['parent']) for c in physical_controls}==pairs
        and all(c['exact'] is True for c in controls)
        and all(c['exact'] is True and (c['pre_encoding_RGB_compared'] is True or
            (counts['reused_OFF_paths']==1 and c['retained_OFF_has_no_pre_encoding_pixels'] is True))
            for c in physical_controls),'Original four S parity controls required')
    checks=result['resource_checks'];expected=[(s['id'],step) for s in upper['slots'] if s['enabled'] for step in TARGETS]
    require([(r['slot_id'],r['step']) for r in checks]==expected and len(checks)==108
        and all(r['contract_sha256']==resource_contract_sha256 and r['all_eight_groups_checked'] is True
            and r['tensor_values_read'] is False and r['tensor_copies_performed']==0 for r in checks),
        'Original108 pre-snapshot resource checks required')
    require((matrix['storage']['measured_rows'],matrix['storage']['raw_states'],matrix['storage']['unique_anchor_files'])==(108,8,24),
        'Original S streaming manifest cohort differs')
    return dict(status='S_COMPLETE_DATA_REVALIDATED_PENDING_ARTIFACTS_AND_ORIGINAL_ALLOCATION',
        CPU_fixture=CPU_fixture,logical_paths=10,new_paths=counts['new_paths'],same_state_rows=108,
        raw_states=8,unique_anchors=24,FP64_moments_recomputed=108,
        artifact_file_bytes_independently_accepted=False,original_GPU_release_accepted=False,
        original_financial_settlement_accepted=False,scientific_S_effect_established=False,
        complete_video_deployment_or_speed_established=False)
