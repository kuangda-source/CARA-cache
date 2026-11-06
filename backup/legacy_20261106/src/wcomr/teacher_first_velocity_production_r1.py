"""Whole four-parent/eight-suffix/four fresh-teacher diagnostic contract."""
import hashlib,json,math
from pathlib import Path
from .math_n1_production_r1 import UUID,MODE_REF,sha,write,verify_admission
from .math_n1_production_r2 import current_window_original_inputs

CONFIG='configs/wc_teacher_first_velocity_full270_production_r1_20261013.json'
CARD='WC-SAME-STATE-TEACHER-FIRST-VELOCITY-FULL270-SUFFIX8-R1-20261013-A'
RUN='wc-teacher-first-velocity-full270-r1'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
COUNTS={'parents':4,'events':4,'suffixes':8,'parent_pairs':144,'suffix_pairs':122,
    'pairs':270,'CFG_calls':540,'videos':12,'Native_references':4,'teacher_pairs':4,'loads':1}
CPU_STATUS='TEACHER_FIRST_TWO_FLOW_FULL24_PARENTS32_ENDPOINT_SUFFIXES_CPU_PASS_NOT_GPU'
RAW_STATUS='TEACHER_FIRST_ALL24_RAW_TWO_FLOW_FRESH_TEACHER_AND_C_CACHE_CPU_PASS_NOT_GPU'


def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS
            or c['strategy']!=STRATEGY or c['parent_method']!='P_OFF' or c['A_method']!='BETA1_ONE_PHASE'
            or c['training'] or c['head_elision'] or c['online_teachers'] or c['forced_future_actions']
            or c['fit_in_parent'] or c['clock_observer_added'] or c['automatic_single_job_GPUh']!=8
            or c['cumulative_cap_GPUh']!=104.97136333301378 or not math.isfinite(c['forecast_complete_GPUh'])
            or not 0<c['forecast_complete_GPUh']<=8 or not c['teacher_only_first_returned_velocity']
            or c['teacher_committed_to_parent_or_suffix'] or c['first_branch_readouts']!=['C','C']
            or len(c['requests'])!=4 or len(c['states'])!=4
            or c['branch_labels']!=['C_REPLAY','TEACHER_FIRST'] or c['mirror_order']!=[False,True,False,True]
            or [s['chosen']['step'] for s in c['states']]!=[10,29,21,27]
            or [(s['source'],s['phase']) for s in c['states']]!=[('D','EARLY'),('D','LATE'),('P','EARLY'),('P','LATE')]
            or c['checkpoint_reserves']!={'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30)}
            or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93 or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests'])):
        raise ValueError('Exact whole270/four fresh teachers/two C-cache suffixes required')
    for req,s in zip(c['requests'],c['states']):
        if (req['name']!=s['scene'] or s['chosen']['actual_pi0_action']!='C'
                or s['default_readout']!=('A' if s['source']=='D' else 'C')
                or s['alternative_readout']==s['default_readout'] or s['alternative_readout'] not in ('C','A')):
            raise ValueError('Original396 four natural C states required')


def validate(project,stage):
    project,stage=Path(project),Path(stage);reg=json.loads((stage/'registration.json').read_text())
    c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    for n,h in reg['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('Frozen teacher-first payload differs: '+n)
    for n,h in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/n)!=h:raise ValueError('Pinned runtime differs: '+n)
    for key in ('selection','parameters','cost','baseline','original396_capture'):
        if sha(stage/c[key+'_ref'])!=c[key+'_sha256']:raise ValueError('Frozen '+key+' differs')
    selection=json.loads((stage/c['selection_ref']).read_text());assert selection['states']==c['states']
    parameters=json.loads((stage/c['parameters_ref']).read_text());fp=parameters.pop('fingerprint')
    assert fp==hashlib.sha256(json.dumps(parameters,sort_keys=True,allow_nan=False).encode()).hexdigest()
    parameters['fingerprint']=fp;assert parameters['gamma']==.7235237005554214
    for n,h in parameters['sources'].items():assert sha(stage/n)==h
    cost=json.loads((stage/c['cost_ref']).read_text())
    assert cost['forecast_complete_GPUh']==c['forecast_complete_GPUh']==sum(cost['components'].values())*cost['contingency_multiplier']/3600
    assert cost['all_pairs']==270 and cost['CFG_calls']==540 and cost['teacher_pairs']==4
    auth=json.loads((stage/c['authority_ref']).read_text())
    assert auth['direct_user_authorization'] and auth['automatic_single_job_gpu_hours']==8 and not auth['usage_reset'] and auth['new_cumulative_cap_gpu_hours']==c['cumulative_cap_GPUh']
    proof=json.loads((stage/'sampling-CPU-result.json').read_text())
    assert proof['status']==CPU_STATUS and proof['actual_CPU_parents']==24 and proof['endpoint_suffixes']==32 and proof['teacher_pairs']==8 and not proof['CUDA_initialized'] and not proof['GPU_submissions']
    for n,h in proof['payload_sha256'].items():assert reg['payload_sha256'].get(n)==h
    raw=json.loads((stage/'independent-CPU-raw-audit.json').read_text())
    assert raw['status']==RAW_STATUS and raw['raw_files']==24 and not raw['GPU_submissions']
    assert raw['one_teacher_strict_restore_first_C_and_future_pi0'] and raw['active_teacher_snapshot_refused']
    assert raw['sampling_result_sha256']==sha(stage/'sampling-CPU-result.json')
    baseline=json.loads((stage/c['baseline_ref']).read_text())
    assert set(baseline['bindings'])=={s['scene'] for s in c['states']}
    capture=json.loads((stage/c['original396_capture_ref']).read_text())
    assert capture['final']['status']=='PI0_SUFFIX8_ALL4_PARENTS8_SUFFIXES12_OUTPUTS_AUDITED_ALL93_SCORED'
    assert baseline['original396_terminal_sha256']==capture['final_sha256']
    for point in c['states']:
        bind=baseline['bindings'][point['scene']];assert bind['point']==point
        assert len(bind['actions'])==len(bind['guided_sha256'])==36
        for key in ('parent_vectors','parent_video_artifact','native_video_artifact'):
            item=bind[key];path=Path(item['path']);assert sha(path)==item['sha256'] and path.stat().st_size==item['bytes']
        for name,row in bind['old_suffixes'].items():
            assert row['first_readout']==name and len(row['actions'])==len(row['guided_sha256'])==37-point['chosen']['step']
            for item in (row['artifact'],row['artifact']['video_artifact']):
                path=Path(item['path']);assert sha(path)==item['sha256'] and path.stat().st_size==item['bytes']
            assert len(row['LPIPS']['frame_distances'])==93
    _,_,old,inputs=current_window_original_inputs(project,project/c['original_parent_stage'])
    assert old['preregistration']['requests']==c['requests']
    from .lpips_resource_identity import audit
    resource=audit(project/c['LPIPS_resource'],sha(stage/'src/wcomr/rv0_lpips.py'))
    assert resource['server_receipt_sha256']==c['LPIPS_resource_receipt_sha256']
    return c,reg,old,inputs,parameters,baseline
