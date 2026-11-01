"""Full14 postrelease identity controls and the sole eight-pair score packet."""
import copy
import json
from pathlib import Path

from .cara_fast_fidelity_r1 import file_sha
from .cara_fast_scoring_manifest_r2 import comparison_input_digest, validate_pair_identities
from .cara_fast_spec_r1 import digest
from .cara_read_write_plan_r1 import validate
from .cara_read_write_runner_binding_r1 import CARD, PRECISION, GEOMETRY
from .cara_s_endpoint_artifacts_r1 import decode_video, verify_file
from .cara_s_endpoint_lifecycle_r1 import released_lifecycle
from .policy_price_terminal_r1 import record, require

SOURCE = 'src/wcomr/cara_read_write_artifacts_r1.py'
PROTOCOL = 'plans/cara_next_stage_20261028/mainline/FIDELITY_PROTOCOL.json'
ASSETS = 'plans/cara_next_stage_20261028/mainline/r2/B36_FROZEN_ASSETS_R1.json'
READ_ROLES = ('RW00', 'RW10', 'RW01', 'RW11')


def check_collection(card, collection, *, cpu_validation=False):
    validate(card)
    require(collection['scope_sha256'] == card['scope_sha256']
        and collection['status'] == 'COMPLETE14_PENDING_RELEASE_NOT_SCORED'
        and collection['physical_model_pairs'] == 512 and collection['scientific_score_pairs'] == 8
        and collection['diagnostic_timing_only'] is True and collection['scientific_accepted'] is False
        and [r['slot'] for r in collection['rows']] == card['physical_matrix'],
        'Exact complete14 ordered unscored M1 collection required')
    for row in collection['rows']:
        slot, result = row['slot'], row['result']
        require(row['status'] == result['status'] == 'COMPLETE'
            and result['scope_sha256'] == card['scope_sha256']
            and result['CPU_fixture_only'] is cpu_validation
            and result['slot_id'] == slot['id'] and result['role'] == slot['role']
            and result['member'] == slot['member']
            and result['solver_steps'] == result['guided_pairs'] == 36
            and result['physical_model_pairs'] == card['roles'][slot['role']]['physical_pairs'],
            'Every original M1 slot must have its complete paid denominator')
        if slot['role'].startswith('RW'):
            intervention = result['intervention']
            require(intervention['corner'] == slot['role'][2:], 'Original four-corner identity differs')
        if slot['role'] != 'NATIVE35':
            expected = card['roles'][slot['role']]['policy']['actions'].copy()
            if slot['role'].startswith('RW'):
                expected[7] = 'D' if slot['role'][-1] == '1' else 'C'
            require([h['actual'] for h in result['semantic_history']] == expected
                and all(h['fallback_reason'] is None for h in result['semantic_history']),
                'M1 left its frozen current write/future policy')
    for member in card['FIT']:
        parents = {r['result']['intervention']['parent_state_sha256'] for r in collection['rows']
            if r['slot']['member'] == member and r['slot']['role'].startswith('RW')}
        require(len(parents) == 1, 'All four original complete parent states must match')
    return digest(collection)


def validate_manifest(manifest):
    require(manifest['schema'] == 'CARA_READ_WRITE_M1_FULL8_SCORE_MANIFEST_R1'
        and manifest['GPU_released'] is True and manifest['cost_settled'] is True
        and manifest['identity_controls_passed'] == 4 and manifest['physical_paths'] == 14
        and manifest['physical_model_pairs'] == 512
        and len(manifest['members']) == len(set(manifest['members'])) == 2,
        'Complete released/settled14 collection and four full latent/RGB controls required')
    pairs = manifest['pairs']
    require(len(pairs) == 8 and {(p['candidate']['member'], p['candidate']['role']) for p in pairs}
        == {(m, r) for m in manifest['members'] for r in READ_ROLES},
        'All eight read/write versus fresh Native pairs required')
    return validate_pair_identities(manifest)


def released_artifacts(capture, expected_launch_sha256, settlement, *, cpu_validation=False, cpu_shape=None):
    # Financial and physical closure runs before any output or score is opened.
    release = released_lifecycle(capture, expected_launch_sha256, settlement, cpu_validation=cpu_validation)
    require(release['container_exit_success'] and release['GPU_released'] and release['cost_settled'],
        'Successful original settled release required before any M1 artifact read')
    launch, registration = record(capture, 'launch'), record(capture, 'registration')
    require(launch['host'] == 'two_card' and launch['physical_paths'] == 14,
        'Original two-card M1 allocation required')
    stage = Path(launch['stage'])
    project = stage.parents[1]
    for path in (CARD, PRECISION, GEOMETRY, ASSETS, PROTOCOL, SOURCE):
        require(file_sha(stage/path) == registration['payload_sha256'][path],
            'Original registered M1 identity/reader source changed: '+path)
    card = json.loads((stage/CARD).read_text())
    require(card['scope_sha256'] == launch['scope_sha256'], 'Original M1 collection scope differs')
    require(cpu_shape is None or cpu_validation, 'Tiny geometry is explicit CPU-fixture-only')
    shape = (93,432,768,3) if cpu_shape is None else tuple(cpu_shape)
    require(shape[0] == 93 and shape[-1] == 3, 'All93 RGB frames required')
    output = project/'outputs'/launch['run_id']
    collection_path = output/'read-write-collection.json'
    collection = json.loads(collection_path.read_text())
    collection_digest = check_collection(card, collection, cpu_validation=cpu_validation)
    terminal = json.loads((output/'read-write-model-runner.json').read_text())
    require(terminal['status'] == 'COMPLETE14_COLLECTION_PENDING_RELEASE'
        and terminal['scope_sha256'] == card['scope_sha256']
        and terminal['source_revision'] == launch['source_revision']
        and terminal['collection_sha256'] == file_sha(collection_path)
        and terminal['complete_paths'] == 14 and terminal['physical_model_pairs'] == 512
        and terminal['CPU_fixture_only'] is cpu_validation, 'Original complete M1 runner terminal required')
    precision = json.loads((stage/PRECISION).read_text())
    # A6000's accepted asset has a .pt suffix but is a ZIP; identity is its full
    # registered digest, never a guessed format or an absent launch field.
    assets = json.loads((stage/ASSETS).read_text())
    model = [a for a in assets['files'] if a['digest_kind'] == 'sha256' and a['digest'] == precision['model_sha256']]
    require(len(model) == 1, 'One original registered Cosmos model asset required')
    relative = Path(model[0]['path'])
    require(not relative.is_absolute() and '..' not in relative.parts, 'Model asset must stay in the original project')
    if not cpu_validation:
        require((project/relative).stat().st_size == model[0]['bytes']
            and file_sha(project/relative) == model[0]['digest'], 'Original complete model asset digest differs')
    artifacts, decoded, descriptors, latents = {}, {}, {}, {}
    requests = {r['name']:r for r in card['inputs']}
    import torch
    for row in collection['rows']:
        slot, result = row['slot'], row['result']
        identifier = slot['id']
        video, tensor = result['video_artifact'], row['tensor_artifact']
        require(video['path'] == result['video_path'] == str(output/'B'/identifier/(slot['member']+'.mp4'))
            and tensor['path'] == str(output/'B'/(identifier+'.pt')), 'Original M1 output location differs')
        verify_file(video, original_output=True)
        verify_file(tensor, original_output=True)
        arguments_file = Path(video['path']).with_suffix('.json')
        arguments = json.loads(arguments_file.read_text())
        expected = {k:v for k,v in requests[slot['member']].items() if k != 'partition'}
        require(all(arguments.get(k) == v for k,v in expected.items()), 'Actual saved M1 request differs')
        saved = torch.load(tensor['path'], map_location='cpu', weights_only=True)
        latent = saved['final_latent']
        expected_latent = json.loads((stage/GEOMETRY).read_text())['expected_real_shape']
        require(isinstance(latent, torch.Tensor) and torch.isfinite(latent).all()
            and (cpu_validation or list(latent.shape) == expected_latent), 'Complete finite original latent required')
        latents[identifier] = latent
        decoded[identifier] = decode_video(video, shape=shape)
        descriptors[identifier] = dict(video, slot_id=identifier, member=slot['member'], role=slot['role'],
            seed=0, host=launch['host'], gpu_uuid=launch['gpu_uuid'], model_sha256=precision['model_sha256'],
            scope_sha256=card['scope_sha256'], precision=precision['precision_sha256'],
            comparison_input_sha256=comparison_input_digest(arguments), execution_request_sha256=digest(arguments),
            argument_file_sha256=file_sha(arguments_file))
        artifacts[identifier] = dict(video=copy.deepcopy(video), tensor=copy.deepcopy(tensor),
            arguments_path=str(arguments_file), arguments_sha256=file_sha(arguments_file))
        verify_file(tensor, original_output=True)
    slots = {(r['slot']['member'], r['slot']['role']):r['slot']['id'] for r in collection['rows']}
    controls, pairs = [], []
    for member in card['FIT']:
        native = slots[(member, 'NATIVE35')]
        for role, control in (('RW00', 'UNIFORM19_C'), ('RW11', 'D8_CONTROL')):
            left, right = slots[(member, role)], slots[(member, control)]
            require(torch.equal(latents[left], latents[right]) and decoded[left] == decoded[right],
                'Full M1 latent/93RGB corner equivalence failed')
            controls.append(dict(member=member, corner=role, independent_control=control, passed=True,
                latent_equal=True, RGB_sha256=decoded[left]['RGB_sha256']))
        for role in READ_ROLES:
            identifier = slots[(member, role)]
            require(decoded[identifier]['PTS'] == decoded[native]['PTS'], 'Original M1/Native PTS differ')
            pairs.append(dict(id='M1_PAIR_'+identifier, candidate=descriptors[identifier], reference=descriptors[native]))
    manifest = dict(schema='CARA_READ_WRITE_M1_FULL8_SCORE_MANIFEST_R1', run_id=launch['run_id'], launch_id=launch['launch_id'],
        scope_sha256=card['scope_sha256'], analysis_scope_sha256=card['scope_sha256'], members=card['FIT'], pairs=pairs,
        protocol_sha256=digest(json.loads((stage/PROTOCOL).read_text())), physical_paths=14, physical_model_pairs=512,
        identity_controls=controls, identity_controls_passed=4, GPU_released=True, cost_settled=True,
        original_launch_sha256=expected_launch_sha256, collection_sha256=collection_digest,
        CPU_fixture_only=cpu_validation, diagnostic_timing_only=True, independent_new_inputs=False,
        scientific_accepted=False, GPU_submissions=0, ledger_written=False)
    validate_manifest(manifest)
    release.update(original_launch_sha256=expected_launch_sha256, collection_sha256=collection_digest)
    return dict(status='COMPLETE14_FOUR_LATENT_RGB_CONTROLS_EIGHT_PAIRS_NOT_SCORED', manifest=manifest,
        artifacts=artifacts, decoded=decoded, release=release, CPU_fixture_only=cpu_validation,
        reader_sha256=file_sha(__file__))
