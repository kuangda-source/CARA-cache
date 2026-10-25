#!/usr/bin/env python3
"""Merge the repaired real-request evidence with unchanged CPU components.

Offline only. This does not register a GPU stage, reserve budget or launch work.
The historical entry acceptance is explicitly superseded, never reused as proof
of the frozen-request seam.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from audit_cara_cal66_entry_cpu_r2 import accept as accept_entry
from audit_cara_cal66_preparation_r1 import audit as historical_components
from wcomr.immutable_stage_payload_r1 import local_python_closure
from wcomr.policy_generator_r1.shared66_card import check_card, MANIFEST, digest

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def audit(capture_path, accepted_path, quote_path):
    capture, accepted, quote = map(read, (capture_path, accepted_path, quote_path))
    replay = accept_entry(capture)
    assert all(accepted[k] == v for k, v in replay.items())
    assert accepted['capture_sha256'] == sha(capture_path)
    historical, binding = historical_components()
    old = read(ROOT / historical['source_receipts']['combination']['acceptance_ref'])
    old_sources = old['execution_source_sha256']
    entries = ['scripts/run_cara_shared66_r1.py', 'scripts/postprocess_cara_shared66_r1.py',
               'scripts/wc_cara_shared66_worker_r1.py', 'scripts/wc_cara_shared66_host_guardian_r1.py',
               'src/wcomr/policy_generator_r1/shared66_terminal.py',
               'src/wcomr/policy_generator_r1/shared66_capture.py',
               'tests/check_cara_shared66_lifecycle_cpu_r1.py', 'tests/check_shared66_storage_cpu_r1.py']
    closure = local_python_closure(ROOT, entries)
    budget_port = 'src/wcomr/gpu_budget_pool_v2.py'
    # The registered SM89 port must be copied unchanged, not the local SM86 file.
    assert capture['registration']['payload_sha256'][budget_port] == old_sources[budget_port]
    closure[budget_port] = old_sources[budget_port]
    expected_changes = {'scripts/run_cara_shared66_r1.py',
                        'src/wcomr/policy_generator_r1/exploration_requests.py',
                        'src/wcomr/policy_generator_r1/frozen_request_arguments.py'}
    changed = {n for n, h in closure.items() if old_sources.get(n) != h}
    assert changed == expected_changes, ('Unvalidated component changed', changed)
    for name in expected_changes - {'scripts/run_cara_shared66_r1.py'}:
        assert closure[name] == capture['registration']['payload_sha256'][name]
    runner = (ROOT / 'scripts/run_cara_shared66_r1.py').read_text()
    calls = [n for n in ast.walk(ast.parse(runner)) if isinstance(n, ast.Call)]
    prechecks = [n.lineno for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == 'validate_slots']
    loads = [n.lineno for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == 'Inference']
    assert len(prechecks) == len(loads) == 1 and prechecks[0] < loads[0]
    card = check_card(read(ROOT / MANIFEST))
    assert sha(ROOT / MANIFEST) == quote['original_manifest_sha256']
    assert quote['scope'] == card['scope'] and quote['matrix_sha256'] == digest(card['matrix'])
    assert quote['roles_sha256'] == digest(card['roles']) and quote['arm_seconds'] == card['quote']['arm_seconds']
    generation = sum(quote['arm_seconds'][s['role']] for s in card['matrix']) / 3600
    assert abs(generation - quote['components']['all66_generation_GPUh']) < 1e-12
    finance = read(ROOT / quote['failed_cost_ref'])
    assert sha(ROOT / quote['failed_cost_ref']) == quote['failed_cost_sha256']
    assert finance['authoritative_ledger_settled'] and finance['exact_actual_GPUh'] == quote['previous_failed_GPUh']
    assert quote['components']['startup_allowance_GPUh'] >= quote['previous_failed_GPUh']
    forecast = sum(quote['components'].values()) * (1 + quote['uncertainty_margin'])
    assert abs(forecast - quote['forecast_GPUh']) < 1e-12 and forecast <= quote['billed_limit_GPUh'] == 8
    assert quote['cumulative_cap_GPUh'] == 226 and quote['deployment_absolute_seconds'] == 257.7712338712067
    assert quote['deployment_native_ratio'] == .8 and quote['post_release_CPU']['wall_limit_hours'] == 6
    assert quote['pool_snapshot']['available_gpu_hours'] >= 8
    return dict(
        status='CAL66_REPAIR_CPU_AND_COMPLETE_QUOTE_ACCEPTED_NO_GPU', observed_unix=time.time(),
        repaired_entry_capture_ref=str(capture_path), repaired_entry_capture_sha256=sha(capture_path),
        repaired_entry_acceptance_ref=str(accepted_path), repaired_entry_acceptance_sha256=sha(accepted_path),
        repaired_entry_source=capture['registration']['source_revision'],
        actual_frozen_class_source_sha256=capture['registration']['runtime_source_sha256']['cosmos_predict2/config.py'],
        frozen_request_chain_CPU_accepted=True, old_entry_acceptance_superseded=True,
        unchanged_component_source_sha256={n:h for n,h in closure.items() if n not in changed},
        repaired_source_sha256={n:closure[n] for n in sorted(changed)},
        budget_port_source='unchanged registered SM89 copy; never overwrite with local SM86 source',
        historical_component_receipts={k:v for k,v in historical['source_receipts'].items() if k != 'entry'},
        historical_bridge_and_original_quality_resources_reused=True,
        reused_lifecycle_scenarios=10, reused_storage_failure_scenarios=6,
        old_synthetic_orchestration_is_not_real_request_evidence=True,
        runner_preload_order_checked=True, real_frozen_CPU_numeric_paths=60, preload_slots=66,
        registered_paths=66, original_alpha_masks_baselines_scope_unchanged=True,
        LPIPS_pairs=48, LPIPS_frames=4464, independent_quality_positions=156,
        quality_binding_sha256=hashlib.sha256(binding).hexdigest(),
        CPU_planning=historical['CPU_planning'], quote_ref=str(quote_path), quote_sha256=sha(quote_path),
        forecast_GPUh=forecast, hard_limit_GPUh=8, cumulative_cap_GPUh=226,
        actual_full_Cosmos_GPU_inference_validated=False, GPU_submissions=0, ledger_written=False,
        GPU_dispatch_ready=False, new_GPU_authorization=False,
        pending=['user instruction to execute recovery',
                 'new R2 run/stage registration binds repaired CPU closure and separate recovery quote',
                 'fresh source/assets/empty storage/exclusive UUID/ledger admission',
                 'actual-start-based single midpoint and terminal checks'])

def main():
    p = argparse.ArgumentParser()
    for name in ('capture', 'accepted', 'quote', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args()
    value = audit(a.capture, a.accepted, a.quote)
    with a.output.open('x') as f:
        json.dump(value, f, indent=2); f.write('\n')
    print(json.dumps({k:value[k] for k in ('status','forecast_GPUh','GPU_submissions','GPU_dispatch_ready')}))

if __name__ == '__main__':
    main()
