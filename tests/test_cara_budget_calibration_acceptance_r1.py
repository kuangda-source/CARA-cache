"""Synthetic terminal metadata mutations; these do not accept the live worker."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from accept_cara_budget_calibration_cpu_r1 import accept


class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'fixture.json'
        capture=json.loads((ROOT/'reports/cara_budget_calibration_four_card_CPU_operational_r1_20261030.json').read_text())
        capture['container_state'].update(Status='exited',Running=False,Pid=0,ExitCode=0,OOMKilled=False)
        rows=[]
        for flow in (False,True):
            rows.append(dict(validation='FULL112_CALIBRATION_PRODUCTION_ROUTES_CPU',flow=flow,
                complete_design_paths=112,complete_two_FIT_queries=51,SA_iterations=30,HC_iterations=1,HC_neighbors=20,
                successful_physical_paths=133,declared_failure_attempts=3,total_physical_attempts=136,
                complete93_frame_RGB=True,Native_allD_timing_RGB_and_CPU_RNG_equal=True,
                original_complete_recovery_without_generation=True,hooks_restored=True,
                Cosmos_model_weights_loaded=False,real_GPU_executed=False,whole_GPU_card_accepted=False,
                failures=[dict(kind=k,physical_attempts=n,no_replay=True) for k,n in (
                    ('first_writer',1),('second_FIT_refusal',12),('policy_fallback',11))]))
        reg=capture['registration']
        capture['CPU_proof']=dict(status='COMPLETE_CALIBRATION_ROUTES_CPU_NOT_GPU',host='four_card',
            registration_sha256=capture['registration_sha256'],payload_sha256=reg['payload_sha256'],
            runtime_source_sha256=reg['runtime_source_sha256'],CUDA_initialized=False,Cosmos_model_weights_loaded=False,
            GPU_submissions=0,ledger_written=False,whole_GPU_card_accepted=False,actual_compile_threads=1,compile_pools=[],
            spec_tests=3,calibration_lifecycle_tests=21,resource_bound=dict(cpus=1,memory_GiB=4,work_seconds=2400,exit_seconds=60),
            numeric=dict(checks=rows,cuda_initialized=False),CPU_process_seconds=1.,started_unix=1.,ended_unix=2.)
        self.original=capture

    def check(self,capture):
        capture['CPU_proof_sha256']=hashlib.sha256((json.dumps(capture['CPU_proof'],indent=2,allow_nan=False)+'\n').encode()).hexdigest()
        self.path.write_text(json.dumps(capture))
        return accept([self.path],source_revision='e31cc212836882e80f835bec0f0c9016a07b30af')

    def test_complete_fixture_has_no_dual_host_or_GPU_authority(self):
        result=self.check(self.original)
        self.assertEqual(result['complete_design_paths'],224)
        self.assertFalse(result['dual_host_accepted']);self.assertFalse(result['GPU_dispatch_ready'])

    def test_live_wrong_resource_or_partial_controls_refused(self):
        for change in ('live','swap','GPU','units','flow'):
            c=copy.deepcopy(self.original)
            if change=='live':c['container_state']['Running']=True
            elif change=='swap':c['host_config']['MemorySwap']=8*2**30
            elif change=='GPU':c['CPU_proof']['CUDA_initialized']=True
            elif change=='units':c['CPU_proof']['calibration_lifecycle_tests']=20
            else:c['CPU_proof']['numeric']['checks'].pop()
            with self.subTest(change=change),self.assertRaises(ValueError):self.check(c)

    def test_partial_query_or_control_matrix_and_replay_refused(self):
        for key,value in [('complete_design_paths',110),('complete_two_FIT_queries',50),
                ('HC_neighbors',19),('declared_failure_attempts',2),('original_complete_recovery_without_generation',False)]:
            c=copy.deepcopy(self.original);c['CPU_proof']['numeric']['checks'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(c)

    def test_wrong_original_stage_or_payload_refused(self):
        for change in ('stage','source'):
            c=copy.deepcopy(self.original)
            if change=='stage':c['launch']['stage']+='/another'
            else:c['CPU_proof']['payload_sha256']={}
            with self.subTest(change=change),self.assertRaises(ValueError):self.check(c)

    def test_other_revision_cannot_replace_original_source(self):
        self.check(self.original)
        with self.assertRaises(ValueError):
            accept([self.path],source_revision='0a5729ef3bebcd1e7c006165f6f4720a9dd7c349')
        with self.assertRaisesRegex(ValueError,'immutable full commit SHA'):
            accept([self.path],source_revision='HEAD')


if __name__=='__main__':unittest.main()
