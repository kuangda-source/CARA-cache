"""Fixed CPU command/container/recovery and queue controls; no Docker dispatch."""
import copy
from pathlib import Path
import json
import os
import shutil
import time
import unittest
from unittest.mock import patch

from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest, profile_from, uniform_mask, policy_from_mask
from wcomr.cara_budget_search_journal_r1 import create_record, read_record, OriginalQueryUnknown
from wcomr.cara_read_write_score_capture_r1 import IMAGE, container_time
from wcomr.cara_source_lifecycle_fit_scores_r1 import bind_scorer
from wcomr.cara_source_lifecycle_fit_broker_r1 import (
    REQUIRED, Client, Host, prepare, paths, score_command, validate_container,
    validate_query, operational_status, status_file,
)
import test_cara_source_lifecycle_fit_scores_r1 as score_fixture

ROOT = Path(__file__).resolve().parents[1]


class FitBrokerTests(unittest.TestCase):
    def setUp(self):
        score_fixture.SourceLifecycleFitScoreTests.setUp(self)
        self.project = Path(self.temp.name)/'project'
        self.stage = self.project/'.sync'/'P1_CPU_BROKER_FIXTURE'
        self.stage.mkdir(parents=True)
        self.artifacts = self.project/'outputs'/'P1_CPU_FIXTURE'/'algorithm'
        self.artifacts.mkdir(parents=True)
        parent = json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_bytes())
        profile = profile_from(parent['profile'])
        dense, _ = uniform_mask(parent['schedule'], profile, 19)
        policy = policy_from_mask(profile, dense)
        context = dict(run_id='P1_CPU_FIXTURE', source_revision='1'*40, launch_id='2'*32,
                       host='two_card', scope_sha256='3'*64, CPU_fixture_only=True)
        self.packet['candidate_id'] = policy['fingerprint']
        self.packet['context_sha256'] = digest(context)
        for pair in self.packet['pairs']:
            for side in ('candidate', 'reference'):
                d = pair[side]
                proof = read_record(Path(d['proof_path']))
                video = self.artifacts/Path(d['path']).name
                shutil.move(d['path'], video)
                proof_file = self.artifacts/Path(d['proof_path']).name
                proof.update(context_sha256=digest(context), timing='CLEAN',
                    semantic_history=[dict(actual=a, fallback_reason=None) for a in policy['actions']],
                    candidate_id=policy['fingerprint'] if side == 'candidate' else 'NATIVE35')
                proof['video'] = dict(path=str(video), sha256=file_sha(video))
                create_record(proof_file, proof)
                d.update(candidate_id=proof['candidate_id'], path=str(video), sha256=file_sha(video),
                         proof_path=str(proof_file), proof_sha256=file_sha(proof_file))
        self.environment = {k: self.config[k] for k in ('torch_home', 'piq_site', 'weights_sha256')}
        self.config = bind_scorer(self.packet, self.environment, cpu_validation=True)
        self.result.update(config_sha256=digest(self.config), packet_sha256=digest(self.packet),
                           original_identity=dict(unit_role='worker'))
        for pair, row in zip(self.packet['pairs'], self.result['rows']):
            row.update(candidate=pair['candidate'], reference=pair['reference'])
        for name in REQUIRED:
            target = self.stage/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, target)
        reg = dict(host='two_card', parent_git_revision='1'*40,
            payload_sha256={n: file_sha(self.stage/n) for n in REQUIRED}, runtime_source_sha256={})
        create_record(self.stage/'registration.json', reg)
        self.spec = dict(schema='CARA_V1_INTERNAL_FIT_BROKER_BINDING_R1', CPU_fixture_only=True,
            project=str(self.project), stage=str(self.stage), context=context, profile=parent['profile'],
            queue=str(self.artifacts.parent/'internal-FIT-queue'), artifact_root=str(self.artifacts),
            registration_sha256=file_sha(self.stage/'registration.json'), environment=self.environment,
            work_stop_monotonic=time.monotonic()+1000, uid=os.getuid(), gid=os.getgid())
        prepare(self.spec)
        self.candidate = self.packet['candidate_id']
        self.query, self.output = paths(self.spec, self.candidate)

    def make_query(self):
        self.query.mkdir()
        create_record(self.query/'request.json', self.config)
        self.output.mkdir()
        create_record(self.output/'manifest.json', self.config)
        command = score_command(self.spec, self.config, self.output)
        self.binding = dict(config_sha256=digest(self.config), binding_sha256=digest(self.spec),
                           command=command, command_sha256=digest(command), no_replay=True)
        create_record(self.query/'launch-intent.json', self.binding)
        (self.output/'container.cid').write_text('f'*64+'\n')
        self.cli_identity = dict(unit_role='cli')
        create_record(self.query/'cli-start.json', dict(identity=self.cli_identity,
                     launch_intent_sha256=file_sha(self.query/'launch-intent.json')))
        end = command.index('--entrypoint')
        env = [command[i+1] for i, value in enumerate(command) if value == '-e']
        host = dict(NanoCpus=2*10**9, Memory=8*2**30, MemorySwap=8*2**30,
            CpusetCpus='26,27', DeviceRequests=None, Devices=[], CapAdd=[], Privileged=False,
            NetworkMode='none', PidMode='host', ReadonlyRootfs=True, AutoRemove=False,
            RestartPolicy=dict(Name='no'))
        state = dict(Status='exited', Running=False, Paused=False, Restarting=False, OOMKilled=False,
            Dead=False, Pid=0, ExitCode=0, StartedAt='2026-11-01T20:00:00.000000001Z',
            FinishedAt='2026-11-01T20:00:04.000000001Z')
        self.container = dict(Id='f'*64, Name='/'+command[command.index('--name')+1], Image=IMAGE,
            Config=dict(Labels={'wcomr.manifest': digest(self.config)}, Env=env,
                        WorkingDir=str(self.project/'runtime'), User=str(os.getuid())+':'+str(os.getgid()),
                        Entrypoint=[command[end+1]], Cmd=command[end+3:]), HostConfig=host, State=state,
            Mounts=[dict(Type='bind', Source=str(p), Destination=str(p), RW=rw) for p, rw in
                ((self.project, False), (self.stage, False), (self.output, True))]
                +[dict(Type='tmpfs', Destination='/tmp')])
        create_record(self.query/'cli-terminal.json', dict(identity=self.cli_identity,
            launch_intent_sha256=file_sha(self.query/'launch-intent.json'), exit_code=0, error=None))
        create_record(self.output/'scores-intent.json', dict(config_sha256=digest(self.config),
            original_identity=self.result['original_identity'], no_replay=True))
        self.result.update(started_unix=container_time(state['StartedAt'])+1,
                           ended_unix=container_time(state['FinishedAt'])-1)
        create_record(self.output/'scores.json', self.result)
        return command

    def host(self):
        return Host(self.spec, lambda: 0.)

    def test_full_readonly_source_and_only_cpu_output_command(self):
        command = self.make_query()
        self.assertNotIn('--gpus', command)
        self.assertEqual(command[command.index('--memory-swap')+1], '8g')
        self.assertEqual(command[command.index('--cpuset-cpus')+1], '26,27')
        self.assertIn('CUDA_VISIBLE_DEVICES=', command)
        self.assertIn('NVIDIA_VISIBLE_DEVICES=void', command)
        state, host = validate_container(self.container, dict(self.binding, container_id='f'*64), self.spec, self.config)
        self.assertEqual(host['NanoCpus'], 2*10**9)
        self.assertEqual(state['ExitCode'], 0)

    def test_changed_device_memory_mount_user_command_or_manifest_cannot_accept(self):
        self.make_query()
        for fault in ('GPU', 'swap', 'privileged', 'mount', 'user', 'command', 'manifest', 'image'):
            container = copy.deepcopy(self.container)
            if fault == 'GPU': container['HostConfig']['DeviceRequests'] = [{'DeviceIDs': ['GPU-UNAUTHORIZED']}]
            elif fault == 'swap': container['HostConfig']['MemorySwap'] = 16*2**30
            elif fault == 'privileged': container['HostConfig']['Privileged'] = True
            elif fault == 'mount': container['Mounts'][0]['RW'] = True
            elif fault == 'user': container['Config']['User'] = '0:0'
            elif fault == 'command': container['Config']['Cmd'][0] = '/unregistered/scorer.py'
            elif fault == 'manifest': container['Config']['Labels']['wcomr.manifest'] = '0'*64
            elif fault == 'image': container['Image'] = 'sha256:'+'0'*64
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                validate_container(container, dict(self.binding, container_id='f'*64), self.spec, self.config)

    def test_full_original_terminal_recovery_seals_once_without_new_cpu(self):
        self.make_query()
        with patch('wcomr.cara_source_lifecycle_fit_broker_r1.inspect_original',
                   return_value=dict(status='OBSERVED', container=self.container)), \
                patch('wcomr.cara_source_lifecycle_fit_broker_r1.observe_original_process',
                      side_effect=lambda handle: dict(original_live=False, observed_unix=time.time())), \
                patch('wcomr.cara_source_lifecycle_fit_broker_r1.subprocess.Popen') as spawn:
            host = self.host()
            result = host.dispatch_query(self.candidate)
            self.assertEqual(result['status'], 'ORIGINAL_COMPLETE_FIT_ACCEPTED')
            original = (self.query/'response.json').read_bytes()
            self.assertEqual(Host.reader(self.spec).dispatch_query(self.candidate)['status'], result['status'])
            self.assertEqual((self.query/'response.json').read_bytes(), original)
            spawn.assert_not_called()
        accepted = Client(self.spec)(self.packet, None)
        self.assertEqual(accepted['status'], 'ACCEPTED_INTERNAL_CALIBRATION_ONLY')
        self.assertEqual(len(accepted['rows']), 2)
        self.assertFalse(accepted['whole_card_scientific_accepted'])

    def test_missing_cid_unknown_or_live_cli_never_dispatches_or_reads_scores(self):
        self.make_query()
        for state in ('missing', 'unknown', 'live'):
            cid = self.output/'container.cid'
            if state == 'missing': cid.unlink()
            elif not cid.exists(): cid.write_text('f'*64)
            with self.subTest(state=state), \
                    patch('wcomr.cara_source_lifecycle_fit_broker_r1.inspect_original',
                          return_value=dict(status='UNKNOWN') if state == 'unknown' else dict(status='OBSERVED', container=self.container)), \
                    patch('wcomr.cara_source_lifecycle_fit_broker_r1.observe_original_process',
                          return_value=dict(original_live=state == 'live')), \
                    patch('wcomr.cara_source_lifecycle_fit_broker_r1.subprocess.Popen') as spawn:
                result = self.host().dispatch_query(self.candidate)
                self.assertEqual(result['status'], 'ORIGINAL_FIT_ACTIVE' if state == 'live' else 'ORIGINAL_FIT_UNKNOWN')
                self.assertFalse((self.query/'response.json').exists())
                spawn.assert_not_called()

    def test_original_worker_failure_does_not_accept_partial_fidelity(self):
        self.make_query()
        self.container['State']['ExitCode'] = 1
        (self.output/'scores.json').unlink()
        with patch('wcomr.cara_source_lifecycle_fit_broker_r1.inspect_original',
                   return_value=dict(status='OBSERVED', container=self.container)), \
                patch('wcomr.cara_source_lifecycle_fit_broker_r1.observe_original_process', return_value=dict(original_live=False)):
            result = self.host().recover_query(self.candidate)
        self.assertEqual(result['status'], 'ORIGINAL_FIT_FAILED')
        self.assertEqual(result['complete_FIT_denominator'], 2)
        self.assertFalse((self.query/'response.json').exists())

    def test_wrong_card_artifact_or_outside_dp_policy_is_refused(self):
        config = copy.deepcopy(self.config)
        config['packet']['pairs'][0]['candidate']['proof_path'] = str(Path(self.temp.name)/'outside.json')
        # A changed manifest is refused even before an external artifact is opened.
        with self.assertRaises((ValueError, FileNotFoundError)):
            validate_query(self.spec, config)
        proof = Path(self.packet['pairs'][0]['candidate']['proof_path'])
        value = read_record(proof)
        value['semantic_history'][23]['actual'] = 'A'
        proof.write_text(json.dumps(value))
        packet = copy.deepcopy(self.packet)
        packet['pairs'][0]['candidate']['proof_sha256'] = file_sha(proof)
        config = bind_scorer(packet, self.environment, cpu_validation=True)
        with self.assertRaises(ValueError):
            validate_query(self.spec, config)

    def test_deadline_refusal_precedes_a_new_cpu_intent_or_dispatch(self):
        self.query.mkdir()
        create_record(self.query/'request.json', self.config)
        with patch('wcomr.cara_source_lifecycle_fit_broker_r1.time.monotonic',
                   return_value=self.spec['work_stop_monotonic']-100), \
                patch('wcomr.cara_source_lifecycle_fit_broker_r1.subprocess.Popen') as spawn:
            with self.assertRaisesRegex(ValueError, 'exit reserve'):
                self.host().dispatch_query(self.candidate)
            spawn.assert_not_called()
        self.assertFalse((self.query/'launch-intent.json').exists())

    def test_client_unknown_retains_one_original_intent_and_status_has_no_scores(self):
        client = Client(self.spec)
        with patch('wcomr.cara_source_lifecycle_fit_broker_r1.time.monotonic',
                   return_value=self.spec['work_stop_monotonic']+1):
            for _ in range(2):
                with self.assertRaises(OriginalQueryUnknown):
                    client(self.packet, None)
        self.assertEqual(len(list(Path(self.spec['queue']).glob('score-*'))), 1)
        status_file(self.spec, self.candidate, 'ORIGINAL_FIT_UNKNOWN')
        reader = read_record
        def no_science(path):
            self.assertEqual(Path(path).name, 'status.json')
            return reader(path)
        with patch('wcomr.cara_source_lifecycle_fit_broker_r1.read_record', side_effect=no_science):
            result = operational_status(self.spec)
        self.assertEqual(result['statuses'], {'ORIGINAL_FIT_UNKNOWN': 1})
        self.assertFalse(result['scientific_scores_exposed'])

    def test_terminal_reader_cannot_start_a_service_or_a_new_query(self):
        self.query.mkdir()
        create_record(self.query/'request.json', self.config)
        reader = Host.reader(self.spec)
        with self.assertRaises(OriginalQueryUnknown):
            reader.dispatch_query(self.candidate)
        with self.assertRaises(OriginalQueryUnknown):
            reader.serve()
        self.assertFalse((self.query/'launch-intent.json').exists())

    def test_terminal_response_published_during_liveness_read_is_consumed_once(self):
        create_record(Path(self.spec['queue'])/'service-start.json', dict(
            identity=dict(unit_role='service'), binding_sha256=digest(self.spec)))
        def ended(handle):
            payload = dict(reason='ORIGINAL_FIT_FAILED', complete_FIT_denominator=2)
            create_record(self.query/'response.json', dict(status='FAILED_ORIGINAL',
                config_sha256=digest(self.config), payload=payload, payload_sha256=digest(payload)))
            return dict(original_live=False)
        with patch('wcomr.cara_source_lifecycle_fit_broker_r1.observe_original_process', side_effect=ended):
            with self.assertRaisesRegex(RuntimeError, 'Original full FIT query failed'):
                Client(self.spec)(self.packet, None)
        self.assertEqual(read_record(self.query/'response.json')['payload']['complete_FIT_denominator'], 2)
        self.assertFalse((self.query/'launch-intent.json').exists())


if __name__ == '__main__':
    unittest.main()
