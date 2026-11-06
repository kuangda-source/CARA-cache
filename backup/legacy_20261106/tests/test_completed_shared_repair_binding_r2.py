"""Complete synthetic N07 receipts for downstream identity tests, never GPU data."""
import copy
from functools import lru_cache
import gzip
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from repair_gpu_fixture_r2 import fixture as complete_fixture, load
from wcomr.completed_shared_repair_binding_r2 import accepted_repair_identity
from wcomr.frozen_repair_acceptance_r2 import accept
from wcomr import frozen_shared_production_r1 as original
from wcomr import runtime_profile40_production_r1 as profile
from wcomr.immutable_stage_payload_r1 import local_python_closure

ROOT=Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def original_fixture():
    capture,launch=complete_fixture()
    from wcomr.frozen_shared_post_r1 import summarize
    capture['final'].update(summarize(copy.deepcopy(capture['final']),capture['bound_inputs'],
        observed_paths=180,child_exit_code=0,bootstrap_repetitions=4096))
    accepted=accept(capture,launch)
    accepted['capture_sha256']='e'*64
    shared=json.loads((ROOT/original.CONFIG).read_text())
    args=dict(capture_sha256=accepted['capture_sha256'],original_shared_config=shared,
        original_shared_config_sha256=original.sha(ROOT/original.CONFIG))
    return accepted,capture,args


def fixture():
    return copy.deepcopy(original_fixture())


def deploy_module():
    name=ROOT/'scripts/deploy_wc_paper_N08_production_cpu_r1.py'
    spec=importlib.util.spec_from_file_location('local_repaired_N08_deployer',name)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class CompletedRepairBindingControls(unittest.TestCase):
    def test_full180_actual_repair_identity_and_original_methods_remain_distinct(self):
        accepted,capture,args=fixture();before=copy.deepcopy((accepted,capture,args))
        result=accepted_repair_identity(accepted,capture,**args)
        self.assertEqual((accepted,capture,args),before)
        self.assertEqual(result['actual_run_id'],capture['launch']['run_id'])
        self.assertNotEqual(result['actual_config_sha256'],result['original_method_config_sha256'])
        self.assertEqual(result['original_runner_paths'],180)
        self.assertFalse(result['original_identity_relabelled'])
        self.assertTrue(result['no_new_GPU_permission'])
        self.assertNotIn('grouped_statistics',result)

    def test_foreign_source_capture_config_scope_or_context_cannot_be_substituted(self):
        accepted,capture,args=fixture()
        for kind in ('run','source','capture','config','accepted_run','method_context','scope','reference'):
            a,c,k=copy.deepcopy((accepted,capture,args))
            if kind=='run':c['launch']['run_id']=original.RUN
            elif kind=='source':a['source_revision']='SYNTHETIC_FOREIGN'
            elif kind=='capture':k['capture_sha256']='0'*64
            elif kind=='config':c['config_sha256']='0'*64
            elif kind=='accepted_run':a.pop('repair_run_id')
            elif kind=='method_context':k['original_shared_config']['method_ids'].pop()
            elif kind=='scope':c['config']['scope_counts']['total_paths']=179
            else:c['config']['references']['original_configuration']['ref']='other.json'
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                accepted_repair_identity(a,c,**k)

    def test_saved_success_live_process_missing_post_or_wrong_guard_proof_never_suffices(self):
        accepted,capture,args=fixture()
        for kind in ('saved_success','still_running','missing_post','CPU_only','guard'):
            a,c,k=copy.deepcopy((accepted,capture,args))
            if kind=='saved_success':a['actual_GPUh']=123.
            elif kind=='still_running':
                own=c['launch']['supervisor_identity']
                c['original_processes']['supervisor_pid']={**own,'state':'S'}
            elif kind=='missing_post':c.pop('post_exit')
            elif kind=='CPU_only':c['production_CPU']['status']='CPU_PREPARATION_ONLY'
            else:c['production_CPU']['guardrail_checks'].pop()
            with self.subTest(kind=kind),self.assertRaises(ValueError):
                accepted_repair_identity(a,c,**k)

    def test_registered_text_rejections_keep180_denominator_and_allow_accepted_available_cohorts(self):
        _,capture,args=fixture();case=capture['bound_inputs']['cases'][-1]['id']
        for row in capture['runner']['runs']:
            if row['section']=='TIMED' and row['case_id']==case:
                row.update(status='TEXT_REJECTED',solver_steps=0,guided_pairs=0)
                for key in ('final_artifact','video_path','warm_guided_artifact'):
                    row.pop(key,None)
        post=load('test_frozen_shared_post_r1')
        final=post.evaluate(capture['bound_inputs'],capture['runner']['matrix'],capture['runner']['runs'])
        final['artifact_inventory']=[dict(path=a['path'],bytes=a['bytes'],sha256=a['sha256'])
            for row in final['rows'] for key in ('final_artifact','warm_guided_artifact','video_artifact')
            if (a:=row.get(key)) is not None]
        for key in ('source_revision','config_sha256','bound_input_fingerprint','scope_counts',
                    'GPU_supervisor','CUDA_initialized'):
            final[key]=copy.deepcopy(capture['final'][key])
        from wcomr.frozen_shared_post_r1 import summarize
        final.update(summarize(copy.deepcopy(final),capture['bound_inputs'],observed_paths=180,
            child_exit_code=0,bootstrap_repetitions=4096));capture['final']=final
        accepted=accept(capture,capture['launch']);accepted['capture_sha256']=args['capture_sha256']
        result=accepted_repair_identity(accepted,capture,**args)
        self.assertEqual(result['original_runner_paths'],180)
        self.assertEqual(result['original_status_counts']['TEXT_REJECTED'],10)
        self.assertFalse(accepted['scientific_full_scope_accepted'])
        self.assertTrue(accepted['scientific_available_cohorts_with_registered_missingness'])

    def test_N08_actual_completion_entry_binds_repair_without_any_network(self):
        accepted,capture,args=fixture();module=deploy_module()
        with patch.object(module.subprocess,'run') as network:
            result=module.accepted_common_identity(accepted,capture,
                capture_sha256=args['capture_sha256'],shared_config_sha256=args['original_shared_config_sha256'],
                shared_config=args['original_shared_config'])
        network.assert_not_called();self.assertEqual(result['actual_source_revision'],capture['launch']['source_revision'])
        with self.assertRaisesRegex(ValueError,'original shared method context'):
            module.accepted_common_identity(accepted,capture,
                capture_sha256=args['capture_sha256'],shared_config_sha256=args['original_shared_config_sha256'])

    def test_N09_actual_contract_recomputes_repair_and_retains_N08_independent_gate(self):
        from test_runtime_profile40_production_r1 import stage_fixture
        accepted,capture,args=fixture()
        with tempfile.TemporaryDirectory() as directory:
            stage=Path(directory);config,bound,_=stage_fixture(stage);refs=config['references']
            shared=args['original_shared_config'];freeze_ref=shared['references']['method_freeze']
            for ref in (dict(ref=original.CONFIG,sha256=args['original_shared_config_sha256']),freeze_ref):
                path=stage/ref['ref'];path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes((ROOT/ref['ref']).read_bytes())
            refs['shared_config']=dict(ref=original.CONFIG,sha256=args['original_shared_config_sha256'])
            refs['method_freeze']=freeze_ref
            freeze=json.loads((stage/freeze_ref['ref']).read_text())
            def store(role,value,compressed=False):
                path=stage/refs[role]['ref'];raw=json.dumps(value).encode()
                path.write_bytes(gzip.compress(raw) if compressed else raw)
                refs[role]['sha256']=original.sha(path)
            store('N07_capture',capture,True);accepted['capture_sha256']=refs['N07_capture']['sha256']
            store('N07_acceptance',accepted)
            c8=json.loads(gzip.decompress((stage/refs['N08_capture']['ref']).read_bytes()))
            c8.update(shared_config=shared,shared_config_sha256=refs['shared_config']['sha256'],method_freeze=freeze)
            store('N08_capture',c8,True)
            a8=json.loads((stage/refs['N08_acceptance']['ref']).read_text())
            (stage/profile.CONFIG).write_text(json.dumps(config))
            with patch('wcomr.balanced_repeat_acceptance_r1.accept',return_value=a8) as n8:
                actual=profile.referenced_contract(stage)
            n8.assert_called_once();self.assertEqual(actual[2],bound)
            self.assertEqual(actual[3]['completed_N07_repair']['actual_run_id'],capture['launch']['run_id'])
            with patch('wcomr.balanced_repeat_acceptance_r1.accept',return_value={**a8,'actual_GPUh':123.}):
                with self.assertRaisesRegex(ValueError,'Recompute'):
                    profile.referenced_contract(stage)

    def test_both_actual_deployment_source_closures_include_repaired_full_acceptance(self):
        files=local_python_closure(ROOT,[
            'scripts/deploy_wc_paper_N08_production_cpu_r1.py',
            'scripts/deploy_wc_paper_N09_production_cpu_r1.py'])
        for name in ('completed_shared_repair_binding_r2','frozen_repair_acceptance_r2',
                     'frozen_repair_cpu_acceptance_r2','runtime_profile40_production_r1'):
            self.assertIn('src/wcomr/'+name+'.py',files)


if __name__=='__main__':unittest.main()
