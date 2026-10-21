import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
import urllib.error
import urllib.request

P = Path(__file__).resolve().parents[1]/'scripts/prepare_wc_four_card_modelscope_hybrid_r3.py'
spec = importlib.util.spec_from_file_location('hybrid', P)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class Response(io.BytesIO):
    def __init__(self, data, start, end, total, override=None):
        super().__init__(data)
        self.status = 206
        self.headers = {'Content-Length':str(end-start+1), 'Content-Range':'bytes %d-%d/%d'%(start,end,total)}
        self.headers.update(override or {})


class Opener:
    def __init__(self, data, first=None):
        self.data, self.first, self.requests = data, first, []
    def open(self, req, timeout):
        self.requests.append(req)
        s,e = map(int, req.headers['Range'][6:].split('-'))
        if len(self.requests) == 1 and self.first:
            if isinstance(self.first, Exception):
                raise self.first
            return self.first(s,e,len(self.data))
        return Response(self.data[s:e+1],s,e,len(self.data))


class Controls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.part = Path(self.temp.name)/'only-new-job.partial'
        self.data = b'abcdefghijkl'
        self.asset = dict(repo_id='nvidia/Cosmos-Reason1-7B',path='model-00001-of-00004.safetensors',size=12,source_revision='3210bec0495fdc7a8d3dbb8d58da5711eab4b423',git_blob=False,digest=hashlib.sha256(self.data).hexdigest(),target_revisions=['a'*40])
        self.policy = dict(chunk_bytes=4, attempts_per_chunk=3, socket_timeout_seconds=90, backoff_initial_seconds=2, backoff_cap_seconds=60, maximum_retry_after_seconds=300)
        self.events, self.sleeps = [], []
    def run_download(self, opener, **kw):
        return c.download(self.asset,self.part,opener,'modelscope',self.policy,lambda *a:None,self.events.append,sleeper=self.sleeps.append,**kw)
    def test_only_missing_suffix_and_same_full_digest(self):
        self.part.write_bytes(self.data[:4]); o=Opener(self.data);self.run_download(o)
        self.assertEqual([q.headers['Range'] for q in o.requests],['bytes=4-7','bytes=8-11'])
        self.assertEqual(self.part.read_bytes(),self.data)
        self.assertTrue(all('Authorization' not in q.headers for q in o.requests))
    def test_short_read_rollback_exact_chunk(self):
        o=Opener(self.data,lambda s,e,t:Response(self.data[s:s+1],s,e,t));self.run_download(o)
        self.assertEqual(o.requests[0].headers['Range'],o.requests[1].headers['Range'])
        self.assertEqual(self.events[0]['code'],'SHORT_OR_OVERSIZED_RESPONSE')
    def test_wrong_range_rollback(self):
        o=Opener(self.data,lambda s,e,t:Response(self.data[s:e+1],s,e,t,{'Content-Range':'bytes 0-3/99'}));self.run_download(o)
        self.assertEqual(self.events[0]['code'],'CONTENT_RANGE_MISMATCH')
    def test_wrong_length_rejected(self):
        o=Opener(self.data,lambda s,e,t:Response(self.data[s:e+1],s,e,t,{'Content-Length':'99'}));self.run_download(o)
        self.assertEqual(self.events[0]['code'],'CONTENT_LENGTH_MISMATCH')
    def test_429_retry_after_obeyed_and_error_scrubbed(self):
        err=urllib.error.HTTPError('https://example.invalid/SECRET_SIGNED_URL',429,'SECRET',{'Retry-After':'7'},None)
        self.run_download(Opener(self.data,err))
        self.assertEqual(self.sleeps,[7]);self.assertNotIn('SECRET',str(self.events))
    def test_excessive_retry_after_retains_prefix(self):
        self.part.write_bytes(self.data[:4])
        err=urllib.error.HTTPError('https://example.invalid',429,'',{'Retry-After':'999'},None)
        with self.assertRaises(c.TransferError):self.run_download(Opener(self.data,err))
        self.assertEqual(self.part.read_bytes(),self.data[:4])
    def test_complete_wrong_hash_never_published(self):
        self.asset['digest']='0'*64
        with self.assertRaisesRegex(c.TransferError,'COMPLETE_OBJECT_HASH_MISMATCH'):self.run_download(Opener(self.data))
        self.assertEqual(self.part.read_bytes(),self.data)
    def test_bad_existing_complete_is_rejected_and_retained(self):
        self.part.write_bytes(b'bad')
        with self.assertRaisesRegex(c.TransferError,'EXISTING_OBJECT_MISMATCH_RETAINED'):c.existing_valid(self.part,self.asset)
        self.assertEqual(self.part.read_bytes(),b'bad')
    def test_no_token_to_modelscope(self):
        with self.assertRaisesRegex(c.TransferError,'MIRROR_CREDENTIAL_OR_SCOPE_REJECTED'):c.request_for(self.asset,0,3,'modelscope','SECRET')
    def test_nonregistered_mirror_configs_refused(self):
        self.asset['path']='config.json'
        with self.assertRaisesRegex(c.TransferError,'MIRROR_ARTIFACT_SCOPE_REJECTED'):c.request_for(self.asset,0,3,'modelscope')
    def test_official_auth_removed_on_cross_domain_redirect(self):
        req,_=c.request_for(self.asset,0,3,'official_hf','SECRET')
        redirected=c.ScopedRedirect().redirect_request(req,None,302,'',{},'https://cdn.example.invalid/file')
        self.assertIsNone(redirected.get_header('Authorization'))
    def test_deadline_preserves_existing_prefix(self):
        self.part.write_bytes(self.data[:4])
        with self.assertRaisesRegex(c.TransferError,'WHOLE_RESOURCE_WALL_LIMIT'):self.run_download(Opener(self.data),deadline=1,clock=lambda:2)
        self.assertEqual(self.part.read_bytes(),self.data[:4])
    def test_symlink_partial_refused(self):
        original=self.part.with_suffix('.old');original.write_bytes(self.data[:4]);self.part.symlink_to(original)
        with self.assertRaisesRegex(c.TransferError,'PARTIAL_SYMLINK_REJECTED'):self.run_download(Opener(self.data))
        self.assertEqual(original.read_bytes(),self.data[:4])
    def test_original_alias_creation(self):
        repo=Path(self.temp.name)/'repo';blob=repo/'blobs'/self.asset['digest'];blob.parent.mkdir(parents=True);blob.write_bytes(self.data)
        c.link_original(blob,repo,self.asset)
        self.assertEqual((repo/'snapshots'/('a'*40)/self.asset['path']).resolve(),blob.resolve())


if __name__ == '__main__':unittest.main()
