"""Run the actual bridge against synthetic legacy receipts and an actual pool."""
import json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from wcomr.gpu_budget_pool_v2 import BudgetPool,atomic_json,sha

class BridgeTests(unittest.TestCase):
    def test_import_waits_for_cpu_post_without_touching_old_ledger(self):
        repo=Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);stage=root/'stage';stage.mkdir();(stage/'src').symlink_to(repo/'src',target_is_directory=True)
            oldstage=root/'old-stage';(oldstage/'scripts').mkdir(parents=True)
            oldscript=oldstage/'scripts/supervise_wc_w3_label64_full864_r1.py';oldscript.write_text('# frozen legacy source\n')
            out=root/'outputs/original-W3';out.mkdir(parents=True)
            before=dict(cap_gpu_hours=105,used_gpu_hours=80,gpu_jobs_launched=94)
            sup=dict(status='W3_LABEL64_GPU_EXITED_REQUIRES_FULL_RAW_CPU_AUDIT',source_revision='old-source',pid=99999999,
                launch_id='old-launch',admission={'uuid':'GPU-original'},budget_before=before,authorized_billed_GPUh_limit=12,
                wall_seconds=10800,ended_unix=time.time(),budget_after={**before,'used_gpu_hours':83,'gpu_jobs_launched':95})
            atomic_json(out/'supervisor.json',sup);atomic_json(root/'reports/budget.json',sup['budget_after'])
            original_sha=sha(root/'reports/budget.json')
            binding=dict(legacy_stage='old-stage',legacy_run='original-W3',legacy_source='old-source',supervisor_pid=99999999,
                supervisor_start_ticks=0,launch_id='old-launch',gpu_uuid='GPU-original',legacy_supervisor_sha256=sha(oldscript),
                cumulative_cap_GPUh=105,origin_used_GPUh=80,origin_jobs=94,authority=dict(direct_user_authorization=True,
                    cumulative_cap_GPUh=105,autonomy_exclusive_upper_GPUh=12,user_reply_quote='dual GPU authorized'))
            atomic_json(stage/'binding.json',binding)
            with (stage/'log').open('w') as log:
                child=subprocess.Popen([sys.executable,str(repo/'scripts/bridge_wc_legacy_w3_budget_v2.py'),
                    '--project',str(root),'--stage',str(stage),'--binding',str(stage/'binding.json')],stdout=log,stderr=subprocess.STDOUT)
                try:
                    deadline=time.monotonic()+5
                    while time.monotonic()<deadline:
                        if (stage/'legacy-bridge.json').exists() and json.loads((stage/'legacy-bridge.json').read_text())['status']=='LEGACY_W3_GPU_SETTLED_WAITING_ORIGINAL_CPU_POST':break
                        if child.poll() is not None:raise AssertionError((stage/'log').read_text())
                        time.sleep(.02)
                    self.assertEqual(BudgetPool(root).read()['used_gpu_hours'],83)
                    self.assertEqual(sha(root/'reports/budget.json'),original_sha)
                    # Original CPU read phase ends. Only now may the mirror change.
                    atomic_json(oldstage/'post-CPU-exit.json',dict(status='W3_LABEL64_FULL_POST_CPU_TERMINAL',exit_code=0))
                    self.assertEqual(child.wait(timeout=30),0,(stage/'log').read_text())
                    self.assertEqual(json.loads((stage/'legacy-bridge.json').read_text())['status'],'LEGACY_W3_BRIDGE_TERMINAL')
                    old=json.loads((root/'reports/budget.json').read_text())
                    self.assertEqual(old['used_gpu_hours'],83);self.assertIn('wc_gpu_v2_inflight_protocol',old)
                    self.assertEqual(BudgetPool(root).read()['gpu_jobs_launched'],95)
                finally:
                    if child.poll() is None:child.terminate();child.wait(timeout=5)

if __name__=='__main__':unittest.main()
