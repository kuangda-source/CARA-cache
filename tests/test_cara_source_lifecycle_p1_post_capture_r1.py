"""New original-container source/resource/unknown/no-partial score controls."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import check_cara_source_lifecycle_p1_score_fixture_r1 as original
from check_cara_source_lifecycle_p1_post_capture_fixture_r1 import build,ended,save
from wcomr import cara_source_lifecycle_p1_score_capture_r1 as capture
from wcomr import cara_source_lifecycle_p1_score_dispatch_r1 as dispatch
from wcomr.cara_fast_fidelity_r1 import file_sha


class P1PostCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.f,cls.packet=original.packet()

    @classmethod
    def tearDownClass(cls):cls.f.doCleanups()

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.args,self.container,self.out=build(Path(self.temp.name),self.packet)

    def recover(self,observed=ended):
        with patch.object(capture,'inspect_original',return_value=dict(status='OBSERVED',container=self.container)),\
                patch.object(capture,'observe_original_process',side_effect=observed):
            return capture.recover(**self.args)

    def test_complete52_only_reuses_old_rows_and_accepts_all_new(self):
        result=self.recover()
        self.assertEqual(result['status'],'ORIGINAL_COMPLETE52_P1_SCORE_ACCEPTED')
        self.assertEqual(result['accepted']['logical_quality_positions'],52)
        self.assertEqual(result['accepted']['internal_scores_recomputed'],0)

    def test_active_unknown_or_failed_never_opens_partial_scores(self):
        (self.out/'scores.json').unlink();(self.out/'scores-intent.json').unlink()
        self.container['State'].update(Status='running',Running=True,Pid=200)
        self.assertEqual(self.recover()['status'],'ORIGINAL_SCORE_ACTIVE')
        with patch.object(capture,'inspect_original',return_value=dict(status='UNKNOWN')):
            self.assertEqual(capture.recover(**self.args)['status'],'ORIGINAL_SCORE_UNKNOWN')
        self.container['State'].update(Status='exited',Running=False,Pid=0,ExitCode=1)
        self.assertEqual(self.recover()['status'],'ORIGINAL_SCORE_FAILED')

    def test_unknown_cli_or_live_worker_cannot_accept(self):
        self.assertEqual(self.recover(lambda h:dict(original_live=None))['status'],'ORIGINAL_SCORE_UNKNOWN')
        cli=self.args['binding']['cli_identity']['pid']
        self.assertEqual(self.recover(lambda h:ended(h) if h['pid']==cli else dict(original_live=True))['status'],'ORIGINAL_SCORE_UNKNOWN')

    def test_changed_id_label_command_or_source_is_refused(self):
        for mode in ('id','label','command'):
            original_container=copy.deepcopy(self.container)
            if mode=='id':self.container['Id']='b'*64
            if mode=='label':self.container['Config']['Labels']['wcomr.manifest']='b'*64
            if mode=='command':self.container['Config']['Cmd'].append('--another-run')
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.recover()
            self.container=original_container
        path=Path(self.args['binding']['stage'])/capture.DISPATCH;path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'source/runtime'):self.recover()

    def test_gpu_swap_restart_or_writable_source_are_refused(self):
        for mode in ('GPU','swap','restart','mount','cores'):
            old=copy.deepcopy(self.container)
            if mode=='GPU':self.container['HostConfig']['Devices']=[{'PathOnHost':'/dev/nvidia0'}]
            if mode=='swap':self.container['HostConfig']['MemorySwap']*=2
            if mode=='restart':self.container['HostConfig']['RestartPolicy']['Name']='always'
            if mode=='mount':self.container['Mounts'][1]['RW']=True
            if mode=='cores':self.container['HostConfig']['CpusetCpus']='26'
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.recover()
            self.container=old

    def test_missing_new_pair_retains_full_denominator_and_cannot_accept(self):
        result=json.loads((self.out/'scores.json').read_bytes());result['rows'].pop();save(self.out/'scores.json',result)
        with self.assertRaises(ValueError):self.recover()

    def test_once_dispatch_and_unknown_recovery_never_spawn_again(self):
        for name in ('scores.json','scores-intent.json'):(self.out/name).unlink()
        stage=Path(self.args['binding']['stage'])
        with patch.object(dispatch,'require_absent'),patch.object(dispatch,'resource_admission',return_value={'CPU_UNIT_ONLY':True}),\
                patch.object(dispatch.subprocess,'Popen',return_value=SimpleNamespace(pid=7777)) as spawned:
            result=dispatch.dispatch(stage,self.args['packet'],self.args['config'],file_sha(stage/'registration.json'),cpu_validation=True,work_seconds=60)
            self.assertEqual(result['status'],'ORIGINAL_SCORE_INTENT_CREATED')
            control,_=dispatch.paths(stage,self.args['config']);sha=file_sha(control/'intent.json')
            recovered=dispatch.dispatch(stage,self.args['packet'],self.args['config'],file_sha(stage/'registration.json'),cpu_validation=True,work_seconds=60)
            self.assertEqual(recovered['status'],'ORIGINAL_SCORE_DISPATCH_UNKNOWN')
            self.assertEqual(spawned.call_count,1);self.assertEqual(file_sha(control/'intent.json'),sha)

    def test_frozen_post_score_command_has_only_exact_writable_output(self):
        stage=Path(self.args['binding']['stage']);config=self.args['config']
        command=dispatch.score_command(stage,config,self.args['binding']['manifest_sha256'],cpu_validation=True)
        self.assertEqual(command[command.index('--cpuset-cpus')+1],'26,27')
        self.assertEqual(command[command.index('--memory-swap')+1],'8g')
        self.assertEqual([command[i+1] for i,v in enumerate(command) if v=='-v' and command[i+1].endswith(':rw')],
                         [str(self.out)+':'+str(self.out)+':rw'])


if __name__=='__main__':unittest.main()
