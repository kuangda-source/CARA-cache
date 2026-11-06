"""Whole-card lifecycle controls; actual Linux Docker FD proof runs on server."""
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT/'src')]
from four_card_bank24_execution_adapter_r1 import LIFECYCLE_SOURCE
from four_card_bank24_container_transport_r1 import retain_full_rows,run_inherited,socket_path
from four_card_bank24_gpu_port_r1 import generate,full_quote,validate_handoff,sha,require_full_CPU
from wc_four_card_bank24_container_cpu_r1 import SETUP,CAPTURE
from check_wc_four_card_bank24_container_cpu_r1 import child_probe_source,negative_post_source


def original(name):return subprocess.check_output(['git','show',LIFECYCLE_SOURCE+':'+name],cwd=ROOT)


class ContainerLifecycleTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        for name in ['scripts/run_wc_drop1_full18_r1.py','scripts/postprocess_wc_scout_gpu_r1.py',
                     'src/wcomr/scout_gpu_lifecycle_r1.py','src/wcomr/gpu_budget_pool_v2.py']:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(original(name))
        self.quote=json.loads(original('reports/wc_scout_BANK24_whole_quote_R1_20261018.json'))
        self.config=json.loads(original('configs/wc_scout_bank24_production_entry_r1_20261018.json'))
        self.plan=self.quote['positions']
    def tearDown(self):self.temp.cleanup()

    def test_full24_quote_explicitly_planning(self):
        q=full_quote(self.quote,self.config['scope_counts'])
        self.assertEqual(len(q['positions']),24);self.assertEqual(q['billed_limit_GPUh'],8.75)
        self.assertAlmostEqual(q['forecast_complete_GPUh'],6.974166666666667)
        self.assertTrue(all(v is None for v in q['actual_new_host_terms_seconds'].values()))
        self.assertFalse(q['actual_new_host_measured_quote_accepted'])
    def test_missing_whole_term_refused(self):
        q=copy.deepcopy(self.quote);q['terms_seconds'].pop('observer_copy_hash_allowance')
        with self.assertRaises(ValueError):full_quote(q,self.config['scope_counts'])
    def test_nan_term_refused(self):
        q=copy.deepcopy(self.quote);q['terms_seconds']['load']=float('nan')
        with self.assertRaises(ValueError):full_quote(q,self.config['scope_counts'])
    def test_split_scope_refused(self):
        q=copy.deepcopy(self.quote);q['positions']=q['positions'][:18]
        with self.assertRaises(ValueError):full_quote(q,self.config['scope_counts'])
    def test_all_missing_retained_without_scores(self):
        rows=retain_full_rows(self.plan,[])
        self.assertEqual(len(rows),24);self.assertTrue(all(r['status']=='NOT_REACHED_RETAINED' for r in rows))
        self.assertFalse(any('LPIPS' in r for r in rows))
    def test_failure_three_started_keeps21_missing(self):
        rows=retain_full_rows(self.plan,[dict(r,status='CPU_CONTROL_VISITED_NOT_NEURAL_OUTPUT') for r in self.plan[:3]])
        self.assertEqual(sum(r['status']=='NOT_REACHED_RETAINED' for r in rows),21)
    def test_duplicate_foreign_path_refused(self):
        for bad in [[self.plan[0],self.plan[0]],[dict(id='foreign')]]:
            with self.assertRaises(ValueError):retain_full_rows(self.plan,bad)
    def test_owned_timeout_stops_own_group(self):
        fd=os.open(self.root/'probe.lock',os.O_CREAT|os.O_RDWR,0o600)
        try:
            with (self.root/'child.log').open('w') as log:
                result=run_inherited([sys.executable,'-c','import time;time.sleep(10)'],fd,dict(os.environ),.05,log)
            self.assertTrue(result['owned_timeout_stop']);self.assertTrue(result['child_exited']);self.assertGreater(result['wall_seconds'],0)
        finally:os.close(fd)
    def test_generated_post_preserves_original_raw_and_all93_logic(self):
        sources,binding=generate(self.root)
        self.assertEqual(len(sources),5)
        self.assertIn('torch.cuda.get_device_capability()==(8,9)',sources['bank24-fourcard-runner.py'])
        for text in ['assert n == 93',"len(guides) == 36",'map_location=\'cpu\', weights_only=True','score_pair(left, right, metric',"owners_alive_after"]:
            self.assertIn(text,sources['bank24-fourcard-post.py']+sources['bank24-fourcard-accept-terminal-function.py'])
        self.assertTrue(binding['full_acceptance24_denominator_and_all_errors_preserved'])
    def test_no_fake_old_execution_revision(self):
        sources,_=generate(self.root)
        self.assertIn("launch['entry_source_revision']",sources['bank24-fourcard-accept-terminal-function.py'])
        self.assertIn("scientific_entry_source_revision",sources['bank24-fourcard-accept-terminal-function.py'])
    def test_missing_full_production_CPU_refused(self):
        with self.assertRaises(FileNotFoundError):require_full_CPU(self.root,'not-a-proof')
    def test_missing_authority_refused_before_read(self):
        with self.assertRaises(ValueError):validate_handoff(self.root,{})
        self.assertFalse((self.root/'reports/gpu-budget-v2.json').exists())
    def test_full_authority_fixture_rejects_truncated_history(self):
        # Test-only JSON data, never a real handoff or project ledger.
        (self.root/'reports').mkdir()
        data=dict(schema='WC_GPU_BUDGET_POOL_V2',cap_gpu_hours=226,origin_used_gpu_hours=79.99637737158223,
            jobs={'CPU_TEST_ONLY_ORIGINAL':dict(status='SETTLED',actual_GPUh=1)},writer_epoch='CPU_TEST_ONLY')
        old=self.root/'reports/CPU_TEST_ONLY_snapshot.json';old.write_text(json.dumps(data))
        current=self.root/'reports/gpu-budget-v2.json';current.write_text(json.dumps(data))
        proof=dict(status='WC_V2_UNIQUE_WRITER_HANDOFF_INDEPENDENTLY_ACCEPTED',old_host_new_GPU_dispatch_fenced=True,
            new_unique_writer='four_card',checks={'CPU_FIXTURE_ONLY':True},cap_GPUh=226,origin_used_GPUh=79.99637737158223,
            reset_history=False,old_authoritative_snapshot_ref='reports/CPU_TEST_ONLY_snapshot.json',
            old_authoritative_snapshot_sha256=sha(old),writer_epoch='CPU_TEST_ONLY')
        self.assertTrue(validate_handoff(self.root,proof)['handoff_accepted'])
        bad=copy.deepcopy(data);bad['jobs']={};current.write_text(json.dumps(bad))
        with self.assertRaises(ValueError):validate_handoff(self.root,proof)
    def test_no_GPU_dispatch_in_actual_CPU_templates(self):
        compile(SETUP,'<CPU-only-setup>','exec');compile(CAPTURE,'<CPU-only-collector>','exec')
        self.assertNotIn('nvidia-smi',SETUP+CAPTURE);self.assertNotIn('.is_relative_to(',SETUP)
        self.assertIn('EXISTING_STAGE_RESTORE_ONLY',SETUP)
        self.assertIn('own_CPU_fixture_lease_free',CAPTURE)
    def test_real_child_and_negative_post_probe_sources_compile(self):
        compile(child_probe_source(),'<inherited-real-child>','exec')
        compile(negative_post_source(self.root,self.root/'TEST_ONLY',self.root/'post-failure-fixture'),'<post-negative>','exec')
    def test_unix_socket_remains_short_across_long_job_namespace(self):
        path=socket_path(Path('/data20t/gaokuangda/worldcache_workspace/bootstrap')/('long-name-'*20))
        self.assertLess(len(os.fsencode(path)),108)
        self.assertEqual(path.parent.parent,Path('/tmp'))


if __name__=='__main__':unittest.main()
