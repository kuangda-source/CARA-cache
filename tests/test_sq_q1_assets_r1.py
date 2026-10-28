import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch
from wcomr.sq_q1_assets_r1 import B1Reader,file_sha,real_geometry
from wcomr.sq_q1_spec_r1 import STATE_KEYS


def tiny_assets(root):
    """A new explicitly synthetic manifest, never the immutable real B1 SHA."""
    def save(name,value):
        path=root/name;torch.save(value,path)
        return dict(name=name,bytes=path.stat().st_size,sha256=file_sha(path))
    anchors=[save('anchor-'+str(n)+'.pt',dict(probe=torch.ones(2),residual=torch.ones(2))) for n in range(20)]
    states=[]
    for index,(prompt,step) in enumerate(STATE_KEYS):
        value=dict(context=(prompt,'Cosmos-Predict2.5-2B-post-trained','SYNTHETIC_CONDITION'),
            step=step,anchors=((anchors[0],anchors[1]),(anchors[2],anchors[3])))
        states.append(dict(prompt=prompt,step=step,artifact=save('state-'+str(index)+'.pt',value)))
    path=root/'manifest.json';path.write_text(json.dumps(dict(states=states,unique_anchors=anchors)))
    return file_sha(path)


class AssetTests(unittest.TestCase):
    def test_all_32_hashes_precede_loading_and_synthetic_geometry_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);digest=tiny_assets(root)
            with patch('wcomr.sq_q1_assets_r1.MANIFEST_SHA',digest):
                reader=B1Reader(root)
                with self.assertRaises(ValueError):reader.load(reader.records[0])
                progress=[];reader.verify_files(lambda done,total:progress.append((done,total)))
                self.assertEqual(progress[-1],(32,32))
                value=reader.load(reader.records[0])
                self.assertEqual(len(value['anchors']),2)
                value.update(current=[dict(original=torch.ones(2),probe=torch.ones(2),embedding=torch.ones(2),adaln=torch.ones(2))]*2,
                    teacher_hidden=[torch.ones(2)]*2,teacher=[torch.ones(2)]*2,
                    readouts={'WC_C':{'outputs':[torch.ones(2)]*2}},pair_inputs=dict(noise=torch.ones(2),latent=torch.ones(2)))
                with self.assertRaises(ValueError):real_geometry(value)

    def test_changed_file_and_symlink_refuse_without_rehashing_all_inputs(self):
        for case in ('changed','symlink'):
            with self.subTest(case=case),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);digest=tiny_assets(root)
                with patch('wcomr.sq_q1_assets_r1.MANIFEST_SHA',digest):
                    reader=B1Reader(root);reader.verify_files(lambda *args:None)
                    path=root/reader.records[0]['artifact']['name']
                    if case=='changed':
                        raw=path.read_bytes();path.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
                    else:
                        other=root/'renamed.pt';path.rename(other);path.symlink_to(other)
                    with self.assertRaises(ValueError):reader.load(reader.records[0])

    def test_real_manifest_sha_cannot_be_replaced_by_a_tiny_fixture(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);tiny_assets(root)
            with self.assertRaises(ValueError):B1Reader(root)


if __name__=='__main__':unittest.main()
