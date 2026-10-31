"""Production entry control flow with explicit model/CUDA substitutes only."""
import contextlib
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType,SimpleNamespace
import unittest
from unittest.mock import Mock,patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]
import run_cara_s_endpoint_r1 as entry
import run_cara_budget_calibration_r1 as handoff
from wcomr import cara_s_endpoint_runner_r1 as loaded
from wcomr import history104_storage_r2 as storage_module
from wcomr import wc73_exclusive_r1 as exclusive
from wcomr import runtime_config
from wcomr.cara_s_endpoint_runner_binding_r1 import RUNNER
from test_cara_s_endpoint_runner_binding_r1 import Fixture


class EntryControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f=Fixture(self.temp.name);self.output=self.f.project/'outputs'/self.f.auth['run_id'];self.output.mkdir()
        self.storage=SimpleNamespace(output=self.output,config=dict(self.f.profile['storage']),check=Mock())
        self.storage.config.update(image_bytes=self.storage.config['output_image_bytes'],journal_bytes=self.storage.config['independent_journal_bytes'])
        self.lease=self.f.project/'.sync/gpu-locks'/(self.f.auth['gpu_uuid']+'.lock');self.lease.parent.mkdir();self.lease.touch()
        self.identity=dict(CPU_metadata_identity=True)
        self.inference=SimpleNamespace(pipe=SimpleNamespace(model=SimpleNamespace(net=SimpleNamespace(blocks=[None]*28))))
        self.collect=Mock(return_value=({'rows':[{}]*32},{'CPU_entry_substitute':True}))
        self.load=Mock(return_value=self.inference);self.initialize=Mock();self.cleanup=Mock();self.context=Mock(return_value=object())
        self.modules={}
        def module(name,**values):
            value=ModuleType(name);value.__path__=[];vars(value).update(values);self.modules[name]=value
            if '.' in name:
                parent,child=name.rsplit('.',1);setattr(self.modules[parent],child,value)
            return value
        class Setup(SimpleNamespace):
            def __init__(self,**values):
                super().__init__(**{'experiment':None,'disable_guardrails':False,'use_torch_compile':False,'offload_diffusion_model':False,**values})
        module('torch',__version__='2.7.1+cu128',set_num_threads=Mock(),
               cuda=SimpleNamespace(synchronize=Mock(),get_device_capability=Mock(return_value=(8,6))))
        module('cosmos_predict2');module('cosmos_predict2.config',SetupArguments=Setup,InferenceArguments=SimpleNamespace)
        module('cosmos_predict2.inference',Inference=self.load)
        for name in ('cosmos_predict2._src','cosmos_predict2._src.predict2','cosmos_predict2._src.predict2.inference',
                     'cosmos_predict2._src.predict2.inference.worldcache_utils','cosmos_predict2._src.predict2.models',
                     'cosmos_predict2._src.predict2.models.video2world_model_rectified_flow'):module(name)
        module('cosmos_oss');module('cosmos_oss.init',init_environment=self.initialize,init_output_dir=Mock(),cleanup_environment=self.cleanup)

    def run_entry(self):
        argv=['entry','--project',str(self.f.project),'--stage',str(self.f.stage),
              '--source-revision',self.f.auth['source_revision'],'--gpu-uuid',self.f.auth['gpu_uuid']]
        original_resolve=Path.resolve
        def resolve(path,*args,**kwargs):
            if str(path)=='/proc/self/fd/999':return original_resolve(self.lease)
            return original_resolve(path,*args,**kwargs)
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules,self.modules))
            stack.enter_context(patch.object(sys,'argv',argv))
            stack.enter_context(patch.dict(os.environ,CUDA_VISIBLE_DEVICES=self.f.auth['gpu_uuid'],
                                            WC_SUPERVISOR_PID=str(os.getppid()),WC_LOCK_FD='999'))
            stack.enter_context(patch.object(Path,'resolve',resolve))
            stack.enter_context(patch.object(storage_module,'storage_for',return_value=self.storage))
            stack.enter_context(patch.object(handoff,'validate_runner_handoff',return_value=self.identity))
            stack.enter_context(patch.object(exclusive,'runner_context_gate',self.context))
            stack.enter_context(patch.object(runtime_config,'install_core_inference_registration'))
            stack.enter_context(patch.object(loaded,'collect_loaded',self.collect))
            entry.main()

    def state(self):return json.loads((self.output/'endpoint-model-runner.json').read_text())

    def test_complete_entry_uses_bound_full_scope(self):
        self.run_entry();state=self.state()
        self.assertEqual(state['status'],'COMPLETE_ENDPOINT_COLLECTION_PENDING_RELEASE');self.assertEqual(state['complete_paths'],32)
        self.assertFalse(state['scientific_accepted']);self.cleanup.assert_called_once();self.collect.assert_called_once()
        args=self.collect.call_args.args
        self.assertIs(args[0],self.inference);self.assertEqual(args[2],self.f.card);self.assertEqual(args[3],self.f.bound)
        self.assertEqual(args[6:8],('two_card',self.output));self.assertEqual(args[8]['physical_paths'],32)
        self.assertEqual(state['identity'],self.identity);self.assertGreaterEqual(state['ended_unix'],state['started_unix'])

    def test_second_call_refuses_before_model_load(self):
        self.run_entry()
        with self.assertRaises(FileExistsError):self.run_entry()
        self.load.assert_called_once();self.collect.assert_called_once();self.cleanup.assert_called_once()

    def test_load_failure_retains_terminal(self):
        self.load.side_effect=RuntimeError('CPU injected load failure')
        with self.assertRaisesRegex(RuntimeError,'load failure'):self.run_entry()
        self.assertEqual(self.state()['status'],'ENDPOINT_MODEL_RUNNER_FAILED');self.cleanup.assert_called_once();self.collect.assert_not_called()

    def test_collection_failure_retains_terminal(self):
        self.collect.side_effect=RuntimeError('CPU injected collection failure')
        with self.assertRaisesRegex(RuntimeError,'collection failure'):self.run_entry()
        self.assertEqual(self.state()['status'],'ENDPOINT_MODEL_RUNNER_FAILED');self.cleanup.assert_called_once()

    def test_cleanup_failure_not_success(self):
        self.cleanup.side_effect=RuntimeError('CPU injected cleanup failure')
        with self.assertRaisesRegex(RuntimeError,'cleanup failure'):self.run_entry()
        self.assertEqual(self.state()['status'],'ENDPOINT_MODEL_CLEANUP_FAILED');self.assertIn('ended_unix',self.state())

    def test_wrong_runtime_refuses_sampling(self):
        self.modules['torch'].__version__='wrong'
        with self.assertRaisesRegex(ValueError,'Pinned endpoint runtime'):self.run_entry()
        self.collect.assert_not_called();self.cleanup.assert_called_once()

    def test_wrong_device_refuses_sampling(self):
        self.modules['torch'].cuda.get_device_capability.return_value=(8,9)
        with self.assertRaisesRegex(ValueError,'Pinned endpoint runtime'):self.run_entry()
        self.collect.assert_not_called();self.cleanup.assert_called_once()

    def test_storage_failure_precedes_context(self):
        self.storage.check.side_effect=OSError('CPU storage low-water')
        with self.assertRaisesRegex(OSError,'low-water'):self.run_entry()
        self.context.assert_not_called();self.load.assert_not_called()

    def test_context_failure_precedes_model(self):
        self.context.side_effect=ValueError('CPU context refused')
        with self.assertRaisesRegex(ValueError,'context refused'):self.run_entry()
        self.load.assert_not_called();self.assertTrue((self.output/'endpoint-model-runner-intent.json').exists())

    def test_environment_failure_retains_terminal(self):
        self.initialize.side_effect=RuntimeError('CPU environment failure')
        with self.assertRaisesRegex(RuntimeError,'environment failure'):self.run_entry()
        self.assertEqual(self.state()['status'],'ENDPOINT_MODEL_RUNNER_FAILED');self.assertIn('ended_unix',self.state())
        self.load.assert_not_called();self.cleanup.assert_called_once()


if __name__=='__main__':unittest.main()
