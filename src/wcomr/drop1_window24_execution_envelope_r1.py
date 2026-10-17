"""Exact whole-card authority and identity binding; no lock, process or GPU IO."""
from .drop1_window24_production_r1 import RUN, COUNTS
from .drop1_window24_cpu_acceptance_r1 import ACCEPTED_STATUS, validate_proof
from .frozen_shared_production_r1 import fingerprint


def input_fingerprint(config):
    return fingerprint(dict(requests=config['requests'], methods=config['methods'],
        plans=config['plans'], scope_counts=config['scope_counts'], references=config['references']))


def validate_authority(config, registration, proof, accepted, authority, *, source_revision,
                       gpu_uuid, registration_sha256, config_sha256, proof_sha256, accepted_sha256):
    validate_proof(proof, config, source_revision=source_revision,
        registration_sha256=registration_sha256, config_sha256=config_sha256)
    expected = dict(source_revision=source_revision, gpu_uuid=gpu_uuid, whole_card_run=RUN,
        registration_sha256=registration_sha256, config_sha256=config_sha256,
        production_CPU_sha256=proof_sha256, independent_CPU_acceptance_sha256=accepted_sha256,
        bound_input_fingerprint=input_fingerprint(config), scope_counts=COUNTS,
        forecast_complete_GPUh=config['forecast_complete_GPUh'], billed_limit_GPUh=config['billed_limit_GPUh'],
        cumulative_cap_GPUh=226, budget_origin_used_GPUh=79.99637737158223,
        autonomy_exclusive_upper_GPUh=12)
    kind = 'EXISTING_PLAN_UNDER12_AUTONOMY' if config['billed_limit_GPUh'] < 12 else 'SPECIFIC_WHOLE_CARD_APPROVAL'
    if (registration['source_revision'] != source_revision
            or accepted.get('status') != ACCEPTED_STATUS or accepted.get('CPU_accepted') is not True
            or any(accepted.get(k) != expected[k] for k in ('source_revision', 'registration_sha256',
                'config_sha256', 'production_CPU_sha256', 'scope_counts'))
            or any(authority.get(k) != v for k, v in expected.items())
            or authority.get('kind') != kind or authority.get('direct_user_authorization') is not True
            or not authority.get('user_reply_quote') or not authority.get('launch_id')):
        raise ValueError('Exact real CPU/source, whole24 budget and existing or specific human authority required')
    return expected
