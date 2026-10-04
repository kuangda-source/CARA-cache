"""In-process official sampler suffix controls, not a counterfactual collector.

The existing conditioning closure stays live. This is neither a serialized
checkpoint nor an action router; real model/GPU validation is a separate gate.
"""
import ast
import copy
from dataclasses import is_dataclass
import hashlib
import inspect
import json
import time

import torch

from .decoder_policy import backend_flags
from .full_sampling import CompleteStateRoundtrip
from .mid_coverage import WC_FIELDS, tree_digest

SAMPLER_SHA = 'c6c68f297859e11c76d2921667a29cabfecef3a7b5d3ab831bf9bb54b25b7d87'
WC_CONFIGURATION = (
    'worldcache_enabled', 'worldcache_num_steps', 'worldcache_ret_ratio',
    'worldcache_rel_l1_thresh', 'probe_depth', 'worldcache_osi_enabled',
    'worldcache_flow_enabled', 'worldcache_flow_scale',
    'worldcache_motion_sensitivity', 'worldcache_saliency_enabled',
    'worldcache_saliency_weight', 'worldcache_dynamic_decay',
)


def code_signature(function):
    # marshal embeds reference/interning flags that can change for unchanged
    # code. Canonical primitive fields give a stable semantic code inventory.
    code = function.__code__
    fields = {'bytecode': code.co_code.hex(), 'constants': code.co_consts,
              'names': code.co_names, 'variables': code.co_varnames,
              'freevars': code.co_freevars, 'cellvars': code.co_cellvars,
              'args': code.co_argcount, 'posonly': code.co_posonlyargcount,
              'kwonly': code.co_kwonlyargcount, 'flags': code.co_flags}
    return hashlib.sha256(json.dumps(fields, sort_keys=True, allow_nan=False).encode()).hexdigest()


def official_suffix(source_path):
    """Copy the pinned complete sampler loop verbatim, without initialization."""
    source = source_path.read_bytes()
    if hashlib.sha256(source).hexdigest() != SAMPLER_SHA:
        raise ValueError('RV0 pinned complete sampler source differs')
    tree = ast.parse(source)
    function = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
                    and n.name == 'generate_samples_from_batch')
    loops = [n for n in function.body if isinstance(n, ast.For)]
    if len(loops) != 1:
        raise ValueError('RV0 official complete loop topology differs')
    names = ('self', 'noise', 'latents', 'velocity_fn', 'seed_g', 'timesteps_iter')
    args = ast.arguments(posonlyargs=[], args=[ast.arg(arg=n) for n in names],
                         vararg=None, kwonlyargs=[], kw_defaults=[], kwarg=None,
                         defaults=[])
    fn = ast.FunctionDef(name='suffix', args=args,
                         body=[copy.deepcopy(loops[0]), ast.Return(ast.Name('latents', ast.Load()))],
                         decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
    namespace = {'torch': torch}
    exec(compile(module, str(source_path), 'exec'), namespace)
    namespace['suffix'].official_loop_ast_sha256 = hashlib.sha256(
        ast.dump(loops[0], include_attributes=False).encode()).hexdigest()
    namespace['suffix'].compiled_code_sha256 = code_signature(namespace['suffix'])
    return namespace['suffix']


def object_state(obj):
    return {k: v for k, v in vars(obj).items() if not callable(v)}


def restore_object_state(obj, saved):
    """Restore the captured instance, including NVIDIA frozen conditions.

    Frozen dataclasses contain mutable tensors despite rejecting ordinary
    attribute assignment. Restore only captured instance attributes using
    Python's low-level reconstruction protocol; retain class and identity.
    """
    frozen = is_dataclass(obj) and obj.__dataclass_params__.frozen
    remove = object.__delattr__ if frozen else delattr
    assign = object.__setattr__ if frozen else setattr
    for key in set(object_state(obj)) - set(saved):
        remove(obj, key)
    for key, value in copy.deepcopy(saved).items():
        assign(obj, key, value)


class SamplerSuffixControl:
    """Repeat an unchanged suffix from an actual post-update state.

    Inputs contain both CFG conditions; no hidden teacher, labels or learned
    decision features are generated. Snapshot at an even CFG boundary only.
    """
    def __init__(self, model, latents, noise, generator, velocity_fn, suffix, *, context):
        self.model, self.net, self.scheduler = model, model.net, model.sample_scheduler
        if (type(context) is not tuple or len(context) != 3
                or any(type(v) is not str or not v for v in context)):
            raise ValueError('RV0 explicit request/model/condition context missing')
        if (self.net.is_context_parallel_enabled or model.config.use_lora
                or not model.config.use_kerras_sigma_at_inference
                or not getattr(self.net, 'worldcache_enabled', False)
                or self.net.worldcache_num_steps != 70
                or getattr(self.net, '_wc_refresh_adapter', None) is not None
                or any(m.training for m in self.net.modules())):
            raise ValueError('RV0 requires unchanged single-process eval WC without sparse/LoRA')
        self.completed = self.scheduler._step_index
        if (type(self.completed) is not int or not 1 <= self.completed <= 33
                or len(self.scheduler.timesteps) != 36
                or self.net.cnt != 2 * self.completed
                or not isinstance(generator, torch.Generator)
                or not isinstance(latents, torch.Tensor)
                or not isinstance(noise, torch.Tensor)
                or latents.shape != noise.shape or latents.device != noise.device):
            raise ValueError('RV0 post-update/CFG/grid/latent/generator boundary differs')
        cells = inspect.getclosurevars(velocity_fn).nonlocals
        if (set(cells) != {'self', 'condition', 'uncondition', 'guidance'}
                or cells['self'] is not model or not callable(suffix)
                or not hasattr(suffix, 'official_loop_ast_sha256')
                or getattr(suffix, 'compiled_code_sha256', None) != code_signature(suffix)):
            raise ValueError('RV0 official live velocity closure or suffix source differs')
        self.context, self.velocity_fn, self.suffix = context, velocity_fn, suffix
        self.source_codes = (code_signature(velocity_fn), code_signature(suffix))
        self.conditions = (cells['condition'], cells['uncondition'])
        self.condition_state = [copy.deepcopy(object_state(c)) for c in self.conditions]
        self.configuration = {k: copy.deepcopy(getattr(self.net, k)) for k in
                              WC_CONFIGURATION if hasattr(self.net, k)}
        self.original_wc_keys = {k for k in WC_FIELDS if hasattr(self.net, k)}
        self.noise = noise.detach().clone()
        self.parent_latents = latents
        self.parent_latent_sha256 = tree_digest(latents)
        self.generator = generator
        self.snapshot = CompleteStateRoundtrip(self.net, self.scheduler, latents, [generator])
        self.parent_fingerprint = self.snapshot.fingerprint()
        self.parameters = [(p, p._version) for p in self.net.parameters()]
        self.bindings = (model.denoise, self.net.forward, self.scheduler.step)
        self.immutable = self.immutable_signature()
        self.records = []

    def immutable_signature(self):
        cells = inspect.getclosurevars(self.velocity_fn).nonlocals
        return tree_digest({
            'context': self.context, 'noise': self.noise,
            'conditions': [c.to_dict(skip_underscore=False) for c in self.conditions],
            'guidance': cells['guidance'], 'backend_flags': backend_flags(),
            'configuration': {k: getattr(self.net, k) for k in self.configuration},
            'tensor_kwargs': {k: str(v) for k, v in self.model.tensor_kwargs.items()},
            'use_lora': self.model.config.use_lora,
            'karras': self.model.config.use_kerras_sigma_at_inference,
            'CP': self.net.is_context_parallel_enabled,
        })

    def check_identity(self):
        if any(m.training for m in self.net.modules()):
            raise ValueError('RV0 shared eval mode changed')
        if (self.model.net is not self.net or self.model.sample_scheduler is not self.scheduler
                or self.bindings != (self.model.denoise, self.net.forward, self.scheduler.step)):
            raise ValueError('RV0 model/scheduler/function identity changed')
        if self.source_codes != (code_signature(self.velocity_fn), code_signature(self.suffix)):
            raise ValueError('RV0 live velocity or suffix code changed')
        if tree_digest(self.parent_latents) != self.parent_latent_sha256:
            raise ValueError('RV0 live parent latent changed')
        params = list(self.net.parameters())
        if len(params) != len(self.parameters) or any(p is not old or p._version != version
                for p, (old, version) in zip(params, self.parameters)):
            raise ValueError('RV0 frozen model parameters changed')
        if self.immutable_signature() != self.immutable:
            raise ValueError('RV0 condition/noise/configuration closure drift')

    def restore_parent(self):
        for condition, saved in zip(self.conditions, self.condition_state):
            restore_object_state(condition, saved)
        for key, value in copy.deepcopy(self.configuration).items():
            setattr(self.net, key, value)
        for key in set(WC_FIELDS) - self.original_wc_keys:
            if hasattr(self.net, key): delattr(self.net, key)
        value = self.snapshot.restore()
        with torch.no_grad():
            self.parent_latents.copy_(value)
        self.check_identity()
        if self.snapshot.fingerprint() != self.parent_fingerprint:
            raise ValueError('RV0 parent complete state failed restoration')
        return value

    @torch.no_grad()
    def repeat(self, label):
        return self._execute_suffix(label)

    @torch.no_grad()
    def _execute_suffix(self, label, *, before=None, after=None, metadata=None,
                        status='UNCHANGED_SUFFIX_COMPLETE_NOT_RV_LABEL'):
        if type(label) is not str or not label or any(r['label'] == label for r in self.records):
            raise ValueError('RV0 unique control label required')
        self.check_identity()
        if self.snapshot.fingerprint() != self.parent_fingerprint:
            raise ValueError('RV0 parent changed before repeated suffix')
        record = {'label': label, 'status': 'STARTED', 'completed_updates': self.completed,
                  'planned_remaining_updates': 36 - self.completed,
                  'current_action_intervention': False, 'counterfactual_label': False}
        if metadata: record.update(metadata)
        self.records.append(record)
        started = time.perf_counter()
        try:
            latent = self.restore_parent()
            if before: before()
            result = self.suffix(self.model, self.noise, latent, self.velocity_fn,
                                 self.generator, self.scheduler.timesteps[self.completed:])
            self.check_identity()
            if self.scheduler._step_index != 36 or self.net.cnt != 2:
                raise ValueError('RV0 suffix did not complete original grid and WC70 tail')
            if after: record.update(after())
            final = CompleteStateRoundtrip(self.net, self.scheduler, result, [self.generator])
            record.update(status=status,
                          final_latent_sha256=tree_digest(result),
                          final_state_components=final.components(),
                          final_state_sha256=final.fingerprint())
            return result.detach().clone()
        except BaseException as error:
            record.update(status='TECH_BLOCKED', error_type=type(error).__name__, error=str(error))
            raise
        finally:
            record['control_wall_seconds'] = time.perf_counter() - started
            self.restore_parent()
            record['parent_restored'] = True

    def snapshot_storage(self):
        """Count owned copies, without CPU transfer or allocating more tensors.

        Physical storage is deduplicated; values describe this state only and
        are not a production peak-VRAM bound or a Toy-to-GPU extrapolation.
        """
        import numpy as np
        from collections.abc import Mapping
        s = self.snapshot
        values = [s.output, s.net_state, s.solver_state,
                  {k: v[1] for k, v in s.buffers.items()}, self.condition_state,
                  self.noise, s.cpu_rng, s.cuda_rng, [v for _, v in s.generators]]
        values.append(s.numpy_rng)
        logical, physical, seen = {}, {}, set()
        def walk(value):
            if isinstance(value, torch.Tensor):
                device = str(value.device)
                logical[device] = logical.get(device, 0) + value.numel() * value.element_size()
                storage = value.untyped_storage()
                key = (device, storage.data_ptr(), storage.nbytes())
                if key not in seen:
                    seen.add(key); physical[device] = physical.get(device, 0) + storage.nbytes()
            elif isinstance(value, np.ndarray):
                logical['numpy'] = logical.get('numpy', 0) + value.nbytes
            elif isinstance(value, Mapping):
                for v in value.values(): walk(v)
            elif isinstance(value, (list, tuple)):
                for v in value: walk(v)
        walk(values)
        return {'logical_tensor_bytes_by_device': logical,
                'unique_owned_tensor_storage_bytes_by_device': physical,
                'snapshot_copies_only_not_live_weights_or_peak': True}
