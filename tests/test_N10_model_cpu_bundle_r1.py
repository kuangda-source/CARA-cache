"""Synthetic whole-bundle receipts test attribution, not real model inference."""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('synthetic_metric_bundle_only',
    ROOT/'scripts/evaluate_wc_N10_models_cpu_bundle_r1.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


def fixture():
    root='/SYNTHETIC_NOT_SERVER';reg=dict(source_revision='SYNTHETIC_NO_MODEL_EXECUTION',
        stage=root,roles=list(M.ROLES),payload_sha256={'upstream/vbench/__init__.py':'a'*64})
    resources={role:dict(path='/SYNTHETIC_RESOURCE/'+role+'.pth',bytes=value[0],sha256=value[1])
               for role,value in M.WEIGHTS.items()}
    values={}
    for role in M.ROLES:
        source=(root+'/external/dino/vision_transformer.py' if role=='DINO' else
                root+'/upstream/vbench/'+role+'.py')
        if role=='MUSIQ_SPAQ':source='/SYNTHETIC_SITE/pyiqa/archs/musiq_arch.py'
        digest=M.MUSIQ_SOURCE_SHA if role=='MUSIQ_SPAQ' else 'b'*64
        if role!='MUSIQ_SPAQ':reg['payload_sha256'][str(Path(source).relative_to(root))]=digest
        outputs={k:dict(device='cpu',dtype='torch.float32',finite=True,requires_grad=False,
            sha256='c'*64,shape=shape if shape is not None else [1,1]) for k,shape in M.OUTPUTS[role].items()}
        actual=dict(role=role,model_class=M.CLASSES[role],parameter_count=123,
            model_source=source,model_source_sha256=digest,actual_model_input_shape=M.INPUTS[role],
            model_eval=True,all_parameters_CPU_FP32=True,outputs=outputs,
            flow_iterations=20,interpolation_iterations=1,scale_factor=1.,text_context_length=32,
            real_tokenizer_vocab_size=49408)
        values[role]=dict(status='N10_METRIC_MODEL_REAL_CPU_SYNTHETIC_INPUT_PASS_NOT_VIDEO_SCORE',
            exit_code=0,role=role,source_revision=reg['source_revision'],registration_sha256='d'*64,
            complete_registered_model_roles=list(M.ROLES),resource_sha256=M.WEIGHTS[role][1],
            resource_path=resources[role]['path'],checkpoint_SHA_verified_before_import=True,
            CUDA_initialized=False,forbidden_events=[],synthetic_inputs_only=True,
            paper_quality_scores_generated=False,final_videos_read=False,GPU_submissions=0,
            server_ledger_written=False,real_checkpoint_loads=[dict(path=resources[role]['path'],map_location='cpu')],
            actual_state_dict_loads=[dict(state_keys=1,missing_keys=[],unexpected_keys=[])],actual=actual,
            dependency_versions={'pyiqa':'0.1.10'},wall_seconds=.01,
            imported_pinned_modules=[dict(path=root+'/upstream/vbench/__init__.py',sha256='a'*64)])
    return reg,resources,values


class WholeMetricModelCPUControls(unittest.TestCase):
    def test_all_five_ordered_roles_and_zero_quality_claim(self):
        reg,resources,values=fixture();calls=[]
        def callback(role):
            calls.append(role);return dict(exit_code=0,data=copy.deepcopy(values[role]))
        result=M.drive(reg,'d'*64,resources,callback)
        self.assertEqual(calls,list(M.ROLES));self.assertEqual(result['status'],M.PASS)
        self.assertEqual(result['role_denominator'],5);self.assertEqual(result['accepted_roles'],5)
        self.assertFalse(result['paper_quality_scores_generated'])

    def test_failed_or_missing_middle_role_keeps_all_five_attempts(self):
        for failure in ('exit','missing','exception'):
            reg,resources,values=fixture();calls=[]
            def callback(role):
                calls.append(role)
                if role=='RAFT_THINGS':
                    if failure=='exception':raise ValueError('SYNTHETIC_ORIGINAL_PROCESS_FAILURE')
                    if failure=='missing':return dict(exit_code=0)
                    return dict(exit_code=1,data={'original_error':'RETAIN'})
                return dict(exit_code=0,data=copy.deepcopy(values[role]))
            result=M.drive(reg,'d'*64,resources,callback)
            self.assertEqual(calls,list(M.ROLES));self.assertEqual(result['accepted_roles'],4)
            self.assertEqual(len(result['rows']),5);self.assertEqual(result['exit_code'],1)

    def test_shrunk_cpu_scope_rejected_without_callbacks(self):
        reg,resources,_=fixture();reg['roles'].pop()
        with self.assertRaises(ValueError):M.drive(reg,'d'*64,resources,lambda role:self.fail('No reduced CPU'))

    def test_wrong_source_cuda_resource_or_state_load_is_not_accepted(self):
        for case in ('source','cuda','weight','path','state','installed_vbench'):
            reg,resources,values=fixture();v=values['DINO']
            if case=='source':v['source_revision']='SYNTHETIC_OTHER'
            elif case=='cuda':v['CUDA_initialized']=True
            elif case=='weight':v['resource_sha256']='0'*64
            elif case=='path':v['real_checkpoint_loads'][0]['path']='/SYNTHETIC_OTHER/weight.pth'
            elif case=='state':v['actual_state_dict_loads'][0]['missing_keys']=['SYNTHETIC_WEIGHT']
            else:v['imported_pinned_modules'][0]['path']='/SYNTHETIC_INSTALLED/vbench/__init__.py'
            with self.subTest(case=case),self.assertRaises(ValueError):M.accept_role('DINO',v,reg,'d'*64,resources)

    def test_shape_nonfinite_precision_gradient_and_missing_model_are_failures(self):
        for case in ('shape','finite','dtype','grad','role'):
            reg,resources,values=fixture();v=values['ViCLIP'];t=v['actual']['outputs']['text_features']
            if case=='shape':t['shape']=[1,512]
            elif case=='finite':t['finite']=False
            elif case=='dtype':t['dtype']='torch.float16'
            elif case=='grad':t['requires_grad']=True
            else:resources.pop('RAFT_THINGS')
            with self.subTest(case=case),self.assertRaises(ValueError):M.accept_role('ViCLIP',v,reg,'d'*64,resources)


if __name__=='__main__':unittest.main()
