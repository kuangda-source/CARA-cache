"""CPU receipt guards for Native24/36, true class origin and complete ten-pair metrics."""
import importlib.util
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch


def module(name):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).resolve().parents[1]/'scripts'/name)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def run():
    audit=module('audit_wc_fair_cal_receipts.py')
    metrics=module('analyze_wc_fair_cal_pairs_cpu.py')
    checks=[];phases=[]
    for point in audit.POINTS:
        n=2*(point['requested_steps']+1);native=point['mode']=='native'
        p={'workpoint':point,'status':'COMPLETE_FULL93_WORKPOINT_NOT_QUALITY_OR_SPEED_ACCEPTANCE',
           'solver_steps':n//2,'CFG_calls':n,'prepare_calls':1,
           'worldcache_enabled':not native,'base_forward_identity':audit.NATIVE if native else audit.WC,
           'trace':[{'call':i+1,'cache_counter_before':0 if native else i%70,'deep_executed':True} for i in range(n)],
           'block_counts':{'denoiser_calls':n,'full_calls':n,'skipped_deep_calls':0},
           'sampling':{'requested_steps':point['requested_steps'],'actual_schedule_steps':n//2,
             'timesteps':list(range(n//2,0,-1)),'use_kerras_sigma':True,'worldcache_horizon':None if native else 70},
           'substage_cuda_isolated':False,'pipeline_wall_seconds':1.0,
           'substage_host_wall':{k:{'calls':1,'seconds':.1} for k in ['prepare','sample','decode','video_guardrail','write']},
           'pipeline_events':[{'stage':k,'value':{'shape':v}} for k,v in zip(audit.base.STAGES,
             [[1],[1],[1,3,93,432,768],[93,432,768,3],[93,432,768,3],[3,93,432,768]])],
           'flags_before':{},'flags_after':{}}
        if point['mode']=='stage':p['refresh_provenance']={}
        assert audit.phase_structure(p,point)==n;phases.append(p);checks.append('accept_'+point['name'])
    mutations=[(1,'solver_steps',36),(1,'CFG_calls',72),(1,'base_forward_identity',audit.WC),
               (0,'worldcache_enabled',True),(0,'sampling',dict(phases[0]['sampling'],worldcache_horizon=70)),
               (0,'trace',phases[0]['trace'][:-1]),(3,'trace',[dict(v,cache_counter_before=0) for v in phases[3]['trace']]),
               (3,'sampling',dict(phases[3]['sampling'],requested_steps=23)),(3,'pipeline_wall_seconds',float('nan')),
               (3,'pipeline_events',phases[3]['pipeline_events'][:-1]),(3,'flags_after',{'changed':True}),
               (0,'block_counts',dict(phases[0]['block_counts'],full_calls=35))]
    for index,key,value in mutations:
        p=deepcopy(phases[index]);p[key]=value
        try:audit.phase_structure(p,audit.POINTS[index])
        except AssertionError:checks.append('refuse_'+str(index)+'_'+key)
        else:raise AssertionError('Invalid fair phase accepted: '+key)
    groups=[{'sample_name':s,'files':[{'variant':p['name']} for p in audit.POINTS]} for s in audit.online.SAMPLES]
    fake={'status':'FOURTEEN_FAIR_CAL_NATIVE_WC_STAGE_VIDEO_AUDIT_PASS_NOT_QUALITY',
          'files':[{}]*14,'measurement_outputs':12,'metric_reference':'native35',
          'planned_native_relative_pairs':10,'measurement_groups':groups}
    calls=[]
    def pair(a,b,s):
        calls.append((s,a['variant'],b['variant']));return {}
    with patch.object(metrics.base,'pair',pair):r=metrics.analyze(fake)
    assert len(r['pairs'])==len(calls)==10 and all(v[1]=='native35' for v in calls)
    assert [v[2] for v in calls]==[p['name'] for p in audit.POINTS[1:]]*2
    checks.append('all_ten_pairs_fixed_native_reference_no_omission')
    for field,value in [('metric_reference','wc006'),('planned_native_relative_pairs',8),('files',[{}]*12)]:
        changed=deepcopy(fake);changed[field]=value
        with patch.object(metrics.base,'pair',pair):
            try:metrics.analyze(changed)
            except AssertionError:checks.append('refuse_metric_'+field)
            else:raise AssertionError('Altered pair matrix accepted')
    return {'status':'FAIR_RECEIPT_NATIVE_GRID_ORIGIN_TEN_PAIR_GUARDS_CPU_PASS','checks':checks,
            'no_actual_video_or_kernel':True}
