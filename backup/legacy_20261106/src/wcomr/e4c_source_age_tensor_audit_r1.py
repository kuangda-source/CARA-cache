"""Reload every diagnostic tensor and independently reconstruct guided error."""
import hashlib
import math
from pathlib import Path

import torch

from .mid_coverage import tree_digest


def audit(state, root, loader, expected_shape):
    root = Path(root).resolve()
    files = []
    points = []
    comparisons = 0
    count = 0

    def read(art):
        nonlocal count
        path = Path(art['path']).resolve()
        if not path.is_relative_to(root) or path.suffix != '.pt':
            raise ValueError('Diagnostic artifact outside bound root')
        raw = path.read_bytes()
        if len(raw) != art['bytes'] or hashlib.sha256(raw).hexdigest() != art['sha256']:
            raise ValueError('Actual source-age artifact bytes differ')
        x = loader(path, weights_only=True, map_location='cpu')
        if {k: tree_digest(v) for k, v in x.items()} != art['tensor_sha256']:
            raise ValueError('Actual source-age tensor binding differs')
        def walk(v):
            nonlocal count
            if isinstance(v, torch.Tensor):
                if v.device.type != 'cpu' or not bool(torch.isfinite(v).all()):
                    raise ValueError('Finite CPU tensor required')
                count += 1
            elif isinstance(v, (list, tuple)):
                for z in v: walk(z)
            else:
                raise ValueError('Unexpected diagnostic tensor structure')
        for value in x.values(): walk(value)
        files.append({'path': str(path), 'sha256': art['sha256'], 'bytes': art['bytes']})
        return x

    def vectors(x, length):
        if set(x) != {'guided', 'final_latent'} or len(x['guided']) != length:
            raise ValueError('Whole guided trajectory and final latent required')
        if any(v.dtype != torch.float32 or list(v.shape) != expected_shape
               for v in x['guided'] + [x['final_latent']]):
            raise ValueError('Actual vector geometry differs')

    for request in state['requests']:
        parents = []
        for row in request['paths']:
            x = read(row['vector_artifact']); vectors(x, 36)
            if ([tree_digest(v) for v in x['guided']] != row['guided_sha256']
                    or tree_digest(x['final_latent']) != row['final_latent_sha256']):
                raise ValueError('Actual parent tensor evidence differs')
            parents.append(x)
            for event in row['origins']:
                birth = event['event']['birth_step']; repeats = []
                for branch in event['branches']:
                    y = read(branch['vector_artifact']); vectors(y, 5)
                    if ([tree_digest(v) for v in y['guided']] != branch['guided_sha256']
                            or tree_digest(y['final_latent']) != branch['final_latent_sha256']):
                        raise ValueError('Actual suffix tensor evidence differs')
                    if branch['source'] is None:
                        if not all(torch.equal(a, b) for a, b in zip(y['guided'], x['guided'][birth-1:birth+4])):
                            raise ValueError('Reloaded policy suffix differs from original parent')
                        comparisons += 5; repeats.append(y)
                    for point in branch['age_points']:
                        z = read(point['artifact'])
                        if set(z) != {'C', 'DENSE_SAME_STATE', 'candidate_latent', 'timestep'}:
                            raise ValueError('Whole actual candidate/teacher payload required')
                        values = list(z['C']) + list(z['DENSE_SAME_STATE']) + [z['candidate_latent']]
                        if (len(z['C']) != 2 or len(z['DENSE_SAME_STATE']) != 2
                                or any(v.dtype != torch.float32 or list(v.shape) != expected_shape for v in values)
                                or tree_digest(z['candidate_latent']) != point['candidate_latent_sha256']
                                or z['timestep'].tolist() != point['timestep']):
                            raise ValueError('Own-state teacher/output coordinates differ')
                        # Match the production FP32 CFG vector, independently reduce
                        # its complete tensor in FP64 without calling the score helper.
                        ec, eu = [a-b for a, b in zip(z['C'], z['DENSE_SAME_STATE'])]
                        mse = (8*ec-7*eu).double().square().mean().item()
                        branch_mse = [v.double().square().mean().item() for v in (ec, eu)]
                        saved = point['same_state_guided_moments']
                        if (not math.isclose(mse, saved['base_guided_MSE'], rel_tol=1e-12, abs_tol=1e-15)
                                or branch_mse != saved['diagnostics']['original_branch_MSE']):
                            raise ValueError('Independent actual guided error differs')
                        guided = z['C'][0] + 7*(z['C'][0]-z['C'][1])
                        if not torch.equal(guided, y['guided'][point['age']]):
                            raise ValueError('C readout differs from actual candidate rollout')
                        comparisons += 1
                        points.append({'event': event['event']['id'], 'source': branch['source'],
                            'age': point['age'], 'guided_MSE': mse, 'branch_MSE': branch_mse})
                if len(repeats) != 2 or not all(torch.equal(a, b) for a, b in zip(
                        repeats[0]['guided'] + [repeats[0]['final_latent']],
                        repeats[1]['guided'] + [repeats[1]['final_latent']])):
                    raise ValueError('Actual repeated policy suffix differs')
                comparisons += 6
        if len(parents) != 2 or not all(torch.equal(a, b) for a, b in zip(
                parents[0]['guided']+[parents[0]['final_latent']], parents[1]['guided']+[parents[1]['final_latent']])):
            raise ValueError('Actual OFF/ON parent tensors differ')
        comparisons += 37
    paths = {str(p.resolve()) for p in root.rglob('*.pt')}
    if (paths != {f['path'] for f in files} or len(files) != 44 or count != 388 or len(points) != 24):
        raise ValueError('Complete44 files/388 tensors/24 points required')
    return {'files': files, 'actual_tensors_reloaded': count, 'actual_age_points_reduced': points,
        'actual_direct_tensor_comparisons': comparisons, 'complete_artifact_set': True,
        'real_GPU_or_video_or_quality_claim': False}
