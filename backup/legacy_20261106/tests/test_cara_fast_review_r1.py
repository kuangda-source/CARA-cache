"""Packet identity, anonymity and materialization controls; no human ratings."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wcomr.cara_fast_b36_figures_r1 import verify_analysis
from wcomr.cara_fast_review_r1 import plan_review, asset_catalog, materialize, validate_response, AXES

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT/'scripts/templates/cara_fast_review_r1.html'


class ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analysis, cls.analysis_sha = verify_analysis(
            ROOT/'reports/cara_fast_B36_complete_analysis_r1_20261029.json', receipt_root=ROOT)
        cls.manifest = json.loads((ROOT/'reports/cara_fast_B36_original_score_manifest_r1_20261029.json').read_text())

    def plan(self):
        return plan_review(copy.deepcopy(self.analysis), copy.deepcopy(self.manifest), b'0'*32)

    def test_complete_roles_and_four_reference_self_controls(self):
        p = self.plan()
        self.assertEqual(len(p['cases']), 32)
        self.assertEqual(len(asset_catalog(p)), 32)
        self.assertEqual(sum(c['role']=='NATIVE35' for c in p['cases']), 4)
        self.assertEqual(len({c['scene'] for c in p['cases']}), 4)
        for scene in {c['scene'] for c in p['cases']}:
            rows = [c for c in p['cases'] if c['scene']==scene]
            self.assertEqual(len(rows), 8)
            self.assertEqual(len({c['role'] for c in rows}), 8)
            self.assertEqual(len({c['reference']['sha256'] for c in rows}), 1)

    def test_public_packet_has_no_role_score_or_source_path_leaks(self):
        p = self.plan()
        body = json.dumps(p['public'])
        for value in ['F19_C', 'F19_A1', 'UNIFORM19_C', 'WC_FAST', 'RA_FAST',
                      'SHARED25_C', 'NATIVE35', 'NATIVE_K', 'T_DD', 'Alex', '/data20t', 'score_id']:
            self.assertNotIn(value, body)
        self.assertEqual(p, self.plan())
        other = plan_review(self.analysis, self.manifest, b'1'*32)
        self.assertNotEqual(p['public']['package_id'], other['public']['package_id'])
        self.assertNotEqual([c['score_id'] for c in p['cases']], [c['score_id'] for c in other['cases']])

    def test_partial_changed_and_fixture_identity_refused(self):
        for kind in ('partial', 'identity', 'fixture', 'reference'):
            a, m = copy.deepcopy(self.analysis), copy.deepcopy(self.manifest)
            if kind=='partial': m['pairs'].pop()
            elif kind=='identity': m['launch_id']='another-run'
            elif kind=='fixture': a['CPU_fixture_only']=True
            else: m['pairs'][0]['reference']['member']='another-input'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                plan_review(a, m, b'0'*32)

    def test_missing_or_changed_original_never_creates_review_html(self):
        p = self.plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaisesRegex(ValueError, 'Missing or changed'):
                materialize(p, root, root/'public', TEMPLATE)
            self.assertFalse((root/'public').exists())
            d = asset_catalog(p)[0]
            (root/(d['sha256']+'.mp4')).write_bytes(b'changed')
            with self.assertRaises(ValueError):
                materialize(p, root, root/'public', TEMPLATE)
            self.assertFalse((root/'public/review.html').exists())

    def test_byte_fixture_copy_and_empty_human_evidence(self):
        # Only exercises file/UI assembly. These are not scientific video fixtures.
        p = self.plan()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);cache=root/'cache';cache.mkdir()
            replacements = {}
            for c in p['cases']:
                for side in ('candidate', 'reference'):
                    d=c[side];old=d['sha256']
                    raw=('CPU_UI_BYTE_FIXTURE:'+old).encode()
                    sha=hashlib.sha256(raw).hexdigest();(cache/(sha+'.mp4')).write_bytes(raw)
                    replacements[old]=(sha,len(raw))
            for c in p['cases']:
                for side in ('candidate', 'reference'):
                    d=c[side];d['sha256'],d['bytes']=replacements[d['sha256']]
            result=materialize(p,cache,root/'public',TEMPLATE)
            self.assertEqual(result['copied_media'],36)
            self.assertEqual(result['human_reviews'],0)
            self.assertFalse(result['independent_human_evidence'])
            self.assertEqual(result['GPU_submissions'],0)
            body=(root/'public/review.html').read_text()
            self.assertNotIn('__PACKET__',body)
            self.assertNotIn('F19_C',body)
            self.assertEqual(len(list((root/'public/media').glob('*.mp4'))),36)
            with self.assertRaisesRegex(ValueError,'Fresh'):
                materialize(p,cache,root/'public',TEMPLATE)

    def test_complete_response_is_not_independent_evidence(self):
        p = self.plan()['public']
        response=dict(package_id=p['package_id'],reviewer='CPU_TEST_NOT_A_HUMAN',
            responses=[dict(case_id=c['case_id'],full_watch_attested=True,
                            **{axis:'uncertain' for axis in AXES}) for c in p['cases']])
        result=validate_response(p,response)
        self.assertFalse(result['independent_human_evidence'])
        self.assertFalse(result['scientific_result_accepted'])
        for kind in ('partial','duplicate','watch','choice','package'):
            r=copy.deepcopy(response)
            if kind=='partial':r['responses'].pop()
            elif kind=='duplicate':r['responses'][0]=copy.deepcopy(r['responses'][1])
            elif kind=='watch':r['responses'][0]['full_watch_attested']=False
            elif kind=='choice':r['responses'][0]['content']='unregistered choice'
            else:r['package_id']='another packet'
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_response(p,r)

    def test_cli_keeps_coordinator_and_receipt_outside_public_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);public=root/'public'
            for key,receipt in [(public/'key.json',root/'receipt.json'),
                                (root/'key.json',public/'receipt.json')]:
                r=subprocess.run([sys.executable,str(ROOT/'scripts/build_cara_fast_b36_review_r1.py'),
                    '--analysis',str(ROOT/'reports/cara_fast_B36_complete_analysis_r1_20261029.json'),
                    '--coordinator',str(key),'--output',str(public),'--receipt',str(receipt),'--plan-only'],
                    text=True,capture_output=True)
                self.assertNotEqual(r.returncode,0)
                self.assertIn('outside the public review directory',r.stderr)
                self.assertFalse(public.exists())

    def test_cli_rebuilds_original_evidence_before_creating_any_packet(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);altered=copy.deepcopy(self.analysis)
            altered['prompt_equal_summaries']['ALL'][2]['metrics']['Alex']+=0.1
            path=root/'altered.json';path.write_text(json.dumps(altered))
            r=subprocess.run([sys.executable,str(ROOT/'scripts/build_cara_fast_b36_review_r1.py'),
                '--analysis',str(path),'--coordinator',str(root/'private-key.json'),
                '--output',str(root/'public'),'--receipt',str(root/'receipt.json'),
                '--receipt-root',str(ROOT),'--plan-only'],text=True,capture_output=True)
            self.assertNotEqual(r.returncode,0)
            self.assertIn('Analysis differs',r.stderr)
            self.assertFalse((root/'private-key.json').exists())
            self.assertFalse((root/'public').exists())


if __name__=='__main__':
    unittest.main()
