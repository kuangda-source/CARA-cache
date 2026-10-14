"""CPU-only whole W3 raw/parent audit after the original GPU handle exits.

This label card has no new Native paths. RGB comparisons establish unchanged
H1 parent controls; they never establish the endpoint of a learned W3 policy.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

SCOPE='manifests/wc_w3_label64_parent18_full864_scope_r1_20261015.json'
REQUESTS='configs/wc_w3_expl_dev8_requests_r1_20261015.jsonl'
CLOCK='reports/wc_w3_actual_schedule_native_CPU_replay_20261015.json'
BASE_CONFIG='configs/wc_p_acr_local12_profile528_production_r1_20261015.json'
RUN='wc-w3-label-expldev8-parent18-local64-full864-r1'


def main():
    p=argparse.ArgumentParser()
    for name in ('project','stage','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();os.environ.update(CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',OMP_NUM_THREADS='2')
    sys.path.insert(0,str(a.stage/'src'))
    import torch
    torch.set_num_threads(2);assert not torch.cuda.is_initialized()
    def forbidden(*args,**kwargs):raise RuntimeError('W3 raw CPU audit forbids CUDA/downloads')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    from wcomr.w3_label64_fullpost_r1 import audit_all
    from wcomr.rv0_video_reader import probe_video,decoded_video
    from wcomr.p_acr_profile528_production_r1 import sha,write
    reg=json.loads((a.stage/'registration.json').read_text())
    assert not a.output.exists()
    assert all(sha(a.stage/n)==h for n,h in reg['payload_sha256'].items())
    for name in (SCOPE,REQUESTS,CLOCK,BASE_CONFIG):assert sha(a.stage/name)==reg['payload_sha256'][name]
    scope=json.loads((a.stage/SCOPE).read_text());counts=scope['scope_counts']
    assert counts['full_paths']==18 and counts['all_origins']==72 and counts['complete_pairs']==864
    root=(a.project/'outputs'/RUN).resolve();supervisor=json.loads((root/'supervisor.json').read_text())
    assert supervisor['status']=='W3_LABEL64_GPU_EXITED_REQUIRES_FULL_RAW_CPU_AUDIT'
    for key in ('pid','child_pid'):assert not Path('/proc/'+str(supervisor[key])).exists()
    runner_path=root/'runner.json';assert sha(runner_path)==supervisor['runner_sha256']
    runner=json.loads(runner_path.read_text())
    assert runner['source_revision']==reg['source_revision'] and runner['scope_counts']==counts
    before=sha(a.project/'reports/budget.json');start=time.perf_counter()
    def asset_path(asset):
        path=Path(asset['path']).resolve()
        if (str(path)!=asset['path'] or not path.is_relative_to(root) or not path.is_file()
                or sha(path)!=asset['sha256'] or path.stat().st_size!=asset['bytes']):
            raise ValueError('Actual immutable W3 asset path/hash/bytes differ')
        return path
    def load(asset):return torch.load(asset_path(asset),weights_only=True,map_location='cpu')
    def video(row):
        path=asset_path(row['video_artifact']);metadata=probe_video(path)
        digest=hashlib.sha256();n=0
        with decoded_video(path) as frames:
            for frame,pts,timebase in frames:digest.update(frame.tobytes());n+=1
        if n!=93:raise ValueError('Complete native93 decode required')
        return {**metadata,'RGB_sha256':digest.hexdigest(),'artifact':row['video_artifact']}
    requests=[json.loads(line) for line in (a.stage/REQUESTS).read_text().splitlines()]
    expected=json.loads((a.stage/BASE_CONFIG).read_text())['expected_real_shape']
    clock=json.loads((a.stage/CLOCK).read_text())['result']
    result={'status':'W3_FULL_RAW_CPU_AUDIT_RUNNING','GPU_submissions':0,'source_revision':reg['source_revision'],
        'scope_counts':counts,'GPU_supervisor':supervisor,'budget_before_sha256':before,
        'method_endpoint_or_speed_claim':False,'new_Native_reference_paths':0}
    write(a.output,result)
    try:
        report=audit_all(runner['runs'],requests,clock=clock,expected_shape=expected,
            load_raw=load,read_video=video,provenance='REAL_SAME_STATE_POST_RF')
        result.update(report)
    except BaseException as error:
        result.update(status='W3_FULL_RAW_CPU_TECH_FAILURE_ALL_DENOMINATORS_RETAINED',
            error_type=type(error).__name__,error=str(error),original_runner_retained=str(runner_path),
            planned_parent_denominator=18,planned_formal_label_denominator=64,planned_warmup_label_denominator=8)
        raise
    finally:
        result.update(CPU_wall_seconds=time.perf_counter()-start,budget_after_sha256=sha(a.project/'reports/budget.json'),
            CUDA_initialized=torch.cuda.is_initialized())
        if result['budget_after_sha256']!=before:raise ValueError('Read-only W3 post changed the budget ledger')
        write(a.output,result)


if __name__=='__main__':main()
