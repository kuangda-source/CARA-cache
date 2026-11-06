"""Accept only the original complete tiny-adjoint Linux CPU terminal."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from accept_cara_read_write_transition_linux_cpu_r1 import original_capture
from cara_read_write_adjoint_linux_cpu_r1 import OVERLAY, STAGE


def accept(launch_path, capture_path):
    cap, revision, overlay = original_capture(launch_path, capture_path, stage=STAGE, overlay_names=OVERLAY)
    proof = cap['CPU_proof'];metrics = proof['metrics']
    assert proof['status'] == 'READ_WRITE_ADJOINT_ACTUAL_LINUX_CPU_PASS_NOT_COSMOS_VJP'
    assert proof['complete_tiny_adjoint'] is True
    whole = metrics['full36_recomputed_adjoint']
    assert whole['agrees_with_direct_graph'] and whole['snapshots_unchanged'] and whole['actual_Cosmos_weights'] is False
    assert math.isfinite(whole['max_absolute_error']) and 0 <= whole['max_absolute_error'] <= 2e-8
    rows = metrics['actual_WC_tiny_point8_auxiliary_derivatives']
    assert [(r['group'], r['epsilon']) for r in rows] == [
        ('read', .5), ('read', 1.), ('write', .1), ('write', .2), ('total', .1), ('total', .2)]
    for row in rows:
        assert all(math.isfinite(row[k]) for k in ('predicted', 'central_FD', 'absolute_error', 'tolerance'))
        assert row['tolerance'] == max(3e-8, abs(row['predicted'])*.05)
        assert abs(row['predicted']-row['central_FD']) <= row['tolerance']
        assert math.isclose(row['absolute_error'], abs(row['predicted']-row['central_FD']), rel_tol=1e-9, abs_tol=1e-15)
    zero = metrics['actual_WC_post35_no_future_cache_consumer']
    assert zero['write'] == 0 and zero['incumbent'] == 'C' and zero['discrete_metadata_gradient'] is False
    dense = metrics['dense_incumbent_same_D_minus_C_sign']
    assert dense['values']['incumbent'] == 'D' and abs(dense['values']['total']-dense['central_FD']) <= 1e-8
    sha = lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return dict(status='ORIGINAL_READ_WRITE_ADJOINT_LINUX_CPU_ACCEPTED_TINY_NOT_COSMOS',
        source_revision=revision, launch_ref=str(launch_path), launch_sha256=sha(launch_path),
        capture_ref=str(capture_path), capture_sha256=sha(capture_path), launch=cap['launch'],
        container_state=cap['container_state'], registration_sha256=cap['registration_sha256'],
        CPU_proof_sha256=cap['CPU_proof_sha256'], affected_source_sha256=overlay,
        tests_run=5, torch_version=proof['torch_version'], metrics=metrics,
        wall_seconds=proof['ended_unix']-proof['started_unix'], actual_Linux_imports=True,
        complete_tiny_adjoint=True, actual_Cosmos_weights=False, real_Cosmos_adjoint=False,
        video_terminal_VJP=False, GPU_submissions=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('launch', 'capture', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = accept(args.launch, args.capture)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], wall_seconds=result['wall_seconds'])))


if __name__ == '__main__':
    main()
