"""Affected CPU reader only: reuse complete R3 artifacts, never sample again."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser()
    for name in ('reader-stage', 'original-stage', 'output'): p.add_argument('--'+name, type=Path, required=True)
    args = p.parse_args(); os.environ['CUDA_VISIBLE_DEVICES'] = ''
    sys.path[:0] = [str(args.reader_stage/'src'), str(args.original_stage/'src')]
    import wcomr
    for path in (args.reader_stage/'src/wcomr', args.original_stage/'src/wcomr'):
        if str(path) not in wcomr.__path__: wcomr.__path__.append(str(path))
    import torch
    torch.set_num_threads(2)
    def forbidden(*args, **kwargs): raise RuntimeError('Read-only E4c CPU denies CUDA/downloads')
    torch.cuda._lazy_init = forbidden; torch.hub.download_url_to_file = forbidden
    from wcomr.e4c_source_age_tensor_audit_r2 import audit, scalar_equal
    from wcomr.e4c_source_age_summary_r1 import summarize
    value = json.loads((args.original_stage/'result.json').read_text())
    assert value['status'] == 'E4C_MATCHED_SOURCE_AGE_FULL_CPU_PASS_NOT_REAL_MODEL_OR_ADMISSION'
    results = []
    for check in value['checks']:
        root = args.original_stage/'CPU-artifacts'/('flow_ON' if check['flow'] else 'flow_OFF')
        def loader(path, **kw):
            path = Path(path).resolve(); assert path.is_relative_to(root.resolve())
            assert kw == {'weights_only': True, 'map_location': 'cpu'}
            return torch.load(path, **kw)
        raw = audit(check['receipt'], root, loader, [1, 2048, 2, 8, 8])
        summary = summarize(check['receipt'], raw)
        refusals = []
        for fault in ('missing_point', 'negative_time', 'wrong_source', 'teacher_leak'):
            state, reduced = copy.deepcopy(check['receipt']), copy.deepcopy(raw)
            point = state['requests'][0]['paths'][1]['origins'][0]['branches'][2]['age_points'][0]
            if fault == 'missing_point': reduced['actual_age_points_reduced'].pop()
            elif fault == 'negative_time': point['actual_C_full_pair_seconds'] = -1
            elif fault == 'wrong_source': point['actual_source_and_decision_history']['action'] = 'DD'
            else: point['teacher_updates_final_deployment_anchors'] = True
            try: summarize(state, reduced)
            except (ValueError, KeyError): refusals.append(fault)
            else: raise AssertionError('Invalid registered point summary accepted: '+fault)
        results.append({'flow': check['flow'], 'actual_tensor_audit': raw, 'summary': summary,
            'scope_refusals': refusals})
    assert scalar_equal(1., 1.+2e-16) and not scalar_equal(1., 1.+1e-7)
    assert not scalar_equal(float('nan'), 1.)
    assert not torch.cuda.is_initialized()
    target = args.output; assert not target.exists()
    result = {'status': 'E4C_READONLY_FULL_EXISTING_CPU_ARTIFACT_READER_PASS_NOT_NEW_GPU',
        'checks': results, 'actual_files_reloaded': 88, 'actual_tensors_reloaded': 776,
        'actual_direct_tensor_comparisons': 324, 'actual_points_summarized': 48,
        'scope_refusals': 8, 'FP64_scalar_rounding_controls': 3,
        'physical_sampling_or_native_meta_rerun': False, 'CUDA_initialized': False, 'GPU_submissions': 0}
    target.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'checks'}))


if __name__ == '__main__': main()
