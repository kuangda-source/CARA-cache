"""Freeze one new resume card and quote; no remote work or reservation."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def build(carry):
    card=json.loads((HERE/'pipeline_r2/manifest.json').read_text())
    matrix=copy.deepcopy(card['matrix'][:2])
    for i,row in enumerate(matrix,1):row['id']=f'RESUME_WARM_{i:03d}'
    matrix+=copy.deepcopy(card['matrix'][8:])
    assert len(matrix)==116 and matrix[2]['id']=='PIPE_009'
    q=card['quote'];full=q['scenarios']['with_5_controls']
    native=json.loads((HERE/'manifest.json').read_text())['quote']['measured_request_seconds']['NATIVE35']
    removed=native+sum((37-t)*q['pair_D_seconds']+q['suffix_overhead_seconds'] for t in (8,34,8,10,12))
    compute=full['non_snapshot_request_GPUh']*3600-removed
    state=full['state_save_GPUh']*3600+109*q['restore_seconds_charged']
    center=(1.1*(compute+state)+1200)/3600
    limits=[(.95*compute+.75*state+1200)/3600,(1.15*compute+1.35*state+1200)/3600]
    run='cara-native-sensitivity8-resume-r3-20261105'
    previous=card['run_id'];scope=card['scope_sha256']
    rows=carry['rows']
    assert [r['slot']['id'] for r in rows]==[f'PIPE_{n:03d}' for n in range(3,9)]
    assert all(r['status']=='COMPLETE' for r in rows)
    card.update(schema='CARA_SENSITIVITY8_RESUME_R3',run_id=run,
        stage_name='cara-budget-calibration-GPU-'+run[5:],phase='AUTHORIZED_SINGLE_RESUME',
        GPU_dispatch_ready=True,matrix=matrix,
        counts=dict(a=3,b=109,c=0,warm=2,controls=2,total_requests=116,reused_Native_records=5,
            carried_controls=3,carried_sensitivity=3,LPIPS_pairs=112,quality_positions=0,
            total_new_paired_calls=sum(r['actual_updates'] if 'actual_updates' in r else 37-r['target_update'] if r['role'] in ('SINGLE_C','RESUME_D') else 36 for r in matrix)),
        authority=dict(execution_authorized=True,user_quote='批准从 PIPE_009 续跑，约 9.84 GPUh',
            approved_at='2026-11-05T00:30:00+08:00',authorizes_GPU=True,authorizes_ledger_reservation=True,
            cumulative_GPUh_policy='TRACK_ACTUAL_NO_CUMULATIVE_HARD_CAP; individual quote above8GPUh needs direct user approval',
            automatic_monitoring_allowed=False),
        reservation_event='SENSITIVITY8_RESUME_R3_WHOLE11_RESERVE',host_memory_logging=True,
        carryover=dict(run_id=previous,launch_id='56926fe31f234746940a9d2d6677335d',scope_sha256=scope,
            source_collection_sha256=carry['collection_sha256'],output_root=carry['output_root'],rows=rows,
            policy='Verify each artifact hash once on import; seed control index and score all six after release. No replay/recharge.'),
        quote=dict(basis=q['basis'],pair_D_seconds=q['pair_D_seconds'],suffix_overhead_seconds=q['suffix_overhead_seconds'],
            removed_completed_compute_seconds=removed,non_snapshot_request_GPUh=compute/3600,
            state_save_GPUh=full['state_save_GPUh'],state_read_restore_GPUh=109*q['restore_seconds_charged']/3600,
            snapshot_save_count=42,restores=109,restore_seconds_charged=q['restore_seconds_charged'],
            fresh_warm_count=2,model_load_GPUh=600/3600,release_GPUh=600/3600,
            forecast_GPUh=center,range_GPUh=limits,hard_GPUh=11.0,expected_wall_hours=center,
            uncertainty=q['uncertainty']+' Per-request GC overhead and real40g peak remain unmeasured.'),
        output_root='/data20t/gaokuangda/worldcache_workspace/outputs/'+run,
        stage_root='/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-GPU-'+run[5:])
    card['storage'].update(total_old_plus_new_images_GiB=384,private_output_GiB=64,provisioned=False)
    card.pop('budget_calibration_r1_image_cleanup',None);card.pop('ledger_snapshot',None)
    del card['scope_sha256']
    card['scope_sha256']=hashlib.sha256(json.dumps(card,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return card


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--carry',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();card=build(json.loads(a.carry.read_text()));a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as stream:json.dump(card,stream,indent=2,ensure_ascii=False);stream.write('\n')
    print(json.dumps(card['quote'],indent=2))
