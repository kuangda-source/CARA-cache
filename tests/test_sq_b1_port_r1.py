"""Real local file copies through a source-only SFTP interface; no tensors."""
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from wcomr.sq_b1_port_r1 import copy_assets


class LocalSource:
    def __init__(self,root):self.root=Path(root);self.calls=0
    def path(self,name):return self.root/Path(name).name
    def open(self,name,mode):
        assert mode=='rb';self.calls+=1;return self.path(name).open(mode)
    def lstat(self,name):
        value=self.path(name).lstat()
        return SimpleNamespace(st_size=value.st_size,st_mtime=value.st_mtime_ns,
            st_mode=value.st_mode,st_uid=value.st_uid,st_gid=value.st_gid)


class ReadvSource(LocalSource):
    def __init__(self,root):super().__init__(root);self.batches=[]
    def open(self,name,mode):
        stream=super().open(name,mode)
        if Path(name).name=='manifest.json':return stream
        owner=self
        class Reader:
            def __enter__(self):return self
            def __exit__(self,*args):stream.close()
            def read(self,size):return stream.read(size)
            def readv(self,chunks):
                owner.batches.append(list(chunks))
                for offset,size in chunks:stream.seek(offset);yield stream.read(size)
        return Reader()


def fixture(root):
    root.mkdir();refs=[]
    for i in range(32):
        data=(str(i)+' exact-old-byte-fixture ').encode()*17;name='fixture-'+str(i)+'.pt'
        (root/name).write_bytes(data);refs.append(dict(name=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    manifest=dict(unique_anchors=refs[:20],states=[dict(artifact=r) for r in refs[20:]])
    raw=(json.dumps(manifest,indent=2)+'\n').encode();(root/'manifest.json').write_bytes(raw)
    return dict(expected_manifest_sha=hashlib.sha256(raw).hexdigest(),
        expected_total_bytes=sum(r['bytes'] for r in refs),minimum_free_bytes=1),refs


class PortTests(unittest.TestCase):
    def test_bounded32_reads_preserve_old_partials_and_exact_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);options,refs=fixture(root/'source')
            first=root/'source'/refs[0]['name'];first.write_bytes(b'R'*(2**20+37))
            refs[0].update(bytes=first.stat().st_size,sha256=hashlib.sha256(first.read_bytes()).hexdigest())
            manifest=dict(unique_anchors=refs[:20],states=[dict(artifact=r) for r in refs[20:]])
            raw=json.dumps(manifest).encode();(root/'source/manifest.json').write_bytes(raw)
            options.update(expected_manifest_sha=hashlib.sha256(raw).hexdigest(),expected_total_bytes=sum(r['bytes'] for r in refs))
            target=root/'target';old=target/'.sq-b1-port-cpu-r1-20261029';old.mkdir(parents=True)
            (old/'original.partial').write_bytes(b'preserve operator-stopped original')
            source=ReadvSource(root/'source')
            result=copy_assets(source,'/readonly',target,readv_requests=32,incoming_name='.sq-b1-port-cpu-r2-20261029',**options)
            self.assertEqual(result['transferred_bytes'],options['expected_total_bytes'])
            self.assertEqual(result['maximum_prefetch_bytes'],2**20)
            self.assertEqual((old/'original.partial').read_bytes(),b'preserve operator-stopped original')
            self.assertTrue(any(len(chunks)==32 for chunks in source.batches))
            self.assertTrue(all(0<len(chunks)<=32 and all(0<n<=32768 for _,n in chunks) for chunks in source.batches))
            self.assertEqual((target/refs[0]['name']).read_bytes(),first.read_bytes())

    def test_complete32_source_stream_and_readback_equal(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);options,refs=fixture(root/'source');source=LocalSource(root/'source');events=[]
            result=copy_assets(source,'/readonly',root/'target',save=lambda value:events.append(value['verified_target_bytes']),**options)
            self.assertEqual(result['copied_files'],32);self.assertEqual(len(result['files']),32)
            self.assertEqual(result['transferred_bytes'],options['expected_total_bytes'])
            self.assertEqual((root/'source/manifest.json').read_bytes(),(root/'target/manifest.json').read_bytes())
            self.assertEqual(sorted(p.name for p in (root/'target').iterdir()),sorted(r['name'] for r in refs)+['manifest.json'])
            self.assertEqual(events[-1],options['expected_total_bytes']);self.assertFalse(result['scientific_or_GPU_acceptance'])

    def test_existing_exact_targets_deduplicate_without_data_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);options,refs=fixture(root/'source');fixture(root/'target');source=LocalSource(root/'source')
            result=copy_assets(source,'/readonly',root/'target',**options)
            self.assertEqual(result['copied_files'],0);self.assertEqual(result['transferred_bytes'],0)
            self.assertEqual(source.calls,1)
            self.assertTrue(all(r['method']=='EXISTING_TARGET_SHA_ONLY_SOURCE_NOT_REREAD' for r in result['files']))

    def test_source_corruption_keeps_partial_and_no_complete_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);options,refs=fixture(root/'source');first=root/'source'/refs[0]['name']
            first.write_bytes(b'X'*first.stat().st_size)
            with self.assertRaisesRegex(ValueError,'SHA differs'):copy_assets(LocalSource(root/'source'),'/readonly',root/'target',**options)
            self.assertFalse((root/'target/manifest.json').exists())
            self.assertTrue(list((root/'target').rglob('*.partial')))

    def test_target_mismatch_and_symlink_are_never_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);options,refs=fixture(root/'source')
            for label in ('bytes','symlink'):
                target=root/label;target.mkdir();leaf=target/refs[0]['name']
                if label=='bytes':leaf.write_bytes(b'original mismatched target')
                else:leaf.symlink_to(root/'source'/refs[0]['name'])
                before=leaf.read_bytes()
                with self.assertRaises(ValueError):copy_assets(LocalSource(root/'source'),'/readonly',target,**options)
                self.assertEqual(leaf.read_bytes(),before);self.assertEqual(leaf.is_symlink(),label=='symlink')

    def test_full_capacity_and_manifest_path_fail_before_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);options,refs=fixture(root/'source')
            with self.assertRaisesRegex(ValueError,'capacity'):
                copy_assets(LocalSource(root/'source'),'/readonly',root/'space',free_bytes=lambda _:0,**options)
            self.assertFalse((root/'space/manifest.json').exists())
            raw=json.loads((root/'source/manifest.json').read_text());raw['unique_anchors'][0]['name']='../escape.pt'
            encoded=json.dumps(raw).encode();(root/'source/manifest.json').write_bytes(encoded)
            options['expected_manifest_sha']=hashlib.sha256(encoded).hexdigest()
            with self.assertRaisesRegex(ValueError,'local artifact leaves'):
                copy_assets(LocalSource(root/'source'),'/readonly',root/'unsafe',**options)
            self.assertFalse((root/'escape.pt').exists())


if __name__=='__main__':unittest.main()
