#!/usr/bin/env python3
"""Offline acceptance with independent frame means, speedups and ledger sums."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]

def same(a,b):
    if not math.isfinite(a) or not math.isfinite(b) or not math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-12):
        raise ValueError('Independent scalar reconstruction differs')

def accept(v):
    scope=json.loads((ROOT/'manifests/wc_paper_N05_core66_preregistration_r1_20261016.json').read_text())
    launch=v['launch'];f=v['final'];runner=v['runner'];supervisor=v['supervisor'];bill=v['billing'];pool=v['pool']
    assert v['status']=='N05_CORE66_ORIGINAL_ONCE_CAPTURE' and v['observed_unix']>=launch['next_check_not_before_unix']
    assert launch['run_id']==scope['run_id'] and launch['scope_counts']==scope['scope_counts']
    assert v['payload_verified'] and all(v['payload_verified'].values()) and v['own_UUID_lock_free']
    assert {r['source_revision'] for r in (launch,f,runner,supervisor,bill,v['production_CPU'])}=={v['registration']['source_revision']}
    assert v['post_exit']['exit_code']==0 and supervisor['child_exit_code']==0
    identities={
        'supervisor_pid':launch['supervisor_identity'],
        'post_watcher_pid':{'pid':launch['post_watcher_pid']},
        'child_pid':supervisor['child_identity']}
    for key,expected in identities.items():
        observed=v['original_processes'][key]
        assert observed['pid']==expected['pid']
        assert observed['state'] in (None,'Z','X') or (
            expected.get('start_ticks') is not None and observed.get('start_ticks')!=expected['start_ticks'])
    assert supervisor['runner_sha256']==v['runner_sha256'] and supervisor['billing_sha256']==v['billing_sha256']
    assert f['scope_counts']==scope['scope_counts'] and f['full_scope_slots']==66 and f['scientific_slots']==44
    assert len(f['rows'])==len(runner['runs'])==66 and len({r['id'] for r in f['rows']})==66
    assert [r['id'] for r in f['rows']]==[r['id'] for r in runner['runs']]
    assert not f['audit_failures'] and not f.get('CPU_terminal_error')
    assert f['status'] in ('N05_CORE66_COMPLETE44_AUDITED_93FRAME_SCORED',
        'N05_CORE66_FULL_SCOPE_REJECTIONS_OR_MISSING_REFERENCES_RETAINED')
    methods=[r['id'] for r in scope['methods']];scenes=[r['name'] for r in scope['requests']]
    rows=f['rows'];formal=[r for r in rows if r['section']=='TIMED'];warm=[r for r in rows if r['section']=='WARMUP']
    assert len(formal)==44 and len(warm)==22
    assert {(r['scene'],r['method']) for r in formal}=={(s,m) for s in scenes for m in methods}
    assert all(r['status'] in ('COMPLETE','TEXT_REJECTED','VIDEO_REJECTED') for r in rows)
    for r in rows:
        if r['status']=='TEXT_REJECTED':assert r['solver_steps']==r['guided_pairs']==0;continue
        assert r['raw_model_audit']=='PASS' and r['request_memory_lifecycle']['components_alive_after']==0
        n={35:36,26:27,18:19}[r['baseline_grid_point']['requested_steps']]
        assert r['solver_steps']==r['guided_pairs']==n
        if r['status']=='COMPLETE':assert r['endpoint_audit']=='PASS' and r['decoded_video']['frames']==93
        else:assert r['endpoint_audit']=='PASS_REJECTED_VIDEO_RETAINED'
    controls=(f['warm_repeat_controls'],f['warm_guided_controls'],f['original420_default_controls'])
    assert [len(c) for c in controls]==[11,5,20]
    for group in controls:
        assert all(r['status'].startswith('PASS') or r['status']=='MISSING_OR_REJECTED_RETAINED' for r in group)
    if all(r['status']=='COMPLETE' for r in rows):
        assert all(r['status'].startswith('PASS') for group in controls for r in group)
    table={(r['scene'],r['method']):r for r in formal if r['status']=='COMPLETE'}
    independent=[]
    for method in methods:
        case=[]
        for scene in scenes:
            r=table.get((scene,method))
            if r is None:case.append(dict(scene=scene,status='REJECTION_RETAINED'));continue
            seconds=r['core_seconds'];assert math.isfinite(seconds) and seconds>0
            result=dict(scene=scene,main_seconds=seconds,LPIPS=None,speedups={})
            for baseline in ('NATIVE35','WC_DEFAULT','RA_DEFAULT'):
                b=table.get((scene,baseline))
                if b is not None:result['speedups'][baseline]=b['core_seconds']/seconds
            if 'LPIPS' in r:
                lp=r['LPIPS'];dist=lp['frame_distances']
                assert lp['frames']==len(dist)==93 and all(math.isfinite(x) and x>=0 for x in dist)
                same(mean(dist),lp['mean_LPIPS']);result['LPIPS']=mean(dist)
                native=table[(scene,'NATIVE35')]
                assert lp['reference_sha256']==native['video_artifact']['sha256']
                assert lp['candidate_sha256']==r['video_artifact']['sha256']
            case.append(result)
        saved=next(r for r in f['methods'] if r['method']==method)
        assert len(saved['scene_rows'])==4
        for actual,written in zip(case,saved['scene_rows']):
            assert actual['scene']==written['scene']
            if 'main_seconds' not in actual:assert written['main_seconds'] is None;continue
            same(actual['main_seconds'],written['main_seconds'])
            if actual['LPIPS'] is not None:same(actual['LPIPS'],written['LPIPS'])
            else:assert written['LPIPS'] is None
            for k,value in actual['speedups'].items():same(value,written['speedups'][k])
        times=[r['main_seconds'] for r in case if 'main_seconds' in r]
        losses=[r['LPIPS'] for r in case if r.get('LPIPS') is not None]
        t=mean(times) if len(times)==4 else None;q=mean(losses) if len(losses)==4 else None
        for actual,written in ((t,saved['complete_four_scene_mean_seconds']),(q,saved['complete_four_scene_mean_LPIPS'])):
            if actual is None:assert written is None
            else:same(actual,written)
        independent.append(dict(method=method,scene_rows=case,mean_seconds=t,mean_LPIPS=q))
    same(bill['wall_seconds']/3600,bill['actual_GPUh']);same(bill['actual_GPUh'],supervisor['actual_GPUh'])
    job=pool['jobs'][scope['run_id']]
    assert job['status']=='SETTLED' and job['billing_sha256']==v['billing_sha256']
    same(job['actual_GPUh'],bill['actual_GPUh'])
    settled=[r for r in pool['jobs'].values() if r['status']=='SETTLED']
    reserved=[r for r in pool['jobs'].values() if r['status']!='SETTLED']
    same(pool['origin_used_gpu_hours']+sum(r['actual_GPUh'] for r in settled),pool['used_gpu_hours'])
    same(sum(r['billed_limit_GPUh'] for r in reserved),pool['reserved_gpu_hours'])
    same(pool['cap_gpu_hours']-pool['used_gpu_hours']-pool['reserved_gpu_hours'],pool['available_gpu_hours'])
    complete=f['status']=='N05_CORE66_COMPLETE44_AUDITED_93FRAME_SCORED'
    assert not complete or len(table)==sum('LPIPS' in r for r in formal)==44
    return dict(status='N05_CORE66_INDEPENDENTLY_ACCEPTED' if complete else 'N05_CORE66_ACCEPTED_WITH_REJECTIONS_RETAINED',
        source_revision=launch['source_revision'],full_denominator=66,formal_denominator=44,
        completed_formal_videos=len(table),scored_formal_videos=sum('LPIPS' in r for r in formal),
        warm_repeat_controls=11,full36_guided_controls=5,old420_default_controls=20,
        rejected_slots=[dict(id=r['id'],status=r['status']) for r in rows if r['status']!='COMPLETE'],
        actual_GPUh=bill['actual_GPUh'],fresh_v2_remaining_GPUh=pool['available_gpu_hours'],
        independent_methods=independent,stable_repeated_speed_claim=False,unseen_input_confirmation=False,
        corrected_neighbor_complete=False,GPU_submissions=0,ledger_written=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
    result=accept(json.loads(gzip.decompress(a.capture.read_bytes())))
    result.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
    a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='independent_methods'}))

if __name__=='__main__':main()
