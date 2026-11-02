"""P1 RPC permission/order/count boundaries using temporary metadata only."""
import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import cara_source_lifecycle_p1_control_r1 as control
from check_cara_source_lifecycle_p1_outer_fixture_r1 import Fixture
from wcomr import cara_source_lifecycle_p1_dispatch_r1 as dispatch
from wcomr import cara_source_lifecycle_p1_capture_r1 as capture
from wcomr.cara_fast_fidelity_r1 import file_sha


class P1ControlTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.f=Fixture(self.temp.name)

    def test_old_card_and_missing_exact_exception_stop_before_credentials_or_ssh(self):
        path=self.f.project/control.AUTH;path.parent.mkdir(parents=True,exist_ok=True)
        for key,value in (('run_id','old-P0'),('central_exception_run_id','old-M1'),
                          ('central_transaction_authorized',False),('execution_authorized',False)):
            auth=copy.deepcopy(self.f.authority);auth[key]=value;path.write_text(json.dumps(auth))
            with self.subTest(key=key),patch.object(control,'ROOT',self.f.project),\
                    patch.object(control,'PROJECT',str(self.f.project)),\
                    patch.object(control.sys,'argv',['control','central-status','--output',str(self.f.project/'receipt.json')]),\
                    patch.object(control,'password',side_effect=AssertionError('No credential access')) as secret,\
                    patch.object(control.subprocess,'Popen',side_effect=AssertionError('No SSH')) as ssh:
                with self.assertRaises(ValueError):control.main()
                secret.assert_not_called();ssh.assert_not_called()

    def test_missing_new_authorization_never_contacts_any_host(self):
        with patch.object(control,'ROOT',self.f.project),\
                patch.object(control.sys,'argv',['control','central-prepare','--output',str(self.f.project/'receipt.json')]),\
                patch.object(control.subprocess,'Popen',side_effect=AssertionError('No SSH')) as ssh:
            with self.assertRaises(FileNotFoundError):control.main()
            ssh.assert_not_called()

    def run_two(self, action, **values):
        packet=dict(arguments=dict(action=action,authority=self.f.authority,
            registration_sha256=file_sha(self.f.stage/'registration.json'),**values))
        output=io.StringIO()
        with contextlib.redirect_stdout(output):exec(control.TWO,dict(packet=packet))
        return json.loads(output.getvalue())

    def test_status_counts_names_only_without_opening_partial_science(self):
        (self.f.stage/'GPU-launch.json').unlink()
        directory=self.f.output/'algorithm/operations';(directory/'path1').mkdir(parents=True)
        # These invalid JSON bodies prove the operational reader only counts names.
        (directory/'path1/request-complete.json').write_text('NEVER_READ_PARTIAL_SCIENCE')
        (directory/'score-abc').mkdir();(directory/'score-abc/intent.json').write_text('NEVER_READ_QUERY')
        with patch.object(dispatch,'recover',return_value=None),patch.object(capture,'inspect_container',return_value=None):
            result=self.run_two('status')
        counts=result['operational_progress']
        self.assertEqual((counts['semantic_denominator'],counts['physical_generation_upper']),(146,142))
        self.assertEqual((counts['completed_physical_request_files'],counts['internal_query_intent_files']),(1,1))
        self.assertFalse(counts['scientific_scores_read'])

    def test_unknown_original_dispatch_recovers_without_new_launch_or_reservation(self):
        unknown=dict(status='ORIGINAL_GPU_UNKNOWN',no_replay=True)
        with patch.object(dispatch,'recover',return_value=unknown),\
                patch.object(dispatch,'dispatch',side_effect=AssertionError('No repeated launch')) as launch:
            self.assertEqual(self.run_two('dispatch'),unknown)
            launch.assert_not_called()

    def test_admission_keeps_complete_scope_and_fresh_resource_gate(self):
        import wcomr.cara_fast_b36_dispatch_r2 as shared
        (self.f.stage/'GPU-launch.json').unlink()
        empty=self.f.project/'empty-output';empty.mkdir()
        journal=self.f.project/'empty-journal';journal.write_bytes(bytes(1024))
        storage=SimpleNamespace(output=empty,journal=SimpleNamespace(path=journal))
        with patch.object(dispatch,'recover',return_value=None),\
                patch.object(dispatch,'ready_inputs',return_value=(None,self.f.reg,self.f.authority,self.f.profile,self.f.quote)),\
                patch.object(dispatch,'fresh_resources',return_value=(storage,{'EXPLICIT_CPU_RESOURCE_SIMULATION':True})) as fresh,\
                patch.object(shared,'assets_check',return_value={'EXPLICIT_CPU_ASSET_SIMULATION':True}),\
                patch.object(capture,'inspect_container',return_value=None):
            result=self.run_two('admit')
        fresh.assert_called_once()
        admission=result['admission']
        self.assertEqual((admission['semantic_positions'],admission['physical_generation_upper'],
            admission['physical_model_pairs_upper'],admission['postrelease_new_pairs_upper']),(146,142,5176,32))
        self.assertEqual(admission['authorization'],self.f.authority)
        self.assertFalse(result['ledger_written']);self.assertEqual(result['GPU_submissions'],0)


if __name__=='__main__':
    unittest.main()
