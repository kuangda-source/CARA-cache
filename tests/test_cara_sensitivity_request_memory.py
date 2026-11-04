"""Small CPU lifecycle tests: no real model, video decoder, CUDA or GPU jobs."""
import gc
from pathlib import Path
from types import SimpleNamespace
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
import weakref

import torch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'plans/cara_next_stage_20261104/sensitivity'))
from runner import collect_loaded
from sampling import load_state,save_state
from wcomr.cpu_owned_state_snapshot import CPUOwnedStateImage


class RequestMemoryTest(unittest.TestCase):
    def checkpoint(self,directory):
        value=torch.arange(2**18,dtype=torch.float32)
        image=CPUOwnedStateImage(dict(value=value,view=value[1:]),
            logical_copy_cap_bytes=3*2**20,CPU_storage_cap_bytes=2**20)
        path=Path(directory)/'state.pt';save_state(path,image,8)
        return path

    def suspend_automatic_gc(self):
        gc.collect();gc.disable()
        self.addCleanup(gc.enable);self.addCleanup(gc.collect)

    def test_unpickler_retains_byte_stores_until_cyclic_collection(self):
        with tempfile.TemporaryDirectory(prefix='cara-memory-') as directory:
            path=self.checkpoint(directory);self.suspend_automatic_gc();refs=[]
            for _ in range(8):
                saved=torch.load(path,map_location='cpu',weights_only=False)
                refs.append(weakref.ref(next(iter(saved['stores'].values()))))
                restored=load_state(saved,device='cpu')
                del restored,saved
            self.assertEqual(sum(ref() is not None for ref in refs),8)
            gc.collect()
            self.assertTrue(all(ref() is None for ref in refs))

    def test_collection_releases_previous_checkpoint_before_next_request(self):
        with tempfile.TemporaryDirectory(prefix='cara-memory-') as directory:
            path=self.checkpoint(directory);self.suspend_automatic_gc();refs=[]
            def execute(*args,output,**kwargs):
                saved=torch.load(path,map_location='cpu',weights_only=False)
                refs.append(weakref.ref(next(iter(saved['stores'].values()))))
                restored=load_state(saved,device='cpu')
                # Same function -> globals -> function cycle as resume_sampler.
                scope=dict(saved=saved);exec('def sampler(): return saved',scope)
                output=Path(output);output.mkdir(parents=True)
                video=output/'declared_CPU_fixture.mp4';video.write_bytes(b'CPU fixture')
                return dict(status='COMPLETE',final_latent=restored['value'][:1].clone(),video_path=str(video))
            class Storage:
                def check(inner):
                    self.assertTrue(all(ref() is None for ref in refs),'Previous checkpoint still alive')
            model=SimpleNamespace(net=torch.nn.Linear(1,1),sample_scheduler=object())
            inference=SimpleNamespace(pipe=SimpleNamespace(model=model))
            card=dict(run_id='declared-CPU-fixture',scope_sha256='CPU-fixture',settings={},roles={},matrix=[dict(id=f'MEM_{i}',member='fixture',role='SINGLE_C',
                target_update=8,section='b') for i in range(8)])
            with patch('sampling.execute',side_effect=execute), \
                    patch('wcomr.full_sampling.CompleteStateRoundtrip',return_value=Mock()), \
                    patch('wcomr.h0_mode.establish_shared_eval'), \
                    patch('wcomr.h0_mode.verify_shared_eval'), \
                    patch('wcomr.cara_f19_speed190_requests_r1.Requests'), \
                    patch('wcomr.cara_s_endpoint_runner_r1.observed_precision',return_value={}):
                result=collect_loaded(inference,dict(fixture=object()),card,
                    dict(wc=SimpleNamespace(apply_worldcache=lambda *a,**k:None)),
                    Path(directory)/'output',Storage(),(),cpu_validation=True)
            self.assertEqual(result['status'],'COMPLETE_PENDING_RELEASE_SCORING')
            self.assertEqual(len(result['rows']),8)
            self.assertTrue(all(ref() is None for ref in refs))
            self.assertFalse(torch.cuda.is_initialized())


if __name__=='__main__':unittest.main()
