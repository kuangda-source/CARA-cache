"""Frozen method proofs and separate complete post/selection source binding."""
import gzip
import hashlib
import json
from pathlib import Path

from .p_reference_same_state_production_r1 import CARD, RUN, COUNTS, binding, sha

PROTOCOL = 'p-reference-execution-protocol.json'
PYTHON = '/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'


def exact_authorization(c, approval):
    if (not approval['direct_user_authorization'] or approval['card'] != CARD
            or approval['run_id'] != RUN or approval['scope_counts'] != COUNTS
            or approval['config_binding_sha256'] != binding(c)
            or approval['forecast_complete_GPUh'] != c['forecast_complete_GPUh']):
        raise ValueError('Exact whole two-flow P-reference above8 approval required')


def validate_execution(c, p, stage):
    stage = Path(stage)
    if (p['card'] != CARD or p['run_id'] != RUN or p['scope_counts'] != COUNTS
            or p['method_binding_sha256'] != binding(c) or p['method_payload_sha256'] != c['payload_sha256']
            or not p['retain_complete_denominators_after_any_failure']
            or not p['read_all_available_point_and_video_artifacts']
            or p['training'] or p['human_review'] or p['quality_or_clean_speed_claim']
            or p['parent_video_frames'] != 93 or not p['above8_requires_exact_full_card_approval']):
        raise ValueError('Exact P-reference complete execution contract differs')
    for n, h in p['execution_payload_sha256'].items():
        if sha(stage/n) != h: raise ValueError('P-reference execution source changed: '+n)
    capture = json.loads((stage/p['production_capture_ref']).read_text())
    if (sha(stage/p['production_capture_ref']) != p['production_capture_sha256']
            or capture['status'] != 'P_REFERENCE_TWO_FLOW_ACTUAL_PRODUCTION_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU'
            or capture['complete_frozen_files_unchanged'] != 459
            or capture['contract_refusals'] != 20 or capture['admission_refusals'] != 9):
        raise ValueError('Actual original accepted459 two-entry CPU proof required')
    item = capture['originals']['production-CPU-receipt.json']
    raw = gzip.decompress((stage/item['local_path']).read_bytes())
    if len(raw) != item['bytes'] or hashlib.sha256(raw).hexdigest() != item['sha256']:
        raise ValueError('Original complete production CPU receipt changed')
    r = json.loads(raw)
    if (r['exit_code'] != 0 or r['child_exit_codes'] != [0, 0]
            or r['config_binding_sha256'] != binding(c) or r['payload_after_sha256'] != c['payload_sha256']
            or r['CUDA_initialized'] or r['GPU_submissions'] or r['ledger_written']):
        raise ValueError('Original actual complete production CPU proof differs')
    return r


def validate_post_proof(c, p, stage):
    stage = Path(stage); r = json.loads((stage/'execution-CPU-receipt.json').read_text())
    if (r['status'] != 'P_REFERENCE_COMPLETE_EXECUTION_CPU_PASS_NOT_GPU' or r['exit_code'] != 0
            or r['method_binding_sha256'] != binding(c) or r['protocol_sha256'] != sha(stage/PROTOCOL)
            or r['method_payload_after_sha256'] != c['payload_sha256']
            or r['execution_payload_after_sha256'] != p['execution_payload_sha256']
            or r['actual_reader']['files'] != 88 or r['actual_reader']['tensors'] != 1160
            or r['actual_reader']['direct_comparisons'] != 420 or r['actual_reader']['points'] != 48
            or r['actual_reader']['actual_old_GPU_video_frames_decoded'] != 372
            or r['CUDA_initialized'] or r['GPU_submissions'] or r['ledger_written']):
        raise ValueError('Exact complete post/selection CPU proof required')
    return r
