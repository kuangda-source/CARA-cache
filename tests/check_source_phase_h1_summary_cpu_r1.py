"""Signed mixed outcomes, ratio-of-means and refusal of incomplete evidence."""
import copy,importlib.util,math
from pathlib import Path
from statistics import mean


def run():
    path=Path(__file__).resolve().parents[1]/'scripts/analyze_wc_source_phase_h1_complete_cpu_r1.py'
    spec=importlib.util.spec_from_file_location('actual_H1_summary',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    losses={'NATIVE':[0]*4,'RA':[.2,.3,.4,.5],'A_NO_P':[.18,.27,.45,.48],
        'P_OFF':[.19,.25,.43,.4],'TABLE_PHASE_H1':[.16,.28,.49,.51],'TABLE_POOLED_H1':[.17,.3,.42,.52]}
    times={'NATIVE':[300,310,320,330],'RA':[200,210,220,230],'A_NO_P':[210,202,218,240],
        'P_OFF':[215,220,225,230],'TABLE_PHASE_H1':[220,205,208,240],'TABLE_POOLED_H1':[200,215,225,245]}
    rows=[]
    for index in range(4):
        for method in module.METHODS:
            q=losses[method][index];frames=[q]*93
            row={'scene':str(index),'method':method,'section':'TIMED','status':'COMPLETE',
                'endpoint_audit':'PASS','decoded_video':{'frames':93},'core_seconds':times[method][index],
                'in_timing_hashes':0,'in_timing_guided_copies':0,'research_checkpoints':0,
                'LPIPS':{'mean_LPIPS':mean(frames),'frame_distances':frames},'actions':None if method=='NATIVE' else ['DD']*36,
                'guided_pairs':36,'solver_steps':36}
            if method.startswith('TABLE_'):
                hist=[];kind='D'
                for step in range(1,37):
                    protected=step<=7 or step==36
                    action='DD' if protected or step in (14,21,25) else 'PP' if step==18 else 'CC'
                    readout='A' if action=='CC' and step%2 else 'C'
                    optimizer=action=='DD' and not protected and step!=25
                    reason='actual_protected_dense' if protected else 'missing_current_calibration' if step==25 else 'MATH_EVENT_TABLE_ABSOLUTE_H1:'+('D' if optimizer else 'P' if action=='PP' else readout)
                    hist.append({'step':step,'action':action,'readout':readout,'protected':protected,
                        'heads':0 if action!='CC' or readout=='C' else 2 if kind=='D' else 4,
                        'decision':{'step':step,'action':action[0],'reason':reason,'state_before':[7,kind,7]},
                        'event':{'source_before':kind,'absolute_error_written_into_root_accumulator':False,
                            'actual_online_candidate_evaluations':0,'actual_online_teacher_calls':0,'optimizer_selected_D':optimizer}})
                    if action!='CC':kind=action[0]
                row['compact_source_history']=hist;row['actions']=[h['action'] for h in hist]
                row['counts']={'DD':11,'PP':1,'C_plain':sum(h['action']=='CC' and h['readout']=='C' for h in hist),
                    'A':sum(h['action']=='CC' and h['readout']=='A' for h in hist)}
            rows.append(row)
    comparisons=[]
    for candidate,base in module.PAIRS:
        values=[]
        for index in range(4):
            qa,qb=losses[candidate][index],losses[base][index];ta,tb=times[candidate][index],times[base][index]
            values.append({'scene':str(index),'LPIPS_change_percent':100*(qa/qb-1),'speedup_baseline_over_candidate':tb/ta})
        comparisons.append({'candidate':candidate,'baseline':base,'denominator':4,'scored_scenes':4,
            'scene_rows':values,'scene_equal_candidate_LPIPS':mean(losses[candidate]),'scene_equal_baseline_LPIPS':mean(losses[base])})
    capture={'final':{'status':'SOURCE_PHASE_H1_FULL24_SCIENCE_ALL36_AUDITED_93FRAME_SCORED',
        'scored_scientific_paths':24,'accepted_paths':36,'budget_before_sha256':'LEDGER','budget_after_sha256':'LEDGER',
        'warm_repeat_controls':[{'warm_repeats_outputs_actions_RGB_equal':True,'same_scene_formal_repeat_equal':True} for _ in range(6)],
        'original_baseline_controls':[{'status':'PASS_ORIGINAL_FINAL_ACTIONS_FULL93RGB_EQUAL'} for _ in range(16)],
        'rows':rows,'comparisons':comparisons},'supervisor':{'child_exit_code':0},'post_exit':{'exit_code':0},
        'original_processes':{'GPU':False,'POST':False},'kernel_lock_free':True,'payload_verified':{'f':True},'ledger_sha256':'LEDGER'}
    result=module.reconstruct(capture)
    pair=next(v for v in result['comparisons'] if v['candidate']=='TABLE_PHASE_H1' and v['baseline']=='RA')
    assert pair['quality_improved_scenes']==2 and pair['faster_scenes']==2
    assert math.isclose(pair['scene_equal_LPIPS_reduction_percent'],-100/35,rel_tol=1e-12)
    assert not math.isclose(pair['scene_equal_LPIPS_reduction_percent'],mean(v['LPIPS_reduction_percent'] for v in pair['per_scene']))
    assert all(v['better_frames']+v['worse_frames']+v['equal_frames']==93 for v in pair['per_scene'])
    assert all(v['protected_D']==8 and v['optimizer_D']==2 and v['nonprotected_nonoptimizer_D']==1 for v in result['actual_candidate_action_and_reason_counts'])
    refused=[]
    for fault in ('absent_final','incomplete_final','live_original','missing_frame','wrong_denominator','wrong_extra_heads','modified_mean'):
        bad=copy.deepcopy(capture)
        if fault=='absent_final':bad.pop('final')
        elif fault=='incomplete_final':bad['final']['status']='RUNNING'
        elif fault=='live_original':bad['original_processes']['GPU']=True
        elif fault=='missing_frame':bad['final']['rows'][1]['LPIPS']['frame_distances'].pop()
        elif fault=='wrong_denominator':bad['final']['comparisons'][0]['denominator']=3
        elif fault=='wrong_extra_heads':next(h for r in bad['final']['rows'] if r['method'].startswith('TABLE_') for h in r['compact_source_history'] if h['action']=='CC' and h['readout']=='A')['heads']=0
        else:bad['final']['rows'][1]['LPIPS']['mean_LPIPS']+=.01
        try:module.reconstruct(bad)
        except (AssertionError,ValueError):refused.append(fault)
        else:raise AssertionError('Invalid scientific summary accepted: '+fault)
    return {'status':'H1_SUMMARY_MIXED_SIGNS_RATIO_OF_MEANS_COMPLETE_SCOPE_REFUSALS_CPU_PASS',
        'mixed_positive_harmful_and_equal_frames_preserved':True,'ratio_of_means_not_mean_of_ratios':True,
        'D_reasons_and_extra_candidate_heads_separated':True,'refusals':refused,
        'synthetic_fixture_not_real_results':True,'GPU_submissions':0,'ledger_written':False}


if __name__=='__main__':
    import json
    print(json.dumps(run()))
