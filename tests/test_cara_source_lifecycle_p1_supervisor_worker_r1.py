"""Actual P1 worker entry checks with an explicit simulated supervisor call."""
import copy
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cara_source_lifecycle_p1_supervisor_worker_r1 as worker
from cara_source_lifecycle_p1_container_r1 import container_arguments,SOURCE,WORKER
import test_cara_source_lifecycle_p1_entry_r1 as entry_fixture
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr import cara_budget_original_handles_r1 as handles
from wcomr import cara_s_endpoint_supervisor_r1 as supervisor
from wcomr import history104_storage_r2 as storage
from wcomr.gpu_budget_pool_v2 import atomic_json,sha

ROOT=Path(__file__).resolve().parents[1]


class P1SupervisorWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f=entry_fixture.Fixture(self.temp.name)
        for name in (SOURCE,WORKER):
            path=self.f.stage/name;path.write_bytes((ROOT/name).read_bytes());self.f.reg['payload_sha256'][name]=sha(path)
        self.f.write()
        self.f.storage.config.update(output_mount=str(self.f.output),journal_path=str(self.f.stage/'P1-journal'),
            image_path=str(self.f.stage/'P1-private.ext4'))
        self.f.storage.journal=SimpleNamespace(path=self.f.stage/'P1-journal')
        self.expected=container_arguments(project=self.f.project,stage=self.f.stage,storage=self.f.storage,
            registration_sha=sha(self.f.stage/'registration.json'),profile=self.f.profile,host='two_card',
            run_id=self.f.authority['run_id'],uuid=self.f.authority['gpu_uuid'],uid=os.getuid(),gid=os.getgid())
        self.f.launch['commands']=dict(container_cli=self.expected)
        atomic_json(self.f.stage/'GPU-launch.json',self.f.launch)
        self.calls=[]

    def run_entry(self,*,live=True,cuda=''):
        with patch.object(sys,'argv',['worker','--project',str(self.f.project),'--stage',str(self.f.stage)]),\
                patch.dict(os.environ,CUDA_VISIBLE_DEVICES=cuda,NVIDIA_VISIBLE_DEVICES=self.f.authority['gpu_uuid']),\
                patch.object(handles,'observe_original_process',return_value=dict(original_live=live)),\
                patch.object(storage,'storage_for',return_value=self.f.storage),\
                patch.object(supervisor,'supervise',side_effect=lambda *args:self.calls.append(args)):
            worker.main()

    def test_entry_reuses_only_the_original_registered_supervisor(self):
        self.run_entry()
        self.assertEqual(self.calls,[(self.f.project,self.f.stage,self.f.storage)])

    def test_unknown_or_ended_guardian_never_starts_supervisor(self):
        for live in (None,False):
            with self.subTest(live=live),self.assertRaisesRegex(ValueError,'guardian must remain live'):self.run_entry(live=live)
        self.assertEqual(self.calls,[])

    def test_cuda_exposure_or_changed_frozen_command_is_refused(self):
        with self.assertRaisesRegex(ValueError,'GPU-hidden'):self.run_entry(cuda=self.f.authority['gpu_uuid'])
        value=copy.deepcopy(self.f.launch);value['commands']['container_cli'][-1]='CHANGED'
        atomic_json(self.f.stage/'GPU-launch.json',value)
        with self.assertRaisesRegex(ValueError,'frozen container command'):self.run_entry()
        self.assertEqual(self.calls,[])

    def test_changed_source_or_old_card_authority_is_refused_before_supervisor(self):
        path=self.f.stage/WORKER;path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(ValueError):self.run_entry()
        self.assertEqual(self.calls,[])


if __name__=='__main__':unittest.main()
