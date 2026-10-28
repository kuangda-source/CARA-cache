"""B metadata fixtures only; GPU I/O is simulated, original A bytes stay unchanged."""
import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr.cara_fast_b36_capture_r1 import capture_terminal,capture_scores,file_sha,captured_file
from wcomr.cara_fast_b36_execution_r1 import RUN,PROFILE,load_handoff
from wcomr.cara_fast_b36_post_r1 import formal_manifest,new_pairs_manifest,assemble_scores,accept_scores,SCORER_SOURCES
from wcomr.cara_fast_b36_terminal_r1 import settle_original,released_terminal,record,audit_monitor,container_record
from wcomr.cara_fast_b36_r1 import COMMON_SOURCES
from wcomr.cara_fast_spec_r1 import digest
from test_cara_fast_b36_execution_r1 import real_binding,complete_fixture,BoundaryTests,script

ROOT=Path(__file__).resolve().parents[1]


def write(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def fixture(project):
    """Schematic producer metadata and tiny non-video bytes stay in this tempdir."""
    card,bound=real_binding()
    collection=complete_fixture(card,bound)
    stage=project/'.sync/cara-fast-f19-b36-CPU-fixture'
    output=project/'outputs'/RUN
    stage.mkdir(parents=True)
    sources=[*COMMON_SOURCES,'src/wcomr/cara_fast_b36_terminal_r1.py','src/wcomr/cara_fast_b36_capture_r1.py',
             'src/wcomr/cara_fast_b36_post_r1.py',*SCORER_SOURCES,'scripts/dispatch_cara_fast_b36_score_cpu_r2.py',
             'scripts/postprocess_cara_fast_b36_r1.py','plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
             'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json']
    profile=json.loads((ROOT/PROFILE).read_text())
    sources+=list(descriptor['path'] for descriptor in profile['A32_handoff_files'].values())
    for name in sources:
        target=stage/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/name).read_bytes())
    hashes={name:file_sha(stage/name) for name in sources}
    profile=json.loads((ROOT/PROFILE).read_text())
    write(stage/PROFILE,profile)
    bound=load_handoff(stage,card,profile)
    hashes[PROFILE]=file_sha(stage/PROFILE)
    registration=dict(host='two_card',stage=str(stage),source_revision='CPU_METADATA_FIXTURE_ONLY',
                      payload_sha256=hashes,runtime_source_sha256=bound['A_runtime_source_sha256'])
    write(stage/'registration.json',registration)
    cpu=dict(passed=True,critical_source_sha256={sources[0]:hashes[sources[0]]})
    write(stage/'execution-CPU-proof.json',cpu)
    core=dict(passed=True,critical_source_sha256={name:file_sha(stage/name) for name in COMMON_SOURCES})
    write(stage/'B36-core-CPU-proof.json',core)
    guardian_identity=dict(pid=21234,start_ticks=123,uid=os.getuid())
    launch=dict(run_id=RUN,phase='B',physical_paths=36,whole_GPUh=5.5,host='two_card',
        gpu_uuid=bound['gpu_uuid'],launch_id='CPU_METADATA_NOT_A_GPU_LAUNCH',stage=str(stage),
        source_revision=registration['source_revision'],scope_sha256=card['scope_sha256'],
        registration_sha256=file_sha(stage/'registration.json'),guardian_identity=guardian_identity,
        container=stage.name+'-gpu',model_sha256=bound['A_model_sha256'],
        A_launch_id=bound['A_launch_id'],frozen_file_sha256=bound['frozen_file_sha256'])
    authority=dict(launch,direct_user_authorization=True,user_quote='SYNTHETIC UNIT DATA ONLY, NO ACTUAL GPU AUTHORITY',
                   new_B36_authorization=True,authorizes_replay=False,CPU_proof_sha256=file_sha(stage/'execution-CPU-proof.json'),
                   core_CPU_proof_sha256=file_sha(stage/'B36-core-CPU-proof.json'))
    write(stage/'pg-GPU-authorization.json',authority)
    launch['authorization_sha256']=file_sha(stage/'pg-GPU-authorization.json')
    write(stage/'GPU-launch.json',launch)
    job=dict(launch,job_id=RUN,forecast_GPUh=5.022,billed_limit_GPUh=5.5)
    pool=BoundaryTests().pool(project)
    gpu=dict(uuid=bound['gpu_uuid'],name='NVIDIA RTX A6000',compute_cap='8.6',pids=[],utilization_percent=0,memory_used_mib=24,unix=__import__('time').time())
    reserved=pool.reserve(job,gpu,bound)
    envelope=dict(central_ledger_host='four_card',new_reservation=True,job=reserved['jobs'][RUN])
    write(stage/'central-reservation.json',envelope)
    write(stage/'launch-binding.json',dict(authorization_sha256=launch['authorization_sha256'],
          central_reservation_sha256=file_sha(stage/'central-reservation.json'),A_handoff_package_sha256=bound['package_sha256']))
    identities=dict(guardian=guardian_identity,container_cli=dict(pid=21235,start_ticks=124),
                    supervisor=dict(pid=21236,start_ticks=125),runner=dict(pid=21237,start_ticks=126,uid=os.getuid()))
    def snapshot(at,active=False,mode='Exclusive_Process'):
        return dict(gpu_uuid=launch['gpu_uuid'],compute_mode=mode,observed_unix=at,mps_processes=[],
                    compute_apps=[dict(identities['runner'],gpu_uuid=launch['gpu_uuid'])] if active else [])
    guardian=dict(status='FAST_B36_HOST_GUARDIAN_TERMINAL',container_exit_code=0,identity=guardian_identity,
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
        video=output/'B'/slot['id']/(slot['member']+'.mp4')
        video.parent.mkdir(parents=True)
        video.write_bytes(('CPU_METADATA_NOT_VIDEO_'+slot['id']).encode())
        tensor=output/'B'/(slot['id']+'.pt')
        tensor.write_bytes(b'CPU_METADATA_NOT_A_TENSOR')
        row['result']['video_path']=str(video)
        row['result']['eligible_clean_time']=slot['eligible_clean_time']
        row['tensor_artifact']=dict(path=str(tensor),sha256=file_sha(tensor),bytes=tensor.stat().st_size)
        arguments={key:value for key,value in inputs[slot['member']].items() if key!='partition'}
        arguments.update(seed=slot['seed'],num_steps=card['roles'][row['result']['concrete_role']]['requested_steps'],
                         prompt_path=None,input_path=None,enable_autoregressive=False,chunk_size=77,chunk_overlap=1)
        write(video.with_suffix('.json'),arguments)
    write(output/'B-collection.json',collection)
    billing=dict(status='FAST_B36_ORIGINAL_WALL_BILL',wall_seconds=10.,actual_GPUh=10/3600,billed_limit_GPUh=5.5,
        **{key:launch[key] for key in ('run_id','phase','host','gpu_uuid','launch_id','source_revision','scope_sha256')})
    billing.update(started_monotonic=1000.,ended_monotonic=1010.,billing_clock_owner='HOST_GUARDIAN',wall_interval_complete=True)
    write(stage/'B-billing.json',billing)
    interval=dict(wall_seconds=9.,started_monotonic=1000.5,ended_monotonic=1009.5,central_cost_owner='HOST_GUARDIAN',
        **{key:launch[key] for key in ('run_id','phase','host','gpu_uuid','launch_id','source_revision','scope_sha256')})
    write(output/'B-supervisor-billing.json',interval)
    supervisor=dict(status='FAST_B36_TERMINAL_CENTRAL_SETTLEMENT_PENDING',child_exit_code=0,
        supervisor_identity=identities['supervisor'],child_identity=identities['runner'],started_unix=1000.,
        observations=3,exclusive_monitor_accepted=True,phase_state_sha256=digest(collection),
        **{key:launch[key] for key in ('run_id','phase','host','gpu_uuid','launch_id','source_revision','scope_sha256')})
    write(output/'B-supervisor.json',supervisor)
    pending=dict(GPU_released=True,original_process_exited=True,technical_accepted=True,cost_settled=False,
        phase_state_sha256=digest(collection),supervisor_billing_sha256=file_sha(output/'B-supervisor-billing.json'),final_snapshot=snapshot(1010),
        **{key:launch[key] for key in ('run_id','phase','host','gpu_uuid','launch_id','scope_sha256')})
    write(output/'B-release-pending-central.json',pending)
    write(output/'B-model-precision.json',bound['A_precision'])
    write(output/'B-runner.json',dict(status='TERMINAL'))
    monitor=[dict(run_id=RUN,launch_id=launch['launch_id'],runner=identities['runner'],
        monotonic_elapsed=elapsed,context_granted=active,snapshot=snapshot(1000+elapsed,active),
        thermal={'temperature.gpu':'50','fan.speed':'60','clocks_event_reasons.active':'0x0'})
        for elapsed,active in [(0.5,False),(4.,True),(8.,True)]]
    (output/'B-exclusive-monitor.jsonl').write_text(''.join(json.dumps(row)+'\n' for row in monitor))
    for suffix in ('.lock','.mode-owner.lock'):
        path=project/'.sync/gpu-locks'/(launch['gpu_uuid']+suffix)
        path.parent.mkdir(parents=True,exist_ok=True)
        path.touch()
    image='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
    docker=dict(Id='CPU-ONLY-CONTAINER',State=dict(Status='exited',Running=False,ExitCode=0,OOMKilled=False,Pid=0),Image=image,
        Config=dict(Labels={'wcomr.manifest':launch['registration_sha256']}),
        HostConfig=dict(DeviceRequests=[dict(DeviceIDs=[launch['gpu_uuid']])],ReadonlyRootfs=True,
            PidMode='host',NetworkMode='none',NanoCpus=2*10**9,Memory=profile['GPU_container']['memory_GiB']*1024**3))
    guardian.update(started_monotonic=1000.,ended_monotonic=1010.,billing_sha256=file_sha(stage/'B-billing.json'),
        container_dispatch_state='STARTED',container_terminal_witness=dict(kind='BOUND_CONTAINER_TERMINAL',complete=True,
            container=container_record(docker)),
        **{key:launch[key] for key in ('phase','host','scope_sha256')})
    write(stage/'pg-host-guardian.json',guardian)
    write(stage/'B-supervisor-start.json',dict(identity=identities['supervisor'],runner_dispatch_state='NOT_ATTEMPTED'))
    write(stage/'B-runner-intent.json',dict(launch_id=launch['launch_id'],supervisor_identity=identities['supervisor'],no_replay=True))
    write(stage/'B-runner-start.json',dict(identity=identities['runner'],launch_id=launch['launch_id']))
    current=snapshot(2000,False,'Default')
    # A different user may legitimately start after this job restored Default.
    current['compute_apps']=[dict(pid=987654,start_ticks=9999,uid=os.getuid()+1)]
    inspected=type('Inspected',(),dict(returncode=0,stdout=json.dumps([docker])))()
    actual_sha=file_sha
    def controlled_sha(path):
        path=Path(path)
        if project/'runtime' in path.parents:return bound['A_runtime_source_sha256'][str(path.relative_to(project/'runtime'))]
        return actual_sha(path)
    with patch('wcomr.cara_fast_b36_capture_r1.file_sha',side_effect=controlled_sha),\
            patch('wcomr.cara_fast_b36_capture_r1.subprocess.run',return_value=inspected),\
            patch('wcomr.cara_fast_b36_capture_r1.same_live_process',return_value=False),\
            patch('wcomr.cara_fast_b36_capture_r1.observe',return_value=current):
        capture=capture_terminal(project,stage,file_sha(stage/'GPU-launch.json'))
    return card,capture,pool,stage,output,docker


def score_fixture(capture,card,settlement,output):
    manifest=formal_manifest(capture,card,settlement)
    path=output/'B-score-CPU/manifest.json'
    write(path,manifest)
    inner=new_pairs_manifest(manifest)
    inner_path=path.parent/'new-pairs-manifest.json'
    write(inner_path,inner)
    raw=json.loads((ROOT/'reports/cara_fast_score_cli_two_card_raw_receipts_r2_20261028.json').read_text())
    template=raw['files']['scoring-control-result.json']['data']['rows'][0]
    rows=[dict(copy.deepcopy(template),id=pair['id'],member=pair['candidate']['member'],
               role=pair['candidate']['role'],candidate=copy.deepcopy(pair['candidate']),
               reference=copy.deepcopy(pair['reference'])) for pair in inner['pairs']]
    new=dict(status='COMPLETE_NOT_INDEPENDENTLY_ACCEPTED',scope_sha256=manifest['scope_sha256'],
        protocol_sha256=manifest['protocol_sha256'],manifest_sha256=file_sha(inner_path),
        worker_sha256=manifest['scorer_source_sha256'][SCORER_SOURCES[0]],rows=rows,
        registered_pairs=[row['id'] for row in rows],CUDA_initialized=False,GPU_submissions=0,
        CPU_METADATA_FIXTURE_ONLY_NO_METRIC_EXECUTION=True)
    new_path=path.parent/'new-scores.json'
    write(new_path,new)
    result=assemble_scores(manifest,file_sha(path),inner,file_sha(inner_path),new,file_sha(new_path))
    write(path.parent/'scores.json',result)
    observed=dict(container_state=dict(Status='exited',ExitCode=0,Running=False,OOMKilled=False),
        host_config=dict(NanoCpus=2*10**9,Memory=8*1024**3,MemorySwap=8*1024**3,CpusetCpus='26,27',
            DeviceRequests=None,NetworkMode='none',ReadonlyRootfs=True),
        manifest_sha256=file_sha(path),manifest_label_sha256=file_sha(path),
        source_actual_sha256=manifest['scorer_source_sha256'],container_wall_seconds=90.)
    return manifest,file_sha(path),result,observed,captured_file(inner_path),captured_file(new_path)


def accepted(capture,card,settlement,inputs):
    manifest,sha,result,execution,new_manifest,new_scores=inputs
    return accept_scores(capture,card,settlement,manifest,sha,result,execution,
                         new_manifest=new_manifest,new_scores=new_scores)


def replace_record(capture,key,change):
    data=record(capture,key)
    change(data)
    raw=json.dumps(data)
    capture['files'][key].update(raw_utf8=raw,bytes=len(raw.encode()),sha256=hashlib.sha256(raw.encode()).hexdigest())


class PostTests(unittest.TestCase):
    def test_complete_B_settle_once_accept32_and_reuse_six_original_scores(self):
        with tempfile.TemporaryDirectory() as directory:
            card,capture,pool,_,output,_=fixture(Path(directory))
            before=pool.read()
            settlement=settle_original(pool,capture,card)
            self.assertEqual(settlement['central_after']['reserved_gpu_hours'],16.5)
            self.assertTrue(released_terminal(capture,card,settlement)['technical_accepted'])
            original_A=settlement['central_after']['jobs']['cara-fast-cal-a32-r2-20261028']
            self.assertEqual(original_A,before['jobs']['cara-fast-cal-a32-r2-20261028'])
            inputs=score_fixture(capture,card,settlement,output)
            manifest=inputs[0]
            result=accepted(capture,card,settlement,inputs)
            self.assertEqual(len(result['rows']),32)
            self.assertEqual(sum(row['candidate']['reused_from_A'] for row in result['rows']),8)
            self.assertEqual(len(new_pairs_manifest(manifest)['pairs']),26)
            reused=[row for row in result['rows'] if 'reused_A_score_id' in row]
            old={row['id']:row for row in record(capture['A32_handoff'],'accepted_scores')['rows']}
            self.assertEqual(len(reused),6)
            for row in reused:
                self.assertEqual(row['Alex_frames'],old[row['reused_A_score_id']]['Alex_frames'])
                self.assertEqual(row['MSE_video'],old[row['reused_A_score_id']]['MSE_video'])
            self.assertEqual(result['frozen_baseline_time_match'],{'WC':'UNMATCHED','RA':'UNMATCHED','NATIVE_K':'MATCHED'})
            repeated=settle_original(pool,capture,card)
            self.assertEqual(repeated['central_before'],repeated['central_after'])

    def test_failed_B_retains_actual_cost_and_denominator_but_cannot_score(self):
        for kind in ('child','partial','monitor','arguments','artifact','precision','overrun'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                card,capture,pool,_,_,_=fixture(Path(directory))
                if kind=='child':replace_record(capture,'supervisor',lambda row:row.update(child_exit_code=7,exclusive_monitor_accepted=False))
                elif kind=='partial':replace_record(capture,'collection',lambda row:row['rows'].pop())
                elif kind=='monitor':capture['monitor_audit']['passed']=False
                elif kind=='artifact':capture['artifacts'].pop(next(iter(capture['artifacts'])))
                elif kind=='precision':replace_record(capture,'precision',lambda row:row.update(outer_autocast=True))
                elif kind=='overrun':
                    replace_record(capture,'billing',lambda row:row.update(wall_seconds=19801.,actual_GPUh=19801/3600,ended_monotonic=20801.))
                    replace_record(capture,'guardian',lambda row:row.update(ended_monotonic=20801.,billing_sha256=capture['files']['billing']['sha256']))
                else:
                    key=next(iter(capture['artifacts']))
                    packet=capture['artifacts'][key]['arguments']
                    value=json.loads(packet['raw_utf8']);value['guidance']=8
                    raw=json.dumps(value)
                    packet.update(raw_utf8=raw,bytes=len(raw.encode()),sha256=hashlib.sha256(raw.encode()).hexdigest())
                settlement=settle_original(pool,capture,card)
                release=released_terminal(capture,card,settlement)
                self.assertTrue(release['cost_settled'])
                self.assertFalse(release['technical_accepted'])
                with self.assertRaises(ValueError):formal_manifest(capture,card,settlement)
                if kind=='overrun':self.assertTrue(settlement['central_after']['budget_overrun_recorded'])

    def test_unknown_live_mixed_A_and_billing_hash_never_mutate_ledger(self):
        for kind in ('live','unknown','A_frozen','bill_hash','different_UUID'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                card,capture,pool,_,_,_=fixture(Path(directory))
                if kind in ('live','unknown'):capture['original_live_handles']['runner']=True if kind=='live' else None
                elif kind=='A_frozen':capture['A32_handoff']['files']['frozen']['sha256']='0'*64
                elif kind=='bill_hash':capture['files']['billing']['sha256']='0'*64
                else:replace_record(capture,'launch',lambda row:row.update(gpu_uuid='GPU-DIFFERENT'))
                before=pool.path.read_bytes()
                with self.assertRaises(ValueError):settle_original(pool,capture,card)
                self.assertEqual(pool.path.read_bytes(),before)

    def test_capture_fence_recovers_without_rescan_and_live_reader_returns_no_science(self):
        with tempfile.TemporaryDirectory() as directory:
            card,capture,_,stage,output,docker=fixture(Path(directory))
            (output/'B-exclusive-monitor.jsonl').unlink()
            with patch('wcomr.cara_fast_b36_capture_r1.subprocess.run',side_effect=AssertionError('No second observer')):
                self.assertEqual(capture_terminal(Path(directory),stage,file_sha(stage/'GPU-launch.json')),capture)
            (stage/'B-terminal-capture.json').unlink()
            with patch('wcomr.cara_fast_b36_capture_r1.same_live_process',return_value=True):
                current=capture_terminal(Path(directory),stage,file_sha(stage/'GPU-launch.json'))
            self.assertEqual(current['status'],'FAST_B36_TERMINAL_READER_LIVE')
            self.assertFalse(current['scientific_rows_returned'])
            (stage/'B-terminal-capture-intent.json').unlink()
            docker['State']['Running']=True
            inspected=type('Inspected',(),dict(returncode=0,stdout=json.dumps([docker])))()
            with patch('wcomr.cara_fast_b36_capture_r1.subprocess.run',return_value=inspected),\
                 patch('wcomr.cara_fast_b36_capture_r1.same_live_process',return_value=True):
                current=capture_terminal(Path(directory),stage,file_sha(stage/'GPU-launch.json'))
            self.assertFalse(current['scientific_rows_returned'])
            self.assertNotIn('files',current)

    def test_original26_plus_six_and_full_curve_resource_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            card,capture,pool,_,output,_=fixture(Path(directory))
            settlement=settle_original(pool,capture,card)
            base=score_fixture(capture,card,settlement,output)
            for kind in ('partial32','reused_curve','partial26','reduction','PTS','curve','GPU','CPU_live','CPU_time','swap'):
                with self.subTest(kind=kind):
                    values=list(copy.deepcopy(base))
                    manifest,manifest_sha,result,execution,inner_packet,new_packet=values
                    if kind=='partial32':result['rows'].pop()
                    elif kind=='reused_curve':next(row for row in result['rows'] if 'reused_A_score_id' in row)['Alex_frames'][0]+=1
                    elif kind=='GPU':execution['host_config']['DeviceRequests']=[dict(DeviceIDs=['GPU-CPU-ONLY'])]
                    elif kind=='CPU_live':execution['container_state']['Running']=True
                    elif kind=='CPU_time':execution['container_wall_seconds']=14401
                    elif kind=='swap':execution['host_config']['MemorySwap']=-1
                    else:
                        new=json.loads(new_packet['raw_utf8'])
                        if kind=='partial26':new['rows'].pop()
                        elif kind=='reduction':new['rows'][0]['Alex']=1
                        elif kind=='PTS':new['rows'][0]['PTS_equal']=False
                        elif kind=='curve':new['rows'][0]['SSIM_frames'].pop()
                        raw=json.dumps(new)
                        new_packet.update(raw_utf8=raw,bytes=len(raw.encode()),sha256=hashlib.sha256(raw.encode()).hexdigest())
                        try:
                            values[2]=assemble_scores(manifest,manifest_sha,json.loads(inner_packet['raw_utf8']),inner_packet['sha256'],new,new_packet['sha256'])
                        except ValueError:
                            if kind=='partial26':continue
                            raise
                    with self.assertRaises(ValueError):accepted(capture,card,settlement,values)

    def test_scoring_reader_and_command_bind_readonly_sources_A_B_and_private_result(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            card,capture,pool,stage,output,docker=fixture(project)
            settlement=settle_original(pool,capture,card)
            values=score_fixture(capture,card,settlement,output)
            path=output/'B-score-CPU/manifest.json'
            docker['Config']['Labels']['wcomr.manifest']=file_sha(path)
            docker['State'].update(StartedAt='2026-10-28T12:00:00.123456789Z',FinishedAt='2026-10-28T12:01:30.123456789Z')
            docker['HostConfig'].update(Memory=8*1024**3,MemorySwap=8*1024**3,CpusetCpus='26,27',DeviceRequests=None)
            inspected=type('Inspected',(),dict(returncode=0,stdout=json.dumps([docker])))()
            def inspect_score(command,**kwargs):
                self.assertEqual(command,['docker','inspect',stage.name+'-B-score-cpu'])
                return inspected
            with patch('wcomr.cara_fast_b36_capture_r1.subprocess.run',side_effect=inspect_score):
                observed=capture_scores(project,stage,path,file_sha(path))
            final=accept_scores(capture,card,settlement,values[0],file_sha(path),record(observed,'scores'),observed['execution'],
                new_manifest=observed['files']['new_manifest'],new_scores=observed['files']['new_scores'])
            self.assertEqual(len(final['rows']),32)
            command=script('postprocess_cara_fast_b36_r1').score_command(project,stage,path,path.parent)
            self.assertNotIn('--gpus',command)
            self.assertEqual(command[command.index('--memory-swap')+1],'8g')
            self.assertEqual(command[command.index('--cpuset-cpus')+1],'26,27')
            self.assertIn('CUDA_VISIBLE_DEVICES=',command)
            self.assertIn('NVIDIA_VISIBLE_DEVICES=void',command)
            for root in (project,stage,output,Path(values[0]['A_output_root'])):
                self.assertIn(str(root)+':'+str(root)+':ro',command)
            self.assertIn(str(path.parent)+':'+str(path.parent)+':rw',command)
            for name in ('outputs','reports','.sync'):
                self.assertNotIn(str(project/name)+':'+str(project/name)+':rw',command)

    def test_wrapper_launches_only26_once_and_never_scores_reused_A(self):
        with tempfile.TemporaryDirectory() as directory:
            card,capture,pool,_,output,_=fixture(Path(directory))
            settlement=settle_original(pool,capture,card)
            values=score_fixture(capture,card,settlement,output)
            path=output/'B-score-CPU/manifest.json'
            for name in ('scores.json','new-pairs-manifest.json','new-scores.json'):(path.parent/name).unlink()
            wrapper=script('score_cara_fast_b36_fidelity_r1')
            calls=[]
            class Child:
                pid=-1
                def wait(self,timeout):
                    self.returncode=0
                    new=json.loads(values[-1]['raw_utf8'])
                    new['manifest_sha256']=file_sha(path.parent/'new-pairs-manifest.json')
                    write(path.parent/'new-scores.json',new)
                    return 0
                def poll(self):return 0
            def launch(command,**kwargs):
                fresh=json.loads((path.parent/'new-pairs-manifest.json').read_text())
                self.assertEqual(len(fresh['pairs']),26)
                self.assertFalse(set(fresh['reused_A_metric_pairs']) & {pair['id'] for pair in fresh['pairs']})
                self.assertEqual(Path(command[2]).name,'score_cara_fast_fidelity_r1.py')
                calls.append(command)
                return Child()
            with patch.object(wrapper.subprocess,'Popen',side_effect=launch),\
                 patch('sys.argv',['score','--manifest',str(path),'--output',str(path.parent/'scores.json')]),\
                 patch.dict(os.environ,dict(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')):
                wrapper.main()
                with self.assertRaises(ValueError):wrapper.main()
            self.assertEqual(len(calls),1)
            self.assertEqual(len(json.loads((path.parent/'scores.json').read_text())['rows']),32)

    def test_monitor_rejects_A_run_mixing_missing_intervals_and_thermal_trigger(self):
        with tempfile.TemporaryDirectory() as directory:
            _,capture,_,_,output,_=fixture(Path(directory))
            original=[json.loads(line) for line in (output/'B-exclusive-monitor.jsonl').read_text().splitlines()]
            for kind in ('A_run','gap','thermal'):
                rows=copy.deepcopy(original)
                if kind=='A_run':rows[-1]['run_id']='cara-fast-cal-a32-r2-20261028'
                elif kind=='gap':rows[-1]['monotonic_elapsed']=100
                else:rows[-1]['thermal']['temperature.gpu']='90'
                with self.subTest(kind=kind),self.assertRaises(ValueError):
                    audit_monitor(rows,record(capture,'launch'),record(capture,'supervisor'),record(capture,'supervisor_billing'),
                        record(capture,'ready'),record(capture,'grant'),record(capture,'pending_release'))


if __name__=='__main__':
    unittest.main()
