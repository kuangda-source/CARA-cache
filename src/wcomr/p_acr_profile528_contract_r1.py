"""Frozen actual PA12 scope and read-only local bindings, not GPU authority."""
import hashlib
import json
import math
from pathlib import Path

CARD='WC-P-ACR-H1-BASE4-DIAG4-LOCAL12-PRICE20-FULL528-R1-20261015-A'
RUN='wc-p-acr-h1-local12-price20-full528-r1'
H1_FP='34ef948ed2a309e8b1cae4b72b780c14e21d63383fa1eadcdfc8803c3d5beef8'
COEFF_FP='a195c62903f58e4bb0d6800a4aa93175472607b44a7b4ae8f2a2d58e607df6cb'
COUNTS={'requests':4,'baseline_parents':4,'diagnostic_parents':4,'full_paths':8,
        'ordinary_pairs':288,'origins':12,'active_D_primary':8,'A_boundary':2,'C_boundary':2,
        'actions':5,'warmups_each_action':1,'formal_repetitions_each_action':3,
        'diagnostic_pairs':240,'warmup_pairs':60,'formal_pairs':180,
        'pairs':528,'CFG_calls':1056,'raw_point_files':12,'raw_point_tensors':480,
        'parent_vector_files':8,'parent_vector_tensors':296,'all_raw_files':20,
        'all_raw_tensors':776,'loads':1}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_contract(c):
    if (c['card']!=CARD or c['run_id']!=RUN or c['scope_counts']!=COUNTS
            or c['H1_fingerprint']!=H1_FP or c['coefficients_fingerprint']!=COEFF_FP
            or c['strategy']!='WORKING_P_AGE_NONZERO_REBASE'
            or c['actions']!=['C','A','D','Pc','Pu'] or c['source_update']!='ACR_READOUT_NOT_REFRESH'
            or c['automatic_single_job_GPUh']!=8 or c['cumulative_cap_GPUh']!=104.97136333301378
            or c['whole_scope_not_split'] is not True
            or any(c[k] for k in ('GPU_authorized','GPU_execution_selected','training','human_review','F_B_enabled',
                'fit_on_current_teacher','ACR_REFRESH','source_rebase','head_elision','budget_reset'))
            or c['new_card_authorization_ref'] is not None
            or c['past_history_difference']!='PAST_ORDINARY_DD_ONLY'
            or c['per_action_constructor_cost_charged'] is not True
            or not math.isfinite(c['forecast_complete_GPUh']) or c['forecast_complete_GPUh']<=0
            or len(c['requests'])!=4 or len(c['states'])!=12):
        raise ValueError('Complete fixed PA12/price20/readout-only scope and CPU-only authority required')
    names=[r['name'] for r in c['requests']]
    if len(set(names))!=4:raise ValueError('Four distinct original CAL requests required')
    for r in c['requests']:
        if (r['seed']!=0 or r['num_steps']!=35 or r['num_output_frames']!=93
                or r['resolution']!='432,768' or r['guidance']!=7):
            raise ValueError('Original seed/spec/CFG/35-request36-update input required')
    for index,scene in enumerate(names):
        states=[s for s in c['states'] if s['scene']==scene]
        steps=[12,23,29 if index in (0,2) else 30]
        if [s['step'] for s in states]!=steps:raise ValueError('No missing state substitution')
        for i,s in enumerate(states):
            late=i==2
            if (s['seed']!=0 or s['expected_source']!='D'
                    or s['expected_source_birth']!=(24 if late else steps[i]-1)
                    or s['expected_source_age']!=(steps[i]-24 if late else 1)
                    or s['expected_H1_readout']!=('A' if late and steps[i]==29 else 'C' if late else 'D')
                    or s['selector_used_new_teacher_or_endpoint']):
                raise ValueError('Preselected actual H1 source/action/age changed')
    if c['checkpoint_reserves']!={'logical_copy_cap_bytes':6*(1<<30),
            'workspace_reserve_bytes':4*(1<<30),'paired_prefix_reserve_bytes':4*(1<<30)}:
        raise ValueError('Original combined physical/owned two-copy gate required')


def validate_local_bindings(root,c):
    """No SSH, CUDA, weights or mutable budget; exact actual input identity."""
    root=Path(root);validate_contract(c)
    values={}
    for role,binding in c['references'].items():
        if sha(root/binding['ref'])!=binding['sha256']:raise ValueError('Changed bound reference: '+role)
        values[role]=json.loads((root/binding['ref']).read_text())
    if (values['requests']['requests']!=c['requests'] or values['selection']['states']!=c['states']
            or values['selection']['base_method_fingerprint']!=H1_FP):
        raise ValueError('Original requests/teacher-free E0 selection differ')
    from .source_phase_absolute_h1_control_r1 import validate_parameters
    table=values['H1'];validate_parameters(table);prior=values['previous']
    if (table['fingerprint']!=H1_FP or table['old_math_parameters_fingerprint']!=prior['fingerprint']
            or table['gamma']!=prior['gamma'] or table['gamma']!=.7235237005554214
            or c['gamma']!=table['gamma']):
        raise ValueError('Actual frozen H1 gamma/table/prior required, not the synthetic CPU regime')
    coeff=values['coefficients']
    coeff_body={k:v for k,v in coeff.items() if k!='fingerprint'}
    if (coeff['fingerprint']!=COEFF_FP or hashlib.sha256(json.dumps(coeff_body,sort_keys=True,allow_nan=False).encode()).hexdigest()!=COEFF_FP
            or coeff['A_gamma']!=table['gamma'] or coeff['current_omitted_teacher_online']):
        raise ValueError('No coefficient refit or different A gamma on PA teacher')
    cost=values['cost']
    if (cost['full_paths']!=8 or cost['complete_pairs']!=528 or cost['loads']!=1
            or cost['forecast_complete_GPUh']!=c['forecast_complete_GPUh']):
        raise ValueError('Complete load/parent/diagnostic/restore cost changed')
    proof=values['profile_CPU']
    if (proof['status']!='PA_PROFILE20_FULL48_96_ORIGINS1920_TRIALS_INDEPENDENT_CPU_ACCEPTED'
            or proof['full_CPU_paths']!=48 or proof['origins']!=96 or proof['extra_pairs']!=1920
            or not proof['all_audit_quiet_candidate_payloads_and_original_parent36_equal']
            or not proof['per_action_preparation_charged_verified'] or proof['GPU_submissions']):
        raise ValueError('Complete profile CPU required; not a real production entry proof')
    setup=values['setup']
    if (setup['model']!='2B/post-trained' or setup['disable_guardrails']
            or setup['offload_diffusion_model'] or setup['use_torch_compile']):
        raise ValueError('Original guarded model/setup required')
    return values


def require_new_GPU_permission(c,permission,production_proof=None):
    # The old remaining48/strict8 budget remains a budget identity. It cannot
    # revoke the subsequent explicit stop of new GPU experiments.
    if (not isinstance(production_proof,dict)
            or production_proof.get('status')!='PA_LOCAL12_PROFILE528_ACTUAL_PRODUCTION_CPU_ACCEPTED'
            or production_proof.get('scope_counts')!=COUNTS
            or not isinstance(permission,dict) or permission.get('direct_user_authorization') is not True
            or permission.get('card')!=CARD or permission.get('scope_counts')!=COUNTS
            or permission.get('forecast_complete_GPUh')!=c['forecast_complete_GPUh']
            or permission.get('production_CPU_accepted') is not True):
        raise ValueError('Fresh concrete PA12 permission and actual production CPU still required')
