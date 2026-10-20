"""Independent CPU acceptance, immutable full-card authority and terminal audit."""
import hashlib
import math
from pathlib import Path

from .policy_interval_assets_r1 import (CONFIG, COUNTS, PROFILE, RUN, CPU_PROOF,
    CPU_BUNDLE, read, sha, matrix, full_rows)


def live(expected, observed):
    return bool(observed and observed.get('pid')==expected['pid']
        and observed.get('start_ticks')==expected['start_ticks']
        and observed.get('state') not in ('Z','X',None))


def accept_cpu(v):
    L=v['launch']
    if v['mode']!='cpu-terminal' or v['observed_unix']<L['final_not_before_unix']:
        raise ValueError('Original scheduled complete CPU observation required')
    if live(L['identity'],v.get('process')):
        return dict(status='ORIGINAL_CPU_RUNNING_REESTIMATE_ONCE',production_CPU_accepted=False,GPU_dispatch_ready=False)
    reg=v['registration'];files=v['files'];bundle=files.get('bundle',{}).get('data',{})
    if bundle.get('exit_code')!=0:
        return dict(status='POLICY_ASSETS_CPU_FAILED_OR_INCOMPLETE_RETAINED',production_CPU_accepted=False,
            GPU_dispatch_ready=False,source_revision=L['source_revision'],GPU_submissions=0)
    if (reg['source_revision']!=L['source_revision'] or v['registration_sha256']!=L['registration_sha256']
        or v['payload_actual_sha256']!=reg['payload_sha256']
        or v['runtime_actual_sha256']!=reg['runtime_source_sha256']):
        raise ValueError('Full production CPU source/runtime identity differs')
    proof=files['proof']['data'];numeric=files['numerical']['data']
    if (not proof.get('production_CPU_accepted') or proof['source_revision']!=L['source_revision']
        or proof['registration_sha256']!=L['registration_sha256']
        or proof['scope_counts']!=COUNTS or proof['matrix']!=matrix() or proof['profile']!=PROFILE
        or proof['actual_Cosmos_request_count']!=4 or proof['guard_refusal_controls']!=12
        or numeric['actual_CPU_paths']!=28 or numeric['source_time_cells_reloaded']!=4060
        or numeric['readout_trials']!=26040 or numeric['formal_cells_across_two_flows']!=3248
        or {c['flow'] for c in numeric['checks']}!={False,True}
        or not all(c['all36_observer_OFF_ON_and_Native_equal'] and c['owners_released']
                   and c['nonlinear_head_used'] for c in numeric['checks'])
        or len(bundle.get('commands',[]))!=3 or any(x['exit_code'] for x in bundle['commands'])
        or bundle['proof_sha256']!=files['proof']['sha256']
        or bundle['numerical_sha256']!=files['numerical']['sha256']):
        raise ValueError('Actual full numerical and guarded production CPU proof missing')
    if any(x.get('CUDA_initialized') or x.get('GPU_submissions') or x.get('ledger_written')
           for x in (bundle,proof,numeric)):
        raise ValueError('CPU validation touched CUDA/GPU/ledger')
    c=files['config']['data']
    return dict(status='POLICY_INTERVAL_ASSETS_FULL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED',
        production_CPU_accepted=True,GPU_dispatch_ready=True,source_revision=L['source_revision'],
        registration_sha256=L['registration_sha256'],config_sha256=files['config']['sha256'],
        proof_sha256=files['proof']['sha256'],numerical_sha256=files['numerical']['sha256'],
        source_files=len(reg['payload_sha256']),CPU_commands=3,CPU_wall_seconds=bundle['CPU_wall_seconds'],
        scope_counts=COUNTS,forecast_complete_GPUh=c['forecast_complete_GPUh'],billed_limit_GPUh=c['billed_limit_GPUh'],
        specific_whole_card_confirmation_required=c['billed_limit_GPUh']>=12,
        actual_GPU_or_action_prices=False,GPU_submissions=0,ledger_written=False)


def validate_authority(auth,c,regsha,proofsha,acceptedsha):
    if (auth.get('run_id')!=RUN or auth.get('scope_counts')!=COUNTS
        or auth.get('registration_sha256')!=regsha or auth.get('production_CPU_sha256')!=proofsha
        or auth.get('independent_CPU_acceptance_sha256')!=acceptedsha
        or auth.get('billed_limit_GPUh')!=c['billed_limit_GPUh']
        or auth.get('forecast_GPUh')!=c['forecast_complete_GPUh']
        or auth.get('cumulative_cap_GPUh')!=226 or auth.get('budget_origin_used_GPUh')!=79.99637737158223
        or not auth.get('direct_user_authorization') or not auth.get('user_reply_quote')
        or not auth.get('launch_id') or not auth.get('gpu_uuid','').startswith('GPU-')):
        raise ValueError('Exact full source, CPU, budget and human authority required')
    if c['billed_limit_GPUh']>=12 and not auth.get('specific_whole_card_approved'):
        raise ValueError('At or above12 requires explicit approval of this complete card')


def accept_terminal(v):
    L=v['launch']
    if v['mode']!='gpu-terminal' or v['observed_unix']<L['next_check_not_before_unix']:
        raise ValueError('Original full terminal time and capture required')
    if any(v['original_live_handles'].values()):
        return dict(status='POLICY_ASSETS_ORIGINAL_RUNNING_REESTIMATE_ONCE',full_protocol_accepted=False)
    if (v['registration_sha256']!=L['registration_sha256']
        or v['payload_actual_sha256']!=v['registration']['payload_sha256']
        or v['runtime_actual_sha256']!=v['registration']['runtime_source_sha256']):
        raise ValueError('Frozen source/runtime changed')
    from .scout_gpu_lifecycle_r1 import finance
    financial=finance(v,L)
    post=v['files'].get('post',{}).get('data')
    if not post or v['files'].get('post_exit',{}).get('data',{}).get('exit_code')!=0:
        return dict(status='POLICY_ASSETS_POST_FAILED_OR_MISSING_RETAINED',full_protocol_accepted=False,finance=financial)
    if post['runner_sha256']!=v['runner_sha256'] or post['config_sha256']!=L['config_sha256']:
        raise ValueError('Post belongs to different original runner/config')
    if v['files']['post_exit']['data']['final_result_sha256']!=v['files']['post']['sha256']:
        raise ValueError('Original post exit is not bound to its saved raw audit')
    if post['generator_input_bundle_sha256']!=v['files']['bundle']['sha256']:
        raise ValueError('Generator bundle bytes differ from accepted raw audit')
    rows=full_rows(v['runner']['runs'])
    if post['registered_paths']!=14 or len(post['rows'])!=14:
        raise ValueError('Missing complete path denominator')
    for p,row,checked in zip(matrix(),rows,post['rows']):
        if any(row.get(k)!=value or checked.get(k)!=value for k,value in p.items()):
            raise ValueError('Original position or independent audit changed')
    accepted=post['original_artifacts_accepted'] and post['reference_parity_accepted']
    return dict(status='POLICY_INTERVAL_ASSETS_FULL_ORIGINALS_AND_FINANCE_ACCEPTED' if accepted else
        'POLICY_INTERVAL_ASSETS_RAW_OR_REFERENCE_GATE_FAILED_RETAINED',full_protocol_accepted=accepted,
        generator_input_ready=accepted and post['generator_input_ready'],registered_paths=14,
        formal_source_time_cells=post['formal_source_time_cells'],registered_formal_source_time_cells=1624,
        missing_or_rejected_paths=post['missing_or_rejected_paths'],finance=financial,
        source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],
        quality_or_clean_speed_result=False,refused_or_failed_rows_preserved=True)
