"""Metadata and refusal controls; no model or GPU execution."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.cara_budget_calibration_r1 import Calibration,PRODUCTION_CONFIG,validate_production_context
from wcomr.cara_budget_runner_binding_r1 import validate,SPEC,PROFILE,LIMITS,SOURCE,RUNNER,REQUIRED
from wcomr.cara_budget_lifecycle_r1 import IDENTITY,JOB_IDENTITY
from wcomr.cara_budget_storage_r1 import StorageLimits
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import sha

ROOT=Path(__file__).resolve().parents[1]


class RunnerBindingTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name);self.stage=self.project/'.sync/cara-budget-calibration-GPU-test'
        self.stage.mkdir(parents=True);(self.project/'runtime').mkdir()
        (self.project/'runtime/source.py').write_text('# Pinned metadata fixture\n')
        paths=REQUIRED
        for name in paths:
            target=self.stage/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/name).read_bytes())
        self.card=json.loads((self.stage/SPEC).read_text())
        self.launch=dict(run_id='cara-budget-calibration-test',launch_id='a'*32,host='four_card',
            gpu_uuid='GPU-11111111-2222-3333-4444-555555555555',stage=str(self.stage),source_revision='b'*40,
            scope_sha256=self.card['scope_sha256'],billed_limit_GPUh=14,CPU_fixture_only=False)
        self.reg=dict(host='four_card',stage=str(self.stage),source_revision='b'*40,
            payload_sha256={n:sha(self.stage/n) for n in paths},runtime_source_sha256={'source.py':sha(self.project/'runtime/source.py')})
        self.proof=dict(passed=True,whole_card_CPU_accepted=True,host='four_card',scope_sha256=self.card['scope_sha256'],
            payload_sha256=self.reg['payload_sha256'],runtime_source_sha256=self.reg['runtime_source_sha256'])
        self.quote=dict(scope_sha256=self.card['scope_sha256'],whole_quote_accepted=True,host_quotes={
            'four_card':dict(hard_GPUh=14,forecast_GPUh=13,physical_paths=112,candidate_queries=51)})
        self.auth={k:self.launch[k] for k in IDENTITY}
        self.auth.update(CPU_fixture_only=False,execution_authorized=True,authorizes_replay=False,
            direct_user_authorization=True,user_quote='Metadata fixture only; not real approval')
        self.write_all()

    def write(self,name,value):
        (self.stage/name).write_text(json.dumps(value,sort_keys=True)+'\n')

    def write_all(self):
        self.write('registration.json',self.reg);self.write('execution-CPU-proof.json',self.proof)
        self.write('whole-quote.json',self.quote)
        self.auth.update(CPU_proof_sha256=sha(self.stage/'execution-CPU-proof.json'),quote_sha256=sha(self.stage/'whole-quote.json'))
        self.write('GPU-authorization.json',self.auth)
        self.launch.update(authorization_sha256=sha(self.stage/'GPU-authorization.json'),registration_sha256=sha(self.stage/'registration.json'))
        job={k:self.launch[k] for k in JOB_IDENTITY};job.update(job_id=self.launch['run_id'],status='RESERVED_OR_RUNNING')
        self.write('central-reservation.json',dict(central_ledger_host='four_card',new_reservation=True,job=job))
        self.launch['central_reservation_sha256']=sha(self.stage/'central-reservation.json')
        self.write('GPU-launch.json',self.launch)

    def test_complete_metadata_binds_new_scope_and_producer(self):
        card,launch,profile,limits,context=validate(self.project,self.stage)
        self.assertNotEqual(card['scope_sha256'],card['original_request_scope_sha256'])
        self.assertEqual(context['physical_paths'],112)
        self.assertEqual(limits.volume_bytes,64*2**30)
        entry=Calibration(root=self.project/'output',card=card,config=PRODUCTION_CONFIG,
            context_sha256=digest(context),RGB_shape=[3,93,432,768],execute=lambda *args:None,
            storage_limits=limits,production_context=context,create=True)
        self.assertIs(entry.binding['CPU_fixture_only'],False)
        self.assertFalse(entry.allow_new)

    def test_missing_approval_or_replay_refused(self):
        for key,value in (('execution_authorized',False),('direct_user_authorization',False),('authorizes_replay',True),('CPU_fixture_only',True)):
            original=self.auth[key];self.auth[key]=value;self.write_all()
            with self.subTest(key=key),self.assertRaises(ValueError):validate(self.project,self.stage)
            self.auth[key]=original

    def test_partial_wrong_host_or_unaccepted_CPU_refused(self):
        for key,value in (('passed',False),('whole_card_CPU_accepted',False),('host','two_card'),('payload_sha256',{})):
            original=self.proof[key];self.proof[key]=value;self.write_all()
            with self.subTest(key=key),self.assertRaises(ValueError):validate(self.project,self.stage)
            self.proof[key]=original

    def test_incomplete_quote_or_wrong_reservation_refused(self):
        self.quote['host_quotes']['four_card']['physical_paths']=111;self.write_all()
        with self.assertRaises(ValueError):validate(self.project,self.stage)
        self.quote['host_quotes']['four_card']['physical_paths']=112;self.write_all()
        envelope=json.loads((self.stage/'central-reservation.json').read_text());envelope['job']['launch_id']='c'*32
        self.write('central-reservation.json',envelope)
        self.launch['central_reservation_sha256']=sha(self.stage/'central-reservation.json');self.write('GPU-launch.json',self.launch)
        with self.assertRaises(ValueError):validate(self.project,self.stage)

    def test_changed_source_or_runtime_refused(self):
        path=self.stage/RUNNER;original=path.read_bytes();path.write_bytes(original+b'\n')
        with self.assertRaises(ValueError):validate(self.project,self.stage)
        path.write_bytes(original);(self.project/'runtime/source.py').write_text('# Changed\n')
        with self.assertRaises(ValueError):validate(self.project,self.stage)

    def test_production_context_geometry_counts_and_mode_cannot_drift(self):
        card,_,_,limits,context=validate(self.project,self.stage)
        for key,value in (('physical_paths',110),('candidate_queries',50),('billed_limit_GPUh',13),('source_revision','HEAD'),('CPU_fixture_only',True)):
            changed={**context,key:value}
            with self.subTest(key=key),self.assertRaises(ValueError):
                validate_production_context(changed,card,PRODUCTION_CONFIG,[3,93,432,768],limits)
        with self.assertRaises(ValueError):validate_production_context(context,card,PRODUCTION_CONFIG,[3,93,16,16],limits)
        with self.assertRaises(ValueError):Calibration(root=self.project/'output',card=card,config=PRODUCTION_CONFIG,
            context_sha256='c'*64,RGB_shape=[3,93,432,768],execute=None,storage_limits=limits,production_context=context,create=True)

    def test_CPU_result_cannot_complete_production_path(self):
        card,_,_,limits,context=validate(self.project,self.stage)
        def execute(*args):
            return dict(status='COMPLETE',solver_steps=36,guided_pairs=36,CPU_fixture=True),None,'a'*64
        entry=Calibration(root=self.project/'output',card=card,config=PRODUCTION_CONFIG,
            context_sha256=digest(context),RGB_shape=[3,93,432,768],execute=execute,
            storage_limits=limits,production_context=context,create=True)
        with self.assertRaises(ValueError):entry.run(allow_new=True)
        self.assertEqual(entry.physical_calls,1)
        self.assertFalse((self.project/'output/warm-native/complete.json').exists())


if __name__=='__main__':unittest.main()
