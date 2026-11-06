#!/usr/bin/env python3
"""Independent raw reconstruction; never relabel the original strict GPU refusal."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from wc_w3_inactive_gt_forensic import (read, sha, require, verify_terminal,
    verify_conditional_history, reconstruct_quality, TRACE)
from summarize_wc_w3_paired_cfg_cpu import check_components, counts, LABELS


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('runner','score','supervisor','original-post','original-runner','semantics','config','output'):
        p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();require(not a.output.exists(),'Independent reconstruction identity consumed')
    inputs=[a.runner,a.score,a.supervisor,a.original_post,a.original_runner,a.semantics,a.config]
    r,s,sup,post,old,proof,c=[read(path) for path in inputs]
    row=verify_terminal(r,sup,post,s['budget'],c);prior=old['cases'][1]['WC']['requests'][0]
    raw=gzip.decompress(a.runner.read_bytes()) if str(a.runner).endswith('.gz') else a.runner.read_bytes()
    require(hashlib.sha256(raw).hexdigest()==s['runner_sha256'] and sha(a.config)==s['config_sha256'], 'Raw score/config binding differs')
    bridge=verify_conditional_history(row,prior,proof)
    require(row['flags_before']==row['flags_after'] and row['prepare_calls']==1
            and row['sample_return_sha256']==row['final_latent_sha256'],'Parent original scope differs')
    by={child['label']:child for child in row['children']};require(list(by)==LABELS,'Control order differs')
    inventory=set(row['final_components']);check_components(row['final_components'],inventory,output=row['final_latent_sha256'])
    raw_counts={}
    for label,child in by.items():
        record=child['record'];report=record['action_report'];events=report['suffix_events']
        mode='PAIRED' if label.startswith('PAIRED') else 'SINGLE' if label.startswith('SINGLE') else 'OFF'
        requested={'OFF':[],'SINGLE':[46],'PAIRED':[45,46]}[mode]
        require(child['status']=='COMPLETE_SUFFIX_NOT_RV_LABEL' and child['action']==mode and record['parent_restored']
                and record['planned_remaining_updates']==14 and record['completed_updates']==22
                and all(len(child[k])==(14 if k=='solver_outputs' else 28) for k in TRACE),'Full suffix/restoration differs')
        require(report['plan']=={'mode':mode,'solver_step':23,'maximum_age_solver_steps':32}
                and report['requested_full_calls']==requested and report['decision_interventions']==len(requested)
                and report['remaining_policy']=='ORIGINAL_WC_ADAPTIVE' and not report['budget_matched']
                and report['current_truth_used_for_decision'] is False and report['RV_label'] is False,'Action scope differs')
        check_components(record['final_state_components'],inventory,fingerprint=record['final_state_sha256'],output=child['final_latent_sha256'])
        for at in ('pre45','pre46'):
            check_components(child[at]['components'],inventory,fingerprint=child[at]['fingerprint'])
            require(all(child[at]['own_history']),'Own CFG history missing')
        require(child['pre45']==by['BASE_first']['pre45'] and child['inputs'][:2]==by['BASE_first']['inputs'][:2], 'Current states/inputs differ')
        for event in events:
            require(event['current_deep_truth_used'] is False,'Current teacher leakage')
            if event['call'] in requested:
                require(event['requested']=='D' and event['paid_probe'] and event['actual_action']=='D'
                        and 1<=event['age_solver_steps']<=32,'Requested actual full action missing')
            else:
                require(event['requested'] is None and (not event['paid_probe'] or event['selected_skip']==event['native_skip']), 'Native future changed outside action')
        raw_counts[label]=counts(row,child)
    for first,second in [('OFF1','OFF2'),('BASE_first','BASE_second'),('SINGLE_first','SINGLE_second'),('PAIRED_first','PAIRED_second')]:
        require(all(by[first][k]==by[second][k] for k in TRACE+['pre45','pre46','final_latent_sha256'])
                and by[first]['record']['final_state_components']==by[second]['record']['final_state_components']
                and by[first]['record']['action_report']==by[second]['record']['action_report'],'Strict repeat differs')
    for label in ('OFF1','OFF2','BASE_first','BASE_second'):
        require(all(by[label][k]==row[k][22 if k=='solver_outputs' else 44:] for k in TRACE)
                and by[label]['record']['final_state_components']==row['final_components'],'Current parent/OFF/BASE bridge differs')
    require(by['BASE_first']['pre46']==by['SINGLE_first']['pre46'],'Unchanged single prefix differs')
    decoded={v['label']:v for v in row['decoded_children']}
    require(list(decoded)==['OFF1','BASE_first','PAIRED_first','SINGLE_first'],'Encoded scope/order differs')
    pipeline=['decode_input','decode_output','guardrail_input','guardrail_output','save_input']
    require([e['stage'] for e in row['pipeline']]==pipeline,'Original parent pipeline incomplete')
    for item in decoded.values():
        require(item['status']=='ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE' and item['flags_before']==item['flags_after']
                and [e['stage'] for e in item['pipeline']]==pipeline,'Child original pipeline incomplete')
    require(row['pipeline']==decoded['OFF1']['pipeline']==decoded['BASE_first']['pipeline']
            and row['artifact']['sha256']==decoded['OFF1']['artifact']['sha256']==decoded['BASE_first']['artifact']['sha256'], 'Current original encoding bridge differs')
    summary=reconstruct_quality(row,s)
    require(summary['comparisons']==s['signed_pairs'],'Reported paired signed arithmetic differs')
    previous_videos={v['path']:v for v in s['videos']}
    for item in [row['artifact']]+[v['artifact'] for v in decoded.values()]+[r['existing_Native']]:
        require(all(previous_videos[item['path']][key]==item[key] for key in ('bytes','sha256')),'Full93 evidence binding differs')
    result={'status':'H_T39_INDEPENDENT_CONDITIONAL_HISTORY_FULL_STATE_REPEATS_FRAMES_COST_PASS_ORIGINAL_STRICT_FAILURE_RETAINED',
            'original_GPU_source_revision':r['source_revision'],'CPU_source_revision':s['CPU_source_revision'],
            'input_file_sha256':{str(path):sha(path) for path in inputs},'original_GPU_exit_code':sup['exit_code'],
            'original_CPU_exit_code':post['exit_code'],'original_strict_error':r['error'],
            'conditional_history':bridge,'strict_repeat_groups':4,'complete_state_inventory_components':len(inventory),
            'current_internal_inputs_strict':True,'paired_pre46_state_changed':by['PAIRED_first']['pre46']!=by['BASE_first']['pre46'],
            'all_raw_compute_counts':raw_counts,'GPU_wall_seconds':sup['wall_seconds'],'GPUh':sup['wall_seconds']/3600,
            'budget_after':sup['budget_after'],**summary,
            'boundary':'One exposed seed2/current step; zero-mask finite-GT-only historical exception is a separate CPU forensic interpretation; no original strict GPU acceptance, clean speed, independent scene CONF, physics or single-action RV labels'}
    with a.output.open('x') as f:f.write(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','GPUh','net_original_WC_fidelity_gain_at_exposed_state','single_branch_repair_at_exposed_state')}))


if __name__=='__main__':main()
