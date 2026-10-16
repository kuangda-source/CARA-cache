"""Real temporary UUID locks/v2 accounting with synthetic GPU/child/CPU proofs.

No original model, generation video, SSH, actual GPU or real budget is used.
"""
from contextlib import ExitStack
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_N10_production_entry_r1 import fixture
from wcomr import automatic_quality_production_r1 as P
from wcomr.automatic_quality_models_r1 import sha
from wcomr.gpu_budget_pool_v2 import BudgetPool, DeviceLease, SCHEMA, atomic_json

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('N10_supervisor_under_test',ROOT/'scripts/supervise_wc_paper_N10_full960_r1.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
UUID='GPU-explicit-synthetic-test-only'


def setup(root,limit=3.):
    root=root.resolve();stage=root/'stage';stage.mkdir();(root/'outputs').mkdir()
    values=fixture();config,registration,inputs=values[:3];bundle=inputs['input_bundle']
    config['billed_limit_GPUh']=limit
    def write(name,value):
        p=stage/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value));return p
    cfg=write(P.CONFIG,config);reg=write('registration.json',registration)
    worker=stage/'scripts/score_wc_paper_N10_full960_r1.py';worker.parent.mkdir()
    worker.write_bytes((ROOT/'scripts/score_wc_paper_N10_full960_r1.py').read_bytes())
    proof=dict(status=P.CPU_STATUS,exit_code=0,source_revision=registration['source_revision'],
        registration_sha256=sha(reg),config_sha256=sha(cfg),runner_source_sha256=sha(worker),
        input_bundle_fingerprint=bundle['fingerprint'],scope_counts=config['scope_counts'],metric_positions=960,
        neural_framework_imported=False,GPU_submissions=0,ledger_written=False)
    proofpath=write('CPU-scoring-entry-result.json',proof)
    authority=dict(kind='STANDING_STRICT_UNDER12' if limit<12 else 'SPECIFIC_WHOLE_CARD_APPROVAL',
        direct_user_authorization=True,user_reply_quote='SYNTHETIC_TEST_AUTHORITY_NOT_REAL_USER_APPROVAL',
        launch_id='SYNTHETIC_ORIGINAL_N10_LAUNCH',source_revision=registration['source_revision'],
        config_sha256=sha(cfg),production_CPU_sha256=sha(proofpath),bound_input_fingerprint=bundle['fingerprint'],
        scope_counts=config['scope_counts'],whole_card_run=config['run_id'],gpu_uuid=UUID,
        forecast_complete_GPUh=config['forecast_GPUh'],billed_limit_GPUh=limit,
        cumulative_cap_GPUh=config['cumulative_cap_GPUh'],budget_origin_used_GPUh=config['budget_origin_used_GPUh'])
    write('N10-launch-authorization.json',authority)
    write('N10-production-CPU-launch.json',dict(source_revision=registration['source_revision'],
        registration_sha256=sha(reg),identity=dict(pid=101,start_ticks=999)))
    write('N10-production-CPU-exit.json',dict(exit_code=0))
    pool=BudgetPool(root)
    value=dict(schema=SCHEMA,cap_gpu_hours=113.,origin_used_gpu_hours=config['budget_origin_used_GPUh'],
        origin_gpu_jobs_launched=0,jobs={},events=[])
    value.update(pool.accounting(value));atomic_json(pool.path,value)
    return stage,values,proof,authority,pool


class FakeChild:
    pid=333
    def poll(self):return 0
    def wait(self,timeout=None):return 0


class ScoringSupervisorControls(unittest.TestCase):
    def context(self,root,stage,values):
        stack=ExitStack();config,reg,bound,accepted,cpureg,resources=values
        stack.enter_context(patch.object(P,'load',return_value=(config,reg,bound['input_bundle'],accepted,cpureg,resources)))
        stack.enter_context(patch('wcomr.gpu_budget_pool_v2.same_live_process',return_value=False))
        stack.enter_context(patch('wcomr.gpu_budget_pool_v2.process_identity',side_effect=lambda pid:dict(pid=pid,start_ticks=555,state='S')))
        stack.enter_context(patch.object(S,'observe',return_value=dict(uuid=UUID,name='NVIDIA RTX A6000',
            memory_used_mib=24,compute_cap='8.6',pids=[])))
        stack.enter_context(patch.object(S.signal,'signal'))
        stack.enter_context(patch.object(S.time,'monotonic',side_effect=[100.,280.]))
        return stack

    def test_original_whole_scope_single_child_actual_wall_settles_additively_and_releases_lease(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();stage,values,proof,authority,pool=setup(root)
            with self.context(root,stage,values),patch.object(S.subprocess,'Popen',return_value=FakeChild()) as launch:
                result=S.run(root,stage,'1'*40,UUID)
            self.assertEqual(launch.call_count,1);self.assertEqual(result['actual_GPUh'],.05)
            final=pool.read();self.assertEqual(final['reserved_gpu_hours'],0.)
            self.assertAlmostEqual(final['used_gpu_hours'],values[0]['budget_origin_used_GPUh']+.05)
            self.assertEqual(final['jobs'][values[0]['run_id']]['scope_counts']['metric_positions'],960)
            self.assertFalse(result['generation_latency_claim']);self.assertEqual(result['child_exit_code'],0)
            env=launch.call_args.kwargs['env'];self.assertEqual(env['CUDA_VISIBLE_DEVICES'],UUID)
            with DeviceLease(root,UUID):pass

    def test_child_spawn_failure_keeps_original_full_scope_bill_and_no_second_child(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();stage,values,*_=setup(root)
            with self.context(root,stage,values),patch.object(S.subprocess,'Popen',side_effect=OSError('SYNTHETIC_SPAWN_FAILURE')) as launch:
                with self.assertRaisesRegex(OSError,'SYNTHETIC'):S.run(root,stage,'1'*40,UUID)
            final=BudgetPool(root).read();self.assertEqual(launch.call_count,1)
            self.assertEqual(final['reserved_gpu_hours'],0.);self.assertEqual(len(final['jobs']),1)
            self.assertEqual(final['jobs'][values[0]['run_id']]['status'],'SETTLED')
            self.assertTrue((root/'outputs'/values[0]['run_id']/'billing.json').is_file())
            with DeviceLease(root,UUID):pass

    def test_wrong_production_proof_or_changed_whole_price_stops_before_GPU_query(self):
        for mode in ('source','worker','price','threshold'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                root=Path(folder).resolve();stage,values,proof,authority,pool=setup(root)
                if mode=='source':proof['source_revision']='0'*40
                elif mode=='worker':proof['runner_source_sha256']='0'*64
                elif mode=='price':authority['forecast_complete_GPUh']=.01
                else:values[0]['billed_limit_GPUh']=12.;authority['billed_limit_GPUh']=12.
                (stage/'CPU-scoring-entry-result.json').write_text(json.dumps(proof))
                (stage/'N10-launch-authorization.json').write_text(json.dumps(authority))
                with self.context(root,stage,values),patch.object(S,'observe') as observe:
                    with self.assertRaises(ValueError):S.run(root,stage,'1'*40,UUID)
                    observe.assert_not_called()
                self.assertFalse(pool.read()['jobs'])

    def test_other_mainline_reservation_and_original_CPU_liveness_are_not_overwritten(self):
        for mode in ('mainline','CPU_live'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                root=Path(folder).resolve();stage,values,*_=setup(root);pool=BudgetPool(root)
                if mode=='mainline':
                    value=pool.read();value['jobs']['ORIGINAL_MAINLINE']=dict(status='RESERVED_OR_RUNNING',billed_limit_GPUh=1.,gpu_uuid='GPU-mainline')
                    value.update(pool.accounting(value));atomic_json(pool.path,value)
                with self.context(root,stage,values),patch.object(S,'observe') as observe:
                    with patch('wcomr.gpu_budget_pool_v2.same_live_process',return_value=mode=='CPU_live'):
                        with self.assertRaises(ValueError):S.run(root,stage,'1'*40,UUID)
                    observe.assert_not_called()
                self.assertNotIn(values[0]['run_id'],pool.read()['jobs'])

    def test_specific_complete12_card_uses_existing_approved_pool_without_new_budget_window(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();stage,values,*_=setup(root,limit=12.)
            with self.context(root,stage,values),patch.object(S.subprocess,'Popen',return_value=FakeChild()):
                result=S.run(root,stage,'1'*40,UUID)
            value=BudgetPool(root).read();job=value['jobs'][values[0]['run_id']]
            self.assertEqual(job['kind'],'V2_SPECIFIC_WHOLE_CARD_APPROVAL')
            self.assertEqual(value['cap_gpu_hours'],113.)
            self.assertEqual(value['origin_used_gpu_hours'],values[0]['budget_origin_used_GPUh'])
            self.assertEqual(result['scope_counts']['metric_positions'],960)


if __name__=='__main__':unittest.main()
