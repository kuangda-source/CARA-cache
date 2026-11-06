"""Complete S collection matrix and OFF/ON witnesses; no dispatch or fitting.

The ten-path matrix is the original upper scope before an independent reuse
audit. The caller owns model loading, admission, resetting and final release.
Only metadata survives a request; full guided/video tensors are hashed before
the next request, with that diagnostic work included in the eventual quote.
"""
import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path

from .policy_generator_r1.interval_grammar import Edge, compile_policy
from .sq_risk_r1 import TARGETS
from .sq_s_sources_r1 import PARENTS

FIT = ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632', 'human_199')
VIDEO_HELPER_PATH = 'cosmos_predict2/_src/imaginaire/visualize/video.py'
VIDEO_HELPER_SHA = 'fef61fb22361c4f571369faf5397c3ce5618671b1a92a8215bc469a21f9bc236'
COUNTS = dict(paths=10, warm_paths=2, OFF_paths=4, ON_paths=4,
    parent_solver_pairs=360, parent_Dense_pairs=220, parent_C_pairs=140,
    extra_Dense_teacher_pairs=56, extra_C_shadow_pairs=52,
    total_pairs=468, total_branch_readouts=936, moment_rows=108,
    F19_raw_states=8, unique_raw_anchors=24, extra_Dense_hidden_head_pairs=0)


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def make_scope(profile, prompts=FIT, *, cpu_fixture=False):
    require(type(cpu_fixture) is bool, 'Explicit CPU fixture flag required')
    prompts = tuple(prompts)
    require(len(prompts) == 2 and len(set(prompts)) == 2
            and all(type(p) is str and p for p in prompts), 'Two fixed distinct inputs required')
    require(cpu_fixture or prompts == FIT, 'Only the original two exposed FIT inputs')
    policies = {}
    for parent, dense in PARENTS.items():
        bounds = dense + (37,)
        policies[parent] = compile_policy(profile, [Edge(a, b) for a, b in zip(bounds, bounds[1:])])
    slots = []
    for parent in PARENTS:
        slots.append(dict(id='warm-' + parent, prompt=prompts[0], parent=parent,
                          purpose='WARM', enabled=False))
    for pi, prompt in enumerate(prompts):
        for hi, parent in enumerate(PARENTS):
            # Fix both observer orders before collection; no time/score sorting.
            order = (False, True) if (pi + hi) % 2 == 0 else (True, False)
            for enabled in order:
                slots.append(dict(id=f'p{pi}-{parent}-' + ('ON' if enabled else 'OFF'),
                    prompt=prompt, parent=parent, purpose='CONTROL', enabled=enabled))
    scope = dict(schema='SQ_S_WHOLE_UPPER_COLLECTION_R1', CPU_fixture_only=cpu_fixture,
        prompts=list(prompts), profile=asdict(profile), policies=policies, slots=slots,
        counts=dict(COUNTS), raw_parent='F19-C', raw_steps=[9, 22, 33, 35],
        reuse_audit_required_before_GPU_quote=True,
        evaluation='Full36 guided/final latent/decoded RGB exact OFF-ON control; no endpoint quality claim',
        GPU_authorized=False)
    scope = json.loads(json.dumps(scope))
    scope['scope_sha256'] = digest(scope)
    return scope


def validate_scope(scope):
    from .policy_generator_r1.interval_grammar import Profile
    require(scope['scope_sha256'] == digest({k:v for k,v in scope.items() if k != 'scope_sha256'}),
            'S scope bytes/identity differ')
    profile = dict(scope['profile'])
    for name in ('protected_dense', 'alpha_candidates'):
        profile[name] = tuple(profile[name])
    expected = make_scope(Profile(**profile), scope['prompts'],
                          cpu_fixture=scope['CPU_fixture_only'])
    require(scope == expected, 'Altered complete S scope, ordering or denominator')


def tensor_signature(value):
    from .mid_coverage import tree_digest
    return dict(shape=list(value.shape), dtype=str(value.dtype), sha256=tree_digest(value))


def file_digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*2**20), b''):
            value.update(block)
    return value.hexdigest()


def rgb_signature(video):
    """The pinned writer's float/uint8 conversion, before encoded metadata."""
    import numpy as np
    import torch
    require(isinstance(video, torch.Tensor) and video.ndim == 4
            and video.shape[0] == 3 and video.shape[1] == 93,
            'Complete decoded Cx93xHxW video required')
    require(bool(torch.isfinite(video).all()), 'Finite decoded video required')
    if torch.is_floating_point(video):
        value = video.detach().clamp(0, 1)
    else:
        require(video.dtype == torch.uint8, 'Pinned writer supports only float or uint8')
        value = video.detach().float().div(255)
    value = np.ascontiguousarray((value.cpu().float().numpy()*255).transpose(1,2,3,0).astype(np.uint8))
    return dict(shape=list(value.shape), dtype=str(value.dtype),
                sha256=hashlib.sha256(memoryview(value)).hexdigest())


class Requests:
    """Consume an admitted caller context; never create one or authorize a GPU."""
    def __init__(self, *, scope, inference, samples, profile, common, sink,
                 logical_copy_cap_bytes, cpu_validation=False, production_context=None):
        validate_scope(scope)
        require(scope['CPU_fixture_only'] == cpu_validation, 'Declared CPU/real input boundary differs')
        if not cpu_validation:
            require(production_context is not None
                and production_context.get('scope_sha256') == scope['scope_sha256']
                and production_context.get('authorizes_S_collection') is True
                and all(production_context.get(k) for k in ('launch_id', 'gpu_uuid', 'source_revision')),
                'A separately authorized, source-bound S collection context is required')
        require(set(samples) == set(scope['prompts']) and callable(sink), 'Exact inputs and bounded sink required')
        require(type(logical_copy_cap_bytes) is int and logical_copy_cap_bytes > 0, 'Explicit copy cap required')
        require(json.loads(json.dumps(asdict(profile))) == scope['profile'], 'Selected production profile differs')
        require(file_digest(Path(common['runtime'])/VIDEO_HELPER_PATH) == VIDEO_HELPER_SHA,
                'Pinned video writer source changed')
        self.scope = copy.deepcopy(scope)
        self.inference, self.samples, self.profile = inference, samples, profile
        self.common, self.sink = common, sink
        self.copy_cap, self.cpu_validation = logical_copy_cap_bytes, cpu_validation
        self.seen = set()
        self.batch_consumed = False

    def __call__(self, slot, output):
        from . import clean_speed20_r1 as clean
        from .sq_s_collection_r1 import execute
        require(slot in self.scope['slots'] and slot['id'] not in self.seen,
                'Registered unattempted S slot required; failures cannot retry')
        self.seen.add(slot['id'])
        sample = self.samples[slot['prompt']]
        require(sample.name == slot['prompt'] and sample.seed == 0 and sample.num_output_frames == 93,
                'Original seed0/93-frame request required')
        videos = []
        module = self.common['inference_module']
        original_writer = module.save_img_or_video
        def writer(video, path, fps):
            videos.append(rgb_signature(video))
            return original_writer(video, path, fps)
        with clean.patched(module, 'save_img_or_video', writer):
            result = execute(self.inference, sample, parent=slot['parent'],
                profile=self.profile, policy=self.scope['policies'][slot['parent']],
                enabled=slot['enabled'], sink=self.sink, logical_copy_cap_bytes=self.copy_cap,
                output=output, **{**self.common, 'audit':True})
        require(result['status'] == 'COMPLETE' and len(videos) == 1,
                'Guardrail rejection/incomplete S request stops the whole card')
        require(result['guided_pairs'] == result['solver_steps'] == len(result['guided']) == 36,
                'Complete36 S parent required')
        history = result['semantic_history']
        require([r['actual'] for r in history] == self.scope['policies'][slot['parent']]['actions']
                and all(r['fallback_reason'] is None for r in history), 'Parent deviated from its fixed policy')
        path = Path(result['video_path'])
        require(path.is_file() and not path.is_symlink(), 'Original guarded encoded output missing')
        # Encoded bytes are independently recorded. The parity control uses
        # every decoded RGB byte, not container/encoder metadata equivalence.
        return dict(status='COMPLETE', CPU_fixture=self.cpu_validation,
            policy_fingerprint=result['policy_fingerprint'],
            guided=[tensor_signature(v) for v in result['guided']],
            final_latent=tensor_signature(result['final_latent']), RGB=videos[0],
            semantic_actions=[r['actual'] for r in history], S_rows=result['S_rows'],
            encoded_video=dict(path=str(path), bytes=path.stat().st_size,
                sha256=file_digest(path)),
            solver_steps=36, diagnostic_only_no_clean_clock=True)


def collect(adapter, output, *, before_request, storage, save):
    """One exclusive complete attempt; preserve failed state and partial files."""
    scope = adapter.scope
    validate_scope(scope)
    require(not getattr(adapter, 'batch_consumed', False), 'Original S batch was already attempted; no retry')
    adapter.batch_consumed = True
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    state = dict(status='RUNNING', scope_sha256=scope['scope_sha256'], counts=scope['counts'],
                 rows=[], OFF_ON_controls=[], scientific_labels_accepted=False)
    save(state)
    witnesses = {}
    try:
        for slot in scope['slots']:
            before_request(slot)
            row = dict(slot=copy.deepcopy(slot), status='ATTEMPTED')
            state['rows'].append(row)
            save(state)
            result = adapter(slot, output / slot['id'])
            require(result['status'] == 'COMPLETE' and result['solver_steps'] == len(result['guided']) == 36,
                    'Incomplete S path stops all subsequent roles')
            require(result['CPU_fixture'] == scope['CPU_fixture_only']
                    and result['policy_fingerprint'] == scope['policies'][slot['parent']]['fingerprint']
                    and result['semantic_actions'] == scope['policies'][slot['parent']]['actions'],
                    'Source/policy/CPU role identity differs')
            moments = result['S_rows']
            require([r['step'] for r in moments] == (list(TARGETS) if slot['enabled'] else []),
                    'Exact enabled27/disabled0 row cohort required')
            require(all(r['prompt'] == slot['prompt'] and r['parent'] == slot['parent']
                    and r['parent_roundtrip_equal'] and not r['teacher_writes_parent']
                    and r['source']['source_captured_before_parent_pair']
                    and not r['source']['current_D_in_source'] for r in moments),
                    'S rows changed protected state or used the current D')
            row.update(status='COMPLETE', result=result)
            if slot['purpose'] == 'CONTROL':
                key = (slot['prompt'], slot['parent'])
                witness = {k:result[k] for k in ('guided', 'final_latent', 'RGB', 'semantic_actions')}
                require(len(witness['guided']) == 36, 'Full36 guided control required')
                if key in witnesses:
                    require(witness == witnesses.pop(key), 'Full36 guided/latent/decoded RGB OFF-ON mismatch')
                    state['OFF_ON_controls'].append(dict(prompt=key[0], parent=key[1], exact=True))
                else:
                    witnesses[key] = witness
            save(state)
        moments = [r for row in state['rows'] for r in row['result']['S_rows']]
        require(len(state['rows']) == 10 and len(state['OFF_ON_controls']) == 4 and not witnesses,
                'Complete ten-path and four OFF-ON denominator required')
        require(sum(row['result']['semantic_actions'].count('D') for row in state['rows']) == 220
                and sum(row['result']['semantic_actions'].count('C') for row in state['rows']) == 140,
                'Exact parent220D/140C denominator required')
        require(len(moments) == 108
            and sum(r['extra_Dense_teacher_pairs'] for r in moments) == 56
            and sum(r['extra_C_readout_pairs'] for r in moments) == 52
            and sum(r['extra_Dense_hidden_replay_heads'] for r in moments) == 0,
            'Full108/56/52 S measurement denominator required')
        stored = storage.finish()
        require((stored['measured_rows'], stored['raw_states'], stored['unique_anchor_files']) == (108,8,24),
                'Complete108/eight-raw/24-anchor storage required')
        state.update(storage=stored, status='COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE')
        save(state)
        return state
    except BaseException as error:
        state.update(status='FAILED_RETAINED_NO_RETRY', error_type=type(error).__name__, error=str(error))
        save(state)
        raise
