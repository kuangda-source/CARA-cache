"""Loaded Cosmos P1 routes; the caller owns whole-card admission and storage."""
import copy
import hashlib
from pathlib import Path

from . import clean_speed20_r1 as clean
from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_spec_r1 import digest
from .cara_source_lifecycle_p1_plan_r1 import validate
from .cara_source_lifecycle_scalar_collection_r1 import execute as scalar_execute
from .mid_coverage import tree_digest
from .paper_latency_r1 import execute_with_timing
from .policy_generator_r1 import p2_native_sampling, production_sampling
from .policy_generator_r1.frozen_request_arguments import request_variant
from .prepared_input import PreparedInputReplay, RNGState
from .wc_time_protocol_p0 import compile_wc_adapter


class Requests:
    def __init__(self, *, inference, samples, card, common, context, before_request,
                 snapshot_limits, cpu_validation=False, card_validator=validate):
        self.profile = card_validator(card)
        if (context['scope_sha256'] != card['scope_sha256'] or context['host'] != 'two_card'
                or context['CPU_fixture_only'] is not cpu_validation
                or not context['launch_id'] or not context['source_revision'] or not context['admission_sha256']):
            raise ValueError('Caller-bound exact P1 source, host and admission required')
        self.inference, self.samples, self.common = inference, samples, common
        self.card, self.context = copy.deepcopy(card), copy.deepcopy(context)
        self.before_request, self.snapshot_limits = before_request, snapshot_limits
        self.cpu_validation, self.seen = cpu_validation, set()
        self.replay = {m: PreparedInputReplay(inference.pipe._get_data_batch_input)
                       for m in card['FIT']+card['CHECK']}
        self.alld = compile_wc_adapter(common['runtime'], common['wc'], force_full=True)[0]

    def __call__(self, slot, output):
        if (slot['id'] in self.seen or slot['member'] not in self.replay or slot['seed'] != 0
                or slot['context_sha256'] != digest(self.context)
                or slot['kind'] not in ('native', 'allD', 'policy', 'scalar')
                or slot['timing'] not in ('CLEAN', 'DIAGNOSTIC', 'OFF')):
            raise ValueError('Bound, unattempted original P1 request required')
        if slot['kind'] in ('policy', 'scalar') and slot['candidate_id'] != slot['policy']['fingerprint']:
            raise ValueError('Dynamic plan fingerprint differs from its bound semantic identity')
        if slot['kind'] == 'scalar':
            parent = next(p for p in self.card['calibration_design']['parents'] if p['id'] == slot['parent_id'])
            if (slot['member'] not in self.card['FIT'] or slot['policy'] != parent['policy']
                    or slot['timing'] != 'DIAGNOSTIC'):
                raise ValueError('Fixed FIT-only source parent and diagnostic timing required')
        self.seen.add(slot['id'])
        self.before_request(slot)
        sample = request_variant(self.samples[slot['member']], seed=0, num_steps=35)
        kwargs = dict(self.common, settings=copy.deepcopy(self.card['settings']),
                      calibration=None, specs={}, output=Path(output), audit=False)
        args, runner = (), production_sampling.execute
        if slot['kind'] == 'native':
            runner = p2_native_sampling.execute
            kwargs['schedule'] = self.card['schedule']
        elif slot['kind'] == 'allD':
            runner, args = clean.execute, ('WC',)
            kwargs['wc'] = self.alld
        else:
            kwargs.update(profile=self.profile, policy=slot['policy'])
            if slot['kind'] == 'scalar':
                runner = scalar_execute
                kwargs.update(label_states=parent['states'], member=slot['member'], parent_id=parent['id'],
                    logical_copy_cap_bytes=self.snapshot_limits['logical_copy_bytes'],
                    CPU_storage_cap_bytes=self.snapshot_limits['total_CPU_images_bytes'])
        captured = []
        writer = self.common['inference_module'].save_img_or_video

        def save(video, path, fps):
            array = video.detach().float().to(device='cpu').contiguous().numpy()
            captured.append(dict(shape=list(array.shape), dtype=str(array.dtype),
                                 sha256=hashlib.sha256(array.tobytes()).hexdigest()))
            return writer(video, path, fps)

        with clean.patched(self.inference.pipe, '_get_data_batch_input', self.replay[slot['member']]), \
                clean.patched(self.common['inference_module'], 'save_img_or_video', save):
            if slot['timing'] == 'OFF':
                result = runner(self.inference, sample, *args, **kwargs)
                result['full_request_seconds'] = production_sampling.complete_request_seconds(result)
            else:
                result = execute_with_timing(runner, self.inference, sample, *args, host='two_card',
                    expected_updates=36, cpu_validation=self.cpu_validation,
                    diagnostic=slot['timing'] != 'CLEAN', **kwargs)
        if (result['status'] != 'COMPLETE' or result['solver_steps'] != 36 or result['guided_pairs'] != 36
                or len(captured) != 1):
            raise ValueError('Full guarded36 request and exactly one complete RGB output required')
        if not self.cpu_validation and (captured[0]['shape'] != [3, 93, 432, 768]
                                       or captured[0]['dtype'] != 'float32'):
            raise ValueError('Original full93 production pre-encoding RGB geometry required')
        if slot['kind'] in ('policy', 'scalar'):
            if ([h['actual'] for h in result['semantic_history']] != slot['policy']['actions']
                    or any(h['fallback_reason'] is not None for h in result['semantic_history'])):
                raise ValueError('Actual original plan departed from its fixed legal actions')
        if slot['timing'] == 'CLEAN' and any(result[k] != 0 for k in (
                'in_timing_guided_copies', 'in_timing_hashes', 'research_checkpoints')):
            raise ValueError('Research instrumentation entered a clean P1 request')
        latent = result.pop('final_latent')
        latent_sha = tree_digest(latent)
        latent_path = Path(output)/'complete-final-latent.pt'
        import torch
        torch.save(latent, latent_path)
        video = Path(result['video_path']).resolve()
        return dict(status='COMPLETE', CPU_fixture_only=self.cpu_validation,
            source_revision=self.context['source_revision'], launch_id=self.context['launch_id'],
            context_sha256=digest(self.context), member=slot['member'], seed=0,
            candidate_id='NATIVE35' if slot['kind'] == 'native' else slot['candidate_id'],
            actual_updates=36, solver_steps=36, guided_pairs=36, fallback_count=0,
            physical_model_pairs=44 if slot['kind'] == 'scalar' else 36,
            video=dict(path=str(video), sha256=file_sha(video)),
            final_latent=dict(path=str(latent_path.resolve()), file_sha256=file_sha(latent_path),
                              tensor_sha256=latent_sha), pre_encode_RGB=captured[0],
            post_request_RNG_sha256=digest(RNGState().signatures()),
            timing=slot['timing'], eligible_clean_time=(slot['timing'] == 'CLEAN' and not self.cpu_validation),
            T_DD=result.get('paper_denoise_decode_seconds'), T_request=result['full_request_seconds'],
            scalar_labels=result.get('scalar_labels', []), semantic_history=result.get('semantic_history'),
            original_result_without_latent=result, scientific_accepted=False)
