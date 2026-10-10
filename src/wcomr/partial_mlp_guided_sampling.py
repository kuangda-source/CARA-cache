"""Ordinary full sampler with the existing P0 controls and all five A modes.

P remains approximate provenance; the legacy C readout uses actual D only.
No source-risk selector, teacher or real video benefit is implied by CPU QA.
"""
import ast
import copy
import hashlib
import inspect
from pathlib import Path
from textwrap import dedent
import types

import torch

from . import partial_mlp_deployment_sampling as p0
from .partial_mlp_guided_readout import GuidedPartialDeployment
from .partial_mlp_deployment_state import DeploymentRoundtrip, tensor_bytes
from .cfg_guided_w1_deployment import METHODS as A_MODES, alpha_at

A_METHODS = tuple('A_P0_'+v for v in A_MODES)
METHODS = p0.METHODS+A_METHODS


class GuidedSamplingOwner(p0.SamplingOwner):
    def __init__(self, model, *, method, context, runtime, wc, rf):
        self.a_method = method.removeprefix('A_P0_')
        if method not in A_METHODS:
            raise ValueError('Explicit registered A plus ROTATION050 P0 method required')
        def constructor(*args, **kwargs):
            return GuidedPartialDeployment(*args, a_method=self.a_method, **kwargs)
        original = p0.SamplingOwner.__init__
        if original.__closure__:
            raise ValueError('P0 owner constructor gained an unbound closure')
        # Identical constructor code, one explicit class factory binding. No
        # mutation of the running P0 module or its namespace is performed.
        derived = types.FunctionType(original.__code__,
            {**original.__globals__, 'PartialDeployment': constructor},
            original.__name__, original.__defaults__)
        derived.__kwdefaults__ = original.__kwdefaults__
        derived(self, model, method='ROTATION_050', context=context,
                runtime=runtime, wc=wc, rf=rf)
        self.head_calls = []
        def observe_head(module, inputs, value):
            self.head_calls.append({'step': self.step, 'slot': int(self.net.cnt) % 2})
        self.hooks.append(self.net.final_layer.register_forward_hook(observe_head))

    def installation(self):
        r = self.deployment.readout
        return super().installation()+(self.a_method, r.method, r.context, id(r), id(r.calibrators),
                                      self.deployment.method, self.deployment.context)

    def check_healthy(self):
        super().check_healthy()
        r = self.deployment.readout
        if r.current is not None or r.poisoned or r.calibrators is not self.deployment.dense:
            raise ValueError('Healthy bound A history and same D-only calibrators required')

    def own_state(self):
        data = super().own_state()
        r = self.deployment.readout
        data['A_readout'] = {'completed': r.completed, 'history': r.history}
        data['actual_head_calls'] = self.head_calls
        return data

    def restore_own_state(self, data):
        super().restore_own_state(data)
        r = self.deployment.readout
        r.completed, r.history = data['A_readout']['completed'], data['A_readout']['history']
        self.head_calls = data['actual_head_calls']

    def checkpoint(self, physical, gate, config):
        self.check_healthy()
        remaining = config['logical_copy_cap_bytes']-gate['logical_tensor_copy_bytes']
        additional = tensor_bytes(self.own_state())
        if additional > remaining:
            raise ValueError('Combined A/P0 checkpoint exceeds remaining logical budget')
        if gate['GPU_logical_copy_bytes'] and torch.cuda.mem_get_info()[0] < gate['required_GPU_headroom_bytes']+2*additional:
            raise ValueError('Insufficient live GPU headroom for complete A/P0 state')
        own = DeploymentRoundtrip(self, logical_copy_cap_bytes=remaining)
        before = physical.fingerprint()
        if config.get('CPU_mutate_owned_state_before_restore', False):
            self.deployment.readout.completed = -99
            self.deployment.readout.history.clear()
            self.deployment.opportunities = -99
            self.deployment.working = [None, None]
            self.head_calls.append({'injected_checkpoint_only': True})
        physical.restore(); own.restore()
        if physical.fingerprint() != before:
            raise ValueError('A/P0 physical sampler state failed complete restoration')
        return {'additional_state_bytes': own.bytes, 'complete_additional_state_restored': True,
            'physical_state_restored': True, 'fingerprint': own.origin,
            'checkpoint_perturbation_executed': bool(config.get('CPU_mutate_owned_state_before_restore', False)),
            'A_completed_and_history_perturbation_restored': True,
            'arbitrary_failed_pair_or_serialized_pipeline_recovery_claim': False}

    @torch.no_grad()
    def finish(self):
        result = super().finish()
        heads = result['deployment']['A_readout']['extra_candidate_heads']
        if len(self.head_calls) != 72+heads:
            raise ValueError('Actual original and candidate head calls do not match accounted cost')
        result['actual_original_plus_candidate_heads'] = copy.deepcopy(self.head_calls)
        return result


def owner(model, method, context, runtime, wc, rf):
    cls = GuidedSamplingOwner if method in A_METHODS else p0.SamplingOwner
    return cls(model, method=method, context=context, runtime=runtime, wc=wc, rf=rf)


def verify_batch(state):
    if state.get('planned_parent_paths') != 72 or len(state.get('requests', [])) != 4:
        raise ValueError('Full four-request eighteen-method A/P0 batch required')
    # Verify every original source/control/reference with the accepted P0
    # verifier. Only its declared subset denominator and input replay count
    # differ; the real full72 scope is checked separately, never discarded.
    base = copy.deepcopy(state); base['planned_parent_paths'] = 52
    for request in base['requests']:
        request['paths'] = request['paths'][:13]
        request['prepared_input_calls'] = request['prepared_input_calls'][:13]
    p0.verify_batch(base)
    for request in state['requests']:
        rows = request['paths']
        if len(rows) != 18 or tuple(r['collect'] for r in rows) != METHODS:
            raise ValueError('All thirteen P0 controls and five A modes required')
        if len(request['prepared_input_calls']) != 18 or any(c['prepared'] != request['prepared_input_calls'][0]['prepared'] for c in request['prepared_input_calls']):
            raise ValueError('Same actual prepared inputs required across every A/P0 mode')
        for row in rows[13:]:
            a = row['collect'].removeprefix('A_P0_')
            d = row['collection_complete']['deployment']; r = d['A_readout']
            if (row['status'] != 'COMPLETE_PARENT_PATH' or len(row['guided_sha256']) != 36
                    or len(row['solver_returns']) != 36 or row['counters'] != list(range(0, 70, 2))+[0]
                    or row['actions'] != rows[4]['actions'] or row['origins']
                    or len(row['P0_roundtrips']) != 4
                    or any(not x['complete_additional_state_restored'] or not x['physical_state_restored']
                        or not x['A_completed_and_history_perturbation_restored'] for x in row['P0_roundtrips'])
                    or [x['step'] for x in row['checkpoints']] != list(p0.parent.STATE_STEPS)
                    or row['conditions_before'] != row['conditions_after']
                    or row['condition_fields_before'] != row['condition_fields_after']
                    or not row['all_modules_eval'] or not row['parameter_versions_unchanged']
                    or d['teacher_calls'] or r['teacher_calls'] or r['extra_candidate_deep_blocks']
                    or len(row['collection_complete']['actual_original_plus_candidate_heads']) != 72+r['extra_candidate_heads']
                    or r['method'] != a or len(r['history']) != 36
                    or row['own_history'] != d['history']
                    or row['vector_artifact']['tensor_sha256']['guided'] != row['guided_list_sha256']
                    or row['vector_artifact']['tensor_sha256']['final_latent'] != row['final_latent_sha256']):
                raise ValueError('Complete A/P0 deployed output/state/conditions/heads missing')
            heads = 0
            for h, ah in zip(d['history'], r['history']):
                if (h['action'] != ah['action'] or ah['step'] != h['step']
                        or ah['shared_alpha'] != alpha_at(a, h['step'])
                        or h['A_readout'] != ah or not h['semantic_P_bypasses_legacy_D_observer']
                        or h['extra_candidate_heads'] != ah['extra_heads']
                        or ah['C_or_P_observation_updates_D_anchor']):
                    raise ValueError('A/P0 semantic action, strength or real head accounting differs')
                if h['action'] != 'DD' and h['true_D_before'] != h['true_D_after']:
                    raise ValueError('A/P0 C/P contaminated actual D calibration')
                if h['action'] == 'PP':
                    if ah['branch_status'] != ['P_NOT_ACTUAL_D']*2 or ah['extra_heads']:
                        raise ValueError('P invoked legacy A D observer or unnecessary A head')
                    if any(s['kind'] != 'P' or s['RA_zero_risk_reset_allowed'] or s['creation_error'] != 'UNKNOWN_NOT_ZERO' for s in h['working_sources']):
                        raise ValueError('Composite P cannot become zero-risk actual D')
                if h['action'] == 'CC':
                    if ah['working_source_kind'] != [s['kind'] for s in h['working_sources']]:
                        raise ValueError('A used a different actual working source')
                    if any(s >= h['step'] for branch in ah['past_D_steps'] for s in branch):
                        raise ValueError('A may read only strictly past actual D on C')
                    if a == 'OFF' and ah['extra_heads']:
                        raise ValueError('OFF must not execute candidate head')
                heads += ah['extra_heads']
            if heads != r['extra_candidate_heads'] or heads != d['extra_candidate_heads']:
                raise ValueError('All original plus A head costs must be retained')
    return {'complete_paths': 72, 'solver_updates': 2592, 'normal_net_calls': 5184,
        'teacher_calls': 0, 'A_P0_real_outputs_enter_full_UniPC': True,
        'real_Cosmos_video_quality_or_clean_speed_claim': False}


def derive():
    # Preserve the accepted P0 transformation with one explicit full-scope
    # constant change. Its own inverse still checks the original guarded body.
    original = dedent(inspect.getsource(p0._derive))
    old, new = 'planned_parent_paths=52,planned_origins=0', 'planned_parent_paths=72,planned_origins=0'
    if original.count(old) != 1:
        raise ValueError('P0 full-scope transformation site differs')
    changed = original.replace(old, new, 1)
    if ast.dump(ast.parse(changed.replace(new, old, 1)), include_attributes=False) != ast.dump(ast.parse(original), include_attributes=False):
        raise ValueError('Combined transformation changed outside full scope')
    ns = {**p0._derive.__globals__, '_owner': owner, 'METHODS': METHODS,
        'verify_batch': verify_batch, '__file__': __file__}
    exec(compile(changed, __file__+'#combined-sampler-derivation', 'exec'), ns)
    batch, proof = ns['_derive']()
    return batch, {**proof, 'P0_derivation_inverse_AST_equal': True,
        'P0_derivation_source_sha256': hashlib.sha256(Path(p0.__file__).read_bytes()).hexdigest(),
        'explicit_scope_change': [52, 72], 'original_P0_controls_retained': 13,
        'additional_A_modes': list(A_MODES)}


run_batch, COMPILER_PROOF = derive()


def audit_vectors(state, root, loader, expected_shape):
    verify_batch(state)
    root = Path(root).resolve(); files = []; references = 0
    for request in state['requests']:
        loaded = {}
        for row in request['paths']:
            art = row['vector_artifact']; path = Path(art['path']).resolve()
            if not path.is_relative_to(root) or path.suffix != '.pt':
                raise ValueError('A/P0 vector outside actual output')
            raw = path.read_bytes()
            if len(raw) != art['bytes'] or hashlib.sha256(raw).hexdigest() != art['sha256']:
                raise ValueError('Actual A/P0 vector changed or truncated')
            value = loader(path, map_location='cpu', weights_only=True)
            if (set(value) != {'guided', 'final_latent'} or len(value['guided']) != 36
                    or any(not isinstance(t, torch.Tensor) or t.dtype != torch.float32 or list(t.shape) != expected_shape
                        or not bool(torch.isfinite(t).all()) for t in value['guided']+[value['final_latent']])
                    or {k: p0.tree_digest(v) for k, v in value.items()} != art['tensor_sha256']
                    or [p0.tree_digest(t) for t in value['guided']] != row['guided_sha256']):
                raise ValueError('Complete actual A/P0 vector geometry or hashes differ')
            loaded[row['collect']] = value
            files.append({'path': str(path), 'bytes': len(raw), 'sha256': art['sha256']})
        pairs = [('OFF', 'SOURCE_D6'), ('DENSE_CONTROL', 'SOURCE_D6'),
                 ('FULL_P_DECLARED_P', 'TRUE_D_REFERENCE'), ('A_P0_OFF', 'ROTATION_050')]
        for a, b in pairs:
            x, y = loaded[a], loaded[b]
            if not all(torch.equal(i, j) for i, j in zip(x['guided']+[x['final_latent']], y['guided']+[y['final_latent']])):
                raise ValueError('A/P0 complete dense or OFF parity control differs')
        for mode in ('ROTATION_050', 'RANDOM_050', 'ROTATION_075', 'RANDOM_075'):
            x, y = loaded[mode], loaded['REF_'+mode]
            for i, j in zip(x['guided']+[x['final_latent']], y['guided']+[y['final_latent']]):
                torch.testing.assert_close(i, j, rtol=1e-5, atol=2e-6)
            references += 1
    if len(files) != 72 or {str(p.resolve()) for p in root.rglob('*.pt')} != {x['path'] for x in files}:
        raise ValueError('All72 original and combined output files required')
    return {'actual_guided_reloaded': 2592, 'actual_latents_reloaded': 72,
        'independent_partial_full_trajectory_comparisons': references,
        'A_OFF_matches_actual_P0_without_substitution': True, 'files': files,
        'real_Cosmos_video_quality_or_clean_speed_claim': False}
