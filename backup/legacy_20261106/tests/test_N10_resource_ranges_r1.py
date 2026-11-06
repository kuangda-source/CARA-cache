"""Small actual byte assembly and mocked curl responses; no public transfers."""
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('range_resource_only', ROOT/'scripts/fetch_wc_N10_viclip_ranges_r1.py')
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)
RAW = b'0123456789ABCDEFGHIJ'
URL = 'https://example.invalid/SYNTHETIC_ONLY'
ETAG = '"SYNTHETIC_OBJECT_ID_NOT_CHECKPOINT_SHA"'


def fixture(root):
    reg = dict(purpose='N10_PINNED_PUBLIC_RESOURCE_ONLY_NO_MODEL_OR_GPU',
        source_revision='SYNTHETIC_NO_REAL_RESOURCE', worker_sha256=M.sha(M.__file__),
        expected_weight=dict(url=URL, sha256=hashlib.sha256(RAW).hexdigest(), bytes=len(RAW), name='SYNTHETIC.pth'),
        chunk_bytes=8, attempts_per_range=6, expected_range_ETag=ETAG,
        curl_executable='/SYNTHETIC_CURL_NOT_EXECUTED')
    (root/'registration.json').write_text(json.dumps(reg))
    return reg


def fake_curl(fault=None):
    calls = []
    def run(command, **kwargs):
        assert command[0] == '/SYNTHETIC_CURL_NOT_EXECUTED'
        start, end = map(int, command[command.index('--range')+1].split('-'))
        data = RAW[start:end+1]; header_range = f'bytes {start}-{end}/{len(RAW)}'
        etag, status, exit_code = ETAG, 206, 0
        index = len(calls); calls.append((start, end))
        if fault:
            data, header_range, etag, status, exit_code = fault(index, data, header_range, etag, status, exit_code)
        body = Path(command[command.index('--output')+1]); body.write_bytes(data)
        header = Path(command[command.index('--dump-header')+1])
        header.write_text('HTTP/1.1 200 Connection established\r\n\r\n'
            'HTTP/2 302\r\nETag: "WRONG_REDIRECT_ID"\r\n\r\n'
            f'HTTP/2 {status}\r\nETag: {etag}\r\nContent-Range: {header_range}\r\n'
            f'Content-Length: {end-start+1}\r\n\r\n')
        return SimpleNamespace(returncode=exit_code, stdout=str(status)+'\n'+str(len(data))+'\n',
                               stderr='SYNTHETIC_PARTIAL_FILE' if exit_code else '')
    return run, calls


class RangeResourceControls(unittest.TestCase):
    def constants(self):
        return patch.multiple(M, URL=URL, SHA=hashlib.sha256(RAW).hexdigest(), SIZE=len(RAW), NAME='SYNTHETIC.pth', CHUNK=8)

    def execute(self, root, fault=None):
        run, calls = fake_curl(fault)
        with self.constants(), patch.object(M.subprocess, 'run', side_effect=run), patch.object(M.time, 'sleep'):
            result = M.download(root)
        return result, calls

    def test_complete_ordered_bytes_and_whole_digest_before_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); fixture(root); result, calls = self.execute(root)
            self.assertEqual(result, 0); self.assertEqual(calls, [(0,7),(8,15),(16,19)])
            self.assertEqual((root/'SYNTHETIC.pth').read_bytes(), RAW)
            self.assertFalse((root/'SYNTHETIC.pth.part').exists())
            final = json.loads((root/'resource-result.json').read_text())
            self.assertEqual(final['actual_sha256'], hashlib.sha256(RAW).hexdigest())
            self.assertEqual(final['completed_ranges'], 3); self.assertEqual(final['failed_HTTP_attempts'], 0)
            self.assertEqual(len(list((root/'ranges').glob('*.json'))), 3)

    def test_short_response_then_retry_does_not_duplicate_or_skip_prefix(self):
        def fault(i, data, r, e, s, code):
            return (data[:-1],r,e,s,18) if i == 0 else (data,r,e,s,code)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); fixture(root); result, calls = self.execute(root, fault)
            self.assertEqual(result, 0); self.assertEqual(calls[:2], [(0,7),(0,7)])
            self.assertEqual((root/'SYNTHETIC.pth').read_bytes(), RAW)
            self.assertEqual((root/'ranges/range_0_7_attempt1.bin').read_bytes(), RAW[:7])
            self.assertEqual(json.loads((root/'resource-result.json').read_text())['failed_HTTP_attempts'], 1)

    def test_wrong_offset_response_is_not_committed_even_when_length_matches(self):
        def fault(i, data, r, e, s, code):
            return (data,'bytes 8-15/20',e,s,code) if i == 0 else (data,r,e,s,code)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); fixture(root); result, calls = self.execute(root, fault)
            self.assertEqual(result, 0); self.assertEqual(calls[:2], [(0,7),(0,7)])
            self.assertEqual((root/'SYNTHETIC.pth').read_bytes(), RAW)
            self.assertFalse(json.loads((root/'ranges/range_0_7_attempt1.json').read_text())['accepted'])

    def test_wrong_object_etag_exhausts_known_requests_without_publication(self):
        def fault(i, data, r, e, s, code): return data,r,'"OTHER_OBJECT"',s,code
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); fixture(root); result, calls = self.execute(root, fault)
            self.assertEqual(result, 1); self.assertEqual(len(calls), 6)
            self.assertFalse((root/'SYNTHETIC.pth').exists()); self.assertEqual((root/'SYNTHETIC.pth.part').stat().st_size, 0)
            self.assertEqual(len(list((root/'ranges').glob('*.json'))), 6)

    def test_http200_range_ignored_is_not_accepted(self):
        def fault(i, data, r, e, s, code): return data,r,e,200,code
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); fixture(root); result, _ = self.execute(root, fault)
            self.assertEqual(result, 1); self.assertEqual((root/'SYNTHETIC.pth.part').stat().st_size, 0)
            self.assertFalse((root/'SYNTHETIC.pth').exists())

    def test_correct_http_headers_still_require_whole_checkpoint_sha(self):
        def fault(i, data, r, e, s, code):
            return (b'X'+data[1:],r,e,s,code) if i == 0 else (data,r,e,s,code)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); fixture(root); result, _ = self.execute(root, fault)
            self.assertEqual(result, 1); self.assertFalse((root/'SYNTHETIC.pth').exists())
            self.assertEqual((root/'SYNTHETIC.pth.part').stat().st_size, len(RAW))
            self.assertIn('Whole checkpoint', json.loads((root/'resource-result.json').read_text())['error'])

    def test_wrong_worker_source_refuses_before_any_curl_or_new_partial(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); reg = fixture(root); reg['worker_sha256']='0'*64
            (root/'registration.json').write_text(json.dumps(reg))
            with self.constants(), patch.object(M.subprocess,'run') as call:
                with self.assertRaises(AssertionError): M.download(root)
                call.assert_not_called()
            self.assertFalse((root/'SYNTHETIC.pth.part').exists())

    def test_original_stage_cannot_be_redispatched(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); fixture(root); self.execute(root)
            old = (root/'resource-result.json').read_bytes()
            with self.constants(), patch.object(M.subprocess,'run') as call:
                with self.assertRaises(AssertionError): M.download(root)
                call.assert_not_called()
            self.assertEqual(old, (root/'resource-result.json').read_bytes())

    def test_header_parser_uses_final_response_after_proxy_and_redirect(self):
        text = ('HTTP/1.1 200 Connection established\n\nHTTP/2 302\nETag: "OLD"\n\n'
                'HTTP/2 206\nETag: "NEW"\nContent-Range: bytes 8-15/20\n\n')
        result = M.last_response_headers(text)
        self.assertEqual(result['status'], 206); self.assertEqual(result['headers']['etag'], '"NEW"')
        self.assertEqual(result['headers']['content-range'], 'bytes 8-15/20')


if __name__ == '__main__': unittest.main()
