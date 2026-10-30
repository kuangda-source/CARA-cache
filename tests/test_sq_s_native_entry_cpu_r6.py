"""Synthetic acceptance packets test refusals; no native acceptance is saved."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import audit_cara_sq_s_production_entry_cpu_r6 as audit
from test_sq_s_execution_r2 import script

ROOT = Path(__file__).resolve().parents[1]
SCOPE = 'plans/cara_next_stage_20261028/sq/S_NATIVE_ENTRY_CPU_R6.json'
LOCAL = 'reports/cara_sq_s_cli_composition_local_r5_20261030.json'


def packet():
    scope = json.loads((ROOT/SCOPE).read_text())
    local = json.loads((ROOT/LOCAL).read_text())['profiles']['four_card']['proof']
    rows = copy.deepcopy(local['rows'])
    for row in rows: row['full_native_WC_RF_module_namespaces'] = True
    controls = [dict(scenario=name, flow=scope['supervisor_flows'][index], host='four_card', passed=True,
        real_Linux_PID_start_ticks_and_inherited_lease=True, original_child_exited=True,
        original_lease_released=True, replay_refused=True, technical_accepted=name == 'complete',
        diagnostic_bill_chargeable=False) for index, name in enumerate(scope['supervisor_scenarios'])]
    result = dict(status='S_NATIVE_IMPORTS_CLI_MATRIX_AND_LINUX_LIFECYCLE_CPU_PASS',
        profile='four_card', scope=scope, actual_platform=dict(system='Linux'), torch_version='2.7.1+cu128',
        unit_controls=dict(tests=scope['unit_controls'], skipped=0, errors=0, failures=0),
        critical_source_sha256=scope['critical_source_sha256'], rows=rows, supervisor_controls=controls,
        actual_full_inference_module_import=True, actual_full_WC_RF_module_imports=True,
        actual_native_parser=True, CPU_import_probes_restored=True,
        model_loads_are_declared_tiny_CPU_standins=True, weight_loads_forbidden=True,
        downloads_and_socket_outbound_blocked=True,
        pinned_config_source_sha256=scope['native_parser_source_sha256'], checkpoint_lookup_is_metadata_sentinel=False,
        checkpoint_cache_lookups=[dict(bytes=scope['diffusion_checkpoint_bytes'])],
        tiny_tensor_load_calls=80, unique_tiny_tensor_files_loaded=64,
        actual_weights_loaded=False, real_generated_video=False, CUDA_initialized=False,
        actual_GPU_entry_accepted=False, full_S_entry_CPU_accepted=False,
        real_S_labels=0, GPU_submissions=0, new_GPUh=0, real_central_ledger_writes=0,
        CPU_wall_seconds=10., CPU_seconds=5., peak_RSS_KiB=1024)
    capture = dict(original_CLI_live=False, source_hashes_equal=True, runtime_hashes_equal=True,
        registration=dict(source_revision='SYNTHETIC_CPU_UNIT_ONLY', GPU_submissions=0,
            payload_sha256=scope['critical_source_sha256']),
        container_state=dict(Running=False, Status='exited', ExitCode=0,
            StartedAt='2026-10-30T00:00:00+00:00', FinishedAt='2026-10-30T00:00:12+00:00'),
        host_config=dict(DeviceRequests=[], NetworkMode='none', Memory=8*2**30,
            MemorySwap=8*2**30, NanoCpus=2*10**9, CpusetCpus='4,5'), result=result)
    digest = hashlib.sha256((json.dumps(capture['registration'], indent=2)+'\n').encode()).hexdigest()
    capture.update(registration_sha256=digest, launch=dict(source_revision='SYNTHETIC_CPU_UNIT_ONLY', registration_sha256=digest))
    return capture, scope


class NativeAcceptanceTests(unittest.TestCase):
    def accept(self, capture, scope):
        capture['result_sha256'] = hashlib.sha256((json.dumps(capture['result'], indent=2,
            allow_nan=False)+'\n').encode()).hexdigest()
        return audit.accept(capture, scope, 'four_card', 'SYNTHETIC_CPU_UNIT_ONLY')

    def test_valid_synthetic_packet_only_classifies_CPU(self):
        capture, scope = packet(); result = self.accept(capture, scope)
        self.assertTrue(result['full_S_entry_CPU_accepted']); self.assertFalse(result['actual_GPU_entry_accepted'])
        self.assertEqual(result['GPU_submissions'], 0)

    def test_local_Darwin_or_skipped_controls_cannot_clear_native_gate(self):
        for mutate in (lambda r: r['actual_platform'].update(system='Darwin'),
                lambda r: r['unit_controls'].update(skipped=1),
                lambda r: r.update(actual_full_WC_RF_module_imports=False)):
            capture, scope = packet(); mutate(capture['result'])
            with self.assertRaises(ValueError): self.accept(capture, scope)

    def test_live_container_GPU_exposure_or_wrong_resources_refused(self):
        for mutate in (lambda c: c.update(original_CLI_live=True),
                lambda c: c['container_state'].update(Running=True),
                lambda c: c['host_config'].update(DeviceRequests=[{}]),
                lambda c: c['host_config'].update(MemorySwap=16*2**30)):
            capture, scope = packet(); mutate(capture)
            with self.assertRaises(ValueError): self.accept(capture, scope)

    def test_missing_role_or_AST_namespace_is_not_full_native_entry(self):
        for mutate in (lambda r: r['rows'][0].update(new_tiny_paths=9),
                lambda r: r['rows'][1].update(full_native_WC_RF_module_namespaces=False),
                lambda r: r.update(tiny_tensor_load_calls=64)):
            capture, scope = packet(); mutate(capture['result'])
            with self.assertRaises(ValueError): self.accept(capture, scope)

    def test_metadata_sentinel_or_bad_checkpoint_size_refused(self):
        for mutate in (lambda r: r.update(checkpoint_lookup_is_metadata_sentinel=True),
                lambda r: r['checkpoint_cache_lookups'][0].update(bytes=59)):
            capture, scope = packet(); mutate(capture['result'])
            with self.assertRaises(ValueError): self.accept(capture, scope)

    def test_live_child_or_chargeable_inner_diagnostic_refused(self):
        for mutate in (lambda r: r['supervisor_controls'][0].update(original_child_exited=False),
                lambda r: r['supervisor_controls'][1].update(diagnostic_bill_chargeable=True)):
            capture, scope = packet(); mutate(capture['result'])
            with self.assertRaises(ValueError): self.accept(capture, scope)

    def test_stale_source_and_self_approved_worker_refused(self):
        capture, scope = packet(); capture['source_hashes_equal'] = False
        with self.assertRaises(ValueError): self.accept(capture, scope)
        capture, scope = packet(); capture['result']['full_S_entry_CPU_accepted'] = True
        with self.assertRaises(ValueError): self.accept(capture, scope)
        capture, scope = packet(); capture['registration_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'registration bytes'): self.accept(capture, scope)

    def test_native_worker_refuses_non_Linux_before_imports_or_output(self):
        checker = script('check_cara_sq_s_production_entry_cpu_r6')
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'must-not-exist.json'
            argv = ['check', '--assets', str(ROOT/'cache/runtime'), '--output', str(output),
                '--profile', 'four_card', '--scope', SCOPE, '--manifest-sha256', 'CPU_NOT_A_GRANT']
            with patch.object(checker.sys, 'argv', argv), patch.object(checker.platform, 'system', return_value='Darwin'):
                with self.assertRaisesRegex(ValueError, 'requires Linux'): checker.main()
            self.assertFalse(output.exists())


if __name__ == '__main__': unittest.main()
