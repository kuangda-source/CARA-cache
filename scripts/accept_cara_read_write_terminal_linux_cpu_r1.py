"""Accept the original real-metric CPU input VJP without extending its scope."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from accept_cara_read_write_transition_linux_cpu_r1 import original_terminal_capture
from cara_read_write_terminal_linux_cpu_r1 import OVERLAY, STAGE
from check_cara_read_write_terminal_linux_cpu_r1 import ALEX_SHA, LINEAR_SHA


def accept(launch_path, capture_path):
    cap, revision, overlay = original_terminal_capture(launch_path, capture_path,
        stage=STAGE, overlay_names=OVERLAY, expected_tests=3)
    proof = cap['CPU_proof'];metrics = proof['metrics']
    assert proof['status'] == 'READ_WRITE_REAL_ALEX_SYNTHETIC_FULL93_CPU_PASS'
    assert proof['actual_Alex_weights'] and proof['terminal_LPIPS_VJP'] and proof['synthetic_video']
    assert proof['frames'] == 93 and proof['geometry'] == [64,64]
    assert proof['real_experiment_video_read'] is False and proof['actual_pretrained_VAE'] is False
    weights = proof['weights_sha256']
    assert len(weights) == 2 and set(weights.values()) == {ALEX_SHA, LINEAR_SHA}
    assert set(proof['metric_weight_loads']) == set(weights)
    row = metrics['full93_stream_equals_direct']
    assert row['frames'] == 93 and row['geometry'] == [64,64] and row['actual_Alex_weights']
    assert row['active_metric_graph_frames'] == 1 and row['gradient_tolerance'] == 2e-8
    assert math.isfinite(row['value']) and row['value'] == row['direct_value']
    assert 0 <= row['gradient_max_error'] <= 2e-8 and row['gradient_max_absolute'] > 1e-7
    derivatives = metrics['full93_real_Alex_directional_FD']
    assert [r['epsilon'] for r in derivatives] == [.02, .01]
    for r in derivatives:
        assert all(math.isfinite(r[k]) for k in ('predicted', 'central_FD', 'absolute_error'))
        assert abs(r['predicted']) > 1e-6
        tolerance = max(1e-6, abs(r['predicted'])*.02)
        assert r['tolerance'] == tolerance and abs(r['predicted']-r['central_FD']) <= tolerance
        assert math.isclose(r['absolute_error'], abs(r['predicted']-r['central_FD']), rel_tol=1e-9, abs_tol=1e-15)
    assert metrics['refusals'] == ['PARTIAL_VIDEO', 'UNBOUND_MODEL_WEIGHT']
    sha = lambda path:hashlib.sha256(Path(path).read_bytes()).hexdigest()
    return dict(status='ORIGINAL_REAL_ALEX_FULL93_CPU_INPUT_VJP_ACCEPTED', source_revision=revision,
        launch_ref=str(launch_path), launch_sha256=sha(launch_path), capture_ref=str(capture_path),
        capture_sha256=sha(capture_path), launch=cap['launch'], container_state=cap['container_state'],
        registration_sha256=cap['registration_sha256'], CPU_proof_sha256=cap['CPU_proof_sha256'],
        affected_source_sha256=overlay, tests_run=3, metrics=metrics, weights_sha256=weights,
        wall_seconds=proof['ended_unix']-proof['started_unix'], real_Alex_input_VJP=True,
        synthetic_video=True, frames=93, geometry=[64,64], real_experiment_video_read=False,
        actual_pretrained_VAE=False, real_Cosmos_adjoint=False, GPU_submissions=0, ledger_written=False)


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
