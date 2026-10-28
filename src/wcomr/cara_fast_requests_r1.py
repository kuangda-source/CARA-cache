"""Mainline preparation entry using unchanged WC73/724/725 engines.

This version deliberately accepts CPU fixtures only. It provides no launch,
reservation, GPU admission or retry mechanism.
"""
import copy
from pathlib import Path

from . import clean_speed20_r1 as clean
from .cara_fast_spec_r1 import digest, profile_from
from .paper_latency_r1 import execute_with_timing
from .policy_generator_r1 import p2_native_sampling, production_sampling
from .policy_generator_r1.frozen_request_arguments import request_variant
from .wc_time_card_r1 import load_calibration
from .wc_time_protocol_p0 import compile_wc_adapter


class Requests:
    def __init__(self, *, inference, samples, card, common, ra_binding, host,
                 cpu_validation=False, frozen=None):
        if not cpu_validation:
            raise ValueError('Preparation entry is CPU-only; new GPU card/admission is unbound')
        if digest({k:v for k,v in card.items() if k != 'scope_sha256'}) != card['scope_sha256']:
            raise ValueError('Altered scope manifest')
        self.card = copy.deepcopy(card)
        self.inference, self.samples, self.common = inference, samples, common
        self.host, self.frozen = host, copy.deepcopy(frozen)
        self.slots = {s['id']:s for s in self.card['physical_matrix']}
        self.seen = set()
        self.profile = profile_from(card['profile'])
        self.schedules = {s['requested_steps']:s for s in card['schedules']}
        self.calibration = load_calibration(ra_binding)
        self.port = compile_wc_adapter(common['runtime'], common['wc'], paper_port=True)[0]
        self.alld = compile_wc_adapter(common['runtime'], common['wc'], force_full=True)[0]

    def __call__(self, slot, output, *, timing=None):
        if self.slots.get(slot['id']) != slot or slot['id'] in self.seen:
            raise ValueError('Unregistered/altered/already attempted slot')
        if slot['phase'] == 'B' and (not self.frozen or self.frozen.get('scope_sha256') != self.card['scope_sha256']
                or self.frozen.get('phase_A_GPU_released') is not True):
            raise ValueError('Released complete A and scope-bound frozen selection required')
        name = slot['role']; role = self.card['roles'][name]
        if role['kind'] == 'selection':
            choice = self.frozen['selected'][role['family']]['candidate']
            if choice not in self.card['finite_grids'][role['family']]:
                raise ValueError('Unregistered finite selection')
            name, role = choice, self.card['roles'][choice]
        if role['kind'] == 'ra' and role['calibration_fingerprint'] != self.calibration.fingerprint:
            raise ValueError('Unchanged RA calibration required')
        sample = request_variant(self.samples[slot['member']], seed=slot['seed'], num_steps=role['requested_steps'])
        self.seen.add(slot['id'])  # Failures consume the physical attempt too.
        settings = copy.deepcopy(self.card['roles']['ALLD']['settings'])
        runner = clean.execute; args = (); extra = {}; module = self.common['wc']
        if role['kind'] == 'native':
            runner = p2_native_sampling.execute; extra['schedule'] = self.schedules[role['requested_steps']]
        elif role['kind'] == 'policy':
            runner = production_sampling.execute
            extra.update(profile=self.profile, policy=role['policy'])
        elif role['kind'] == 'wc':
            module = self.port; settings = copy.deepcopy(role['settings']); args = ('WC',)
        elif role['kind'] == 'allD':
            module = self.alld; args = ('WC',)
        elif role['kind'] == 'ra':
            args = ('RA',); extra['specs'] = {'SOURCE_RA': role['RA_spec']}
        else:
            raise ValueError('Unknown concrete execution role')
        kwargs = {**self.common, 'wc':module, 'settings':settings,
                  'calibration':self.calibration, 'specs':{}, 'output':Path(output), 'audit':True, **extra}
        enabled = slot['timing_enabled'] if timing is None else timing
        if enabled:
            result = execute_with_timing(runner, self.inference, sample, *args, host=self.host,
                expected_updates=self.schedules[role['requested_steps']]['actual_updates'],
                cpu_validation=True, diagnostic=slot['purpose']=='control', **kwargs)
        else:
            result = runner(self.inference, sample, *args, **kwargs)
            if result.get('core_seconds'):
                result['full_request_seconds'] = production_sampling.complete_request_seconds(result)
        result.update(slot_id=slot['id'],role=slot['role'],concrete_role=name,scope_sha256=self.card['scope_sha256'],
                      T_DD=result.get('paper_denoise_decode_seconds'),T_request=result.get('full_request_seconds'),
                      canonical_timing='wcomr.paper_latency_r1',CPU_fixture=True)
        return result
