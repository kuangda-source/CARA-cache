"""Bounded local resource controls; not a production CPU acceptance."""
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error


ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
w=module('r4worker','scripts/finish_wc_four_card_resources_cpu_r4.py')
s=module('r3support','scripts/prepare_wc_four_card_modelscope_hybrid_r3.py')
l=module('r4life','scripts/wc_four_card_resource_cpu_r4.py')
POLICY=dict(chunk_bytes=4,attempts_per_chunk=2,socket_timeout_seconds=1,maximum_retry_after_seconds=300,backoff_initial_seconds=0,backoff_cap_seconds=0)


class Reply(io.BytesIO):
    status=206
    def __init__(self,body,headers):super().__init__(body);self.headers=headers


class OfflineResourceControls(unittest.TestCase):
    def fetch(self,path,opener):
        data=b'abcdef';asset=dict(url=w.ALEX_URL,bytes=6,sha256=hashlib.sha256(data).hexdigest())
        with patch.object(w,'ALEX_BYTES',6),patch.object(w,'ALEX_SHA',asset['sha256']):
            return w.fetch_alex(asset,path,opener,POLICY,s,lambda n:None,lambda e:None,deadline=100,clock=lambda:0,sleeper=lambda _:None)

    def test_full_registered_range_and_credential_free_request(self):
        requests=[]
        class Opener:
            def open(self,r,timeout):
                requests.append(r);start,end=map(int,r.headers['Range'][6:].split('-'))
                return Reply(b'abcdef'[start:end+1],{'Content-Range':'bytes %d-%d/6'%(start,end),'Content-Length':str(end-start+1)})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'partial';self.fetch(p,Opener());self.assertEqual(p.read_bytes(),b'abcdef')
        self.assertEqual([r.headers['Range'] for r in requests],['bytes=0-3','bytes=4-5'])
        self.assertTrue(all('Authorization' not in r.headers for r in requests))

    def test_short_response_preserves_original_prefix(self):
        class Opener:
            def open(self,r,timeout):return Reply(b'e',{'Content-Range':'bytes 4-5/6','Content-Length':'2'})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'partial';p.write_bytes(b'abcd')
            with self.assertRaises(s.TransferError):self.fetch(p,Opener())
            self.assertEqual(p.read_bytes(),b'abcd')

    def test_wrong_range_never_appends(self):
        class Opener:
            def open(self,r,timeout):return Reply(b'abcd',{'Content-Range':'bytes 0-3/99','Content-Length':'4'})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'partial'
            with self.assertRaises(s.TransferError):self.fetch(p,Opener())
            self.assertEqual(p.read_bytes(),b'')

    def test_complete_bad_digest_remains_unpublished(self):
        class Opener:
            def open(self,r,timeout):
                start,end=map(int,r.headers['Range'][6:].split('-'))
                return Reply(b'xxxxxx'[start:end+1],{'Content-Range':'bytes %d-%d/6'%(start,end),'Content-Length':str(end-start+1)})
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'partial'
            with self.assertRaises(AssertionError):self.fetch(p,Opener())
            self.assertEqual(p.read_bytes(),b'xxxxxx')

    def test_existing_bad_cache_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'alex.pth';p.write_bytes(b'bad')
            with self.assertRaises(ValueError):w.cache_valid(p)
            self.assertEqual(p.read_bytes(),b'bad')

    def test_unregistered_source_rejected(self):
        with self.assertRaises(ValueError):w.validate_alex(dict(url='https://example.org/alex.pth',bytes=w.ALEX_BYTES,sha256=w.ALEX_SHA))

    def test_retry_after_bounded_and_no_exception_secret(self):
        error=urllib.error.HTTPError('https://example.org/?private=secret',429,'limit',{'Retry-After':'7'},None)
        self.assertEqual(s.retry_delay(error,0,POLICY,0),7)
        self.assertEqual(s.error_info(error),dict(code='HTTP_ERROR',http_status=429))

    def test_unchanged_guarded_probe_and_offline_child_network_denial(self):
        source=w.guarded_source((ROOT/'scripts/repair_wc_four_card_environment_r2.py').read_text())
        self.assertIn('FROZEN_PRODUCTION_GUARDED_INFERENCE_IMPORT_CPU_ONLY_OK',source)
        compile(source,'guarded','exec');compile(w.LPIPS_PROBE,'lpips','exec')
        import socket
        with patch.object(socket.socket,'connect'),patch.object(socket.socket,'connect_ex'),patch.object(socket,'create_connection'):
            exec(w.NETWORK_GUARD,{})
            with self.assertRaisesRegex(RuntimeError,'OFFLINE_CPU'):socket.create_connection(('127.0.0.1',1))

    def test_remote_setup_and_capture_compile_without_execution(self):
        compile(l.SETUP,'setup','exec');compile('L={}\nMODE="terminal"\n'+l.CAPTURE,'capture','exec')


if __name__=='__main__':unittest.main()
