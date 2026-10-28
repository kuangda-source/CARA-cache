import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from test_sq_s_batch_r1 import Adapter, Store, profile
from wcomr.sq_s_batch_r1 import digest, make_scope
from wcomr.sq_s_physical_r1 import PhysicalRequests, collect, make_physical_scope

IDENTITY = digest(dict(explicit_CPU_fixture=True))


class Base(Adapter):
    def __call__(self, slot, output):
        result = super().__call__(slot, output)
        for row in result['guided']+[result['final_latent']]:
            row.update(shape=[1,1,1,1], dtype='torch.float32')
        return result


def decode_fixture(result):
    return dict(frames=93, sha256=result.get('decode_hash', result['guided'][0]['sha256']))


def retained(base):
    old = Base()
    slot = next(s for s in old.scope['slots'] if s['id'] == 'p0-Shared25-C-OFF')
    result = old(slot, Path('DECLARED_CPU_METADATA_NO_SAMPLING'))
    result['RGB'] = decode_fixture(result)
    value = dict(CPU_fixture=True, slot_id=slot['id'], original_host='two_card', old_bytes_verified=True,
        new_ON_equivalence_accepted=False, execution_identity_sha256=IDENTITY, result=result)
    value['witness_sha256'] = digest(value)
    return value


def entry(host='two_card', mutate=None):
    base = Base(mutate)
    witness = retained(base) if host == 'two_card' else None
    scope = make_physical_scope(base.scope, host, IDENTITY, witness)
    return PhysicalRequests(base, scope, IDENTITY, witness=witness, CPU_decode_fixture=decode_fixture)


class PhysicalTests(unittest.TestCase):
    def test_complete_nine_and_ten_physical_paths_preserve_all_labels(self):
        for host, paths, heads, deep in [('two_card',9,864,502), ('four_card',10,936,552)]:
            adapter = entry(host)
            counts = adapter.physical_scope['counts']
            self.assertEqual((counts['new_paths'], counts['branch_readouts'], counts['deep_block_calls']),
                             (paths, heads, deep))
            self.assertEqual((counts['moment_rows'],counts['extra_Dense_teacher_pairs'],counts['extra_C_shadow_pairs']),
                             (108,56,52))
            before = []
            with tempfile.TemporaryDirectory() as directory:
                state = collect(adapter, Path(directory)/'whole', before_request=lambda s:before.append(s['id']),
                                storage=Store(), save=lambda s:None)
                self.assertEqual(len(adapter.base.calls), paths)
                self.assertEqual(len(before), paths)
                self.assertEqual(len(state['rows']), 10)
                self.assertEqual(len(state['OFF_ON_controls']), 4)
                self.assertEqual(state['physical_execution']['actual_new_paths'], paths)
                if host == 'two_card':
                    self.assertNotIn('p0-Shared25-C-OFF', before)
                    self.assertFalse((Path(directory)/'whole/p0-Shared25-C-OFF').exists())
                    self.assertTrue(state['physical_execution']['OFF_ON_controls'][0]['retained_OFF_has_no_pre_encoding_pixels'])

    def test_Ada_cannot_import_original_A6000_witness(self):
        base = Base()
        with self.assertRaisesRegex(ValueError, 'cannot be pooled'):
            make_physical_scope(base.scope, 'four_card', IDENTITY, retained(base))

    def test_witness_corruption_and_CPU_substitution_refused(self):
        for kind in ('short', 'policy', 'CPU', 'binding', 'ON_slot'):
            base = Base(); witness = retained(base)
            if kind == 'short': witness['result']['guided'].pop()
            if kind == 'policy': witness['result']['policy_fingerprint'] = '0'*64
            if kind == 'CPU': witness['CPU_fixture'] = False
            if kind == 'binding': witness['execution_identity_sha256'] = '0'*64
            if kind == 'ON_slot': witness['slot_id'] = 'p0-Shared25-C-ON'
            witness['witness_sha256'] = digest({k:v for k,v in witness.items() if k != 'witness_sha256'})
            with self.assertRaises(ValueError):
                make_physical_scope(base.scope, 'two_card', IDENTITY, witness)

    def test_rehashed_wrong_physical_denominator_refused(self):
        base = Base(); witness = retained(base)
        scope = make_physical_scope(base.scope, 'two_card', IDENTITY, witness)
        scope['counts']['new_paths'] = 10
        scope['physical_scope_sha256'] = digest({k:v for k,v in scope.items() if k != 'physical_scope_sha256'})
        with self.assertRaisesRegex(ValueError, 'denominator changed'):
            PhysicalRequests(base, scope, IDENTITY, witness=witness, CPU_decode_fixture=decode_fixture)

    def test_actual_common_RGB_mismatch_retains_failure_and_blocks_rewrap(self):
        def bad(slot,result):
            if slot['id'] == 'p0-Shared25-C-ON': result['decode_hash'] = '0'*64
        adapter = entry(mutate=bad); snapshots=[];store=Store()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'OFF-ON mismatch'):
                collect(adapter,Path(directory)/'bad',before_request=lambda s:None,
                        storage=store,save=lambda s:snapshots.append(copy.deepcopy(s)))
            self.assertFalse(store.finished)
            self.assertEqual(snapshots[-1]['status'],'FAILED_RETAINED_NO_RETRY')
            with self.assertRaisesRegex(ValueError,'already consumed'):
                PhysicalRequests(adapter.base, adapter.physical_scope, IDENTITY,
                    witness=adapter.witness, CPU_decode_fixture=decode_fixture)

    def test_legacy_without_pre_encoding_pixels_is_eligible(self):
        def change_unretained_pixels(slot,result):
            if slot['id'] == 'p0-Shared25-C-ON': result['RGB']['sha256'] = '0'*64
        adapter = entry(mutate=change_unretained_pixels)
        with tempfile.TemporaryDirectory() as directory:
            state = collect(adapter,Path(directory)/'whole',before_request=lambda s:None,storage=Store(),save=lambda s:None)
            self.assertEqual(state['status'],'COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE')

    def test_two_fresh_roles_keep_additional_pre_encoding_control(self):
        def bad(slot,result):
            if slot['id'] == 'p1-F19-C-ON': result['RGB']['sha256'] = '0'*64
        adapter = entry(mutate=bad);snapshots=[]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'pre-encoding RGB mismatch'):
                collect(adapter,Path(directory)/'bad',before_request=lambda s:None,
                        storage=Store(),save=lambda s:snapshots.append(copy.deepcopy(s)))
            self.assertEqual(snapshots[-1]['status'],'FAILED_RETAINED_NO_RETRY')
            self.assertFalse(any(s['status']=='COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE' for s in snapshots))

    def test_resource_failure_consumes_underlying_sampler(self):
        adapter=entry();snapshots=[]
        def refuse(slot): raise OSError('CPU resource fixture')
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(OSError):
                collect(adapter,Path(directory)/'bad',before_request=refuse,storage=Store(),save=lambda s:snapshots.append(copy.deepcopy(s)))
            self.assertEqual(adapter.base.calls,[])
            with self.assertRaisesRegex(ValueError,'already consumed'):
                collect(adapter,Path(directory)/'retry',before_request=lambda s:None,storage=Store(),save=lambda s:None)

    def test_real_context_and_fresh_original_admission_are_required(self):
        root=Path(__file__).resolve().parents[1]/'plans/cara_next_stage_20261028/sq'
        witness=json.loads((root/'S_RETAINED_OFF_WITNESS_R1.json').read_text())
        physical=json.loads((root/'S_PHYSICAL_TWO_CARD_R1.json').read_text())
        from wcomr.policy_generator_r1.interval_grammar import Profile
        pp=json.loads((root/'S_SUPPORT_RECONCILIATION_R2.json').read_text())['profile']
        for k in ('protected_dense','alpha_candidates'): pp[k]=tuple(pp[k])
        base=SimpleNamespace(scope=make_scope(Profile(**pp)))
        binding=witness['execution_identity_sha256']
        with self.assertRaisesRegex(ValueError,'decode stand-in'):
            PhysicalRequests(base,physical,binding,witness=witness,CPU_decode_fixture=decode_fixture)
        with self.assertRaisesRegex(ValueError,'Separately admitted'):
            PhysicalRequests(base,physical,binding,witness=witness)
        context=dict(authorizes_S_collection=True,host='two_card',physical_scope_sha256=physical['physical_scope_sha256'],
            execution_identity_sha256=binding,launch_id='CPU_GUARD_TEST',gpu_uuid='CPU_GUARD_TEST',source_revision='CPU_GUARD_TEST')
        with self.assertRaisesRegex(ValueError,'Fresh original'):
            PhysicalRequests(base,physical,binding,witness=witness,production_context=context)


if __name__ == '__main__':
    unittest.main()
