"""Affected reporters: complete/partial scopes, missing scores and original handles."""
import copy
import importlib.util
import json
from contextlib import contextmanager
from pathlib import Path
import tempfile


def run(stage,c,scope,reused):
    from wcomr.e3_complete64_terminal_r1 import inventory,summarize
    from wcomr.e3_complete64_execution_r1 import exact_authorization,original_gone
    from wcomr.e3_complete64_production_r1 import binding,RUN
    def load(name):
        spec=importlib.util.spec_from_file_location(name,Path(stage)/('scripts/'+name+'.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
    post=load('postprocess_wc_e3_complete64_cpu_r1')
    selector=load('select_and_launch_wc_e3_complete64_r1')
    supervisor={'run_id':RUN,'pid':11,'source_revision':'CPU_FIXTURE_NO_GPU',
        'config_sha256':'CPU_FIXTURE_NO_SELECTED_CONFIG','status':'E3_COMPLETE64_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT',
        'budget_after':{},'blocks':[dict(id=b['id'],planned_paths=len(b['paths']),pid=100+i,exit_code=0) for i,b in enumerate(scope['blocks'])]}
    receipts={}
    for b,process in zip(scope['blocks'],supervisor['blocks']):
        q={'sample_name':b['paths'][0]['sample_name'],'paths':[{'collect':p['method'],'status':'COMPLETE_PARENT_PATH'} for p in b['paths']]}
        receipts[b['id']]={'block':b,'run_id':RUN,'planned_paths':len(b['paths']),
            'source_revision':supervisor['source_revision'],'config_sha256':supervisor['config_sha256'],
            'pid':process['pid'],'batch':{'requests':[q]},'source_receipt':{'CPU_FIXTURE':True},
            'model_context':'CPU_FIXTURE','artifact_root':'/CPU_FIXTURE_NEVER_REAL'}
    slots=inventory(scope,supervisor,receipts,reused)
    assert len(slots)==64 and sum(s['status']=='COMPLETE_REQUIRES_RAW_AUDIT' for s in slots)==64
    variants=[]
    partial=copy.deepcopy(receipts);b=scope['blocks'][0]
    partial[b['id']]['batch']['requests'][0]['paths']=partial[b['id']]['batch']['requests'][0]['paths'][:1]
    partial[b['id']]['status']='CPU_FIXTURE_PROTECTED_STOP'
    items=inventory(scope,supervisor,partial,reused)
    assert len(items)==64 and items[b['paths'][0]['slot']]['status']=='COMPLETE_REQUIRES_RAW_AUDIT'
    assert sum(s['status']=='ATTEMPTED_NO_ROW_RETAINED' for s in items)==len(b['paths'])-1
    variants.append('completed_prefix_scored_even_later_block_failure')
    before=copy.deepcopy(supervisor);before['blocks'][0].pop('pid');missing=dict(receipts);missing.pop(b['id'])
    assert sum(x['status']=='UNSTARTED_RETAINED' for x in inventory(scope,before,missing,reused))==len(b['paths'])
    variants.append('unstarted_slots_retained')
    refused=[]
    for label,change in [('scope_missing',lambda a,b,d,e:a['all64_slots'].pop()),
            ('scope_duplicate',lambda a,b,d,e:a['all64_slots'].__setitem__(1,a['all64_slots'][0])),
            ('reuse_missing',lambda a,b,d,e:e.pop(next(iter(e)))),
            ('unexpected_row',lambda a,b,d,e:d[next(iter(d))]['batch']['requests'][0]['paths'].append({'collect':'FOREIGN'})),
            ('receipt_foreign_source',lambda a,b,d,e:d[next(iter(d))].update(source_revision='FOREIGN')),
            ('changed_reuse',lambda a,b,d,e:e[next(iter(e))]['row']['video_artifact'].update(sha256='BAD'))]:
        a,b,d,e=map(copy.deepcopy,(scope,supervisor,receipts,reused));change(a,b,d,e)
        try:inventory(a,b,d,e)
        except ValueError:refused.append(label)
        else:raise AssertionError('Affected inventory admitted '+label)
    # Exercise actual score_slots loop over64 with one incompatible, one raw fault,
    # one unstarted and one metric exception. The injected metric is explicitly Toy.
    for item in slots:
        item.update(status='RAW_VALID_COMPATIBLE_READY_TO_SCORE',compatible=True,scored=False,score=None,
            candidate={'path':str(item['slot']),'sha256':format(item['slot']+1,'064x')},
            reference={'path':'NATIVE_FIXTURE','sha256':'f'*64})
    slots[1].update(status='RAW_VALID_REFERENCE_INCOMPATIBLE_RETAINED',compatible=False)
    slots[2].update(status='RAW_AUDIT_FAILED_RETAINED',compatible=False)
    slots[3].update(status='UNSTARTED_RETAINED',compatible=None)
    calls=[];saved=[]
    @contextmanager
    def decode(path):yield path
    def metric(left,right,model,reference_sha256,candidate_sha256):
        calls.append(int(right))
        if right=='4':raise ValueError('CPU_FIXTURE_METRIC_FAILURE')
        # Some candidates improve and some harm; dense/special rows are not zero-filled.
        v=(int(right)%8+1)/100
        return {'frames':93,'frame_distances':[v]*93,'pts':[[i,1,16] for i in range(93)],
            'mean_LPIPS':v,'reference_sha256':reference_sha256,'candidate_sha256':candidate_sha256}
    post.score_slots(slots,None,decode,metric,lambda:saved.append(True))
    summary=summarize(slots)
    assert len(calls)==61 and len(saved)==61 and summary['scored_pairs']==60 and summary['gaps_retained']==4
    assert summary['actual_frame_distances']==5580 and len(summary['contrasts'])==24
    assert slots[4]['status']=='SCORE_FAILED_RETAINED' and slots[4]['score'] is None
    assert all(not row['same_card_clean_timing_comparison'] for contrast in summary['contrasts'] for row in contrast['per_scene'])
    # Independent scalar reconstruction of every matched contrast.
    indexed={(s['strategy'],s['sample_name'],s['method']):s for s in slots if s['scored']}
    for contrast in summary['contrasts']:
        for row in contrast['per_scene']:
            a=indexed[(contrast['candidate'][0],row['sample_name'],contrast['candidate'][1])]['score']['mean_LPIPS']
            b=indexed[(contrast['baseline'][0],row['sample_name'],contrast['baseline'][1])]['score']['mean_LPIPS']
            assert abs(row['baseline_minus_candidate_LPIPS']-(b-a))<1e-14
    mutations=[]
    for label,mutate in [('denominator',lambda x:x.pop()),('NaN',lambda x:x[0]['score']['frame_distances'].__setitem__(0,float('nan'))),
            ('missing_frame',lambda x:x[0]['score']['frame_distances'].pop()),
            ('wrong_video',lambda x:x[0]['score'].update(candidate_sha256='0'*64)),
            ('false_mean',lambda x:x[0]['score'].update(mean_LPIPS=100)),
            ('missing_zero_filled',lambda x:x[1].update(scored=True))]:
        v=copy.deepcopy(slots);mutate(v)
        try:summarize(v)
        except ValueError:mutations.append(label)
        else:raise AssertionError('Affected score summary admitted '+label)
    original_gone(supervisor,11,lambda pid:False)
    for label,probe in [('supervisor_live',lambda pid:pid==11),('child_live',lambda pid:pid==100)]:
        try:original_gone(supervisor,11,probe)
        except ValueError:variants.append(label+'_refused')
        else:raise AssertionError('Live original admitted for CPU post')
    approved={'direct_user_authorization':True,'card':c['card'],'run_id':RUN,
        'scope_counts':c['scope_counts'],'config_binding_sha256':binding(c),'forecast_complete_GPUh':c['forecast_complete_GPUh'],
        'CPU_ONLY_FIXTURE_NEVER_AUTHORITATIVE':True}
    exact_authorization(c,approved);authority_refusals=[]
    for key,value in [('direct_user_authorization',False),('card','OTHER'),('run_id','OTHER'),('scope_counts',{}),
            ('config_binding_sha256','BAD'),('forecast_complete_GPUh',8.)]:
        a=copy.deepcopy(approved);a[key]=value
        try:exact_authorization(c,a)
        except ValueError:authority_refusals.append(key)
        else:raise AssertionError('Wrong complete-card authority admitted')
    # Execute the actual launch_handles wrapper with isolated FakeProcess only.
    calls=[]
    class FakeProcess:
        def __init__(self,command,**kwargs):self.pid=500+len(calls);calls.append((command,kwargs))
    import subprocess
    old_popen=subprocess.Popen
    try:
        subprocess.Popen=FakeProcess
        with tempfile.TemporaryDirectory(prefix='E3_SELECTED_HANDLES_CPU_') as folder:
            stage_copy=Path(folder);(stage_copy/'e3-complete64-config.json').write_text('{}')
            value=selector.launch_handles(stage_copy,stage_copy,'CPU_FIXTURE',c,'CPU_PROD','CPU_SELECTED','CPU_PROTOCOL')
            assert len(calls)==2 and value['gpu_supervisor_pid']==500 and value['post_CPU_pid']==501
            assert calls[1][0][-2:]==['--original-supervisor-pid','500']
            assert all(k['env']['CUDA_VISIBLE_DEVICES']=='' for _,k in calls)
            assert not (stage_copy/'outputs').exists()
    finally:subprocess.Popen=old_popen
    return {'status':'AFFECTED_E3_FULL64_POST_SELECTION_TOY_CPU_PASS_NOT_GPU',
        'inventory_slots':64,'score_routing_slots':64,'stub93_scored':60,'metric_calls_including_failure':61,
        'retained_gap_slots':4,'inventory_refusals':refused,'summary_refusals':mutations,
        'original_handle_controls':variants,'authority_refusals':authority_refusals,
        'actual_wrapper_isolated_process_launches':2,'not_actual_metric_or_GPU_results':True}
