import copy
import pytest
import torch
from wcomr.w1d import grouped_error
from wcomr.w1d_analysis import analyze


def receipt(zero=False):
    truth = torch.ones(1, 4, 4, 4, 4)
    official = truth.clone() if zero else truth + 1
    localized = truth.clone()
    localized[:, :, :, 2:, 2:] += 3
    residual = {'official': official, 'scalar': truth+.5, 'shrink': truth+2}
    velocity = {'official': official, 'scalar': localized, 'shrink': truth+2}
    scores = {mode: {'prewarp_residual': grouped_error(residual[mode], truth, 'residual'),
                     'postwarp_residual': grouped_error(residual[mode], truth, 'residual'),
                     'velocity': grouped_error(velocity[mode], truth, 'velocity'),
                     'reason': mode, 'history': {'anchor_steps': [0, 2]}} for mode in residual}
    records = [{'call': call, 'cache_counter': call+4, 'cfg_branch': (call-1)%2,
                'candidates': copy.deepcopy(scores), 'truth_tail_seconds': 0, 'diagnostic_seconds': 0}
               for call in range(1, 9)]
    off = {key: [] for key in ['guardrail_events', 'forward_output_sha256', 'trace', 'pipeline_events', 'decoder_calls', 'decoded_rgb']}
    off.update(outcome='ACCEPTED', block_counts={}, cache_end_sha256='x', sampling=None,
               video_sha256='v', flags_before={}, flags_after={}, shadow_records=[])
    on = copy.deepcopy(off); on['shadow_records'] = records
    cases = [{'name': str(i), 'status': 'PAIR_PARITY_PASS', 'off': copy.deepcopy(off),
              'on': copy.deepcopy(on), 'selection': {'calls': list(range(1, 9))},
              'coverage': 'FULL_FOUR_PAIR_SCREEN'} for i in range(8)]
    return {'status': 'W1D_CAL8_ATTEMPTED_ALL_PARITY_PASS', 'protocol': {'samples': [str(i) for i in range(8)]}, 'cases': cases}


def test_localized_error_and_ranking_reversal_are_not_global_improvement():
    result = analyze(receipt())
    groups = result['group_aggregate']['velocity']['spatial']
    assert [g['candidates']['scalar']['mean_sample_sse_ratio_to_official'] for g in groups] == [0, 0, 0, 9]
    assert [g['candidates']['scalar']['improved_samples'] for g in groups] == [8, 8, 8, 0]
    assert sum(g['mean_sample_official_error_share'] for g in groups) == pytest.approx(1)
    assert len([r for r in result['ranking_reversals'] if r['modes'] == ['official', 'scalar']]) == 64
    assert result['frozen_screen_status'] == 'NO_GAIN_CAL8_IN_SCOPE'


def test_partition_overlap_and_mismatched_coordinates_fail_closed():
    r = receipt()
    score = r['cases'][0]['on']['shadow_records'][0]['candidates']['scalar']['velocity']
    score['partitions']['spatial'][1]['bounds'] = copy.deepcopy(score['partitions']['spatial'][0]['bounds'])
    with pytest.raises(ValueError, match='Overlapping'):
        analyze(r)
    r = receipt()
    score = r['cases'][0]['on']['shadow_records'][0]['candidates']['scalar']['velocity']
    score['partitions']['time'][0]['elements'] += 1
    with pytest.raises(ValueError, match='element count'):
        analyze(r)


def test_partial_and_zero_official_errors_cannot_create_a_signal():
    r = receipt(zero=True); r['cases'] = r['cases'][:2]; r['status'] = 'GENERATING'
    result = analyze(r, partial=True)
    assert result['status'] == 'LIVE_PARTIAL_DESCRIPTIVE_NO_DECISION'
    assert result['frozen_screen_status'] == 'LIVE_PARTIAL_NO_DECISION'
    assert all(g['candidates']['scalar']['mean_sample_sse_ratio_to_official'] is None
               for g in result['group_aggregate']['velocity']['time'])
    with pytest.raises(AssertionError):
        analyze(r)
