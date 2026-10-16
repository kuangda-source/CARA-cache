"""Real isolated current-source packets and temporary Git installation; no SSH/GPU."""
from contextlib import redirect_stdout
import gzip
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wcomr.immutable_stage_payload_r1 import local_python_closure
from wcomr.frozen_shared_production_r1 import sha, write

ROOT = Path(__file__).resolve().parents[1]


def script(name):
    spec = importlib.util.spec_from_file_location('synthetic_N09_' + name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class RuntimeProfile40PackagingControls(unittest.TestCase):
    def test_reference_only_gate_reuses_same_contract_without_physical_loader(self):
        from test_runtime_profile40_production_r1 import stage_fixture, accepted_doubles
        from wcomr import runtime_profile40_production_r1 as production
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder); config, bound, _ = stage_fixture(stage)
            with accepted_doubles(stage),patch('wcomr.frozen_shared_production_r1.validate') as physical:
                observed, data, actual, reused = production.referenced_contract(stage)
            physical.assert_not_called(); self.assertEqual(observed, config); self.assertEqual(actual, bound)
            self.assertEqual(reused['original_full102_CPU_paths'], 102)
            self.assertEqual(len(reused['source_sha256']), 4); self.assertNotIn('shared_numeric_reuse', reused)

    def test_missing_real_config_refuses_before_network_and_base_must_match_original_N08(self):
        module = script('deploy_wc_paper_N09_production_cpu_r1')
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); args = ['SYNTHETIC','--base-CPU-capture',str(root / 'missing.gz'),
                '--stage','.sync/wc-paper-n09-SYNTHETIC','--output',str(root / 'launch.json')]
            with patch.object(sys,'argv',args),patch.object(module,'ROOT',root), \
                    patch.object(sys,'path',list(sys.path)),patch.object(module.subprocess,'run') as network:
                with self.assertRaises(FileNotFoundError):module.main()
                network.assert_not_called()
        from test_balanced_repeat_cpu_acceptance_r1 import fixture
        base = fixture()
        data = dict(N08_capture=dict(config_sha256=base['files']['config']['sha256'],
                                   production_CPU_sha256=base['files']['proof']['sha256']))
        self.assertTrue(module.accepted_base_identity(base, data)['CPU_accepted'])
        data['N08_capture']['production_CPU_sha256'] = '0' * 64
        with self.assertRaises(ValueError):module.accepted_base_identity(base, data)

    def test_actual_readonly_capture_body_runs_stdlib_only_on_original_files(self):
        module = script('capture_wc_paper_N09_production_cpu_r1')
        from wcomr.runtime_profile40_production_r1 import CONFIG
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); stage = root / '.sync/SYNTHETIC_N09'; stage.mkdir(parents=True)
            for name in ('src/wcomr/__init__.py','src/wcomr/gpu_budget_pool_v2.py'):
                target = stage / name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT / name,target)
            write(stage / 'control.json',{'SYNTHETIC_ONLY':True})
            write(stage / CONFIG,{'references':{'control':{'ref':'control.json','sha256':sha(stage / 'control.json')}}})
            files = [str(p.relative_to(stage)) for p in stage.rglob('*') if p.is_file()]
            write(stage / 'registration.json',dict(source_revision='1' * 40,payload_sha256={n:sha(stage / n) for n in files}))
            launch = dict(project=str(root),stage=str(stage),source_revision='1' * 40,
                registration_sha256=sha(stage / 'registration.json'),identity=dict(pid=99999999,start_ticks=123))
            original = {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
            env = {k:v for k,v in os.environ.items() if k != 'PYTHONPATH'}
            child = subprocess.run([sys.executable,'-S','-c',module.remote_code(launch)],cwd=root,
                env=dict(env,PYTHONDONTWRITEBYTECODE='1'),capture_output=True,timeout=10)
            self.assertEqual(child.returncode,0,child.stderr.decode())
            observed = json.loads(gzip.decompress(child.stdout))
            self.assertTrue(all(observed['payload_verified'].values()))
            self.assertEqual(observed['files']['control']['data'],{'SYNTHETIC_ONLY':True})
            self.assertFalse(observed['files']['bundle']['exists']); self.assertEqual(observed['GPU_submissions'],0)
            self.assertEqual({str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()},original)

    def test_actual_Git_installer_dispatches_one_CPU_child_and_preserves_original_base(self):
        module = script('deploy_wc_paper_N09_production_cpu_r1')
        spec = importlib.util.spec_from_file_location('synthetic_N09_archive_fixture',ROOT / 'tests/test_immutable_stage_payload_r1.py')
        helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
        from wcomr.immutable_stage_payload_r1 import plan,git_archive
        with tempfile.TemporaryDirectory() as folder:
            root,base,old,_ = helper.fixture(Path(folder))
            target = root / '.sync/base'; target.parent.mkdir(); shutil.move(str(base),target); base = target
            names = ['src/wcomr/immutable_stage_payload_r1.py','src/wcomr/gpu_budget_pool_v2.py']
            for name in names:
                path = root / name; path.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT / name,path)
            worker = 'scripts/run_wc_paper_N09_production_cpu_bundle_r1.py'
            helper.write(root,worker,b'# SYNTHETIC CHILD NEVER EXECUTED\n')
            subprocess.run(['git','add','.'],cwd=root,check=True,capture_output=True)
            subprocess.run(['git','-c','user.name=Synthetic CPU Control','-c','user.email=synthetic@invalid',
                'commit','-qm','Synthetic isolated N09 CPU source'],cwd=root,check=True,capture_output=True)
            revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
            value = plan(root,config_roots=['configs/final.json'],python_entrypoints=['scripts/entry.py'],
                extra_files=names + [worker],base_registration_sha256=old['base_registration_sha256'],
                base_source_revision=old['base_source_revision'],numeric_sources={})
            archive = git_archive(root,value,revision)
            metadata = dict(base='.sync/base',base_original_absolute=str(base),stage='.sync/wc-paper-n09-SYNTHETIC',
                source_revision=revision,plan=value,expected_CPU_commands=8)
            envelope = json.dumps(metadata).encode() + b'\n' + archive
            before = {str(p.relative_to(base)):p.read_bytes() for p in base.rglob('*') if p.is_file()}
            code = module.BOOTSTRAP.replace("'/home/gaokuangda/data/gkd/worldcache_omr'",repr(str(root)))
            identity = dict(pid=12345,start_ticks=123450,state='R',command='SYNTHETIC run_wc_paper_N09_production_cpu_bundle_r1.py')
            with patch.object(sys,'stdin',SimpleNamespace(buffer=io.BytesIO(envelope))),patch.object(sys,'path',list(sys.path)), \
                    patch.object(subprocess,'Popen',return_value=SimpleNamespace(pid=12345)) as spawned, \
                    patch('wcomr.gpu_budget_pool_v2.process_identity',return_value=identity),redirect_stdout(io.StringIO()):
                exec(compile(code,'SYNTHETIC_N09_CPU_INSTALLER_NO_SSH','exec'),{})
                self.assertEqual(spawned.call_count,1)
                with patch.object(sys,'stdin',SimpleNamespace(buffer=io.BytesIO(envelope))),self.assertRaises(ValueError):
                    exec(compile(code,'SYNTHETIC_N09_DUPLICATE_REFUSED','exec'),{})
                self.assertEqual(spawned.call_count,1)
            stage = root / '.sync/wc-paper-n09-SYNTHETIC'
            registration = json.loads((stage / 'registration.json').read_text())
            launch = json.loads((stage / 'N09-production-CPU-launch.json').read_text())
            self.assertEqual(registration['CPU_scope'],'FROZEN_N09_PRODUCTION_CPU_PREPARATION_NO_GPU')
            self.assertEqual(Path(launch['project']).resolve(),root.resolve()); self.assertEqual(launch['expected_CPU_commands'],8)
            self.assertEqual(launch['first_collection_not_before_unix'] - launch['launched_unix'],300.)
            self.assertEqual(spawned.call_args.kwargs['env']['CUDA_VISIBLE_DEVICES'],'')
            self.assertFalse((root / 'reports/gpu-budget-v2.json').exists())
            self.assertEqual({str(p.relative_to(base)):p.read_bytes() for p in base.rglob('*') if p.is_file()},before)

    def test_complete_current_source_packet_runs_all_seven_groups_without_workspace_imports(self):
        module = script('deploy_wc_paper_N09_production_cpu_r1')
        from wcomr.runtime_profile40_cpu_acceptance_r1 import PATTERNS
        files = local_python_closure(ROOT,module.ENTRIES + module.TESTS)
        files.update({n:sha(ROOT / n) for n in module.TEST_DATA})
        for name in module.TESTS:self.assertIn(name,files)
        for name in module.ENTRIES:self.assertIn(name,files)
        with tempfile.TemporaryDirectory() as folder:
            stage = Path(folder)
            for name in files:
                path = stage / name; path.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT / name,path)
            env = dict(os.environ,PYTHONPATH=str(stage / 'src') + os.pathsep + str(stage / 'tests'),
                PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',
                OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
            total = 0
            for pattern in PATTERNS:
                child = subprocess.run([sys.executable,'-m','unittest','discover','-s',str(stage / 'tests'),
                    '-p',pattern,'-v'],cwd=stage,env=env,capture_output=True,timeout=45,text=True)
                self.assertEqual(child.returncode,0,pattern + '\n' + child.stdout + child.stderr)
                match = re.search(r'Ran (\d+) tests?',child.stderr); self.assertIsNotNone(match)
                total += int(match.group(1))
            print('ISOLATED_N09_CURRENT_PACKET files=' + str(len(files)) + ' groups=7 tests=' + str(total) + ' actual_Cosmos_entry=0')


if __name__ == '__main__':unittest.main()
