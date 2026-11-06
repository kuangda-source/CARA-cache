"""H-T42 full four-cell binding; one new WC parent, fixed existing Native reference."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import torch
from .full_sampling import CompleteStateRoundtrip
from .mid_coverage import WC_FIELDS, tree_digest
from .rv0_fork import WC_CONFIGURATION
from .rv0_cfg_factorial_causal import run_cfg_factorial_batch

CARD='WC-W3-CFG-FACTORIAL-R1-20261008-A'
RUN='wc-w3-cfg-factorial-r1'
COUNTS={'WC_parents':1,'complete_suffixes':10,'new_videos':6,'existing_Native_references':1,'factorial_cell_losses':4,'primary_signed_comparisons':4,'interaction_contrasts':1}
DYNAMIC={'GPU_execution_selected','gpu_uuid','production_cpu_receipt_sha256','cumulative_cap_GPUh','budget_extension_authority'}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def binding(config):
    return hashlib.sha256(json.dumps({k:v for k,v in config.items() if k not in DYNAMIC},sort_keys=True,separators=(',',':')).encode()).hexdigest()

def load_module(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def read_prior(stage):
    raw=gzip.decompress((stage/'reports/wc_w3_d46_r3_complete_20261008_runner_json_native.gz').read_bytes())
    r=json.loads(raw)
    if r['status']!='D46_TWO_SEEDS_GPU_CORE_COMPLETE_AUDIT_AND_SCORE_PENDING' or r['cases'][1]['seed']!=2:
        raise ValueError('Completed original seed2 provenance differs')
    return r,r['cases'][1]['WC']['requests'][0]

def validate_contract(c,stage):
    s=c['preregistration'];original=json.loads((stage/'seed-config.json').read_text())
    if (s['card']!=CARD or s['run_id']!=RUN or s['scope_counts']!=COUNTS or s['seed']!=2
            or s['snapshot_step']!=22 or s['snapshot_after_call']!=44
            or s['requested_full_calls']!={'BASE':[],'CFG0':[45],'CFG1':[46],'PAIRED':[45,46]}
            or s['same_existing_request']!=original['preregistration']['requests'][1]
            or s['suffix_order']!=['OFF1','OFF2','BASE_first','CFG1_second','CFG0_first','PAIRED_second','PAIRED_first','CFG0_second','CFG1_first','BASE_second']
            or s['main_comparisons']!=['CFG0_vs_BASE','CFG1_vs_BASE','PAIRED_vs_CFG0','PAIRED_vs_BASE']
            or s['remaining_policy']!='ORIGINAL_WC_ADAPTIVE_FROM_EACH_OWN_STATE'
            or not 0<s['forecast']['forecast_complete_GPUh']<=2
            or c['sampling_protocol']!=original['sampling_protocol']
            or type(c['GPU_execution_selected']) is not bool
            or c['execution_run_id']!=RUN or s['estimand']!='CURRENT_CARD_SHARED_STATE_FIXED_REGISTERED_NATIVE_REFERENCE'
            or s['historical_full_state_equality_required'] is not False
            or not s['within_card_complete_state_equality_and_restoration_required']
            or not s['prospective_raw_solver_dictionary_required']
            or type(c['cumulative_cap_GPUh']) not in (int,float) or c['cumulative_cap_GPUh']<24):
        raise ValueError('Complete registered paired CFG scope/protocol/autonomy differs')
    if sha(stage/c['preregistration_ref'])!=c['preregistration_sha256'] or json.loads((stage/c['preregistration_ref']).read_text())!=s:
        raise ValueError('Frozen preregistration bytes differ')
    policy=json.loads((stage/'manifests/wc_execution_autonomy_authorization_20261007.json').read_text())
    if (policy['automatic_single_job_gpu_hours']!=2 or policy['cumulative_cap_gpu_hours']!=24
            or policy['usage_reset'] is not False or policy['legacy_per_card_seconds_caps_revoked'] is not True):
        raise ValueError('Direct user autonomy/budget policy differs')

def validate_budget_authority(c,project,stage):
    import math
    cap=c['cumulative_cap_GPUh'];authority=c.get('budget_extension_authority')
    if not math.isfinite(cap):raise ValueError('Finite cumulative cap required')
    if cap==24:
        if authority is not None:raise ValueError('Unexpected extension authority at original24 cap')
        return
    if type(authority) is not dict or set(authority)!={'ref','sha256'}:
        raise ValueError('Direct cumulative budget extension authority required')
    ref=authority['ref']
    if (not ref.startswith('manifests/') or '..' in Path(ref).parts or Path(ref).is_absolute()
            or sha(stage/ref)!=authority['sha256']):
        raise ValueError('Bound budget authorization file differs')
    proof=json.loads((stage/ref).read_text())
    if (proof.get('previous_cap_gpu_hours')!=24 or proof.get('new_cumulative_cap_gpu_hours')!=cap
            or proof.get('usage_reset') is not False or proof.get('direct_user_authorization') is not True
            or proof.get('approved_card')!=CARD or proof.get('run_id')!=RUN
            or not proof.get('source_user_instruction') or not proof.get('authorized_unix')):
        raise ValueError('Actual direct extension scope/cumulative history differs')
    live=json.loads((project/'reports/budget.json').read_text())
    if live['cap_gpu_hours']!=cap:raise ValueError('Authorized cap and live cumulative ledger differ')


def validate(project,stage):
    c=json.loads((stage/'factorial-config.json').read_text());validate_contract(c,stage);validate_budget_authority(c,project,stage)
    for name,h in c['payload_sha256'].items():
        if sha(stage/name)!=h:raise ValueError('Frozen staged source/evidence changed: '+name)
    for name,h in c['project_input_sha256'].items():
        if sha(project/name)!=h:raise ValueError('Original project identity changed: '+name)
    if c.get('registered_input_staged_paths')!={'reports/budget.json':'factorial-budget-at-registration.json'}:
        raise ValueError('Registered budget archive alias differs')
    for name,h in c['preregistration']['input_sha256'].items():
        alias=c['registered_input_staged_paths'].get(name,name)
        if sha(stage/alias)!=h:raise ValueError('Registered existing evidence changed: '+name)
    if json.loads((stage/'factorial-request.jsonl').read_text())!=c['preregistration']['same_existing_request']:
        raise ValueError('Production request bytes/config differ')
    # Same original asset/scheduler/guardrail validator, independent staged copy.
    load_module(stage/'scripts/run_wc_s0_profile.py','paired_asset_validator').validate(project,stage,project/'runtime')
    proof=json.loads((stage/c['core_cpu_audit_ref']).read_text())
    if (proof['status']!='CFG_FACTORIAL_CORE_CPU_NATIVE_AND_INDEPENDENT_RAW_SCOPE_RECONSTRUCTION_PASS_NOT_GPU'
            or proof['source_revision']!=c['core_source_revision'] or proof['mutation_refusals']!=92
            or (proof['complete_successful_parents'],proof['complete_successful_suffixes'],proof['successful_mock_outputs'])!=(4,40,24)
            or proof['CUDA_initialized'] is not False or not proof['budget_unchanged']):
        raise ValueError('Actual paired core CPU evidence differs')
    core=json.loads((stage/c['core_manifest_ref']).read_text())
    if any(c['payload_sha256'].get(n)!=h for n,h in core['payload_sha256'].items()):
        raise ValueError('Passed core CPU source changed')
    raw=gzip.decompress((stage/c['core_receipt_ref']).read_bytes());receipt=json.loads(raw)
    if receipt['exit_code']!=0 or receipt['result_sha256']!=proof['original_result_sha256'] or receipt['source_revision']!=c['core_source_revision']:
        raise ValueError('Actual core CPU receipt/source differs')
    for key in ['existing_Native']:
        item=c['preregistration'][key];path=Path(item['path'])
        if ((project/'outputs/wc-w3-d46-fresh-seeds-r3').resolve() not in path.resolve().parents
                or path.stat().st_size!=item['bytes'] or sha(path)!=item['sha256']):
            raise ValueError('Frozen original video changed: '+key)
    old,_=read_prior(stage)
    if old['model_context']!='Cosmos-Predict2.5-2B:'+sha(project/'configs/f1_setup.json'):
        raise ValueError('Historical model context differs')
    return c,stage

def validate_selected(c,project,stage):
    if c['GPU_execution_selected'] is not True or c['gpu_uuid']!='GPU-cebf7119-cf03-23b9-e192-cd196332b704':
        raise ValueError('Fresh selected target required')
    path=project/c['production_cpu_stage']/'receipt.json'
    if sha(path)!=c['production_cpu_receipt_sha256']:raise ValueError('Actual production CPU receipt changed')
    r=json.loads(path.read_text())
    if (r['exit_code']!=0 or r['status']!='CFG_FACTORIAL_PRODUCTION_CPU_PASS_NOT_GPU'
            or r['CUDA_initialized'] is not False or r['GPU_submissions']!=0
            or r['config_binding_sha256']!=binding(c) or r['payload_after_sha256']!=c['payload_sha256']):
        raise ValueError('Same-source actual production CPU proof required')
    return r

def run_portfolio(inference,samples,wc,settings,*,state,save,output,inference_module,mode_setup,runtime,scope,sampling_policy,prior_row):
    if (len(samples)!=1 or not all(samples[0].model_dump(mode='json')[k]==v for k,v in scope['same_existing_request'].items()) or state.get('cases')):
        raise ValueError('Exactly one original seed2 request required')
    sample=samples[0];model=inference.pipe.model;net=model.net
    initial=CompleteStateRoundtrip(net,model.sample_scheduler,torch.zeros(1));fingerprint=initial.fingerprint()
    original_keys={k for k in WC_FIELDS if hasattr(net,k)}
    settings_before={k:copy.deepcopy(getattr(net,k)) for k in WC_CONFIGURATION if hasattr(net,k)}
    def restore():
        initial.restore()
        for name in set(WC_FIELDS)-original_keys:
            if hasattr(net,name):delattr(net,name)
        for name,value in settings_before.items():setattr(net,name,copy.deepcopy(value))
        if initial.fingerprint()!=fingerprint:raise ValueError('Paired production initial restore failed')
    case={'name':sample.name,'seed':sample.seed,'status':'STARTED','WC':{}}
    state.update(planned_scope=COUNTS,cases=[case],existing_Native=scope['existing_Native']);save()
    try:
        context=(scope['run_id']+':'+sample.name,state['model_context'],tree_digest(sample.model_dump(mode='json')))
        config={'sample_names':[sample.name],'run_id':scope['run_id'],'target_calls':[46],'paired_full_calls':[45,46],
            'maximum_age_solver_steps':32,'logical_copy_cap_bytes':6*(1<<30),'workspace_reserve_bytes':4*(1<<30)}
        run_cfg_factorial_batch(inference,samples,wc,settings,state=case['WC'],save=save,output=output/sample.name/'WC',
            inference_module=inference_module,contexts=[context],mode_setup=mode_setup,runtime=runtime,config=config)
        case['fixed_reference_estimand']='CURRENT_CARD_SHARED_STATE_FIXED_REGISTERED_NATIVE_REFERENCE'
        case['historical_full_state_acceptance']=False
        case['status']='CFG_FACTORIAL_GPU_CONTROLS_COMPLETE_FIXED_REFERENCE_SCORE_PENDING'
        state['status']='CFG_FACTORIAL_GPU_CORE_COMPLETE_FIXED_REFERENCE_AUDIT_SCORE_PENDING';save()
    except BaseException as error:
        state.update(status='CFG_FACTORIAL_TECH_BLOCKED_FULL_DENOMINATOR_RETAINED',error=str(error));save();raise
    finally:restore()
