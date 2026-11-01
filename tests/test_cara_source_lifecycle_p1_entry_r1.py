"""P1 production metadata/resource/queue boundaries; no real authority or GPU work."""
import copy
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wcomr import cara_source_lifecycle_p1_runner_binding_r1 as binding
from wcomr.cara_budget_host_policy_r1 import POLICY_SHA256
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import atomic_json, sha
from wcomr import history104_storage_r2 as storage_module
import run_cara_source_lifecycle_p1_r1 as entry

ROOT=Path(__file__).resolve().parents[1]


class Fixture:
    def __init__(self,root):
        self.project=Path(root)
        self.stage=self.project/'.sync'/binding.STAGE_NAME
        self.stage.mkdir(parents=True)
        (self.project/'runtime').mkdir()
        (self.project/'runtime/CPU.py').write_text('# CPU metadata only\n')
        for name in binding.REQUIRED:
            target=self.stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
        self.extra=json.loads((self.stage/binding.RUNTIME_ENTRY).read_bytes())
        for name,source in self.extra['snapshots'].items():
            path=self.project/'runtime'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(source)
        self.card=json.loads((self.stage/binding.CARD).read_bytes())
        self.profile=json.loads((self.stage/binding.PROFILE).read_bytes())
        self.profile['hard_GPUh']=18.
        atomic_json(self.stage/binding.PROFILE,self.profile)
        self.reg=dict(host='two_card',stage=str(self.stage),source_revision='b'*40,container_image=binding.IMAGE,
            payload_sha256={n:sha(self.stage/n) for n in binding.REQUIRED},
            runtime_source_sha256={'CPU.py':sha(self.project/'runtime/CPU.py')})
        self.authority=dict(run_id=binding.RUN_ID,stage=str(self.stage),launch_id='a'*32,host='two_card',gpu_uuid=binding.GPU,
            source_revision='b'*40,scope_sha256=self.card['scope_sha256'],billed_limit_GPUh=18.,
            CPU_fixture_only=False,execution_authorized=True,authorizes_replay=False,card_kind=binding.KIND,
            authorization_basis='DIRECT_USER_SINGLE_CARD',user_quote='EXPLICIT LOCAL METADATA FIXTURE, NOT REAL USER AUTHORITY',
            execution_host_policy_sha256=POLICY_SHA256,semantic_positions=146,physical_generation_upper=142)
        fields=('complete_algorithm_reused_source_bound','actual_host_FIT_broker_reused_source_bound',
            'guardian_FIT_cleanup_reused_source_bound','production_total_entry_CPU_accepted',
            'released_full146_reader_and_new32_scores_CPU_accepted')
        self.proof=dict(schema='CARA_V1_P1_WHOLE_CPU_COMPOSED_R1',whole_card_CPU_accepted=True,host='two_card',
            scope_sha256=self.card['scope_sha256'],payload_sha256=self.reg['payload_sha256'],
            runtime_source_sha256=self.reg['runtime_source_sha256'],execution_host_policy_sha256=POLICY_SHA256,
            supplemental_runtime_sha256=self.extra['files'],
            **{k:True for k in fields})
        names=('source_parent_requests','shadow_dense_compute','shadow_state_capture_hash_restore','fresh_baselines',
            'candidate_FIT','selected_candidate_CHECK','search_FIT','selected_search_CHECK','warm_and_controls',
            'internal_FIT_CPU_held_allocation','internal_container_startup','model_load_admission_stop_release','variation_margin')
        costs={name:1800. for name in names}
        self.quote=dict(schema='CARA_V1_P1_WHOLE_ACCEPTED_QUOTE_R1',whole_quote_accepted=True,scope_sha256=self.card['scope_sha256'],
            host='two_card',components_seconds=costs,forecast_GPUh=sum(costs.values())/3600,snapshot_cost_basis_accepted=True,
            evidence_refs=['EXPLICIT CPU METADATA FIXTURE ONLY'],
            fair_search_query_bounds=dict(path_seconds=360.,FIT_score_seconds=600.,overhead_seconds=30.),
            **{k:self.profile[k] for k in ('hard_GPUh','semantic_positions','physical_generation_upper','physical_model_pairs_upper',
                'internal_FIT_queries_upper','internal_FIT_metric_pairs_upper','postrelease_new_metric_pairs_upper')})
        self.guardian={k:self.authority[k] for k in binding.IDENTITY}
        self.guardian.update(started_monotonic=100.,original_handles=dict(guardian={'CPU_METADATA_ONLY':True}))
        self.output=self.project/'outputs'/binding.RUN_ID
        self.queue=self.output/'internal-FIT-queue'
        self.queue.mkdir(parents=True)
        self.storage=SimpleNamespace(output=self.output,check=lambda:None,
            config=dict(image_bytes=64*2**30,journal_bytes=48*2**20,minimum_output_free_bytes=8*2**30,
                        minimum_host_free_bytes=16*2**30,minimum_free_inodes=8192))
        self.write()

    def write(self):
        atomic_json(self.stage/'registration.json',self.reg)
        atomic_json(self.stage/'execution-CPU-proof.json',self.proof)
        atomic_json(self.stage/'whole-quote.json',self.quote)
        self.authority.update(CPU_proof_sha256=sha(self.stage/'execution-CPU-proof.json'),quote_sha256=sha(self.stage/'whole-quote.json'))
        atomic_json(self.stage/'GPU-authorization.json',self.authority)
        atomic_json(self.stage/'fresh-admission.json',dict(CPU_metadata_fixture=True))
        self.launch={k:self.authority[k] for k in binding.IDENTITY}
        self.launch.update(CPU_fixture_only=False,guardian_identity=self.guardian['original_handles']['guardian'],
            registration_sha256=sha(self.stage/'registration.json'),authorization_sha256=sha(self.stage/'GPU-authorization.json'),
            admission_sha256=sha(self.stage/'fresh-admission.json'))
        job={k:self.launch[k] for k in binding.JOB_IDENTITY}
        job.update(job_id=binding.RUN_ID,status='RESERVED_OR_RUNNING')
        atomic_json(self.stage/'central-reservation.json',dict(central_ledger_host='four_card',new_reservation=True,job=job))
        self.launch['central_reservation_sha256']=sha(self.stage/'central-reservation.json')
        atomic_json(self.stage/'GPU-launch.json',self.launch)
        atomic_json(self.stage/'guardian.json',self.guardian)
        context={k:self.launch[k] for k in binding.IDENTITY}
        context.update(CPU_fixture_only=False,phase='SOURCE_LIFECYCLE_V1_P1',hard_GPUh=18.,guardian_started_monotonic=100.,
            launch_sha256=sha(self.stage/'GPU-launch.json'),registration_sha256=self.launch['registration_sha256'],
            admission_sha256=self.launch['admission_sha256'],
            model_precision_sha256=json.loads((self.stage/binding.PRECISION).read_bytes())['precision_sha256'])
        self.spec=dict(project=str(self.project),stage=str(self.stage),CPU_fixture_only=False,context=context,
            profile=self.card['profile'],artifact_root=str(self.output/'algorithm'),queue=str(self.queue),
            registration_sha256=sha(self.stage/'registration.json'),GPU_launch_sha256=sha(self.stage/'GPU-launch.json'),
            work_stop_monotonic=100.+18*3600-600,environment={},uid=os.getuid(),gid=os.getgid())
        atomic_json(self.queue/'binding.json',self.spec)
        atomic_json(self.queue/'service-start.json',dict(binding_sha256=digest(self.spec),identity={'CPU_SERVICE_ONLY':True}))


class P1ProductionEntryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.f=Fixture(self.temp.name)

    def test_whole146_context_and_queue_share_one_guardian_epoch(self):
        card,launch,profile,context,spec,quote=binding.validate(self.f.project,self.f.stage)
        self.assertEqual(context,spec['context'])
        self.assertEqual(context['guardian_started_monotonic'],100.)
        self.assertEqual((card['physical_paths_upper'],profile['physical_generation_upper']),(146,142))
        self.assertEqual(quote['postrelease_new_metric_pairs_upper'],32)

    def test_published_unset_hard_limit_cannot_pass_admission(self):
        draft=json.loads((ROOT/binding.PROFILE).read_bytes())
        self.assertIsNone(draft['hard_GPUh'])
        with self.assertRaisesRegex(ValueError,'frozen hard limit'):binding.validate_profile(draft,self.f.card['scope_sha256'])

    def test_old_card_standing_small_card_or_replay_are_not_p1_authority(self):
        for key,value in (('run_id','cara-read-write-M1-full14-r1-20261101'),
                ('card_kind','CARA_SOURCE_LIFECYCLE_P0_POINT20_FULL14'),
                ('authorization_basis','USER_STANDING_BELOW2_GPUH_MAINLINE'),('execution_authorized',False),
                ('authorizes_replay',True),('host','four_card')):
            old=self.f.authority[key];self.f.authority[key]=value;self.f.write()
            with self.subTest(key=key),self.assertRaises(ValueError):binding.validate_inputs(self.f.project,self.f.stage)
            self.f.authority[key]=old

    def test_every_new_glue_and_reused_component_gate_remains_required(self):
        for key in ('whole_card_CPU_accepted','complete_algorithm_reused_source_bound','actual_host_FIT_broker_reused_source_bound',
                'guardian_FIT_cleanup_reused_source_bound','production_total_entry_CPU_accepted','released_full146_reader_and_new32_scores_CPU_accepted'):
            self.f.proof[key]=False;self.f.write()
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'CPU'):binding.validate_inputs(self.f.project,self.f.stage)
            self.f.proof[key]=True

    def test_complete_held_cpu_snapshot_and_release_costs_cannot_be_omitted(self):
        for key in ('shadow_state_capture_hash_restore','internal_FIT_CPU_held_allocation','model_load_admission_stop_release'):
            original=self.f.quote['components_seconds'].pop(key);self.f.write()
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'quote'):binding.validate_inputs(self.f.project,self.f.stage)
            self.f.quote['components_seconds'][key]=original
        self.f.quote['snapshot_cost_basis_accepted']=False;self.f.write()
        with self.assertRaisesRegex(ValueError,'quote'):binding.validate_inputs(self.f.project,self.f.stage)

    def test_changed_source_runtime_or_admission_is_refused(self):
        for path in (self.f.stage/binding.RUNNER,self.f.project/'runtime/CPU.py',
                     self.f.project/'runtime/packages/cosmos-oss/cosmos_oss/init.py',self.f.stage/'fresh-admission.json'):
            raw=path.read_bytes();path.write_bytes(raw+b' ')
            with self.subTest(path=path.name),self.assertRaises(ValueError):binding.validate(self.f.project,self.f.stage)
            path.write_bytes(raw)

    def test_other_guardian_epoch_or_partial_queue_binding_is_refused(self):
        for key,value in (('guardian_started_monotonic',101.),('scope_sha256','e'*64),('model_precision_sha256','f'*64)):
            changed=copy.deepcopy(self.f.spec);changed['context'][key]=value
            atomic_json(self.f.queue/'binding.json',changed)
            with self.subTest(key=key),self.assertRaises(ValueError):binding.validate(self.f.project,self.f.stage)

    def test_total_cli_rejects_invalid_handoff_before_cuda_or_model_load(self):
        values=binding.validate(self.f.project,self.f.stage)
        with patch.object(sys,'argv',['entry','--project',str(self.f.project),'--stage',str(self.f.stage),
                '--source-revision','b'*40,'--gpu-uuid',binding.GPU]), \
                patch.dict(os.environ,CUDA_VISIBLE_DEVICES=binding.GPU), \
                patch.object(binding,'validate',return_value=values), \
                patch.object(storage_module,'storage_for',return_value=self.f.storage), \
                patch('run_cara_budget_calibration_r1.validate_runner_handoff',side_effect=ValueError('CPU invalid original handoff')), \
                patch('wcomr.wc73_exclusive_r1.runner_context_gate',side_effect=AssertionError('CUDA before accepted original handoff')):
            with self.assertRaisesRegex(ValueError,'invalid original handoff'):entry.main()
        self.assertFalse((self.f.output/'P1-model-runner-intent.json').exists())


if __name__=='__main__':unittest.main()
