"""Independent complete64 real-input contract for current-P source control.

The complete32 parent supplies immutable calibration and matched Native data;
its card or authorization never authorizes this new run.
"""
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

from .current_birth_real_inputs_r1 import load, sha
from .real_working_epoch_parameters_r1 import METHODS, FINGERPRINT, THRESHOLD, digest
from .source_aware_current_birth_control_r1 import CURRENT_BIRTH_RULE
from .source_aware_working_epoch_control_r2 import STRATEGIES
from .cfg_guided_w1_deployment_production import NAMES

CARD = 'WC-CURRENT-BIRTH-CAPD-FULL64-R1-20261010-A'
RUN = 'wc-current-birth-capd-full64-r1'
CONFIG = 'current-birth-full64-config.json'
REQUESTS = 'current-birth-full64-requests.jsonl'
COUNTS = {'requests':4, 'working_epoch_strategies':2, 'methods_per_request':8,
    'complete_paths':64, 'maximum_videos':64, 'solver_updates':2304, 'net_calls':4608,
    'maximum_guided_outputs':2304, 'maximum_final_latents':64,
    'reused_native_reference_slots':4, 'maximum_fidelity_pairs':64}
DYNAMIC = {'GPU_execution_selected', 'gpu_uuid', 'single_job_exception_authority',
    'production_cpu_stage', 'production_cpu_receipt_sha256'}


def binding(c):
    return digest({k:v for k,v in c.items() if k not in DYNAMIC})


def validate_contract(c, stage):
    stage=Path(stage); r=c['preregistration']
    expected={'card':CARD, 'run_id':RUN, 'scope_counts':COUNTS,
        'strategies':list(STRATEGIES), 'methods':list(METHODS), 'repetitions':['first'],
        'branch_order':['conditional','negative_prompt'], 'guided_weights':[8,-7],
        'state_steps':[12,30,35,36], 'current_P_birth_rule':CURRENT_BIRTH_RULE,
        'fixed_P_steps':[], 'P_mode':'ROTATION_050', 'P_layers':[4,10,16,22],
        'P_block_size':128, 'P_ratio':.5, 'shared_A_phase_boundary':25,
        'shared_A_strength':[1.,.5], 'maximum_consecutive_P':2,
        'borrowed_D_drift_ratio':1., 'P_future_drift_empirically_calibrated':False,
        'RA_calibration_fingerprint':FINGERPRINT, 'RA_threshold':THRESHOLD,
        'reference_policy':'REUSE_FOUR_ACCEPTED_NATIVE_ONLY_IF_EXACT_INPUT_SOLVER_AND_PROTECTED_PREFIX_MATCH',
        'teacher_calls':0, 'training':False, 'boundary_or_alpha_sweep':False,
        'clean_latency_claim':False, 'independent_confirmation_claim':False}
    if any(r.get(k)!=v for k,v in expected.items()):
        raise ValueError('Complete64 current-P scope, controls or fixed parameters differ')
    if (c['execution_run_id']!=RUN or c['expected_real_components']!=1216
        or c['expected_real_shape']!=[1,16,24,54,96]
        or c['logical_copy_cap_bytes']!=6*(1<<30) or c['workspace_reserve_bytes']!=4*(1<<30)
        or c['paired_prefix_reserve_bytes']!=4*(1<<30)
        or c['cumulative_cap_GPUh']!=77.89524658965853 or c['automatic_single_job_GPUh']!=4
        or type(c['GPU_execution_selected']) is not bool
        or not math.isfinite(r['forecast']['forecast_complete_GPUh'])
        or not 0<r['forecast']['forecast_complete_GPUh']<48
        or [x['name'] for x in r['requests']]!=NAMES
        or c['sampling_protocol']['actual_steps']!=36 or c['sampling_protocol']['cfg_calls']!=72
        or c['sampling_protocol']['timesteps']!=r['timesteps']):
        raise ValueError('Complete64 runtime, forecast or budget binding differs')
    for request in r['requests']:
        if (request['seed']!=0 or request['guidance']!=7 or request['num_steps']!=35
            or request['num_output_frames']!=93 or request['resolution']!='432,768'):
            raise ValueError('Original four CAL settings required')
    actual=[json.loads(line) for line in (stage/REQUESTS).read_text().splitlines() if line]
    if (actual!=r['requests'] or sha(stage/c['preregistration_ref'])!=c['preregistration_sha256']
        or json.loads((stage/c['preregistration_ref']).read_text())!=r):
        raise ValueError('Exact complete64 registration and requests required')


def validate(project, stage):
    project,stage=Path(project),Path(stage)
    c=json.loads((stage/CONFIG).read_text()); validate_contract(c,stage)
    for root,key in ((stage,'payload_sha256'),(project,'project_input_sha256'),(project/'runtime','runtime_source_sha256')):
        for name,value in c[key].items():
            if sha(root/name)!=value: raise ValueError('Complete64 original source changed: '+name)
    policy=json.loads((stage/'manifests/wc_execution_autonomy_authorization_20261010_4gpuh.json').read_text())
    window=json.loads((stage/'manifests/budget_authorization_20261009_wc_new_window_48gpuh.json').read_text())
    if (policy['automatic_single_job_gpu_hours']!=4 or policy['usage_reset']
        or not policy['legacy_per_card_seconds_caps_revoked'] or not window['direct_user_authorization']
        or window['usage_reset'] or window['authorized_remaining_gpu_hours']!=48
        or window['new_cumulative_cap_gpu_hours']!=c['cumulative_cap_GPUh']
        or json.loads((project/'reports/budget.json').read_text())['cap_gpu_hours']!=c['cumulative_cap_GPUh']):
        raise ValueError('Current direct budget and single-card authorization differs')
    rows=[json.loads(line) for line in (project/'configs/cal_w1d8.jsonl').read_text().splitlines() if line]
    if any([x for x in rows if x['name']==r['name']]!=[r] for r in c['preregistration']['requests']):
        raise ValueError('Full original CAL request identity differs')
    reg=json.loads((stage/c['batch_cpu_registration_ref']).read_text())
    audit=json.loads((stage/c['batch_cpu_audit_ref']).read_text())
    if (any(c['payload_sha256'].get(n)!=v for n,v in reg['payload_sha256'].items())
        or audit['exit_code']!=0 or audit['GPU_submissions']!=0 or audit['ledger_written']
        or not audit['independent_source_complete_results_and_actual_artifact_hashes_verified']
        or reg['current_P_birth_rule']!=CURRENT_BIRTH_RULE):
        raise ValueError('New current-P complete CPU source proof required')
    result=json.loads(gzip.decompress((stage/audit['files']['result.json']['local_path']).read_bytes()))
    if (result['status']!='CURRENT_BIRTH_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'
        or result['planned_scope']!=reg['CPU_scope'] or result['CUDA_initialized']
        or result['additional_current_birth_mutation_refusals']!=12
        or result['registered_strategies']!=list(STRATEGIES)
        or (result['actual_complete_solver_updates'],result['actual_normal_net_calls'],result['actual_all_tensors_reloaded'])!=(9216,18432,4736)
        or (audit['independent_tensor_reload']['actual_tensors'],audit['independent_tensor_reload']['full_partial_references'],
            audit['independent_tensor_reload']['independently_replayed_working_policy_decisions'])!=(4736,16,4032)):
        raise ValueError('Whole current-target256 sampler CPU result differs')
    calibration,specs,references,parent,evidence=load(stage)
    if (c['input_binding_fingerprint']!=evidence['binding_fingerprint']
        or c['project_input_sha256']!=parent['project_input_sha256']
        or c['runtime_source_sha256']!={**parent['runtime_source_sha256'],**reg['runtime_source_sha256']}
        or c['sampling_protocol']!=parent['sampling_protocol']
        or c['historical_wc_settings']!=parent['historical_wc_settings']):
        raise ValueError('Same full actual parent/input/solver binding required')
    for ref in references:
        artifact=ref['artifact'];path=Path(artifact['path']).resolve()
        if (not path.is_relative_to((project/'outputs').resolve())
            or path.stat().st_size!=artifact['bytes'] or sha(path)!=artifact['sha256']):
            raise ValueError('Original actual matched Native artifact changed')
    spec=importlib.util.spec_from_file_location('current_birth_existing_assets',stage/'scripts/run_wc_s0_profile.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.validate(project,stage,project/'runtime')
    return c,(calibration,specs,references,evidence)


def validate_selected(c, project, stage):
    if not c['GPU_execution_selected'] or c['gpu_uuid']!='GPU-cebf7119-cf03-23b9-e192-cd196332b704':
        raise ValueError('New complete64 selected target required')
    authority=c['single_job_exception_authority']
    if c['preregistration']['forecast']['forecast_complete_GPUh']>4:
        if not isinstance(authority,dict) or sha(Path(stage)/authority['ref'])!=authority['sha256']:
            raise ValueError('Above4 complete64 requires exact direct human approval')
        approved=json.loads((Path(stage)/authority['ref']).read_text())
        if (not approved['direct_user_authorization'] or approved['card']!=CARD or approved['run_id']!=RUN
            or approved['scope_counts']!=COUNTS or approved['preregistration_sha256']!=c['preregistration_sha256']
            or approved['forecast_complete_GPUh']!=c['preregistration']['forecast']['forecast_complete_GPUh']):
            raise ValueError('Approval does not cover this complete64 card')
    elif authority is not None:
        raise ValueError('Within4 complete card must use standing autonomous authority')
    path=Path(project)/c['production_cpu_stage']/'receipt.json'
    if sha(path)!=c['production_cpu_receipt_sha256']:raise ValueError('Actual full64 production CPU changed')
    proof=json.loads(path.read_text())
    if (proof['exit_code']!=0 or proof['status']!='CURRENT_BIRTH_FULL64_PRODUCTION_CPU_PASS_NOT_GPU'
        or proof['CUDA_initialized'] or proof['GPU_submissions'] or proof['config_binding_sha256']!=binding(c)
        or proof['payload_after_sha256']!=c['payload_sha256']):
        raise ValueError('Same-source complete64 actual production CPU receipt required')
    return proof
