"""Fresh full146 released-file reader and original once-only real Alex scorer."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch

from wcomr import cara_source_lifecycle_p1_artifacts_r1 as reader
from wcomr import cara_source_lifecycle_p1_scores_r1 as scores
from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from wcomr.cara_budget_supervisor_r1 import stop_original
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import atomic_json
from check_cara_source_lifecycle_p1_released_fixture_r1 import build,read_fixture

ROOT=Path(__file__).resolve().parents[1]


def run(root,stage,*,deadline):
    root,stage=Path(root),Path(stage);root.mkdir(parents=True,exist_ok=False)
    args,state=build(root/'released')
    before=(len(state['runtime'].calls),len(state['runtime'].scores),state['runtime'].clock)
    packet=read_fixture(args,state)
    assert packet['manifest']['semantic_denominator']==146
    assert packet['manifest']['identity_controls_passed']==12
    assert len(packet['manifest']['quality_positions'])==52 and len(packet['manifest']['new_pairs'])<=32
    assert packet['original_metrics_recomputed']==0
    summary=state['collection'].root/'algorithm-summary.json';summary_sha=file_sha(summary)
    recovered=read_fixture(args,state)
    assert recovered==packet and file_sha(summary)==summary_sha
    assert before==(len(state['runtime'].calls),len(state['runtime'].scores),state['runtime'].clock)
    refusals=[]
    changed=copy.deepcopy(args);changed['capture']['files']['pending_release']={'exists':False}
    try:read_fixture(changed,state)
    except ValueError as error:assert 'release' in str(error);refusals.append('no_original_release')
    else:raise AssertionError('Unreleased original accepted')
    with patch.object(reader,'observe_original_process',return_value=dict(original_live=None)):
        try:read_fixture(args,state)
        except ValueError as error:assert 'FIT service' in str(error);refusals.append('service_unknown')
        else:raise AssertionError('Unknown original service accepted')
    first=next(iter(packet['physical_artifacts'].values()))
    saved=Path(first['arguments_path']);raw=saved.read_bytes();value=json.loads(raw);value['seed']=123
    atomic_json(saved,value)
    try:
        try:read_fixture(args,state)
        except ValueError as error:assert 'saved P1 request' in str(error);refusals.append('saved_arguments')
        else:raise AssertionError('Different actual inference arguments accepted')
    finally:saved.write_bytes(raw)
    response=next(state['queue'].glob('score-*/response.json'));raw=response.read_bytes()
    wrong=json.loads(raw);wrong['payload']['full_fidelity_rows'].pop();atomic_json(response,wrong)
    try:
        try:read_fixture(args,state)
        except ValueError as error:assert 'precisely' in str(error);refusals.append('changed_internal_response')
        else:raise AssertionError('Changed internal accepted bytes consumed')
    finally:response.write_bytes(raw)
    overlay=stage.parent/'wc-time-score-CPU-two_card-r1-20261027'
    config=scores.bind_post_scorer(packet,dict(torch_home=str(overlay/'torch'),piq_site=str(overlay/'site'),weights_sha256={}),
                                   cpu_validation=True)
    manifest,output=root/'manifest.json',root/'scores.json';atomic_json(manifest,config)
    def child(target):
        command=[sys.executable,str(ROOT/scores.WORKER),'--manifest',str(manifest),'--output',str(target),'--cpu-validation']
        started=time.time()
        with target.with_suffix('.log').open('x') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
            identity=bind_original_process(process.pid)
            try:code=process.wait(timeout=min(900,deadline-time.monotonic()))
            finally:stop_original(process,identity)
        observed=observe_original_process(identity);assert observed['original_live'] is False
        result=json.loads(target.read_bytes()) if target.exists() else None
        execution=dict(kind='ACTUAL_CPU_FIXTURE_CHILD',exit_code=code,original_process_ended=True,GPU_hidden=True,
            original_identity=identity,original_observation=observed,config_sha256=digest(config),
            source_sha256=config['source_sha256'],wall_seconds=time.time()-started,result_sha256=digest(result))
        return result,execution,command
    result,execution,command=child(output)
    assert execution['exit_code']==0,output.with_suffix('.log').read_text()[-3500:]
    accepted=scores.accept_scores(packet,config,result,execution,cpu_validation=True)
    assert len(accepted['rows'])==52 and accepted['internal_scores_recomputed']==0
    assert any(r['PSNR_is_infinite'] and r['PSNR_video_dB']=='+inf' for r in result['rows'])
    assert any(r['gradient_ratio_status']=='ZERO_REFERENCE_ENERGY' for r in result['rows'])
    for row in accepted['rows']:
        if row['metric_source']=='SEALED_INTERNAL':
            assert row['metrics']==packet['manifest']['internal_rows'][row['pair_key']]['metrics']
    originals=[output,output.with_name(output.stem+'-intent.json')]
    sha_before={str(p):file_sha(p) for p in originals}
    repeated=subprocess.run(command,capture_output=True,timeout=20)
    assert repeated.returncode!=0 and sha_before=={p:file_sha(p) for p in sha_before}
    # A separate intentional failure keeps every registered pair. The successful
    # child's original result and intent are never resubmitted or overwritten.
    target=Path(config['manifest']['new_pairs'][1]['candidate']['path']);raw=target.read_bytes()
    target.write_bytes(b'EXPLICIT_INDEPENDENT_CPU_FAILURE_FIXTURE')
    try:failed,failed_execution,_=child(root/'failed-scores.json')
    finally:target.write_bytes(raw)
    assert failed_execution['exit_code']!=0 and failed['status']=='P1_FAILED_NEW_PAIR_DENOMINATOR_RETAINED'
    assert failed['registered_pairs']==result['registered_pairs'] and len(failed['rows'])==1
    try:scores.accept_scores(packet,config,failed,failed_execution,cpu_validation=True)
    except ValueError:refusals.append('failed_original_score_full_denominator')
    else:raise AssertionError('Partial failed score accepted')
    return dict(status='P1_REAL_FULL146_READER_AND_ORIGINAL_POST_SCORE_CPU_PASS',
        semantic_positions=146,physical_video_latent_reads=packet['manifest']['physical_paths'],
        source_labels=64,identity_controls=12,logical_quality_positions=52,
        original_sealed_internal_pairs=len(packet['manifest']['internal_rows']),
        original_postrelease_new_pairs=len(result['rows']),all_frames=93,geometry=[64,64,3],
        actual_metric_weights=True,internal_service_and_internal_scores_simulated=True,
        actual_original_Linux_service_and_postscore_processes_ended=True,
        immutable_reader_recovery_no_callbacks=True,no_replay=True,refusals=refusals,
        post_score_execution=execution,failed_score_execution=failed_execution,
        failure_denominator=len(failed['registered_pairs']),failure_completed_pairs=1,
        accepted_sha256=digest(accepted),packet_sha256=digest(packet),
        production_model_weights_loaded=False,old_algorithm_or_metric_experiments_repeated=False,
        production_GPU_entry_accepted=False,GPU_submissions=0,ledger_written=False)
