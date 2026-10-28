"""Keep S's ten logical roles while reusing one admitted historical OFF role."""
import copy
from pathlib import Path

from .sq_s_batch_r1 import collect as logical_collect, digest, require, validate_scope
from .sq_s_reuse_r1 import decoded_rgb_signature


def validate_witness(upper, witness, execution_identity_sha256):
    require(witness['witness_sha256'] == digest({k:v for k,v in witness.items() if k != 'witness_sha256'}),
            'Retained OFF witness identity changed')
    require(witness['CPU_fixture'] == upper['CPU_fixture_only']
            and witness['execution_identity_sha256'] == execution_identity_sha256,
            'Retained OFF CPU/real execution binding differs')
    slot = next(s for s in upper['slots'] if s['id'] == witness['slot_id'])
    require(slot == dict(id='p0-Shared25-C-OFF', prompt=upper['prompts'][0], parent='Shared25-C',
                         purpose='CONTROL', enabled=False), 'Only the original first-input Shared25-C OFF can reuse')
    result = witness['result']
    require(witness['original_host'] == 'two_card' and witness['old_bytes_verified'] is True
            and witness['new_ON_equivalence_accepted'] is False
            and result['status'] == 'COMPLETE' and result['CPU_fixture'] == upper['CPU_fixture_only']
            and result['solver_steps'] == len(result['guided']) == 36 and result['S_rows'] == []
            and result['policy_fingerprint'] == upper['policies']['Shared25-C']['fingerprint']
            and result['semantic_actions'] == upper['policies']['Shared25-C']['actions']
            and result['RGB']['frames'] == 93,
            'Incomplete or changed retained OFF role')
    for row in result['guided']+[result['final_latent']]:
        require(set(row) == {'shape', 'dtype', 'sha256'} and len(row['sha256']) == 64,
                'Complete typed guided/latent identities required')


def make_physical_scope(upper, host, execution_identity_sha256, witness=None):
    validate_scope(upper)
    require(host in ('two_card', 'four_card') and len(execution_identity_sha256) == 64,
            'Registered host and frozen execution identity required')
    imported = []
    if witness is not None:
        require(host == 'two_card', 'Original A6000 OFF cannot be pooled into Ada execution')
        validate_witness(upper, witness, execution_identity_sha256)
        imported = [witness['slot_id']]
    slots = [copy.deepcopy(s) for s in upper['slots'] if s['id'] not in imported]
    parent_D = sum(upper['policies'][s['parent']]['actions'].count('D') for s in slots)
    parent_C = 36*len(slots)-parent_D
    counts = dict(new_paths=len(slots), reused_OFF_paths=len(imported), logical_paths=10,
        warm_paths=2, new_ON_paths=4, new_OFF_paths=4-len(imported),
        parent_Dense_pairs=parent_D, parent_C_pairs=parent_C,
        extra_Dense_teacher_pairs=56, extra_C_shadow_pairs=52,
        total_pairs=36*len(slots)+108, branch_readouts=2*(36*len(slots)+108),
        deep_block_calls=2*(parent_D+56), moment_rows=108, raw_states=8, unique_anchors=24)
    value = dict(schema='SQ_S_PHYSICAL_COLLECTION_R1', CPU_fixture_only=upper['CPU_fixture_only'],
        upper_scope_sha256=upper['scope_sha256'], host=host,
        execution_identity_sha256=execution_identity_sha256, physical_slots=slots,
        reused_slot_ids=imported, witness_sha256=witness['witness_sha256'] if witness else None,
        counts=counts, old_clean_timing_reused=False, additional_independent_samples=0,
        state='CPU_PREPARATION_PENDING_COMPLETE_GPU_CARD_ADMISSION', GPU_authorized=False)
    value['physical_scope_sha256'] = digest(value)
    return value


class PhysicalRequests:
    """Only real new roles call the accepted sampler; imports are metadata only."""
    def __init__(self, base, physical_scope, execution_identity_sha256, *, witness=None,
                 CPU_decode_fixture=None, production_context=None):
        expected = make_physical_scope(base.scope, physical_scope['host'], execution_identity_sha256, witness)
        require(physical_scope == expected, 'Frozen physical scope or denominator changed')
        require(not getattr(base, 'batch_consumed', False), 'Original sampler batch was already consumed')
        cpu = base.scope['CPU_fixture_only']
        require((CPU_decode_fixture is None) or (cpu and callable(CPU_decode_fixture)),
                'A decode stand-in is allowed only in the explicit CPU fixture')
        if not cpu:
            context = production_context or {}
            require(context.get('authorizes_S_collection') is True
                    and context.get('host') == physical_scope['host']
                    and context.get('physical_scope_sha256') == physical_scope['physical_scope_sha256']
                    and context.get('execution_identity_sha256') == execution_identity_sha256
                    and all(context.get(k) for k in ('launch_id', 'gpu_uuid', 'source_revision')),
                    'Separately admitted actual S physical context required')
            if witness:
                require(context.get('fresh_reuse_witness_sha256') == witness['witness_sha256'],
                        'Fresh original file/source/backend admission required before OFF reuse')
        self.base, self.scope = base, base.scope
        self.physical_scope = copy.deepcopy(physical_scope)
        self.witness = copy.deepcopy(witness)
        self.decode_fixture = CPU_decode_fixture
        self.seen, self.new_results = set(), {}
        self.batch_consumed = False

    def __call__(self, slot, output):
        require(slot['id'] not in self.seen, 'Original logical role was already consumed')
        self.seen.add(slot['id'])
        if slot['id'] in self.physical_scope['reused_slot_ids']:
            require(not Path(output).exists(), 'An imported OFF may not create a new sampling directory')
            result = copy.deepcopy(self.witness['result'])
            result.update(reused_original=True, witness_sha256=self.witness['witness_sha256'])
            return result
        result = self.base(slot, output)
        # Keep the VAE decoder/writer pixels as an extra fresh-pair witness.
        # The common legacy/new comparison uses decoded saved-MP4 pixels.
        pre_encoding = copy.deepcopy(result['RGB'])
        rgb = (self.decode_fixture(result) if self.decode_fixture else
               decoded_rgb_signature(result['encoded_video']['path']))
        require(rgb.get('frames') == 93 and len(rgb.get('sha256', '')) == 64,
                'Complete decoded saved-video RGB required')
        result.update(RGB=rgb, pre_encoding_RGB=pre_encoding, reused_original=False,
                      CPU_decode_fixture=self.decode_fixture is not None)
        self.new_results[slot['id']] = copy.deepcopy(result)
        return result

    def finish(self, state):
        expected = {s['id'] for s in self.physical_scope['physical_slots']}
        require(set(self.new_results) == expected and len(self.seen) == 10,
                'Complete logical and physical role denominators required')
        fresh_controls = []
        for control in state['OFF_ON_controls']:
            slots = [s for s in self.scope['slots'] if s['purpose'] == 'CONTROL'
                     and s['prompt'] == control['prompt'] and s['parent'] == control['parent']]
            fresh = [self.new_results[s['id']] for s in slots if s['id'] in self.new_results]
            if len(fresh) == 2:
                require(fresh[0]['pre_encoding_RGB'] == fresh[1]['pre_encoding_RGB'],
                        'Fresh OFF-ON pre-encoding RGB mismatch')
            fresh_controls.append(dict(control, pre_encoding_RGB_compared=len(fresh) == 2,
                retained_OFF_has_no_pre_encoding_pixels=len(fresh) == 1))
        return dict(scope=copy.deepcopy(self.physical_scope), actual_new_paths=len(self.new_results),
            actual_imported_OFF=len(self.physical_scope['reused_slot_ids']),
            OFF_ON_controls=fresh_controls, actual_GPU_or_scientific_acceptance=False)


def collect(adapter, output, *, before_request, storage, save):
    state = None
    require(not getattr(adapter.base, 'batch_consumed', False), 'Original sampler batch was already consumed')
    adapter.base.batch_consumed = True
    def before(slot):
        if slot['id'] not in adapter.physical_scope['reused_slot_ids']:
            before_request(slot)
    def pending(value):
        value = copy.deepcopy(value)
        if value['status'] == 'COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE':
            value['status'] = 'COMPLETE_LOGICAL_DATA_PENDING_PHYSICAL_CONTROLS'
        save(value)
    try:
        state = logical_collect(adapter, output, before_request=before, storage=storage, save=pending)
        state['physical_execution'] = adapter.finish(state)
        state['status'] = 'COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE'
        save(state)
        return state
    except BaseException as error:
        if state is not None:
            state.update(status='FAILED_RETAINED_NO_RETRY', error_type=type(error).__name__, error=str(error))
            save(state)
        raise
