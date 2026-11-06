"""Actual once-only post-score Docker/recovery with two fresh synthetic pairs.

The32-pair worker and full released reader are reused by exact source. Fifty
internal fixture rows are simulated here so this affected transport probe only
computes two new pairs and preserves a separate two-denominator/one-row failure.
"""
import argparse
import copy
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts'),str(ROOT/'tests')]

from wcomr import cara_source_lifecycle_p1_score_capture_r1 as capture
from wcomr import cara_source_lifecycle_p1_score_dispatch_r1 as dispatch
from wcomr.cara_source_lifecycle_p1_scores_r1 import pair_key,bind_post_scorer
from wcomr.cara_budget_original_handles_r1 import bind_original_process,observe_original_process
from wcomr.cara_budget_search_journal_r1 import create_record,read_record
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from wcomr.gpu_budget_pool_v2 import atomic_json
from check_cara_source_lifecycle_fit_host_cpu_r1 import host_limits,media_command as old_media_command,execute_media
import check_cara_source_lifecycle_p1_score_fixture_r1 as fixture

SOURCE='scripts/check_cara_source_lifecycle_p1_post_host_cpu_r1.py'


def production_service_branch(stage,reg,environment):
    """Exercise the real serve/AS/affinity branch under GPU-hidden metadata.

    No allocation, mode change, budget transaction or query is dispatched. The
    simulated guardian is this actual bounded CPU parent and is labeled below.
    """
    from wcomr.cara_source_lifecycle_p1_service_r1 import HeldFITService,CARD,PRECISION,KIND
    from wcomr.cara_source_lifecycle_p1_identity_r1 import GPU
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    project=stage.parents[1];separate=stage.with_name(stage.name+'-service');separate.mkdir(mode=0o700)
    for n in reg['payload_sha256']:
        target=separate/n;target.parent.mkdir(parents=True,exist_ok=True);os.link(stage/n,target)
    copied=copy.deepcopy(reg);copied['stage']=str(separate);atomic_json(separate/'registration.json',copied)
    identity=bind_original_process(os.getpid());card=read_record(separate/CARD)
    keys=dict(run_id='P1-serve-CPU-'+digest(str(separate))[:24],launch_id=digest(str(separate))[:32],host='two_card',
        gpu_uuid=GPU,stage=str(separate),source_revision=reg['parent_git_revision'],scope_sha256=card['scope_sha256'],billed_limit_GPUh=18.)
    authority=dict(keys,CPU_fixture_only=False,card_kind=KIND,execution_authorized=True,authorizes_replay=False,
        authorization_basis='DIRECT_USER_SINGLE_CARD',user_quote='EXPLICIT_CPU_ALLOCATION_METADATA_SIMULATION_NO_GPU_OR_USER_AUTHORITY')
    create_record(separate/'GPU-authorization.json',authority)
    create_record(separate/'GPU-launch.json',dict(keys,CPU_fixture_only=False,guardian_identity=identity,
        registration_sha256=file_sha(separate/'registration.json'),authorization_sha256=file_sha(separate/'GPU-authorization.json'),
        admission_sha256='0'*64,CPU_only_allocation_metadata_simulation=True))
    guardian=dict(keys,CPU_fixture_only=False,started_monotonic=time.monotonic(),original_handles={'guardian':identity})
    atomic_json(separate/'guardian.json',guardian)
    service=HeldFITService(project,separate,environment);closed=None
    try:
        started=service.start(guardian);assert service.identity['pid']!=identity['pid']
        assert os.sched_getaffinity(service.identity['pid'])=={26,27}
        limits=Path('/proc/'+str(service.identity['pid'])+'/limits').read_text()
        assert any(line.split()[-3:-1]==['4294967296','4294967296'] for line in limits.splitlines() if line.startswith('Max address space'))
        service.check()
    finally:closed=service.close()
    assert closed['complete'] and closed['exit_code']==0 and closed['terminal_error'] is None
    assert closed['counts']['requested_queries']==0 and observe_original_process(service.identity)['original_live'] is False
    return dict(actual_production_serve_branch=True,CPU_only_allocation_metadata_simulation=True,GPU_allocation_created=False,
        stage=str(separate),start=started,terminal=closed,actual_affinity=[26,27],actual_RLIMIT_AS_bytes=4*2**30,
        internal_queries_dispatched=0,original_process_ended=True,GPU_submissions=0,ledger_written=False)


def media(output):
    assert os.environ['CUDA_VISIBLE_DEVICES']=='' and os.environ['NVIDIA_VISIBLE_DEVICES']=='void'
    assert os.sched_getaffinity(0)=={26,27};signal.alarm(600)
    from check_cara_s_endpoint_real_video_r1 import write_video
    from wcomr.cara_s_endpoint_artifacts_r1 import decode_video
    files={}
    for i in range(2):
        for role in ('candidate','reference'):
            name=role+'-'+str(i)+'.mp4';path=output/name
            assert not path.exists()
            write_video(path,'P1_POST_TRANSPORT_'+str(i)+'_'+('IDENTICAL' if i==1 else role),height=64,width=64)
            descriptor=dict(path=str(path),bytes=path.stat().st_size,sha256=file_sha(path))
            files[name]=dict(video=descriptor,decoded=decode_video(descriptor,shape=(93,64,64,3)))
    bad=output/'bad-1.mp4';bad.write_bytes(b'EXPLICIT_INDEPENDENT_CPU_CODEC_FAILURE')
    files[bad.name]=dict(video=dict(path=str(bad),bytes=bad.stat().st_size,sha256=file_sha(bad)),
                         decoded=files['candidate-1.mp4']['decoded'])
    create_record(output/'post-media.json',dict(CPU_fixture_only=True,files=files,frames=93,
        generative_weights=False,GPU_submissions=0))


def prepared_packet(original,stage,media_rows,*,failed=False):
    packet=copy.deepcopy(original);m=packet['manifest']
    chosen_positions=[next(p for p in m['quality_positions'] if p['pair_key']==pair_key(q)) for q in m['new_pairs'][:2]]
    chosen_ids={p['id'] for p in chosen_positions}
    replacements={}
    for i,row in enumerate(chosen_positions):
        for side in ('candidate','reference'):
            name='bad-1.mp4' if failed and i==1 and side=='candidate' else side+'-'+str(i)+'.mp4'
            replacements[row[side]['proof_sha256']]=media_rows[name]
    for row in m['quality_positions']:
        for side in ('candidate','reference'):
            d=row[side]
            if d['proof_sha256'] in replacements:
                media_row=replacements[d['proof_sha256']]
                d.update(path=media_row['video']['path'],sha256=media_row['video']['sha256'])
                packet['decoded'][d['proof_sha256']]=media_row['decoded']
        row['pair_key']=pair_key(row)
    internal,new={},[]
    for row in m['quality_positions']:
        key=row['pair_key'];pair={k:row[k] for k in ('member','candidate','reference')}
        if row['id'] in chosen_ids:
            new.append(dict(id='P1_NEW_'+key,**pair,
                expected_decoded_RGB_sha256=[packet['decoded'][row[s]['proof_sha256']]['RGB_sha256'] for s in ('candidate','reference')]))
        else:
            metric=fixture.metric(pair,packet['decoded'])
            internal[key]=dict(pair=pair,metrics=metric,metrics_sha256=digest(metric),
                original_response_path='/EXPLICIT_CURRENT_CPU_PROBE/simulated-internal.json',
                original_response_sha256='a'*64,original_execution_sha256='b'*64)
    assert len(internal)==50 and len(new)==2
    m.update(internal_rows=internal,new_pairs=new)
    create_record(stage/'GPU-launch.json',dict(CPU_fixture_only=True,fixture_only_no_GPU_allocation=True,
        run_id=m['run_id'],launch_id=m['launch_id']))
    m['original_launch_sha256']=packet['release']['original_launch_sha256']=file_sha(stage/'GPU-launch.json')
    return packet


def run_score(stage,packet,environment,deadline):
    config=bind_post_scorer(packet,environment,cpu_validation=True)
    first=dispatch.dispatch(stage,packet,config,file_sha(stage/'registration.json'),cpu_validation=True,work_seconds=600)
    assert first['status']=='ORIGINAL_SCORE_INTENT_CREATED'
    control,out=dispatch.paths(stage,config);intent_sha=file_sha(control/'intent.json')
    repeated=dispatch.dispatch(stage,packet,config,file_sha(stage/'registration.json'),cpu_validation=True,work_seconds=600)
    assert repeated['status'] in ('ORIGINAL_SCORE_DISPATCH_UNKNOWN','ORIGINAL_SCORE_DISPATCH_ACTIVE','ORIGINAL_SCORE_ACTIVE',
        'ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED','ORIGINAL_SCORE_FAILED')
    assert file_sha(control/'intent.json')==intent_sha
    while True:
        state=dispatch.recover(stage)
        if state['status'] in ('ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED','ORIGINAL_SCORE_FAILED'):break
        assert time.monotonic()<deadline and state['status'] in (
            'ORIGINAL_SCORE_DISPATCH_UNKNOWN','ORIGINAL_SCORE_DISPATCH_ACTIVE','ORIGINAL_SCORE_ACTIVE','ORIGINAL_SCORE_UNKNOWN')
        time.sleep(.5)
    assert file_sha(control/'intent.json')==intent_sha
    terminal=state['supervisor_terminal'];assert terminal['cleanup_error'] is None
    originals=[out/'scores.json',control/'intent.json',out/'scores-intent.json',control/'container.cid']
    before={str(p):file_sha(p) for p in originals}
    again=dispatch.recover(stage);assert again['status']==state['status']
    assert before=={p:file_sha(p) for p in before}
    if state['status']=='ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED':
        assert terminal['exit_code']==0 and terminal['error'] is None
        accepted=state['score_capture']['accepted'];assert accepted['logical_quality_positions']==52
        assert accepted['new_scored_pairs']==2 and accepted['reused_internal_unique_pairs']==50
        assert accepted['internal_scores_recomputed']==0
    else:
        assert terminal['exit_code']!=0 and terminal['error'] is not None
        raw=read_record(out/'scores.json')
        assert raw['status']=='P1_FAILED_NEW_PAIR_DENOMINATOR_RETAINED' and len(raw['registered_pairs'])==2 and len(raw['rows'])==1
    cid=(control/'container.cid').read_text().strip()
    observed=capture.inspect_original(cid);assert observed['status']=='OBSERVED'
    binding=dict(read_record(control/'intent.json'),container_id=cid,cli_identity=read_record(control/'container-cli-start.json')['identity'])
    actual,host,_=capture.validate_container(observed['container'],binding,config,cpu_validation=True)
    assert actual['Status']=='exited' and actual['Pid']==0 and not actual['Running']
    supervisor=read_record(control/'supervisor-start.json')['identity']
    assert observe_original_process(supervisor)['original_live'] is False
    return dict(status=state['status'],stage=str(stage),intent_sha256=intent_sha,container_id=cid,
        container_state=actual,host_config=host,supervisor_terminal=terminal,
        original_supervisor_ended=True,scorer_result_sha256=file_sha(out/'scores.json'),
        new_dispatches_on_duplicate=0,new_dispatches_on_terminal_recovery=0,
        success_new_pairs=2 if state['status']=='ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED' else 0,
        expected_failed_denominator=2 if state['status']=='ORIGINAL_SCORE_FAILED' else 0,
        expected_failed_completed_pairs=1 if state['status']=='ORIGINAL_SCORE_FAILED' else 0)


def probe(stage,output,bounds):
    project=stage.parents[1];reg=read_record(stage/'registration.json');started=time.time()
    assert not output.exists() and reg['host']=='two_card'
    assert all(file_sha(stage/n)==h for n,h in reg['payload_sha256'].items())
    assert all(file_sha(project/'runtime'/n)==h for n,h in reg['runtime_source_sha256'].items())
    scratch=stage/'post-CPU-scratch';scratch.mkdir();tempfile.tempdir=str(scratch)
    tested=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromName(n) for n in (
        'test_cara_source_lifecycle_p1_central_r1','test_cara_source_lifecycle_p1_dispatch_r1',
        'test_cara_source_lifecycle_p1_post_capture_r1','test_cara_source_lifecycle_p1_post_probe_packet_r1',
        'test_cara_source_lifecycle_p1_host_entry_r1','test_cara_source_lifecycle_p1_capture_r1')))
    assert tested.testsRun==31 and tested.wasSuccessful() and not tested.skipped
    fixture_case,packet=fixture.packet()
    try:
        environment=dict(torch_home=str(stage.parent/'wc-time-score-CPU-two_card-r1-20261027/torch'),
            piq_site=str(stage.parent/'wc-time-score-CPU-two_card-r1-20261027/site'),weights_sha256={})
        artifacts=project/'outputs'/(stage.name+'-media');artifacts.mkdir()
        control=stage/'media-control';control.mkdir()
        label=digest(dict(source=reg['parent_git_revision'],stage=str(stage),kind='TWO_NEW_POST_PAIRS'))
        command=old_media_command(project,stage,artifacts,control,environment,label)
        from check_cara_source_lifecycle_fit_host_cpu_r1 import SOURCE as ORIGINAL_MEDIA
        command[command.index(str(stage/ORIGINAL_MEDIA))]=str(stage/SOURCE)
        media_result=execute_media(command,project,stage,artifacts,control,label)
        media_rows=read_record(artifacts/'post-media.json')['files']
        success_packet=prepared_packet(packet,stage,media_rows)
        success=run_score(stage,success_packet,environment,time.monotonic()+600)
        assert success['status']=='ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED'
        failed_stage=stage.with_name(stage.name+'-failure');failed_stage.mkdir(mode=0o700)
        for n,h in reg['payload_sha256'].items():
            path=failed_stage/n;path.parent.mkdir(parents=True,exist_ok=True);os.link(stage/n,path)
        # The immutable source closure is shared; generated CPU controls/outputs
        # have separate namespaces and can never become another GPU experiment.
        copied=copy.deepcopy(reg);copied['stage']=str(failed_stage)
        atomic_json(failed_stage/'registration.json',copied)
        failed_packet=prepared_packet(packet,failed_stage,media_rows,failed=True)
        failed=run_score(failed_stage,failed_packet,environment,time.monotonic()+600)
        assert failed['status']=='ORIGINAL_SCORE_FAILED'
        service_branch=production_service_branch(stage,reg,environment)
        proof=dict(status='ACTUAL_P1_POST_DOCKER_ONCE_RECOVERY_CPU_PASS',source_revision=reg['parent_git_revision'],
            registration_sha256=file_sha(stage/'registration.json'),payload_sha256=reg['payload_sha256'],
            runtime_source_sha256=reg['runtime_source_sha256'],host='two_card',CPU_fixture_only=True,
            started_unix=started,ended_unix=time.time(),parent_bounds=bounds,parent_identity=bind_original_process(os.getpid()),
            tests_run=31,actual_media_container=media_result,actual_post_score_containers=[success,failed],
            production_serve_branch=service_branch,
            logical_quality_positions=52,real_new_metric_pairs=2,simulated_internal_rows=50,
            expected_failed_denominator=2,expected_failed_completed_pairs=1,
            original32_pair_worker_experiment_replayed=False,actual_Cosmos_weights=False,real_V1_video=False,
            whole_GPU_entry_accepted=False,P1_GPU_authorized=False,GPU_submissions=0,ledger_written=False)
        assert all(file_sha(stage/n)==h for n,h in reg['payload_sha256'].items())
        create_record(output,proof)
    finally:fixture_case.doCleanups()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('role',choices=('probe','media'))
    parser.add_argument('--stage',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.role=='media':return media(args.output)
    bounds=host_limits();identity=bind_original_process(os.getpid())
    create_record(args.stage/'host-start.json',dict(identity=identity,parent_bounds=bounds,started_unix=time.time(),CPU_fixture_only=True,GPU_submissions=0))
    error=None
    try:
        deadline=time.monotonic()+30;grant=args.stage/'host-dispatch-grant.json'
        while not grant.exists() and time.monotonic()<deadline:time.sleep(.05)
        assert grant.exists() and read_record(grant)['identity']==identity
        probe(args.stage,args.output,bounds)
    except BaseException as caught:
        error=dict(type=type(caught).__name__,message=str(caught));raise
    finally:create_record(args.stage/'host-terminal.json',dict(identity=identity,ended_unix=time.time(),error=error,
        CPU_fixture_only=True,GPU_submissions=0,ledger_written=False))


if __name__=='__main__':main()
