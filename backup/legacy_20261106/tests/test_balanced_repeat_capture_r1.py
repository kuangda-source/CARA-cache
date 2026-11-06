"""Actual metadata body on a temp project; no SSH, tensors or model imports."""
import builtins
import gzip
import importlib.util
import io
import json
from pathlib import Path
import os
import subprocess
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch

from wcomr.frozen_shared_production_r1 import sha, write
from wcomr.gpu_budget_pool_v2 import SCHEMA, BudgetPool

ROOT = Path(__file__).resolve().parents[1]


def script():
    path = ROOT / 'scripts/capture_wc_paper_N08_balanced_full40_r1.py'
    spec = importlib.util.spec_from_file_location('synthetic_N08_capture', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module


class OnceCaptureControls(unittest.TestCase):
    def test_before_original_ETA_never_calls_SSH(self):
        module = script()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); launch = root / 'launch.json'; output = root / 'capture.gz'
            write(launch, dict(dispatch=dict(next_check_not_before_unix=1000.)))
            args = ['SYNTHETIC', '--launch-ref', str(launch), '--output', str(output)]
            with patch.object(sys, 'argv', args), patch.object(module.time, 'time', return_value=999.), \
                    patch.object(module.subprocess, 'run') as network:
                with self.assertRaisesRegex(SystemExit, 'Before original'): module.main()
            network.assert_not_called(); self.assertFalse(output.exists())

    def test_admission_aliases_original_registration_and_no_numeric_or_scientific_import(self):
        self.check_body('admission')

    def test_terminal_reads_exact_SHA_bound_references_without_numeric_import(self):
        self.check_body('terminal')

    def test_cold_interpreter_without_site_packages_reads_only_stdlib_metadata(self):
        module = script()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); stage = root / '.sync/SYNTHETIC'; package = stage / 'src/wcomr'
            package.mkdir(parents=True)
            for name in ('__init__.py', 'gpu_budget_pool_v2.py'):
                (package / name).write_bytes((ROOT / 'src/wcomr' / name).read_bytes())
            registration = dict(source_revision='SYNTHETIC_NO_GPU', payload_sha256={
                'src/wcomr/' + n: sha(package / n) for n in ('__init__.py', 'gpu_budget_pool_v2.py')})
            write(stage / 'registration.json', registration)
            pool = dict(schema=SCHEMA, cap_gpu_hours=100., origin_used_gpu_hours=0., origin_gpu_jobs_launched=0, jobs={}, events=[])
            pool.update(BudgetPool.accounting(pool)); write(root / 'reports/gpu-budget-v2.json', pool)
            original = (root / 'reports/gpu-budget-v2.json').read_bytes()
            launch = dict(project=str(root), stage=str(stage), source_revision=registration['source_revision'],
                registration_sha256=sha(stage / 'registration.json'), run_id='SYNTHETIC_RUN', gpu_uuid='GPU-SYNTHETIC')
            code = module.remote_code(launch, 'admission').replace("'/home/gaokuangda/data/gkd/worldcache_omr'", repr(str(root)))
            # The child starts without any site packages. Telemetry alone is
            # a declared stand-in; BudgetPool and both source files are real.
            prefix = "import subprocess\nsubprocess.check_output=lambda cmd,**kw: 'GPU-SYNTHETIC, NVIDIA RTX A6000, 24' if '-i' in cmd else ''\n"
            env = {k: v for k, v in os.environ.items() if k != 'PYTHONPATH'}
            child = subprocess.run([sys.executable, '-S', '-c', prefix + code],
                cwd=root, env=env, capture_output=True, timeout=10)
            self.assertEqual(child.returncode, 0, child.stderr.decode())
            captured = json.loads(gzip.decompress(child.stdout))
            self.assertEqual(captured['registration_sha256'], sha(stage / 'registration.json'))
            self.assertTrue(all(captured['payload_verified'].values()))
            self.assertEqual((root / 'reports/gpu-budget-v2.json').read_bytes(), original)

    def check_body(self, mode):
        module = script()
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory); root = parent / 'physical'; root.mkdir()
            alias = parent / 'logical'; alias.symlink_to(root, target_is_directory=True)
            storage = parent / 'storage'; storage.mkdir(); (root / 'outputs').symlink_to(storage, target_is_directory=True)
            stage = root / '.sync/SYNTHETIC'; stage.mkdir(parents=True)
            source = stage / 'src/control.py'; source.parent.mkdir(); source.write_text('# SYNTHETIC\n')
            registration = dict(source_revision='SYNTHETIC_NOT_DEPLOYED', payload_sha256={'src/control.py': sha(source)})
            write(stage / 'registration.json', registration)
            launch = dict(project=str(alias), stage=str(stage), source_revision=registration['source_revision'],
                registration_sha256=sha(stage / 'registration.json'), run_id='SYNTHETIC_RUN', gpu_uuid='GPU-SYNTHETIC')
            if mode == 'terminal':
                # Only test the actual collector's reference reading, not a valid inference config.
                from wcomr.balanced_repeat_production_r1 import CONFIG
                target = stage / 'meta/shared.json.gz'; target.parent.mkdir(); target.write_bytes(gzip.compress(b'{"synthetic":true}'))
                config = dict(references={'shared_config': dict(ref='meta/shared.json.gz', sha256=sha(target))})
                write(stage / CONFIG, config); launch['config_sha256'] = sha(stage / CONFIG)
            code = module.remote_code(launch, mode); literal = "'/home/gaokuangda/data/gkd/worldcache_omr'"
            self.assertEqual(code.count(literal), 1); code = code.replace(literal, repr(str(alias)))
            output = io.BytesIO(); original_import = builtins.__import__
            def imports(name, *args, **kwargs):
                if name in ('torch', 'wcomr.balanced_repeat_production_r1', 'wcomr.frozen_shared_production_r1'):
                    raise AssertionError('Metadata collector imported a numeric production dependency')
                return original_import(name, *args, **kwargs)
            def telemetry(command, **kwargs): return 'GPU-SYNTHETIC, NVIDIA RTX A6000, 24' if '-i' in command else ''
            with patch('wcomr.gpu_budget_pool_v2.BudgetPool.read', return_value={'synthetic': True}), \
                    patch('subprocess.check_output', side_effect=telemetry), patch.object(sys, 'path', list(sys.path)), \
                    patch.object(sys, 'stdout', SimpleNamespace(buffer=output)), patch('builtins.__import__', side_effect=imports):
                exec(compile(code, 'SYNTHETIC_METADATA_ONLY_NO_NETWORK', 'exec'), {})
            captured = json.loads(gzip.decompress(output.getvalue()))
            self.assertEqual(captured['registration_sha256'], sha(stage / 'registration.json'))
            self.assertEqual(captured['output_root'], str((storage / 'SYNTHETIC_RUN').resolve()))
            self.assertNotIn('runner', captured); self.assertNotIn('final', captured)
            if mode == 'terminal': self.assertEqual(captured['shared_config'], {'synthetic': True})


class HalfwayTechnicalControls(unittest.TestCase):
    @staticmethod
    def fixture(start=100.,end=300.):
        from wcomr.balanced_repeat_execution_r1 import COUNTS
        from wcomr.balanced_repeat_health_r1 import RUN
        own=dict(pid=99999991,start_ticks=11);child=dict(pid=99999992,start_ticks=22)
        post=dict(pid=99999993,start_ticks=33)
        launch=dict(project='/SYNTHETIC_PROJECT',stage='/SYNTHETIC_PROJECT/.sync/N08',run_id=RUN,
            source_revision='SYNTHETIC_NO_GPU',launch_id='SYNTHETIC_ONLY',gpu_uuid='GPU-SYNTHETIC',
            scope_counts=COUNTS.copy(),config_sha256='c'*64,registration_sha256='a'*64,
            supervisor_identity=own,post_watcher_identity=post,started_unix=start,
            midpoint_health_not_before_unix=(start+end)/2,next_check_not_before_unix=end)
        supervisor=dict(child_pid=child['pid'],child_identity=child,**{k:launch[k] for k in
            ('source_revision','launch_id','run_id','gpu_uuid','config_sha256','scope_counts')})
        value=dict(status='N08_FULL40_ORIGINAL_ONCE_CAPTURE',mode='admission',launch=launch,
            registration=dict(source_revision=launch['source_revision'],payload_sha256={'source.py':'b'*64}),
            registration_sha256=launch['registration_sha256'],payload_verified={'source.py':True},
            supervisor=supervisor,original_processes={k:dict(v,state='S') for k,v in
                (('supervisor_pid',own),('child_pid',child),('post_watcher_pid',post))})
        return launch,value

    def test_halfway_binds_full40_and_all_original_admitted_processes(self):
        import copy
        from wcomr import balanced_repeat_health_r1 as H
        launch,admission=self.fixture();expected=H.bind(launch,admission)
        self.assertEqual(expected['health_not_before_unix'],200.)
        self.assertEqual(expected['final_not_before_unix'],300.)
        self.assertEqual(expected['scope_counts']['total_paths'],40)
        for kind in ('source','scope','PID','halfway','payload'):
            l,a=copy.deepcopy((launch,admission))
            if kind=='source':a['registration']['source_revision']='FOREIGN'
            elif kind=='scope':l['scope_counts']['scientific_paths']=29
            elif kind=='PID':a['original_processes']['child_pid']['start_ticks']=999
            elif kind=='halfway':l['midpoint_health_not_before_unix']=199.
            else:a['payload_verified']['source.py']=False
            with self.subTest(kind=kind),self.assertRaises(ValueError):H.bind(l,a)

    def test_before_halfway_and_after_final_never_query_or_create_attempt(self):
        from wcomr import balanced_repeat_health_r1 as H
        launch,admission=self.fixture();expected=H.bind(launch,admission)
        for now in (199.,300.):
            with tempfile.TemporaryDirectory() as folder:
                output=Path(folder)/'health.json'
                def forbidden(*args,**kwargs):raise AssertionError('No premature or late SSH')
                with self.subTest(now=now),self.assertRaises(ValueError):
                    H.collect(expected,output,now=now,execute=forbidden)
                self.assertEqual(list(Path(folder).iterdir()),[])

    def test_one_halfway_observation_cache_and_attempt_fence(self):
        from wcomr import balanced_repeat_health_r1 as H
        launch,admission=self.fixture();expected=H.bind(launch,admission);calls=[]
        reply=dict(status='N08_MIDPOINT_READONLY_TECHNICAL_HEALTH',expected=expected,observed_unix=201.,
            original_processes={k:dict(v,match='ORIGINAL_PROCESS_LIVE') for k,v in expected['processes'].items()},
            final_scientific_results_read=False,no_quality_or_method_latency_readout=True)
        def execute(command,**kwargs):
            calls.append(command);return SimpleNamespace(returncode=0,stdout=json.dumps(reply).encode(),stderr=b'')
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'health.json'
            first,queried=H.collect(expected,output,now=200.,execute=execute)
            second,repeated=H.collect(expected,output,now=201.,execute=execute)
            self.assertTrue(queried);self.assertFalse(repeated);self.assertEqual(first,second);self.assertEqual(len(calls),1)
            output.unlink()
            with self.assertRaises(FileExistsError):H.collect(expected,output,now=201.,execute=execute)
            self.assertEqual(len(calls),1)

    def test_halfway_timeout_or_bad_reply_is_unknown_never_permission_to_restart(self):
        from wcomr import balanced_repeat_health_r1 as H
        launch,admission=self.fixture();expected=H.bind(launch,admission)
        for mode in ('timeout','malformed'):
            def execute(*args,**kwargs):
                if mode=='timeout':raise subprocess.TimeoutExpired('SYNTHETIC_SSH',45)
                return SimpleNamespace(returncode=0,stdout=b'NOT_JSON',stderr=b'')
            with tempfile.TemporaryDirectory() as folder:
                output=Path(folder)/'unknown.json';value,_=H.collect(expected,output,now=200.,execute=execute)
                self.assertIn('N08_MIDPOINT',value['status']);self.assertIn('UNKNOWN',value['status'])
                self.assertFalse(value['original_task_terminal']);self.assertEqual(value['GPU_submissions'],0)

    def test_full40_progress_retains_missing_running_refusal_and_excess_without_science(self):
        from wcomr import balanced_repeat_health_r1 as H
        value=H.technical_progress(dict(status='N08_FULL40_RUNNING',private='DO_NOT_LEAK',runs=[
            dict(section='WARMUP',status='COMPLETE',core_seconds=999.,LPIPS='DO_NOT_LEAK'),
            dict(section='TIMED',status='TEXT_REJECTED'),dict(section='TIMED',status='RUNNING')]))
        self.assertEqual(value['registered_total'],40);self.assertEqual(value['not_reached'],37)
        self.assertEqual(value['sections']['WARMUP']['registered'],10)
        self.assertEqual(value['sections']['TIMED']['registered'],30)
        self.assertEqual(value['sections']['TIMED']['running'],1)
        self.assertNotIn('DO_NOT_LEAK',json.dumps(value));self.assertNotIn('core_seconds',json.dumps(value))
        self.assertEqual(H.technical_progress(dict(runs=[{}]*41))['excess_positions'],1)

    def test_actual_halfway_body_cold_stdlib_never_opens_final_or_exports_quality(self):
        import time
        from wcomr import balanced_repeat_health_r1 as H
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();stage=root/'.sync/N08';stage.mkdir(parents=True)
            now=time.time();launch,admission=self.fixture(now-900,now+300)
            launch.update(project=str(root),stage=str(stage))
            write(stage/H.CONFIG,dict(run_id=H.RUN));launch['config_sha256']=sha(stage/H.CONFIG)
            write(stage/'registration.json',dict(source_revision=launch['source_revision']))
            launch['registration_sha256']=sha(stage/'registration.json')
            admission['registration_sha256']=launch['registration_sha256']
            admission['supervisor']['config_sha256']=launch['config_sha256']
            expected=H.bind(launch,admission);output=root/'outputs'/H.RUN;output.mkdir(parents=True)
            write(output/'supervisor.json',dict(admission['supervisor'],status='N08_FULL40_GPU_RUNNING',
                pid=expected['processes']['supervisor']['pid'],start_ticks=expected['processes']['supervisor']['start_ticks']))
            write(output/'runner.json',dict(status='N08_FULL40_RUNNING',source_revision=launch['source_revision'],
                config_sha256=launch['config_sha256'],scope_counts=launch['scope_counts'],runs=[
                dict(status='RUNNING',section='TIMED',LPIPS='DO_NOT_LEAK',core_seconds=99.)]))
            (stage/'N08-CPU-final-results.json').write_text('DO_NOT_LEAK_INVALID_FINAL')
            (output/'GPU.log').write_text('LPIPS DO_NOT_LEAK\nRuntimeError DO_NOT_LEAK\n')
            write(root/'reports/gpu-budget-v2.json',dict(jobs={H.RUN:dict(status='RESERVED_OR_RUNNING',
                **{k:launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256')})}))
            before={str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            prefix="import pathlib,subprocess\nold_read=pathlib.Path.read_bytes\ndef checked(p):\n if p.name=='N08-CPU-final-results.json':raise AssertionError('Final must only be statted')\n return old_read(p)\npathlib.Path.read_bytes=checked\nsubprocess.check_output=lambda cmd,**kw:'GPU-SYNTHETIC, NVIDIA RTX A6000, 0, 24, 49140' if '-i' in cmd else ''\n"
            code=H.remote_code(expected).replace("'/home/gaokuangda/data/gkd/worldcache_omr'",repr(str(root)))
            env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'}
            child=subprocess.run([sys.executable,'-S','-c',prefix+code],cwd=root,env=env,capture_output=True,timeout=10)
            self.assertEqual(child.returncode,0,child.stderr.decode());value=json.loads(child.stdout)
            self.assertEqual(value['status'],'N08_MIDPOINT_READONLY_TECHNICAL_HEALTH')
            self.assertEqual(value['technical_progress']['registered_total'],40)
            self.assertNotIn('DO_NOT_LEAK',json.dumps(value));self.assertNotIn('final',value)
            self.assertTrue(value['files']['CPU_final_metadata_only']['exists'])
            self.assertEqual(value['bounded_technical_logs']['GPU']['error_labels']['runtimeerror'],1)
            self.assertEqual({str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()},before)


if __name__ == '__main__': unittest.main()
