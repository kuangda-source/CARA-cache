"""Saved-condition, real source C/RF routing and Q1 selection controls.

The head and teacher here are declared CPU fixtures, never Cosmos weights.
"""
import copy
from dataclasses import dataclass, replace
from enum import Enum
import json
from pathlib import Path
import random
import unittest
from unittest.mock import patch

import numpy as np
import torch

from test_scout_readout_v22 import fixture
from wcomr.full_sampling import CompleteStateRoundtrip
from wcomr.sq_q1_readout_r1 import (PROMPTS, STEPS, source_from_anchors, transfer,
    output_distortion, evaluate_saved_state, select_shared_codecs)
from wcomr.sq_schedule_profile_r2 import candidate_set, pure_C_policy, plans_from_moments
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.sq_risk_r1 import F19, TARGETS

ROOT = Path(__file__).resolve().parents[1]


class CPUDataType(str, Enum):
    VIDEO = 'video'


@dataclass(frozen=True)
class SavedCPUCondition:
    data_type: CPUDataType
    use_video_condition: bool
    gt_frames: torch.Tensor
    condition_video_input_mask_B_C_T_H_W: torch.Tensor

    @property
    def is_video(self):
        return self.data_type == CPUDataType.VIDEO

    def to_dict(self):
        return vars(self).copy()


def saved_fixture(prompt=PROMPTS[0], step=22, flow=False):
    kernel, args = fixture(flow=flow, step=step)
    context = (prompt, args['context'][1], args['context'][2])
    anchors = tuple(tuple(replace(a, context=context) for a in pair) for pair in args['anchors'])
    conditions = [SavedCPUCondition(CPUDataType.VIDEO, c.use_video_condition, c.gt_frames,
                                    c.condition_video_input_mask_B_C_T_H_W) for c in args['pair_inputs'][3]]
    inputs = args['pair_inputs'][:3]+(tuple(conditions),)
    output = kernel.run('C', source=source_from_anchors(anchors), current=args['current'], pair_inputs=inputs)[0]
    payload = dict(context=context, step=step, xi=args['xi'], anchors=tuple(tuple(vars(a) for a in p) for p in anchors),
                   current=args['current'], pair_inputs=dict(noise=inputs[0],latent=inputs[1],timestep=inputs[2],
                   conditions=[dict(class_name=type(c).__qualname__, fields={**vars(c),'data_type':'video'}) for c in conditions]),
                   readouts={'WC_C':{'outputs':tuple(v.clone() for v in output)}},
                   teacher=tuple(v+.05 for v in output), P0_actual_dense=True,
                   P1_dense_head_RF_equal=True, P2_C_actual_parent_equal=True)
    schema = [(SavedCPUCondition, {'data_type':CPUDataType}) for _ in (0,1)]
    return kernel, payload, schema


class Q1Tests(unittest.TestCase):
    def test_restored_condition_and_tensor_alias_transfer(self):
        tensor = torch.ones(2)
        condition = SavedCPUCondition(CPUDataType.VIDEO, True, tensor, tensor)
        moved = transfer((condition,tensor,tensor), 'meta')
        self.assertIs(moved[0].gt_frames, moved[1]);self.assertIs(moved[1],moved[2])
        self.assertEqual(moved[0].data_type, CPUDataType.VIDEO)

    def test_actual_output_error_cancellation_is_separate(self):
        d = (torch.ones(2,3),torch.ones(2,3))
        c = tuple(v+1 for v in d);q = tuple(v+.5 for v in d)
        error = output_distortion(q,c,d)
        for j in ('BR','CFG'):
            self.assertEqual(error[j]['q_total'],.25)
            self.assertEqual(error[j]['q_codec'],.25)
            self.assertEqual(error[j]['twice_alignment'],-1)

    def test_eight_formal_readouts_original_parity_and_no_mutation(self):
        for flow in (False,True):
            kernel,payload,schema = saved_fixture(flow=flow)
            before = copy.deepcopy(payload)
            result = evaluate_saved_state(kernel,payload,schema,device='cpu',max_copy_bytes=128*2**20)
            self.assertEqual(len(result['rows']),8);self.assertEqual(result['new_deep_pairs'],0)
            self.assertTrue(result['original_C_exact'] and result['state_roundtrip_equal'])
            for rate in ('R16','R12'):
                self.assertEqual(len({r['actual_bytes'] for r in result['rows'] if r['rate']==rate}),1)
            self.assertTrue(torch.equal(payload['current'][0]['probe'],before['current'][0]['probe']))

    def test_wrong_original_output_stops_before_codec_and_no_tolerance_tuning(self):
        kernel,payload,schema = saved_fixture()
        payload['readouts']['WC_C']['outputs'] = tuple(v+1 for v in payload['readouts']['WC_C']['outputs'])
        with patch('wcomr.sq_q1_readout_r1.packed_source',side_effect=AssertionError('codec must not run')):
            with self.assertRaisesRegex(ValueError,'Original C replay mismatch'):
                evaluate_saved_state(kernel,payload,schema,device='cpu',max_copy_bytes=128*2**20)

    def test_copy_cap_and_missing_control_refuse_before_head(self):
        kernel,payload,schema = saved_fixture()
        def forbidden(*args,**kwargs):raise AssertionError('head must not run')
        kernel.net.final_layer.forward=forbidden
        with self.assertRaisesRegex(ValueError,'cap exceeded'):
            evaluate_saved_state(kernel,payload,schema,device='cpu',max_copy_bytes=1)
        payload['P2_C_actual_parent_equal']=False
        with self.assertRaisesRegex(ValueError,'controls'):
            evaluate_saved_state(kernel,payload,schema,device='cpu',max_copy_bytes=128*2**20)

    def test_head_failure_restores_model_solver_and_three_rngs(self):
        kernel,payload,schema = saved_fixture()
        snapshot=CompleteStateRoundtrip(kernel.net,kernel.model.sample_scheduler,torch.zeros(1));before=snapshot.fingerprint()
        def broken(*args,**kwargs):
            kernel.net.audit_buffer.add_(1);kernel.model.sample_scheduler.history.append(torch.zeros(1))
            random.random();np.random.rand();torch.rand(3)
            raise OSError('injected Q1 head error')
        kernel.net.final_layer.forward=broken
        with self.assertRaisesRegex(OSError,'injected'):
            evaluate_saved_state(kernel,payload,schema,device='cpu',max_copy_bytes=128*2**20)
        self.assertEqual(snapshot.fingerprint(),before)

    def test_complete_cohort_selection_and_partial_refusal(self):
        states=[]
        for prompt in PROMPTS:
            for step in STEPS:
                kernel,payload,schema=saved_fixture(prompt,step)
                states.append(evaluate_saved_state(kernel,payload,schema,device='cpu',max_copy_bytes=128*2**20))
        selected=select_shared_codecs(states)
        self.assertEqual(len(selected['selections']),8)
        self.assertEqual(sum(len(a) for a in selected['execution_aliases'].values()),8)
        self.assertFalse(selected['partial_state_selection'])
        with self.assertRaisesRegex(ValueError,'All 12'):select_shared_codecs(states[:-1])


class SProfileTests(unittest.TestCase):
    def setUp(self):
        value=json.loads((ROOT/'manifests/cara_DEV128_scope_r1_20261026.json').read_text())['profile']
        value={k:tuple(v) if k in ('protected_dense','alpha_candidates') else v for k,v in value.items()}
        self.profile=Profile(**value)
        self.uniform=[1,2,3,4,5,6,7,16,19,22,23,24,25,26,27,28,29,31,36]

    def test_production_age_and_old_scout_default_are_distinct(self):
        full=candidate_set(self.profile);short=candidate_set(replace(self.profile,max_source_age=6))
        self.assertEqual(self.profile.max_source_age,28)
        self.assertEqual(len(full['candidates']),170);self.assertEqual(len(short['candidates']),158)
        self.assertTrue(all(24 in c['dense'] for c in full['candidates']))
        pure_C_policy(self.profile,self.uniform)
        with self.assertRaises(ValueError):pure_C_policy(replace(self.profile,max_source_age=6),self.uniform)
        self.assertEqual(candidate_set(self.profile,supports_history=lambda *h:False)['candidates'],[])

    def test_missing_moments_refuse_and_full_fixture_masks_deduplicate(self):
        baselines={'F19_C':list(F19),'Uniform19_C':self.uniform,'time_prior_C':self.uniform}
        rows=[dict(prompt=p,parent=h,step=t,moments={'normalized':dict(BR=1.,DIAG=2.,CFG=3.)})
              for p in PROMPTS for h in ('Shared25-C','F19-C') for t in TARGETS]
        kw=dict(baselines=baselines,execution_identity={'fixture':True},propagation={t:1. for t in TARGETS},supports_history=lambda *h:True)
        with self.assertRaisesRegex(ValueError,'INCOMPLETE'):plans_from_moments(rows[:12],self.profile,**kw)
        result=plans_from_moments(rows,self.profile,**kw)
        self.assertEqual(len(result['execution_equivalence']),2)
        self.assertTrue(any(set(v)>={'F19_C','S_CFG19','S_DIAG19','S_BR19'} for v in result['execution_equivalence'].values()))


if __name__=='__main__':unittest.main()
