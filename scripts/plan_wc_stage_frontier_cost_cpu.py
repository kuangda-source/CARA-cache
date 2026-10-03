#!/usr/bin/env python3
"""Budget the online test and full strong-baseline follow-up without submitting."""
import argparse
import hashlib
import json
import math
from pathlib import Path


def plan(previous_cost,terminal,f1):
    budget=terminal['budget'];used=budget['used_gpu_hours']
    assert budget['cap_gpu_hours']==12 and budget['gpu_jobs_launched']==42
    assert type(used) in (float,int) and math.isfinite(used) and 0<=used<12
    assert not any(k.endswith('_inflight') for k in budget)
    a=previous_cost['cost_admission'];dense=a['control_per_output_seconds']
    light=a['measurement_per_output_seconds'];load=a['load_seconds'];book=a['bookkeeping_seconds']
    native=max(p['seconds']['native']['end_to_end'] for p in f1['pairs'] if p['native_outcome']=='ACCEPTED')
    assert dense>=native and all(math.isfinite(v) and v>0 for v in (dense,light,load,book))
    rows=[]
    # Native/fewer-step/low/high-threshold WC and adaptive S are conservatively
    # charged the full proxy: no assumption about native skip decisions or
    # a linear reduction in runtime with denoising steps.
    for name,controls,n_full,n_light,outputs,cap in (
            ('online_two_exposed_CAL_window_and_cadence',2,4,2,8,3600),
            ('two_CAL_native_fewer_step_three_WC_points_and_selected_stage',2,10,2,14,6300),
            ('one_new_CONF_DD_native_fewer_step_selected_WC_and_stage',2,3,1,6,3000)):
        unbuffered=controls*dense+n_full*dense+n_light*light+load+book
        complete=unbuffered*1.2+30
        assert outputs==controls+n_full+n_light and complete<=cap
        rows.append({'name':name,'planned_outputs':outputs,'DD_controls':controls,
                     'full_proxy_outputs':n_full,'light_proxy_outputs':n_light,
                     'unbuffered_seconds':unbuffered,'buffer_factor':1.2,
                     'shutdown_seconds':30,'complete_planning_seconds':complete,
                     'proposed_cap_seconds':cap,'selected':False,'GPU_submitted':False})
    remaining=(12-used)*3600;total=sum(r['proposed_cap_seconds'] for r in rows)
    return {'status':'ONLINE_STAGE_AND_STRONG_BASELINE_COST_DRAFT_FIRST_CARD_FITS_ALL_CAPS_NOT_JOINTLY_ADMITTED',
            'CPU_only':True,'budget':budget,'remaining_seconds':remaining,'remaining_GPU_hours':12-used,
            'historical_accepted_native_max_seconds':native,'full_proxy_seconds':dense,
            'light_proxy_seconds':light,'load_seconds':load,'bookkeeping_seconds':book,
            'cards':rows,'all_three_proposed_caps_seconds':total,
            'all_three_caps_fit_current_budget':total+15<=remaining,
            'cap_sum_excess_seconds':max(0,total+15-remaining),
            'first_card_budget_admissible':rows[0]['proposed_cap_seconds']+15<=remaining,
            'first_two_caps_fit_current_budget':sum(r['proposed_cap_seconds'] for r in rows[:2])+15<=remaining,
            'reserved_seconds':0,'new_GPU_submission':False,'quality_acceptance':False,
            'limits':['Only costs, not selected execution cards; real source/CPU/assets/import/metadata and fresh admission still required.',
                'Adaptive stage outputs use the full proxy; fewer steps receive no runtime discount.',
                'Native and WC thresholds use current shared mode/pipeline; historical Native timing is a cost reference, not current output equivalence.',
                'Do not shrink baseline or CONF denominators to fit caps. Recompute after actual settlement/refund; no budget reset.',
                'Two exposed CAL and one new CONF are a bounded test, not the complete24-CAL/independent research plan.',
                'Automatic semantic/physics evaluation and larger independent confirmation need separately measured cost; not silently treated as free.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('previous-cost','terminal','f1','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();paths=[a.previous_cost,a.terminal,a.f1]
    r=plan(*(json.loads(f.read_text()) for f in paths))
    r['input_files_sha256']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths}
    r['planning_code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:r[k] for k in ('status','remaining_seconds','cards','all_three_caps_fit_current_budget','cap_sum_excess_seconds')}))
