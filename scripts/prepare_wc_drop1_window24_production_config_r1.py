#!/usr/bin/env python3
"""Bind a complete24 config/quote only after original full N09 acceptance."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--N09-capture', type=Path, required=True)
    p.add_argument('--N09-acceptance', type=Path, required=True)
    p.add_argument('--quote-output', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    sys.path.insert(0, str(ROOT / 'src'))
    from wcomr import drop1_window24_production_r1 as production
    from wcomr.drop1_window_original_controls_r1 import verify
    from wcomr.runtime_profile40_acceptance_r1 import accept
    dest = ROOT / production.CONFIG
    if dest.exists() or a.quote_output.exists() or a.output.exists():
        raise ValueError('Preserve each original config/quote/preparation receipt')

    def binding(path):
        path = path.resolve(); relative = path.relative_to(ROOT)
        return dict(ref=str(relative), sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def read(path):
        raw = path.read_bytes()
        return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)

    N09 = read(a.N09_capture); accepted = accept(N09, N09['launch'])
    saved = read(a.N09_acceptance)
    if (not accepted['full_runtime_profile_scope_accepted']
            or any(saved.get(k) != v for k, v in accepted.items())
            or saved.get('capture_sha256') != binding(a.N09_capture)['sha256']):
        raise ValueError('Complete original N09 GPU/post/scalar/financial independent acceptance required')
    files = {k: ROOT / v for k, v in production.FIXED_REFERENCES.items()}
    values = {k: read(v) for k, v in files.items()}
    spec = importlib.util.spec_from_file_location('original18_source_acceptor', ROOT / 'scripts/analyze_wc_drop1_full18_r1.py')
    original = importlib.util.module_from_spec(spec); spec.loader.exec_module(original)
    old_accepted = original.analyze(values['old_capture'], values['original_config'])
    if not old_accepted['accepted'] or any(values['old_acceptance'].get(k) != v for k, v in old_accepted.items()):
        raise ValueError('Original whole18 accepted raw evidence required')
    verify(values['old_controls'], values['old_capture'], values['old_acceptance'],
           values['original_config'], values['static_scope'], values['baseline'], values['old_controls']['evidence'])
    production.numerical.validate_static_manifest(values['static_scope'], values['original_config'])
    scenes = [r['name'] for r in values['static_scope']['requests']]
    quote = production.estimate_whole24(values['old_capture'], N09, accepted, scenes)
    quote_bytes = (json.dumps(quote, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    quote_relative = a.quote_output.resolve().relative_to(ROOT)
    refs = {k: binding(v) for k, v in files.items()}
    refs.update(N09_capture=binding(a.N09_capture), N09_acceptance=binding(a.N09_acceptance),
                cost=dict(ref=str(quote_relative), sha256=hashlib.sha256(quote_bytes).hexdigest()))
    c = dict(values['original_config'], card=production.CARD, run_id=production.RUN,
        namespace='DROP1_WINDOW24', methods=list(production.METHODS), scope_counts=production.COUNTS,
        CPU_scope=production.CPU_COUNTS, plans={k: list(v) for k, v in production.plans().items()},
        budget_origin_used_GPUh=79.99637737158223, continued_A_actual_updates=[21, 22, 23],
        forecast_complete_GPUh=quote['forecast_complete_GPUh'], billed_limit_GPUh=quote['billed_limit_GPUh'],
        references=refs)
    production.validate_contract(c)
    config_bytes = (json.dumps(c, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()
    # All original evidence and the whole estimate are validated before either
    # file is committed. Neither file can overwrite an earlier selection.
    with a.quote_output.open('xb') as h: h.write(quote_bytes)
    with dest.open('xb') as h: h.write(config_bytes)
    result = dict(status='WINDOW24_REAL_N09_BOUND_WHOLE_QUOTE_AND_CONFIG_NOT_PRODUCTION_CPU_OR_GPU',
        scope_counts=production.COUNTS, config_ref=production.CONFIG,
        config_sha256=hashlib.sha256(config_bytes).hexdigest(), quote_ref=str(quote_relative),
        quote_sha256=hashlib.sha256(quote_bytes).hexdigest(),
        source_references=refs, forecast_complete_GPUh=c['forecast_complete_GPUh'],
        billed_limit_GPUh=c['billed_limit_GPUh'],
        specific_whole_card_confirmation_required=quote['specific_whole_card_confirmation_required'],
        source_N09_whole_acceptance_reexecuted=True, original18_acceptance_reexecuted=True,
        actual_full24_production_CPU_accepted=False, GPU_submissions=0, ledger_written=False,
        new_A3_quality_or_speed_results=None)
    with a.output.open('x') as h:
        json.dump(result, h, ensure_ascii=False, indent=2, allow_nan=False); h.write('\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
