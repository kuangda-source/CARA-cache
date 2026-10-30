"""Accept original S asset CPU receipts without any remote call or model load."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
sha = lambda raw: hashlib.sha256(raw).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def accept(capture, installed, specification, verifier_sha256):
    launch, consumed, exit = (capture[key] for key in ('launch', 'consumed', 'worker_exit'))
    proof = capture['proof']
    require(capture['status'] == 'ORIGINAL_S_ASSET_CPU_CAPTURE' and capture['original_worker_live'] is False
        and capture['current_asset_stamps_and_links_unchanged'] is True
        and exit['status'] == 'S_ASSET_CPU_TERMINAL' and exit['exit_code'] == 0,
        'Original successful terminal and fresh asset identity required')
    require(all(value['host'] == installed['host'] for value in (capture, launch, consumed, exit, proof))
        and all(value['stage'] == installed['stage'] for value in (capture, launch, consumed, exit)),
        'Original installed host and source stage required')
    require(all(value['registration_sha256'] == installed['registration_sha256']
        for value in (capture, launch, consumed, exit, proof))
        and exit['source_revision'] == consumed['source_revision'] == installed['source_revision'],
        'Original accepted S registration and source revision required')
    require(all((value['identity']['pid'], value['identity']['start_ticks']) ==
        (launch['identity']['pid'], launch['identity']['start_ticks']) for value in (consumed, exit)),
        'Recover the same original worker PID and start ticks')
    worker = subprocess.check_output(['git', 'show', launch['worker_source_revision']
        + ':scripts/cara_sq_s_assets_cpu_r1.py'], cwd=ROOT)
    require(all(value['worker_sha256'] == sha(worker) for value in (launch, consumed, exit, proof))
        and launch['verifier_sha256'] == proof['verifier_module_sha256'] == verifier_sha256,
        'Published CPU worker and original accepted streaming verifier required')
    proof_raw = (json.dumps(proof, indent=2, allow_nan=False) + '\n').encode()
    require(sha(proof_raw) == capture['proof_sha256'] == exit['verification_sha256']
        and proof['status'] == 'S_MODEL_AND_AUXILIARY_ASSETS_SHA_VERIFIED_CPU_ONLY',
        'Exact original full digest proof bytes required')
    require(proof['asset_contract_sha256'] == sha((ROOT / 'plans/cara_next_stage_20261028/sq/S_MODEL_ASSETS_R1.json').read_bytes())
        and proof['all_snapshot_links_verified'] is True
        and len(proof['files']) == len(specification['files']) == 20,
        'Complete frozen S asset membership required')
    for descriptor, row in zip(specification['files'], proof['files']):
        require(row['path'] == descriptor['path'] and row['digest'] == descriptor['digest']
            and len(row['stamp']) == 5 and row['stamp'][2] == descriptor['bytes']
            and all(type(value) is int for value in row['stamp']), 'Asset digest, size or identity differs')
    require(proof['bytes_read'] == specification['total_file_bytes'] == 21348071882
        and capture['progress']['checked'] == capture['progress']['total'] == 20
        and capture['progress']['bytes_checked'] == proof['bytes_read'], 'Complete original bytes required')
    require(all(value['GPU_submissions'] == value['ledger_writes'] == 0
        for value in (capture, launch, consumed, exit, proof))
        and proof['model_weights_deserialized'] is proof['torch_imported'] is False
        and exit['authorizes_retry'] is False, 'CPU-only content verification required')
    require(exit['resources'] == dict(cpus=[4, 5], address_space_GiB=2, maximum_file_MiB=64,
        wall_seconds=1800, CPU_seconds=1800, nice=10, GPU='hidden')
        and 0 < exit['wall_seconds'] < 1800 and 0 <= exit['CPU_seconds'] < 1800
        and 0 < exit['peak_RSS_KiB'] < 2 * 2**20, 'Original bounded CPU execution required')
    return dict(status='S_FROZEN_ASSETS_CONTENT_CPU_ACCEPTED_NOT_GPU_CARD', passed=True,
        host=installed['host'], source_revision=installed['source_revision'], stage=installed['stage'],
        registration_sha256=installed['registration_sha256'], asset_proof_sha256=capture['proof_sha256'],
        worker_source_revision=launch['worker_source_revision'], worker_sha256=sha(worker),
        verifier_module_sha256=verifier_sha256, actual_files_hashed=20, actual_bytes_hashed=proof['bytes_read'],
        worker_identity=exit['identity'], resources=exit['resources'], wall_seconds=exit['wall_seconds'],
        CPU_seconds=exit['CPU_seconds'], peak_RSS_KiB=exit['peak_RSS_KiB'],
        actual_start_unix=consumed['started_unix'], actual_end_unix=exit['ended_unix'],
        first_successful_capture_unix=capture['observed_unix'],
        completed_before_planned_halfway=exit['ended_unix'] < launch['started_unix'] + 300,
        fresh_dispatch_asset_identity_recheck_required=True, model_weights_deserialized=False,
        real_S_labels=0, GPU_authority_created=False, GPU_submissions=0, ledger_writes=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=('two_card', 'four_card'), required=True)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Retain the original acceptance receipt')
    installed = json.loads((ROOT / ('reports/cara_sq_s_complete_' + args.host
        + '_source_install_r6_20261030.json')).read_text())
    specification = json.loads((ROOT / 'plans/cara_next_stage_20261028/sq/S_MODEL_ASSETS_R1.json').read_text())
    verifier = json.loads((ROOT / 'reports/cara_fast_B36_asset_CPU_acceptance_r1_20261029.json').read_text())
    value = accept(json.loads(args.capture.read_text()), installed, specification, verifier['asset_module_sha256'])
    value.update(capture_ref=str(args.capture), capture_sha256=sha(args.capture.read_bytes()),
        auditor_source_sha256=sha(Path(__file__).read_bytes()))
    with args.output.open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: value[key] for key in ('status', 'host', 'actual_files_hashed', 'wall_seconds')}))


if __name__ == '__main__':
    main()
