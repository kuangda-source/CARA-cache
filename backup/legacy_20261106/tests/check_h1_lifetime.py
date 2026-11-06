"""Pinned-source CPU wiring: all 18 cells, refresh isolation and failure receipt."""
import ast
import hashlib
import inspect
import linecache
from pathlib import Path
import tempfile
import types
from enum import Enum
from typing import List, Optional, Tuple, Union

import torch
from einops import rearrange

from wcomr.h0_mode import establish_shared_eval
from wcomr.h1_lifetime import H1LifetimeProbe, build_h1_forward
from wcomr.measurement import BlockCounts
from wcomr.mid_coverage import WC_FIELDS, tree_digest
from wcomr.shadow_metrics import tensor_error


def run(source_path):
    data = Path(source_path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == 'b485cb8fd6e262a40e5823365c34ef7db1bc036c591d7577489e04077c515903'
    tree = ast.parse(data.decode())
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in (
        'compute_optimal_gamma', 'estimate_optical_flow', 'warp_feature',
        'worldcache_mini_train_dit_forward', 'apply_worldcache')]

    class DataType(Enum):
        VIDEO = 1

    namespace = dict(torch=torch, amp=torch.amp, F=torch.nn.functional,
        rearrange=rearrange, DataType=DataType, List=List, Optional=Optional,
        Tuple=Tuple, Union=Union, log=types.SimpleNamespace(info=lambda *x: None))
    exec(compile(tree, str(source_path), 'exec'), namespace)

    class Op(torch.nn.Module):
        def forward(self, q, k, v):
            return (q * 1.002).reshape(1, 128, 2048)

    class Block(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.self_attn = types.SimpleNamespace(attn_op=Op())
            self.register_buffer('visits', torch.zeros(()))

        def forward(self, x, **kwargs):
            self.visits.add_(1)
            q = x.reshape(1, 128, 16, 128)
            return self.self_attn.attn_op(q, q, q).reshape_as(x) + .002

    class Toy(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.blocks = torch.nn.ModuleList([Block() for _ in range(4)])
            self.use_crossattn_projection = False
            self.use_wan_fp32_strategy = False
            self.t_embedder = lambda t: (t.unsqueeze(-1), None)
            self.t_embedding_norm = lambda t: t
            self.final_layer = lambda x, *args, **kwargs: x
            self.unpatchify = lambda x: x

        def prepare_embedded_sequence(self, x, **kwargs):
            return x, None, None

    def kernel(q, k, v, mask, sim, cdf, full):
        assert (sim, cdf) == (.1, .98)
        return (q * 1.002 * (.999 if full else .99)).reshape(1, 128, 2048), {'selected_fraction': .7}

    config = {'source_solver_step': 17, 'reuse_ages': [1, 2, 4],
        'warmups': 1, 'repeats': 3, 'dense_fallback_layers': [2], 'policy': {'sim': .1, 'cdf': .98}}
    spatial = torch.linspace(.7, 1.3, 128 * 2048).reshape(1, 2, 8, 8, 2048)
    checks = []
    for flow in (False, True):
        for skip_future in (False, True):
            ns = dict(namespace)
            pure = dict(namespace)
            # Function globals must belong to each independent namespace;
            # copying a dict alone would leave apply_worldcache bound to the
            # original forward and silently bypass the diagnostic.
            exec(compile(tree, str(source_path), 'exec'), ns)
            exec(compile(tree, str(source_path), 'exec'), pure)
            original = ns['worldcache_mini_train_dit_forward']
            if skip_future:
                # CPU control only: both paired paths share a fixed artificial
                # schedule. Age 3 refreshes the deployed cache; held references
                # must remain at age-0 despite that refresh. GPU source is stock.
                source = inspect.getsource(original)
                anchor = '    # --- Execution Branching ---'
                source = source.replace(anchor,
                    '    if self.cnt >= 34 and self.cnt not in (38, 39):\n'
                    '        skip_forward = True\n'
                    '        residual_x = self.residual_cache[current_idx]\n'
                    '        self.resume_flag[current_idx] = False\n\n' + anchor)
                path = '<h1-cpu-fixed-schedule-%s>' % flow
                linecache.cache[path] = (len(source), None, source.splitlines(keepends=True), path)
                exec(compile(source, path, 'exec'), ns)
                exec(compile(source, path, 'exec'), pure)
                original = ns['worldcache_mini_train_dit_forward']
            with tempfile.TemporaryDirectory(prefix='wc-h1-cpu-') as directory:
                diagnostic = H1LifetimeProbe(config, context=('request', 'model', 'condition'),
                                              kernel=kernel, raw_output=directory)
                ns['worldcache_mini_train_dit_forward'] = build_h1_forward(original, diagnostic)
                settings = dict(num_steps=84, ret_ratio=.2, rel_l1_thresh=-1,
                                probe_depth=1, osi_enabled=True, flow_enabled=flow, flow_scale=1)
                plain = pure['apply_worldcache'](Toy(), **settings)
                observed = ns['apply_worldcache'](Toy(), **settings)
                establish_shared_eval(plain)
                establish_shared_eval(observed)
                diagnostic.install_operators(observed)
                counts = BlockCounts(observed.blocks, cache_model=observed)
                for counter in range(42):
                    x = spatial + counter * .0001 * (1 + spatial.square())
                    args = x, torch.ones(1), torch.ones(1)
                    a = plain(*args)
                    b = observed(*args)
                    assert torch.equal(a, b), (flow, skip_future, counter)
                assert diagnostic.coverage()['future_source_age_cells'] == 18
                assert len(diagnostic.source_records) == 2 and len(diagnostic.records) == 6
                assert [(x['call'], x['age'], x['cfg_slot']) for x in diagnostic.records] == [
                    (35, 1, 0), (36, 1, 1), (37, 2, 0), (38, 2, 1), (41, 4, 0), (42, 4, 1)]
                assert counts.result() == {'denoiser_calls': 42,
                    'full_calls': 36 if skip_future else 42,
                    'skipped_deep_calls': 6 if skip_future else 0}
                for a, b in zip(plain.buffers(), observed.buffers()):
                    assert torch.equal(a, b)
                assert tree_digest({k: getattr(plain, k) for k in WC_FIELDS if hasattr(plain, k)}) == \
                    tree_digest({k: getattr(observed, k) for k in WC_FIELDS if hasattr(observed, k)})
                for record in diagnostic.records:
                    assert record['prediction_before_current_shadow_truth']
                    assert record['future_D_double_replay_bitwise_equal']
                    assert record['shadow_D_matches_deployed_full'] == (None if skip_future else True)
                    truth = torch.load(record['truth_raw_snapshot']['path'], map_location='cpu', weights_only=True)
                    for row in record['completed_arms']:
                        snapshot = row['raw_snapshot']
                        assert hashlib.sha256(Path(snapshot['path']).read_bytes()).hexdigest() == snapshot['sha256']
                        value = torch.load(snapshot['path'], map_location='cpu', weights_only=True)
                        for field in ('postwarp_residual', 'velocity'):
                            assert tensor_error(value[field], truth[field]) == row[field]
                        assert len(row['wall_ms']) == 3
                        assert row['provenance']['identity']['solver_step'] == 17
                        assert row['provenance']['source_is_approximate'] == (row['arm'] != 'dense')
                        assert not row['provenance']['inserted_into_online_cache_or_calibrator']
                assert len(list(Path(directory).glob('*/*.pt'))) == 30
                diagnostic.close()
                counts.close()
                checks.append({'flow': flow, 'CPU_artificial_future_skip_control': skip_future,
                    'paired_calls': 42, 'source_arms': 6, 'paired_lifetime_cells': 18,
                    'raw_files': 30, 'outputs_buffers_cache_counts_exact': True,
                    'all_raw_candidate_errors_independently_recomputed': True,
                    'age3_deployed_refresh_does_not_refresh_held_reference': skip_future})

    # Failure preserves the full requested matrix; no source is promoted and no
    # alternative branch point is silently selected.
    def nonfinite(q, k, v, mask, sim, cdf, full):
        value, meta = kernel(q, k, v, mask, sim, cdf, full)
        return (value if full else value * float('nan')), meta

    ns = dict(namespace)
    exec(compile(tree, str(source_path), 'exec'), ns)
    diagnostic = H1LifetimeProbe(config, context=('failure', 'model', 'condition'), kernel=nonfinite)
    ns['worldcache_mini_train_dit_forward'] = build_h1_forward(ns['worldcache_mini_train_dit_forward'], diagnostic)
    model = ns['apply_worldcache'](Toy(), num_steps=84, ret_ratio=.2, rel_l1_thresh=-1,
                                 probe_depth=1, osi_enabled=True)
    establish_shared_eval(model)
    diagnostic.install_operators(model)
    failed = False
    for counter in range(42):
        try:
            model(spatial + counter * .0001, torch.ones(1), torch.ones(1))
        except ValueError as error:
            assert 'nonfinite/undefined' in str(error)
            failed = True
            break
    assert failed and len(diagnostic.source_attempts) == 1
    assert len(diagnostic.source_attempts[0]['completed_source_arms']) == 3
    assert not diagnostic.references and not diagnostic.records
    assert not model._w1_shadow_active and diagnostic.mode == 'dense'
    diagnostic.close()
    checks.append({'failed_sparse_source_retained_in_6_source_18_lifetime_denominators': True,
                   'no_source_promotion_reselect_or_future_cells_on_failure': True})
    assert not torch.cuda.is_initialized()
    return {'status': 'H1_PINNED_SOURCE_CPU_WIRING_PASS_NOT_REAL_MODEL_LIFETIME_RESULT',
        'checks': checks, 'cuda_initialized': False, 'source_sha256': hashlib.sha256(data).hexdigest(),
        'limits': 'Toy modules/synthetic sparse kernel; artificial skip control is CPU-only; '
                  'no actual weights, GPU, forked rollout, video or scientific lifetime result'}
