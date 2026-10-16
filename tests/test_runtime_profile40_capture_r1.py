"""Actual once-capture body in isolated stdlib Python, no SSH or CUDA execution."""
import gzip
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from wcomr.frozen_shared_production_r1 import sha, write
from wcomr.gpu_budget_pool_v2 import SCHEMA,BudgetPool
from wcomr.runtime_profile40_production_r1 import CONFIG,RUN

ROOT=Path(__file__).resolve().parents[1]


def script():
    spec=importlib.util.spec_from_file_location('synthetic_capture_N09',
        ROOT/'scripts/capture_wc_paper_N09_runtime_profile40_r1.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class OnceProfileCaptureControls(unittest.TestCase):
    def test_health_and_terminal_each_refuse_before_own_time_without_SSH(self):
        module=script()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);launch=root/'launch.json';output=root/'never.gz'
            write(launch,dict(dispatch=dict(midpoint_health_not_before_unix=500.,next_check_not_before_unix=1000.)))
            for mode,now in (('health',499.),('terminal',999.)):
                with patch.object(sys,'argv',['test','--launch-ref',str(launch),'--output',str(output),'--mode',mode]), \
                        patch.object(module.time,'time',return_value=now),patch.object(module.subprocess,'run') as network:
                    with self.assertRaisesRegex(SystemExit,'Before original'):module.main()
                network.assert_not_called();self.assertFalse(output.exists())

    def test_original_body_health_has_no_science_terminal_reads_scalar_bytes_no_Torch(self):
        module=script()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();stage=root/'.sync/SYNTHETIC_N09';package=stage/'src/wcomr'
            package.mkdir(parents=True)
            for name in ('__init__.py','gpu_budget_pool_v2.py'):
                (package/name).write_bytes((ROOT/'src/wcomr'/name).read_bytes())
            registration=dict(source_revision='SYNTHETIC_NO_GPU',payload_sha256={
                'src/wcomr/'+n:sha(package/n) for n in ('__init__.py','gpu_budget_pool_v2.py')})
            write(stage/'registration.json',registration)
            pool=dict(schema=SCHEMA,cap_gpu_hours=113.,origin_used_gpu_hours=0.,origin_gpu_jobs_launched=0,jobs={},events=[])
            pool.update(BudgetPool.accounting(pool));write(root/'reports/gpu-budget-v2.json',pool)
            ledger_before=(root/'reports/gpu-budget-v2.json').read_bytes()
            output=root/'outputs'/RUN;output.mkdir(parents=True)
            profile=output/'profile-scalars.json';write(profile,dict(synthetic=True,not_GPU_measurement=True))
            row=dict(status='COMPLETE',mode='PROFILE_LEAN',private_science='MUST_NOT_LEAK',
                component_profile_artifact=dict(path=str(profile),sha256=sha(profile),bytes=profile.stat().st_size))
            write(output/'runner.json',dict(runs=[row]))
            write(stage/CONFIG,dict(references={}))
            (stage/'N09-CPU-final-results.json').write_text('INVALID_DO_NOT_OPEN_DURING_HEALTH')
            launch=dict(project=str(root),stage=str(stage),run_id=RUN,source_revision=registration['source_revision'],
                registration_sha256=sha(stage/'registration.json'),config_sha256=sha(stage/CONFIG),gpu_uuid='GPU-SYNTHETIC')
            prefix="import subprocess\nsubprocess.check_output=lambda cmd,**kw:'GPU-SYNTHETIC, NVIDIA RTX A6000, 0' if '-i' in cmd else ''\n"
            env={k:v for k,v in os.environ.items() if k!='PYTHONPATH'}
            captures={}
            for mode in ('health','terminal'):
                code=module.remote_code(launch,mode).replace("'/home/gaokuangda/data/gkd/worldcache_omr'",repr(str(root)))
                child=subprocess.run([sys.executable,'-S','-c',prefix+code],cwd=root,env=env,capture_output=True,timeout=10)
                self.assertEqual(child.returncode,0,child.stderr.decode())
                captures[mode]=json.loads(gzip.decompress(child.stdout))
            health=captures['health'];terminal=captures['terminal']
            self.assertEqual(health['technical_progress']['original_runner_positions'],1)
            for field in ('runner','final','profile_scalar_originals'):
                self.assertNotIn(field,health)
            self.assertNotIn('MUST_NOT_LEAK',json.dumps(health))
            self.assertNotIn('final',health['original_file_receipts'])
            observed=terminal['profile_scalar_originals'][str(profile)]
            self.assertEqual(observed['sha256'],sha(profile));self.assertTrue(observed['matches_original_row_identity'])
            self.assertEqual(observed['data'],dict(synthetic=True,not_GPU_measurement=True))
            self.assertIn('parse_error',terminal['original_file_receipts']['final'])
            self.assertEqual((root/'reports/gpu-budget-v2.json').read_bytes(),ledger_before)

    def test_original_transport_failure_and_malformed_bytes_preserved_without_retry(self):
        module=script()
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);launch=root/'launch.json';write(launch,dict(dispatch=dict(next_check_not_before_unix=0)))
            for mode in ('timeout','malformed'):
                output=root/(mode+'.gz');args=['test','--launch-ref',str(launch),'--output',str(output)]
                result=type('Result',(),dict(returncode=0,stdout=b'ORIGINAL_INVALID',stderr=b''))()
                with patch.object(sys,'argv',args),patch.object(module.subprocess,'run',return_value=result,
                        side_effect=subprocess.TimeoutExpired('SYNTHETIC_SSH',150) if mode=='timeout' else None) as network:
                    with self.assertRaises((subprocess.TimeoutExpired,gzip.BadGzipFile)):module.main()
                self.assertEqual(network.call_count,1)
                if mode=='timeout':
                    self.assertFalse(json.loads(gzip.decompress(output.read_bytes()))['original_task_terminal'])
                else:self.assertEqual(output.read_bytes(),b'ORIGINAL_INVALID')
                with patch.object(sys,'argv',args),patch.object(module.subprocess,'run') as retry:
                    with self.assertRaises(FileExistsError):module.main()
                retry.assert_not_called()


if __name__=='__main__':unittest.main()
