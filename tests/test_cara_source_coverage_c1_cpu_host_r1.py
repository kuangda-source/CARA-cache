"""CPU host capture identity and no-replay controls, using metadata only."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('c1_cpu_host',ROOT/'scripts/cara_source_coverage_c1_cpu_host_r1.py')
host=importlib.util.module_from_spec(spec)
spec.loader.exec_module(host)


class CPUHost(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.stage=Path(self.temp.name)
        raw=json.dumps(dict(payload_sha256={})).encode()
        (self.stage/'registration.json').write_bytes(raw)
        self.intent=dict(registration_sha256=host.sha(raw))
        (self.stage/'CPU-intent.json').write_text(json.dumps(self.intent))
        self.inspected=dict(Image=host.IMAGE,Name='/'+host.NAME,Id='a'*64,
            Config=dict(Labels={'cara.C1.registration':host.sha(raw)}),
            State=dict(Running=False,ExitCode=0,Pid=0),HostConfig=dict(DeviceRequests=None,
                Memory=8*2**30,MemorySwap=8*2**30,NanoCpus=2_000_000_000,
                CpusetCpus='26,27',NetworkMode='none',ReadonlyRootfs=True))
        self.addCleanup(patch.stopall)
        patch.object(host,'STAGE',self.stage).start()

    def test_terminal_original_proof_bytes_and_sha_are_retained(self):
        folder=self.stage/'linux-results-r1';folder.mkdir()
        raw=b'{"status":"CPU_FIXTURE_METADATA"}\n'
        (folder/'C1_CPU_PROOF_R1.json').write_bytes(raw)
        with patch.object(host,'inspect',return_value=self.inspected):
            observed=host.capture()
        self.assertEqual(observed['status'],'ORIGINAL_C1_CPU_TERMINAL')
        self.assertEqual(observed['proof_sha256'],host.sha(raw))
        self.assertEqual(observed['GPU_submissions'],0)

    def test_gpu_swap_and_changed_registration_are_rejected(self):
        for key,value in (('DeviceRequests',[{'Count':1}]),('MemorySwap',9*2**30)):
            data=copy.deepcopy(self.inspected);data['HostConfig'][key]=value
            with patch.object(host,'inspect',return_value=data),self.assertRaises(ValueError):
                host.capture()
        (self.stage/'registration.json').write_bytes(b'{}')
        with self.assertRaisesRegex(ValueError,'registration differs'):
            host.capture()

    def test_existing_intent_never_prepares_or_launches_a_second_cpu(self):
        with patch.object(host,'capture',return_value={'status':'ORIGINAL'}),patch.object(host,'download') as download:
            self.assertEqual(host.prepare('a'*40,'b'*64),{'status':'ORIGINAL'})
            download.assert_not_called()

    def test_r2_uses_original_interpreter_and_readonly_environment(self):
        python=str(host.ROOT/'envs/wc-cosmos-py310-cu128-r3/bin/python')
        self.intent['runtime_python']=python
        (self.stage/'CPU-intent.json').write_text(json.dumps(self.intent))
        self.inspected['Config'].update(Cmd=['timeout','300',python],
            Env=['CUDA_VISIBLE_DEVICES=','NVIDIA_VISIBLE_DEVICES=void'])
        self.inspected['HostConfig']['Binds']=[str(host.ROOT/p)+':'+str(host.ROOT/p)+':ro'
            for p in ('envs','system-libs-r1')]
        with patch.object(host,'GENERATION',2),patch.object(host,'inspect',return_value=self.inspected):
            self.assertEqual(host.capture()['status'],'ORIGINAL_C1_CPU_TERMINAL')
            self.inspected['HostConfig']['Binds'].pop()
            with self.assertRaisesRegex(ValueError,'runtime mounts'):
                host.capture()


if __name__=='__main__':
    unittest.main()
