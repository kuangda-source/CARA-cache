"""Read accepted local clocks; never infer missing loop-start timestamps or launch jobs."""
import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import statistics as st
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
CARDS = {
    'DEV128': ('cara_DEV128_A6000_terminal_20261027_0400.json',
               'cara_DEV128_A6000_accepted_20261027_0404.json',
               ('QUALITY', 'TIMING_REPEAT'), 'NATIVE35', 128, 120),
    'CAL66': ('cara_CAL66_A6000_terminal_20261026_0930.json',
              'cara_CAL66_A6000_terminal_accepted_20261026_0930.json',
              ('QUALITY',), 'NATIVE35', 66, 52),
    'H104': ('cara_history104_R2_terminal_20261024_2315.json',
             'cara_history104_R2_accepted_20261024_2315.json',
             ('CALIBRATION', 'VALIDATION'), 'NATIVE', 104, 80),
    'C112': ('cara_cost112_GPU_terminal_20261025_1115.json',
             'cara_cost112_GPU_accepted_20261025_1115.json',
             ('CALIBRATION', 'VALIDATION'), 'NATIVE', 112, 80),
}
FIELDS = ('core_seconds', 'guarded_pipeline_without_write_seconds',
          'method_install_seconds', 'video_write_seconds', 'method_cleanup_seconds',
          'full_request_seconds')
PIPE = 'cosmos_predict2/_src/predict2/inference/video2world.py'
PIPE_SHA = '59aa9e236a5e7e26490f5cfcb94ab95ce911d9c38eba61dd8aef7d067e458a95'


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def record(v, key):
    item = v['files'][key]
    raw = item['raw_utf8'].encode()
    assert hashlib.sha256(raw).hexdigest() == item['sha256']
    return json.loads(raw)


def replay(name):
    cap, acc, *_ = CARDS[name]
    v, a = read(ROOT / 'reports' / cap), read(ROOT / 'reports' / acc)
    assert a['capture_sha256'] == sha(ROOT / 'reports' / cap)
    if name == 'DEV128':
        from wcomr.policy_generator_r1.dev128_terminal import accept
        settlement = ROOT / a['central_settlement_ref']
        assert sha(settlement) == a['central_settlement_sha256']
        v['central_settlement'] = read(settlement)
    elif name == 'CAL66':
        from wc_two_card_cara_cal66_gpu_r1 import accept_terminal as accept
    elif name == 'H104':
        from wcomr.policy_generator_r1.historical_terminal import accept
    else:
        from wcomr.policy_generator_r1.cost112_terminal import accept
    result = accept(v)
    assert result['full_protocol_accepted']
    assert all(a[k] == value for k, value in result.items())
    return dict(original_acceptance_replayed=True, status=result['status'])


def audit_card(name):
    cap, acc, sections, baseline, total, formal = CARDS[name]
    cp, ap = ROOT / 'reports' / cap, ROOT / 'reports' / acc
    before = {str(p.relative_to(ROOT)): sha(p) for p in (cp, ap)}
    # Each worker has isolated module globals, including the accepted CAL66 SM86 adapter.
    accepted = json.loads(subprocess.check_output(
        [sys.executable, __file__, '--worker', name], cwd=ROOT, text=True))
    v, a = read(cp), read(ap)
    reg, runner = record(v, 'registration'), record(v, 'runner')
    for path in ('src/wcomr/clean_speed20_r1.py',
                 'src/wcomr/policy_generator_r1/production_sampling.py'):
        assert reg['payload_sha256'][path] == sha(ROOT / path)
    assert v['runtime_actual_sha256'][PIPE] == reg['runtime_source_sha256'][PIPE] == PIPE_SHA
    assert len(v['requests']) == total
    # Original request hashes bind result fields via the accepted runner receipt.
    batch = {r['slot']['id']: r for r in runner['batch']['rows']}
    inventory = collections.Counter()
    rows = []
    for identifier, request in v['requests'].items():
        slot, result = request['slot'], request['result']
        for k in result:
            if any(t in k.lower() for t in ('seconds', 'timestamp', 'started', 'ended')):
                inventory[k] += 1
        assert all(result[k] == batch[identifier]['result'][k] for k in FIELDS)
        if slot['section'] not in sections:
            continue
        assert not result['audit'] and result['clean_deployment_timing']
        assert result['in_timing_guided_copies'] == result['in_timing_hashes'] == 0
        assert result['status'] == 'COMPLETE'
        values = {k: result[k] for k in FIELDS}
        assert all(math.isfinite(x) and x >= 0 for x in values.values())
        core, guarded, full = (values[k] for k in
                              ('core_seconds', 'guarded_pipeline_without_write_seconds', 'full_request_seconds'))
        assert 0 < core <= guarded <= full
        assert math.isclose(full, math.fsum(values[k] for k in FIELDS if k not in
                                          ('core_seconds', 'full_request_seconds')), abs_tol=1e-8)
        rows.append(dict(id=identifier, role=slot['role'], member=slot['member'],
                         repeat=slot['repeat'], section=slot['section'], **values,
                         guarded_outside_core_seconds=guarded-core,
                         full_outside_core_seconds=full-core,
                         paper_denoise_decode_seconds=None))
    assert len(rows) == formal
    grouped = {}
    for role in sorted({r['role'] for r in rows}):
        rr = [r for r in rows if r['role'] == role]
        prompts = sorted({r['member'] for r in rr})
        per_prompt = []
        for member in prompts:
            subset = [r for r in rr if r['member'] == member]
            # Match repeated Native requests; do not overweight first four DEV prompts.
            repeats = sorted(r['repeat'] for r in subset)
            assert repeats == sorted(r['repeat'] for r in rows
                                     if r['role'] == baseline and r['member'] == member)
            per_prompt.append(dict(member=member, repeats=repeats,
                **{k: st.mean(r[k] for r in subset) for k in
                   FIELDS + ('guarded_outside_core_seconds', 'full_outside_core_seconds')}))
        means = {k: st.mean(p[k] for p in per_prompt) for k in
                 FIELDS + ('guarded_outside_core_seconds', 'full_outside_core_seconds')}
        grouped[role] = dict(prompts=len(prompts), requests=len(rr), means=means,
                             per_prompt=per_prompt, paper_denoise_decode_seconds=None)
    for role, group in grouped.items():
        group['speedups'] = {k: grouped[baseline]['means'][k] / group['means'][k]
                             for k in ('core_seconds', 'full_request_seconds')}
        group['paper_denoise_decode_speedup'] = None
    # Cross-check primary means against the already published scientific analysis.
    analysis_refs = {'DEV128':'cara_DEV128_A6000_complete_analysis_20261027.json',
                     'CAL66':'cara_CAL66_A6000_complete_analysis_20261026.json'}
    if name in analysis_refs:
        prior = read(ROOT / 'reports' / analysis_refs[name])
        summaries = prior['summaries']
        for role, group in grouped.items():
            expected = summaries[role]['budget']['mean_candidate']
            assert math.isclose(expected, group['means']['full_request_seconds'], abs_tol=1e-9)
    assert before == {str(p.relative_to(ROOT)): sha(p) for p in (cp, ap)}
    return dict(source_bindings=before, acceptance=accepted, original_paths=total,
                analyzed_clean_paths=formal, sections=list(sections), baseline=baseline,
                host=v['launch'].get('host', 'four_card'), source_revision=v['launch']['source_revision'],
                timer_payload_sha256=reg['payload_sha256']['src/wcomr/clean_speed20_r1.py'],
                upstream_pipeline_sha256=PIPE_SHA, all_request_timing_key_counts=dict(inventory),
                exact_paper_boundary_recoverable=False,
                missing='No denoising-loop-start/decode-end timestamps or preprocessing subintervals.',
                averaging='Average repeats within prompt first, then equal prompt means; speedup is ratio of means.',
                original_full_clock_verified=True, groups=grouped, rows=rows,
                load_seconds=runner['load_seconds'], original_receipts_unchanged=True)


def historical_inventory():
    result = {}
    for arm in ('native', 'worldcache'):
        p = ROOT / f'reports/f1_smoke_r3_{arm}.json'
        integrity = read(ROOT / f'reports/f1_smoke_r3_{arm}_integrity.json')
        if 'source_sha256' in integrity:
            assert integrity['source_sha256'] == sha(p)
        v = read(p)
        assert {(r['name'], r['sha256']) for r in v['samples']} == {
            (r['name'], r['sha256']) for r in integrity['artifacts']}
        result[arm] = dict(path=str(p.relative_to(ROOT)), sha256=sha(p),
                           accepted=len(v['samples']), rejected=len(v['rejections']),
                           historical_receipt_hash_bound='source_sha256' in integrity,
                           stage_keys=sorted({k for r in v['samples'] for k in r['stages']}))
    result['F1_caveat'] = ('F1 measured generate_samples_from_batch and model.decode separately; '
        'these are function durations, not contiguous loop-start-to-decode-end timestamps. '
        'Cold first case/refusals/offload and old protocol prohibit importing their overhead into CAL66/DEV128.')
    p = ROOT / 'paper/results/accepted_N08_separate_intervals_20261017/data.json'
    provenance = read(p.with_name('provenance.json'))
    assert provenance['output_sha256']['data.json'] == sha(p)
    for binding in provenance['source_bindings'].values():
        assert sha(ROOT / binding['path']) == binding['sha256']
    n = read(p)
    result['N08'] = dict(path=str(p.relative_to(ROOT)), sha256=sha(p),
                        formal_paths=n['formal_paths'], semantics=n['interval_semantics'],
                        exact_paper_boundary_recoverable=False)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--worker', choices=CARDS)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.worker:
        print(json.dumps(replay(args.worker))); return
    cards = {name: audit_card(name) for name in CARDS}
    output = dict(status='ACCEPTED_RAW_CLOCK_BOUNDARY_AUDIT_NO_EXACT_PAPER_RECONSTRUCTION',
        paper_definition_url='https://arxiv.org/html/2603.22286v1',
        paper_boundary='denoising loop start through decoding completion',
        observed_pipeline_boundary='generate_vid2world: input/text/conditioning preparation + sampling + decoding',
        core_is_paper_equivalent=False, cards=cards, historical_inventory=historical_inventory(),
        GPU_submissions=0, SSH_queries=0, ledger_written=False, thresholds_changed=False,
        scientific_acceptance_changed=False, missing_times_imputed=False)
    assert args.output and not args.output.exists()
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({name:{role:{'full':g['means']['full_request_seconds'],
          'pipeline':g['means']['core_seconds'], **g['speedups']} for role,g in card['groups'].items()}
          for name,card in cards.items()}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
