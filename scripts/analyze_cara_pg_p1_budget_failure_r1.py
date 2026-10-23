"""Offline attribution from complete accepted P1/price originals. No GPU or refit.

Recomputes full-request components, proxy scores, masks, measured rejection,
Native closure and price-context decomposition. Counterfactual costs are
explicit diagnostics and never overwrite a bundle, policy or decision.
"""
import argparse, collections, hashlib, json, math, statistics, time
from pathlib import Path
from wcomr.policy_generator_r1.interval_grammar import Profile, Edge, compile_policy
from wcomr.policy_generator_r1.search_protocol import choose_observed, front_dense_control
from wcomr.policy_generator_r1.proposal_tables import Costs
from wcomr.policy_generator_r1.continuation_preparation import TIME_BOUNDARY


def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def record(v,k):
    r=v['files'][k]; raw=r['raw_utf8'].encode()
    assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
    return json.loads(raw)
def avg(x): return statistics.mean(x)
def close(a,b): assert math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8),(a,b)

def analyze(capture, acceptance, price_capture):
    v=json.loads(Path(capture).read_text()); accepted=json.loads(Path(acceptance).read_text())
    assert accepted['full_protocol_accepted'] and accepted['capture_sha256']==digest(capture)
    r=record(v,'runner'); b=r['batch']; c=record(v,'consumer'); bundle=record(v,'new_bundle')
    assert b['status']=='BUDGET_NOT_VERIFIED' and b['selected'] is None and b['query_attempts']==4
    rows=b['rows']; assert len(rows)==64
    native=[x for x in rows if x['id'].startswith('native_fit_')]
    assert all(x['status']=='COMPLETE' for x in native)
    ntime=avg(x['full_request_seconds'] for x in native); ncore=avg(x['core_seconds'] for x in native)
    outside=ntime-ncore; shared=c['costs']['shared_seconds']; native_pred=shared+math.fsum(c['costs']['dense_seconds'])
    gap=ntime-native_pred; B=c['budget_seconds']; close(.8*ntime,B)
    close(shared,bundle['costs']['shared_seconds']+outside)
    stats={(x['member'],x['source'],x['update']):x for x in c['statistics']}
    candidates=[]; selection_records=[]
    for cand in b['candidates']:
        q=cand['query_slot']; policy=cand['proposal']['policy']
        rr=[x for x in rows if x['id'].startswith('q'+str(q)+'_fit_')]
        assert len(rr)==4 and all(x['status']=='COMPLETE' for x in rr)
        ap=[]
        for t,a in enumerate(policy['actions']):
            table=c['costs']['dense_seconds'] if a=='D' else c['costs']['C_seconds'] if a=='C' else c['costs']['A_seconds_by_alpha'][str(policy['shared_alpha'][t])]
            ap.append(table[t])
        pred=shared+math.fsum(ap);close(pred,cand['proposal']['predicted_seconds'])
        per=[];proxy=[]
        for row in rr:
            h=row['semantic_history'];assert len(h)==36 and all(x['actual']==x['planned'] and x['fallback_reason'] is None for x in h)
            assert [x['actual'] for x in h]==policy['actions'] and row['teacher_calls']==0 and row['online_fitting'] is False
            names=('method_install_seconds','guarded_pipeline_without_write_seconds','video_write_seconds','method_cleanup_seconds')
            close(math.fsum(row[k] for k in names),row['full_request_seconds'])
            score=json.loads(v['scores'][row['id']]['raw_utf8']);assert score['frames']==len(score['frame_distances'])==93
            close(avg(score['frame_distances']),row['LPIPS'])
            loss=0.
            for t,a in enumerate(policy['actions'],1):
                if a=='D':continue
                s=stats[row['member'],policy['source_before'][t-1],t];alpha=policy['shared_alpha'][t-1] or 0.
                loss+=max(0.,s['e2']+2*alpha*s['ed']+alpha**2*s['d2'])
            proxy.append(loss)
            per.append(dict(id=row['id'],member=row['member'],LPIPS=row['LPIPS'],full_seconds=row['full_request_seconds'],core_seconds=row['core_seconds'],outside_core_seconds=row['full_request_seconds']-row['core_seconds'],video_write_seconds=row['video_write_seconds'],install_seconds=row['method_install_seconds'],cleanup_seconds=row['method_cleanup_seconds'],started_unix=row['started_unix']))
            selection_records.append(dict(fingerprint=policy['fingerprint'],prompt=row['member'],seed=0,split='CAL_FIT',status='COMPLETE',LPIPS=row['LPIPS'],measured_seconds=row['full_request_seconds'],timing_protocol=TIME_BOUNDARY,profile_identity=c['profile']['identity'],endpoint_basis='NATURAL_FULL_TRAJECTORY_ALL_REGISTERED_FRAMES_LPIPS'))
        if cand['proposal']['proxy_loss'] is not None:close(avg(proxy),cand['proposal']['proxy_loss'])
        obs=avg(x['full_seconds'] for x in per); core=avg(x['core_seconds'] for x in per); outer=obs-core
        anchors=[];history=[]
        for t,a in enumerate(policy['actions'],1):
            if a=='D':anchors.append(t)
            else:history.append(dict(target=t,action=a,source_age=t-anchors[-1],actual_window=anchors[-2:],teacher_window=[anchors[-1]-1,anchors[-1]],history_gap=anchors[-1]-anchors[-2]))
        candidates.append(dict(role=cand['roles'][0],query_slot=q,fingerprint=policy['fingerprint'],actions=''.join(policy['actions']),counts=policy['counts'],A_alpha_counts=dict(collections.Counter(str(x) for x in policy['shared_alpha'] if x is not None)),predicted_seconds=pred,observed_mean_seconds=obs,mean_LPIPS=avg(x['LPIPS'] for x in per),recomputed_teacher_proxy=avg(proxy),predicted_slack_seconds=B-pred,over_budget_seconds=obs-B,over_budget_percent=100*(obs/B-1),prediction_underestimate_seconds=obs-pred,core_prediction_underestimate_seconds=core-(pred-outside),outside_prediction_underestimate_seconds=outer-outside,after_descriptive_Native_rebase_residual_seconds=obs-(pred+gap),prompt_rows=per,history_points=history,history_mismatch_targets=sum(x['actual_window']!=x['teacher_window'] for x in history),max_source_age=max(x['source_age'] for x in history),fallbacks=0))
    choice=choose_observed(selection_records,members=tuple((x,0) for x in c['CAL_FIT_members']),candidate_fingerprints=[x['fingerprint'] for x in candidates],budget_seconds=B,timing_protocol=TIME_BOUNDARY,profile_identity=c['profile']['identity'],split='CAL_FIT',loss_ceiling=1e100)
    assert not choice['order'] and choice['selected'] is None
    pv=json.loads(Path(price_capture).read_text()); price=record(pv,'runner')
    # The P1 bundle is byte-identical to the fully accepted replacement bundle.
    assert pv['files']['bundle']['sha256']==v['files']['new_bundle']['sha256']
    contexts={}
    for mode in ('CONTROL','PRICE'):
        group=[x for x in price['runs'] if x['section']=='FORMAL' and x['mode']==mode]
        assert len(group)==4
        contexts[mode]=dict(D_seconds=avg(math.fsum(z['D_action_seconds'] for z in x['action_clocks']) for x in group),prefix_seconds=avg(math.fsum(z['shared_prefix_seconds'] for z in x['action_clocks']) for x in group),whole_pair_seconds=avg(math.fsum(z['whole_pair_seconds'] for z in x['action_clocks']) for x in group),core_seconds=avg(x['core_seconds'] for x in group))
    contexts['mix_shift_relative_CONTROL_seconds']=(contexts['CONTROL']['whole_pair_seconds']-contexts['PRICE']['whole_pair_seconds'])/2
    contexts['P1_Native_minus_CONTROL_core_seconds']=ncore-contexts['CONTROL']['core_seconds']
    contexts['timer_boundary_residual_seconds']=gap-contexts['mix_shift_relative_CONTROL_seconds']-contexts['P1_Native_minus_CONTROL_core_seconds']
    assert abs(contexts['timer_boundary_residual_seconds'])<.01
    close(gap,contexts['mix_shift_relative_CONTROL_seconds']+contexts['P1_Native_minus_CONTROL_core_seconds']+contexts['timer_boundary_residual_seconds'])
    # Purely counterfactual CPU feasibility: preserve B, no new endpoint query.
    cp=dict(c['profile']);cp['protected_dense']=tuple(cp['protected_dense']);cp['alpha_candidates']=tuple(cp['alpha_candidates']);profile=Profile(**cp)
    cc=dict(c['costs']);cc['A_seconds_by_alpha']={float(k):tuple(a) for k,a in cc['A_seconds_by_alpha'].items()}
    diagnostic=[]
    for name,offset in [('ORIGINAL',0.),('NATIVE_CLOSURE_ONLY',gap)]:
        cost=Costs(**{**cc,'shared_seconds':shared+offset})
        for mode in ('C','A'):
            p=front_dense_control(profile,cost,budget_seconds=B,mode=mode,quantum_seconds=c['quantum_seconds'])
            diagnostic.append(dict(scenario=name,mode=mode,offset_seconds=offset,counts=p['policy']['counts'],predicted_seconds=p['predicted_seconds'],actual_budget_verified=False))
    fixed_counts=[]
    for n in (24,25,26):
        dense=list(range(1,n))+[36];bounds=dense+[37]
        for mode in ('C','A'):
            edges=tuple(Edge(s,e,(s+1,e-1) if mode=='A' and e>s+1 else (),1. if mode=='A' and e>s+1 else 0.) for s,e in zip(bounds,bounds[1:]));policy=compile_policy(profile,edges);cost=Costs(**cc)
            pred=cost.shared_seconds+math.fsum(cost.edge_seconds(e) for e in edges)
            fixed_counts.append(dict(dense_count=n,mode=mode,original_prediction=pred,Native_rebased_prediction=pred+gap,actual_measured=n==26))
    baseline=candidates[0];comparisons=[]
    for x in candidates[1:]:
        delta=[a['LPIPS']-z['LPIPS'] for a,z in zip(x['prompt_rows'],baseline['prompt_rows'])]
        comparisons.append(dict(role=x['role'],relative_mean_LPIPS_change_percent=100*(x['mean_LPIPS']/baseline['mean_LPIPS']-1),per_prompt_LPIPS_deltas=delta,improved_prompts=sum(d<0 for d in delta),mean_time_difference_seconds=x['observed_mean_seconds']-baseline['observed_mean_seconds'],not_repeated_balanced_timing=True))
    return dict(status='COMPLETE_ACCEPTED_P1_OFFLINE_CAUSAL_BOUNDARIES_AND_REPAIR_ANALYSIS',created_unix=time.time(),evidence={k:dict(path=str(p),sha256=digest(p)) for k,p in [('capture',capture),('acceptance',acceptance),('price_capture',price_capture)]},frozen_budget_seconds=B,Native=dict(observed_full_seconds=ntime,observed_core_seconds=ncore,outside_core_seconds=outside,action_model_full_seconds=native_pred,pre_endpoint_closure_gap_seconds=gap),scope=dict(registered_positions=64,executed_paths=30,scored_pairs=16,query_attempts=4,remaining_query_upper_bound_unused=4,SELECT_executed=0,TEST_executed=0,technical_or_refusal_failures=0),candidates=candidates,measured_selection_recomputed=choice,price_context_decomposition=contexts,descriptive_quality_comparisons=comparisons,CPU_cost_counterfactuals=diagnostic,fixed_prefix_cost_diagnostics=fixed_counts,attribution=dict(total_request_underprediction_confirmed=True,all_D_closure_gap_preexisted_candidates=True,no_feasible_incumbent_disables_refinement_confirmed=True,fallback_or_extra_teacher_cause=False,quality_guard_caused_original_stop=False,individual_action_misbias_not_identifiable_from_clean_request_totals=True,thermal_clock_or_system_load_causality_not_established=True,teacher_proxy_is_not_endpoint_quality=True),new_endpoint_queries=0,GPU_submissions=0,production_files_modified=False,budget_or_selection_changed=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--acceptance',type=Path,required=True);p.add_argument('--price-capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    v=analyze(a.capture,a.acceptance,a.price_capture)
    with a.output.open('x') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(status=v['status'],Native=v['Native'],price_context=v['price_context_decomposition'],counterfactuals=v['CPU_cost_counterfactuals'],quality=v['descriptive_quality_comparisons']),ensure_ascii=False))
if __name__=='__main__':main()
