"""Frozen full source/phase16 calibration, with four necessary parent replays."""
import hashlib,json,math
from pathlib import Path
from .math_n1_production_r1 import UUID,MODE_REF,sha,write,verify_admission
from .math_n1_production_r2 import current_window_original_inputs

CONFIG='configs/wc_source_phase16_full368_production_r1_20261012.json'
CARD='WC-SOURCE-PHASE16-BASE4-DIAG4-FULL368-R1-20261012-A'
RUN='wc-source-phase16-full368-r1'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
COUNTS={'baseline_parents':4,'diagnostic_parents':4,'full_paths':8,'points':16,
    'ordinary_pairs':288,'offline_pairs':80,'pairs':368,'CFG_calls':736,
    'candidate_scores':64,'teachers':16,'raw_files':16,'raw_tensors':192,'loads':1}
CPU_STATUS='SOURCE_PHASE16_TWO_FLOW_FULL16_PARENTS32_STATES_CPU_PASS_NOT_GPU'
RAW_STATUS='SOURCE_PHASE16_ALL32_RAW384_CFG_RECONSTRUCTION_CPU_PASS_NOT_REAL_LABELS'


def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS
            or c['strategy']!=STRATEGY or c['parent_method']!='P_OFF'
            or c['A_method']!='BETA1_ONE_PHASE' or c['training'] or c['head_elision']
            or c['forced_P_or_C_suffixes'] or c['fit_in_parent'] or c['online_teacher_deployment']
            or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=104.97136333301378
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<=8
            or len(c['requests'])!=4 or len(c['states'])!=16
            or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93
                   or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests'])
            or c['checkpoint_reserves']!={'logical_copy_cap_bytes':6*(1<<30),
                'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30)}
            or c['labels']!=['C','D_REFERENCE_A','FUSION_A','NEW_P']):
        raise ValueError('Exact full16/all8 parent controls/full368 calibration required')
    scenes=[r['name'] for r in c['requests']]
    for scene in scenes:
        states=[s for s in c['states'] if s['scene']==scene]
        if (len(states)!=4 or {(s['source'],s['phase']) for s in states}!=
                {('D','EARLY'),('D','LATE'),('P','EARLY'),('P','LATE')}
                or len({s['chosen']['step'] for s in states})!=4
                or any(not s['chosen']['partial_ready'] or s['chosen']['state_before'][5]>=2 for s in states)):
            raise ValueError('Fixed complete source/phase cells and actual new-P eligibility required')


def validate(project,stage):
    project,stage=Path(project),Path(stage);reg=json.loads((stage/'registration.json').read_text())
    c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    for n,h in reg['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('Immutable calibration payload differs: '+n)
    for n,h in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/n)!=h:raise ValueError('Pinned runtime differs: '+n)
    for key in ('selection','parameters','cost','baseline'):
        if sha(stage/c[key+'_ref'])!=c[key+'_sha256']:raise ValueError('Frozen '+key+' changed')
    selection=json.loads((stage/c['selection_ref']).read_text())
    if selection['states']!=c['states'] or selection['parent_method']!='P_OFF':raise ValueError('Natural points changed')
    params=json.loads((stage/c['parameters_ref']).read_text());fp=params.pop('fingerprint')
    if fp!=hashlib.sha256(json.dumps(params,sort_keys=True,allow_nan=False).encode()).hexdigest():raise ValueError('Parameters fingerprint differs')
    params['fingerprint']=fp
    if params['gamma']!=.7235237005554214:raise ValueError('Frozen shared gamma required')
    for n,h in params['sources'].items():
        if sha(stage/n)!=h:raise ValueError('Original parameter evidence changed: '+n)
    auth=json.loads((stage/c['authority_ref']).read_text())
    if (not auth['direct_user_authorization'] or auth['automatic_single_job_gpu_hours']!=8
            or auth['new_cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh'] or auth['usage_reset']):raise ValueError('Current human authority required')
    if json.loads((stage/c['cost_ref']).read_text())['forecast_complete_GPUh']!=c['forecast_complete_GPUh']:raise ValueError('Whole cost changed')
    proof=json.loads((stage/'sampling-CPU-result.json').read_text())
    if (proof['status']!=CPU_STATUS or proof['actual_CPU_paths']!=16 or proof['natural_points']!=32
            or proof['CUDA_initialized'] or proof['GPU_submissions']):raise ValueError('Complete two-flow sampling CPU required')
    for n,h in proof['payload_sha256'].items():
        if reg['payload_sha256'].get(n)!=h:raise ValueError('Production differs from tested core: '+n)
    raw=json.loads((stage/'independent-CPU-raw-audit.json').read_text())
    if raw['status']!=RAW_STATUS or raw['raw_tensors']!=384 or raw['GPU_submissions']:raise ValueError('All CPU raw tensors required')
    baseline=json.loads((stage/c['baseline_ref']).read_text())
    if set(baseline['bindings'])!={r['name'] for r in c['requests']}:raise ValueError('All original parent bindings required')
    for b in baseline['bindings'].values():
        for key in ('final_artifact','video_artifact'):
            asset=b[key];path=Path(asset['path']);assert sha(path)==asset['sha256'] and path.stat().st_size==asset['bytes']
    _,_,old,inputs=current_window_original_inputs(project,project/c['original_parent_stage'])
    if old['preregistration']['requests']!=c['requests']:raise ValueError('Original four requests changed')
    return c,reg,old,inputs,params,baseline
