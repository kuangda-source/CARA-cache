"""Real old16/cost/local32 proofs, synthetic N07/N08 and physical loader.

No new video, model, CUDA execution, GPU approval or financial result.
"""
import copy
from contextlib import ExitStack
import gzip
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from wcomr import action_price12_production_r1 as P
from wcomr import frozen_shared_production_r1 as shared_module
from wcomr.frozen_shared_production_r1 import sha

ROOT=Path(__file__).resolve().parents[1]
PROOF='reports/wc_paper_N09_action12_full32_adapter_and_whole_cost_CPU_preparation_20261016.json'
# Isolated production CPU packets point this at the existing project runtime.
# The local fallback is the accepted source-only nine-file CPU fixture.
RUNTIME=Path(os.environ.get('WC_ACTION12_TEST_RUNTIME',str(
    ROOT/'runtime' if (ROOT/'runtime').is_dir() else
    ROOT/'.sync/wc-phase-runtime-local-r2-20261016/runtime')))


def fixture():
    scope=json.loads((ROOT/P.SCOPE).read_text())
    quote=json.loads((ROOT/'reports/wc_paper_N09_action16_full12_944_historical_cost_preview_R2_20261016.json').read_text())
    shared=json.loads((ROOT/shared_module.CONFIG).read_text())
    config=dict(card=P.CARD,run_id=P.RUN,scope_counts=P.COUNTS,
        bound_action_fingerprint=scope['fingerprint'],strategy=P.STRATEGY,parent_method='P_OFF',
        readout='BETA1_ONE_PHASE',memory_policy='REQUEST_BOUNDARY_GC_ONLY',autonomy_exclusive_upper_GPUh=12,
        guardrails_enabled=True,incremental_clock_boundary=scope['cost_boundary'],
        research_capture_charged_to_whole_card=True,training=False,online_teachers=False,F_B_enabled=False,
        P_ACR=False,T1=False,head_elision=False,new_prices_deployed=False,clean_repeated_latency_claim=False,
        forecast_complete_GPUh=quote['forecast_complete_GPUh'],billed_limit_GPUh=quote['billed_limit_GPUh'],
        cumulative_cap_GPUh=shared['cumulative_cap_GPUh'],budget_origin_used_GPUh=shared['budget_origin_used_GPUh'])
    return config,scope,shared,quote


def stage_fixture(stage):
    config,scope,shared,quote=fixture();refs={}
    def copy_original(ref):
        p=stage/ref;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/ref,p)
        return dict(ref=ref,sha256=sha(p))
    def put(name,ref,value,compressed=False):
        p=stage/ref;p.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(value).encode();p.write_bytes(gzip.compress(raw) if compressed else raw)
        refs[name]=dict(ref=ref,sha256=sha(p))
    refs['shared_config']=copy_original(shared_module.CONFIG)
    refs['action_scope']=copy_original(P.SCOPE)
    refs['method_freeze']=copy_original(scope['references']['final_five_role_freeze']['ref'])
    protocol='manifests/wc_paper_N08_balanced_repeat40_protocol_r1_20261016.json'
    refs['timing_protocol']=copy_original(protocol)
    for value in scope['references'].values():copy_original(value['ref'])
    for value in quote['references'].values():copy_original(value['ref'])
    for name in scope['source_bindings']:copy_original(name)
    for name in P.ADAPTER_SOURCES:copy_original(name)
    prep=json.loads((ROOT/PROOF).read_text())
    copy_original(prep['archive_adapter_reused_unchanged_HEAD']['path'])
    refs['whole_cost']=copy_original('reports/wc_paper_N09_action16_full12_944_historical_cost_preview_R2_20261016.json')
    refs['adapter_CPU_preparation']=copy_original(PROOF)
    refs['adapter_CPU_raw']=copy_original(prep['original_ref'])
    refs['adapter_CPU_acceptance']=copy_original(prep['independent_acceptance_ref'])
    freeze=json.loads((stage/refs['method_freeze']['ref']).read_text())
    timing=json.loads((stage/protocol).read_text())
    put('N07_capture','SYNTHETIC_N07.json.gz',dict(config_sha256=refs['shared_config']['sha256'],
        launch=dict(source_revision='SYNTHETIC_N07_NOT_REAL_COMPLETION')),True)
    put('N08_capture','SYNTHETIC_N08.json.gz',dict(shared_config_sha256=refs['shared_config']['sha256'],
        shared_config=shared,timing_protocol=timing,method_freeze=freeze,
        launch=dict(source_revision='SYNTHETIC_N08_NOT_REAL_COMPLETION')),True)
    put('N07_acceptance','SYNTHETIC_N07_ACCEPTED.json',dict(terminal_receipt_audit_accepted=True,
        scientific_available_cohorts_with_registered_missingness=True,original_runner_paths=180,
        capture_sha256=refs['N07_capture']['sha256'],source_revision='SYNTHETIC_N07_NOT_REAL_COMPLETION'))
    put('N08_acceptance','SYNTHETIC_N08_ACCEPTED.json',dict(terminal_receipt_audit_accepted=True,
        full_raw_and_fidelity_scope_accepted=True,own_GPU_and_finance_released=True,
        original_runner_paths=40,original_CPU_post_exit_code=0,source_revision='SYNTHETIC_N08_NOT_REAL_COMPLETION'))
    config['references']=refs;p=stage/P.CONFIG;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(config))
    return config,scope,shared


def mainline_doubles(stage):
    stack=ExitStack()
    for name,module in [('N07','wcomr.frozen_shared_acceptance_r1'),('N08','wcomr.balanced_repeat_acceptance_r1')]:
        value=json.loads((stage/('SYNTHETIC_'+name+'_ACCEPTED.json')).read_text())
        stack.enter_context(patch(module+'.accept',return_value=value))
    return stack


class Action12ProductionControls(unittest.TestCase):
    def test_full_scope_cost_window_and_no_method_or_price_deployment(self):
        config,scope,shared,quote=fixture()
        self.assertEqual(P.validate_contract(config,scope,shared,quote),scope)
        self.assertEqual(config['forecast_complete_GPUh'],10.045)
        for key,value in [('forecast_complete_GPUh',1.),('billed_limit_GPUh',10.),
                ('budget_origin_used_GPUh',0.),('parent_method','TABLE_PHASE_H1'),
                ('new_prices_deployed',True),('clean_repeated_latency_claim',True),
                ('guardrails_enabled',False),('head_elision',True),('autonomy_exclusive_upper_GPUh',13)]:
            changed=copy.deepcopy(config);changed[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):P.validate_contract(changed,scope,shared,quote)
        changed=copy.deepcopy(scope);changed['complete_parent_matrix'].pop()
        with self.assertRaises(ValueError):P.validate_contract(config,changed,shared,quote)

    def test_saved_cost_and_complete32_proofs_recomputed_with_exact_current_sources(self):
        with tempfile.TemporaryDirectory() as folder:
            stage=Path(folder);config,scope,shared=stage_fixture(stage)
            with mainline_doubles(stage):observed=P.referenced_contract(stage)
            self.assertEqual(observed[2],scope);self.assertEqual(observed[3]['registered_adapter_CPU_paths'],24)
            self.assertEqual(observed[3]['independently_reloaded_tensors'],1528)
            self.assertEqual(len(observed[3]['source_sha256']),3)
            self.assertEqual(observed[3]['new_full32_paths_run'],0)

    def test_unaccepted_mainline_foreign_cost_source_or_CPU_proof_refused_before_physical_load(self):
        for mode in ('N07','N08','source','cost','CPU','raw_recompute'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                stage=Path(folder);config,scope,shared=stage_fixture(stage)
                if mode in ('N07','N08','cost','CPU'):
                    role={'N07':'N07_acceptance','N08':'N08_acceptance','cost':'whole_cost','CPU':'adapter_CPU_acceptance'}[mode]
                    p=stage/config['references'][role]['ref'];value=json.loads(p.read_text())
                    if mode in ('N07','N08'):value['terminal_receipt_audit_accepted']=False
                    elif mode=='cost':value['components']['complete512_extra_trial_seconds']-=1.
                    else:value['raw_tensors']=1527
                    p.write_text(json.dumps(value));config['references'][role]['sha256']=sha(p)
                    (stage/P.CONFIG).write_text(json.dumps(config))
                elif mode=='source':
                    p=stage/P.ADAPTER_SOURCES[0];p.write_text(p.read_text()+'\n# SYNTHETIC_CHANGED_SOURCE\n')
                with mainline_doubles(stage),patch.object(shared_module,'validate') as physical:
                    if mode=='raw_recompute':
                        value=json.loads((stage/'SYNTHETIC_N08_ACCEPTED.json').read_text());value['actual_GPUh']=999.
                        with patch('wcomr.balanced_repeat_acceptance_r1.accept',return_value=value):
                            with self.assertRaisesRegex(ValueError,'Recompute'):P.validate(stage,stage)
                    else:
                        with self.assertRaises(ValueError):P.validate(stage,stage)
                    physical.assert_not_called()

    def test_physical_parameters_and_all_nine_runtime_files_reuse_exactly(self):
        with tempfile.TemporaryDirectory() as folder:
            stage=Path(folder);config,scope,shared=stage_fixture(stage)
            prep=json.loads((ROOT/PROOF).read_text());raw=json.loads(gzip.decompress((ROOT/prep['original_ref']).read_bytes()))
            for name in raw['runtime_source_sha256']:
                p=stage/'runtime'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(RUNTIME/name,p)
            params=json.loads((stage/scope['references']['math_parameters']['ref']).read_text())
            returned=(shared,dict(source_revision='SYNTHETIC_PHYSICAL_LOADER'),{},None,{},params,{},dict(reused=True))
            with mainline_doubles(stage),patch.object(shared_module,'validate',return_value=returned) as physical:
                observed=P.validate(stage,stage)
            self.assertEqual(observed[4],params);self.assertEqual(physical.call_count,1)
            bad=stage/'runtime'/next(iter(raw['runtime_source_sha256']));bad.write_bytes(b'SYNTHETIC_RUNTIME_CHANGE')
            with mainline_doubles(stage),patch.object(shared_module,'validate',return_value=returned):
                with self.assertRaisesRegex(ValueError,'runtime'):P.validate(stage,stage)

    def test_actual_CPU_UUID_full_bill_and_strict_under12_authority(self):
        config,scope,shared,quote=fixture();reg=dict(source_revision='1'*40)
        proof=dict(source_revision='1'*40,status=P.CPU_STATUS,exit_code=0,registration_sha256='a'*64,
            config_sha256='b'*64,bound_action_fingerprint=scope['fingerprint'],scope_counts=P.COUNTS,
            CUDA_initialized=False,GPU_submissions=0,model_weights_loaded=0,ledger_written=False,
            actual_sample_argument_variants=4,matrix=scope['complete_parent_matrix'],
            guardrail_checks=[dict(scene=r['name'],unguarded_execution_refused=True) for r in scope['requests']])
        authority=dict(launch_id='SYNTHETIC_NOT_A_REAL_LAUNCH',direct_user_authorization=True,
            user_reply_quote='SYNTHETIC_NOT_REAL_APPROVAL',kind='STANDING_STRICT_UNDER12',source_revision='1'*40,
            config_sha256='b'*64,production_CPU_sha256='c'*64,bound_input_fingerprint=scope['fingerprint'],
            bound_action_fingerprint=scope['fingerprint'],scope_counts=P.COUNTS,whole_card_run=P.RUN,
            gpu_uuid='GPU-synthetic',forecast_complete_GPUh=config['forecast_complete_GPUh'],
            billed_limit_GPUh=config['billed_limit_GPUh'],cumulative_cap_GPUh=config['cumulative_cap_GPUh'],
            budget_origin_used_GPUh=config['budget_origin_used_GPUh'])
        def check():return P.validate_authority(config,scope,reg,proof,authority,revision='1'*40,gpu_uuid='GPU-synthetic',
            config_sha256='b'*64,proof_sha256='c'*64,registration_sha256='a'*64)
        check()
        for target,key,value in [(proof,'exit_code',1),(proof,'actual_sample_argument_variants',3),
                (proof,'matrix',scope['complete_parent_matrix'][:-1]),(proof,'CUDA_initialized',True),
                (authority,'gpu_uuid','GPU-other'),(authority,'forecast_complete_GPUh',.1)]:
            old=target[key];target[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):check()
            target[key]=old
        config['billed_limit_GPUh']=authority['billed_limit_GPUh']=12.
        with self.assertRaises(ValueError):check()
        authority['kind']='SPECIFIC_WHOLE_CARD_APPROVAL';check()


if __name__=='__main__':unittest.main()
