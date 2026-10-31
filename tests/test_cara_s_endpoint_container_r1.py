"""Prospective command/worker metadata controls; no Docker or GPU execution."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import cara_s_endpoint_container_r1 as builder
import cara_s_endpoint_supervisor_worker_r1 as worker
from wcomr import cara_s_endpoint_supervisor_r1 as supervisor
from wcomr import history104_storage_r2 as storage_module
from wcomr import cara_budget_original_handles_r1 as handles
from wcomr.gpu_budget_pool_v2 import atomic_json,sha


class ContainerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name).resolve();self.stage=self.project/'.sync/cara-S-endpoint-GPU-METADATA'
        self.stage.mkdir(parents=True);self.run_id='cara-S-endpoint-14gpuh-r1-20261030'
        self.profile=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_CONTAINER_PROFILE_R1.json').read_text())
        self.profile.update(schema='CARA_ENDPOINT_CONTAINER_PROFILE_R1',physical_paths=32,new_scoring_pairs=12,hard_GPUh=5.25)
        self.profile.pop('candidate_queries');self.profile['hosts']={'two_card':self.profile['hosts']['two_card']}
        self.uuid='GPU-cebf7119-cf03-23b9-e192-cd196332b704'
        output=self.project/'outputs'/self.run_id;journal=self.project/'reports/fixture.journal'
        self.storage=SimpleNamespace(output=output,journal=SimpleNamespace(path=journal),check=lambda:None,
            config=dict(output_mount=str(output),image_path=str(self.project/'image.ext4'),image_bytes=64*2**30,
                journal_path=str(journal),journal_bytes=48*2**20,minimum_output_free_bytes=4*2**30,
                minimum_host_free_bytes=128*2**20,minimum_free_inodes=1024))
        self.kwargs=dict(project=self.project,stage=self.stage,storage=self.storage,registration_sha='a'*64,
            profile=self.profile,host='two_card',run_id=self.run_id,uuid=self.uuid,uid=os.getuid(),gid=os.getgid())

    def command(self):return builder.container_arguments(**self.kwargs)

    def test_both_scopes_single_GPU_and_zero_swap(self):
        for paths,pairs in ((32,12),(25,8)):
            self.profile.update(physical_paths=paths,new_scoring_pairs=pairs)
            with patch.object(subprocess,'run',side_effect=AssertionError('Builder must never execute')):
                command=self.command()
            for option,value in [('--cpus','2'),('--memory','40g'),('--memory-swap','40g'),('--network','none'),
                ('--pid','host'),('--cpuset-cpus','24,25'),('--name',self.stage.name+'-gpu'),
                ('--gpus','device='+self.uuid),('--cidfile',str(self.stage/'container.cid'))]:
                self.assertEqual(command.count(option),1);self.assertEqual(command[command.index(option)+1],value)
            self.assertIn('--read-only',command);self.assertNotIn('--privileged',command)
            self.assertIn('CUDA_VISIBLE_DEVICES=',command);self.assertIn('NVIDIA_VISIBLE_DEVICES='+self.uuid,command)
            self.assertIn('TORCHINDUCTOR_COMPILE_THREADS=1',command)
            self.assertEqual(command[-5:],[str(self.stage/builder.WORKER),'--project',str(self.project),'--stage',str(self.stage)])

    def test_only_registered_mounts_writable_and_source_readonly(self):
        command=self.command();volumes=[command[i+1] for i,v in enumerate(command) if v=='-v']
        writable={v.rsplit(':',1)[0].split(':')[0] for v in volumes if v.endswith(':rw')}
        self.assertEqual(writable,{str(self.stage),str(self.storage.output),str(self.storage.journal.path),str(self.project/'.sync/gpu-locks')})
        for source in (self.project,self.stage/'src',self.stage/'scripts',Path(self.storage.config['image_path'])):
            self.assertIn(str(source)+':'+str(source)+':ro',volumes)
        for broad in ('outputs','reports','.sync'):
            self.assertNotIn(str(self.project/broad)+':'+str(self.project/broad)+':rw',volumes)

    def test_changed_resource_image_or_scope_refused(self):
        for section,key,value in [('GPU_container','memory_swap_GiB',48),('GPU_container','image','sha256:'+'b'*64),
                                  ('GPU_container','network','host'),('storage','output_image_bytes',32*2**30)]:
            profile=copy.deepcopy(self.profile);profile[section][key]=value;self.kwargs['profile']=profile
            with self.subTest(key=key),self.assertRaises(ValueError):self.command()
        self.kwargs['profile']=self.profile;self.kwargs['run_id']='../other'
        with self.assertRaises(ValueError):self.command()

    def test_four_card_and_partial_scope_refused(self):
        self.kwargs['host']='four_card'
        with self.assertRaises(ValueError):self.command()
        self.kwargs['host']='two_card';self.profile['physical_paths']=31
        with self.assertRaises(ValueError):self.command()

    def test_wrong_output_journal_or_low_water_refused(self):
        original=copy.deepcopy(self.storage.config)
        for key,value in [('output_mount',str(self.project/'outputs/other')),('journal_bytes',1),('minimum_output_free_bytes',0)]:
            self.storage.config=dict(original,**{key:value})
            with self.subTest(key=key),self.assertRaises(ValueError):self.command()

    def prepare_worker_metadata(self):
        for name in (builder.PROFILE,builder.WORKER,'scripts/cara_s_endpoint_container_r1.py'):
            destination=self.stage/name;destination.parent.mkdir(parents=True,exist_ok=True)
            if name==builder.PROFILE:atomic_json(destination,self.profile)
            else:shutil.copyfile(ROOT/name,destination)
        self.registration=dict(payload_sha256={n:sha(self.stage/n) for n in (builder.PROFILE,builder.WORKER,'scripts/cara_s_endpoint_container_r1.py')})
        atomic_json(self.stage/'registration.json',self.registration)
        self.authority=dict(CPU_fixture_only=False,execution_authorized=True,authorizes_replay=False)
        atomic_json(self.stage/'GPU-authorization.json',self.authority)
        self.kwargs['registration_sha']=sha(self.stage/'registration.json')
        self.launch=dict(CPU_fixture_only=False,authorization_sha256=sha(self.stage/'GPU-authorization.json'),
            registration_sha256=sha(self.stage/'registration.json'),billed_limit_GPUh=5.25,host='two_card',
            run_id=self.run_id,gpu_uuid=self.uuid,guardian_identity={'CPU_metadata_fixture':True},
            commands=dict(container_cli=self.command()))
        atomic_json(self.stage/'GPU-launch.json',self.launch)

    def invoke_worker(self,guardian_live=True):
        with patch.object(sys,'argv',['worker','--project',str(self.project),'--stage',str(self.stage)]),\
             patch.dict(os.environ,CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES=self.uuid),\
             patch.object(storage_module,'storage_for',return_value=self.storage),\
             patch.object(handles,'observe_original_process',return_value={'original_live':guardian_live}),\
             patch.object(supervisor,'supervise') as execute:
            worker.main();execute.assert_called_once_with(self.project,self.stage,self.storage)

    def test_bound_worker_reaches_original_supervisor_without_execution_in_fixture(self):
        self.prepare_worker_metadata();self.invoke_worker()

    def test_worker_refuses_fixture_authority_and_changed_command(self):
        self.prepare_worker_metadata();original=copy.deepcopy(self.launch)
        for fault in ('fixture','authority','source','command'):
            self.launch=copy.deepcopy(original)
            if fault=='fixture':self.launch['CPU_fixture_only']=True
            elif fault=='authority':self.launch['authorization_sha256']='0'*64
            elif fault=='source':self.launch['registration_sha256']='0'*64
            else:self.launch['commands']['container_cli'].insert(2,'--privileged')
            atomic_json(self.stage/'GPU-launch.json',self.launch)
            with self.subTest(fault=fault),self.assertRaises(ValueError):self.invoke_worker()

    def test_worker_refuses_dead_or_unknown_original_guardian(self):
        self.prepare_worker_metadata()
        for live in (False,None):
            with self.subTest(live=live),self.assertRaisesRegex(ValueError,'guardian must still be live'):
                self.invoke_worker(guardian_live=live)


if __name__=='__main__':unittest.main()
