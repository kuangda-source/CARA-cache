import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.policy_price_refresh_contract_r1 import COUNTS, matrix, quote_from_complete_assets
from wcomr.policy_interval_assets_r1 import cells, matrix as original_matrix, rounds_for


def fixture():
    runs = []
    for p in original_matrix():
        row = dict(p, status='COMPLETE', started_unix=0., ended_unix=300.)
        if p['mode'] == 'COLLECT':
            row['interval_cells'] = [dict(source=s, target=t, price_trials=[
                dict(action=a, round=r, seconds=.3) for r, actions in rounds_for(s,t) for a in actions])
                for s,t in cells()]
        runs.append(row)
    return dict(runner=dict(runs=runs), billing=dict(wall_seconds=24800.)), dict(
        full_protocol_accepted=True, formal_source_time_cells=1624, finance=dict(finance_accepted=True))


class PriceRefresh(unittest.TestCase):
    def test_all_cells_get_three_formal_repeats_and_native_is_explicitly_reused(self):
        cap, acc = fixture(); q = quote_from_complete_assets(cap, acc)
        self.assertEqual(len(matrix()), 10)
        self.assertEqual(COUNTS['total_readout_trials'], 2030 * 12)
        self.assertEqual(COUNTS['formal_cells'], 4 * len(cells()))
        self.assertEqual(q['extra_readout_trials'], 11340)
        self.assertEqual(q['terms_seconds']['original_GPU_wall_minus_only_reused_Native'], 23600.)
        self.assertEqual(q['original_tensor_IO_reduction_credited_seconds'], 0)
        self.assertFalse(q['GPU_dispatch_ready'])

    def test_partial_domain_and_unaccepted_finance_fail(self):
        cap, acc = fixture()
        bad = copy.deepcopy(cap); bad['runner']['runs'][-1]['interval_cells'].pop()
        with self.assertRaises(ValueError): quote_from_complete_assets(bad, acc)
        acc['finance']['finance_accepted'] = False
        with self.assertRaises(ValueError): quote_from_complete_assets(cap, acc)

    def test_high_cost_cannot_be_hidden_under_autonomy_limit(self):
        cap, acc = fixture(); cap['billing']['wall_seconds'] = 60000.
        q = quote_from_complete_assets(cap, acc)
        self.assertGreater(q['billed_limit_GPUh'], 12)
        self.assertTrue(q['specific_whole_card_approval_required'])


if __name__ == '__main__': unittest.main()
