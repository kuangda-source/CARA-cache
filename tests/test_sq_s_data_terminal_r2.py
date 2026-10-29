"""Independent S scalar/source/complete-witness controls, all explicit fixtures."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from test_sq_s_runner_r1 import fixture as matrix_fixture,REFUSALS
from wcomr.sq_s_physical_r1 import make_physical_scope
from wcomr import sq_s_data_terminal_r2 as terminal

ROOT=Path(__file__).resolve().parents[1]


def moments(C=1.,U=2.,K=.5,energy=3.):
    BR=(C+U)/2;diag=64*C+49*U;guided=diag-112*K
    return dict(C=C,U=U,K=K,BR=BR,DIAG=diag,CFG=guided,CFG_formula=guided,
        identity_abs_error=0.,identity_tolerance=128*terminal.EPS64*max(diag,abs(-112*K),1e-300),
        teacher_branch_energy=energy,normalization='MEAN_TEACHER_BRANCH_ENERGY',
        normalized=dict(BR=BR/energy,DIAG=diag/energy,CFG=guided/energy),coefficients=[8,-7],reduction_dtype='FP64')


def fixture():
    result,upper,physical,identity,contract=matrix_fixture()
    result['actual_CUDA']=False
    result['matrix'].update(scientific_labels_accepted=False)
    result['matrix']['physical_execution']['actual_GPU_or_scientific_acceptance']=False
    result['model_entry']=dict(status='S_MODEL_AND_MATRIX_COMPLETE_AWAITING_ORIGINAL_ALLOCATION_TERMINAL',
        CPU_fixture=True,execution_identity_sha256=identity,physical_scope_sha256=physical['physical_scope_sha256'],
        model_load_attempts=1,model_loads=1,environment_cleanup_attempted=True,environment_cleanup_accepted=True,
        precision=dict(conditional_frame_timestep=.1,use_wan_fp32_strategy=True,outer_autocast=False),
        actual_scientific_labels_accepted=False,original_GPU_release_accepted=False,original_financial_settlement_accepted=False)
    for record in result['matrix']['rows']:
        value=record['result'];slot=record['slot']
        value.update(diagnostic_only_no_clean_clock=True,
            encoded_video=dict(path='/CPU_FIXTURE/'+slot['id']+'/video.mp4',bytes=100,sha256='b'*64))
        for row in value['S_rows']:
            context=['CPU_SYNTHETIC',slot['prompt'],upper['policies'][slot['parent']]['fingerprint']]
            row.update(context=context,paid_prefix_equal=True,
                raw_state_selected=slot['parent']=='F19-C' and row['step'] in (9,22,33,35),moments=moments())
            row['source']['context']=context
            row['source'].update(parent=row['parent'],step=row['step'])
    return result,upper,physical,identity,contract


def accept(result,upper,physical,identity,contract,**kwargs):
    return terminal.check_result(result,upper,physical,identity_sha256=identity,resource_contract_sha256=contract,
        expected_shape=[1],CPU_fixture=True,**kwargs)


def first(result):return next(r['result']['S_rows'][0] for r in result['matrix']['rows'] if r['slot']['enabled'])


class DataTerminalTests(unittest.TestCase):
    def test_full108_scalar_rows_are_recomputed_without_claiming_artifacts_or_GPU_release(self):
        result,upper,physical,identity,contract=fixture();r=accept(result,upper,physical,identity,contract)
        self.assertEqual(r['FP64_moments_recomputed'],108)
        self.assertFalse(r['artifact_file_bytes_independently_accepted'])
        self.assertFalse(r['original_GPU_release_accepted']);self.assertFalse(r['scientific_S_effect_established'])

    def test_other_A6000_all_new_ten_path_binding_is_supported(self):
        result,upper,physical,identity,contract=fixture()
        physical=make_physical_scope(upper,'two_card',identity)
        result.update(host='two_card',physical_scope_sha256=physical['physical_scope_sha256'])
        result['matrix']['physical_execution']['scope']=physical
        result['model_entry']['physical_scope_sha256']=physical['physical_scope_sha256']
        self.assertEqual(accept(result,upper,physical,identity,contract)['new_paths'],10)

    def test_CPU_data_cannot_enter_default_real_acceptance(self):
        result,upper,physical,identity,contract=fixture()
        with self.assertRaises(ValueError):terminal.check_result(result,upper,physical,
            identity_sha256=identity,resource_contract_sha256=contract,expected_shape=[1])

    def test_near_cancellation_and_zero_CFG_are_not_rejected_by_relative_error(self):
        result,upper,physical,identity,contract=fixture()
        first(result)['moments']=moments(49.,64.,56.)
        self.assertEqual(accept(result,upper,physical,identity,contract)['same_state_rows'],108)

    def test_module_is_importable_with_Torch_forbidden(self):
        code="import sys;sys.path.insert(0,"+repr(str(ROOT/'src'))+");sys.modules['torch']=None;from wcomr import sq_s_data_terminal_r2;assert 'torch' not in sq_s_data_terminal_r2.__dict__"
        subprocess.run([sys.executable,'-c',code],check=True,capture_output=True,text=True)


MORE_REFUSALS=dict(
    fabricated_CUDA=lambda r:r.update(actual_CUDA=True),
    missing_model_cleanup=lambda r:r['model_entry'].update(environment_cleanup_accepted=False),
    repeated_model_load=lambda r:r['model_entry'].update(model_load_attempts=2,model_loads=2),
    unregistered_coefficients=lambda r:first(r)['moments'].update(coefficients=[7,-6]),
    changed_DIAG=lambda r:first(r)['moments'].update(DIAG=1.),
    changed_CFG=lambda r:first(r)['moments'].update(CFG=1.),
    inflated_cancellation_tolerance=lambda r:first(r)['moments'].update(identity_tolerance=100.),
    changed_normalization=lambda r:first(r)['moments']['normalized'].update(CFG=1.),
    zero_teacher_energy=lambda r:first(r)['moments'].update(teacher_branch_energy=0.),
    nonfinite_moment=lambda r:first(r)['moments'].update(C=float('nan')),
    wrong_FP64_reduction=lambda r:first(r)['moments'].update(reduction_dtype='FP32'),
    raw_scope_changed=lambda r:first(r).update(raw_state_selected=True),
    wrong_teacher_call=lambda r:first(r).update(extra_Dense_teacher_pairs=2),
    changed_context=lambda r:first(r)['source'].update(context=['FOREIGN']),
    foreign_policy_context=lambda r:(first(r)['context'].__setitem__(-1,'FOREIGN'),
        first(r)['source']['context'].__setitem__(-1,'FOREIGN')),
    foreign_source_parent=lambda r:first(r)['source'].update(parent='FOREIGN'),
    foreign_source_step=lambda r:first(r)['source'].update(step=35),
    missing_physical_parity=lambda r:r['matrix']['physical_execution']['OFF_ON_controls'].pop(),
    skipped_fresh_pixel_comparison=lambda r:r['matrix']['physical_execution']['OFF_ON_controls'][0].update(
        pre_encoding_RGB_compared=False,retained_OFF_has_no_pre_encoding_pixels=True),
    wrong_latent_shape=lambda r:r['matrix']['rows'][0]['result']['final_latent'].update(shape=[2]),
    unregistered_dtype=lambda r:r['matrix']['rows'][0]['result']['guided'][0].update(dtype='torch.float16'),
    missing_frame=lambda r:r['matrix']['rows'][0]['result']['RGB'].update(frames=92),
    scientific_matrix_claim=lambda r:r['matrix'].update(scientific_labels_accepted=True),
    clean_latency_claim=lambda r:r['matrix']['rows'][0]['result'].update(diagnostic_only_no_clean_clock=False))


def refusal(mutate):
    def test(self):
        result,upper,physical,identity,contract=fixture();mutate(result)
        with self.assertRaises(ValueError):accept(result,upper,physical,identity,contract)
    return test


for name,mutate in dict(REFUSALS,**MORE_REFUSALS).items():
    setattr(DataTerminalTests,'test_refuse_'+name,refusal(mutate))


class ScalarTests(unittest.TestCase):
    def test_independent_acceptance_of_actual_collector_FP64_reductions(self):
        import torch
        from wcomr.sq_risk_r1 import branch_moments
        generator=torch.Generator().manual_seed(129)
        for scale in (1e-12,1.,1e12):
            teacher=tuple(torch.randn(128,generator=generator)*scale for _ in range(2))
            candidate=tuple(x+torch.randn(128,generator=generator)*scale for x in teacher)
            terminal.check_moments(dict(moments=branch_moments(candidate,teacher)))

    def test_covariance_bound_is_independent_of_guided_identity(self):
        row=dict(moments=moments(1.,1.,-2.))
        with self.assertRaisesRegex(ValueError,'covariance'):terminal.check_moments(row)

    def test_exact_normalization_uses_no_epsilon(self):
        row=dict(moments=moments(0.,0.,0.,1e-200));terminal.check_moments(row)

    def test_encoded_artifact_cannot_escape_original_role(self):
        result,upper,physical,identity,contract=fixture()
        with self.assertRaisesRegex(ValueError,'escaped'):
            accept(result,upper,physical,identity,contract,new_output_root='/OTHER_ROOT')


if __name__=='__main__':unittest.main()
