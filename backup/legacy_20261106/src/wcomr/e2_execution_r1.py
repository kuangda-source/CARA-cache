"""Complete E2 wrapper identity, resource accounting and memory observation."""
import hashlib
import json
import math
import time
from pathlib import Path

CARD='WC-E2-PHASE-A-CONF40-TIMING32-PARITY4-R1-20261011-A'
RUN='wc-e2-phase-a-conf40-timing32-parity4-r1'
UUID='GPU-cebf7119-cf03-23b9-e192-cd196332b704'
COUNTS={'scientific_paths':72,'confirmation_paths':40,'timing_paths':32,'parity_paths':4,
        'complete_actual_GPU_paths':76,'solver_updates':2736,'CFG_calls':5472}
DYNAMIC={'GPU_execution_selected','gpu_uuid','production_cpu_receipt_sha256','single_job_exception_authority'}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for value in iter(lambda:f.read(4<<20),b''):h.update(value)
    return h.hexdigest()


def binding(c):
    return hashlib.sha256(json.dumps({k:v for k,v in c.items() if k not in DYNAMIC},
        sort_keys=True,separators=(',',':')).encode()).hexdigest()


def write(path,value):
    path=Path(path);temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temp.replace(path)


def validate_execution(c,p,stage):
    if (p['card']!=CARD or p['run_id']!=RUN or p['scope_counts']!=COUNTS
            or p['method_config_binding_sha256']!=binding(c)
            or p['method_payload_sha256']!=c['payload_sha256']
            or p['single_job_autonomy_GPUh']!=8 or p['maximum_available_pairs']!=68
            or p['maximum_confirmation_pairs']!=32 or p['frames_per_pair']!=93
            or p['GPU_execution_selected'] or p['method_CPU_capture_ref']!=
            'reports/wc_e2_production_cpu_r1_terminal_20261011_capture.json'):
        raise ValueError('Frozen full76 execution wrapper differs')
    for n,h in p['execution_payload_sha256'].items():
        if sha(Path(stage)/n)!=h:raise ValueError('Frozen execution/score source differs: '+n)
    proof=json.loads((Path(stage)/p['method_CPU_capture_ref']).read_text())
    if (proof['exit_code']!=0 or not proof['original_source_raw_identity_requests_and_scope_independently_verified']
            or proof['config_binding_sha256']!=binding(c) or proof['payload_files']!=231
            or proof['GPU_submissions'] or proof['ledger_written']):
        raise ValueError('Actual original production CPU evidence missing')
    return p


def admit(c,budget,gpu,selected_CPU,protocol_sha256):
    """Pure admission; method validate_selected verifies exact approval bytes."""
    if (not c['GPU_execution_selected'] or c['gpu_uuid']!=UUID or c['scope_counts']!=COUNTS
            or c['automatic_single_job_GPUh']!=8
            or budget['cap_gpu_hours']!=c['cumulative_cap_GPUh'] or any('inflight' in k for k in budget)
            or gpu['uuid']!=UUID or gpu['compute_cap']!='8.6' or gpu['pids'] or gpu['memory_used_mib']>1024
            or selected_CPU['status']!='E2_SELECTED_EXECUTION_CPU_PASS_NOT_GPU'
            or selected_CPU['exit_code']!=0 or selected_CPU['GPU_submissions']
            or selected_CPU['config_binding_sha256']!=binding(c)
            or selected_CPU['execution_protocol_sha256']!=protocol_sha256):
        raise ValueError('Fresh exact E2 GPU, source-bound selected CPU or budget admission differs')
    remaining=budget['cap_gpu_hours']-budget['used_gpu_hours'];forecast=c['forecast_complete_GPUh']
    if not math.isfinite(forecast) or not 0<forecast<=remaining:
        raise ValueError('Whole76 cost does not fit remaining budget')
    if forecast>8 and not isinstance(c['single_job_exception_authority'],dict):
        raise ValueError('Complete above8 E2 requires exact direct approval')
    return remaining,min(remaining,8.) if forecast<=8 else remaining


def instrument_save(state,save,sink,provider,reset,clock=time.time):
    """Metadata outside clocks; never mutate the frozen sampler's state."""
    begun=set();ended=set()
    def observe(row,event):
        try:
            if event=='BEGIN':reset()
            memory=provider()
        except (RuntimeError,OSError) as error:
            memory={'status':'MEMORY_OBSERVATION_UNAVAILABLE','error':str(error)}
        sink({'id':row['id'],'section':row['section'],'method':row['method'],
            'event':event,'status':row['status'],'observed_unix':clock(),'memory':memory})
    def wrapped():
        for row in state.get('slots',[]):
            if row['status']=='STARTED' and row['id'] not in begun:
                observe(row,'BEGIN');begun.add(row['id'])
            if row['status'] in ('COMPLETE_PATH','TEXT_REJECTED','VIDEO_REJECTED','TECH_BLOCKED') and row['id'] in begun and row['id'] not in ended:
                observe(row,'END');ended.add(row['id'])
        save()
    return wrapped
