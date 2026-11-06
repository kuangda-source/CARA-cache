"""Run pinned native utility bodies; no weights, codecs or neural models."""
import ast
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np
import torch
import torch.nn.functional as F

from wcomr.imaging_quality import prepare_frame

ROOT = Path(__file__).resolve().parents[1]
PACK = json.loads((ROOT/'reports/wc_paper_N10_complete_pinned_code_resource_pack_20261016.json').read_text())


def original_class(relative, name):
    record = next(r for r in PACK['records'] if r['path']==relative)
    path = ROOT/PACK['source_root']/relative; raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==record['sha256']
    node=next(n for n in ast.parse(raw).body if isinstance(n,ast.ClassDef) and n.name==name)
    namespace={'F':F,'torch':torch,'np':np}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    return namespace[name]


class NativeMetricUtilityControls(unittest.TestCase):
    def test_actual_AMT_single_unpad_and_probe_expression_preserve_batch(self):
        Padder=original_class('vbench/third_party/amt/utils/utils.py','InputPadder')
        original=torch.zeros(1,3,432,768);padder=Padder(original.shape,16)
        prediction=padder.pad(original)
        path=ROOT/'scripts/evaluate_wc_N10_metric_model_cpu_r1.py'
        expressions=[n.value for n in ast.walk(ast.parse(path.read_text())) if isinstance(n,ast.Assign)
                     and any(isinstance(t,ast.Name) and t.id=='prediction' for t in n.targets)
                     and 'padder.unpad' in ast.unparse(n.value)]
        self.assertEqual(len(expressions),1)
        result=eval(compile(ast.Expression(expressions[0]),str(path),'eval'),{'padder':padder,'prediction':prediction})
        self.assertEqual(list(result.shape),[1,3,432,768]);self.assertTrue(torch.equal(result,original))

    def test_AMT_native_multi_tensor_unpad_restores_uneven_geometry(self):
        Padder=original_class('vbench/third_party/amt/utils/utils.py','InputPadder')
        left=torch.arange(3*17*19).view(1,3,17,19).float();right=left+1
        padder=Padder(left.shape,16);padded=padder.pad(left,right);result=padder.unpad(*padded)
        self.assertIsInstance(result,list);self.assertEqual(len(result),2)
        self.assertTrue(torch.equal(result[0],left));self.assertTrue(torch.equal(result[1],right))

    def test_RAFT_native_pad_pair_and_single_flow_unpad_keep_batch(self):
        Padder=original_class('vbench/third_party/RAFT/core/utils_core/utils.py','InputPadder')
        image=torch.zeros(1,3,17,19);padder=Padder(image.shape)
        left,right=padder.pad(image,image)
        flow=torch.zeros(1,2,*left.shape[-2:]);output=padder.unpad(flow)
        self.assertEqual(list(left.shape),list(right.shape));self.assertEqual(list(output.shape),[1,2,17,19])

    def test_actual_MUSIQ_preprocessing_is_longer512_and_raw_unit_interval(self):
        frame=np.full((432,768,3),64,dtype=np.uint8);result=prepare_frame(frame)
        self.assertEqual(list(result.shape),[1,3,288,512]);self.assertEqual(result.dtype,torch.float32)
        self.assertTrue(torch.allclose(result,torch.full_like(result,64/255.),atol=1e-7))


if __name__=='__main__':unittest.main()
