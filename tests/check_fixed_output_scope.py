"""Pure identity, full cost, budget and real exposed-mask rejection controls."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile

from wcomr.fixed_output_scope import validate_scope, validate_mask, cost_gate, budget_gate


def run(config, root, stage=None):
    root = Path(root)
    stage = Path(stage) if stage is not None else root
    validate_scope(config);cost_gate(config)
    budget = {'used_gpu_hours': 7.407626319933526, 'cap_gpu_hours': 12,
              'budget_authorization_ref': 'manifests/budget_authorization_20261003.json'}
    budget_gate(budget, 1800)
    checks = ['scope_and_complete_cost', 'current_cumulative12_budget']
    changes = [('planned_output_files', 3), ('sample_names', ['common']),
               ('max_gpu_wall_seconds', 6000), ('online_policy', True),
               ('teacher_trace_used_offline', False), ('fixed_deep_CFG_calls', 35)]
    for key, value in changes:
        bad = copy.deepcopy(config);bad[key] = value
        try: validate_scope(bad)
        except ValueError: pass
        else: raise AssertionError('Changed scope accepted: ' + key)
        checks.append('reject_scope_' + key)
    bad = copy.deepcopy(config)
    bad['cost_admission'] = {'planning_envelope_seconds': 1780, 'shutdown_settlement_margin_seconds': 30}
    try: cost_gate(bad)
    except ValueError: pass
    else: raise AssertionError('Incomplete1800 cost accepted')
    checks.append('reject_full_cost_over_cap')
    for change in [{'cap_gpu_hours': 4}, {'used_gpu_hours': 11.51},
                   {'used_gpu_hours': float('nan')}, {'other_inflight': {'run_id': 'other'}}]:
        try: budget_gate(dict(budget, **change), 1800)
        except ValueError: pass
        else: raise AssertionError('Bad budget accepted')
        checks.append('reject_budget_' + next(iter(change)))
    archive = root / 'reports/wc_light_output_r1_runner_20261004.json.gz'
    raw = gzip.decompress(archive.read_bytes()) if archive.exists() else (
        root / 'outputs/wc-light-output-r1/diagnostic/receipt.json').read_bytes()
    manifest = (stage / config['mask_manifest']).read_bytes()
    with tempfile.TemporaryDirectory(prefix='fixed-scope-cpu-') as tmp:
        directory = Path(tmp)
        path = directory / 'outputs/wc-light-output-r1/diagnostic/receipt.json'
        path.parent.mkdir(parents=True);path.write_bytes(raw)
        mask_path = directory / config['mask_manifest'];mask_path.parent.mkdir(parents=True)
        mask_path.write_bytes(manifest)
        row = validate_mask(config, directory, directory)
        assert sum(row['dense_calls']) == 38
        checks.append('actual_immutable_exposed_human38_mask')
        for key, value in [('dense_calls', [True] * 72), ('model_id', 'wrong'),
                           ('condition_id', 'wrong'), ('role', 'online')]:
            altered = json.loads(manifest)
            selected, = [r for r in altered['masks'] if r['sample_name'] == 'human_199']
            selected[key] = value;mask_path.write_text(json.dumps(altered))
            try: validate_mask(config, directory, directory)
            except ValueError: pass
            else: raise AssertionError('Altered actual mask accepted: ' + key)
            checks.append('reject_mask_' + key)
        mask_path.write_bytes(manifest);path.write_bytes(raw + b' ')
        try: validate_mask(config, directory, directory)
        except ValueError: pass
        else: raise AssertionError('Modified original receipt accepted')
        checks.append('reject_source_receipt_byte_change')
    return {'status': 'FIXED_FOUR_SCOPE_COST_BUDGET_ACTUAL_MASK_CPU_PASS', 'checks': checks,
        'CUDA_imported': False, 'mask_manifest_sha256': hashlib.sha256(manifest).hexdigest(),
        'original_raw_receipt_sha256': hashlib.sha256(raw).hexdigest()}
