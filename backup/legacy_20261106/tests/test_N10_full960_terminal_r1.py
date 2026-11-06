"""Synthetic whole960 GPU journals on real accepted CPU/input metadata.

No model, generated video, GPU, SSH, real lock or real ledger is used. Synthetic
scores remain labelled unit-only and are never saved as research results.
"""
import base64
from collections import Counter
from contextlib import contextmanager
import copy
import gzip
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path
from statistics import mean
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from wcomr.automatic_quality_batch_r1 import execute
from wcomr.automatic_quality_terminal_r1 import accept
from wcomr.gpu_budget_pool_v2 import BudgetPool,SCHEMA

ROOT=Path(__file__).resolve().parents[1]


def load_module(ref,name):
    spec=importlib.util.spec_from_file_location(name,ROOT/ref);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def artifact(data=None,*,raw=None,newline=True):
    if raw is None:raw=(json.dumps(data,ensure_ascii=True,indent=2,allow_nan=False)+('\n' if newline else '')).encode()
    return dict(exists=True,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),raw_base64=base64.b64encode(raw).decode(),**({'data':data} if data is not None else {}))


def original_data(ref):
    raw=(ROOT/ref).read_bytes();return artifact(json.loads(gzip.decompress(raw) if ref.endswith('.gz') else raw),raw=raw)


def pack_journal(value,events,tail=b''):
    raw=b''.join((json.dumps(e,ensure_ascii=False,allow_nan=False,separators=(',',':'))+'\n').encode() for e in events)+tail
    value['files']['journal']=artifact(raw=raw)
    if events and events[-1]['kind']=='FINAL':
        final=events[-1]['result'];saved=dict(final,original_journal_sha256=hashlib.sha256(raw).hexdigest(),original_journal_bytes=len(raw))
        encoded=json.dumps(saved,ensure_ascii=False,allow_nan=False,indent=2).encode()
        value['files']['metrics']=artifact(saved,raw=gzip.compress(encoded))
        runner=value['files']['runner']['data'];runner.update(metric_status_counts=final['metric_status_counts'],
            all_ready_positions_scored=final['all_ready_positions_scored'],original_journal_sha256=hashlib.sha256(raw).hexdigest())
    else:
        value['files']['metrics']=dict(exists=False)
    value['files']['runner']=artifact(value['files']['runner']['data'])
    value['files']['supervisor']['data']['runner_sha256']=value['files']['runner']['sha256']
    value['files']['supervisor']=artifact(value['files']['supervisor']['data'])


def fixture():
    CPUraw=(ROOT/'reports/wc_paper_N10_full960_production_CPU_R1_collection_20261018_042130.json.gz').read_bytes()
    CPU=json.loads(gzip.decompress(CPUraw));reg=CPU['registration'];c=CPU['files']['config']['data']
    savedraw=(ROOT/'reports/wc_paper_N10_full960_production_CPU_R1_independent_acceptance_20261018.json').read_bytes();saved=json.loads(savedraw)
    launcher=load_module('scripts/launch_wc_N10_full960_r1.py','unit_N10_launcher')
    auth=launcher.authority_for(CPU,saved,accepted_sha256=hashlib.sha256(savedraw).hexdigest(),gpu_uuid='GPU-unit-full960',launch_id='UNIT_ONLY_FULL960')
    files={name:original_data(info['ref']) for name,info in c['references'].items()}
    bundle=files['accepted_inputs']['data']['input_bundle'];stage=CPU['launch']['stage']
    authfile=artifact(auth)
    launch=dict(status='N10_FULL960_DISPATCHED_ADMISSION_PENDING',source_revision=reg['source_revision'],
        project=CPU['launch']['project'],stage=stage,run_id=c['run_id'],launch_id=auth['launch_id'],gpu_uuid=auth['gpu_uuid'],
        scope_counts=c['scope_counts'],config_sha256=CPU['files']['config']['sha256'],registration_sha256=CPU['registration_sha256'],
        production_CPU_sha256=saved['production_CPU_sha256'],independent_CPU_acceptance_sha256=hashlib.sha256(savedraw).hexdigest(),
        authorization_sha256=authfile['sha256'],bound_input_fingerprint=bundle['fingerprint'],
        supervisor_pid=901001,supervisor_identity=dict(pid=901001,start_ticks=5001,state='S',command='SYNTHETIC_ONLY'),
        forecast_GPUh=4.915,billed_limit_GPUh=6.25,next_check_not_before_unix=100.,midpoint_health_not_before_unix=50.)
    for name,key in [('production_CPU','proof'),('production_bundle','bundle'),('CPU_exit','exit')]:
        files[name]=artifact(CPU['files'][key]['data'],newline=name!='production_CPU')
        assert files[name]['sha256']==CPU['files'][key]['sha256'],name
    files.update(config=artifact(c),CPU_launch=artifact(CPU['launch']),authorization=authfile,
        CPU_independent_remote=artifact(saved,raw=savedraw))
    assert files['config']['sha256']==launch['config_sha256']
    registration=artifact(reg);assert registration['sha256']==launch['registration_sha256']
    runner=dict(status='N10_FULL960_FINISHED_FAILURES_RETAINED',source_revision=launch['source_revision'],config_sha256=launch['config_sha256'],
        scope_counts=c['scope_counts'],input_bundle_fingerprint=bundle['fingerprint'],
        original_admission=dict(run_id=c['run_id'],launch_id=launch['launch_id'],gpu_uuid=launch['gpu_uuid'],reservation_limit_GPUh=6.25,ledger_written=False))
    billing=artifact(dict(status='N10_FULL960_ACTUAL_SCORING_GPU_BILL',source_revision=launch['source_revision'],launch_id=launch['launch_id'],
        run_id=c['run_id'],gpu_uuid=launch['gpu_uuid'],config_sha256=launch['config_sha256'],scope_counts=c['scope_counts'],
        actual_GPUh=.5,wall_seconds=1800.,billed_limit_GPUh=6.25,generation_latency_claim=False,original_output_root_available=True))
    sup=dict(status='N10_FULL960_ORIGINAL_GPU_TERMINAL_NOT_QUALITY_ACCEPTANCE',source_revision=launch['source_revision'],
        config_sha256=launch['config_sha256'],scope_counts=c['scope_counts'],registration_sha256=launch['registration_sha256'],
        run_id=c['run_id'],launch_id=launch['launch_id'],gpu_uuid=launch['gpu_uuid'],supervisor_identity=dict(launch['supervisor_identity'],state='R'),
        child_identity=dict(pid=901002,start_ticks=5002,state='S',command='SYNTHETIC_SCORER'),child_exit_code=0,
        billing_sha256=billing['sha256'],actual_GPUh=.5)
    files.update(supervisor=artifact(sup),runner=artifact(runner),billing=billing)
    job=dict(status='SETTLED',actual_GPUh=.5,billing_sha256=billing['sha256'],forecast_GPUh=4.915,billed_limit_GPUh=6.25,
        **{k:launch[k] for k in ('source_revision','launch_id','gpu_uuid','config_sha256','scope_counts','production_CPU_sha256','authorization_sha256','bound_input_fingerprint')})
    pool=dict(schema=SCHEMA,cap_gpu_hours=226,origin_used_gpu_hours=79.99637737158223,origin_gpu_jobs_launched=0,jobs={c['run_id']:job},events=[])
    pool.update(BudgetPool.accounting(pool))
    value=dict(status='N10_FULL960_ORIGINAL_ONCE_CAPTURE',mode='terminal',observed_unix=101.,launch=launch,
        registration=reg,registration_artifact=registration,registration_sha256=registration['sha256'],payload_actual_sha256=reg['payload_sha256'],
        files=files,CPU_capture=CPU,CPU_capture_sha256=hashlib.sha256(CPUraw).hexdigest(),CPU_capture_raw_base64=base64.b64encode(CPUraw).decode(),
        CPU_independent=saved,CPU_independent_sha256=hashlib.sha256(savedraw).hexdigest(),CPU_independent_raw_base64=base64.b64encode(savedraw).decode(),
        expected_original_handles=dict(supervisor=launch['supervisor_identity'],child=sup['child_identity']),
        original_processes=dict(supervisor=dict(pid=901001,state=None,start_ticks=None),child=dict(pid=901002,state=None,start_ticks=None)),
        pool=pool,own_UUID_lock_exists=True,own_UUID_lock_free=True,own_GPU=launch['gpu_uuid']+', NVIDIA RTX A6000, 0, 0',
        compute_apps='',unit_fixture_only=True,GPU_submissions=0,ledger_written=False)

    def score(row):
        dimension=row['dimension'];m=bundle['methods'].index(row['method'])
        result=dict(case_id=row['case_id'],method=row['method'],dimension=dimension,status='SCORED',
            value=bool(m%2) if dimension=='dynamic_degree' else .8-m*.02,
            **{k:row[k] for k in ('video_sha256','prompt_sha256','scorer_fingerprint')},
            observed_sampling=row['expected_sampling'],unweighted_original_per_video_result=True)
        sources={'src/wcomr/imaging_quality.py','src/wcomr/rv0_video_reader.py'} if dimension=='MUSIQ_LONGER512' else {'upstream/vbench/'+dimension+'.py'}
        if dimension in ('subject_consistency','overall_consistency'):sources.add('upstream/vbench/utils.py')
        result['metric_source_sha256']={stage+'/'+n:reg['payload_sha256'][n] for n in sources}
        if dimension=='MUSIQ_LONGER512':
            result.update(value=50.-m,frame_scores=[50.-m]*93,pts=[[i,'1/16'] for i in range(93)],
                decoder_evidence=dict(backend='ORIGINAL_FFMPEG_READER',model_input_shapes=[[1,3,288,512]]*93))
        else:
            decord=dimension in ('subject_consistency','overall_consistency');s=row['expected_sampling']
            result['decoder_evidence']=dict(readers=[dict(backend='DECORD',source_frames=93,source_fps=16.)] if decord else
                [dict(backend='OPENCV',source_frames=93,source_fps=16.,released=True)],
                batches=[s['frame_indices']] if decord else [],
                selections=[] if decord else [s['frame_indices'],s['target_indices']] if dimension=='motion_smoothness' else [s['frame_indices']],
                decoder_pixels_or_preprocessing_not_replaced=True,metric_decoder_not_assumed_byte_equal_to_N07_RGB_backend=True)
        return result

    @contextmanager
    def factory(dimension):yield SimpleNamespace(dimension=dimension,scorer_fingerprint=bundle['scorer_fingerprint'],score=score)
    events=[];execute(bundle,c['comparisons'],factory,events.append,clock=itertools.count(0,.01).__next__,bootstrap_repetitions=4096)
    pack_journal(value,events)
    return value,launch,events,bundle


class OriginalFull960TerminalControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=fixture()

    def sample(self):return copy.deepcopy(self.base)

    def test_whole960_all645_and_independent_prompt_means_with_negative_method_result(self):
        value,launch,_,_=self.sample();result=accept(value,launch)
        self.assertTrue(result['full_protocol_accepted'],result['errors']);self.assertTrue(result['full_scientific_scope_accepted'])
        self.assertEqual(result['valid_scored_metric_positions'],645)
        self.assertEqual(result['observed_metric_status_counts'],{'SCORED':645,'VIDEO_UNAVAILABLE':155,'NOT_APPLICABLE_STATIC_SCOPE':160})
        self.assertTrue(result['independent_prompt_seed_means_verified'])
        contrast=next(r for r in result['summary']['comparisons'] if r['candidate']=='A_NO_P' and r['baseline']=='NATIVE35' and r['dimension']=='subject_consistency')
        self.assertLess(contrast['available_cohort_mean_delta'],0)
        self.assertEqual(result['evidence_kind'],'SYNTHETIC_UNIT_ONLY_NOT_REAL_RESEARCH')

    def test_raw_sha_changed_decoder_or_omitted_MUSIQ_frame_cannot_pass(self):
        for mode in ('sha','decoder','MUSIQ'):
            value,launch,events,_=self.sample()
            with self.subTest(mode=mode):
                if mode=='sha':value['files']['config']['data']['forecast_GPUh']=.1
                else:
                    row=next(e['row'] for e in events if e['kind']=='ROW' and e['row']['dimension']==('MUSIQ_LONGER512' if mode=='MUSIQ' else 'subject_consistency'))
                    if mode=='MUSIQ':row['frame_scores'].pop()
                    else:row['decoder_evidence']['readers'][0]['source_frames']=92
                    # Only raw journal is changed: a saved summary cannot hide it.
                    value['files']['journal']=artifact(raw=b''.join((json.dumps(e,separators=(',',':'),ensure_ascii=False)+'\n').encode() for e in events))
                with self.assertRaises(ValueError):accept(value,launch)

    def test_interrupted_prefix_keeps_partial_rows_and_trailing_bytes(self):
        value,launch,events,_=self.sample();prefix=[]
        for e in events:
            prefix.append(e)
            if sum(x['kind']=='ROW' for x in prefix)==140:break
        value['files']['runner']['data']['status']='N10_FULL960_TECHNICAL_FAILURE_FULL_SCOPE_RETAINED'
        value['files']['supervisor']['data']['child_exit_code']=1
        pack_journal(value,prefix,b'{"original_incomplete_tail"')
        result=accept(value,launch);self.assertFalse(result['full_protocol_accepted'])
        self.assertFalse(result['full_scientific_scope_accepted']);self.assertEqual(result['valid_scored_metric_positions'],140)
        self.assertEqual(len(result['rows']),960);self.assertIsNone(result['summary']);self.assertIsNotNone(result['original_unfinished_tail'])

    def test_one_metric_failure_retains_644_valid_scores_and_original_denominator(self):
        value,launch,_,bundle=self.sample()
        failed=next((r['case_id'],r['method'],r['dimension']) for r in bundle['rows']
                    if r['input_status']=='READY_TO_SCORE')
        @contextmanager
        def factory(dimension):
            records={(r['case_id'],r['method'],r['dimension']):r for r in self.base[0]['files']['metrics']['data']['rows'] if r['status']=='SCORED'}
            def score(planned):
                if (planned['case_id'],planned['method'],planned['dimension'])==failed:raise RuntimeError('EXPLICIT_UNIT_METRIC_FAILURE')
                return copy.deepcopy(records[planned['case_id'],planned['method'],planned['dimension']])
            yield SimpleNamespace(dimension=dimension,scorer_fingerprint=bundle['scorer_fingerprint'],score=score)
        events=[];execute(bundle,value['files']['config']['data']['comparisons'],factory,events.append,clock=itertools.count(0,.01).__next__,bootstrap_repetitions=4096)
        pack_journal(value,events);result=accept(value,launch)
        self.assertTrue(result['original_terminal_attempt_protocol_accepted']);self.assertFalse(result['full_protocol_accepted'])
        self.assertFalse(result['full_scientific_scope_accepted']);self.assertEqual(len(result['rows']),960)
        self.assertEqual(result['valid_scored_metric_positions'],644)
        self.assertEqual(result['observed_metric_status_counts']['METRIC_FAILED'],1)

    def test_wrong_bill_preserves_valid_science_but_not_protocol(self):
        value,launch,_,_=self.sample();value['pool']['jobs'][launch['run_id']]['billing_sha256']='0'*64
        result=accept(value,launch);self.assertTrue(result['full_scientific_scope_accepted']);self.assertFalse(result['full_protocol_accepted'])

    def test_other_account_after_release_does_not_invalidate_own_release(self):
        value,launch,_,_=self.sample();value['compute_apps']=launch['gpu_uuid']+', 999888'
        self.assertTrue(accept(value,launch)['full_protocol_accepted'])

    def test_live_original_and_before_ETA_do_not_become_terminal(self):
        value,launch,_,_=self.sample();value['original_processes']['child']=dict(pid=901002,start_ticks=5002,state='S')
        self.assertFalse(accept(value,launch)['full_protocol_accepted']);value['observed_unix']=99.
        with self.assertRaises(ValueError):accept(value,launch)

    def test_N09_ordering_and_real_CPU_hash_are_required_before_dispatch(self):
        m=load_module('scripts/launch_wc_N10_full960_r1.py','N10_launch_guard_unit')
        cap=self.base[0]['CPU_capture'];accepted=copy.deepcopy(self.base[0]['CPU_independent'])
        accepted['CPU_accepted']=False
        with self.assertRaises(ValueError):m.authority_for(cap,accepted,accepted_sha256='f'*64,gpu_uuid='GPU-unit',launch_id='UNIT')
        with self.assertRaises(ValueError):m.prior_N09({}, {}, 'f'*64)

    def test_N09_legitimate_refusals_keep_whole40_ordering_eligibility(self):
        m=load_module('scripts/launch_wc_N10_full960_r1.py','N10_N09_ordering_unit')
        prior=dict(launch=dict(run_id='UNIT_N09',source_revision='f'*40),billing_sha256='a'*64,
                   runner=dict(runs=[dict(status='COMPLETE')]*38+[dict(status='TEXT_REJECTED'),dict(status='VIDEO_REJECTED')]),
                   supervisor=dict(child_exit_code=0))
        accepted=dict(capture_sha256='b'*64,terminal_receipt_audit_accepted=True,
                      original_finance_status='ORIGINAL_ACTUAL_BILL_AND_ADDITIVE_SETTLEMENT_MATCH',
                      own_GPU_finance_released=True,original_CPU_post_exit_code=0,
                      original_runner_paths=40,registered_total_paths=40,actual_GPUh=.5)
        self.assertEqual(m.prior_N09(prior,accepted,'b'*64)['run_id'],'UNIT_N09')
        prior['runner']['runs'][0]=dict(status='TECHNICAL_FAILURE')
        with self.assertRaises(ValueError):m.prior_N09(prior,accepted,'b'*64)

    def test_client_remote_programs_compile_and_preETA_never_connects(self):
        launcher=load_module('scripts/launch_wc_N10_full960_r1.py','N10_program_compile_unit')
        collector=load_module('scripts/capture_wc_N10_full960_r1.py','N10_collector_preETA_unit')
        compile(launcher.REMOTE,'<N10_DISPATCH_REMOTE>','exec')
        compile(collector.REMOTE,'<N10_CAPTURE_REMOTE>','exec')
        with tempfile.TemporaryDirectory() as tmp:
            launch_ref=Path(tmp)/'original-launch.json';output=Path(tmp)/'must-not-exist.json.gz'
            launch_ref.write_text(json.dumps(dict(dispatch=self.base[1])))
            args=['capture','--launch-ref',str(launch_ref),'--mode','terminal','--output',str(output)]
            with patch.object(sys,'argv',args),patch.object(collector.time,'time',return_value=99.), \
                    patch.object(collector.subprocess,'run',side_effect=AssertionError('No early SSH')) as remote:
                with self.assertRaisesRegex(ValueError,'Before original N10 check time'):collector.main()
                remote.assert_not_called()
            self.assertFalse(output.exists())

    def test_cold_offline_acceptor_imports_without_neural_framework(self):
        code='import sys;sys.path.insert(0,'+repr(str(ROOT/'src'))+');import wcomr.automatic_quality_terminal_r1;assert "torch" not in sys.modules'
        p=subprocess.run([sys.executable,'-S','-c',code],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)


if __name__=='__main__':unittest.main()
