"""Fast production routing with explicit clean/diagnostic audit boundaries.

The existing host guardian owns admission, exclusivity and billing. This class
only consumes that caller's bound context; it never launches or reserves work.
R1 sources and their completed CPU evidence remain unchanged.
"""
import copy
from pathlib import Path

from . import clean_speed20_r1 as clean
from .cara_fast_requests_r1 import Requests as PreparationRequests
from .paper_latency_r1 import execute_with_timing
from .policy_generator_r1 import p2_native_sampling, production_sampling
from .policy_generator_r1.frozen_request_arguments import request_variant


class Requests(PreparationRequests):
    def __init__(self, *, cpu_validation=False, production_context=None, **kwargs):
        card, host = kwargs['card'], kwargs['host']
        if not cpu_validation and (production_context is None
                or production_context.get('scope_sha256') != card['scope_sha256']
                or production_context.get('host') != host
                or not production_context.get('gpu_uuid')
                or not production_context.get('launch_id')):
            raise ValueError('Bound admitted production context required; this adapter grants no execution authority')
        # Reuse the unchanged setup/registration/calibration/AST adapters. R1's
        # request executor is never called: its audit and CPU flags are literals.
        super().__init__(cpu_validation=True, **kwargs)
        self.cpu_validation = cpu_validation
        self.production_context = production_context

    def __call__(self, slot, output, *, timing=None):
        if self.slots.get(slot['id']) != slot or slot['id'] in self.seen:
            raise ValueError('Unregistered/altered/already attempted slot')
        if timing is not None and not self.cpu_validation:
            raise ValueError('Timing override is CPU-test-only')
        if slot['phase'] == 'B' and (not self.frozen
                or self.frozen.get('scope_sha256') != self.card['scope_sha256']
                or self.frozen.get('phase_A_GPU_released') is not True):
            raise ValueError('Released complete A and scope-bound frozen selection required')
        name = slot['role']
        role = self.card['roles'][name]
        if role['kind'] == 'selection':
            name = self.frozen['selected'][role['family']]['candidate']
            if name not in self.card['finite_grids'][role['family']]:
                raise ValueError('Unregistered finite selection')
            role = self.card['roles'][name]
        if role['kind'] == 'ra' and role['calibration_fingerprint'] != self.calibration.fingerprint:
            raise ValueError('Unchanged RA calibration required')
        sample = request_variant(self.samples[slot['member']], seed=slot['seed'],
                                 num_steps=role['requested_steps'])
        self.seen.add(slot['id'])
        settings = copy.deepcopy(self.card['roles']['ALLD']['settings'])
        runner, args, extra, module = clean.execute, (), {}, self.common['wc']
        if role['kind'] == 'native':
            runner = p2_native_sampling.execute
            extra['schedule'] = self.schedules[role['requested_steps']]
        elif role['kind'] == 'policy':
            runner = production_sampling.execute
            extra.update(profile=self.profile, policy=role['policy'])
        elif role['kind'] == 'wc':
            module, settings, args = self.port, copy.deepcopy(role['settings']), ('WC',)
        elif role['kind'] == 'allD':
            module, args = self.alld, ('WC',)
        elif role['kind'] == 'ra':
            args = ('RA',)
            extra['specs'] = {'SOURCE_RA': role['RA_spec']}
        else:
            raise ValueError('Unknown concrete execution role')
        kwargs = {**self.common, 'wc': module, 'settings': settings,
                  'calibration': self.calibration, 'specs': {}, 'output': Path(output),
                  'audit': slot['audit_enabled'], **extra}
        enabled = slot['timing_enabled'] if timing is None else timing
        if enabled:
            result = execute_with_timing(runner, self.inference, sample, *args,
                host=self.host, expected_updates=self.schedules[role['requested_steps']]['actual_updates'],
                cpu_validation=self.cpu_validation,
                diagnostic=not slot['eligible_clean_time'], **kwargs)
        else:
            result = runner(self.inference, sample, *args, **kwargs)
            if result.get('core_seconds'):
                result['full_request_seconds'] = production_sampling.complete_request_seconds(result)
        if slot['eligible_clean_time'] and any(result[key] != 0 for key in (
                'in_timing_guided_copies', 'in_timing_hashes', 'research_checkpoints')):
            raise ValueError('Research instrumentation entered a registered clean request')
        result.update(slot_id=slot['id'], role=slot['role'], concrete_role=name,
            scope_sha256=self.card['scope_sha256'], T_DD=result.get('paper_denoise_decode_seconds'),
            T_request=result.get('full_request_seconds'), canonical_timing='wcomr.paper_latency_r1',
            CPU_fixture=self.cpu_validation, eligible_clean_time=slot['eligible_clean_time'],
            audit_enabled=slot['audit_enabled'])
        return result
