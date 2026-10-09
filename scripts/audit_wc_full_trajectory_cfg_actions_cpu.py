#!/usr/bin/env python3
"""Read every completed native parent CFG pair; no models, GPU, or budget writes."""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import time


PREREG = Path('manifests/wc_full_trajectory_cfg_actions_cpu_r1_preregistration_20261009.json')
OUTPUT = Path('reports/wc_full_trajectory_cfg_actions_cpu_r1_20261009.json')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    assert not OUTPUT.exists()
    p = json.loads(PREREG.read_text())
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    assert subprocess.check_output(['git', 'show', revision+':'+str(PREREG)]) == PREREG.read_bytes()
    assert subprocess.check_output(['git', 'show', revision+':scripts/audit_wc_full_trajectory_cfg_actions_cpu.py']) == Path(__file__).read_bytes()
    start = time.perf_counter(); rows = []; parents = []; evidence = []
    for source in p['completed_sources']:
        objects = {}
        capture_path = Path(source['files']['capture']['path'])
        for key, item in source['files'].items():
            path = Path(item['path']); compressed = path.read_bytes()
            assert sha(compressed) == item['sha256'], str(path)
            raw = gzip.decompress(compressed) if path.suffix == '.gz' else compressed
            objects[key] = json.loads(raw)
            evidence.append({'path': str(path), 'bytes': len(compressed), 'sha256': sha(compressed), 'native_SHA': sha(raw)})
        capture, runner, score, supervisor = (objects[k] for k in ('capture', 'runner', 'CPU_score', 'supervisor'))
        assert capture['status'] == 'TEACHER_ORIGINAL_TERMINAL_NATIVE_CAPTURE_SUCCESS'
        assert capture['GPU_exit_code'] == capture['CPU_exit_code'] == supervisor['exit_code'] == 0
        assert runner['run_id'] == supervisor['run_id'] == capture['run_id'] == source['run_id']
        assert runner['source_revision'] == supervisor['source_revision'] == capture['source_revision']
        for key in ('runner', 'CPU_score', 'supervisor'):
            raw = gzip.decompress(Path(source['files'][key]['path']).read_bytes())
            assert sha(raw) == capture['files'][key]['sha256']
        assert score['local_CFG_pairs'] == 40 and score['raw_tensor_count'] == 120 and score['strict_repeat_groups'] == 20
        assert not score['CUDA_initialized'] and len(score['videos']) == 2
        assert runner['status'] == 'TEACHER_GPU_COMPLETE_REQUIRES_CPU_RAW_AUDIT_AND_LOCAL_SCORING'
        off, on = runner['teacher']['parents']
        assert off['phase'] == 'OFF' and on['phase'] == 'ON'
        for key in ('inputs', 'outputs', 'deep', 'banks', 'solver_outputs', 'final_latent_sha256', 'final_components', 'final_solver_configuration', 'sample_return_sha256', 'pipeline'):
            assert off[key] == on[key], (source['run_id'], key)
        assert off['artifact']['sha256'] == on['artifact']['sha256']
        for parent in (off, on):
            assert parent['status'] == 'COMPLETE_PARENT'
            assert all(len(parent[k]) == 72 for k in ('inputs', 'outputs', 'deep', 'banks'))
            assert len(parent['solver_outputs']) == 36
            phase_rows = []
            for step in range(1, 37):
                deep = parent['deep'][2*(step-1):2*step]
                assert all(type(x) is int and x in (0, 26) for x in deep), (source['run_id'], step, deep)
                mode = ''.join('D' if x else 'C' for x in deep)
                full = sum(x != 0 for x in deep)
                row = {'run_id': source['run_id'], 'sample_name': runner['config']['sample_names'][0], 'phase': parent['phase'],
                       'solver_step': step, 'original_calls': [2*step-1, 2*step], 'actual_deep_blocks': deep,
                       'actual_original_mode': mode, 'actual_original_full_calls': full,
                       'CC_DD_only_executor_covers_fixed_action': mode in ('CC', 'DD'),
                       'frozen_mask_OR_mode': 'DD' if full else 'CC',
                       'frozen_mask_OR_full_calls': 2 if full else 0,
                       'frozen_mask_OR_additional_full_calls': (2 if full else 0)-full,
                       'counterfactual_future_actions_or_cost_measured': False}
                rows.append(row); phase_rows.append(row)
            tally = {mode: sum(r['actual_original_mode'] == mode for r in phase_rows) for mode in ('CC', 'DC', 'CD', 'DD')}
            parents.append({'run_id': source['run_id'], 'phase': parent['phase'], 'actual_parent_full_calls': sum(r['actual_original_full_calls'] for r in phase_rows),
                            'actual_parent_cache_calls': 72-sum(r['actual_original_full_calls'] for r in phase_rows),
                            'complete_36_pair_tally': tally, 'mixed_pairs': tally['DC']+tally['CD'],
                            'frozen_mask_OR_additional_full_calls': sum(r['frozen_mask_OR_additional_full_calls'] for r in phase_rows)})
    assert len(rows) == p['scope']['complete_CFG_pairs'] == 216 and len(parents) == p['scope']['full_parents'] == 6
    result = {'status': 'COMPLETE_OLD_FULL_TRAJECTORY_CFG_ACTION_ALIGNMENT_CPU_NOT_POLICY_RESULT',
              'source_revision': revision, 'preregistration_sha256': sha(PREREG.read_bytes()), 'scope': p['scope'],
              'input_evidence': evidence, 'parents': parents, 'complete_pair_rows': rows,
              'all_three_complete_36_update_masks_are_CC_DD_only': all(r['CC_DD_only_executor_covers_fixed_action'] for r in rows),
              'exposed_trajectories': 3, 'unique_trajectory_positions': 108, 'independent_scene_samples': False,
              'GPU_submissions': 0, 'Torch_loaded': False, 'budget_written': False,
              'endpoint_labels': 0, 'future_cost_labels': 0, 'new_policy_full_calls_prediction': False,
              'CPU_wall_seconds': time.perf_counter()-start}
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: result[k] for k in ('status', 'source_revision', 'scope', 'parents', 'all_three_complete_36_update_masks_are_CC_DD_only', 'CPU_wall_seconds')}))


if __name__ == '__main__':
    main()
