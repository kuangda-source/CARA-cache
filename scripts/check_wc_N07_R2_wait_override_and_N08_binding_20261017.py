#!/usr/bin/env python3
"""CPU-only checks on the saved actual180 receipt; no SSH or model inference."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main():
    from wcomr.frozen_repair_acceptance_r2 import accept, accept_after_human_wait_override
    from wcomr.completed_shared_repair_binding_r2 import accepted_repair_identity
    raw = (ROOT / 'reports/wc_paper_N07_refusal_repair180_R2_terminal_collection_20261017_1250.json.gz').read_bytes()
    value = json.loads(gzip.decompress(raw))
    launch = value['launch']
    accepted = json.loads((ROOT / 'reports/wc_paper_N07_refusal_repair180_R2_terminal_canonical_independent_acceptance_20261017.json').read_text())
    authority = accepted['direct_human_waiting_override']
    checks = []

    def rejects(label, fn):
        try:
            fn()
        except ValueError:
            checks.append(label)
        else:
            raise AssertionError('Expected rejection: ' + label)

    rejects('old_ETA_guard_still_requires_explicit_new_authority', lambda: accept(value, launch))
    for key, bad in [('human_quote', 'untrusted alternative'), ('new_GPU_submissions', 1),
                     ('authorized_at_unix', value['observed_unix'] + 1),
                     ('launch_sha256', '0' * 64)]:
        altered = copy.deepcopy(authority)
        altered[key] = bad
        rejects('waiting_override_rejects_' + key,
            lambda a=altered: accept_after_human_wait_override(value, launch, a))

    altered = copy.deepcopy(value)
    altered['original_processes']['post_watcher_pid'] = {**launch['post_watcher_identity'], 'state': 'S'}
    result = accept_after_human_wait_override(altered, launch, authority)
    assert not result['scientific_full_scope_accepted'] and result['status'].endswith('NO_RESTART')
    checks.append('explicit_waiting_override_does_not_accept_live_CPU_post')
    for label, mutate in [
        ('complete180_denominator_preserved', lambda v: v['final']['rows'].pop()),
        ('additive_original_budget_still_checked', lambda v: v['pool'].update(used_gpu_hours=1.)),
        ('all93_frame_score_identity_still_checked', lambda v: next(r for r in v['final']['rows'] if 'LPIPS' in r)['LPIPS']['frame_distances'].pop())]:
        altered = copy.deepcopy(value)
        mutate(altered)
        rejects(label, lambda v=altered: accept_after_human_wait_override(v, launch, authority))

    shared_path = ROOT / 'configs/wc_paper_N07_frozen_shared_production_r1_20261016.json'
    identity = accepted_repair_identity(accepted, value, capture_sha256=hashlib.sha256(raw).hexdigest(),
        original_shared_config=json.loads(shared_path.read_text()),
        original_shared_config_sha256=hashlib.sha256(shared_path.read_bytes()).hexdigest())
    assert identity['actual_run_id'] == launch['run_id'] and identity['original_runner_paths'] == 180
    assert identity['original_status_counts']['TEXT_REJECTED'] == 20
    assert not identity['original_identity_relabelled'] and identity['no_new_GPU_permission']
    checks.append('actual_full_R2_N08_binding_recomputes_all_receipts_with_registered_missingness')
    output = ROOT / 'reports/wc_paper_N07_R2_wait_override_and_N08_binding_CPU_20261017.json'
    assert not output.exists()
    result = dict(status='ACTUAL_SAVED_R2_EARLY_ACCEPTANCE_AND_DOWNSTREAM_CPU_CHECKS_PASS',
        controls=len(checks), checks=checks, completed_N07_identity=identity,
        original_server_or_capture_modified=False, SSH_queries=0, GPU_submissions=0,
        generator_training=False, ledger_written=False)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
