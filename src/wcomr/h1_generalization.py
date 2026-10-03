"""Trace-only source selection and isolated multi-window H1 shadow references."""
from contextlib import contextmanager
import json

from .h0_complement import H0ComplementProbe
from .h1_lifetime import H1LifetimeProbe
from .mid_coverage import tree_digest

REGIONS = [{'name': 'early', 'source_step_bounds': [8, 12]},
           {'name': 'late', 'source_step_bounds': [25, 29]}]


def select_sources(trace, regions, *, prefix_steps=33, probe_start_counter=14):
    """Earliest paired official full, using only the baseline execution trace.

    The fixed source bounds are disjoint from each other's 1/2/4 reuse windows.
    Probe availability is inferred from pinned official branching; the actual
    observed H1 probe additionally requires resume_flag and two past anchors.
    """
    if json.dumps(regions, sort_keys=True) != json.dumps(REGIONS, sort_keys=True):
        raise ValueError('Frozen early/late selection regions changed')
    if prefix_steps != 33 or probe_start_counter != 14 or len(trace) != 66:
        raise ValueError('Complete official baseline33/66 trace required')
    for i, row in enumerate(trace):
        if (type(row.get('call')) is not int or row['call'] != i + 1
                or type(row.get('cache_counter_before')) is not int
                or row['cache_counter_before'] != i
                or type(row.get('deep_executed')) is not bool):
            raise ValueError('Malformed baseline call/CFG/true-full trace')
    selected = []
    for region in regions:
        lower, upper = region['source_step_bounds']
        candidates = []
        for step in range(lower, upper + 1):
            pair = trace[2 * (step - 1):2 * step]
            histories = []
            for branch, row in enumerate(pair):
                past = [p['cache_counter_before'] for p in trace[:row['call'] - 1]
                        if p['deep_executed'] and p['cache_counter_before'] % 2 == branch]
                histories.append(past[-2:])
            if (step + 4 <= prefix_steps
                    and all(row['deep_executed'] and row['cache_counter_before'] >= probe_start_counter
                            for row in pair)
                    and all(len(history) == 2 for history in histories)):
                candidates.append((step, histories))
        if not candidates:
            raise ValueError('No paired official full in frozen ' + region['name']
                             + ' region; no source replacement or denominator reduction')
        step, histories = candidates[0]
        selected.append({'region': region['name'], 'bounds': [lower, upper],
                         'source_solver_step': step,
                         'source_cfg_calls': [2 * step - 1, 2 * step],
                         'historical_true_full_counters': histories,
                         'eligible_source_steps': [p[0] for p in candidates]})
    return {'rule': 'EARLIEST_PAIRED_TRUE_FULL_WITH_PAID_PROBE_AND_TWO_PAST_SAME_CFG_ANCHORS',
            'selection_inputs': ['call', 'cache_counter_before', 'deep_executed'],
            'baseline_trace_sha256': tree_digest(trace),
            'selected': selected, 'candidate_errors_used_for_selection': False}


class H1GeneralizationProbe:
    """Each region owns a separate unchanged H1 reference implementation.

    Attention wrappers are installed once. Only the active region controls the
    shadow backend, and all actual sampling calls stay on the original backend.
    """
    def __init__(self, config, *, selection, context, kernel=None, raw_output=None):
        expected = select_sources(config['_baseline_trace'], config['source_regions'])
        if selection != expected:
            raise ValueError('Source selection differs from pre-candidate baseline trace')
        self.config, self.kernel, self.restores = config, kernel, []
        self.active, self.default_mode = None, 'dense'
        self.children = {}
        for selected in selection['selected']:
            child_config = dict(config, source_solver_step=selected['source_solver_step'])
            path = raw_output / selected['region'] if raw_output is not None else None
            self.children[selected['region']] = H1LifetimeProbe(
                child_config, context=context, kernel=kernel, raw_output=path)

    @property
    def mode(self):
        return self.active.mode if self.active is not None else self.default_mode

    @mode.setter
    def mode(self, value):
        self.default_mode = value

    @property
    def cached_prediction(self):
        return next(iter(self.children.values())).cached_prediction

    @cached_prediction.setter
    def cached_prediction(self, value):
        for child in self.children.values():
            child.cached_prediction = value

    @contextmanager
    def activate(self, child):
        if self.active is not None:
            raise ValueError('Overlapping H1 shadow region activation')
        self.active = child
        try:
            yield
        finally:
            self.active = None

    def start(self, net):
        for child in self.children.values():
            child.start(net)

    def before(self, net, **kwargs):
        for child in self.children.values():
            with self.activate(child):
                child.before(net, **kwargs)

    def collect(self, net, hidden):
        for child in self.children.values():
            with self.activate(child):
                child.collect(net, hidden)

    def observe(self, net, branch):
        for child in self.children.values():
            child.observe(net, branch)

    def install_operators(self, net):
        H0ComplementProbe.install_operators(self, net)

    def close(self):
        H0ComplementProbe.close(self)

    def flatten(self, name):
        return [dict(record, region=region) for region, child in self.children.items()
                for record in getattr(child, name)]

    @property
    def source_records(self):
        return self.flatten('source_records')

    @property
    def source_attempts(self):
        return self.flatten('source_attempts')

    @property
    def records(self):
        return self.flatten('records')

    @property
    def attempts(self):
        return self.flatten('attempts')

    def coverage(self):
        regional = {region: child.coverage() for region, child in self.children.items()}
        if self.active is not None or set(regional) != {'early', 'late'}:
            raise ValueError('Incomplete regional source/age coverage')
        return {'regions': regional, 'source_cfg_states': 4, 'source_arms': 12,
                'future_cfg_age_states': 12, 'future_source_age_cells': 36,
                'all_held_references_immutable': True}
