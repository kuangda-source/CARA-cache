"""CPU loader/environment stand-ins; no weights, CUDA or scientific S labels."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from wcomr.h0_mode import mode_snapshot
from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.sq_s_batch_r1 import digest,make_scope
from wcomr.sq_s_physical_r1 import make_physical_scope
from wcomr import sq_s_model_entry_r1 as entry

ROOT=Path(__file__).resolve().parents[1]


class Tiny(torch.nn.Module):
    def __init__(self):
        super().__init__();self.blocks=torch.nn.ModuleList([torch.nn.Linear(2,2,bias=False)])
        self.use_wan_fp32_strategy=True


def fixture():
    base=ROOT/'plans/cara_next_stage_20261028/sq'
    identity=json.loads((base/'S_EXECUTION_IDENTITY_R1.json').read_text())
    identity['expected_real_shape']=[1,8,2,8,8]
    identity['identity_sha256']=digest({k:v for k,v in identity.items() if k!='identity_sha256'})
    raw=json.loads((base/'S_SUPPORT_RECONCILIATION_R2.json').read_text())['profile']
    for name in ('protected_dense','alpha_candidates'):raw[name]=tuple(raw[name])
    profile=Profile(**raw);upper=make_scope(profile,cpu_fixture=True)
    physical=make_physical_scope(upper,'four_card',identity['identity_sha256'])
    contract=json.loads((base/'S_RESOURCE_GUARD_CPU_CONTRACT_R1.json').read_text())
    net=Tiny();model=SimpleNamespace(net=net,precision=torch.float32,
        config=SimpleNamespace(conditional_frame_timestep=.1),sample_scheduler=SimpleNamespace(timesteps=torch.arange(3)))
    inference=SimpleNamespace(pipe=SimpleNamespace(model=model));events=[];health=[];matrix=[];results=[]
    def record(name,*args,**kwargs):events.append(name)
    def setup(**kwargs):
        record('setup');return SimpleNamespace(**dict(kwargs,output_dir=Path(kwargs['output_dir']),experiment=None))
    def arguments(**kwargs):record('request');return SimpleNamespace(**kwargs)
    def load(setup):record('load');return inference
    api=SimpleNamespace(config=SimpleNamespace(SetupArguments=setup,InferenceArguments=arguments),
        inference=SimpleNamespace(Inference=load),
        initialize=SimpleNamespace(init_environment=lambda:record('init'),
            init_output_dir=lambda *a,**k:record('output'),cleanup_environment=lambda:record('cleanup')),
        install_registration=lambda *a:record('register'),
        wc=SimpleNamespace(apply_worldcache=lambda *a,**k:record('worldcache')),rf=SimpleNamespace())
    bundle=dict(identity=identity,upper=upper,physical=physical,profile=profile,resource_contract=contract,
        mode_types=mode_snapshot(net)['module_types'],store_limits=dict(maximum_total_bytes=16*2**20,
            maximum_file_bytes=8*2**20,minimum_free_bytes=2**20),CPU_decode_fixture=lambda r:r)
    storage=SimpleNamespace(check=lambda:record('storage'))
    return bundle,storage,api,inference,events,health,matrix,results


class ModelEntryTests(unittest.TestCase):
    def run_entry(self,*,before=None,loader_error=False,matrix_error=False,cleanup_error=False,CPU_fixture=True,context_factory=None):
        bundle,storage,api,inference,events,health,matrix,results=fixture()
        if before:before(bundle,storage,api,inference)
        if loader_error:
            def fail(setup):events.append('load');raise OSError('Controlled loader failure')
            api.inference.Inference=fail
        if cleanup_error:
            def fail_cleanup():events.append('cleanup');raise RuntimeError('Controlled cleanup failure')
            api.initialize.cleanup_environment=fail_cleanup
        def collect(**kwargs):
            events.append('matrix')
            self.assertIs(kwargs['request_kwargs']['inference'],inference)
            self.assertFalse(any(m.training for m in inference.pipe.model.net.modules()))
            kwargs['before_request'](bundle['upper']['slots'][0]);kwargs['verify_mode']()
            if matrix_error:raise ValueError('Controlled matrix failure')
            return dict(status='S_COMPLETE_MATRIX_AWAITING_MODEL_CLEANUP_AND_ALLOCATION_TERMINAL',
                CPU_fixture=True,CPU_loader_and_matrix_standins=True)
        with tempfile.TemporaryDirectory() as directory,patch.object(entry,'run_matrix',side_effect=collect):
            output=Path(directory)
            kwargs=dict(bundle=bundle,runtime=ROOT/'cache/runtime',output=output,storage=storage,
                context=context_factory(bundle) if context_factory else {},runtime_api=api,save_health=lambda r:health.append(copy.deepcopy(r)),
                save_matrix=matrix.append,save_result=results.append,CPU_fixture=CPU_fixture)
            self.last=(bundle,storage,api,inference,events,health,matrix,results)
            try:return entry.execute(**kwargs),self.last
            finally:
                if getattr(storage,'_s_model_entry_consumed',False):
                    with self.assertRaisesRegex(ValueError,'recover without retry'):entry.execute(**kwargs)

    def test_one_original_load_and_cleanup_precede_result_publication(self):
        result,(_,_,_,_,events,health,_,results)=self.run_entry()
        self.assertEqual(events.count('load'),1);self.assertEqual(events.count('cleanup'),1)
        self.assertLess(events.index('register'),events.index('load'))
        self.assertLess(events.index('load'),events.index('worldcache'))
        self.assertLess(events.index('worldcache'),events.index('matrix'))
        self.assertEqual(results,[result]);model=result['model_entry']
        self.assertEqual(model['model_loads'],1);self.assertTrue(model['environment_cleanup_accepted'])
        self.assertFalse(model['original_GPU_release_accepted']);self.assertFalse(model['actual_scientific_labels_accepted'])
        self.assertFalse(torch.cuda.is_initialized())

    def test_original_path_typed_setup_parser_is_supported(self):
        result,_=self.run_entry();self.assertTrue(result['model_entry']['CPU_fixture'])

    def test_loader_failure_retains_original_attempt_and_cleans_once(self):
        with self.assertRaisesRegex(OSError,'loader failure'):self.run_entry(loader_error=True)
        *_,events,health,matrix,results=self.last
        self.assertEqual(events.count('load'),1);self.assertNotIn('matrix',events)
        self.assertEqual(events.count('cleanup'),1);self.assertEqual(health[-1]['model_loads'],0)
        self.assertEqual(health[-1]['model_load_attempts'],1);self.assertFalse(results)

    def test_matrix_failure_cleans_model_without_publishing_complete_result(self):
        with self.assertRaisesRegex(ValueError,'matrix failure'):self.run_entry(matrix_error=True)
        *_,events,health,matrix,results=self.last
        self.assertEqual(events.count('cleanup'),1);self.assertFalse(results)
        self.assertEqual(health[-1]['error_type'],'ValueError')

    def test_cleanup_failure_cannot_publish_complete_result(self):
        with self.assertRaisesRegex(RuntimeError,'cleanup failure'):self.run_entry(cleanup_error=True)
        *_,events,health,matrix,results=self.last
        self.assertFalse(results);self.assertFalse(health[-1]['environment_cleanup_accepted'])

    def test_cleanup_failure_retains_original_loader_failure_too(self):
        with self.assertRaisesRegex(RuntimeError,'cleanup failure'):self.run_entry(loader_error=True,cleanup_error=True)
        *_,events,health,matrix,results=self.last
        self.assertEqual(health[-1]['error_type'],'OSError')
        self.assertEqual(health[-1]['cleanup_error_type'],'RuntimeError');self.assertFalse(results)

    def test_CPU_fixture_cannot_enter_the_production_default(self):
        with self.assertRaisesRegex(ValueError,'CPU/real'):self.run_entry(CPU_fixture=False)
        *_,events,health,matrix,results=self.last
        self.assertNotIn('load',events)

    def test_guardrail_disable_refused_before_environment_or_load(self):
        def mutate(b,*args):
            b['identity']['model_setup']['disable_guardrails']=True
            b['identity']['identity_sha256']=digest({k:v for k,v in b['identity'].items() if k!='identity_sha256'})
            b['physical']=make_physical_scope(b['upper'],'four_card',b['identity']['identity_sha256'])
        with self.assertRaisesRegex(ValueError,'Original guarded'):self.run_entry(before=mutate)
        *_,events,health,matrix,results=self.last
        self.assertNotIn('init',events);self.assertNotIn('load',events)

    def test_setup_parser_cannot_change_original_flow_scale(self):
        def mutate(b,s,api,i):
            original=api.config.SetupArguments
            def changed(**kwargs):
                value=original(**kwargs);value.worldcache_flow_scale=3.;return value
            api.config.SetupArguments=changed
        with self.assertRaisesRegex(ValueError,'setup parser'):self.run_entry(before=mutate)

    def test_input_parser_cannot_change_original_prompt(self):
        def mutate(b,s,api,i):
            original=api.config.InferenceArguments
            def changed(**kwargs):
                value=original(**kwargs);value.prompt='Changed CPU prompt';return value
            api.config.InferenceArguments=changed
        with self.assertRaisesRegex(ValueError,'request objects'):self.run_entry(before=mutate)

    def test_Wan_strategy_change_stops_before_matrix_and_cleans(self):
        def mutate(b,s,a,i):i.pipe.model.net.use_wan_fp32_strategy=False
        with self.assertRaisesRegex(ValueError,'Wan strategy'):self.run_entry(before=mutate)
        *_,events,health,matrix,results=self.last
        self.assertNotIn('matrix',events);self.assertEqual(events.count('cleanup'),1)

    def test_model_conditional_timestep_change_stops_before_matrix(self):
        def mutate(b,s,a,i):i.pipe.model.config.conditional_frame_timestep=.2
        with self.assertRaisesRegex(ValueError,'condition'):self.run_entry(before=mutate)

    @staticmethod
    def real_bundle(bundle,*args):
        base=ROOT/'plans/cara_next_stage_20261028/sq'
        bundle['identity']=json.loads((base/'S_EXECUTION_IDENTITY_R1.json').read_text())
        bundle['upper']=make_scope(bundle['profile'])
        bundle['resource_contract']=json.loads((base/'S_RESOURCE_GUARD_REAL_CONTRACT_R1.json').read_text())
        bundle['witness']=json.loads((base/'S_RETAINED_OFF_WITNESS_R1.json').read_text())
        bundle['physical']=make_physical_scope(bundle['upper'],'two_card',bundle['identity']['identity_sha256'],bundle['witness'])
        bundle['CPU_decode_fixture']=None

    @staticmethod
    def metadata_context(bundle):
        # Synthetic validation input only; no environment/model load is allowed
        # by these refusal tests and no authorization artifact is written.
        return dict(authorizes_S_collection=True,scope_sha256=bundle['upper']['scope_sha256'],
            physical_scope_sha256=bundle['physical']['physical_scope_sha256'],
            execution_identity_sha256=bundle['identity']['identity_sha256'],
            S_resource_contract_sha256=bundle['resource_contract']['contract_sha256'],host='two_card',
            source_revision='CPU_SYNTHETIC_NOT_EXECUTION_AUTHORITY',launch_id='CPU_ONLY',
            gpu_uuid='GPU-FOREIGN-CPU-VALIDATION',fresh_reuse_witness_sha256=bundle['witness']['witness_sha256'])

    def test_retained_OFF_cannot_load_on_a_foreign_GPU(self):
        with self.assertRaisesRegex(ValueError,'original OFF hardware'):
            self.run_entry(before=self.real_bundle,CPU_fixture=False,context_factory=self.metadata_context)
        *_,events,health,matrix,results=self.last
        self.assertNotIn('load',events);self.assertFalse(torch.cuda.is_initialized())

    def test_Q1_only_context_cannot_authorize_S_loading(self):
        def context(bundle):return dict(self.metadata_context(bundle),authorizes_S_collection=False)
        with self.assertRaisesRegex(ValueError,'S-only context'):
            self.run_entry(before=self.real_bundle,CPU_fixture=False,context_factory=context)
        *_,events,health,matrix,results=self.last
        self.assertNotIn('load',events)

    def test_real_loader_refuses_a_CPU_decode_adapter_before_loading(self):
        def bundle(value,*args):self.real_bundle(value);value['CPU_decode_fixture']=lambda r:r
        with self.assertRaisesRegex(ValueError,'CPU decode fixture'):
            self.run_entry(before=bundle,CPU_fixture=False,context_factory=self.metadata_context)


if __name__=='__main__':unittest.main()
