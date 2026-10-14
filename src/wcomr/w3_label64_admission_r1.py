"""No-side-effect exact whole W3 permission and fresh device/budget admission."""
from .w3_label64_production_contract_r1 import CAP,require_new_permission
from .p_acr_profile528_admission_r1 import verify_admission as original_fresh_admission


def verify_permission(scope,permission,proof,reg,*,scope_sha256,proof_sha256):
    require_new_permission(scope,permission,proof,source_revision=reg['source_revision'],scope_sha256=scope_sha256)
    if (permission.get('production_CPU_sha256')!=proof_sha256
            or proof.get('scope_sha256')!=scope_sha256 or proof.get('exit_code')!=0
            or proof.get('GPU_submissions')!=0 or proof.get('CUDA_initialized') is not False
            or proof.get('weights_loaded')!=0 or proof.get('launch_controls_accepted') is not True
            or proof.get('launcher_supervisor_post_paths_verified') is not True
            or not isinstance(permission.get('user_reply_quote'),str) or not permission['user_reply_quote'].strip()
            or not isinstance(permission.get('launch_id'),str) or not permission['launch_id']):
        raise ValueError('Exact full W3 source/scope/CPU and new human card authorization required')


def verify_admission(scope,permission,proof,ledger,gpu,uuid):
    if permission.get('authorized_single_job_GPUh') is None:
        raise ValueError('Explicit whole W3 billed limit required, no implicit under8 launch')
    c={'cumulative_cap_GPUh':CAP,'forecast_complete_GPUh':proof['forecast_complete_GPUh']}
    p={**permission,'specific_over8_exception':permission.get('explicit_strictly_over8_GPUh_whole_card_approved') is True}
    try:return original_fresh_admission(c,p,ledger,gpu,uuid)
    except ValueError as error:raise ValueError('Fresh whole W3 admission refused: '+str(error)) from error
