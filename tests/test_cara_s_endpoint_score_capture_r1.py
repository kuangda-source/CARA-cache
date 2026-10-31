"""Original-container recovery fixtures; Docker and score values are synthetic."""
import copy
import datetime
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_s_endpoint_score_capture_r1 as reader
from wcomr.cara_s_endpoint_scores_r1 import bind_scorer, SCORER_SOURCES, ROOT, WORKER
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_fast_spec_r1 import digest
from test_cara_s_endpoint_scores_r1 import fixture as score_fixture


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def timestamp(value):return datetime.datetime.fromtimestamp(value,datetime.timezone.utc).isoformat().replace('+00:00','Z')


def fixture(project,*,alias=False):
    original=score_fixture(project,alias=alias);packet=original['packet']
    stage=project/'.sync/cara-S-endpoint-CPU-fixture-recovery';stage.mkdir(parents=True)
    save(stage/'GPU-launch.json',dict(CPU_fixture_only=True,launch_id=packet['manifest']['launch_id']))
    packet['release']['original_launch_sha256']=file_sha(stage/'GPU-launch.json')
    packet['manifest']['release_sha256']=digest(packet['release'])
    config=bind_scorer(packet,{k:original['config'][k] for k in ('torch_home','piq_site','weights_sha256')},cpu_validation=True)
    for source in SCORER_SOURCES+(reader.SOURCE,):
        target=stage/source;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/source).read_bytes())
    runtime=project/'runtime';runtime.mkdir(exist_ok=True);(runtime/'CPU-only.txt').write_text('synthetic runtime')
    registration=dict(host='two_card',payload_sha256={p:file_sha(stage/p) for p in SCORER_SOURCES+(reader.SOURCE,)},
        runtime_source_sha256={'CPU-only.txt':file_sha(runtime/'CPU-only.txt')})
    save(stage/'registration.json',registration)
    out=project/'outputs'/config['run_id']/'endpoint-score-CPU'
    save(out/'manifest.json',config);manifest_sha=file_sha(out/'manifest.json')
    identity=copy.deepcopy(original['result']['original_identity'])
    cli=copy.deepcopy(identity);cli['pid']+=1
    binding=dict(CPU_fixture_only=True,stage=str(stage),container=stage.name+'-endpoint-score-cpu',container_id='a'*64,
        launch_id=config['launch_id'],run_id=config['run_id'],analysis_scope_sha256=config['analysis_scope_sha256'],
        artifact_packet_sha256=digest(packet),original_gpu_launch_sha256=packet['release']['original_launch_sha256'],
        registration_sha256=file_sha(stage/'registration.json'),manifest_sha256=manifest_sha,container_user='1000:1000',cli_identity=cli)
    intent=dict(manifest_sha256=manifest_sha,no_replay=True,CPU_fixture_only=True,
        registered_pairs=[p['id'] for p in config['pairs']],worker_sha256=config['scorer_source_sha256'][WORKER],original_identity=identity)
    save(out/'scores-intent.json',intent)
    result=original['result'];result.update(manifest_sha256=manifest_sha,started_unix=1001.,ended_unix=1002.)
    save(out/'scores.json',result)
    container=dict(Id=binding['container_id'],Name='/'+binding['container'],Image=reader.IMAGE,
        State=dict(Status='exited',Running=False,Pid=0,ExitCode=0,OOMKilled=False,StartedAt=timestamp(1000),FinishedAt=timestamp(1003)),
        HostConfig=dict(NanoCpus=10**9,Memory=8*1024**3,MemorySwap=8*1024**3,CpusetCpus='26',DeviceRequests=None,Devices=[],
            Privileged=False,NetworkMode='none',ReadonlyRootfs=True,PidMode='host',AutoRemove=False,RestartPolicy={'Name':'no'},CapAdd=None),
        Mounts=[dict(Type='bind',Source=str(p),Destination=str(p),RW=rw) for p,rw in ((project,False),(stage,False),(out,True))],
        Config=dict(Labels={'wcomr.manifest':manifest_sha},Env=['CUDA_VISIBLE_DEVICES=','NVIDIA_VISIBLE_DEVICES=void','PYTHONPATH='+str(stage/'scripts')+':'+str(stage/'src')],
            WorkingDir=str(runtime),User='1000:1000',Entrypoint=[str(project/'envs/wc-cosmos-py310-cu128-r3/bin/python')],
            Cmd=[str(stage/WORKER),'--manifest',str(out/'manifest.json'),'--output',str(out/'scores.json'),'--cpu-validation']))
    return dict(binding=binding,packet=packet,config=config,cpu_validation=True),container,out


def ended(handle):
    return dict(status='ORIGINAL_NOT_LIVE',original_live=False,original_pid=handle['pid'],
        original_start_ticks=handle['start_ticks'],observed_host_view=handle['host_view'])


class CaptureControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.args,self.container,self.out=fixture(Path(self.temp.name)/'full')

    def capture(self,observation=ended):
        with patch.object(reader,'inspect_original',return_value=dict(status='OBSERVED',container=self.container)), \
             patch.object(reader,'observe_original_process',side_effect=observation):
            return reader.recover(**self.args)

    def test_complete12(self):
        accepted=self.capture()['accepted'];self.assertEqual(accepted['new_scored_pairs'],12)
        self.assertEqual(accepted['formal_logical_positions'],24)

    def test_alias8(self):
        self.args,self.container,self.out=fixture(Path(self.temp.name)/'alias',alias=True)
        self.assertEqual(self.capture()['accepted']['new_scored_pairs'],8)

    def test_active_does_not_open_scores(self):
        self.container['State'].update(Status='running',Running=True,Pid=200)
        (self.out/'scores.json').unlink();(self.out/'scores-intent.json').unlink()
        self.assertEqual(self.capture()['status'],'ORIGINAL_SCORE_ACTIVE')

    def test_unknown_does_not_open_scores(self):
        (self.out/'scores.json').unlink()
        with patch.object(reader,'inspect_original',return_value=dict(status='UNKNOWN',reason='TEST')):
            self.assertEqual(reader.recover(**self.args)['status'],'ORIGINAL_SCORE_UNKNOWN')

    def test_failed_does_not_open_partial_scores(self):
        self.container['State']['ExitCode']=1;(self.out/'scores.json').unlink()
        self.assertEqual(self.capture()['status'],'ORIGINAL_SCORE_FAILED')

    def test_live_cli_does_not_accept(self):
        self.assertEqual(self.capture(lambda h:dict(original_live=True))['status'],'ORIGINAL_SCORE_ACTIVE')

    def test_live_worker_does_not_accept(self):
        cli=self.args['binding']['cli_identity']['pid']
        self.assertEqual(self.capture(lambda h:ended(h) if h['pid']==cli else dict(original_live=True))['status'],'ORIGINAL_SCORE_UNKNOWN')

    def test_replaced_container_refused(self):
        self.container['Id']='b'*64
        with self.assertRaisesRegex(ValueError,'ID/name'):self.capture()

    def test_wrong_manifest_label_refused(self):
        self.container['Config']['Labels']['wcomr.manifest']='b'*64
        with self.assertRaisesRegex(ValueError,'ID/name'):self.capture()

    def test_gpu_device_refused(self):
        self.container['HostConfig']['Devices']=[{'PathOnHost':'/dev/nvidia0'}]
        with self.assertRaisesRegex(ValueError,'bounded'):self.capture()

    def test_wrong_limits_refused(self):
        self.container['HostConfig']['MemorySwap']=16*1024**3
        with self.assertRaisesRegex(ValueError,'bounded'):self.capture()

    def test_restart_refused(self):
        self.container['HostConfig']['RestartPolicy']['Name']='always'
        with self.assertRaisesRegex(ValueError,'bounded'):self.capture()

    def test_writable_stage_refused(self):
        self.container['Mounts'][1]['RW']=True
        with self.assertRaisesRegex(ValueError,'read-only'):self.capture()

    def test_extra_volume_refused(self):
        self.container['Mounts'].append(dict(Type='volume',Source='/other',Destination='/other',RW=True))
        with self.assertRaisesRegex(ValueError,'read-only'):self.capture()

    def test_changed_command_refused(self):
        self.container['Config']['Cmd'].append('--another-run')
        with self.assertRaisesRegex(ValueError,'entrypoint'):self.capture()

    def test_changed_worker_identity_refused(self):
        value=json.loads((self.out/'scores.json').read_text());value['original_identity']['pid']+=10
        save(self.out/'scores.json',value)
        with self.assertRaisesRegex(ValueError,'process replaced'):self.capture()

    def test_changed_source_refused(self):
        (Path(self.args['binding']['stage'])/WORKER).write_text('changed')
        with self.assertRaisesRegex(ValueError,'source/runtime'):self.capture()

    def test_changed_manifest_refused(self):
        (self.out/'manifest.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'manifest bytes'):self.capture()

    def test_wrong_interval_refused(self):
        self.container['State']['FinishedAt']=timestamp(1001.5)
        with self.assertRaisesRegex(ValueError,'interval'):self.capture()

    def test_actual_docker_nanosecond_timestamp(self):
        self.assertEqual(reader.container_time('2026-10-31T12:37:09.617180999Z'),1793450229.617180)
        self.container['State'].update(StartedAt='1970-01-01T00:16:40.000000001Z',FinishedAt='1970-01-01T00:16:43.000000999Z')
        self.assertEqual(self.capture()['status'],'ORIGINAL_COMPLETE24_SCORE_ACCEPTED')

    def test_timezone_missing_refused(self):
        with self.assertRaisesRegex(ValueError,'UTC timestamp'):reader.container_time('2026-10-31T12:37:09.617180999')

    def test_cpu_fixture_cannot_be_production(self):
        self.args['cpu_validation']=False
        with self.assertRaisesRegex(ValueError,'boundary'):self.capture()


if __name__=='__main__':unittest.main()
