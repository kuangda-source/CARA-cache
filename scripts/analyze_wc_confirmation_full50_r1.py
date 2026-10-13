"""Independently reconstruct the frozen full50 matrix and all93-frame summaries."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
CAPTURE='reports/wc_source_confirmation_scheduled_collection_20261013.json'
CONFIG='configs/wc_source_conditional_confirmation_full50_production_r1_20261013.json'


def main():
    path=ROOT/CAPTURE;x=json.loads(path.read_text());c=json.loads((ROOT/CONFIG).read_text())
    f=x['final'];sup=x['supervisor'];post=x['post_exit'];rows=f['rows']
    assert x['source_revision']==f['source_revision']=='e48ba58047b09507ea6f438f5077ebffb4fb2114'
    assert all(x['payload_verified'].values()) and len(x['payload_verified'])==684
    assert x['config_sha256']==hashlib.sha256((ROOT/CONFIG).read_bytes()).hexdigest()
    assert f['scope_counts']==c['scope_counts'] and f['candidate_freeze_sha256']==c['candidate_freeze_sha256']
    assert sup['child_exit_code']==post['exit_code']==0 and x['kernel_lock_free']
    assert not any(x['original_processes'].values()) and not x['original_production_CPU_pid_alive']
    assert f['budget_before_sha256']==f['budget_after_sha256']==x['ledger_sha256']
    assert not f['CUDA_initialized'] and not f['ledger_written']
    used=x['ledger']['used_gpu_hours'];cost=sup['wall_seconds']/3600
    assert math.isclose(used-sup['budget_before']['used_gpu_hours'],cost,abs_tol=1e-10)
    template=ROOT/c['matrix_template_ref']
    assert hashlib.sha256(template.read_bytes()).hexdigest()==c['matrix_template_sha256']
    planned=json.loads(template.read_text())['rows'];assert len(rows)==len(planned)==50
    for row,p in zip(rows,planned):
        assert all(row[k]==v for k,v in p.items())
        assert row['solver_steps']==row['guided_pairs']==36 and row['actual_request_seed']==p['seed']
        assert row['request_context_seed_tag']=='fixed-seed'+str(p['seed'])+'-request'
        assert all(row[k]==0 for k in ('in_timing_guided_copies','in_timing_hashes','research_checkpoints'))
        assert row['status'] in ('COMPLETE','VIDEO_REJECTED')
        assert row['endpoint_audit']==('PASS' if row['status']=='COMPLETE' else 'PASS_REJECTED_VIDEO_RETAINED')
        if row['status']=='COMPLETE':assert row['decoded_video']['frames']==93
    assert len(f['warm_repeat_controls'])==len(f['original_CAL_controls'])==5
    assert all(r['status'].startswith('PASS_') for r in f['warm_repeat_controls']+f['original_CAL_controls'])
    formal=[r for r in rows if r['section']=='TIMED'];assert len(formal)==40
    lookup={(r['scene'],r['method']):r for r in formal};assert len(lookup)==40
    for r in formal:
        if r['status']=='VIDEO_REJECTED':assert 'LPIPS' not in r;continue
        l=r['LPIPS'];a=l['frame_distances'];native=lookup[(r['scene'],'NATIVE')]
        assert len(a)==l['frames']==93 and all(math.isfinite(v) and v>=0 for v in a)
        assert math.isclose(mean(a),l['mean_LPIPS'],rel_tol=1e-12,abs_tol=1e-12)
        assert l['reference_sha256']==native['video_artifact']['sha256']
        assert l['candidate_sha256']==r['video_artifact']['sha256']
        if r['method']=='NATIVE':assert r['actions'] is None and not any(a)
        if r['method']=='TABLE_PHASE_H1':
            assert r['method_fingerprint']=='34ef948ed2a309e8b1cae4b72b780c14e21d63383fa1eadcdfc8803c3d5beef8'
            assert r['counts']==dict(DD=26,PP=0,C_plain=5,A=5,C_or_A_after_P=0)
    assert sum('LPIPS' in r for r in formal)==f['scored_formal_videos']==39
    methods=[]
    for method in c['methods']:
        selected=[r for r in formal if r['method']==method];scored=[r for r in selected if 'LPIPS' in r]
        assert len(selected)==8
        methods.append(dict(method=method,request_seed_denominator=8,scored_videos=len(scored),
            statuses=dict(Counter(r['status'] for r in selected)),all8_mean_main_seconds=mean(r['core_seconds'] for r in selected),
            full4prompt_two_seed_mean_LPIPS=mean(r['LPIPS']['mean_LPIPS'] for r in scored) if len(scored)==8 else None,
            available_only_mean_LPIPS_descriptive=mean(r['LPIPS']['mean_LPIPS'] for r in scored)))
    comparisons=[]
    for comp in f['comparisons']:
        vals=[]
        for request in c['requests']:
            a,b=lookup[(request['name'],comp['candidate'])],lookup[(request['name'],comp['baseline'])]
            if 'LPIPS' not in a or 'LPIPS' not in b:continue
            aq,bq=a['LPIPS']['mean_LPIPS'],b['LPIPS']['mean_LPIPS']
            vals.append(dict(scene=request['name'],seed=request['seed'],candidate_LPIPS=aq,baseline_LPIPS=bq,
                improved=aq<bq,delta_LPIPS=aq-bq,
                better_frames=sum(v<w for v,w in zip(a['LPIPS']['frame_distances'],b['LPIPS']['frame_distances']))))
        assert len(vals)==comp['scored_request_seed_pairs']
        complete=len(vals)==8
        if complete:
            aq,bq=mean(v['candidate_LPIPS'] for v in vals),mean(v['baseline_LPIPS'] for v in vals)
            assert math.isclose(aq,comp['prompt_equal_candidate_LPIPS'],abs_tol=1e-12)
            assert math.isclose(bq,comp['prompt_equal_baseline_LPIPS'],abs_tol=1e-12)
            reduction=100*(1-aq/bq)
            assert math.isclose(reduction,comp['prompt_equal_LPIPS_reduction_percent'],abs_tol=1e-10)
        else:
            assert 'prompt_equal_candidate_LPIPS' not in comp;reduction=None
        comparisons.append(dict(candidate=comp['candidate'],baseline=comp['baseline'],denominator=8,
            paired_videos=len(vals),improved_paired_videos=sum(v['improved'] for v in vals),
            complete_four_prompt_LPIPS_reduction_percent=reduction,available_paired_rows=vals))
    by={m['method']:m for m in methods}
    result=dict(status='FROZEN_CONF_FULL50_TERMINAL_AND_ALL39_COMPATIBLE93_FRAME_RESULTS_ACCEPTED_ONE_RA_REJECTION',
        inputs={CAPTURE:hashlib.sha256(path.read_bytes()).hexdigest(),CONFIG:hashlib.sha256((ROOT/CONFIG).read_bytes()).hexdigest()},
        all50_terminal=True,formal_paths=40,scored_formal_videos=39,rejected_rows=[{k:r[k] for k in ('id','scene','seed','method','status')} for r in rows if r['status']!='COMPLETE'],
        methods=methods,comparisons=comparisons,H1_speedup_over_Native=by['NATIVE']['all8_mean_main_seconds']/by['TABLE_PHASE_H1']['all8_mean_main_seconds'],
        H1_all8_same_26D5A5C=True,actual_GPUh=cost,used_GPUh=used,remaining_GPUh=x['ledger']['cap_gpu_hours']-used,
        GPU_and_post_original_handles_ended=True,physics_claim=False,repeated_speed_claim=False,
        frames_are_not_independent_videos=True,new_fit_or_threshold_tuning=False)
    out=ROOT/'reports/wc_source_confirmation_full50_independent_acceptance_20261013.json'
    assert not out.exists();out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','H1_speedup_over_Native','actual_GPUh','used_GPUh','remaining_GPUh')}))


if __name__=='__main__':main()
