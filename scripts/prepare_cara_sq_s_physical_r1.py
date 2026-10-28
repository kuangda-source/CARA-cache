"""Bind original S inputs/model and prospective per-host physical matrices."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
DEST = 'plans/cara_next_stage_20261028/sq/'


def read(name):
    return json.loads((ROOT/name).read_text())


def sha(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def main():
    from wcomr.cara_fast_binding_r2 import load_card
    from wcomr.drop1_full18_r1 import MODE_REF
    from wcomr.policy_generator_r1.interval_grammar import Profile
    from wcomr.sq_s_batch_r1 import digest, make_scope, FIT
    from wcomr.sq_s_physical_r1 import make_physical_scope
    from four_card_policy_assets_port_r1 import reconstruct, IMAGE
    from wcomr.sq_q1_spec_r1 import CHECKPOINT_SHA
    names = [DEST+n for n in ('S_EXECUTION_IDENTITY_R1.json', 'S_RETAINED_OFF_WITNESS_R1.json',
                              'S_PHYSICAL_TWO_CARD_R1.json', 'S_PHYSICAL_FOUR_CARD_R1.json')]
    if any((ROOT/name).exists() for name in names):
        raise FileExistsError('Retain the original prospective execution and matrix bindings')
    card = load_card(ROOT, 'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
    inputs = [{k:v for k,v in row.items() if k != 'partition'} for row in card['inputs'] if row['name'] in FIT]
    if tuple(row['name'] for row in inputs) != FIT:
        raise ValueError('Keep both original exposed FIT requests in fixed order')
    prior = next(row for row in read('configs/cara_DEV128_requests_r1_20261026.json')['requests']
                 if row['name'] == FIT[0])
    if inputs[0] != prior:
        raise ValueError('Prospective AV28 request differs from the original retained OFF input')
    _, parent, *_ = reconstruct(ROOT)
    profile = read(DEST+'S_SUPPORT_RECONCILIATION_R2.json')['profile']
    for name in ('protected_dense', 'alpha_candidates'):
        profile[name] = tuple(profile[name])
    upper = make_scope(Profile(**profile))
    old = read(DEST+'S_REUSE_CPU_R1.json')
    if upper['policies']['Shared25-C'] != old['original_request']['policy']:
        raise ValueError('Retained OFF and new parent policies differ')
    identity = dict(schema='SQ_S_PROSPECTIVE_EXECUTION_IDENTITY_R1', inputs=inputs,
        original_mainline_input_scope_sha256=card['scope_sha256'],
        model_setup=read('configs/f1_setup.json'), setup_overrides=dict(keep_going=True, worldcache_enabled=True),
        historical_WC_settings=parent['historical_wc_settings'], expected_real_shape=parent['expected_real_shape'],
        primary_checkpoint_sha256=CHECKPOINT_SHA, image=IMAGE, torch_version='2.7.1+cu128',
        shared_eval_mode_ref=MODE_REF, shared_eval_mode_sha256=sha(MODE_REF),
        numerical_source_sha256=old['current_source_sha256'],
        runtime_source_sha256=old['runtime_source_sha256'],
        request_precision='Original pinned inference precision; capture actual backend flags at start',
        retained_OFF_host='two_card', retained_OFF_GPU_UUID=old['original_GPU_UUID'],
        hosts=dict(two_card=dict(architecture='SM86', device_class='RTX A6000'),
                   four_card=dict(architecture='SM89', device_class='RTX 6000 Ada')),
        auxiliary_model_assets_fresh_admission_still_required=True,
        full_video_evaluation=dict(protocol='Fidelity-v2', source='plans/cara_next_stage_20261028/01_Master_Experiment_Plan.md',
            source_sha256=sha('plans/cara_next_stage_20261028/01_Master_Experiment_Plan.md'),
            this_collection_role='Old FIT same-state labels and OFF/ON numerical controls only',
            future_S_END_requires_prospective_complete_video_scope=True), GPU_authorized=False)
    identity['identity_sha256'] = digest(identity)
    accepted_name = 'reports/cara_sq_s_reuse_two_card_cpu_accepted_r2_20261029.json'
    accepted = read(accepted_name)
    if not accepted['passed'] or sha(accepted['capture_ref']) != accepted['capture_sha256']:
        raise ValueError('Original independent file witness acceptance differs')
    capture = read(accepted['capture_ref'])
    if capture['result']['scope'] != old or capture['result']['decoded_RGB93'] != old['decoded_RGB93']:
        raise ValueError('Original accepted witness scope differs')
    result = capture['result']
    metadata = dict(status='COMPLETE', CPU_fixture=False, solver_steps=36,
        policy_fingerprint=upper['policies']['Shared25-C']['fingerprint'],
        guided=[row['S_typed_tensor'] for row in result['signatures']['guided']],
        final_latent=result['signatures']['final_latent']['S_typed_tensor'], RGB=result['decoded_RGB93'],
        semantic_actions=upper['policies']['Shared25-C']['actions'], S_rows=[],
        encoded_video=old['artifact_checks']['video_artifact'], diagnostic_only_no_clean_clock=True)
    witness = dict(schema='SQ_S_RETAINED_OFF_METADATA_R1', CPU_fixture=False,
        slot_id='p0-Shared25-C-OFF', original_host='two_card', old_bytes_verified=True,
        new_ON_equivalence_accepted=False, execution_identity_sha256=identity['identity_sha256'],
        source=dict(accepted_ref=accepted_name, accepted_sha256=sha(accepted_name),
            capture_ref=accepted['capture_ref'], capture_sha256=accepted['capture_sha256'],
            original_GPU_UUID=old['original_GPU_UUID'], original_files=result['files']), result=metadata)
    witness['witness_sha256'] = digest(witness)
    records = [identity, witness,
        make_physical_scope(upper, 'two_card', identity['identity_sha256'], witness),
        make_physical_scope(upper, 'four_card', identity['identity_sha256'])]
    for name, record in zip(names, records):
        with (ROOT/name).open('x') as stream:
            json.dump(record, stream, indent=2, allow_nan=False)
            stream.write('\n')
    print(json.dumps({host: records[i]['counts'] for host,i in [('two_card', 2), ('four_card', 3)]}))


if __name__ == '__main__':
    main()
