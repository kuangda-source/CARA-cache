"""Actual 48MiB journals, writer failures and concurrent CPU-only processes."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.history104_storage_r2 import FixedJournal,KEYS,SLOT_BYTES,HEADER
from wcomr.sq_control_storage_r1 import SQStorageGuard,EXTRA_KEYS,SCHEMA,storage_for

ROOT=Path(__file__).resolve().parents[1]
EVENTS=[]


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='SQ_CPU_JOURNAL_ONLY_');self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.path=self.root/'CPU-48MiB.journal'
        if hasattr(os,'posix_fallocate'):FixedJournal(self.path).create()
        else:
            with self.path.open('xb') as f:
                for _ in range(2*len(KEYS)):f.write(bytes(SLOT_BYTES))
        self.config=dict(run_id='CPU_SYNTHETIC_NO_GPU_AUTHORITY',output_mount=str(self.root/'out'),
            journal_path=str(self.path));(self.root/'out').mkdir()
        self.storage=SQStorageGuard(self.config,self.root/'.sync/gpu-locks')

    def test_original_six_slot_format_and_size_are_unchanged(self):
        self.assertEqual(self.path.stat().st_size,48*2**20)
        self.assertEqual(self.storage.original.journal.path,self.storage.journal.path)
        self.storage.persist('billing',self.root/'bill.json',dict(CPU_fixture=True),atomic_json)
        self.assertEqual(FixedJournal(self.path).read('billing'),dict(CPU_fixture=True))

    def test_all_release_and_diagnostic_keys_are_separately_durable(self):
        for i,key in enumerate(EXTRA_KEYS):
            self.storage.persist(key,self.root/(key+'.json'),dict(CPU_fixture=True,index=i),atomic_json)
        for i,key in enumerate(EXTRA_KEYS):
            self.assertEqual(self.storage.journal.read(key),dict(CPU_fixture=True,index=i))
        packet=FixedJournal(self.path).read('accounting')
        self.assertEqual(packet['schema'],SCHEMA);self.assertEqual(set(packet['records']),set(EXTRA_KEYS))

    def test_independent_durability_precedes_original_file_failure(self):
        def failed(*args):raise OSError(28,'CPU synthetic output full')
        value=dict(CPU_fixture=True,original_bill_sha='a'*64)
        with self.assertRaises(OSError):self.storage.persist('pending_release',self.root/'absent.json',value,failed)
        self.assertFalse((self.root/'absent.json').exists())
        self.assertEqual(self.storage.journal.read('pending_release'),value)

    def test_same_key_updates_preserve_every_other_logical_record(self):
        self.storage.journal.write('allocation_release',dict(v=1))
        self.storage.journal.write('pending_release',dict(v=2))
        self.storage.journal.write('allocation_release',dict(v=3))
        self.assertEqual(self.storage.journal.read('allocation_release'),dict(v=3))
        self.assertEqual(self.storage.journal.read('pending_release'),dict(v=2))

    def test_existing_standard_slots_are_not_reinitialized(self):
        original=FixedJournal(self.path);original.write('guardian',dict(original='retained'))
        self.storage.journal.write('allocation_release',dict(v=1))
        self.assertEqual(original.read('guardian'),dict(original='retained'))

    def test_foreign_packet_is_refused_without_overwrite(self):
        FixedJournal(self.path).write('accounting',dict(schema='FOREIGN',run_id=self.config['run_id'],records={}))
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'Foreign'):self.storage.journal.write('pending_release',{})
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)

    def test_other_run_packet_is_refused_without_overwrite(self):
        FixedJournal(self.path).write('accounting',dict(schema=SCHEMA,run_id='FOREIGN',records={}))
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'Foreign'):self.storage.journal.write('allocation_release',{})
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)

    def test_corrupt_nonempty_accounting_is_not_treated_as_new(self):
        with self.path.open('r+b') as f:f.seek(KEYS.index('accounting')*2*SLOT_BYTES+HEADER);f.write(b'CPU_CORRUPT')
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'corrupt'):self.storage.journal.write('allocation_release',{})
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)

    def test_oversize_packet_retains_the_previous_valid_generation(self):
        self.storage.journal.write('allocation_release',dict(v=1))
        with self.assertRaisesRegex(ValueError,'too large'):
            self.storage.journal.write('pending_release',dict(value='x'*SLOT_BYTES))
        self.assertEqual(self.storage.journal.read('allocation_release'),dict(v=1))
        with self.assertRaisesRegex(ValueError,'No durable'):self.storage.journal.read('pending_release')

    def test_unknown_key_cannot_clobber_a_slot(self):
        before=hashlib.sha256(self.path.read_bytes()).hexdigest()
        with self.assertRaisesRegex(ValueError,'Unregistered'):self.storage.journal.write('arbitrary',{})
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)

    def test_source_stage_factory_uses_the_same_registered_paths(self):
        stage=self.root/'.sync/CPU_ONLY';stage.mkdir(parents=True)
        atomic_json(stage/'history104-storage.json',self.config)
        selected=storage_for(stage)
        self.assertEqual(selected.output,self.storage.output)
        self.assertEqual(selected.journal.lock_path,self.storage.journal.lock_path)
        with self.assertRaisesRegex(ValueError,'stage required'):storage_for(self.root/'FOREIGN')

    def test_two_CPU_process_writers_retain_both_final_records(self):
        code='''import json,sys,time
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from wcomr.sq_control_storage_r1 import SQStorageGuard
config=json.loads(sys.argv[2]);guard=SQStorageGuard(config,sys.argv[3]);go=Path(sys.argv[4])
until=time.monotonic()+20
while not go.exists():
 if time.monotonic()>until:raise TimeoutError('CPU barrier')
 time.sleep(.01)
for i in range(8):guard.journal.write(sys.argv[5],dict(CPU_fixture=True,writer=sys.argv[5],index=i))
'''
        go=self.root/'go';children=[]
        try:
            for key in ('allocation_release','pending_release'):
                child=subprocess.Popen([sys.executable,'-c',code,str(ROOT/'src'),json.dumps(self.config),
                    str(self.root/'.sync/gpu-locks'),str(go),key],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                children.append(child);EVENTS.append(dict(kind='ACTUAL_JOURNAL_CPU_WRITER',pid=child.pid,process=child))
            go.touch()
            for child in children:
                out,error=child.communicate(timeout=30);self.assertEqual(child.returncode,0,error.decode())
            for key in ('allocation_release','pending_release'):
                self.assertEqual(self.storage.journal.read(key),dict(CPU_fixture=True,writer=key,index=7))
        finally:
            for child in children:
                if child.poll() is None:child.kill();child.wait()


if __name__=='__main__':unittest.main()
