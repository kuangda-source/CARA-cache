"""Isolated metadata fixtures; these declarations are not real GPU authority."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from wcomr import cara_s_endpoint_runner_binding_r1 as binding
from wcomr.cara_budget_host_policy_r1 import POLICY_SHA256
from wcomr.cara_fast_binding_r2 import load_card
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_s_uniform_endpoint_binding_r1 import map_physical_slots
from wcomr.cara_s_uniform_endpoint_execution_r1 import request_card
from wcomr.gpu_budget_pool_v2 import sha

ROOT=Path(__file__).resolve().parents[1]
PLAN='plans/cara_next_stage_20261028/mainline/r2/S_UNIFORM_BUDGET_ENDPOINT32_PROPOSAL_R1_20261031.json'


class Fixture:
    def __init__(self,project,alias=False,endpoint7=False):
        self.project=Path(project);self.stage=self.project/'.sync/cara-S-endpoint-GPU-CPU-metadata'
        self.stage.mkdir(parents=True);(self.project/'runtime').mkdir()
        (self.project/'runtime/CPU-source.py').write_text('# CPU metadata fixture, not a production runtime\n')
        self.proposal=json.loads((ROOT/PLAN).read_text());base=load_card(ROOT,binding.BASE)
        policy=self.proposal['new_policies']['SU19_CFG_C'] if alias else base['roles']['UNIFORM19_C']['policy']
        if endpoint7:
            self.proposal=json.loads((ROOT/'configs/cara_endpoint_proposal.json').read_text())
            policy=self.proposal['new_policies']['BUDGET_SEARCH19_C']
        origin=self.proposal['budget_comparator']
        frozen=dict(schema='CARA_BUDGET_COMPLETE_MASK_FREEZE_R1',CPU_fixture_only=False,new_GPU_authority=False,
            complete_physical_paths=112,complete_two_FIT_queries=51,
            selected=dict(dense=[i+1 for i,a in enumerate(policy['actions']) if a=='D'],policy_fingerprint=policy['fingerprint']),
            policy=policy,**{k:origin['original_'+k] for k in ('run_id','launch_id','source_revision','scope_sha256')})
        self.freeze=self.project/'outputs'/frozen['run_id']/'calibration-frozen-mask.json'
        self.freeze.parent.mkdir(parents=True);self.freeze.write_text(json.dumps(frozen)+'\n')
        self.bound=map_physical_slots(self.proposal,policy)
        self.bound.update(CPU_fixture_only=False,status='FROZEN_POLICY_BOUND_WHOLE_CPU_PENDING',
            proposal_scope_sha256=self.proposal['scope_sha256'],original_calibration=frozen,
            original_freeze_path=str(self.freeze),original_freeze_sha256=sha(self.freeze))
        self.bound['binding_sha256']=digest(self.bound)
        self.card=request_card(self.proposal,self.bound,base)
        self.profile=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_CONTAINER_PROFILE_R1.json').read_text())
        self.profile.update(schema='CARA_ENDPOINT_CONTAINER_PROFILE_R1',scope_sha256=self.card['scope_sha256'],
            endpoint_binding_sha256=self.bound['binding_sha256'],hard_GPUh=5.25,
            physical_paths=len(self.card['physical_matrix']),new_scoring_pairs=self.bound['counts']['unique_new_scoring_pairs'])
        self.profile['hosts']={'two_card':self.profile['hosts']['two_card']}
        if endpoint7:
            self.profile['endpoint7']=True
            self.profile['storage'].update(minimum_output_free_bytes=8*2**30,minimum_host_free_bytes=16*2**30,minimum_host_free_before_provision_bytes=80*2**30)
        self.profile.pop('candidate_queries')
        configs={binding.CARD:self.card,binding.BINDING:self.bound,binding.PROPOSAL:self.proposal,binding.PROFILE:self.profile}
        required=binding.REQUIRED+(('src/wcomr/cara_endpoint7_binding_r1.py','src/wcomr/cara_endpoint7_plan_r1.py') if endpoint7 else ())
        for name in required:
            target=self.stage/name;target.parent.mkdir(parents=True,exist_ok=True)
            if name in configs:target.write_text(json.dumps(configs[name])+'\n')
            else:target.write_bytes((ROOT/name).read_bytes())
        self.reg=dict(host='two_card',stage=str(self.stage),source_revision='b'*40,container_image=binding.IMAGE,
            payload_sha256={p:sha(self.stage/p) for p in required},
            runtime_source_sha256={'CPU-source.py':sha(self.project/'runtime/CPU-source.py')})
        self.auth=dict(run_id='cara-S-endpoint-cpu-metadata',launch_id='a'*32,host='two_card',gpu_uuid=self.proposal['gpu_uuid'],
            stage=str(self.stage),source_revision='b'*40,scope_sha256=self.card['scope_sha256'],billed_limit_GPUh=5.25,
            CPU_fixture_only=False,execution_authorized=True,authorizes_replay=False,direct_user_authorization=True,
            user_quote='CPU metadata fixture, never user authority',new_endpoint_authorization=True,
            card_kind='CARA_SU19_BUDGET_ENDPOINT',physical_paths=self.profile['physical_paths'],
            endpoint_binding_sha256=self.bound['binding_sha256'],original_budget_freeze_sha256=sha(self.freeze),
            execution_host_policy_sha256=POLICY_SHA256)
        self.proof=dict(passed=True,whole_card_CPU_accepted=True,selected_policy_affected_CPU_accepted=True,
            host='two_card',scope_sha256=self.card['scope_sha256'],endpoint_binding_sha256=self.bound['binding_sha256'],
            original_budget_freeze_sha256=sha(self.freeze),payload_sha256=self.reg['payload_sha256'],
            runtime_source_sha256=self.reg['runtime_source_sha256'],execution_host_policy_sha256=POLICY_SHA256)
        self.quote=dict(whole_quote_accepted=True,scope_sha256=self.card['scope_sha256'],
            endpoint_binding_sha256=self.bound['binding_sha256'],execution_host_policy_sha256=POLICY_SHA256,
            host_quotes={'two_card':dict(physical_paths=self.profile['physical_paths'],new_scoring_pairs=self.profile['new_scoring_pairs'],
                hard_GPUh=5.25,forecast_GPUh=4.5,components_seconds=dict(generation=15000,path_artifacts=300,
                admission_and_model_load=300,stop_and_release=600),evidence_refs=['CPU metadata only'])})
        self.write_all()

    def write(self,name,value):
        (self.stage/name).write_text(json.dumps(value,indent=2)+'\n')

    def write_all(self):
        self.write('registration.json',self.reg);self.write('execution-CPU-proof.json',self.proof);self.write('whole-quote.json',self.quote)
        self.auth.update(CPU_proof_sha256=sha(self.stage/'execution-CPU-proof.json'),quote_sha256=sha(self.stage/'whole-quote.json'))
        self.write('GPU-authorization.json',self.auth)
        self.launch={k:self.auth[k] for k in binding.IDENTITY}
        self.launch.update(CPU_fixture_only=False,registration_sha256=sha(self.stage/'registration.json'),
            authorization_sha256=sha(self.stage/'GPU-authorization.json'),
            **{k:self.auth[k] for k in ('physical_paths','endpoint_binding_sha256','original_budget_freeze_sha256')})
        job={k:self.launch[k] for k in binding.JOB_IDENTITY};job.update(job_id=self.launch['run_id'],status='RESERVED_OR_RUNNING')
        self.write('central-reservation.json',dict(central_ledger_host='four_card',new_reservation=True,job=job))
        self.launch['central_reservation_sha256']=sha(self.stage/'central-reservation.json');self.write('GPU-launch.json',self.launch)

    def validate(self):return binding.validate(self.project,self.stage)


class Binding(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.f=Fixture(self.temp.name)

    def test_complete32_context(self):
        *_,context=self.f.validate()
        self.assertEqual(context['physical_paths'],32);self.assertEqual(context['phase'],'ENDPOINT')
        self.assertEqual(context['model_precision_sha256'],self.f.proposal['precision_sha256'])

    def test_complete_alias25_context(self):
        with tempfile.TemporaryDirectory() as root:
            f=Fixture(root,True);*_,context=f.validate()
            self.assertEqual(context['physical_paths'],25)
            self.assertEqual(f.profile['new_scoring_pairs'],8)

    def test_independent_direct_authority(self):
        for key,value in [('execution_authorized',False),('direct_user_authorization',False),('new_endpoint_authorization',False),
                          ('authorizes_replay',True),('CPU_fixture_only',True)]:
            old=self.f.auth[key];self.f.auth[key]=value;self.f.write_all()
            with self.subTest(key=key),self.assertRaises(ValueError):self.f.validate()
            self.f.auth[key]=old

    def test_two_card_only(self):
        self.f.auth['host']=self.f.reg['host']='four_card';self.f.write_all()
        with self.assertRaisesRegex(ValueError,'two-card'):self.f.validate()

    def test_stale_payload(self):
        (self.f.stage/binding.LOADED).write_text('# modified\n')
        with self.assertRaisesRegex(ValueError,'source/runtime'):self.f.validate()

    def test_stale_runtime(self):
        (self.f.project/'runtime/CPU-source.py').write_text('# modified\n')
        with self.assertRaisesRegex(ValueError,'source/runtime'):self.f.validate()

    def test_missing_complete_CPU(self):
        for key in ('passed','whole_card_CPU_accepted','selected_policy_affected_CPU_accepted'):
            self.f.proof[key]=False;self.f.write_all()
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'CPU acceptance'):self.f.validate()
            self.f.proof[key]=True

    def test_CPU_bound_to_selected_policy(self):
        self.f.proof['endpoint_binding_sha256']='f'*64;self.f.write_all()
        with self.assertRaisesRegex(ValueError,'CPU acceptance'):self.f.validate()

    def test_original_freeze_changed(self):
        self.f.freeze.write_text(self.f.freeze.read_text()+' ')
        with self.assertRaisesRegex(ValueError,'budget freeze'):self.f.validate()

    def test_partial_quote(self):
        self.f.quote['host_quotes']['two_card']['physical_paths']=31;self.f.write_all()
        with self.assertRaisesRegex(ValueError,'host quote'):self.f.validate()

    def test_release_cost_missing(self):
        self.f.quote['host_quotes']['two_card']['components_seconds'].pop('stop_and_release');self.f.write_all()
        with self.assertRaisesRegex(ValueError,'allocation costs'):self.f.validate()

    def test_original_reservation_only(self):
        value=json.loads((self.f.stage/'central-reservation.json').read_text());value['job']['launch_id']='f'*32
        self.f.write('central-reservation.json',value)
        self.f.launch['central_reservation_sha256']=sha(self.f.stage/'central-reservation.json');self.f.write('GPU-launch.json',self.f.launch)
        with self.assertRaisesRegex(ValueError,'central reservation'):self.f.validate()

    def test_launch_physical_scope(self):
        self.f.launch['physical_paths']=25;self.f.write('GPU-launch.json',self.f.launch)
        with self.assertRaisesRegex(ValueError,'launch field'):self.f.validate()

    def test_frozen_counts_cannot_be_resigned_partial(self):
        self.f.bound['original_calibration']['complete_physical_paths']=111
        self.f.freeze.write_text(json.dumps(self.f.bound['original_calibration'])+'\n')
        self.f.bound['original_freeze_sha256']=sha(self.f.freeze)
        self.f.bound['binding_sha256']=digest({k:v for k,v in self.f.bound.items() if k!='binding_sha256'})
        self.f.card=request_card(self.f.proposal,self.f.bound,load_card(ROOT,binding.BASE))
        for name,value in [(binding.BINDING,self.f.bound),(binding.CARD,self.f.card)]:
            self.f.write(name,value);self.f.reg['payload_sha256'][name]=sha(self.f.stage/name)
        self.f.write_all()
        with self.assertRaisesRegex(ValueError,'budget freeze'):self.f.validate()


if __name__=='__main__':unittest.main()
