"""Full960 production-entry controls with explicit synthetic inputs/scorers.

No actual model CPU acceptance, codec, server, GPU or budget write is exercised.
"""
import copy
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_N10_complete_batch_r1 import inputs, Scorers
from wcomr import automatic_quality_production_r1 as P
from wcomr.automatic_quality_models_r1 import ROLES, SELF_REF, WEIGHTS, sha
from wcomr.automatic_quality_r1 import fingerprint

ROOT = Path(__file__).resolve().parents[1]


def fixture():
    bundle, _, contrasts = inputs()
    protocol_sha = 'a' * 64
    bundle['evaluator_identity']['measurement_protocol_sha256'] = protocol_sha
    bundle['scorer_fingerprint'] = fingerprint(bundle['evaluator_identity'])
    for row in bundle['rows']: row['scorer_fingerprint'] = bundle['scorer_fingerprint']
    bundle['fingerprint'] = fingerprint({k: v for k, v in bundle.items() if k != 'fingerprint'})
    bound = dict(status='N10_ACCEPTED_COMMON_OUTPUT_INPUTS_BOUND_NOT_METRIC_RUNTIME',
        measurement_protocol_sha256=protocol_sha, static_eligible_prompts=0, input_bundle=bundle)
    reg = dict(purpose=P.PURPOSE, source_revision='1'*40)
    modelreg = dict(source_revision='2'*40, roles=list(ROLES),
        purpose='N10_FULL_FIVE_METRIC_MODEL_CPU_ONLY_NOT_SCORING',
        payload_sha256={SELF_REF: sha(ROOT/SELF_REF)})
    accepted = dict(status='N10_ALL_FIVE_MODEL_CPU_INDEPENDENTLY_ACCEPTED_NOT_QUALITY',
        CPU_accepted=True, accepted_models=5, registered_model_denominator=5,
        source_revision=modelreg['source_revision'], registration_sha256='b'*64,
        rows=[dict(role=role, status='CPU_ROLE_ACCEPTED',
            proof=dict(constructor_source_sha256=sha(ROOT/SELF_REF))) for role in ROLES])
    resource = dict(resources={role:dict(path='/SYNTHETIC/'+role+'.pth',bytes=size,sha256=digest)
                               for role,(size,digest) in WEIGHTS.items()})
    config = dict(purpose=P.PURPOSE, run_id='wc-paper-n10-synthetic-full960-r1',
        input_bundle_fingerprint=bundle['fingerprint'], measurement_protocol_sha256=protocol_sha,
        scorer_fingerprint=bundle['scorer_fingerprint'], methods=bundle['methods'], dimensions=list(P.DIMENSIONS),
        scope_counts=dict(generation_positions=160, metric_positions=960, prompt_groups=8,
                          seeds=[17,43], methods=10, new_generation_paths=0),
        bootstrap_repetitions=4096, comparisons=contrasts, forecast_GPUh=2.5, billed_limit_GPUh=3.,
        cumulative_cap_GPUh=113., budget_origin_used_GPUh=79.99637737158223,
        whole_card_cost_includes_load_warm_scoring_and_release=True,
        generation_latency_claim=False, weighted_quality_total=None,
        references={'model_CPU_registration':dict(sha256='b'*64)})
    return config,reg,bound,accepted,modelreg,resource


def staged(folder):
    stage=Path(folder).resolve(); values=fixture();config,reg=values[:2]
    sources=['src/wcomr/'+name for name in ('automatic_quality_production_r1.py',
        'automatic_quality_models_r1.py','automatic_quality_batch_r1.py','automatic_quality_r1.py',
        'frozen_shared_statistics_r1.py','gpu_budget_pool_v2.py')]
    sources+=['scripts/score_wc_paper_N10_full960_r1.py']
    payload={}
    for ref in sources:
        target=stage/ref;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/ref,target)
        payload[ref]=sha(target)
    for name,value in zip(P.FILES,values[2:]):
        path=stage/(name+'.json');path.write_text(json.dumps(value))
        payload[path.name]=sha(path);config['references'][name]=dict(ref=path.name,sha256=sha(path))
    values[3]['registration_sha256']=config['references']['model_CPU_registration']['sha256']
    path=stage/'model_CPU_acceptance.json';path.write_text(json.dumps(values[3]));payload[path.name]=sha(path)
    config['references']['model_CPU_acceptance']['sha256']=sha(path)
    path=stage/P.CONFIG;path.write_text(json.dumps(config));payload[path.name]=sha(path)
    reg['payload_sha256']=payload;(stage/'registration.json').write_text(json.dumps(reg))
    return values


class ProductionEntryControls(unittest.TestCase):
    def test_complete_contract_preserves_all_original960_without_loading_framework(self):
        values=fixture();bundle=P.validate(*values)
        self.assertEqual(len(bundle['rows']),960)
        self.assertEqual(sum(r['input_status']=='READY_TO_SCORE' for r in bundle['rows']),800)

    def test_smaller_scope_renamed_seed_or_missing_static_cohort_is_refused(self):
        for mode in ('truncated','reassigned','static','price','run_id'):
            with self.subTest(mode=mode):
                values=fixture();config,_,bound=values[:3]
                if mode=='truncated':bound['input_bundle']['rows'].pop()
                elif mode=='reassigned':bound['input_bundle']['cases'][0]['seed']=43
                elif mode=='static':bound['static_eligible_prompts']=1
                elif mode=='price':config['forecast_GPUh']=4.
                else:config['run_id']='../another-run'
                with self.assertRaises(ValueError):P.validate(*values)

    def test_incomplete_model_proof_or_different_constructor_or_weight_refuses(self):
        for mode in ('incomplete','constructor','registration','weight'):
            with self.subTest(mode=mode):
                values=fixture()
                if mode=='incomplete':values[3]['rows'].pop()
                elif mode=='constructor':values[3]['rows'][0]['proof']['constructor_source_sha256']='0'*64
                elif mode=='registration':values[3]['registration_sha256']='0'*64
                else:values[5]['resources']['ViCLIP']['sha256']='0'*64
                with self.assertRaises(ValueError):P.validate(*values)

    def test_stage_immutable_source_and_proof_hashes_checked_before_model_import(self):
        with tempfile.TemporaryDirectory() as folder:
            staged(folder);config,reg,bundle,*_=P.load(folder)
            self.assertEqual(config['scope_counts']['metric_positions'],960)
            path=Path(folder)/'accepted_inputs.json';path.write_text(path.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'payload changed'):P.load(folder)

    def test_actual_CLI_contract_cpu_in_isolation_has_no_Torch_or_GPU_or_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            staged(folder);script=Path(folder)/'scripts/score_wc_paper_N10_full960_r1.py'
            command=[sys.executable,'-S',str(script),'--project',folder,'--stage',folder,'--cpu-check']
            first=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            value=json.loads((Path(folder)/'CPU-scoring-entry-result.json').read_text())
            self.assertEqual(value['metric_positions'],960);self.assertFalse(value['neural_framework_imported'])
            self.assertEqual(value['GPU_submissions'],0);self.assertFalse(value['ledger_written'])
            self.assertNotEqual(subprocess.run(command,capture_output=True).returncode,0)
            self.assertFalse((Path(folder)/'reports/gpu-budget-v2.json').exists())

    def test_admission_requires_same_live_parent_source_uuid_and_additive_pool_origin(self):
        config=fixture()[0];parent=dict(pid=101,start_ticks=900,state='S')
        authority=dict(launch_id='SYNTHETIC_LAUNCH',config_sha256='c'*64,source_revision='1'*40,gpu_uuid='GPU-synthetic')
        job=dict(status='RESERVED_OR_RUNNING',source_revision='1'*40,config_sha256='c'*64,
            launch_id=authority['launch_id'],gpu_uuid='GPU-synthetic',forecast_GPUh=2.5,billed_limit_GPUh=3.,
            supervisor_pid=101,supervisor_start_ticks=900,kind='V2')
        pool=dict(jobs={config['run_id']:job},cap_gpu_hours=113.,origin_used_gpu_hours=config['budget_origin_used_GPUh'])
        def check():return P.admitted_job(config,pool=pool,source_revision='1'*40,
            config_sha256='c'*64,gpu_uuid='GPU-synthetic',authority=authority,parent=parent)
        self.assertFalse(check()['ledger_written'])
        for target,key,value in ((parent,'start_ticks',901),(job,'status','SETTLED'),
                (job,'gpu_uuid','GPU-other'),(pool,'origin_used_gpu_hours',0.)):
            old=target[key];target[key]=value
            with self.assertRaises(ValueError):check()
            target[key]=old
        pool['jobs']['ORIGINAL_MAINLINE_STILL_RESERVED']=dict(status='RESERVED_OR_RUNNING')
        with self.assertRaises(ValueError):check()
        del pool['jobs']['ORIGINAL_MAINLINE_STILL_RESERVED']
        config['billed_limit_GPUh']=job['billed_limit_GPUh']=12.
        with self.assertRaises(ValueError):check()
        job['kind']='V2_SPECIFIC_WHOLE_CARD_APPROVAL';self.assertFalse(check()['ledger_written'])

    def test_full960_original_journal_and_derived_result_agree_with_rejections_kept(self):
        bundle,raw,contrasts=inputs(rejected=True);scorers=Scorers(bundle,raw)
        with tempfile.TemporaryDirectory() as folder:
            result=P.score_complete(bundle,contrasts,scorers,folder,bootstrap_repetitions=2)
            written=json.loads(gzip.decompress((Path(folder)/'metric-results.json.gz').read_bytes()))
            self.assertEqual(result,written);self.assertEqual(len(result['rows']),960)
            self.assertEqual(result['metric_status_counts']['VIDEO_UNAVAILABLE'],5)
            self.assertEqual(result['original_journal_sha256'],sha(Path(folder)/'original-metric-events.jsonl'))
            with self.assertRaises(FileExistsError):P.score_complete(bundle,contrasts,scorers,folder,bootstrap_repetitions=2)

    def test_interrupted_original_journal_remains_readonly_without_false_final(self):
        bundle,raw,contrasts=inputs()
        def stop(planned,result):raise KeyboardInterrupt('SYNTHETIC_INTERRUPTION')
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(KeyboardInterrupt):
                P.score_complete(bundle,contrasts,Scorers(bundle,raw,effect=stop),folder,bootstrap_repetitions=2)
            self.assertFalse((Path(folder)/'metric-results.json.gz').exists())
            original=P.read_journal(Path(folder)/'original-metric-events.jsonl')
            rebuilt=P.reconstruct(bundle,original['events'])
            self.assertEqual(len(rebuilt['rows']),960);self.assertIsNone(rebuilt['final'])
            self.assertFalse(rebuilt['new_work_started'])


if __name__=='__main__':unittest.main()
