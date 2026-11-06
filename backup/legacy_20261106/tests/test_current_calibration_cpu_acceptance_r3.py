"""Mutation controls for the independent reader; synthetic metadata, no CPU launch."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from accept_cara_budget_calibration_cpu_r3 import accept,encoded_sha,COUNTS,HOST_CONFIG,STAGES,TWO_CARD_R4_STAGE


class CurrentCPUAcceptanceTests(unittest.TestCase):
    def fixture(self,host='four_card'):
        scope='a'*64;revision='b'*40
        blobs={'plans/cara_next_stage_20261028/mainline/r2/BUDGET_RUN_SPEC_R1.json':json.dumps(dict(scope_sha256=scope)).encode()}
        base=dict(host=host,payload_sha256={},runtime_source_sha256={'pinned.py':'c'*64})
        plan=dict(base_registration_sha256=encoded_sha(base),overlay_sha256={n:hashlib.sha256(v).hexdigest() for n,v in blobs.items()})
        package=dict(source_revision=revision,plan_sha256=encoded_sha(plan),overlay_files=len(blobs))
        reg=dict(host=host,stage='/fixture/.sync/'+STAGES[host],parent_git_revision=revision,
            base_registration_sha256=encoded_sha(base),payload_sha256=plan['overlay_sha256'],
            runtime_source_sha256=base['runtime_source_sha256'],expected_host_config=HOST_CONFIG)
        launch=dict(host=host,stage=reg['stage'],container=STAGES[host]+'-cpu',
            status='PAPER_TIMING_CPU_LAUNCHED_NOT_GPU',registration_sha256=encoded_sha(reg),started_unix=1.)
        controls=[dict(module=n,tests_run=count,errors=0,failures=0,skipped=0,
            Linux_observations=[{}]*({'test_cara_budget_supervisor_r1':11,'test_cara_budget_host_guardian_r1':12}.get(n,0))) for n,count in COUNTS.items()]
        rows=[dict(flow=flow,validation='COMPLETE112_CALIBRATION_ROUTES_CPU_NOT_GPU',complete_design_paths=112,
            complete_two_FIT_queries=51,SA_iterations=30,HC_iterations=1,HC_neighbors=20,
            successful_physical_paths=133,declared_failure_attempts=3,total_physical_attempts=136,
            complete93_frame_RGB=True,Native_allD_timing_RGB_and_full_CPU_RNG_equal=True,
            original_complete_recovery_without_generation=True,hooks_restored=True,CUDA_RNG_exercised=False,
            Cosmos_model_weights_loaded=False,real_GPU_executed=False,whole_GPU_card_accepted=False,
            failures=[dict(kind=k,physical_attempts=n,no_replay=True) for k,n in
                (('first_writer',1),('second_FIT_refusal',12),('policy_fallback',11))]) for flow in (False,True)]
        proof=dict(host=host,scope_sha256=scope,status='CURRENT_COMPLETE_CALIBRATION_AND_EXECUTION_CONTROLS_CPU_NOT_GPU',
            registration_sha256=encoded_sha(reg),payload_sha256=reg['payload_sha256'],runtime_source_sha256=reg['runtime_source_sha256'],
            spec_tests=3,execution_control_tests=134,control_results=controls,numeric=dict(checks=rows,cuda_initialized=False),
            resource_bound=dict(cpus=1,memory_GiB=4,work_seconds=2400,exit_seconds=60),actual_compile_threads=1,compile_pools=[],
            CUDA_initialized=False,Cosmos_model_weights_loaded=False,GPU_submissions=0,ledger_written=False,
            whole_GPU_card_accepted=False,real_Docker_GPU_lifecycle_exercised=False,real_64GiB_storage_exercised=False,
            dispatch_child_spawn_simulated=True,started_unix=2.,ended_unix=3.)
        cap=dict(launch=launch,registration=reg,CPU_proof=proof,registration_sha256=encoded_sha(reg),CPU_proof_sha256=encoded_sha(proof),
            host_config=HOST_CONFIG,payload_intact=True,runtime_intact=True,
            container_state=dict(Status='exited',Running=False,Pid=0,ExitCode=0,OOMKilled=False))
        return cap,launch,plan,base,revision,blobs,package

    def check(self,values):
        c,l,p,b,r,blobs,package=values
        return accept(c,l,p,b,r,published_bytes=blobs.__getitem__,package_receipt=package)

    def test_complete_both_host_fixtures_do_not_grant_GPU_or_whole_dispatch_acceptance(self):
        for host in STAGES:
            result=self.check(self.fixture(host));self.assertEqual(result['complete_design_paths'],224)
            self.assertFalse(result['GPU_dispatch_ready']);self.assertFalse(result['whole_card_CPU_accepted'])

    def test_R4_is_an_independent_two_card_stage_with_unchanged_complete_scope(self):
        for host in STAGES:
            x=copy.deepcopy(self.fixture(host));cap,launch=x[:2]
            reg=cap['registration'];proof=cap['CPU_proof']
            reg['stage']=launch['stage']='/fixture/.sync/'+TWO_CARD_R4_STAGE
            launch['container']=TWO_CARD_R4_STAGE+'-cpu'
            cap['registration_sha256']=launch['registration_sha256']=proof['registration_sha256']=encoded_sha(reg)
            cap['CPU_proof_sha256']=encoded_sha(proof)
            if host=='two_card':
                result=self.check(x)
                self.assertEqual(result['status'],'CURRENT_R4_CPU_MATRIX_ACCEPTED_NOT_GPU_DISPATCH')
                self.assertEqual(result['complete_design_paths'],224)
            else:
                with self.assertRaises(ValueError):self.check(x)

    def test_live_failure_or_wrong_resource_is_refused(self):
        for target,key,value in [('container_state','Running',True),('container_state','ExitCode',9),
                ('container_state','OOMKilled',True),('host_config','MemorySwap',8*2**30)]:
            x=copy.deepcopy(self.fixture());x[0][target][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.check(x)

    def test_missing_Linux_controls_or_query_and_replay_scope_is_refused(self):
        for change in ('skip','duplicate','scenario','flow','queries','replay','GPU','clock'):
            x=copy.deepcopy(self.fixture());p=x[0]['CPU_proof']
            if change=='skip':p['control_results'][-1]['skipped']=1
            elif change=='duplicate':p['control_results'][-1]=p['control_results'][0]
            elif change=='scenario':p['control_results'][-1]['Linux_observations'].pop()
            elif change=='flow':p['numeric']['checks'].pop()
            elif change=='queries':p['numeric']['checks'][0]['complete_two_FIT_queries']=50
            elif change=='replay':p['numeric']['checks'][0]['original_complete_recovery_without_generation']=False
            elif change=='GPU':p['CUDA_initialized']=True
            else:p['ended_unix']=3000
            x[0]['CPU_proof_sha256']=encoded_sha(p)
            with self.subTest(change=change),self.assertRaises(ValueError):self.check(x)

    def test_original_launch_and_source_or_package_cannot_be_replaced(self):
        for change in ('launch','revision','blob','package','proof'):
            x=copy.deepcopy(self.fixture())
            if change=='launch':x[1]['stage']+='/replacement'
            elif change=='revision':x=list(x);x[4]='d'*40
            elif change=='blob':x[5][next(iter(x[5]))]=b'changed'
            elif change=='package':x[6]['plan_sha256']='0'*64
            else:x[0]['CPU_proof_sha256']='0'*64
            with self.subTest(change=change),self.assertRaises(ValueError):self.check(x)


if __name__=='__main__':unittest.main()
