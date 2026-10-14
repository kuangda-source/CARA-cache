"""Whole-card launch controls only: fake PIDs, no SSH/model/budget mutation."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wcomr.w3_label64_production_contract_r1 import CARD,CAP
COUNTS=json.loads((Path(__file__).resolve().parents[1]/'manifests/wc_w3_label64_parent18_full864_scope_r1_20261015.json').read_text())['scope_counts']
from wcomr.w3_label64_admission_r1 import verify_permission,verify_admission

ROOT=Path(__file__).resolve().parents[1]


def script(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


LAUNCH=script('launch_wc_w3_label64_full864_r1')
SUPERVISOR=script('supervise_wc_w3_label64_full864_r1')
POST=script('watch_wc_w3_label64_post_cpu_r1')


def config():return json.loads((ROOT/LAUNCH.CONFIG).read_text())


def fixtures(c=None):
    c=c or config();reg={'source_revision':'e'*40}
    proof={'status':'W3_LABEL64_FULL18_ACTUAL_PRODUCTION_CPU_ACCEPTED','scope_counts':COUNTS,
        'source_revision':reg['source_revision'],'scope_sha256':'config-hash','exit_code':0,'GPU_submissions':0,
        'CUDA_initialized':False,'weights_loaded':0,'launch_controls_accepted':True,
        'launcher_supervisor_post_paths_verified':True,'full72_collector_CPU_accepted':True,
        'full90_post_CPU_controls_accepted':True,'whole_card_supervisor_CPU_accepted':True,
        'forecast_complete_GPUh':11.645827780327332}
    permission={'card':CARD,'scope_counts':COUNTS,'forecast_complete_GPUh':proof['forecast_complete_GPUh'],
        'production_CPU_accepted':True,'direct_user_authorization':True,'source_revision':reg['source_revision'],
        'scope_sha256':'config-hash','production_CPU_sha256':'proof-hash','launch_id':'CPU-fixture-only',
        'user_reply_quote':'CPU fixture only, never real GPU approval','authorized_single_job_GPUh':12.,
        'scope_sha256':'config-hash','cumulative_cap_GPUh':CAP,'whole_card_not_split':True,
        'explicit_strictly_over8_GPUh_whole_card_approved':True}
    ledger={'cap_gpu_hours':CAP,'used_gpu_hours':79.996377372,'gpu_jobs_launched':1}
    gpu={'uuid':'GPU-CPU-fixture','name':'NVIDIA RTX A6000','compute_cap':'8.6','memory_used_mib':24,'pids':[]}
    return c,permission,proof,reg,ledger,gpu


class Full864Launch(unittest.TestCase):
    def test_exact_new_card_source_and_CPU_permission(self):
        c,p,proof,reg,_,_=fixtures()
        verify_permission(c,p,proof,reg,scope_sha256='config-hash',proof_sha256='proof-hash')
        for key in ('source_revision','scope_sha256','production_CPU_sha256','user_reply_quote','launch_id'):
            bad=copy.deepcopy(p);bad[key]=''
            with self.assertRaises(ValueError):verify_permission(c,bad,proof,reg,scope_sha256='config-hash',proof_sha256='proof-hash')

    def test_old_or_unvalidated_CPU_cannot_authorize(self):
        c,p,proof,reg,_,_=fixtures()
        old={'direct_user_authorization':True,'automatic_single_job_GPUh':8,'remaining_GPUh':48}
        with self.assertRaises(ValueError):verify_permission(c,old,proof,reg,scope_sha256='config-hash',proof_sha256='proof-hash')
        for key,new in [('launch_controls_accepted',False),('CUDA_initialized',True),('weights_loaded',1),('exit_code',1)]:
            bad=copy.deepcopy(proof);bad[key]=new
            with self.assertRaises(ValueError):verify_permission(c,p,bad,reg,scope_sha256='config-hash',proof_sha256='proof-hash')

    def test_remaining_original_window_no_reservation(self):
        c,p,_,_,ledger,gpu=fixtures();before=copy.deepcopy(ledger)
        remaining,limit=verify_admission(c,p,fixtures()[2],ledger,gpu,gpu['uuid'])
        self.assertAlmostEqual(remaining,24.97498596101378);self.assertEqual(limit,12.)
        self.assertEqual(before,ledger)

    def test_inflight_wrong_cap_or_insufficient_balance_refused(self):
        c,p,_,_,ledger,gpu=fixtures()
        for change in ({'other_inflight':{}},{'cap_gpu_hours':48.},
                {'used_gpu_hours':CAP-1}, {'used_gpu_hours':float('nan')}, {'used_gpu_hours':True}):
            with self.assertRaises(ValueError):verify_admission(c,p,fixtures()[2],{**ledger,**change},gpu,gpu['uuid'])

    def test_fresh_UUID_VRAM_device_and_process_gate(self):
        c,p,_,_,ledger,gpu=fixtures()
        for change in ({'uuid':'GPU-stale'},{'memory_used_mib':1025},{'memory_used_mib':-1},
                {'pids':[123]},{'compute_cap':'8.0'},{'name':'different GPU'}):
            with self.assertRaises(ValueError):verify_admission(c,p,fixtures()[2],ledger,{**gpu,**change},gpu['uuid'])

    def test_strict_over8_and_complete_forecast_limit(self):
        c,p,proof,_,ledger,gpu=fixtures()
        for limit in (7.,8.001,11.,float('nan'),True):
            with self.assertRaises(ValueError):verify_admission(c,{**p,'authorized_single_job_GPUh':limit},proof,ledger,gpu,gpu['uuid'])
        with self.assertRaises(ValueError):verify_admission(c,{**p,'explicit_strictly_over8_GPUh_whole_card_approved':False},proof,ledger,gpu,gpu['uuid'])
        _,limit=verify_admission(c,p,proof,ledger,gpu,gpu['uuid']);self.assertEqual(limit,12.)

    def test_actual_child_and_post_argv_share_scope(self):
        a=SimpleNamespace(stage=Path('/fixture/.sync/PA'),project=Path('/fixture'),
            source_revision='e'*40,authorization=Path('/fixture/new-approval.json'))
        child=SUPERVISOR.child_command(a,'GPU-CPU-fixture')
        self.assertIn(str(a.authorization),child);self.assertIn(a.source_revision,child)
        self.assertEqual(Path(child[2]).name,'run_wc_w3_label64_full864_r1.py')
        output,post=POST.paths(a.stage,a.project)
        self.assertEqual(output,a.project/'outputs/wc-w3-label-expldev8-parent18-local64-full864-r1')
        self.assertEqual(Path(post[1]).name,'postprocess_wc_w3_label64_full864_cpu_r1.py')
        compile(LAUNCH.remote_code({'stage':str(a.stage)},{},'GPU-fixture'),'same-real-dispatch','exec')

    def test_default_plan_and_no_permission_never_SSH(self):
        with tempfile.TemporaryDirectory() as directory:
            ref=Path(directory)/'launch.json';ref.write_text(json.dumps({'launch':{'stage':'/CPU-fixture','source_revision':'e'*40}}))
            with patch.object(LAUNCH.subprocess,'run',side_effect=AssertionError('SSH forbidden')) as remote:
                with contextlib.redirect_stdout(io.StringIO()) as output:LAUNCH.main(['--cpu-launch-ref',str(ref)])
                self.assertEqual(json.loads(output.getvalue())['SSH_calls'],0)
                with self.assertRaises(ValueError):LAUNCH.main(['--cpu-launch-ref',str(ref),'--launch'])
                remote.assert_not_called()

    @contextlib.contextmanager
    def stage_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);stage=root/'.sync/PA-CPU-fixture';stage.mkdir(parents=True)
            c,p,proof,reg,_,_=fixtures()
            path=stage/LAUNCH.CONFIG;path.parent.mkdir();path.write_text(json.dumps(c))
            sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
            reg['payload_sha256']={LAUNCH.CONFIG:sha(path)}
            reg_path=stage/'registration.json';reg_path.write_text(json.dumps(reg))
            proof['scope_sha256']=sha(path);proof['registration_sha256']=sha(reg_path)
            proof_path=stage/'production-CPU-result.json';proof_path.write_text(json.dumps(proof))
            p.update(scope_sha256=sha(path),production_CPU_sha256=sha(proof_path))
            yield root,stage,{'stage':str(stage),'source_revision':reg['source_revision'],'registration_sha256':sha(reg_path)},p

    def test_one_dispatch_then_original_handle_returned(self):
        with self.stage_fixture() as (root,stage,launch,p):
            with patch.object(LAUNCH.subprocess,'Popen',side_effect=[SimpleNamespace(pid=101),SimpleNamespace(pid=102)]) as spawn:
                first=LAUNCH.dispatch(root,launch,p,'GPU-CPU-fixture')
                second=LAUNCH.dispatch(root,launch,p,'GPU-CPU-fixture')
            self.assertEqual(spawn.call_count,2);self.assertEqual(second['original'],first)
            self.assertEqual(second['status'],'ORIGINAL_W3_DISPATCH_RETURNED_NO_RESTART')
            self.assertEqual(first['post_command'][-1],'101')
            changed={**p,'launch_id':'different'}
            with self.assertRaises(ValueError):LAUNCH.dispatch(root,launch,changed,'GPU-CPU-fixture')

    def test_unknown_claim_never_restarts(self):
        with self.stage_fixture() as (root,stage,launch,p):
            (stage/'GPU-dispatch-claim').mkdir()
            with patch.object(LAUNCH.subprocess,'Popen',side_effect=AssertionError('No restart')) as spawn:
                with self.assertRaisesRegex(ValueError,'Unknown original'):LAUNCH.dispatch(root,launch,p,'GPU-CPU-fixture')
                spawn.assert_not_called()

    def test_post_spawn_failure_preserves_original_supervisor(self):
        with self.stage_fixture() as (root,stage,launch,p):
            with patch.object(LAUNCH.subprocess,'Popen',side_effect=[SimpleNamespace(pid=101),OSError('fixture post failure')]):
                with self.assertRaises(OSError):LAUNCH.dispatch(root,launch,p,'GPU-CPU-fixture')
            receipt=json.loads((stage/'GPU-launch.json').read_text())
            self.assertEqual(receipt['supervisor_pid'],101)
            self.assertEqual(receipt['status'],'W3_ORIGINAL_SUPERVISOR_DISPATCHED_POST_FAILED')
            with patch.object(LAUNCH.subprocess,'Popen',side_effect=AssertionError('No duplicate')) as spawn:
                original=LAUNCH.dispatch(root,launch,p,'GPU-CPU-fixture');spawn.assert_not_called()
            self.assertEqual(original['original'],receipt)


if __name__=='__main__':unittest.main()
