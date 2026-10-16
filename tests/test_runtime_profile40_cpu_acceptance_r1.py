"""Synthetic original CPU receipts and mocked bundle children, never real admission."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_runtime_profile40_production_r1 import fixture as contract_fixture
from wcomr import runtime_profile40_cpu_acceptance_r1 as cpu
from wcomr.runtime_profile40_production_r1 import CPU_STATUS, COUNTS, PROFILE_SOURCES, CONFIG, CPU_RESULT
from wcomr.frozen_shared_production_r1 import fingerprint, sha, write

ROOT = Path(__file__).resolve().parents[1]


def bundle(revision, stage, project, registration_sha256, config_sha256, proof_sha256, payload, python='SYNTHETIC_PYTHON'):
    commands = [[python, '-m', 'unittest', 'discover', '-s', stage + '/tests', '-p', pattern, '-v']
                for pattern in cpu.PATTERNS]
    commands.append([python, stage + '/' + cpu.WORKER, '--project', project, '--stage', stage, '--cpu-check'])
    return dict(status=cpu.BUNDLE_STATUS, exit_code=0, source_revision=revision, stage=stage, project=project,
        python_executable=python, registration_sha256=registration_sha256, config_sha256=config_sha256,
        production_CPU_sha256=proof_sha256, commands=[dict(command=c, exit_code=0) for c in commands],
        control_source_sha256={'tests/' + n: payload['tests/' + n] for n in cpu.PATTERNS},
        bundle_source_sha256=payload[cpu.BUNDLE_WORKER], wall_seconds=1., GPU_submissions=0,
        model_weights_loaded=0, ledger_written=False, shared_runtime_written=False, original_base_stage_written=False)


def fixture():
    config, scope, protocol, freeze, shared, bound = contract_fixture()
    refs = {name:dict(ref='SYNTHETIC/' + name + '.json', sha256=fingerprint(v)) for name, v in (
        ('runtime_scope', scope), ('timing_protocol', protocol), ('method_freeze', freeze))}
    shared['references']['method_freeze'] = refs['method_freeze']
    refs['shared_config'] = dict(ref='SYNTHETIC/shared.json', sha256=fingerprint(shared)); config['references'] = refs
    numeric = {'src/SYNTHETIC_NUMERIC_' + str(i) + '.py':hashlib.sha256(str(i).encode()).hexdigest() for i in range(99)}
    observer = {n:scope['source_bindings'][n]['sha256'] for n in PROFILE_SOURCES}
    payload = {**numeric, **observer, cpu.WORKER:'a' * 64, cpu.BUNDLE_WORKER:'d' * 64,
               **{'tests/' + n:hashlib.sha256(n.encode()).hexdigest() for n in cpu.PATTERNS}}
    registration = dict(source_revision='1' * 40, payload_sha256=payload)
    proof = dict(status=CPU_STATUS, exit_code=0, source_revision=registration['source_revision'],
        registration_sha256=fingerprint(registration), config_sha256=fingerprint(config),
        runner_source_sha256='a' * 64, bound_profile_fingerprint=fingerprint(bound),
        scope_counts=copy.deepcopy(COUNTS), matrix=copy.deepcopy(bound['execution_plan']),
        actual_sample_argument_variants=10, CUDA_initialized=False, GPU_submissions=0,
        model_weights_loaded=0, ledger_written=False,
        native_forward_identity=dict(qualified_name='cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward', sha256='b' * 64),
        guardrail_checks=[dict(scene=r['name'], unguarded_execution_refused=True) for r in bound['requests']],
        unchanged_profile_and_numeric_CPU_reuse=dict(original_full102_CPU_paths=102, new_full102_paths_run=0,
            source_sha256=observer, shared_numeric_reuse=dict(status='ACCEPTED_FULL952_NUMERICAL_DEPENDENCIES_REUSED',
                checked_source_files=99, source_sha256=numeric)))
    project = '/SYNTHETIC_PROJECT'; stage = project + '/.sync/N09_SYNTHETIC'
    b = bundle(registration['source_revision'], stage, project, fingerprint(registration), fingerprint(config), fingerprint(proof), payload)
    identity = dict(pid=9001, start_ticks=90010)
    exit = dict(exit_code=0, source_revision=registration['source_revision'], registration_sha256=fingerprint(registration),
        original_CPU_identity=identity, production_CPU_sha256=fingerprint(proof), bundle_result_sha256=fingerprint(b))
    values = [('config', config), ('runtime_scope', scope), ('timing_protocol', protocol), ('method_freeze', freeze),
              ('shared_config', shared), ('bundle', b), ('proof', proof), ('CPU_exit', exit)]
    return dict(status='N09_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE', registration=registration,
        registration_sha256=fingerprint(registration), launch=dict(source_revision=registration['source_revision'],
            registration_sha256=fingerprint(registration), identity=identity, first_collection_not_before_unix=10.,
            stage=stage, project=project), observed_unix=20., process=dict(pid=9001, state=None, start_ticks=None),
        files={n:dict(exists=True, sha256=fingerprint(v), data=v) for n, v in values},
        payload_verified={n:True for n in payload}, payload_actual_sha256=copy.deepcopy(payload),
        GPU_submissions=0, ledger_written=False)


class RuntimeProfile40CPUAcceptanceControls(unittest.TestCase):
    def test_complete_same_source_eight_commands_accept_only_CPU_not_GPU(self):
        value = fixture(); original = copy.deepcopy(value); accepted = cpu.accept(value)
        self.assertTrue(accepted['CPU_accepted']); self.assertEqual(accepted['CPU_commands'], 8)
        self.assertEqual(accepted['scope_counts']['total_paths'], 40)
        self.assertFalse(accepted['whole_GPU_card_selected']); self.assertFalse(accepted['real_video_or_speed_result'])
        self.assertEqual(value, original)

    def test_original_live_process_waits_and_reused_PID_does_not_get_restarted(self):
        value = fixture(); value['process'].update(state='R', start_ticks=90010)
        self.assertFalse(cpu.accept(value)['CPU_accepted'])
        value['process']['start_ticks'] += 1
        self.assertTrue(cpu.accept(value)['CPU_accepted'])

    def test_CPU_transient_state_change_keeps_same_PID_start_identity(self):
        value = fixture()
        value['launch']['identity'] = dict(value['launch']['identity'], state='S', command='SYNTHETIC_ORIGINAL_COMMAND')
        value['files']['CPU_exit']['data']['original_CPU_identity'] = dict(
            value['files']['CPU_exit']['data']['original_CPU_identity'], state='R', command='SYNTHETIC_SAME_ORIGINAL_COMMAND')
        self.assertTrue(cpu.accept(value)['CPU_accepted'])

    def test_failed_missing_or_wrong_original_CPU_exit_never_accepts(self):
        value = fixture(); value['files']['bundle']['data']['exit_code'] = 1
        self.assertIn('FAILED_RESULT', cpu.accept(value)['status'])
        value = fixture(); value['files']['CPU_exit']['exists'] = False
        self.assertIn('MISSING_RESULTS', cpu.accept(value)['status'])
        for key, changed in [('exit_code', 1), ('source_revision', '2' * 40),
                ('bundle_result_sha256', '0' * 64), ('original_CPU_identity', dict(pid=9002, start_ticks=90020))]:
            value = fixture(); value['files']['CPU_exit']['data'][key] = changed
            with self.subTest(key=key),self.assertRaises(ValueError):cpu.accept(value)

    def test_early_partial_payload_and_changed_reference_are_rejected(self):
        for mode in ('early', 'payload_count', 'payload_SHA', 'reference'):
            value = fixture()
            if mode == 'early':value['observed_unix'] = 9.
            elif mode == 'payload_count':value['payload_verified'].pop(next(iter(value['payload_verified'])))
            elif mode == 'payload_SHA':value['payload_actual_sha256'][cpu.WORKER] = '0' * 64
            else:value['files']['runtime_scope']['sha256'] = '0' * 64
            with self.subTest(mode=mode),self.assertRaises(ValueError):cpu.accept(value)

    def test_scope_guard_native_GPU_and_reused102_99_source_controls(self):
        for mode in ('typed', 'scope', 'guard', 'native', 'GPU', 'observer', 'numeric'):
            value = fixture(); proof = value['files']['proof']['data']
            if mode == 'typed':proof['actual_sample_argument_variants'] = 9
            elif mode == 'scope':proof['matrix'].pop()
            elif mode == 'guard':proof['guardrail_checks'].pop()
            elif mode == 'native':proof['native_forward_identity']['qualified_name'] = 'SYNTHETIC_OTHER_CLASS'
            elif mode == 'GPU':proof['CUDA_initialized'] = True
            elif mode == 'observer':proof['unchanged_profile_and_numeric_CPU_reuse']['source_sha256'].pop(PROFILE_SOURCES[0])
            else:proof['unchanged_profile_and_numeric_CPU_reuse']['shared_numeric_reuse']['source_sha256']['src/EXTRA.py'] = '0' * 64
            with self.subTest(mode=mode),self.assertRaises(ValueError):cpu.accept(value)

    def test_no_skipped_entry_changed_command_source_or_stage_can_pass_bundle(self):
        for mode in ('short', 'wrong_entry', 'source', 'stage', 'failed', 'weights'):
            value = fixture(); b = value['files']['bundle']['data']
            if mode == 'short':b['commands'].pop()
            elif mode == 'wrong_entry':b['commands'][-1]['command'][-1] = '--help'
            elif mode == 'source':b['control_source_sha256'].pop('tests/' + cpu.PATTERNS[0])
            elif mode == 'stage':b['stage'] = '/FOREIGN_STAGE'
            elif mode == 'failed':b['commands'][0]['exit_code'] = 1
            else:b['model_weights_loaded'] = 1
            with self.subTest(mode=mode),self.assertRaises(ValueError):cpu.accept(value)

    def test_actual_bundle_driver_runs_all_eight_declared_mocked_children_and_preserves_once(self):
        from test_runtime_profile40_supervision_r1 import fixture as supervision_fixture, load_script, process
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = supervision_fixture(root); stage = values[2]
            proof = (stage / CPU_RESULT).read_bytes()
            for n in (CPU_RESULT, 'N09-production-CPU-exit.json', 'N09-CPU-bundle-result.json'):(stage / n).unlink()
            driver = load_script('run_wc_paper_N09_production_cpu_bundle_r1')
            def call(command, **kwargs):
                self.assertEqual(kwargs['env']['CUDA_VISIBLE_DEVICES'], '')
                self.assertEqual(kwargs['cwd'], root / 'runtime')
                if command[-1] == '--cpu-check':(stage / CPU_RESULT).write_bytes(proof)
                return 0
            with patch.object(driver.subprocess, 'call', side_effect=call) as invoked, \
                    patch('wcomr.gpu_budget_pool_v2.process_identity', side_effect=process):
                result = driver.run(root, stage)
            self.assertEqual(invoked.call_count, 8); self.assertEqual(result['status'], cpu.BUNDLE_STATUS)
            cpu.validate_bundle(result, values[3]['source_revision'], registration_sha256=sha(stage / 'registration.json'),
                config_sha256=sha(stage / CONFIG), proof_sha256=sha(stage / CPU_RESULT), payload_sha256=values[3]['payload_sha256'])
            old = (stage / 'N09-CPU-bundle-result.json').read_bytes()
            with self.assertRaises(FileExistsError):driver.run(root, stage)
            self.assertEqual((stage / 'N09-CPU-bundle-result.json').read_bytes(), old)

    def test_bundle_failure_keeps_original_commands_and_does_not_start_actual_entry(self):
        from test_runtime_profile40_supervision_r1 import fixture as supervision_fixture, load_script, process
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); values = supervision_fixture(root); stage = values[2]
            for n in (CPU_RESULT, 'N09-production-CPU-exit.json', 'N09-CPU-bundle-result.json'):(stage / n).unlink()
            driver = load_script('run_wc_paper_N09_production_cpu_bundle_r1')
            with patch.object(driver.subprocess, 'call', side_effect=[0, 0, 3]) as invoked, \
                    patch('wcomr.gpu_budget_pool_v2.process_identity', side_effect=process):
                with self.assertRaises(RuntimeError):driver.run(root, stage)
            import json
            result = json.loads((stage / 'N09-CPU-bundle-result.json').read_text())
            self.assertEqual(result['exit_code'], 1); self.assertEqual(len(result['commands']), 3)
            self.assertEqual(invoked.call_count, 3); self.assertFalse((stage / CPU_RESULT).exists())
            self.assertEqual(json.loads((stage / 'N09-production-CPU-exit.json').read_text())['exit_code'], 1)

    def test_once_capture_saves_original_compressed_bytes_and_offline_CLI_accepts_without_SSH(self):
        from test_runtime_profile40_supervision_r1 import load_script
        import contextlib,gzip,io,json,os,subprocess,sys
        from types import SimpleNamespace
        value = fixture(); raw = gzip.compress(json.dumps(value).encode())
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); launch = root / 'launch.json'; write(launch, {'launch':value['launch']})
            output = root / 'original.json.gz'; module = load_script('capture_wc_paper_N09_production_cpu_r1')
            args = ['SYNTHETIC', '--launch-ref', str(launch), '--output', str(output)]
            with patch.object(sys, 'argv', args),patch.object(module.time, 'time', return_value=20.), \
                    patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0,stdout=raw,stderr=b'')) as ssh, \
                    contextlib.redirect_stdout(io.StringIO()):
                module.main()
                self.assertEqual(ssh.call_count, 1)
                with self.assertRaises(FileExistsError):module.main()
                self.assertEqual(ssh.call_count, 1)
            self.assertEqual(output.read_bytes(), raw)
            accepted = root / 'SYNTHETIC_CPU_ACCEPTANCE_NOT_REAL.json'
            call = subprocess.run([sys.executable, str(ROOT / 'scripts/accept_wc_paper_N09_production_cpu_r1.py'),
                '--capture', str(output), '--output', str(accepted)],text=True,capture_output=True,
                env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'))
            self.assertEqual(call.returncode, 0, call.stderr)
            result = json.loads(accepted.read_text()); self.assertTrue(result['CPU_accepted'])
            self.assertEqual(result['capture_sha256'], sha(output))

    def test_before_ETA_does_not_query_and_transport_timeout_is_not_terminal(self):
        from test_runtime_profile40_supervision_r1 import load_script
        import gzip,json,subprocess,sys
        value = fixture()
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); launch = root / 'launch.json'; write(launch, {'launch':value['launch']})
            output = root / 'original.json.gz'; module = load_script('capture_wc_paper_N09_production_cpu_r1')
            args = ['SYNTHETIC', '--launch-ref', str(launch), '--output', str(output)]
            with patch.object(sys, 'argv', args),patch.object(module.time, 'time', return_value=9.), \
                    patch.object(module.subprocess, 'run') as ssh:
                with self.assertRaises(SystemExit):module.main()
                ssh.assert_not_called(); self.assertFalse(output.exists())
            with patch.object(sys, 'argv', args),patch.object(module.time, 'time', return_value=20.), \
                    patch.object(module.subprocess, 'run', side_effect=subprocess.TimeoutExpired('SYNTHETIC_SSH',1)) as ssh:
                with self.assertRaises(subprocess.TimeoutExpired):module.main()
                self.assertEqual(ssh.call_count, 1)
            result = json.loads(gzip.decompress(output.read_bytes()))
            self.assertFalse(result['original_task_terminal']); self.assertTrue(result['no_CPU_or_GPU_relaunch_authority'])
            with self.assertRaises(ValueError):cpu.accept(result)

    def test_malformed_return_is_retained_before_parse_error_and_remote_code_is_stdlib_syntax(self):
        from test_runtime_profile40_supervision_r1 import load_script
        import ast,subprocess,sys
        from types import SimpleNamespace
        value = fixture(); module = load_script('capture_wc_paper_N09_production_cpu_r1')
        ast.parse(module.remote_code(value['launch']))
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); launch = root / 'launch.json'; write(launch, {'launch':value['launch']})
            output = root / 'raw.json.gz'; args = ['SYNTHETIC','--launch-ref',str(launch),'--output',str(output)]
            with patch.object(sys,'argv',args),patch.object(module.time,'time',return_value=20.), \
                    patch.object(module.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=b'SYNTHETIC_INVALID_GZIP',stderr=b'')) as ssh:
                with self.assertRaises(OSError):module.main()
                self.assertEqual(ssh.call_count,1)
            self.assertEqual(output.read_bytes(),b'SYNTHETIC_INVALID_GZIP')


if __name__ == '__main__':unittest.main()
