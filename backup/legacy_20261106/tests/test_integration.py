"""Run the pinned upstream forward with CPU toy blocks, not a fake reimplementation.
These verify wiring only, not CUDA/model parity or video quality.
"""
import ast
from enum import Enum
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional, Tuple, Union
import torch
from wcomr.integration import build_forward, inject_source

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'vendor/WorldCache/Models/Cosmos-Predict2.5/cosmos_predict2/_src/predict2/inference/worldcache_utils.py'


class DataType(Enum):
    VIDEO = 1


def upstream():
    tree = ast.parse(SOURCE.read_text())
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and
                 n.name in ('compute_optimal_gamma', 'worldcache_mini_train_dit_forward', 'apply_worldcache')]
    ns = dict(torch=torch, amp=torch.amp, DataType=DataType, Optional=Optional,
              List=List, Tuple=Tuple, Union=Union, log=SimpleNamespace(info=lambda *a: None))
    exec(compile(tree, str(SOURCE), 'exec'), ns)
    return ns


class Block(torch.nn.Module):
    def __init__(self, factor):
        super().__init__(); self.factor = factor
    def forward(self, x, **kwargs):
        return x * self.factor + 0.01


class Toy(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.blocks = torch.nn.ModuleList([Block(1.02), Block(1.03), Block(1.04)])
        self.use_crossattn_projection = False
        self.use_wan_fp32_strategy = False
        self.t_embedder = lambda t: (t.unsqueeze(-1), None)
        self.t_embedding_norm = lambda t: t
        self.final_layer = lambda x, *args, **kwargs: x
        self.unpatchify = lambda x: x
    def prepare_embedded_sequence(self, x, **kwargs):
        return x, None, None


def model(mode=None, threshold=1):
    ns=upstream()
    if mode:
        ns['worldcache_mini_train_dit_forward'] = build_forward(ns['worldcache_mini_train_dit_forward'], mode)
    return ns['apply_worldcache'](Toy(), num_steps=20, ret_ratio=0.3,
                                 rel_l1_thresh=threshold, probe_depth=1, osi_enabled=True)


def run(m, count=20):
    outputs=[]
    for i in range(count):
        x=torch.full((1,2,2,2,3),1+i*0.001)
        outputs.append(m(x, torch.ones(1), torch.ones(1)))
    return outputs


def test_candidate_off_bitwise_official_behavior():
    ns=upstream(); f=ns['worldcache_mini_train_dit_forward']
    assert build_forward(f,'official') is f
    for a,b in zip(run(model()),run(model('official'))):
        assert torch.equal(a,b)


def test_no_skip_matches_exact_block_stack():
    m=model('scalar',threshold=-1)
    for i,out in enumerate(run(m)):
        x=torch.full((1,2,2,2,3),1+i*0.001)
        for block in m.blocks: x=block(x)
        assert torch.equal(x,out)


def test_anchors_only_on_full_computations_and_cfg_separation():
    m=model('scalar'); run(m, count=12)
    assert m._w1_calibrators[0].receipt()['anchor_steps']==[2,4]
    assert m._w1_calibrators[1].receipt()['anchor_steps']==[3,5]
    assert m._w1_last_reason=='scalar'
    assert m._w1_calibrators[0] is not m._w1_calibrators[1]


def test_prompt_reset_and_model_isolation():
    a,b=model('scalar'),model('scalar')
    run(a); run(a,1); run(b,1)
    assert a._w1_generation==2 and b._w1_generation==1
    assert a._w1_calibrators[0].receipt()['anchor_steps']==[0]
    assert not a._w1_calibrators[1].anchors
    assert a._w1_calibrators is not b._w1_calibrators


def test_injection_is_narrow_and_fails_closed():
    import pytest
    with pytest.raises(RuntimeError): inject_source('def unrelated(): pass')
