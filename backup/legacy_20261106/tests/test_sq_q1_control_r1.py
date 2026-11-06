"""Q1 control wrappers with no real GPU, budget, mode or service mutation."""
import copy
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from test_sq_q1_execution_r1 import ROOT,authority_fixture,script
from test_sq_q1_terminal_r1 import fixture
from wcomr.gpu_budget_pool_v2 import atomic_json,sha,DeviceLease
from wcomr.sq_q1_spec_r1 import RUN,COUNTS,LIMITS,SCOPE,PROFILE,QUOTES
from wcomr.sq_q1_stage_r1 import install,stage_path,prepare_intent,dispatch,exclusive_json
from wcomr.sq_q1_capture_r1 import capture


class ControlTests(unittest.TestCase):
    def test_recovery_covers_old_stage_and_unknown_docker_without_dispatch(self):
        control=script('cara_sq_q1_control_r1')
        for case in ('old_intent','unknown','actual_missing'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                project=Path(directory)
                if case=='old_intent':
                    old=project/'.sync/cara-sq-q1-saved-two-card-r1-20261028';old.mkdir(parents=True)
                    atomic_json(old/'GPU-intent.json',dict(CPU_ONLY=True))
                def inspect(command,**kwargs):
                    name=command[-1]
                    error=('Cannot connect to Docker daemon' if case=='unknown' else
                        ('Error response from daemon: No such container: ' if case=='actual_missing' else 'Error: No such container: ')+name)
                    return type('Result',(),dict(returncode=1,stdout='',stderr=error))()
                stream=io.StringIO();program=control.RECOVER.replace('/data20t/gaokuangda/worldcache_workspace',str(project))
                with patch('sys.stdin',io.StringIO(json.dumps(dict(host='two_card',run=RUN)))),\
                        patch.object(control.subprocess,'run',side_effect=inspect),contextlib.redirect_stdout(stream):
                    exec(program,{})
                result=json.loads(stream.getvalue())
                if case=='old_intent':self.assertIn('r1-20261028/GPU-intent.json',result['handles'])
                elif case=='unknown':
                    self.assertTrue(result['handles'])
                    self.assertTrue(all(row['status']=='UNKNOWN_RECOVER_ONLY' for row in result['handles'].values()))
                else:self.assertEqual(result['handles'],{})
                self.assertEqual(result['GPU_submissions'],0)

    def test_prepared_inputs_reuse_checks_original_sha_fresh_identity_and_empty_output(self):
        from wcomr import sq_q1_stage_r1 as module
        from test_sq_q1_assets_r1 import tiny_assets
        for case in ('pass','changed','nonempty','old_intent','sha'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);old,_,reg,_=authority_fixture(project,
                    stage_name='cara-sq-q1-saved-two-card-r1-20261028')
                stage=stage_path(project,'two_card');stage.mkdir(parents=True)
                atomic_json(stage/'registration.json',reg)
                assets=project/module.ASSETS;assets.mkdir(parents=True);manifest=tiny_assets(assets)
                weight=project/module.WEIGHT;weight.parent.mkdir(parents=True);weight.write_bytes(b'CPU_ONLY_WEIGHT')
                digest=sha(weight);output=project/'outputs'/RUN;output.mkdir(parents=True)
                with patch.object(module,'MANIFEST_SHA',manifest),patch.object(module,'CHECKPOINT_SHA',digest),\
                        patch.object(module,'CHECKPOINT_BYTES',weight.stat().st_size),\
                        patch('wcomr.history104_storage_r2.StorageGuard') as guard:
                    guard.return_value.check.return_value=dict(CPU_SYNTHETIC=True)
                    module.verify_assets(project,old)
                    expected={key+'_sha256':sha(old/name) for key,name in dict(
                        registration='registration.json',assets='Q1-asset-verification.json',storage='history104-storage.json').items()}
                    if case=='changed':weight.write_bytes(b'CPU_ONLY_WEIGHT')
                    elif case=='nonempty':(output/'original-attempt').write_text('KEEP')
                    elif case=='old_intent':atomic_json(old/'GPU-intent.json',dict(CPU_ONLY=True))
                    elif case=='sha':expected['assets_sha256']='f'*64
                    if case=='pass':
                        result=module.reuse_prepared_inputs(project,'two_card',expected)
                        self.assertEqual(result['verified_asset_files'],33)
                        self.assertEqual(sha(stage/'Q1-asset-verification.json'),expected['assets_sha256'])
                        with self.assertRaises(ValueError):module.reuse_prepared_inputs(project,'two_card',expected)
                    else:
                        with self.assertRaises(ValueError):module.reuse_prepared_inputs(project,'two_card',expected)
                        self.assertFalse((stage/'Q1-prepared-inputs-reuse.json').exists())

    def test_GPU_stage_copies_only_accepted_source_and_is_once_only(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);base,_,reg,_=authority_fixture(project)
            reg.update(GPU_submissions=0,resource_limits=dict(GPU='hidden'))
            atomic_json(base/'registration.json',reg)
            proof=dict(passed=True,GPU_submissions=0,source_revision=reg['source_revision'],
                critical_source_sha256=reg['payload_sha256'])
            raw=json.dumps(proof);before=sha(base/'registration.json')
            result=install(project,'two_card',base,proof,raw,before)
            self.assertEqual(result['status'],'Q1_GPU_SOURCE_STAGED_NO_AUTHORITY')
            self.assertFalse((Path(result['stage'])/'pg-GPU-authorization.json').exists())
            self.assertEqual(sha(base/'registration.json'),before)
            self.assertEqual(install(project,'two_card',base,proof,raw,before)['status'],
                'Q1_EXISTING_STAGE_RECOVER_ONLY')

    def test_GPU_stage_rejects_unaccepted_source_without_creating_a_stage(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);base,_,reg,_=authority_fixture(project)
            proof=dict(passed=False,GPU_submissions=0,source_revision=reg['source_revision'],
                critical_source_sha256=reg['payload_sha256'])
            with self.assertRaises(ValueError):install(project,'two_card',base,proof,json.dumps(proof),sha(base/'registration.json'))
            self.assertFalse(stage_path(project,'two_card').exists())

    def test_host_preference_and_scope_bound_authority_do_not_select_busy_hosts(self):
        control=script('cara_sq_q1_control_r1')
        probes={h:dict(host=h,admissible=True,source_revision='SYNTHETIC_CPU_ONLY',scope_sha256='a'*64,
            CPU_proof_sha256='b'*64,quote_sha256='c'*64,registration_sha256='d'*64,
            storage_contract_sha256='e'*64,observed_unix=time.time(),
            selected_gpu=dict(uuid='GPU-CPU-CONTROL')) for h in LIMITS}
        self.assertEqual(control.select_host(probes),'four_card')
        probes['four_card']['admissible']=False;self.assertEqual(control.select_host(probes),'two_card')
        probes['two_card']['admissible']=False
        with self.assertRaises(ValueError):control.select_host(probes)
        probes['two_card']['admissible']=True
        approval=dict(direct_user_authorization=True,user_quote='CPU UNIT INPUT ONLY, NOT HUMAN AUTHORITY',
            run_id=RUN,scope_counts=COUNTS,allowed_host_hard_limits_GPUh=LIMITS,
            host_policy='PREFER_ADMISSIBLE_FOUR_ELSE_TWO',source_revision='SYNTHETIC_CPU_ONLY',
            scope_sha256='a'*64,CPU_proof_sha256='b'*64,quote_sha256={h:'c'*64 for h in LIMITS},
            authorizes_retry=False,authorizes_S_collection=False)
        result=control.selected_authority(approval,probes['two_card'])
        self.assertEqual(result['whole_GPUh'],1.25)
        for key in ('direct_user_authorization','authorizes_retry','authorizes_S_collection'):
            changed=copy.deepcopy(approval);changed[key]=not approval[key]
            with self.assertRaises(ValueError):control.selected_authority(changed,probes['two_card'])

    def test_any_existing_host_intent_prevents_all_reservation_and_dispatch(self):
        control=script('cara_sq_q1_control_r1')
        recovered={h:dict(handles={},central_job=None) for h in LIMITS}
        recovered['two_card']['handles']['GPU-intent.json']={'SYNTHETIC_CPU_CONTROL':True}
        with patch.object(control,'recover_both',return_value=recovered),\
                patch.object(control,'preflight_both',side_effect=AssertionError('Must recover only')):
            result=control.launch(type('Arguments',(),{})())
        self.assertEqual(result['GPU_submissions'],0)
        self.assertEqual(result['status'],'Q1_EXISTING_INTENT_OR_ENVELOPE_RECOVER_ONLY')

    def test_live_capture_returns_allowlisted_counts_without_loading_scientific_rows(self):
        from wcomr import sq_q1_capture_r1 as module
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=stage_path(project,'two_card');stage.mkdir(parents=True)
            launch=dict(run_id=RUN,stage=str(stage),host='two_card',container=stage.name+'-gpu',
                launch_id='CPU_NO_GPU',gpu_uuid='GPU-CPU-CONTROL',registration_sha256='a'*64,
                guardian_identity=dict(pid=1,start_ticks=2))
            atomic_json(stage/'GPU-launch.json',launch)
            out=project/'outputs'/RUN;out.mkdir(parents=True)
            atomic_json(out/'Q1-health.json',dict(completed_states=2,head_calls={},states=['SECRET_SCIENTIFIC_ROWS'],selections={'x':1}))
            con=dict(State=dict(Running=True),Config=dict(Labels={'wcomr.manifest':'a'*64}),
                HostConfig=dict(DeviceRequests=[dict(DeviceIDs=[launch['gpu_uuid']])]))
            result=type('Result',(),dict(returncode=0,stdout=json.dumps([con])))()
            with patch.object(module.subprocess,'run',return_value=result),patch.object(module,'same_live_process',return_value=True):
                observed=capture(project,stage,sha(stage/'GPU-launch.json'))
            self.assertEqual(observed['health']['completed_states'],2)
            self.assertNotIn('states',observed['health']);self.assertNotIn('selections',observed['health'])
            self.assertNotIn('files',observed);self.assertFalse(observed['scientific_rows_returned'])

    def test_terminal_capture_keeps_original_bytes_and_complete_readout_cohort(self):
        from wcomr import sq_q1_capture_r1 as module
        from wcomr.sq_q1_terminal_r1 import settle_original,analyse_released
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=stage_path(project,'two_card')
            saved,scope,pool=fixture(project,stage_name=stage.name)
            names=dict(launch='GPU-launch.json',registration='registration.json',authorization='pg-GPU-authorization.json',
                CPU_acceptance='execution-CPU-proof.json',storage='history104-storage.json',
                central_reservation='central-reservation.json',launch_binding='launch-binding.json',
                guardian='pg-host-guardian.json',ready='pg-runner-context-ready.json',grant='pg-runner-context-granted.json')
            output=project/'outputs'/RUN;output.mkdir(parents=True)
            for key,name in names.items():(stage/name).write_text(saved['files'][key]['raw_utf8'])
            for key,name in dict(supervisor='Q1-supervisor.json',collection='Q1-collection.json',
                billing='Q1-billing.json',pending_release='Q1-release-pending-central.json',
                allocation_release='Q1-allocation-release.json',
                supervisor_billing='Q1-supervisor-billing-diagnostic.json',
                supervisor_release='Q1-supervisor-release-diagnostic.json').items():
                (output/name).write_text(saved['files'][key]['raw_utf8'])
            (output/'Q1-exclusive-monitor.jsonl').write_text(saved['monitor_raw_utf8'])
            original=saved['container'];con=dict(Id=original['id'],State=original['state'],Image=original['image'],
                Config=dict(Labels={'wcomr.manifest':original['manifest_sha256']}),
                HostConfig=dict(DeviceRequests=original['device_requests'],ReadonlyRootfs=True,
                    PidMode='host',NetworkMode='none',NanoCpus=2*10**9,CpusetCpus='24,25',Memory=16*2**30,MemorySwap=16*2**30))
            inspected=type('Result',(),dict(returncode=0,stdout=json.dumps([con])))()
            with patch.object(module.subprocess,'run',return_value=inspected),\
                    patch.object(module,'same_live_process',return_value=False),patch.object(module,'lock_free',return_value=True):
                result=capture(project,stage,sha(stage/'GPU-launch.json'))
            settlement=settle_original(pool,result,scope)
            self.assertEqual(len(analyse_released(result,scope,settlement)['codec_selection']['selections']),8)
            self.assertEqual(result['files']['collection']['sha256'],saved['files']['collection']['sha256'])

    def test_CPU_post_command_is_GPU_hidden_readonly_and_bounded(self):
        post=script('postprocess_cara_sq_q1_r1')
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=stage_path(project,'two_card');stage.mkdir(parents=True)
            atomic_json(stage/'registration.json',dict(host='two_card'))
            atomic_json(stage/PROFILE,json.loads((ROOT/PROFILE).read_text()))
            output=project/'outputs'/RUN/'CPU-post'
            command=post.container_arguments(project,stage,output)
            self.assertNotIn('--gpus',command)
            self.assertIn('CUDA_VISIBLE_DEVICES=',command);self.assertIn('NVIDIA_VISIBLE_DEVICES=void',command)
            self.assertEqual(command[command.index('--memory')+1],'8g')
            self.assertEqual(command[command.index('--memory-swap')+1],'8g')
            self.assertIn(str(stage)+':'+str(stage)+':ro',command)
            self.assertNotIn(str(stage)+':'+str(stage)+':rw',command)
            self.assertIn('300',command);self.assertIn(str(stage/'scripts/postprocess_cara_sq_q1_r1.py'),command)

    def test_private_storage_refuses_same_filesystem_before_format_or_mount(self):
        from wcomr import sq_q1_stage_r1 as module
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=stage_path(project,'two_card');stage.mkdir(parents=True)
            profile=json.loads((ROOT/PROFILE).read_text());(project/'reports').mkdir()
            profile['hosts']['two_card'].update(image_path=str(project/'private/image.img'),
                journal_path=str(project/'reports/fixture.journal'))
            atomic_json(stage/PROFILE,profile)
            with patch.object(module.subprocess,'run',side_effect=AssertionError('No external mutation allowed')):
                with self.assertRaisesRegex(ValueError,'different filesystems'):
                    module.provision_storage(project,'two_card','UNIT_FAKE_NON_SECRET')
            self.assertFalse((project/'private/image.img').exists())
            self.assertFalse((project/'outputs'/RUN).exists())

    def test_streamed_asset_hashes_and_identity_stamp_reject_later_changes(self):
        from wcomr import sq_q1_stage_r1 as module
        from test_sq_q1_assets_r1 import tiny_assets
        for hf_link in (False,True):
            with self.subTest(hf_link=hf_link),tempfile.TemporaryDirectory() as directory:
                project=Path(directory);stage=stage_path(project,'two_card');stage.mkdir(parents=True)
                assets=project/module.ASSETS;assets.mkdir(parents=True)
                manifest=tiny_assets(assets);weight=project/module.WEIGHT;weight.parent.mkdir(parents=True)
                weight.write_bytes(b'CPU UNIT WEIGHTS ONLY');digest=sha(weight)
                if hf_link:
                    blob=project/'cache/huggingface/hub/models--nvidia--Cosmos-Predict2.5-2B/blobs'/digest
                    blob.parent.mkdir(parents=True);weight.rename(blob);weight.symlink_to(blob)
                with patch.object(module,'MANIFEST_SHA',manifest),patch.object(module,'CHECKPOINT_SHA',digest),\
                        patch.object(module,'CHECKPOINT_BYTES',weight.stat().st_size):
                    result=module.verify_assets(project,stage)
                self.assertEqual(len(result['files']),33)
                self.assertTrue(module.asset_identity_current(stage))
                weight.write_bytes(b'CPU UNIT WEIGHTS ONLY')
                self.assertFalse(module.asset_identity_current(stage))

    @unittest.skipUnless(Path('/proc/self').exists(),'Real Linux handoff, no GPU entry executed')
    def test_consumed_handoff_starts_one_CPU_stub_and_never_replays(self):
        from wcomr import sq_q1_stage_r1 as module
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=stage_path(project,'two_card')
            physical=project/'physical';physical.mkdir();alias=project/'alias';alias.symlink_to(physical,target_is_directory=True)
            with DeviceLease(alias,'GPU-CPU-ALIAS') as lease:
                module.verify_lease_fd(alias,'GPU-CPU-ALIAS',lease.handle.fileno())
                with self.assertRaises(ValueError):module.verify_lease_fd(project,'GPU-CPU-ALIAS',lease.handle.fileno())
            original,authority,registration,job=authority_fixture(project,stage_name=stage.name)
            envelope=json.loads((stage/'central-reservation.json').read_text())
            (stage/'central-reservation.json').unlink();(stage/'launch-binding.json').unlink()
            (stage/'scripts/cara_sq_q1_guardian_r1.py').write_text('''import json,os,sys
from pathlib import Path
sys.path.insert(0,__SOURCE__)
from wcomr.sq_q1_stage_r1 import publish_launch
stage=Path(__file__).resolve().parents[1]
publish_launch(stage.parents[1],stage)
assert os.environ['CUDA_VISIBLE_DEVICES']==''
assert json.load(sys.stdin)=={'sudo_password':'UNIT_FAKE_NON_SECRET'}
(Path(__file__).resolve().parents[1]/'CPU_STUB_ONLY.json').write_text(json.dumps({'GPU_submissions':0}))
'''.replace('__SOURCE__',repr(str(ROOT/'src'))))
            children=[];popen=subprocess.Popen
            def spawn(*args,**kwargs):
                child=popen(*args,**kwargs);children.append(child);return child
            with patch.object(module,'asset_identity_current',return_value=True),\
                    patch.object(module,'validate',return_value=(json.loads((ROOT/SCOPE).read_text()),registration,authority)),\
                    patch.object(module.subprocess,'Popen',side_effect=spawn):
                intent=prepare_intent(project,'two_card',authority)
                result=dispatch(project,'two_card',envelope,intent['intent_sha256'],'UNIT_FAKE_NON_SECRET')
                self.assertEqual(children[0].wait(timeout=30),0)
                self.assertFalse(result['actual_GPU_started'])
                with self.assertRaises(ValueError):dispatch(project,'two_card',envelope,intent['intent_sha256'],'UNIT_FAKE_NON_SECRET')
                self.assertEqual(len(children),1)

    @unittest.skipUnless(Path('/proc/self').exists(),'Real Linux handoff child and raw CPU post CLI')
    def test_early_child_exit_keeps_its_self_published_original_identity(self):
        from wcomr import sq_q1_stage_r1 as module
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=stage_path(project,'two_card')
            _,authority,registration,_=authority_fixture(project,stage_name=stage.name)
            envelope=json.loads((stage/'central-reservation.json').read_text())
            (stage/'central-reservation.json').unlink();(stage/'launch-binding.json').unlink()
            stub='''import sys
from pathlib import Path
sys.path.insert(0,__SOURCE__)
from wcomr.sq_q1_stage_r1 import publish_launch
stage=Path(__file__).resolve().parents[1]
publish_launch(stage.parents[1],stage)
raise SystemExit(7)
'''.replace('__SOURCE__',repr(str(ROOT/'src')))
            (stage/'scripts/cara_sq_q1_guardian_r1.py').write_text(stub)
            children=[];popen=subprocess.Popen
            def spawn(*args,**kwargs):
                child=popen(*args,**kwargs);children.append(child);return child
            with patch.object(module,'asset_identity_current',return_value=True),\
                    patch.object(module,'validate',return_value=(json.loads((ROOT/SCOPE).read_text()),registration,authority)),\
                    patch.object(module.subprocess,'Popen',side_effect=spawn):
                intent=prepare_intent(project,'two_card',authority)
                result=dispatch(project,'two_card',envelope,intent['intent_sha256'],None)
                self.assertEqual(children[0].wait(timeout=30),7)
                self.assertEqual(result['guardian_identity']['pid'],children[0].pid)
                self.assertIsNotNone(result['guardian_identity']['start_ticks'])
                with self.assertRaises(ValueError):dispatch(project,'two_card',envelope,intent['intent_sha256'],None)
                self.assertEqual(len(children),1)

    @unittest.skipUnless(Path('/proc/self').exists(),'Real Linux handoff child and raw CPU post CLI')
    def test_credential_pipe_failure_preserves_original_launch_bytes(self):
        from wcomr import sq_q1_stage_r1 as module
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);stage=stage_path(project,'two_card')
            _,authority,registration,_=authority_fixture(project,stage_name=stage.name)
            envelope=json.loads((stage/'central-reservation.json').read_text())
            (stage/'central-reservation.json').unlink();(stage/'launch-binding.json').unlink()
            stub='''import sys
from pathlib import Path
sys.path.insert(0,__SOURCE__)
from wcomr.sq_q1_stage_r1 import publish_launch
stage=Path(__file__).resolve().parents[1]
publish_launch(stage.parents[1],stage)
raise SystemExit(7)
'''.replace('__SOURCE__',repr(str(ROOT/'src')))
            (stage/'scripts/cara_sq_q1_guardian_r1.py').write_text(stub)
            children=[];popen=subprocess.Popen
            def spawn(*args,**kwargs):
                child=popen(*args,**kwargs);children.append(child);original=child.stdin
                class FailedPipe:
                    def write(self,data):raise BrokenPipeError('CPU_SYNTHETIC_CREDENTIAL_PIPE_FAILURE')
                    def close(self):original.close()
                child.stdin=FailedPipe();return child
            with patch.object(module,'asset_identity_current',return_value=True),\
                    patch.object(module,'validate',return_value=(json.loads((ROOT/SCOPE).read_text()),registration,authority)),\
                    patch.object(module.subprocess,'Popen',side_effect=spawn):
                intent=prepare_intent(project,'two_card',authority)
                result=dispatch(project,'two_card',envelope,intent['intent_sha256'],None)
                self.assertEqual(children[0].wait(timeout=30),7)
                self.assertEqual((json.dumps(result,indent=2)+'\n').encode(),(stage/'GPU-launch.json').read_bytes())
                self.assertNotIn('credential_delivery_error',result)
                diagnostic=json.loads((stage/'GPU-credential-delivery-diagnostic.json').read_text())
                self.assertEqual(diagnostic['error_type'],'BrokenPipeError')
                with self.assertRaises(ValueError):dispatch(project,'two_card',envelope,intent['intent_sha256'],None)
                self.assertEqual(len(children),1)

    @unittest.skipUnless(Path('/proc/self').exists(),'Real Linux handoff child and raw CPU post CLI')
    def test_actual_CPU_post_CLI_requires_settlement_before_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);captured,scope,pool=fixture(project)
            from wcomr.sq_q1_terminal_r1 import settle_original
            settlement=settle_original(pool,captured,scope)
            for name,value in (('capture.json',captured),('settlement.json',settlement)):
                atomic_json(project/name,value)
            output=project/'analysis.json'
            value=subprocess.run([sys.executable,str(ROOT/'scripts/postprocess_cara_sq_q1_r1.py'),
                '--capture',str(project/'capture.json'),'--settlement',str(project/'settlement.json'),
                '--output',str(output)],capture_output=True,text=True,timeout=300,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void'))
            self.assertEqual(value.returncode,0,value.stderr)
            result=json.loads(output.read_text());self.assertEqual(len(result['codec_selection']['selections']),8)
            self.assertFalse(result['CUDA_initialized'])


if __name__=='__main__':unittest.main()
