#!/usr/bin/env python3
"""Stdlib-only complete64 statistics fixtures, not video/LPIPS evaluation."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    from wcomr.current_birth_full64_scores_r1 import (
        COUNTS,METHODS,STRATEGIES,NAMES,LEGACY_METHODS,pairing_slots,actual_costs,summarize)
    target=Path('reports/wc_current_birth_full64_scores_cpu_r1_results_20261010.json')
    assert not target.exists()
    registry=Path('manifests/wc_current_birth_full64_scoring_source_r1_preregistration_20261010.json')
    reg=json.loads(registry.read_text())
    sha=lambda n:hashlib.sha256(Path(n).read_bytes()).hexdigest()
    assert {n:sha(n) for n in reg['source_sha256']}==reg['source_sha256']
    def art(label):return {'path':'/synthetic/'+label+'.mp4','bytes':1,'sha256':hashlib.sha256(label.encode()).hexdigest()}
    def score(ref,candidate,value):
        values=[value+.001*(i%5) for i in range(93)]
        return {'frames':93,'pts':[[i,'1/16'] for i in range(93)],'frame_distances':values,
            'mean_LPIPS':sum(values)/93,'reference_sha256':ref['sha256'],'candidate_sha256':candidate['sha256']}
    runner={'planned_scope':COUNTS,'completed_strategies':list(STRATEGIES),'batches':{}}
    pairing={};pairs=[];legacy={'pairs':[]}
    for si,strategy in enumerate(STRATEGIES):
        requests=[];slots=[]
        for ni,name in enumerate(NAMES):
            native=art('native/'+name);rows=[]
            for mi,method in enumerate(METHODS):
                candidate=art(strategy+'/'+name+'/'+method)
                actions=['DD']*7+['CC']*28+['DD']
                if method not in ('SOURCE_RA','DYNAMIC_NO_P','DENSE_CONTROL'):actions[12:14]=['PP','PP']
                if method=='DENSE_CONTROL':actions=['DD']*36
                extra=8 if method.startswith('A_CPD_') and method!='A_CPD_OFF' else 0
                readout={'extra_candidate_heads':extra,'teacher_calls':0,'extra_candidate_deep_blocks':0}
                rows.append({'collect':method,'status':'COMPLETE_PARENT_PATH','actions':actions,
                    'instrumented_parent_pipeline_wall_seconds':100+mi+si,
                    'collection_complete':{'complete_pairs':36,'actual_original_plus_candidate_heads':[{}]*(72+extra),
                        'deployment':{'A_readout':readout} if method!='SOURCE_RA' else None}})
                checks={'same_prepared_data':True,'same_actual_solver_configuration':True,'same_first_seven_dense_guided':True}
                slots.append({'sample_name':name,'method':method,'compatible':True,'checks':checks,
                    'incompatible_fields':[],'no_replacement_or_other_seed':True,'Native_artifact':native,'video_artifact':candidate})
                effect={0:0,1:0,2:-.01,3:-.01,4:-.01,5:-.05,6:-.04,7:-.1}[mi]
                s=score(native,candidate,.4+.02*ni+effect-.003*si)
                if method=='A_CPD_W1_ONE_PHASE':
                    s['frame_distances'][0]+=.1;s['mean_LPIPS']=sum(s['frame_distances'])/93
                pairs.append({'strategy':strategy,'sample_name':name,'method':method,
                    'reference':native,'candidate':candidate,'score':s})
            requests.append({'sample_name':name,'paths':rows})
        pairing[strategy]={'complete_pairing_slots':32,'compatible_pairs':32,'incompatible_pairs':0,'pairs':slots}
        runner['batches'][strategy]={'requests':requests}
    for ni,name in enumerate(NAMES):
        native=art('native/'+name)
        for method in LEGACY_METHODS:
            candidate=art('legacy/'+name+'/'+method)
            legacy['pairs'].append({'sample_name':name,'method':method,'reference':native,'candidate':candidate,
                'score':score(native,candidate,.43+.02*ni)})
    started=time.perf_counter();costs=actual_costs(runner);full=summarize(pairs,pairing,costs,legacy)
    assert len(pairing_slots(pairing))==64 and full['scored_pairs']==64 and full['actual_frame_distances']==5952
    assert len(full['per_slot'])==64 and len(full['registered_same_card_contrasts'])==24
    assert len(full['legacy_quality_only_contrasts'])==48
    positive=next(v for v in full['registered_same_card_contrasts']
        if v['candidate']==[STRATEGIES[0],'A_CPD_W1_ONE_PHASE'] and v['baseline']==[STRATEGIES[0],'CPD'])
    assert positive['improved_scenes']==4 and all(r['degraded_frames']==1 for r in positive['per_scene'])
    assert not any(v['same_card_instrumented_cost_comparison'] for v in full['legacy_quality_only_contrasts'])
    badpairing=copy.deepcopy(pairing);slot=badpairing[STRATEGIES[1]]['pairs'][13]
    slot['compatible']=False;slot['checks']['same_prepared_data']=False;slot['incompatible_fields']=['same_prepared_data']
    badpairing[STRATEGIES[1]].update(compatible_pairs=31,incompatible_pairs=1)
    kept=pairs[:45]+pairs[46:];gap=summarize(kept,badpairing,costs,legacy)
    assert gap['scored_pairs']==63 and gap['actual_frame_distances']==5859 and len(gap['per_slot'])==64
    assert sum(not r['scored'] for r in gap['per_slot'])==1
    assert next(r for r in gap['per_slot'] if not r['scored'])['mean_LPIPS'] is None
    refused=[]
    def reject(name,function):
        try:function()
        except (ValueError,KeyError,TypeError):refused.append(name)
        else:raise AssertionError('Invalid complete64 fixture accepted: '+name)
    reject('drop_pair',lambda:summarize(pairs[:-1],pairing,costs,legacy))
    reject('duplicate_pair',lambda:summarize(pairs[:-1]+[pairs[0]],pairing,costs,legacy))
    reject('reorder_pair',lambda:summarize([pairs[1],pairs[0]]+pairs[2:],pairing,costs,legacy))
    reject('drop_strategy',lambda:summarize(pairs,{STRATEGIES[0]:pairing[STRATEGIES[0]]},costs,legacy))
    reject('drop_cost',lambda:summarize(pairs,pairing,costs[:-1],legacy))
    reject('fill_incompatible_slot',lambda:summarize(pairs,badpairing,costs,legacy))
    for label,mutate in [('frame92',lambda v:v['score']['frame_distances'].pop()),
        ('mean_changed',lambda v:v['score'].__setitem__('mean_LPIPS',9.)),
        ('nan_frame',lambda v:v['score']['frame_distances'].__setitem__(0,float('nan'))),
        ('duplicate_PTS',lambda v:v['score']['pts'].__setitem__(1,v['score']['pts'][0])),
        ('candidate_SHA',lambda v:v['candidate'].__setitem__('sha256','0'*64)),
        ('reference_SHA',lambda v:v['reference'].__setitem__('sha256','1'*64))]:
        wrong=copy.deepcopy(pairs);mutate(wrong[0]);reject(label,lambda:summarize(wrong,pairing,costs,legacy))
    for label,key,value in [('negative_time','instrumented_pipeline_wall_seconds',-1.),
        ('nan_time','instrumented_pipeline_wall_seconds',float('nan')),
        ('bad_full_count','complete_branch_calls',72),('teacher','teacher_calls',1)]:
        wrong=copy.deepcopy(costs);wrong[0][key]=value;reject(label,lambda:summarize(pairs,pairing,wrong,legacy))
    wrong=copy.deepcopy(runner);wrong['batches'][STRATEGIES[0]]['requests'][0]['paths'][7]['actions'][9]='CC'
    reject('dense_control_not_full36',lambda:actual_costs(wrong))
    reject('legacy28_missing',lambda:summarize(pairs,pairing,costs,{'pairs':legacy['pairs'][:-1]}))
    assert 'torch' not in sys.modules
    result={'status':'CURRENT_BIRTH_FULL64_STATISTICS_CPU_PASS_NOT_REAL_VIDEOS_OR_LPIPS',
        'CPU_wall_seconds':time.perf_counter()-started,'synthetic_complete_score_slots':64,
        'synthetic_all_frame_values':5952,'explicit_single_incompatible_slot_case':{'kept_slots':64,'scored_pairs':63,'missing_mean':None},
        'same_card_contrasts':24,'legacy_quality_only_contrasts':48,'mutation_refusals':refused,
        'harmful_frames_and_scene_equal_denominators_retained':True,'torch_imported':False,'GPU_submissions':0,
        'actual_new64_video_or_metric_execution':False,'budget_written':False,'source_sha256':reg['source_sha256']}
    target.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='source_sha256'}))


if __name__=='__main__':main()
