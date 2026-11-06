#!/usr/bin/env python3
"""Pure CPU mask identity/protection rejection controls on actual exposed masks."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.fixed_refresh_mask import FixedRefreshMask
from prepare_wc_fixed_masks_cpu import prepare


def check(mask_path, receipt_path, audit_path):
    data = json.loads(mask_path.read_text())
    assert data == prepare(receipt_path, audit_path)
    checks = []
    for row in data['masks']:
        kw = {k: row[k] for k in ['sample_name', 'model_id', 'condition_id',
                                 'source_receipt_sha256', 'horizon', 'warm_calls']}
        kw['dense_calls'] = tuple(row['dense_calls'])
        mask = FixedRefreshMask(**kw)
        mask.bind(('CPU_DIAGNOSTIC:' + row['sample_name'], row['model_id'], row['condition_id']))
        assert sum(not mask.skip(c, (c - 1) % 2) for c in range(1, 73)) == sum(row['dense_calls'])
        mutations = [{'dense_calls': kw['dense_calls'][:-1]},
                     {'dense_calls': tuple(1 for v in kw['dense_calls'])},
                     {'source_receipt_sha256': 'x' * 64}, {'horizon': 35}]
        for position in [0, 13, 70, 71]:
            calls = list(kw['dense_calls']); calls[position] = False
            mutations.append({'dense_calls': tuple(calls)})
        for change in mutations:
            try: FixedRefreshMask(**dict(kw, **change))
            except ValueError: pass
            else: raise AssertionError(change)
        for context in [('CPU_DIAGNOSTIC:wrong', row['model_id'], row['condition_id']),
                        ('CPU_DIAGNOSTIC:' + row['sample_name'], 'other', row['condition_id']),
                        ('CPU_DIAGNOSTIC:' + row['sample_name'], row['model_id'], 'other')]:
            try: mask.bind(context)
            except ValueError: pass
            else: raise AssertionError(context)
        for call, branch in [(0, 0), (73, 0), (1, 1)]:
            try: mask.skip(call, branch)
            except ValueError: pass
            else: raise AssertionError((call, branch))
        checks.append({'sample': row['sample_name'], 'dense_calls': sum(row['dense_calls']),
            'mask_rejection_controls': len(mutations), 'context_rejection_controls': 3,
            'call_CFG_rejection_controls': 3})
    files = [mask_path, receipt_path, audit_path, Path(__file__),
             Path(__file__).resolve().parents[1] / 'src/wcomr/fixed_refresh_mask.py',
             Path(__file__).with_name('prepare_wc_fixed_masks_cpu.py')]
    return {'status': 'TWO_EXPOSED_MASK_IDENTITY_WARM_TAIL_REJECTION_CPU_PASS',
        'checks': checks, 'total_rejection_controls': sum(sum(q[k] for k in
            ['mask_rejection_controls', 'context_rejection_controls', 'call_CFG_rejection_controls']) for q in checks),
        'inputs_and_code_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        'CPU_only': True, 'new_GPU_submission': False, 'quality_acceptance': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--masks', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.masks, args.receipt, args.audit)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'], 'rejection_controls': result['total_rejection_controls']}))
