"""Fresh whole-card permission/CPU/source/budget/device checks, no side effects."""
import math

from .p_acr_profile528_contract_r1 import CARD,COUNTS,require_new_GPU_permission


def verify_permission(c,permission,proof,reg,*,config_sha256,proof_sha256):
    require_new_GPU_permission(c,permission,proof)
    if (permission.get('config_sha256')!=config_sha256
            or permission.get('production_CPU_sha256')!=proof_sha256
            or permission.get('source_revision')!=reg['source_revision']
            or proof.get('source_revision')!=reg['source_revision']
            or proof.get('config_sha256')!=config_sha256
            or proof.get('exit_code')!=0 or proof.get('GPU_submissions')!=0
            or proof.get('CUDA_initialized') is not False or proof.get('weights_loaded')!=0
            or proof.get('launch_controls_accepted') is not True
            or proof.get('launcher_supervisor_post_paths_verified') is not True
            or not isinstance(permission.get('user_reply_quote'),str)
            or not permission['user_reply_quote'].strip()
            or not isinstance(permission.get('launch_id'),str) or not permission['launch_id']):
        raise ValueError('Exact source/config/production CPU and new human whole-card permission required')


def verify_admission(c,permission,ledger,gpu,uuid):
    def finite(value):
        return isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value)
    cap=ledger['cap_gpu_hours'];used=ledger['used_gpu_hours']
    if not finite(cap) or not finite(used):raise ValueError('Finite actual ledger required')
    remaining=cap-used
    if (used<0
            or cap!=c['cumulative_cap_GPUh'] or any('inflight' in name for name in ledger)
            or not 0<remaining<=48+1e-9 or c['forecast_complete_GPUh']>remaining
            or not isinstance(uuid,str) or not uuid.startswith('GPU-') or gpu['uuid']!=uuid
            or 'A6000' not in gpu['name'] or gpu['compute_cap']!='8.6'
            or not finite(gpu['memory_used_mib']) or not 0<=gpu['memory_used_mib']<=1024 or gpu['pids']):
        raise ValueError('Fresh locked PA budget/device admission unavailable')
    limit=permission.get('authorized_single_job_GPUh',8.)
    if (not finite(limit)
            or limit<c['forecast_complete_GPUh'] or limit>remaining
            or limit>8 and permission.get('specific_over8_exception') is not True):
        raise ValueError('Whole-card billed limit or specific over8 permission required')
    return remaining,float(limit)
