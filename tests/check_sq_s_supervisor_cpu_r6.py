"""Real Linux S supervisor/PID/lease controls over new tiny CPU collections.

GPU observations, temperature and credential/storage boundaries are synthetic.
The CPU child publishes the exact collection from the preceding CLI matrix;
it neither loads a model nor creates a CUDA context.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from test_sq_s_execution_r2 import fixture, script
from wcomr.gpu_budget_pool_v2 import atomic_json, DeviceLease, same_live_process
from wcomr import sq_s_execution_r2 as execution
from wcomr import sq_control_storage_r1 as storage_module
from wcomr import wc73_exclusive_r1 as exclusive
from wcomr.sq_s_data_terminal_r2 import check_result
from wcomr.sq_s_spec_r2 import RUN


def run(row, scenario):
    if not Path('/proc/self').exists(): raise ValueError('Actual Linux supervisor controls required')
    if scenario not in ('complete', 'missing_row', 'runner_failure', 'thermal'):
        raise ValueError('Frozen CPU supervisor scenario required')
    scope_path = Path(row['CPU_fixture_scopes_path'])
    assert hashlib.sha256(scope_path.read_bytes()).hexdigest() == row['CPU_fixture_scopes_sha256']
    scopes = json.loads(scope_path.read_text())
    original_collection = (Path(row['output'])/'S-collection.json').read_bytes()
    collection = json.loads(original_collection)
    assert collection['CPU_fixture'] and scopes['upper']['CPU_fixture_only']
    if scenario == 'missing_row':
        next(r['result']['S_rows'] for r in collection['matrix']['rows'] if r['slot']['enabled']).pop()
    worker = script('cara_sq_s_worker_r2')
    with tempfile.TemporaryDirectory(prefix='S-supervisor-CPU-') as directory:
        project = Path(directory)
        stage, authority, registration, _ = fixture(project, row['host'])
        output = project/'outputs'/RUN; output.mkdir(parents=True)
        bundle = dict(scopes, execution_profile=execution.read(stage/'plans/cara_next_stage_20261028/sq/S_EXECUTION_PROFILE_R2.json'))
        source = stage/'CPU-collection.json'; atomic_json(source, collection)
        child_source = '''import json,os,time
from pathlib import Path
from wcomr.gpu_budget_pool_v2 import process_identity,atomic_json
stage=Path(__file__).resolve().parents[1];project=stage.parents[1]
assert str(os.getppid())==os.environ['WC_SUPERVISOR_PID']
assert Path('/proc/self/fd/'+os.environ['WC_LOCK_FD']).resolve()==project/'.sync/gpu-locks'/(__UUID__+'.lock')
if __CASE__=='runner_failure':raise SystemExit(7)
identity={key:process_identity(os.getpid())[key] for key in ('pid','start_ticks')};identity['uid']=os.getuid()
atomic_json(stage/'pg-runner-context-ready.json',dict(identity=identity))
while not (stage/'pg-runner-context-granted.json').exists():time.sleep(.02)
if __CASE__=='thermal':time.sleep(60)
(project/'outputs'/__RUN__/'S-collection.json').write_bytes((stage/'CPU-collection.json').read_bytes())
'''.replace('__UUID__', repr(authority['gpu_uuid'])).replace('__CASE__', repr(scenario)).replace('__RUN__', repr(RUN))
        (stage/'scripts/run_cara_sq_s_r2.py').write_text(child_source)
        class Journal:
            def __init__(self): self.records = []
            def write(self, key, value): self.records.append((key, copy.deepcopy(value)))
        class Storage:
            def __init__(self): self.output = output; self.journal = Journal()
            def check(self): return {}
            def persist(self, key, path, value, writer): self.journal.write(key, value); writer(path, value)
        storage = Storage()
        atomic_json(stage/'pg-host-guardian.json', dict(authority, billing_clock_owner='HOST_GUARDIAN',
            started_monotonic=time.monotonic(), started_unix=time.time()))
        def observe(uuid):
            ready = stage/'pg-runner-context-ready.json'; apps = []
            if ready.exists():
                identity = json.loads(ready.read_text())['identity']
                if same_live_process(identity): apps = [dict(identity, gpu_uuid=uuid, memory_MiB=1)]
            return dict(gpu_uuid=uuid, compute_mode='Exclusive_Process', compute_apps=apps,
                mps_processes=[], observed_unix=time.time())
        def check(bundle, value, new_output):
            # Byte-bound data came from the completed tiny CLI. Its artifacts
            # remain under that original CPU root, not the supervisor sandbox.
            return check_result(value, bundle['upper'], bundle['physical'],
                identity_sha256=bundle['identity']['identity_sha256'],
                resource_contract_sha256=bundle['resource_contract']['contract_sha256'],
                expected_shape=bundle['identity']['expected_real_shape'],
                new_output_root=str(Path(row['output'])/'paths'), CPU_fixture=True)
        before_signal = signal.getsignal(signal.SIGTERM)
        caught = None
        try:
            with patch.object(execution, 'validate', return_value=(bundle, registration, authority)), \
                    patch.object(storage_module, 'storage_for', return_value=storage), \
                    patch.object(exclusive, 'observe', side_effect=observe), \
                    patch.object(worker, 'read_thermal', return_value={'temperature.gpu': '90' if scenario == 'thermal' else '42'}), \
                    patch.object(worker, 'check_collection', side_effect=check):
                try: worker.supervise(SimpleNamespace(project=project, stage=stage))
                except (ValueError, RuntimeError) as error: caught = error
                assert (caught is None) is (scenario == 'complete'), caught
                with unittest.TestCase().assertRaisesRegex(ValueError, 'recover it'):
                    worker.supervise(SimpleNamespace(project=project, stage=stage))
        finally:
            signal.signal(signal.SIGTERM, before_signal)
        state = execution.read(output/'S-supervisor.json')
        release = execution.read(output/'S-supervisor-release-diagnostic.json')
        bill = execution.read(output/'S-supervisor-billing-diagnostic.json')
        assert not same_live_process(state['child_identity'])
        assert release['original_process_exited'] and release['GPU_released']
        assert release['technical_accepted'] is (scenario == 'complete')
        assert bill['billing_clock_owner'] == 'SUPERVISOR_DIAGNOSTIC'
        assert bill['diagnostic_only'] is True and bill['chargeable'] is False
        assert not (project/'reports/gpu-budget-v2.json').exists()
        with DeviceLease(project, authority['gpu_uuid']): pass
        if scenario == 'complete':
            assert (output/'S-collection.json').read_bytes() == source.read_bytes()
            assert (stage/'pg-runner-context-granted.json').exists()
        if scenario == 'thermal':
            assert any(
                key == 'telemetry' and value['thermal']['temperature.gpu'] == '90'
                for key, value in storage.journal.records)
        return dict(scenario=scenario, flow=row['flow'], host=row['host'], passed=True,
            real_Linux_PID_start_ticks_and_inherited_lease=True, original_child_exited=True,
            original_lease_released=True, replay_refused=True, data_checker_CPU_boundary=True,
            original_CLI_collection_sha256=hashlib.sha256(original_collection).hexdigest(),
            child_CPU_collection_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
            deliberate_missing_row=scenario == 'missing_row',
            diagnostic_bill_chargeable=False, diagnostic_wall_seconds=bill['wall_seconds'],
            technical_accepted=release['technical_accepted'], GPU_observation_is_synthetic=True,
            runner_replaced_by_CPU_collection_publisher=True,
            GPU_submissions=0, real_S_labels=0, real_central_ledger_writes=0)
