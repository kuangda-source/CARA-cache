#!/usr/bin/env python3
"""CPU/meta topology and shared-eval startup gate; no weights, CUDA or kernels."""
import argparse
import hashlib
import importlib
import inspect
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--contract', type=Path, required=True)
    args = parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU gate requires explicit empty CUDA_VISIBLE_DEVICES')
    contract = json.loads(args.contract.read_text())
    sys.path[:0] = [str(args.runtime), str(args.runtime/'packages/cosmos-oss'),
                   str(args.runtime/'packages/cosmos-cuda')]
    import torch
    if torch.cuda.is_initialized():
        raise ValueError('CUDA already initialized before CPU gate')

    def forbidden(*args, **kwargs):
        raise RuntimeError('CUDA/Triton execution forbidden in H0 native-mode CPU gate')

    torch.cuda._lazy_init = forbidden
    import triton

    class ImportOnlyDriver:
        def get_benchmarker(self):
            return forbidden

        def __getattr__(self, name):
            raise RuntimeError('Triton driver forbidden in CPU gate: ' + name)

    triton.runtime.driver.active = ImportOnlyDriver()
    from cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit import MinimalV1LVGDiT
    from cosmos_predict2._src.predict2.networks.minimal_v4_dit import SACConfig, CheckpointMode
    import transformer_engine as te
    from unittest.mock import patch
    from wcomr.h0_mode import establish_shared_eval, verify_shared_eval

    pins = {}
    for rel, digest in contract['source_sha256'].items():
        if rel.startswith('python-package/'):
            package, rest = rel.removeprefix('python-package/').split('/', 1)
            module = importlib.import_module(package)
            path = Path(module.__file__).parent/rest
        else:
            path = args.runtime/rel
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError('Native mode source changed: ' + rel)
        pins[rel] = actual
    kwargs = dict(contract['net_kwargs'])
    kwargs['sac_config'] = SACConfig(
        mode=CheckpointMode(kwargs['sac_config']['mode']),
        every_n_blocks=kwargs['sac_config']['every_n_blocks'],
    )
    native_init = te.pytorch.RMSNorm.__init__

    def meta_norm_init(self, *args, **kw):
        kw['device'] = 'meta'
        return native_init(self, *args, **kw)

    def meta_norm_reset(self):
        # Native TE reset materializes even a meta weight on CUDA. No weights
        # are required for this topology/mode gate; retain classes and flags.
        assert self.weight.device.type == 'meta'

    with patch.object(te.pytorch.RMSNorm, '__init__', meta_norm_init), \
            patch.object(te.pytorch.RMSNorm, 'reset_parameters', meta_norm_reset), \
            torch.device('meta'):
        net = MinimalV1LVGDiT(**kwargs)
    assert all(p.device.type == 'meta' for p in net.parameters())
    parameters = sum(p.numel() for p in net.parameters())
    assert parameters == contract['parameter_count']
    receipt = establish_shared_eval(net, contract['module_types'])
    assert receipt['before']['training_modules'] == contract['default_training_modules']
    verify_shared_eval(net, receipt)
    assert not torch.cuda.is_initialized()
    print(json.dumps({
        'status': 'ACTUAL_NATIVE_META_DEFAULT_MODE_AND_SHARED_EVAL_STARTUP_CPU_PASS',
        'torch': torch.__version__, 'mode': receipt, 'source_sha256': pins,
        'parameter_count': parameters, 'cuda_initialized': False,
        'weights_loaded': False, 'forward_executed': False,
        'contract_sha256': hashlib.sha256(args.contract.read_bytes()).hexdigest(),
        'train_method_source_sha256': hashlib.sha256(
            inspect.getsource(torch.nn.Module.train).encode()).hexdigest(),
        'cpu_adaptation': 'TE RMSNorm explicit meta device and skip meta reset; '
                          'import-only Triton benchmark factory denies execution',
        'interpretation': 'Topology and startup mode evidence; no GPU train/eval '
                          'output-equivalence claim or repaired H0 result',
    }))


if __name__ == '__main__':
    main()
