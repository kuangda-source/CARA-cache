"""Whole-cost controls on the actual saved full368 scientific/billing receipt."""
import copy
import hashlib
import json
import math
from pathlib import Path
import unittest

from wcomr.action_price16_cost_r1 import source_costs,estimate,registered_plan,COUNTS

ROOT=Path(__file__).resolve().parents[1]
SCOPE='manifests/wc_paper_N09_action16_prices_scope_r2_20261016.json'
CAPTURE='reports/wc_source_phase16_live_or_terminal_capture_20261012.json'
ACCEPTED='reports/wc_source_phase16_complete_scalar_and_cell_analysis_20261012.json'


def fixture():
    data=json.loads((ROOT/CAPTURE).read_text());accepted=json.loads((ROOT/ACCEPTED).read_text())
    source=source_costs(data,accepted,capture_sha256=hashlib.sha256((ROOT/CAPTURE).read_bytes()).hexdigest())
    scope=json.loads((ROOT/SCOPE).read_text())
    return data,accepted,source,scope


def reseal(value):
    raw={k:v for k,v in value.items() if k!='fingerprint'}
    value['fingerprint']=hashlib.sha256(json.dumps(raw,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


class WholeActionCostControls(unittest.TestCase):
    def test_full12_944_includes_all512_probe_restore_and_research_work(self):
        data,accepted,source,scope=fixture();original=copy.deepcopy(scope)
        result=estimate(scope,source,frozen_historical_D_incremental_seconds=6.25420393414485)
        self.assertEqual(result['scope_counts'],COUNTS);self.assertEqual(len(result['planned_positions']),12)
        self.assertEqual(sum(r['additional_trial_pairs'] for r in result['planned_positions']),512)
        self.assertAlmostEqual(sum(result['components'].values()),result['subtotal_before_margin_seconds'])
        self.assertEqual(result['forecast_complete_GPUh'],math.ceil(sum(result['components'].values())*1.2)/3600)
        self.assertFalse(result['new_GPU_card_selected']);self.assertFalse(result['actual_new_action_prices_measured'])
        self.assertEqual(scope,original)

    def test_pair_difference_recomputed_from_every_successful_parent(self):
        data,accepted,source,scope=fixture()
        expected=[]
        for scene in source['source_scenes']:
            base,diag=[next(r for r in data['runner']['runs'] if r['scene']==scene and r['kind']==k)
                       for k in ('BASELINE','DIAGNOSTIC')]
            expected.append(((diag['ended_unix']-diag['started_unix'])-(base['ended_unix']-base['started_unix']))/20)
        self.assertEqual(source['maximum_inclusive_extra_pair_seconds'],max(expected))
        self.assertGreater(source['maximum_inclusive_extra_pair_seconds'],40.)
        self.assertTrue(source['diagnostic_difference_is_not_a_pure_action_price'])

    def test_missing_rejected_changed_scope_or_failed_parent_control_refused(self):
        data,accepted,source,scope=fixture()
        for name in ('missing','rejected','control','bill','source'):
            value=copy.deepcopy(data);proof=copy.deepcopy(accepted)
            if name=='missing':value['runner']['runs'].pop()
            elif name=='rejected':value['runner']['runs'][0]['status']='TEXT_REJECTED'
            elif name=='control':value['final']['parents'][0]['old_final_actions_and93RGB_equal']=False
            elif name=='bill':value['supervisor']['wall_seconds']=1.
            else:proof['raw_checked_receipt_sha256']='0'*64
            with self.subTest(name=name),self.assertRaises(ValueError):
                source_costs(value,proof,capture_sha256=accepted['raw_checked_receipt_sha256'])

    def test_resealed_smaller_matrix_trial_or_missing_round_is_not_the_complete_card(self):
        _,_,_,scope=fixture()
        for name in ('paths','trials','rounds','states'):
            value=copy.deepcopy(scope)
            if name=='paths':value['complete_parent_matrix'].pop()
            elif name=='trials':value['scope_counts']['trial_pairs']=128
            elif name=='rounds':value['action_rounds'].pop()
            else:value['states'].pop()
            reseal(value)
            with self.subTest(name=name),self.assertRaises(ValueError):registered_plan(value)

    def test_unknown_whole_load_or_other_scene_cannot_be_replaced_by_action_price(self):
        data,accepted,source,scope=fixture();data['runner']['load_seconds']=None
        with self.assertRaises(ValueError):source_costs(data,accepted,capture_sha256=accepted['raw_checked_receipt_sha256'])
        source['source_scenes'][0]='OTHER'
        with self.assertRaises(ValueError):estimate(scope,source,frozen_historical_D_incremental_seconds=.1)

    def test_large_full_cost_keeps_original_plan_and_marks_specific_approval(self):
        _,_,source,scope=fixture();source['maximum_inclusive_extra_pair_seconds']*=2
        result=estimate(scope,source,frozen_historical_D_incremental_seconds=6.25420393414485)
        self.assertGreaterEqual(result['forecast_complete_GPUh'],12.)
        self.assertTrue(result['specific_complete_card_approval_required'])
        self.assertEqual(result['scope_counts']['trial_pairs'],512)


if __name__=='__main__':unittest.main()
