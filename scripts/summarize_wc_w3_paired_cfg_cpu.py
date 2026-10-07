#!/usr/bin/env python3
"""Independent standard-library reconstruction from original paired receipts."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

TRACE=['inputs','outputs','deep','banks','solver_outputs']
LABELS=['OFF1','OFF2','BASE_first','SINGLE_second','PAIRED_first','PAIRED_second','SINGLE_first','BASE_second']
COUNTS={'WC_parents':1,'complete_suffixes':8,'new_videos':5,'existing_Native_references':1,'primary_signed_comparisons':2}

def read(path):
    raw=Path(path).read_bytes();return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)

def component_digest(value):
    h=hashlib.sha256()
    for key in sorted(value):h.update(str(key).encode());h.update(repr(value[key]).encode())
    return h.hexdigest()

def check_components(value,inventory,*,fingerprint=None,output=None):
    assert isinstance(value,dict) and set(value)==inventory and bool(value)
    assert all(isinstance(v,str) and len(v)==64 and set(v)<=set('0123456789abcdef') for v in value.values())
    if fingerprint is not None:assert component_digest(value)==fingerprint
    if output is not None:assert value['output']==output

def counts(row,child):
    deep=child['deep'];prefix=row['deep'][:44];report=child['record']['action_report'];events=report['suffix_events']
    assert len(prefix)==44 and len(deep)==28 and [e['call'] for e in events]==list(range(45,73))
    assert all(d in (0,26) for d in prefix+deep)
    assert all(e['cfg_slot']==(e['call']-1)%2 and e['solver_step']==(e['call']-1)//2+1 and (e['actual_action']=='D')==(d==26) for e,d in zip(events,deep))
    assert events[-3]['native_cycle_reset'] and deep[-2:]==[26,26]
    return {'prefix_before_snapshot_CFG':[sum(d==26 for d in prefix[slot::2]) for slot in (0,1)],
        'current45_46_CFG':[int(d==26) for d in deep[:2]],
        'future47_72_CFG':[sum(d==26 for d in deep[2:][slot::2]) for slot in (0,1)],
        'whole_CFG':[sum(d==26 for d in (prefix+deep)[slot::2]) for slot in (0,1)]}

def reconstruct(r,s,sup,old):
    assert sup['exit_code']==0 and sup['source_revision']==r['source_revision']
    assert r['status']=='PAIRED_CFG_GPU_CORE_AND_HISTORY_COMPLETE_AUDIT_SCORE_PENDING'
    assert s['status']=='PAIRED_CFG_COMPLETE_FULL93_AUDIT_THREE_LOSSES_TWO_SIGNED_PAIRS_NOT_CONF'
    assert r['planned_scope']==s['planned_scope']==COUNTS and len(r['cases'])==1 and r['cases'][0]['seed']==2
    assert not s['CUDA_initialized'] and s['GPU_submissions']==0 and len(s['videos'])==6
    assert set(s['losses'])=={'BASE','SINGLE','PAIRED'} and len(s['signed_pairs'])==2 and all(v['full93_decode'] for v in s['videos'])
    assert s['budget']==sup['budget_after']
    assert math.isclose(s['budget']['used_gpu_hours'],sup['budget_before']['used_gpu_hours']+sup['wall_seconds']/3600,abs_tol=1e-12)
    row=r['cases'][0]['WC']['requests'][0];prior=old['cases'][1]['WC']['requests'][0]
    assert old['cases'][1]['seed']==2 and r['model_context']==old['model_context']
    assert row['status']=='PAIRED_CFG_ALL_CONTROLS_COMPLETE_NOT_QUALITY' and row['target_call']==46 and row['slot']==1
    assert row['prepare_calls']==1 and row['sample_return_sha256']==row['final_latent_sha256'] and row['flags_before']==row['flags_after']
    assert all(len(row[k])==(36 if k=='solver_outputs' else 72) for k in TRACE)
    inventory=set(row['final_components'])
    assert {'output','cpu_rng','python_rng','numpy_rng','cuda_rng','explicit_generators','net.cnt','solver._step_index'}<=inventory
    check_components(row['final_components'],inventory,output=row['final_latent_sha256'])
    assert all(row[k]==prior[k] for k in TRACE+['final_latent_sha256','final_components'])
    assert [c['label'] for c in row['children']]==LABELS
    by={c['label']:c for c in row['children']};oldby={c['label']:c for c in prior['children']}
    raw_counts={}
    for label,child in by.items():
        rec=child['record'];report=rec['action_report'];events=report['suffix_events']
        mode='PAIRED' if label.startswith('PAIRED') else 'SINGLE' if label.startswith('SINGLE') else 'OFF'
        requested={'OFF':[],'SINGLE':[46],'PAIRED':[45,46]}[mode]
        assert child['status']=='COMPLETE_SUFFIX_NOT_RV_LABEL' and child['action']==mode and rec['parent_restored']
        assert all(len(child[k])==(14 if k=='solver_outputs' else 28) for k in TRACE)
        assert rec['planned_remaining_updates']==14 and rec['completed_updates']==22
        assert report['plan']=={'mode':mode,'solver_step':23,'maximum_age_solver_steps':32}
        assert report['requested_full_calls']==requested and report['decision_interventions']==len(requested)
        assert report['remaining_policy']=='ORIGINAL_WC_ADAPTIVE' and not report['budget_matched'] and report['current_truth_used_for_decision'] is False and report['RV_label'] is False
        check_components(rec['final_state_components'],inventory,fingerprint=rec['final_state_sha256'],output=child['final_latent_sha256'])
        for at in ('pre45','pre46'):
            check_components(child[at]['components'],inventory,fingerprint=child[at]['fingerprint'])
            assert all(child[at]['own_history'])
        assert child['pre45']==by['BASE_first']['pre45'] and child['inputs'][:2]==by['BASE_first']['inputs'][:2]
        for e in events:
            assert e['current_deep_truth_used'] is False
            if e['call'] in requested:
                assert e['requested']=='D' and e['paid_probe'] and e['actual_action']=='D' and 1<=e['age_solver_steps']<=32
            else:assert e['requested'] is None and (not e['paid_probe'] or e['selected_skip']==e['native_skip'])
        raw_counts[label]=counts(row,child)
    for a,b in [('OFF1','OFF2'),('BASE_first','BASE_second'),('SINGLE_first','SINGLE_second'),('PAIRED_first','PAIRED_second')]:
        assert all(by[a][k]==by[b][k] for k in TRACE+['pre45','pre46','final_latent_sha256'])
        assert by[a]['record']['final_state_components']==by[b]['record']['final_state_components'] and by[a]['record']['action_report']==by[b]['record']['action_report']
    for label in ('OFF1','OFF2','BASE_first','BASE_second'):
        assert all(by[label][k]==row[k][22 if k=='solver_outputs' else 44:] for k in TRACE)
        assert by[label]['record']['final_state_components']==row['final_components']
    assert by['BASE_first']['pre46']==by['SINGLE_first']['pre46']
    decoded={c['label']:c for c in row['decoded_children']};olddecoded={c['label']:c for c in prior['decoded_children']}
    assert list(decoded)==['OFF1','BASE_first','PAIRED_first','SINGLE_first']
    pipe=['decode_input','decode_output','guardrail_input','guardrail_output','save_input']
    assert [e['stage'] for e in row['pipeline']]==pipe
    for item in decoded.values():
        assert item['status']=='ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE' and item['flags_before']==item['flags_after'] and [e['stage'] for e in item['pipeline']]==pipe
    assert decoded['OFF1']['pipeline']==decoded['BASE_first']['pipeline']==row['pipeline']
    assert row['artifact']['sha256']==decoded['OFF1']['artifact']['sha256']==decoded['BASE_first']['artifact']['sha256']
    for name,oldname in [('BASE_first','BASE_first'),('SINGLE_first','REFRESH_first')]:
        assert all(by[name][k]==oldby[oldname][k] for k in TRACE+['pre46','final_latent_sha256'])
        assert by[name]['record']['final_state_components']==oldby[oldname]['record']['final_state_components']
        assert all(decoded[name]['artifact'][k]==olddecoded[oldname]['artifact'][k] for k in ('bytes','sha256'))
    assert [raw_counts[label]['current45_46_CFG'] for label in ('BASE_first','SINGLE_first','PAIRED_first')]==[[0,0],[0,1],[1,1]]
    for label in ('BASE','SINGLE','PAIRED'):
        loss=s['losses'][label];assert len(loss['frame_distances'])==len(loss['pts'])==loss['frames']==93
        assert all(math.isfinite(v) and v>=0 for v in loss['frame_distances'])
        assert loss['mean_LPIPS']==sum(loss['frame_distances'])/93
        assert loss['candidate_sha256']==decoded[label+'_first']['artifact']['sha256']
        assert loss['reference_sha256']==r['existing_Native']['sha256'] and loss['pts']==s['losses']['BASE']['pts']
        assert s['control_costs'][label]==[by[label+'_'+suffix]['record']['control_wall_seconds'] for suffix in ('first','second')]
        assert all(math.isfinite(t) and t>0 for t in s['control_costs'][label])
    comparisons=[]
    for reference,reported in zip(('BASE','SINGLE'),s['signed_pairs']):
        a,b=s['losses'][reference],s['losses']['PAIRED'];delta=[x-y for x,y in zip(a['frame_distances'],b['frame_distances'])]
        before,after=raw_counts[reference+'_first'],raw_counts['PAIRED_first']
        current=sum(after['current45_46_CFG'])-sum(before['current45_46_CFG'])
        future=sum(before['future47_72_CFG'])-sum(after['future47_72_CFG'])
        total=sum(before['whole_CFG'])-sum(after['whole_CFG']);assert total==future-current
        q=a['mean_LPIPS']-b['mean_LPIPS'];t=math.fsum(s['control_costs'][reference])/2-math.fsum(s['control_costs']['PAIRED'])/2
        assert reported['comparison']=='PAIRED_vs_'+reference and reported['frame_signed_changes']==delta
        assert reported['signed_quality']==q and math.isclose(reported['signed_diagnostic_seconds'],t,abs_tol=1e-12)
        assert reported['relative_fidelity_improvement_percent']==100*q/a['mean_LPIPS']
        assert reported['improved_frames']==sum(x>0 for x in delta) and reported['worse_frames']==sum(x<0 for x in delta) and reported['tied_frames']==sum(x==0 for x in delta)
        for label in (reference,'PAIRED'):
            for k in ('whole_CFG','current45_46_CFG','future47_72_CFG'):assert reported['compute_counts'][label][k]==raw_counts[label+'_first'][k]
        assert reported['three_equal31_frame_mean_changes']==[math.fsum(delta[i:i+31])/31 for i in (0,31,62)]
        comparisons.append({'comparison':'PAIRED_vs_'+reference,'reference_LPIPS':a['mean_LPIPS'],'PAIRED_LPIPS':b['mean_LPIPS'],
            'signed_quality':q,'relative_improvement_percent':100*q/a['mean_LPIPS'],'improved_frames':sum(x>0 for x in delta),
            'worse_frames':sum(x<0 for x in delta),'tied_frames':sum(x==0 for x in delta),'frame_signed_changes':delta,
            'three_equal31_frame_mean_changes':reported['three_equal31_frame_mean_changes'],'reference_counts':before,'PAIRED_counts':after,
            'current_full_added':current,'strict_future_full_saved':future,'whole_full_saved':total,'signed_diagnostic_seconds':t})
    return {'status':'PAIRED_CFG_INDEPENDENT_RAW_STATE_REPEATS_HISTORY_QUALITY_COST_RECONSTRUCTION_PASS_NOT_CONF',
        'source_revision':r['source_revision'],'planned_scope':COUNTS,'strict_repeat_groups':4,'complete_state_inventory_components':len(inventory),
        'original_parent_BASE_SINGLE_state_and_encoded_bridges':True,'all_current_inputs_equal':True,'paired_pre46_changed':by['PAIRED_first']['pre46']!=by['BASE_first']['pre46'],
        'all_raw_counts':raw_counts,'comparisons':comparisons,'GPU_wall_seconds':sup['wall_seconds'],'GPUh':sup['wall_seconds']/3600,
        'budget_after':sup['budget_after'],'repeat_diagnostic_ranges':{k:max(v)-min(v) for k,v in s['control_costs'].items()},
        'net_original_WC_fidelity_gain_at_this_exposed_state':comparisons[0]['signed_quality']>0,
        'single_branch_repair_at_this_exposed_state':comparisons[1]['signed_quality']>0,
        'independent_CONF':False,'clean_speed_measurement':False,'physics_or_semantic_acceptance':False,'formal_single_action_RV_labels':False,
        'boundaries':'One exposed seed2/current step, own-state native adaptive suffix; exact repeats and frames are not independent scene samples; full wall includes all controls and diagnostics'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('runner','score','supervisor','original-runner','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    result=reconstruct(*[read(path) for path in (a.runner,a.score,a.supervisor,a.original_runner)])
    raw=gzip.decompress(a.runner.read_bytes()) if str(a.runner).endswith('.gz') else a.runner.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==read(a.score)['runner_sha256']
    result['input_file_sha256']={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (a.runner,a.score,a.supervisor,a.original_runner)}
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','GPUh','net_original_WC_fidelity_gain_at_this_exposed_state','single_branch_repair_at_this_exposed_state')}))

if __name__=='__main__':main()
