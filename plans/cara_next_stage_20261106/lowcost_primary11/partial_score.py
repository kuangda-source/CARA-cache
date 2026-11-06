"""Authorized four-pair C06 CPU scoring; never accepts the failed nine-input run."""
import argparse
import hashlib
import json
import os
from pathlib import Path


def selected_rows(card, collection):
    if (collection['run_id'] != card['run_id']
            or collection['scope_sha256'] != card['scope_sha256']
            or collection['status'] != 'FAILED_NO_RETRY'):
        raise ValueError('The original failed continuation is required')
    member = card['inputs_by_alias']['C06']
    rows = [r for r in collection['rows'] if r['slot']['member'] == member]
    if (len(rows) != 5 or any(r['status'] != 'COMPLETE' for r in rows)
            or [r['slot']['id'] for r in rows] != [f'CONFIRM10_{i:03d}' for i in range(27, 32)]
            or {r['slot']['role'] for r in rows} != set(card['roles'])):
        raise ValueError('Exactly the five completed original C06 arms are required')
    return rows


def main():
    p = argparse.ArgumentParser()
    for name in ('manifest', 'collection', 'release', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError('Recover the original partial scorer; never replay')
    if hashlib.sha256(a.collection.read_bytes()).hexdigest() != '0357504fde26cabe331820e09a12ccea8bbb9ff6b620ac6ac09c51f136b028b8':
        raise ValueError('Original failed collection bytes changed')
    card = json.loads(a.manifest.read_text())
    release = json.loads(a.release.read_text())
    if not all(release[k] for k in ('cost_settled', 'GPU_released', 'mode_restored', 'original_processes_ended')):
        raise ValueError('Partial scoring requires settled original resource closure')
    if (release['launch_id'] != 'e6d9ad460313484caa8f10a9b842e387'
            or card['run_id'] != 'cara-generator-v1-confirm10-continuation-r1-20261106'):
        raise ValueError('Exact failed continuation identity required')
    if os.environ['CUDA_VISIBLE_DEVICES'] != '' or os.environ['NVIDIA_VISIBLE_DEVICES'] != 'void':
        raise ValueError('CPU-only partial scorer required')
    rows = selected_rows(card, json.loads(a.collection.read_text()))
    native = next(r for r in rows if r['slot']['role'] == 'NATIVE35')
    import torch
    import lpips
    from wcomr.cara_fast_fidelity_r1 import score_video_pair
    from wcomr.gpu_budget_pool_v2 import atomic_json
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    def forbidden(*args, **kwargs):
        raise RuntimeError('Partial scoring forbids CUDA and downloads')
    torch.cuda._lazy_init = forbidden
    torch.hub.download_url_to_file = forbidden
    alex = lpips.LPIPS(net='alex', version='0.1', verbose=False).cpu().eval()
    state = dict(status='PARTIAL_SCORING', run_id=card['run_id'], scope_sha256=card['scope_sha256'],
        complete_members=[native['slot']['member']], native_T_DD={native['slot']['member']: native['result']['T_DD']},
        rows=[], release=release, whole_run_success=False, nine_input_endpoint='NOT_EVALUABLE',
        original_ten_input_endpoint='NOT_EVALUABLE', GPU_submissions=0)
    atomic_json(a.output, state)
    for row in rows:
        slot = row['slot']
        if slot['role'] == 'NATIVE35':
            continue
        fidelity = score_video_pair(row['result']['video_artifact'], native['result']['video_artifact'], alex)
        actions = ''.join(x['actual'] for x in row['result']['semantic_history'])
        expected = ''.join(card['roles'][slot['role']]['policy']['actions'])
        if actions != expected:
            raise ValueError('Executed mask differs from the frozen C06 mask')
        state['rows'].append(dict(slot=slot, Alex=fidelity['Alex'], T_DD=row['result']['T_DD'],
            fidelity=fidelity, mask_matches=True))
        atomic_json(a.output, state)
    state.update(status='PARTIAL_SCORES_COMPLETE', CUDA_initialized=torch.cuda.is_initialized())
    atomic_json(a.output, state)


if __name__ == '__main__':
    main()
