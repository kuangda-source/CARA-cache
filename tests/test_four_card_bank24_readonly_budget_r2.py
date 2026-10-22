"""Exercise the real read-only budget contract that failed in the CPU post."""
import fcntl
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
from four_card_bank24_gpu_port_r1 import readonly_budget_source
from wcomr.gpu_budget_pool_v2 import BudgetPool


class ReadOnlyBudgetTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.project=Path(self.temp.name)
        self.pool=self.project/'reports/gpu-budget-v2.json';self.pool.parent.mkdir()
        self.lock=self.project/'.sync/gpu-budget-v2.lock';self.lock.parent.mkdir();self.lock.touch()
        value=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226.,origin_used_gpu_hours=79.99637737158223,
            origin_gpu_jobs_launched=0,jobs={},events=[])
        value.update(BudgetPool.accounting(value));self.pool.write_text(json.dumps(value))
        def require(condition,message):
            if not condition:raise ValueError(message)
        namespace=dict(Path=Path,read=lambda p:json.loads(Path(p).read_text()),require=require)
        exec(compile(readonly_budget_source(),'<actual-registered-readonly-budget>','exec'),namespace)
        self.reader=namespace['ReadOnlyBudgetPool'](self.project)

    def tearDown(self):
        for p in [self.pool.parent,self.lock.parent]:p.chmod(0o700)
        self.temp.cleanup()

    def fingerprint(self):
        return {str(p.relative_to(self.project)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_ino,p.stat().st_mtime_ns)
            for p in [self.pool,self.lock]}

    def test_existing_readonly_pool_and_lock_are_not_written_or_replaced(self):
        before=self.fingerprint()
        self.pool.chmod(0o444);self.lock.chmod(0o444)
        self.pool.parent.chmod(0o555);self.lock.parent.chmod(0o555)
        real_open=Path.open
        def guarded(path,*args,**kwargs):
            mode=args[0] if args else kwargs.get('mode','r')
            if path in [self.pool,self.lock]:
                self.assertFalse(any(c in mode for c in 'wax+'),'Reader attempted a writable file mode')
            return real_open(path,*args,**kwargs)
        with patch.object(Path,'open',guarded):value=self.reader.read()
        self.assertEqual(value['used_gpu_hours'],79.99637737158223)
        self.assertEqual(before,self.fingerprint())

    def test_missing_lock_is_rejected_without_creation(self):
        self.lock.unlink()
        with self.assertRaisesRegex(ValueError,'never creates'):self.reader.read()
        self.assertFalse(self.lock.exists())

    def test_missing_pool_is_rejected_without_initialization(self):
        self.pool.unlink()
        with self.assertRaisesRegex(ValueError,'never initializes'):self.reader.read()
        self.assertFalse(self.pool.exists())

    def test_active_writer_lock_is_rejected_without_wait_or_mutation(self):
        before=self.fingerprint()
        with self.lock.open('rb') as writer:
            fcntl.flock(writer,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(BlockingIOError):self.reader.read()
        self.assertEqual(before,self.fingerprint())

    def test_inconsistent_stored_accounting_is_rejected_without_repair(self):
        value=json.loads(self.pool.read_text());value['used_gpu_hours']+=1
        self.pool.write_text(json.dumps(value));before=self.fingerprint()
        with self.assertRaisesRegex(ValueError,'original accounting'):self.reader.read()
        self.assertEqual(before,self.fingerprint())

    def test_original_accounting_rejects_unknown_job_status(self):
        value=json.loads(self.pool.read_text());value['jobs']={'bad':{'status':'UNKNOWN'}}
        self.pool.write_text(json.dumps(value));before=self.fingerprint()
        with self.assertRaises(ValueError):self.reader.read()
        self.assertEqual(before,self.fingerprint())

    def test_symlink_lock_is_rejected_without_following(self):
        target=self.project/'outside-lock';target.touch();self.lock.unlink();self.lock.symlink_to(target)
        with self.assertRaisesRegex(ValueError,'physical budget lock'):self.reader.read()
        self.assertEqual(target.read_bytes(),b'')

    def test_symlink_pool_is_rejected_without_following(self):
        target=self.project/'outside-pool';self.pool.rename(target);self.pool.symlink_to(target)
        before=target.read_bytes()
        with self.assertRaisesRegex(ValueError,'physical pool'):self.reader.read()
        self.assertEqual(target.read_bytes(),before)


if __name__=='__main__':unittest.main()
