"""Read-only local B screen: clocks, observed timing bounds and oracle prices."""
import argparse
import hashlib
import json
from pathlib import Path


def analyze(capture, relative):
    final = capture['final']; rows = []
    for b in final['B_points']:
        point = next(p for p in final['points'] if (p['scene'],p['step']) == (b['scene'],b['step']))
        actual = next(r for r in relative['rows'] if (r['scene'],r['step']) == (b['scene'],b['step']))
        identity = point['feature_row']['identity']; gain = point['feature_row']['raw_full_paid_proxies']['gain']
        methods = []; dense = next(v for v in b['summaries'] if v['mode']=='DENSE_PLAIN')
        for mode in b['summaries']:
            m = next(r for r in actual['methods'] if r['mode']==mode['mode'])
            assert m['absolute_guided_MSE'] == mode['absolute_guided_MSE']
            assert m['median_seconds'] == mode['median_seconds'] and len(mode['timed_seconds'])==3
            times=mode['timed_seconds']; delta=dense['median_seconds']-mode['median_seconds']
            risk=gain*gain*mode['absolute_guided_MSE']
            breakpoint=delta/risk if risk>0 and delta>0 else None
            methods.append(dict(mode=mode['mode'],actual_three_times_seconds=times,
                median_seconds=mode['median_seconds'],range_seconds=max(times)-min(times),
                absolute_guided_MSE=mode['absolute_guided_MSE'],relative_guided_RMSE=m['relative_guided_RMSE'],
                all_observed_candidate_times_below_all_observed_dense_times=max(times)<min(dense['timed_seconds']),
                nominal_seconds_saved_vs_D=delta,
                posthoc_local_D_vs_mode_lambda_breakpoint=breakpoint,
                primary_525_146_local_oracle_prefers_mode_over_D=delta>525.1463509809399*risk))
        dominates=[]
        for a in methods:
            for other in methods:
                if a['mode']==other['mode']:continue
                if (a['absolute_guided_MSE']<=other['absolute_guided_MSE']
                        and max(a['actual_three_times_seconds'])<min(other['actual_three_times_seconds'])):
                    dominates.append(dict(faster_mode=a['mode'],dominated_mode=other['mode'],
                        error_no_greater_and_observed_timing_intervals_disjoint=True))
        l2=next(v for v in b['summaries'] if v['mode']=='L2')
        records=l2['all_four_trial_receipts'][1]['arm']['records']
        assert len(records)==4 and {r['age'] for r in records}=={2}
        assert all(r['born']==identity['source_birth'] and r['source_kind']==identity['source_kind'] for r in records)
        rows.append(dict(scene=b['scene'],step=b['step'],parent_continues=point['parent_continues'],
            input_sha256=point['input_sha256'],source_state_sha256=point['source_state_sha256'],
            true_D_state_sha256=point['true_D_state_sha256'],artifact=point['artifact'],
            working_source=identity['source_kind'],working_age=2,source_tau=identity['source_tau'],
            current_tau=identity['current_tau'],actual_delta_tau=abs(identity['source_tau']-identity['current_tau']),
            true_D_tau=identity['true_D_tau'],gain=gain,L2_layer_provenance=records,
            logical_L2_bank_bytes=l2['all_four_trial_receipts'][1]['arm']['cache_bytes'],
            diagnostic_shared_history_bytes=l2['all_four_trial_receipts'][1]['parent_history_bytes'],
            deployment_memory_tax_measured=False,methods=methods,observed_robust_local_dominance=dominates))
    assert len(rows)==4 and all(r['parent_continues']=='CC' for r in rows)
    return dict(status='FOUR_B_STATES_CLOCK_TIMING_AND_LOCAL_ORACLE_RECONSTRUCTED_NOT_POLICY',rows=rows,
        conclusions=dict(physical_skip_saving_exceeds_within_card_observed_repeat_range=True,
            equal_step_age_does_not_mean_equal_tau_span=True,
            smaller_tau_span_is_not_sufficient_for_smaller_observed_L2_error=True,
            source_and_phase_not_causally_separated=True),
        limitations=['Three repeated points are observed bounds, not statistical confidence intervals.',
            'Mode risks use saved same-state teacher labels; the oracle breakpoint is not an online rule.',
            'Full paired D/B prices share probes here; no C/A or cross-card price equivalence is claimed.',
            'Borrowed diagnostic bank bytes are not isolated deployment allocated/reserved/peak memory.',
            'No endpoint video for B, no continuous refresh/source-lifetime or global sparse claim.'],
        GPU_submissions=0,ledger_written=False,inflight_confirmation_not_observed=True)


def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);a=p.parse_args()
    first=a.root/'reports/wc_fb_probe_scheduled_collection_20261013.json'
    second=a.root/'reports/wc_fb_probe_B_relative_error_independent_analysis_20261013.json'
    value=analyze(json.loads(first.read_text()),json.loads(second.read_text()))
    value['source_sha256']={str(x.relative_to(a.root)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (first,second)}
    out=a.root/'reports/wc_B_probe_clocks_timing_oracle_conditions_20261013.json'
    assert not out.exists();out.write_text(json.dumps(value,indent=2)+'\n')
    for r in value['rows']:
        l=next(m for m in r['methods'] if m['mode']=='L2')
        print(r['scene'],r['step'],'delta_tau',r['actual_delta_tau'],'lambda_breakpoint',l['posthoc_local_D_vs_mode_lambda_breakpoint'])


if __name__=='__main__':main()
