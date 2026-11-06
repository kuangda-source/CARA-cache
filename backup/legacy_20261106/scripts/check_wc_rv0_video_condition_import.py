#!/usr/bin/env python3
"""Actual frozen Video2World class import/origin check; never load weights/CUDA."""
import argparse
import ast
import copy
from dataclasses import FrozenInstanceError, fields
import hashlib
import importlib
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True)
    p.add_argument('--stage', type=Path, required=True)
    a = p.parse_args()
    os.environ.update(CUDA_VISIBLE_DEVICES='', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
    sys.path[:0] = [str(a.stage/'src'), str(a.runtime),
                   str(a.runtime/'packages/cosmos-oss'), str(a.runtime/'packages/cosmos-cuda')]
    import torch
    assert not torch.cuda.is_initialized()
    def forbidden(*args, **kwargs):
        raise RuntimeError('CUDA and Triton benchmarking forbidden during CPU import')
    torch.cuda._lazy_init = forbidden
    import triton
    class ImportOnlyDriver:
        def get_benchmarker(self): return forbidden
        def __getattr__(self, name): raise RuntimeError('CPU import forbids Triton driver '+name)
    triton.runtime.driver.active = ImportOnlyDriver()
    name = 'cosmos_predict2._src.predict2.configs.video2world.defaults.conditioner'
    # The unrelated Reason1 config import asserts a Transformers helper that
    # includes torch.cuda.is_available(). Bind installed package metadata only
    # in this exiting import process; never change GPU runtime or upstream.
    import transformers.utils as hf_utils
    from transformers.utils import import_utils
    from packaging.version import Version
    flash_version = importlib.metadata.version('flash_attn')
    assert import_utils._is_package_available('flash_attn')
    assert torch.version.cuda and Version(flash_version) >= Version('2.1.0')
    previous = (hf_utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available)
    availability_before = bool(previous[0]())
    def metadata_only_flash_availability():
        assert not torch.cuda.is_initialized()
        return True
    hf_utils.is_flash_attn_2_available = metadata_only_flash_availability
    import_utils.is_flash_attn_2_available = metadata_only_flash_availability
    # get_umt5_emb evaluates current_device() in an unused constructor default
    # at import time. Bind that default's ordinal without a driver/context.
    # No tokenizer/model instance is constructed in this check.
    previous_current_device = torch.cuda.current_device
    torch.cuda.current_device = lambda: 0
    try:
        module = importlib.import_module(name)
    finally:
        hf_utils.is_flash_attn_2_available, import_utils.is_flash_attn_2_available = previous
        torch.cuda.current_device = previous_current_device
    source = a.runtime/'cosmos_predict2/_src/predict2/configs/video2world/defaults/conditioner.py'
    raw = source.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == 'd58f515074237843b707d67001751c0e022546061348728e6322faaaa22e837c'
    assert Path(module.__file__).resolve() == source.resolve()
    cls = module.Video2WorldCondition
    assert cls.__module__ == name and cls.__dataclass_params__.frozen
    node = next(n for n in ast.parse(raw).body if isinstance(n, ast.ClassDef) and n.name == cls.__name__)
    actual = ast.parse(inspect.getsource(cls)).body[0]
    assert ast.dump(actual, include_attributes=False) == ast.dump(node, include_attributes=False)
    from wcomr.rv0_fork import object_state, restore_object_state
    from wcomr.mid_coverage import tree_digest
    value = cls(crossattn_emb=torch.ones(1, 3, 4), fps=torch.tensor([16.]),
                use_video_condition=torch.tensor([False]))
    value = value.set_video_condition(torch.ones(1, 2, 2, 2, 4), 0, 0, num_conditional_frames=1)
    value = value.edit_for_inference(is_cfg_conditional=False, num_conditional_frames=1)
    saved = copy.deepcopy(object_state(value)); identity = id(value)
    for tensor in [value.gt_frames, value.crossattn_emb, value.condition_video_input_mask_B_C_T_H_W]:
        tensor.add_(1)
    value.use_video_condition.logical_not_()
    object.__setattr__(value, 'child_only_field', 'drift')
    restore_object_state(value, saved)
    assert id(value) == identity and tree_digest(object_state(value)) == tree_digest(saved)
    assert not hasattr(value, 'child_only_field')
    try: value.gt_frames = None
    except FrozenInstanceError: pass
    else: raise AssertionError('Actual imported condition lost frozen behavior')
    assert not torch.cuda.is_initialized()
    print(json.dumps({'status': 'ACTUAL_VIDEO_CONDITION_IMPORT_ORIGIN_FROZEN_RESTORE_PASS_NO_CUDA',
        'module': name, 'path': str(source.resolve()), 'source_sha256': digest,
        'class_AST_sha256': hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest(),
        'class': cls.__name__, 'frozen_dataclass': True,
        'fields': [f.name for f in fields(cls)], 'CUDA_initialized': False,
        'CPU_import_only_flash_availability_adapter': {
            'installed_version': flash_version, 'installed_package_present': True,
            'version_at_least_2p1': True, 'original_helper_available': availability_before,
            'CUDA_hardware_availability_not_overridden': True,
            'original_helpers_restored': hf_utils.is_flash_attn_2_available is previous[0]
                 and import_utils.is_flash_attn_2_available is previous[1],
            'GPU_runtime_adapter': False, 'kernel_executed': False},
        'CPU_import_only_current_device_default_adapter': {
            'constructor_default_ordinal': 0, 'CUDA_context_created': False,
            'original_current_device_restored': torch.cuda.current_device is previous_current_device,
            'GPU_runtime_adapter': False, 'model_instantiated': False},
        'weights_loaded': False, 'GPU_submissions': 0, 'RV_labels': 0}))


if __name__ == '__main__': main()
