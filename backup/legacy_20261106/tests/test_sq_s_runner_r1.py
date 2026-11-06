"""S runner failure sequencing and independent complete-cohort refusal controls."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.sq_s_batch_r1 import make_scope
from wcomr.sq_s_physical_r1 import make_physical_scope
from wcomr.sq_s_sources_r1 import PARENTS
from wcomr import sq_s_runner_r1 as runner

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    raw=json.loads((ROOT/'plans/cara_next_stage_20261028/sq/S_SUPPORT_RECONCILIATION_R2.json').read_text())['profile']
    for key in ('protected_dense','alpha_candidates'):raw[key]=tuple(raw[key])
    upper=make_scope(Profile(**raw),cpu_fixture=True)
    identity,contract='a'*64,'c'*64
    physical=make_physical_scope(upper,'four_card',identity)
    controls=[dict(prompt=p,parent=h,exact=True,pre_encoding_RGB_compared=True,
        retained_OFF_has_no_pre_encoding_pixels=False) for p in upper['prompts'] for h in PARENTS]
    rows=[]
    for slot in upper['slots']:
        moments=[]
        for step in (range(8,36) if slot['enabled'] else []):
            if step==24:continue
            moments.append(dict(prompt=slot['prompt'],parent=slot['parent'],step=step,
                parent_roundtrip_equal=True,teacher_writes_parent=False,
                source=dict(source_captured_before_parent_pair=True,current_D_in_source=False,
                    source_anchor_steps=list(t for t in PARENTS[slot['parent']] if t<step)[-2:]),
                extra_Dense_teacher_pairs=int(step not in PARENTS[slot['parent']]),
                extra_C_readout_pairs=int(step in PARENTS[slot['parent']]),extra_Dense_hidden_replay_heads=0))
        policy=upper['policies'][slot['parent']]
        value=dict(status='COMPLETE',CPU_fixture=True,solver_steps=36,
            guided=[dict(dtype='torch.float32',shape=[1],sha256='b'*64) for _ in range(36)],
            final_latent=dict(dtype='torch.float32',shape=[1],sha256='b'*64),
            RGB=dict(frames=93,sha256='b'*64),pre_encoding_RGB=dict(frames=93,sha256='b'*64),
            policy_fingerprint=policy['fingerprint'],semantic_actions=list(policy['actions']),S_rows=moments)
        rows.append(dict(slot=copy.deepcopy(slot),status='COMPLETE',result=value))
    matrix=dict(status='COMPLETE_DATA_ONLY_AWAITING_TERMINAL_ACCEPTANCE',scope_sha256=upper['scope_sha256'],
        counts=upper['counts'],rows=rows,OFF_ON_controls=[{k:r[k] for k in ('prompt','parent','exact')} for r in controls],
        physical_execution=dict(scope=physical,actual_new_paths=10,actual_imported_OFF=0,OFF_ON_controls=controls),
        storage=dict(measured_rows=108,raw_states=8,unique_anchor_files=24))
    result=dict(status='S_COMPLETE_MATRIX_AWAITING_MODEL_CLEANUP_AND_ALLOCATION_TERMINAL',
        CPU_fixture=True,host='four_card',matrix=matrix,upper_scope_sha256=upper['scope_sha256'],
        physical_scope_sha256=physical['physical_scope_sha256'],execution_identity_sha256=identity,
        resource_contract_sha256=contract,resource_checks=[dict(slot_id=s['id'],step=t,contract_sha256=contract,
            all_eight_groups_checked=True,tensor_values_read=False,tensor_copies_performed=0)
            for s in upper['slots'] if s['enabled'] for t in range(8,36) if t!=24],
        attempted_new_role_ids=[s['id'] for s in physical['physical_slots']],
        original_state_restored=True,parameters_and_precision_unchanged=True,
        actual_scientific_labels_accepted=False,GPU_released=False,central_cost_settled=False)
    return result,upper,physical,identity,contract


class CompleteCohortTests(unittest.TestCase):
    def test_full_fixture_is_data_only_and_never_GPU_release(self):
        result,upper,physical,identity,contract=fixture()
        accepted=runner.check_complete_matrix(result,upper,physical,identity,contract,CPU_fixture=True)
        self.assertEqual(accepted['complete_same_state_rows'],108)
        self.assertFalse(accepted['original_GPU_release_accepted'])
        self.assertFalse(accepted['original_financial_settlement_accepted'])

    def test_CPU_fixture_cannot_be_used_by_the_production_default(self):
        with self.assertRaises(ValueError):runner.check_complete_matrix(*fixture())


def on(result):return next(r['result'] for r in result['matrix']['rows'] if r['slot']['enabled'])


REFUSALS=dict(
    live_matrix=lambda r:r.update(status='RUNNING'),
    wrong_host=lambda r:r.update(host='two_card'),
    missing_role=lambda r:r['matrix']['rows'].pop(),
    changed_role_order=lambda r:r['matrix']['rows'].reverse(),
    missing_moment=lambda r:on(r)['S_rows'].pop(),
    current_D_in_source=lambda r:on(r)['S_rows'][0]['source'].update(current_D_in_source=True),
    teacher_writes_parent=lambda r:on(r)['S_rows'][0].update(teacher_writes_parent=True),
    foreign_anchor=lambda r:on(r)['S_rows'][0]['source'].update(source_anchor_steps=[1,35]),
    altered_guided_witness=lambda r:on(r)['guided'][0].update(sha256='d'*64),
    altered_pre_encoding_pixels=lambda r:on(r)['pre_encoding_RGB'].update(sha256='d'*64),
    missing_guard=lambda r:r['resource_checks'].pop(),
    guard_copied_before_refusal=lambda r:r['resource_checks'][0].update(tensor_copies_performed=1),
    missing_raw=lambda r:r['matrix']['storage'].update(raw_states=7),
    missing_anchor=lambda r:r['matrix']['storage'].update(unique_anchor_files=23),
    stale_contract=lambda r:r.update(resource_contract_sha256='d'*64),
    final_reset_failed=lambda r:r.update(original_state_restored=False),
    changed_parameters=lambda r:r.update(parameters_and_precision_unchanged=False),
    premature_scientific_acceptance=lambda r:r.update(actual_scientific_labels_accepted=True),
    premature_GPU_release=lambda r:r.update(GPU_released=True),
    premature_financial_settlement=lambda r:r.update(central_cost_settled=True))


def refusal_test(mutate):
    def test(self):
        result,upper,physical,identity,contract=fixture();mutate(result)
        with self.assertRaises(ValueError):
            runner.check_complete_matrix(result,upper,physical,identity,contract,CPU_fixture=True)
    return test


for name,mutate in REFUSALS.items():setattr(CompleteCohortTests,'test_refuse_'+name,refusal_test(mutate))


class FailureSequencingTests(unittest.TestCase):
    def exercise(self,callback_failure=False,restore_failure=False,constructor_failure=False):
        result,upper,physical,identity,contract=fixture()
        parameter=torch.nn.Parameter(torch.ones(1));net=SimpleNamespace(named_parameters=lambda:[('p',parameter)])
        inference=SimpleNamespace(pipe=SimpleNamespace(model=SimpleNamespace(net=net)))
        state=dict(value='original',restores=0,verify=0);health=[];store=SimpleNamespace()
        def restore():
            state['restores']+=1
            if restore_failure and state['restores']==2:raise ValueError('Controlled final restore failure')
            state['value']='original'
        initial=SimpleNamespace(fingerprint=lambda:state['value'],restore=restore)
        def before(slot):
            if callback_failure:raise OSError('Controlled storage boundary')
        def verify():state['verify']+=1
        def collect(adapter,output,*,before_request,storage,save):
            state['value']='dirty';before_request(upper['slots'][0])
            self.assertEqual(state['value'],'original')
            state['value']='dirty after forward';raise RuntimeError('Controlled sampler failure')
        base=SimpleNamespace();adapter=SimpleNamespace()
        with tempfile.TemporaryDirectory() as directory:
            kwargs=dict(request_kwargs=dict(scope=upper,inference=inference,sink=store),physical_scope=physical,
                execution_identity_sha256=identity,resource_contract=dict(contract_sha256=contract),store=store,
                output=Path(directory)/'never-created',initial=initial,before_request=before,verify_mode=verify,
                save_matrix=lambda value:None,save_health=lambda value:health.append(copy.deepcopy(value)))
            error=ValueError if restore_failure or constructor_failure else OSError if callback_failure else RuntimeError
            with patch.object(runner,'ResourceCheckedRequests',return_value=base,
                    side_effect=ValueError('Controlled source binding refusal') if constructor_failure else None),\
                    patch.object(runner,'PhysicalRequests',return_value=adapter),patch.object(runner,'collect',collect):
                with self.assertRaises(error):runner.run_matrix(**kwargs)
                self.assertEqual(health[-1]['attempted_new_role_ids'],[] if constructor_failure else [upper['slots'][0]['id']])
                self.assertEqual(health[-1]['status'],'S_MATRIX_FAILED_RETAINED_NO_RETRY')
                with self.assertRaisesRegex(ValueError,'recover without retry'):runner.run_matrix(**kwargs)
        return state,health

    def test_sampler_failure_restores_original_state_and_cannot_retry(self):
        state,health=self.exercise();self.assertEqual(state['value'],'original')
        self.assertTrue(health[-1]['original_state_restored']);self.assertEqual(state['verify'],2)

    def test_storage_failure_before_first_forward_is_retained_and_restored(self):
        state,health=self.exercise(callback_failure=True)
        self.assertEqual(health[-1]['error_type'],'OSError');self.assertEqual(state['value'],'original')

    def test_failed_final_restore_keeps_both_original_and_restoration_failures(self):
        state,health=self.exercise(restore_failure=True)
        self.assertEqual(health[-1]['error_type'],'RuntimeError')
        self.assertEqual(health[-1]['restoration_error_type'],'ValueError')
        self.assertFalse(health[-1]['original_state_restored'])

    def test_source_binding_refusal_before_any_role_is_retained_and_restored(self):
        state,health=self.exercise(constructor_failure=True)
        self.assertEqual(health[-1]['error_type'],'ValueError')
        self.assertEqual(state['value'],'original');self.assertEqual(state['restores'],1)


if __name__=='__main__':unittest.main()
