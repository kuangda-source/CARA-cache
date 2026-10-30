"""Real 48MiB journal writes; synthetic allocation actions and metadata only."""
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest

from wcomr import cara_budget_guardian_journal_r1 as writer
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
from wcomr.history104_storage_r2 import StorageGuard,FixedJournal,KEYS,SLOT_BYTES
from wcomr.policy_price_terminal_r1 import record
from wcomr.cara_budget_lifecycle_r1 import financial_terminal
from test_cara_budget_lifecycle_r1 import fixture,put


class GuardianJournalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.stage=Path(self.temp.name);self.path=self.stage/'CPU-only-control.journal'
        if hasattr(os,'posix_fallocate'):FixedJournal(self.path).create()
        else:
            with self.path.open('xb') as stream:
                for _ in range(2*len(KEYS)):stream.write(bytes(SLOT_BYTES))
        self.storage=StorageGuard(dict(output_mount=str(self.stage/'CPU-output'),journal_path=str(self.path)))
        self.capture,_,_=fixture()
        for key in self.capture['files']:
            value=record(self.capture,key)
            if 'stage' in value:value['stage']=str(self.stage)
            put(self.capture,key,value)
        reg=record(self.capture,'registration');reg['payload_sha256'][writer.SOURCE]=sha(writer.__file__)
        self.registration=reg;reg_sha=put(self.capture,'registration',reg)
        self.capture['payload_actual_sha256']=reg['payload_sha256']
        auth_sha=self.capture['files']['authorization']['sha256']
        envelope=record(self.capture,'central_reservation');envelope['job'].update(stage=str(self.stage),
            registration_sha256=reg_sha,authorization_sha256=auth_sha)
        envelope_sha=put(self.capture,'central_reservation',envelope)
        self.launch=record(self.capture,'launch');self.launch.update(registration_sha256=reg_sha,
            authorization_sha256=auth_sha,central_reservation_sha256=envelope_sha)
        self.expected=put(self.capture,'launch',self.launch)
        self.capture['container']['manifest_sha256']=reg_sha
        self.clock=20.

    def begin(self):
        return writer.GuardianJournal(self.stage,self.launch,self.registration,self.storage,cpu_validation=True,
            monotonic=lambda:self.clock,wall=lambda:100.)

    def finish(self,guard,**kwargs):
        self.clock=200.
        return guard.finish(container_terminal_witness=dict(kind='NO_CONTAINER_DISPATCH',complete=True),
            mode_restoration=dict(restored=True,status='PRIOR_MODE_UNCHANGED'),error=ValueError('CPU declared admission failure'),**kwargs)

    def import_terminal(self):
        for key in ('guardian','billing'):put(self.capture,key,json.loads((self.stage/(key+'.json')).read_text()))
        self.capture['container']=None
        for role in ('container_cli','supervisor','runner'):self.capture['process_observations'][role]=None
        for key in ('supervisor_start','runner_start','runner_intent'):self.capture['files'][key]={'exists':False}
        self.capture['own_UUID_lock_free']=self.capture['mode_owner_lock_free']=None

    def test_preallocation_failure_emits_financially_valid_original_witness(self):
        guard=self.begin();bill=self.finish(guard);self.import_terminal()
        self.assertEqual(financial_terminal(self.capture,self.expected,cpu_validation=True)[1]['actual_GPUh'],.05)
        self.assertEqual(bill['actual_GPUh'],.05)
        self.assertEqual(set(guard.state['allocation_never_attempted_witness']),set(writer.ATTEMPTS))

    def test_bound_container_and_all_handles_reach_original_financial_reader(self):
        guard=self.begin()
        for attempt in writer.ATTEMPTS:guard.operation(attempt,lambda:None)
        original=record(self.capture,'guardian')
        for role in ('container_cli','supervisor','runner'):guard.bind_child(role,original['original_handles'][role])
        self.clock=200.
        container=self.capture['container']
        guard.finish(container_terminal_witness=dict(kind='BOUND_CONTAINER_TERMINAL',complete=True,
            container_id=container['id'],container=container),mode_restoration=original['mode_restoration'],container_exit_code=0)
        for key in ('guardian','billing'):put(self.capture,key,json.loads((self.stage/(key+'.json')).read_text()))
        self.assertEqual(financial_terminal(self.capture,self.expected,cpu_validation=True)[1]['actual_GPUh'],.05)
        self.assertEqual(sha(self.stage/'billing.json'),guard.state['billing_sha256'])

    def test_durable_attempt_precedes_action_and_cannot_repeat(self):
        guard=self.begin();seen=[]
        def action():seen.append(self.storage.journal.read('guardian')['allocation_attempts']['mode_lock_attempted'])
        guard.operation('mode_lock_attempted',action)
        self.assertEqual(seen,[True]);self.assertTrue(guard.state['mode_owner_fenced'])
        with self.assertRaises(ValueError):guard.operation('mode_lock_attempted',action)
        self.finish(guard);self.assertNotIn('allocation_never_attempted_witness',guard.state)

    def test_failed_mirror_does_not_execute_action_or_allow_another(self):
        guard=self.begin();actions=[]
        def fail(*unused):raise OSError(28,'CPU fixture full output')
        guard.writer=fail
        with self.assertRaises(OSError):guard.operation('mode_lock_attempted',lambda:actions.append('executed'))
        self.assertEqual(actions,[])
        self.assertTrue(self.storage.journal.read('guardian')['allocation_attempts']['mode_lock_attempted'])
        with self.assertRaises(ValueError):guard.operation('device_lease_attempted',lambda:actions.append('executed'))

    def test_action_failure_retains_attempt_and_original_error(self):
        guard=self.begin()
        def fail():raise RuntimeError('CPU fixture mode command failed')
        with self.assertRaises(RuntimeError):guard.operation('mode_change_attempted',fail)
        self.finish(guard)
        self.assertTrue(guard.state['GPU_mode_change_attempted'])
        self.assertNotIn('allocation_never_attempted_witness',guard.state)

    def test_terminal_mirror_failure_recovers_same_bill_without_remeasurement(self):
        guard=self.begin()
        def fail(*unused):raise OSError(28,'CPU fixture full output')
        guard.writer=fail
        with self.assertRaises(OSError):self.finish(guard)
        original=self.storage.journal.read('billing');self.clock=1000.
        recovered=writer.recover_terminal_mirrors(self.stage,self.launch,self.storage)
        self.assertFalse(recovered['remeasured'])
        self.assertEqual(json.loads((self.stage/'billing.json').read_text()),original)
        writer.recover_terminal_mirrors(self.stage,self.launch,self.storage)
        self.import_terminal();financial_terminal(self.capture,self.expected,cpu_validation=True)
        with self.assertRaises(ValueError):self.finish(guard)

    def test_original_or_foreign_journal_never_reinitialized(self):
        guard=self.begin()
        with self.assertRaises(ValueError):self.begin()
        self.storage.journal.write('guardian',dict(foreign='CPU fixture'))
        before=self.storage.journal.read('guardian')
        with self.assertRaises(ValueError):self.begin()
        self.assertEqual(self.storage.journal.read('guardian'),before)

    def test_corrupt_nonempty_control_slot_refused(self):
        with self.path.open('r+b') as stream:
            stream.seek(KEYS.index('billing')*2*SLOT_BYTES+100);stream.write(b'CPU corrupt fixture')
        with self.assertRaises(ValueError):self.begin()
        self.assertFalse((self.stage/'guardian-intent.json').exists())

    def test_recovery_refuses_foreign_or_mismatched_terminal(self):
        guard=self.begin();self.finish(guard)
        before=(self.stage/'billing.json').read_bytes()
        foreign=copy.deepcopy(self.launch);foreign['launch_id']='FOREIGN'
        with self.assertRaises(ValueError):writer.recover_terminal_mirrors(self.stage,foreign,self.storage)
        bill=self.storage.journal.read('billing');bill['actual_GPUh']+=1;self.storage.journal.write('billing',bill)
        with self.assertRaises(ValueError):writer.recover_terminal_mirrors(self.stage,self.launch,self.storage)
        self.assertEqual((self.stage/'billing.json').read_bytes(),before)

    def test_live_or_partial_journal_not_recoverable_as_terminal(self):
        guard=self.begin()
        self.storage.journal.write('billing',dict(CPU_fixture_only=True))
        with self.assertRaises(ValueError):writer.recover_terminal_mirrors(self.stage,self.launch,self.storage)

    def test_bound_children_and_deadline_use_original_host_and_clock(self):
        guard=self.begin();identity=record(self.capture,'guardian')['original_handles']['container_cli']
        guard.bind_child('container_cli',identity)
        with self.assertRaises(ValueError):guard.bind_child('runner',identity)
        altered=copy.deepcopy(identity);altered['pid']=900;altered['host_view']['pid_namespace_inode']+=1
        with self.assertRaises(ValueError):guard.bind_child('runner',altered)
        self.assertEqual(guard.remaining_seconds(600),6600.)
        self.clock=6620.
        with self.assertRaises(TimeoutError):guard.remaining_seconds(600)

    def test_fixture_or_wrong_source_cannot_record_production_guardian(self):
        with self.assertRaises(ValueError):writer.GuardianJournal(self.stage,self.launch,self.registration,self.storage)
        self.registration['payload_sha256'][writer.SOURCE]='0'*64
        with self.assertRaises(ValueError):self.begin()

    def test_unknown_container_never_has_complete_bill(self):
        guard=self.begin();guard.operation('container_dispatch_attempted',lambda:None);self.clock=200.
        bill=guard.finish(container_terminal_witness=dict(complete=False,reason='CPU observation unavailable'),
            mode_restoration=dict(restored=False),error=TimeoutError('CPU fixture observation timeout'))
        self.assertFalse(bill['wall_interval_complete']);self.assertEqual(bill['actual_GPUh'],.05)
        self.assertNotIn('allocation_never_attempted_witness',guard.state)


if __name__=='__main__':unittest.main()
