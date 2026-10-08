#!/usr/bin/env python3
"""Stdlib reconstruction of the terminal native receipts and reported geometry.

The bound server CPU audit reconstructs all 120 actual tensors. This additional
local audit preserves that provenance and recomputes scalar energy, scope,
repeat/state evidence and fees without importing Torch or running inference.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path

PREFIX = 'reports/wc_cfg_mechanism_confirmation_r1_terminal_20261009_'
MODES = ('CC', 'DC', 'CD', 'DD')
ORIGINS = ('S22', 'S23_after_CC', 'S23_after_DC', 'S23_after_CD', 'S23_after_DD')


def same(a, b):
    assert math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-12), (a, b)


def digest_json(value):
    h = hashlib.sha256()
    def add(x):
        if isinstance(x, dict):
            for key in sorted(x):
                h.update(str(key).encode()); add(x[key])
        elif isinstance(x, list):
            h.update(b'list')
            for item in x: add(item)
        elif x is None or type(x) in (int, float, str, bool):
            h.update(repr(x).encode())
        else:
            raise TypeError(type(x))
    add(value)
    return h.hexdigest()


def main():
    capture_path = Path(PREFIX + 'capture.json')
    capture = json.loads(capture_path.read_text())
    assert capture['status'] == 'TEACHER_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS'
    native = {}
    for key, entry in capture['files'].items():
        compressed = Path(entry['local_path']).read_bytes()
        assert hashlib.sha256(compressed).hexdigest() == entry['compressed_sha256']
        raw = gzip.decompress(compressed)
        assert len(raw) == entry['bytes'] and hashlib.sha256(raw).hexdigest() == entry['sha256']
        if key in ('runner', 'supervisor', 'CPU_receipt', 'CPU_score', 'budget', 'config'):
            native[key] = json.loads(raw)
    runner, sup, cpu, score, budget, config = [native[k] for k in (
        'runner', 'supervisor', 'CPU_receipt', 'CPU_score', 'budget', 'config')]
    assert sup['exit_code'] == cpu['exit_code'] == 0
    assert runner['source_revision'] == sup['source_revision'] == score['source_revision'] == capture['source_revision']
    assert cpu['score_sha256'] == capture['files']['CPU_score']['sha256']
    assert score['runner_sha256'] == capture['files']['runner']['sha256']
    assert score['budget'] == budget == sup['budget_after'] == capture['budget_settled']
    same(budget['used_gpu_hours'], sup['budget_before']['used_gpu_hours'] + sup['wall_seconds']/3600)
    assert budget['gpu_jobs_launched'] == sup['budget_before']['gpu_jobs_launched'] + 1
    assert not any('inflight' in key for key in budget) and budget['cap_gpu_hours'] == 50
    scope = {'full_parents':2, 'new_videos':2, 'actual_state_origins':5,
        'action_cells_per_origin':4, 'strict_repeats_per_cell':2,
        'local_CFG_velocity_pairs':40, 'net_calls_in_diagnostics':80,
        'full_counterfactual_suffixes':0, 'endpoint_labels':0}
    assert score['scope'] == capture['planned_scope'] == config['preregistration']['scope_counts'] == scope
    assert score['full_parent_parity'] and not score['CUDA_initialized']
    assert score['net_condition_witnesses_verified']==224 and score['solver_space_witnesses_verified']==76
    assert config['preregistration']['confirmation_request']['seed']==3
    assert score['old_seed2_video_is_not_a_seed3_control']
    assert (score['local_CFG_pairs'], score['raw_tensor_count'], score['strict_repeat_groups']) == (40,120,20)
    for key in ('endpoint_or_absolute_physics_quality_claim','formal_RV_labels','independent_CONF','clean_speed_measurement'):
        assert score[key] is False
    off, on = runner['teacher']['parents']
    for key in ('inputs','outputs','deep','banks','solver_outputs','net_measurements','solver_measurements','final_components',
                'final_solver_configuration','sample_return_sha256','final_latent_sha256',
                'flags_before','flags_after','pipeline'):
        assert off[key] == on[key], key
    assert len(off['inputs']) == 72 and len(off['solver_outputs']) == 36
    assert len(off['final_components']) == 1216 and off['artifact']['sha256'] == on['artifact']['sha256']
    assert len(score['videos']) == 2 and all(v['full93_decode'] for v in score['videos'])
    assert [o['label'] for o in on['origins']] == [o['label'] for o in score['origins']] == list(ORIGINS)
    tensor_hashes = 0; repeats = 0; summary = []
    for index, (origin, scored) in enumerate(zip(on['origins'], score['origins'])):
        assert origin['status'] == 'COMPLETE_LOCAL_ORIGIN' and len(origin['pairs']) == 8
        rows = origin['pairs']
        assert [r['label'] for r in rows] == [m+'_'+rep for m in MODES for rep in ('first','second')]
        for row in rows:
            assert row['status'] == 'COMPLETE_TWO_CALL_LOCAL_TEACHER_REQUIRES_INDEPENDENT_AUDIT' and row['parent_restored']
            assert row['origin_completed_updates'] == (22 if index == 0 else 23)
            assert len(row['net_measurements'])==len(row['post_denoise_measurements'])==2
            assert row['origin_measurement']['sampler_latent']['tree_sha256']==row['origin_components']['output']
            for witness,signature in zip(row['net_measurements'],row['inputs']):
                assert witness['x_B_C_T_H_W']['tree_sha256']==signature['kwargs']['x_B_C_T_H_W']
                assert witness['condition']['full_gt_frames']['tree_sha256']==signature['kwargs']['gt_frames']
                assert witness['condition']['condition_mask']['tree_sha256']==signature['kwargs']['condition_video_input_mask_B_C_T_H_W']
            assert len(row['origin_components']) == len(row['pair_end_components']) == 1216
            assert row['origin_fingerprint'] == digest_json(row['origin_components'])
            assert row['pair_end_fingerprint'] == digest_json(row['pair_end_components'])
            assert row['origin_components'] == rows[0]['origin_components'] and row['inputs'] == rows[0]['inputs']
            assert row['origin_solver_configuration'] == row['pair_end_solver_configuration']
            assert [e['actual_action'] for e in row['action_report']['events']] == list(row['mode'])
            assert row['deep'] == [26 if action == 'D' else 0 for action in row['mode']]
            artifact = row['artifact']
            assert artifact['space'] == 'POST_DENOISE_BEFORE_SOLVER'
            assert set(artifact['tensor_sha256']) == {'conditional','unconditional','guided'}
            assert all(shape == [1,16,24,54,96] for shape in artifact['shape'].values())
            tensor_hashes += len(artifact['tensor_sha256'])
        for mode in MODES:
            first, second = [r for r in rows if r['mode'] == mode]
            skip = {'label','wall_seconds','artifact','solver_outputs','solver_measurements','child_latent_sha256','solver_step_reused_measured_velocity_without_net_call'}
            assert {k:v for k,v in first.items() if k not in skip} == {k:v for k,v in second.items() if k not in skip}
            assert first['artifact']['tensor_sha256'] == second['artifact']['tensor_sha256']
            if index == 0:
                child = next(o for o in on['origins'] if o['label'] == 'S23_after_'+mode)
                assert first['solver_step_reused_measured_velocity_without_net_call']
                assert len(first['solver_measurements'])==1 and not second['solver_measurements']
                assert first['solver_measurements'][0]['raw_return_tree_sha256']==first['solver_outputs'][0]
                assert first['solver_measurements'][0]['next_sampler_latent']['tree_sha256']==first['child_latent_sha256']
                assert all(r['origin_components']['output'] == first['child_latent_sha256'] for r in child['pairs'])
            repeats += 1
        metrics = scored['metrics']; geo = metrics['CC_error_geometry']; cells = metrics['cells']
        assert metrics['guidance'] == 7 and metrics['ideal_branch_weights'] == [8,-7]
        assert metrics['shape_BCTHW'] == [1,16,24,54,96] and metrics['elements_per_branch'] == 16*24*54*96
        assert not metrics['CUDA_initialized'] and metrics['DD_zero_is_teacher_definition']
        a, b, dot = [geo[k] for k in ('unweighted_conditional_MSE','unweighted_unconditional_MSE','signed_branch_error_dot_mean')]
        same(geo['weighted_energy_sum'], 64*a+49*b)
        same(geo['signed_cross_term'], -112*dot)
        same(geo['ideal_float64_guided_MSE'], 64*a+49*b-112*dot)
        same(scored['independent_signed_energy'], geo['ideal_float64_guided_MSE'])
        if a and b: same(geo['branch_error_cosine'], dot/math.sqrt(a*b))
        else: assert geo['branch_error_cosine'] is None
        if geo['weighted_energy_sum']:
            same(geo['ideal_combined_to_independent_energy_ratio'], geo['ideal_float64_guided_MSE']/geo['weighted_energy_sum'])
        else: assert geo['ideal_combined_to_independent_energy_ratio'] is None
        ref = cells['CC']['guided_velocity_MSE_to_DD']
        assert cells['DD']['guided_velocity_MSE_to_DD'] == 0
        for mode in MODES:
            loss = cells[mode]['guided_velocity_MSE_to_DD']
            same(loss, scored['independent_guided_MSE'][mode])
            if ref: same(cells[mode]['relative_MSE_reduction_vs_CC_percent'], 100*(ref-loss)/ref)
            else: assert cells[mode]['relative_MSE_reduction_vs_CC_percent'] is None
        summary.append({'origin':origin['label'],'guided_MSE':{m:cells[m]['guided_velocity_MSE_to_DD'] for m in MODES},
            'relative_reduction_percent':{m:cells[m]['relative_MSE_reduction_vs_CC_percent'] for m in MODES},
            'CC_error_geometry':geo,'measured_branch_factorization':metrics['same_branch_output_factorization']})
    assert tensor_hashes == 120 and repeats == 20
    result = {'status':'TEACHER_TERMINAL_LOCAL_STDLIB_SCOPE_REPEAT_ENERGY_AND_FEE_RECONSTRUCTION_PASS',
        'capture_sha256':hashlib.sha256(capture_path.read_bytes()).hexdigest(),'source_revision':capture['source_revision'],
        'scope':scope,'tensor_hashes_verified':120,'strict_repeat_groups':20,'full_parent_parity':True,
        'actual_GPU_wall_seconds':sup['wall_seconds'],'settled_GPUh':budget['used_gpu_hours'],
        'remaining_GPUh':50-budget['used_gpu_hours'],'origins':summary,
        'actual_tensor_reconstruction_provenance':'bound server CPU scorer, native receipt and score bytes preserved',
        'net_condition_witnesses_verified':224,'solver_space_witnesses_verified':76,
        'local_actual_tensor_reconstruction':False,'endpoint_or_RV_or_CONF_claim':False,'GPU_submissions':0}
    output = Path(PREFIX + 'independent_CPU_audit.json')
    assert not output.exists(); output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
