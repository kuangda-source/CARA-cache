"""Actual loader logic and failed-parent reuse guards, CPU-only local fixtures."""
import ast
import glob
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('r42worker',ROOT/'scripts/finish_wc_four_card_resources_cpu_r4.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)
DIAG=json.loads((ROOT/'reports/wc_four_card_R4_1_NVRTC_loader_readonly_diagnosis_20261022.json').read_text())


def installed_loader(cdll,check_output):
    tree=ast.parse(DIAG['loader_source'])
    body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['_get_sys_extension','_load_nvrtc']]
    assert len(body)==2
    scope=dict(os=os,glob=glob,platform=types.SimpleNamespace(system=lambda:'Linux'),ctypes=types.SimpleNamespace(CDLL=cdll,RTLD_GLOBAL=256),subprocess=types.SimpleNamespace(check_output=check_output))
    exec(compile(ast.Module(body=body,type_ignores=[]),'<actual-installed-NVRTC-loader>','exec'),scope)
    return scope['_load_nvrtc']


class NativeLoaderAndReuseControls(unittest.TestCase):
    def test_actual_loader_uses_existing_package_home_without_ldconfig(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'lib').mkdir()
            for name in ['libnvrtc.so.12','libnvrtc.alt.so.12','libnvrtc-builtins.so.12.8']:(root/'lib'/name).touch()
            loader=installed_loader(lambda p,mode:p,lambda *a,**k:self.fail('ldconfig must not be used for the configured package'))
            with patch.dict(os.environ,{'CUDA_HOME':str(root),'CUDA_PATH':str(root)},clear=True):
                self.assertEqual(loader(),str(root/'lib/libnvrtc.so.12'))

    def test_actual_loader_missing_package_reproduces_ldconfig_fallback(self):
        def missing(*a,**k):raise FileNotFoundError('ldconfig unavailable in the resource container')
        loader=installed_loader(lambda *a,**k:self.fail('No known CUDA_HOME file'),missing)
        with patch.dict(os.environ,{'CUDA_HOME':'/registered-nonexistent-path'},clear=True),patch.object(glob,'glob',return_value=[]):
            with self.assertRaisesRegex(FileNotFoundError,'ldconfig'):loader()

    def test_native_resource_requires_matching_installed_loader_and_process_home(self):
        with tempfile.TemporaryDirectory() as d:
            env=Path(d);site=env/'lib/python3.10/site-packages';home=site/'nvidia/cuda_nvrtc'
            (home/'lib').mkdir(parents=True);(home/'lib/libnvrtc.so.12').write_bytes(b'fixture')
            loader=site/'transformer_engine/common/__init__.py';loader.parent.mkdir(parents=True);loader.write_text('unchanged installed loader\n')
            with patch.dict(os.environ,{'CUDA_HOME':str(home),'CUDA_PATH':str(home)}):
                value=w.existing_nvrtc_resource(env,w.sha(loader));self.assertEqual(value['library_bytes'],7)
                with self.assertRaises(AssertionError):w.existing_nvrtc_resource(env,'0'*64)

    def parent(self,root):
        root=Path(root)
        values={'manifest.json':dict(availability_assets=[dict(path='registered-fixture')]),
            'result.json':dict(status='R4_CPU_RESOURCE_FAILURE_RETAINED',environment_metadata_unchanged=True,environment_metadata_after='metadata',runtime_critical_sources_unchanged=True,commands=[dict(phase='frozen110-offline-paths-tokenizer',exit_code=0,exact_marker=True),dict(phase='unchanged-guarded-inference-import',exit_code=1)])}
        for name,value in values.items():(root/name).write_text(json.dumps(value))
        (root/'worker.py').write_text('original worker')
        (root/'frozen110-offline-paths-tokenizer.py').write_text('original successful resolver')
        (root/'frozen110-offline-paths-tokenizer.log').write_text('FROZEN110_OFFLINE_HF_PATHS_AND_REASON_TOKENIZER_CPU_OK\n')
        return dict(prior_failed_cpu_job=str(root),prior_failed_cpu_manifest_sha256=w.sha(root/'manifest.json'),prior_failed_cpu_result_sha256=w.sha(root/'result.json'),prior_failed_cpu_worker_sha256=w.sha(root/'worker.py'),prior_resolver_probe_sha256=w.sha(root/'frozen110-offline-paths-tokenizer.py'),prior_resolver_log_sha256=w.sha(root/'frozen110-offline-paths-tokenizer.log'),environment_metadata_sha256='metadata',availability_assets=values['manifest.json']['availability_assets'])

    def test_successful_command_reused_without_accepting_failed_job(self):
        with tempfile.TemporaryDirectory() as d:
            m=self.parent(d);v=w.prior_resolver_proof(m)
            self.assertTrue(v['original_failed_job_not_accepted']);self.assertEqual(v['successful_command']['exit_code'],0)

    def test_nonzero_parent_command_refused_even_if_new_result_hash_is_bound(self):
        with tempfile.TemporaryDirectory() as d:
            m=self.parent(d);p=Path(d)/'result.json';v=json.loads(p.read_text());v['commands'][0]['exit_code']=1;p.write_text(json.dumps(v));m['prior_failed_cpu_result_sha256']=w.sha(p)
            with self.assertRaises(AssertionError):w.prior_resolver_proof(m)

    def test_parent_availability_scope_change_refused(self):
        with tempfile.TemporaryDirectory() as d:
            m=self.parent(d);m['availability_assets']=[dict(path='different-input')]
            with self.assertRaises(AssertionError):w.prior_resolver_proof(m)


if __name__=='__main__':unittest.main()
