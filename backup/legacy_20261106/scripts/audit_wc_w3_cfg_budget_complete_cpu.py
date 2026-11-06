#!/usr/bin/env python3
"""Independently reconstruct the actual fixed-CFG-quota masks, complete states, all93 scores and fees.

Read-only local audit. Execute only after the exact bound original GPU and
full93 CPU scoring are terminal. Never imports or calls the live evaluator.
"""
import gzip
import hashlib
import json
import math
from pathlib import Path
from audit_wc_w3_cfg_budget_core_cpu import check_components, configuration, digest

TRACE=('inputs','outputs','deep','banks','solver_outputs')
CELLS=('BASE','CFG0','CFG1','PAIRED')
LABELS=['OFF1','OFF2','BASE_first','CFG1_second','CFG0_first','PAIRED_second','PAIRED_first','CFG0_second','CFG1_first','BASE_second']
ENCODED=['OFF1','BASE_first','CFG0_first','PAIRED_first','CFG1_first']
PIPELINE=['decode_input','decode_output','guardrail_input','guardrail_output','save_input']
PREFIX='reports/wc_w3_cfg_budget_complete_r1_20261009_'


def close(a,b):
    assert math.isclose(a,b,rel_tol=0,abs_tol=1e-12), (a,b)


def main():
    capture=json.loads(Path('reports/wc_w3_cfg_budget_complete_r1_terminal_capture_20261009.json').read_text())
    originals={}
    for key,item in capture['files'].items():
        compressed=Path(item['local_path']).read_bytes();raw=gzip.decompress(compressed)
        assert hashlib.sha256(compressed).hexdigest()==item['compressed_sha256']
        assert hashlib.sha256(raw).hexdigest()==item['sha256'] and len(raw)==item['bytes']
        if key in ('runner','supervisor','CPU_receipt','CPU_score','budget'):originals[key]=json.loads(raw)
    r,sup,receipt,score,budget=[originals[k] for k in ('runner','supervisor','CPU_receipt','CPU_score','budget')]
    c=json.loads(Path('configs/wc_w3_cfg_budget_selected_r1_20261009.json').read_text())
    assert r['source_revision']==sup['source_revision']==receipt['source_revision']==capture['source_revision']
    assert r['config']==c and r['scientific_run_id']==c['preregistration']['run_id']==c['execution_run_id']
    assert sup['exit_code']==receipt['exit_code']==0
    assert r['status']=='CFG_BUDGET_GPU_CORE_COMPLETE_FIXED_REFERENCE_AUDIT_SCORE_PENDING'
    assert score['status']=='CFG_BUDGET_COMPLETE_FULL93_AUDIT_FOUR_LOSSES_FOUR_PAIRS_ONE_INTERACTION_NOT_CONF'
    assert receipt['score_sha256']==capture['files']['CPU_score']['sha256']
    assert score['runner_sha256']==capture['files']['runner']['sha256']
    assert score['config_sha256']==sup['config_sha256']==hashlib.sha256(Path('configs/wc_w3_cfg_budget_selected_r1_20261009.json').read_bytes()).hexdigest()
    assert score['planned_scope']==r['planned_scope']==c['preregistration']['scope_counts']
    assert capture['payload_after_sha256']==receipt['payload_after_sha256']==c['payload_sha256']
    assert score['CUDA_initialized'] is False and score['GPU_submissions']==0
    assert score['physics_or_semantic_acceptance'] is False
    assert not score['independent_CONF'] and not score['clean_speed_measurement'] and not score['formal_single_action_RV_labels']
    assert len(r['cases'])==1 and len(r['cases'][0]['WC']['requests'])==1
    assert r['existing_Native']==c['preregistration']['existing_Native']
    row=r['cases'][0]['WC']['requests'][0];inventory=set(row['final_components'])
    assert {'output','python_rng','numpy_rng','cpu_rng','cuda_rng','explicit_generators','solver._internal_dict','solver._step_index','net.cnt'}<=inventory
    assert any(n.startswith('mode.') for n in inventory) and any(n.startswith('buffer.') for n in inventory)
    check_components(row['final_components'],inventory,output=row['final_latent_sha256'])
    conf=configuration(row['final_solver_configuration'],row['final_components'])
    assert all(len(row[k])==(36 if k=='solver_outputs' else 72) for k in TRACE)
    parent=c['preregistration']['parent_action_mask'];assert len(parent)==72
    assert ['D' if n else 'C' for n in row['deep']]==parent
    assert all(n in (0,26) for n in row['deep'])
    assert [sum(n=='D' for n in parent[slot::2]) for slot in (0,1)]==[18,17]
    assert row['prepare_calls']==1 and row['target_call']==46 and row['slot']==1 and row['flags_before']==row['flags_after']
    assert row['sample_return_sha256']==row['final_latent_sha256']
    assert [e['stage'] for e in row['pipeline']]==PIPELINE
    by={x['label']:x for x in row['children']};assert list(by)==LABELS and len(row['children'])==10
    tail={k:row[k][22 if k=='solver_outputs' else 44:] for k in TRACE}
    for label, child in by.items():
        rec = child['record']; report = rec['action_report']; events = report['suffix_events']
        mode='OFF' if label.startswith('OFF') else label.split('_')[0]
        swaps={'OFF':[],'BASE':[],'CFG0':[[45,47]],'CFG1':[[46,48]],'PAIRED':[[45,47],[46,48]]}[mode]
        expected=list(parent)
        for current,donor in swaps:expected[current-1]='D';expected[donor-1]='C'
        assert child['status']=='COMPLETE_SUFFIX_NOT_RV_LABEL' and child['action']==mode and rec['parent_restored']
        assert rec['completed_updates']==22 and rec['planned_remaining_updates']==14
        assert all(len(child[k])==(14 if k=='solver_outputs' else 28) for k in TRACE)
        actual=list(parent[:44])+['D' if n else 'C' for n in child['deep']]
        assert actual==expected==report['actual_actions'] and len(actual)==72
        assert [sum(n=='D' for n in actual[slot::2]) for slot in (0,1)]==report['per_CFG_full_counts']==[18,17]
        msha=lambda values:hashlib.sha256(''.join(values).encode()).hexdigest()
        assert report['parent_mask_sha256']==msha(parent) and report['actual_mask_sha256']==msha(expected)
        assert report['quota_matched_per_CFG'] and report['budget_matched']
        assert report['plan']==(None if mode=='OFF' else {'mode':mode,'parent_mask':parent,'prefix_calls':44,'maximum_age_solver_steps':32})
        assert report['planned_action_changes']==2*len(swaps)
        assert report['remaining_policy']==('ORIGINAL_WC_ADAPTIVE_REFERENCE' if mode=='OFF' else 'OFFLINE_FIXED_PARENT_MASK_WITH_REGISTERED_CFG_POSITION_EXCHANGES')
        assert report['current_truth_used_for_decision'] is False and report['RV_label'] is False
        assert report['paid_mask_decisions']==(0 if mode=='OFF' else sum(e['paid_probe'] for e in events))
        assert report['native_tail_proposal_preservation_required'] is False
        assert report['tail_native_proposal_disagreements']==[e['call'] for e in events if e.get('tail_native_proposal_disagreement')]
        check_components(rec['final_state_components'], inventory, rec['final_state_sha256'], child['final_latent_sha256'])
        assert configuration(child['final_solver_configuration'],rec['final_state_components']) == conf
        for at in ('pre45','pre46'):
            point = child[at]
            check_components(point['components'], inventory, point['fingerprint'])
            assert configuration(point['solver_configuration'],point['components']) == conf and all(point['own_history'])
        assert child['pre45'] == by['BASE_first']['pre45'] and child['inputs'][:2] == by['BASE_first']['inputs'][:2]
        assert [e['call'] for e in events] == list(range(45,73)) and events[-3]['native_cycle_reset']
        assert child['deep'][-2:] == [26,26]
        for event, deep in zip(events,child['deep']):
            assert deep in (0,26) and event['actual_action'] == ('D' if deep else 'C')
            assert event['cfg_slot'] == (event['call']-1)%2 and event['solver_step'] == (event['call']-1)//2+1
            assert event['current_deep_truth_used'] is False
            if mode=='OFF':assert event['requested'] is None and (not event['paid_probe'] or event['selected_skip']==event['native_skip'])
            elif event['paid_probe']:
                assert event['requested']==event['planned_action']==expected[event['call']-1]
                assert event['selected_skip']==(expected[event['call']-1]=='C')
                if expected[event['call']-1]=='C' or event['call'] in sum(swaps,[]):assert 1<=event['age_solver_steps']<=32
            else:assert event['call'] in (71,72) and expected[event['call']-1]=='D'
    repeats=[('OFF1','OFF2')]+[(n+'_first',n+'_second') for n in CELLS]
    for a,b in repeats:
        assert all(by[a][k]==by[b][k] for k in TRACE+('final_latent_sha256','pre45','pre46','final_solver_configuration'))
        assert by[a]['record']['final_state_components']==by[b]['record']['final_state_components']
        assert by[a]['record']['action_report']==by[b]['record']['action_report']
    for label in ('OFF1','OFF2','BASE_first','BASE_second'):
        assert all(by[label][k]==tail[k] for k in TRACE) and by[label]['final_latent_sha256']==row['final_latent_sha256']
        assert by[label]['record']['final_state_components']==row['final_components']
    for a,b in [('BASE_first','CFG1_first'),('CFG0_first','PAIRED_first')]:
        assert by[a]['pre46']==by[b]['pre46'] and all(by[a][k][:1]==by[b][k][:1] for k in ('outputs','deep','banks'))
    assert [by[n+'_first']['deep'][:4] for n in CELLS]==[[0,0,26,26],[26,0,0,26],[0,26,26,0],[26,26,0,0]]
    decoded={x['label']:x for x in row['decoded_children']};assert list(decoded)==ENCODED
    for child in decoded.values():
        assert child['status']=='ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE' and child['flags_before']==child['flags_after']
        assert [e['stage'] for e in child['pipeline']]==PIPELINE
    assert decoded['OFF1']['pipeline']==decoded['BASE_first']['pipeline']==row['pipeline']
    assert decoded['OFF1']['artifact']['sha256']==decoded['BASE_first']['artifact']['sha256']==row['artifact']['sha256']
    artifacts=[row['artifact']]+[x['artifact'] for x in decoded.values()]+[r['existing_Native']]
    assert len(artifacts)==len(score['videos'])==7 and len({v['path'] for v in artifacts})==7
    assert [{k:v[k] for k in ('path','bytes','sha256')} for v in score['videos']]==artifacts
    for video in score['videos']:
        probe=video['probe'];assert video['full93_decode'] and probe['frames']==93 and probe['HWC']==[432,768,3] and probe['fps']==16
        assert probe['pts']==[1024*i for i in range(93)] and probe['time_base']=='1/16384' and not probe['resize_crop_subsample']
    losses=score['losses'];assert set(losses)==set(CELLS)
    for n in CELLS:
        loss=losses[n];assert loss['frames']==len(loss['frame_distances'])==len(loss['pts'])==93
        assert loss['reference_sha256']==r['existing_Native']['sha256'] and loss['candidate_sha256']==decoded[n+'_first']['artifact']['sha256']
        assert loss['pts']==[[1024*i,'1/16384'] for i in range(93)]
        assert all(math.isfinite(x) and x>=0 for x in loss['frame_distances'])
        close(loss['mean_LPIPS'],math.fsum(loss['frame_distances'])/93)
    counts={};costs={};prefix=row['deep'][:44]
    for n in CELLS:
        deep=by[n+'_first']['deep']
        counts[n]={'prefix_CFG':[sum(d>0 for d in prefix[slot::2]) for slot in (0,1)],'current_CFG':[int(d>0) for d in deep[:2]],'future_CFG':[sum(d>0 for d in deep[2:][slot::2]) for slot in (0,1)],'whole_CFG':[sum(d>0 for d in (prefix+deep)[slot::2]) for slot in (0,1)]}
        costs[n]=[by[n+'_'+suffix]['record']['control_wall_seconds'] for suffix in ('first','second')]
        assert all(math.isfinite(x) and x>0 for x in costs[n])
    assert all(v['whole_CFG']==[18,17] for v in counts.values())
    assert score['same_per_CFG_computation_quota']==[18,17] and score['all_cells_whole_full_calls']==35
    assert all(v['current_CFG']=={'BASE':[0,0],'CFG0':[1,0],'CFG1':[0,1],'PAIRED':[1,1]}[n] for n,v in counts.items())
    fs=score['factorial_summary'];assert fs['actual_counts']==counts and fs['control_costs']==costs and fs['contrasts']==score['signed_pairs']
    pairs=[('BASE','CFG0'),('BASE','CFG1'),('CFG0','PAIRED'),('BASE','PAIRED')];assert len(fs['contrasts'])==4
    reconstructed=[]
    for contrast,(ref,candidate) in zip(fs['contrasts'],pairs):
        frame=[a-b for a,b in zip(losses[ref]['frame_distances'],losses[candidate]['frame_distances'])];signed=math.fsum(frame)/93
        assert contrast['comparison']==candidate+'_vs_'+ref and contrast['frame_signed_changes']==frame
        close(contrast['signed_quality'],signed);close(contrast['relative_fidelity_improvement_percent'],100*signed/losses[ref]['mean_LPIPS'])
        assert contrast['improved_frames']==sum(x>0 for x in frame) and contrast['worse_frames']==sum(x<0 for x in frame) and contrast['tied_frames']==sum(x==0 for x in frame)
        assert contrast['three_equal31_frame_mean_changes']==[math.fsum(frame[i:i+31])/31 for i in (0,31,62)]
        assert contrast['current_full_added']==sum(counts[candidate]['current_CFG'])-sum(counts[ref]['current_CFG'])
        assert contrast['strict_future_full_saved']==sum(counts[ref]['future_CFG'])-sum(counts[candidate]['future_CFG'])
        assert contrast['whole_full_saved']==sum(counts[ref]['whole_CFG'])-sum(counts[candidate]['whole_CFG'])
        close(contrast['signed_diagnostic_seconds'],math.fsum(costs[ref])/2-math.fsum(costs[candidate])/2)
        reconstructed.append({k:v for k,v in contrast.items() if k!='frame_signed_changes'})
    interaction=[a+b-c-d for a,b,c,d in zip(losses['CFG0']['frame_distances'],losses['CFG1']['frame_distances'],losses['BASE']['frame_distances'],losses['PAIRED']['frame_distances'])]
    assert fs['interaction']['frame_signed_interactions']==interaction;close(fs['interaction']['signed_quality'],math.fsum(interaction)/93)
    assert budget==sup['budget_after']==receipt['budget_at_end']==score['budget'] and budget['cap_gpu_hours']==50
    assert budget['gpu_jobs_launched']==sup['budget_before']['gpu_jobs_launched']+1 and not any('inflight' in k for k in budget)
    assert budget['budget_authorization_history']==sup['budget_before']['budget_authorization_history']
    close(budget['used_gpu_hours'],sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600)
    authority=c['single_job_exception_authority'];proof=json.loads(Path(authority['ref']).read_text())
    assert hashlib.sha256(Path(authority['ref']).read_bytes()).hexdigest()==authority['sha256']==capture['single_job_authority_sha256']
    assert proof['direct_user_authorization'] and proof['scope_counts']==c['preregistration']['scope_counts'] and proof['preregistration_sha256']==c['preregistration_sha256']
    assert proof['approved_forecast_GPUh']==c['preregistration']['forecast']['forecast_complete_GPUh']==2.082740046511187
    assert capture['lock_released'] and sup['release']['pids']==[] and set(capture['original_PIDs_absent'])=={sup['pid'],sup['child_pid'],receipt['pid'],receipt['score_pid']}
    out={'status':'CFG_BUDGET_COMPLETE_NATIVE_STATE_WORK_FULL93_AND_FEES_INDEPENDENT_RECONSTRUCTION_PASS_NOT_CONF','source_revision':capture['source_revision'],'original_runner_sha256':capture['files']['runner']['sha256'],'original_score_sha256':capture['files']['CPU_score']['sha256'],'full_component_count':len(inventory),'raw_solver_dictionary_bound':True,'strict_repeat_groups':len(repeats),'full_new_videos':6,'existing_Native_videos':1,'decoded_files':7,'full_suffixes':10,'actual_current_deep_work':{n:by[n+'_first']['deep'][:2] for n in CELLS},'actual_counts':counts,'fixed_CFG_full_counts':[18,17],'all_cells_whole_full_calls':35,'all_masks_independently_reconstructed':True,'cell_LPIPS':{n:losses[n]['mean_LPIPS'] for n in CELLS},'comparisons':reconstructed,'interaction_signed_quality':math.fsum(interaction)/93,'all93_signed_frames_retained':True,'GPU_wall_seconds':sup['wall_seconds'],'actual_GPUh':sup['wall_seconds']/3600,'used_GPUh':budget['used_gpu_hours'],'remaining_GPUh':50-budget['used_gpu_hours'],'old_fees_and_history_retained':True,'single_job_authority_sha256':authority['sha256'],'original_PIDs_absent':capture['original_PIDs_absent'],'CUDA_initialized':False,'GPU_submissions_by_this_audit':0,'independent_CONF':False,'clean_speed_measurement':False,'formal_single_action_RV_labels':False}
    p=Path('reports/wc_w3_cfg_budget_complete_r1_independent_reconstruction_20261009.json')
    with p.open('x') as f:f.write(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':out['status'],'cells':out['cell_LPIPS'],'actual_GPUh':out['actual_GPUh'],'used_GPUh':out['used_GPUh'],'full_component_count':len(inventory)}))

if __name__=='__main__':main()
