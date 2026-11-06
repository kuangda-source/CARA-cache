#!/usr/bin/env python3
"""Review complete original prices after the original terminal acceptor passes."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts'))
from four_card_policy_assets_port_r1 import IMAGE
from wcomr.policy_interval_assets_r1 import read, sha
from wcomr.policy_interval_assets_lifecycle_r1 import accept_terminal
from wcomr.policy_asset_price_review_r1 import analyze_prices


def review(capture_path, acceptance_path, launch_path, contention_path):
    cap, accepted, launch, contention = map(read, (capture_path, acceptance_path, launch_path, contention_path))
    if cap.get('launch') != launch:
        raise ValueError('Different original launch receipt')
    original = accept_terminal(cap)
    binding = cap['container_binding']
    if (not original.get('full_protocol_accepted') or not original.get('generator_input_ready')
            or any(accepted.get(k) != v for k, v in original.items())
            or accepted.get('capture_sha256') != sha(capture_path)
            or accepted.get('container_binding_accepted') is not True
            or binding.get('image') != IMAGE or binding.get('readonly_root') is not True
            or binding.get('pid_mode') != 'host'
            or binding.get('registration_sha256') != launch['registration_sha256']
            or binding['state']['Running'] or binding['state']['ExitCode'] != 0):
        raise ValueError('Complete original acceptance and successful stopped container required')
    if (contention.get('launch_id') != launch['launch_id']
            or contention.get('gpu_uuid') != launch['gpu_uuid']):
        raise ValueError('Competition evidence must bind this exact launch and GPU')
    if (not launch['started_unix'] <= contention.get('observed_unix', 0) <= cap['observed_unix']
            or not any(p.get('gpu_uuid') == launch['gpu_uuid']
                       and p.get('is_registered_runner') is False
                       for p in contention.get('own_UUID_apps', []))):
        raise ValueError('Require a saved, timed observation of another context on this UUID')
    result = analyze_prices(cap['runner']['runs'])
    result.update(original_artifacts_accepted=True, launch_id=launch['launch_id'],
        gpu_uuid=launch['gpu_uuid'], known_same_GPU_contention=True,
        source_bindings=[dict(ref=str(p), sha256=sha(p))
            for p in (capture_path, acceptance_path, launch_path, contention_path)],
        GPU_submissions=0, ledger_written=False)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('capture', 'accepted', 'launch-ref', 'contention-ref', 'output'):
        p.add_argument('--' + key, required=True, type=Path)
    a = p.parse_args()
    result = review(a.capture, a.accepted, a.launch_ref, a.contention_ref)
    with a.output.open('x') as f:
        json.dump(result, f, indent=2, allow_nan=False); f.write('\n')
    print(json.dumps({k: result[k] for k in ('status', 'triply_measured_cells', 'clean_action_prices_accepted')}))


if __name__ == '__main__':
    main()
