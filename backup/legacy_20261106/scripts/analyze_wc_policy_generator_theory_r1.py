#!/usr/bin/env python3
"""Small mathematical examples and source audit; no model, GPU or remote work.

These examples check implications and counterexamples, not empirical fidelity.
The registered collection recipe and all production stages remain unchanged.
"""
import argparse
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.policy_generator_r1.budgeted_planner import ScoredEdge, cost_units, solve
from wcomr.policy_generator_r1.interval_grammar import Edge, Profile, enumerate_edges
from wcomr.policy_generator_r1.search_protocol import choose_observed


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError('Preserve the original analysis receipt; choose a new output')
    checks = []

    # Exact rational arithmetic for a correction whose optimum is alpha=1/2.
    e, d = (F(1), F(0)), (F(-2), F(0))
    e2 = sum(x*x for x in e) / 2
    ed = sum(x*y for x,y in zip(e,d)) / 2
    d2 = sum(x*x for x in d) / 2
    values = []
    for alpha in (F(0), F(1,2), F(1)):
        polynomial = e2 + 2*alpha*ed + alpha*alpha*d2
        direct = sum((x+alpha*y)**2 for x,y in zip(e,d)) / 2
        assert polynomial == direct
        values.append(dict(alpha=float(alpha),MSE=float(direct)))
    assert -ed/d2 == F(1,2)
    checks.append(dict(id='QUADRATIC_CONDITIONAL_IDENTITY',verified=True,
        exact_rational_example=values,continuous_optimum=0.5,
        requires_same_state_history_and_output_linear_fusion=True,
        does_not_establish_endpoint_or_global_optimality=True))

    # A true additive graph can be solved conservatively while losing feasible
    # unrounded proposals. This is not a measurement on either server.
    profile = Profile(36, tuple(range(1,37)), 0, 1, 1, 'THEORY_ONLY_QUANTIZATION')
    graph = tuple(ScoredEdge(Edge(t,t+1),1.01,0.0) for t in range(1,37))
    coarse = solve(profile,graph,budget_seconds=36.36,shared_seconds=0,
                   quantum_seconds=0.25,paths_per_state=1,maximum_final_paths=1)
    fine = solve(profile,graph,budget_seconds=36.36,shared_seconds=0,
                 quantum_seconds=0.01,paths_per_state=1,maximum_final_paths=1)
    assert not coarse['proposals'] and len(fine['proposals']) == 1
    checks.append(dict(id='CONSERVATIVE_COST_ROUNDING_HAS_COVERAGE_LOSS',verified=True,
        synthetic_unrounded_seconds=36.36,coarse_quantum=0.25,
        coarse_charged_predicted_seconds=36*cost_units(1.01,0.25)*0.25,
        coarse_no_proposal=True,fine_quantum=0.01,fine_proposal_exists=True,
        all_36_step_rounding_padding_upper_bound_seconds=9.0,
        claim='Ceiling bounds predicted costs, not actual latency'))

    local_errors = {'P':(F(1),F(-1)),'Q':(F(3,5),F(3,5))}
    cancellation = {k:dict(local_sum_squares=float(sum(x*x for x in v)),
        final_state_error_squared=float(sum(v)**2)) for k,v in local_errors.items()}
    assert cancellation['P']['local_sum_squares'] > cancellation['Q']['local_sum_squares']
    assert cancellation['P']['final_state_error_squared'] < cancellation['Q']['final_state_error_squared']
    checks.append(dict(id='ADDITIVE_LOCAL_MSE_CAN_REVERSE_ENDPOINT_RANKING',verified=True,
        one_dimensional_additive_sampler_example=cancellation,
        observation='Cross-step directions alone reverse ranking even without off-policy state drift'))

    # Illustrative two-anchor extrapolator, explicitly not a WC formula claim.
    source,target=4,5
    predictions={older:F(source*source)+F(target-source,source-older)*(source*source-older*older)
                 for older in (3,1)}
    assert predictions[3] == 23 and predictions[1] == 21
    checks.append(dict(id='LATEST_BOUNDARY_IS_NOT_SUFFICIENT_FOR_TWO_ANCHOR_READOUT',verified=True,
        hypothetical_extrapolator='r_s+(t-s)/(s-p)*(r_s-r_p), with r_j=j^2',
        latest_source=4,target=5,prediction_older3=23,prediction_older1=21,
        not_claimed_to_be_actual_WC_operator=True))

    losses={'S1_C':0.10,'S1_A':0.09,'S2_C':0.11,'S2_A':0.01}
    sequential=losses['S1_A'];joint=min(losses.values())
    assert sequential > joint
    checks.append(dict(id='JOINT_DOMAIN_CAN_HAVE_VALUE',verified=True,
        all_four_abstract_choices_assumed_budget_feasible=True,synthetic_loss_table=losses,
        D_then_A_from_C_loss=sequential,joint_optimum_loss=joint,
        universal_joint_advantage_or_finite_query_guarantee=False))

    # Exact simple-prefix optimality under deliberately restrictive assumptions.
    benefits=(8,4,2,1)
    pairs=[(benefits[i]+benefits[j],(i+1,j+1)) for i in range(4) for j in range(i+1,4)]
    optimum=max(pairs)
    assert optimum==(12,(1,2))
    checks.append(dict(id='FRONT_DENSE_CAN_BE_EXACTLY_OPTIMAL_IN_A_VALID_SPECIAL_CASE',verified=True,
        independent_refresh_benefits=list(benefits),equal_cost_refresh_budget=2,
        optimal_positions=list(optimum[1]),assumptions=['additive independent benefits','nonincreasing position benefit','equal costs','chosen prefix legal'],
        empirical_WC_or_H1_explanation_proven=False))

    # Existing recipe's pointwise two-control quality guard is stronger than
    # beating either single control's average. Keep its real current semantics.
    members=(('p1',0),('p2',0))
    records=[]
    for policy,loss in [('C',(0.0,0.1)),('A',(0.1,0.0))]:
        for member,value in zip(members,loss):
            records.append(dict(fingerprint=policy,prompt=member[0],seed=member[1],
                status='COMPLETE',split='CAL_SELECT',timing_protocol='THEORY',
                profile_identity='THEORY',LPIPS=value,measured_seconds=1.,
                endpoint_basis='NATURAL_FULL_TRAJECTORY_ALL_REGISTERED_FRAMES_LPIPS'))
    guarded=choose_observed(records,members=members,candidate_fingerprints=('C','A'),
        budget_seconds=2.,timing_protocol='THEORY',profile_identity='THEORY',
        split='CAL_SELECT',loss_ceiling={'p1':0.01,'p2':0.01})
    assert guarded['selected'] is None
    checks.append(dict(id='POINTWISE_CONTROL_TAIL_GUARD_NEED_NOT_ADMIT_A_BASELINE',verified=True,
        C_losses=[0.,0.1],A_losses=[0.1,0.],both_control_mean_losses=0.05,
        pointwise_min_plus_tolerance=0.01,all_times_feasible=True,
        actual_prototype_status=guarded['status'],
        implication='Do not infer unconditional baseline dominance or a time-only infeasibility from this status'))

    n,K,delta=2,4,0.05
    epsilon=math.sqrt(math.log(2*K/delta)/(2*n))
    assert epsilon>1
    checks.append(dict(id='TWO_PROMPT_SELECTION_NOT_A_STRONG_GENERALIZATION_CERTIFICATE',verified=True,
        independent_prompt_clusters=n,frozen_finalists_and_controls=K,delta=delta,
        hypothetical_loss_bound_assumption='L in [0,1] solely for illustration; actual raw LPIPS not assumed bounded by1',
        Hoeffding_union_bound_epsilon=epsilon,bound_is_vacuous=True,
        empirical_generalization_result=False))

    config_ref='configs/wc_policy_interval_assets_full1624_r1_20261020.json'
    cfg=json.loads((ROOT/config_ref).read_text());pr=cfg['profile']
    profile=Profile(pr['horizon'],tuple(pr['protected_dense']),pr['max_source_age'],
        pr['min_C_anchors'],pr['min_A_anchors'],'THEORY_STRUCTURAL_COUNT_ONLY',tuple(pr['alpha_candidates']))
    edges=enumerate_edges(profile);ways={profile.horizon+1:1};by_start={}
    for edge in edges:by_start.setdefault(edge.start,[]).append(edge)
    for start in range(profile.horizon,0,-1):ways[start]=sum(ways[e.end] for e in by_start[start])
    # Seven mandatory first D updates satisfy the adapter's anchor requirement
    # before every optional reuse edge. Thus node path counting suffices here.
    cells=sum(range(1,29));assert cells==406 and len(edges)==63372
    checks.append(dict(id='REGISTERED_DOMAIN_STRUCTURAL_COUNTS',verified=True,
        registered_config_ref=config_ref,registered_config_sha256=sha(ROOT/config_ref),
        source_time_cells_per_CAL=cells,formal_four_CAL_cells=4*cells,
        structural_interval_readout_edges=len(edges),complete_structural_paths=str(ways[1]),
        history_basis=pr['source_history'],actual_runtime_or_GPU_acceptance=False))

    audited=[
        'src/wcomr/policy_generator_r1/budgeted_planner.py',
        'src/wcomr/policy_generator_r1/interval_grammar.py',
        'src/wcomr/policy_generator_r1/proposal_tables.py',
        'src/wcomr/policy_generator_r1/search_protocol.py',
        'src/wcomr/policy_interval_assets_sampling_r1.py',
        'src/wcomr/policy_interval_readout_r1.py',
        'plans/cara_policy_generator_20261020/generator_recipe_r1.json',config_ref]
    text=(ROOT/'src/wcomr/policy_interval_assets_sampling_r1.py').read_text()
    assert "older=self.bank[s-1][b]" in text and 'source_anchor_steps=[source_step-1,source_step]' in text
    result=dict(schema_version=1,status='SYNTHETIC_THEORY_CHECKS_AND_SOURCE_AUDIT_NOT_MODEL_EVIDENCE',
        checks=checks,checks_verified=len(checks),all_checks_verified=all(x['verified'] for x in checks),
        source_bindings={name:dict(sha256=sha(ROOT/name),bytes=(ROOT/name).stat().st_size) for name in audited},
        scope='Algebra, finite grammar and counterexamples; no actual trajectory, video, price or quality measurements',
        frozen_recipe_modified=False,collection_config_modified=False,model_loaded=False,
        server_SSH_calls=0,GPU_submissions=0,ledger_written=False,
        production_CPU_accepted=False,GPU_dispatch_ready=False)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(output=str(args.output),checks_verified=len(checks),
        structural_edges=len(edges),structural_paths=str(ways[1]),GPU_submissions=0)))


if __name__=='__main__':
    main()
