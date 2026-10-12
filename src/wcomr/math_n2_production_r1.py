"""Fresh-window production contract for full36 plus eighteen full warmups."""
import hashlib,json,math
from pathlib import Path
from .math_n2_batch_r1 import RUN,CARD,METHODS,matrix
from .math_n1_production_r1 import UUID,MODE_REF,sha,write,verify_admission
from .math_n1_production_r2 import current_window_original_inputs

CONFIG='configs/wc_math_n2_full36_production_r1_20261012.json'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
COUNTS={'requests':4,'methods':9,'scientific_paths':36,'full_warmup_paths':18,'total_paths':54,
        'ordinary_pairs':1944,'ordinary_CFG_calls':3888,'loads':1,'teacher_pairs':0,'score_videos':36}
CPU_STATUS='MATH_N2_ALL72_AUDIT40_CLEAN32_ENDPOINT_CPU_PASS_NOT_GPU'

def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS or c['methods']!=list(METHODS)
            or c['strategy']!=STRATEGY or c['A_method']!='BETA1_ONE_PHASE' or c['head_elision']
            or c['training'] or c['online_teachers'] or c['automatic_single_job_GPUh']!=8
            or c['cumulative_cap_GPUh']!=104.97136333301378 or len(c['requests'])!=4
            or not 0<c['forecast_complete_GPUh']<=8 or not math.isfinite(c['forecast_complete_GPUh'])
            or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93
                   or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests'])):
        raise ValueError('Exact full36/nine controls and eighteen full warmups required')
    matrix([r['name'] for r in c['requests']])

def validate(project,stage):
    project,stage=Path(project),Path(stage);reg=json.loads((stage/'registration.json').read_text())
    c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    for n,h in reg['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('Immutable N2 payload differs: '+n)
    for n,h in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/n)!=h:raise ValueError('Pinned actual runtime changed: '+n)
    auth=json.loads((stage/c['authority_ref']).read_text())
    if (not auth['direct_user_authorization'] or auth['automatic_single_job_gpu_hours']!=8
            or auth['new_cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh'] or auth['usage_reset']):
        raise ValueError('Current user remaining48/strict-over8 authority required')
    p=json.loads((stage/c['parameters_ref']).read_text());fingerprint=p.pop('fingerprint')
    if fingerprint!=hashlib.sha256(json.dumps(p,sort_keys=True,allow_nan=False).encode()).hexdigest():
        raise ValueError('Frozen related-error parameters changed')
    p['fingerprint']=fingerprint
    if sha(stage/c['parameters_ref'])!=c['parameters_sha256']:raise ValueError('Parameters ref changed')
    for n,h in p['sources'].items():
        if sha(stage/n)!=h:raise ValueError('N1 complete fit or cost evidence changed: '+n)
    if sha(stage/c['cost_ref'])!=c['cost_sha256']:raise ValueError('Full54 load/warmup/control cost changed')
    cost=json.loads((stage/c['cost_ref']).read_text())
    if cost['forecast_complete_GPUh']!=c['forecast_complete_GPUh']:raise ValueError('Cost and card disagree')
    proof=json.loads((stage/'sampling-CPU-result.json').read_text())
    if (proof['status']!=CPU_STATUS or proof['actual_CPU_paths']!=144 or proof['CUDA_initialized']
            or proof['GPU_submissions'] or proof['clean_control_paths']!=40):
        raise ValueError('All two-flow144 sampling/clean/endpoints CPU proof required')
    for n,h in proof['payload_sha256'].items():
        if reg['payload_sha256'].get(n)!=h:raise ValueError('Production differs from sampling CPU bytes: '+n)
    _,_,old,inputs=current_window_original_inputs(project,project/c['original_parent_stage'])
    calibration,specs,*_=inputs
    if old['preregistration']['requests']!=c['requests']:raise ValueError('Original four same-seed inputs changed')
    if specs[STRATEGY]['SOURCE_RA']['threshold']!=p['original_RA_threshold']:
        raise ValueError('Math lambda borrowed a different original threshold')
    if not 0<=p['gamma']<=1:raise ValueError('Frozen common source fusion gain required')
    return c,reg,old,inputs,p
