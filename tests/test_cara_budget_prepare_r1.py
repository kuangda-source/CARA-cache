"""Source staging, immutable recovery and pre-approval separation on local CPU."""
import copy
import io
import json
import os
from pathlib import Path
import tarfile
import tempfile
import time
import unittest
from unittest.mock import patch

from wcomr import cara_budget_prepare_r1 as prepare
from wcomr import cara_budget_central_r1 as central
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr.gpu_budget_pool_v2 import sha
from wcomr.immutable_stage_payload_r1 import overlay_bytes

ROOT=Path(__file__).resolve().parents[1]


class PreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template=prepare.source_plan(ROOT,'a'*64,'b'*40)
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w:gz') as tar:
            for name in cls.template['overlay_sha256']:
                raw=(ROOT/name).read_bytes();member=tarfile.TarInfo(name);member.size=len(raw)
                tar.addfile(member,io.BytesIO(raw))
        cls.archive=stream.getvalue()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name);self.base=self.project/'.sync/base-CPU'
        self.base.mkdir(parents=True);(self.project/'runtime').mkdir()
        (self.base/'original.txt').write_text('Original untouched base')
        (self.project/'runtime/pinned.py').write_text('# Pinned runtime\n')
        self.reg=dict(host='two_card',stage=str(self.base),source_revision='b'*40,
            payload_sha256={'original.txt':sha(self.base/'original.txt')},
            runtime_source_sha256={'pinned.py':sha(self.project/'runtime/pinned.py')})
        self.update_base()
        self.observations={host:dict(host=host,stage=str(self.project/'.sync'/stage),run_id=central.RUN,
            observation_complete=True,observed_unix=time.time(),dispatch_records=[],container=None)
            for host,stage in central.STAGES.items() if host in prepare.HOSTS}

    def update_base(self):
        (self.base/'registration.json').write_text(json.dumps(self.reg,indent=2)+'\n')
        self.plan=dict(self.template,base_registration_sha256=sha(self.base/'registration.json'))

    def install(self,host='two_card'):
        return prepare.prepare(self.project,host,self.base,self.archive,self.plan,'c'*40,self.observations)

    def test_source_plan_has_transitive_local_imports_and_all_new_entries(self):
        files=self.plan['overlay_sha256']
        for name in (*prepare.EXTRA,'src/wcomr/cara_budget_lifecycle_r1.py',
                     'src/wcomr/wc73_execution_r1.py','tests/test_cara_budget_dispatch_r1.py'):
            self.assertIn(name,files)
        self.assertEqual(set(overlay_bytes(self.archive,self.plan)),set(files))
        self.assertFalse(self.plan['execution_authorized'])

    def test_selected_host_stage_is_complete_immutable_and_grants_no_GPU_authority(self):
        original=(self.base/'original.txt').read_bytes()
        for host in prepare.HOSTS:
            self.reg['host']=host;self.update_base()
            registration=self.install(host);stage=Path(registration['stage'])
            self.assertEqual(registration['host'],host)
            self.assertEqual(registration['GPU_submissions_by_installer'],0)
            self.assertFalse((stage/'GPU-authorization.json').exists())
            self.assertFalse((stage/'GPU-launch.json').exists())
            self.assertEqual(self.install(host),registration)
            self.assertEqual((self.base/'original.txt').read_bytes(),original)
            self.assertTrue(all(sha(stage/n)==h for n,h in registration['payload_sha256'].items()))

    def test_changed_runtime_or_existing_payload_is_not_silently_refreshed(self):
        registration=self.install();stage=Path(registration['stage'])
        path=stage/prepare.SOURCE;path.write_bytes(path.read_bytes()+b'\n')
        with self.assertRaisesRegex(ValueError,'Existing or partial stage'):self.install()
        path.write_bytes((ROOT/prepare.SOURCE).read_bytes())
        (self.project/'runtime/pinned.py').write_text('# Changed runtime')
        with self.assertRaisesRegex(ValueError,'runtime differs'):self.install()

    def test_partial_stage_and_symlink_are_preserved_and_refused(self):
        stage=self.project/'.sync'/central.STAGES['two_card'];stage.mkdir()
        (stage/'partial.txt').write_text('Keep original partial evidence')
        with self.assertRaises(ValueError):self.install()
        self.assertEqual((stage/'partial.txt').read_text(),'Keep original partial evidence')
        (stage/'partial.txt').unlink();stage.rmdir()
        stage.symlink_to(self.base,target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):self.install('two_card')

    def test_original_selected_dispatch_or_unknown_prevents_preparation(self):
        self.observations['two_card']['dispatch_records']=['GPU-intent.json']
        with self.assertRaises(ValueError):self.install()
        self.observations['two_card']['dispatch_records']=[];self.observations['two_card']['observation_complete']=False
        with self.assertRaises(ValueError):self.install()
        self.assertFalse((self.project/'.sync'/central.STAGES['two_card']).exists())

    def test_wrong_base_host_or_corrupt_archive_does_not_create_stage(self):
        with self.assertRaisesRegex(ValueError,'Two-card host'):self.install('four_card')
        self.reg['host']='four_card';self.update_base()
        with self.assertRaisesRegex(ValueError,'host/base'):self.install()
        self.reg['host']='two_card';self.update_base()
        self.archive=b'Corrupt transport'
        with self.assertRaises(tarfile.ReadError):self.install()
        self.assertFalse((self.project/'.sync'/central.STAGES['two_card']).exists())

    def test_CPU_base_uses_explicit_parent_marker_and_exact_registration_bytes(self):
        self.reg['parent_git_revision']=self.reg.pop('source_revision');self.update_base()
        self.plan['base_revision_field']='parent_git_revision'
        registration=self.install()
        self.assertEqual(registration['read_only_base_registration_sha256'],sha(self.base/'registration.json'))
        self.assertEqual(registration['source_revision'],'c'*40)

    def test_observer_requires_exact_Docker_absence_and_reports_any_original_intent(self):
        with patch.object(prepare,'inspect_container',side_effect=AssertionError('No four-card probe')):
            with self.assertRaisesRegex(ValueError,'only two-card'):prepare.observe_original(self.project,'four_card')
        with patch.object(prepare,'inspect_container',return_value=None):
            row=prepare.observe_original(self.project,'two_card')
        self.assertTrue(row['observation_complete']);self.assertFalse(row['stage_exists'])
        stage=Path(row['stage']);stage.mkdir();(stage/'GPU-intent.json').write_text('incomplete')
        with patch.object(prepare,'inspect_container',return_value=None):
            self.assertEqual(prepare.observe_original(self.project,'two_card')['dispatch_records'],['GPU-intent.json'])
        with patch.object(prepare,'inspect_container',side_effect=TimeoutError('Daemon observation unavailable')):
            with self.assertRaises(TimeoutError):prepare.observe_original(self.project,'two_card')

    def test_unapproved_design_cannot_bind_production_authority(self):
        registration=self.install();stage=Path(registration['stage'])
        auth=dict(run_id=central.RUN,host='two_card',stage=str(stage),CPU_fixture_only=False,
            execution_authorized=False,direct_user_authorization=False,user_quote='',authorizes_replay=False,billed_limit_GPUh=14)
        with self.assertRaises(ValueError):prepare.bind_authority(self.project,stage,auth,{}, {})
        self.assertFalse((stage/'GPU-authorization.json').exists())


if __name__=='__main__':unittest.main()
