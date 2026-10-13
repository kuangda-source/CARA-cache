"""Check both-seed denominators, harmful outcomes, reference identities and watcher."""
import copy,hashlib,importlib.util,json,math,tempfile
from pathlib import Path
from statistics import mean


def run(stage,project,c):
    from wcomr.source_confirmation_post_r1 import planned_rows,aggregate
    from wcomr.source_conditional_confirmation_production_r1 import CONFIG,RUN
    losses={'NATIVE':[0]*8,'RA':[.2,.3,.4,.5,.25,.35,.45,.55],
        'A_NO_P':[.18,.29,.42,.48,.24,.36,.41,.56],
        'P_OFF':[.19,.28,.44,.45,.22,.34,.43,.54],
        'TABLE_PHASE_H1':[.15,.33,.38,.6,.2,.4,.35,.65]}
    rows=[]
    for planned in planned_rows(c):
        method=planned['method'];index=next((i for i,r in enumerate(c['requests']) if r['name']==planned['scene']),0)
        q=losses[method][index];native=hashlib.sha256((planned['scene']+'NATIVE').encode()).hexdigest()
        rows.append({**planned,'status':'COMPLETE','actual_request_seed':planned['seed'],
            'request_context_seed_tag':'fixed-seed'+str(planned['seed'])+'-request',
            'solver_steps':36,'guided_pairs':36,'in_timing_hashes':0,'in_timing_guided_copies':0,'research_checkpoints':0,
            'core_seconds':300 if method=='NATIVE' else 150+index,
            'actions':None if method=='NATIVE' else ['DD']*36,
            'video_artifact':{'sha256':native if method=='NATIVE' else hashlib.sha256((planned['scene']+method).encode()).hexdigest()},
            'LPIPS':{'frame_distances':[q]*93,'mean_LPIPS':mean([q]*93),'reference_sha256':native}})
    result=aggregate(c,rows);pair=result['comparisons'][0]
    assert result['scored_formal_videos']==40 and result['independent_prompt_count']==4
    assert pair['complete_two_seed_prompts']==4 and pair['scored_request_seed_pairs']==8
    assert pair['improved_prompts']==2
    target=100*(1-mean(losses['TABLE_PHASE_H1'])/mean(losses['RA']))
    assert math.isclose(pair['prompt_equal_LPIPS_reduction_percent'],target,abs_tol=1e-12)
    assert not math.isclose(target,mean(v['LPIPS_reduction_percent'] for v in pair['per_request_seed']))
    assert all(v['better_frames']+v['worse_frames']+v['equal_frames']==93 for v in pair['per_request_seed'])
    missing=copy.deepcopy(rows);next(r for r in missing if r['section']=='TIMED' and r['method']=='TABLE_PHASE_H1').pop('LPIPS')
    partial=aggregate(c,missing)['comparisons'][0]
    assert partial['complete_two_seed_prompts']==3 and partial['scored_request_seed_pairs']==7
    assert 'prompt_equal_LPIPS_reduction_percent' not in partial
    refused=[]
    for fault in ('missing_path','wrong_seed','wrong_context','missing_frame','wrong_reference','modified_mean','live_status'):
        bad=copy.deepcopy(rows);r=next(r for r in bad if r['section']=='TIMED' and r['method']=='TABLE_PHASE_H1')
        if fault=='missing_path':bad.pop()
        elif fault=='wrong_seed':r['actual_request_seed']=0
        elif fault=='wrong_context':r['request_context_seed_tag']='fixed-seed0-request'
        elif fault=='missing_frame':r['LPIPS']['frame_distances'].pop()
        elif fault=='wrong_reference':r['LPIPS']['reference_sha256']='wrong-other-seed'
        elif fault=='modified_mean':r['LPIPS']['mean_LPIPS']+=.01
        else:r['status']='RUNNING'
        try:aggregate(c,bad)
        except (ValueError,AssertionError,KeyError):refused.append(fault)
        else:raise AssertionError('Incomplete/incorrect science metadata accepted: '+fault)
    spec=importlib.util.spec_from_file_location('actual_confirmation_watch',stage/'scripts/watch_wc_source_conditional_confirmation_cpu_r1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    output,command=module.paths(stage,project)
    assert output==project/'outputs'/RUN
    assert command[1:]==[str(stage/'scripts/postprocess_wc_source_conditional_confirmation_cpu_r1.py'),'--project',str(project),'--stage',str(stage)]
    watched=[]
    with tempfile.TemporaryDirectory() as tmp:
        fake=Path(tmp);(fake/CONFIG).parent.mkdir(parents=True)
        for key,value in [('run_id','wrong-output'),('post_all_frame_count',8),('candidate_frozen',False),('methods',c['methods'][:-1])]:
            bad=copy.deepcopy(c);bad[key]=value;(fake/CONFIG).write_text(json.dumps(bad))
            try:module.paths(fake,project)
            except ValueError:watched.append(key)
            else:raise AssertionError('Changed actual watcher contract accepted')
    original=(stage/'scripts/run_wc_source_conditional_confirmation_template_r1.py').read_text()
    final=(stage/'scripts/run_wc_source_conditional_confirmation_r1.py').read_text()
    marker="    assert os.environ['CUDA_VISIBLE_DEVICES']"
    assert original[original.index(marker):]==final[final.index(marker):]
    return {'status':'CONFIRMATION_BOTH_SEEDS_SIGNED_REFERENCE_AND_ACTUAL_WATCHER_CPU_PASS',
        'unchanged_full50_GPU_execution_branch_vs_accepted_template':True,
        'all50_rows_40_formal_four_prompts_two_seeds_verified':True,
        'incomplete_seed_group_has_no_complete_mean':True,'ratio_of_means_not_mean_of_ratios':True,
        'harmful_prompts_and_frame_counts_preserved':True,'refused':refused,'watch_refusals':watched,
        'synthetic_fixture_not_real_confirmation_result':True,'GPU_submissions':0,'ledger_written':False}
