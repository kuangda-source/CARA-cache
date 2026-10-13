"""Isolated F16/B4 full432 production contract; mainline settings unchanged."""
import hashlib,json,math
from pathlib import Path
from .math_n1_production_r1 import UUID,MODE_REF,sha,write,verify_admission
from .math_n1_production_r2 import current_window_original_inputs

CONFIG='configs/wc_fb_probe_r1_20261013.json'
CARD='WC-FB-PROBE-F16-B4-BASE4-DIAG4-FULL432-R1-20261013-A'
RUN='wc-fb-probe-full432-r1'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
COUNTS={'baseline_parents':4,'diagnostic_parents':4,'full_paths':8,'F_points':16,
 'B_points':4,'B_modes':9,'B_warm_per_mode':1,'B_timed_per_mode':3,
 'ordinary_pairs':288,'offline_pairs':144,'pairs':432,'CFG_calls':864,'loads':1}
CPU_STATUS='FB_PROBE_TWO_FLOW_CPU_PASS_NOT_GPU'
PRODUCTION_CPU_STATUS='FB_PROBE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU'


def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS
        or c['strategy']!=STRATEGY or c['parent_method']!='P_OFF'
        or c['A_method']!='BETA1_ONE_PHASE' or c['training'] or c['head_elision']
        or c['fit_in_parent'] or c['online_teacher_deployment'] or c['forced_P_or_C_suffixes']
        or c['mainline_F_B_enabled'] or not c['isolated_exploration']
        or not c['F_labels_reused_only_after_exact_replay'] or not c['two_flow_CPU_required']
        or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=104.97136333301378
        or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<=8
        or len(c['requests'])!=4 or len(c['states'])!=16
        or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93
               or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests'])
        or c['F_config']!={'warmups':10,'timed_repeats':30,'channels':16}
        or c['checkpoint_reserves']!={'logical_copy_cap_bytes':6*(1<<30),
             'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30)}):
        raise ValueError('Exact isolated F16/B4 full432 scope and unchanged mainline required')
    b=c['B_config']; expected=[('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632',27),
        ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632',21),('human_199',29),('human_199',15)]
    if ([(v['scene'],v['step']) for v in c['b_points']]!=expected or b['states']!=c['b_points']
        or b['modes']!=['DENSE_PLAIN','DENSE_P0_STATE','DENSE_M8_STATE','DENSE_L2_STATE',
            'P0_ROTATION','P0_RANDOM','M8_ROTATION','M8_RANDOM','L2']
        or b['warmups']!=1 or b['timed_repeats']!=3 or b['active_fraction']!=.5
        or b['MLP_layers_P0']!=[4,10,16,22] or b['MLP_layers_M8']!=[4,7,10,13,16,19,22,25]
        or b['L2_layers']!=[13,19] or b['mask_seed_recipe']!='SHA256(FB-R1:{scene}:{step}) first8 big-endian modulo(2**63-1)'):
        raise ValueError('Frozen four-state/nine-mode B scope required')
    if len(c['old_points'])!=16 or {(v['selection']['scene'],v['selection']['chosen']['step']) for v in c['old_points']}!={(s['scene'],s['chosen']['step']) for s in c['states']}:
        raise ValueError('All original same-state labels required')


def validate(project,stage,require_CPU=True):
    project,stage=Path(project),Path(stage)
    reg=json.loads((stage/'registration.json').read_text());c=json.loads((stage/CONFIG).read_text())
    validate_contract(c)
    for n,h in reg['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('Immutable F/B payload differs: '+n)
    for n,h in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/n)!=h:raise ValueError('Pinned runtime differs: '+n)
    for key in ('selection','parameters','cost','baseline','labels','F_analysis_parameters','old_labels_capture'):
        if sha(stage/c[key+'_ref'])!=c[key+'_sha256']:raise ValueError('Frozen '+key+' changed')
    selection=json.loads((stage/c['selection_ref']).read_text())
    if selection['states']!=c['states'] or selection['parent_method']!='P_OFF':raise ValueError('Natural states changed')
    labels=json.loads((stage/c['labels_ref']).read_text())
    if labels['states']!=c['old_points'] or not labels['no_new_F_teacher_calls']:raise ValueError('Original16 label binding changed')
    for point in c['old_points']:
        artifact=point['raw_artifact'];p=Path(artifact['path'])
        if not p.is_file() or p.stat().st_size!=artifact['bytes'] or sha(p)!=artifact['sha256']:
            raise ValueError('Original teacher/candidate raw asset missing or changed')
    params=json.loads((stage/c['parameters_ref']).read_text());fp=params.pop('fingerprint')
    if fp!=hashlib.sha256(json.dumps(params,sort_keys=True,allow_nan=False).encode()).hexdigest():raise ValueError('Parameter fingerprint differs')
    params['fingerprint']=fp
    if params['gamma']!=.7235237005554214:raise ValueError('Frozen shared gamma required')
    for n,h in params['sources'].items():
        if sha(stage/n)!=h:raise ValueError('Original parameter evidence changed: '+n)
    auth=json.loads((stage/c['authority_ref']).read_text())
    if (not auth['direct_user_authorization'] or auth['automatic_single_job_gpu_hours']!=8
            or auth['new_cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh'] or auth['usage_reset']):raise ValueError('Current human authority required')
    if json.loads((stage/c['cost_ref']).read_text())['forecast_complete_GPUh']!=c['forecast_complete_GPUh']:raise ValueError('Whole cost changed')
    if require_CPU:
        proof=json.loads((stage/'sampling-CPU-result.json').read_text())
        if (proof['status']!=CPU_STATUS or proof['actual_CPU_paths']!=16 or proof['natural_points']!=32
            or proof['B_trials']!=288 or proof['CUDA_initialized'] or proof['GPU_submissions']):
            raise ValueError('Complete actual two-flow F/B CPU proof required')
        if proof['payload_sha256']!=reg['payload_sha256']:raise ValueError('CPU-tested payload differs')
    baseline=json.loads((stage/c['baseline_ref']).read_text())
    if set(baseline['bindings'])!={r['name'] for r in c['requests']}:raise ValueError('All original parent bindings required')
    for b in baseline['bindings'].values():
        for key in ('final_artifact','video_artifact'):
            asset=b[key];path=Path(asset['path'])
            if sha(path)!=asset['sha256'] or path.stat().st_size!=asset['bytes']:raise ValueError('Original parent asset changed')
    _,_,old,inputs=current_window_original_inputs(project,project/c['original_parent_stage'])
    if old['preregistration']['requests']!=c['requests']:raise ValueError('Original four requests changed')
    return c,reg,old,inputs,params,baseline
