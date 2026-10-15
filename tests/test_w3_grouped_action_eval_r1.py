"""Cohort integrity, train-only scaling, held-label and score-feature isolation."""
import copy,gzip,json,sys,unittest
from dataclasses import replace
from pathlib import Path
import numpy as np
from wcomr.w3_grouped_action_eval_r1 import accept_dataset,fit_fold,evaluate,COHORTS,replay_saved_features
ROOT=Path(__file__).resolve().parents[1]

class GroupedTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.original=json.loads(gzip.decompress((ROOT/'reports/wc_w3_label64_full864_collection_20261016_0100.json.gz').read_bytes()))
  cls.repair=json.loads(gzip.decompress((ROOT/'reports/wc_w3_readonly_video_audit_r2_collection_20261016_0119.json.gz').read_bytes()))
  cls.data,cls.accept=accept_dataset(ROOT,cls.original,cls.repair)
 def test_real_cohorts_do_not_include_warm_or_hide_failed_video(self):
  self.assertEqual((len(self.data),sum(s['primary'] for s in self.data)),(56,48))
  self.assertEqual((self.accept['primary_prompt_groups'],self.accept['sensitivity_prompt_groups']),(6,7))
  self.assertFalse(self.accept['all72_success_claim'])
  self.assertEqual(len([x for x in self.data if not x['RGB_complete']]),8)
 def test_held_labels_and_H1_scores_cannot_change_T1_T2_predictions(self):
  rows=[x for x in self.data if x['primary']];held=rows[0]['group']
  for model in ('T1','T2'):
   reg,pred,train,test=fit_fold(rows,held,model)
   tampered=[]
   for sample in rows:
    value={**sample,'frozen_T0_prediction':sample['frozen_T0_prediction']*100,'original_H1_action':'P'}
    if sample['group']==held:value['label']=replace(sample['label'],q_C=sample['label'].q_C*1000,q_A=sample['label'].q_A*1000)
    tampered.append(value)
   reg2,pred2,_,_=fit_fold(tampered,held,model)
   self.assertTrue(np.array_equal(reg.weights,reg2.weights));self.assertTrue(np.array_equal(reg.mean,reg2.mean))
   self.assertTrue(all(np.array_equal(pred[k],pred2[k]) for k in pred))
   expected=np.array([x['feature'][model].values for x in train])
   self.assertTrue(np.array_equal(reg.mean,expected.mean(0)))
   self.assertFalse(set(reg.training_prompts)&{x['feature'][model].observation.prompt for x in test})
 def test_fake_primary_admission_and_double_gain_are_refused(self):
  mutations=[lambda v:v['capture']['result']['labels'][0].__setitem__('primary_grouped_fit_admitted',True),
    lambda v:next(x for x in v['capture']['result']['labels'] if x['parent_id']=='9_FORMAL_DIAGNOSTIC').__setitem__('primary_grouped_fit_admitted',True),
    lambda v:v['capture']['result']['labels'][0]['gain_squared_targets'].__setitem__(0,v['capture']['result']['labels'][0]['gain_squared_targets'][0]*2),
    lambda v:v['capture']['exit'].__setitem__('source_revision','foreign'),
    lambda v:v['capture']['result'].__setitem__('raw_files',79)]
  for i,mutate in enumerate(mutations):
   bad=copy.deepcopy(self.repair);mutate(bad)
   with self.assertRaises((ValueError,AssertionError,KeyError)):accept_dataset(ROOT,self.original,bad)
 def test_saved_future_prefix_or_material_float_change_refused(self):
  runs=next(v['data'] for k,v in self.original['capture']['receipts'].items() if k.endswith('/runner.json'))['runs']
  rows=runs[3]['feature_rows'];clock=json.loads((ROOT/'reports/wc_w3_actual_schedule_native_CPU_replay_20261015.json').read_text())['result']
  for kind in ('prefix','value'):
   bad=copy.deepcopy(rows)
   if kind=='prefix':bad[10]['features']['T2']['prefix_steps'].append(36)
   else:bad[10]['features']['T2']['values'][0]+=1e-8
   with self.assertRaises(AssertionError):replay_saved_features(bad,clock)
 def test_all_folds_and_metric_denominators(self):
  for name in COHORTS:
   value=evaluate(self.data,name);n=value['prompt_groups']
   self.assertEqual(len(value['folds']),2*n);self.assertEqual(len(value['point_predictions']),4*8*n)
   for fold in value['folds']:
    self.assertNotIn(fold['held_group'],fold['training_groups']);self.assertEqual(fold['training_rows'],(n-1)*8)
    self.assertEqual(len(fold['feature_names']),13 if fold['model']=='T1' else 27)
   for model in value['models']:self.assertEqual(sum(model['action_counts'].values()),8*n)
if __name__=='__main__':unittest.main()
