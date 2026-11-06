"""Teacher-free production readout; isolated same-state E1 collection adapter.

No refresh changes, teacher inputs, IG fitting, GPU dispatcher or ledger writes.
The conservative implementation repeats C reconstruction; its cost is not hidden.
"""
import threading
import time
import torch
from .light_sampling import synchronize
from . import scout_parent_v22 as parent
from .scout_readout_v22 import ScoutReadoutKernel, LABELS, validate_state
from .scout_cfg_common_proposal_r1 import common_long_proposal
from .paper_latency_r1 import execute_with_timing
from .clean_speed20_r1 import patched

NEW_LABEL = 'R4_COMMON_LONG'
ALL_LABELS = LABELS + (NEW_LABEL,)
_LOCK = threading.Lock()

class CommonLongKernel(ScoutReadoutKernel):
    def evaluate(self, label, **kw):
        synchronize(); begin=time.perf_counter()
        value=self._evaluate_candidate(label, **kw)
        synchronize()
        value['diagnostic_readout_seconds']=time.perf_counter()-begin
        value['device_peak_allocated_cumulative_bytes']=(torch.cuda.max_memory_allocated()
            if torch.cuda.is_initialized() else None)
        value['peak_is_cumulative_not_incremental']=True
        value['clock_includes_roundtrip_copy_hash']=True
        return value

    def _evaluate_candidate(self, label, **kw):
        if label != NEW_LABEL:
            return super().evaluate(label, **kw)
        spans = validate_state(kw['context'], kw['step'], kw['xi'], kw['anchors'])
        a = super().evaluate('A_PHASE', **kw)
        if spans['age'] < 3:
            return dict(a, new_label=NEW_LABEL, fallback='EXACT_A_PHASE',
                        evaluated_components=['A_PHASE'], teacher_used=False)
        r = super().evaluate('R4_GLOBAL', **kw)
        c = super().evaluate('WC_C', **kw)
        outputs = common_long_proposal(C=c['outputs'], A_component=a['component_outputs'],
            R4_component=r['component_outputs'], step=kw['step'],
            anchor_step=kw['anchors'][0][-1].step)
        return dict(outputs=outputs, alpha=spans['alpha'], new_label=NEW_LABEL,
            evaluated_components=['A_PHASE','R4_GLOBAL','WC_C'], teacher_used=False,
            components_costed_separately=True,
            state_roundtrips=[a['state_roundtrip'],r['state_roundtrip'],c['state_roundtrip']],
            common_increment_only=True, difference_source='A_PHASE',
            parent_collector_not_deployment_latency=True)


def execute(inference, sample, *, timing_host, timing_cpu_validation=False, **kw):
    """Actual full sampler observer, with continuous and complete-request clocks.

Returns C-policy free-running video, NOT a CommonLong-policy video. Both clocks
include shadow/copy/I/O diagnostics and are ineligible as deployment latency.
"""
    if not _LOCK.acquire(blocking=False):
        raise RuntimeError('Concurrent common-long observer installation forbidden')
    original_sink = kw['sink']
    def costed_sink(payload):
        age=payload['step']-payload['source_anchor_steps'][-1]
        payload['legacy_readout_head_pairs']=payload['readout_head_pairs']
        payload['readout_head_pairs'] += 2 if age < 3 else 5
        payload['new_candidate_extra_head_pairs'] = 2 if age < 3 else 5
        original_sink(payload)
    kw=dict(kw,sink=costed_sink)
    try:
        with patched(parent,'ScoutReadoutKernel',CommonLongKernel), patched(parent,'LABELS',ALL_LABELS):
            result = execute_with_timing(parent.execute,inference,sample,
                host=timing_host,cpu_validation=timing_cpu_validation,
                expected_updates=36,diagnostic=True,**kw)
        result.update(readout_labels=list(ALL_LABELS),candidate=NEW_LABEL,
            free_running_policy='SHARED25_C',candidate_free_running=False,
            timing_is_diagnostic=True)
        return result
    finally:
        _LOCK.release()
