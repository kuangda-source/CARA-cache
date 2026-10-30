"""Real small CPU files from the original S store; no model/video claims."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_sq_s_data_terminal_r2 import fixture as data_fixture
from test_sq_s_storage_r1 import fixture as raw_fixture
from wcomr.gpu_budget_pool_v2 import sha,atomic_json
from wcomr.sq_s_storage_r1 import SCollectionStore
from wcomr.sq_s_artifact_terminal_r2 import check_artifacts

ROOT=Path(__file__).resolve().parents[1]


def fixture(output):
    collection,upper,*_=data_fixture();output.mkdir()
    sink=SCollectionStore(output/'streaming',prompts=upper['prompts'],maximum_total_bytes=28*2**30,
        maximum_file_bytes=2*2**30,minimum_free_bytes=512*2**20)
    for record in collection['matrix']['rows']:
        value=record['result'];path=output/'paths'/record['slot']['id']/'CPU_ONLY.mp4'
        path.parent.mkdir(parents=True);path.write_bytes(b'CPU fixture bytes, not a video')
        value['encoded_video']=dict(path=str(path),bytes=path.stat().st_size,sha256=sha(path))
        for row in value['S_rows']:
            _,raw=raw_fixture(row['prompt'],row['parent'],row['step'])
            if raw is not None:
                raw.update(context=row['context'],source=row['source'])
                for pair in raw['anchors']:
                    for anchor in pair:anchor['context']=row['context']
            sink(copy.deepcopy(row),raw)
            row['diagnostic_seconds_including_shadow_copy_hash_sink']=.01
    collection['matrix']['storage']=sink.finish();atomic_json(output/'S-collection.json',collection)
    return collection


def accept(collection,output):
    return check_artifacts(collection,output,collection_sha256=sha(output/'S-collection.json'),CPU_fixture=True)


class ArtifactTests(unittest.TestCase):
    def test_complete_real_store_bytes_include_all108_rows32_tensors_and_ten_fixture_videos(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'CPU_ONLY';collection=fixture(output);value=accept(collection,output)
            self.assertEqual((value['row_files'],value['raw_files'],value['anchor_files'],value['video_files']),(108,8,24,10))
            self.assertEqual(len(value['files']),151)
            self.assertTrue(value['original_file_bytes_accepted']);self.assertFalse(value['raw_tensor_replay_accepted'])
            self.assertFalse(value['scientific_S_effect_established'])

    def test_CPU_files_cannot_enter_real_artifact_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'CPU_ONLY';collection=fixture(output)
            with self.assertRaisesRegex(ValueError,'real/CPU'):
                check_artifacts(collection,output,collection_sha256=sha(output/'S-collection.json'))

    def test_changed_tensor_bytes_and_unregistered_partial_are_refused(self):
        for kind in ('tensor','partial','missing'):
            with self.subTest(kind=kind),tempfile.TemporaryDirectory() as directory:
                output=Path(directory)/'CPU_ONLY';collection=fixture(output)
                path=next((output/'streaming').glob('anchor-*.pt'))
                if kind=='tensor':path.write_bytes(b'changed raw bytes')
                elif kind=='missing':path.unlink()
                else:(output/'streaming'/'unexpected.partial').write_bytes(b'original failed attempt')
                with self.assertRaises((ValueError,OSError)):accept(collection,output)

    def test_scalar_drift_is_refused_even_if_all_changed_file_checksums_are_rebound(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'CPU_ONLY';collection=fixture(output);root=output/'streaming'
            manifest=json.loads((root/'manifest.json').read_text());entry=manifest['rows'][0]['artifact']
            path=root/entry['name'];row=json.loads(path.read_text());row['context']=['FOREIGN'];atomic_json(path,row)
            entry.update(bytes=path.stat().st_size,sha256=sha(path))
            refs=[entry['artifact'] for group in ('rows','raw_states','anchors') for entry in manifest[group]]
            manifest['payload_bytes_before_manifest']=sum(row['bytes'] for row in refs);atomic_json(root/'manifest.json',manifest)
            collection['matrix']['storage']['manifest'].update(bytes=(root/'manifest.json').stat().st_size,sha256=sha(root/'manifest.json'))
            collection['matrix']['storage']['actual_stored_bytes']=manifest['payload_bytes_before_manifest']+(root/'manifest.json').stat().st_size
            atomic_json(output/'S-collection.json',collection)
            with self.assertRaisesRegex(ValueError,'saved scalar row'):accept(collection,output)

    def test_all_native_terminal_modules_import_with_Torch_forbidden(self):
        code=("import sys;sys.path.insert(0,"+repr(str(ROOT/'src'))+");sys.modules['torch']=None;"
            "from wcomr import sq_s_capture_r2,sq_s_terminal_r2,sq_s_artifact_terminal_r2,sq_s_monitor_terminal_r2")
        subprocess.run([sys.executable,'-c',code],check=True,capture_output=True,text=True)

    def test_native_CLIs_parse_and_postprocess_refuses_visible_GPU_before_reading_data(self):
        for name in ('capture_cara_sq_s_r2.py','postprocess_cara_sq_s_r2.py'):
            subprocess.run([sys.executable,str(ROOT/'scripts'/name),'--help'],check=True,capture_output=True,text=True)
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);output=root/'must-not-exist.json'
            result=subprocess.run([sys.executable,str(ROOT/'scripts/postprocess_cara_sq_s_r2.py'),
                '--project',str(root),'--stage',str(ROOT),'--capture',str(root/'missing-capture.json'),
                '--settlement',str(root/'missing-settlement.json'),'--output',str(output)],
                env=dict(os.environ,CUDA_VISIBLE_DEVICES='FORBIDDEN_CPU_PROOF',NVIDIA_VISIBLE_DEVICES='void'),
                capture_output=True,text=True)
            self.assertNotEqual(result.returncode,0);self.assertIn('must hide all GPUs',result.stderr)
            self.assertFalse(output.exists())


if __name__=='__main__':unittest.main()
