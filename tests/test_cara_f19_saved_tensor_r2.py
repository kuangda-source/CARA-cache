"""FP32 branch ordering, complete lag cohorts, extrapolation and original-scalar controls."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from wcomr import cara_f19_saved_tensor_r2 as saved


class SavedDiagnostics(unittest.TestCase):
    def fixture(self, root):
        records, payloads = [], {}
        for prompt in ('a','b'):
            for step in (22,23,25,33,34,35):
                c=torch.full((1,1,1,2,2),step*.1)
                u=c-step*.01
                D=(c,u)
                C=(c+.02,u+.02)
                A=(c+.01,u+.01)
                key=f'{prompt}:{step}'
                records.append(dict(prompt=prompt,step=step,artifact=dict(key=key)))
                payloads[key]=dict(context=(prompt,'CPU_fixture','Shared25_C'),step=step,xi=step/36,
                    teacher=D,readouts=dict(WC_C=dict(outputs=C),A_PHASE=dict(outputs=A)),
                    anchors=([dict(step=20),dict(step=21)],[dict(step=20),dict(step=21)]),
                    summary=dict(WC_C=dict(MSE=saved.mse(saved.guided(C),saved.guided(D))),
                                 A_PHASE=dict(MSE=saved.mse(saved.guided(A),saved.guided(D)))),
                    P0_actual_dense=True,P1_dense_head_RF_equal=True,P2_C_actual_parent_equal=True)
        raw=json.dumps(dict(states=records)).encode()
        (root/'manifest.json').write_bytes(raw)
        return payloads,hashlib.sha256(raw).hexdigest()

    def test_full_twelve_state_fp32_and_ten_lags_plus_four_causal_predictions(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);values,digest=self.fixture(root)
            with patch.object(saved,'load_state',side_effect=lambda _,ref:copy.deepcopy(values[ref['key']])):
                result=saved.analyze(root,digest)
            self.assertEqual(result['original_scalar_checks_reproduced'],24)
            self.assertEqual(len(result['state_rows']),12)
            self.assertEqual(len(result['delta_hold_rows']),10)
            self.assertEqual(len(result['linear_delta_extrapolation_rows']),4)
            self.assertEqual(result['lag_summaries']['1']['pairs'],6)
            self.assertEqual(result['lag_summaries']['2']['pairs'],4)
            for row in result['delta_hold_rows']:
                self.assertAlmostEqual(row['held_guided_MSE_FP32'],.0049*row['actual_update_lag']**2,places=6)
                self.assertGreater(row['unconditional_refresh_held_delta_MSE_FP32'],row['held_guided_MSE_FP32'])
            for row in result['state_rows']:
                self.assertGreater(row['cancellation_fraction'],.98)
                self.assertGreater(row['conditional_D_unconditional_C_MSE_FP32'],row['WC_C_guided_MSE_FP32'])
            self.assertLess(result['linear_delta_extrapolation_summary']['MSE'],1e-9)
            self.assertFalse(result['GPU_screen_ready'])
            self.assertIsNone(result['actual_LPIPS'])

    def test_original_scalar_or_parent_changes_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);values,digest=self.fixture(root)
            for key,value in [('summary',None),('context',None)]:
                changed=copy.deepcopy(values)
                if key=='summary':changed['a:22']['summary']['WC_C']['MSE']+=.1
                else:changed['a:23']['context']=('a','another_model','Shared25_C')
                with patch.object(saved,'load_state',side_effect=lambda _,ref:copy.deepcopy(changed[ref['key']])):
                    with self.assertRaises(ValueError):saved.analyze(root,digest)


if __name__=='__main__':
    torch.set_num_threads(2)
    unittest.main()
