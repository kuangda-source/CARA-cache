#!/usr/bin/env python3
"""Complete accepted104/112 attribution, no fitting or dispatch.

Counterfactual anchors only cover 64 cache targets. The independent PG-fullD
control cannot simultaneously serve as a replacement anchor and a test target.
"""
import argparse
import hashlib
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.policy_generator_r1.cost112_terminal import accept as accept112
from wcomr.policy_generator_r1.historical_terminal import accept as accept104


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_accepted(cap, acceptance, replay):
    v = json.loads(cap.read_text()); a = json.loads(acceptance.read_text())
    assert a['capture_sha256'] == sha(cap)
    assert replay(v) == {k:x for k,x in a.items() if k not in ('capture_ref','capture_sha256')}
    return v, a


def components(r):
    c = dict(install=r['method_install_seconds'], pipeline_core=r['core_seconds'],
             guarded_outside_core=r['guarded_pipeline_without_write_seconds']-r['core_seconds'],
             video_write=r['video_write_seconds'], cleanup=r['method_cleanup_seconds'])
    assert abs(sum(c.values())-r['full_request_seconds']) < 1e-8
    return c


def stats(xs):
    return dict(n=len(xs), mean=st.mean(xs), minimum=min(xs), maximum=max(xs),
                stdev=st.stdev(xs) if len(xs)>1 else 0.)


def run(c112, a112, c104, a104):
    v, a = load_accepted(c112,a112,accept112); old, _ = load_accepted(c104,a104,accept104)
    validation = a['scientific']['timing']['validation']; req = v['requests']
    controls = {(r['member'],r['repeat']):r for r in validation if r['role']=='PG_ALL_D'}
    thermal = {}
    for line in v['monitor_raw_utf8'].splitlines():
        r=json.loads(line)
        if r.get('thermal'):thermal[r['thermal']['observed_unix']]=r['thermal']

    def thermal_fraction(r):
        xs=[x for t,x in thermal.items() if r['started_unix']<=t<=r['ended_unix']]
        assert xs
        return sum(x['SW_thermal_slowdown']=='Active' for x in xs)/len(xs)

    rows=[]; control_rows=[]
    for row in validation:
        target=req[row['id']]['result']; anchor=req[row['anchor_id']]['result']
        control=req[controls[row['member'],row['repeat']]['id']]['result']
        tc,ac,gc=components(target),components(anchor),components(control)
        drift={k:gc[k]-ac[k] for k in ac}
        save=row['anchor_seconds']-row['predicted_seconds']
        remainder={k:tc[k]-gc[k] for k in tc}
        remainder['pipeline_core']+=save
        assert abs(sum(drift.values())+sum(remainder.values())-row['underestimate_seconds'])<1e-8
        r=dict(**row,components_target=tc,components_anchor=ac,components_control=gc,
               reference_control_drift_seconds=sum(drift.values()),reference_control_components=drift,
               remaining_after_control_seconds=sum(remainder.values()),remaining_components=remainder,
               anchor_age_seconds=target['started_unix']-anchor['started_unix'],
               target_thermal_fraction=thermal_fraction(target),anchor_thermal_fraction=thermal_fraction(anchor),
               control_thermal_fraction=thermal_fraction(control))
        rows.append(r)
        if row['role']=='PG_ALL_D':control_rows.append(r)
    cache=[r for r in rows if r['role']!='PG_ALL_D'];counterfactual=[]
    for rule in ('original','later_control','mean_two','max_two'):
        errors=[]
        for r in cache:
            anchor=r['anchor_seconds']; ctrl=anchor+r['reference_control_drift_seconds']
            control_id=controls[r['member'],r['repeat']]['id']
            assert req[control_id]['result']['ended_unix'] < req[r['id']]['result']['started_unix']
            replacement={'original':anchor,'later_control':ctrl,'mean_two':(anchor+ctrl)/2,'max_two':max(anchor,ctrl)}[rule]
            err=r['underestimate_seconds']-(replacement-anchor)
            errors.append((err,abs(err)/r['actual_seconds']))
        counterfactual.append(dict(rule=rule,targets=64,independent_validation=False,
            mean_absolute_relative_error=st.mean(x[1] for x in errors),maximum_underestimate_seconds=max(x[0] for x in errors),
            underestimate_over2_count=sum(x[0]>2 for x in errors)))
    matched=[]
    for identifier, new in req.items():
        s=new['slot']
        if s['section'] not in ('CALIBRATION','VALIDATION'):continue
        prior=old['requests'][identifier]
        assert prior['slot']['member']==s['member'] and prior['policy']==new['policy']
        nc,oc=components(new['result']),components(prior['result'])
        matched.append(dict(id=identifier,member=s['member'],role=s['role'],repeat=s['repeat'],
            delta_seconds={k:nc[k]-oc[k] for k in nc},
            full_delta_seconds=new['result']['full_request_seconds']-prior['result']['full_request_seconds']))
    assert len(matched)==80
    groups={}
    for label,rs in [('all72',rows),('cache64',cache),('fullD8',control_rows),
                     ('thermal_at_target', [r for r in rows if r['target_thermal_fraction']>0]),
                     ('no_observed_target_thermal',[r for r in rows if r['target_thermal_fraction']==0])]:
        groups[label]=dict(underestimate=stats([r['underestimate_seconds'] for r in rs]),
            reference_drift=stats([r['reference_control_drift_seconds'] for r in rs]),
            underestimate_over2_count=sum(r['underestimate_seconds']>2 for r in rs))
    return dict(status='COMPLETE104_112_ATTRIBUTION_NO_FIT_NO_GPU',
        inputs={str(p):sha(p) for p in (c112,a112,c104,a104)},
        original112_timing_gate_failed=not a['timing_model_validated'],
        numerical_decomposition_is_not_causal_attribution=True,coefficients_changed=False,
        validation_rows_removed=0,thresholds_changed=False,new_GPU_submissions=0,server_changes=False,
        worst=max(rows,key=lambda x:x['underestimate_seconds']),control_drift8=control_rows,
        groups=groups,counterfactual_anchor_rules_cache64=counterfactual,
        matched104_112_differences80=matched,
        matched_mean_delta_seconds={k:st.mean(r['delta_seconds'][k] for r in matched) for k in matched[0]['delta_seconds']},
        matched_full_delta_seconds=stats([r['full_delta_seconds'] for r in matched]),
        per_role_mean_delta={role:{k:st.mean(r['delta_seconds'][k] for r in matched if r['role']==role) for k in matched[0]['delta_seconds']} for role in sorted({r['role'] for r in matched})},
        rows72=rows,limitations=[
            'core_seconds includes the entire generate_vid2world call, not only denoising; guarded_outside_core includes text/video guardrails and other outer processing.',
            'The independent fullD control measures an earlier same-block deviation; it cannot identify the exact common drift at the later cache request.',
            'Thermal exposure groups are descriptive, workload-confounded and not independent randomized groups; 30-second observations may miss transient throttling.',
            'Two runs on identical prompts/seeds are paired repeat observations, not new inputs; no old GPU or current idle device state identifies historical thermal causality.'])


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('capture112','accepted112','capture104','accepted104','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();v=run(a.capture112,a.accepted112,a.capture104,a.accepted104)
    with a.output.open('x') as f:json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
    print(json.dumps({k:v[k] for k in ('status','groups','counterfactual_anchor_rules_cache64','matched_mean_delta_seconds','matched_full_delta_seconds')},ensure_ascii=False,indent=2))
