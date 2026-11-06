"""Reconstruct the saved B endpoint diagnostic from one immutable capture.

Only local JSON is read. No CUDA, SSH, model execution, or budget writes.
Keep the plain-C versus original parent-A distinction in the acceptance proof.
"""
import argparse
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '988ace1834af14c4ed535ed7b025c9619fec948e'
LABELS = {'PARENT_PI0', 'C_REPLAY', 'DENSE_VELOCITY', 'L2_VELOCITY'}


def analyze(r):
    assert r['source_revision'] == SOURCE and r['payload_files'] == 730
    assert len(r['payload_verified']) == 730 and all(r['payload_verified'].values())
    assert all(not p['exists'] for p in r['original_processes'].values())
    assert r['kernel_lock_free'] and not r['compute_apps']
    assert 'GPU-cebf7119-cf03-23b9-e192-cd196332b704' in r['GPU']
    sup, runner, final = r['supervisor'], r['runner'], r['final']
    assert sup['child_exit_code'] == r['post_exit']['exit_code'] == 0
    assert sup['pid'] == r['launch']['supervisor_pid'] == 710803
    assert sup['child_pid'] == runner['pid'] == 710917
    assert r['launch']['post_watcher_pid'] == 710804
    assert sup['source_revision'] == runner['source_revision'] == final['source_revision'] == SOURCE
    assert sup['runner_sha256'] == r['runner_sha256']
    assert final['status'] == 'B_SAVED_VELOCITY_ALL4_PARENTS12_SUFFIXES16_VIDEOS_AUDITED_ALL93_SCORED'
    assert runner['status'] == 'BLOCK_SAVED_VELOCITY_ALL4_PARENTS12_SUFFIXES16_OUTPUTS_GPU_COMPLETE_CPU_PENDING'
    assert final['scope_counts']['pairs'] == runner['scope_counts']['pairs'] == 312
    assert final['scope_counts']['CFG_calls'] == 624
    assert final['scope_counts']['teacher_pairs'] == final['scope_counts']['B_executor_pairs'] == 0
    assert final['scope_counts']['loads'] == 1
    assert final['scored_videos'] == len(final['outputs']) == 16
    assert final['GPU_submissions'] == 0 and not final['ledger_written'] and not final['CUDA_initialized']
    assert final['budget_before_sha256'] == final['budget_after_sha256'] == r['ledger_sha256']
    assert final['instrumented_time_not_clean_speed'] and final['not_actual_B_refresh_or_closed_loop']
    assert len(runner['runs']) == len(final['parents']) == 4
    assert [p['point']['chosen']['step'] for p in runner['runs']] == [21, 27, 15, 29]
    assert [p['point']['source'] for p in runner['runs']] == ['P', 'D', 'P', 'D']
    states = []
    for i, parent in enumerate(runner['runs']):
        n = parent['point']['chosen']['step']
        assert parent['status'] == 'COMPLETE' and len(parent['guided_sha256']) == len(parent['actions']) == 36
        assert parent['original_parent_all36_guided_equal'] and parent['original_parent_final_actions_equal']
        assert parent['actual_pair_computations'] == 36 + 3 * (37 - n)
        event = parent['event']; branches = {b['label']: b for b in event['branches']}
        assert set(branches) == LABELS - {'PARENT_PI0'}
        assert len({b['first_C_cache_state_sha256'] for b in branches.values()}) == 1
        assert len({b['first_C_velocity_sha256'] for b in branches.values()}) == 1
        assert len(event['serial_restores']) == 6
        assert event['actual_teacher_calls'] == event['actual_B_executor_calls'] == 0
        assert event['first_physical_action'] == 'CC'
        assert event['only_first_returned_velocity_changed'] and event['offline_saved_vectors_not_new_D_or_P_anchor']
        outputs = {o['label']: o for o in final['outputs'] if o['index'] == i}
        assert set(outputs) == LABELS
        for label, out in outputs.items():
            assert out['status'] == 'COMPLETE' and out['scene'] == parent['scene'] and out['step'] == n
            video, score = out['video'], out['LPIPS']
            assert video['frames'] == score['frames'] == len(score['frame_distances']) == 93
            assert len(score['pts']) == 93 and all(math.isfinite(x) for x in score['frame_distances'])
            assert abs(mean(score['frame_distances']) - score['mean_LPIPS']) < 1e-12
            assert score['candidate_sha256'] == video['artifact']['sha256']
            assert score['reference_sha256'] == outputs['C_REPLAY']['LPIPS']['reference_sha256']
            assert score['pts'] == outputs['C_REPLAY']['LPIPS']['pts']
            if label == 'PARENT_PI0':
                continue
            b = branches[label]
            assert b['first_readout'] == b['readout_actions'][0] == 'C' and b['actions'][0] == 'CC'
            assert len(b['guided_sha256']) == len(b['actions']) == len(b['source_policy_tail']) == 37 - n
            first = b['source_policy_tail'][0]
            assert first['A_readout']['shared_alpha'] == 0 and first['A_readout']['readout_action'] == 'C'
            assert first['true_D_before'] == first['true_D_after']
            assert all(not h['source_policy']['decision']['reason'].startswith('MATH_EVENT_SUFFIX_FIRST:')
                       for h in b['source_policy_tail'][1:])
        replay = branches['C_REPLAY']
        assert replay['first_returned_velocity_sha256'] == replay['first_C_velocity_sha256']
        record = [h for h in parent['A_history'] if h['step'] == n]
        assert len(record) == 1
        record = record[0]
        check = dict(guided=replay['guided_sha256'] == parent['guided_sha256'][n - 1:],
                     final_latent=replay['final_latent_sha256'] == parent['final_latent_sha256'],
                     physical_actions=replay['actions'] == parent['actions'][n - 1:],
                     decoded_RGB=outputs['C_REPLAY']['video']['RGB_sha256'] == outputs['PARENT_PI0']['video']['RGB_sha256'])
        assert check['physical_actions']
        if record['readout_action'] == 'C':
            assert record['shared_alpha'] == 0 and all(check.values())
            boundary = 'PARENT_C_FULL_REPLAY_PARITY_PASS'
        else:
            assert record['readout_action'] == 'A' and record['shared_alpha'] == .5
            assert not check['guided'] and not check['final_latent'] and not check['decoded_RGB']
            boundary = 'ORIGINAL_PARENT_A_VERSUS_FORCED_FIRST_C_NONPARITY_RETAINED'
        metrics = {k: o['LPIPS']['mean_LPIPS'] for k, o in outputs.items()}
        diffs = {}
        for candidate, baseline in [('DENSE_VELOCITY', 'C_REPLAY'), ('L2_VELOCITY', 'C_REPLAY'),
                                    ('L2_VELOCITY', 'DENSE_VELOCITY')]:
            left, right = outputs[candidate]['LPIPS']['frame_distances'], outputs[baseline]['LPIPS']['frame_distances']
            diffs[candidate + '_vs_' + baseline] = dict(
                LPIPS_change_percent=100 * (metrics[candidate] / metrics[baseline] - 1),
                improved_frames=sum(a < b for a, b in zip(left, right)),
                worse_frames=sum(a > b for a, b in zip(left, right)),
                equal_frames=sum(a == b for a, b in zip(left, right)))
        states.append(dict(index=i, scene=parent['scene'], step=n, source=parent['point']['source'],
                           parent_readout=record['readout_action'], parent_alpha=record['shared_alpha'],
                           additional_parent_parity=check, parent_boundary=boundary,
                           mean_LPIPS=metrics, comparisons=diffs))
    assert sum(p['actual_pair_computations'] for p in runner['runs']) == 312
    averages = {k: mean(s['mean_LPIPS'][k] for s in states) for k in LABELS}
    comparisons = []
    for recorded in final['comparisons']:
        a, b = recorded['candidate'], recorded['baseline']
        assert recorded['denominator'] == recorded['scored_states'] == 4
        assert abs(recorded['complete_four_state_equal_candidate_LPIPS'] - averages[a]) < 1e-12
        assert abs(recorded['complete_four_state_equal_baseline_LPIPS'] - averages[b]) < 1e-12
        comparisons.append(dict(candidate=a, baseline=b, four_state_equal_LPIPS_change_percent=100 * (averages[a] / averages[b] - 1),
                                improved_states=sum(s['mean_LPIPS'][a] < s['mean_LPIPS'][b] for s in states), denominator=4))
    actual = sup['wall_seconds'] / 3600
    ledger = r['ledger']; before, after = sup['budget_before'], sup['budget_after']
    assert abs(after['used_gpu_hours'] - before['used_gpu_hours'] - actual) < 1e-10
    assert ledger == after and 'wc_block_saved_velocity_inflight' not in ledger
    assert ledger['gpu_jobs_launched'] == before['gpu_jobs_launched'] + 1
    return dict(status='REGISTERED_THREE_C_STATE_ENDPOINT_DIAGNOSTIC_ACCEPTED_PARENT_READOUT_BOUNDARY_RETAINED',
                source_revision=SOURCE, payload_files=730, registered_scope_accepted=True,
                unconditional_parent_replay_parity_pass=False, parent_C_full_replay_parity_points=2,
                parent_A_first_C_nonparity_points=2, parent_A_difference_retained=True,
                states=states, four_state_equal_mean_LPIPS=averages, comparisons=comparisons,
                independent_videos_not_claimed=4, distinct_scenes=2, all_16_outputs_full93_scored=True,
                actual_GPUh=actual, cumulative_settled_GPUh=ledger['used_gpu_hours'],
                cumulative_cap_GPUh=ledger['cap_gpu_hours'], remaining_GPUh=ledger['cap_gpu_hours']-ledger['used_gpu_hours'],
                GPU_end_unix=sup['ended_unix'], CPU_post_end_unix=r['post_exit']['ended_unix'],
                CPU_wall_seconds=final['CPU_wall_seconds'], all_original_handles_ended=True,
                no_clean_speed_or_actual_B_refresh_claim=True, new_GPU_submissions=0,
                new_model_or_teacher_calls=0, server_contacts_by_analysis=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', default='reports/wc_block_saved_velocity_full312_collection_20261014_1745.json.gz')
    parser.add_argument('--output', default='reports/wc_block_saved_velocity_full312_independent_acceptance_20261014.json')
    args = parser.parse_args()
    path, dest = ROOT / args.capture, ROOT / args.output
    assert not dest.exists(), 'Preserve existing acceptance; use a fresh output'
    stored = path.read_bytes(); raw = gzip.decompress(stored) if path.suffix == '.gz' else stored
    r = json.loads(raw); result = analyze(r)
    controls = []
    for kind in ('wrong_source', 'missing_frame', 'mean_tamper', 'different_first_C_cache'):
        changed = copy.deepcopy(r)
        if kind == 'wrong_source': changed['source_revision'] = 'wrong'
        elif kind == 'missing_frame': changed['final']['outputs'][0]['LPIPS']['frame_distances'].pop()
        elif kind == 'mean_tamper': changed['final']['outputs'][0]['LPIPS']['mean_LPIPS'] += .01
        else: changed['runner']['runs'][0]['event']['branches'][0]['first_C_cache_state_sha256'] = 'wrong'
        try: analyze(changed)
        except AssertionError: controls.append(kind)
        else: raise AssertionError('Corrupted capture accepted: ' + kind)
    result.update(capture_ref=args.capture, capture_sha256=hashlib.sha256(stored).hexdigest(),
                  uncompressed_sha256=hashlib.sha256(raw).hexdigest(), negative_controls_refused=controls,
                  script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with dest.open('x') as handle: handle.write(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({k: result[k] for k in ('status','actual_GPUh','remaining_GPUh','comparisons')}))


if __name__ == '__main__':
    main()
