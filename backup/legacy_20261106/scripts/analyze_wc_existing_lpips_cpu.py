#!/usr/bin/env python3
"""Score registered existing FAIR videos with the frozen deployed CPU metric."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_manifest(data):
    pairs = data['pairs']
    if len(pairs) != 10 or len(data['control_files']) != 2:
        raise ValueError('Preserve ten Native pairs and two separate D/D control files')
    samples = sorted({p['sample'] for p in pairs})
    if len(samples) != 2:
        raise ValueError('Two exposed CAL samples required')
    for sample in samples:
        rows = [p for p in pairs if p['sample'] == sample]
        if {p['variant'] for p in rows} != {'native23', 'wc004', 'wc006', 'wc008', 'stage_every1'}:
            raise ValueError('Complete per-scene workpoint denominator required')
        if len({(p['reference']['path'], p['reference']['sha256']) for p in rows}) != 1:
            raise ValueError('One matched Native35 reference per scene required')
        for row in rows:
            if row['reference']['sha256'] == row['candidate']['sha256']:
                raise ValueError('A candidate pair cannot be substituted by a self pair')
            for side in ['reference', 'candidate']:
                if not Path(row[side]['path']).is_absolute():
                    raise ValueError('Registered artifact paths must be absolute')
    return samples


def main():
    parser = argparse.ArgumentParser()
    for name in ['project', 'stage', 'manifest', 'output']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Preserve existing analysis identity'
    manifest = json.loads(args.manifest.read_text())
    samples = validate_manifest(manifest)
    assert sha(__file__) == manifest['analysis_script_sha256']
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    os.environ['HF_HUB_OFFLINE'] = '1'
    os.environ['TRANSFORMERS_OFFLINE'] = '1'
    sys.path.insert(0, str(args.stage/'src'))
    config = json.loads((args.stage/'causal-config.json').read_text())
    for name in ['src/wcomr/rv0_lpips.py', 'src/wcomr/rv0_video_reader.py']:
        assert sha(args.stage/name) == config['payload_sha256'][name] == manifest['frozen_sources'][name]
    resource = args.project/config['lpips_resource_stage']
    spec = importlib.util.spec_from_file_location('resource_auditor', args.stage/'scripts/audit_wc_rv0_lpips_resource.py')
    auditor = importlib.util.module_from_spec(spec); spec.loader.exec_module(auditor)
    audited = auditor.audit(args.project, resource, manifest['frozen_sources']['src/wcomr/rv0_lpips.py'])
    sys.path.insert(0, str(resource/'site'))
    import numpy as np
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*a, **k):
        raise RuntimeError('Existing-video CPU analysis forbids CUDA and downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2)
    import lpips
    from wcomr.rv0_lpips import PROTOCOL, prepare_rgb, score_pair
    from wcomr.rv0_video_reader import decoded_video, probe_video
    assert PROTOCOL == audited['protocol']
    assert Path(lpips.__file__).resolve() == (resource/'site/lpips/__init__.py').resolve()
    model = lpips.LPIPS(net='alex', version='0.1', spatial=False, verbose=False).cpu().eval()
    for p in model.parameters(): p.requires_grad_(False)
    files = {v['path']: v['sha256'] for row in manifest['pairs'] for v in [row['reference'], row['candidate']]}
    files.update({v['path']: v['sha256'] for v in manifest['control_files']})
    for row in manifest.get('W1_pairs', []):
        for side in ['reference', 'candidate']:
            files[row[side]['path']] = row[side]['sha256']
    protected = dict(files)
    protected[str(args.project/'reports/budget.json')] = manifest['budget_sha256']
    before = {path: sha(path) for path in protected}
    assert before == protected
    record = {'status': 'EXISTING_FAIR_LPIPS_CPU_STARTED', 'CPU_only': True,
              'analysis_role': 'EXISTING_NATIVE_FIDELITY_NOT_CAUSAL_LABELS',
              'planned_pairs': 10, 'samples': samples, 'pairs': [], 'checks': {},
              'planned_W1_pairs': len(manifest.get('W1_pairs', [])), 'W1_pairs': [],
              'manifest_sha256': sha(args.manifest), 'analysis_code_sha256': sha(__file__),
              'frozen_metric_sources': manifest['frozen_sources'],
              'metric_protocol': {k:v for k,v in PROTOCOL.items() if k not in ['benefit', 'policy']},
              'resource_receipt_sha256': sha(resource/'receipt.json'),
              'protected_file_sha256_before': before, 'started_unix': time.time(),
              'GPU_submissions': 0, 'new_generation': 0, 'formal_RV_training_labels': 0,
              'quality_acceptance': False, 'physics_acceptance': False, 'independent_confirmation': False}
    tick = time.perf_counter()
    def save():
        temp = args.output.with_suffix('.tmp')
        temp.write_text(json.dumps(record, indent=2, allow_nan=False)+'\n'); temp.replace(args.output)
    def score(a, b):
        with decoded_video(a['path']) as left, decoded_video(b['path']) as right:
            return score_pair(left, right, model, reference_sha256=a['sha256'], candidate_sha256=b['sha256'])
    save()
    try:
        zero = prepare_rgb(np.zeros((1, 1, 3), dtype=np.uint8)); white = prepare_rgb(np.full((1, 1, 3), 255, dtype=np.uint8))
        assert float(zero.min()) == -1 and float(white.max()) == 1
        # Complete D/D check is a control, not a Native quality pair.
        control = score(*manifest['control_files'])
        assert all(v == 0 for v in control['frame_distances'])
        record['checks']['DD_complete93'] = control
        first = manifest['pairs'][0]
        # Consume full streams so reader cleanup also validates EOF; no media saved.
        with decoded_video(first['reference']['path']) as left, decoded_video(first['candidate']['path']) as right:
            a = next(left); b = next(right)
            for _ in left: pass
            for _ in right: pass
        assert not np.array_equal(a[0], b[0])
        distinct = score_pair([a], [b], model, reference_sha256=first['reference']['sha256'],
                              candidate_sha256=first['candidate']['sha256'], expected_frames=1)
        assert distinct['mean_LPIPS'] > 0
        changed = np.clip(a[0].astype(np.int16)+1, 0, 255).astype(np.uint8)
        assert not np.array_equal(changed, a[0])
        perturbed = score_pair([a], [(changed, a[1], a[2])], model,
            reference_sha256=first['reference']['sha256'], candidate_sha256=hashlib.sha256(changed.tobytes()).hexdigest(), expected_frames=1)
        assert perturbed['mean_LPIPS'] > 0
        record['checks']['distinct_decoded_first_frame'] = distinct
        record['checks']['plus1_clipped_in_memory_first_frame'] = dict(perturbed, candidate_identity_is_RGB_fixture_not_video=True)
        record['checks']['UINT8_endpoints_minus1_plus1'] = True
        save()
        for pair in manifest['pairs']:
            start = time.perf_counter()
            value = score(pair['reference'], pair['candidate'])
            record['pairs'].append(dict(pair, score=value, CPU_wall_seconds=time.perf_counter()-start))
            save()
            print(json.dumps({'completed_pairs': len(record['pairs']), 'planned_pairs': 10,
                              'sample': pair['sample'], 'variant': pair['variant'],
                              'mean_LPIPS': value['mean_LPIPS']}), flush=True)
        assert len(record['pairs']) == 10
        for pair in manifest.get('W1_pairs', []):
            start = time.perf_counter()
            value = score(pair['reference'], pair['candidate'])
            record['W1_pairs'].append(dict(pair, score=value, CPU_wall_seconds=time.perf_counter()-start))
            save()
            print(json.dumps({'completed_W1_pairs': len(record['W1_pairs']),
                              'planned_W1_pairs': record['planned_W1_pairs'], 'sample': pair['sample'],
                              'mean_LPIPS': value['mean_LPIPS']}), flush=True)
        assert len(record['W1_pairs']) == record['planned_W1_pairs']
        record['status'] = 'EXISTING_FAIR_TEN_FULL93_LPIPS_CPU_PASS_NOT_METHOD_ACCEPTANCE'
        record['exit_code'] = 0
    except BaseException as error:
        record.update(status='EXISTING_FAIR_LPIPS_CPU_FAILED_DENOMINATOR_PRESERVED',
                      error_type=type(error).__name__, error=str(error), exit_code=1)
        raise
    finally:
        after = {path: sha(path) for path in protected}
        record.update(protected_file_sha256_after=after, original_videos_and_budget_unchanged=before==after,
                      CUDA_initialized=torch.cuda.is_initialized(), CPU_wall_seconds=time.perf_counter()-tick,
                      ended_unix=time.time())
        save()
        assert before == after and not torch.cuda.is_initialized()
    print(json.dumps({'status': record['status'], 'CPU_wall_seconds': record['CPU_wall_seconds']}), flush=True)


if __name__ == '__main__':
    main()
