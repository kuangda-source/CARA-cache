"""Fixed-reference within-card diagnostics; both historical audit refusals remain."""
import math
from wc_w3_inactive_gt_forensic import compare_inputs, verify_semantics, require, TRACE
from summarize_wc_w3_paired_cfg_cpu import component_digest, counts

STATUS='CURRENT_CARD_FIXED_REFERENCE_FULL93_DIAGNOSTIC_NOT_HISTORICAL_ACCEPTANCE_NOT_CONF'
CURRENT_DICT='4290c3338b03fac3ab3e6a635d743dc1102e107ea9dcbb0a711b3f17bb2b8813'
OLD_DICT='656db0d17bb50e304fc414820b3b4844d4b81eb025f0212d0fc7a68c7d4f9eda'


def component_difference(a,b):
    require(set(a)==set(b), 'Historical component inventory differs')
    differences={k:{'current':a[k],'original':b[k]} for k in a if a[k]!=b[k]}
    require(differences=={'solver._internal_dict':{'current':CURRENT_DICT,'original':OLD_DICT}}, 'Unexpected historical state difference')
    return differences


def fixed_reference_history(row,prior,proof):
    mask=verify_semantics(proof)
    require(row['status']=='PAIRED_CFG_ALL_CONTROLS_COMPLETE_NOT_QUALITY', 'Full original generation required')
    differences={'parent':compare_inputs(row['inputs'],prior['inputs'],mask)}
    require(len(differences['parent'])==72, 'Registered full GT-only parent difference missing')
    for k in TRACE[1:]+['final_latent_sha256','pipeline','flags_before','flags_after','sample_return_sha256']:
        require(row[k]==prior[k], 'Historical functional parent difference: '+k)
    components={'parent_final':component_difference(row['final_components'],prior['final_components'])}
    by={c['label']:c for c in row['children']};old={c['label']:c for c in prior['children']}
    decoded={c['label']:c['artifact'] for c in row['decoded_children']};olddecoded={c['label']:c['artifact'] for c in prior['decoded_children']}
    for name,oname in [('BASE_first','BASE_first'),('SINGLE_first','REFRESH_first')]:
        a,b=by[name],old[oname];differences[name]=compare_inputs(a['inputs'],b['inputs'],mask)
        require(len(differences[name])==28, 'Registered child GT-only coverage missing')
        require(all(a[k]==b[k] for k in TRACE[1:]+['final_latent_sha256']), 'Historical functional child difference')
        components[name+'_final']=component_difference(a['record']['final_state_components'],b['record']['final_state_components'])
        components[name+'_pre46']=component_difference(a['pre46']['components'],b['pre46']['components'])
        for value in (a['pre46'],b['pre46']):require(component_digest(value['components'])==value['fingerprint'], 'Historical pre46 raw fingerprint inconsistent')
        require({k:v for k,v in a['pre46'].items() if k not in {'components','fingerprint'}}=={k:v for k,v in b['pre46'].items() if k not in {'components','fingerprint'}}, 'Other historical pre46 fields differ')
        require(all(decoded[name][k]==olddecoded[oname][k] for k in ('bytes','sha256')), 'Historical child encoding differs')
    require(all(row['artifact'][k]==prior['artifact'][k] for k in ('bytes','sha256')), 'Historical parent encoding differs')
    inputs=row['inputs']+[x for c in row['children'] for x in c['inputs']]
    require(len(inputs)==296 and all(x['kwargs']['condition_video_input_mask_B_C_T_H_W']==mask for x in inputs), 'Current zero-mask input scope differs')
    gt={x['kwargs']['gt_frames'] for x in inputs};require(len(gt)==1, 'GT changes within current card')
    for child in row['children']:
        for value in (child['pre45']['components'],child['pre46']['components'],child['record']['final_state_components']):
            require(value['solver._internal_dict']==CURRENT_DICT, 'Current numerical/config raw identity not shared')
    return {'status':'FUNCTIONAL_REPLAYS_AND_CURRENT_SHARED_CONFIG_OBSERVED_WITH_HISTORICAL_DICT_HASH_UNRESOLVED',
            'historical_input_differences':differences,'historical_component_differences':components,
            'historical_full_state_identity_accepted':False,'H_T39_acceptance':False,
            'historical_dict_difference_exactly_explained':False,'fixed_reference_only':True}


def arithmetic(row,score):
    require(score['status']==STATUS and score['original_strict_GPU_acceptance'] is False, 'Fixed-reference interpretation differs')
    by={c['label']:c for c in row['children']};decoded={c['label']:c['artifact'] for c in row['decoded_children']}
    call_counts={};costs={}
    for label in ('BASE','SINGLE','PAIRED'):
        loss=score['losses'][label];values=loss['frame_distances']
        require(loss['frames']==len(values)==len(loss['pts'])==93 and all(math.isfinite(x) and x>=0 for x in values)
                and loss['mean_LPIPS']==sum(values)/93 and loss['pts']==score['losses']['BASE']['pts']
                and loss['candidate_sha256']==decoded[label+'_first']['sha256'], 'Full93 score arithmetic/identity differs')
        call_counts[label]=counts(row,by[label+'_first'])
        costs[label]=[by[label+'_'+suffix]['record']['control_wall_seconds'] for suffix in ('first','second')]
        require(costs[label]==score['control_costs'][label] and all(math.isfinite(x) and x>0 for x in costs[label]), 'Actual repeated cost differs')
    require([call_counts[x]['current45_46_CFG'] for x in ('BASE','SINGLE','PAIRED')]==[[0,0],[0,1],[1,1]], 'Actual current actions differ')
    result=[]
    for label in ('BASE','SINGLE'):
        a,b=score['losses'][label],score['losses']['PAIRED'];delta=[x-y for x,y in zip(a['frame_distances'],b['frame_distances'])]
        q=a['mean_LPIPS']-b['mean_LPIPS'];before,after=call_counts[label],call_counts['PAIRED']
        current=sum(after['current45_46_CFG'])-sum(before['current45_46_CFG']);future=sum(before['future47_72_CFG'])-sum(after['future47_72_CFG'])
        total=sum(before['whole_CFG'])-sum(after['whole_CFG']);require(total==future-current,'Whole compute accounting differs')
        result.append({'comparison':'PAIRED_vs_'+label,'reference_LPIPS':a['mean_LPIPS'],'PAIRED_LPIPS':b['mean_LPIPS'],
            'signed_quality':q,'relative_improvement_percent':100*q/a['mean_LPIPS'],'improved_frames':sum(x>0 for x in delta),
            'worse_frames':sum(x<0 for x in delta),'tied_frames':sum(x==0 for x in delta),'frame_signed_changes':delta,
            'three_equal31_frame_mean_changes':[math.fsum(delta[i:i+31])/31 for i in (0,31,62)],
            'reference_counts':before,'PAIRED_counts':after,'current_full_added':current,'strict_future_full_saved':future,'whole_full_saved':total,
            'signed_diagnostic_seconds':math.fsum(costs[label])/2-math.fsum(costs['PAIRED'])/2})
    return result
