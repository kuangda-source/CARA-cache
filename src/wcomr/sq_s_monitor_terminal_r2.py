"""Stream the original long S monitor without importing Torch or copying it."""
import hashlib
import json
import math
from pathlib import Path

from .gpu_budget_pool_v2 import finite,sha
from .policy_asset_price_review_r1 import exclusive_gate
from .sq_s_data_terminal_r2 import require,digest as data_digest
from .sq_s_spec_r2 import RUN


def check_monitor(path,launch,supervisor,inner,ready,grant,*,maximum_bytes):
    path=Path(path);before=path.stat()
    require(not path.is_symlink() and path.is_file() and 0<before.st_size<=maximum_bytes<=512*2**20,
        'Original bounded S monitor file required')
    runner=supervisor['child_identity']
    require(ready['identity']==grant['runner']==runner and ready['GPU_context_held'] is True
        and grant['gpu_uuid']==launch['gpu_uuid']
        and grant['source_revision']==ready['source_revision']==launch['source_revision'],
        'Original S sole-runner context grant differs')
    active=False;last=0.;maximum_gap=maximum_temperature=0.;count=0;digest=hashlib.sha256()
    with path.open('rb') as stream:
        while True:
            raw=stream.readline(65537)
            if not raw:break
            require(len(raw)<=65536 and raw.endswith(b'\n'),'Incomplete or oversized S monitor sample')
            digest.update(raw);row=json.loads(raw);count+=1
            elapsed=row['monotonic_elapsed'];gap=elapsed-last
            require(finite(elapsed) and 0<=gap<=45,'Interrupted or reversed original S monitoring')
            last=elapsed;maximum_gap=max(maximum_gap,gap)
            require(row['run_id']==launch['run_id']==RUN and row['launch_id']==launch['launch_id']
                and row['runner']==runner and type(row['context_granted']) is bool
                and (not active or row['context_granted']),'Mixed original S monitor or regressed context grant')
            active=active or row['context_granted'];snapshot=row['snapshot']
            require(exclusive_gate(snapshot,gpu_uuid=launch['gpu_uuid'],
                phase='active' if active or snapshot['compute_apps'] else 'idle',runner=runner,
                now=snapshot['observed_unix'])['observation_passed'],'Foreign or unknown original S GPU context')
            temperature=float(row['thermal']['temperature.gpu'])
            require(math.isfinite(temperature) and 0<=temperature<90,'Original S thermal stop or invalid sample')
            thermal_time=row['thermal_monotonic']
            require(finite(thermal_time) and abs(inner['started_monotonic']+elapsed-thermal_time)<=45,
                'Original S thermal observation is stale')
            maximum_temperature=max(maximum_temperature,temperature)
    after=path.stat();stamp=lambda stat:[stat.st_dev,stat.st_ino,stat.st_size,stat.st_mtime_ns,stat.st_ctime_ns]
    require(stamp(before)==stamp(after) and count==supervisor['observations'] and count>0
        and active and 0<=inner['wall_seconds']-last<=45,'Original full S monitor changed or missed its terminal interval')
    return dict(status='S_ORIGINAL_FULL_MONITOR_PASS',accepted=True,path=str(path),bytes=after.st_size,
        sha256=digest.hexdigest(),file_identity=stamp(after),samples=count,max_monitor_gap_seconds=maximum_gap,
        max_temperature_C=maximum_temperature,last_elapsed_seconds=last,runner=runner,
        launch_id=launch['launch_id'],source_revision=launch['source_revision'],
        input_sha256={key:data_digest(value) for key,value in dict(launch=launch,supervisor=supervisor,
            inner=inner,ready=ready,grant=grant).items()},
        validator_sha256=sha(__file__),raw_monitor_transferred=False)
