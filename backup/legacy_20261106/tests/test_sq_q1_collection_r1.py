"""Full Q1 entry and refusal controls with explicit small-tensor CPU fixtures."""
import copy
import unittest

import torch

from test_sq_q1_readout_r1 import saved_fixture
from wcomr.innovation_gain_observer_r1 import restore_readout_inputs
from wcomr.sq_q1_collection_r1 import collect_saved_q1, STATE_KEYS, COUNTS
from wcomr.sq_q1_readout_r1 import select_shared_codecs
from wcomr.sq_readout_subgraph_r1 import dense_hidden_outputs


def fixture_cohort():
    values = {}
    for prompt, step in STATE_KEYS:
        kernel,payload,schema = saved_fixture(prompt,step,flow=True)
        inputs = restore_readout_inputs(payload,schema,'cpu')
        payload['teacher_hidden'] = [r['original']+.1 for r in inputs['current']]
        payload['teacher'] = dense_hidden_outputs(kernel,inputs,payload['teacher_hidden'])
        values[(prompt,step)] = payload
    return kernel, schema, values


class CollectionTests(unittest.TestCase):
    def run_cohort(self, mutate=None, records=None):
        kernel, schema, values = fixture_cohort()
        if mutate: mutate(values)
        events,loaded = [],[]
        def load(row):
            loaded.append((row['prompt'],row['step']))
            return copy.deepcopy(values[loaded[-1]])
        result = collect_saved_q1(kernel,records or [dict(prompt=p,step=s) for p,s in STATE_KEYS],
            load,schema,device='cpu',max_copy_bytes=128*2**20,save_health=events.append)
        self.assertTrue(all('states' not in e and 'selections' not in e for e in events))
        self.assertFalse(kernel.net.final_layer._forward_hooks)
        self.assertFalse(kernel.net.final_layer._forward_pre_hooks)
        return result, events, loaded

    def test_complete_fixed_cohort_and_all_extra_head_denominators(self):
        result,events,loaded = self.run_cohort()
        self.assertTrue(result['complete_Q1_cohort'])
        self.assertEqual(loaded,list(STATE_KEYS))
        self.assertEqual(sum(v['completed'] for v in result['head_calls'].values()),222)
        self.assertEqual(result['scope_counts'],COUNTS)
        self.assertEqual(len(result['states']),12)
        self.assertIsNone(result['selections'])
        selected_fixture = select_shared_codecs(result['states'])
        self.assertFalse(selected_fixture['partial_state_selection'])
        self.assertEqual(result['new_deep_pairs'],0)

    def test_original_preview_failure_stops_before_any_codec_or_selection(self):
        def mutate(values):values[STATE_KEYS[0]]['readouts']['WC_C']['outputs'][0].add_(.1)
        result,events,loaded = self.run_cohort(mutate)
        self.assertFalse(result['complete_Q1_cohort'])
        self.assertIsNone(result['selections'])
        self.assertEqual(result['head_calls']['formal']['started'],0)
        self.assertEqual(result['head_calls']['warm']['completed'],4)
        self.assertEqual(result['head_calls']['controls']['completed'],4)
        self.assertEqual(loaded,[STATE_KEYS[0]])

    def test_later_original_C_failure_preserves_denominator_without_partial_selection(self):
        def mutate(values):values[STATE_KEYS[2]]['readouts']['WC_C']['outputs'][0].add_(.1)
        result,events,loaded = self.run_cohort(mutate)
        self.assertEqual(result['completed_states'],2)
        self.assertEqual(result['failure']['kind'],'FORMAL_ORIGINAL_C')
        self.assertIsNone(result['selections'])
        self.assertFalse(result['complete_Q1_cohort'])
        self.assertEqual(result['head_calls']['formal']['completed'],34)
        self.assertEqual(loaded,list(STATE_KEYS[:3]))

    def test_incomplete_cohort_refused_before_loader_or_head(self):
        kernel,schema,_ = fixture_cohort()
        def forbidden(row): raise AssertionError('Loader must not run')
        with self.assertRaisesRegex(ValueError,'complete registered twelve-state'):
            collect_saved_q1(kernel,[dict(prompt=p,step=s) for p,s in STATE_KEYS[:-1]],
                forbidden,schema,device='cpu',max_copy_bytes=128*2**20,save_health=lambda row:None)


if __name__ == '__main__': unittest.main()
