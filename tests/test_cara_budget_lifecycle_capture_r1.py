import copy
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from wcomr import cara_budget_lifecycle_capture_r1 as reader
from wcomr import cara_budget_lifecycle_r1 as lifecycle
from wcomr.policy_price_terminal_r1 import record
from test_cara_budget_lifecycle_r1 import fixture, put


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name).resolve();self.stage=self.project/'.sync/cara-budget-calibration-GPU-CPU-FIXTURE'
        self.stage.mkdir(parents=True);(self.project/'runtime').mkdir()
        c,_,_=fixture()
        for key in c['files']:
            data=record(c,key)
            if 'stage' in data:data['stage']=str(self.stage)
            put(c,key,data)
        reg=record(c,'registration');reg['payload_sha256'][reader.SOURCE]=reader.file_sha(reader.__file__)
        for source in (reader.SOURCE,lifecycle.SOURCE):
            path=self.stage/source;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(Path(reader.__file__ if source==reader.SOURCE else lifecycle.__file__).read_bytes())
        (self.project/'runtime/runtime.py').write_text('CPU metadata fixture only\n')
        reg['runtime_source_sha256']={'runtime.py':reader.file_sha(self.project/'runtime/runtime.py')}
        reg_sha=put(c,'registration',reg)
        envelope=record(c,'central_reservation');envelope['job'].update(stage=str(self.stage),
            registration_sha256=reg_sha,authorization_sha256=c['files']['authorization']['sha256'])
        envelope_sha=put(c,'central_reservation',envelope)
        launch=record(c,'launch');launch.update(registration_sha256=reg_sha,
            authorization_sha256=c['files']['authorization']['sha256'],central_reservation_sha256=envelope_sha,
            container=self.stage.name+'-gpu')
        self.expected=put(c,'launch',launch)
        c['container'].update(name=launch['container'],manifest_sha256=reg_sha)
        guardian=record(c,'guardian');guardian['container_terminal_witness']['container']=c['container']
        guardian['billing_sha256']=c['files']['billing']['sha256'];put(c,'guardian',guardian)
        for key,name in reader.METADATA.items():(self.stage/name).write_text(c['files'][key]['raw_utf8'])
        locks=self.project/'.sync/gpu-locks';locks.mkdir()
        for suffix in ('.lock','.mode-owner.lock'):(locks/(launch['gpu_uuid']+suffix)).touch()
        self.original=c

    def capture(self,container=True,observations=None):
        observations=observations or self.original['process_observations']
        by_pid={r['original_pid']:r for r in observations.values()}
        with patch.object(reader,'inspect_container',return_value=self.original['container'] if container else None),\
                patch.object(reader,'observe_original_process',side_effect=lambda h:by_pid[h['pid']]):
            return reader.capture_lifecycle(self.project,self.stage,self.expected)

    def test_full_original_capture_reaches_readonly_financial_validator(self):
        before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.stage.rglob('*') if p.is_file()}
        captured=self.capture()
        self.assertEqual(lifecycle.financial_terminal(captured,self.expected,cpu_validation=True)[1]['actual_GPUh'],.05)
        after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.stage.rglob('*') if p.is_file()}
        self.assertEqual(before,after);self.assertFalse(captured['scientific_rows_returned'])

    def test_live_or_unknown_never_reads_scientific_or_terminal_files(self):
        for live in (True,None):
            observations=copy.deepcopy(self.original['process_observations']);observations['runner']['original_live']=live
            with patch.object(reader,'captured_file',wraps=reader.captured_file) as opened:
                result=self.capture(observations=observations)
            self.assertEqual(result['status'],'ORIGINAL_CALIBRATION_LIVE_OR_UNKNOWN')
            self.assertEqual([c.args[0].name for c in opened.call_args_list],['GPU-launch.json','guardian.json'])

    def test_docker_transport_failure_remains_unknown(self):
        observations={r['original_pid']:r for r in self.original['process_observations'].values()}
        with patch.object(reader,'inspect_container',side_effect=subprocess.TimeoutExpired('docker',20)),\
                patch.object(reader,'observe_original_process',side_effect=lambda h:observations[h['pid']]):
            result=reader.capture_lifecycle(self.project,self.stage,self.expected)
        self.assertEqual(result['reason'],'ORIGINAL_CONTAINER_OBSERVATION_UNKNOWN')

    def test_missing_or_replaced_container_cannot_certify_terminal(self):
        captured=self.capture(container=False)
        with self.assertRaises((ValueError,TypeError)):lifecycle.financial_terminal(captured,self.expected,cpu_validation=True)
        self.original['container']['id']='0'*64
        captured=self.capture()
        with self.assertRaises(ValueError):lifecycle.financial_terminal(captured,self.expected,cpu_validation=True)

    def test_busy_lock_is_observed_without_releasing_its_owner(self):
        path=self.project/'.sync/gpu-locks/GPU-CPU-FIXTURE.lock'
        with path.open('r+b') as owner:
            fcntl.flock(owner,fcntl.LOCK_EX|fcntl.LOCK_NB)
            captured=self.capture();self.assertFalse(captured['own_UUID_lock_free'])
            with self.assertRaises(ValueError):lifecycle.financial_terminal(captured,self.expected,cpu_validation=True)
            self.assertFalse(reader.lock_free(path))

    def test_wrong_launch_or_changed_source_refused(self):
        with self.assertRaises(ValueError):reader.capture_lifecycle(self.project,self.stage,'0'*64)
        (self.stage/lifecycle.SOURCE).write_text('changed CPU fixture source')
        captured=self.capture()
        with self.assertRaises(ValueError):lifecycle.financial_terminal(captured,self.expected,cpu_validation=True)

    def test_preallocation_failure_capture_with_absent_lock_files(self):
        guardian=record(self.original,'guardian')
        for role in ('container_cli','supervisor','runner'):guardian['original_handles'][role]=None
        guardian.update(container_terminal_witness=dict(kind='NO_CONTAINER_DISPATCH',complete=True),
            container_dispatch_state='NOT_ATTEMPTED',GPU_mode_change_attempted=False,mode_owner_fenced=False,
            error_type='CredentialUnavailable',allocation_never_attempted_witness=dict(mode_lock_attempted=False,
                device_lease_attempted=False,mode_change_attempted=False,container_dispatch_attempted=False))
        (self.stage/reader.METADATA['guardian']).write_text(json.dumps(guardian))
        for key in ('supervisor_start','runner_start','runner_intent'):(self.stage/reader.METADATA[key]).unlink()
        for path in (self.project/'.sync/gpu-locks').iterdir():path.unlink()
        captured=self.capture(container=False)
        self.assertIsNone(captured['own_UUID_lock_free']);self.assertIsNone(captured['mode_owner_lock_free'])
        self.assertEqual(lifecycle.financial_terminal(captured,self.expected,cpu_validation=True)[1]['actual_GPUh'],.05)


if __name__=='__main__':unittest.main()
