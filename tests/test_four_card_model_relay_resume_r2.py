import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
import urllib.error
import urllib.request
from contextlib import redirect_stdout


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("relay_r2", ROOT / "scripts/relay_wc_four_card_frozen_models_resume_r2.py")
relay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(relay)
legacy_spec = importlib.util.spec_from_file_location("relay_r1", ROOT / "scripts/relay_wc_four_card_frozen_models_r1.py")
legacy = importlib.util.module_from_spec(legacy_spec)
legacy_spec.loader.exec_module(legacy)


class Response(io.BytesIO):
    def __init__(self, data, start, end, total, status=206, overrides=None):
        super().__init__(data)
        self.status = status
        self.headers = {"Content-Length": str(end-start+1),
                        "Content-Range": "bytes %d-%d/%d" % (start,end,total)}
        self.headers.update(overrides or {})


class Opener:
    def __init__(self, data, first_error=None):
        self.data, self.first_error, self.requests = data, first_error, []

    def open(self, req, timeout):
        self.requests.append(req)
        value = req.headers.get("Range")
        start, end = map(int, value[6:].split("-")) if value else (0,len(self.data)-1)
        if len(self.requests) == 1 and self.first_error:
            if isinstance(self.first_error, Exception):
                raise self.first_error
            return self.first_error(start,end,len(self.data))
        return Response(self.data[start:end+1],start,end,len(self.data),206 if value else 200)


class DownloadTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.partial = Path(self.tmp.name)/"registered.partial"
        self.data = b"abcdefghijkl"
        self.asset = dict(repo_id="nvidia/Cosmos-Reason1-7B",path="fixed.safetensors",
            source_revision="a"*40,size=len(self.data),git_blob=False,
            digest=hashlib.sha256(self.data).hexdigest())
        self.policy = dict(chunk_bytes=4,attempts_per_chunk=3,socket_timeout_seconds=90,
                           backoff_initial_seconds=2,backoff_cap_seconds=30)
        self.events, self.progress, self.sleeps = [], [], []

    def download(self, opener):
        relay.fixed_range_download(self.asset,self.partial,opener,"local-secret-placeholder",
            self.policy,lambda done,timing:self.progress.append(done),self.events.append,
            sleeper=self.sleeps.append)

    def test_valid_prefix_is_retained_and_only_suffix_requested(self):
        self.partial.write_bytes(self.data[:4])
        opener=Opener(self.data)
        self.download(opener)
        self.assertEqual([r.headers["Range"] for r in opener.requests],["bytes=4-7","bytes=8-11"])
        self.assertEqual(self.partial.read_bytes(),self.data)

    def test_short_read_rolls_back_before_retry(self):
        opener=Opener(self.data,lambda s,e,t:Response(self.data[s:s+2],s,e,t))
        self.download(opener)
        self.assertEqual(opener.requests[0].headers["Range"],opener.requests[1].headers["Range"])
        self.assertEqual(self.events[0]["code"],"SHORT_BOUNDED_RESPONSE")
        self.assertEqual(self.partial.read_bytes(),self.data)
        self.assertEqual(self.sleeps,[2])

    def test_wrong_content_range_is_rejected_without_appending(self):
        opener=Opener(self.data,lambda s,e,t:Response(self.data[s:e+1],s,e,t,
            overrides={"Content-Range":"bytes 0-3/99"}))
        self.download(opener)
        self.assertEqual(self.events[0]["code"],"CONTENT_RANGE_MISMATCH")
        self.assertEqual(self.partial.read_bytes(),self.data)

    def test_wrong_content_length_is_rejected(self):
        opener=Opener(self.data,lambda s,e,t:Response(self.data[s:e+1],s,e,t,
            overrides={"Content-Length":"9"}))
        self.download(opener)
        self.assertEqual(self.events[0]["code"],"CONTENT_LENGTH_MISMATCH")
        self.assertEqual(self.partial.read_bytes(),self.data)

    def test_http_error_is_classified_and_does_not_log_secret_url(self):
        error=urllib.error.HTTPError("https://example.test/?secret=do-not-log",503,
            "local-secret-placeholder",{},None)
        opener=Opener(self.data,error)
        self.download(opener)
        self.assertEqual(self.events[0]["http_status"],503)
        serialized=json.dumps(self.events)
        self.assertNotIn("secret",serialized)
        self.assertNotIn("https",serialized)
        self.assertNotEqual(opener.requests[0].full_url,opener.requests[1].full_url)

    def test_unauthorized_stops_without_exhausting_retries(self):
        error=urllib.error.HTTPError("https://example.test",401,"private",{},None)
        opener=Opener(self.data,error)
        with self.assertRaises(relay.TransferError):self.download(opener)
        self.assertEqual(len(opener.requests),1)
        self.assertEqual(self.partial.stat().st_size,0)

    def test_small_complete_file_uses_200_without_range(self):
        self.policy["chunk_bytes"]=len(self.data)+1
        opener=Opener(self.data)
        self.download(opener)
        self.assertNotIn("Range",opener.requests[0].headers)
        self.assertEqual(self.partial.read_bytes(),self.data)

    def test_bad_preserved_prefix_cannot_pass_whole_file_hash(self):
        self.partial.write_bytes(b"xxxx")
        with self.assertRaises(relay.TransferError) as caught:self.download(Opener(self.data))
        self.assertEqual(caught.exception.code,"COMPLETE_LOCAL_HASH_MISMATCH")
        self.assertTrue(self.partial.exists())

    def test_repeated_timeout_keeps_original_checkpoint(self):
        self.partial.write_bytes(self.data[:4])
        class TimeoutOpener:
            def open(self,req,timeout):raise TimeoutError("secret endpoint")
        with self.assertRaises(relay.TransferError):self.download(TimeoutOpener())
        self.assertEqual(self.partial.read_bytes(),self.data[:4])
        self.assertEqual([x["code"] for x in self.events],["SOCKET_TIMEOUT"]*3)
        self.assertEqual(self.sleeps,[2,4])

    def test_cross_host_redirect_does_not_forward_credential(self):
        req=urllib.request.Request("https://huggingface.co/fixed",headers={"Authorization":"Bearer private"})
        redirected=legacy.ScopedRedirect().redirect_request(req,None,302,"redirect",{},"https://cdn.example.test/fixed")
        self.assertFalse(redirected.has_header("Authorization"))

    def test_inventory_hashes_existing_blob_and_checks_alias(self):
        workspace=Path(self.tmp.name).resolve()/"workspace"
        repo=workspace/"cache/huggingface/hub/models--nvidia--Cosmos-Reason1-7B"
        blob=repo/"blobs"/self.asset["digest"]
        blob.parent.mkdir(parents=True)
        blob.write_bytes(self.data)
        target=repo/"snapshots"/("a"*40)/self.asset["path"]
        target.parent.mkdir(parents=True)
        target.symlink_to(blob)
        asset=dict(self.asset,target_revisions=["a"*40])
        output=io.StringIO()
        with redirect_stdout(output):exec(relay.INVENTORY,{"WORKSPACE":str(workspace),"ASSETS":[asset]})
        found=json.loads(output.getvalue())[0]
        self.assertTrue(found["complete_valid"])
        self.assertTrue(found["links_match"])
        self.assertFalse(found["partial_exists"])


if __name__ == "__main__":
    unittest.main()
