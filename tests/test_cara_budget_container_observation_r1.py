"""Exact Docker absence responses; unknown errors never mean no allocation."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch
from wcomr import cara_budget_lifecycle_capture_r1 as reader

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from accept_cara_budget_allocation_cpu_r3 import accept
ORIGINAL='17cf1e348ec4f56d717c44ee5fd596b7054345a0'


class ContainerObservationTests(unittest.TestCase):
    name='cara-budget-observation-CPU-only'

    def test_three_exact_missing_responses(self):
        for prefix in ('Error: No such object: ','Error: No such container: ',
                       'Error response from daemon: No such container: '):
            result=subprocess.CompletedProcess([],1,'[]\n',prefix+self.name+'\n')
            with self.subTest(prefix=prefix),patch.object(reader.subprocess,'run',return_value=result) as command:
                self.assertIsNone(reader.inspect_container(self.name))
                self.assertEqual(command.call_args.args[0],['docker','inspect','--type','container',self.name])
                self.assertEqual(command.call_args.kwargs['timeout'],20)

    def test_wrong_name_permission_daemon_and_nonstandard_exit_remain_unknown(self):
        cases=[(1,'Error response from daemon: No such container: other'),(1,'permission denied'),
               (1,'Cannot connect to the Docker daemon'),(1,'Error: No such container: '+self.name+'\nadditional error'),
               (125,'Error: No such container: '+self.name)]
        for code,message in cases:
            with self.subTest(message=message),patch.object(reader.subprocess,'run',return_value=subprocess.CompletedProcess([],code,'',message)):
                with self.assertRaises(RuntimeError):reader.inspect_container(self.name)

    def test_timeout_is_not_missing(self):
        with patch.object(reader.subprocess,'run',side_effect=subprocess.TimeoutExpired('docker',20)):
            with self.assertRaises(subprocess.TimeoutExpired):reader.inspect_container(self.name)

    def test_original_normalized_container_shape_unchanged(self):
        raw=dict(Id='c'*64,Name='/'+self.name,Image='sha256:'+'e'*64,
            HostConfig=dict(DeviceRequests=[dict(DeviceIDs=['GPU-CPU-FIXTURE'])]),
            Config=dict(Labels={'wcomr.manifest':'a'*64}),State=dict(Status='exited',Running=False,Pid=0,ExitCode=0))
        with patch.object(reader.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps([raw]),'')):
            result=reader.inspect_container(self.name)
        self.assertEqual(result,dict(id=raw['Id'],name=self.name,image=raw['Image'],manifest_sha256='a'*64,
            device_ids=['GPU-CPU-FIXTURE'],state=raw['State']))
        for request in (None,[],[{},{}]):
            changed=copy.deepcopy(raw);changed['HostConfig']['DeviceRequests']=request
            with patch.object(reader.subprocess,'run',return_value=subprocess.CompletedProcess([],0,json.dumps([changed]),'')):
                with self.assertRaises(ValueError):reader.inspect_container(self.name)

    def test_original_allocation_CPU_revalidation_pins_published_source(self):
        path=ROOT/'reports/cara_budget_allocation_four_card_CPU_capture_r3_20261030.json'
        accepted=accept(path,source_revision=ORIGINAL)
        self.assertEqual(accepted['verified_source_revision'],ORIGINAL)
        self.assertEqual(accepted['tests_run'],13)
        self.assertFalse(accepted['actual_GPU_lifecycle_accepted'])
        with self.assertRaises(ValueError):accept(path)
        for moving in ('HEAD','main',ORIGINAL[:8]):
            with self.assertRaises(ValueError):accept(path,source_revision=moving)


if __name__=='__main__':unittest.main()
