"""Mixed outcomes and registered contrast signs in the complete four-scene matrix."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def main():
    root=Path(__file__).parents[1]
    spec=importlib.util.spec_from_file_location('four_scene_scores',root/'src/wcomr/cfg_ra_plus_a_scores.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    refs=[{'sample_name':n,'outcome':'ACCEPTED','artifact':{'sha256':str(i+1)*64}} for i,n in enumerate(m.NAMES)]
    table=[[.20,.18,.15,.14,.13,.12,.11], [.20,.23,.28,.29,.27,.26,.25],
           [.30,.29,.32,.31,.33,.30,.28], [.40,.42,.38,.36,.39,.34,.37]]
    pairs=[];costs=[]
    for i,n in enumerate(m.NAMES):
        for j,method in enumerate(m.METHODS):
            value=table[i][j];candidate={'sha256':format(j+11,'064x')}
            pairs.append({'sample_name':n,'method':method,'reference':refs[i]['artifact'],'candidate':candidate,
                'score':{'frames':93,'pts':[[k,'1/16'] for k in range(93)],
                    'frame_distances':[value+.001*(k%3-1) for k in range(93)],'mean_LPIPS':value,
                    'reference_sha256':refs[i]['artifact']['sha256'],'candidate_sha256':candidate['sha256']}})
            costs.append({'sample_name':n,'method':method,'complete_branch_calls':38,
                'instrumented_pipeline_wall_seconds':200+10*j,
                'extra_candidate_heads':58 if j>=3 else 0,'A_teacher_calls':0,'A_extra_deep_blocks':0})
        costs.append({'sample_name':n,'method':'NATIVE','complete_branch_calls':72,'instrumented_pipeline_wall_seconds':320})
    result=m.summarize(pairs,refs,costs)
    assert (result['original_scenes'],result['original_method_paths'],result['original_reference_slots'],result['scored_pairs'])==(4,28,4,28)
    assert len(result['registered_contrasts'])==10
    for j,method in enumerate(m.METHODS):
        expected=[r[0]-r[j] for r in table];actual=result['scene_equal_aggregates'][j]
        assert actual['method']==method and math.isclose(actual['scene_equal_mean_WC_minus_method'],math.fsum(expected)/4,abs_tol=1e-12)
        assert actual['improved_scenes']==sum(v>0 for v in expected) and actual['degraded_scenes']==sum(v<0 for v in expected)
    for contrast in result['registered_contrasts']:
        a,b=m.METHODS.index(contrast['candidate']),m.METHODS.index(contrast['baseline'])
        expected=[row[b]-row[a] for row in table]
        assert math.isclose(contrast['scene_equal_mean_baseline_minus_candidate'],math.fsum(expected)/4,abs_tol=1e-12)
        for item,v in zip(contrast['per_scene'],expected):
            assert math.isclose(item['baseline_minus_candidate_LPIPS'],v,abs_tol=1e-12)
            assert (item['improved_frames'],item['degraded_frames'],item['tied_frames'])==(93*int(v>0),93*int(v<0),93*int(v==0))
            assert item['baseline_minus_candidate_instrumented_seconds']==10*(b-a)
            assert not item['frames_are_independent_samples'] and not item['clean_speed_claim']
    missing=copy.deepcopy(refs);missing[-1]={'sample_name':m.NAMES[-1],'outcome':'VIDEO_REJECTED','artifact':None}
    gap=m.summarize(pairs[:-7],missing,costs)
    assert gap['scored_pairs']==21 and gap['original_method_paths']==28 and gap['accepted_reference_scenes']==3
    assert not gap['missing_scores_filled_with_zero']
    no_refs=[{'sample_name':n,'outcome':'TEXT_REJECTED','artifact':None} for n in m.NAMES]
    empty=m.summarize([],no_refs,costs)
    assert empty['scored_pairs']==0 and all(c['scene_equal_mean_baseline_minus_candidate'] is None for c in empty['registered_contrasts'])
    bad=[]
    for kind in ('matrix','source','frames','mean','PTS','nonfinite','cost','missing_cost','call_count','reference_order'):
        p,r,c=copy.deepcopy(pairs),copy.deepcopy(refs),copy.deepcopy(costs)
        if kind=='matrix':p.pop()
        if kind=='source':p[-1]['score']['reference_sha256']='f'*64
        if kind=='frames':p[-1]['score']['frame_distances'].pop()
        if kind=='mean':p[-1]['score']['mean_LPIPS']+=.01
        if kind=='PTS':p[-1]['score']['pts'][-1]=[0,'1/16']
        if kind=='nonfinite':p[-1]['score']['frame_distances'][-1]=float('nan')
        if kind=='cost':c[-1]['instrumented_pipeline_wall_seconds']=-1
        if kind=='missing_cost':c.pop()
        if kind=='call_count':c[-1]['complete_branch_calls']=True
        if kind=='reference_order':r.reverse()
        try:m.summarize(p,r,c)
        except ValueError:bad.append(kind)
        else:raise AssertionError('Invalid complete evaluation accepted: '+kind)
    sources=['src/wcomr/cfg_ra_plus_a_scores.py','tests/check_cfg_ra_plus_a_scores_cpu.py']
    report={'complete_matrix_and_ten_contrasts_verified':True,'sample_names':m.NAMES,'methods':m.METHODS,
        'mixed_positive_negative_scenes_preserved':True,'rejected_reference_slot_not_replaced':True,
        'all_rejected_slots_retained_without_zero_fill':True,'instrumented_time_and_fidelity_separate':True,
        'invalid_provenance_refusals':bad,'GPU_submissions':0,'new_metric_execution':False,
        'source_sha256':{n:hashlib.sha256((root/n).read_bytes()).hexdigest() for n in sources}}
    target=root/'reports/wc_ra_plus_a_score_summary_cpu_controls_20261010.json'
    assert not target.exists();target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
