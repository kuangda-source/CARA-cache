#!/usr/bin/env python3
"""Hash-bound CPU inspection of WC/Sparge interfaces; never imports model code."""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def function(source, name, owner=None):
    tree = ast.parse(source)
    nodes = tree.body
    if owner:
        nodes = next(n for n in nodes if isinstance(n, ast.ClassDef) and n.name == owner).body
    return next(n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name)


def audit(root, sparge_dir):
    inputs = {}

    def read_json(relative):
        path = root / relative
        inputs[relative] = sha(path)
        return json.loads(path.read_text())

    meta = read_json('reports/wc_s0_checkpoint_metadata_r2_20261001.json')
    terminal = read_json('reports/wc_s0_cpu_terminal_audit_20261001.json')
    lock = read_json('manifests/wc_s0_sparge_source_lock_20261001.json')
    cal = read_json('reports/w1d_cal8_r1_runner.json')
    native = read_json('reports/f1_smoke_r3_native.json')
    require(meta['status'] == 'CPU_ACTUAL_CHECKPOINT_META_PASS_NOT_WEIGHT_LOAD_OR_FORWARD', 'metadata not accepted')
    require(meta['tensor_devices'] == ['meta'], 'not meta-only evidence')
    require(meta['torch']['cuda_initialized_before'] is False and meta['torch']['cuda_initialized_after'] is False, 'CUDA initialized')
    require(meta['budget_unchanged'] and terminal['local_remote_runtime_identical'], 'terminal evidence not accepted')
    require(inputs['reports/wc_s0_checkpoint_metadata_r2_20261001.json'] == terminal['probes']['r2']['receipt_sha256'], 'metadata receipt changed since terminal audit')
    require(all(x['pid_absent'] for x in terminal['probes'].values()), 'probe still live')
    require(sha(root / 'reports/budget.json') == terminal['budget_sha256'] == meta['budget_sha256_before'], 'budget changed')
    require(native['setup']['context_parallel_size'] == 1, 'CP>1 unsupported')

    runtime = {}
    for name, entry in meta['runtime_source'].items():
        path = root / 'cache/runtime/cosmos_predict2/_src/predict2' / name
        require(sha(path) == entry['sha256'] == terminal['runtime_hashes'][name], 'runtime source drift: ' + name)
        runtime[name] = path.read_text()
    sparse = {}
    for name, entry in lock['files'].items():
        path = sparge_dir / name
        require(path.stat().st_size == entry['bytes'] and sha(path) == entry['sha256'], 'Sparge source drift: ' + name)
        sparse[name] = path.read_text()
        if path.suffix == '.py':
            ast.parse(sparse[name])

    shapes = meta['attention_weight_shapes']
    for layer in range(28):
        for kind in ['self_attn', 'cross_attn']:
            for proj in ['q_proj', 'k_proj', 'v_proj', 'output_proj']:
                expected = [2048, 1024] if kind == 'cross_attn' and proj in ['k_proj', 'v_proj'] else [2048, 2048]
                item = shapes[f'net.blocks.{layer}.{kind}.{proj}.weight']
                require(item['shape'] == expected and item['dtype'] == 'torch.bfloat16', 'weight shape/dtype mismatch')
            for norm in ['q_norm', 'k_norm']:
                require(shapes[f'net.blocks.{layer}.{kind}.{norm}.weight']['shape'] == [128], 'head norm mismatch')

    pointer = ['cases', 0, 'on', 'shadow_records', 0, 'candidates', 'official', 'prewarp_residual', 'layout', 'shape']
    hidden = cal
    for key in pointer:
        hidden = hidden[key]
    require(hidden == [1, 24, 27, 48, 2048], 'recorded hidden layout changed')
    tokens = math.prod(hidden[1:4])
    attention = runtime['networks/minimal_v4_dit.py']
    op = runtime['networks/a2a_cp.py']
    net = runtime['configs/video2world/defaults/net.py']
    assigned = {}
    for node in ast.parse(net).body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            for target in node.targets:
                if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name) and target.value.id == 'COSMOS_V1_2B_NET_MININET':
                    assigned[target.attr] = node.value.value
    require(all(assigned.get(k) == v for k, v in {'model_channels': 2048, 'num_heads': 16, 'num_blocks': 28}.items()) and 'atten_backend="minimal_a2a"' in net, 'config contract changed')
    qkv = function(attention, 'compute_qkv', 'Attention')
    compute = function(attention, 'compute_attention', 'Attention')
    flatten = function(op, 'forward', 'MinimalA2AAttnOp')
    require('b ... (h l)' in ast.get_source_segment(op, flatten), 'dense output flatten missing')
    require('self.output_proj(result)' in ast.get_source_segment(attention, compute), 'projection boundary changed')
    require('only apply to self-attention' in ast.get_source_segment(attention, qkv), 'RoPE boundary changed')
    api = function(sparse['spas_sage_attn/core.py'], 'block_sparse_sage2_attn_cuda')
    args = [a.arg for a in api.args.args]
    require('mask_id' in args and 'tensor_layout' in args and 'pvthreshd' in args, 'explicit mask API missing')
    require('is_causal' not in args, 'causal contract requires renewed audit')
    cuda = sparse['csrc/qattn/qk_int_sv_f16_cuda_sm80.cu']
    binding = sparse['csrc/qattn/pybind.cpp']
    no_pv = 'qk_int8_sv_f16_accum_f16_block_sparse_attn_inst_buf'
    require('m.def("' + no_pv + '"' in binding, 'no-PV binding missing')
    require('float, true, 0, DTypeOut' in cuda and 'float, true, 1, DTypeOut' in cuda, 'PV dispatch modes changed')
    mask = [1, 16, (tokens + 127) // 128, (tokens + 63) // 64]
    return {
        'status': 'HASH_BOUND_SOURCE_CHECKPOINT_INTERFACE_AUDIT_PASS_NOT_KERNEL_OR_PROFILE',
        'input_sha256': inputs,
        'runtime_files_verified': len(runtime), 'sparge_files_verified': len(sparse),
        'sparge_commit': lock['commit'],
        'checkpoint_sha256': meta['checkpoint_sha256'],
        'checkpoint_attention_weights_checked': 28 * 2 * 6,
        'checkpoint_tensor_elements_not_parameter_count': meta['parameter_elements'],
        'recorded_hidden_layout': hidden,
        'hidden_layout_json_pointer': '/' + '/'.join(map(str, pointer)),
        'inferred_qkv_nhd_not_direct_hook': [1, tokens, 16, 128],
        'ampere_block_shape': [128, 64], 'inferred_block_mask_shape': mask,
        'lut_int32_bytes': math.prod(mask) * 4,
        'valid_block_count_int32_bytes': math.prod(mask[:3]) * 4,
        'integration': {
            'backend': 'minimal_a2a', 'context_parallel_size': 1,
            'qkv_source_line': qkv.lineno, 'attention_source_line': compute.lineno,
            'output': 'NHD kernel output must flatten H,D before existing output_proj',
            'scope': 'deep self-attention layers 2..27 only; probe/cross attention stay dense',
            'preserve': 'QKV projection, RMSNorm, self-attention RoPE, output projection and CP setter interface',
        },
        'confounds': {
            'public_full_mask_still_pv_skips': True,
            'no_pv_low_level_binding': no_pv,
            'required_first_comparison': 'dense vs full-QK/no-PV vs sparse-QK/no-PV; optional PV matched as separate factor',
            'quantization': 'INT8 Q/K, FP16 V on Ampere; BF16 output allocated from BF16 Q',
            'sparsity': 'compute retained-block density directly; do not use upstream triangular denominator for noncausal mask',
            'overhead': 'include NHD/HND packing, contiguous, quantization, LUT creation and synchronization',
        },
        'not_verified': ['actual runtime QKV hook', 'full build tree and compiled extensions',
                         'GPU import/finite/numerical parity', 'real kernel speed', 'WC remaining cost profile', 'method quality-time gain'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--sparge-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.root, args.sparge_source)
    require(not args.output.exists(), 'preserve existing audit output')
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(result['status'])


if __name__ == '__main__':
    main()
