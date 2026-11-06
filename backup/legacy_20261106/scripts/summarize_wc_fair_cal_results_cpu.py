#!/usr/bin/env python3
"""Bind all fourteen results and describe the complete Native-relative matrix."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

VARIANTS=['native35','native23','wc004','wc006','wc008','stage_every1']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def proxy_dominates(a,b):
    """Simultaneous wall/MSE/SSIM/temporal dominance, not semantic quality."""
    av=[a['pipeline_wall_seconds'],a['RGB_MSE_0to1'],1-a['mean_luma_SSIM_win7'],
        a['temporal_difference_MSE_0to1']]
    bv=[b['pipeline_wall_seconds'],b['RGB_MSE_0to1'],1-b['mean_luma_SSIM_win7'],
        b['temporal_difference_MSE_0to1']]
    if any(not math.isfinite(v) for v in av+bv):
        raise ValueError('Nonfinite descriptive cost or fidelity proxy')
    return all(x<=y for x,y in zip(av,bv)) and any(x<y for x,y in zip(av,bv))


def summarize(runner_path,audit_path,metrics_path,terminal_path,cost_path):
    raw=gzip.decompress(runner_path.read_bytes());runner=json.loads(raw)
    audit,metrics,terminal,cost=(json.loads(p.read_text()) for p in
        (audit_path,metrics_path,terminal_path,cost_path))
    raw_sha=hashlib.sha256(raw).hexdigest()
    assert raw_sha==audit['receipt_sha256']==terminal['receipt_sha256']
    assert metrics['input_audit_sha256']==sha(audit_path)
    assert runner['status']=='FOURTEEN_COMPLETE_FAIR_OUTPUTS_REQUIRE_AUDIT_NOT_FRONTIER_ACCEPTANCE'
    assert audit['status']=='FOURTEEN_FAIR_CAL_NATIVE_WC_STAGE_VIDEO_AUDIT_PASS_NOT_QUALITY'
    assert metrics['status']=='TWO_EXPOSED_CAL_TEN_NATIVE_RELATIVE_FAIR_DIAGNOSTICS_NOT_ACCEPTANCE'
    assert terminal['status']=='FAIR_CAL_SOURCE_ASSETS_FULL_COST_RELEASE_AUDIT_PASS_REQUIRES_FOURTEEN_OUTPUT_AUDIT'
    assert terminal['source_revision']==audit['frozen_gpu_source']
    assert len(audit['files'])==runner['planned_output_files']==14 and len(metrics['pairs'])==10
    assert terminal['original_pids_absent']==[terminal['supervisor']['pid'],
        terminal['supervisor']['child_pid'],runner['pid']]
    assert terminal['global_lock_free']
    # Other users may still be working on the server's other GPUs. Release
    # evidence is scoped to this card's admitted UUID and original handles.
    release=terminal['supervisor']['release'];gpu=release['uuid']
    assert not release['pids']
    assert not any(line.split(',')[0].strip()==gpu
                   for line in terminal['compute_after'].splitlines())
    assert audit['original_GPU_budget_unchanged_during_CPU']
    assert metrics['CPU_only'] and not metrics['new_GPU_submission']
    assert metrics['original_GPU_budget_unchanged_during_CPU']
    budget=terminal['budget'];supervisor=terminal['supervisor'];wall=terminal['gpu_wall_seconds']
    assert budget==supervisor['budget_after'] and supervisor['exit_code']==0
    assert budget['cap_gpu_hours']==12 and budget['gpu_jobs_launched']==44
    assert not any(k.endswith('_inflight') for k in budget)
    assert supervisor['reserved_seconds']==6300 and math.isfinite(wall) and 0<wall<=6300
    assert math.isclose(budget['used_gpu_hours'],supervisor['budget_before']['used_gpu_hours']+wall/3600,
                        rel_tol=0,abs_tol=1e-12)
    pairs={(p['sample_name'],p['variant']):p for p in metrics['pairs']}
    assert len(pairs)==10 and all(p['reference']=='native35' for p in pairs.values())
    requests=runner['measurements']['requests'];groups=audit['measurement_groups']
    assert len(groups)==len(requests)==2
    rows=[];comparisons=[]
    for group,request in zip(groups,requests):
        name=group['sample_name'];assert name==request['sample_name']
        files=group['files'];assert [f['variant'] for f in files]==VARIANTS
        assert [p['workpoint']['name'] for p in request['phases']]==VARIANTS
        baseline=files[0];scene=[]
        for index,(file,phase) in enumerate(zip(files,request['phases'])):
            assert file['workpoint']==phase['workpoint']
            assert file['deep_CFG_calls']==sum(t['deep_executed'] for t in phase['trace'])
            assert phase['solver_steps']==file['solver_steps']==(24 if index==1 else 36)
            assert phase['CFG_calls']==file['CFG_calls']==phase['solver_steps']*2
            if index:
                pair=pairs[(name,file['variant'])]
                assert pair['baseline_sha256']==baseline['sha256'] and pair['candidate_sha256']==file['sha256']
                whole=pair['whole_video'];assert whole['frames']==93 and whole['transitions']==92
            else:
                # An identical reference has zero reference error by definition.
                # This is not an additional quality measurement or video pair.
                whole={'RGB_MSE_0to1':0.0,'mean_luma_SSIM_win7':1.0,
                       'temporal_difference_MSE_0to1':0.0}
            seconds=file['pipeline_wall_seconds'];assert math.isfinite(seconds) and seconds>0
            row={'sample_name':name,'variant':file['variant'],'video_sha256':file['sha256'],
                'reference_video_sha256':baseline['sha256'],'workpoint':file['workpoint'],
                'solver_steps':phase['solver_steps'],'CFG_calls':phase['CFG_calls'],
                'deep_CFG_calls':file['deep_CFG_calls'],'pipeline_wall_seconds':seconds,
                'descriptive_Native35_over_variant':baseline['pipeline_wall_seconds']/seconds,
                'descriptive_wall_reduction_fraction':1-seconds/baseline['pipeline_wall_seconds'],
                'reference_self_error_by_definition':index==0,'whole_video':whole}
            for k in ('RGB_MSE_0to1','mean_luma_SSIM_win7','temporal_difference_MSE_0to1'):
                row[k]=whole[k]
            if file['variant']=='stage_every1':
                provenance=file['provenance'];events=phase['refresh_provenance']['events']
                reads=[e['call'] for e in events if e['action']=='cache'
                    and any(s['kind']!='dense' for s in e['references_read'])]
                assert reads==provenance['cache_calls_reading_approximate']
                row.update(S_CFG_calls=provenance['sparse_CFG_calls'],
                    S_count=len(provenance['sparse_CFG_calls']),
                    S_attention_operators=provenance['sparse_attention_operators'],
                    window_eligible_per_CFG=provenance['window_eligible_per_CFG'],
                    cache_calls_reading_approximate=reads,
                    approximate_reads_after_stage_window=[c for c in reads if (c+1)//2>27])
                wc_trace=request['phases'][3]['trace']
                row['native_deep_decision_differences_vs_wc006']=[{
                    'call':a['call'],'solver_step':(a['call']+1)//2,'CFG_slot':(a['call']-1)%2,
                    'WC_deep':a['deep_executed'],'stage_deep':b['deep_executed']}
                    for a,b in zip(wc_trace,phase['trace']) if a['deep_executed']!=b['deep_executed']]
            scene.append(row)
        assert scene[3]['video_sha256']==runner['scope']['expected_WC_sha256'][name]
        for row in scene:
            row['descriptive_proxy_dominated_by']=[a['variant'] for a in scene
                if a['variant']!=row['variant'] and proxy_dominates(a,row)]
        stage=scene[5];wc=scene[3]
        comparisons.append({'sample_name':name,'WC006_over_stage_wall':wc['pipeline_wall_seconds']/stage['pipeline_wall_seconds'],
            'stage_minus_WC006_native_relative_RGB_MSE':stage['RGB_MSE_0to1']-wc['RGB_MSE_0to1'],
            'stage_minus_WC006_native_relative_SSIM':stage['mean_luma_SSIM_win7']-wc['mean_luma_SSIM_win7'],
            'stage_minus_WC006_native_relative_temporal_MSE':stage['temporal_difference_MSE_0to1']-wc['temporal_difference_MSE_0to1'],
            'stage_proxy_dominated_by':stage['descriptive_proxy_dominated_by'],
            'proxy_undominated_variants':[r['variant'] for r in scene if not r['descriptive_proxy_dominated_by']]})
        rows.extend(scene)
    remaining=(12-budget['used_gpu_hours'])*3600
    conf=cost['cards'][2];assert conf['planned_outputs']==6 and conf['complete_planning_seconds']<=conf['proposed_cap_seconds']
    return {'status':'ALL_FOURTEEN_FAIR_OUTPUTS_AUDITED_TEN_NATIVE_RELATIVE_CAL_DIAGNOSTICS_NOT_FRONTIER',
        'CPU_only':True,'run_id':runner['scope']['run_id'],'card':runner['run_card'],
        'source_revision':terminal['source_revision'],'receipt_sha256':raw_sha,
        'planned_outputs':14,'audited_outputs':14,'native_relative_pairs':10,'rows':rows,
        'descriptive_stage_comparisons':comparisons,'GPU_wall_seconds':wall,'GPU_hours':wall/3600,
        'budget':budget,'remaining_GPU_hours':remaining/3600,'remaining_seconds':remaining,
        'original_PIDs_lock_GPU_released':True,
        'followup_budget':{'CONF_proposal':{**conf,'selected':False,'GPU_submitted':False},
            'CONF_cap_with_15s_admission_fits':conf['proposed_cap_seconds']+15<=remaining,
            'reserved_seconds':0},
        'next_GPU_card_selected':False,'new_GPU_submission':False,'native_GPU_uninstrumented_parity':False,
        'quality_acceptance':False,'semantic_or_physics_acceptance':False,'quality_time_frontier_claim':False,
        'independent_confirmation':False,'causal_refresh_value_labels':False,'replicated_speed_claim':False,
        'limits':['All twelve measurement configurations and all ten Native-relative pairs retained.',
            'Four-dimensional dominance uses single ordered wall, RGB MSE, luma SSIM and temporal MSE only.',
            'An undominated point is a descriptive CAL proxy, not a validated semantic quality-time frontier.',
            'Native source/grid/deep execution is audited; separate uninstrumented real-GPU parity is absent.',
            'Two exposed CAL inputs, one run per configuration; no independent CONF or stable speed.',
            'No matched-cost causal labels, training, paid scoring or added human review.',
            'Later work requires scientific candidate selection and separately frozen cost/resource admission.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('runner','audit','metrics','terminal','cost','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();paths=[a.runner,a.audit,a.metrics,a.terminal,a.cost]
    r=summarize(*paths);r['input_files_sha256']={str(p):sha(p) for p in paths};r['summary_code_sha256']=sha(Path(__file__))
    a.output.write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:r[k] for k in ['status','rows','descriptive_stage_comparisons','GPU_wall_seconds','remaining_GPU_hours','followup_budget']}))
