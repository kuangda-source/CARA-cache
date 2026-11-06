"""Protected identities survive aliases, custom JSON names and bounded read errors."""
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from wcomr.frozen_input_exposure_r1 import Identities
from wcomr.cara_final_exposure_r1 import collect_protected_outputs, identity_locations


class FinalExposureTests(unittest.TestCase):
    def setUp(self):
        self.records = [dict(name=name, prompt_sha256=hashlib.sha256(text.encode()).hexdigest(),
            category='human', group_members=[name]) for name, text in (
                ('human_1', 'protected synthetic text'), ('human_10', 'development synthetic text'))]
        self.index = Identities(self.records)
        self.protected = {'human_1'}

    def test_custom_collection_embedded_payload_hash_and_no_outcome_export(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); (root/'outputs').mkdir()
            data = dict(source=json.dumps(dict(prompt_sha256=self.records[0]['prompt_sha256'],
                LPIPS=0.91234567, T_DD=83712.987)), member='human_10')
            raw = json.dumps(data).encode()
            (root/'outputs'/'B-collection.json').write_bytes(raw)
            out = collect_protected_outputs(root, self.index, self.protected)
            self.assertEqual(set(out['identity_hits']), self.protected)
            self.assertEqual(out['documents'][0]['sha256'], hashlib.sha256(raw).hexdigest())
            self.assertNotIn('0.91234567', json.dumps(out))
            self.assertNotIn('83712.987', json.dumps(out))
            self.assertEqual(out['read_errors'], [])

    def test_native_tensor_filename_and_gzip_are_scanned_without_decoding(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); out = root/'outputs'; out.mkdir()
            (out/'human_1.pt').write_bytes(b'not a tensor')
            (out/'custom.json.gz').write_bytes(gzip.compress(json.dumps(dict(name='human_1_seed17')).encode()))
            value = collect_protected_outputs(root, self.index, self.protected)
            self.assertEqual(len(value['identity_hits']['human_1']), 2)
            self.assertFalse(value['videos_or_tensors_decoded'])
            self.assertFalse(value['read_errors'])

    def test_full_catalog_and_metadata_preserve_existing_exemption_boundary(self):
        self.assertEqual(identity_locations(self.records, self.index, self.protected), [])
        self.assertEqual(identity_locations(dict(identity_hits={'human_1': []}), self.index, self.protected), [])
        self.assertEqual(identity_locations(dict(rows=[dict(name='human_10')]), self.index, self.protected), [])
        self.assertEqual(identity_locations(dict(rows=[dict(name='human_1')]), self.index, self.protected)[0]['name'], 'human_1')

    def test_missing_tree_malformed_and_size_limit_never_produce_clear_reads(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with self.assertRaises(ValueError):collect_protected_outputs(root, self.index, self.protected)
            (root/'outputs').mkdir()
            (root/'outputs'/'bad.json').write_text('{')
            (root/'outputs'/'large.json').write_text(' ' * 50)
            with patch('wcomr.cara_final_exposure_r1.MAX_JSON_BYTES', 40):
                value = collect_protected_outputs(root, self.index, self.protected)
            self.assertEqual(len(value['read_errors']), 2)
            self.assertTrue(any(row['size_limit'] for row in value['read_errors']))
            self.assertEqual(value['documents'], [])

    def test_internal_alias_is_walked_and_external_or_dangling_links_remain_errors(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); out = root/'outputs'; out.mkdir()
            (out/'run.json').write_text(json.dumps(dict(name='human_1')))
            (out/'alias.json').symlink_to(out/'run.json')
            value = collect_protected_outputs(root, self.index, self.protected)
            self.assertEqual(len(value['documents']), 1)
            self.assertEqual(len(value['in_scope_aliases']), 1)
            self.assertFalse(value['read_errors'])
            (root/'external.json').write_text('{}')
            (out/'external.json').symlink_to(root/'external.json')
            (out/'missing.json').symlink_to(out/'absent.json')
            self.assertEqual(len(collect_protected_outputs(root, self.index, self.protected)['read_errors']), 2)

    def test_accepted_hash_reuse_does_not_hide_later_identity_changes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); out = root/'outputs'; out.mkdir()
            path = out/'old.json'; path.write_text(json.dumps(dict(name='human_10')))
            known = {str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest()}
            value = collect_protected_outputs(root, self.index, self.protected, known)
            self.assertEqual(value['prior_clear_documents_reused'], 1)
            path.write_text(json.dumps(dict(name='human_1')))
            value = collect_protected_outputs(root, self.index, self.protected, known)
            self.assertEqual(value['prior_clear_documents_reused'], 0)
            self.assertIn('human_1', value['identity_hits'])


if __name__ == '__main__':
    unittest.main()
