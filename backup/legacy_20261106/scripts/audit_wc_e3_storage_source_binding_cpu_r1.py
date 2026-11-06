#!/usr/bin/env python3
"""Read the frozen method graph and prior CPU proof without importing Torch."""
import ast
import gzip
import hashlib
import json
from pathlib import Path
import time


def main():
    root = Path(__file__).resolve().parents[1]
    started = time.perf_counter()
    refs = ['configs/wc_current_birth_full64_selected_r1_20261010.json',
            'configs/wc_e1_diag8_production_r2_20261011.json',
            'manifests/wc_full64_partial_recovery_cpu_r1_20261011.json',
            'reports/wc_e1_storage_full_sampler_cpu_r1_terminal_20261011_capture.json']
    old, gpu, recovery, capture = [json.loads((root / ref).read_text()) for ref in refs]
    sha = lambda data: hashlib.sha256(data).hexdigest()
    assert sha((root / refs[0]).read_bytes()) == recovery['original_config_sha256'] == gpu['parent_config_sha256']
    assert capture['exit_code'] == 0 and capture['independent_source_complete_results_and_actual_artifact_hashes_verified']
    historical = {}
    for name in ('registration.json', 'result.json'):
        item = capture['files'][name]
        compressed = (root / item['local_path']).read_bytes()
        assert sha(compressed) == item['compressed_sha256']
        raw = gzip.decompress(compressed)
        assert len(raw) == item['bytes'] and sha(raw) == item['sha256']
        historical[name] = json.loads(raw)
        refs.append(item['local_path'])
    registration, cpu = historical['registration.json'], historical['result.json']
    assert cpu['status'] == 'CPU_STORAGE_FULL_SAMPLER_CPU_PASS_NOT_REAL_MODEL'
    assert (cpu['complete_successful_paths'], cpu['actual_all_tensors_reloaded'],
            cpu['actual_complete_solver_updates'], cpu['actual_CPU_backed_additional_roundtrips']) == (128, 4736, 9216, 896)
    assert cpu['registered_strategies'] == old['preregistration']['strategies']
    assert cpu['current_birth_rule'] == old['preregistration']['current_P_birth_rule']
    assert not cpu['CUDA_initialized'] and cpu['GPU_submissions'] == 0
    original_sources = {n: h for n, h in old['payload_sha256'].items()
                        if n.startswith('src/wcomr/') and n.endswith('.py')}
    assert len(original_sources) == 225
    assert all(sha((root / n).read_bytes()) == h for n, h in original_sources.items())
    todo = ['src/wcomr/source_aware_current_birth_sampling_r2.py',
            'src/wcomr/source_aware_CPU_storage_sampling_r1.py']
    graph = {}
    while todo:
        name = todo.pop()
        if name in graph:
            continue
        data = (root / name).read_bytes()
        graph[name] = sha(data)
        for node in ast.walk(ast.parse(data)):
            candidates = []
            if isinstance(node, ast.ImportFrom) and node.level == 1:
                candidates = ['src/wcomr/' + n + '.py' for n in
                              ([node.module] if node.module else [a.name for a in node.names])]
            if isinstance(node, ast.ImportFrom) and node.level == 0 and (node.module or '').startswith('wcomr.'):
                candidates = ['src/' + node.module.replace('.', '/') + '.py']
            if isinstance(node, ast.Import):
                candidates += ['src/' + a.name.replace('.', '/') + '.py'
                               for a in node.names if a.name.startswith('wcomr.')]
            todo.extend(n for n in candidates if (root / n).is_file())
    added = set(graph) - set(original_sources)
    assert added == {'src/wcomr/source_aware_CPU_storage_sampling_r1.py',
                     'src/wcomr/cpu_owned_state_snapshot.py'} and len(graph) == 57
    assert all(h == gpu['payload_sha256'][n] == registration['payload_sha256'][n] for n, h in graph.items())
    assert all(h == original_sources[n] for n, h in graph.items() if n not in added)
    assert all(registration['runtime_source_sha256'].get(n, h) == h for n, h in old['runtime_source_sha256'].items())
    tree = ast.parse((root / 'src/wcomr/source_aware_CPU_storage_sampling_r1.py').read_bytes())
    owner = next(node for node in tree.body if isinstance(node, ast.ClassDef))
    assert owner.name == 'CPUStorageSamplingOwner'
    assert ast.dump(owner.bases[0]) == ast.dump(ast.parse('original.CurrentBirthSamplingOwner', mode='eval').body)
    overrides = [node.name for node in owner.body if isinstance(node, ast.FunctionDef)]
    assert overrides == ['installation', 'checkpoint']
    def assigned(name):
        nodes = [node for node in tree.body if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == name for t in node.targets)]
        assert len(nodes) == 1
        return ast.dump(nodes[0].value)
    for name in ('METHODS', 'STRATEGIES', 'valid_P_interval', 'CURRENT_BIRTH_RULE',
                 'CurrentBirthDeployment', 'verify_batch', 'derive', 'audit_vectors'):
        assert assigned(name) == ast.dump(ast.parse('original.' + name, mode='eval').body)
    assert assigned('run_batch') == ast.dump(ast.parse(
        "bind_globals(original.run_batch, {'DynamicSamplingOwner': CPUStorageSamplingOwner})", mode='eval').body)
    assert assigned('CurrentBirthSamplingOwner') == ast.dump(ast.parse('CPUStorageSamplingOwner', mode='eval').body)
    installation = next(node for node in owner.body if isinstance(node, ast.FunctionDef) and node.name == 'installation')
    assert len(installation.body) == 1 and isinstance(installation.body[0], ast.Return)
    assert ast.dump(installation.body[0].value) == ast.dump(ast.parse(
        "super().installation() + ('CPU_OWNED_STORAGE_SERIAL_RESTORE_R1',)", mode='eval').body)
    result = dict(status='E3_FROZEN_METHOD_GRAPH_AND_CPU_STORAGE_DERIVATION_READONLY_PASS_NOT_GPU_CLEARANCE',
                  old_full64_source_revision=recovery['original_GPU_source_revision'],
                  original_source_files_locally_unchanged=225, reachable_method_graph_files=57,
                  reachable_original_method_files_unchanged=55, additional_storage_module_refs=sorted(added),
                  actual_GPU_and_accepted_full_CPU_graph_sha256_identical=True,
                  owner_overrides=overrides, ordinary_batch_owner_binding_only=True,
                  methods_strategies_controller_readout_and_verifier_inherited=True,
                  reused_full_CPU_source_revision=capture['source_revision'],
                  reused_full_CPU_successful_paths=128, reused_full_CPU_actual_tensors=4736,
                  reused_full_CPU_additional_roundtrips=896,
                  reused_full_CPU_strategies=cpu['registered_strategies'],
                  no_numeric_sampler_rerun=True, full_E1_actual_GPU_audit_still_required=True,
                  E3_source_selection_path_rehash_and_complete_forecast_still_required=True,
                  E3_GPU_card_not_selected=True, scientific_quality_or_clean_speed_claim=False,
                  CUDA_initialized=False, GPU_submissions=0, ledger_written=False,
                  CPU_wall_seconds=time.perf_counter() - started,
                  graph_sha256=dict(sorted(graph.items())),
                  source_sha256={n: sha((root / n).read_bytes()) for n in refs +
                                 ['scripts/audit_wc_e3_storage_source_binding_cpu_r1.py']})
    target = root / 'reports/wc_e3_storage_source_binding_readonly_cpu_r1_20261011.json'
    assert not target.exists()
    target.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'reachable_method_graph_files',
                                            'reachable_original_method_files_unchanged', 'CPU_wall_seconds', 'GPU_submissions')}))


if __name__ == '__main__':
    main()
