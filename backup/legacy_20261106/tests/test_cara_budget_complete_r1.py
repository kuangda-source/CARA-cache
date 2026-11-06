"""Tiny full112 artifact fixtures plus real lifecycle audit; no model/GPU."""
import copy
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

import numpy as np

from wcomr import cara_budget_complete_r1 as complete
from wcomr.cara_budget_calibration_r1 import Calibration,PRODUCTION_CONFIG
from wcomr.cara_budget_runner_binding_r1 import SPEC,PROFILE,LIMITS
from wcomr.cara_budget_storage_r1 import StorageLimits
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_budget_search_journal_r1 import create_record,read_record
from wcomr.gpu_budget_pool_v2 import BudgetPool,SCHEMA,sha
from wcomr.policy_price_terminal_r1 import record
from test_cara_budget_lifecycle_r1 import fixture,put

ROOT=Path(__file__).resolve().parents[1]


class CompleteTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name);self.stage=self.project/'.sync/original-CPU-fixture'
        self.card=json.loads((ROOT/SPEC).read_text());self.card['calibration']['RGB_shape']=[3,93,2,2]
        self.card.pop('scope_sha256');self.card['scope_sha256']=digest(self.card)
        self.capture,_,job=fixture()
        identity={k:job[k] for k in complete.IDENTITY};identity.update(stage=str(self.stage),scope_sha256=self.card['scope_sha256'])
        reg=record(self.capture,'registration');reg['stage']=str(self.stage)
        reg['payload_sha256'].update({complete.SOURCE:sha(complete.__file__),complete.PRODUCER:sha(ROOT/complete.PRODUCER),PROFILE:sha(ROOT/PROFILE)})
        self.capture['payload_actual_sha256']=reg['payload_sha256'];regsha=put(self.capture,'registration',reg)
        auth=record(self.capture,'authorization');auth.update(identity);authsha=put(self.capture,'authorization',auth)
        job.update(identity,registration_sha256=regsha,authorization_sha256=authsha)
        envsha=put(self.capture,'central_reservation',dict(central_ledger_host='four_card',job=job))
        self.launch=record(self.capture,'launch');self.launch.update(identity,registration_sha256=regsha,authorization_sha256=authsha,central_reservation_sha256=envsha)
        self.expected=put(self.capture,'launch',self.launch)
        self.capture['container']['manifest_sha256']=regsha
        bill=record(self.capture,'billing');bill.update(identity);billsha=put(self.capture,'billing',bill)
        guardian=record(self.capture,'guardian');guardian.update(identity,billing_sha256=billsha)
        guardian['container_terminal_witness']['container']=self.capture['container'];put(self.capture,'guardian',guardian)
        pending=record(self.capture,'pending_release');pending.update(identity);put(self.capture,'pending_release',pending)
        self.context={**identity,'CPU_fixture_only':True,'launch_sha256':self.expected,'registration_sha256':regsha,
            'runner_profile_sha256':sha(ROOT/PROFILE),'candidate_queries':51,'physical_paths':112}
        self.limits=StorageLimits(**json.loads((ROOT/LIMITS).read_text())['limits'])
        self.output=self.project/'outputs'/self.launch['run_id'];self.output.mkdir(parents=True)
        self.calls=0
        def execute(slot,policy,output):
            self.calls+=1;output.mkdir();(output/'CPU-fixture.txt').write_text('Synthetic writer\n')
            policy=policy or self.card['roles'][slot['role']].get('policy')
            rgb=np.full((3,93,2,2),.6 if policy else .5,dtype=np.float32)
            result=dict(status='COMPLETE',solver_steps=36,guided_pairs=36,CPU_fixture=True,
                T_DD=.5 if slot['timing_enabled'] else None,T_request=1.)
            if policy:result['semantic_history']=[dict(actual=a,fallback_reason=None) for a in policy['actions']]
            return result,rgb,'a'*64
        entry=Calibration(root=self.output/'calibration',card=self.card,config=PRODUCTION_CONFIG,
            context_sha256=digest(self.context),RGB_shape=[3,93,2,2],execute=execute,
            cpu_validation=True,create=True,storage_limits=self.limits)
        collection=entry.run(allow_new=True);self.assertTrue(collection['complete'])
        create_record(self.output/'calibration-collection.json',collection)
        precision=dict(model_precision='torch.bfloat16',use_wan_fp32_strategy=True,conditional_frame_timestep=.1,outer_autocast=False)
        create_record(self.output/'calibration-model-precision.json',precision)
        create_record(self.output/'calibration-runner.json',dict(phase='CALIBRATION',status='CALIBRATION_CPU_COMPLETE',
            source_revision=self.launch['source_revision'],scope_sha256=self.card['scope_sha256'],context_sha256=digest(self.context),
            started_unix=10.,ended_unix=20.,scientific_freeze_written=False,precision=precision))
        create_record(self.output/'calibration-runner-intent.json',dict(context=self.context,identity=record(self.capture,'runner_start')['identity']))
        pool=BudgetPool(self.project/'ledger');pool.path.parent.mkdir(parents=True)
        before=dict(schema=SCHEMA,cap_gpu_hours=226.,origin_used_gpu_hours=50.,origin_gpu_jobs_launched=10,
            jobs={job['job_id']:job,'old-unknown-16.5':dict(status='RESERVED_OR_RUNNING',gpu_uuid='GPU-OLD',billed_limit_GPUh=16.5)},events=[])
        before.update(pool.accounting(before));pool.path.write_text(json.dumps(before))
        after=pool.settle(job['job_id'],bill['actual_GPUh'],billsha)
        self.settlement=dict(central_ledger_host='four_card',launch_id=self.launch['launch_id'],billing_sha256=billsha,central_before=before,central_after=after)
        # Stage model/approval metadata is mocked only in these CPU fixtures.
        mocked=patch.object(complete,'validate',return_value=(self.card,self.launch,{},self.limits,self.context))
        self.validator=mocked.start();self.addCleanup(mocked.stop)

    def accept(self):
        return complete.accept(self.project,self.stage,self.capture,self.expected,self.settlement,cpu_validation=True)

    def change(self,path,update):
        value=read_record(path);update(value);path.write_text(json.dumps(value))

    def test_complete_full112_and_once_fixture_freeze_no_generation(self):
        first=complete.freeze_once(self.project,self.stage,self.capture,self.expected,self.settlement,cpu_validation=True)
        second=complete.freeze_once(self.project,self.stage,self.capture,self.expected,self.settlement,cpu_validation=True)
        self.assertEqual(self.calls,112);self.assertTrue(first['new_freeze_created']);self.assertFalse(second['new_freeze_created'])
        self.assertEqual(first['freeze_sha256'],second['freeze_sha256']);self.assertFalse(first['complete_search_accepted'])
        self.assertFalse(first['scientific_freeze_written']);self.assertTrue(first['CPU_fixture_freeze_written'])
        self.assertEqual(first['complete_two_FIT_queries'],51)
        self.assertFalse((self.output/'calibration-frozen-mask.json').exists())
        self.assertEqual(self.settlement['central_after']['reserved_gpu_hours'],16.5)

    def test_live_or_unsettled_rejected_before_any_scientific_file_read(self):
        self.capture['process_observations']['runner']['original_live']=True
        with patch.object(complete,'read_record',side_effect=AssertionError('Science opened too early')):
            with self.assertRaises(ValueError):self.accept()
        self.assertFalse(self.validator.called)
        self.capture['process_observations']['runner']['original_live']=False
        self.settlement['central_after']=self.settlement['central_before']
        with patch.object(complete,'read_record',side_effect=AssertionError('Science opened too early')):
            with self.assertRaises(ValueError):self.accept()

    def test_unrestored_or_failed_allocation_rejected_before_scientific_read(self):
        original=copy.deepcopy(self.capture)
        for failure in ('unrestored','failed'):
            self.capture=copy.deepcopy(original);guardian=record(self.capture,'guardian')
            if failure=='unrestored':guardian['mode_restoration']['restored']=False
            else:
                self.capture['container']['state'].update(ExitCode=137,OOMKilled=True)
                guardian.update(container_exit_code=137,error_type='GPUWorkerFailure')
                guardian['container_terminal_witness']['container']=self.capture['container']
            put(self.capture,'guardian',guardian)
            with self.subTest(failure=failure),patch.object(complete,'read_record',side_effect=AssertionError('Science opened too early')):
                with self.assertRaises(ValueError):self.accept()
        self.assertFalse(self.validator.called)

    def test_wrong_context_and_reader_source_refused(self):
        self.context['launch_sha256']='b'*64
        with self.assertRaises(ValueError):self.accept()
        self.context['launch_sha256']=self.expected
        self.capture['payload_actual_sha256']={}
        with self.assertRaises(ValueError):self.accept()

    def test_partial_or_extra_incomplete_path_refused(self):
        self.change(self.output/'calibration-collection.json',lambda v:v.update(complete_physical_paths=111))
        with self.assertRaises(ValueError):self.accept()
        self.change(self.output/'calibration-collection.json',lambda v:v.update(complete_physical_paths=112))
        (self.output/'calibration/unrecorded-failed-path').mkdir()
        with self.assertRaises(ValueError):self.accept()

    def test_physical_counts_timing_and_RNG_mutations_refused(self):
        path=self.output/'calibration/query-000001-FIT0/complete.json';raw=path.read_bytes()
        for key,value in (('actual_D',18),('solver_steps',35),('rng_sha256','x'*64),('T_DD',-1),('CPU_fixture_only',False)):
            path.write_bytes(raw);self.change(path,lambda v:v.update({key:value}))
            with self.subTest(key=key),self.assertRaises(ValueError):self.accept()

    def test_damaged_RGB_or_generation_never_frozen(self):
        path=self.output/'calibration/query-000051-FIT1/endpoint/RGB.npy'
        raw=path.read_bytes();path.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
        with self.assertRaises(ValueError):self.accept()
        path.write_bytes(raw)
        (self.output/'calibration/query-000051-FIT1/generation/CPU-fixture.txt').write_text('changed')
        with self.assertRaises(ValueError):self.accept()

    def test_collection_best_or_query_return_tampering_refused(self):
        path=self.output/'calibration-collection.json';raw=path.read_bytes()
        self.change(path,lambda v:v['search']['best_complete_candidate'].update(query_id=50))
        with self.assertRaises(ValueError):self.accept()
        path.write_bytes(raw)
        (self.output/'calibration/queries/query-000051.return.json').unlink()
        with self.assertRaises(ValueError):self.accept()
        self.assertEqual(self.calls,112)

    def test_existing_conflicting_freeze_preserved(self):
        path=self.output/'CPU-calibration-frozen-mask.json';path.write_text('{"original":"preserve"}')
        with self.assertRaises(ValueError):complete.freeze_once(self.project,self.stage,self.capture,self.expected,self.settlement,cpu_validation=True)
        self.assertEqual(path.read_text(),'{"original":"preserve"}')

    def test_production_CLI_rejects_CPU_before_writing_receipt(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        import accept_cara_budget_complete_r1 as cli
        # CLI is prospectively bound; the fixture still cannot pass production mode.
        reg=record(self.capture,'registration')
        reg['payload_sha256']['scripts/accept_cara_budget_complete_r1.py']=sha(cli.__file__)
        put(self.capture,'registration',reg)
        capture=self.project/'capture.json';settlement=self.project/'settlement.json';output=self.project/'accept.json'
        capture.write_text(json.dumps(self.capture));settlement.write_text(json.dumps(self.settlement))
        argv=['accept','--project',str(self.project),'--stage',str(self.stage),'--capture',str(capture),
            '--settlement',str(settlement),'--output',str(output),'--expected-launch-sha256',self.expected,'--freeze']
        with patch.object(sys,'argv',argv),self.assertRaises(ValueError):cli.main()
        self.assertFalse(output.exists());self.assertFalse((self.output/'calibration-frozen-mask.json').exists())

    def test_CPU_fixture_cannot_accept_as_production(self):
        with self.assertRaises(ValueError):complete.accept(self.project,self.stage,self.capture,self.expected,self.settlement)
        self.assertFalse(self.validator.called)


if __name__=='__main__':unittest.main()
