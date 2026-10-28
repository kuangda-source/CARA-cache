"""Freeze the original-host forensic scope; never stage or authorize a GPU."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
SCOPE = 'plans/cara_next_stage_20261028/sq/S_REUSE_CPU_R1.json'
AUDIT = 'reports/cara_sq_s_reuse_static_identity_r1_20261029.json'
TERMINAL = 'reports/cara_DEV128_A6000_terminal_20261027_0400.json'
ACCEPTED = 'reports/cara_DEV128_A6000_accepted_20261027_0404.json'
CHECKPOINT_PROOF = 'reports/cara_sq_q1_two_card_asset_cpu_terminal_r1_20261029.json'


def read(name):
    return json.loads((ROOT/name).read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    from wcomr.policy_generator_r1.interval_grammar import Profile
    from wcomr.sq_s_batch_r1 import make_scope
    if any((ROOT/name).exists() for name in (SCOPE, AUDIT)):
        raise FileExistsError('Preserve the original proposed CPU scope and static audit')
    value = read(TERMINAL)
    accepted = read(ACCEPTED)
    if (accepted['full_protocol_accepted'] is not True or accepted['capture_ref'] != TERMINAL
            or accepted['capture_sha256'] != sha(ROOT/TERMINAL)):
        raise ValueError('Original independent terminal acceptance differs')
    registration = json.loads(value['files']['registration']['raw_utf8'])
    original = value['requests']['DIAGNOSTIC_SHARED25_C_0_1']
    pp = read('plans/cara_next_stage_20261028/sq/S_SUPPORT_RECONCILIATION_R2.json')['profile']
    for key in ('protected_dense', 'alpha_candidates'):
        pp[key] = tuple(pp[key])
    proposed = make_scope(Profile(**pp))
    if original['policy'] != proposed['policies']['Shared25-C']:
        raise ValueError('Old and proposed parent policies differ')
    if value['payload_actual_sha256'] != registration['payload_sha256']:
        raise ValueError('Original terminal source identity differs')
    matched, changed = {}, {}
    for name, expected in registration['payload_sha256'].items():
        if name.startswith('src/wcomr/') and name.endswith('.py'):
            actual = sha(ROOT/name)
            if actual == expected:
                matched[name] = expected
            else:
                changed[name] = dict(original=expected, current=actual)
    # This sole change is in admission/context observation, outside sampling.
    if set(changed) != {'src/wcomr/policy_generator_r1/production_exclusive.py'}:
        raise ValueError('Review additional historical source changes before freezing reuse')
    current = {name: matched[name] for name in (
        'src/wcomr/policy_generator_r1/production_sampling.py',
        'src/wcomr/clean_speed20_r1.py', 'src/wcomr/cfg_guided_w1_forward.py',
        'src/wcomr/policy_interval_readout_r1.py', 'src/wcomr/h0_mode.py')}
    metadata = [dict(path=registration['stage']+'/registration.json',
                     bytes=value['files']['registration']['bytes'],
                     sha256=value['files']['registration']['sha256'])]
    for name in ('configs/f1_setup.json', 'configs/cara_DEV128_requests_r1_20261026.json'):
        if sha(ROOT/name) != registration['payload_sha256'][name]:
            raise ValueError('Old setup/request source changed: '+name)
        metadata.append(dict(path=registration['stage']+'/'+name,
                             bytes=(ROOT/name).stat().st_size,
                             sha256=registration['payload_sha256'][name]))
        current[name] = registration['payload_sha256'][name]
    checkpoint = read(CHECKPOINT_PROOF)['verification']
    weights = [dict(path=name, **record) for name, record in checkpoint['files'].items()
               if record['immutable_HF_link']]
    if len(weights) != 1:
        raise ValueError('Exactly one previously verified model checkpoint required')
    control = next(row for row in value['controls']
                   if row['right'] == original['slot']['id'])
    if not (control['latent_equal'] and control['RGB93_equal']):
        raise ValueError('Original lean/diagnostic equality control is absent')
    scope = dict(schema='SQ_S_ORIGINAL_HOST_REUSE_CPU_R1', host='two_card',
        purpose='Verify original files and bridge legacy/new tensor hashes; decode retained RGB only',
        legacy_terminal_ref=TERMINAL, legacy_terminal_sha256=sha(ROOT/TERMINAL),
        legacy_acceptance_ref=ACCEPTED, legacy_acceptance_sha256=sha(ROOT/ACCEPTED),
        original_source_revision=registration['source_revision'],
        original_GPU_UUID=value['launch']['gpu_uuid'],
        proposed_parent_policy=proposed['policies']['Shared25-C'],
        proposed_upper_scope_sha256=proposed['scope_sha256'],
        original_request=original, artifact_checks=value['artifact_checks'][original['slot']['id']],
        decoded_RGB93=control['right_rgb'], metadata_files=metadata,
        current_source_sha256=current, runtime_source_sha256=registration['runtime_source_sha256'],
        previously_verified_checkpoint=weights[0], checkpoint_proof_ref=CHECKPOINT_PROOF,
        checkpoint_proof_sha256=sha(ROOT/CHECKPOINT_PROOF),
        maximum_input_file_bytes=512*2**20, unit_controls=5,
        CPU_limits=dict(CPUs=2, RAM_bytes=8*2**30, wall_seconds=1800,
                        output_file_bytes=64*2**20, network='none', GPU='hidden'),
        GPU_authorized=False, GPU_submissions=0, S_labels_collected=0,
        new_ON_equivalence_accepted=False, physical_S_matrix_frozen=False)
    audit = dict(status='S_LEGACY_PARENT_POLICY_AND_NUMERICAL_SOURCE_MATCHED_PENDING_ORIGINAL_FILE_AUDIT',
        policy_exact_equal=True, original_policy_fingerprint=original['policy']['fingerprint'],
        unchanged_historical_wcomr_python_files=len(matched), unchanged_source_sha256=matched,
        changed_historical_sources=changed,
        changed_source_boundary='Admission/context observation only; not used to establish output parity',
        model_setup_and_AV28_request_bytes_unchanged=True,
        original_host_only=True, no_clean_timing_reuse=True,
        reused_artifacts_are_not_new_independent_samples=True,
        pending=['Read and SHA-check original files on the original host',
                 'Bridge complete36 guided and final latent; decode complete93 RGB',
                 'Bind the actual future S request/model/backend and compare new ON before acceptance',
                 'Freeze host-specific deduplicated physical matrix and complete quote'],
        scope_ref=SCOPE, GPU_submissions=0, ledger_writes=0)
    for name, record in ((SCOPE, scope), (AUDIT, audit)):
        with (ROOT/name).open('x') as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
            stream.write('\n')
    print(json.dumps(dict(status=audit['status'], matched_sources=len(matched), scope=SCOPE)))


if __name__ == '__main__':
    main()
