"""Finite complete-matrix dominance and receipt/SHA/Native23-grid controls."""
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from copy import deepcopy


def run():
    spec=importlib.util.spec_from_file_location('fair_summary',Path(__file__).resolve().parents[1]/'scripts/summarize_wc_fair_cal_results_cpu.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    def point(wall,mse,ssim,temp):
        return dict(pipeline_wall_seconds=wall,RGB_MSE_0to1=mse,mean_luma_SSIM_win7=ssim,temporal_difference_MSE_0to1=temp)
    a=point(200,.002,.95,.001);b=point(220,.004,.9,.003)
    assert m.proxy_dominates(a,b) and not m.proxy_dominates(b,a)
    assert not m.proxy_dominates(a,a)
    assert not m.proxy_dominates(point(190,.005,.96,.0005),b)
    assert not m.proxy_dominates(point(230,.001,.99,.0001),b)
    try:m.proxy_dominates(point(float('nan'),.002,.95,.001),b)
    except ValueError:pass
    else:raise AssertionError('Nonfinite proxy admitted')
    checks=['strict_all_four_proxy_dominance_ties_and_tradeoffs','refuse_nonfinite_proxy']
    with TemporaryDirectory() as directory:
        paths={n:Path(directory)/(n+('.gz' if n=='runner' else '.json')) for n in ['runner','audit','metrics','terminal','cost']}
        groups=[];requests=[];pairs=[];expected={}
        for sample in ('fixture_CAL_A','fixture_CAL_B'):
            files=[];phases=[]
            for i,n in enumerate(m.VARIANTS):
                mode='native' if i<2 else ('stage' if i==5 else 'worldcache')
                steps=24 if i==1 else 36;calls=steps*2
                workpoint={'name':n,'mode':mode,'requested_steps':steps-1,'threshold':None if i<2 else [.04,.06,.08,.06][i-2]}
                digest=hashlib.sha256((sample+n).encode()).hexdigest()
                seconds=[350,240,230,220,190,200][i]
                f={'variant':n,'workpoint':workpoint,'sha256':digest,'deep_CFG_calls':calls,
                   'solver_steps':steps,'CFG_calls':calls,'pipeline_wall_seconds':seconds}
                p={'workpoint':workpoint,'solver_steps':steps,'CFG_calls':calls,
                   'trace':[{'call':j+1,'deep_executed':True} for j in range(calls)]}
                if i==5:
                    f['provenance']={'cache_calls_reading_approximate':[],'sparse_CFG_calls':[],
                        'sparse_attention_operators':0,'window_eligible_per_CFG':[0,0]}
                    p['refresh_provenance']={'events':[]}
                if i:
                    vals=[(.003,.93,.002),(.003,.94,.002),(.004,.90,.003),(.006,.86,.004),(.002,.95,.001)][i-1]
                    pairs.append({'sample_name':sample,'variant':n,'reference':'native35',
                        'baseline_sha256':files[0]['sha256'],'candidate_sha256':digest,
                        'whole_video':{'frames':93,'transitions':92,'RGB_MSE_0to1':vals[0],
                            'mean_luma_SSIM_win7':vals[1],'temporal_difference_MSE_0to1':vals[2]}})
                files.append(f);phases.append(p)
            expected[sample]=files[3]['sha256']
            groups.append({'sample_name':sample,'files':files});requests.append({'sample_name':sample,'phases':phases})
        before=9.691073425147268;wall=1800
        runner={'status':'FOURTEEN_COMPLETE_FAIR_OUTPUTS_REQUIRE_AUDIT_NOT_FRONTIER_ACCEPTANCE',
                'pid':303,'planned_output_files':14,'run_card':'CPU_FIXTURE_NO_REAL_GPU',
                'scope':{'run_id':'CPU_FIXTURE','expected_WC_sha256':expected},'measurements':{'requests':requests}}
        audit={'status':'FOURTEEN_FAIR_CAL_NATIVE_WC_STAGE_VIDEO_AUDIT_PASS_NOT_QUALITY',
               'files':[{}]*14,'measurement_groups':groups,'frozen_gpu_source':'fixture',
               'original_GPU_budget_unchanged_during_CPU':True}
        metrics={'status':'TWO_EXPOSED_CAL_TEN_NATIVE_RELATIVE_FAIR_DIAGNOSTICS_NOT_ACCEPTANCE',
                 'pairs':pairs,'CPU_only':True,'new_GPU_submission':False,'original_GPU_budget_unchanged_during_CPU':True}
        budget={'cap_gpu_hours':12,'gpu_jobs_launched':44,'used_gpu_hours':before+wall/3600}
        terminal={'status':'FAIR_CAL_SOURCE_ASSETS_FULL_COST_RELEASE_AUDIT_PASS_REQUIRES_FOURTEEN_OUTPUT_AUDIT',
                  'source_revision':'fixture','original_pids_absent':[101,202,303],'global_lock_free':True,
                  'compute_after':'fixture_GPU_B, 404','budget':budget,'gpu_wall_seconds':wall,
                  'supervisor':{'pid':101,'child_pid':202,'exit_code':0,'budget_before':{'used_gpu_hours':before},
                                'budget_after':budget,'reserved_seconds':6300,
                                'release':{'uuid':'fixture_GPU_A','pids':[]}}}
        cost={'cards':[{}, {},{'planned_outputs':6,'complete_planning_seconds':2808.5259551551935,'proposed_cap_seconds':3000}]}
        def write(r=runner,a=audit,t=terminal,v=metrics):
            packed=json.dumps(r).encode();sha=hashlib.sha256(packed).hexdigest()
            paths['runner'].write_bytes(gzip.compress(packed,mtime=0))
            ad=dict(a,receipt_sha256=sha);paths['audit'].write_text(json.dumps(ad))
            paths['metrics'].write_text(json.dumps(dict(v,input_audit_sha256=m.sha(paths['audit']))))
            paths['terminal'].write_text(json.dumps(dict(t,receipt_sha256=sha)))
            paths['cost'].write_text(json.dumps(cost))
        write();result=m.summarize(*(paths[n] for n in paths))
        assert len(result['rows'])==12 and result['native_relative_pairs']==10
        assert all(r['variant']=='native35' for r in result['rows'] if r['reference_self_error_by_definition'])
        assert all(c['stage_proxy_dominated_by']==[] for c in result['descriptive_stage_comparisons'])
        assert all('wc006' not in c['proxy_undominated_variants'] for c in result['descriptive_stage_comparisons'])
        assert result['followup_budget']['CONF_cap_with_15s_admission_fits']
        assert not any(result[k] for k in ['quality_acceptance','quality_time_frontier_claim','independent_confirmation','replicated_speed_claim'])
        checks.append('complete_twelve_rows_ten_pairs_cost_bound_no_acceptance')
        checks.append('unrelated_GPU_work_does_not_block_target_release')
        mutations=[]
        rr=deepcopy(runner);rr['measurements']['requests'][1]['phases'][1]['solver_steps']=36
        mutations.append(('second_CAL_wrong_Native23_grid',rr,audit,terminal,metrics))
        vv=deepcopy(metrics);vv['pairs']=vv['pairs'][:-1]
        mutations.append(('missing_tenth_pair',runner,audit,terminal,vv))
        vv=deepcopy(metrics);vv['pairs'][0]['candidate_sha256']='0'*64
        mutations.append(('metric_wrong_video_SHA',runner,audit,terminal,vv))
        tt=deepcopy(terminal);tt['source_revision']='other'
        mutations.append(('wrong_frozen_source',runner,audit,tt,metrics))
        tt=deepcopy(terminal);tt['budget']['used_gpu_hours']+=.1
        mutations.append(('changed_settled_budget',runner,audit,tt,metrics))
        tt=deepcopy(terminal);tt['compute_after']='fixture_GPU_A, 505'
        mutations.append(('target_GPU_still_busy',runner,audit,tt,metrics))
        vv=deepcopy(metrics);vv['pairs'][0]['whole_video']['RGB_MSE_0to1']=float('nan')
        mutations.append(('nonfinite_metric',runner,audit,terminal,vv))
        for label,r,a,t,v in mutations:
            write(r,a,t,v)
            try:m.summarize(*(paths[n] for n in paths))
            except (AssertionError,ValueError):checks.append('refuse_'+label)
            else:raise AssertionError('Invalid fair summary admitted: '+label)
    return {'status':'FAIR_COMPLETE_MATRIX_SUMMARY_CPU_GUARDS_PASS_NOT_EXPERIMENT_RESULTS','CPU_only':True,'checks':checks}
