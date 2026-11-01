"""Compose saved CPU/storage receipts; no server, GPU or ledger access."""
import hashlib
import json
from pathlib import Path
import time

from wcomr.cara_budget_host_policy_r1 import POLICY_SHA256
from wcomr.cara_read_write_runner_binding_r1 import CARD, REQUIRED, validate_profile, PROFILE
from wcomr.cara_read_write_dispatch_r1 import REQUIRED as DISPATCH
from wcomr.cara_s_endpoint_guardian_journal_r1 import encoded_sha

ROOT = Path(__file__).resolve().parents[1]


def main():
    read = lambda p:json.loads((ROOT/p).read_text())
    sha = lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    base = ROOT/'plans/cara_next_stage_20261101/read_write'
    destinations = [ROOT/'reports/cara_read_write_storage_accepted_r1_20261101.json',
        ROOT/'reports/cara_read_write_whole_CPU_accepted_r1_20261101.json', base/'M1_FULL14_WHOLE_QUOTE_R3.json']
    assert not any(p.exists() for p in destinations)
    entry_ref = 'reports/cara_read_write_entry_Linux_CPU_accepted_r1_20261101.json'
    accepted = read(entry_ref)
    capture = read(accepted['capture_ref'])
    assert sha(accepted['capture_ref']) == accepted['capture_sha256'] and capture['exit_code'] == 0
    cap = capture['result']
    reg = cap['registration']
    assert accepted['status'] == 'ORIGINAL_M1_ENTRY_LOADED_AND_REAL8_SCORER_LINUX_CPU_ACCEPTED'
    assert accepted['tests_run'] == 67 and cap['container_state']['ExitCode'] == 0
    assert encoded_sha(reg) == accepted['registration_sha256']
    for p in set(REQUIRED+DISPATCH):
        assert reg['payload_sha256'][p] == sha(p), p
    guardian_ref = 'reports/cara_s_endpoint_guardian_CPU_accepted_r2_20261031.json'
    guardian = read(guardian_ref)
    assert sha(guardian['capture_ref']) == guardian['capture_sha256']
    old = read(guardian['capture_ref'])['result']['registration']['payload_sha256']
    common = ('src/wcomr/cara_s_endpoint_host_guardian_r1.py', 'src/wcomr/cara_s_endpoint_supervisor_r1.py',
        'src/wcomr/cara_s_endpoint_guardian_journal_r1.py', 'scripts/cara_budget_process_bootstrap_r1.py')
    assert all(old[p] == reg['payload_sha256'][p] == sha(p) for p in common)
    evidence = {entry_ref:sha(entry_ref), guardian_ref:sha(guardian_ref)}
    for p in ('reports/cara_read_write_Linux_CPU_accepted_r2_20261101.json',
              'reports/cara_read_write_collection14_Linux_CPU_accepted_r1_20261101.json'):
        receipt = read(p)
        assert receipt['GPU_submissions'] == 0 and receipt['container_state']['ExitCode'] == 0
        assert sha(receipt['capture_ref']) == receipt['capture_sha256']
        evidence[p] = sha(p)
    stored_ref = 'reports/cara_read_write_storage_capture_r1_20261101.json'
    stored_capture = read(stored_ref)
    assert stored_capture['exit_code'] == 0
    stored = stored_capture['result']
    result = stored['state']['result']
    original = stored['launch']
    assert stored['observation']['original_live'] is False and stored['operator_intact']
    assert stored['state']['identity'] == original['identity']
    assert stored['state']['status'] == result['status'] == 'TWO_CARD_PRIVATE16_STORAGE_PROVISIONED_NO_GPU'
    assert original['operator_sha256'] == result['operator_sha256'] == sha('scripts/provision_cara_read_write_storage_r1.py')
    config = result['storage_contract']
    card, profile = read(CARD), read(PROFILE)
    validate_profile(profile, card['scope_sha256'])
    assert config['run_id'] == 'cara-read-write-M1-full14-r1-20261101'
    assert config['image_bytes'] == 16*2**30 and config['journal_bytes'] == 48*2**20
    for key in ('minimum_output_free_bytes','minimum_host_free_bytes','minimum_free_inodes'):
        assert config[key] == profile['storage'][key]
    observed = stored['independent_storage_observation']
    assert observed['journal_pristine'] and observed['output_children'] == []
    assert observed['image_allocated_bytes'] >= config['image_bytes'] and observed['journal_allocated_bytes'] >= config['journal_bytes']
    assert result['persistence_probe_bytes'] == 2**20 and result['persistence_probe_removed']
    storage = dict(status='ORIGINAL_M1_PRIVATE16_STORAGE_ACCEPTED_NO_GPU', observed_unix=time.time(),
        capture_ref=stored_ref, capture_sha256=sha(stored_ref), original_identity=original['identity'],
        source_revision=original['source_revision'], operator_sha256=original['operator_sha256'],
        provision_sha256=observed['provision_sha256'], storage_contract=config,
        original_process_exited=True, journal_pristine=True, output_empty=True,
        persistence_probe_bytes=result['persistence_probe_bytes'], persistence_probe_sha256=result['persistence_probe_sha256'],
        new_volume_full93_IO_remeasured=False, original_full93_IO_component_reused=True,
        GPU_submissions=0, ledger_written=False)
    proof = dict(status='M1_COMPOSED_SOURCE_BOUND_WHOLE_CPU_PREPARATION_ACCEPTED_NOT_GPU_ADMISSION',
        observed_unix=time.time(), passed=True, whole_card_CPU_accepted=True, host='two_card',
        source_revision=accepted['source_revision'], scope_sha256=card['scope_sha256'],
        payload_sha256=reg['payload_sha256'], runtime_source_sha256=reg['runtime_source_sha256'],
        execution_host_policy_sha256=POLICY_SHA256, required_hosts=['two_card'],
        required_host_whole_card_CPU_accepted=True, actual_module_full14_accepted=True,
        loaded_runner_accepted=True, dispatch_finance_release_accepted=True, postrelease_eight_pair_scorer_accepted=True,
        evidence_sha256=evidence, reused_guardian_source_sha256={p:old[p] for p in common},
        source_registration_sha256=accepted['registration_sha256'],
        physical_paths=14, physical_model_pairs=512, new_scoring_pairs=8, tests_run=67,
        actual_new_private16_storage_accepted=True, real_Docker_GPU_lifecycle_exercised=False,
        GPU_model_execution_exercised=False, real_model_VJP=False, scientific_accepted=False,
        execution_authorized=False, GPU_dispatch_ready=False, GPU_submissions=0, ledger_written=False,
        four_card_contacted=False)
    quote = read('plans/cara_next_stage_20261101/read_write/M1_FULL14_WHOLE_QUOTE_DRAFT_R2.json')
    quote.update(schema='CARA_READ_WRITE_FULL14_WHOLE_QUOTE_R3',
        status='COMPLETE_PREPARATION_QUOTE_FRESH_GPU_AND_CENTRAL_ADMISSION_PENDING',
        hard_GPUh=quote['proposed_hard_GPUh'], whole_quote_accepted=True,
        execution_host_policy_sha256=POLICY_SHA256,
        entry_CPU_accepted_ref=entry_ref, entry_CPU_accepted_sha256=sha(entry_ref),
        storage_accepted_ref=str(destinations[0].relative_to(ROOT)), snapshot_allowance_still_forecast=True)
    assert abs(sum(quote['components_seconds'].values())/3600-quote['forecast_GPUh']) < 1e-9
    for path, value in zip(destinations, (storage, proof, quote)):
        with path.open('x') as stream:
            json.dump(value, stream, indent=2, allow_nan=False)
            stream.write('\n')
    print(json.dumps(dict(status=proof['status'], source_revision=proof['source_revision'],
        forecast_GPUh=quote['forecast_GPUh'], hard_GPUh=quote['hard_GPUh'], GPU_submissions=0)))


if __name__ == '__main__':
    main()
