"""Accept only the original complete Wan2.1-source/tiny-weight CPU terminal."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from accept_cara_read_write_transition_linux_cpu_r1 import original_capture
from cara_read_write_vae_linux_cpu_r1 import OVERLAY, STAGE
from wcomr.cara_read_write_vae_r1 import WAN_SHA256


def accept(launch_path, capture_path):
    cap, revision, overlay = original_capture(launch_path, capture_path,
        stage=STAGE, overlay_names=OVERLAY, expected_tests=3)
    proof = cap['CPU_proof'];metrics = proof['metrics']
    assert proof['status'] == 'READ_WRITE_VAE_ACTUAL_LINUX_CPU_PASS_NOT_COSMOS_VJP'
    assert proof['actual_Wan21_import'] and proof['VAE_source_sha256'] == WAN_SHA256
    assert proof['actual_pretrained_VAE'] is False
    for length,frames in ((1,1), (24,93)):
        assert metrics['hard_forward_'+str(length)] == dict(full_frames=frames, bitwise_equal=True,
            caller_cache_unchanged=True, original_no_grad_reference=True, calibration_graph_retained=True)
    row = metrics['cross_chunk_last_frame_VJP']
    assert all(math.isfinite(row[k]) for k in ('predicted', 'central_FD', 'absolute_error'))
    assert abs(row['predicted']) > 1e-5 and row['epsilon'] == 1e-4
    assert abs(row['predicted']-row['central_FD']) <= 1e-8
    assert math.isclose(row['absolute_error'], abs(row['predicted']-row['central_FD']), rel_tol=1e-9, abs_tol=1e-15)
    assert row['previous_chunk_gradient_nonzero'] and row['actual_pretrained_weights'] is False
    sha = lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return dict(status='ORIGINAL_READ_WRITE_VAE_LINUX_CPU_ACCEPTED_TINY_NOT_PRETRAINED',
        source_revision=revision, launch_ref=str(launch_path), launch_sha256=sha(launch_path),
        capture_ref=str(capture_path), capture_sha256=sha(capture_path), launch=cap['launch'],
        container_state=cap['container_state'], registration_sha256=cap['registration_sha256'],
        CPU_proof_sha256=cap['CPU_proof_sha256'], affected_source_sha256=overlay,
        actual_Linux_Wan21_import=True, VAE_source_sha256=WAN_SHA256, tests_run=3,
        metrics=metrics, wall_seconds=proof['ended_unix']-proof['started_unix'],
        actual_pretrained_VAE=False, video_Alex_VJP=False, actual93_GPU_memory=False,
        GPU_submissions=0, ledger_written=False)


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
