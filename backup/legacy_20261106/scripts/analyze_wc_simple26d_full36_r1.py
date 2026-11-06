#!/usr/bin/env python3
"""Independent reconstruction from one collected immutable terminal receipt."""
import argparse,gzip,json,math,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.simple26d_r1 import CONFIG,RUN,audit_row,matrix,plans
from wcomr.simple26d_post_r1 import summaries
from wcomr.gpu_budget_pool_v2 import BudgetPool,sha

def analyze(value):
    config=json.loads((ROOT/CONFIG).read_text());scenes=[r['name'] for r in config['requests']]
    assert all(value['payload_verified'].values()) and value['post_exit']['exit_code']==0
    assert value['supervisor']['child_exit_code']==0
    assert value['supervisor']['source_revision']==value['launch']['source_revision']
    assert value['own_UUID_lock_free'] and all(p['state'] in (None,'Z','X') for p in value['original_processes'].values())
    final=value['final'];rows=final['rows'];expected=matrix(scenes)
    assert len(rows)==len(expected)==36 and len(value['runner']['runs'])==36
    baseline=json.loads((ROOT/config['references']['baseline']['ref']).read_text())
    native={r['scene']:r for r in baseline['rows'] if r['method']=='NATIVE'}
    assert len(native)==4 and len(final['warm_repeat_controls'])==6 and len(final['warm_guided_controls'])==6
    assert all(r['status'].startswith('PASS') for r in final['warm_guided_controls'])
    scored=0;rejections=[]
    for row,planned in zip(rows,expected):
        audit_row(row,planned)
        if row['status'] not in ('COMPLETE','VIDEO_REJECTED','TEXT_REJECTED'):raise ValueError('Technical incomplete path')
        if row['status']!='COMPLETE':rejections.append({k:row[k] for k in ('id','scene','method','status')});continue
        assert row['endpoint_audit']=='PASS' and row['decoded_video']['frames']==93
        assert row['counts']['DD']==26 and row['counts']['PP']==0
        assert row['counts']['A']==plans()[row['method']].count('A')
        if row['section']!='TIMED':continue
        lp=row['LPIPS'];distances=lp['frame_distances']
        assert lp['frames']==len(distances)==93 and all(math.isfinite(x) for x in distances)
        assert abs(sum(distances)/93-lp['mean_LPIPS'])<1e-12
        assert lp['reference_sha256']==native[row['scene']]['video_artifact']['sha256']
        assert lp['candidate_sha256']==row['video_artifact']['sha256'];scored+=1
    independent=summaries(rows,scenes)
    assert all(final[k]==v for k,v in independent.items())
    assert len(final['original_baseline_controls'])==8
    assert all(r['status'].startswith('PASS') or r['status']=='MISSING_OR_REJECTED_RETAINED' for r in final['original_baseline_controls'])
    pool=value['pool'];totals=BudgetPool.accounting(pool)
    assert all(pool[k]==v for k,v in totals.items())
    bill=value['billing'];job=pool['jobs'][RUN]
    assert job['status']=='SETTLED' and job['billing_sha256']==value['billing_sha256']
    assert job['actual_GPUh']==bill['actual_GPUh']==value['supervisor']['actual_GPUh']
    assert abs(bill['wall_seconds']/3600-bill['actual_GPUh'])<1e-12
    assert bill['gpu_uuid']==value['launch']['gpu_uuid'] and bill['launch_id']==value['launch']['launch_id']
    return dict(status='SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED' if not rejections else 'SIMPLE26D_FULL36_TERMINAL_WITH_REJECTIONS_RETAINED',
        formal_denominator=24,full_denominator=36,scored_formal_videos=scored,scored_formal_frames=93*scored,
        rejections=rejections,actual_GPUh=bill['actual_GPUh'],pool_totals=totals,**independent)

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();raw=a.capture.read_bytes();result=analyze(json.loads(gzip.decompress(raw)))
    result.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture))
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','formal_denominator','scored_formal_videos','actual_GPUh')}))

if __name__=='__main__':main()
