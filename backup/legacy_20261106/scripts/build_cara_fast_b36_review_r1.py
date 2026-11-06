"""Prepare or materialize a label-anonymous review of all accepted B36 positions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from wcomr.cara_fast_b36_figures_r1 import verify_analysis
from wcomr.cara_fast_review_r1 import plan_review, asset_catalog, materialize


def main():
    parser = argparse.ArgumentParser()
    for name in ('analysis', 'coordinator', 'output', 'receipt'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--videos', type=Path)
    parser.add_argument('--plan-only', action='store_true')
    parser.add_argument('--receipt-root', type=Path, default=ROOT)
    args = parser.parse_args()
    if args.receipt.exists():
        raise ValueError('Fresh preparation receipt required')
    output, key = args.output.resolve(), args.coordinator.resolve()
    if key == output or output in key.parents:
        raise ValueError('Coordinator key must be outside the public review directory')
    if args.receipt.resolve() == output or output in args.receipt.resolve().parents:
        raise ValueError('Preparation receipt must stay outside the public review directory')
    analysis, analysis_sha = verify_analysis(args.analysis, receipt_root=args.receipt_root)
    descriptor = analysis['input_file_sha256']['manifest']
    manifest_path = Path(descriptor['path'])
    if not manifest_path.is_absolute():
        manifest_path = args.receipt_root/manifest_path
    manifest = json.loads(manifest_path.read_bytes())
    if key.exists():
        if key.stat().st_mode & 0o077:
            raise ValueError('Coordinator key must have0600 permissions')
        prior = json.loads(key.read_text())
        if prior['analysis_sha256'] != analysis_sha:
            raise ValueError('Recover the original packet key for this accepted analysis')
        nonce = bytes.fromhex(prior['nonce'])
    else:
        prior = None
        nonce = secrets.token_bytes(32)
    plan = plan_review(analysis, manifest, nonce)
    coordinator = dict(schema='CARA_REVIEW_COORDINATOR_PRIVATE_R1', nonce=nonce.hex(),
                       analysis_sha256=analysis_sha, manifest_sha256=descriptor['sha256'], **plan)
    if prior is not None and prior != coordinator:
        raise ValueError('Original coordinator mapping changed; do not silently reassign cases')
    if prior is None:
        key.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(key, os.O_WRONLY|os.O_CREAT|os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as handle:
            json.dump(coordinator, handle, ensure_ascii=False, indent=2)
            handle.write('\n')
    assets = asset_catalog(plan)
    result = dict(status='B36_REVIEW_PLAN_READY_ORIGINAL_VIDEOS_REQUIRED',
        analysis_sha256=analysis_sha, manifest_sha256=descriptor['sha256'],
        package_id=plan['public']['package_id'], scenes=4, cases=32,
        original_unique_videos=len(assets), original_video_bytes=sum(d['bytes'] for d in assets),
        assets=assets, public_directory=str(output), coordinator_path=str(key),
        rendered_html=False, human_reviews=0, independent_human_evidence=False,
        metrics_computed=False, GPU_submissions=0, new_GPU_authority=False)
    if not args.plan_only:
        if args.videos is None:
            raise ValueError('Explicit hash-addressed original video directory required')
        result.update(materialize(plan, args.videos, output,
                                  ROOT/'scripts/templates/cara_fast_review_r1.html'))
        result['rendered_html'] = True
    result['source_sha256'] = {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in (
        'scripts/build_cara_fast_b36_review_r1.py', 'src/wcomr/cara_fast_review_r1.py',
        'scripts/templates/cara_fast_review_r1.html')}
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    with args.receipt.open('x') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'scenes', 'cases', 'rendered_html', 'human_reviews', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
