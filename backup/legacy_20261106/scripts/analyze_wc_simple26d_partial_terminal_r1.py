#!/usr/bin/env python3
"""Audit the OOM terminal prefix without granting full-card acceptance."""
import argparse,gzip,json,math,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.simple26d_r1 import CONFIG,RUN,METHODS,matrix,plans,audit_row
from wcomr.simple26d_post_r1 import summaries
from wcomr.h1_cost_curve_post_r1 import endpoint_identity
from wcomr.gpu_budget_pool_v2 import BudgetPool,sha

def analyze(value):
    config=json.loads((ROOT/CONFIG).read_text());scenes=[r['name'] for r in config['requests']]
    expected=matrix(scenes);runner=value['runner'];final=value['final'];rows=final['rows']
    assert all(value['payload_verified'].values()) and len(value['payload_verified'])==1644
    assert value['supervisor']['source_revision']==value['launch']['source_revision']=='36f5583f321b70778129c8231a849ef7e370827d'
    assert value['supervisor']['child_exit_code']==1 and value['post_exit']['exit_code']==0
    assert runner['status']=='SIMPLE26D_TECHNICAL_STOP_FULL24_SCOPE_RETAINED'
    assert runner['error_type']=='OutOfMemoryError' and 'CUDA out of memory' in runner['error']
    assert value['own_UUID_lock_free'] and all(p['state'] in (None,'Z','X') for p in value['original_processes'].values())
    assert len(rows)==len(expected)==36 and len(runner['runs'])==29
    assert [r['id'] for r in rows]==[r['id'] for r in expected]
    assert [r['id'] for r in runner['runs']]==[p['id'] for p in expected[:29]]
    assert all(r['status']=='COMPLETE' for r in rows[:28])
    assert rows[28]['id']=='timed_2_FRONT_DENSE_A' and rows[28]['status']=='RUNNING'
    assert all(r['status']=='NOT_REACHED_FULL_SCOPE_RETAINED' for r in rows[29:])
    assert all('LPIPS' not in r and 'decoded_video' not in r for r in rows[28:])
    baseline=json.loads((ROOT/config['references']['baseline']['ref']).read_text())
    assert sha(ROOT/config['references']['baseline']['ref'])==config['references']['baseline']['sha256']
    native={r['scene']:r for r in baseline['rows'] if r['method']=='NATIVE'}
    warm=[];scored=[];fixed_checks=[]
    for row,planned in zip(rows,expected):
        audit_row(row,planned)
        if row['status']!='COMPLETE':continue
        assert row['endpoint_audit']=='PASS' and row['decoded_video']['frames']==93
        assert row['counts']==dict(DD=26,PP=0,A=plans()[row['method']].count('A'),
            C_plain=plans()[row['method']].count('C'),C_or_A_after_P=0)
        if row['section']=='WARMUP':
            assert row['warm_guided_outputs']==36;warm.append(row);continue
        lp=row['LPIPS'];distances=lp['frame_distances']
        assert lp['frames']==len(distances)==93 and len(lp['pts'])==93
        assert all(math.isfinite(x) for x in distances)
        assert abs(sum(distances)/93-lp['mean_LPIPS'])<1e-12
        assert lp['reference_sha256']==native[row['scene']]['video_artifact']['sha256']
        assert lp['candidate_sha256']==row['video_artifact']['sha256']
        scored.append(row)
        if row['method'] in ('FIXED_A','FIXED_PLAIN'):
            prior=next(r for r in baseline['rows'] if (r['scene'],r['method'])==(row['scene'],row['method']))
            endpoint_identity(row,prior)
            fixed_checks.append(dict(scene=row['scene'],method=row['method'],old420_final_actions_RGB_equal=True))
    assert len(warm)==12 and len(scored)==16 and len(fixed_checks)==6
    assert len(final['warm_repeat_controls'])==len(final['warm_guided_controls'])==6
    assert all(x['status']=='PASS_ALL36_WARM_REPEAT_EQUAL' for x in final['warm_guided_controls'])
    assert all(x['warm_repeats_outputs_actions_RGB_equal'] and x['same_scene_formal_repeat_equal'] for x in final['warm_repeat_controls'])
    independent=summaries(rows,scenes)
    assert all(final[k]==v for k,v in independent.items())
    assert all(m['complete_four_scene_mean_LPIPS'] is None for m in independent['methods'])
    assert all(c['complete_mean_absolute_change'] is None for c in independent['contrasts'])
    pool=value['pool'];totals=BudgetPool.accounting(pool);assert all(pool[k]==v for k,v in totals.items())
    bill=value['billing'];job=pool['jobs'][RUN]
    assert job['status']=='SETTLED' and job['billing_sha256']==value['billing_sha256']
    assert job['actual_GPUh']==bill['actual_GPUh']==value['supervisor']['actual_GPUh']
    assert abs(bill['wall_seconds']/3600-bill['actual_GPUh'])<1e-12
    assert bill['gpu_uuid']==value['launch']['gpu_uuid'] and bill['launch_id']==value['launch']['launch_id']
    assert pool['cap_gpu_hours']==config['cumulative_cap_GPUh'] and pool['origin_used_gpu_hours']==79.99637737158223
    lookup={(r['scene'],r['method']):r for r in scored}
    values=[]
    for scene in scenes:
        cells=[]
        for method in METHODS:
            row=next(r for r in rows if r['section']=='TIMED' and (r['scene'],r['method'])==(scene,method))
            cells.append(dict(method=method,raw_status=row['status'],
                resolved_terminal_status='TECH_FAILED_CUDA_OOM' if row['status']=='RUNNING' else row['status'],
                LPIPS=row.get('LPIPS',{}).get('mean_LPIPS'),diagnostic_seconds=row.get('core_seconds'),counts=row.get('counts')))
        values.append(dict(scene=scene,cells=cells))
    # Paired frame coverage is descriptive within each video, not sample size.
    coverage=[]
    for a,b in [('FIXED_A','UNIFORM_A'),('FIXED_PLAIN','UNIFORM_C'),('UNIFORM_A','UNIFORM_C'),('FRONT_DENSE_A','FRONT_DENSE_C')]:
        for scene in scenes:
            x,y=lookup.get((scene,a)),lookup.get((scene,b))
            if x is None or y is None:continue
            lx,ly=x['LPIPS'],y['LPIPS'];assert lx['pts']==ly['pts'] and lx['reference_sha256']==ly['reference_sha256']
            pairs=list(zip(lx['frame_distances'],ly['frame_distances']))
            coverage.append(dict(scene=scene,candidate=a,baseline=b,LPIPS_change_percent=100*(lx['mean_LPIPS']/ly['mean_LPIPS']-1),
                improved_frames=sum(x<y for x,y in pairs),tied_frames=sum(x==y for x,y in pairs),worse_frames=sum(x>y for x,y in pairs),frames=93,
                independent_video_pairs=1))
    return dict(status='SIMPLE26D_OOM_TERMINAL_PARTIAL_ORIGINALS_AUDITED_WHOLE_CARD_NOT_ACCEPTED',
        source_revision=value['launch']['source_revision'],whole_card_accepted=False,strict_complete_analyzer_refusal='CHILD_EXIT_CODE_1',
        original_denominator=36,formal_denominator=24,warmup_denominator=12,complete_originals=28,
        complete_warmups=12,scored_formal_videos=16,scored_formal_frames=1488,rejected_paths=0,
        failed_path=dict(id=rows[28]['id'],raw_status='RUNNING',resolved_terminal_status='TECH_FAILED_CUDA_OOM',
            actual_failed_path_pairs='UNKNOWN_NOT_ZERO',error_type=runner['error_type'],error=runner['error']),
        not_reached_positions=[r['id'] for r in rows[29:]],planned_ordinary_pairs=1296,
        ordinary_pairs_of_completed_paths_only=28*36,complete_total_pairs='UNKNOWN_DUE_TO_FAILED_PATH',
        actual_GPUh=bill['actual_GPUh'],wall_seconds=bill['wall_seconds'],pool_totals=totals,
        old420_fixed_controls=fixed_checks,original_missing_fixed_controls=2,warm_guided_repeat_controls=6,
        paired_frame_coverage=coverage,scene_table=values,legacy_W3_scientific_acceptance_performed=False,
        new_GPU_submissions=0,no_automatic_rerun=True,**independent)

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();result=analyze(json.loads(gzip.decompress(a.capture.read_bytes())))
    result.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture))
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','whole_card_accepted','complete_originals','scored_formal_videos','actual_GPUh','pool_totals')}))

if __name__=='__main__':main()
