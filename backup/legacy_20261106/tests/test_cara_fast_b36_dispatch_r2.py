"""Temporary filesystem/CPU children only; GPU/engine/resource I/O is simulated."""
import base64
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

from wcomr import cara_fast_b36_dispatch_r2 as dispatch
from wcomr.cara_fast_b36_execution_r1 import RUN,PROFILE,read
from wcomr.cara_fast_b36_terminal_r1 import settle_original,record
from wcomr.gpu_budget_pool_v2 import sha
from test_cara_fast_b36_execution_r1 import BoundaryTests,real_binding,script
from test_cara_fast_b36_post_r1 import fixture,score_fixture,write


class DispatchTests(unittest.TestCase):
    def test_grant_precedes_staging_and_existing_stage_is_never_replaced(self):
        profile=read(Path(__file__).resolve().parents[1]/PROFILE)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'.sync').mkdir()
            stage=root/'.sync'/dispatch.STAGE_NAME
            payload=dict(authority=dict(direct_user_authorization=False),files={PROFILE:base64.b64encode(json.dumps(profile).encode()).decode()})
            with self.assertRaises(ValueError):dispatch.prepare_stage(root,stage,payload)
            self.assertFalse(stage.exists())
            stage.mkdir();(stage/'original').write_bytes(b'RETAIN_ORIGINAL_STAGE')
            with self.assertRaises(ValueError):dispatch.prepare_stage(root,stage,payload)
            self.assertEqual((stage/'original').read_bytes(),b'RETAIN_ORIGINAL_STAGE')

    def test_full_asset_digests_and_snapshot_then_changed_stamp_or_target_refuse(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);blob=root/'blobs';blob.mkdir()
            contents=[b'SYNTHETIC_SHA256_ASSET',b'SYNTHETIC_GIT_BLOB']
            files=[]
            for index,body in enumerate(contents):
                path=blob/str(index);path.write_bytes(body)
                kind='sha256' if index==0 else 'git_blob_sha1'
                digest=hashlib.sha256(body).hexdigest() if index==0 else hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
                files.append(dict(path=str(path.relative_to(root)),bytes=len(body),digest=digest,digest_kind=kind))
            link=root/'snapshot';link.symlink_to(blob/'0')
            spec=dict(files=files,snapshot_links=[dict(path='snapshot',target='blobs/0')])
            checked=dispatch.assets_check(root,spec)
            dispatch.assets_unchanged(root,spec,checked)
            (blob/'0').write_bytes(b'X'*len(contents[0]))
            # Some registered filesystems coalesce timestamps within one tick.
            # This case tests a definite changed stamp; the full digest check
            # below independently rejects changed content at any timestamp.
            stat=(blob/'0').stat()
            os.utime(blob/'0',ns=(stat.st_atime_ns,stat.st_mtime_ns+10**9))
            with self.assertRaises(ValueError):dispatch.assets_unchanged(root,spec,checked)
            with self.assertRaises(ValueError):dispatch.assets_check(root,spec)
            (blob/'0').write_bytes(contents[0]);link.unlink();link.symlink_to(blob/'1')
            with self.assertRaises(ValueError):dispatch.assets_check(root,spec)

    @unittest.skipUnless(Path('/proc/self').exists(),'Linux exact child PID/start ticks')
    def test_once_intent_central_mismatch_recovery_and_no_partial_science(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            fixtures=BoundaryTests();fixtures.card,fixtures.bound=real_binding()
            stage,authority,job,bound=fixtures.fixture(root)
            registration=read(stage/'registration.json')
            card,_=real_binding()
            (stage/dispatch.ASSETS).write_text(json.dumps(dict(files=[],snapshot_links=[])))
            write(stage/'fresh-admission.json',dict(registration_sha256=sha(stage/'registration.json'),
                authorization_sha256=sha(stage/'pg-GPU-authorization.json'),asset_spec_sha256=sha(stage/dispatch.ASSETS),assets=[]))
            central=dict(central_ledger_host='four_card',budget_overrun_recorded=False,observed_unix=time.time(),job=job)
            children=[];original_popen=subprocess.Popen
            def launch_cpu_child(command,**kwargs):
                self.assertEqual(Path(command[1]).name,'cara_fast_b36_host_guardian_r1.py')
                child=original_popen([sys.executable,'-c','import sys,json;json.load(sys.stdin)'],**kwargs)
                children.append(child);return child
            class Storage:
                def check(self):return {}
            with patch.object(dispatch,'validate',return_value=(card,registration,authority,bound)),\
                 patch.object(dispatch,'storage_for',return_value=Storage()),\
                 patch.object(dispatch,'fresh_idle',return_value=({},0)),patch.object(dispatch,'english_resources',return_value={}),\
                 patch.object(dispatch.subprocess,'Popen',side_effect=launch_cpu_child):
                bad=copy.deepcopy(central);bad['job']['launch_id']='WRONG-LAUNCH'
                with self.assertRaises(ValueError):dispatch.launch(root,stage,'CPU_DUMMY_SECRET',bad)
                self.assertFalse((stage/'GPU-intent.json').exists())
                dispatched=dispatch.launch(root,stage,'CPU_DUMMY_SECRET',central)
                children[0].wait(timeout=10)
                self.assertEqual(dispatched['guardian_identity']['pid'],children[0].pid)
                pending=dispatch.launch(root,stage,'CPU_DUMMY_SECRET',None)
                self.assertIn('RECOVER_ONLY',pending['status'])
                self.assertEqual(len(children),1)
                launched=dispatch.publish_launch(root,stage)
                self.assertEqual(dispatch.launch(root,stage,'CPU_DUMMY_SECRET',None),launched)
                with self.assertRaises(FileExistsError):dispatch.publish_launch(root,stage)
            self.assertNotIn('CPU_DUMMY_SECRET',(stage/'GPU-intent.json').read_text())
            write(root/'outputs'/RUN/'B-collection.json',dict(rows=[dict(status='COMPLETE',result=dict(UNFINISHED_SCIENTIFIC_SCORE=999))]))
            observed=dispatch.status(root,stage)
            self.assertEqual(observed['progress']['denominator'],36)
            self.assertNotIn('UNFINISHED_SCIENTIFIC_SCORE',json.dumps(observed))

    @unittest.skipUnless(Path('/proc/self').exists(),'Linux score CLI PID/start ticks and once fencing')
    def test_post_release_CPU_dispatch_once_recovers_same_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory)
            card,capture,pool,stage,output,_=fixture(project)
            settlement=settle_original(pool,capture,card)
            values=score_fixture(capture,card,settlement,output)
            manifest_path=output/'B-score-CPU/manifest.json'
            for name in ('scores.json','new-pairs-manifest.json','new-scores.json'):(manifest_path.parent/name).unlink()
            manifest=values[0]
            Path(manifest['torch_home'],'hub/checkpoints').mkdir(parents=True)
            Path(manifest['torch_home'],'hub/checkpoints/alexnet-owt-7be5be79.pth').write_bytes(b'CPU_METADATA_NOT_A_WEIGHT')
            Path(manifest['piq_site']).mkdir(parents=True)
            module=script('dispatch_cara_fast_b36_score_cpu_r2')
            data=dict(stage=str(stage),registration_sha256=sha(stage/'registration.json'),capture=capture,settlement=settlement,
                manifest=base64.b64encode(manifest_path.read_bytes()).decode(),manifest_sha256=sha(manifest_path),
                operator_sha256=sha(stage/'scripts/dispatch_cara_fast_b36_score_cpu_r2.py'))
            source=module.REMOTE
            original_root="root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace')"
            original_sha="sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()"
            self.assertEqual(source.count(original_root),1);self.assertEqual(source.count(original_sha),1)
            source=source.replace(original_root,'root=cpu_fixture_project').replace(original_sha,'sha=cpu_fixture_sha')
            runtime=json.loads(capture['files']['registration']['raw_utf8'])['runtime_source_sha256']
            def controlled_sha(path):
                if project/'runtime' in path.parents:return runtime[str(path.relative_to(project/'runtime'))]
                return sha(path)
            children=[];original_popen=subprocess.Popen
            def launch_cpu_child(command,**kwargs):
                self.assertNotIn('--gpus',command)
                self.assertEqual(Path(command[-5]).name,'score_cara_fast_b36_fidelity_r1.py')
                child=original_popen([sys.executable,'-c','pass'],**kwargs);children.append(child);return child
            missing=subprocess.CompletedProcess(['docker'],1,stdout='',stderr='Error: No such object: '+stage.name+'-B-score-cpu')
            def inspect_score(command,**kwargs):
                self.assertEqual(command,['docker','inspect',stage.name+'-B-score-cpu'])
                return missing
            results=[]
            for repeat in range(2):
                stream=io.StringIO()
                with patch('sys.stdin',io.StringIO(json.dumps(data))),patch('sys.stdout',stream),\
                     patch('subprocess.run',side_effect=inspect_score),patch('subprocess.Popen',side_effect=launch_cpu_child),\
                     patch('os.sched_getaffinity',return_value={26,27}):
                    try:exec(compile(source,'B36_CPU_DISPATCH_RESOURCE_ADAPTER','exec'),dict(cpu_fixture_project=project,cpu_fixture_sha=controlled_sha))
                    except SystemExit as error:self.assertEqual(error.code,None)
                results.append(json.loads(stream.getvalue()))
                if children:children[0].wait(timeout=10)
            self.assertEqual(len(children),1)
            self.assertEqual(results[0],results[1])
            self.assertEqual(results[0]['new_metric_computations'],26)
            self.assertEqual(results[0]['reused_accepted_A_metric_pairs'],6)
            self.assertEqual(results[0]['container'],stage.name+'-B-score-cpu')

    @unittest.skipUnless(Path('/proc/self').exists(),'Use the registered Linux runtime source through a readonly symlink')
    def test_isolated_prepare_process_loads_B_overlay_and_original_A_package(self):
        source_root=Path(__file__).resolve().parents[1]
        module=script('cara_fast_b36_dispatch_r2')
        card,bound=real_binding()
        core=read(source_root/'reports/cara_fast_B36_CPU_acceptance_r1_20261029.json')
        profile=read(source_root/PROFILE)
        with tempfile.TemporaryDirectory() as directory:
            project=Path(directory);(project/'.sync').mkdir()
            actual_runtime=Path('/data20t/gaokuangda/worldcache_workspace/runtime')
            (project/'runtime').symlink_to(actual_runtime,target_is_directory=True)
            base=project/'.sync/A_SOURCE_CPU_FIXTURE';base.mkdir()
            names={str(path.relative_to(source_root)) for path in (source_root/'src').rglob('*.py')}
            names.update(str(path.relative_to(source_root)) for path in (source_root/'scripts').glob('*.py'))
            names.update(core['critical_source_sha256'])
            names.update(descriptor['path'] for descriptor in profile['A32_handoff_files'].values())
            names.update([PROFILE,dispatch.ASSETS,'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json',
                'plans/cara_next_stage_20261028/mainline/r2/WHOLE_QUOTE.json',
                'plans/cara_next_stage_20261028/mainline/RUN_MANIFEST.json'])
            hashes={name:sha(source_root/name) for name in names}
            for name in names:
                target=base/name;target.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(source_root/name,target)
            write(base/'registration.json',dict(CPU_METADATA_BASE_ONLY=True,payload_sha256=hashes))
            proof=dict(passed=True,critical_source_sha256=hashes,
                receipts={host:dict(runtime_source_sha256=bound['A_runtime_source_sha256']) for host in ('four_card','two_card')},
                CPU_METADATA_FIXTURE_ONLY_NOT_GPU_AUTHORITY=True)
            authority=dict(direct_user_authorization=True,user_quote='CPU_METADATA_FIXTURE_ONLY_NOT_GPU_AUTHORITY',
                new_B36_authorization=True,authorizes_replay=False,run_id=RUN,phase='B',physical_paths=36,whole_GPUh=5.5,
                host='two_card',gpu_uuid=bound['gpu_uuid'],A_launch_id=bound['A_launch_id'],
                frozen_file_sha256=bound['frozen_file_sha256'],scope_sha256=card['scope_sha256'],
                launch_id='CPU_PREPARE_ONLY_NO_GPU',source_revision='CPU_METADATA_FIXTURE')
            operators={name:expected for name,expected in hashes.items() if name.startswith('src/wcomr/cara_fast_b36_')}
            operators['src/wcomr/__init__.py']=hashes['src/wcomr/__init__.py']
            sent=set(operators)|{PROFILE}
            target=project/'.sync'/dispatch.STAGE_NAME
            payload=dict(action='prepare',stage=str(target),base_stage=str(base),base_registration_sha256=sha(base/'registration.json'),
                hashes=hashes,files={name:base64.b64encode((source_root/name).read_bytes()).decode() for name in sent},
                operator_sources=operators,CPU_proof=proof,core_CPU_proof=core,authority=authority,
                runtime_source_sha256=bound['A_runtime_source_sha256'],base_source_revision=bound['A_source_revision'],
                source_revision='CPU_METADATA_FIXTURE')
            prefix="project=Path('/data20t/gaokuangda/worldcache_workspace')"
            self.assertEqual(module.REMOTE.count(prefix),1)
            remote=module.REMOTE.replace(prefix,'project=Path('+repr(str(project))+')')
            result=subprocess.run([sys.executable,'-c',remote],input=json.dumps(payload),text=True,capture_output=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr[-3000:])
            accepted=json.loads(result.stdout)
            self.assertEqual(accepted['status'],'B36_SOURCE_PREPARED_NO_GPU')
            self.assertFalse((target/'GPU-intent.json').exists())
            self.assertFalse((target/'GPU-launch.json').exists())
            self.assertEqual(sha(target/PROFILE),hashes[PROFILE])


if __name__=='__main__':
    unittest.main()
