"""Remaining per-input pipeline and measured whole-card quote. No remote work."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def build(measurement,backing_read,reuse_check,ledger,deletion):
    original=json.loads((HERE/'manifest.json').read_text())
    card=copy.deepcopy(original);inputs=original['inputs'];first=inputs[0]['name']
    reused=reuse_check['records'];reused_names=[r['row']['slot']['member'] for r in reused]
    matrix=[]
    def add(source):
        row=copy.deepcopy(source);row['original_slot_id']=row['id'];row['id']=f'PIPE_{len(matrix)+1:03d}';matrix.append(row)
    for row in original['matrix']:
        if row['section']=='warm':add(row)
    for member in (r['name'] for r in inputs):
        if member not in reused_names:
            add(next(r for r in original['matrix'] if r['section']=='a' and r['member']==member))
        if member==first:
            for row in original['matrix']:
                if row['section']=='control' and row['role'] in ('NATIVE35','RESUME_D'):add(row)
        for t in original['sensitivity_steps']:
            add(next(r for r in original['matrix'] if r['section']=='b' and r['member']==member and r['target_update']==t))
        if member==first:
            for row in original['matrix']:
                if row['role']=='FULL_SINGLE_C':add(row)
    q=original['quote'];pair=q['pair_D_seconds'];overhead=q['suffix_overhead_seconds']
    # Complete old record clocks less their mtime capture windows and clean Native.
    record_clocks=[2178.0906244842336,1542.478001604788,902.824264857918,1220.294984748587,1096.5093813948333]
    capture_windows=[1736.603970508,1099.0378595,560.481872465,854.217985778,745.803422049]
    record_extra=sum(a-b for a,b in zip(record_clocks,capture_windows))/5-q['measured_request_seconds']['NATIVE35']
    warm=450.159909889102+223.38863776158541
    cold_seconds=measurement['state_bytes']/(backing_read['MB_per_second']*1e6)
    restore=measurement['torch_load_seconds']+measurement['restore_equivalent_seconds']+cold_seconds
    saves=42*measurement['save_total_single_hash_seconds']
    suffix=sum((37-t)*pair+overhead for t in original['sensitivity_steps'])*8
    record=3*(q['measured_request_seconds']['NATIVE35']+record_extra)
    controls=3*q['measured_request_seconds']['NATIVE35']+sum((37-t)*pair+overhead for t in (8,34))
    def price(keep_controls):
        physical=117+5*keep_controls;loads=112+2*keep_controls
        compute=warm+record+suffix+controls*keep_controls;state=saves+loads*restore
        center=(1.1*(compute+state)+1200)/3600
        low=(.95*compute+.75*state+1200)/3600
        high=(1.15*compute+1.35*state+1200)/3600
        hard=math.ceil(high*4)/4
        return dict(requests=physical,guided_pairs=1972+140*keep_controls,with_controls=bool(keep_controls),
            non_snapshot_request_GPUh=compute/3600,state_save_GPUh=saves/3600,state_read_restore_GPUh=loads*restore/3600,
            model_load_GPUh=600/3600,release_GPUh=600/3600,center_GPUh=center,range_GPUh=[low,high],
            recommended_hard_GPUh=hard,expected_wall_hours=center,
            available_after_proposed_hard_reservation_GPUh=ledger['totals']['available_gpu_hours']-hard)
    scenarios=dict(with_5_controls=price(True),without_5_controls=price(False));primary=scenarios['with_5_controls']
    quote=dict(basis='CAL35 D-pair/Native clocks + original non-capture record residual + measured single-hash CPU state path; cold backing read added to warm torch.load',
        pair_D_seconds=pair,suffix_overhead_seconds=overhead,record_non_capture_extra_seconds=record_extra,
        snapshot_save_count=42,restores_with_controls=114,cold_state_read_seconds=cold_seconds,restore_seconds_charged=restore,
        CPU_measurement=measurement,backing_read=backing_read,scenarios=scenarios,
        forecast_GPUh=primary['center_GPUh'],range_GPUh=primary['range_GPUh'],hard_GPUh=primary['recommended_hard_GPUh'],
        uncertainty='Engineering range, not a confidence interval: compute 0.95–1.15, measured state path 0.75–1.35; center includes 10% variation. CPU transfer proxy, one save sample, XFS backing-path save not a new mounted loop. H2D/D2H and new-loop overhead remain unmeasured.')
    run='cara-native-sensitivity8-pipeline-r2-20261104'
    old_root='/data20t/gaokuangda/worldcache_workspace/outputs/cara-native-sensitivity8-confirm4-r1-20261104'
    f17_stage='/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-GPU-f17-confirm4-r1-20261104'
    card.update(schema='CARA_SENSITIVITY8_PIPELINE_R2',run_id=run,stage_name='cara-budget-calibration-GPU-'+run[5:],
        phase='FORMAL_QUOTE_AWAITING_APPROVAL',GPU_dispatch_ready=False,matrix=matrix,
        counts=dict(a=3,b=112,c=0,warm=2,controls=5,total_requests=len(matrix),reused_Native_records=5,
            suffix_paired_calls=1792,total_new_paired_calls=2112,LPIPS_pairs=112,quality_positions=0),
        authority=dict(execution_authorized=False,user_quote='走流水线，去掉重复哈希，并删掉budget-calibration-r1的64GiB镜像，然后给我正式报价',
            authorizes_GPU=False,authorizes_ledger_reservation=False,cap_increase_allowed=False,automatic_monitoring_allowed=False),
        pipeline=dict(order='per input: existing/new Native, all 14 suffixes, discard only newly written state_before files',
            delete_new_state_files_after_complete_suffixes=True,reused_state_policy='READ_ONLY_KEEP_THROUGH_COMPLETE_RELEASE_SCORE_ANALYSIS',
            retained='metrics.json, all36 pre-update latents, terminal latent, 14 guided tensors, MP4s'),
        reuse=dict(run_id=original['run_id'],scope_sha256=original['scope_sha256'],collection=old_root+'/collection.json',output_root=old_root,
            record_ids=[r['row']['slot']['id'] for r in reused],members=reused_names,files_checked=reuse_check['files_checked'],
            integrity_scope=reuse_check['integrity_scope'],stored_file_hashes=reuse_check['stored_file_hashes'],
            state_files=[dict(member=r['row']['slot']['member'],**f) for r in reused for f in r['files']]),
        reuse_confirmation=dict(run_id='cara-f17-confirm4-r1-20261104',scope_sha256='831797c82e8d1fa4ffe31716c5696da768b960571efe93dec8f094dfc0b5e6be',
            collection='/data20t/gaokuangda/worldcache_workspace/outputs/cara-f17-confirm4-r1-20261104/collection.json',
            scores=f17_stage+'/released-score-control/scores.json',release=f17_stage+'/released-score-control/release.json',
            required='COMPLETE original 18 requests, released, uniquely settled, accepted CPU scores; do not rescore/replay'),
        storage=dict(private_output_GiB=64,journal_MiB=48,RAM_GiB=40,swap_GiB=0,snapshot_logical_GiB=24,snapshot_CPU_GiB=16,
            minimum_output_free_bytes=4*2**30,max_concurrent_new_record_state_sets=1,
            retained_per_new_input_upper_bytes=407_000_000,peak_new_payload_upper_bytes=47_033_000_000+2*407_000_000+122*50_000_000,
            peak_calculation='one record 47.033GB + two retained 0.407GB sets + at most50MB per122 new requests; plus4GiB low water and ext4 overhead',
            old_read_only_image_GiB=256,total_old_plus_new_images_GiB=320,provisioned=False),quote=quote,
        ledger_snapshot=ledger['totals'],budget_calibration_r1_image_cleanup=deletion,
        output_root='/data20t/gaokuangda/worldcache_workspace/outputs/'+run,
        stage_root='/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-GPU-'+run[5:])
    del card['precheck']
    del card['scope_sha256']
    card['scope_sha256']=hashlib.sha256(json.dumps(card,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return card


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('measurement','backing-read','reuse-check','ledger','deletion','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();read=lambda path:json.loads(path.read_text())
    card=build(read(a.measurement)['measurement'],read(a.backing_read),read(a.reuse_check),read(a.ledger),read(a.deletion))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('x') as f:json.dump(card,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps(card['quote']['scenarios']))
