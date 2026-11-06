"""Metadata/OS-boundary controls only: no model, GPU driver or metric execution."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr.cara_fast_capture_r2 import capture_terminal,capture_scores,file_sha
from wcomr.cara_fast_collection_r2 import freeze_selection
from wcomr.cara_fast_execution_r2 import RUN,PROFILE
from wcomr.cara_fast_post_r2 import calibration_manifest,accept_scores,MODEL_SHA256,SCORER_SOURCES
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_fast_terminal_r2 import settle_original,released_terminal,record,audit_monitor
import test_cara_fast_execution_r2 as execution_fixtures

ROOT=Path(__file__).resolve().parents[1]


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2)+'\n')


def fixture(project):
    """Schematic producer metadata and tiny non-video bytes stay in this tempdir."""
    card,collection=execution_fixtures.complete_fixture()
    stage=project/'.sync/cara-fast-cal-a32-CPU-fixture'
    output=project/'outputs'/RUN
    stage.mkdir(parents=True)
    sources=['src/wcomr/cara_fast_terminal_r2.py','src/wcomr/cara_fast_capture_r2.py',
             'src/wcomr/cara_fast_post_r2.py',*SCORER_SOURCES]
    for name in sources:
        target=stage/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes())
    hashes={name:file_sha(stage/name) for name in sources}
    profile=json.loads((ROOT/PROFILE).read_text())
    write(stage/PROFILE,profile)
    hashes[PROFILE]=file_sha(stage/PROFILE)
    registration=dict(host='two_card',stage=str(stage),source_revision='CPU_METADATA_FIXTURE_ONLY',
                      payload_sha256=hashes,runtime_source_sha256={})
    write(stage/'registration.json',registration)
    cpu=dict(passed=True,critical_source_sha256={sources[0]:hashes[sources[0]]})
    write(stage/'execution-CPU-proof.json',cpu)
    guardian_identity=dict(pid=21234,start_ticks=123,uid=os.getuid())
    launch=dict(run_id=RUN,phase='A',physical_paths=32,whole_GPUh=5,host='two_card',
        gpu_uuid='GPU-CPU-CONTROL',launch_id='CPU_METADATA_NOT_A_GPU_LAUNCH',stage=str(stage),
        source_revision=registration['source_revision'],scope_sha256=card['scope_sha256'],
        registration_sha256=file_sha(stage/'registration.json'),guardian_identity=guardian_identity,
        container=stage.name+'-gpu',model_sha256=MODEL_SHA256)
    authority=dict(launch,direct_user_authorization=True,user_quote='SYNTHETIC UNIT DATA ONLY, NO ACTUAL GPU AUTHORITY',
                   authorizes_phase_B=False,CPU_proof_sha256=file_sha(stage/'execution-CPU-proof.json'))
    write(stage/'pg-GPU-authorization.json',authority)
    launch['authorization_sha256']=file_sha(stage/'pg-GPU-authorization.json')
    write(stage/'GPU-launch.json',launch)
    job=dict(launch,job_id=RUN,forecast_GPUh=4.95,billed_limit_GPUh=5)
    pool=execution_fixtures.ExecutionTests().ledger(project)
    reserved=pool.reserve(job,execution_fixtures.ExecutionTests().gpu())
    envelope=dict(central_ledger_host='four_card',new_reservation=True,job=reserved['jobs'][RUN])
    write(stage/'central-reservation.json',envelope)
    write(stage/'launch-binding.json',dict(authorization_sha256=launch['authorization_sha256'],
          central_reservation_sha256=file_sha(stage/'central-reservation.json')))
    identities=dict(guardian=guardian_identity,container_cli=dict(pid=21235,start_ticks=124),
                    supervisor=dict(pid=21236,start_ticks=125),runner=dict(pid=21237,start_ticks=126,uid=os.getuid()))
    def snapshot(at,active=False,mode='Exclusive_Process'):
        return dict(gpu_uuid=launch['gpu_uuid'],compute_mode=mode,observed_unix=at,mps_processes=[],
                    compute_apps=[dict(identities['runner'],gpu_uuid=launch['gpu_uuid'])] if active else [])
    guardian=dict(status='FAST_A32_HOST_GUARDIAN_TERMINAL',container_exit_code=0,identity=guardian_identity,
        container_cli_identity=identities['container_cli'],mode_restoration=dict(restored=True),
        mode_admission=dict(verified_snapshot=snapshot(1000)),
        **{key:launch[key] for key in ('run_id','launch_id','gpu_uuid','source_revision')})
    write(stage/'pg-host-guardian.json',guardian)
    write(stage/'pg-runner-context-ready.json',dict(identity=identities['runner'],GPU_context_held=True,
          source_revision=launch['source_revision']))
    write(stage/'pg-runner-context-granted.json',dict(runner=identities['runner'],gpu_uuid=launch['gpu_uuid'],
          source_revision=launch['source_revision']))
    inputs={row['name']:row for row in card['inputs']}
    for row in collection['rows']:
        slot=row['slot']
        video=output/'A'/slot['id']/(slot['member']+'.mp4')
        video.parent.mkdir(parents=True)
        video.write_bytes(('CPU_METADATA_NOT_VIDEO_'+slot['id']).encode())
        tensor=output/'A'/(slot['id']+'.pt')
        tensor.write_bytes(b'CPU_METADATA_NOT_A_TENSOR')
        row['result']['video_path']=str(video)
        row['result']['eligible_clean_time']=slot['eligible_clean_time']
        row['tensor_artifact']=dict(path=str(tensor),sha256=file_sha(tensor),bytes=tensor.stat().st_size)
        arguments={key:value for key,value in inputs[slot['member']].items() if key!='partition'}
        arguments.update(seed=slot['seed'],num_steps=card['roles'][slot['role']]['requested_steps'],
                         prompt_path=None,input_path=None,enable_autoregressive=False,chunk_size=77,chunk_overlap=1)
        write(video.with_suffix('.json'),arguments)
    write(output/'A-collection.json',collection)
    billing=dict(status='FAST_A32_ORIGINAL_WALL_BILL',wall_seconds=10.,actual_GPUh=10/3600,billed_limit_GPUh=5,
        **{key:launch[key] for key in ('run_id','phase','host','gpu_uuid','launch_id','source_revision','scope_sha256')})
    write(output/'A-billing.json',billing)
    supervisor=dict(status='FAST_A32_TERMINAL_CENTRAL_SETTLEMENT_PENDING',child_exit_code=0,
        supervisor_identity=identities['supervisor'],child_identity=identities['runner'],started_unix=1000.,
        observations=3,exclusive_monitor_accepted=True,phase_state_sha256=digest(collection),
        **{key:launch[key] for key in ('run_id','phase','host','gpu_uuid','launch_id','source_revision','scope_sha256')})
    write(output/'A-supervisor.json',supervisor)
    pending=dict(GPU_released=True,original_process_exited=True,technical_accepted=True,cost_settled=False,
        phase_state_sha256=digest(collection),billing_sha256=file_sha(output/'A-billing.json'),final_snapshot=snapshot(1010),
        **{key:launch[key] for key in ('run_id','phase','host','gpu_uuid','launch_id','scope_sha256')})
    write(output/'A-release-pending-central.json',pending)
    write(output/'A-model-precision.json',dict(model_precision='torch.bfloat16',use_wan_fp32_strategy=True))
    write(output/'A-runner.json',dict(status='TERMINAL'))
    monitor=[dict(run_id=RUN,launch_id=launch['launch_id'],runner=identities['runner'],
        monotonic_elapsed=elapsed,context_granted=active,snapshot=snapshot(1000+elapsed,active),
        thermal={'temperature.gpu':'50','fan.speed':'60','clocks_event_reasons.active':'0x0'})
        for elapsed,active in [(0.5,False),(4.,True),(8.,True)]]
    (output/'A-exclusive-monitor.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in monitor))
    for suffix in ('.lock','.mode-owner.lock'):
        path=project/'.sync/gpu-locks'/(launch['gpu_uuid']+suffix)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.touch()
    image='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
    docker=dict(State=dict(Status='exited',Running=False,ExitCode=0,OOMKilled=False,Pid=0),Image=image,
        Config=dict(Labels={'wcomr.manifest':launch['registration_sha256']}),
        HostConfig=dict(DeviceRequests=[dict(DeviceIDs=[launch['gpu_uuid']])],ReadonlyRootfs=True,
            PidMode='host',NetworkMode='none',NanoCpus=2*10**9,Memory=profile['GPU_container']['memory_GiB']*1024**3))
    current=snapshot(2000,False,'Default')
    # A different user may legitimately start after this job restored Default.
    current['compute_apps']=[dict(pid=987654,start_ticks=9999,uid=os.getuid()+1)]
    inspected=type('Inspected',(),dict(returncode=0,stdout=json.dumps([docker])))()
    with patch('wcomr.cara_fast_capture_r2.subprocess.run',return_value=inspected),\
            patch('wcomr.cara_fast_capture_r2.same_live_process',return_value=False),\
            patch('wcomr.cara_fast_capture_r2.observe',return_value=current):
        capture=capture_terminal(project,stage,file_sha(stage/'GPU-launch.json'))
    return card,capture,pool,stage,output,docker


def score_fixture(capture,card,settlement):
    manifest=calibration_manifest(capture,card,settlement)
    raw=json.loads((ROOT/'reports/cara_fast_score_cli_two_card_raw_receipts_r2_20261028.json').read_text())
    original=raw['files']['scoring-control-result.json']['data']['rows'][0]
    rows=[dict(copy.deepcopy(original),id=pair['id'],member=pair['candidate']['member'],role=pair['candidate']['role'],
               candidate=copy.deepcopy(pair['candidate']),reference=copy.deepcopy(pair['reference'])) for pair in manifest['pairs']]
    manifest_sha=digest(manifest)
    result=dict(status='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED',scope_sha256=manifest['scope_sha256'],
        protocol_sha256=manifest['protocol_sha256'],manifest_sha256=manifest_sha,
        worker_sha256=manifest['scorer_source_sha256'][SCORER_SOURCES[0]],rows=rows,
        registered_pairs=[row['id'] for row in rows],CUDA_initialized=False,GPU_submissions=0,
        CPU_METADATA_FIXTURE_ONLY_NO_METRIC_EXECUTION=True)
    execution=dict(container_state=dict(Status='exited',ExitCode=0,Running=False,OOMKilled=False),
        host_config=dict(NanoCpus=2*10**9,Memory=8*1024**3,DeviceRequests=None,NetworkMode='none',ReadonlyRootfs=True),
        manifest_sha256=manifest_sha,manifest_label_sha256=manifest_sha,
        source_actual_sha256=manifest['scorer_source_sha256'],container_wall_seconds=90.)
    return manifest,manifest_sha,result,execution


class PostTests(unittest.TestCase):
    def test_complete_terminal_settle_all12_accept_and_freeze_once(self):
        with tempfile.TemporaryDirectory() as directory:
            card,capture,pool,stage,_,_=fixture(Path(directory))
            before=pool.read()
            settlement=settle_original(pool,capture,card)
            self.assertEqual(settlement['central_after']['reserved_gpu_hours'],16.5)
            self.assertAlmostEqual(settlement['central_after']['used_gpu_hours'],before['used_gpu_hours']+10/3600)
            release=released_terminal(capture,card,settlement)
            self.assertTrue(release['technical_accepted'])
            self.assertTrue(release['GPU_released'])
            self.assertTrue(capture['current_GPU_snapshot']['compute_apps'])
            manifest,sha,result,execution=score_fixture(capture,card,settlement)
            self.assertEqual(len(manifest['pairs']),12)
            native_k=next(pair for pair in manifest['pairs'] if pair['candidate']['role']=='NATIVE22')
            self.assertNotEqual(native_k['candidate']['execution_request_sha256'],native_k['reference']['execution_request_sha256'])
            accepted=accept_scores(capture,card,settlement,manifest,sha,result,execution)
            frozen=freeze_selection(card,record(capture,'collection'),release,accepted,stage/'frozen.json')
            self.assertEqual(set(frozen['selected']),{'WC','RA','NATIVE_K'})
            self.assertFalse(frozen['authorizes_phase_B'])
            self.assertFalse(frozen['CHECK_accessed'])
            repeated=settle_original(pool,capture,card)
            self.assertEqual(repeated['central_before'],repeated['central_after'])
            with self.assertRaises(ValueError):
                freeze_selection(card,record(capture,'collection'),release,accepted,stage/'frozen.json')

    def test_failed_run_still_settles_but_scoring_is_blocked(self):
        for kind in ('child','partial','monitor','arguments','artifact','overrun'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                card,capture,pool,_,_,_=fixture(Path(directory))
                bad=copy.deepcopy(capture)
                def replace(key,change):
                    data=record(bad,key)
                    change(data)
                    raw=json.dumps(data)
                    bad['files'][key].update(raw_utf8=raw,bytes=len(raw.encode()),sha256=hashlib.sha256(raw.encode()).hexdigest())
                if kind=='child':replace('supervisor',lambda row:row.update(child_exit_code=7,exclusive_monitor_accepted=False))
                elif kind=='partial':replace('collection',lambda row:row['rows'].pop())
                elif kind=='monitor':bad['monitor_audit']['passed']=False
                elif kind=='arguments':
                    key=next(iter(bad['artifacts']))
                    meta=bad['artifacts'][key]['arguments']
                    arguments=json.loads(meta['raw_utf8']);arguments['guidance']=8
                    raw=json.dumps(arguments)
                    meta.update(raw_utf8=raw,bytes=len(raw.encode()),sha256=hashlib.sha256(raw.encode()).hexdigest())
                elif kind=='artifact':bad['artifacts'].pop(next(iter(bad['artifacts'])))
                else:
                    replace('billing',lambda row:row.update(wall_seconds=18001.,actual_GPUh=18001/3600))
                settlement=settle_original(pool,bad,card)
                release=released_terminal(bad,card,settlement)
                self.assertTrue(release['cost_settled'])
                self.assertFalse(release['technical_accepted'])
                with self.assertRaises(ValueError):calibration_manifest(bad,card,settlement)
                if kind=='overrun':self.assertTrue(settlement['central_after']['budget_overrun_recorded'])

    def test_unknown_handles_mixed_bill_and_foreign_ledger_refuse_without_write(self):
        for kind in ('live','unknown','bill_hash','other_job','origin'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                card,capture,pool,_,_,_=fixture(Path(directory))
                before=pool.path.read_bytes()
                if kind in ('live','unknown'):
                    capture['original_live_handles']['runner']=True if kind=='live' else None
                    with self.assertRaises(ValueError):settle_original(pool,capture,card)
                    self.assertEqual(pool.path.read_bytes(),before)
                elif kind=='bill_hash':
                    capture['files']['billing']['sha256']='0'*64
                    with self.assertRaises(ValueError):settle_original(pool,capture,card)
                    self.assertEqual(pool.path.read_bytes(),before)
                else:
                    settlement=settle_original(pool,capture,card)
                    if kind=='other_job':
                        settlement['central_after']['jobs']['old-uncertainty-0']['billed_limit_GPUh']=1
                    else:settlement['central_after']['origin_used_gpu_hours']+=1
                    settlement['central_after'].update(pool.accounting(settlement['central_after']))
                    with self.assertRaises(ValueError):released_terminal(capture,card,settlement)

    def test_scores_reject_partial_wrong_references_dirty_execution_and_bad_reductions(self):
        with tempfile.TemporaryDirectory() as directory:
            card,capture,pool,_,_,_=fixture(Path(directory))
            settlement=settle_original(pool,capture,card)
            base=score_fixture(capture,card,settlement)
            for kind in ('partial','reference','comparison','curve','reduction','PTS','PSNR','gradient','CPU_live','GPU_visible','CPU_time'):
                with self.subTest(kind=kind):
                    manifest,sha,result,execution=copy.deepcopy(base)
                    if kind=='partial':result['rows'].pop()
                    elif kind=='reference':result['rows'][0]['reference']['slot_id']='DIAGNOSTIC_NOT_A_CLEAN_ANCHOR'
                    elif kind=='comparison':manifest['pairs'][0]['candidate']['comparison_input_sha256']='0'*64
                    elif kind=='curve':result['rows'][0]['Alex_frames'].pop()
                    elif kind=='reduction':result['rows'][0]['Alex']=1
                    elif kind=='PTS':result['rows'][0]['PTS_equal']=False
                    elif kind=='PSNR':result['rows'][0]['PSNR_video_dB']=99
                    elif kind=='gradient':result['rows'][0]['gradient_energy_ratio']=2
                    elif kind=='CPU_live':execution['container_state']['Running']=True
                    elif kind=='GPU_visible':execution['host_config']['DeviceRequests']=[dict(DeviceIDs=['GPU-CPU-CONTROL'])]
                    else:execution['container_wall_seconds']=7201
                    with self.assertRaises(ValueError):
                        accept_scores(capture,card,settlement,manifest,sha,result,execution)

    def test_reader_recovers_original_complete_result_and_never_rescans(self):
        with tempfile.TemporaryDirectory() as directory:
            card,capture,_,stage,output,_=fixture(Path(directory))
            (output/'A-exclusive-monitor.jsonl').unlink()
            with patch('wcomr.cara_fast_capture_r2.subprocess.run',side_effect=AssertionError('No second observer')):
                recovered=capture_terminal(Path(directory),stage,file_sha(stage/'GPU-launch.json'))
            self.assertEqual(recovered,capture)

    def test_live_GPU_or_live_stopped_reader_never_returns_partial_scientific_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            _,_,_,stage,_,docker=fixture(Path(directory))
            launch_sha=file_sha(stage/'GPU-launch.json')
            (stage/'A-terminal-capture.json').unlink()
            with patch('wcomr.cara_fast_capture_r2.subprocess.run',side_effect=AssertionError('No new observer')):
                for live,status in [(True,'FAST_A32_TERMINAL_READER_LIVE'),(False,'FAST_A32_TERMINAL_READER_STOPPED_NO_RETRY')]:
                    with patch('wcomr.cara_fast_capture_r2.same_live_process',return_value=live):
                        result=capture_terminal(Path(directory),stage,launch_sha)
                    self.assertEqual(result['status'],status)
                    self.assertFalse(result['scientific_rows_returned'])
            (stage/'A-terminal-capture-intent.json').unlink()
            docker['State']['Running']=True
            inspected=type('Inspected',(),dict(returncode=0,stdout=json.dumps([docker])))()
            with patch('wcomr.cara_fast_capture_r2.subprocess.run',return_value=inspected),\
                    patch('wcomr.cara_fast_capture_r2.same_live_process',return_value=True),\
                    patch('wcomr.cara_fast_capture_r2.observe',side_effect=AssertionError('No terminal GPU audit yet')):
                result=capture_terminal(Path(directory),stage,launch_sha)
            self.assertFalse(result['scientific_rows_returned'])
            self.assertNotIn('files',result)
            self.assertFalse((stage/'A-terminal-capture-intent.json').exists())

    def test_monitor_rejects_gaps_foreign_context_and_thermal_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            _,capture,_,stage,output,_=fixture(Path(directory))
            original=[json.loads(line) for line in (output/'A-exclusive-monitor.jsonl').read_text().splitlines()]
            for kind in ('gap','foreign','thermal'):
                rows=copy.deepcopy(original)
                if kind=='gap':rows[-1]['monotonic_elapsed']=100
                elif kind=='foreign':rows[-1]['snapshot']['compute_apps'][0]['pid']+=1
                else:rows[-1]['thermal']['temperature.gpu']='90'
                with self.subTest(kind=kind),self.assertRaises(ValueError):
                    audit_monitor(rows,record(capture,'launch'),record(capture,'supervisor'),record(capture,'billing'),
                                  record(capture,'ready'),record(capture,'grant'),record(capture,'pending_release'))

    def test_settlement_preserves_a_later_authorized_central_cap(self):
        with tempfile.TemporaryDirectory() as directory:
            card,capture,pool,_,_,_=fixture(Path(directory))
            with pool.transaction() as value:
                value['cap_gpu_hours']=250
                pool.commit(value,dict(type='CPU_FIXTURE_LATER_APPROVED_CAP_CHANGE'))
            settlement=settle_original(pool,capture,card)
            self.assertEqual(settlement['central_before']['cap_gpu_hours'],250)
            self.assertEqual(settlement['central_after']['cap_gpu_hours'],250)
            self.assertTrue(released_terminal(capture,card,settlement)['technical_accepted'])

    def test_scoring_capture_uses_actual_container_source_and_complete_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            card,capture,pool,stage,output,docker=fixture(project)
            settlement=settle_original(pool,capture,card)
            manifest,_,result,_=score_fixture(capture,card,settlement)
            path=output/'A-score-CPU/manifest.json'
            write(path,manifest)
            result['manifest_sha256']=file_sha(path)
            write(path.parent/'scores.json',result)
            docker['Config']['Labels']['wcomr.manifest']=file_sha(path)
            docker['State'].update(StartedAt='2026-10-28T12:00:00.123456789Z',FinishedAt='2026-10-28T12:01:30.123456789Z')
            docker['HostConfig'].update(Memory=8*1024**3,DeviceRequests=None)
            for running in (True,False):
                docker['State']['Running']=running
                inspected=type('Inspected',(),dict(returncode=0,stdout=json.dumps([docker])))()
                with patch('wcomr.cara_fast_capture_r2.subprocess.run',return_value=inspected):
                    observed=capture_scores(project,stage,path,file_sha(path))
                if running:
                    self.assertFalse(observed['scientific_rows_returned'])
                    self.assertNotIn('files',observed)
                else:
                    accepted=accept_scores(capture,card,settlement,manifest,file_sha(path),record(observed,'scores'),observed['execution'])
                    self.assertEqual(len(accepted['rows']),12)
                    self.assertEqual(observed['execution']['container_wall_seconds'],90)

    def test_CPU_command_exposes_no_GPU_and_preserves_source_artifacts_readonly(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            card,capture,pool,stage,output,_=fixture(project)
            settlement=settle_original(pool,capture,card)
            path=output/'A-score-CPU/manifest.json'
            write(path,calibration_manifest(capture,card,settlement))
            spec=importlib.util.spec_from_file_location('postprocess_fast',ROOT/'scripts/postprocess_cara_fast_r2.py')
            module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
            command=module.score_command(project,stage,path,path.parent)
            self.assertNotIn('--gpus',command)
            self.assertIn('CUDA_VISIBLE_DEVICES=',command)
            self.assertIn('NVIDIA_VISIBLE_DEVICES=void',command)
            self.assertEqual(command[command.index('--memory')+1],'8g')
            self.assertEqual(command[command.index('--cpus')+1],'2')
            self.assertIn('wcomr.manifest='+file_sha(path),command)
            for bound in (project,stage,output):self.assertIn(str(bound)+':'+str(bound)+':ro',command)
            self.assertIn(str(path.parent)+':'+str(path.parent)+':rw',command)

    def test_late_GPU_probe_failure_cannot_block_original_finance_or_release(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            card,_,pool,stage,_,docker=fixture(project)
            (stage/'A-terminal-capture-intent.json').unlink()
            (stage/'A-terminal-capture.json').unlink()
            inspected=type('Inspected',(),dict(returncode=0,stdout=json.dumps([docker])))()
            with patch('wcomr.cara_fast_capture_r2.subprocess.run',return_value=inspected),\
                    patch('wcomr.cara_fast_capture_r2.same_live_process',return_value=False),\
                    patch('wcomr.cara_fast_capture_r2.observe',side_effect=OSError('DECLARED_LATE_PROBE_FAILURE')):
                capture=capture_terminal(project,stage,file_sha(stage/'GPU-launch.json'))
            self.assertTrue(capture['current_GPU_snapshot']['observation_unavailable'])
            settlement=settle_original(pool,capture,card)
            self.assertTrue(released_terminal(capture,card,settlement)['technical_accepted'])


if __name__=='__main__':
    unittest.main()
