"""Frozen old point8 Native identities, compared with fresh point20 references."""
from .cara_read_write_identity_r1 import M1
from .policy_price_terminal_r1 import require

BRIDGE = 'plans/cara_next_stage_20261101/source_lifecycle/P0_POINT8_NATIVE_BRIDGE_R1.json'
ACCEPTED_SHA256 = 'f6d7274a69522bb663dc991d4a656b4cbd7b666a9d3beb043027b44b9960c4dc'
PACKET_SHA256 = '67ba575c1a84beb83620126e448af9acf18fb959a2566ea5e4638f7115938ace'


def compare(bridge, card, decoded, descriptors, *, cpu_validation=False):
    require(bridge['schema'] == 'CARA_P0_POINT8_NATIVE_FULL93_BRIDGE_R1'
        and bridge['CPU_fixture_only'] is cpu_validation
        and bridge['original_run_id'] == M1.run_id
        and set(bridge['references']) == set(card['FIT']), 'Exact original point8 Native bridge required')
    if not cpu_validation:
        require(bridge['accepted_sha256'] == ACCEPTED_SHA256 and bridge['packet_sha256'] == PACKET_SHA256
            and bridge['original_launch_id'] == '7949388215944eb98c7f64f21e8e1dd1'
            and bridge['original_source_revision'] == 'b930df4b04a0924d8bea0af32c0f7aaf8c33a5c8',
            'Original accepted point8 provenance required; never replay its references')
    controls = []
    for member in card['FIT']:
        original = bridge['references'][member]
        identifier = next(s['id'] for s in card['physical_matrix']
                          if s['member'] == member and s['role'] == 'NATIVE35')
        require(decoded[identifier] == original['decoded'],
                'Fresh point20 Native differs from original point8 full93 RGB/PTS')
        require(all(descriptors[identifier][k] == original['descriptor'][k] for k in
            ('member', 'role', 'seed', 'host', 'gpu_uuid', 'model_sha256', 'precision',
             'comparison_input_sha256', 'execution_request_sha256')),
            'Fresh point20 Native request/model/precision identity differs from point8')
        controls.append(dict(member=member, fresh_slot_id=identifier, original_slot_id=original['descriptor']['slot_id'],
            full93_RGB_equal=True, PTS_equal=True, RGB_sha256=decoded[identifier]['RGB_sha256'],
            original_GPU_or_scoring_replayed=False))
    return controls
