"""Original P1 financial transactions on a temporary ledger, no remote access."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from check_cara_source_lifecycle_p1_outer_fixture_r1 import Fixture
from wcomr import cara_source_lifecycle_p1_central_r1 as central
from wcomr import cara_source_lifecycle_p1_dispatch_r1 as dispatch
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
from wcomr.wc73_execution_r1 import hold


class P1CentralTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.f=Fixture(self.temp.name)

    def test_full_original_reservation_adds_one24_step_and_preserves_two_holds(self):
        before=self.f.pool.read();envelope,snapshot=self.f.reserved()
        self.assertEqual(envelope['cap_increments24'],1)
        self.assertEqual(snapshot['ledger']['cap_gpu_hours'],250.)
        self.assertEqual(envelope['job']['billed_limit_GPUh'],18.)
        self.assertEqual(envelope['reservation_base']['reserved_gpu_hours'],16.5)
        for name,value in before['jobs'].items():self.assertEqual(snapshot['ledger']['jobs'][name],value)
        self.assertEqual(dispatch.central_binding(self.f.stage,self.f.authority,snapshot),envelope)

    def test_no_cap_raise_when_whole_funds_already_suffice(self):
        value=self.f.pool.read();value['origin_used_gpu_hours']=180.;value.update(self.f.pool.accounting(value));atomic_json(self.f.pool.path,value)
        envelope,snapshot=self.f.reserved()
        self.assertEqual(envelope['cap_increments24'],0)
        self.assertEqual(snapshot['ledger']['cap_gpu_hours'],226.)
        dispatch.central_binding(self.f.stage,self.f.authority,snapshot)

    def test_old_exception_or_missing_increment_permission_cannot_spend(self):
        for key,value in (('central_transaction_authorized',False),('central_exception_run_id','old-P0'),
                          ('standing_cap_increment24_authorized',False),('authorization_basis','USER_STANDING_BELOW2_GPUH_MAINLINE')):
            before=self.f.pool.path.read_bytes();original=self.f.authority[key];self.f.authority[key]=value;self.f.write()
            with self.subTest(key=key),self.assertRaises(ValueError):central.reserve(self.f.project,self.f.admission(),self.f.absence())
            self.assertEqual(self.f.pool.path.read_bytes(),before);self.f.authority[key]=original

    def test_unknown_original_handle_or_stale_admission_never_reserves(self):
        for mode in ('unknown','stale','source'):
            admission=self.f.admission();absence=self.f.absence();before=self.f.pool.path.read_bytes()
            if mode=='unknown':absence['two_card']['observation_complete']=False
            if mode=='stale':admission['observed_unix']-=61
            if mode=='source':admission['central_operator_sha256']='f'*64
            with self.subTest(mode=mode),self.assertRaises(ValueError):central.reserve(self.f.project,admission,absence)
            self.assertEqual(self.f.pool.path.read_bytes(),before)

    def test_recovery_never_adds_another_reservation_or_cap_event(self):
        first,_=self.f.reserved();before=self.f.pool.path.read_bytes()
        again=central.reserve(self.f.project,self.f.admission(),self.f.absence())
        self.assertEqual(again,first);self.assertEqual(self.f.pool.path.read_bytes(),before)
        self.assertEqual(len(self.f.pool.read()['events']),2)

    def test_lost_ledger_write_restores_only_original_exact_transaction(self):
        before=self.f.pool.path.read_bytes()
        with patch.object(central,'atomic_json',side_effect=OSError('CPU lost original ledger write')):
            with self.assertRaises(OSError):central.reserve(self.f.project,self.f.admission(),self.f.absence())
        self.assertEqual(self.f.pool.path.read_bytes(),before)
        recovered=central.reserve(self.f.project,self.f.admission(),self.f.absence())
        self.assertEqual(self.f.pool.read(),recovered['central_after'])
        self.assertEqual(recovered['cap_increments24'],1)

    def test_stale_snapshot_changed_cap_or_old_liability_is_refused(self):
        envelope,snapshot=self.f.reserved()
        for mode in ('stale','cap','liability','cost'):
            changed=copy.deepcopy(snapshot)
            if mode=='stale':changed['observed_unix']-=61
            if mode=='cap':changed['ledger']['cap_gpu_hours']+=24
            if mode=='liability':next(v for v in changed['ledger']['jobs'].values() if hold(v))['billed_limit_GPUh']+=.1
            if mode=='cost':changed['ledger']['jobs'][self.f.authority['run_id']]['billed_limit_GPUh']-=1
            changed['ledger'].update(self.f.pool.accounting(changed['ledger']))
            with self.subTest(mode=mode),self.assertRaises(ValueError):dispatch.central_binding(self.f.stage,self.f.authority,changed)


if __name__=='__main__':unittest.main()
