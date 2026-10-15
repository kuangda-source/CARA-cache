"""Concurrent real flock/atomic accounting; no model or server access."""
import copy,json,multiprocessing as mp,tempfile,unittest
from pathlib import Path
from wcomr.gpu_budget_pool_v2 import BudgetPool,DeviceLease,atomic_json

def legacy():
    return dict(job_id='original-W3',kind='LEGACY_W3',status='RESERVED_OR_RUNNING',billed_limit_GPUh=12,
        gpu_uuid='GPU-original',source_revision='old-frozen-source',launch_id='original-launch',
        supervisor_pid=123,supervisor_start_ticks=456,stage='original-stage')

def newjob(i,limit=6):
    return dict(job_id='new-'+str(i),gpu_uuid='GPU-'+str(i),source_revision='new-source',config_sha256='a'*64,
        launch_id='launch-'+str(i),forecast_GPUh=limit-.1,billed_limit_GPUh=limit)

def gpu(i):return dict(uuid='GPU-'+str(i),name='NVIDIA RTX A6000',compute_cap='8.6',memory_used_mib=413,pids=[])
def reserve_worker(project,i,q):
    try:BudgetPool(project).reserve(newjob(i),gpu(i));q.put('ACCEPT')
    except ValueError:q.put('REFUSE')
def settle_worker(project,i):BudgetPool(project).settle('new-'+str(i),1+i/10,'b'*64)

class PoolTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);self.pool=BudgetPool(self.root)
        self.auth=dict(direct_user_authorization=True,cumulative_cap_GPUh=105,autonomy_exclusive_upper_GPUh=12,user_reply_quote='双卡锁和记账，空闲卡同26D')
        self.pool.initialize(cap=105,origin_used=80,origin_jobs=94,authorization=self.auth,legacy_job=legacy())
        atomic_json(self.root/'reports/budget.json',dict(cap_gpu_hours=105,used_gpu_hours=105,gpu_jobs_launched=95,wc_w3_label64_inflight={'supervisor_pid':123}))
    def tearDown(self):self.tmp.cleanup()
    def test_device_exclusion_and_other_device_independent(self):
        with DeviceLease(self.root,'GPU-original'):
            with self.assertRaises(BlockingIOError):DeviceLease(self.root,'GPU-original').acquire()
            with DeviceLease(self.root,'GPU-0'):pass
        with DeviceLease(self.root,'GPU-original'):pass
    def test_atomic_concurrent_reserve_never_overbooks(self):
        ctx=mp.get_context('fork');q=ctx.Queue();children=[ctx.Process(target=reserve_worker,args=(self.root,i,q)) for i in range(3)]
        for p in children:p.start()
        for p in children:p.join();self.assertEqual(p.exitcode,0)
        answers=[q.get(timeout=2) for p in children]
        self.assertEqual(answers.count('ACCEPT'),2);v=self.pool.read();self.assertEqual(v['reserved_gpu_hours'],24);self.assertEqual(v['available_gpu_hours'],1)
        self.assertEqual(json.loads((self.root/'reports/budget.json').read_text())['used_gpu_hours'],105)
    def test_concurrent_settle_and_legacy_snapshot_does_not_erase(self):
        for i in range(2):self.pool.reserve(newjob(i),gpu(i))
        ctx=mp.get_context('fork');children=[ctx.Process(target=settle_worker,args=(self.root,i)) for i in range(2)]
        for p in children:p.start()
        for p in children:p.join();self.assertEqual(p.exitcode,0)
        # Original writer does exactly its old snapshot rewrite.
        atomic_json(self.root/'reports/budget.json',dict(cap_gpu_hours=105,used_gpu_hours=83,gpu_jobs_launched=95))
        self.pool.settle('original-W3',3,'c'*64);v=self.pool.read()
        self.assertAlmostEqual(v['used_gpu_hours'],85.1);self.assertEqual(v['gpu_jobs_launched'],97)
        self.assertEqual(self.pool.mirror_after_legacy_post(post_exit=self.root/'post.json',expected_legacy_pid=123),'DEFERRED_UNTIL_ORIGINAL_CPU_POST_TERMINAL')
        self.assertEqual(json.loads((self.root/'reports/budget.json').read_text())['used_gpu_hours'],83)
        atomic_json(self.root/'post.json',dict(status='W3_LABEL64_FULL_POST_CPU_TERMINAL',exit_code=0))
        self.pool.mirror_after_legacy_post(post_exit=self.root/'post.json',expected_legacy_pid=123)
        self.assertAlmostEqual(json.loads((self.root/'reports/budget.json').read_text())['used_gpu_hours'],85.1)
    def test_replay_conflict_nonfinite_and_limit(self):
        self.pool.reserve(newjob(0),gpu(0))
        with self.assertRaises(ValueError):self.pool.reserve(newjob(0),gpu(0))
        self.pool.settle('new-0',1,'b'*64);original=self.pool.read()
        self.assertEqual(self.pool.settle('new-0',1,'b'*64),original)
        with self.assertRaises(ValueError):self.pool.settle('new-0',2,'b'*64)
        for n in (float('nan'),float('inf'),-1):
            with self.assertRaises(ValueError):self.pool.settle('original-W3',n,'a'*64)
        with self.assertRaises(ValueError):self.pool.reserve(newjob(1,12),gpu(1))
        bad=legacy();bad['source_revision']='different-source'
        with self.assertRaises(ValueError):self.pool.initialize(cap=105,origin_used=80,origin_jobs=94,authorization=self.auth,legacy_job=bad)
    def test_overrun_is_recorded_not_hidden(self):
        self.pool.reserve(newjob(0),gpu(0));v=self.pool.settle('new-0',6.1,'b'*64)
        self.assertTrue(v['budget_overrun_recorded']);self.assertAlmostEqual(v['used_gpu_hours'],86.1)
        with self.assertRaises(ValueError):self.pool.reserve(newjob(1,1),gpu(1))

if __name__=='__main__':unittest.main()
