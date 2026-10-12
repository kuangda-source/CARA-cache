"""Complete six-method/full24 plus12 warmups using accepted H1 bytes."""
import json,math
from pathlib import Path
from .source_phase_absolute_h1_control_r1 import validate_parameters
from .math_n1_production_r1 import UUID,MODE_REF,sha,write,verify_admission
from .math_n1_production_r2 import current_window_original_inputs

CONFIG='configs/wc_source_phase_h1_full24_production_r1_20261013.json'
METHODS=('NATIVE','RA','A_NO_P','P_OFF','TABLE_PHASE_H1','TABLE_POOLED_H1')
RUN='wc-source-phase-h1-full24-r1'
CARD='WC-SOURCE-PHASE-ABSOLUTE-H1-FULL24-WARM12-R1-20261013-A'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
COUNTS={'requests':4,'methods':6,'scientific_paths':24,'full_warmup_paths':12,'total_paths':36,
    'ordinary_pairs':1296,'ordinary_CFG_calls':2592,'loads':1,'teacher_pairs':0,'score_videos':24}
CPU_STATUS='SOURCE_PHASE_ABSOLUTE_H1_TWO_FLOW_ALL48_AUDIT48_LEAN_CPU_PASS_NOT_GPU'


def matrix(scenes):
    if len(scenes)!=4 or len(set(scenes))!=4:raise ValueError('All four fixed CAL scenes required')
    rows=[]
    for rep in (1,2):
        for method in METHODS:rows.append({'id':f'warm_{rep}_{method}','scene':scenes[0],'method':method,'section':'WARMUP','round':rep})
    for i,scene in enumerate(scenes):
        for method in METHODS if i%2==0 else METHODS[::-1]:
            rows.append({'id':f'timed_{i}_{method}','scene':scene,'method':method,'section':'TIMED','round':1})
    assert len(rows)==36 and sum(r['section']=='TIMED' for r in rows)==24
    return rows


def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS or c['methods']!=list(METHODS)
            or c['strategy']!=STRATEGY or c['A_method']!='BETA1_ONE_PHASE'
            or any(c[k] for k in ('head_elision','training','online_teachers','real_new_input_confirmation','endpoint_tuning'))
            or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=104.97136333301378
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<=8
            or len(c['requests'])!=4 or c['main_timing']!='SYNCHRONIZED_TEXT_ENCODING_DENOISING_VAE_DECODING'
            or c['primary_lambda']!=525.1463509809399 or c['warmup_repeats']!=2
            or any(r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93 or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests'])):
        raise ValueError('Exact complete24/six controls and twelve full warmups required')
    matrix([r['name'] for r in c['requests']])


def validate(project,stage):
    project,stage=Path(project),Path(stage);reg=json.loads((stage/'registration.json').read_text());c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    for n,h in reg['payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('Frozen H1 payload differs: '+n)
    for n,h in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/n)!=h:raise ValueError('Pinned runtime changed: '+n)
    auth=json.loads((stage/c['authority_ref']).read_text())
    assert auth['direct_user_authorization'] and auth['automatic_single_job_gpu_hours']==8 and not auth['usage_reset'] and auth['new_cumulative_cap_gpu_hours']==c['cumulative_cap_GPUh']
    for key in ('cost','baseline','previous_parameters'):
        assert sha(stage/c[key+'_ref'])==c[key+'_sha256']
    cost=json.loads((stage/c['cost_ref']).read_text());assert cost['forecast_complete_GPUh']==c['forecast_complete_GPUh'] and cost['total_paths']==36
    previous=json.loads((stage/c['previous_parameters_ref']).read_text())
    tables={}
    for group in ('SOURCE_PHASE','SOURCE'):
        item=c['table_parameters'][group];assert sha(stage/item['ref'])==item['sha256']
        p=json.loads((stage/item['ref']).read_text());validate_parameters(p)
        assert p['table_model']['grouping']==group and p['old_math_parameters_fingerprint']==previous['fingerprint'] and p['gamma']==previous['gamma']
        assert p['lambda_seconds_per_weighted_absolute_MSE']==c['primary_lambda'] and p['cost_seconds']==previous['cost_seconds']
        for n,h in p['sources'].items():assert sha(stage/n)==h
        tables[group]=p
    for n,h in previous['sources'].items():assert sha(stage/n)==h
    proof=json.loads((stage/'sampling-CPU-result.json').read_text())
    assert proof['status']==CPU_STATUS and proof['actual_CPU_paths']==96 and proof['complete_method_paths']==proof['clean_control_paths']==48 and not proof['CUDA_initialized'] and not proof['GPU_submissions']
    assert {v['flow'] for v in proof['checks']}=={False,True}
    assert all(set(v['sources_exercised'])=={'D','P'} and set(v['readouts_exercised'])=={'C','A'} for v in proof['checks'])
    for n,h in proof['payload_sha256'].items():assert reg['payload_sha256'].get(n)==h
    _,_,old,inputs=current_window_original_inputs(project,project/c['original_parent_stage'])
    assert old['preregistration']['requests']==c['requests']
    specs=inputs[1][STRATEGY]
    assert specs['SOURCE_RA']['threshold']==previous['original_RA_threshold']
    prices=previous['cost_seconds'];actual=specs['A_CPD_BETA1_ONE_PHASE']['costs']
    assert (actual.C,actual.P,actual.D)==(prices['C'],prices['P'],prices['D'])
    baseline=json.loads((stage/c['baseline_ref']).read_text())
    assert len(baseline['rows'])==16 and set(r['method'] for r in baseline['rows'])==set(METHODS[:4])
    for row in baseline['rows']:
        for key in ('video_artifact','final_artifact'):
            a=row[key];p=Path(a['path']);assert sha(p)==a['sha256'] and p.stat().st_size==a['bytes']
    return c,reg,old,inputs,tables,previous
