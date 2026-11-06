#!/usr/bin/env python3
"""Local structural controls only; no CUDA, weights, SSH or sampling."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.interval_policy_v6_r1 import compile_interval_plan,initial_development_candidates,select_calibrated_candidate


def validate():
    checks=[]
    def check(name,condition):
        if not condition:raise AssertionError(name)
        checks.append(dict(name=name,passed=True))
    def reject(name,call):
        try:call()
        except ValueError:check(name,True)
        else:raise AssertionError(name)
    p=initial_development_candidates()
    check('full21_interval_ends_at_retained24',p['K25_FRONT_FULL'].correction_steps==(21,22,23))
    check('late_only_keeps_C21',p['K25_FRONT_LATE'].correction_steps==(22,23))
    check('move22_truncates_drop21_interval',p['K25_MOVE22_DROP21_FULL'].correction_steps==(21,))
    check('move_only_is_plain_C',not p['K26_MOVE22_C'].correction_steps)
    check('moving_D_does_not_request_correction_at33',p['K25_MOVE22_DROP21_FULL'].actions[32]=='C')
    check('same_25D_single_A_position_control',p['SINGLE22'].dense_steps==p['SINGLE23'].dense_steps
        and len(p['SINGLE22'].correction_steps)==len(p['SINGLE23'].correction_steps)==1)
    check('full_C_A_layout_pair_same_D_and_alpha',p['K26_MOVE22_C'].dense_steps==p['K26_MOVE22_FULL'].dense_steps
        and p['K26_MOVE22_FULL'].alpha==p['K26_FRONT_FULL'].alpha==1)
    check('A_never_reanchors',p['K25_FRONT_FULL'].source_steps[20:24]==(20,20,20,20))
    reject('stale_A22_overlay_rejected',lambda:compile_interval_plan(move_dense=((33,22),),
        drop_dense=(21,),coverage='explicit_ablation',explicit_A=(21,22,23)))
    reject('protected_boundary_deletion_rejected',lambda:compile_interval_plan(drop_dense=(1,)))
    reject('excess_source_age_rejected',lambda:compile_interval_plan(base_dense=tuple(range(1,8))+(36,)))
    reject('ambiguous_move_drop_rejected',lambda:compile_interval_plan(move_dense=((33,22),),drop_dense=(33,)))
    reject('nonfinite_alpha_rejected',lambda:compile_interval_plan(alpha=float('nan')))
    # These are structural examples only, not accepted real model windows.
    check('other_window_shapes_compile',compile_interval_plan(drop_dense=(20,)).correction_steps==(20,)
          and compile_interval_plan(drop_dense=(27,)).correction_steps==(27,28,29))
    scenes=('cal_a','cal_b'); candidates=('simple','interval')
    rows=[dict(candidate=c,scene=s,status='COMPLETE',LPIPS=.1 if c=='simple' else .08,
               measured_seconds=10 if c=='simple' else 11,measurement_protocol_sha256='a'*64)
               for c in candidates for s in scenes]
    args=dict(scenes=scenes,candidates=candidates,per_prompt_loss_ceiling={s:.12 for s in scenes},
              tail_limit=0,measurement_protocol_sha256='a'*64)
    check('budget_changes_shared_choice',select_calibrated_candidate(rows,budget_seconds=10,**args)['selected']=='simple'
          and select_calibrated_candidate(rows,budget_seconds=11,**args)['selected']=='interval')
    failed=[dict(r) for r in rows];failed[-1]['status']='VIDEO_REJECTED'
    check('refused_endpoint_retained_no_imputation',select_calibrated_candidate(failed,budget_seconds=11,**args)['selected']=='simple')
    reject('incomplete_matrix_rejected',lambda:select_calibrated_candidate(rows[:-1],budget_seconds=11,**args))
    reject('foreign_test_row_rejected',lambda:select_calibrated_candidate(rows+[dict(rows[0],scene='test')],budget_seconds=11,**args))
    mixed=[dict(r) for r in rows];mixed[-1]['measurement_protocol_sha256']='b'*64
    reject('mixed_legacy_diagnostic_clock_rejected',lambda:select_calibrated_candidate(mixed,budget_seconds=11,**args))
    return dict(status='LOCAL_STRUCTURAL_COMPILER_AND_CAL_SELECTION_CONTROLS_PASS',checks=checks,
        number_of_checks=len(checks),candidate_plans={k:v.manifest() for k,v in p.items()},
        synthetic_selector_fixtures_not_research_results=True,
        source_bindings={str(x.relative_to(ROOT)):dict(sha256=hashlib.sha256(x.read_bytes()).hexdigest(),bytes=x.stat().st_size)
            for x in (ROOT/'src/wcomr/interval_policy_v6_r1.py',Path(__file__).resolve())},
        actual_production_CPU_accepted=False,GPU_dispatch_ready=False,
        CUDA_calls=0,model_loads=0,SSH_calls=0,new_GPU_submissions=0,new_video_results=None)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--output',required=True);ns=a.parse_args()
    result=validate();out=Path(ns.output);out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','number_of_checks','actual_production_CPU_accepted','new_GPU_submissions')}))
