"""Distinct point20 entry, ledger and postrelease controls; synthetic CPU only."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_read_write_runner_binding_r1 as binding
from wcomr import cara_read_write_central_r1 as central
from wcomr import cara_read_write_artifacts_r1 as reader
from wcomr.cara_read_write_identity_r1 import M1, P0, for_run
from wcomr.cara_source_lifecycle_native_bridge_r1 import BRIDGE
from wcomr.gpu_budget_pool_v2 import atomic_json, sha
from wcomr.policy_price_terminal_r1 import record
from check_cara_read_write_packet_fixture_r1 import packet
from test_cara_read_write_entry_r1 import Fixture
import test_cara_read_write_central_r1 as original_central
from test_cara_s_endpoint_artifacts_r1 import write_media, decode
from test_cara_budget_lifecycle_r1 import fixture as lifecycle_fixture, put


class Entry(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(self.temp.name, P0)

    def test_new_point20_full14_binding_and_frozen_commands(self):
        card,launch,profile,context = binding.validate(self.f.project,self.f.stage)
        self.assertEqual((card['target_update'],context['phase'],context['target_update']),
                         (20,P0.phase,20))
        self.assertIn('D20_CONTROL',card['roles'])
        command = self.f.command()
        self.assertIn(str(self.f.stage/'scripts/cara_read_write_supervisor_worker_r1.py'),command)
        self.assertEqual(profile['hard_GPUh'],1.95)
        self.assertEqual(for_run(launch['run_id']),P0)

    def test_point8_authority_stage_or_proof_cannot_bind_point20(self):
        for key,value in [('run_id',M1.run_id),('target_update',8),('card_kind',M1.card_kind)]:
            original = self.f.auth[key]
            self.f.auth[key] = value
            self.f.write_all()
            with self.subTest(key=key),self.assertRaises(ValueError):
                binding.validate(self.f.project,self.f.stage)
            self.f.auth[key] = original
        for mapping,key,value in [(self.f.proof,'target_update',8),
                (self.f.proof,'point20_whole_card_accepted',False),
                (self.f.proof,'cross_point_Native_bridge_controls_accepted',False),
                (self.f.quote,'run_id',M1.run_id)]:
            original = mapping[key]
            mapping[key] = value
            self.f.write_all()
            with self.subTest(key=key),self.assertRaises(ValueError):
                binding.validate(self.f.project,self.f.stage)
            mapping[key] = original


class Central(unittest.TestCase):
    def setUp(self):
        self.f = original_central.CentralTests('runTest')
        self.f.setUp()
        self.addCleanup(self.f.temp.cleanup)
        self.f.auth.update(run_id=P0.run_id,stage=str(self.f.project/'.sync'/P0.stage_name),
            card_kind=P0.card_kind,target_update=20,central_exception_run_id=P0.run_id)
        self.f.observations['two_card'].update(run_id=P0.run_id,stage=self.f.auth['stage'])
        self.f.admission['status'] = P0.phase+'_COMPLETE_FRESH_ADMISSION_NO_GPU'
        self.f.refresh_authority()

    def test_only_new_card_is_reserved_and_recovered_once(self):
        first = self.f.reserve()
        after = self.f.pool.read()
        self.assertEqual(first,self.f.reserve())
        self.assertEqual(after,self.f.pool.read())
        self.assertEqual(after['jobs'][P0.run_id]['billed_limit_GPUh'],1.95)
        self.assertNotIn(M1.run_id,after['jobs'])
        self.assertEqual(after['reserved_gpu_hours'],18.45)
        self.assertEqual({k:after['jobs'][k] for k in self.f.before['jobs']},self.f.before['jobs'])

    def test_closed_M1_exception_or_point8_identity_cannot_authorize_P0(self):
        for key,value in [('central_exception_run_id',M1.run_id),('central_transaction_authorized',False),
                          ('card_kind',M1.card_kind),('target_update',8)]:
            original = self.f.auth[key]
            self.f.auth[key] = value
            self.f.refresh_authority()
            with self.subTest(key=key),self.assertRaises(ValueError):
                self.f.reserve()
            self.assertEqual(self.f.pool.read(),self.f.before)
            self.f.auth[key] = original

    def test_new_original_bill_settles_once_without_recharging_M1(self):
        capture,expected,job = lifecycle_fixture(run_id=P0.run_id,billed_limit_GPUh=1.95,
            host='two_card',gpu_uuid=self.f.auth['gpu_uuid'],extra_sources={
                central.SOURCE:sha(central.__file__),
                'src/wcomr/cara_s_endpoint_lifecycle_r1.py':sha(Path(central.__file__).parent/'cara_s_endpoint_lifecycle_r1.py')})
        guardian = record(capture,'guardian')
        guardian['status'] = 'CARA_ENDPOINT_GUARDIAN_TERMINAL_R1'
        put(capture,'guardian',guardian)
        authority = record(capture,'authorization')
        authority.update(central_transaction_authorized=True,central_user_quote='CPU exact new P0 fixture',
            card_kind=P0.card_kind,target_update=20,central_exception_run_id=P0.run_id)
        auth_sha = put(capture,'authorization',authority)
        job['authorization_sha256'] = auth_sha
        envelope_sha = put(capture,'central_reservation',dict(central_ledger_host='four_card',job=job))
        launch = record(capture,'launch')
        launch.update(authorization_sha256=auth_sha,central_reservation_sha256=envelope_sha)
        expected = put(capture,'launch',launch)
        before = copy.deepcopy(self.f.before)
        before['jobs'][P0.run_id] = job
        before.update(central.Pool.accounting(before))
        atomic_json(self.f.pool.path,before)
        first = central.settle(self.f.project,capture,expected,cpu_validation=True)
        after = self.f.pool.read()
        self.assertEqual(first,central.settle(self.f.project,capture,expected,cpu_validation=True))
        self.assertEqual(after,self.f.pool.read())
        self.assertEqual(after['reserved_gpu_hours'],16.5)
        self.assertEqual(after['jobs'][P0.run_id]['actual_GPUh'],.05)


class Artifacts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.args = packet(self.temp.name,write_media,identity=P0)
        self.stage = Path(record(self.args['capture'],'launch')['stage'])

    def read(self):
        with patch.object(reader,'decode_video',side_effect=decode):
            return reader.released_artifacts(**self.args)

    def test_all_four_corners_at20_native_bridges_and_8_new_pairs(self):
        saved = self.read()
        manifest = saved['manifest']
        self.assertEqual((manifest['target_update'],manifest['cross_point_Native_controls_passed'],
                          len(manifest['pairs'])),(20,2,8))
        self.assertEqual(manifest['original_point8_new_scoring'],0)
        self.assertEqual({c['independent_control'] for c in manifest['identity_controls']},
                         {'UNIFORM19_C','D20_CONTROL'})
        for member in manifest['members']:
            traces = manifest['source_consumption'][member]
            for role in ('RW01','RW11'):
                self.assertEqual(traces[role]['C_consumers'],[[21],[21]])
                self.assertEqual(traces[role]['replaced_after_update'],[23,23])
            for role in ('RW00','RW10'):
                self.assertEqual(traces[role]['minted'],[False,False])

    def test_point8_intervention_cannot_pass_point20_artifacts(self):
        card = json.loads((self.stage/P0.manifest).read_text())
        output = self.stage.parents[1]/'outputs'/P0.run_id/'read-write-collection.json'
        collection = json.loads(output.read_text())
        for row in collection['rows']:
            if row['slot']['role'].startswith('RW'):
                row['result']['intervention']['target_update'] = 8
                break
        with self.assertRaisesRegex(ValueError,'target update'):
            reader.check_collection(card,collection,cpu_validation=True)

    def test_both_native_bridges_required_before_score_binding(self):
        manifest = self.read()['manifest']
        manifest['cross_point_Native_controls'].pop()
        with self.assertRaisesRegex(ValueError,'bridges before scoring'):
            reader.validate_manifest(manifest)

    def test_changed_native_RGB_request_or_bridge_bytes_refused(self):
        from wcomr.cara_source_lifecycle_native_bridge_r1 import compare
        saved = self.read()
        bridge = json.loads((self.stage/BRIDGE).read_text())
        card = json.loads((self.stage/P0.manifest).read_text())
        descriptors = {p[side]['slot_id']:p[side] for p in saved['manifest']['pairs']
                       for side in ('candidate','reference')}
        for fault in ('RGB','request'):
            changed = copy.deepcopy(bridge)
            first = changed['references'][card['FIT'][0]]
            if fault=='RGB':
                first['decoded']['RGB_sha256'] = '0'*64
            else:
                first['descriptor']['execution_request_sha256'] = '0'*64
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                compare(changed,card,saved['decoded'],descriptors,cpu_validation=True)
        with (self.stage/BRIDGE).open('ab') as stream:
            stream.write(b' ')
        with self.assertRaises(ValueError):
            self.read()


class ScoreRecovery(unittest.TestCase):
    def test_new_point20_original_score_container_accepts8_without_replay(self):
        from wcomr import cara_read_write_score_capture_r1 as capture
        from test_cara_read_write_score_capture_r1 import fixture, ended
        with tempfile.TemporaryDirectory() as root:
            args,container,_ = fixture(Path(root)/'project',identity=P0)
            with patch.object(capture,'inspect_original',return_value=dict(status='OBSERVED',container=container)), \
                 patch.object(capture,'observe_original_process',side_effect=ended):
                result = capture.recover(**args)
            self.assertEqual(result['accepted']['new_scored_pairs'],8)
            self.assertEqual(result['accepted']['reused_original_rows'],0)


if __name__ == '__main__':
    unittest.main()
