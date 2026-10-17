"""Complete synthetic960 input preparation with no price/GPU/model shortcuts."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

from test_N10_production_entry_r1 import fixture
from wcomr.automatic_quality_preparation_r1 import build_unpriced
from wcomr.automatic_quality_r1 import fingerprint


def prepare(values):
    config, registration, inputs, CPU, CPU_registration, resources = values
    return build_unpriced(inputs, CPU, CPU_registration, resources, config['comparisons'],
        source_revision=registration['source_revision'], references=config['references'])


class CompleteUnpricedQualityPreparation(unittest.TestCase):
    def test_frozen_comparison_function_does_not_import_the_legacy_generation_stack(self):
        root=Path(__file__).resolve().parents[1]
        spec=importlib.util.spec_from_file_location('pure_N10_preparation',root/'scripts/prepare_wc_N10_unpriced_production_scope_r1.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        source=(root/'src/wcomr/frozen_shared_post_r1.py').read_text()
        source+='\nraise RuntimeError("LEGACY_MODULE_BODY_MUST_NOT_EXECUTE")\n'
        methods=json.loads((root/'manifests/wc_paper_N07_N08_method_freeze_r1_20261016.json').read_text())['method_ids']
        pairs=module.original_comparisons(source,methods)
        self.assertEqual(len(pairs),18)
        self.assertEqual({a for a,b in pairs},{'A_NO_P','TABLE_PHASE_H1'})
        with self.assertRaises(ValueError):module.original_comparisons('def another_function(): pass\n',methods)

    def test_all960_five_models_and_missing_price_remain_explicit(self):
        values=fixture();before=copy.deepcopy(values);result=prepare(values)
        self.assertEqual(values,before)
        self.assertEqual(result['unpriced_config_template']['scope_counts']['metric_positions'],960)
        self.assertEqual(result['original_input_status_counts'],{'READY_TO_SCORE':800,'NOT_APPLICABLE_STATIC_SCOPE':160})
        self.assertIsNone(result['unpriced_config_template']['forecast_GPUh'])
        self.assertIsNone(result['unpriced_config_template']['billed_limit_GPUh'])
        self.assertTrue(result['complete_production_validation_refused_for_missing_price'])
        self.assertFalse(result['actual_production_CPU_accepted'])
        self.assertEqual(result['real_quality_scores'],0)

    def test_source_selection_positions_do_not_become_model_or_price_observations(self):
        result=prepare(fixture());rows={r['dimension']:r for r in result['dimension_workload']}
        self.assertEqual(rows['subject_consistency']['planned_selected_source_positions'],160*93)
        self.assertEqual(rows['motion_smoothness']['planned_target_positions'],160*46)
        self.assertEqual(rows['overall_consistency']['planned_selected_source_positions'],160*8)
        self.assertEqual(rows['temporal_flickering']['original_model_entries'],0)
        self.assertTrue(all(r['actual_model_forward_calls'] is None and r['actual_GPU_seconds'] is None for r in rows.values()))

    def test_unavailable_original_positions_are_kept_in_all_dimensions(self):
        values=fixture();inputs=values[2];b=inputs['input_bundle'];first=b['rows'][0]
        for row in b['rows']:
            if row['case_id']==first['case_id'] and row['method']==first['method'] and row['dimension']!='temporal_flickering':
                row['input_status']='VIDEO_UNAVAILABLE';row['video_path']=row['video_sha256']=None
        b['fingerprint']=fingerprint({k:v for k,v in b.items() if k!='fingerprint'})
        result=prepare(values)
        self.assertEqual(result['original_input_status_counts']['VIDEO_UNAVAILABLE'],5)
        self.assertEqual(sum(result['original_input_status_counts'].values()),960)

    def test_missing_role_truncated_scope_and_duplicate_comparison_are_refused(self):
        for mode in ('role','scope','comparison'):
            with self.subTest(mode=mode):
                values=fixture()
                if mode=='role': values[3]['rows'].pop()
                elif mode=='scope':values[2]['input_bundle']['rows'].pop()
                else:values[0]['comparisons'].append(copy.deepcopy(values[0]['comparisons'][0]))
                with self.assertRaises(ValueError):prepare(values)


if __name__=='__main__':unittest.main()
