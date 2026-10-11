"""Post/selection bindings separate from unchanged accepted449 sampler payload."""
import gzip
import hashlib
import json
from pathlib import Path
from .e3_complete64_production_r1 import binding, sha, CARD, RUN, COUNTS

PROTOCOL='e3-execution-protocol.json'
PYTHON='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def validate_execution(c,p,stage):
    stage=Path(stage)
    if (p['card']!=CARD or p['run_id']!=RUN or p['scope_counts']!=COUNTS
            or p['method_binding_sha256']!=binding(c)
            or p['method_payload_sha256']!=c['payload_sha256']
            or not p['score_valid_prefix_even_whole_card_failed'] or p['training'] or p['human_review']
            or p['clean_speed_claim'] or p['metric_frames']!=93
            or p['above8_requires_exact_full_card_approval'] is not True):
        raise ValueError('E3 full64 post/selection execution contract differs')
    for n,h in p['execution_payload_sha256'].items():
        if sha(stage/n)!=h:raise ValueError('E3 post/selection source changed: '+n)
    capture=json.loads((stage/p['production_capture_ref']).read_text())
    if (sha(stage/p['production_capture_ref'])!=p['production_capture_sha256'] or capture['exit_code']!=0
            or not capture['original_source_actual_entry_contract_and_wrapper_independently_verified']):
        raise ValueError('Actual accepted full20 production CPU source proof required')
    item=capture['files']['production-CPU-receipt.json']
    raw=gzip.decompress((stage/item['local_path']).read_bytes())
    if len(raw)!=item['bytes'] or hashlib.sha256(raw).hexdigest()!=item['sha256']:
        raise ValueError('Original full20 production CPU receipt changed')
    r=json.loads(raw)
    if (r['exit_code']!=0 or r['payload_after_sha256']!=c['payload_sha256']
            or r['config_binding_sha256']!=binding(c) or r['CUDA_initialized']
            or r['GPU_submissions'] or r['ledger_written']):
        raise ValueError('Original accepted449 production CPU receipt differs')
    return r


def validate_post_proof(c,p,stage):
    stage=Path(stage);r=json.loads((stage/'execution-CPU-receipt.json').read_text())
    if (r['status']!='E3_COMPLETE64_POST_SELECTION_ACTUAL_CPU_PASS_NOT_GPU' or r['exit_code']!=0
            or r['method_binding_sha256']!=binding(c) or r['protocol_sha256']!=sha(stage/PROTOCOL)
            or r['method_payload_after_sha256']!=c['payload_sha256']
            or r['execution_payload_after_sha256']!=p['execution_payload_sha256']
            or r['CUDA_initialized'] or r['GPU_submissions'] or r['ledger_written']
            or r['actual_reuse_reader']['validated_original_paths']!=10
            or r['actual_reuse_reader']['actual_tensors_reloaded']!=370):
        raise ValueError('Exact post/selection CPU proof required')
    return r


def exact_authorization(c,approved):
    if (not approved['direct_user_authorization'] or approved['card']!=CARD or approved['run_id']!=RUN
            or approved['scope_counts']!=COUNTS or approved['config_binding_sha256']!=binding(c)
            or approved['forecast_complete_GPUh']!=c['forecast_complete_GPUh']):
        raise ValueError('Exact full64/54fresh/20load above8 direct approval required')


def original_gone(supervisor, pid, exists):
    if (supervisor['pid']!=pid or supervisor['run_id']!=RUN
            or supervisor['status']!='E3_COMPLETE64_EXITED_REQUIRES_COMPLETE_SCOPE_RAW_CPU_AUDIT'
            or exists(pid) or any(exists(b['pid']) for b in supervisor['blocks'] if 'pid' in b)
            or 'wc_e3_complete64_inflight' in supervisor['budget_after']):
        raise ValueError('Original E3 GPU supervisor/children must exit and settle before CPU')
    return True
