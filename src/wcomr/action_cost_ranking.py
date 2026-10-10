"""Complete paired post-paid-probe costs for action ranking, not total latency.

The frozen global rule uses every registered scene, origin and timed repeat.
Two-stage summaries are descriptive and never silently install stepwise costs.
"""
from dataclasses import dataclass
import hashlib
import json
import math

from .source_aware_cpd_control import Costs


BOUNDARY = 'POST_ALREADY_PAID_TWO_SHALLOW_PROBES_THROUGH_POST_RF_PAIR'
RULE = 'SCENE_AND_STEP_EQUAL_MEAN_OF_ALL_THREE_POST_PROBE_TIMINGS'
MODES = ('C','A_W1_ONE_PHASE','A_BETA1_ONE_PHASE','ROTATION_050',
         'DENSE_REFERENCE','DENSE_WITH_P0')
SCENES = ('av_28b7cf08-cfb8-41e4-8b1b-d669aa69e632','human_199',
          'misc_13398218_3840_2160_60fps','av_51b45829-502e-4143-9c32-c026bd6ab191')
ORIGINS = tuple((s,t) for s in SCENES for t in (12,30))


def positive(value):
    return type(value) in (int,float) and math.isfinite(value) and value > 0


@dataclass(frozen=True)
class IncrementalRankingCosts(Costs):
    boundary: str = BOUNDARY
    cost_role: str = 'ACTION_ORDER_ONLY_NOT_TOTAL_PAIR_OR_END_TO_END_TIME'

    def __post_init__(self):
        super().__post_init__()
        if self.boundary != BOUNDARY or self.cost_role != 'ACTION_ORDER_ONLY_NOT_TOTAL_PAIR_OR_END_TO_END_TIME':
            raise ValueError('Paid-probe incremental ranking boundary required')


@dataclass(frozen=True)
class ActionCostRanking:
    fingerprint: str
    source_kind: str
    global_means: tuple
    per_registered_step_means: tuple
    complete_raw_timings: tuple
    boundary: str = BOUNDARY
    aggregation: str = RULE

    def for_reuse_mode(self, mode):
        if mode not in MODES[:3]:
            raise ValueError('Original C or an explicitly selected shared A readout required')
        mean = dict(self.global_means)
        # Dense with projection-cache maintenance is the P-enabled deployment D.
        # Plain dense remains an overhead control, not the selected cheap D.
        fingerprint = hashlib.sha256((self.fingerprint+':reuse='+mode+':'+BOUNDARY).encode()).hexdigest()
        return IncrementalRankingCosts(fingerprint,mean[mode],mean['DENSE_WITH_P0'],
                                      mean['ROTATION_050'])


def build_ranking(rows, *, boundary, source_kind, source_sha256):
    if (boundary != BOUNDARY or source_kind not in
            ('INDEPENDENTLY_CAPTURED_REAL_FULL_ACTION_COST_CARD','SYNTHETIC_INTERFACE_CONTROL')
            or type(source_sha256) is not str or len(source_sha256) != 64
            or any(c not in '0123456789abcdef' for c in source_sha256)
            or type(rows) is not list or len(rows) != 8):
        raise ValueError('Bound complete eight-origin paired action-cost table required')
    actual = []
    by_origin = {}
    for row in rows:
        if type(row) is not dict:
            raise ValueError('Registered origin must be a structured receipt')
        origin = (row.get('scene'),row.get('step'))
        if origin not in ORIGINS or origin in by_origin:
            raise ValueError('Missing, duplicate or foreign registered origin')
        if row.get('incremental_post_paid_probe_cost_not_full_pair') is not True:
            raise ValueError('Incremental paid-probe boundary witness missing')
        costs, heads, readouts = (row.get(k) for k in
            ('costs','warmup_actual_output_head_calls','warmup_A_readouts'))
        if (not all(type(v) is dict for v in (costs,heads,readouts))
                or set(costs) != set(MODES) or set(heads) != set(MODES)
                or set(readouts) != set(MODES[1:3])):
            raise ValueError('All six actions and both explicit A receipts required')
        values = []
        for mode in MODES:
            timed = costs[mode]
            if (type(timed) is not list or len(timed) != 3
                    or any(not positive(v) for v in timed)):
                raise ValueError('All three finite positive timed repeats required')
            if mode in MODES[1:3]:
                a = readouts[mode]
                if (type(a) is not dict or type(a.get('extra_heads')) is not int or not 0 <= a['extra_heads'] <= 2
                        or heads[mode] != 2+a['extra_heads']
                        or a.get('extra_deep_blocks') != 0 or a.get('teacher_calls') != 0
                        or a.get('shared_alpha') != (1 if origin[1]<25 else .5)
                        or a.get('post_RF_fusion') is not True
                        or a.get('C_readout_updates_D_anchor') is not False):
                    raise ValueError('Actual shared A heads, phase or true-D semantics differ')
            elif heads[mode] != 2:
                raise ValueError('Actual original C/P/D pair must pay two output heads')
            values.append((mode,tuple(float(v) for v in timed)))
        by_origin[origin] = tuple(values)
    if set(by_origin) != set(ORIGINS):
        raise ValueError('Full four-scene two-origin denominator required')
    for scene,step in ORIGINS:
        actual.append((scene,step,by_origin[(scene,step)]))
    # Mean repeats within each origin, then equal origins. With this balanced
    # design, each scene and each registered time receive equal weight.
    means = {key:{m:math.fsum(v)/3 for m,v in values}
             for key,values in by_origin.items()}
    global_means = tuple((m,math.fsum(means[o][m] for o in ORIGINS)/8) for m in MODES)
    per_step = tuple((t,tuple((m,math.fsum(means[(s,t)][m] for s in SCENES)/4)
                     for m in MODES)) for t in (12,30))
    payload = {'source_kind':source_kind,'source_sha256':source_sha256,
               'boundary':boundary,'aggregation':RULE,'raw_all_144_timings':actual}
    fingerprint=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),
                                        allow_nan=False).encode()).hexdigest()
    return ActionCostRanking(fingerprint,source_kind,global_means,per_step,tuple(actual))
