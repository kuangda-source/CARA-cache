"""Full cost-input scope and shared-prefix invariance; synthetic only, no Torch."""
import copy
import json
import math
from pathlib import Path
from types import SimpleNamespace
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.action_cost_ranking import BOUNDARY,MODES,ORIGINS,build_ranking
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs,PartialPrior,SourceAwareCPDController


def fixture():
    rows=[]
    for i,(scene,step) in enumerate(ORIGINS):
        means=dict(zip(MODES,(.25,.5,.75,2.,2.25,2.5)))
        rows.append({'scene':scene,'step':step,
            'costs':{m:[v+(i%2)/8+j/16 for j in range(3)] for m,v in means.items()},
            'warmup_actual_output_head_calls':dict(zip(MODES,(2,4,4,2,2,2))),
            'warmup_A_readouts':{m:{'extra_heads':2,'extra_deep_blocks':0,
                'teacher_calls':0,'shared_alpha':1 if step<25 else .5,
                'post_RF_fusion':True,'C_readout_updates_D_anchor':False} for m in MODES[1:3]},
            'incremental_post_paid_probe_cost_not_full_pair':True})
    return rows


def build(rows):
    return build_ranking(rows,boundary=BOUNDARY,
        source_kind='SYNTHETIC_INTERFACE_CONTROL',source_sha256='1'*64)


def main():
    rows=fixture();saved=copy.deepcopy(rows);ranking=build(rows)
    assert rows==saved and len(ranking.complete_raw_timings)==8
    assert sum(len(values)*3 for _,_,values in ranking.complete_raw_timings)==144
    assert dict(ranking.global_means)==dict(zip(MODES,(.375,.625,.875,2.125,2.375,2.625)))
    assert build(list(reversed(rows)))==ranking
    cal=Calibration('SYNTHETIC_PREFIX_INVARIANCE',
        {(a,s):1. for a in range(1,36) for s in range(a+1,37)},
        {s:1. for s in range(1,37)})
    prior=PartialPrior('SYNTHETIC_POSITIVE_P_CREATION_FLOOR',.1,.2)
    full_paths=updates=0
    actions=set()
    for reuse in MODES[:3]:
        base=ranking.for_reuse_mode(reuse)
        assert base.D==dict(ranking.global_means)['DENSE_WITH_P0']
        for values in ([.4]*35,[0.]*35,[.2,1.,.01,.7,.3]*7,[.5]*35):
            reference=None
            for prefix in (0.,.5,8.):
                costs=base if prefix==0 else Costs('SYNTHETIC_COMPLETE_COSTS_PREFIX='+str(prefix),
                            base.C+prefix,base.D+prefix,base.P+prefix)
                owner=SourceAwareCPDController(cal,1.,costs,prior)
                owner.commit_protected_dense(1,actual_action='D',pair_completed=True)
                for step,value in enumerate(values,2):
                    packet=[SimpleNamespace(slot=b,counter=2*(step-1)%70+b,
                                            delta_y=value) for b in (0,1)]
                    decision=owner.decide(step,packet,both_sources_ready=True,partial_ready=True)
                    owner.commit(decision,actual_action=decision.action,pair_completed=True)
                got=([c.action for c in owner.history],owner._state())
                if reference is None:reference=got
                else:assert got==reference
                checkpoint=owner.state_dict();owner.restore(checkpoint)
                assert owner.state_dict()==checkpoint and not owner.poisoned
                actions.update(got[0]);full_paths+=1;updates+=36
    assert (full_paths,updates)==(36,1296) and actions=={'C','P','D'}
    refusals=[]
    mutations=[('missing_origin',lambda x:x.pop()),
        ('duplicate_origin',lambda x:x.__setitem__(-1,copy.deepcopy(x[0]))),
        ('foreign_scene',lambda x:x[0].update(scene='unknown')),
        ('foreign_step',lambda x:x[0].update(step=13)),
        ('missing_C',lambda x:x[0]['costs'].pop('C')),
        ('missing_A',lambda x:x[0]['costs'].pop('A_W1_ONE_PHASE')),
        ('warmup_as_repeat',lambda x:x[0]['costs']['C'].append(1.)),
        ('missing_repeat',lambda x:x[0]['costs']['C'].pop()),
        ('zero_time',lambda x:x[0]['costs']['C'].__setitem__(0,0.)),
        ('negative_time',lambda x:x[0]['costs']['C'].__setitem__(0,-1.)),
        ('nonfinite_time',lambda x:x[0]['costs']['C'].__setitem__(0,float('nan'))),
        ('boolean_time',lambda x:x[0]['costs']['C'].__setitem__(0,True)),
        ('wrong_boundary',lambda x:x[0].update(incremental_post_paid_probe_cost_not_full_pair=False)),
        ('missing_head',lambda x:x[0]['warmup_actual_output_head_calls'].pop('C')),
        ('unpaid_C_head',lambda x:x[0]['warmup_actual_output_head_calls'].update(C=1)),
        ('unpaid_A_head',lambda x:x[0]['warmup_actual_output_head_calls'].update(A_W1_ONE_PHASE=2)),
        ('wrong_phase',lambda x:x[0]['warmup_A_readouts']['A_W1_ONE_PHASE'].update(shared_alpha=.5)),
        ('teacher_in_A',lambda x:x[0]['warmup_A_readouts']['A_W1_ONE_PHASE'].update(teacher_calls=1)),
        ('false_D_anchor',lambda x:x[0]['warmup_A_readouts']['A_W1_ONE_PHASE'].update(C_readout_updates_D_anchor=True))]
    for label,mutate in mutations:
        bad=copy.deepcopy(rows);mutate(bad)
        try:build(bad)
        except ValueError:refusals.append(label)
        else:raise AssertionError('Altered complete cost table accepted: '+label)
    assert len(refusals)==19 and rows==saved
    return {'status':'FULL_COST_RANKING_CPU_PASS_SYNTHETIC_NOT_ACTUAL_TIMINGS',
        'full_cost_rows':48,'all_timed_values':144,'full_policy_paths':full_paths,
        'full_policy_updates':updates,'all_three_actions_exercised':True,
        'shared_prefix_decisions_and_risk_state_equal':True,'healthy_restore':True,
        'source_input_unchanged':True,'registered_refusals':refusals,
        'two_stage_costs_not_installed':True,'GPU_submissions':0,'ledger_written':False,
        'real_cost_or_new_policy_video_or_quality_claim':False}


if __name__=='__main__':print(json.dumps(main()))
