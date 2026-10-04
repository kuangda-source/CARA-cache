"""Pinned Video2World class bodies combined with full one-action CPU controls.

Weights, conditioning construction, attention, decoder and writer remain Toy
fixtures. This checks the real frozen class interface, not real-model inference.
"""
import ast
import copy
from dataclasses import FrozenInstanceError, dataclass
import hashlib
import importlib.util
from pathlib import Path
import random
import sys
import types
from typing import Dict, Optional

import torch

from wcomr.mid_coverage import tree_digest
from wcomr.rv0_fork import object_state, restore_object_state
from wcomr.rv0_actions import OneActionSuffixControl

VIDEO_SOURCE = 'cosmos_predict2/_src/predict2/configs/video2world/defaults/conditioner.py'
VIDEO_SHA = 'd58f515074237843b707d67001751c0e022546061348728e6322faaaa22e837c'


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pinned_video_condition(runtime, data_type):
    """Compile the entire unchanged subclass; do not substitute V2 or GR00T."""
    base = load('check_rv0_restore_cpu').pinned_condition(runtime, data_type)
    raw = (runtime/VIDEO_SOURCE).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == VIDEO_SHA
    nodes = [n for n in ast.parse(raw).body
             if isinstance(n, ast.ClassDef) and n.name == 'Video2WorldCondition']
    assert len(nodes) == 1
    module = types.ModuleType('cpu_rv0_pinned_video_condition')
    sys.modules[module.__name__] = module
    def no_parallel(*args, **kwargs):
        raise AssertionError('Context parallel broadcast is outside this CPU fixture')
    vars(module).update(Text2WorldCondition=base, dataclass=dataclass, Dict=Dict,
                        Optional=Optional, torch=torch, random=random,
                        broadcast_split_tensor=no_parallel)
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    body = ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[]))
    exec(compile(body, str(runtime/VIDEO_SOURCE)+'#cpu-whole-class', 'exec'), vars(module))
    return module.Video2WorldCondition, hashlib.sha256(
        ast.dump(nodes[0], include_attributes=False).encode()).hexdigest()


def exercise(*, inference, samples, wc, settings, flow, runtime, **kwargs):
    model = inference.pipe.model
    original_conditioner = model.conditioner.get_condition_with_negative_prompt
    frozen, class_sha = pinned_video_condition(runtime,
        wc.worldcache_mini_train_dit_forward.__globals__['DataType'])

    def conditions(batch):
        gt = torch.arange(32, dtype=torch.float32).reshape(1, 2, 2, 2, 4)/31
        result = []
        for slot in (0, 1):
            value = frozen(crossattn_emb=torch.ones(1, 3, 4)*
                           (1+slot+.1*(batch['prompt']=='human')),
                           fps=batch['fps'], padding_mask=torch.zeros(1, 1, 2, 4),
                           use_video_condition=torch.tensor([slot==0]))
            value = value.set_video_condition(gt.clone(), 0, 0, num_conditional_frames=1)
            value = value.edit_for_inference(is_cfg_conditional=slot==0, num_conditional_frames=1)
            assert value.gt_frames.shape[2] == 2
            assert value.condition_video_input_mask_B_C_T_H_W[:, :, 0].eq(1).all()
            assert value.condition_video_input_mask_B_C_T_H_W[:, :, 1].eq(0).all()
            assert bool(value.use_video_condition.all())
            result.append(value)
        return tuple(result)

    probe = conditions({'fps': torch.tensor([16.]), 'prompt': 'common'})[0]
    saved = copy.deepcopy(object_state(probe)); identity = id(probe)
    try:
        probe.gt_frames = torch.zeros_like(probe.gt_frames)
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError('Video condition no longer frozen')
    for value in vars(probe).values():
        if isinstance(value, torch.Tensor):
            if value.dtype == torch.bool: value.logical_not_()
            else: value.add_(1)
    object.__setattr__(probe, 'child_only_field', 'drift')
    restore_object_state(probe, saved)
    assert id(probe) == identity and tree_digest(object_state(probe)) == tree_digest(saved)
    assert not hasattr(probe, 'child_only_field')
    try:
        probe.use_video_condition = False
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError('Restore removed frozen behavior')

    actions = load('check_rv0_actions_cpu')
    captures = []
    sample_name = [None]

    class AuditedVideoControl(OneActionSuffixControl):
        def __init__(self, *args, **kw):
            super().__init__(*args, **kw)
            assert all(type(c) is frozen and c.__dataclass_params__.frozen for c in self.conditions)
            self.condition_ids = tuple(id(c) for c in self.conditions)
            self.condition_sha = [tree_digest(object_state(c)) for c in self.conditions]
            # Exercise restoration of all real mutable fields and child-only
            # attributes before executing any branch, then keep the parent.
            for condition in self.conditions:
                condition.gt_frames.add_(.5)
                condition.condition_video_input_mask_B_C_T_H_W.zero_()
                condition.use_video_condition.logical_not_()
                object.__setattr__(condition, 'child_only_field', 'test')
            self.restore_parent()
            self.assert_conditions()
            self.audit_capture = {'sample': sample_name[0], 'flow': flow,
                'threshold': self.net.worldcache_rel_l1_thresh,
                'condition_before': self.condition_sha,
                'condition_class_AST_sha256': class_sha,
                'condition_fields': sorted(object_state(self.conditions[0])),
                'branches': [], 'failures': []}
            captures.append(self.audit_capture)

        def assert_conditions(self):
            assert tuple(id(c) for c in self.conditions) == self.condition_ids
            assert [tree_digest(object_state(c)) for c in self.conditions] == self.condition_sha
            for c in self.conditions:
                assert type(c) is frozen and c.__dataclass_params__.frozen
                assert not hasattr(c, 'child_only_field')
                try:
                    c.gt_frames = None
                except FrozenInstanceError:
                    pass
                else:
                    raise AssertionError('Branch restore removed frozen behavior')

        def run_action(self, label, plan):
            try:
                result = super().run_action(label, plan)
            except ValueError:
                self.assert_conditions()
                self.audit_capture['failures'].append(copy.deepcopy(self.records[-1]))
                raise
            self.assert_conditions()
            record = copy.deepcopy(self.records[-1])
            record['condition_after_restore'] = [tree_digest(object_state(c)) for c in self.conditions]
            record['condition_identity_and_frozen_behavior_preserved'] = True
            self.audit_capture['branches'].append(record)
            return result

    original_control = actions.OneActionSuffixControl
    model.conditioner.get_condition_with_negative_prompt = conditions
    actions.OneActionSuffixControl = AuditedVideoControl
    checks = []
    try:
        for sample in samples:
            sample_name[0] = sample.name
            result = actions.exercise(inference=inference, samples=[sample], wc=wc,
                settings=settings, flow=flow, runtime=runtime, **kwargs)
            for row in result:
                row.update(sample=sample.name, actual_Video2World_class_AST=True,
                    pinned_video_source_sha256=VIDEO_SHA,
                    all_real_mutable_condition_fields_restored=True,
                    Video2World_set_and_edit_for_inference_exercised=True)
            checks.extend(result)
        assert len(captures) == 4 and sum(len(c['branches']) for c in captures) == 48
        return [{'flow': flow, 'checks': checks, 'raw_captures': captures,
                 'real_frozen_class_AST_sha256': class_sha,
                 'whole_class_body_not_V2_or_GR00T': True,
                 'condition_construction_weights_network_decoder_writer_are_Toy': True}]
    finally:
        model.conditioner.get_condition_with_negative_prompt = original_conditioner
        actions.OneActionSuffixControl = original_control


def run(runtime):
    runtime = Path(runtime)
    fixture = load('check_full_sampling')
    controls = fixture.run(runtime, exercise=lambda **k: exercise(runtime=runtime, **k))
    assert not torch.cuda.is_initialized()
    assert len(controls['checks']) == 2
    return {'status': 'PINNED_VIDEO_CONDITION_CD_JOINT_CPU_PASS_NOT_REAL_GPU',
            'controls': controls, 'video_source': VIDEO_SOURCE, 'video_source_sha256': VIDEO_SHA,
            'CPU_flow_groups': 2, 'scene_names': ['common', 'human'],
            'native_threshold_controls_per_scene': 2, 'CFG_slots': [0, 1],
            'complete_suffixes': 96, 'CUDA_initialized': False,
            'GPU_submissions': 0, 'RV_labels': 0}
