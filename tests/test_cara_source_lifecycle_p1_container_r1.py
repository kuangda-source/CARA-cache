"""Exact P1 container arguments and scope refusal; no Docker or GPU calls."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from cara_source_lifecycle_p1_container_r1 import container_arguments,WORKER
from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import RUN_ID,STAGE_NAME,GPU,PROFILE

ROOT=Path(__file__).resolve().parents[1]


class P1ContainerTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name);self.stage=self.project/'.sync'/STAGE_NAME
        self.profile=json.loads((ROOT/PROFILE).read_bytes());self.profile['hard_GPUh']=18.
        output=self.project/'outputs'/RUN_ID;journal=self.project/'.sync/P1-journal'
        limits=self.profile['storage']
        config=dict(output_mount=str(output),image_bytes=limits['output_image_bytes'],
            journal_bytes=limits['independent_journal_bytes'],journal_path=str(journal),
            image_path=str(self.project/'.sync/P1-private.ext4'),
            **{k:limits[k] for k in ('minimum_output_free_bytes','minimum_host_free_bytes','minimum_free_inodes')})
        self.values=dict(project=self.project,stage=self.stage,storage=SimpleNamespace(output=output,config=config,journal=SimpleNamespace(path=journal)),
            registration_sha='a'*64,profile=self.profile,host='two_card',run_id=RUN_ID,uuid=GPU,uid=1001,gid=999)

    def test_exact_whole_resources_original_worker_and_mounts(self):
        command=container_arguments(**self.values)
        for flag,value in (('--cpus','2'),('--memory','40g'),('--memory-swap','40g'),('--cpuset-cpus','24,25'),
                            ('--network','none'),('--pid','host'),('--cidfile',str(self.stage/'container.cid'))):
            self.assertEqual(command[command.index(flag)+1],value)
        self.assertIn('--read-only',command);self.assertIn(str(self.stage/WORKER),command)
        self.assertIn('CUDA_VISIBLE_DEVICES=',command);self.assertIn('NVIDIA_VISIBLE_DEVICES='+GPU,command)
        writable=[command[i+1] for i,v in enumerate(command) if v=='-v' and command[i+1].endswith(':rw')]
        self.assertEqual(set(writable),{str(p)+':'+str(p)+':rw' for p in (self.stage,self.values['storage'].output,
            self.values['storage'].journal.path,self.project/'.sync/gpu-locks')})
        self.assertIn(str(self.stage/'src')+':'+str(self.stage/'src')+':ro',command)

    def test_old_card_other_host_or_root_owner_is_refused(self):
        for key,value in (('stage',self.stage.parent/'cara-read-write-M1-GPU-old'),('run_id','old-M1'),
                          ('host','four_card'),('uuid','GPU-OTHER'),('uid',0),('gid',0)):
            values=dict(self.values);values[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):container_arguments(**values)

    def test_private_storage_size_and_margin_cannot_be_downgraded(self):
        for key in ('image_bytes','journal_bytes','minimum_output_free_bytes','minimum_host_free_bytes','minimum_free_inodes'):
            old=self.values['storage'].config[key];self.values['storage'].config[key]=old//2
            with self.subTest(key=key),self.assertRaises(ValueError):container_arguments(**self.values)
            self.values['storage'].config[key]=old

    def test_unfrozen_published_hard_limit_cannot_construct_dispatch(self):
        self.profile['hard_GPUh']=None
        with self.assertRaisesRegex(ValueError,'frozen hard limit'):container_arguments(**self.values)


if __name__=='__main__':unittest.main()
