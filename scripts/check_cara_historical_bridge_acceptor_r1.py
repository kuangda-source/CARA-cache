#!/usr/bin/env python3
"""Exercise rejection boundaries on a completed original CPU capture in memory."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from audit_cara_historical_bridge_cpu_r1 import accept


def check(original):
    accepted = accept(original)
    cases = [
        ('still_running', ('container', 'state', 'Running'), True),
        ('nonzero_exit', ('container', 'state', 'ExitCode'), 1),
        ('out_of_memory', ('container', 'state', 'OOMKilled'), True),
        ('writable_root', ('container', 'readonly_root'), False),
        ('source_changed', ('registration', 'source_revision'), 'changed'),
        ('CUDA_initialized', ('proof', 'data', 'CUDA_initialized'), True),
        ('weights_loaded', ('proof', 'data', 'model_weights_loaded'), True),
        ('missing_request', ('proof', 'data', 'actual_request_count'), 5),
        ('short_video', ('proof', 'data', 'codec', 'RGB_frames'), 92),
        ('transport_failed', ('proof', 'data', 'transport', 'original_fd_inode_match'), False),
        ('short_scope', ('proof', 'data', 'numeric', 'actual_CPU_paths'), 147),
        ('alpha_mismatch', ('proof', 'data', 'numeric', 'checks', 0, 'checks', 0, 'alpha_and_true_anchor_history_equal'), False),
        ('numerical_mismatch', ('proof', 'data', 'numeric', 'checks', 0, 'checks', 0, 'all36_guided_equal'), False),
        ('audit_lean_missing', ('proof', 'data', 'numeric', 'checks', 0, 'all36_audit_lean_controls'), False),
        ('wrong_proof_SHA', ('proof', 'sha256'), '0' * 64),
    ]
    rejected = []
    for name, path, value in cases:
        v = copy.deepcopy(original)
        target = v
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = value
        # Semantic mutations must reach the semantic checks, not stop at a stale hash.
        if path[:2] == ('proof', 'data'):
            raw = (json.dumps(v['proof']['data'], indent=2, allow_nan=False) + '\n').encode()
            v['proof']['sha256'] = hashlib.sha256(raw).hexdigest()
        try:
            accept(v)
        except ValueError as error:
            rejected.append(dict(case=name, rejection=str(error)))
        else:
            raise AssertionError('Acceptor admitted ' + name)
    return dict(status='ORIGINAL_CPU_ACCEPTED_AND_15_MUTATIONS_REJECTED',
                original_acceptance_status=accepted['status'], rejected=rejected,
                original_capture_modified=False, GPU_submissions=0)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--capture', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    raw = args.capture.read_bytes()
    result = check(json.loads(raw))
    result.update(capture_ref=str(args.capture), capture_sha256=hashlib.sha256(raw).hexdigest(),
                  checker_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  acceptor_sha256=hashlib.sha256(Path(__file__).with_name('audit_cara_historical_bridge_cpu_r1.py').read_bytes()).hexdigest())
    with args.output.open('x') as f:
        json.dump(result, f, indent=2)
        f.write('\n')
    print(result['status'])
