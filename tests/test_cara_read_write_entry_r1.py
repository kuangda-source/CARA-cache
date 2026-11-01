"""M1 entry metadata and prospective container controls; no Docker/GPU jobs."""
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import cara_read_write_container_r1 as container
import cara_read_write_supervisor_worker_r1 as worker
from wcomr import cara_read_write_runner_binding_r1 as binding
from wcomr import cara_read_write_dispatch_r1 as dispatch
from wcomr import cara_budget_dispatch_r1 as original_dispatch
from wcomr import cara_budget_original_handles_r1 as handles
from wcomr import cara_s_endpoint_supervisor_r1 as supervisor
from wcomr import history104_storage_r2 as storage_module
from wcomr.cara_budget_host_policy_r1 import POLICY_SHA256
from wcomr.gpu_budget_pool_v2 import atomic_json, sha


class Fixture:
    def __init__(self, project):
        self.project = Path(project)
        self.stage = self.project/'.sync/cara-read-write-M1-GPU-CPU-metadata'
        self.stage.mkdir(parents=True)
        (self.project/'runtime').mkdir()
        (self.project/'runtime/CPU.py').write_text('# explicit metadata fixture, no production authority\n')
        names = set(binding.REQUIRED+dispatch.REQUIRED)
        for name in names:
            target = self.stage/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, target)
        self.card = json.loads((self.stage/binding.CARD).read_text())
        self.profile = json.loads((self.stage/binding.PROFILE).read_text())
        self.reg = dict(host='two_card', stage=str(self.stage), source_revision='b'*40, container_image=binding.IMAGE,
            payload_sha256={n:sha(self.stage/n) for n in names},
            runtime_source_sha256={'CPU.py':sha(self.project/'runtime/CPU.py')})
        self.auth = dict(run_id='cara-read-write-M1-cpu-metadata', launch_id='a'*32, host='two_card', gpu_uuid=binding.GPU,
            stage=str(self.stage), source_revision='b'*40, scope_sha256=self.card['scope_sha256'], billed_limit_GPUh=1.95,
            physical_paths=14, CPU_fixture_only=False, execution_authorized=True, authorizes_replay=False,
            card_kind='CARA_READ_WRITE_M1_FULL14', authorization_basis='USER_STANDING_BELOW2_GPUH_MAINLINE',
            user_quote='EXPLICIT CPU METADATA FIXTURE, NOT USER AUTHORITY', execution_host_policy_sha256=POLICY_SHA256)
        self.proof = dict(passed=True, whole_card_CPU_accepted=True, host='two_card', scope_sha256=self.card['scope_sha256'],
            payload_sha256=self.reg['payload_sha256'], runtime_source_sha256=self.reg['runtime_source_sha256'],
            execution_host_policy_sha256=POLICY_SHA256, actual_module_full14_accepted=True,
            loaded_runner_accepted=True, dispatch_finance_release_accepted=True, postrelease_eight_pair_scorer_accepted=True)
        self.quote = json.loads((ROOT/'plans/cara_next_stage_20261101/read_write/M1_FULL14_WHOLE_QUOTE_DRAFT_R2.json').read_text())
        self.quote.update(whole_quote_accepted=True, hard_GPUh=1.95)
        self.storage = SimpleNamespace(output=self.project/'outputs'/self.auth['run_id'],
            journal=SimpleNamespace(path=self.project/'reports/M1-CPU.journal'), check=lambda:None)
        self.storage.config = dict(output_mount=str(self.storage.output), image_path=str(self.project/'private16.ext4'),
            image_bytes=16*2**30, journal_path=str(self.storage.journal.path), journal_bytes=48*2**20,
            minimum_output_free_bytes=4*2**30, minimum_host_free_bytes=16*2**30, minimum_free_inodes=1024)
        self.write_all()

    def write_all(self):
        atomic_json(self.stage/'registration.json', self.reg)
        atomic_json(self.stage/'execution-CPU-proof.json', self.proof)
        atomic_json(self.stage/'whole-quote.json', self.quote)
        self.auth.update(CPU_proof_sha256=sha(self.stage/'execution-CPU-proof.json'), quote_sha256=sha(self.stage/'whole-quote.json'))
        atomic_json(self.stage/'GPU-authorization.json', self.auth)
        atomic_json(self.stage/'fresh-admission.json', dict(CPU_metadata_fixture=True))
        self.launch = {k:self.auth[k] for k in binding.IDENTITY}
        self.launch.update(CPU_fixture_only=False, physical_paths=14,
            authorization_sha256=sha(self.stage/'GPU-authorization.json'), registration_sha256=sha(self.stage/'registration.json'),
            admission_sha256=sha(self.stage/'fresh-admission.json'))
        job = {k:self.launch[k] for k in binding.JOB_IDENTITY}
        job.update(job_id=self.auth['run_id'], status='RESERVED_OR_RUNNING')
        atomic_json(self.stage/'central-reservation.json', dict(central_ledger_host='four_card', new_reservation=True, job=job))
        self.launch['central_reservation_sha256'] = sha(self.stage/'central-reservation.json')
        atomic_json(self.stage/'GPU-launch.json', self.launch)

    def command(self):
        return container.container_arguments(project=self.project, stage=self.stage, storage=self.storage,
            registration_sha=sha(self.stage/'registration.json'), profile=self.profile, host='two_card',
            run_id=self.auth['run_id'], uuid=binding.GPU, uid=os.getuid(), gid=os.getgid())


class Entry(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(self.temp.name)

    def test_exact14_source_bound_context(self):
        card, launch, profile, context = binding.validate(self.f.project, self.f.stage)
        self.assertEqual(card['counts']['physical_model_pairs'], 512)
        self.assertEqual((context['phase'], context['physical_paths']), ('READ_WRITE_M1', 14))
        self.assertEqual(profile['storage']['output_image_bytes'], 16*2**30)

    def test_all_affected_CPU_gates_and_closed_whole_quote_required(self):
        for key in ('passed', 'whole_card_CPU_accepted', 'actual_module_full14_accepted', 'loaded_runner_accepted',
                    'dispatch_finance_release_accepted', 'postrelease_eight_pair_scorer_accepted'):
            self.f.proof[key] = False
            self.f.write_all()
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'CPU acceptance'):
                binding.validate(self.f.project, self.f.stage)
            self.f.proof[key] = True
        self.f.quote['whole_quote_accepted'] = False
        self.f.write_all()
        with self.assertRaisesRegex(ValueError, 'whole M1 quote'):
            binding.validate(self.f.project, self.f.stage)

    def test_old_cards_other_host_or_replay_are_not_authority(self):
        for key, value in [('card_kind', 'CARA_SU19_BUDGET_ENDPOINT'), ('host', 'four_card'),
                           ('authorizes_replay', True), ('execution_authorized', False),
                           ('CPU_fixture_only', True), ('billed_limit_GPUh', 2.0)]:
            original = self.f.auth[key]
            self.f.auth[key] = value
            self.f.write_all()
            with self.subTest(key=key), self.assertRaises(ValueError):
                binding.validate(self.f.project, self.f.stage)
            self.f.auth[key] = original

    def test_runtime_source_and_admission_mutation_refused(self):
        for path in (self.f.project/'runtime/CPU.py', self.f.stage/binding.LOADED, self.f.stage/'fresh-admission.json'):
            raw = path.read_bytes()
            path.write_bytes(raw+b' ')
            with self.subTest(path=str(path)), self.assertRaises(ValueError):
                binding.validate(self.f.project, self.f.stage)
            path.write_bytes(raw)

    def test_changed_original_reservation_refused(self):
        value = json.loads((self.f.stage/'central-reservation.json').read_text())
        value['job']['launch_id'] = 'f'*32
        atomic_json(self.f.stage/'central-reservation.json', value)
        self.f.launch['central_reservation_sha256'] = sha(self.f.stage/'central-reservation.json')
        atomic_json(self.f.stage/'GPU-launch.json', self.f.launch)
        with self.assertRaisesRegex(ValueError, 'reservation'):
            binding.validate(self.f.project, self.f.stage)

    def test_exact_command_is_nonexecuting_single_gpu_zero_swap(self):
        with patch.object(subprocess, 'run', side_effect=AssertionError('Builder executed')):
            command = self.f.command()
        for key, value in [('--cpus', '2'), ('--cpuset-cpus', '24,25'), ('--memory', '40g'),
            ('--memory-swap', '40g'), ('--network', 'none'), ('--pid', 'host'),
            ('--gpus', 'device='+binding.GPU), ('--cidfile', str(self.f.stage/'container.cid'))]:
            self.assertEqual(command.count(key), 1)
            self.assertEqual(command[command.index(key)+1], value)
        self.assertIn('--read-only', command)
        self.assertNotIn('--privileged', command)
        self.assertIn('CUDA_VISIBLE_DEVICES=', command)
        self.assertEqual(command[-5:], [str(self.f.stage/container.WORKER), '--project', str(self.f.project), '--stage', str(self.f.stage)])
        volumes = [command[i+1] for i, value in enumerate(command) if value == '-v']
        writable = {value[:-3] for value in volumes if value.endswith(':rw')}
        self.assertEqual(writable, {str(p)+':'+str(p) for p in
            (self.f.stage, self.f.storage.output, self.f.storage.journal.path, self.f.project/'.sync/gpu-locks')})
        for p in (self.f.stage/'src', self.f.stage/'scripts'):
            self.assertIn(str(p)+':'+str(p)+':ro', volumes)

    def test64GiB_or_reduced_lowwater_cannot_be_substituted(self):
        for key, value in [('image_bytes', 64*2**30), ('minimum_output_free_bytes', 1),
                           ('minimum_host_free_bytes', 1), ('journal_bytes', 1)]:
            original = self.f.storage.config[key]
            self.f.storage.config[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'contract differs'):
                self.f.command()
            self.f.storage.config[key] = original

    def test_profile_cannot_expand_scope_hard_limit_or_memory(self):
        for key, value in [('physical_paths', 13), ('physical_model_pairs', 504), ('hard_GPUh', 2),
                           ('temperature_stop_C', 91)]:
            original = self.f.profile[key]
            self.f.profile[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.f.command()
            self.f.profile[key] = original

    def test_original_unknown_recovery_precedes_all_admission_and_submission(self):
        unknown = dict(status='ORIGINAL_DISPATCH_RECOVER_ONLY', guardian_observation={'original_live':None})
        with patch.object(dispatch, 'recover', return_value=unknown), \
             patch.object(dispatch, 'ready_inputs', side_effect=AssertionError('New admission after intent')), \
             patch.object(dispatch.subprocess, 'Popen', side_effect=AssertionError('New child after intent')):
            result = dispatch.dispatch(self.f.project, self.f.stage, {}, None)
        self.assertEqual(result, unknown)

    def test_original_intent_and_child_are_not_repeated(self):
        # No production processes: the child is an explicit in-memory sink.
        (self.f.stage/'GPU-launch.json').unlink()
        child = SimpleNamespace(pid=123456, stdin=io.BytesIO())
        commands = dict(container_cli=['EXPLICIT_CPU_FIXTURE_NO_DOCKER'], runner=['EXPLICIT_CPU_FIXTURE_NO_GPU'])
        with patch.object(dispatch, 'ready_inputs', return_value=(self.f.card, self.f.reg, self.f.auth, self.f.profile)), \
             patch.object(dispatch, 'central_binding'), patch.object(dispatch, 'fresh_resources', return_value=(self.f.storage, {})), \
             patch.object(dispatch, 'frozen_commands', return_value=commands), \
             patch.object(dispatch, 'bind_original_process', side_effect=lambda pid:dict(pid=pid, start_ticks=1, host_view='CPU')), \
             patch.object(original_dispatch, 'observe_original_process', return_value={'original_live':None}), \
             patch.object(dispatch.subprocess, 'Popen', return_value=child) as spawn:
            first = dispatch.dispatch(self.f.project, self.f.stage, {}, 'EXPLICIT_CPU_FAKE_SECRET')
            second = dispatch.dispatch(self.f.project, self.f.stage, {}, 'EXPLICIT_CPU_FAKE_SECRET')
        self.assertEqual(spawn.call_count, 1)
        self.assertEqual(first['status'], 'ORIGINAL_GUARDIAN_DISPATCHED_AWAIT_LAUNCH')
        self.assertEqual(second['status'], 'ORIGINAL_DISPATCH_RECOVER_ONLY')
        self.assertNotIn('EXPLICIT_CPU_FAKE_SECRET', (self.f.stage/'GPU-intent.json').read_text())

    def test_worker_checks_original_guardian_source_and_command_before_supervision(self):
        self.f.launch.update(guardian_identity={'EXPLICIT_CPU_METADATA':True}, commands={'container_cli':self.f.command()})
        atomic_json(self.f.stage/'GPU-launch.json', self.f.launch)
        with patch.object(sys, 'argv', ['worker', '--project', str(self.f.project), '--stage', str(self.f.stage)]), \
             patch.dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES=binding.GPU), \
             patch.object(storage_module, 'storage_for', return_value=self.f.storage), \
             patch.object(handles, 'observe_original_process', return_value={'original_live':True}), \
             patch.object(supervisor, 'supervise') as supervise:
            worker.main()
            supervise.assert_called_once_with(self.f.project, self.f.stage, self.f.storage)
        for live in (None, False):
            with patch.object(sys, 'argv', ['worker', '--project', str(self.f.project), '--stage', str(self.f.stage)]), \
                 patch.dict(os.environ, CUDA_VISIBLE_DEVICES='', NVIDIA_VISIBLE_DEVICES=binding.GPU), \
                 patch.object(handles, 'observe_original_process', return_value={'original_live':live}), \
                 patch.object(supervisor, 'supervise', side_effect=AssertionError('Dead guardian started worker')):
                with self.subTest(live=live), self.assertRaisesRegex(ValueError, 'guardian must still be live'):
                    worker.main()

    def test16GiB_fresh_boundary_refuses_old64GiB_before_gpu_probe(self):
        self.f.storage.config['image_bytes'] = 64*2**30
        with patch.object(dispatch, 'storage_for', return_value=self.f.storage), \
             patch.object(dispatch, 'selected_gpu', side_effect=AssertionError('Probed after invalid storage')):
            with self.assertRaisesRegex(ValueError, 'Original16GiB'):
                dispatch.fresh_resources(self.f.project, self.f.stage, self.f.auth, self.f.profile)


if __name__ == '__main__':
    unittest.main()
