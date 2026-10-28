"""Focused source-cut and rejection checks; synthetic tensors, no real weights."""
import ast
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from test_sq_q1_readout_r1 import saved_fixture
from wcomr.innovation_gain_observer_r1 import restore_readout_inputs
from wcomr.sq_readout_subgraph_r1 import (compile_head, DIT_PATH, BASE_CONFIG,
    selected_settings, load_head_weights, original_controls, original_backend_policy)
from wcomr.decoder_policy import backend_flags
from wcomr.full_sampling import CompleteStateRoundtrip

ROOT = Path(__file__).resolve().parents[1]


class SubgraphTests(unittest.TestCase):
    def test_original_backend_flags_restore_after_failure_without_CUDA_init(self):
        before = backend_flags(); precision = torch.get_float32_matmul_precision()
        with patch('torch.cuda._lazy_init', side_effect=AssertionError('CPU check must not initialize CUDA')):
            with self.assertRaisesRegex(RuntimeError, 'injected failure'):
                with original_backend_policy(ROOT/'cache/runtime') as proof:
                    self.assertTrue(proof['flags']['matmul_allow_tf32'])
                    self.assertTrue(proof['flags']['cudnn_allow_tf32'])
                    self.assertTrue(proof['flags']['cudnn_benchmark'])
                    self.assertFalse(proof['flags']['cudnn_deterministic'])
                    raise RuntimeError('injected failure')
        self.assertEqual(backend_flags(), before)
        self.assertEqual(torch.get_float32_matmul_precision(), precision)

    def test_selected_experiment_overrides_are_source_bound(self):
        settings = selected_settings(ROOT/'cache/runtime')
        self.assertTrue(settings['use_wan_fp32_strategy'])
        self.assertEqual(settings['conditional_frame_timestep'], .1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/BASE_CONFIG; path.parent.mkdir(parents=True)
            path.write_text('changed_source = True\n')
            with self.assertRaisesRegex(ValueError, 'experiment source changed'):
                selected_settings(Path(directory))

    def test_whole_pinned_class_and_unpatchify_mixed_precision(self):
        cls, unpatchify, proof = compile_head(ROOT/'cache/runtime')
        source = ast.parse((ROOT/'cache/runtime'/DIT_PATH).read_bytes())
        node = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == 'FinalLayer')
        self.assertEqual(proof['entire_FinalLayer_AST_sha256'],
                         hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest())
        head = cls(8, 2, 1, 2, use_adaln_lora=True, adaln_lora_dim=4).float().eval()
        hidden = torch.ones(1, 2, 3, 4, 8, dtype=torch.bfloat16)
        output = head(hidden, torch.zeros(1, 2, 8), torch.zeros(1, 2, 24))
        self.assertEqual(output.dtype, torch.float32)
        owner = type('PatchFixture', (), {'patch_spatial':2, 'patch_temporal':1})()
        self.assertEqual(tuple(unpatchify(owner, output).shape), (1, 2, 2, 6, 8))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/DIT_PATH; path.parent.mkdir(parents=True)
            path.write_text('class FinalLayer: pass\n')
            with self.assertRaisesRegex(ValueError, 'source changed'):
                compile_head(Path(directory))

    def test_unregistered_weights_refused(self):
        with self.assertRaisesRegex(ValueError, 'three registered'):
            load_head_weights(torch.nn.Identity(), {'net.final_layer.linear.weight':torch.ones(1)})

    def test_original_C_and_dense_control_preserve_inputs_and_report_mismatch(self):
        kernel, payload, schema = saved_fixture(flow=True)
        inputs = restore_readout_inputs(payload, schema, 'cpu')
        payload['teacher_hidden'] = [r['original']+.1 for r in inputs['current']]
        noise, latent, timestep, conditions = inputs['pair_inputs']
        payload['teacher'] = []
        for branch in (0, 1):
            row = inputs['current'][branch]
            head = kernel.net.unpatchify(kernel.net.final_layer(payload['teacher_hidden'][branch],
                row['embedding'], adaln_lora_B_T_3D=row['adaln']))
            payload['teacher'].append(kernel.to_velocity(kernel.model, noise, latent, timestep,
                conditions[branch], _supplied_net_output=head))
        good = original_controls(kernel, inputs, payload)
        self.assertTrue(good['original_controls_exact']); self.assertEqual(good['head_calls'], 4)
        bad = copy.deepcopy(payload)
        bad['readouts']['WC_C']['outputs'][0].add_(.1)
        rejected = original_controls(kernel, inputs, bad)
        self.assertFalse(rejected['original_controls_exact'])
        self.assertTrue(rejected['stored_dense_hidden_head']['exact'])
        self.assertEqual(rejected['codec_pairs'], 0)

    def test_original_control_head_failure_restores_buffers_solver_and_rng(self):
        kernel, payload, schema = saved_fixture(flow=True)
        inputs = restore_readout_inputs(payload, schema, 'cpu')
        payload['teacher_hidden'] = [r['original'] for r in inputs['current']]
        snapshot = CompleteStateRoundtrip(kernel.net, kernel.model.sample_scheduler,inputs['pair_inputs'][1])
        before = snapshot.fingerprint()
        def fail(*args, **kwargs):
            kernel.net.audit_buffer.add_(1)
            kernel.model.sample_scheduler.history.append(torch.ones(1))
            torch.rand(3)
            raise RuntimeError('head failure')
        with patch.object(kernel.net.final_layer,'forward',side_effect=fail):
            with self.assertRaisesRegex(RuntimeError, 'head failure'):
                original_controls(kernel, inputs, payload)
        self.assertEqual(snapshot.fingerprint(),before)


if __name__ == '__main__': unittest.main()
