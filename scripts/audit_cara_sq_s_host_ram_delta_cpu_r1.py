"""Compose unchanged native S evidence with actual affected Linux controls."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def accept(packet):
    require(packet['status'] == 'S_RAM50_ORIGINAL_CPU_CAPTURE'
        and packet['original_CLI_live'] is False and packet['result'] is not None,
        'Original affected CPU worker must be terminal')
    result, reg, prior, old = (packet[key] for key in
        ('result', 'registration', 'prior_native_proof', 'prior_registration'))
    container = packet['container']
    require(container['state']['Status'] == 'exited' and container['state']['ExitCode'] == 0
        and not container['state']['OOMKilled']
        and container['image'] == 'sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d',
        'Pinned CPU container did not exit successfully')
    require(container['configuration'] == dict(NanoCpus=2000000000, Memory=2 * 2**30,
        MemorySwap=2 * 2**30, CpusetCpus='4,5', DeviceRequests=None, NetworkMode='none', ReadonlyRootfs=True),
        'Original bounded GPU-hidden CPU container required')
    require(result['passed'] is True and result['tests'] == 32
        and result['skipped'] == result['failures'] == result['errors'] == 0
        and result['actual_platform']['system'] == 'Linux' and result['torch_imported'] is False,
        'All32 affected Linux controls without Torch required')
    require(result['registration_sha256'] == packet['registration_sha256']
        and result['payload_actual_sha256'] == reg['payload_sha256']
        and result['runtime_actual_sha256'] == reg['runtime_source_sha256'] == old['runtime_source_sha256'],
        'Actual new source and unchanged pinned runtime bytes required')
    require(prior['passed'] is True and prior['full_S_entry_CPU_accepted'] is True
        and prior['native_parser_accepted'] is True and prior['host'] == reg['host']
        and prior['skipped'] == 0 and prior['payload_sha256'] == old['payload_sha256']
        and packet['prior_native_proof_sha256'] == reg['prior_native_CPU_sha256'],
        'Original complete native parser/matrix/lifecycle evidence required')
    changed = {name for name, digest in old['payload_sha256'].items()
        if reg['payload_sha256'].get(name) != digest}
    require(changed == {'src/wcomr/sq_s_spec_r2.py', 'src/wcomr/sq_s_execution_r2.py',
        'tests/test_sq_s_execution_r2.py'}, 'Unexpected change outside host admission and its fixture')
    identity = json.loads((ROOT / 'plans/cara_next_stage_20261028/sq/S_EXECUTION_IDENTITY_R1.json').read_text())
    require(all(old['payload_sha256'][name] == reg['payload_sha256'][name] == digest
        for name, digest in identity['numerical_source_sha256'].items()), 'Frozen numerical implementation changed')
    for name, digest in reg['payload_sha256'].items():
        if name in changed or name not in old['payload_sha256']:
            require(sha(subprocess.check_output(['git', 'show', reg['source_revision'] + ':' + name], cwd=ROOT)) == digest,
                'Affected source must match its published revision')
    profile = result['current_profile']
    require(profile['host_RAM_GiB'] == 40 and profile['minimum_host_MemAvailable_GiB'] == 50
        and reg.get('native_boot_id') and result['GPU_submissions'] == result['ledger_writes'] == 0,
        'Original40GiB hard cap plus10GiB host headroom required')
    critical = {name: reg['payload_sha256'][name] for name in prior['critical_source_sha256']}
    return dict(status='S_UNCHANGED_NATIVE_COMPONENTS_PLUS_RAM50_LINUX_CPU_ACCEPTED', passed=True,
        host=reg['host'], stage=reg['stage'], source_revision=reg['source_revision'],
        registration_sha256=packet['registration_sha256'], payload_sha256=reg['payload_sha256'],
        critical_source_sha256=critical, actual_platform=result['actual_platform'], skipped=0,
        full_S_entry_CPU_accepted=True, native_parser_accepted=True,
        acceptance_method='Unchanged original native components plus actual affected Linux admission/lifecycle tests',
        original_native_proof_sha256=packet['prior_native_proof_sha256'],
        reused_native_evidence=dict(unit_controls=prior['unit_controls'], complete_tiny_paths=prior['complete_tiny_paths'],
            Linux_supervisor_controls=prior['Linux_supervisor_controls']),
        affected_Linux_controls=32, numerical_pipeline_reexecuted=False,
        numerical_source_sha256=identity['numerical_source_sha256'], affected_source_paths=sorted(changed),
        container_RAM_GiB=40, minimum_host_MemAvailable_GiB=50, host_headroom_GiB=10,
        actual_GPU_entry_accepted=False, actual_S_labels=0, GPU_submissions=0, ledger_writes=0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Retain original accepted CPU evidence')
    proof = accept(json.loads(args.capture.read_text()))
    proof.update(capture_ref=str(args.capture), capture_sha256=sha(args.capture.read_bytes()),
        auditor_source_sha256=sha(Path(__file__).read_bytes()))
    with args.output.open('x') as stream:
        json.dump(proof, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps({key: proof[key] for key in ('status', 'host', 'affected_Linux_controls', 'source_revision')}))


if __name__ == '__main__':
    main()
