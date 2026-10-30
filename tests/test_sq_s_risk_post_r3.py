"""Frozen S scalar/grammar equivalence; actual FP64 small CPU reductions only."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

import torch

from wcomr.policy_generator_r1.interval_grammar import Profile,digest
from wcomr.sq_risk_r1 import TARGETS,branch_moments
from wcomr.sq_schedule_profile_r2 import plans_from_moments
from wcomr.sq_s_spec_r2 import SCOPE,RISK,HISTORY
from wcomr.sq_s_risk_post_r3 import from_validated_rows
from prepare_cara_sq_s_history_support_r3 import build

ROOT=Path(__file__).resolve().parents[1]


def inputs():
    read=lambda path:json.loads((ROOT/path).read_text())
    return read(SCOPE),read(RISK),read(HISTORY)


def rows(contract,kind='different'):
    result=[]
    for prompt in contract['prompts']:
        for parent in contract['parents']:
            for step in TARGETS:
                c,u={9:(3.,3.),11:(2.2,-2.2),13:(4.,0.)}.get(step,(0.,0.)) if kind=='different' else (0.,0.)
                teacher=(torch.ones(2,dtype=torch.float64),torch.ones(2,dtype=torch.float64))
                candidate=(teacher[0]+c,teacher[1]+u)
                if kind=='tiny_positive' and step==9:
                    teacher=(torch.zeros(1,dtype=torch.float64),torch.ones(1,dtype=torch.float64))
                    candidate=(torch.full((1,),1e-150,dtype=torch.float64),teacher[1])
                result.append(dict(prompt=prompt,parent=parent,step=step,noise_grid_sha256=contract['noise_grid_sha256'],
                    moments=branch_moments(candidate,teacher)))
    return result


def execute(data,scope,contract,history):
    return from_validated_rows(data,scope,contract,history,{'EXPLICIT_CPU_FIXTURE':True})


class RiskTests(unittest.TestCase):
    def test_actual_FP64_reductions_keep_original_risk_policies_scores_and_aliases(self):
        scope,contract,history=inputs();data=rows(contract)
        values=dict(contract['profile'])
        for key in ('protected_dense','alpha_candidates'):values[key]=tuple(values[key])
        support={tuple(value) for value in history['supported_C_histories']}
        original=plans_from_moments(data,Profile(**values),baselines=contract['baselines'],
            execution_identity={'EXPLICIT_CPU_FIXTURE':True},propagation={step:1. for step in TARGETS},
            supports_history=lambda *value:value in support)
        result=execute(data,scope,contract,history)
        self.assertEqual(result['risk'],original['risk']);self.assertEqual(result['policies'],original['policies'])
        self.assertEqual(result['execution_equivalence'],original['execution_equivalence'])
        for name in ('BR','DIAG','CFG'):
            self.assertEqual(result['choices'][name]['dense'],original['choices'][name]['dense'])
            self.assertEqual(result['scores'][name],[{key:row[key] for key in ('remove','add','score')} for row in original['scores'][name]])
        self.assertEqual({name:value['exchange']['add'] for name,value in result['choices'].items()},dict(BR=9,DIAG=13,CFG=11))
        self.assertTrue(all(choice['exchange']['remove']==8 for choice in result['choices'].values()))
        self.assertFalse(result['GPU_ready']);self.assertFalse(result['free_running_or_endpoint_acceptance'])

    def test_zero_gain_returns_F19_and_uniform_time_prior_share_one_execution(self):
        scope,contract,history=inputs();result=execute(rows(contract,'flat'),scope,contract,history)
        self.assertEqual(len(result['execution_equivalence']),2)
        self.assertTrue(all(value['exchange'] is None for value in result['choices'].values()))
        self.assertTrue(any(set(names)=={'F19_C','S_BR19','S_DIAG19','S_CFG19'} for names in result['execution_equivalence'].values()))
        self.assertTrue(any(set(names)=={'Uniform19_C','time_prior_C'} for names in result['execution_equivalence'].values()))

    def test_strictly_positive_tiny_gain_does_not_acquire_an_unregistered_epsilon(self):
        scope,contract,history=inputs();result=execute(rows(contract,'tiny_positive'),scope,contract,history)
        self.assertTrue(all(value['exchange']['add']==9 for value in result['choices'].values()))
        self.assertTrue(all(0<value['score']<1e-290 for value in result['choices'].values()))

    def test_missing_duplicate_foreign_or_wrong_grid_rows_cannot_make_a_mask(self):
        scope,contract,history=inputs()
        for kind in ('old12','duplicate','foreign','grid'):
            with self.subTest(kind=kind):
                data=rows(contract)
                if kind=='old12':data=data[:12]
                if kind=='duplicate':data[-1]=copy.deepcopy(data[0])
                if kind=='foreign':data[-1]['prompt']='FOREIGN'
                if kind=='grid':data[-1]['noise_grid_sha256']='f'*64
                with self.assertRaises(ValueError):execute(data,scope,contract,history)

    def test_all_objectives_require_the_same_frozen_weights_and_candidate_support(self):
        scope,contract,history=inputs();data=rows(contract)
        for kind in ('weights','propagation','old158','history','objective'):
            with self.subTest(kind=kind):
                changed=copy.deepcopy(contract);proof=copy.deepcopy(history)
                if kind=='weights':changed['parent_weights']=[.75,.25]
                if kind=='propagation':changed['propagation']['g'][0]=2.
                if kind=='old158':changed['candidate_count']=158
                if kind=='history':proof['supported_C_histories'].pop()
                if kind=='objective':changed['objectives']=['CFG']
                changed['rule_sha256']=digest({key:value for key,value in changed.items() if key!='rule_sha256'})
                proof['rule_sha256']=changed['rule_sha256']
                with self.assertRaises(ValueError):execute(data,scope,changed,proof)

    def test_nonfinite_or_overflowed_risk_is_refused(self):
        scope,contract,history=inputs()
        for kind in ('nonfinite','overflow'):
            with self.subTest(kind=kind):
                data=rows(contract)
                if kind=='nonfinite':data[0]['moments']['normalized']['CFG']=float('nan')
                else:
                    for row in data:
                        for name in ('BR','DIAG','CFG'):row['moments']['normalized'][name]=1.7e308
                with self.assertRaises(ValueError):execute(data,scope,contract,history)

    def test_prompt_disagreement_is_reported_without_changing_frozen_weights(self):
        scope,contract,history=inputs();data=rows(contract)
        for row in data:
            if row['prompt']==contract['prompts'][1] and row['step'] in (9,15):
                teacher=(torch.ones(2,dtype=torch.float64),torch.ones(2,dtype=torch.float64))
                error=4.5 if row['step']==15 else 0.
                row['moments']=branch_moments(tuple(value+error for value in teacher),teacher)
        result=execute(data,scope,contract,history)
        self.assertFalse(result['ranking_diagnostics']['BR']['same_top_exchange'])
        self.assertEqual(result['choices']['BR']['exchange']['add'],15)
        self.assertEqual(result['risk']['BR'][15],10.125)
        self.assertFalse(result['guided_identity_diagnostics']['selection_threshold_added'])
        self.assertFalse(result['GPU_ready'])

    def test_original_production_selector_history_proof_is_exactly_reproducible(self):
        scope,contract,history=inputs();self.assertEqual(build(scope,contract),history)
        self.assertEqual(history['checked_distinct_policies'],172)
        self.assertEqual(history['checked_selector_pairs'],6192)
        self.assertFalse(history['free_running_or_endpoint_acceptance'])

    def test_native_risk_module_imports_without_Torch(self):
        code="import sys;sys.path.insert(0,"+repr(str(ROOT/'src'))+");sys.modules['torch']=None;from wcomr import sq_s_risk_post_r3"
        subprocess.run([sys.executable,'-c',code],check=True,capture_output=True,text=True)


if __name__=='__main__':unittest.main()
