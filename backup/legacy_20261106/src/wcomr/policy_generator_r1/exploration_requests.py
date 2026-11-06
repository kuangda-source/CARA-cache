"""Shared CAL production requests; immutable arguments and original engines."""
from .frozen_request_arguments import request_variant


class Requests:
    def __init__(self, *, inference, samples, profile, roles, schedules, common):
        self.inference = inference
        self.samples = samples
        self.profile = profile
        self.roles = roles
        self.schedules = {r['requested_steps']: r for r in schedules}
        self.common = common
        self.seen = set()

    def prepare(self, slot):
        role = self.roles[slot['role']]
        if role['kind'] not in ('native', 'policy'):
            raise ValueError('Unknown registered request kind')
        n = role['requested_steps']
        if role['kind'] == 'policy' and n != 35:
            raise ValueError('Registered cache policies require the original 35-step request')
        schedule = self.schedules[n]
        if 'actual_updates' in slot and slot['actual_updates'] != schedule['actual_updates']:
            raise ValueError('Physical slot and registered schedule differ')
        return role, request_variant(self.samples[slot['member']], seed=slot['seed'], num_steps=n)

    def validate_slots(self, slots):
        """Run before model loading; no sampling, output writes or attempted slots."""
        if len({s['id'] for s in slots}) != len(slots):
            raise ValueError('Duplicate physical slot')
        return [self.prepare(s)[1] for s in slots]

    def __call__(self, slot, output):
        if slot['id'] in self.seen:
            raise ValueError('Physical slot already attempted')
        self.seen.add(slot['id'])
        role, sample = self.prepare(slot)
        kw = dict(self.common, output=output)
        if role['kind'] == 'native':
            from .p2_native_sampling import execute
            return execute(self.inference, sample, schedule=self.schedules[sample.num_steps], **kw)
        from .production_sampling import execute
        return execute(self.inference, sample, profile=self.profile, policy=role['policy'], **kw)
