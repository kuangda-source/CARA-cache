#!/usr/bin/env python3
"""CPU-only immutable original180 audit, all compatible93-frame LPIPS and groups."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('project', 'stage'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0, str(args.stage / 'src'))
    from wcomr.frozen_shared_production_r1 import CONFIG, RUN, fingerprint, sha, write, validate_contract
    from wcomr.frozen_shared_post_r1 import (
        GPU_TERMINAL_STATUS, audit_payload, audit_rows, inspect_video, read_tensor, score_rows,
        summarize, warm_controls,
    )
    from wcomr.gpu_budget_pool_v2 import same_live_process
    config = json.loads((args.stage / CONFIG).read_text())
    registration = json.loads((args.stage / 'registration.json').read_text())
    binding = config['references']['bound_inputs']
    assert sha(args.stage / binding['ref']) == binding['sha256']
    bound = json.loads((args.stage / binding['ref']).read_text())
    plan = validate_contract(config, bound)
    assert all(sha(args.stage / name) == digest for name, digest in registration['payload_sha256'].items())
    root = (args.project / 'outputs' / RUN).resolve()
    supervisor = json.loads((root / 'supervisor.json').read_text())
    assert supervisor['status'] == GPU_TERMINAL_STATUS
    assert supervisor['source_revision'] == registration['source_revision']
    assert supervisor['config_sha256'] == sha(args.stage / CONFIG)
    assert supervisor['scope_counts'] == config['scope_counts']
    # Exact identity, not a later unrelated process reusing the same PID.
    assert not same_live_process(dict(pid=supervisor['pid'], start_ticks=supervisor['start_ticks']))
    if supervisor.get('child_identity'):
        assert not same_live_process(supervisor['child_identity'])
    runner_path = root / 'runner.json'
    runner = json.loads(runner_path.read_text()) if runner_path.exists() else {'runs': []}
    if runner_path.exists():
        assert sha(runner_path) == supervisor['runner_sha256']
        assert runner['source_revision'] == registration['source_revision']
        assert runner['config_sha256'] == sha(args.stage / CONFIG)
        assert runner['bound_input_fingerprint'] == fingerprint(bound)
        assert runner['scope_counts'] == config['scope_counts']
    import torch
    torch.set_num_threads(2)
    def forbidden(*a, **kw): raise RuntimeError('N07 CPU audit forbids CUDA/downloads')
    assert not torch.cuda.is_initialized()
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    destination = args.stage / 'CPU-final-results.json'
    assert not destination.exists()
    start = time.time()
    value = dict(status='N07_SHARED180_CPU_AUDIT_RUNNING', source_revision=registration['source_revision'],
        config_sha256=sha(args.stage / CONFIG), bound_input_fingerprint=fingerprint(bound),
        scope_counts=config['scope_counts'], GPU_supervisor=supervisor, audit_failures=[],
        GPU_submissions=0, ledger_written=False, CUDA_initialized=False)
    def save():
        value['CPU_wall_seconds'] = time.time() - start
        write(destination, value)
    def save_audit(progress): value.update(progress); save()
    save()
    try:
        value.update(audit_rows(runner['runs'], plan, bound,
            lambda row, planned, b: audit_payload(row, planned, b, root),
            lambda row: inspect_video(root, row), save=save_audit))
        rows = value['rows']
        controls, failed = warm_controls(rows, plan,
            lambda row: read_tensor(root, row['warm_guided_artifact'], 'guided'))
        value.update(warm_repeat_controls=controls)
        value['audit_failures'].extend(failed); save()
        from wcomr.lpips_resource_identity import audit
        resource = args.project / '.sync/wc-rv0-lpips-resource-v2'
        value['LPIPS_resource_identity'] = audit(resource, sha(args.stage / 'src/wcomr/rv0_lpips.py'))
        sys.path.insert(0, str(resource / 'site'))
        import lpips
        assert importlib.metadata.version('lpips') == '0.1.4'
        assert Path(lpips.__file__).resolve() == (resource / 'site/lpips/__init__.py').resolve()
        metric = lpips.LPIPS(net='alex', version='0.1', spatial=False, verbose=False).cpu().eval()
        for parameter in metric.parameters(): parameter.requires_grad_(False)
        from wcomr.rv0_video_reader import decoded_video
        from wcomr.rv0_lpips import score_pair
        def score(reference, candidate):
            with decoded_video(reference['video_path']) as left, decoded_video(candidate['video_path']) as right:
                return score_pair(left, right, metric,
                    reference_sha256=reference['video_artifact']['sha256'],
                    candidate_sha256=candidate['video_artifact']['sha256'])
        value['audit_failures'].extend(score_rows(rows, score, save=save))
        value.update(summarize(value, bound, observed_paths=len(runner['runs']),
                               child_exit_code=supervisor['child_exit_code']))
        value['artifact_inventory'] = [dict(path=str(p), bytes=p.stat().st_size, sha256=sha(p))
            for p in sorted(root.rglob('*')) if p.is_file() and p.suffix in ('.pt', '.mp4')]
        assert not torch.cuda.is_initialized(); save()
        if value['audit_failures']:
            raise RuntimeError('N07 original audit failures retained; valid subgroups do not replace full acceptance')
    except BaseException as error:
        value.update(CPU_terminal_error_type=type(error).__name__, CPU_terminal_error=str(error))
        if value['status'] == 'N07_SHARED180_CPU_AUDIT_RUNNING':
            value['status'] = 'N07_SHARED180_CPU_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED'
        save(); raise


if __name__ == '__main__': main()
