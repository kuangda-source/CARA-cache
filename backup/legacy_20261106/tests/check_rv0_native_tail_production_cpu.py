"""Complete-card identity, accounting and old-loss reuse refusal controls."""
import argparse
import copy
import json
from pathlib import Path
import sys


def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',type=Path,required=True)
    args=p.parse_args();sys.path.insert(0,str(args.stage/'src'))
    from wcomr.rv0_native_tail_execution import validate_config, reserve_budget, settle_budget
    from wcomr.rv0_native_tail_scores import reused_losses, signed_tail_diagnostics
    config=json.loads((args.stage/'tail-config.json').read_text())
    validate_config(config)
    refused=[]
    changes=[('missing_suffix',lambda c:c['scope'].__setitem__('scope_counts',[1,8,6,2])),
        ('wrong_order',lambda c:c['scope']['order'].reverse()),
        ('tail_scope',lambda c:c['scope'].__setitem__('responsive_calls_only',[68,69,70])),
        ('missing_case',lambda c:c['scope']['scenes'][0]['cases'].pop()),
        ('wrong_seed_scene',lambda c:c.__setitem__('sample_names',['common'])),
        ('prereg_mask',lambda c:c['preregistration']['parent_action_mask'].__setitem__(68,'D')),
        ('core_source',lambda c:c['core_cpu_payload_sha256'].__setitem__('src/wcomr/rv0_native_tail.py','0'*64)),
        ('cost_gt2',lambda c:c['cost'].__setitem__('complete_planning_proxy_seconds',7201)),
        ('invented_approval',lambda c:c.__setitem__('execution_scope_authority',{})),
        ('missing_metric',lambda c:c['payload_sha256'].pop('scripts/analyze_wc_w3_native_tail_response_lpips_cpu.py'))]
    for name,change in changes:
        bad=copy.deepcopy(config);change(bad)
        try:validate_config(bad)
        except ValueError:refused.append(name)
        else:raise AssertionError('Malformed complete native-tail contract accepted:'+name)
    selected=copy.deepcopy(config);selected.update(GPU_execution_selected=True,
        gpu_uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704',production_cpu_receipt_sha256='1'*64,
        production_cpu_payload_sha256={**config['payload_sha256'],'tail-config.json':'2'*64})
    # Synthetic selected proof is confined to this non-launching unit check.
    budget={'cap_gpu_hours':24,'budget_authorization_ref':'manifests/budget_authorization_20261005_wc_24gpuh.json',
        'used_gpu_hours':16.269307783438254,'gpu_jobs_launched':51}
    reserved=reserve_budget(budget,selected,123)
    settled=settle_budget(reserved,budget,selected,3600,123)
    assert settled['used_gpu_hours']==budget['used_gpu_hours']+1 and settled['gpu_jobs_launched']==52
    assert not any(k.endswith('_inflight') for k in settled)
    bad=copy.deepcopy(reserved);bad['used_gpu_hours']=23
    try:settle_budget(bad,budget,selected,3600,123)
    except ValueError:refused.append('changed_reservation')
    else:raise AssertionError('Changed shared ledger accepted')
    prior=json.loads((args.stage/config['prior_score_ref']).read_text())
    old={p['label']:p for p in prior['pairs'] if p['scene']=='human_199'}
    plan={'row':{'artifact':old['BASE1']['candidate'],'decoded_children':[
        {'label':'FIXED46_first','artifact':old['SWAP1_first']['candidate']},
        {'label':'FIXED61_first','artifact':old['SWAP0_first']['candidate']}]}}
    scores=reused_losses(prior,plan,config,prior['metric_protocol'])
    assert len(scores)==3 and [s['score']['mean_LPIPS'] for s in scores]==[
        old[n]['score']['mean_LPIPS'] for n in ['BASE1','SWAP1_first','SWAP0_first']]
    for name in ['prior_metric','candidate_bytes','reference_bytes']:
        a,b,c=copy.deepcopy(prior),copy.deepcopy(plan),copy.deepcopy(config)
        if name=='prior_metric':a['metric_protocol']['resize_crop_subsample']=True
        elif name=='candidate_bytes':b['row']['decoded_children'][0]['artifact']['sha256']='0'*64
        else:c['references']['human_199']['Native35']['sha256']='0'*64
        try:reused_losses(a,b,c,prior['metric_protocol'])
        except ValueError:refused.append(name)
        else:raise AssertionError('Incompatible old loss reused:'+name)
    # Known R2 actual losses supply positive and negative sign controls. These
    # synthetic TAIL records are explicitly a CPU fixture, never new scores.
    pairs=copy.deepcopy(scores)
    for name in ('46','61'):
        pairs.append({'scene':'human_199','label':'TAIL'+name+'_first',
            'reference':config['references']['human_199']['Native35'],
            'candidate':old['BASE1']['candidate'],'score':copy.deepcopy(old['BASE1']['score'])})
    children=[]
    for name in ('46','61'):
        for mode in ('FIXED','TAIL'):
            for index,repeat in enumerate(('first','second')):
                children.append({'label':mode+name+'_'+repeat,'record':{
                    'control_wall_seconds':10+2*index+(4 if mode=='TAIL' else 0),
                    'action_report':{'per_CFG_full_counts':[21 if mode=='TAIL' else 20,18],
                        'tail_action_changes':[69] if mode=='TAIL' else []}}})
    receipt={'requests':[{'children':children}]}
    signed=signed_tail_diagnostics(pairs,receipt,config)
    assert signed[0]['LPIPS_FIXED_minus_TAIL']<0 and signed[1]['LPIPS_FIXED_minus_TAIL']>0
    assert all(d['mean_control_wall_FIXED_minus_TAIL']==-4 for d in signed)
    assert all(d['costs']['TAIL']['whole_CFG_full_counts']==[21,18] for d in signed)
    for name in ('incomplete_signed_pairs','corrupt_frame_mean'):
        damaged=copy.deepcopy(pairs)
        if name=='incomplete_signed_pairs':damaged.pop()
        else:damaged[-1]['score']['mean_LPIPS']+=.1
        try:signed_tail_diagnostics(damaged,receipt,config)
        except ValueError:refused.append(name)
        else:raise AssertionError('Invalid complete signed scores accepted:'+name)
    assert len(refused)==16
    print(json.dumps({'status':'NATIVE_TAIL_AFFECTED_PRODUCTION_CONTRACT_ACCOUNTING_AND_REUSE_CPU_PASS_NOT_GPU',
        'refusals':refused,'old_sampling_fixture_rerun':False,'GPU_submissions':0}))


if __name__=='__main__':main()
