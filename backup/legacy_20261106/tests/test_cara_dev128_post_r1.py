"""Actual post entry, release barriers, 10h child envelope and source-bound spawn.

Heavy metrics/decoded videos use the separately accepted CPU evidence. This
suite injects declared complete packets; it does not fabricate model evidence.
"""
import copy,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace,ModuleType
from unittest.mock import patch
from wcomr.policy_generator_r1.dev128_card import RUN,MANIFEST,REQUESTS
from wcomr.gpu_budget_pool_v2 import atomic_json
from wcomr.policy_price_terminal_r1 import record
from test_cara_dev128_terminal_r1 import fixture,METRIC

class Post(unittest.TestCase):
 def exercise(self,fail_release=False):
  import postprocess_cara_dev128_r1 as post
  import wcomr.policy_generator_r1.dev128_execution as contract
  import wcomr.policy_generator_r1.dev128_collection as collection
  import wcomr.policy_generator_r1.dev128_capture as capture
  import wcomr.policy_generator_r1.dev128_quality as quality
  import wcomr.policy_generator_r1.dev128_quality_process as qp
  import wcomr.policy_generator_r1.production_evidence as evidence
  import wcomr.gpu_budget_pool_v2 as budget
  try:import torch
  except ImportError:self.skipTest('Real torch CPU runs on registered hosts')
  self.assertFalse(torch.cuda.is_initialized());v=fixture();events=[]
  with tempfile.TemporaryDirectory() as d:
   root=Path(d);stage=root/'stage';stage.mkdir();out=root/'outputs'/RUN;out.mkdir(parents=True)
   sup=record(v,'supervisor');sup['child_identity']['pid']=99999999
   if fail_release:sup['exclusive_monitor_accepted']=False
   for key,name in [('runner','runner.json'),('billing','billing.json')]:atomic_json(out/name,record(v,key))
   atomic_json(out/'supervisor.json',sup)
   raw_bill=evidence.sha(out/'billing.json');pool=copy.deepcopy(v['pool']);pool['jobs'][RUN]['billing_sha256']=raw_bill
   binding=dict(identity=record(v,'quality_plan')['evaluator_identity']);atomic_json(stage/'quality-binding.json',binding)
   atomic_json(stage/'pg-GPU-authorization.json',v['launch'])
   card=record(v,'card');requests=[dict(name=m,prompt='CPU '+m) for m in card['DEV_members']];atomic_json(stage/REQUESTS,dict(requests=requests))
   reg=dict(payload_sha256={'quality-binding.json':evidence.sha(stage/'quality-binding.json')})
   class Metric:
    def cpu(self):return self
    def eval(self):return self
    def parameters(self):return []
   fake=ModuleType('lpips');fake.LPIPS=lambda **kw:Metric()
   def scores(c,b,o,m,i,release,save):
    self.assertTrue(all(release[k] for k in ('GPU_released','ledger_settled','lock_free','CUDA_hidden')))
    self.assertEqual(release['billing_sha256'],raw_bill);self.assertEqual(len(b['rows']),128)
    events.append('LPIPS80');return record(v,'score_progress')
   def quality_child(b,bp,p,release,o):
    self.assertEqual(len(p['rows']),288);self.assertEqual(events,['LPIPS80']);events.append('QUALITY288')
   with patch.dict(os.environ,CUDA_VISIBLE_DEVICES=''),patch.dict(sys.modules,lpips=fake),patch.object(contract,'validate',lambda *a:({},reg,card)),patch.object(budget.BudgetPool,'read',lambda self:pool),patch.object(collection,'score_after_release',scores),patch.object(evidence,'metric_resource_identity',lambda p:METRIC),patch.object(quality,'plan',lambda *a:record(v,'quality_plan')),patch.object(qp,'run_bound_child',quality_child),patch.object(capture,'collect',lambda *a:v),patch('resource.getrlimit',return_value=(8*2**30,8*2**30)),patch('os.sched_getaffinity',return_value={0,1},create=True),patch.object(sys,'argv',['post','--project',str(root),'--stage',str(stage)]):
    if fail_release:
     with self.assertRaises(AssertionError):post.main()
     self.assertEqual(events,[]);self.assertFalse((out/'post-results.json').exists())
    else:
     post.main();r=json.loads((out/'post-results.json').read_text());self.assertEqual(r['scientific']['complete_paths'],128);self.assertEqual(events,['LPIPS80','QUALITY288'])
 def test_actual_post_entry(self):self.exercise()
 def test_unreleased_blocks_all_metrics(self):self.exercise(True)

class ModelChild(unittest.TestCase):
 def test_new_orchestration_original_metric_source(self):
  import hashlib
  from wcomr.policy_generator_r1.dev128_quality_process import run_bound_child,ENTRY
  h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
  with tempfile.TemporaryDirectory() as d,patch.dict(os.environ,CUDA_VISIBLE_DEVICES=''):
   root=Path(d);stage=root/'stage';(stage/'scripts').mkdir(parents=True);(stage/ENTRY).write_text('# declared fixture')
   atomic_json(stage/'registration.json',dict(payload_sha256={ENTRY:h(stage/ENTRY)}))
   overlay=root/'cache/overlay';overlay.mkdir(parents=True);(overlay/'file.py').write_text('# fixture')
   lock=overlay.parent/'dependency-overlay-manifest.json';atomic_json(lock,dict(base_environment_modified=False,files={'file.py':h(overlay/'file.py')}))
   b=dict(identity={'declared':True},registration={'stage':'/original/accepted/model'},dependency_overlay=str(overlay),dependency_overlay_manifest_sha256=h(lock));bp=stage/'quality-binding.json';atomic_json(bp,b);out=root/'out';out.mkdir();calls=[]
   release=dict(GPU_released=True,ledger_settled=True,lock_free=True,CUDA_hidden=True)
   run_bound_child(b,bp,dict(evaluator_identity=b['identity']),release,out,run=lambda cmd,**kw:calls.append((cmd,kw)))
   self.assertEqual(calls[0][0][1],str(stage/ENTRY));self.assertEqual(calls[0][1]['env']['CUDA_VISIBLE_DEVICES'],'')
   with self.assertRaises(ValueError):run_bound_child(b,bp,dict(evaluator_identity=b['identity']),dict(release,GPU_released=False),out,run=lambda *a,**kw:calls.append(1))
   (stage/ENTRY).write_text('changed')
   with self.assertRaises(ValueError):run_bound_child(b,bp,dict(evaluator_identity=b['identity']),release,out,run=lambda *a,**kw:calls.append(1))
   self.assertEqual(len(calls),1)
