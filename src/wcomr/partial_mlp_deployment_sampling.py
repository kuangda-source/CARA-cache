"""Actual P0 outputs enter the ordinary full guarded UniPC trajectory.

The full-GEMM inactive-substitution reference is a paid diagnostic control.
Explicit AST replacements preserve the parent sampler/condition/guarded return.
Neither CPU mock files nor instrumented timings establish real video benefits.
"""
import ast
import copy
import hashlib
import inspect
import math
from pathlib import Path
from textwrap import dedent

import torch

from . import cfg_guided_w1_sampling as parent
from .cfg_paired_probe_native_policy import NativePolicyPairedExecutor
from .cfg_paired_probe_production import compile_production
from .cfg_ra_calibration import SharedSchedulePairExecutor
from .partial_mlp_deployment import PartialDeployment, PartialDeploymentPair, compile_partial_deployment, D_STEPS
from .partial_mlp_deployment_state import DeploymentRoundtrip, plain, tensor_bytes
from .mid_coverage import tree_digest

LAYERS = (4, 10, 16, 22)
# Exercise P-created sources, consecutive P, C reuse, late reset, then actual D.
# This is a CPU integration schedule, not a new scientific scheduling policy.
P_STEPS = (9, 10, 15, 16, 21, 22, 27, 28, 33, 34)
METHODS = ('SOURCE_D6', 'TRUE_D_REFERENCE', 'OFF', 'DENSE_CONTROL',
    'ROTATION_050', 'REF_ROTATION_050', 'RANDOM_050', 'REF_RANDOM_050',
    'ROTATION_075', 'REF_ROTATION_075', 'RANDOM_075', 'REF_RANDOM_075', 'FULL_P_DECLARED_P')


class SamplingOwner:
    def __init__(self, model, *, method, context, runtime, wc, rf):
        if method not in METHODS:
            raise ValueError('One registered full-sampler method required')
        self.model, self.net, self.method, self.context = model, model.net, method, context
        self.reference = method.startswith('REF_')
        self.deployment = None
        self.cache, self.hooks, self.linear_rows = {}, [], []
        self.step = 0
        if method in ('SOURCE_D6', 'TRUE_D_REFERENCE') or self.reference:
            _, denoise, core = compile_production(runtime, wc, rf)
        else:
            self.deployment = PartialDeployment(model, method=method, context=context,
                layers=LAYERS, p_steps=P_STEPS)
            _, denoise, core = compile_partial_deployment(runtime, wc, rf, self.deployment)
        self.compiler = dict(core)
        self.base = NativePolicyPairedExecutor(model, denoise, torch,
            wc_forward=wc.worldcache_mini_train_dit_forward,
            rf_denoise=rf.Video2WorldModelRectifiedFlow.denoise)
        self.executor = (PartialDeploymentPair(self.base, self.deployment) if self.deployment
                         else SharedSchedulePairExecutor(self.base))
        self.choose = self._select
        if self.reference:
            for layer in LAYERS:
                def substitute(module, inputs, full, l=layer):
                    key = (l, int(self.net.cnt) % 2)
                    value = full
                    if self.step in P_STEPS:
                        if key not in self.cache:
                            raise ValueError('Independent full-GEMM reference has no past projection')
                        tokens = math.prod(full.shape[:-1])
                        ids = self.reference_indices(tokens)
                        value = self.cache[key].reshape(tokens, full.shape[-1]).clone()
                        value[ids] = full.reshape(tokens, full.shape[-1])[ids]
                        value = value.reshape_as(full)
                    self.cache[key] = value.detach().clone()
                    return value
                self.hooks.append(self.net.blocks[layer].mlp.register_forward_hook(substitute))
        for layer in LAYERS:
            for name in ('layer1', 'layer2'):
                def observe(module, inputs, l=layer, n=name):
                    self.linear_rows.append({'step': self.step, 'slot': int(self.net.cnt) % 2,
                        'layer': l, 'Linear': n, 'rows': math.prod(inputs[0].shape[:-1])})
                self.hooks.append(getattr(self.net.blocks[layer].mlp, name).register_forward_pre_hook(observe))

    @property
    def history(self):
        return self.deployment.history if self.deployment else self.executor.history

    def _select(self, packets):
        raise ValueError('The bound inner paid-probe selector must be used')

    def pair(self, noise, latent, timestep, conditions, choose):
        if choose is not self.choose:
            raise ValueError('Original full-sampler P0 owner selector required')
        self.step = len(self.history)+1
        if not self.deployment:
            self.executor.forced_action = ('DD' if self.step in P_STEPS
                and (self.reference or self.method == 'TRUE_D_REFERENCE') else None)
        value = self.executor.pair(noise, latent, timestep, conditions, self.executor.choose)
        if not self.deployment and self.net.cnt == 0:
            self.cache.clear()
        return value

    def reference_indices(self, tokens):
        # Independent index construction; do not call candidate block_indices.
        method = self.method.removeprefix('REF_')
        full_blocks = tokens//128
        if tokens % 128 or full_blocks < 2:
            raise ValueError('Full-GEMM CPU reference requires registered full-block layout')
        count = math.floor(full_blocks*(.5 if method.endswith('050') else .75))
        if method.startswith('RANDOM'):
            key = 'P0-DEPLOYMENT-CORE-R1:'+repr(self.context)+':'+str(self.step)
            seed = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big') % (2**63-1)
            blocks = torch.randperm(full_blocks, generator=torch.Generator().manual_seed(seed))[:count].tolist()
        else:
            start = P_STEPS.index(self.step)*count
            blocks = [(start+i) % full_blocks for i in range(count)]
        return torch.tensor(sorted(b*128+i for b in blocks for i in range(128)))

    def check_healthy(self):
        d = self.deployment
        if (torch.is_grad_enabled() or self.base.running or self.base.poisoned
                or self.model.net is not self.net
                or (d is not None and (d.current is not None or d.poisoned
                    or (d.core is not None and (d.core._pair is not None
                        or d.core._slot is not None or d.core.poisoned or not d.core._original))))
                or (d is None and self.executor.running)):
            raise ValueError('Only inactive healthy installed P0 sampling boundaries can restore')

    def installation(self):
        return (id(self), id(self.model), id(self.net), self.method, self.context,
            tuple((id(p), p._version) for p in self.net.parameters()),
            tuple((l, self.net.blocks[l].mlp.forward) for l in LAYERS),
            tuple(id(h) for h in self.hooks))

    def own_state(self):
        data = {'step': self.step, 'reference_cache': self.cache, 'Linear_inputs': self.linear_rows}
        if self.deployment:
            d = self.deployment
            data['deployment'] = {k: getattr(d, k) for k in ('working', 'history', 'epoch',
                'opportunities', '_condition_identity', '_noise_identity', '_layout_identity')}
            data['dense_calibrators'] = [dict(vars(c)) for c in d.dense]
            data['pair_last'], data['base_last'] = self.executor.last, self.base.last
            data['projection'] = (None if d.core is None else
                {'cache': d.core.cache, 'records': d.core.records, 'last_step': d.core.last_step})
        else:
            data['shared'] = self.executor.snapshot()
        return data

    def restore_own_state(self, data):
        self.step, self.cache, self.linear_rows = data['step'], data['reference_cache'], data['Linear_inputs']
        if self.deployment:
            d = self.deployment
            for k, v in data['deployment'].items():
                setattr(d, k, v)
            for c, saved in zip(d.dense, data['dense_calibrators']):
                vars(c).clear(); vars(c).update(saved)
            self.executor.last, self.base.last = data['pair_last'], data['base_last']
            if d.core is not None:
                d.core.cache = data['projection']['cache']
                d.core.records = data['projection']['records']
                d.core.last_step = data['projection']['last_step']
        else:
            self.executor.restore(data['shared'])

    def fingerprint(self):
        return tree_digest(plain(self.own_state()))

    def checkpoint(self, physical, gate, config):
        self.check_healthy()
        remaining = config['logical_copy_cap_bytes']-gate['logical_tensor_copy_bytes']
        # Count every additional tensor conservatively, including aliases, and
        # admit both restore copies before cloning any additional live state.
        extra_bytes = tensor_bytes(self.own_state())
        if extra_bytes > remaining:
            raise ValueError('Combined physical/P0 checkpoint exceeds logical copy cap')
        if gate['GPU_logical_copy_bytes']:
            required = gate['required_GPU_headroom_bytes']+2*extra_bytes
            if torch.cuda.mem_get_info()[0] < required:
                raise ValueError('Insufficient live GPU headroom for combined P0 checkpoint')
        own = DeploymentRoundtrip(self, logical_copy_cap_bytes=remaining)
        before = physical.fingerprint()
        if config.get('CPU_mutate_owned_state_before_restore', False):
            # Explicit successful-checkpoint perturbations, no failed-pair repair.
            self.step = -99
            self.linear_rows.append({'injected_checkpoint_only': True})
            for t in self.cache.values():
                t.add_(123)
            if self.deployment:
                d = self.deployment
                d.epoch = -99; d.opportunities = -99
                d.working = [None, None]; d.history.clear()
                for c in d.dense:
                    c.numerator = 999; c.pairs = 999
                    for a in c.anchors:
                        a.probe.add_(123); a.residual.add_(123)
                if d.core is not None:
                    d.core.records.clear(); d.core.last_step = -99
                    for c in d.core.cache.values():
                        c.value.add_(123); c.updated_at.fill_(-99); c.source.fill_(9)
            else:
                self.executor.history.clear(); self.executor.anchor = -99
        physical.restore()
        own.restore()
        if physical.fingerprint() != before:
            raise ValueError('Ordinary sampler physical checkpoint restoration differs')
        return {'additional_state_bytes': own.bytes, 'complete_additional_state_restored': True,
            'physical_state_restored': True, 'fingerprint': own.origin,
            'checkpoint_perturbation_executed': bool(config.get('CPU_mutate_owned_state_before_restore', False)),
            'arbitrary_failed_pair_or_serialized_pipeline_recovery_claim': False}

    @torch.no_grad()
    def finish(self):
        self.check_healthy()
        if len(self.history) != 36:
            raise ValueError('Complete ordinary P0 full36 path required')
        return {'method': self.method, 'fixed_P_steps': list(P_STEPS),
            'deployment': self.deployment.finish() if self.deployment else None,
            'Linear_inputs': copy.deepcopy(self.linear_rows), 'complete_pairs': 36,
            'independent_full_GEMM_reference': self.reference}

    def close(self):
        for h in self.hooks:
            h.remove()
        if self.deployment:
            self.deployment.close()


def _owner(model, method, context, runtime, wc, rf):
    return SamplingOwner(model, method=method, context=context, runtime=runtime, wc=wc, rf=rf)


def _derive():
    source = dedent(inspect.getsource(parent.run_batch))
    # Whole explicit owner binding replaces the original score-only collector.
    start = source.index('                collector = GuidedW1Collector(')
    end = source.index('                factory,proof = compile_velocity', start)
    old_owner = source[start:end]
    bindings = """                collector = _owner(model,collect,context,runtime,wc,rf_module)
                executor = collected = collector
                core = collector.compiler
"""
    replacements = [
        ('planned_parent_paths=8,planned_origins=8,planned_post_RF_branch_tensors=64', 'planned_parent_paths=52,planned_origins=0,planned_post_RF_branch_tensors=0'),
        ("calibration_collection_policy='UNIFORM_SHARED_D6'", "calibration_collection_policy='P0_FIXED_D6_CHAIN_INTEGRATION'"),
        ('selected_steps=list(SELECTED_STEPS)', 'selected_steps=list(_P_STEPS)'),
        ('for collect in (False,True):', 'for collect in _METHODS:'),
        ("label = sample.name+('_COLLECT_ON' if collect else '_COLLECT_OFF')", "label = sample.name+'_'+collect"),
        (old_owner, bindings),
        ("row['origins'] = collector.records", "row['origins'] = []"),
        ("row.setdefault('capture_gates',[]).append({'step':step,**gate})", "row.setdefault('capture_gates',[]).append({'step':step,**gate})\n                        row.setdefault('P0_roundtrips',[]).append({'step':step,**collector.checkpoint(snapshot,gate,config)})"),
        ('verdict=verify_batch(state)', 'verdict=_verify_batch(state)'),
        ('                    hooks.close()', '                    collector.close()\n                    hooks.close()')]
    changed = source
    for old, new in replacements:
        if changed.count(old) != 1:
            raise ValueError('P0 full-sampler explicit AST transformation site differs: '+old[:90])
        changed = changed.replace(old, new, 1)
    inverse = changed
    for old, new in reversed(replacements):
        if inverse.count(new) != 1:
            raise ValueError('P0 full-sampler inverse transformation ambiguity')
        inverse = inverse.replace(new, old, 1)
    if ast.dump(ast.parse(inverse), include_attributes=False) != ast.dump(ast.parse(source), include_attributes=False):
        raise ValueError('Ordinary pipeline changed outside explicit P0 ownership/scope/checkpoints')
    namespace = {**vars(parent), '_owner': _owner, '_METHODS': METHODS,
        '_P_STEPS': P_STEPS, '_verify_batch': verify_batch}
    exec(compile(changed, str(Path(__file__))+'#full-P0-deployment', 'exec'), namespace)
    return namespace['run_batch'], {'inverse_AST_equal': True, 'explicit_sites': len(replacements),
        'parent_source_sha256': hashlib.sha256(Path(parent.__file__).read_bytes()).hexdigest(),
        'ordinary_full_UniPC_guarded_return_preserved': True}


def verify_batch(state):
    if (state.get('planned_parent_paths') != 52 or state.get('planned_origins') != 0
            or state.get('planned_post_RF_branch_tensors') != 0 or len(state.get('requests', [])) != 4):
        raise ValueError('Full four-request thirteen-method P0 scope required')
    for request in state['requests']:
        rows = request['paths']
        if len(rows) != 13 or tuple(r['collect'] for r in rows) != METHODS:
            raise ValueError('Every registered method/control/reference must complete for every request')
        for row in rows:
            method = row['collect']
            p = method not in ('SOURCE_D6', 'OFF', 'DENSE_CONTROL')
            ref = method.startswith('REF_') or method == 'TRUE_D_REFERENCE'
            actions = ['DD' if s in D_STEPS else ('DD' if ref else 'PP') if p and s in P_STEPS else 'CC' for s in range(1, 37)]
            if (row['status'] != 'COMPLETE_PARENT_PATH' or row['actions'] != actions
                    or len(row['guided_sha256']) != 36 or len(row['solver_returns']) != 36
                    or row['counters'] != list(range(0, 70, 2))+[0]
                    or row['origins'] or [c['step'] for c in row['checkpoints']] != list(parent.STATE_STEPS)
                    or len(row['P0_roundtrips']) != 4
                    or any(not c['complete_additional_state_restored'] or not c['physical_state_restored'] for c in row['P0_roundtrips'])
                    or row['conditions_before'] != row['conditions_after']
                    or row['condition_fields_before'] != row['condition_fields_after']
                    or not row['all_modules_eval'] or not row['parameter_versions_unchanged']
                    or row['collection_complete']['complete_pairs'] != 36
                    or row['vector_artifact']['tensor_sha256']['guided'] != row['guided_list_sha256']
                    or row['vector_artifact']['tensor_sha256']['final_latent'] != row['final_latent_sha256']):
                raise ValueError('Complete ordinary P0 route/state/conditions/output missing')
            d = row['collection_complete']['deployment']
            if d is not None:
                if (d['teacher_calls'] != 0 or d['extra_candidate_heads'] != 0
                        or len(d['history']) != 36 or row['own_history'] != d['history']):
                    raise ValueError('Unexpected P0 teacher or incomplete deployed source history')
                for h in d['history']:
                    if h['action'] != 'DD' and h['true_D_before'] != h['true_D_after']:
                        raise ValueError('C/P contaminated actual D-only calibration')
                    if h['action'] == 'PP' and any(v['kind'] != 'P' or v['creation_error'] != 'UNKNOWN_NOT_ZERO'
                            or v['RA_zero_risk_reset_allowed'] for v in h['working_sources']):
                        raise ValueError('P was incorrectly treated as actual dense or zero-risk source')
        if len(request['prepared_input_calls']) != 13 or any(c['prepared'] != request['prepared_input_calls'][0]['prepared'] for c in request['prepared_input_calls']):
            raise ValueError('Actual prepared input must remain identical across all methods')
    return {'complete_paths': 52, 'solver_updates': 1872, 'normal_net_calls': 3744,
        'teacher_calls': 0, 'ordinary_full_sampler_executed': True,
        'real_Cosmos_video_quality_or_clean_speed_claim': False}


run_batch, COMPILER_PROOF = _derive()


def audit_vectors(state, root, loader, expected_shape):
    verify_batch(state)
    root = Path(root).resolve(); files = []; partial_comparisons = 0
    for request in state['requests']:
        values = {}
        for row in request['paths']:
            art = row['vector_artifact']; p = Path(art['path']).resolve()
            if not p.is_relative_to(root) or p.suffix != '.pt':
                raise ValueError('P0 actual vector artifact outside output')
            raw = p.read_bytes()
            if len(raw) != art['bytes'] or hashlib.sha256(raw).hexdigest() != art['sha256']:
                raise ValueError('Actual P0 vector changed or truncated')
            x = loader(p, map_location='cpu', weights_only=True)
            if (set(x) != {'guided', 'final_latent'} or len(x['guided']) != 36
                    or any(not isinstance(t, torch.Tensor) or t.dtype != torch.float32
                        or list(t.shape) != expected_shape or not bool(torch.isfinite(t).all())
                        for t in x['guided']+[x['final_latent']])
                    or {k: tree_digest(v) for k, v in x.items()} != art['tensor_sha256']
                    or [tree_digest(t) for t in x['guided']] != row['guided_sha256']):
                raise ValueError('Full actual P0 tensor identities or geometry differ')
            values[row['collect']] = x
            files.append({'path': str(p), 'bytes': len(raw), 'sha256': art['sha256']})
        def pair(actual, ref, direct):
            a = values[actual]; b = values[ref]
            for x, y in zip(a['guided']+[a['final_latent']], b['guided']+[b['final_latent']]):
                if direct:
                    if not torch.equal(x, y):
                        raise ValueError('Complete P0 dense/OFF trajectory equality control differs')
                else:
                    torch.testing.assert_close(x, y, rtol=1e-5, atol=2e-6)
        pair('OFF', 'SOURCE_D6', True); pair('DENSE_CONTROL', 'SOURCE_D6', True)
        pair('FULL_P_DECLARED_P', 'TRUE_D_REFERENCE', True)
        for mode in ('ROTATION_050', 'RANDOM_050', 'ROTATION_075', 'RANDOM_075'):
            pair(mode, 'REF_'+mode, False); partial_comparisons += 1
    if len(files) != 52 or {str(p.resolve()) for p in root.rglob('*.pt')} != {v['path'] for v in files}:
        raise ValueError('Complete52 tensor files required without omission/extras')
    return {'actual_guided_reloaded': 1872, 'actual_latents_reloaded': 52,
        'independent_partial_full_trajectory_comparisons': partial_comparisons,
        'dense_and_OFF_controls_direct_equal': True, 'files': files,
        'CPU_reference_rtol': 1e-5, 'CPU_reference_atol': 2e-6,
        'real_video_quality_or_clean_speed_claim': False}
