"""Central reservation rejection paths with isolated filesystem fixtures."""
import contextlib,copy,io,json,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wc_cara_ig_b1_gpu_r1 as control
from wcomr.gpu_budget_pool_v2 import SCHEMA,atomic_json
from wcomr.policy_generator_r1.dev128_finance import HostBudgetPool

class Dispatch(unittest.TestCase):
 def exercise(self,change=None):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);pool=HostBudgetPool(root)
   prior=dict(schema=SCHEMA,cap_gpu_hours=226,origin_used_gpu_hours=180.,origin_gpu_jobs_launched=10,
    jobs={'DEV128':dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-old',launch_id='original',billed_limit_GPUh=12.,confirmed_GPU_submission=True)},events=[])
   prior.update(pool.accounting(prior));atomic_json(pool.path,prior)
   auth=dict(run_id=control.RUN,launch_id='new',source_revision='accepted',gpu_uuid='GPU-new',stage='new-stage',scope_counts=control.COUNTS,billed_limit_GPUh=1.5,host='two_card')
   release=dict(exclusive_accepted=True,child_dead=True,launch=dict(launch_id='original',gpu_uuid='GPU-old'))
   p=dict(source_stage=str(root),auth=auth,two_probe=dict(observed_unix=time.time(),intents={},released_DEV128=release),four_probe=dict(observed_unix=time.time(),intents={}))
   if change:change(p,prior);prior.update(pool.accounting(prior));atomic_json(pool.path,prior)
   source=control.CENTRAL.replace("'/data20t/gaokuangda/worldcache_workspace'",repr(str(root)))
   with patch('sys.stdin',io.StringIO(json.dumps(p))),contextlib.redirect_stdout(io.StringIO()):
    if change:
     with self.assertRaises(AssertionError):exec(compile(source,'CPU-central-fixture','exec'),{})
     self.assertEqual(pool.read(),prior)
    else:
     exec(compile(source,'CPU-central-fixture','exec'),{})
     after=pool.read();self.assertEqual(after['jobs']['DEV128'],prior['jobs']['DEV128'])
     self.assertEqual(after['reserved_gpu_hours'],13.5)
 def test_preserve_original_liability(self):self.exercise()
 def test_no_live_GPU_overlap(self):self.exercise(lambda p,v:p['two_probe']['released_DEV128'].update(child_dead=False))
 def test_no_cross_host_duplicate(self):self.exercise(lambda p,v:p['four_probe']['intents'].update(other='existing'))
 def test_keep_future_budget(self):self.exercise(lambda p,v:v.update(origin_used_gpu_hours=200.))
 def test_original_identity_required(self):self.exercise(lambda p,v:p['two_probe']['released_DEV128']['launch'].update(launch_id='wrong'))
 def test_remote_sources_parse(self):
  for name in ('PREPARE','PROBE','CENTRAL','LAUNCH'):compile(getattr(control,name),name,'exec')
if __name__=='__main__':unittest.main()
