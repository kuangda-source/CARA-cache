"""N09 production contract with synthetic prior-run proofs and physical loader.

The four original observer/numerical source bytes are real local files. Prior
GPU acceptances, runtime loading, proposed prices and authorizations are doubles.
"""
import copy
from contextlib import ExitStack
import gzip
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from test_runtime_profile40_execution_r1 import fixture as execution_fixture
from wcomr import frozen_shared_production_r1 as shared_module
from wcomr import runtime_profile40_production_r1 as P
from wcomr.frozen_shared_production_r1 import fingerprint,sha

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    scope,protocol,freeze,bound,_=execution_fixture()
    shared=dict(method_ids=freeze['method_ids'],cumulative_cap_GPUh=113.,
        budget_origin_used_GPUh=79.99637737158223,references={})
    config=dict(card=P.CARD,run_id=P.RUN,scope_counts=copy.deepcopy(P.COUNTS),
        main_timing='SYNCHRONIZED_TEXT_ENCODING_DENOISING_VAE_DECODING',
        strategy='WORKING_P_AGE_NONZERO_REBASE',memory_policy='REQUEST_BOUNDARY_GC_ONLY',
        deployment_profiling=True,guardrails_enabled=True,clean_repeated_latency_claim=False,
        autonomy_exclusive_upper_GPUh=12,training=False,online_teachers=False,F_B_enabled=False,
        P_ACR=False,T1=False,head_elision=False,bound_profile_fingerprint=fingerprint(bound),
        forecast_complete_GPUh=4.1,billed_limit_GPUh=4.5,cumulative_cap_GPUh=113.,
        budget_origin_used_GPUh=shared['budget_origin_used_GPUh'])
    return config,scope,protocol,freeze,shared,bound


def stage_fixture(stage):
    stage=stage.resolve();config,scope,protocol,freeze,shared,bound=fixture();refs={}
    def put(name,ref,value,compressed=False):
        path=stage/ref;path.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(value).encode();path.write_bytes(gzip.compress(raw) if compressed else raw)
        refs[name]=dict(ref=ref,sha256=sha(path));return path
    put('method_freeze','freeze.json',freeze)
    shared['references']['method_freeze']=refs['method_freeze']
    put('shared_config',shared_module.CONFIG,shared)
    put('runtime_scope','scope.json',scope);put('timing_protocol','protocol.json',protocol)
    source={}
    for name in P.PROFILE_SOURCES:
        target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
        source[name]=sha(target)
    capture=dict(launch=dict(source_revision='SYNTHETIC_ORIGINAL102_PROOF'),payload_actual_sha256=source)
    put('profile_CPU_capture','original102.json.gz',capture,compressed=True)
    accepted=dict(status='DEPLOYMENT_PROFILE_FULL102_CPU_INDEPENDENTLY_ACCEPTED_NOT_GPU_PROFILE',
        actual_CPU_paths=102,ordinary_pairs=3516,CFG_calls=7032,source_revision=capture['launch']['source_revision'],
        capture_sha256=refs['profile_CPU_capture']['sha256'])
    put('profile_CPU_acceptance','accepted102.json',accepted)
    put('N07_capture','original_N07.json.gz',dict(config_sha256=refs['shared_config']['sha256'],
        launch=dict(source_revision='SYNTHETIC_ORIGINAL_N07')),compressed=True)
    put('N08_capture','original_N08.json.gz',dict(shared_config_sha256=refs['shared_config']['sha256'],
        shared_config=shared,timing_protocol=protocol,method_freeze=freeze,
        launch=dict(source_revision='SYNTHETIC_ORIGINAL_N08')),compressed=True)
    put('N07_acceptance','accepted_N07.json',dict(terminal_receipt_audit_accepted=True,
        scientific_available_cohorts_with_registered_missingness=True,original_runner_paths=180,
        capture_sha256=refs['N07_capture']['sha256'],source_revision='SYNTHETIC_ORIGINAL_N07'))
    put('N08_acceptance','accepted_N08.json',dict(terminal_receipt_audit_accepted=True,
        full_raw_and_fidelity_scope_accepted=True,own_GPU_and_finance_released=True,
        original_runner_paths=40,original_CPU_post_exit_code=0,source_revision='SYNTHETIC_ORIGINAL_N08'))
    config['references']=refs;path=stage/P.CONFIG;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(config))
    registration=dict(source_revision='1'*40)
    returned=(shared,registration,{},None,{},None,dict(method_ids=freeze['method_ids']),
        dict(status='SYNTHETIC_UNCHANGED952_PHYSICAL_LOADER'))
    return config,bound,returned


def accepted_doubles(stage):
    stack=ExitStack()
    for name,module in [('N07','wcomr.frozen_shared_acceptance_r1'),('N08','wcomr.balanced_repeat_acceptance_r1')]:
        value=json.loads((stage/('accepted_'+name+'.json')).read_text())
        stack.enter_context(patch(module+'.accept',return_value=value))
    return stack


class RuntimeProfileProductionControls(unittest.TestCase):
    def test_original40_scope_contract_separate_from_clean_timing_and_original_budget(self):
        config,scope,protocol,freeze,shared,bound=fixture()
        self.assertEqual(P.validate_contract(config,scope,protocol,freeze,shared),bound)
        self.assertEqual(bound['scope_counts']['profiled_paths'],20)
        for field,value in [('clean_repeated_latency_claim',True),('head_elision',True),
                ('forecast_complete_GPUh',4.6),('budget_origin_used_GPUh',0.),('deployment_profiling',False)]:
            candidate=copy.deepcopy(config);candidate[field]=value
            with self.assertRaises(ValueError):P.validate_contract(candidate,scope,protocol,freeze,shared)

    def test_actual_loader_requires_all_prior_acceptances_and_exact_original_profile_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            stage=Path(folder);config,bound,returned=stage_fixture(stage)
            with accepted_doubles(stage),patch.object(shared_module,'validate',return_value=returned) as physical:
                observed=P.validate(stage,stage)
            self.assertEqual(observed[6],bound);self.assertEqual(observed[7]['original_full102_CPU_paths'],102)
            self.assertEqual(observed[7]['new_full102_paths_run'],0);self.assertEqual(physical.call_count,1)
            self.assertEqual(len(observed[7]['source_sha256']),4)

    def test_unaccepted_mainline_changed_reference_or_observer_fails_before_physical_loader(self):
        for mode in ('N07','N08','reference','source'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                stage=Path(folder);config,bound,returned=stage_fixture(stage)
                if mode in ('N07','N08'):
                    role=mode+'_acceptance';path=stage/config['references'][role]['ref'];value=json.loads(path.read_text())
                    value['terminal_receipt_audit_accepted']=False;path.write_text(json.dumps(value))
                    config['references'][role]['sha256']=sha(path);(stage/P.CONFIG).write_text(json.dumps(config))
                elif mode=='reference':(stage/'scope.json').write_text('{}')
                else:
                    path=stage/P.PROFILE_SOURCES[0];path.write_text(path.read_text()+'\n# SYNTHETIC_SOURCE_CHANGE\n')
                with accepted_doubles(stage),patch.object(shared_module,'validate',return_value=returned) as physical:
                    with self.assertRaises(ValueError):P.validate(stage,stage)
                    physical.assert_not_called()

    def test_source_CPU_whole_price_UUID_authority_and_exact12_gate(self):
        config,scope,protocol,freeze,shared,bound=fixture();registration=dict(source_revision='1'*40)
        proof=dict(source_revision='1'*40,status=P.CPU_STATUS,exit_code=0,registration_sha256='a'*64,
            config_sha256='b'*64,bound_profile_fingerprint=fingerprint(bound),scope_counts=P.COUNTS,
            CUDA_initialized=False,GPU_submissions=0,model_weights_loaded=0,ledger_written=False,
            actual_sample_argument_variants=10,matrix=bound['execution_plan'],
            guardrail_checks=[dict(scene=r['name'],unguarded_execution_refused=True) for r in bound['requests']])
        authority=dict(launch_id='SYNTHETIC_NOT_A_REAL_LAUNCH',direct_user_authorization=True,
            user_reply_quote='SYNTHETIC_AUTHORITY_NOT_REAL_HUMAN_APPROVAL',kind='STANDING_STRICT_UNDER12',
            source_revision='1'*40,config_sha256='b'*64,production_CPU_sha256='c'*64,
            bound_input_fingerprint=fingerprint(bound),scope_counts=P.COUNTS,whole_card_run=P.RUN,
            gpu_uuid='GPU-synthetic',forecast_complete_GPUh=4.1,billed_limit_GPUh=4.5,
            cumulative_cap_GPUh=113.,budget_origin_used_GPUh=config['budget_origin_used_GPUh'])
        def check():return P.validate_authority(config,bound,registration,proof,authority,revision='1'*40,
            gpu_uuid='GPU-synthetic',config_sha256='b'*64,proof_sha256='c'*64,registration_sha256='a'*64)
        check()
        for target,key,value in ((proof,'exit_code',1),(proof,'CUDA_initialized',True),
                (proof,'model_weights_loaded',1),(proof,'guardrail_checks',[]),(proof,'actual_sample_argument_variants',9),
                (authority,'gpu_uuid','GPU-other'),
                (authority,'forecast_complete_GPUh',.01),(authority,'production_CPU_sha256','0'*64)):
            old=target[key];target[key]=value
            with self.assertRaises(ValueError):check()
            target[key]=old
        config['billed_limit_GPUh']=authority['billed_limit_GPUh']=12.
        with self.assertRaises(ValueError):check()
        authority['kind']='SPECIFIC_WHOLE_CARD_APPROVAL';check()

    def test_prior_capture_scope_and_raw_recomputed_acceptance_cannot_be_transplanted(self):
        for mode in ('capture_scope','source','raw_recompute'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                stage=Path(folder);config,bound,returned=stage_fixture(stage)
                if mode=='capture_scope':
                    role='N08_capture';path=stage/config['references'][role]['ref']
                    value=json.loads(gzip.decompress(path.read_bytes()))
                    value['method_freeze']['repeat_timing_bindings']['RA_CFG_CACHE']='RA_DOUBLE'
                    path.write_bytes(gzip.compress(json.dumps(value).encode()))
                elif mode=='source':
                    role='N07_acceptance';path=stage/config['references'][role]['ref']
                    value=json.loads(path.read_text());value['source_revision']='FOREIGN_ORIGINAL_SOURCE'
                    path.write_text(json.dumps(value))
                if mode!='raw_recompute':
                    config['references'][role]['sha256']=sha(path);(stage/P.CONFIG).write_text(json.dumps(config))
                with accepted_doubles(stage),patch.object(shared_module,'validate',return_value=returned) as physical:
                    if mode=='raw_recompute':
                        raw=json.loads((stage/'accepted_N08.json').read_text());raw['actual_GPUh']=123.
                        with patch('wcomr.balanced_repeat_acceptance_r1.accept',return_value=raw):
                            with self.assertRaisesRegex(ValueError,'Recompute'):P.validate(stage,stage)
                    else:
                        with self.assertRaises(ValueError):P.validate(stage,stage)
                    physical.assert_not_called()


if __name__=='__main__':unittest.main()
