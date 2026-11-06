#!/usr/bin/env python3
"""Read audited first point and optional complete Human point; preserve all costs."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def load_bundle(config, receipt, terminal, score, score_audit, supervisor, originals):
    raw = {name: path.read_bytes() for name, path in [
        ('config', config), ('receipt', receipt), ('terminal', terminal), ('score', score), ('score_audit', score_audit)]}
    if receipt.suffix == '.gz':
        raw['receipt'] = gzip.decompress(raw['receipt'])
    raw['supervisor'] = supervisor.read_bytes()
    raw['originals'] = originals.read_bytes()
    return {**{name: json.loads(value) for name, value in raw.items()},
            'bytes': {name: len(value) for name, value in raw.items()},
            'sha256': {name: hashlib.sha256(value).hexdigest() for name, value in raw.items()}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    for name in ['config', 'receipt', 'terminal', 'score', 'score-audit', 'supervisor', 'originals']:
        parser.add_argument('--human-'+name, type=Path)
    args = parser.parse_args(); args.root = args.root.resolve()
    if args.output.exists():
        raise ValueError('Keep prior summary identity; do not overwrite')
    sys.path.insert(0, str(args.root/'src'))
    from wcomr.rv0_two_point_summary import summarize, historical_masks
    first = load_bundle(args.root/'configs/wc_w3_small_cd_approved_r1_20261005.json',
        args.root/'reports/wc_w3_small_cd_runner_20261005.json.gz',
        args.root/'reports/wc_w3_small_cd_failed_terminal_audit_20261005.json',
        args.root/'reports/wc_w3_small_cd_failed_card_lpips_cpu_20261005.json',
        args.root/'reports/wc_w3_small_cd_failed_card_lpips_cpu_audit_20261005.json',
        args.root/'reports/wc_w3_small_cd_supervisor_20261005.json',
        args.root/'reports/wc_w3_small_cd_original_receipts_20261005.json')
    paths = [getattr(args, 'human_'+name) for name in ['config', 'receipt', 'terminal', 'score', 'score_audit', 'supervisor', 'originals']]
    if any(paths) and not all(paths):
        raise ValueError('All seven Human originals are required; missing rows cannot be filled')
    human = load_bundle(*paths) if all(paths) else None
    result = summarize(first, human)
    historical_name = 'reports/wc_fair_cal_r1_runner_20261004.json.gz'
    historical_raw = (args.root/historical_name).read_bytes()
    historical_sha = hashlib.sha256(historical_raw).hexdigest()
    if historical_sha != first['config']['historical_reference_bindings'][historical_name]:
        raise ValueError('Frozen original FAIR mask receipt digest differs')
    result['historical_action_masks'] = historical_masks(first['config'], json.loads(gzip.decompress(historical_raw)))
    if result['historical_action_masks'][0]['historical_official_WC_target_action'] != result['points'][0]['official_WC_target_action']:
        raise ValueError('Current Common target must match the historical original decision')
    result['historical_mask_receipt_sha256'] = historical_sha
    result['source_sha256'] = {name: bundle['sha256'] for name, bundle in [('first', first), ('human', human)] if bundle}
    result['summary_code_sha256'] = {str(path.relative_to(args.root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in [Path(__file__).resolve(), args.root/'src/wcomr/rv0_two_point_summary.py']}
    result['CPU_only'] = True
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': result['status'], 'actual_complete_points': result['actual_complete_scientific_points'],
                      'physical_attempt_accounting': result['physical_attempt_accounting']}))


if __name__ == '__main__': main()
