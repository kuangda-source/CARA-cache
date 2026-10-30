"""Native post-release adapter for the frozen S risk and one-exchange rule.

The original Torch collector/schedule modules remain byte-identical. This
adapter uses their unchanged scalar rule and the same production grammar;
CPU history-slot evidence is not free-running or endpoint evidence.
"""
import math

from .policy_generator_r1.interval_grammar import Edge,Profile,compile_policy,digest
from .sq_s_data_terminal_r2 import TARGETS,require
from .sq_s_spec_r2 import IDENTITY_SHA,UPPER_SHA


def C_policy(profile,dense):
    require(len(dense)==19 and dense==sorted(set(dense)) and 24 in dense,
        'Original ordered S19 mask and extra protected D24 required')
    return compile_policy(profile,[Edge(start,end) for start,end in zip(dense,dense[1:]+[37])])


def domain(scope,contract):
    require(contract['rule_sha256']==digest({k:v for k,v in contract.items() if k!='rule_sha256'})
        and contract['execution_identity_sha256']==IDENTITY_SHA
        and scope['scope_sha256']==contract['upper_scope_sha256']==UPPER_SHA
        and scope['scope_sha256']==digest({k:v for k,v in scope.items() if k!='scope_sha256'})
        and scope['profile']==contract['profile'],'Original pre-data S risk-rule identity differs')
    require(contract['objectives']==['BR','DIAG','CFG']
        and contract['rank_rule']=='R(add)-R(remove); positive only; ties by (remove,add)'
        and contract['missing_rows_fill_or_interpolation'] is False
        and contract['posthoc_second_budget_search_authorized'] is False
        and contract['all_objectives_use_identical_normalization_cohort_weights_support_and_candidates'] is True,
        'Original common S objectives, tie rule and no-search contract required')
    values=dict(contract['profile'])
    for key in ('protected_dense','alpha_candidates'):values[key]=tuple(values[key])
    profile=Profile(**values);base=contract['baselines']['F19_C']
    require(C_policy(profile,base)==scope['policies']['F19-C'],'Original F19 parent and risk initialization differ')
    protected=set(profile.protected_dense)|{24};candidates=[]
    for remove in sorted(set(base)-protected):
        for add in sorted(set(TARGETS)-set(base)):
            dense=sorted((set(base)-{remove})|{add})
            try:policy=C_policy(profile,dense)
            except ValueError:continue
            past=[];histories=[]
            for step,action in enumerate(policy['actions'],1):
                if action=='D':past.append(step)
                else:histories.append([step,past[-2],past[-1]])
            candidates.append(dict(remove=remove,add=add,dense=dense,history=histories,
                policy_fingerprint=policy['fingerprint']))
    require(len(candidates)==contract['candidate_count']==170 and profile.max_source_age==28,
        'Original common production S candidate denominator differs')
    baselines={name:C_policy(profile,dense) for name,dense in contract['baselines'].items()}
    require(set(baselines)=={'F19_C','Uniform19_C','time_prior_C'}
        and baselines['Uniform19_C']==baselines['time_prior_C'],
        'Original teacher-free Uniform19/time-prior alias required')
    return profile,candidates,baselines


def rank(risk,candidates,base):
    ranked=sorted([dict(remove=row['remove'],add=row['add'],score=risk[row['add']]-risk[row['remove']])
        for row in candidates],key=lambda row:(-row['score'],row['remove'],row['add']))
    best=ranked[0] if ranked and ranked[0]['score']>0 else None
    selected=next(row for row in candidates if best and (row['remove'],row['add'])==(best['remove'],best['add'])) if best else None
    return dict(dense=base if selected is None else selected['dense'],exchange=selected,
        score=0. if best is None else best['score']),ranked


def validated_domain(scope,contract,history):
    """Accept independent selector-slot coverage before any new S dispatch."""
    profile,candidates,baselines=domain(scope,contract)
    require(history['rule_sha256']==contract['rule_sha256'] and history['status']=='S_SELECTOR_HISTORY_SLOTS_CPU_PASS'
        and history['GPU_submissions']==0 and history['free_running_or_endpoint_acceptance'] is False
        and history['candidate_policy_fingerprints']==[row['policy_fingerprint'] for row in candidates]
        and history['production_source_sha256']==contract['legacy_source_sha256']['production_sampling'],
        'Original independent S selector/history-slot CPU proof required')
    policies={policy['fingerprint']:policy for policy in baselines.values()}
    policies.update({row['policy_fingerprint']:C_policy(profile,row['dense']) for row in candidates})
    expected_history=set()
    for policy in policies.values():
        past=[]
        for step,action in enumerate(policy['actions'],1):
            if action=='D':past.append(step)
            else:expected_history.add((step,*past[-2:]))
    require(history['supported_C_histories']==[list(row) for row in sorted(expected_history)]
        and history['checked_policy_fingerprints']==sorted(policies)
        and history['checked_distinct_policies']==len(policies)
        and history['checked_selector_pairs']==36*len(policies),
        'Incomplete original common S history-slot support')
    return profile,candidates,baselines


def from_validated_rows(rows,scope,contract,history,execution_identity):
    """The caller first accepts FP64 moments, original release and all bytes."""
    profile,candidates,baselines=validated_domain(scope,contract,history)
    prompts=contract['prompts'];parents=contract['parents'];objectives=('BR','DIAG','CFG')
    require(prompts==scope['prompts'] and len(prompts)==2 and parents==['Shared25-C','F19-C']
        and contract['prompt_weights']==[.5,.5] and contract['parent_weights']==[.5,.5]
        and contract['propagation']==dict(kind='UNIFORM_G1',targets=list(TARGETS),g=[1.]*27),
        'Frozen common S prompt/parent/propagation weights differ')
    expected={(prompt,parent,step) for prompt in prompts for parent in parents for step in TARGETS}
    indexed={(row['prompt'],row['parent'],row['step']):row for row in rows}
    require(len(rows)==len(indexed)==108 and set(indexed)==expected,'Complete original108 S rows required; no fill or interpolation')
    require(all(row['noise_grid_sha256']==contract['noise_grid_sha256'] for row in rows),
        'Original common actual S noise grid differs')
    def aggregate(selected_prompts):
        value={name:{} for name in objectives}
        for name in objectives:
            for step in TARGETS:
                scalars=[indexed[prompt,parent,step]['moments']['normalized'][name]
                    for prompt in selected_prompts for parent in parents]
                require(all(type(x) in (float,int) and math.isfinite(x) and x>=0 for x in scalars),
                    'Finite original normalized S risks required')
                value[name][step]=sum(.5*x for x in scalars)/len(selected_prompts)
                require(math.isfinite(value[name][step]),'Aggregated S risk is nonfinite')
        return value
    risk=aggregate(prompts);choices={};scores={};policies=dict(baselines)
    for name in objectives:
        choice,scores[name]=rank(risk[name],candidates,contract['baselines']['F19_C']);choices[name]=choice
        policies['S_'+name+'19']=C_policy(profile,choice['dense'])
    classes={}
    for name,policy in policies.items():
        classes.setdefault(digest([execution_identity,policy['actions'],policy['shared_alpha']]),[]).append(name)
    per_prompt={}
    for prompt in prompts:
        per_risk=aggregate([prompt]);per_prompt[prompt]={}
        for name in objectives:
            choice,ranking=rank(per_risk[name],candidates,contract['baselines']['F19_C'])
            per_prompt[prompt][name]=dict(choice=choice,ranking=ranking)
    diagnostic={name:dict(same_top_exchange=all(
        per_prompt[prompt][name]['choice']['dense']==per_prompt[prompts[0]][name]['choice']['dense'] for prompt in prompts),
        score_gap_top2=scores[name][0]['score']-scores[name][1]['score']) for name in objectives}
    identity_check=dict(max_normalized_absolute_error=max(
        row['moments']['identity_abs_error']/row['moments']['teacher_branch_energy'] for row in rows),
        max_normalized_tolerance=max(
        row['moments']['identity_tolerance']/row['moments']['teacher_branch_energy'] for row in rows),
        scope='FP64 guided identity reduction only; not a total local-risk or endpoint error bound',
        selection_threshold_added=False)
    return dict(status='S_FROZEN_RISK_AND_COMMON_MASK_PROPOSALS_NOT_ENDPOINT_ACCEPTANCE',
        rule_sha256=contract['rule_sha256'],risk=risk,choices=choices,scores=scores,policies=policies,
        execution_equivalence=classes,per_prompt_diagnostics=per_prompt,ranking_diagnostics=diagnostic,
        guided_identity_diagnostics=identity_check,
        CFG_DIAG_same_mask=choices['CFG']['dense']==choices['DIAG']['dense'],
        complete_same_state_rows=108,common_candidate_count=170,
        parent_local_risk_is_not_endpoint_marginal=True,free_running_or_endpoint_acceptance=False,
        GPU_ready=False)
