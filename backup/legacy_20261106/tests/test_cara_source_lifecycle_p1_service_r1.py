"""P1 service binding and original-only cleanup, without GPU or Docker work."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from wcomr.cara_budget_search_journal_r1 import OriginalQueryUnknown, create_record, read_record
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from wcomr import cara_source_lifecycle_p1_service_r1 as service

ROOT = Path(__file__).resolve().parents[1]


class HeldFITServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)/'project'
        self.stage = self.project/'.sync'/'P1_CPU_SERVICE_FIXTURE'
        self.stage.mkdir(parents=True)
        self.identity = dict(pid=100, start_ticks=200, host_view=dict(unit='fixture'))
        self.card = json.loads((ROOT/service.CARD).read_bytes())
        for name in (service.CARD, service.PRECISION):
            target = self.stage/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT/name).read_bytes())
        self.registration = dict(payload_sha256={service.SOURCE:file_sha(ROOT/service.SOURCE),
            service.CARD:file_sha(self.stage/service.CARD),service.PRECISION:file_sha(self.stage/service.PRECISION)})
        create_record(self.stage/'registration.json', self.registration)
        self.launch = dict(run_id='P1_CPU_SERVICE_FIXTURE', launch_id='a'*32, host='two_card',
            gpu_uuid='GPU-CPU-FIXTURE', stage=str(self.stage), source_revision='b'*40,
            scope_sha256=self.card['scope_sha256'], billed_limit_GPUh=14., guardian_identity=self.identity,
            CPU_fixture_only=False, admission_sha256='c'*64, registration_sha256=file_sha(self.stage/'registration.json'))
        self.authority = {k:self.launch[k] for k in ('run_id','launch_id','host','gpu_uuid','stage','source_revision','scope_sha256','billed_limit_GPUh')}
        self.authority.update(CPU_fixture_only=False, card_kind=service.KIND, execution_authorized=True,
            authorization_basis='DIRECT_USER_SINGLE_CARD', user_quote='EXPLICIT SYNTHETIC LOCAL TEST ONLY',authorizes_replay=False)
        create_record(self.stage/'GPU-authorization.json', self.authority)
        self.launch['authorization_sha256'] = file_sha(self.stage/'GPU-authorization.json')
        create_record(self.stage/'GPU-launch.json', self.launch)
        self.guardian = {k:self.launch[k] for k in ('run_id','launch_id','host','gpu_uuid','stage','source_revision','scope_sha256','billed_limit_GPUh')}
        self.guardian.update(started_monotonic=100., original_handles=dict(guardian=self.identity))
        self.environment = dict(torch_home='/CPU/torch', piq_site='/CPU/site', weights_sha256={})

    def test_new_card_uses_one_original_epoch_and_exact_shared_runner_context(self):
        with patch.object(service, 'bind_original_process', return_value=self.identity), \
                patch.object(service, 'OriginalAllocationClock') as clock:
            spec, actual_clock = service.binding(self.project,self.stage,self.guardian,self.environment)
        self.assertIs(actual_clock, clock.return_value)
        self.assertEqual(spec['work_stop_monotonic'], 100.+14*3600-600)
        self.assertEqual(spec['context']['model_precision_sha256'], json.loads((self.stage/service.PRECISION).read_bytes())['precision_sha256'])
        self.assertEqual(spec['context']['guardian_started_monotonic'], 100.)
        self.assertEqual(spec['context']['admission_sha256'], self.launch['admission_sha256'])
        self.assertEqual(spec['artifact_root'],str(self.project/'outputs'/'P1_CPU_SERVICE_FIXTURE'/'algorithm'))
        self.environment['weights_sha256']['changed'] = 'd'*64
        self.assertEqual(spec['environment']['weights_sha256'], {})

    def test_old_card_authority_or_another_guardian_cannot_start_service(self):
        for fault in ('old_card','old_basis','replay','wrong_guardian'):
            authority = copy.deepcopy(self.authority)
            identity = self.identity
            if fault=='old_card': authority['card_kind']='CARA_READ_WRITE_M1_FULL14'
            if fault=='old_basis': authority['authorization_basis']='USER_STANDING_BELOW2_GPUH_MAINLINE'
            if fault=='replay': authority['authorizes_replay']=True
            if fault=='wrong_guardian': identity=dict(self.identity,pid=999)
            read = read_record
            def fixture(path):
                if Path(path).name=='GPU-authorization.json': return authority
                return read(path)
            with self.subTest(fault=fault), patch.object(service,'read_record',side_effect=fixture), \
                    patch.object(service,'bind_original_process',return_value=identity), \
                    patch.object(service,'subprocess') as processes:
                with self.assertRaises(ValueError):
                    service.binding(self.project,self.stage,self.guardian,self.environment)
                processes.Popen.assert_not_called()

    def prepared(self):
        held = service.HeldFITService(self.project,self.stage,self.environment)
        output = self.project/'outputs'/'P1_CPU_SERVICE_FIXTURE'
        queue = output/'internal-FIT-queue'
        queue.mkdir(parents=True)
        held.spec = dict(project=str(self.project),stage=str(self.stage),queue=str(queue),
            artifact_root=str(output/'algorithm'),context=dict(run_id='P1_CPU_SERVICE_FIXTURE'))
        held.identity = self.identity
        held.child = Mock()
        held.child.returncode = 0
        held.clock = Mock()
        return held,queue

    def test_cleanup_seals_original_stop_once_and_never_creates_another_child(self):
        held,queue = self.prepared()
        create_record(queue/'service-terminal.json',dict(binding_sha256=digest(held.spec),error=None,ended_unix=123.))
        with patch.object(service,'observe_original_process',return_value=dict(original_live=False)), \
                patch.object(service,'subprocess') as processes:
            result = held.close()
            self.assertTrue(result['complete'])
            self.assertEqual(result['identity'],self.identity)
            self.assertFalse(result['new_GPU_bill'])
            with self.assertRaises(OriginalQueryUnknown): held.close()
            processes.Popen.assert_not_called()
        self.assertEqual(read_record(queue/'stop-request.json'),dict(context_sha256=digest(held.spec['context'])))
        self.assertEqual(read_record(queue/'guardian-service-closed.json'),result)

    def test_missing_original_child_or_cpu_cleanup_witness_retains_unknown(self):
        held,queue = self.prepared()
        held.child = None
        with self.assertRaisesRegex(OriginalQueryUnknown,'child witness'): held.close()
        self.assertFalse((queue/'guardian-service-closed.json').exists())
        held,queue = service.HeldFITService(self.project,self.stage,self.environment),queue
        held.start_attempted = True
        with self.assertRaises(OriginalQueryUnknown): held.start(self.guardian)

    def test_unresolved_query_prevents_claiming_full_service_cleanup(self):
        held,queue = self.prepared()
        create_record(queue/'service-terminal.json',dict(binding_sha256=digest(held.spec),error=None,ended_unix=123.))
        query = queue/('score-'+'e'*64)
        query.mkdir()
        create_record(query/'status.json',dict(status='ORIGINAL_CPU_ACTIVE'))
        with patch.object(service,'observe_original_process',return_value=dict(original_live=False)):
            with self.assertRaisesRegex(OriginalQueryUnknown,'query closure'): held.close()
        self.assertFalse((queue/'guardian-service-closed.json').exists())


if __name__ == '__main__':
    unittest.main()
