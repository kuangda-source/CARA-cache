"""Exact full312/16-video saved-velocity diagnostic, separate from deployment."""
import hashlib
import json
import math
from pathlib import Path
from .math_n1_production_r1 import UUID,MODE_REF,sha,write,verify_admission
from .math_n1_production_r2 import current_window_original_inputs

CONFIG='configs/wc_block_velocity_suffix3_full312_production_r1_20261013.json'
CARD='WC-B-SAVED-VELOCITY-FULL312-SUFFIX12-VIDEOS16-R1-20261013-A'
RUN='wc-block-saved-velocity-full312-r1'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
LABELS=('C_REPLAY','DENSE_VELOCITY','L2_VELOCITY')
COUNTS=dict(parents=4,events=4,suffixes=12,parent_pairs=144,suffix_pairs=168,
    pairs=312,CFG_calls=624,videos=16,Native_references=2,teacher_pairs=0,B_executor_pairs=0,loads=1)
CPU_STATUS='B_SAVED_VELOCITY_SUFFIX3_TWO_FLOW32_PARENTS64_SUFFIXES_CPU_PASS_NOT_GPU'
RAW_STATUS='FOUR_SAVED_B_REFERENCE_ALL_IDENTITIES_SHAPES_REPEATS_AND_REFUSALS_CPU_PASS'


def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS
            or c['strategy']!=STRATEGY or c['parent_method']!='P_OFF' or c['A_method']!='BETA1_ONE_PHASE'
            or any(c[k] for k in ('training','head_elision','online_teachers','forced_future_actions',
                                  'fit_in_parent','clock_observer_added','real_B_refresh','saved_vectors_committed_to_anchor'))
            or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=104.97136333301378
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<=8
            or not c['only_first_returned_velocity_changed'] or c['first_branch_readouts']!=['C','C','C']
            or c['branch_labels']!=['C_REPLAY','DENSE_VELOCITY','L2_VELOCITY']
            or c['mirror_order']!=[False,True,False,True] or len(c['states'])!=4 or len(c['requests'])!=4
            or [s['chosen']['step'] for s in c['states']]!=[21,27,15,29]
            or [s['source'] for s in c['states']]!=['P','D','P','D']
            or len(c['point_records'])!=4
            or any(r['seed']!=0 or r['guidance']!=7 or r['num_steps']!=35
                   or r['num_output_frames']!=93 or r['resolution']!='432,768' for r in c['requests'])):
        raise ValueError('Complete four B states, three C-state suffixes and exact312 scope required')
    for req,point,bound in zip(c['requests'],c['states'],c['point_records']):
        if (req['name']!=point['scene'] or bound['point']!=point or bound['scene']!=point['scene']
                or bound['step']!=point['chosen']['step'] or point['chosen']['actual_pi0_action']!='C'
                or point['chosen']['age']!=2):
            raise ValueError('Exact four existing natural B points required')


def validate(project,stage):
    project,stage=Path(project),Path(stage);reg=json.loads((stage/'registration.json').read_text())
    c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    for n,h in reg['payload_sha256'].items():assert sha(stage/n)==h
    for n,h in reg['runtime_source_sha256'].items():assert sha(project/'runtime'/n)==h
    for key in ('parameters','cost','baseline'):assert sha(stage/c[key+'_ref'])==c[key+'_sha256']
    params=json.loads((stage/c['parameters_ref']).read_text());values=dict(params);fp=values.pop('fingerprint')
    assert fp==hashlib.sha256(json.dumps(values,sort_keys=True,allow_nan=False).encode()).hexdigest()
    assert params['gamma']==.7235237005554214
    for n,h in params['sources'].items():assert sha(stage/n)==h
    cost=json.loads((stage/c['cost_ref']).read_text())
    assert cost['all_pairs']==312 and cost['videos']==16 and cost['teacher_pairs']==cost['fresh_B_executor_pairs']==0
    assert c['forecast_complete_GPUh']==cost['forecast_complete_GPUh']==sum(cost['components'].values())*cost['contingency_multiplier']/3600
    auth=json.loads((stage/c['authority_ref']).read_text())
    assert auth['direct_user_authorization'] and auth['automatic_single_job_gpu_hours']==8 and auth['new_cumulative_cap_gpu_hours']==c['cumulative_cap_GPUh']
    proof=json.loads((stage/'sampling-CPU-result.json').read_text())
    assert proof['status']==CPU_STATUS and proof['actual_CPU_parents']==32 and proof['endpoint_suffixes']==64
    assert not proof['CUDA_initialized'] and proof['GPU_submissions']==0
    for n,h in proof['payload_sha256'].items():assert reg['payload_sha256'].get(n)==h
    saved=json.loads((stage/'saved-reference-CPU-result.json').read_text())
    assert saved['status']==RAW_STATUS and len(saved['rows'])==4 and not saved['CUDA_initialized']
    for n,h in saved['payload_sha256'].items():assert reg['payload_sha256'].get(n)==h
    for point,row in zip(c['point_records'],saved['rows']):
        assert (row['scene'],row['step'])==(point['scene'],point['step'])
        assert row['artifact_sha256']==point['artifact']['sha256'] and row['same_registered_state'] and row['all_four_repeats_equal']
        for key in ('input_sha256','source_state_sha256','true_D_state_sha256'):assert row[key]==point[key]
        artifact=point['artifact'];p=Path(artifact['path']);assert sha(p)==artifact['sha256'] and p.stat().st_size==artifact['bytes']
    baseline=json.loads((stage/c['baseline_ref']).read_text())
    assert set(baseline['bindings'])=={r['name'] for r in c['requests']}
    for bind in baseline['bindings'].values():
        assert len(bind['actions'])==len(bind['guided_sha256'])==36
        for key in ('parent_vectors','native_video_artifact'):
            a=bind[key];p=Path(a['path']);assert sha(p)==a['sha256'] and p.stat().st_size==a['bytes']
    _,_,old,inputs=current_window_original_inputs(project,project/c['original_parent_stage'])
    assert all(r in old['preregistration']['requests'] for r in c['requests'])
    from .lpips_resource_identity import audit
    resource=audit(project/c['LPIPS_resource'],sha(stage/'src/wcomr/rv0_lpips.py'))
    assert resource['server_receipt_sha256']==c['LPIPS_resource_receipt_sha256']
    return c,reg,old,inputs,params,baseline
