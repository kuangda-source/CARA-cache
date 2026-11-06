#!/usr/bin/env python3
"""Derive both exposed official masks from SHA-bound completed raw receipts."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.fixed_refresh_mask import FixedRefreshMask


def prepare(receipt_path, audit_path):
    raw = gzip.decompress(receipt_path.read_bytes())
    receipt, audit = json.loads(raw), json.loads(audit_path.read_text())
    sha = hashlib.sha256(raw).hexdigest()
    if sha != audit['receipt_sha256'] or audit['status'] != 'TEN_LIGHT_OUTPUT_STRUCTURAL_DD_PROVENANCE_AND_TIMING_AUDIT_PASS_NOT_QUALITY':
        raise ValueError('Completed independent ten-output audit must match raw receipt')
    masks = []
    for request, context in zip(receipt['measurements']['requests'], receipt['reference_contexts']):
        official = [p for p in request['phases'] if p['kind'] == 'official']
        assert len(official) == 2 and official[0]['trace'] == official[1]['trace']
        rows = official[0]['trace']
        assert len(rows) == 72 and [r['cache_counter_before'] for r in rows] == list(range(70)) + [0, 1]
        mask = FixedRefreshMask(request['sample_name'], context[1], context[2],
            tuple(r['deep_executed'] for r in rows), sha)
        mask.bind(tuple(context));masks.append(mask.to_dict())
    assert len(masks) == 2
    return {'status': 'CPU_EXPOSED_OFFICIAL_MASKS_BOUND_NOT_GPU_CARD',
        'source_receipt_sha256': sha, 'source_audit_sha256': hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        'masks': masks, 'new_GPU_submission': False, 'execution_selected': False,
        'limits': ['These masks use previously exposed complete official traces.',
            'Both diagnostic arms receive the same frozen decisions; no online teacher routing claim.',
            'Actual GPU mask parity and candidate fidelity remain unverified.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.receipt, args.audit)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'status': result['status'],
        'dense_calls': {m['sample_name']: sum(m['dense_calls']) for m in result['masks']}}))
