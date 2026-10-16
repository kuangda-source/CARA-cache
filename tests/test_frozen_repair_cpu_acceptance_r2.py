"""Same-source CPU envelope/authority controls; all process records are synthetic."""
import copy
import importlib.util
from pathlib import Path
import unittest

from wcomr import frozen_repair180_r2 as repair
from wcomr.frozen_repair_cpu_acceptance_r2 import (
    PATTERNS,BUNDLE_WORKER,WORKER,CPU_BUNDLE_STATUS,validate_bundle,validate_proof,accept)
from wcomr.frozen_repair_entry_r2 import ENTRIES,validate_all_entries
from wcomr.frozen_shared_execution_r1 import point

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    path=Path(__file__).with_name('test_frozen_repair180_r2.py')
    spec=importlib.util.spec_from_file_location('repair_scope_fixture',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    config,old,bound=module.fixture()
    numeric=repair.original.sampling_source_closure(ROOT)
    rp=repair.validate_repair_proof(ROOT,config)
    names=set(numeric)|set(rp['source_sha256'])|{p for p,_ in ENTRIES.values()}|{WORKER,BUNDLE_WORKER}|{'tests/'+p for p in PATTERNS}
    payload={n:repair.sha(ROOT/n) for n in names}
    registration=dict(source_revision='SYNTHETIC_METADATA_NOT_DEPLOYED',payload_sha256=payload)
    proof=dict(status=repair.PRODUCTION_CPU_STATUS,exit_code=0,source_revision=registration['source_revision'],
        registration_sha256='a'*64,config_sha256=repair.sha(ROOT/repair.CONFIG),bound_input_fingerprint=repair.fingerprint(bound),
        scope_counts=config['scope_counts'],matrix=repair.validate_contract(config,bound),actual_sample_argument_variants=160,
        runner_source_sha256=payload[WORKER],CUDA_initialized=False,GPU_submissions=0,model_weights_loaded=0,ledger_written=False,
        native_forward_identity=dict(qualified_name='cosmos_predict2._src.predict2.networks.minimal_v1_lvg_dit.MinimalV1LVGDiT.forward',sha256='b'*64),
        guardrail_checks=[dict(case_id=c['id'],seed=c['seed'],method=m,unguarded_execution_refused=True)
            for c in bound['cases'][:2] for m in bound['method_ids'] if point(m)['family'] in ('NATIVE','FIXED26')],
        unchanged_numeric_CPU_reuse=dict(status='ACCEPTED_FULL952_NUMERICAL_DEPENDENCIES_REUSED',checked_source_files=len(numeric),
            source_sha256=numeric,request_boundary_repair=rp,metadata_entry_derivations=validate_all_entries(ROOT)))
    return config,bound,registration,proof


def bundle_fixture(registration):
    python='/synthetic/python';stage='/synthetic/project/.sync/stage';project='/synthetic/project'
    commands=[[python,'-m','unittest','discover','-s',stage+'/tests','-p',p,'-v'] for p in PATTERNS]
    commands.append([python,stage+'/'+WORKER,'--project',project,'--stage',stage,'--cpu-check'])
    return dict(status=CPU_BUNDLE_STATUS,exit_code=0,stage=stage,project=project,python_executable=python,
        source_revision=registration['source_revision'],commands=[dict(command=c,exit_code=0) for c in commands],
        control_source_sha256={n:registration['payload_sha256'][n] for n in [BUNDLE_WORKER]+['tests/'+n for n in PATTERNS]},
        GPU_submissions=0,model_weights_loaded=0,ledger_written=False,shared_runtime_written=False,original_base_stage_written=False)


class RepairCPUControls(unittest.TestCase):
    def test_complete_original_repair_proof_and_eight_guard_checks(self):
        config,bound,reg,proof=fixture()
        self.assertEqual(len(proof['guardrail_checks']),8)
        validate_proof(proof,config,bound,reg,registration_sha256='a'*64,config_sha256=proof['config_sha256'])
        for field in ('guardrail_checks','actual_sample_argument_variants'):
            bad=copy.deepcopy(proof);bad[field]=bad[field][:-1] if field=='guardrail_checks' else 159
            with self.subTest(field=field),self.assertRaises(ValueError):
                validate_proof(bad,config,bound,reg,registration_sha256='a'*64,config_sha256=proof['config_sha256'])

    def test_stage_entry_numerical_or_repair_source_changes_refuse_acceptance(self):
        config,bound,reg,proof=fixture()
        variants=[]
        p=copy.deepcopy(proof);p['runner_source_sha256']='0'*64;variants.append(p)
        p=copy.deepcopy(proof);p['unchanged_numeric_CPU_reuse']['checked_source_files']=98;variants.append(p)
        p=copy.deepcopy(proof);p['unchanged_numeric_CPU_reuse']['request_boundary_repair']['successful_CPU_paths']=519;variants.append(p)
        p=copy.deepcopy(proof);p['unchanged_numeric_CPU_reuse']['metadata_entry_derivations']['worker']['original_stage_or_script_written']=True;variants.append(p)
        for bad in variants:
            with self.assertRaises(ValueError):validate_proof(bad,config,bound,reg,registration_sha256='a'*64,config_sha256=proof['config_sha256'])

    def test_all_nine_CPU_commands_source_and_actual_entry_are_required(self):
        _,_,reg,_=fixture();bundle=bundle_fixture(reg)
        self.assertEqual(len(bundle['commands']),9);validate_bundle(bundle,reg['source_revision'],payload=reg['payload_sha256'])
        for index in (0,7,8):
            bad=copy.deepcopy(bundle);bad['commands'][index]['exit_code']=1
            with self.assertRaises(ValueError):validate_bundle(bad,reg['source_revision'],payload=reg['payload_sha256'])

    def test_original_once_capture_accepts_only_the_complete_terminal_CPU(self):
        config,bound,reg,proof=fixture();bundle=bundle_fixture(reg)
        launch=dict(source_revision=reg['source_revision'],registration_sha256='a'*64,
            identity=dict(pid=101,start_ticks=200),first_collection_not_before_unix=1000,
            stage=bundle['stage'])
        capture=dict(status='N07_REPAIR_PRODUCTION_CPU_ORIGINAL_ONCE_CAPTURE',launch=launch,
            registration=reg,registration_sha256='a'*64,observed_unix=1001,
            payload_verified={n:True for n in reg['payload_sha256']},
            process=dict(pid=101,start_ticks=None,state=None),GPU_submissions=0,ledger_written=False,
            files=dict(bundle=dict(exists=True,data=bundle,sha256='1'*64),
                proof=dict(exists=True,data=proof,sha256='2'*64),
                config=dict(exists=True,data=config,sha256=proof['config_sha256']),
                bound_inputs=dict(exists=True,data=bound,sha256=config['references']['bound_inputs']['sha256'])))
        result=accept(capture);self.assertTrue(result['CPU_accepted']);self.assertEqual(result['CPU_commands'],9)
        self.assertFalse(result['whole_GPU_card_selected']);self.assertEqual(result['guardrail_refusal_checks'],8)
        active=copy.deepcopy(capture);active['process']=dict(pid=101,start_ticks=200,state='S')
        self.assertIn('STILL_RUNNING',accept(active)['status'])
        failed=copy.deepcopy(capture);failed['files']['bundle']['data']['exit_code']=1
        self.assertIn('FAILED_RETAINED',accept(failed)['status'])
        missing=copy.deepcopy(capture);missing['files']['proof']['exists']=False
        self.assertIn('MISSING_RESULTS',accept(missing)['status'])
        early=copy.deepcopy(capture);early['observed_unix']=999
        with self.assertRaises(ValueError):accept(early)
        bad=copy.deepcopy(capture);bad['files']['bundle']['data']['project']='/another/project'
        with self.assertRaises(ValueError):accept(bad)
        bad=copy.deepcopy(capture);bad['launch']['project']='/another/project'
        with self.assertRaises(ValueError):accept(bad)

    def test_original_card_approval_and_standing_under12_do_not_authorize_retry(self):
        config,bound,reg,proof=fixture();kwargs=dict(revision=reg['source_revision'],gpu_uuid='GPU-SYNTHETIC',
            config_sha256=proof['config_sha256'],proof_sha256='c'*64,registration_sha256='a'*64)
        authority=dict(source_revision=reg['source_revision'],config_sha256=proof['config_sha256'],production_CPU_sha256='c'*64,
            bound_input_fingerprint=repair.fingerprint(bound),scope_counts=config['scope_counts'],whole_card_run=repair.RUN,
            gpu_uuid='GPU-SYNTHETIC',forecast_complete_GPUh=config['forecast_complete_GPUh'],billed_limit_GPUh=config['billed_limit_GPUh'],
            cumulative_cap_GPUh=config['cumulative_cap_GPUh'],budget_origin_used_GPUh=config['budget_origin_used_GPUh'],
            direct_user_authorization=True,user_reply_quote='SYNTHETIC NEGATIVE CONTROL, NOT A HUMAN GPU APPROVAL',
            launch_id='SYNTHETIC_NO_DISPATCH',kind='SPECIFIC_WHOLE_CARD_APPROVAL')
        repair.validate_launch_authority(config,bound,reg,proof,authority,**kwargs)
        for changes in (dict(whole_card_run=repair.original.RUN),dict(kind='STANDING_STRICT_UNDER12'),dict(direct_user_authorization=False)):
            with self.assertRaises(ValueError):repair.validate_launch_authority(config,bound,reg,proof,{**authority,**changes},**kwargs)


if __name__=='__main__':unittest.main()
