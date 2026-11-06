"""Exercise resource commit/failure boundaries with tiny bytes and no network."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'scripts/fetch_wc_N10_viclip_resource_r1.py'
SPEC=importlib.util.spec_from_file_location('tiny_resource_fixture_only',SOURCE)
WORKER=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(WORKER)
DATA=b'SYNTHETIC_TINY_RESOURCE_NOT_MODEL'


class Response(io.BytesIO):
    status=200
    headers={}


class ResourceDownloadControls(unittest.TestCase):
    def run_worker(self,stage,data=DATA,*,expected_sha=None,expected_size=None):
        digest=expected_sha or hashlib.sha256(DATA).hexdigest()
        size=len(DATA) if expected_size is None else expected_size
        registration=dict(purpose='N10_PINNED_PUBLIC_RESOURCE_ONLY_NO_MODEL_OR_GPU',
            source_revision='SYNTHETIC_NOT_DEPLOYED',worker_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            expected_weight=dict(url='https://invalid.example/SYNTHETIC',sha256=digest,bytes=size,name='tiny.bin'))
        (stage/'registration.json').write_text(json.dumps(registration))
        with patch.multiple(WORKER,URL='https://invalid.example/SYNTHETIC',SHA=digest,SIZE=size,NAME='tiny.bin'), \
             patch.object(sys,'argv',[str(SOURCE),'--stage',str(stage)]), \
             patch.object(WORKER.urllib.request,'urlopen',return_value=Response(data)) as opened:
            with self.assertRaises(SystemExit) as stop:WORKER.main()
        return stop.exception.code,json.loads((stage/'resource-result.json').read_text()),opened

    def test_only_exact_registered_whole_bytes_are_committed(self):
        with tempfile.TemporaryDirectory() as directory:
            stage=Path(directory);code,result,opened=self.run_worker(stage)
            self.assertEqual(code,0);self.assertEqual((stage/'tiny.bin').read_bytes(),DATA)
            self.assertFalse((stage/'tiny.bin.part').exists())
            self.assertEqual(result['actual_sha256'],hashlib.sha256(DATA).hexdigest())
            self.assertEqual(result['source_revision'],'SYNTHETIC_NOT_DEPLOYED')
            self.assertEqual(opened.call_count,1)

    def test_wrong_checksum_or_incomplete_bytes_preserve_partial_without_success(self):
        for data,digest in ((DATA,'0'*64),(DATA[:-1],None)):
            with self.subTest(bytes=len(data)),tempfile.TemporaryDirectory() as directory:
                stage=Path(directory);code,result,_=self.run_worker(stage,data,expected_sha=digest)
                self.assertEqual(code,1);self.assertFalse((stage/'tiny.bin').exists())
                self.assertEqual((stage/'tiny.bin.part').read_bytes(),data)
                self.assertTrue(result['partial_file_preserved'])

    def test_oversized_response_cannot_be_committed(self):
        with tempfile.TemporaryDirectory() as directory:
            stage=Path(directory);code,result,_=self.run_worker(stage,DATA+b'EXTRA')
            self.assertEqual(code,1);self.assertFalse((stage/'tiny.bin').exists())
            self.assertEqual(result['error_type'],'ValueError')

    def test_original_result_or_payload_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            stage=Path(directory);self.run_worker(stage)
            original=(stage/'tiny.bin').read_bytes();receipt=(stage/'resource-result.json').read_bytes()
            with self.assertRaises(AssertionError):self.run_worker(stage)
            self.assertEqual((stage/'tiny.bin').read_bytes(),original)
            self.assertEqual((stage/'resource-result.json').read_bytes(),receipt)


if __name__=='__main__':unittest.main()
