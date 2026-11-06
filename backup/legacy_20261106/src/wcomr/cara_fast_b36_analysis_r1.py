"""Aggregate complete accepted B36 metadata; never score or select a policy."""
import copy
from pathlib import Path

from .cara_fast_b36_post_r1 import accept_scores
from .cara_fast_b36_terminal_r1 import bound_A, record
from .cara_fast_capture_r2 import file_sha
from .cara_fast_execution_r2 import require
from .cara_fast_spec_r1 import digest

ROOT = Path(__file__).resolve().parents[2]
CLOCKS = ('T_DD', 'T_request')
BASELINES = {'WC_FAST': 'WC', 'RA_FAST': 'RA', 'NATIVE_K': 'NATIVE_K'}
METRICS = (
    'Alex', 'Alex_frames', 'Alex_q95_higher', 'Alex_worst',
    'Alex_first_worst_frame_zero_based', 'MSE_video', 'PSNR_video_dB',
    'PSNR_is_infinite', 'SSIM', 'SSIM_frames', 'reference_temporal_L1',
    'reference_gradient_L1', 'candidate_gradient_energy',
    'reference_gradient_energy', 'gradient_energy_ratio', 'gradient_ratio_status',
)
MEAN_METRICS = ('Alex', 'SSIM', 'reference_temporal_L1', 'reference_gradient_L1')


def mean(values):
    return sum(values) / len(values)


def summarize(card, binding, collection, manifest, accepted):
    """Inputs have passed the original terminal and score boundary below."""
    physical = {row['slot']['id']: row for row in binding['A_collection']['rows'] + collection['rows']}
    repeats = [physical[slot['id']] for slot in card['physical_matrix'] if slot['section'] == 'B_REPEAT']
    rows = []
    for pair, score in zip(manifest['pairs'], accepted['rows']):
        candidate = pair['candidate']
        member, role = candidate['member'], candidate['role']
        formal = physical[candidate['slot_id']]
        samples = [formal] + [row for row in repeats
            if row['slot']['member'] == member and row['slot']['role'] == role]
        times = {clock: mean([row['result'][clock] for row in samples]) for clock in CLOCKS}
        rows.append(dict(member=member, role=role, concrete_role=candidate['concrete_role'],
            partition='FIT' if member in card['FIT'] else 'CHECK', score_id=score['id'],
            source_phase=candidate['source_phase'], reused_A_source=candidate['reused_from_A'],
            reused_A_score_id=score.get('reused_A_score_id'), formal_slot_id=candidate['slot_id'],
            formal_time={clock: formal['result'][clock] for clock in CLOCKS}, time_mean=times,
            timing_samples=[dict(slot_id=row['slot']['id'], phase=row['slot']['phase'],
                section=row['slot']['section'], **{clock: row['result'][clock] for clock in CLOCKS}) for row in samples],
            metrics={key: copy.deepcopy(score[key]) for key in METRICS},
            FIT_baseline_time_match=manifest['frozen_baseline_time_match'].get(BASELINES.get(role))))
    native = {row['member']: row for row in rows if row['role'] == 'NATIVE35'}
    for row in rows:
        row['speedup'] = {clock: native[row['member']]['time_mean'][clock] / row['time_mean'][clock]
                          for clock in CLOCKS}

    groups = {}
    for partition, members in [('ALL', [row['name'] for row in card['inputs']]),
                                ('FIT', card['FIT']), ('CHECK', card['CHECK'])]:
        native_means = {clock: mean([native[member]['time_mean'][clock] for member in members]) for clock in CLOCKS}
        summary = []
        for role in card['formal_roles']:
            selected = [row for row in rows if row['role'] == role and row['member'] in members]
            times = {clock: mean([row['time_mean'][clock] for row in selected]) for clock in CLOCKS}
            undefined = [row['member'] for row in selected if row['metrics']['gradient_energy_ratio'] is None]
            summary.append(dict(role=role, members=list(members), prompt_count=len(members),
                time_mean=times, speedup={clock: native_means[clock] / times[clock] for clock in CLOCKS},
                metrics={key: mean([row['metrics'][key] for row in selected]) for key in MEAN_METRICS},
                gradient_energy_ratio=None if undefined else mean([row['metrics']['gradient_energy_ratio'] for row in selected]),
                gradient_ratio_status='UNDEFINED_FOR_AT_LEAST_ONE_MEMBER' if undefined else 'FINITE',
                undefined_gradient_members=undefined,
                PSNR_per_member={row['member']: row['metrics']['PSNR_video_dB'] for row in selected},
                FIT_baseline_time_match=manifest['frozen_baseline_time_match'].get(BASELINES.get(role))))
        groups[partition] = summary

    sensitivity = []
    for role, family in BASELINES.items():
        selected = [row for row in rows if row['role'] == role and row['partition'] == 'FIT']
        require(all(row['source_phase'] == 'A' and native[row['member']]['source_phase'] == 'A'
                    for row in selected), 'FIT sensitivity requires the original A formal sources')
        per_member = [dict(member=row['member'], baseline_slot_id=row['formal_slot_id'],
            native_slot_id=native[row['member']]['formal_slot_id'],
            baseline_time=copy.deepcopy(row['formal_time']), native_time=copy.deepcopy(native[row['member']]['formal_time']),
            speedup={clock: native[row['member']]['formal_time'][clock] / row['formal_time'][clock] for clock in CLOCKS})
            for row in selected]
        baseline_time = {clock: mean([row['baseline_time'][clock] for row in per_member]) for clock in CLOCKS}
        native_time = {clock: mean([row['native_time'][clock] for row in per_member]) for clock in CLOCKS}
        sensitivity.append(dict(role=role, family=family, per_member=per_member,
            baseline_time_mean=baseline_time, native_time_mean=native_time,
            speedup={clock: native_time[clock] / baseline_time[clock] for clock in CLOCKS},
            FIT_baseline_time_match=manifest['frozen_baseline_time_match'][family]))

    return dict(per_member=rows, prompt_equal_summaries=groups, FIT_phase_A_only_sensitivity=sensitivity)


def analyze_complete(capture, card, settlement, manifest, manifest_file_sha256,
                     score_capture, accepted, *, cpu_validation=False):
    """Revalidate all original metadata before exposing any result aggregate."""
    registration = record(capture, 'registration')
    proof = record(capture, 'CPU_acceptance')
    dependencies = {**proof['critical_source_sha256'], **{name: registration['payload_sha256'][name]
        for name in ('src/wcomr/cara_fast_b36_post_r1.py', 'src/wcomr/cara_fast_b36_terminal_r1.py')}}
    require(all(file_sha(ROOT/name) == expected for name, expected in dependencies.items()),
            'Use the original admitted scientific validators and CPU-accepted source')
    require(score_capture['status'] == 'FAST_B36_SCORE_TERMINAL_CAPTURE', 'Original stopped B scorer required')
    result = record(score_capture, 'scores')
    validated = accept_scores(capture, card, settlement, manifest, manifest_file_sha256,
        result, score_capture['execution'], new_manifest=score_capture['files']['new_manifest'],
        new_scores=score_capture['files']['new_scores'])
    require(accepted == validated, 'Original accepted complete32 receipt differs')
    launch = record(capture, 'launch')
    source = launch['source_revision']
    fixture = result.get('CPU_METADATA_FIXTURE_ONLY_NO_METRIC_EXECUTION') is True or not (
        len(source) == 40 and all(character in '0123456789abcdef' for character in source))
    require(cpu_validation or not fixture, 'CPU metadata fixtures cannot produce a B36 scientific report')
    binding = bound_A(capture, card)
    summary = summarize(card, binding, record(capture, 'collection'), manifest, validated)
    return dict(schema='CARA_FAST_B36_COMPLETE_ANALYSIS_R1',
        status='CPU_METADATA_FIXTURE_ONLY' if cpu_validation else 'COMPLETE_ACCEPTED_B36_ANALYSIS',
        CPU_fixture_only=cpu_validation, run_id=launch['run_id'], launch_id=launch['launch_id'],
        source_revision=launch['source_revision'], host=launch['host'], gpu_uuid=launch['gpu_uuid'],
        scope_sha256=card['scope_sha256'], protocol_sha256=card['fidelity_protocol_sha256'],
        A_launch_id=binding['A_launch_id'], frozen_file_sha256=binding['frozen_file_sha256'],
        frozen_baselines={family: {key: copy.deepcopy(value[key]) for key in ('candidate', 'time_match', 'mismatch')}
                          for family, value in binding['frozen']['selected'].items()},
        evidence_digest=dict(terminal=digest(capture), settlement=digest(settlement),
            manifest_file=manifest_file_sha256, score_capture=digest(score_capture), accepted_scores=digest(accepted)),
        formal_logical_positions=32, nonself_pairs=28, native_self_checks=4,
        reused_A_sources=8, reused_A_metric_pairs=6, newly_scored_pairs=26,
        timing_rule=card['timing_analysis'], group_speedup_rule='Ratio of prompt-equal Native and role time means',
        PSNR_rule='Retain each original whole-video PSNR, including +inf; no pooled or finite-subset reduction',
        gradient_ratio_rule='Prompt-equal mean only when every member is defined; otherwise null with member identities',
        new_selection=False, new_veto_thresholds=False, independent_new_inputs=False,
        endpoint_competitive_claim=False, GPU_submissions=0, metrics_computed=False,
        authorizes_replay=False, **summary)
