import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import prepare_wc_four_card_nltk_resources_r1 as resources
import four_card_bank24_execution_tools_r1 as tools
from supervise_wc_four_card_bank24_gpu_r1 import container_command


class NltkResourceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.hub = self.root / 'cache/huggingface/hub/models--nvidia--Cosmos-Guardrail1'
        self.source = self.hub / 'snapshots/pinned/blocklist/nltk_data'
        leaf = self.source / 'tokenizers/punkt_tab/english/collocations.tab'
        leaf.parent.mkdir(parents=True)
        blob = self.hub / 'blobs/content'
        blob.parent.mkdir()
        blob.write_bytes(b'pinned tokenizer bytes\n')
        leaf.symlink_to(blob)
        self.manifest = self.root / 'manifest.json'
        self.manifest.write_text(json.dumps({'revision': 'pinned',
            'subdirectory': 'blocklist/nltk_data', 'files': {
                leaf.relative_to(self.source).as_posix(): {
                    'bytes': blob.stat().st_size, 'sha256': resources.sha(blob)}}}))
        digest = resources.sha(self.manifest)
        self.patches = [patch.object(resources, 'MANIFEST_SHA', digest),
                        patch.object(tools, 'NLTK_MANIFEST_SHA', digest)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        self.temp.cleanup()

    def test_materialization_preserves_bytes_and_source_and_reuses_exact_output(self):
        original = self.source / 'tokenizers/punkt_tab/english/collocations.tab'
        first = resources.materialize(self.root, self.manifest)
        self.assertTrue(original.is_symlink())
        self.assertEqual(first['files'], 1)
        self.assertEqual(tools.verify_nltk_resources(self.root)['files'], 1)
        again = resources.materialize(self.root, self.manifest)
        self.assertEqual(again['status'], 'EXISTING_EXACT_NLTK_MATERIALIZATION')

    def test_source_hash_mismatch_is_rejected_without_publication(self):
        (self.hub / 'blobs/content').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'bytes differ'):
            resources.materialize(self.root, self.manifest)
        self.assertFalse((self.root / resources.RESOURCE_REL).exists())

    def test_source_symlink_outside_model_is_rejected_even_with_matching_bytes(self):
        original = self.source / 'tokenizers/punkt_tab/english/collocations.tab'
        outside = self.root / 'outside'
        outside.write_bytes(original.read_bytes())
        original.unlink()
        original.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'escaped'):
            resources.materialize(self.root, self.manifest)

    def test_published_symlink_is_rejected_even_with_matching_bytes(self):
        resources.materialize(self.root, self.manifest)
        p = self.root / resources.RESOURCE_REL / 'tokenizers/punkt_tab/english/collocations.tab'
        p.unlink()
        p.symlink_to(self.hub / 'blobs/content')
        with self.assertRaisesRegex(ValueError, 'symbolic links'):
            tools.verify_nltk_resources(self.root)

    def test_actual_docker_entry_receives_materialized_directory(self):
        resources.materialize(self.root, self.manifest)
        env = tools.process_environment(self.root, self.root / 'caches', 'GPU-TEST')
        self.assertEqual(env['NLTK_DATA'], str(self.root / resources.RESOURCE_REL))
        (self.root / 'stage').mkdir()
        (self.root / 'stage/gpu-container-manifest.json').write_text('{}')
        cmd = container_command(self.root, self.root / 'stage', self.root / 'output',
                                {'container': 'unit', 'gpu_uuid': 'GPU-TEST'}, 'unit-image', env)
        self.assertIn('NLTK_DATA=' + env['NLTK_DATA'], cmd)
        self.assertIn('--network', cmd)
        self.assertIn('none', cmd)

    def test_missing_resources_fail_before_gpu_observation(self):
        stage = self.root / 'stage'
        stage.mkdir()
        with patch.object(tools, 'validate_authorization', return_value=({}, {}, {}, {})), \
             patch.object(tools, 'module', side_effect=AssertionError('GPU must not be observed')):
            with self.assertRaisesRegex(ValueError, 'Physical Guardrail'):
                tools._dispatch_locked(self.root, stage, {})

    def test_published_byte_change_is_rejected(self):
        resources.materialize(self.root, self.manifest)
        p = self.root / resources.RESOURCE_REL / 'tokenizers/punkt_tab/english/collocations.tab'
        p.chmod(0o644)
        p.write_bytes(b'wrong bytes')
        with self.assertRaisesRegex(ValueError, 'bytes differ'):
            tools.verify_nltk_resources(self.root)

    def test_missing_manifest_is_rejected(self):
        resources.materialize(self.root, self.manifest)
        (self.root / resources.RESOURCE_REL).with_suffix('.manifest.json').unlink()
        with self.assertRaisesRegex(ValueError, 'manifest required'):
            tools.verify_nltk_resources(self.root)


if __name__ == '__main__':
    unittest.main()
