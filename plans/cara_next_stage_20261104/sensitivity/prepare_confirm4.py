"""Frozen clean subset and measured whole-card quote; no remote operations."""
import copy
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TARGET=HERE/'f17_confirm4/manifest.json'

if __name__=='__main__':
    original=json.loads((HERE/'manifest.json').read_text())
    card=copy.deepcopy(original)
    rows=[copy.deepcopy(r) for r in original['matrix'] if r['section'] in ('warm','c')]
    for i,row in enumerate(rows,1):
        row['original_slot_id']=row['id'];row['id']=f'F17_{i:03d}'
    prices=original['quote']['measured_request_seconds']
    # Actual complete warm requests from the settled sensitivity8 collection.
    warm=[450.159909889102,223.38863776158541]
    clean=4*sum(prices[r] for r in ('NATIVE35','F17_A2_LIGHT_C','F19_A1','WC_T006'))
    raw=clean+sum(warm)
    quote=dict(basis='CAL35 accepted clean request means; sensitivity8 actual warm clocks; 10% variation plus 600s model/load and 600s release',
        clean_request_seconds={r:prices[r] for r in ('NATIVE35','F17_A2_LIGHT_C','F19_A1','WC_T006')},
        warm_request_seconds=warm,clean_GPUh=clean/3600,warm_GPUh=sum(warm)/3600,
        variation_GPUh=.1*raw/3600,model_load_GPUh=600/3600,release_margin_GPUh=600/3600,
        forecast_GPUh=(raw*1.1+1200)/3600,hard_GPUh=1.95,
        source_refs=['reports/cara_f19_speed190_complete_r1_20261103/complete_analysis.json',
                     'plans/cara_next_stage_20261104/sensitivity/RUN_HANDOFF.md'])
    run='cara-f17-confirm4-r1-20261104'
    names={r['member'] for r in rows}
    card.update(schema='CARA_F17_CONFIRM4_SUBSET_R1',run_id=run,stage_name='cara-budget-calibration-GPU-'+run[5:],
        phase='F17_SUBSET_APPROVED_IF_FORECAST_LT2',GPU_dispatch_ready=False,
        inputs=[r for r in original['inputs'] if r['name'] in names],matrix=rows,
        sensitivity_steps=[],counts=dict(a=0,b=0,c=16,warm=2,controls=0,total_requests=18,
            suffix_paired_calls=0,LPIPS_pairs=12,quality_positions=48),quote=quote,
        authority=dict(user_quote='先跑F17确认；18请求冻结子集，正式报价小于2GPUh时按原准入一次预留并启动',
            hard_GPUh=1.95,max_forecast_exclusive_GPUh=2,cap_increase_allowed=False,automatic_monitoring_allowed=False),
        storage=dict(private_output_GiB=16,journal_MiB=48,RAM_GiB=40,swap_GiB=0,
            note='MP4 and terminal latent only; no Native recording or state checkpoint saves'),
        original_sensitivity_scope_sha256=original['scope_sha256'],sensitivity_status='PENDING_NO_SUCCESSOR_AUTHORITY',
        output_root='/data20t/gaokuangda/worldcache_workspace/outputs/'+run,
        stage_root='/data20t/gaokuangda/worldcache_workspace/.sync/cara-budget-calibration-GPU-'+run[5:])
    del card['scope_sha256']
    card['scope_sha256']=hashlib.sha256(json.dumps(card,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    TARGET.parent.mkdir(exist_ok=True)
    with TARGET.open('x') as stream:json.dump(card,stream,indent=2,ensure_ascii=False);stream.write('\n')
    print(json.dumps(dict(run_id=run,quote=quote,scope_sha256=card['scope_sha256'])))
