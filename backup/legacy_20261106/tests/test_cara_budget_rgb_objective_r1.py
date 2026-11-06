import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import numpy as np

from wcomr.cara_budget_rgb_objective_r1 import save_endpoint, read_endpoint, full_rgb_mse


class RGBObjectiveTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name)/'endpoint'
        self.identity = dict(member='CPU_FIXTURE', context_sha256='1'*64, kind='NATIVE',
            RGB_shape=[3,93,2,2], generation_seed=0)
        self.rgb = np.zeros((3,93,2,2), dtype=np.float32)

    def test_loss_uses_all93_frames_and_all_channels_pixels(self):
        changed = self.rgb.copy()
        changed[2,92,1,1] = 1
        self.assertEqual(full_rgb_mse(changed,self.rgb), 1/self.rgb.size)
        self.assertEqual(full_rgb_mse(self.rgb,self.rgb), 0)
        self.assertEqual(full_rgb_mse(np.ones_like(self.rgb),self.rgb), 1)

    def test_original_array_roundtrip_and_identity(self):
        self.rgb[:] = np.linspace(0,1,self.rgb.size,dtype=np.float32).reshape(self.rgb.shape)
        saved = save_endpoint(self.path,self.identity,self.rgb)
        recovered, receipt = read_endpoint(self.path,self.identity)
        self.assertTrue(np.array_equal(recovered,self.rgb))
        self.assertEqual(saved,receipt)
        self.assertFalse(recovered.flags.writeable)
        with self.assertRaises(FileExistsError): save_endpoint(self.path,self.identity,self.rgb)

    def test_wrong_teacher_input_context_seed_or_geometry_refused(self):
        save_endpoint(self.path,self.identity,self.rgb)
        for change in (dict(member='CHECK'),dict(context_sha256='2'*64),dict(generation_seed=1),
                       dict(RGB_shape=[3,93,1,4]),dict(kind='CANDIDATE')):
            with self.subTest(change=change),self.assertRaises(ValueError):
                read_endpoint(self.path,dict(self.identity,**change))

    def test_partial_invalid_or_wrong_encoding_never_saved(self):
        for rgb in (self.rgb[:,:92], self.rgb.astype(np.uint8), self.rgb.astype(np.float64),
                    self.rgb+2, self.rgb-1, self.rgb+np.nan, self.rgb+np.inf):
            with self.subTest(shape=rgb.shape,dtype=str(rgb.dtype)), self.assertRaises(ValueError):
                save_endpoint(self.path,self.identity,rgb)
            self.assertFalse(self.path.exists())

    def test_changed_rgb_or_missing_terminal_never_accepted(self):
        save_endpoint(self.path,self.identity,self.rgb)
        path = self.path/'RGB.npy'
        original = path.read_bytes()
        path.write_bytes(original[:-1]+bytes([original[-1]^1]))
        with self.assertRaises(ValueError): read_endpoint(self.path,self.identity)
        path.write_bytes(original)
        (self.path/'complete.json').unlink()
        with self.assertRaises(ValueError): read_endpoint(self.path,self.identity)

    def test_geometry_mismatch_and_nonfinite_objective_refused(self):
        with self.assertRaises(ValueError): full_rgb_mse(self.rgb,self.rgb[:,:,:1])
        with self.assertRaises(ValueError): full_rgb_mse(self.rgb+np.nan,self.rgb)


if __name__=='__main__':
    unittest.main()
