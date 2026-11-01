"""Fixed real Alex weights, synthetic full93 RGB, CPU-only numerical controls.

Only the two prehashed metric checkpoints may be loaded. Cosmos/VAE weights
and original experiment videos are outside this component check.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time


ALEX_SHA = '7be5be791159472b1fbf3c69796f7cb30dca7ad8466c2df70058c37116cdee02'
LINEAR_SHA = 'df73285e35b22355a2df87cdb6b70b343713b667eddbda73e1977e0c860835c0'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('runtime', 'stage', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--host', required=True)
    args = parser.parse_args()
    assert args.host == 'two_card' and os.sched_getaffinity(0) == {26} and not args.output.exists()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    signal.alarm(600)
    started = time.time()
    sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
    reg = json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/name) == digest for name,digest in reg['payload_sha256'].items())
    assert all(sha(args.runtime/name) == digest for name,digest in reg['runtime_source_sha256'].items())
    metric_stage = args.stage.parent/'wc-time-score-CPU-two_card-r1-20261027'
    os.environ.update(TORCH_HOME=str(metric_stage/'torch'), HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    sys.path[:0] = [str(args.stage/'src'), str(metric_stage/'site')]
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    assert not torch.cuda.is_initialized()

    def forbidden(*args, **kwargs):
        raise RuntimeError('Terminal CPU check forbids CUDA, downloads and generative-model weights')

    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    import lpips
    checkpoint = metric_stage/'torch/hub/checkpoints/alexnet-owt-7be5be79.pth'
    linear = Path(lpips.__file__).parent/'weights/v0.1/alex.pth'
    weights = {str(checkpoint.resolve()): ALEX_SHA, str(linear.resolve()): LINEAR_SHA}
    assert all(sha(name) == digest for name,digest in weights.items())
    load = torch.load
    loaded = []

    def metric_load(path, *positional, **keywords):
        target = str(Path(path).resolve())
        if target not in weights or sha(target) != weights[target]:
            raise RuntimeError('Only the two bound Alex metric checkpoints may be loaded')
        loaded.append(target)
        return load(path, *positional, **keywords)

    torch.load = metric_load
    alex = lpips.LPIPS(net='alex', version='0.1', verbose=False).cpu().eval().requires_grad_(False)
    assert set(loaded) == set(weights)
    from wcomr.cara_read_write_terminal_r1 import StreamingAlexTerminal, float_rgb
    objective = StreamingAlexTerminal(alex, geometry=(64,64))
    grid = torch.arange(3*93*64*64, dtype=torch.float32).reshape(1,3,93,64,64)
    candidate = (.55*torch.sin(grid/71)+.2*torch.cos(grid/113)).requires_grad_()
    native = (.4*torch.sin(grid/89)+.2*torch.cos(grid/127)).detach()

    def direct(value):
        return sum(alex(float_rgb(value[:, :, i])*2-1,
                        float_rgb(native[:, :, i])*2-1).reshape(-1).mean().double()
                   for i in range(93))/93

    observed = objective.loss(candidate, native)
    gradient = torch.autograd.grad(observed, candidate)[0]
    expected = direct(candidate)
    direct_gradient = torch.autograd.grad(expected, candidate)[0]
    error = float((gradient-direct_gradient).abs().max())
    assert float(observed) == float(expected) and error <= 2e-8
    assert bool(torch.isfinite(gradient).all()) and float(gradient.abs().max()) > 1e-7
    metrics = dict(full93_stream_equals_direct=dict(frames=93, geometry=[64,64],
        value=float(observed), direct_value=float(expected), gradient_max_error=error,
        gradient_tolerance=2e-8, gradient_max_absolute=float(gradient.abs().max()),
        active_metric_graph_frames=1, actual_Alex_weights=True))
    del expected, direct_gradient
    direction = (candidate.detach()-native)*.2
    predicted = float((gradient*direction).sum())
    assert abs(predicted) > 1e-6
    derivatives = []
    for epsilon in (.02, .01):
        with torch.no_grad():
            numerical = float((direct(candidate+epsilon*direction)-direct(candidate-epsilon*direction))/(2*epsilon))
        difference = abs(predicted-numerical)
        tolerance = max(1e-6, abs(predicted)*.02)
        assert difference <= tolerance
        derivatives.append(dict(epsilon=epsilon, predicted=predicted, central_FD=numerical,
            absolute_error=difference, tolerance=tolerance))
    metrics['full93_real_Alex_directional_FD'] = derivatives
    refusals = []
    try:
        objective.value_and_vjp(candidate[:, :, :92], native[:, :, :92])
    except ValueError:
        refusals.append('PARTIAL_VIDEO')
    try:
        metric_load('/UNBOUND_GENERATIVE_CHECKPOINT')
    except RuntimeError:
        refusals.append('UNBOUND_MODEL_WEIGHT')
    assert refusals == ['PARTIAL_VIDEO', 'UNBOUND_MODEL_WEIGHT']
    metrics['refusals'] = refusals
    assert not torch.cuda.is_initialized() and all(sha(name) == digest for name,digest in weights.items())
    signal.alarm(60)
    receipt = dict(status='READ_WRITE_REAL_ALEX_SYNTHETIC_FULL93_CPU_PASS',
        host=args.host, started_unix=started, ended_unix=time.time(), actual_CPU_affinity=[26],
        source_revision=reg['parent_git_revision'], registration_sha256=sha(args.stage/'registration.json'),
        payload_sha256=reg['payload_sha256'], runtime_source_sha256=reg['runtime_source_sha256'],
        tests_run=3, metrics=metrics, torch_version=torch.__version__, weights_sha256=weights,
        metric_weight_loads=loaded, actual_Alex_weights=True, synthetic_video=True,
        real_experiment_video_read=False, geometry=[64,64], frames=93,
        actual_Cosmos_weights=False, actual_pretrained_VAE=False, actual_Cosmos_model_VJP=False,
        terminal_LPIPS_VJP=True, complete_augmented_adjoint=False, CUDA_initialized=False,
        GPU_submissions=0, ledger_written=False, work_seconds=600, exit_seconds=60)
    with args.output.open('x') as stream:
        json.dump(receipt, stream, indent=2, allow_nan=False)
        stream.write('\n')
    print(json.dumps(dict(status=receipt['status'], wall_seconds=time.time()-started)))


if __name__ == '__main__':
    main()
