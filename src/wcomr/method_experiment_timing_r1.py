"""Opt-in entrypoints for future method cards. Historical collectors unchanged."""
from .paper_latency_r1 import execute_with_timing
from .policy_generator_r1.exploration_requests import Requests


class TimedRequests(Requests):
    """Same frozen role/mask/seed registry and no-replay rule; additive clocks."""
    def __init__(self, *, timing_host, timing_cpu_validation=False, **kwargs):
        super().__init__(**kwargs)
        self.timing_host, self.timing_cpu_validation = timing_host, timing_cpu_validation

    def __call__(self, slot, output):
        if slot['id'] in self.seen:
            raise ValueError('Physical slot already attempted')
        self.seen.add(slot['id'])
        role, sample = self.prepare(slot)
        kw = dict(self.common, output=output, timing_host=self.timing_host,
                  timing_cpu_validation=self.timing_cpu_validation)
        if role['kind'] == 'native':
            return short_native(self.inference, sample, schedule=self.schedules[sample.num_steps], **kw)
        return policy(self.inference, sample, profile=self.profile, policy=role['policy'], **kw)


def policy(inference, sample, *, timing_host, timing_cpu_validation=False, **kwargs):
    from .policy_generator_r1.production_sampling import execute
    return execute_with_timing(execute, inference, sample, host=timing_host, expected_updates=36,
                               cpu_validation=timing_cpu_validation, **kwargs)


def native(inference, sample, *, timing_host, timing_cpu_validation=False, **kwargs):
    from .clean_speed20_r1 import execute
    return execute_with_timing(execute, inference, sample, 'NATIVE', host=timing_host, expected_updates=36,
                               cpu_validation=timing_cpu_validation, **kwargs)


def short_native(inference, sample, *, timing_host, schedule, timing_cpu_validation=False, **kwargs):
    from .policy_generator_r1.p2_native_sampling import execute
    return execute_with_timing(execute, inference, sample, host=timing_host,
                               expected_updates=schedule['actual_updates'], schedule=schedule,
                               cpu_validation=timing_cpu_validation, **kwargs)


def scout_parent(inference, sample, *, timing_host, timing_cpu_validation=False, **kwargs):
    from .scout_parent_v22 import execute
    return execute_with_timing(execute, inference, sample, host=timing_host, expected_updates=36,
                               cpu_validation=timing_cpu_validation, diagnostic=bool(kwargs.get('enabled')),
                               **kwargs)
