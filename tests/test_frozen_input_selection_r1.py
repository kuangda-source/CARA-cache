"""Synthetic identity-selection controls; no real final inputs are chosen."""
import copy
import unittest

from wcomr.frozen_input_selection_r1 import select


def fixture():
    categories = ['av', 'human', 'misc', 'robot']
    records = [dict(name=f'{c}_SYNTHETIC_{i}', category=c,
                    group_members=[f'{c}_SYNTHETIC_{i}'], prompt_sha256='synthetic')
               for c in categories for i in range(6)]
    group = ['av_SYNTHETIC_0', 'av_SYNTHETIC_1']
    for record in records[:2]:
        record['group_members'] = group[:]
    protocol = dict(categories_in_order=categories, prompts_per_category=2,
                    seeds_in_order=[17, 43], salt='SYNTHETIC_FIXED_SALT')
    development = dict(N05=dict(status='N05_CORE66_INDEPENDENTLY_ACCEPTED', full_denominator=66, formal_denominator=44),
        N06=dict(status='SIMPLE26D_FULL36_INDEPENDENT_TERMINAL_ACCEPTED', full_denominator=36, formal_denominator=24),
        latest_development_observed_unix=100)
    method_freeze = dict(method_ids=['NATIVE35', 'NATIVE26', 'NATIVE18', 'WC_DEFAULT', 'RA_DEFAULT',
        'A_NO_P', 'TABLE_PHASE_H1', 'FRONT_DENSE_C', 'FRONT_DENSE_A', 'UNIFORM_C'],
        parameters_frozen_from='DEVELOPMENT_ONLY', final_test_outputs_seen=False, freeze_unix=200)
    audit = dict(no_endpoint_or_timing_values_extracted=True, read_errors=[],
                 all_registered_GPU_jobs_terminal=True, observed_unix=300,
                 identity_hits=['av_SYNTHETIC_1', 'robot_SYNTHETIC_0'])
    return records, protocol, development, method_freeze, audit


class InputSelection(unittest.TestCase):
    def test_fixed_hash_ranking_complete_groups_and_both_seeds(self):
        records, protocol, development, methods, audit = fixture()
        original = copy.deepcopy(records)
        result = select(records, [], protocol, development=development, method_freeze=methods, remote_audit=audit)
        reordered = select(records[::-1], [], protocol, development=development, method_freeze=methods, remote_audit=audit)
        self.assertEqual(result, reordered)
        self.assertEqual(records, original)
        self.assertEqual(len(result['cases']), 16)
        self.assertTrue({'av_SYNTHETIC_0', 'av_SYNTHETIC_1'}.issubset(result['excluded_group_members']))
        for category in protocol['categories_in_order']:
            self.assertEqual(sum(r['category'] == category for r in result['selected_sources']), 2)
        for source in result['selected_sources']:
            self.assertEqual([r['seed'] for r in result['cases'] if r['prompt_id'] == source['name']], [17, 43])

    def test_reject_partial_development_or_stale_scientific_audit(self):
        for kind in ('partial_N05', 'partial_N06', 'old_audit', 'audit_metrics', 'live_GPU', 'test_tuning'):
            r, p, d, m, a = fixture()
            if kind == 'partial_N05': d['N05']['full_denominator'] = 65
            elif kind == 'partial_N06': d['N06']['status'] = 'PARTIAL'
            elif kind == 'old_audit': a['observed_unix'] = 199
            elif kind == 'audit_metrics': a['no_endpoint_or_timing_values_extracted'] = False
            elif kind == 'live_GPU': a['all_registered_GPU_jobs_terminal'] = False
            else: m['final_test_outputs_seen'] = True
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                select(r, [], p, development=d, method_freeze=m, remote_audit=a)

    def test_no_group_or_method_can_be_silently_dropped(self):
        r, p, d, m, a = fixture()
        bad = copy.deepcopy(r)
        bad[0]['group_members'] = [bad[0]['name']]
        with self.assertRaises(ValueError): select(bad, [], p, development=d, method_freeze=m, remote_audit=a)
        m['method_ids'].remove('FRONT_DENSE_C')
        with self.assertRaises(ValueError): select(r, [], p, development=d, method_freeze=m, remote_audit=a)
        r, p, d, m, a = fixture()
        m['method_ids'][-1] = 'P_ACR'
        with self.assertRaises(ValueError): select(r, [], p, development=d, method_freeze=m, remote_audit=a)
        r, p, d, m, a = fixture()
        excluded = [x['name'] for x in r if x['category'] == 'misc']
        with self.assertRaises(ValueError): select(r, excluded, p, development=d, method_freeze=m, remote_audit=a)


if __name__ == '__main__':
    unittest.main()
