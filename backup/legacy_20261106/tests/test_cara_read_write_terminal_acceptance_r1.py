"""Original real-Alex CPU acceptance and incomplete/overstated proof refusals."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from accept_cara_read_write_terminal_linux_cpu_r1 import accept


class Acceptance(unittest.TestCase):
    def setUp(self):
        self.launch = ROOT/'reports/cara_read_write_terminal_Linux_CPU_prepare_r1_20261101.json'
        self.capture = ROOT/'reports/cara_read_write_terminal_Linux_CPU_capture_r1_20261101.json'

    def test_original_real_metric_complete93_input_VJP_accepted(self):
        result = accept(self.launch, self.capture)
        self.assertTrue(result['real_Alex_input_VJP'])
        self.assertTrue(result['synthetic_video'])
        self.assertFalse(result['actual_pretrained_VAE'])
        self.assertFalse(result['real_Cosmos_adjoint'])

    def reject_proof(self, mutate):
        value = json.loads(self.capture.read_text());cap = value['result']
        mutate(cap['CPU_proof'])
        cap['CPU_proof_sha256'] = hashlib.sha256((json.dumps(cap['CPU_proof'], indent=2)+'\n').encode()).hexdigest()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)/'capture.json';target.write_text(json.dumps(value))
            with self.assertRaises(AssertionError):
                accept(self.launch, target)

    def test_partial_frames_weights_and_missing_derivative_refused(self):
        self.reject_proof(lambda p:p.update(frames=92))
        self.reject_proof(lambda p:p['weights_sha256'].pop(next(iter(p['weights_sha256']))))
        self.reject_proof(lambda p:p['metrics']['full93_real_Alex_directional_FD'].pop())

    def test_forged_tolerance_and_real_model_scope_refused(self):
        self.reject_proof(lambda p:p['metrics']['full93_real_Alex_directional_FD'][0].update(
            central_FD=0, absolute_error=.014033786952495575, tolerance=1))
        self.reject_proof(lambda p:p.update(actual_pretrained_VAE=True))
        self.reject_proof(lambda p:p.update(real_experiment_video_read=True))


if __name__ == '__main__':
    unittest.main()
