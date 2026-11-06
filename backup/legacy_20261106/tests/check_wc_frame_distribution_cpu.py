"""Descriptive temporal tradeoffs, timestamps and full-frame coverage controls."""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path


def run(root):
    spec=importlib.util.spec_from_file_location('frame_analysis', root/'scripts/analyze_wc_frame_distribution_cpu.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    def pair(values, candidate):
        return {'reference': {'sha256': 'a'*64}, 'candidate': {'sha256': candidate*64},
            'score': {'frames':93,'pts': [[i,'1/16'] for i in range(93)],
                'frame_distances':values,'mean_LPIPS':sum(values)/93,
                'reference_sha256':'a'*64,'candidate_sha256':candidate*64}}
    # A small positive video mean can coexist with a whole deteriorated time interval.
    base=pair([.4]*93,'b');new=pair([.3]*31+[.5]*31+[.35]*31,'c')
    bins=[[0,30],[31,61],[62,92]];result=module.compare(base,new,bins=bins)
    assert result['positive_frames']==62 and result['negative_frames']==31 and result['zero_frames']==0
    assert [r['mean_baseline_minus_variant']>0 for r in result['bin_means']]==[True,False,True]
    assert math.isclose(result['mean_paired_difference'], .05/3, abs_tol=1e-12)
    assert math.isclose(result['variant_mean_largest10_distances'], .5, abs_tol=1e-12)
    assert math.isclose(result['paired_difference_quantiles_type7']['0.5'], .05, abs_tol=1e-12)
    assert module.quantile([0,2,4],.25)==1 and module.quantile([0,2,4],.75)==3
    zero=module.compare(base,copy.deepcopy(base),bins=bins)
    assert zero['zero_frames']==93 and zero['positive_frames']==0 and zero['mean_paired_difference']==0
    refusals=[]
    for name in ['truncated','subsample','duplicate_pts','other_pts','reference','candidate','nonfinite','changed_mean','other_bins']:
        changed=copy.deepcopy(new);b=copy.deepcopy(bins)
        if name=='truncated':changed['score']['frames']=92
        elif name=='subsample':changed['score']['frame_distances'].pop()
        elif name=='duplicate_pts':changed['score']['pts'][1]=changed['score']['pts'][0].copy()
        elif name=='other_pts':changed['score']['pts'][0][0]=-1
        elif name=='reference':changed['reference']['sha256']='d'*64;changed['score']['reference_sha256']='d'*64
        elif name=='candidate':changed['score']['candidate_sha256']='d'*64
        elif name=='nonfinite':changed['score']['frame_distances'][0]=float('nan')
        elif name=='changed_mean':changed['score']['mean_LPIPS']+=.1
        elif name=='other_bins':b=[[0,30],[31,61],[63,92]]
        try:module.compare(base,changed,bins=b)
        except ValueError:refusals.append(name)
        else:raise AssertionError('Invalid distribution input accepted: '+name)
    return {'status':'FRAME_DISTRIBUTION_TEMPORAL_TRADEOFF_AND_FULL_COVERAGE_CPU_CONTROL_PASS',
        'refusals':refusals,'controlled_distributed_mixed_and_exact_zero':True,
        'true_video_scores':False,'GPU_submissions':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    print(json.dumps(run(parser.parse_args().root)))
