"""P1 original dispatch/publication/resource gates, all GPU calls simulated."""
import copy
import io
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch,Mock

from check_cara_source_lifecycle_p1_outer_fixture_r1 import Fixture
from wcomr import cara_source_lifecycle_p1_dispatch_r1 as dispatch
from wcomr.gpu_budget_pool_v2 import atomic_json,sha
from wcomr.cara_budget_search_journal_r1 import create_record


class P1DispatchTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.f=Fixture(self.temp.name)

    def test_complete_source_CPU_quote_and_commands_before_dispatch(self):
        card,reg,auth,profile,quote=dispatch.ready_inputs(self.f.project,self.f.stage)
        self.assertEqual((sum(card['semantic_positions'].values()),profile['physical_generation_upper']),(146,142))
        commands=dispatch.frozen_commands(self.f.project,self.f.stage,reg,auth,profile,self.f.storage)
        self.assertIn(str(self.f.stage/'scripts/cara_source_lifecycle_p1_supervisor_worker_r1.py'),commands['container_cli'])
        self.assertEqual(commands['runner'][-1],self.f.authority['gpu_uuid'])

    def test_once_intent_unknown_recovery_never_dispatches_again(self):
        _,snapshot=self.f.reserved()
        for name in ('GPU-launch.json','guardian.json'):(self.f.stage/name).unlink()
        child=SimpleNamespace(pid=7777,stdin=io.BytesIO())
        identity=dict(pid=7777,start_ticks=100,host_view=dict(boot_id='12345678-1234-1234-1234-123456789abc',pid_namespace_inode=123))
        with patch.object(dispatch,'fresh_resources',return_value=(self.f.storage,{'GPU_SIMULATED':True})),\
                patch.object(dispatch.subprocess,'Popen',return_value=child) as spawn,\
                patch.object(dispatch,'bind_original_process',return_value=identity),\
                patch('wcomr.cara_budget_dispatch_r1.observe_original_process',return_value=dict(original_live=None)):
            first=dispatch.dispatch(self.f.project,self.f.stage,snapshot,'EXPLICIT_CPU_CREDENTIAL')
            self.assertEqual(first['status'],'ORIGINAL_GUARDIAN_DISPATCHED_AWAIT_LAUNCH')
            intent_sha=sha(self.f.stage/'GPU-intent.json')
            # recover() uses the original launch/dispatch witnesses. A missing
            # bootstrap is UNKNOWN, and must never authorize a second child.
            second=dispatch.dispatch(self.f.project,self.f.stage,snapshot,'CPU')
            self.assertEqual(second['status'],'ORIGINAL_DISPATCH_RECOVER_ONLY')
            self.assertFalse(second['authorizes_retry'])
            self.assertEqual(spawn.call_count,1);self.assertEqual(sha(self.f.stage/'GPU-intent.json'),intent_sha)

    def test_publish_original_launch_before_FIT_queue_exists(self):
        _,snapshot=self.f.reserved()
        commands=dispatch.frozen_commands(self.f.project,self.f.stage,self.f.reg,self.f.authority,self.f.profile,self.f.storage)
        identity=dict(pid=7777,start_ticks=100,host_view={'EXPLICIT_CPU_ONLY':True})
        intent={k:self.f.authority[k] for k in dispatch.IDENTITY}
        intent.update(semantic_positions=146,physical_generation_upper=142,admission_sha256=sha(self.f.stage/'fresh-admission.json'),
            registration_sha256=sha(self.f.stage/'registration.json'),authorization_sha256=sha(self.f.stage/'GPU-authorization.json'),
            central_reservation_sha256=sha(self.f.stage/'central-reservation.json'),commands=commands,
            central_snapshot=snapshot,CPU_fixture_only=False,no_replay=True)
        create_record(self.f.stage/'GPU-intent.json',intent)
        create_record(self.f.stage/'GPU-dispatch.json',dict(guardian_identity=identity,intent_sha256=sha(self.f.stage/'GPU-intent.json'),launch_id=self.f.authority['launch_id']))
        (self.f.stage/'GPU-launch.json').unlink()
        # The model's later binding requires a running guardian and FIT queue;
        # publication must work before either exists, then allocate starts them.
        import shutil
        shutil.rmtree(self.f.queue)
        with patch.object(dispatch,'bind_original_process',return_value=identity),\
                patch.object(dispatch,'storage_for',return_value=self.f.storage):
            launch,storage=dispatch.publish_launch(self.f.project,self.f.stage)
        self.assertEqual(launch['guardian_identity'],identity)
        self.assertEqual(launch['semantic_positions'],146)
        self.assertFalse(self.f.queue.exists())

    def test_changed_CPU_gate_or_environment_cannot_be_dispatched(self):
        self.f.proof['production_total_entry_CPU_accepted']=False;self.f.write()
        with self.assertRaisesRegex(ValueError,'CPU'):dispatch.ready_inputs(self.f.project,self.f.stage)
        self.f.proof['production_total_entry_CPU_accepted']=True;self.f.write()
        path=self.f.stage/dispatch.ENVIRONMENT;path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'environment'):dispatch.ready_inputs(self.f.project,self.f.stage)

    def resource_call(self,*,memory_GiB=52,cores=(24,25,26,27),busy=False):
        admission=self.f.admission()
        atomic_json(self.f.stage/'fresh-admission.json',dict(registration_sha256=sha(self.f.stage/'registration.json'),
            authorization_sha256=sha(self.f.stage/'GPU-authorization.json'),asset_spec_sha256=sha(self.f.stage/dispatch.ASSETS),assets=[]))
        gpu=admission['resources']['gpu'];gpu['pids']=[999] if busy else []
        observation=dict(gpu_uuid=self.f.authority['gpu_uuid'],compute_apps=[],mps_processes=[])
        original_read=Path.read_text;original_sha=dispatch.sha
        def read(path,*args,**kwargs):
            return 'MemAvailable: '+str(memory_GiB*2**20)+' kB\n' if str(path)=='/proc/meminfo' else original_read(path,*args,**kwargs)
        def hashed(path):return self.f.environment['weights_sha256'].get(str(path)) or original_sha(path)
        piq=Path(self.f.environment['piq_site'])/'piq/__init__.py';piq.parent.mkdir(parents=True,exist_ok=True);piq.write_text('# CPU fixture')
        with patch.object(dispatch,'storage_for',return_value=self.f.storage),patch.object(dispatch,'assets_unchanged'),\
                patch.object(dispatch,'english_resources'),patch.object(dispatch,'selected_gpu',return_value=gpu),\
                patch.object(dispatch,'observe',return_value=observation),patch.object(dispatch,'DeviceLease'),\
                patch.object(dispatch.subprocess,'check_output',return_value='[{"Id":"'+self.f.profile['GPU_container']['image']+'"}]'),\
                patch('wcomr.cara_budget_lifecycle_capture_r1.inspect_container',return_value=None),\
                patch.object(dispatch.os,'sched_getaffinity',return_value=set(cores),create=True),\
                patch.object(Path,'read_text',read),patch.object(dispatch,'sha',side_effect=hashed):
            return dispatch.fresh_resources(self.f.project,self.f.stage,self.f.authority,self.f.profile)

    def test_fresh_combined_GPU_and_sidecar_CPU_resources_are_required(self):
        storage,observed=self.resource_call()
        self.assertEqual(observed['MemAvailable_bytes'],52*2**30)
        with self.assertRaisesRegex(ValueError,'CPU/memory'):self.resource_call(memory_GiB=51)
        with self.assertRaisesRegex(ValueError,'CPU/memory'):self.resource_call(cores=(24,25))
        with self.assertRaisesRegex(ValueError,'idle'):self.resource_call(busy=True)


if __name__=='__main__':unittest.main()
