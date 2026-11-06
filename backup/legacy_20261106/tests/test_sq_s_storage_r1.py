"""Actual CPU-file streaming, anchor reuse and terminal storage failures."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import torch

from wcomr.sq_risk_r1 import TARGETS
from wcomr.sq_s_sources_r1 import PARENTS
from wcomr.sq_s_storage_r1 import RAW_STEPS,SCollectionStore

tensor_loader=torch.load

def fixture(prompt,parent,step):
    context=['CPU:'+prompt,'declared_small_model',parent]
    past=tuple(t for t in PARENTS[parent] if t<step)[-2:]
    selected=parent=='F19-C' and step in RAW_STEPS
    source=dict(context=context,parent=parent,step=step,source_anchor_steps=list(past),
        current_D_in_source=False,source_captured_before_parent_pair=True)
    row=dict(prompt=prompt,parent=parent,step=step,context=context,source=source,
        raw_state_selected=selected,moments=dict(C=1.,U=2.,K=.5),parent_roundtrip_equal=True)
    if not selected:return row,None
    anchors=tuple(tuple(dict(context=context,branch=b,step=t,xi=t/37,probe=torch.full((2,3),float(t)+b/10),
        residual=torch.full((2,3),float(t)+b/10+.5)) for t in past) for b in (0,1))
    raw=dict(schema='SQ_S_F19_RAW_CPU_DATA_R2',prompt=prompt,parent=parent,step=step,
        context=context,source=source,anchors=anchors,current=[dict(original=torch.ones(2,3)) for _ in (0,1)],
        teacher=(torch.ones(2,3),torch.ones(2,3)),teacher_features=[dict(hidden=torch.ones(2,3)) for _ in (0,1)],
        pair_inputs=dict(latent=torch.zeros(2,3)),P1_Dense_hidden_head_replay_accepted=False,
        serialized_whole_pipeline_resume_accepted=False)
    return row,raw


def store(root,**kwargs):
    return SCollectionStore(root,prompts=('P0_CPU','P1_CPU'),maximum_total_bytes=kwargs.get('total',4*2**20),
        maximum_file_bytes=kwargs.get('file',2**20),minimum_free_bytes=2**20)


class StorageTests(unittest.TestCase):
    def test_complete108_streams_eight_raw_and_deduplicates24_anchors(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'complete';sink=store(root)
            for prompt in sink.prompts:
                for parent in PARENTS:
                    for step in TARGETS:sink(*fixture(prompt,parent,step))
            receipt=sink.finish();manifest=json.loads((root/'manifest.json').read_text())
            self.assertEqual((len(manifest['rows']),len(manifest['raw_states']),len(manifest['anchors'])),(108,8,24))
            self.assertEqual(receipt['actual_stored_bytes'],sum(p.stat().st_size for p in root.iterdir()))
            self.assertFalse(list(root.glob('*.partial')))
            for entry in manifest['rows']+manifest['raw_states']:
                artifact=entry['artifact'];path=root/artifact['name']
                self.assertEqual(path.stat().st_size,artifact['bytes'])
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),artifact['sha256'])
            selected={r['step']:r for r in manifest['raw_states'] if r['prompt']=='P0_CPU'}
            a,b=(tensor_loader(root/selected[t]['artifact']['name'],map_location='cpu',weights_only=True) for t in (33,35))
            self.assertNotIn('anchors',a);self.assertEqual(a['anchor_refs'],b['anchor_refs'])
            for pair in a['anchor_refs']:
                for ref in pair:
                    anchor=tensor_loader(root/ref['name'],map_location='cpu',weights_only=True)
                    self.assertIn(anchor['step'],(27,30));self.assertEqual(anchor['probe'].device.type,'cpu')
            with self.assertRaises(ValueError):sink(*fixture('P0_CPU','Shared25-C',8))
            with self.assertRaises(FileExistsError):store(root)

    def test_same_anchor_identity_cannot_change_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            sink=store(Path(directory)/'changed');sink(*fixture('P0_CPU','F19-C',33))
            row,raw=fixture('P0_CPU','F19-C',35);raw['anchors'][0][0]['probe'].add_(1)
            with self.assertRaisesRegex(ValueError,'different true-anchor bytes'):sink(row,raw)
            self.assertTrue(sink.failed);self.assertFalse((sink.root/'manifest.json').exists())
            with self.assertRaises(ValueError):sink.finish()

    def test_current_D_source_and_missing_selected_raw_fail_terminally(self):
        with tempfile.TemporaryDirectory() as directory:
            for label in ('current_D','missing_raw'):
                sink=store(Path(directory)/label)
                row,raw=fixture('P0_CPU','Shared25-C',8) if label=='current_D' else fixture('P0_CPU','F19-C',9)
                if label=='current_D':row['source']['source_anchor_steps'][-1]=row['step']
                else:raw=None
                with self.assertRaises(ValueError):sink(row,raw)
                self.assertTrue(sink.failed);self.assertFalse(list(sink.root.iterdir()))
                with self.assertRaises(ValueError):sink(*fixture('P0_CPU','Shared25-C',9))

    def test_actual_stream_file_and_total_caps_keep_original_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            large=store(Path(directory)/'file',total=8192,file=4096)
            row,raw=fixture('P0_CPU','F19-C',9)
            raw['anchors'][0][0]['probe']=torch.zeros(8192)
            with self.assertRaises((RuntimeError,OSError)):large(row,raw)
            self.assertTrue(large.failed);self.assertTrue(list(large.root.glob('*.partial')))
            self.assertFalse((large.root/'manifest.json').exists());self.assertLessEqual(large.written,4096)
            total=store(Path(directory)/'total',total=4096,file=4096)
            with self.assertRaises(OSError):
                for step in range(8,22):total(*fixture('P0_CPU','Shared25-C',step))
            self.assertTrue(total.failed);self.assertLessEqual(total.written,4096)
            self.assertTrue(list(total.root.glob('*.partial')))
            with self.assertRaises(ValueError):total.finish()

    def test_duplicate_row_and_incomplete_finish_cannot_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            sink=store(Path(directory)/'duplicate');args=fixture('P0_CPU','Shared25-C',8);sink(*args)
            original={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sink.root.iterdir()}
            with self.assertRaises(ValueError):sink(*args)
            self.assertTrue(sink.failed)
            self.assertEqual(original,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sink.root.iterdir()})
            incomplete=store(Path(directory)/'incomplete')
            with self.assertRaises(ValueError):incomplete.finish()
            self.assertTrue(incomplete.failed)
            with self.assertRaises(ValueError):incomplete(*fixture('P0_CPU','Shared25-C',8))


if __name__=='__main__':unittest.main()
