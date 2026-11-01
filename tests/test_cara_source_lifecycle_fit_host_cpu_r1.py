"""Host probe cohorts use the production broker grammar and CPU command."""
import ast
import json
from pathlib import Path
import tempfile
import unittest

from check_cara_source_lifecycle_fit_host_cpu_r1 import cohort, media_command
from cara_source_lifecycle_fit_host_cpu_r1 import REMOTE
from wcomr.cara_fast_spec_r1 import profile_from, uniform_mask, policy_from_mask
from wcomr.cara_source_lifecycle_search_r1 import legal_swaps
from wcomr.cara_source_lifecycle_fit_scores_r1 import bind_scorer
from wcomr.cara_source_lifecycle_fit_broker_r1 import validate_query

ROOT = Path(__file__).resolve().parents[1]


class HostFitCPUProbeTests(unittest.TestCase):
    def test_complete_three_distinct_cohorts_share_only_native_reference(self):
        parent = json.loads((ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json').read_bytes())
        profile = profile_from(parent['profile'])
        d19, _ = uniform_mask(parent['schedule'], profile, 19)
        d22, _ = uniform_mask(parent['schedule'], profile, 22)
        dense = [d19, d22, legal_swaps(profile, d19, 19)[0][2]]
        policies = [policy_from_mask(profile, d) for d in dense]
        self.assertEqual(len({p['fingerprint'] for p in policies}), 3)
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)/'project'
            stage = project/'.sync'/'HOST_CPU_FIXTURE'
            artifacts = project/'outputs'/'HOST_CPU_FIXTURE'/'algorithm'
            artifacts.mkdir(parents=True)
            environment = dict(torch_home=str(project/'torch'), piq_site=str(project/'piq'), weights_sha256={})
            spec = dict(project=str(project), stage=str(stage), artifact_root=str(artifacts),
                queue=str(artifacts.parent/'internal-FIT-queue'), profile=parent['profile'],
                environment=environment, CPU_fixture_only=True,
                context=dict(run_id='HOST_CPU_FIXTURE', source_revision='1'*40,
                    launch_id='2'*32, CPU_fixture_only=True, host='two_card'))
            for kind in ('reference', 'K19', 'K22', 'SWAP19'):
                for i in range(2):
                    (artifacts/(kind+'-'+str(i)+'.mp4')).write_bytes((kind+str(i)).encode())
            packets = [cohort(spec, p, k) for p, k in zip(policies, ('K19', 'K22', 'SWAP19'))]
            for packet in packets:
                config = bind_scorer(packet, environment, cpu_validation=True)
                validate_query(spec, config)
                self.assertEqual(len(packet['pairs']), 2)
                self.assertEqual(packet['score_shape'], [93, 64, 64, 3])
                for pair in packet['pairs']:
                    proof = json.loads(Path(pair['reference']['proof_path']).read_bytes())
                    self.assertEqual([h['actual'] for h in proof['semantic_history']], ['D']*36)
            for i in range(2):
                self.assertEqual(packets[0]['pairs'][i]['reference'], packets[1]['pairs'][i]['reference'])
                self.assertNotEqual(packets[0]['pairs'][i]['candidate'], packets[1]['pairs'][i]['candidate'])

    def test_media_command_has_real_two_core_boundary_without_gpu_or_socket(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)/'project'
            stage = project/'.sync'/'HOST_CPU_FIXTURE'
            artifact = project/'outputs'/'HOST_CPU_FIXTURE'/'algorithm'
            control = artifact.parent/'CPU-control'
            artifact.mkdir(parents=True)
            command = media_command(project, stage, artifact, control, dict(torch_home=str(project/'torch')), 'a'*64)
            self.assertNotIn('--gpus', command)
            self.assertEqual(command[command.index('--memory')+1], '8g')
            self.assertEqual(command[command.index('--memory-swap')+1], '8g')
            self.assertEqual(command[command.index('--cpuset-cpus')+1], '26,27')
            self.assertEqual(command[command.index('--network')+1], 'none')
            self.assertIn('CUDA_VISIBLE_DEVICES=', command)
            self.assertIn('NVIDIA_VISIBLE_DEVICES=void', command)
            self.assertIn(str(stage)+':'+str(stage)+':ro', command)
            self.assertIn(str(artifact)+':'+str(artifact)+':rw', command)
            self.assertFalse(any('docker.sock' in value for value in command))
        ast.parse(REMOTE)


if __name__ == '__main__':
    unittest.main()
