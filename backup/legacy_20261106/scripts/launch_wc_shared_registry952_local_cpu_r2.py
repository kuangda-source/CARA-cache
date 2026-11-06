#!/usr/bin/env python3
"""Seal committed execution sources without archiving bulk historical receipts."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
STAGE = '.sync/wc-paper-shared-registry952-local-cpu-r2-20261016'
GENERATION = 'R2'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    stage = ROOT / STAGE
    stage.mkdir()
    source = stage / 'source'
    source.mkdir()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=10).strip()
    # No -l: blob-size queries for historical data can trigger costly reads.
    records = subprocess.check_output([
        'git', 'ls-tree', '-r', '-z', revision, '--', 'src/', 'tests/',
        'scripts/', 'manifests/', 'configs/', 'pyproject.toml',
    ], cwd=ROOT, timeout=25)
    binding, object_ids = {}, {}
    for record in records.split(b'\0'):
        if not record:
            continue
        meta, name = record.split(b'\t', 1)
        mode, kind, blob = meta.split()
        relative = Path(os.fsdecode(name))
        assert not relative.is_absolute() and '..' not in relative.parts
        if kind != b'blob' or mode not in (b'100644', b'100755'):
            continue
        data = (ROOT / relative).read_bytes()
        identity = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        assert identity == blob.decode(), 'Uncommitted execution source: ' + str(relative)
        target = source / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        binding[str(relative)] = hashlib.sha256(data).hexdigest()
        object_ids[str(relative)] = identity
    required = ['scripts/check_wc_frozen_shared_registry952_local_cpu_r1.py',
                'tests/check_frozen_shared_execution_sampling_cpu_r1.py',
                'src/wcomr/frozen_shared_execution_r1.py',
                'manifests/wc_paper_shared_registry952_local_CPU_preregistration_r1_20261016.json']
    assert all(name in binding for name in required)
    registration = dict(source_revision=revision, payload_sha256=binding, Git_blob_ids=object_ids,
        expected_CPU_paths=952, expected_pairs=32816, expected_CFG_calls=65632,
        packaging_policy='EXACT_COMMITTED_EXECUTION_SOURCE_CONFIG_TESTS_WITHOUT_HISTORICAL_RESULTS',
        GPU_submissions=0, SSH_queries=0, ledger_written=False)
    regpath = stage / 'registration.json'
    regpath.write_text(json.dumps(registration, indent=2) + '\n')
    result = ROOT / f'reports/wc_paper_shared_registry952_local_CPU_{GENERATION}_result_20261016.json'
    exitpath = ROOT / f'reports/wc_paper_shared_registry952_local_CPU_{GENERATION}_exit_20261016.json'
    artifacts = stage / 'artifacts'
    runtime = ROOT / '.sync/wc-paper-n05-core216-local-cpu-r1-20261016/runtime'
    log = stage / 'full952.log'
    assert not result.exists() and not exitpath.exists() and not artifacts.exists()
    command = [str(ROOT / '.venv/bin/python'),
        str(source / 'scripts/check_wc_frozen_shared_registry952_local_cpu_r1.py'),
        '--runtime', str(runtime), '--artifacts', str(artifacts), '--output', str(result),
        '--exit', str(exitpath), '--registration', str(regpath)]
    environment = dict(os.environ, CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1',
        TRANSFORMERS_OFFLINE='1', PYTHONDONTWRITEBYTECODE='1', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    started = time.time()
    with log.open('xb') as handle:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=handle,
            stderr=subprocess.STDOUT, env=environment, cwd=source, start_new_session=True)
    identity = subprocess.check_output(['ps', '-p', str(child.pid), '-o', 'pid=,lstart=,command='],
                                       text=True, timeout=10).strip()
    assert 'check_wc_frozen_shared_registry952_local_cpu_r1.py' in identity
    receipt = dict(status='SHARED_REGISTRY952_LOCAL_CPU_SINGLE_LAUNCH_CONFIRMED_LIVE',
        pid=child.pid, started_unix=started, source_revision=revision,
        command=command, process_at_admission=identity, test_source_ref=str(source.relative_to(ROOT)),
        registration_ref=str(regpath.relative_to(ROOT)), registration_sha256=hashlib.sha256(regpath.read_bytes()).hexdigest(),
        payload_sha256=binding, expected_CPU_paths=952, expected_pairs=32816, expected_CFG_calls=65632,
        runtime_ref=str(runtime.relative_to(ROOT)), artifacts_ref=str(artifacts.relative_to(ROOT)),
        result_ref=str(result.relative_to(ROOT)), exit_ref=str(exitpath.relative_to(ROOT)), log_ref=str(log.relative_to(ROOT)),
        first_collection_not_before_unix=started + 12 * 60, expected_local_runtime_minutes=[7, 12],
        prior_packaging_failure_ref='reports/wc_paper_shared_registry952_source_packaging_R1_failure_20261016.json',
        final_inputs_frozen=False, final_methods_frozen=False, N05_original_stage_or_handles_touched=False,
        GPU_submissions=0, SSH_queries=0, ledger_written=False)
    args.output.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('payload_sha256', 'command', 'process_at_admission')}))


if __name__ == '__main__':
    main()
