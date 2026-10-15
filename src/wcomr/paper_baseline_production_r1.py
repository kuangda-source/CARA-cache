"""N05 core66 production contract; no launch or budget mutation on import."""
import hashlib
import json
import math
from pathlib import Path

from .paper_baseline_grid_r1 import METHODS, NATIVE_UPDATES, matrix, point

CONFIG='configs/wc_paper_N05_core66_production_r1_20261016.json'
RUN='wc-paper-n05-core11-cal4-full66-r1'
CARD='WC-PAPER-N05-CORE11-CAL4-FULL66-R1-20261016-A'
COUNTS=dict(requests=4,methods=11,scientific_paths=44,full_warmup_paths=22,total_paths=66,
            ordinary_pairs=2220,ordinary_CFG_calls=4440,loads=1,teacher_pairs=0,score_videos=44)
PRODUCTION_CPU_STATUS='N05_CORE66_ACTUAL_PRODUCTION_ENTRY_CPU_PASS_NOT_GPU'
LOCAL_CPU_STATUS='N05_CORE216_LOCAL_CPU_MATRIX_PARAMETER_PATHS_AND_MOCKS_INDEPENDENTLY_ACCEPTED'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
DEFAULTS=('NATIVE35','WC_DEFAULT','RA_DEFAULT','A_NO_P','TABLE_PHASE_H1')

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(path,value):
    from .gpu_budget_pool_v2 import atomic_json
    atomic_json(path,value)
def diagnostic_warm(row):return row['section']=='WARMUP' and row['method'] in DEFAULTS

def validate_launch_authority(c,reg,proof,auth,*,revision,gpu_uuid,config_sha256,production_sha256,registration_sha256):
    validate_contract(c)
    if (reg['source_revision']!=revision or proof['source_revision']!=revision or auth['source_revision']!=revision
            or proof['status']!=PRODUCTION_CPU_STATUS or proof['exit_code']!=0
            or proof['registration_sha256']!=registration_sha256
            or proof['config_sha256']!=config_sha256 or auth['config_sha256']!=config_sha256
            or auth['production_CPU_sha256']!=production_sha256
            or not auth['direct_user_authorization'] or auth['autonomy_exclusive_upper_GPUh']!=12
            or not auth['user_reply_quote'] or not auth['launch_id']
            or auth['whole_card_run']!=RUN or auth['gpu_uuid']!=gpu_uuid):
        raise ValueError('Complete CPU/source/single-launch/under12 authority binding differs')

def verify_N06_prerequisite(project,acceptance,*,now=None):
    """Never inspect the original running stage before its registered ETA."""
    import time
    if (time.time() if now is None else now)<1792097651.2794473:
        raise ValueError('Before original N06 collection ETA; no prerequisite read')
    if (acceptance.get('status') not in ('SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED',
                'SIMPLE26D_FULL36_TERMINAL_WITH_REJECTIONS_RETAINED')
            or acceptance.get('full_denominator')!=36 or acceptance.get('formal_denominator')!=24):
        raise ValueError('Complete independently accepted original N06 required before N05 GPU')
    stage=Path(project)/'.sync/wc-simple26d-memory-production-r2-20261015'
    final=json.loads((stage/'CPU-final-results.json').read_text())
    end=json.loads((stage/'post-CPU-exit.json').read_text())
    out=Path(project)/'outputs/wc-simple26d-memory-cal4-full36-r2'
    supervisor=json.loads((out/'supervisor.json').read_text())
    bill=json.loads((out/'billing.json').read_text())
    if (end['exit_code']!=0 or supervisor['child_exit_code']!=0 or len(final['rows'])!=36
            or supervisor['source_revision']!='0795a008bc94401bcc30a5fb456a2620aae0f2ea'
            or acceptance['actual_GPUh']!=bill['actual_GPUh']
            or len(final['old28_memory_parity_controls'])!=28
            or not all(r['status'].startswith('PASS') for r in final['old28_memory_parity_controls'])):
        raise ValueError('Original N06 terminal artifact/model/finance acceptance differs')
    return dict(status='ORIGINAL_N06_ACCEPTANCE_BOUND_BEFORE_N05_GPU',
        original_stage=str(stage),post_sha256=sha(stage/'post-CPU-exit.json'),
        final_sha256=sha(stage/'CPU-final-results.json'),billing_sha256=sha(out/'billing.json'))

def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS
            or c['methods']!=list(METHODS) or c['strategy']!=STRATEGY
            or c['autonomy_exclusive_upper_GPUh']!=12
            or c['cumulative_cap_GPUh']!=104.97136333301378
            or not 0<c['forecast_complete_GPUh']<=c['billed_limit_GPUh']<12
            or c['billed_limit_GPUh']!=9.5 or c['warmup_repeats']!=2
            or c['diagnostic_warm_methods']!=list(DEFAULTS)
            or c['expected_diagnostic_warm_paths']!=10 or c['expected_warm_guided_outputs']!=360
            or c['main_timing']!='SYNCHRONIZED_TEXT_ENCODING_DENOISING_VAE_DECODING'
            or c['memory_policy']!='REQUEST_BOUNDARY_GC_ONLY'
            or c['direct_corrected_neighbor_included'] or not c['neighbor_gap_retained']
            or any(c[k] for k in ('training','online_teachers','F_B_enabled','P_ACR','T1','head_elision','new_final_test_inputs'))
            or len(c['requests'])!=4
            or any(r['seed']!=0 or r['num_steps']!=35 or r['guidance']!=7
                or r['num_output_frames']!=93 or r['resolution']!='432,768' for r in c['requests'])):
        raise ValueError('Exact complete finite N05 core66 production contract required')
    plan=matrix([r['name'] for r in c['requests']])
    if (sum(point(r['method'])['actual_updates'] for r in plan)!=2220
            or sum(diagnostic_warm(r) for r in plan)!=10):
        raise ValueError('Finite native grids or complete warmup domain changed')
    return plan

def validate(project,stage):
    # Reuse already accepted physical inputs/checkpoint/calibration; this does
    # not execute PA, select its GPU card or replace the new grid CPU evidence.
    from .p_acr_profile528_production_r1 import validate as physical
    project,stage=Path(project),Path(stage)
    base,reg,old,inputs,values=physical(project,stage)
    c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    if c['requests']!=base['requests']:
        raise ValueError('Original four CAL request bytes differ')
    refs={}
    for key,binding in c['references'].items():
        path=stage/binding['ref']
        if sha(path)!=binding['sha256']:raise ValueError('N05 reference changed: '+key)
        refs[key]=json.loads(path.read_text())
    core,cost,proof=refs['scope'],refs['cost'],refs['sampling_CPU_acceptance']
    if (core['scope_counts']!=COUNTS or core['requests']!=c['requests']
            or [m['id'] for m in core['methods']]!=list(METHODS)
            or cost['scope_counts']!=COUNTS or cost['forecast_complete_GPUh']!=c['forecast_complete_GPUh']
            or cost['billed_limit_GPUh']!=c['billed_limit_GPUh']
            or proof['status']!=LOCAL_CPU_STATUS or proof['actual_CPU_paths']!=216
            or proof['audit_lean_mock_pairs']!=88 or proof['default_full36_guided_and_mock_bridges']!=40
            or proof['production_CPU_accepted'] or proof['real_video_quality_or_speed_claim']):
        raise ValueError('Whole66 cost/scope and independent full216 CPU proof required')
    numeric=refs['sampling_CPU_raw']
    if (numeric['status']!='N05_CORE_GRID_FULL216_LOCAL_TOY_CPU_PASS_NOT_PRODUCTION'
            or numeric['actual_CPU_paths']!=216 or numeric['ordinary_pairs']!=7360
            or numeric['CFG_calls']!=14720 or numeric['CUDA_initialized']):
        raise ValueError('All local sampler paths must be accepted with explicit Toy boundaries')
    for name,digest in numeric['source_sha256'].items():
        if reg['payload_sha256'].get(name)!=digest:
            raise ValueError('Production core differs from complete sampling CPU: '+name)
    for name,digest in numeric['runtime_source_sha256'].items():
        if reg['runtime_source_sha256'].get(name)!=digest:
            raise ValueError('Production upstream differs from sampling CPU: '+name)
    clock=refs['native_scheduler_CPU']
    if ({r['requested_steps']:r['actual_updates'] for r in clock['rows']}!=NATIVE_UPDATES
            or any(r['CFG_calls']!=2*r['actual_updates'] for r in clock['rows'])):
        raise ValueError('Real three-grid scheduler CPU proof required')
    expected={(r['name'],m) for r in c['requests'] for m in DEFAULTS}
    baseline=refs['default20']
    if len(baseline['rows'])!=20 or {(r['scene'],r['method']) for r in baseline['rows']}!=expected:
        raise ValueError('All twenty original420 endpoint controls required')
    for row in baseline['rows']:
        for key in ('final_artifact','video_artifact'):
            f=row[key];path=Path(f['path'])
            if sha(path)!=f['sha256'] or path.stat().st_size!=f['bytes']:
                raise ValueError('Original baseline artifact identity changed')
    return c,reg,old,inputs,{'SOURCE_PHASE':values['H1']},values['previous']

def audit_row(row,planned):
    if any(row.get(k)!=v for k,v in planned.items()):raise ValueError('N05 row identity/order differs')
    if row['status']=='TEXT_REJECTED':
        if row.get('solver_steps')!=0 or row.get('guided_pairs')!=0 or row.get('final_artifact'):
            raise ValueError('Text rejection cannot contain a model path')
        return
    if row['status'] not in ('COMPLETE','VIDEO_REJECTED'):return
    p=point(row['method']);n=p['actual_updates'];diag=diagnostic_warm(planned)
    if (row['baseline_grid_point']!=p or row['solver_steps']!=n or row['guided_pairs']!=n
            or len(row['scheduler_timesteps'])!=n
            or row['in_timing_hashes'] or row['research_checkpoints']
            or row['in_timing_guided_copies']!=(n if diag else 0) or row['audit']!=diag
            or not row['write_deferred_after_main_timer'] or not math.isfinite(row['core_seconds'])
            or row['core_seconds']<=0):raise ValueError('Actual grid/update/timing path differs')
    if diag and row.get('warm_guided_outputs')!=36:raise ValueError('Full default warm trace missing')
    installed=row['installed_thresholds']
    if len(installed)!=1:raise ValueError('Exactly one method installation required')
    if p['family']=='NATIVE':
        if (row['actions'] is not None or set(row['native_block_CFG_counts'].values())!={2*n}
                or not row['native_count_adaptation']['inverse_bytes_and_AST_equal']):
            raise ValueError('Native must run both branches and all dense blocks')
    else:
        if len(row['actions'])!=36 or any(a not in ('DD','DC','CD','CC','PP') for a in row['actions']):
            raise ValueError('All actual branch actions required')
        if p['family']=='WC' and installed[0]['net_WC_threshold']!=p['threshold']:
            raise ValueError('WC installed threshold differs')
        if p['family']=='RA' and installed[0]['controller_RA_threshold']!=p['threshold']:
            raise ValueError('RA installed threshold differs')
    memory=row['request_memory_lifecycle']
    if memory['components_alive_after']!=0 or memory['within_request_algorithm_or_guardrails_changed']:
        raise ValueError('Request owner leak or changed algorithm')
    if row['method']=='TABLE_PHASE_H1':
        history=row['source_history']
        if len(history)!=36 or [h['action'] for h in history]!=row['actions']:
            raise ValueError('Complete original H1 source history required')
        for h in history:
            if h['teacher_calls'] or h['P_updates_true_D_or_zero_risk_RA_anchor']:
                raise ValueError('Online teacher or false trusted anchor')
            if h['action']!='DD' and h['true_D_before']!=h['true_D_after']:
                raise ValueError('Approximate action changed true D history')
            if h['action']=='PP' and (h['source_policy']['creation_floor_proxy_after']<=0
                    or any(s['kind']!='P' or s['RA_zero_risk_reset_allowed'] for s in h['working_sources'])):
                raise ValueError('Original P0 must keep approximate source identity and nonzero birth error')
