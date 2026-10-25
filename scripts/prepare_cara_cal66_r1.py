#!/usr/bin/env python3
"""Compile the CAL66 design and quote from immutable accepted sources; no dispatch."""
import argparse
import copy
import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.policy_generator_r1.shared_exploration import base_dense, shared_dense, compile_dense

OLD = 'manifests/cara_shared_CAL106_scope_quote_r1_20261025.json'
ENERGY = 'reports/wc_scout_saved_assets_actual_CPU_r1_20261018.json'
HISTORY = 'reports/cara_history104_R2_terminal_20261024_2315.json'
OUT = 'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json'


def read(ref):
    return json.loads((ROOT / ref).read_text())


def sha(ref):
    return hashlib.sha256((ROOT / ref).read_bytes()).hexdigest()


def mask_audit(old, profile):
    source = read(ENERGY)['result']
    full = old['energy_scores']
    unweighted = source['X_S_schedule_candidates']['unweighted']['scene_equal_scores']
    # Recover g^2 from the saved component arrays, checking both input trajectories.
    priors = []
    for row in source['X_S_native_variations']:
        priors.append([0.] + [w/u for w, u in zip(row['gain_squared_weighted'][1:], row['unweighted'][1:])])
    assert all(math.isclose(x, y, rel_tol=1e-12, abs_tol=1e-15) for x, y in zip(*priors))
    result = []
    for n in (24, 25, 26):
        s = base_dense(n)
        generated = shared_dense(full, n)
        template = sorted((set(s) - {33}) | {next(t for t in range(8, 24) if t not in s)})
        masks = dict(full_energy=generated['dense'], propagation_prior_only=shared_dense(priors[0], n)['dense'],
                     unweighted_energy=shared_dense(unweighted, n)['dense'], simple_template=template)
        alias_groups = {}
        for name, mask in masks.items():
            alias_groups.setdefault(','.join(map(str, mask)), []).append(name)
        families = {}
        for family, mask in [('S', s), ('Shared', generated['dense'])]:
            all_a = compile_dense(profile, mask, correction=True)
            age3 = compile_dense(profile, mask, correction=True, age_cap=3)
            step_rows = [dict(step=t, D=t in mask, action_all=a, action_age3=b,
                              alpha_all=all_a['shared_alpha'][t-1], alpha_age3=age3['shared_alpha'][t-1],
                              source=all_a['source_before'][t-1],
                              reuse_age=None if a == 'D' else t-all_a['source_before'][t-1])
                         for t, (a, b) in enumerate(zip(all_a['actions'], age3['actions']), 1)]
            families[family] = dict(dense=list(mask), all_A_count=all_a['actions'].count('A'),
                                    age3_A_count=age3['actions'].count('A'), steps=step_rows,
                                    replaced_A_positions=[r['step'] for r in step_rows if r['action_all'] != r['action_age3']])
        result.append(dict(quota=n, families=families, masks=masks, mask_alias_groups=list(alias_groups.values())))
    assert result[1]['families']['Shared']['dense'] == sorted(set(base_dense(26)) - {33})
    assert result[0]['families']['Shared']['dense'] == sorted(set(base_dense(25)) - {33})
    return dict(status='CPU_STRUCTURE_NOT_ENDPOINT_EVIDENCE', source_ref=ENERGY, source_sha256=sha(ENERGY),
                prior_reconstructed_from_two_saved_component_arrays=True, rows=result,
                equivalence_scope='Frozen quotas24/25/26, current36-update setting only', GPU_submissions=0)


def bridge_refs(member):
    old = read(HISTORY)
    result = {}
    for role in ('S26_C', 'SHARED26_C'):
        key = 'CALIBRATION_' + role + '_0_1'
        request = old['requests'][key]
        assert request['slot']['member'] == member
        rgb = next((c['left_rgb'] if c['left'] == key else c['right_rgb']
                   for c in old['controls'] if key in (c['left'], c['right'])), None)
        result[role] = dict(capture_ref=HISTORY, capture_sha256=sha(HISTORY), slot_id=key,
                            policy_fingerprint=request['policy']['fingerprint'],
                            artifact_checks=old['artifact_checks'][key], RGB93=rgb,
                            original_video_decode_binding_required_before_production_CPU=rgb is None,
                            native_reference_must_be_verified_before_cross_batch_LPIPS=True)
    return result


def build():
    old = read(OLD)
    p = copy.deepcopy(old['profile'])
    p['protected_dense'], p['alpha_candidates'] = tuple(p['protected_dense']), tuple(p['alpha_candidates'])
    profile = Profile(**p)
    arms = {k: copy.deepcopy(old['roles'][k]) for k in ('NATIVE35', 'NATIVE26', 'NATIVE28')}
    aliases = {}
    for n in (24, 25):
        for suffix in ('C', 'A_PHASE'):
            key = f'S{n}_{suffix}'
            arms[key] = copy.deepcopy(old['roles'][key])
        arms[f'SHARED{n}_C'] = copy.deepcopy(old['roles'][f'SHARED{n}_C'])
        mask = old['generation'][str(n)]['dense']
        arms[f'SHARED{n}_A_PHASE_ALL'] = dict(kind='policy', requested_steps=35,
            policy=compile_dense(profile, mask, correction=True), correction_age_cap=None)
        arms[f'SHARED{n}_A_PHASE_AGE3'] = copy.deepcopy(old['roles'][f'SHARED{n}_A_PHASE'])
        aliases[f'SHARED{n}_A_PHASE_AGE3'] = f'SHARED{n}_A_PHASE'
    formal_roles = list(arms)
    # Historical roles remain exact, but are bridge controls, not formal CAL samples.
    for key in ('S26_C', 'SHARED26_C'):
        arms[key] = copy.deepcopy(old['roles'][key])
    members = old['CAL_FIT_members']
    matrix = []

    def add(section, role, member, repeat):
        matrix.append(dict(id=f'{section}_{role}_{members.index(member)}_{repeat}', section=section,
                           role=role, member=member, seed=0, repeat=repeat,
                           actual_updates=arms[role]['requested_steps'] + 1))

    warm = ['NATIVE35', 'NATIVE26', 'NATIVE28', 'S24_C', 'SHARED24_A_PHASE_ALL', 'SHARED24_A_PHASE_AGE3']
    timing = ['NATIVE35', 'SHARED24_A_PHASE_AGE3', 'SHARED25_A_PHASE_AGE3']
    for role in warm:
        add('WARM', role, members[0], 0)
    for i, member in enumerate(members):
        offset = (3*i) % len(formal_roles)
        order = formal_roles[offset:] + formal_roles[:offset]
        for role in order:
            add('QUALITY', role, member, 1)
        if i < 2:
            for role in reversed(order):
                if role in timing:
                    add('TIMING_REPEAT', role, member, 2)
    for role in ('S26_C', 'SHARED26_C'):
        add('HISTORICAL_BRIDGE', role, members[0], 0)
    assert len(matrix) == 66 and len(set(s['id'] for s in matrix)) == 66
    costs = read('reports/cara_cost112_complete_timing_thermal_analysis_20261025.json')
    measured = {r['role']: r['complete_request_mean_seconds'] for r in costs['descriptive_CAL_role_summary']}
    seconds = {k: measured.get(k, measured['PG_ALL_D']) for k in arms}
    generation = sum(seconds[s['role']] for s in matrix)/3600
    forecast = (generation + .15 + .35)*1.15
    audit = mask_audit(old, profile)
    bound_refs = [OLD, ENERGY, HISTORY, 'reports/cara_history104_R2_accepted_20261024_2315.json',
                  'reports/cara_shared_CAL106_combination_CPU_accepted_r3_20261025.json',
                  'reports/cara_cost112_complete_timing_thermal_analysis_20261025.json',
                  'plans/cara_policy_generator_20261020/CAL66_DESIGN_AND_DECISION_CONTRACT_R1_20261025.md',
                  'docs/discussions/CAL66_6PRO_REFERENCE_20261025/03_CPU_Mask_Derivation.json']
    return dict(status='CAL66_DESIGN_FROZEN_NO_PRODUCTION_ACCEPTANCE_NO_GPU_AUTHORITY',
        supersedes_proposal=OLD, source_bindings={r: sha(r) for r in bound_refs},
        profile=old['profile'], roles=arms, formal_roles=formal_roles, CAL_FIT_members=members,
        prior_role_aliases=aliases, schedules=[s for s in old['schedules'] if s['requested_steps'] in (26, 28, 35)],
        matrix=matrix, historical_bridges=bridge_refs(members[0]), mask_audit=audit,
        scope=dict(formal_roles=13, total_role_identities=15, CAL=4, seeds=[0], quality_paths=52,
                   timing_repeat_paths=6, warm_paths=6, historical_bridge_paths=2, total_paths=66,
                   guided_pairs=sum(s['actual_updates'] for s in matrix),
                   CFG_calls=2*sum(s['actual_updates'] for s in matrix), loads=1,
                   LPIPS_pairs=48, LPIPS_frames=4464, independent_quality_videos=52,
                   independent_quality_positions=156, SELECT_paths=0, DEV_paths=0, TEST_paths=0),
        quote=dict(basis='Accepted112 exact role means; every unmeasured role uses PG_ALL_D mean',
            arm_seconds=seconds, components=dict(generation_GPUh=generation, model_load_GPUh=.15, artifact_save_release_GPUh=.35),
            uncertainty_margin=.15, forecast_GPUh=forecast, proposed_limit_GPUh=8.,
            forecast_fits_proposed_limit=forecast<=8., limit_approved=False, cumulative_cap_GPUh=226,
            post_release_CPU=dict(GPU_held=False, cpus=2, memory_GiB=8, wall_limit_hours=6, vCPU_hours_upper=12,
                                  LPIPS_pairs=48, independent_quality_videos=52, independent_quality_positions=156,
                                  metrics=['MUSIQ','subject_consistency','motion_smoothness'],
                                  real_model_resources_and_throughput_CPU_pending=True)),
        contract=dict(original_alpha=old['contract']['original_alpha'], beta=1,
            final_absolute_seconds=257.7712338712067, final_relative_native=.8,
            final_estimand='max(prompt_equal_mean_T/257.7712338712067, prompt_equal_mean_T/(0.8*prompt_equal_mean_Native))',
            final_bootstrap=dict(unit='paired_prompt_cluster', repeats='average_within_prompt_first',
                                 resamples=20000, seed=20261025, one_sided_confidence=.95, quantile='higher'),
            CAL_bootstrap_is_descriptive_only=True, CAL_does_not_accept_final_deployment=True,
            warm_roles=warm, timing_repeat_roles=timing, repeat_members=members[:2],
            repeats_not_extra_quality_samples=True, no_time_or_quality_imputation=True,
            no_partial_tuning=True, no_interpolated_Native_quality=True, no_unregistered_steps=True,
            bridge_failure_blocks_historical_pooling_not_new_formal_identity=True,
            stronger_baseline_S26_A_preserved_as_history_not_current_formal_arm=True,
            old_CAL106_unchanged=True, no_GPU_authority=True),
        production_entry_CPU_accepted=False, combination_CPU_accepted=False,
        quality_models_CPU_accepted=False, GPU_dispatch_ready=False, GPU_submissions=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    card = build()
    with args.output.open('x') as f:
        json.dump(card, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps(dict(scope=card['scope'], quote=card['quote']['forecast_GPUh'], limit=8.)))


if __name__ == '__main__':
    main()
