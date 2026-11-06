"""Exact N07 receipt schema to all960 quality slots; every video is synthetic."""
import copy
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from wcomr.automatic_quality_inputs_r1 import PROTOCOL_ROLE, prepare
from wcomr.automatic_quality_r1 import VBENCH_COMMIT, vbench_metadata

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = 'manifests/wc_paper_N10_automatic_quality_measurement_prereg_r1_20261016.json'


def fixture(*, rejected=False):
    path = Path(__file__).with_name('test_frozen_shared_acceptance_r1.py')
    spec = importlib.util.spec_from_file_location('synthetic_N07_quality_bridge_fixture', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    value, launch = module.fixture()
    raw_protocol = (ROOT / PROTOCOL).read_bytes(); protocol = json.loads(raw_protocol)
    protocol_sha = hashlib.sha256(raw_protocol).hexdigest()
    value['config']['references'][PROTOCOL_ROLE] = dict(ref=PROTOCOL, sha256=protocol_sha)
    value['registration']['payload_sha256'][PROTOCOL] = protocol_sha
    value['payload_verified'][PROTOCOL] = True
    launch['started_unix'] = protocol['registered_unix'] + 1
    launch['next_check_not_before_unix'] = launch['started_unix'] + 1
    value['observed_unix'] = launch['started_unix'] + 2
    if rejected:
        original = next(r for r in value['runner']['runs'][40:] if r['method'] == 'A_NO_P')
        row = next(r for r in value['final']['rows'] if r['id'] == original['id'])
        removed = row.pop('video_artifact')['path']; row.pop('decoded_video'); row.pop('LPIPS')
        original.update(status='VIDEO_REJECTED', video_path=None)
        row.update(status='VIDEO_REJECTED', video_path=None,
            endpoint_audit='NOT_APPLICABLE_VIDEO_REJECTION_RETAINED',
            LPIPS_missing_reason='ORIGINAL_CANDIDATE_UNAVAILABLE_OR_AUDIT_FAILED')
        value['final']['artifact_inventory'] = [a for a in value['final']['artifact_inventory'] if a['path'] != removed]
        from wcomr.frozen_shared_post_r1 import summarize
        value['final'].update(summarize(value['final'], value['bound_inputs'], observed_paths=180,
                                        child_exit_code=0, bootstrap_repetitions=8))
    # This is the actual original independent acceptor on fully declared fake
    # receipts, not a fabricated "pass" boolean supplied to the bridge.
    from wcomr.frozen_shared_acceptance_r1 import accept
    accepted = accept(value, launch, bootstrap_repetitions=8)
    raw = gzip.compress(json.dumps(value).encode())
    digest = hashlib.sha256(raw).hexdigest(); accepted['capture_sha256'] = digest
    identity = dict(vbench_commit=VBENCH_COMMIT, synthetic_no_model_or_resources=True)
    return value, accepted, protocol, identity, dict(capture_sha256=digest, protocol_sha256=protocol_sha), raw, raw_protocol


class AcceptedCommonQualityInputControls(unittest.TestCase):
    def test_all160_original_formal_and_all960_dimension_positions_without_mutation(self):
        value, accepted, protocol, identity, identities, _, _ = fixture()
        before = copy.deepcopy((value, accepted, protocol, identity))
        result = prepare(value, accepted, protocol, identity, **identities)
        self.assertEqual((value, accepted, protocol, identity), before)
        bundle = result['input_bundle']
        self.assertEqual(bundle['registered_generation_positions'], 160)
        self.assertEqual(bundle['registered_metric_positions'], 960)
        self.assertEqual(result['input_status_counts'], dict(READY_TO_SCORE=800, NOT_APPLICABLE_STATIC_SCOPE=160))
        self.assertEqual(result['static_eligible_prompts'], 0)
        self.assertFalse(result['actual_metric_model_CPU_accepted'])
        self.assertEqual(result['real_quality_scores_generated'], 0)
        meta = vbench_metadata(bundle, 'overall_consistency')
        self.assertEqual(sum(len(r['video_list']) for r in meta), 160)
        self.assertEqual({m['prompt_en'] for m in meta}, {c['prompt'] for c in value['bound_inputs']['cases']})
        self.assertEqual(vbench_metadata(bundle, 'temporal_flickering'), [])

    def test_real_original_rejection_propagates_to_all_positions_without_becoming_success(self):
        value, accepted, protocol, identity, ids, _, _ = fixture(rejected=True)
        self.assertFalse(accepted['scientific_full_scope_accepted'])
        result = prepare(value, accepted, protocol, identity, **ids)
        self.assertEqual(result['original_generation_status_counts'], dict(COMPLETE=159, VIDEO_REJECTED=1))
        self.assertEqual(result['input_status_counts']['VIDEO_UNAVAILABLE'], 5)
        self.assertEqual(result['input_status_counts']['NOT_APPLICABLE_STATIC_SCOPE'], 160)
        missing = [r for r in result['input_bundle']['rows'] if r['original_generation_status'] == 'VIDEO_REJECTED']
        self.assertEqual(len(missing), 6); self.assertTrue(all(r['video_path'] is None for r in missing))

    def test_incomplete_unaccepted_or_transplanted_originals_are_refused(self):
        original = fixture()[:5]
        for kind in ('acceptance', 'source', 'capture', 'payload', 'short', 'bound'):
            value, accepted, protocol, identity, ids = copy.deepcopy(original)
            if kind == 'acceptance': accepted['scientific_available_cohorts_with_registered_missingness'] = False
            elif kind == 'source': accepted['source_revision'] = 'SYNTHETIC_OTHER'
            elif kind == 'capture': ids['capture_sha256'] = '0' * 64
            elif kind == 'payload': value['payload_verified'].pop(PROTOCOL)
            elif kind == 'short': value['final']['rows'].pop()
            else: value['bound_inputs']['cases'][0]['prompt'] = 'Filename-derived replacement'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                prepare(value, accepted, protocol, identity, **ids)

    def test_metric_protocol_must_already_be_in_original_stage_not_added_after_generation(self):
        original = fixture()[:5]
        for kind in ('reference', 'registration', 'hash', 'late', 'dropped_dimension', 'sampling', 'outputs_seen'):
            value, accepted, protocol, identity, ids = copy.deepcopy(original)
            if kind == 'reference': value['config']['references'].pop(PROTOCOL_ROLE)
            elif kind == 'registration': value['registration']['payload_sha256'].pop(PROTOCOL); value['payload_verified'].pop(PROTOCOL)
            elif kind == 'hash': ids['protocol_sha256'] = '0' * 64
            elif kind == 'late': protocol['registered_unix'] = value['launch']['started_unix'] + 1
            elif kind == 'dropped_dimension': protocol['dimensions'].pop()
            elif kind == 'sampling': protocol['dimension_sampling']['overall_consistency']['frame_indices'] = list(range(93))
            else: protocol['final_N07_generation_outputs_seen'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                prepare(value, accepted, protocol, identity, **ids)

    def test_original_cases_methods_and_source_schema_cannot_be_reassigned(self):
        original = fixture()[:5]
        for kind in ('row_method', 'row_section', 'static_label', 'seed', 'source_schema', 'argument'):
            value, accepted, protocol, identity, ids = copy.deepcopy(original)
            if kind == 'row_method': value['final']['rows'][0]['method'] = 'SYNTHETIC_OTHER'
            elif kind == 'row_section': value['final']['rows'][0]['section'] = 'TIMED'
            elif kind == 'static_label': value['bound_inputs']['cases'][0]['static_eligible'] = True
            elif kind == 'seed': value['bound_inputs']['cases'][0]['seed'] = 0
            elif kind == 'source_schema': value['bound_inputs']['source_bindings'][0]['original_fields'].append('static_eligible')
            else: value['bound_inputs']['argument_variants'][0]['arguments']['prompt'] = 'SYNTHETIC_CHANGED'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                prepare(value, accepted, protocol, identity, **ids)

    def test_actual_CLI_under_cold_stdlib_emits_all_six_metadata_files_and_no_scores(self):
        value, accepted, protocol, identity, ids, raw, protocol_raw = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            files = dict(capture=root/'capture.json.gz', acceptance=root/'acceptance.json', protocol=root/'protocol.json',
                evaluator_identity=root/'evaluator.json', metadata_root=root/'metadata', output=root/'inputs.json.gz')
            files['capture'].write_bytes(raw); files['acceptance'].write_text(json.dumps(accepted))
            files['protocol'].write_bytes(protocol_raw); files['evaluator_identity'].write_text(json.dumps(identity))
            command = [sys.executable, '-S', str(ROOT/'scripts/prepare_wc_paper_N10_accepted_common_inputs_r1.py')]
            for k, p in files.items(): command += ['--'+k.replace('_','-'),str(p)]
            child = subprocess.run(command, env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}, capture_output=True, timeout=15)
            self.assertEqual(child.returncode, 0, child.stderr.decode())
            result = json.loads(gzip.decompress(files['output'].read_bytes()))
            self.assertFalse(result['model_imported']); self.assertFalse(result['source_metric_worker_or_GPU_started'])
            self.assertEqual(len(result['metadata_files']), 6)
            self.assertEqual(result['input_bundle']['registered_metric_positions'], 960)
            self.assertEqual(json.loads((files['metadata_root']/'temporal_flickering.json').read_text()), [])
            for artifact in result['metadata_files']:
                self.assertEqual(hashlib.sha256(Path(artifact['ref']).read_bytes()).hexdigest(), artifact['sha256'])
            self.assertEqual(len(json.loads((files['metadata_root']/'MUSIQ_LONGER512.json').read_text())), 160)

    def test_resource_unavailable_and_zero_static_cohort_keep_empty_quality_values(self):
        value, accepted, protocol, identity, ids, _, _ = fixture()
        bundle = prepare(value, accepted, protocol, identity, **ids)['input_bundle']
        rows = []
        for planned in bundle['rows']:
            rows.append(dict(case_id=planned['case_id'], method=planned['method'], dimension=planned['dimension'],
                status='RESOURCE_UNAVAILABLE' if planned['input_status'] == 'READY_TO_SCORE' else planned['input_status'],
                value=None))
        from wcomr.automatic_quality_r1 import summarize
        result = summarize(bundle, rows, [('TABLE_PHASE_H1', 'RA_DEFAULT')], bootstrap_repetitions=8)
        self.assertEqual(result['registered_metric_positions'], 960)
        self.assertEqual(result['metric_status_counts'], dict(RESOURCE_UNAVAILABLE=800, NOT_APPLICABLE_STATIC_SCOPE=160))
        self.assertTrue(all(r['full_eligible_prompt_mean'] is None for r in result['methods']))
        self.assertTrue(all(r['available_cohort_mean_delta'] is None for r in result['comparisons']))
        static = next(r for r in result['comparisons'] if r['dimension'] == 'temporal_flickering')
        self.assertEqual(static['eligible_prompt_denominator'], 0)
        self.assertIsNone(static['available_cohort_prompt_bootstrap95'])

    def test_missing_stage_reference_can_be_recovered_from_original_Git_bytes_without_regeneration(self):
        from wcomr.automatic_quality_inputs_r1 import original_source_protocol
        value, accepted, protocol, identity, ids, _, raw = fixture()
        revision = subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        proof = original_source_protocol(ROOT, revision, raw)
        self.assertEqual(proof['sha256'], ids['protocol_sha256'])
        self.assertFalse(proof['source_files_written']); self.assertEqual(proof['GPU_submissions'], 0)
        # Explicitly synthetic GPU metadata; only the Git byte proof is real.
        value['config']['references'].pop(PROTOCOL_ROLE)
        value['registration']['payload_sha256'].pop(PROTOCOL); value['payload_verified'].pop(PROTOCOL)
        for container in (value['launch'], value['registration'], value['final'], accepted):
            container['source_revision'] = revision
        result = prepare(value, accepted, protocol, identity, source_proof=proof, **ids)
        self.assertEqual(result['measurement_protocol_identity_source'], 'ORIGINAL_SOURCE_GIT_BLOB_READONLY_RECOVERY')
        self.assertEqual(result['input_bundle']['registered_generation_positions'], 160)
        self.assertEqual(result['GPU_submissions'], 0)
        with self.assertRaises(ValueError): original_source_protocol(ROOT, revision, raw+b'CHANGED')
        with self.assertRaises(ValueError): original_source_protocol(ROOT,
            '15d77ac55de7f5715a76901c47e407663d41c9d3', raw)


if __name__ == '__main__': unittest.main()
