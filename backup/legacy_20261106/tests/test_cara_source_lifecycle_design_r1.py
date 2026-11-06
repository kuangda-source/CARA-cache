"""Real metadata audit, prospective source coverage and no-consumer control."""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

import torch

from wcomr.cara_fast_spec_r1 import profile_from
from wcomr.cara_read_write_state_r1 import read_write_corners
from wcomr.cara_source_lifecycle_design_r1 import calibration_design
from wcomr.cara_source_lifecycle_trace_r1 import consumers
from audit_cara_source_lifecycle_coverage_r1 import audit
from test_cara_read_write_provenance_r1 import bound, snapshots, ROOT

METRICS = {}
MANIFEST = ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json'
METADATA = ROOT/'reports/cara_v1_S108_original_metadata_read_r1_20261101.json'


class Design(unittest.TestCase):
    def test_complete_original108_metadata_audit_and_coverage_gap(self):
        result = audit(METADATA,MANIFEST)
        self.assertEqual(result['all_rows']['unique_t_a_b'],39)
        self.assertEqual(result['actual_C_shadow_D_rows']['unique_t_a_b'],17)
        self.assertEqual(result['actual_C_shadow_D_rows']['exact_stage_and_current_age_with_different_previous_gap'],[])
        self.assertFalse(result['old_labels_fitted'])
        METRICS['old_coverage'] = dict(rows=108,unique_source_triples=39,
            actual_C_shadow_D_rows=56,C_shadow_unique_source_triples=17,C_only_exact_age_gap_contrasts=0)

    def test_metadata_rehash_cannot_substitute_foreign_original_rows(self):
        value = json.loads(METADATA.read_text())
        item = value['result']['files'][0]
        row = json.loads(item['raw_utf8']);row['source']['source_anchor_steps']=[1,2]
        item['raw_utf8']=json.dumps(row);item['sha256']=hashlib.sha256(item['raw_utf8'].encode()).hexdigest()
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'foreign.json';path.write_text(json.dumps(value))
            with self.assertRaises(AssertionError):audit(path,MANIFEST)

    def test_generic_four_parents_cover19_22_and_new_C_source_gap_contrasts(self):
        card=json.loads(MANIFEST.read_text())
        result=calibration_design(card['schedule'],profile_from(card['profile']),card['FIT'])
        self.assertEqual([p['D'] for p in result['parents']],[19,19,22,22])
        self.assertTrue(all(len(p['states'])==8 for p in result['parents']))
        self.assertEqual(result['same_state_shadow_D_labels'],64)
        self.assertGreaterEqual(len(result['exact_stage_age_gap_contrasts']),1)
        self.assertFalse(result['F19_initialization'])
        self.assertFalse(result['measured_errors_used'])
        for p in result['parents']:
            self.assertTrue(all(s['t'] not in p['dense_steps'] for s in p['states']))
        METRICS['prospective_C_coverage'] = dict(parents=4,paths=8,shadow_D_labels_max=64,
            exact_stage_age_previous_gap_contrasts=result['exact_stage_age_gap_contrasts'],
            generic_mask_rules=True,error_values_used=False)

    def test_M1_original_complete_consumer_trace_is_reused(self):
        data=json.loads((ROOT/'reports/cara_read_write_final_collection_original_r1_20261101.json').read_text())
        traces=[]
        for row in data['rows']:
            if row['slot']['role'] in ('RW01','RW11'):
                trace=consumers(row['result']['semantic_history'],8)
                self.assertEqual(trace['C_consumers'],[list(range(9,16))+[17,18]]*2)
                self.assertEqual(trace['replaced_after_update'],[19,19])
                traces.append(trace)
        self.assertEqual(len(traces),4)
        METRICS['original_M1_source8'] = dict(C_consumers=list(range(9,16))+[17,18],
            replaced_after_update=19,original_accepted_rows=4,new_scoring=0)

    def test_no_future_C_consumer_write_swap_zero_on_original_tiny_transition(self):
        step,mask=bound();states=snapshots(step,mask)
        with torch.no_grad():
            c,d=step(states[34],'C'),step(states[34],'D')
            corners=read_write_corners(c,d)
            no_write=step(corners['00'],'D')
            write=step(corners['01'],'D')
        self.assertTrue(torch.equal(no_write.latent,write.latent))
        METRICS['no_future_consumer'] = dict(intervention_update=35,future_actions=['D'],
            identical_y_and_different_cache=True,full_remaining_endpoint_latent_bitwise_equal=True,
            actual_Cosmos_weights=False,real_video=False)


if __name__ == '__main__':
    torch.set_num_threads(2)
    unittest.main()
