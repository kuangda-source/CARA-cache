"""Fresh terminal audit of both serialized CPU fusion arms, with durable stages."""
import argparse
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--code-root', type=Path, required=True)
    parser.add_argument('--job', type=Path, required=True)
    parser.add_argument('--base', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Use empty CUDA visibility')
    require(not args.output.exists(), 'Choose a new audit receipt identity')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    result = {'pid': os.getpid(), 'started_unix': time.time(), 'status': 'STARTED',
              'gpu_workload_started': False, 'arms': [],
              'scope': 'Fresh official input digests, serialized tensors and untouched weights. Runner formula evidence retained; no model/task/GPU acceptance.'}

    def save():
        temp = args.output.with_suffix('.tmp')
        temp.write_text(json.dumps(result, indent=2) + '\n')
        temp.replace(args.output)

    save()
    try:
        lock = (args.project / '.sync/l0-fusion.lock').open('a')
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        supervisor_path = args.job / 'supervisor.json'
        supervisor_bytes = supervisor_path.read_bytes()
        supervisor = json.loads(supervisor_bytes)
        require(supervisor['exit_code'] == 0 and supervisor['status'] == 'CPU_FUSION_EXIT0_REQUIRES_FULL_ARTIFACT_AUDIT', 'Fusion supervisor is not cleanly terminal')
        require(supervisor['source_hashes_match_after'] and supervisor['budget_unchanged'], 'Supervisor source/accounting audit failed')
        for name, want in supervisor['source_sha256'].items():
            require(hashlib.sha256((args.code_root / name).read_bytes()).hexdigest() == want, 'Fusion source differs: ' + name)
        protocol_path = args.code_root / 'manifests/l0_cpu_fusion_protocol_20261001.json'
        protocol = json.loads(protocol_path.read_text())
        models = Path(supervisor['model_output'])
        fusion_path = models / 'fusion.json'
        fusion_bytes = fusion_path.read_bytes()
        fusion = json.loads(fusion_bytes)
        original_pids = [supervisor['pid'], supervisor['child_pid'], fusion['pid']]
        require(all(not Path('/proc/%d/cmdline' % p).exists() for p in original_pids), 'Original fusion process still exists')
        require(fusion['status'] == 'CPU_FUSION_COMPLETE_NOT_MODEL_LOAD_TASK_OR_GPU_READY' and not fusion['cuda_initialized'], 'Full CPU fusion receipt is incomplete')
        require(json.loads((args.project / 'reports/budget.json').read_text()) == supervisor['budget_before'] == supervisor['budget_after'], 'GPU ledger changed')
        from wcomr.lora_cpu_fusion import check_file, file_hash, tensor_hash
        from wcomr.lora_header_audit import audit_adapter, validate_tensor_table
        require(file_hash(protocol_path) == fusion['protocol_sha256'], 'Protocol digest differs')
        require(file_hash(args.code_root / 'public/merge_lora.py') == fusion['upstream_sha256'] == protocol['upstream_sha256'], 'Pinned upstream merger digest differs')
        result.update(status='FRESH_INPUT_HASH_AUDIT', original_pids=original_pids,
                      all_original_pids_absent=True, cpu_lock_free_before_audit=True,
                      source_commit=supervisor['source_commit'], source_hashes_match=True,
                      supervisor_sha256=hashlib.sha256(supervisor_bytes).hexdigest(),
                      fusion_receipt_sha256=hashlib.sha256(fusion_bytes).hexdigest(),
                      cpu_fusion_wall_seconds=supervisor['wall_seconds'],
                      child_ru_maxrss_kib=supervisor['child_ru_maxrss_kib'])
        save()
        records = [check_file(args.base / row['path'], row) for row in protocol['base_files']]
        snapshots = {}
        for name, row in protocol['adapters'].items():
            snapshot = args.cache / ('models--' + row['repo'].replace('/', '--')) / 'snapshots' / row['revision']
            snapshots[name] = snapshot
            records.extend(check_file(snapshot / f['path'], f) for f in row['files'])
        require(records == fusion['input_integrity'] == fusion['input_integrity_after'], 'Fresh input digests differ from before/after fusion')
        index = json.loads((args.base / protocol['index']).read_text())
        base_headers = {}
        for filename in protocol['shards']:
            path = args.base / filename
            with path.open('rb') as stream:
                length = int.from_bytes(stream.read(8), 'little')
                header = json.loads(stream.read(length))
            entries = validate_tensor_table(header, path.stat().st_size - 8 - length)
            require(not base_headers.keys() & entries.keys(), 'Duplicate base tensor')
            require(all(index['weight_map'].get(k) == filename for k in entries), 'Base index differs')
            base_headers.update(entries)
        require(len(base_headers) == 825 and set(base_headers) == set(index['weight_map']), 'Full base coverage differs')
        targets = {}
        for name, snapshot in snapshots.items():
            path = snapshot / 'adapter_model.safetensors'
            with path.open('rb') as stream:
                length = int.from_bytes(stream.read(8), 'little')
                header = json.loads(stream.read(length))
            audit = audit_adapter(header, length, path.stat().st_size,
                                  json.loads((snapshot / 'adapter_config.json').read_text()), base_headers, 1.)
            targets[name] = {r['target'] for r in audit['targets']}
            require(len(targets[name]) == 300, 'Full adapter target coverage differs')
        result.update(status='FRESH_SERIALIZED_TENSOR_AUDIT', fresh_input_integrity=records)
        save()
        import torch
        from safetensors import safe_open
        require(not torch.cuda.is_initialized(), 'Unexpected CUDA initialization')
        torch.set_num_threads(protocol['cpu_threads'])
        require(len(fusion['arms']) == len(protocol['recipes']) == 2, 'Two-arm coverage differs')
        with torch.inference_mode():
            for arm, recipe in zip(fusion['arms'], protocol['recipes']):
                require(arm['name'] == recipe['name'] and arm['recipe'] == recipe['adapters'], 'Arm recipe or order differs')
                require(arm['status'] == 'FULL_CPU_FUSION_SERIALIZATION_AND_UNTARGETED_INVARIANCE_PASS', 'Arm is incomplete')
                want_targets = set().union(*(targets[r['name']] for r in recipe['adapters']))
                require(arm['target_count'] == len(want_targets) == 300, 'Arm target coverage differs')
                rows = {r['key']: r for r in arm['tensors']}
                require(len(rows) == len(arm['tensors']) == 825 and set(rows) == set(base_headers), 'Arm tensor records are incomplete/duplicated')
                require(len(arm['shards']) == len(protocol['shards']) == 3, 'Arm shard records incomplete')
                directory = models / arm['name']
                summary = {'name': arm['name'], 'tensor_count': 0, 'target_count': 300,
                           'untargeted_count': 0, 'target_bytes_changed_count': 0,
                           'max_runner_formula_abs_error': 0., 'shards': []}
                for shard, filename in zip(arm['shards'], protocol['shards']):
                    path = directory / filename
                    require(path.is_file() and not path.is_symlink() and Path(shard['path']).resolve() == path.resolve(), 'Serialized shard path differs')
                    require(path.stat().st_size == shard['bytes'] and file_hash(path) == shard['sha256'], 'Fresh serialized shard digest differs')
                    with safe_open(str(path), framework='pt', device='cpu') as saved, safe_open(str(args.base / filename), framework='pt', device='cpu') as original:
                        require(set(saved.keys()) == set(original.keys()), 'Serialized key coverage differs')
                        for key in saved.keys():
                            tensor = saved.get_tensor(key)
                            row = rows[key]
                            require(tensor.device.type == 'cpu' and torch.isfinite(tensor).all(), 'Nonfinite or non-CPU serialized tensor')
                            require(list(tensor.shape) == row['shape'] == base_headers[key]['shape'] and str(tensor.dtype) == row['dtype'], 'Serialized tensor layout differs')
                            expected_dtype = {'F64': torch.float64, 'F32': torch.float32,
                                              'F16': torch.float16, 'BF16': torch.bfloat16}[base_headers[key]['dtype']]
                            require(tensor.dtype == expected_dtype, 'Original base dtype was not preserved')
                            require(tensor_hash(tensor) == row['after_sha256'], 'Fresh serialized tensor digest differs')
                            target = key in want_targets
                            require(row['adapter_target'] == target and row['bytes_changed'] == (row['before_sha256'] != row['after_sha256']), 'Target/change bookkeeping differs')
                            if target:
                                error = row['max_formula_abs_error']
                                require(math.isfinite(error) and error >= 0 and math.isfinite(row['relative_delta_norm']) and row['relative_delta_norm'] >= 0, 'Invalid runner formula record')
                                summary['max_runner_formula_abs_error'] = max(summary['max_runner_formula_abs_error'], error)
                                summary['target_bytes_changed_count'] += int(row['bytes_changed'])
                            else:
                                require(not row['bytes_changed'] and tensor_hash(original.get_tensor(key)) == row['before_sha256'] == row['after_sha256'], 'Fresh untouched base bytes differ')
                                summary['untargeted_count'] += 1
                            summary['tensor_count'] += 1
                            del tensor
                    summary['shards'].append(dict(shard, fresh_tensor_audit='PASS'))
                    result['current_arm'] = summary
                    save()
                require(summary['tensor_count'] == 825 and summary['untargeted_count'] == 525, 'Final per-arm coverage differs')
                require(json.loads((directory / protocol['index']).read_text()) == index, 'Saved index differs')
                require((directory / 'config.json').read_bytes() == (args.base / 'config.json').read_bytes(), 'Saved config differs')
                for relative in protocol['auxiliary_paths']:
                    path = directory / relative
                    require(path.is_symlink() and path.resolve() == (args.base / relative).resolve(), 'Auxiliary reference differs')
                summary['status'] = 'FRESH825_SERIALIZED_FINITE_DIGEST_AND525_UNTARGETED_PASS'
                result['arms'].append(summary)
                save()
        require(supervisor_path.read_bytes() == supervisor_bytes and fusion_path.read_bytes() == fusion_bytes, 'Terminal receipt changed during audit')
        for name, want in supervisor['source_sha256'].items():
            require(hashlib.sha256((args.code_root / name).read_bytes()).hexdigest() == want, 'Fusion source changed during audit')
        require(json.loads((args.project / 'reports/budget.json').read_text()) == supervisor['budget_after'], 'Ledger changed during audit')
        require(not torch.cuda.is_initialized(), 'Unexpected CUDA initialization')
        result.pop('current_arm', None)
        result.update(status='CPU_FUSION_TWO_ARMS_FRESH_FULL_ARTIFACT_AUDIT_PASS_NOT_MODEL_TASK_GPU',
                      finished_unix=time.time(), all1650_serialized_tensors_finite=True,
                      budget_unchanged=True, budget=supervisor['budget_after'], cuda_initialized=False,
                      original_input_before_after_and_fresh_digests_match=True)
        save()
        fcntl.flock(lock, fcntl.LOCK_UN)
    except BaseException as error:
        result.update(status='CPU_FUSION_ARTIFACT_AUDIT_FAILED_OR_INTERRUPTED', finished_unix=time.time(),
                      error_type=type(error).__name__, error=str(error))
        save()
        raise
    print(json.dumps({'status': result['status'], 'receipt': str(args.output)}))


if __name__ == '__main__':
    main()
