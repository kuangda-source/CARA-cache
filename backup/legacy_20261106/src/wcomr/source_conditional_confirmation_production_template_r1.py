"""Full50 confirmation production template; explicit freeze is required for GPU."""
import json,math
from pathlib import Path
from .source_phase_absolute_h1_control_r1 import validate_parameters
from .source_conditional_confirmation_batch_r1 import METHODS,matrix,RUN
from .math_n1_production_r1 import UUID,MODE_REF,sha,write,verify_admission
from .math_n1_production_r2 import current_window_original_inputs

CONFIG='configs/wc_source_conditional_confirmation_full50_production_template_r1_20261013.json'
CARD='WC-SOURCE-CONDITIONAL-CONF40-WARM10-R1-20261013-A'
STRATEGY='WORKING_P_AGE_NONZERO_REBASE'
COUNTS={'requests':8,'methods':5,'scientific_paths':40,'full_warmup_paths':10,'total_paths':50,
    'ordinary_pairs':1800,'ordinary_CFG_calls':3600,'loads':1,'teacher_pairs':0,'score_videos':40}
CPU_STATUS='SOURCE_CONFIRMATION_TWO_FLOW_ALL80_AUDIT80_LEAN80_LEGACY_SEED17_43_CPU_PASS_NOT_GPU'


def validate_contract(c,*,require_frozen=True):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS or c['methods']!=list(METHODS)
            or c['strategy']!=STRATEGY or c['A_method']!='BETA1_ONE_PHASE'
            or any(c[k] for k in ('head_elision','training','online_teachers','endpoint_tuning'))
            or not c['real_new_input_confirmation'] or c['automatic_single_job_GPUh']!=8
            or c['cumulative_cap_GPUh']!=104.97136333301378 or c['primary_lambda']!=525.1463509809399
            or not math.isfinite(c['forecast_complete_GPUh']) or not 0<c['forecast_complete_GPUh']<=8
            or len(c['requests'])!=8 or c['warmup_request']['seed']!=0 or c['warmup_repeats']!=2
            or c['candidate_template']!='TABLE_PHASE_H1'
            or any(r['num_steps']!=35 or r['num_output_frames']!=93 or r['resolution']!='432,768' or r['guidance']!=7 for r in c['requests']+[c['warmup_request']])):
        raise ValueError('Exact full40/two seeds/five methods plus10 CAL warmups required')
    matrix(c['requests'],c['warmup_request'])
    if require_frozen and (not c['candidate_frozen'] or not c['candidate_freeze_ref']
            or not c['candidate_freeze_sha256'] or c['template_production_CPU_only']):
        raise ValueError('Explicit post-development candidate freeze required before GPU')
    if not c['candidate_frozen'] and (c['candidate_freeze_ref'] is not None or c['candidate_freeze_sha256'] is not None):
        raise ValueError('Unfrozen candidate must not carry a fabricated freeze receipt')
    if c['candidate_frozen'] and (not c['candidate_freeze_ref'] or not c['candidate_freeze_sha256']):
        raise ValueError('Frozen candidate needs an actual versioned freeze receipt')


def validate(project,stage,*,require_frozen=True):
    project,stage=Path(project),Path(stage);reg=json.loads((stage/'registration.json').read_text())
    c=json.loads((stage/CONFIG).read_text());validate_contract(c,require_frozen=require_frozen)
    for name,digest in reg['payload_sha256'].items():
        if sha(stage/name)!=digest:raise ValueError('Frozen confirmation payload differs: '+name)
    for name,digest in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/name)!=digest:raise ValueError('Pinned runtime changed: '+name)
    for key in ('cost','previous_parameters','input_manifest','input_protocol','input_audit','matrix_template'):
        assert sha(stage/c[key+'_ref'])==c[key+'_sha256']
    manifest=json.loads((stage/c['input_manifest_ref']).read_text())
    assert manifest['requests']==c['requests'] and manifest['method_positions']==40 and manifest['warmups_planned']==10
    assert manifest['original_E2_full76_unchanged'] and manifest['old_P13h_remains_deferred']
    for source in manifest['selected_sources']:assert sha(stage/source['path'])==source['sha256']
    audit=json.loads((stage/c['input_audit_ref']).read_text())
    assert audit['GPU_submissions']==0 and not audit['ledger_written']
    cost=json.loads((stage/c['cost_ref']).read_text())
    assert cost['total_paths']==50 and cost['forecast_complete_GPUh']==c['forecast_complete_GPUh']
    assert c['forecast_complete_GPUh']==sum(cost['components'].values())*cost['contingency_multiplier']/3600
    auth=json.loads((stage/c['authority_ref']).read_text())
    assert auth['direct_user_authorization'] and auth['automatic_single_job_gpu_hours']==8 and not auth['usage_reset']
    assert auth['new_cumulative_cap_gpu_hours']==c['cumulative_cap_GPUh']
    previous=json.loads((stage/c['previous_parameters_ref']).read_text());tables={}
    for group in ('SOURCE_PHASE','SOURCE'):
        item=c['table_parameters'][group];assert sha(stage/item['ref'])==item['sha256']
        table=json.loads((stage/item['ref']).read_text());validate_parameters(table)
        assert table['old_math_parameters_fingerprint']==previous['fingerprint']
        assert table['gamma']==previous['gamma'] and table['lambda_seconds_per_weighted_absolute_MSE']==c['primary_lambda']
        for name,digest in table['sources'].items():assert sha(stage/name)==digest
        tables[group]=table
    for name,digest in previous['sources'].items():assert sha(stage/name)==digest
    proof=json.loads((stage/'sampling-CPU-result.json').read_text())
    assert proof['status']==CPU_STATUS and proof['actual_CPU_paths']==240 and proof['confirmation_requests']==8
    assert proof['complete_method_paths']==proof['clean_control_paths']==proof['legacy_control_paths']==80
    assert not proof['CUDA_initialized'] and not proof['GPU_submissions']
    for name,digest in proof['payload_sha256'].items():assert reg['payload_sha256'].get(name)==digest
    _,_,old,inputs=current_window_original_inputs(project,project/c['original_parent_stage'])
    assert c['warmup_request'] in old['preregistration']['requests']
    prices=previous['cost_seconds'];actual=inputs[1][STRATEGY]['A_CPD_BETA1_ONE_PHASE']['costs']
    assert (actual.C,actual.P,actual.D)==(tables['SOURCE_PHASE']['source_A_cost_seconds']['D'],prices['P'],prices['D'])
    if require_frozen:
        assert sha(stage/c['candidate_freeze_ref'])==c['candidate_freeze_sha256']
        freeze=json.loads((stage/c['candidate_freeze_ref']).read_text())
        assert freeze['method']=='TABLE_PHASE_H1' and freeze['method_fingerprint']==tables['SOURCE_PHASE']['fingerprint']
        assert freeze['confirmation_endpoint_tuning']==False
    return c,reg,old,inputs,tables,previous
