"""Affected production requests for the search evaluator's CPU preparation.

The existing full sampler, native route, policy route, guardrails and writer are
used. This version refuses GPU execution until the whole search card is bound.
"""
import copy
from pathlib import Path

import numpy as np
import torch

from . import clean_speed20_r1 as clean
from .cara_budget_search_r1 import FIT_MEMBERS, SCHEDULE_SHA256, PROFILE_FINGERPRINT
from .cara_budget_search_journal_r1 import create_record, read_record, sync_directory
from .cara_budget_rgb_objective_r1 import save_endpoint, read_endpoint, full_rgb_mse, file_sha
from .cara_fast_requests_r2 import Requests
from .cara_fast_spec_r1 import digest, policy_from_mask, profile_from


class EndpointRequests:
    def __init__(self, *, root, card, context_sha256, RGB_shape, inference, samples, common,
                 ra_binding, host, cpu_validation=False, before_request=None, create=False,
                 timing_enabled=True):
        if cpu_validation is not True:
            raise ValueError('Search evaluator is CPU preparation only; whole GPU card is unbound')
        self.profile = profile_from(card['profile'])
        if (digest({k:v for k,v in card.items() if k != 'scope_sha256'}) != card['scope_sha256']
                or digest(card['schedule']) != SCHEDULE_SHA256
                or self.profile.fingerprint != PROFILE_FINGERPRINT or tuple(card['FIT']) != FIT_MEMBERS):
            raise ValueError('Original registered search grid/profile/FIT required')
        if (not isinstance(context_sha256,str) or len(context_sha256) != 64
                or any(c not in '0123456789abcdef' for c in context_sha256)):
            raise ValueError('Source/request/RNG context digest required')
        if len(RGB_shape) != 4 or RGB_shape[:2] != [3,93] or any(type(n) is not int or n <= 0 for n in RGB_shape):
            raise ValueError('Complete93-frame RGB geometry required')
        self.root, self.card = Path(root), copy.deepcopy(card)
        self.context, self.shape = context_sha256, list(RGB_shape)
        self.kwargs = dict(inference=inference, samples=samples, common=common,
            ra_binding=ra_binding, host=host, cpu_validation=True)
        self.before_request, self.timing_enabled = before_request, timing_enabled
        self.physical_calls = 0
        binding = dict(CPU_fixture_only=True, original_scope_sha256=card['scope_sha256'],
            context_sha256=context_sha256, RGB_shape=RGB_shape, host=host,
            timing_enabled=timing_enabled, evaluator_source_sha256=file_sha(__file__))
        if create:
            self.root.mkdir(mode=0o700)
            sync_directory(self.root.parent)
            create_record(self.root/'binding.json', binding)
        elif read_record(self.root/'binding.json') != binding:
            raise ValueError('Original evaluator context differs')

    def identity(self, member, kind, query=None):
        sample = next(r for r in self.card['inputs'] if r['name'] == member)
        return dict(context_sha256=self.context, original_scope_sha256=self.card['scope_sha256'],
            member=member, frozen_input_sha256=digest(sample), generation_seed=0,
            requested_steps=35, actual_updates=36, RGB_shape=self.shape, kind=kind,
            query_sha256=query['request_sha256'] if query else None,
            policy_fingerprint=query['policy']['fingerprint'] if query else None,
            CPU_fixture_only=True)

    def execute_one(self, member, index, *, query=None):
        kind = 'CANDIDATE' if query else 'NATIVE'
        identity = self.identity(member, kind, query)
        name = f'query-{query["query_id"]:06d}-FIT{index}' if query else f'teacher-FIT{index}'
        physical = self.root/name
        if physical.exists():
            if query:
                raise ValueError('Existing candidate attempt; recover original query journal, never re-execute')
            # Teacher reuse is restricted to this exact evaluator context and
            # accepted original request, never an old compressed video.
            proof = read_record(physical/'result.json')
            if proof['identity'] != identity or proof['status'] != 'COMPLETE':
                raise ValueError('Original complete teacher request required')
            read_endpoint(physical/'endpoint', identity)
            return physical, identity
        physical.mkdir(mode=0o700)
        sync_directory(physical.parent)
        create_record(physical/'intent.json', identity)
        card = copy.deepcopy(self.card)
        card.pop('scope_sha256')
        role = 'SEARCH_CANDIDATE' if query else 'NATIVE35'
        if query:
            card['roles'][role] = dict(kind='policy', requested_steps=35, policy=query['policy'])
        slot = dict(id=name, phase='SEARCH_CPU_COMPONENT', purpose='ENDPOINT_OBJECTIVE',
            member=member, role=role, seed=0, timing_enabled=self.timing_enabled,
            audit_enabled=False, eligible_clean_time=False)
        card.update(physical_matrix=[slot], formal_matrix=[], CPU_FRAGMENT_ONLY=True, GPU_dispatch_ready=False)
        card['scope_sha256'] = digest(card)
        captured = []
        module = self.kwargs['common']['inference_module']
        original_writer = module.save_img_or_video

        def capture(video, path, fps):
            captured.append(video.detach().to(device='cpu',dtype=torch.float32).numpy().copy())
            return original_writer(video,path,fps)

        if self.before_request:
            self.before_request()
        self.physical_calls += 1
        with clean.patched(module,'save_img_or_video',capture):
            result = Requests(card=card, **self.kwargs)(slot, physical/'generation')
        if (result['status'] != 'COMPLETE' or result['solver_steps'] != 36
                or result['guided_pairs'] != 36 or len(captured) != 1):
            raise ValueError('Complete guarded full36 endpoint required; partial/refusal cannot be scored')
        if query:
            history = result['semantic_history']
            if ([h['actual'] for h in history] != query['policy']['actions']
                    or any(h['fallback_reason'] is not None for h in history)):
                raise ValueError('Actual candidate departed from fixed19D policy')
        proof = dict(status='COMPLETE', identity=identity, solver_steps=36, guided_pairs=36,
            actual_D=19 if query else 36, policy_exact_without_fallback=bool(query),
            RGB_captures=1, T_DD=result['T_DD'], T_request=result['T_request'],
            CPU_fixture_only=True, actual_model_weights=False)
        create_record(physical/'result.json', proof)
        save_endpoint(physical/'endpoint', identity, captured[0])
        return physical, identity

    def prepare_teachers(self):
        return [self.execute_one(member,index) for index,member in enumerate(FIT_MEMBERS)]

    def __call__(self, request):
        if (digest({k:v for k,v in request.items() if k != 'request_sha256'}) != request['request_sha256']
                or request['context_sha256'] != self.context or tuple(request['FIT_members']) != FIT_MEMBERS
                or request['generation_seed'] != 0 or request['requested_steps'] != 35
                or request['actual_updates'] != 36 or request['D_pair_budget'] != 19
                or type(request['query_id']) is not int or request['query_id'] < 1
                or len(request['dense']) != 19 or 24 not in request['dense']
                or policy_from_mask(self.profile,request['dense']) != request['policy']):
            raise ValueError('Original complete registered search query required')
        teachers = self.prepare_teachers()
        candidates = [self.execute_one(member,index,query=request) for index,member in enumerate(FIT_MEMBERS)]
        rows = []
        # Both physical endpoints must complete before any objective is returned.
        for member, (candidate,candidate_id), (teacher,teacher_id) in zip(FIT_MEMBERS,candidates,teachers):
            rgb, observed = read_endpoint(candidate/'endpoint',candidate_id)
            reference, native = read_endpoint(teacher/'endpoint',teacher_id)
            rows.append(dict(member=member,status='COMPLETE',RGB_MSE=full_rgb_mse(rgb,reference),
                candidate_RGB_sha256=observed['RGB_sha256'],teacher_RGB_sha256=native['RGB_sha256'],
                complete_frames=93, CPU_fixture_only=True))
        return dict(request_sha256=request['request_sha256'], rows=rows)
