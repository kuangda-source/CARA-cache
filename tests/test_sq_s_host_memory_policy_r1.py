"""Host admission headroom stays separate from the unchanged 40GiB hard cap."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from test_sq_s_execution_r2 import fixture, script, validate_fixture
from test_sq_gpu_allocation_r1 import Storage
from wcomr import sq_control_storage_r1, sq_gpu_allocation_r1, sq_s_execution_r2
from wcomr.gpu_budget_pool_v2 import atomic_json, sha
from wcomr.sq_s_spec_r2 import PROFILE, RUN

ROOT = Path(__file__).resolve().parents[1]


class HostMemoryPolicyTests(unittest.TestCase):
    def test_new_policy_keeps_40GiB_cap_and_10GiB_host_headroom(self):
        profile = json.loads((ROOT / PROFILE).read_text())
        old = json.loads((ROOT / 'plans/cara_next_stage_20261028/sq/S_EXECUTION_PROFILE_R2.json').read_text())
        self.assertEqual(profile['host_RAM_GiB'], 40)
        self.assertEqual(profile['minimum_host_MemAvailable_GiB'], 50)
        self.assertEqual(old['minimum_host_MemAvailable_GiB'], 52)
        for key in old.keys() - {'schema', 'minimum_host_MemAvailable_GiB'}:
            self.assertEqual(profile[key], old[key], key)

    def check_guardian_boundary(self, available_bytes, accepted):
        guardian = script('cara_sq_s_guardian_r2')
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            stage, _, _, _ = fixture(project)
            validated = validate_fixture(project, stage)
            storage = Storage(project / 'outputs' / RUN)
            def allocation(*args, **kwargs):
                return args[7]()
            with patch.object(sq_s_execution_r2, 'validate', return_value=validated), \
                    patch.object(sq_control_storage_r1, 'storage_for', return_value=storage), \
                    patch.object(sq_gpu_allocation_r1, 'run_allocation', side_effect=allocation), \
                    patch.object(guardian, 'available_memory_bytes', return_value=available_bytes), \
                    patch.object(guardian.os, 'sched_getaffinity', return_value={24, 25}, create=True), \
                    patch.object(guardian, 'container_arguments', return_value=['CPU_ONLY_COMMAND']) as command:
                if accepted:
                    self.assertEqual(guardian.run(SimpleNamespace(project=project, stage=stage), 'CPU_NON_SECRET'),
                        ['CPU_ONLY_COMMAND'])
                    self.assertEqual(command.call_count, 1)
                else:
                    with self.assertRaisesRegex(ValueError, 'host RAM'):
                        guardian.run(SimpleNamespace(project=project, stage=stage), 'CPU_NON_SECRET')
                    command.assert_not_called()

    def test_one_byte_below_50GiB_refuses_before_container(self):
        self.check_guardian_boundary(50 * 2**30 - 1, False)

    def test_exactly_50GiB_can_build_original_container(self):
        self.check_guardian_boundary(50 * 2**30, True)

    def test_observed_51_67GiB_is_not_blocked_by_the_old_rounding_margin(self):
        self.check_guardian_boundary(55479066624, True)

    def test_source_validator_rejects_less_than_10GiB_headroom(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            stage, _, _, _ = fixture(project)
            profile = json.loads((stage / PROFILE).read_text())
            profile['minimum_host_MemAvailable_GiB'] = 49
            atomic_json(stage / PROFILE, profile)
            registration = json.loads((stage / 'registration.json').read_text())
            registration['payload_sha256'][PROFILE] = sha(stage / PROFILE)
            atomic_json(stage / 'registration.json', registration)
            with self.assertRaisesRegex(ValueError, 'resource boundary'):
                sq_s_execution_r2.validate_source(project, stage)

    def test_same_kernel_identity_survives_a_container_hostname(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            stage, _, _, _ = fixture(project)
            with patch.object(sq_s_execution_r2, 'kernel_boot_id', return_value=sq_s_execution_r2.kernel_boot_id()), \
                    patch.object(sq_s_execution_r2.socket, 'gethostname', return_value='CPU_CONTAINER_HOSTNAME'):
                sq_s_execution_r2.validate_source(project, stage)

    def test_foreign_kernel_boot_identity_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            stage, _, _, _ = fixture(project)
            registration = json.loads((stage / 'registration.json').read_text())
            registration['native_boot_id'] = 'CPU_FOREIGN_BOOT_ID'
            atomic_json(stage / 'registration.json', registration)
            with self.assertRaisesRegex(ValueError, 'host/stage'):
                sq_s_execution_r2.validate_source(project, stage)


if __name__ == '__main__':
    unittest.main()
