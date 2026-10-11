"""Frozen natural12 experiment inputs and fresh48 authorization checks."""
import json
import math
from pathlib import Path
from .e1_diag8_production_r2 import UUID,MODE_REF,sha,write

CONFIG='configs/wc_math_n1_natural12_production_r1_20261012.json'
CARD='WC-MATH-N1-NATURAL12-R1-20261012-A'
RUN='wc-math-n1-natural-unit-r1'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
COUNTS={'parents':4,'points':12,'P_points':8,'D_controls':4,'pairs':180,'CFG_calls':360,'scores':48,'loads':1}

def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS
            or c['strategy']!=STRATEGY or c['A_method']!='BETA1_ONE_PHASE'
            or c['gamma_diagnostic']!=[0.,.5,1.] or c['training'] or c['head_elision']
            or c['forced_P_or_C_suffixes'] or c['deployed_variant']!='D_REFERENCE_UNIT'
            or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=104.97136333301378
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<=8
            or len(c['requests'])!=4 or len(c['states'])!=12
            or sum(p['source']=='P' for p in c['states'])!=8
            or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93
                   or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests'])
            or c['checkpoint_reserves']!={'logical_copy_cap_bytes':6*(1<<30),
                'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30)}
            or c['fit_target']!='SCENE_EQUAL_NORMALIZED_GUIDED_OUTPUT_MSE'
            or c['fit_target_energy_epsilon']!=1e-12):
        raise ValueError('Exact complete natural12/pairs180 source/readout scope required')

def validate(project,stage,require_CPU=True):
    project,stage=Path(project),Path(stage)
    reg=json.loads((stage/'registration.json').read_text());c=json.loads((stage/CONFIG).read_text())
    validate_contract(c)
    for n,h in reg['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('Immutable N1 payload changed: '+n)
    for n,h in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/n)!=h:raise ValueError('Pinned N1 runtime changed: '+n)
    idx=json.loads((stage/c['state_index_ref']).read_text())
    if (idx['states']!=c['states'] or idx['requests']!=c['requests']
            or sha(stage/c['state_index_ref'])!=c['state_index_sha256']):
        raise ValueError('Frozen natural selection or actual original inputs changed')
    if sha(stage/c['original_guided_bindings_ref'])!=c['original_guided_bindings_sha256']:
        raise ValueError('Original full36 guided record bindings changed')
    auth=json.loads((stage/c['authority_ref']).read_text())
    if (not auth['direct_user_authorization'] or auth['automatic_single_job_gpu_hours']!=8
            or auth['new_cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh'] or auth['usage_reset']):
        raise ValueError('Current human remaining48/strict-over8 authorization required')
    cost=json.loads((stage/c['cost_ref']).read_text())
    if sha(stage/c['cost_ref'])!=c['cost_sha256'] or cost['forecast_complete_GPUh']!=c['forecast_complete_GPUh']:
        raise ValueError('Whole replay/teacher/head/restore/load cost changed')
    from .e3_complete64_production_r1 import validate as old_validate
    _,_,old,inputs=old_validate(project,project/c['original_parent_stage'])
    if old['preregistration']['requests']!=c['requests']:raise ValueError('All four original CAL requests required')
    if require_CPU:
        proof=json.loads((stage/'sampling-CPU-result.json').read_text())
        if (proof['status']!='MATH_N1_TWO_FLOW_FULL8_CPU_PATHS12_STATES_PASS_NOT_GPU'
                or proof['actual_CPU_paths']!=8 or proof['CUDA_initialized'] or proof['GPU_submissions']):
            raise ValueError('Actual complete two-flow sampling CPU proof required')
        for n,h in proof['payload_sha256'].items():
            if reg['payload_sha256'].get(n)!=h:raise ValueError('Production differs from tested CPU bytes: '+n)
    return c,reg,old,inputs,idx

def verify_admission(c,ledger,gpu):
    rem=ledger['cap_gpu_hours']-ledger['used_gpu_hours']
    if (ledger['cap_gpu_hours']!=c['cumulative_cap_GPUh'] or any('inflight' in k for k in ledger)
            or not 0<rem<=48+1e-9 or c['forecast_complete_GPUh']>rem
            or gpu['uuid']!=UUID or gpu['compute_cap']!='8.6' or gpu['memory_used_mib']>1024 or gpu['pids']):
        raise ValueError('Fresh actual N1 GPU/lock/current-budget admission unavailable')
    return rem,min(8.,rem)
