"""CPU-only dispatch boundary controls; no Docker or remote host use."""
import copy
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_s_endpoint_score_dispatch_r1 as dispatch
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from test_cara_s_endpoint_score_capture_r1 import fixture as capture_fixture,save,ROOT

ORIGINAL_COMMAND=dispatch.score_command


def fixture(project,*,endpoint7=False):
    args,container,out=capture_fixture(project,endpoint7=endpoint7)
    stage=Path(args['binding']['stage'])
    for source in (dispatch.SOURCE,dispatch.BOOTSTRAP):
        target=stage/source;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source,target)
    registration=json.loads((stage/'registration.json').read_text())
    registration['payload_sha256'].update({p:file_sha(stage/p) for p in (dispatch.SOURCE,dispatch.BOOTSTRAP)})
    save(stage/'registration.json',registration)
    result=json.loads((out/'scores.json').read_text())
    for name in ('scores.json','scores-intent.json'):(out/name).unlink()
    values=dict(stage=stage,packet=args['packet'],config=args['config'],registration_sha256=file_sha(stage/'registration.json'),
        cpu_validation=True,work_seconds=5.)
    container['Config']['User']=str(os.getuid())+':'+str(os.getgid())
    return values,container,out,result


class DispatchControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.args,self.container,self.out,_=fixture(Path(self.temp.name)/'project')
        self.control=self.args['stage']/'endpoint-score-control'
        self.popen=patch.object(dispatch.subprocess,'Popen').start();self.addCleanup(patch.stopall)
        self.popen.return_value.pid=999
        self.absent=patch.object(dispatch,'require_absent').start()
        self.admit=patch.object(dispatch,'resource_admission',return_value=dict(CPU_test=True)).start()
        self.command=patch.object(dispatch,'score_command',return_value=['CPU-FIXTURE-NOT-EXECUTED']).start()

    def test_intent_persists_before_spawn(self):
        def spawned(*args,**kwargs):
            self.assertTrue((self.control/'intent.json').is_file())
            self.assertFalse((self.out/'scores.json').exists())
            self.assertEqual(kwargs['env']['NVIDIA_VISIBLE_DEVICES'],'void')
            return type('Child',(),{'pid':999})()
        self.popen.side_effect=spawned
        self.assertEqual(dispatch.dispatch(**self.args)['status'],'ORIGINAL_SCORE_INTENT_CREATED')

    def test_second_call_only_recovers(self):
        dispatch.dispatch(**self.args)
        self.assertEqual(dispatch.dispatch(**self.args)['status'],'ORIGINAL_SCORE_DISPATCH_UNKNOWN')
        self.assertEqual(self.popen.call_count,1);self.assertEqual(self.admit.call_count,1)

    def test_spawn_failure_never_replays(self):
        self.popen.side_effect=OSError('CPU fixture spawn failure')
        with self.assertRaises(OSError):dispatch.dispatch(**self.args)
        self.assertEqual(dispatch.dispatch(**self.args)['status'],'ORIGINAL_SCORE_DISPATCH_UNKNOWN')
        self.assertEqual(self.popen.call_count,1)

    def test_unknown_docker_refuses_before_intent(self):
        self.absent.side_effect=ValueError('unknown Docker')
        with self.assertRaisesRegex(ValueError,'unknown'):dispatch.dispatch(**self.args)
        self.assertFalse((self.control/'intent.json').exists());self.popen.assert_not_called()

    def test_resource_refusal_before_intent(self):
        self.admit.side_effect=ValueError('resource refusal')
        with self.assertRaisesRegex(ValueError,'resource'):dispatch.dispatch(**self.args)
        self.assertFalse((self.control/'intent.json').exists());self.popen.assert_not_called()

    def test_existing_scores_refused(self):
        save(self.out/'scores.json',{})
        with self.assertRaisesRegex(ValueError,'Existing score'):dispatch.dispatch(**self.args)
        self.popen.assert_not_called()

    def test_changed_registered_source_refused(self):
        (self.args['stage']/dispatch.BOOTSTRAP).write_text('changed')
        with self.assertRaisesRegex(ValueError,'source/runtime'):dispatch.dispatch(**self.args)
        self.popen.assert_not_called()

    def test_no_longer_cpu_deadline(self):
        self.args['work_seconds']=721
        with self.assertRaisesRegex(ValueError,'shorten'):dispatch.dispatch(**self.args)
        self.popen.assert_not_called()

    def test_cpu_fixture_not_production(self):
        self.args['cpu_validation']=False
        with self.assertRaisesRegex(ValueError,'boundary'):dispatch.dispatch(**self.args)
        self.popen.assert_not_called()

    def test_torn_intent_refuses_replay(self):
        self.control.mkdir();(self.control/'intent.json').write_text('{')
        with self.assertRaises(ValueError):dispatch.dispatch(**self.args)
        self.popen.assert_not_called()

    def test_original_unbound_cid_refuses_spawn(self):
        self.control.mkdir();(self.control/'container.cid').write_text('a'*64)
        with self.assertRaisesRegex(ValueError,'Unbound'):dispatch.dispatch(**self.args)
        self.popen.assert_not_called()

    def test_frozen_command_change_refused(self):
        dispatch.dispatch(**self.args);intent=json.loads((self.control/'intent.json').read_text())
        intent['command']=['changed'];save(self.control/'intent.json',intent)
        with self.assertRaisesRegex(ValueError,'frozen'):dispatch.recover(self.args['stage'])

    def test_production_command_layout(self):
        config=copy.deepcopy(self.args['config']);config['CPU_bound']['cpus']=2
        command=ORIGINAL_COMMAND(self.args['stage'],config,'a'*64)
        for option,value in (('--cpus','2'),('--memory','8g'),('--memory-swap','8g'),('--cpuset-cpus','26,27'),('--network','none')):
            self.assertEqual(command[command.index(option)+1],value)
        self.assertNotIn('--gpus',command);self.assertNotIn('--cpu-validation',command)
        self.assertIn('CUDA_VISIBLE_DEVICES=',command);self.assertIn('NVIDIA_VISIBLE_DEVICES=void',command)
        self.assertIn(str(self.args['stage'])+':'+str(self.args['stage'])+':ro',command)
        self.assertEqual(command[command.index('--cidfile')+1],str(self.control/'container.cid'))


if __name__=='__main__':unittest.main()
