"""Reconstruct the accepted full60 curve from captured receipts, on CPU only.

Does not import the production summarizer, contact SSH, run a model, or write
the GPU ledger. Remote raw-file and tensor controls remain separately reported.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SOURCE = '361ea5c9372332299f7ca29dbffe0ab942274d0f'
METHODS = ('NATIVE', 'WC', 'RA', 'A_NO_P', 'P_OFF', 'H1_LOW',
           'H1_MID', 'H1_HIGH', 'FIXED_A', 'FIXED_PLAIN')
SCENES = ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199',
          'misc_13398218_3840_2160_60fps',
          'av_51b45829-502e-4143-9c32-c026bd6ab191')
LAMBDAS = dict(zip(METHODS[5:8], (131.28658774523498,
                              525.1463509809399, 2100.5854039237597)))
MASK_A = ['D'] * 24 + ['A'] * 5 + ['C', 'D'] + ['C'] * 4 + ['D']
MASK_C = ['C' if a == 'A' else a for a in MASK_A]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)


def identity(a, b):
    return (a['final_latent_sha256'] == b['final_latent_sha256']
            and a['decoded_video']['RGB_sha256'] == b['decoded_video']['RGB_sha256']
            and a['actions'] == b['actions'])


def analyze(x):
    require(x['source_revision'] == SOURCE and all(x['payload_verified'].values())
            and len(x['payload_verified']) == 711, 'Immutable full711 source required')
    require(x['supervisor']['child_exit_code'] == 0 and x['post_exit']['exit_code'] == 0,
            'Both original GPU and post must have ended successfully')
    require(all(not p['exists'] for p in x['original_processes'].values())
            and x['kernel_lock_free'], 'Original handles and kernel lock must be released')
    require(x['production_CPU']['status'] ==
            'H1_COST_CURVE_FULL60_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU',
            'Original production CPU acceptance required')
    f = x['final']; rows = f['rows']
    require(f['source_revision'] == SOURCE and len(rows) == 60,
            'Original complete60 source and denominator required')
    require(f['accepted_paths'] == 60 and f['accepted_scientific_paths'] == 40
            and f['rejected_paths'] == 0 and f['scored_scientific_paths'] == 40,
            'All accepted40 scores required for this specific completed card')
    expected = []
    for repeat in (1, 2):
        for m in METHODS if repeat == 1 else METHODS[::-1]:
            expected.append((f'warm_{repeat}_{m}', SCENES[0], m, 'WARMUP', repeat))
    for i, scene in enumerate(SCENES):
        for m in METHODS if i % 2 == 0 else METHODS[::-1]:
            expected.append((f'timed_{i}_{m}', scene, m, 'TIMED', 1))
    require([(r['id'], r['scene'], r['method'], r['section'], r['round'])
             for r in rows] == expected, 'Registered order and complete input matrix differ')
    formal = {(r['scene'], r['method']): r for r in rows if r['section'] == 'TIMED'}
    for r in rows:
        diagnostic = r['section'] == 'WARMUP' and r['method'] in ('H1_MID', 'FIXED_A')
        require(r['status'] == 'COMPLETE' and r['endpoint_audit'] == 'PASS'
                and r['guided_pairs'] == 36 and r['solver_steps'] == 36,
                'Incomplete terminal, full36, or artifact audit')
        require(r['in_timing_guided_copies'] == (36 if diagnostic else 0)
                and r['in_timing_hashes'] == 0 and r['research_checkpoints'] == 0,
                'Formal timing includes removable research instrumentation')
        require(math.isfinite(r['core_seconds']) and r['core_seconds'] > 0
                and r['write_deferred_after_main_timer'], 'Finite actual main time required')
        require(r['decoded_video']['frames'] == 93, 'Incomplete decoded video')
        if r['method'] == 'NATIVE':
            require(r['actions'] is None, 'Native must not be assigned cache actions')
        else:
            require(len(r['actions']) == 36, 'Complete actual CFG actions required')
        if r['method'].startswith('H1_'):
            require(r['curve_lambda'] == LAMBDAS[r['method']], 'Unregistered lambda')
        if r['section'] == 'TIMED':
            q = r['LPIPS']; values = q['frame_distances']
            require(q['frames'] == 93 and len(values) == 93
                    and all(math.isfinite(v) and v >= 0 for v in values),
                    'All93 finite full-frame scores required')
            require(close(math.fsum(values) / 93, q['mean_LPIPS']),
                    'Stored LPIPS mean differs from all93 reconstruction')
            native = formal[(r['scene'], 'NATIVE')]
            require(q['candidate_sha256'] == r['video_artifact']['sha256']
                    and q['reference_sha256'] == native['video_artifact']['sha256'],
                    'Wrong candidate or same-input Native reference')
        if r['method'].startswith(('H1_', 'FIXED_')):
            require(len(r['source_history']) == 36 and r['online_teacher_calls'] == 0,
                    'All36 source records and no online teacher required')
            for h in r['source_history']:
                require(h['teacher_calls'] == 0
                        and not h['P_updates_true_D_or_zero_risk_RA_anchor'],
                        'Teacher or false Dense source mutation')
                require(h['action'] == 'DD' or h['true_D_before'] == h['true_D_after'],
                        'Approximation mutated true-D history')
    for scene in SCENES:
        require(identity(formal[(scene, 'H1_MID')], formal[(scene, 'FIXED_A')]),
                'MID and fixed-A endpoint/action/RGB control failed')
        require(identity(formal[(scene, 'H1_LOW')], formal[(scene, 'FIXED_PLAIN')]),
                'Observed low/plain identity is not supported by hashes')
        for m, plan in [('H1_MID', MASK_A), ('FIXED_A', MASK_A),
                        ('H1_LOW', MASK_C), ('FIXED_PLAIN', MASK_C)]:
            r = formal[(scene, m)]
            actual = [h['A_readout']['readout_action'] for h in r['source_history']]
            require(actual == plan, 'Actual semantic C/A/D sequence differs')
    for m in METHODS:
        warm = [r for r in rows if r['section'] == 'WARMUP' and r['method'] == m]
        require(len(warm) == 2 and identity(*warm), 'Forward/reverse warm repeat differs')
    require(len(f['warm_guided_controls']) == 2
            and all(c['status'] == 'PASS_ALL36_MID_FIXED_A_GUIDED_EQUAL'
                    and c['outputs_per_arm'] == 36 for c in f['warm_guided_controls']),
            'Remote full144 guided tensor equality proof missing')
    methods = []
    for m in METHODS:
        rr = [formal[(s, m)] for s in SCENES]
        sec = mean(r['core_seconds'] for r in rr)
        q = mean(r['LPIPS']['mean_LPIPS'] for r in rr)
        server = next(t for t in f['methods'] if t['method'] == m)
        require(close(sec, server['complete_four_scene_mean_seconds'])
                and close(q, server['complete_four_scene_mean_LPIPS']),
                'Server aggregate differs from independent prompt reconstruction')
        methods.append(dict(method=m, mean_main_seconds=sec, mean_LPIPS=q,
            Native_over_method=sum(formal[(s, 'NATIVE')]['core_seconds'] for s in SCENES)
            / sum(r['core_seconds'] for r in rr),
            per_scene=[dict(scene=r['scene'], seconds=r['core_seconds'],
                LPIPS=r['LPIPS']['mean_LPIPS'], counts=r.get('counts')) for r in rr]))
    contrasts = []
    for candidate, base in [('FIXED_A', 'FIXED_PLAIN'), ('H1_MID', 'FIXED_A'),
                            ('H1_HIGH', 'H1_MID'), ('A_NO_P', 'WC'),
                            ('A_NO_P', 'RA'), ('P_OFF', 'A_NO_P')]:
        qq = []
        for s in SCENES:
            a, b = formal[(s, candidate)], formal[(s, base)]
            qa, qb = a['LPIPS']['mean_LPIPS'], b['LPIPS']['mean_LPIPS']
            qq.append(dict(scene=s, candidate_LPIPS=qa, baseline_LPIPS=qb,
                LPIPS_change_percent=100 * (qa / qb - 1),
                seconds_added=a['core_seconds'] - b['core_seconds'],
                better_frames=sum(u < v for u, v in zip(a['LPIPS']['frame_distances'],
                                                        b['LPIPS']['frame_distances'])),
                worse_frames=sum(u > v for u, v in zip(a['LPIPS']['frame_distances'],
                                                       b['LPIPS']['frame_distances']))))
        ma, mb = (next(m for m in methods if m['method'] == n) for n in (candidate, base))
        contrasts.append(dict(candidate=candidate, baseline=base, per_scene=qq,
            improved_scenes=sum(q['candidate_LPIPS'] < q['baseline_LPIPS'] for q in qq),
            LPIPS_change_percent_of_scene_means=100 * (ma['mean_LPIPS'] / mb['mean_LPIPS'] - 1),
            seconds_added=ma['mean_main_seconds'] - mb['mean_main_seconds']))
    bill = x['supervisor']['wall_seconds'] / 3600
    require(close(x['ledger']['used_gpu_hours'],
                  x['supervisor']['budget_before']['used_gpu_hours'] + bill),
            'Ledger settled cost differs from original supervisor wall')
    return dict(status='FULL60_RECEIPT_AND_ALL40_FULL93_AGGREGATES_INDEPENDENTLY_ACCEPTED',
        source_revision=SOURCE, paths=60, scored_formal_videos=40, scored_formal_frames=3720,
        methods=methods, contrasts=contrasts, actual_GPUh=bill,
        used_GPUh=x['ledger']['used_gpu_hours'], cap_GPUh=x['ledger']['cap_gpu_hours'],
        remaining_GPUh=x['ledger']['cap_gpu_hours'] - x['ledger']['used_gpu_hours'],
        original_processes_ended_and_lock_released=True,
        remote_full144_guided_tensor_equality_proof_accepted=True,
        local_analysis_does_not_reload_remote_tensor_pixels=True,
        one_formal_time_per_method_scene_not_repeated_speed=True,
        four_exposed_CAL_seed0_not_new_confirmation=True,
        GPU_submissions=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source = ROOT / args.input; output = ROOT / args.output
    require(not output.exists(), 'Preserve existing acceptance receipt')
    stored = source.read_bytes()
    raw = gzip.decompress(stored) if source.suffix == '.gz' else stored
    result = analyze(json.loads(raw))
    result.update(input_ref=args.input, input_sha256=hashlib.sha256(raw).hexdigest(),
                  stored_input_sha256=hashlib.sha256(stored).hexdigest())
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('methods', 'contrasts')}))


if __name__ == '__main__':
    main()
