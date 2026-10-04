"""Pinned frozen-condition restoration and two-parent/four-suffix CPU wiring."""
import ast
import copy
import hashlib
import importlib.util
import sys
import tempfile
import types
from abc import ABC
from dataclasses import FrozenInstanceError, dataclass, fields
from pathlib import Path
from typing import Any, Dict, Optional

import torch

from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.mid_coverage import WC_FIELDS, tree_digest
from wcomr.prepared_input import RNGState
from wcomr.rv0_fork import WC_CONFIGURATION, object_state, restore_object_state
from wcomr.rv0_restore import capture_gate, run_restore_controls

CONDITION_SHA = '47554e88f2a5d5157e30b18b1d7ad4a4ee55a99dfbaf7071f680c7acf438843a'


def pinned_condition(runtime, data_type):
    raw = (runtime/'cosmos_predict2/_src/predict2/conditioner.py').read_bytes()
    assert hashlib.sha256(raw).hexdigest() == CONDITION_SHA
    nodes = [n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef)
             and n.name in ('BaseCondition', 'Text2WorldCondition')]
    assert [n.name for n in nodes] == ['BaseCondition', 'Text2WorldCondition']
    module = types.ModuleType('cpu_rv0_pinned_frozen_condition')
    sys.modules[module.__name__] = module
    vars(module).update(ABC=ABC, dataclass=dataclass, fields=fields,
                        Dict=Dict, Any=Any, Optional=Optional, torch=torch, DataType=data_type)
    future = ast.ImportFrom(module='__future__', names=[ast.alias(name='annotations')], level=0)
    body = ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[]))
    exec(compile(body, '<pinned-frozen-condition>', 'exec'), vars(module))
    return module.Text2WorldCondition


def exercise(*, inference, samples, wc, settings, mode_setup, flow, runtime, **unused):
    model, net, scheduler = inference.pipe.model, inference.pipe.model.net, inference.pipe.model.sample_scheduler
    prior_forward, prior_prepare = net.forward, net.prepare_embedded_sequence
    prior_conditioner = model.conditioner.get_condition_with_negative_prompt
    caller = CompleteStateRoundtrip(net, scheduler, torch.zeros(1)); before = caller.fingerprint()
    configuration = {k: copy.deepcopy(getattr(net, k)) for k in WC_CONFIGURATION if hasattr(net, k)}
    keys = {k for k in WC_FIELDS if hasattr(net, k)}
    frozen = pinned_condition(runtime, wc.worldcache_mini_train_dit_forward.__globals__['DataType'])
    probe = frozen(crossattn_emb=torch.ones(2), fps=torch.tensor([16.]))
    saved = copy.deepcopy(object_state(probe)); original_id = id(probe)
    try:
        probe.crossattn_emb = torch.zeros(2)
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError('Pinned condition unexpectedly permits ordinary setattr')
    probe.crossattn_emb.add_(1); object.__setattr__(probe, 'extra_child_field', 'drift')
    restore_object_state(probe, saved)
    assert id(probe) == original_id and tree_digest(object_state(probe)) == tree_digest(saved)
    assert not hasattr(probe, 'extra_child_field')
    try:
        probe.fps = torch.zeros(1)
    except FrozenInstanceError:
        pass
    else:
        raise AssertionError('Restore removed frozen-condition behavior')
    net.prepare_embedded_sequence = lambda x, **kwargs: (x.movedim(1, -1).contiguous(), None, None)
    def conditions(batch):
        return tuple(frozen(crossattn_emb=torch.ones(1,3,4)*(1+slot+.1*(batch['prompt']=='human')),
                            fps=batch['fps']) for slot in (0, 1))
    model.conditioner.get_condition_with_negative_prompt = conditions
    try:
        entry = RNGState(); expected = {}
        with tempfile.TemporaryDirectory(prefix='rv0-restore-cpu-') as directory:
            for sample in samples:
                wc.apply_worldcache(net, **{k.removeprefix('worldcache_'): v for k, v in settings.items()})
                paths = inference.generate([sample], output_dir=Path(directory)/('ordinary_'+sample.name))
                expected[sample.name] = hashlib.sha256(Path(paths[0]).read_bytes()).hexdigest()
            caller.restore(); entry.restore()
            config = {'run_id': 'CPU_RESTORE', 'sample_names': [s.name for s in samples],
                      'snapshot_step': 22, 'suffix_labels': ['A','B'],
                      'logical_copy_cap_bytes': 6*(1<<30), 'transient_copy_factor': 2,
                      'workspace_reserve_bytes': 4*(1<<30), 'expected_parent_video_sha256': expected}
            state = {}
            run_restore_controls(inference, samples, wc, settings, state=state, save=lambda: None,
                output=Path(directory)/'controls', contexts=[('CPU_RESTORE:'+s.name,'toy','condition:'+s.name) for s in samples],
                mode_setup=mode_setup, sampler_source=runtime/'cosmos_predict2/_src/predict2/models/text2world_model_rectified_flow.py',
                config=config)
        assert len(state['requests']) == 2
        for row in state['requests']:
            assert row['all_suffix_inputs_outputs_solver_deep_latent_state_equal']
            assert row['historical_official_video_bridge_equal']
            assert len(row['controls']) == 2 and row['prepare_calls'] == 1
            for child in row['controls']:
                assert len(child['inputs']) == 28 and len(child['solver_outputs']) == 14
        # The metadata gate must refuse oversize copies and insufficient GPU
        # headroom before allocations. These values are synthetic gate inputs.
        for totals, cap, free in [({'cpu':100},99,None), ({'cuda:0':100},200,499)]:
            try:
                capture_gate({'logical_copy_bytes_by_device':totals},logical_copy_cap_bytes=cap,
                    transient_copy_factor=2,workspace_reserve_bytes=300,available_gpu_bytes=free)
            except ValueError:
                pass
            else:
                raise AssertionError('Illegal capture allocation admitted')
        return [{'flow':flow, 'pinned_frozen_condition_assignment_refused':True,
                 'condition_identity_values_and_frozen_behavior_restored':True,
                 'two_parents_four_unchanged_suffixes_and_ordinary_continuations_equal':True,
                 'ordinary_mock_output_bridges_equal':True,
                 'copy_cap_and_live_headroom_refused_before_allocation':True,
                 'conditioner_source_sha256':CONDITION_SHA,
                 'requests':state['requests'], 'real_model_or_GPU_restore_acceptance':False}]
    finally:
        net.forward=prior_forward;net.prepare_embedded_sequence=prior_prepare
        model.conditioner.get_condition_with_negative_prompt=prior_conditioner
        for key in set(WC_FIELDS)-keys:
            if hasattr(net,key):delattr(net,key)
        for key,value in configuration.items():setattr(net,key,value)
        caller.restore();assert caller.fingerprint()==before


def run(runtime):
    spec=importlib.util.spec_from_file_location('cpu_restore_fixture',Path(__file__).with_name('check_full_sampling.py'))
    fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
    result=fixture.run(runtime,exercise=lambda **kwargs:exercise(runtime=Path(runtime),**kwargs))
    assert not torch.cuda.is_initialized()
    return {'status':'PINNED_FROZEN_CONDITION_AND_RESTORE_CORE_CPU_PASS_NOT_REAL_GPU',
            'controls':result,'CUDA_initialized':False,'GPU_submissions':0,'RV_labels':0}
