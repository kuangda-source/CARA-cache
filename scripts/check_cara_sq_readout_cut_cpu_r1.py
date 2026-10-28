"""One registered real-weight CPU readout control, or head-only host preparation."""
import argparse
import gc
import hashlib
import io
import json
import os
from pathlib import Path
import resource
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'tests')]
import torch
from wcomr.innovation_gain_observer_r1 import restore_readout_inputs
from wcomr.scout_readout_v22 import validate_state
from wcomr.sq_q1_readout_r1 import PROMPTS
from wcomr.sq_readout_subgraph_r1 import build_kernel, original_controls, CHECKPOINT_SHA

SCOPE = 'plans/cara_next_stage_20261028/sq/Q1_READOUT_CONTROL_CPU_R3.json'
WEIGHT = ('cache/huggingface/hub/models--nvidia--Cosmos-Predict2.5-2B/'
          'snapshots/15a82a2ec231bc318692aa0456a36537c806e7d4/'
          'base/post-trained/81edfebe-bd6a-4039-8c1d-737df1a790bf_ema_bf16.pt')


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(8*1024**2), b''):
            h.update(block)
    return h.hexdigest()


def run(args):
    scope = json.loads((ROOT/args.scope).read_text())
    if (scope['prompt'] != PROMPTS[0] or scope['step'] != 22 or scope['new_GPU_submissions'] != 0
            or scope['roles'] != ['original_C_pair', 'stored_dense_hidden_head_pair']
            or scope['codec_pairs'] != 0 or scope['original_files_readonly'] is not True):
        raise ValueError('Frozen single-state CPU control scope differs')
    stream = io.StringIO()
    tests = unittest.TextTestRunner(stream=stream, verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromName('test_sq_readout_subgraph_r1'))
    if not tests.wasSuccessful():
        raise RuntimeError(stream.getvalue())
    print('READOUT_CUT_FIXTURES_PASS', flush=True)
    project = ROOT.parent.parent
    runtime = project/'runtime'
    started = time.monotonic()
    checkpoint = project/WEIGHT
    if sha(checkpoint) != CHECKPOINT_SHA:
        raise ValueError('Original 2B checkpoint SHA differs')
    weights = torch.load(checkpoint, map_location='cpu', weights_only=True, mmap=True)
    kernel, proof = build_kernel(runtime, weights)
    selected = proof['selected_experiment_settings']
    if scope['selected_experiment_settings'] != {key:selected[key]
            for key in ('use_wan_fp32_strategy','conditional_frame_timestep')}:
        raise ValueError('Selected experiment differs from the corrected frozen CPU scope')
    del weights; gc.collect()
    result = dict(status='PINNED_READOUT_CUT_HEAD_PREPARED_CPU', profile=args.profile,
        source_scope=scope, fixture_checks=dict(tests=tests.testsRun, failures=len(tests.failures),
        errors=len(tests.errors), log=stream.getvalue(), real_model=False),
        checkpoint=dict(path=str(checkpoint), bytes=checkpoint.stat().st_size, sha256=CHECKPOINT_SHA),
        build_and_weight_hash_seconds=time.monotonic()-started, source_proof=proof,
        actual_saved_state=None, actual_weighted_head_executed=False,
        complete_Q1_cohort=False, codec_pairs=0, new_states=0, new_videos=0,
        new_GPU_submissions=0, new_GPUh=0, ledger_writes=0, GPU_ready=False)
    print('ORIGINAL_HEAD_WEIGHTS_VERIFIED', flush=True)
    if args.profile == 'two_card':
        if sha(args.assets/'manifest.json') != args.manifest_sha256:
            raise ValueError('B1 manifest SHA differs')
        manifest = json.loads((args.assets/'manifest.json').read_text())
        rows = [r for r in manifest['states'] if (r['prompt'], r['step']) == (PROMPTS[0], 22)]
        if len(rows) != 1:
            raise ValueError('One preregistered AV28 step22 state required')
        verified = []
        def read(ref):
            path = args.assets/ref['name']
            if (path.is_symlink() or path.resolve().parent != args.assets.resolve()
                    or path.stat().st_size != ref['bytes'] or sha(path) != ref['sha256']):
                raise ValueError('Original B1 path/bytes/SHA differs')
            verified.append(ref)
            return torch.load(path, map_location='cpu', weights_only=True, mmap=True)
        started = time.monotonic()
        payload = read(rows[0]['artifact'])
        payload['anchors'] = tuple(tuple(read(ref) for ref in pair) for pair in payload['anchors'])
        if not all(payload[key] for key in ('P0_actual_dense', 'P1_dense_head_RF_equal', 'P2_C_actual_parent_equal')):
            raise ValueError('Accepted same-state original controls required')
        sys.path[:0] = [str(runtime), str(runtime/'packages/cosmos-oss'), str(runtime/'packages/cosmos-cuda')]
        from cosmos_predict2._src.predict2.conditioner import DataType
        from check_rv0_video_actions_cpu import pinned_video_condition
        condition, class_sha = pinned_video_condition(runtime, DataType)
        schema = [(condition, {'data_type':DataType}) for _ in (0, 1)]
        inputs = restore_readout_inputs(payload, schema, 'cpu')
        support = validate_state(inputs['context'], inputs['step'], inputs['xi'], inputs['anchors'])
        if inputs['context'][1] != 'Cosmos-Predict2.5-2B-post-trained':
            raise ValueError('Registered original model identity differs')
        result['asset_read_hash_and_restore_seconds'] = time.monotonic()-started
        result['verified_B1_files'] = verified
        result['condition_class_AST_sha256'] = class_sha
        result['condition_mode'] = 'EXISTING_PINNED_WHOLE_CLASS_CPU_COMPILATION'
        result['full_condition_module_imported'] = False
        print('AV28_STEP22_RESTORED', flush=True)
        started = time.monotonic()
        controls = original_controls(kernel, inputs, payload)
        result['actual_saved_state'] = dict(prompt=PROMPTS[0], step=22, support=support,
            controls=controls, controls_wall_seconds=time.monotonic()-started,
            current_metadata=[{key:dict(shape=list(value.shape), dtype=str(value.dtype))
                for key, value in row.items()} for row in inputs['current']])
        result['actual_weighted_head_executed'] = True
        result['status'] = ('ORIGINAL_READOUT_CONTROLS_EXACT_CPU' if controls['original_controls_exact']
                            else 'ORIGINAL_READOUT_CONTROLS_MISMATCH_CPU_NO_CODEC_SCORING')
    if torch.cuda.is_initialized():
        raise RuntimeError('CPU readout preparation initialized CUDA')
    result['CUDA_initialized'] = False
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--assets', type=Path, required=True); p.add_argument('--manifest-sha256', required=True)
    p.add_argument('--profile', choices=('two_card','four_card'), required=True)
    p.add_argument('--scope', default=SCOPE)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): raise FileExistsError('Keep the original CPU result')
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('NVIDIA_VISIBLE_DEVICES') != 'void':
        raise RuntimeError('CPU preparation must hide GPU devices')
    def forbidden(*args, **kwargs):
        raise RuntimeError('GPU context and download forbidden in CPU preparation')
    torch.cuda._lazy_init = forbidden; torch.hub.download_url_to_file = forbidden
    torch.set_num_threads(2); os.nice(10)
    started, cpu = time.monotonic(), time.process_time()
    result = run(args)
    result.update(wall_seconds=time.monotonic()-started, CPU_seconds=time.process_time()-cpu,
        peak_RSS_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        torch_version=torch.__version__, observed_unix=time.time())
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write('\n')
    print(result['status'], flush=True)


if __name__ == '__main__': main()
