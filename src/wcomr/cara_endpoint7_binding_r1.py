"""Bind the selected46 scope to existing accepted raw freeze bytes, without rereading RGB."""
import copy
from .cara_fast_spec_r1 import digest,policy_from_mask,profile_from
from .policy_price_terminal_r1 import require
from .cara_endpoint7_plan_r1 import NEW_ROLES,REUSED_ROLES,validate as validate_selected

SCHEMA='CARA_ENDPOINT7_BOUND_PROPOSAL_R1'

def proposal(selected,old):
    validate_selected(selected)
    require(selected['same_batch_F19'] and len(selected['physical_matrix'])==46,'Only user-selected46 supported')
    value=copy.deepcopy(old)
    value.update(schema=SCHEMA,endpoint7=True,selected_manifest_scope_sha256=selected['scope_sha256'],
        scientific_roles=list(REUSED_ROLES+NEW_ROLES),formal_matrix=copy.deepcopy(selected['formal_matrix']),
        identity_controls=copy.deepcopy(selected['identity_controls']),
        new_policies={r:copy.deepcopy(selected['roles'][r]['policy']) for r in NEW_ROLES},
        physical_matrix=[{k:v for k,v in s.items() if k not in ('phase','purpose')} for s in selected['physical_matrix']],
        counts=dict(logical_quality_positions=28,reused_metric_positions=12,new_scoring_pairs=16,
            new_GPU_paths=46,warm_paths=7,allD_control_paths=1,formal_candidate_paths=16,
            fresh_native_and_A1_and_F19_controls=12,timing_repeat_paths=10,clean_timing_samples=38,
            postrelease_decoded_identity_controls=13),
        status='SELECTED46_BOUND_POLICIES_PRODUCTION_PREPARATION',CPU_fixture_only=False)
    value['timing'].update(primary_batch_roles=['NATIVE35','F19_A1',*NEW_ROLES,'F19_C'],
        historical_Uniform_times='Separate historical context; never pooled with this allocation')
    value['timing'].pop('historical_F19_and_Uniform_times',None)
    value['acceptance'].pop('all9_identity_controls_required',None)
    value['acceptance'].pop('complete32_and_original_release_before_CPU',None)
    value['acceptance'].update(all13_identity_controls_required=True,
        complete46_and_original_release_before_CPU=True,
        new_scoring='Once only all sixteen new candidate-versus-original-Native pairs, all93 frames')
    value['readiness'].pop('whole32_CPU_accepted',None)
    value['readiness'].update(whole46_CPU_accepted=False,budget_comparator_policy_bound=True,
        budget_comparator_affected_CPU_accepted=True)
    value['budget_comparator']['policy_bound']=True
    value['recipe']['F19_riskswap']=dict(initialization='F19_C',remove_D=21,add_D=35,
        equivalent_objectives=['BR','DIAG','CFG'],new_search=False)
    for s in value['physical_matrix']:s['section']=s['section'].removeprefix('B_')
    value['scope_sha256']=digest({k:v for k,v in value.items() if k!='scope_sha256'})
    validate(value)
    return value

def validate(value):
    require(value['schema']==SCHEMA and value['endpoint7'] is True,'Explicit seven-role proposal required')
    members=value['FIT']+value['CHECK'];physical=value['physical_matrix'];formal=value['formal_matrix']
    require(len(members)==len(set(members))==4 and len(value['FIT'])==len(value['CHECK'])==2,'Original four CAL required')
    require(len(formal)==28 and {(r['member'],r['role']) for r in formal}=={(m,r) for m in members for r in REUSED_ROLES+NEW_ROLES},'Complete28 logical positions required')
    require(all(r['mode']==('REUSE_COMPLETE_SCORE' if r['role'] in REUSED_ROLES else 'GENERATE_AND_SCORE') for r in formal),'Original12 reuse/new16 roles differ')
    expected=[('WARM',('NATIVE35','F19_A1')+NEW_ROLES+('F19_C',),value['FIT'][:1]),
        ('ALLD_EQUIVALENCE',('ALLD',),value['FIT'][:1]),('FORMAL',NEW_ROLES,members),
        ('REPLAY_CONTROL',('NATIVE35','F19_A1','F19_C'),members),('REPEAT',NEW_ROLES+('F19_C',),value['CHECK'])]
    require(len(physical)==len({r['id'] for r in physical})==46,'Complete46 denominator required')
    for section,roles,inputs in expected:
        actual=[(r['member'],r['role']) for r in physical if r['section']==section]
        required={(m,r) for m in inputs for r in roles}
        require(len(actual)==len(required) and set(actual)==required,'Missing/duplicate section: '+section)
    require(all(r['seed']==0 and not r['audit_enabled'] and r['eligible_clean_time']==(r['section'] in ('FORMAL','REPLAY_CONTROL','REPEAT')) for r in physical),'Clean timing/seed differs')
    require(len(value['identity_controls'])==13 and {(r['member'],r['role']) for r in value['identity_controls']}=={(m,r) for m in members for r in ('NATIVE35','F19_A1','F19_C')}|{(value['FIT'][0],'ALLD')},'Complete13 RGB controls required')
    require(set(value['new_policies'])==set(NEW_ROLES) and len({p['fingerprint'] for p in value['new_policies'].values()})==4,'Four distinct accepted policies required')
    for p in value['new_policies'].values():
        dense=[i+1 for i,a in enumerate(p['actions']) if a=='D']
        require(len(dense)==19 and p==policy_from_mask(profile_from(value['profile']),dense),'Exact compiled19D policy required')
    require(not value['GPU_authorized'] and not value['GPU_dispatch_ready'] and not value['ledger_written'] and value['GPU_submissions']==0,'Proposal is not authority')

def mapping(value,policy):
    validate(value)
    require(policy==value['new_policies']['BUDGET_SEARCH19_C'],'Only accepted original budget winner permitted')
    formal=copy.deepcopy(value['formal_matrix'])
    ids={(s['section'],s['member'],s['role']):s['id'] for s in value['physical_matrix']}
    for r in formal:
        if r['mode']=='GENERATE_AND_SCORE':
            r.update(physical_slot_id=ids[('FORMAL',r['member'],r['role'])],metric_alias_of_role=None,counts_as_independent_sample_from_alias=False)
    return dict(budget_policy=copy.deepcopy(policy),budget_role_representative='BUDGET_SEARCH19_C',
        proposal_slot_aliases={s['id']:s['id'] for s in value['physical_matrix']},
        physical_matrix=copy.deepcopy(value['physical_matrix']),formal_matrix=formal,
        identity_controls=copy.deepcopy(value['identity_controls']),
        counts=dict(logical_quality_positions=28,reused_metric_positions=12,new_logical_quality_positions=16,
            new_GPU_paths=46,unique_new_scoring_pairs=16,clean_timing_samples=38),final_quote_must_use_unique_physical_paths=True)

def bind(value,accepted,frozen,freeze_sha256):
    require(accepted['complete_search_accepted'] and accepted['scientific_freeze_written'] and not accepted['CPU_fixture_only']
        and accepted['freeze_sha256']==freeze_sha256 and accepted['complete_physical_paths']==112 and accepted['complete_two_FIT_queries']==51,'Original complete once-freeze acceptance required')
    for k in ('launch_id','run_id','scope_sha256','source_revision','policy','selected','collection_sha256','billing_sha256','actual_GPUh'):
        require(frozen[k]==accepted[k],'Accepted freeze identity differs: '+k)
    result=mapping(value,frozen['policy'])
    result.update(schema='CARA_ENDPOINT7_EXISTING_FREEZE_BINDING_R1',status='FROZEN_POLICY_BOUND_WHOLE_CPU_PENDING',
        proposal_scope_sha256=value['scope_sha256'],original_calibration=copy.deepcopy(frozen),
        original_freeze_path=accepted['freeze_path'],original_freeze_sha256=freeze_sha256,
        CPU_fixture_only=False,whole_card_CPU_accepted=False,selected_policy_affected_CPU_accepted=True,
        GPU_authorized=False,GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False,new_freeze_created=False)
    result['binding_sha256']=digest(result)
    return result
