"""Complete collection identity after original financial and resource closure.

The collection gate is not an artifact/RGB gate or scoring authorization.
Failed technical runs remain eligible for their original financial settlement.
"""
from pathlib import Path

from .cara_fast_spec_r1 import digest
from .cara_s_endpoint_lifecycle_r1 import released_lifecycle
from .cara_s_uniform_endpoint_execution_r1 import check_collection
from .gpu_budget_pool_v2 import sha
from .policy_price_terminal_r1 import record, require

SOURCE = 'src/wcomr/cara_s_endpoint_release_r1.py'
EXECUTION_SOURCE = 'src/wcomr/cara_s_uniform_endpoint_execution_r1.py'
CARD = 'configs/cara_endpoint_request_card.json'
BINDING = 'configs/cara_endpoint_frozen_binding.json'


def released_collection(capture, expected_launch_sha256, settlement, card, bound, *, cpu_validation=False):
    # No collection or scientific artifacts are opened before original closure.
    release = released_lifecycle(capture, expected_launch_sha256, settlement, cpu_validation=cpu_validation)
    require(release['container_exit_success'], 'Original successful settled release required before collection read')
    launch = record(capture, 'launch')
    registration = record(capture, 'registration')
    authority = record(capture, 'authorization')
    require(launch['host'] == 'two_card' and launch['scope_sha256'] == card['scope_sha256']
            and card['scope_sha256'] == digest({k: v for k, v in card.items() if k != 'scope_sha256'})
            and card['CPU_fixture_only'] is bound['CPU_fixture_only'] is cpu_validation
            and card['schema'] == 'CARA_SU19_BUDGET_ENDPOINT_REQUEST_CARD_R1'
            and card['endpoint_binding_sha256'] == bound['binding_sha256']
            and bound['binding_sha256'] == digest({k: v for k, v in bound.items() if k != 'binding_sha256'}),
            'Original endpoint card/binding/host identity differs')
    require(authority['new_endpoint_authorization'] is True
            and authority['card_kind'] == 'CARA_SU19_BUDGET_ENDPOINT'
            and authority['physical_paths'] == launch['physical_paths'] == len(card['physical_matrix'])
            and authority['endpoint_binding_sha256'] == launch['endpoint_binding_sha256'] == bound['binding_sha256']
            and authority['original_budget_freeze_sha256'] == launch['original_budget_freeze_sha256']
            == card['original_budget_freeze_sha256'] == bound['original_freeze_sha256']
            and launch['launch_id'] != bound['original_calibration']['launch_id'],
            'Separate new endpoint authority and original budget freeze required')
    require(record(capture, 'endpoint_card') == card and record(capture, 'endpoint_binding') == bound
            and capture['files']['endpoint_card']['sha256'] == registration['payload_sha256'][CARD]
            and capture['files']['endpoint_binding']['sha256'] == registration['payload_sha256'][BINDING]
            and registration['payload_sha256'][SOURCE] == sha(__file__)
            and registration['payload_sha256'][EXECUTION_SOURCE] == sha(Path(__file__).with_name('cara_s_uniform_endpoint_execution_r1.py')),
            'Original registered endpoint manifests or reader source differs')
    collection = record(capture, 'collection')
    collection_digest = check_collection(card, collection, cpu_validation=cpu_validation)
    require(record(capture, 'runner_terminal')['collection_sha256'] == collection_digest
            and record(capture, 'runner_terminal')['scope_sha256'] == card['scope_sha256'],
            'Original runner collection digest differs')
    return dict(status='COMPLETE_ENDPOINT_COLLECTION_RELEASED_ARTIFACT_ACCEPTANCE_PENDING',
        run_id=launch['run_id'], launch_id=launch['launch_id'], scope_sha256=card['scope_sha256'],
        source_revision=launch['source_revision'], original_launch_sha256=expected_launch_sha256,
        endpoint_binding_sha256=bound['binding_sha256'], original_budget_freeze_sha256=bound['original_freeze_sha256'],
        collection_sha256=collection_digest, lifecycle=release, physical_paths=len(collection['rows']),
        CPU_fixture_only=cpu_validation, new_GPU_authority=False, ledger_written=False, GPU_submissions=0,
        artifact_identity_accepted=False, scientific_accepted=False, scoring_dispatch_allowed=False)
