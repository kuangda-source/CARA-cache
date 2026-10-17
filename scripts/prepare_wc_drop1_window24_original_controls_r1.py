#!/usr/bin/env python3
"""Prepare every old endpoint control from accepted complete18 saved evidence."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = dict(
    original_capture='reports/wc_drop1_full18_terminal_collection_20261018_0001.json.gz',
    original_acceptance='reports/wc_drop1_full18_independent_acceptance_20261018.json',
    original_config='configs/wc_drop1_cal4_three_arm_full18_r1_20261017.json',
    new_static_scope='manifests/wc_drop1_correction_window_full24_static_scope_20261018.json',
    original_native_bindings='manifests/wc_simple26d_prior420_bindings_r1_20261015.json',
    original_acceptor='scripts/analyze_wc_drop1_full18_r1.py')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--acceptance-output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists() or a.acceptance_output.exists():
        raise ValueError('Preserve existing input control and acceptance files')
    raw = {k: (ROOT / f).read_bytes() for k, f in FILES.items()}
    evidence = {k: dict(ref=FILES[k], sha256=hashlib.sha256(b).hexdigest()) for k, b in raw.items()}
    values = {k: json.loads(gzip.decompress(b) if FILES[k].endswith('.gz') else b)
              for k, b in raw.items() if k != 'original_acceptor'}
    spec = importlib.util.spec_from_file_location('saved_original_drop1_acceptor', ROOT / FILES['original_acceptor'])
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    recomputed = module.analyze(values['original_capture'], values['original_config'])
    saved = values['original_acceptance']
    assert recomputed['accepted'] and all(saved[k] == v for k, v in recomputed.items())
    assert saved['capture_sha256'] == evidence['original_capture']['sha256']
    native_ref = values['original_config']['references']['baseline']
    assert native_ref == evidence['original_native_bindings']
    sys.path.insert(0, str(ROOT / 'src'))
    from wcomr.drop1_window_original_controls_r1 import bind, verify
    args = (values['original_capture'], saved, values['original_config'],
            values['new_static_scope'], values['original_native_bindings'], evidence)
    result = bind(*args); accepted = verify(result, *args)
    with a.output.open('x') as h:
        json.dump(result, h, indent=2, ensure_ascii=False, allow_nan=False); h.write('\n')
    accepted.update(controls_ref=str(a.output), controls_sha256=hashlib.sha256(a.output.read_bytes()).hexdigest(),
                    builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    original_raw_acceptor_reexecuted=True, SSH_queries=0, ledger_written=False)
    with a.acceptance_output.open('x') as h:
        json.dump(accepted, h, indent=2, ensure_ascii=False, allow_nan=False); h.write('\n')
    print(json.dumps(accepted))


if __name__ == '__main__':
    main()
