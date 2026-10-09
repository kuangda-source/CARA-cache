"""Development controls and one predetermined RA threshold initialization.

The threshold uses paid features on the accepted shared-D6 calibration parents,
never candidate endpoint quality. It is an initial operating point, not an
equal-time guarantee or an additional fit to generated candidate videos.
"""
from statistics import median

from .cfg_ra_calibration import SharedSchedulePairExecutor
from .cfg_ra_joint_control import Calibration, finite_nonnegative, guided_proxy


THRESHOLD_RULE = 'MEDIAN_EIGHT_COMPLETE_SHARED_D6_INTERVAL_PAID_RISKS'


def threshold_from_collection(state, calibration):
    if (not isinstance(calibration, Calibration) or state.get('planned_parent_paths') != 4
            or state.get('planned_child_arms') != 12 or not state.get('initial_state_restored')
            or len(state.get('requests', [])) != 2):
        raise ValueError('Complete accepted shared-D6 collection and bound prior required')
    from .cfg_ra_calibration_sampling import verify_batch
    verify_batch(state)
    intervals = []
    for request in state['requests']:
        history = request['paths'][0]['own_history']
        if len(history) != 36 or [h['step'] for h in history] != list(range(1,37)):
            raise ValueError('Complete observed paid-feature collection history required')
        for anchor, stop in ((7,13),(13,19),(19,25),(25,31)):
            risks = []
            for step in range(anchor+1,stop+1):
                record = history[step-1]
                packets = record['paid_probes']
                if (record['anchor_before'] != anchor or record['protected']
                        or len(packets) != 2
                        or [(p['slot'],p['counter']) for p in packets]
                        != [(0,2*(step-1)),(1,2*(step-1)+1)]
                        or record['action'] != ('DD' if step == stop else 'CC')
                        or (anchor,step) not in calibration.rho_at
                        or step not in calibration.gains):
                    raise ValueError('Complete observed six-step shared interval differs')
                proxy = guided_proxy(packets[0]['delta_y'],packets[1]['delta_y'],
                    calibration.rho_at[(anchor,step)])
                added = proxy*calibration.gains[step]
                if not finite_nonnegative(added):
                    raise ValueError('Nonfinite observed interval risk')
                risks.append({'step':step,'paid_branch_proxies':[p['delta_y'] for p in packets],
                    'guided_proxy':proxy,'propagation_gain':calibration.gains[step],
                    'added_risk':added})
            total = sum(r['added_risk'] for r in risks)
            if not finite_nonnegative(total):
                raise ValueError('Nonfinite complete interval sum')
            intervals.append({'sample_name':request['sample_name'],'anchor':anchor,
                'refresh_step':stop,'paid_risks':risks,'accumulated_risk':total})
    threshold = median(i['accumulated_risk'] for i in intervals)
    if len(intervals) != 8 or not finite_nonnegative(threshold) or threshold == 0:
        raise ValueError('Positive observed initial RA operating point unavailable')
    return {'rule':THRESHOLD_RULE,'threshold':threshold,
        'calibration_fingerprint':calibration.fingerprint,'observed_intervals':intervals,
        'endpoint_quality_used_to_choose_threshold':False,
        'matches_actual_RA_time_or_dense_count':False,
        'development_initial_point_not_optimized_threshold':True}


class JointNativePairExecutor(SharedSchedulePairExecutor):
    """Simple control: refresh both if either actual native paid probe says D."""
    def _select(self, packets):
        step = len(self.history)+1
        if (not self.running or self._selection is not None or self.forced_action is not None
                or len(packets) != 2
                or [(p.slot,p.counter) for p in packets]
                != [(0,2*(step-1)%70),(1,2*(step-1)%70+1)]
                or any(type(p.native_cache) is not bool for p in packets)):
            raise ValueError('One actual source-bound native joint selection required')
        self._selection = 'CC' if all(p.native_cache for p in packets) else 'DD'
        return self._selection
