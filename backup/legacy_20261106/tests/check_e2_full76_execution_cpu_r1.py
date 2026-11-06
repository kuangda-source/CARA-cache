#!/usr/bin/env python3
"""Complete76 saved-CPU metadata,6324 scalar fixtures and dispatch controls."""
import argparse
import copy
import gzip
import hashlib
import json
from pathlib import Path
import random
import sys


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    sys.path.insert(0,str(args.root/'src'))
    from wcomr.e2_full76_reports_r1 import bind_pairs,summarize
    from wcomr.e2_execution_r1 import binding,admit,instrument_save,UUID
    proof=json.loads((args.root/'reports/wc_e2_confirmation_timing_cpu_r3_terminal_20261011_capture.json').read_text())
    original=json.loads(gzip.decompress((args.root/proof['files']['result.json']['local_path']).read_bytes()))
    inputs=json.loads((args.root/'manifests/wc_e2_confirmation_full72_inputs_r1_20261011.json').read_text())
    rows=copy.deepcopy(next(c for c in original['checks'] if c['status']=='PASS' and c['flow'] is False)['receipt']['slots'])
    assert len(rows)==76
    # These CAL bridges and scalar losses are fixtures, not old2B data/LPIPS.
    cal_names=list(dict.fromkeys(r['request_name'] for r in rows if r['section']!='CONFIRMATION'))
    old={'model_context':'FIXTURE','comparison':{'references':[],'batch':{'requests':[]}}};old_raw={'matched_fidelity_pairs':[]}
    for name in cal_names:
        methods=[next(r for r in rows if r['request_name']==name and r['method']==m) for m in ('WC','RA','W1_ONE_PHASE','BETA1_ONE_PHASE')]
        ref={'sample_name':name,'request':methods[0]['request'],'flags_before':methods[0]['flags_before'],
            'outcome':'ACCEPTED','artifact':{'path':'FIXTURE_ONLY','bytes':1,'sha256':'1'*64}}
        old['comparison']['references'].append(ref)
        old['comparison']['batch']['requests'].append({'sample_name':name,'paths':copy.deepcopy(methods)})
        old_raw['matched_fidelity_pairs'].extend({'sample_name':name,'method':r['method'],'reference':ref['artifact']} for r in methods)
    for row in rows:
        if row['section']=='TIMING':
            row['pipeline_wall_seconds']={'WC':10.,'RA':9.,'W1_ONE_PHASE':11.,'BETA1_ONE_PHASE':10.}[row['method']]
            row['online_setup_pipeline_cleanup_seconds']=row['pipeline_wall_seconds']+1.
    pairs=bind_pairs(rows,old,old_raw,'FIXTURE');assert len(pairs)==68 and all(p['status']=='PAIRED' for p in pairs)
    def fill(pairs):
        for p in pairs:
            if p['status']=='PAIRED':
                value={'WC':.6,'RA':.5,'W1_ONE_PHASE':.4,'BETA1_ONE_PHASE':.35}[p['method']]
                if p['section']=='CONFIRMATION' and p['method']=='W1_ONE_PHASE' and p['request_name']=='robot_022_E2_seed17':value=.7
                p['score']={'frames':93,'frame_distances':[value]*93,'pts':[[i,'1/16'] for i in range(93)],
                    'mean_LPIPS':value,'reference_sha256':p['reference']['sha256'],'candidate_sha256':p['candidate']['sha256']}
        return pairs
    pairs=fill(pairs);summary=summarize(rows,pairs,inputs)
    assert summary['scored_pairs']==68 and summary['actual_full_frame_distances']==6324
    assert len(summary['timing_eight_groups'])==8 and len(summary['timing_four_contrasts'])==4
    a,b=summary['co_primary_comparisons'];assert a['complete_prompt_units']==b['complete_prompt_units']==4
    assert a['bootstrap_resamples']==b['bootstrap_resamples']==256
    assert abs(a['prompt_equal_LPIPS_gain']-.0625)<1e-12 and a['worst_prompt_gain']<0
    assert a['all_four_prompt_units'][-1]['seeds'][0]['harmful_frames']==93
    assert all(t['four_rounds'][0]['online_seconds_saved']<0 for t in summary['timing_four_contrasts'])
    damaged=copy.deepcopy(rows)
    ref=next(r for r in damaged if r['section']=='CONFIRMATION' and r['method']=='NATIVE' and r['request_name']=='robot_022_E2_seed17')
    ref['status']='VIDEO_REJECTED'
    missing=fill(bind_pairs(damaged,old,old_raw,'FIXTURE'));part=summarize(damaged,missing,inputs)
    assert len(missing)==68 and part['scored_pairs']==64
    assert all(p['complete_prompt_units']==3 and p['planned_prompt_units']==4 for p in part['co_primary_comparisons'])
    all_missing=copy.deepcopy(rows)
    for row in all_missing:
        if row['method']=='NATIVE':row['status']='VIDEO_REJECTED'
    empty=summarize(all_missing,fill(bind_pairs(all_missing,old,old_raw,'FIXTURE')),inputs)
    assert empty['scored_pairs']==36 and all(p['complete_prompt_units']==0 for p in empty['co_primary_comparisons'])
    bridge_missing=fill(bind_pairs(rows,{**old,'model_context':'OTHER'},old_raw,'FIXTURE'))
    assert summarize(rows,bridge_missing,inputs)['scored_pairs']==32
    scalar_refusals=0
    mutations=[lambda p:p.pop(),lambda p:p.reverse(),lambda p:p[0].update(id='OTHER'),
        lambda p:p[4]['score'].update(frames=92),lambda p:p[4]['score']['frame_distances'].pop(),
        lambda p:p[4]['score']['frame_distances'].__setitem__(0,float('nan')),
        lambda p:p[4]['score'].update(mean_LPIPS=9.),lambda p:p[5]['score'].update(reference_sha256='2'*64)]
    for change in mutations:
        bad=copy.deepcopy(pairs);change(bad)
        try:summarize(rows,bad,inputs)
        except ValueError:scalar_refusals+=1
        else:raise AssertionError('Changed full E2 score scope accepted')
    config=args.root/'e2-config.json'
    if not config.exists():config=args.root/'configs/wc_e2_production_r1_20261011.json'
    c=json.loads(config.read_text())
    c.update(GPU_execution_selected=True,gpu_uuid=UUID,single_job_exception_authority={'ref':'FIXTURE_NOT_APPROVAL','sha256':'1'*64})
    budget={'cap_gpu_hours':77.89524658965853,'used_gpu_hours':39.183807747546176,'gpu_jobs_launched':75,'automatic_single_job_gpu_hours':4}
    gpu={'uuid':UUID,'compute_cap':'8.6','pids':[],'memory_used_mib':24}
    selected={'status':'E2_SELECTED_EXECUTION_CPU_PASS_NOT_GPU','exit_code':0,'GPU_submissions':0,
        'config_binding_sha256':binding(c),'execution_protocol_sha256':'3'*64}
    remaining,limit=admit(c,budget,gpu,selected,'3'*64);assert remaining==limit==38.71143884211235
    autonomy=copy.deepcopy(c);autonomy.update(forecast_complete_GPUh=8.,single_job_exception_authority=None)
    assert admit(autonomy,budget,gpu,{**selected,'config_binding_sha256':binding(autonomy)},'3'*64)[1]==8.
    admission_refusals=0
    mutations=[('c','GPU_execution_selected',False),('c','gpu_uuid','OTHER'),('c','automatic_single_job_GPUh',4),
        ('c','single_job_exception_authority',None),('c','forecast_complete_GPUh',float('nan')),
        ('c','scope_counts',{'complete_actual_GPU_paths':72}),('b','cap_gpu_hours',50.),
        ('b','used_gpu_hours',77.),('b','OTHER_inflight',{}),('g','uuid','OTHER'),('g','compute_cap','9.0'),
        ('g','pids',[1]),('g','memory_used_mib',1025),('s','exit_code',1),('s','GPU_submissions',1),
        ('s','config_binding_sha256','OTHER'),('s','execution_protocol_sha256','OTHER')]
    for obj,key,value in mutations:
        values={'c':copy.deepcopy(c),'b':copy.deepcopy(budget),'g':copy.deepcopy(gpu),'s':copy.deepcopy(selected)};values[obj][key]=value
        try:admit(values['c'],values['b'],values['g'],values['s'],'3'*64)
        except ValueError:admission_refusals+=1
        else:raise AssertionError('Wrong resource/scope admission accepted')
    metadata={'slots':[dict(r,status='NOT_STARTED') for r in rows]};journal=[];saved=[];resets=[]
    before=random.getstate();original_bytes=json.dumps(metadata,sort_keys=True)
    wrapped=instrument_save(metadata,lambda:saved.append(1),journal.append,
        lambda:{'allocated_bytes':1},lambda:resets.append(1),clock=lambda:0.)
    wrapped();assert json.dumps(metadata,sort_keys=True)==original_bytes
    for row in metadata['slots']:
        row['status']='STARTED';snap=json.dumps(metadata,sort_keys=True);wrapped();wrapped();assert json.dumps(metadata,sort_keys=True)==snap
        row['status']='COMPLETE_PATH';snap=json.dumps(metadata,sort_keys=True);wrapped();assert json.dumps(metadata,sort_keys=True)==snap
    assert len(journal)==152 and len(resets)==76 and len(saved)==229 and random.getstate()==before
    assert 'torch' not in sys.modules
    assert not args.output.exists()
    result={'status':'E2_COMPLETE76_EXECUTION_REPORTING_SCALAR_CPU_PASS_NOT_GPU_OR_METRIC',
        'actual_saved_CPU_metadata_source':proof['source_revision'],'full_original_positions':76,'scalar_pair_positions':68,
        'scalar_frame_distances':6324,'primary_prompt_units':4,'primary_seed_units':8,'bootstrap_resamples_per_candidate':256,
        'all_missing_or_bridge_missing_controls_keep68':True,'harmful_prompt_and_all93_harmful_frames_retained':True,
        'admission_refusals':admission_refusals,'scalar_refusals':scalar_refusals,'actual_memory_boundaries':152,
        'memory_resets':76,'original_save_calls_preserved':229,'RNG_and_method_metadata_unchanged':True,
        'scope_8_not_old4_checked':True,'Torch_imported':False,'GPU_submissions':0,'ledger_written':False,
        'CAL_bridges_and_distances_are_synthetic':True,'actual_LPIPS_or_video_or_speed_claim':False,
        'source_sha256':{n:hashlib.sha256((args.root/n).read_bytes()).hexdigest() for n in
            ['src/wcomr/e2_execution_r1.py','src/wcomr/e2_full76_reports_r1.py','tests/check_e2_full76_execution_cpu_r1.py']}}
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
