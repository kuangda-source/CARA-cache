"""Mixed scene outcomes, missing references and invalid provenance controls."""
import copy
import importlib.util
from pathlib import Path


def main():
    spec=importlib.util.spec_from_file_location('score_summary',Path(__file__).parents[1]/'src/wcomr/cfg_ra_comparison_scores.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    refs=[{'sample_name':n,'outcome':'ACCEPTED','artifact':{'sha256':str(i+1)*64}} for i,n in enumerate(m.NAMES)]
    pairs=[];costs=[]
    for i,n in enumerate(m.NAMES):
        for j,method in enumerate(m.METHODS):
            value=([.2,.18,.15] if i==0 else [.2,.23,.28])[j]
            pair={'sample_name':n,'method':method,'reference':refs[i]['artifact'],'candidate':{'sha256':str(j+3)*64},
                  'score':{'frames':93,'pts':[[k,'1/16'] for k in range(93)],'frame_distances':[value]*93,
                           'mean_LPIPS':value,'reference_sha256':refs[i]['artifact']['sha256'],'candidate_sha256':str(j+3)*64}}
            pairs.append(pair)
            costs.append({'sample_name':n,'method':method,'complete_branch_calls':38,
                          'instrumented_pipeline_wall_seconds':[200,210,190][j]})
        costs.append({'sample_name':n,'method':'NATIVE','complete_branch_calls':72,'instrumented_pipeline_wall_seconds':300})
    result=m.summarize(pairs,refs,costs)
    ra=result['scene_equal_aggregates'][-1]
    assert abs(ra['scene_equal_mean_WC_minus_method']+.015)<1e-12
    assert (ra['improved_scenes'],ra['degraded_scenes'])==(1,1)
    assert result['per_scene_method'][2]['improved_frames']==93 and result['per_scene_method'][-1]['degraded_frames']==93
    assert not result['per_scene_method'][1]['descriptive_same_run_fidelity_and_instrumented_time_both_improve']
    assert result['per_scene_method'][2]['descriptive_same_run_fidelity_and_instrumented_time_both_improve']
    missing=copy.deepcopy(refs);missing[1]={'sample_name':m.NAMES[1],'outcome':'VIDEO_REJECTED','artifact':None}
    partial=m.summarize(pairs[:3],missing,costs)
    assert partial['scored_pairs']==3 and partial['original_method_paths']==6 and partial['accepted_reference_scenes']==1
    assert not partial['missing_scores_filled_with_zero']
    bad=[]
    for kind in ('matrix','source','frames','mean','PTS','nonfinite','cost'):
        p,r,c=copy.deepcopy(pairs),copy.deepcopy(refs),copy.deepcopy(costs)
        if kind=='matrix':p.pop()
        if kind=='source':p[-1]['score']['reference_sha256']='f'*64
        if kind=='frames':p[-1]['score']['frame_distances'].pop()
        if kind=='mean':p[-1]['score']['mean_LPIPS']+=.01
        if kind=='PTS':p[-1]['score']['pts'][-1]=[0,'1/16']
        if kind=='nonfinite':p[-1]['score']['frame_distances'][-1]=float('nan')
        if kind=='cost':c[-1]['instrumented_pipeline_wall_seconds']=-1
        try:m.summarize(p,r,c)
        except ValueError:bad.append(kind)
        else:raise AssertionError('Invalid complete evaluation accepted: '+kind)
    print({'mixed_positive_negative_scenes_preserved':True,'rejected_reference_slot_not_replaced':True,
           'instrumented_time_and_fidelity_separate':True,'invalid_provenance_refusals':bad,'GPU_submissions':0})


if __name__=='__main__':main()
