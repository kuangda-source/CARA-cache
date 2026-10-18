#!/usr/bin/env python3
"""CPU-only audit of every scout original, with refusals and failures retained."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for n in ('project', 'stage'): p.add_argument('--'+n, type=Path, required=True)
    a = p.parse_args(); os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
        TORCH_HOME='/home/gaokuangda/.cache/torch', OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    sys.path.insert(0, str(a.stage/'src'))
    from wcomr.scout_gpu_lifecycle_r1 import bound_dependency, read, sha, counts, RUNS, VECTORS, audit_registered_rows, repeat_and_prefix
    from wcomr.gpu_budget_pool_v2 import BudgetPool, atomic_json, same_live_process
    meta, c, reg, cap, accepted = bound_dependency(a.project, a.stage)
    kind = c['kind']; root = (a.project/'outputs'/RUNS[kind]).resolve(); sup = read(root/'supervisor.json')
    assert sup['status'] == 'SCOUT_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
    assert not any(same_live_process(x) for x in (sup['supervisor_identity'], sup.get('child_identity')) if x)
    runner = read(root/'runner.json') if (root/'runner.json').exists() else dict(runs=[])
    assert not sup.get('runner_sha256') or sha(root/'runner.json') == sup['runner_sha256']
    from wcomr.scout_sampling_r1 import matrix
    planned = matrix(kind, [r['name'] for r in c['requests']]); actual = {r['id']: r for r in runner['runs']}
    assert len(actual) == len(runner['runs']) and set(actual) <= {r['id'] for r in planned}
    rows = [dict(actual.get(r['id'], dict(r, status='NOT_REACHED_RETAINED'))) for r in planned]
    before = BudgetPool(a.project).read(); started = time.perf_counter()
    result = dict(status='SCOUT_ALL_ORIGINALS_CPU_AUDIT_RUNNING', kind=kind, scope_counts=counts(kind), rows=rows,
        lifecycle_source_revision=reg['source_revision'], execution_source_revision=meta['entry_source_revision'],
        registration_sha256=sha(a.stage/'registration.json'), entry_registration_sha256=meta['entry_registration_sha256'],
        GPU_submissions=0, ledger_written=False, CUDA_initialized=False, row_failures=[], reference_failures=[],
        timing_claim=c['timing_claim'], diagnostic_not_clean_latency=True)
    target = a.stage/'CPU-final-results.json'; save = lambda: atomic_json(target, result); save()
    import torch
    torch.set_num_threads(2)
    def forbidden(*args, **kwargs): raise RuntimeError('Scout CPU post prohibits CUDA/download')
    torch.cuda._lazy_init = forbidden; torch.hub.download_url_to_file = forbidden
    from wcomr.mid_coverage import tree_digest
    from wcomr.rv0_video_reader import probe_video, decoded_video

    def asset(info):
        path = Path(info['path']).resolve()
        assert path.is_relative_to(root) and sha(path) == info['sha256'] and path.stat().st_size == info['bytes']
        return path

    def decode(path):
        info = probe_video(path); digest = hashlib.sha256(); n = 0
        with decoded_video(path) as stream:
            for frame, pts, base in stream: digest.update(frame.tobytes()); n += 1
        assert n == 93 and info['HWC'] == [432, 768, 3]
        return dict(frames=n, probe=info, RGB_sha256=digest.hexdigest())

    def probe_delta(vectors):
        values = [vectors[k].reshape(-1) for k in VECTORS[:4]]
        assert len({tuple(vectors[k].shape) for k in VECTORS[:4]}) == 1
        total = 0.; n = values[0].numel()
        for i in range(0, n, 1048576):
            p20c, p20u, p21c, p21u = [v[i:i+1048576].double() for v in values]
            total += float((8*(p21c-p20c)-7*(p21u-p20u)).square().sum())
        return dict(guided_probe_delta_RMS=(total/n)**.5, squared_sum=total, elements=n,
                    definition='RMS(8*(p21c-p20c)-7*(p21u-p20u))', current_teacher_used=False)

    for row, plan in zip(rows, planned):
        if row['status'] not in ('COMPLETE', 'VIDEO_REJECTED'): save(); continue
        try:
            # Audit semantics before loading any potentially large tensor.
            scratch = [dict(r, status='NOT_REACHED_RETAINED') for r in planned]
            scratch[planned.index(plan)] = row; audit_registered_rows(c, scratch)
            final = torch.load(asset(row['final_artifact']), map_location='cpu', weights_only=True)['final_latent']
            assert list(final.shape) == [1, 16, 24, 54, 96] and bool(torch.isfinite(final).all())
            assert tree_digest(final) == row['final_latent_sha256']; del final
            if plan['section'] == 'WARMUP':
                guides = torch.load(asset(row['warm_guided_artifact']), map_location='cpu', weights_only=True)['guided']
                assert len(guides) == 36 and tree_digest(guides) == row['warm_guided_tree_sha256']
                assert all(list(g.shape) == [1, 16, 24, 54, 96] and bool(torch.isfinite(g).all()) for g in guides)
                row['guided_step_sha256'] = [tree_digest(g) for g in guides]; del guides
            if plan['observer']:
                vectors = torch.load(asset(row['scout_vectors_artifact']), map_location='cpu', weights_only=True)
                assert set(vectors) == set(VECTORS) and set(row['scout_vector_metadata']) == set(VECTORS)
                actualmeta = {}
                for k, v in vectors.items():
                    assert v.device.type == 'cpu' and v.is_floating_point() and bool(torch.isfinite(v).all())
                    actualmeta[k] = dict(shape=list(v.shape), dtype=str(v.dtype), tree_sha256=tree_digest(v))
                assert actualmeta == row['scout_vector_metadata']
                assert all(list(vectors[k].shape) == [1, 16, 24, 54, 96] for k in VECTORS[4:])
                if plan['method'] in ('D21', 'G01_LATE_A', 'VARIATION26_C'):
                    assert torch.equal(vectors['v_actual21'], vectors['v_returned21'])
                row.update(vector_audit='PASS', visible_probe_delta=probe_delta(vectors)); del vectors
            row['raw_model_audit'] = 'PASS'
            if row['status'] == 'VIDEO_REJECTED': row['endpoint_audit'] = 'PASS_REJECTED_VIDEO_RETAINED'; save(); continue
            path = Path(row['video_path']).resolve(); assert path.is_relative_to(root)
            row.update(video_artifact=dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size),
                       decoded_video=decode(path), endpoint_audit='PASS')
        except Exception as error:
            row.update(endpoint_audit='AUDIT_FAILURE', audit_error_type=type(error).__name__, audit_error=str(error))
            result['row_failures'].append(dict(id=row['id'], error_type=type(error).__name__, error=str(error)))
        save()
    try:
        result.update(repeat_and_prefix(c, rows))
    except Exception as error:
        result['control_failure'] = dict(error_type=type(error).__name__, error=str(error))
    # CAL uses pinned old Native originals. BANK uses only its own newly generated
    # matching Native references; unavailable references never become zero scores.
    references = []
    if kind == 'BANK24':
        references = [r for r in rows if r['section'] == 'TIMED' and r['method'] == 'NATIVE35' and r.get('endpoint_audit') == 'PASS']
    else:
        from wcomr.scout_production_entry_r1 import read as reference
        wc = reference(Path(meta['entry_stage']), c, 'window_config')
        baseline = read(Path(meta['entry_stage'])/wc['references']['baseline']['ref'])
        assert sha(Path(meta['entry_stage'])/wc['references']['baseline']['ref']) == wc['references']['baseline']['sha256']
        for old in baseline['rows']:
            if old['method'] != 'NATIVE': continue
            try:
                path = Path(old['video_artifact']['path']); assert sha(path) == old['video_artifact']['sha256']
                assert path.stat().st_size == old['video_artifact']['bytes']
                assert decode(path) == old['decoded_video']; references.append(old)
            except Exception as error:
                result['reference_failures'].append(dict(scene=old['scene'], error_type=type(error).__name__, error=str(error)))
    result['Native_reference_bindings'] = [dict(scene=r['scene'], video_artifact=r['video_artifact'], decoded_video=r['decoded_video']) for r in references]
    eligible = [r for r in rows if r['section'] == 'TIMED' and r['method'] != 'NATIVE35' and r.get('endpoint_audit') == 'PASS']
    if eligible and references:
        from wcomr.lpips_resource_identity import audit
        resource = a.project/'.sync/wc-rv0-lpips-resource-v2'
        result['LPIPS_resource_identity'] = audit(resource, sha(a.stage/'src/wcomr/rv0_lpips.py'))
        sys.path.insert(0, str(resource/'site')); import lpips
        assert importlib.metadata.version('lpips') == '0.1.4' and Path(lpips.__file__).resolve() == (resource/'site/lpips/__init__.py').resolve()
        metric = lpips.LPIPS(net='alex', version='0.1', spatial=False, verbose=False).cpu().eval()
        for parameter in metric.parameters(): parameter.requires_grad_(False)
        from wcomr.rv0_lpips import score_pair
        for row in eligible:
            ref = next((r for r in references if r['scene'] == row['scene']), None)
            if ref is None: row['LPIPS_missing_reason'] = 'MATCHING_NATIVE_UNAVAILABLE_RETAINED'; save(); continue
            try:
                with decoded_video(ref['video_artifact']['path']) as left, decoded_video(row['video_path']) as right:
                    row['LPIPS'] = score_pair(left, right, metric, reference_sha256=ref['video_artifact']['sha256'],
                                             candidate_sha256=row['video_artifact']['sha256'])
            except Exception as error:
                row['LPIPS_audit_failure'] = dict(error_type=type(error).__name__, error=str(error))
            save()
        del metric
    # Bind all old endpoints and warm prefixes without rerunning old video paths.
    if kind == 'CAL12':
        result['old_CAL_bindings'] = []
        wc = read(Path(meta['entry_stage'])/c['references']['window_config']['ref'])
        old = read(Path(meta['entry_stage'])/wc['references']['old_capture']['ref'])
        assert sha(Path(meta['entry_stage'])/wc['references']['old_capture']['ref']) == wc['references']['old_capture']['sha256']
        oldrows = old['final']['rows']
        for r in oldrows:
            if r['section'] != 'TIMED': continue
            result['old_CAL_bindings'].append(dict(scene=r['scene'], method=r['method'], final_artifact=r['final_artifact'],
                video_artifact=r['video_artifact'], final_latent_sha256=r['final_latent_sha256'], decoded_video=r['decoded_video'],
                LPIPS=r['LPIPS'], actions=r['actions'], A_history=r['A_history']))
        result['old_prefix_controls'] = []
        for m, oldm, n in [('G01_LATE_A', 'S25-C', 21), ('VARIATION26_C', 'S26-C', 21)]:
            oldwarm = next(r for r in oldrows if r['section'] == 'WARMUP' and r['method'] == oldm and r['round'] == 1)
            asset0 = oldwarm['warm_guided_artifact']; path = Path(asset0['path'])
            assert sha(path) == asset0['sha256'] and path.stat().st_size == asset0['bytes']
            values = torch.load(path, map_location='cpu', weights_only=True)['guided']
            assert tree_digest(values) == oldwarm['warm_guided_tree_sha256']
            hashes = [tree_digest(v) for v in values]; del values
            current = next(r for r in rows if r['id'] == 'warm_1_'+m)
            status = 'UNAVAILABLE_RETAINED'
            if current.get('guided_step_sha256'):
                assert current['guided_step_sha256'][:n] == hashes[:n]; status = 'PASS_OLD_COMMON_PREFIX'
            result['old_prefix_controls'].append(dict(method=m, old_method=oldm, compared_outputs=n, status=status,
                old_artifact=asset0, old_guided_step_sha256=hashes))
    memory = runner.get('request_memory_records', [])
    assert memory == [dict(id=r['id'], **r['request_memory_lifecycle']) for r in runner['runs'] if 'request_memory_lifecycle' in r]
    result.update(status='SCOUT_FULL_SCOPE_POST_TERMINAL_FAILURES_RETAINED', CPU_wall_seconds=time.perf_counter()-started,
        original_runner_paths=len(runner['runs']), request_memory_records=memory,
        accepted_video_paths=sum(r.get('endpoint_audit') == 'PASS' for r in rows),
        scored_formal_paths=sum('LPIPS' in r for r in rows), pool_before=before, pool_after=BudgetPool(a.project).read())
    assert result['pool_after']['jobs'][RUNS[kind]] == before['jobs'][RUNS[kind]] and not torch.cuda.is_initialized()
    save()


if __name__ == '__main__': main()
