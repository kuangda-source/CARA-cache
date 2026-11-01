"""New immutable-inventory reader on a fresh unit fixture; no real score/model work."""
import contextlib
import copy
import json
from pathlib import Path
import tempfile
import unittest

import test_cara_source_lifecycle_p1_collection_r1 as fixture
from wcomr.cara_fast_fidelity_r1 import file_sha
from wcomr.cara_budget_search_journal_r1 import read_record
from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_source_lifecycle_p1_inventory_r1 import read_inventory,semantic_slots


class P1InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=fixture.P1CollectionTests('runTest');cls.f.setUp()
        cls.collection,cls.runtime=cls.f.collection('new-reader-unit-fixture')
        execute=cls.runtime.execute
        def off_clock(slot,output):
            proof=execute(slot,output)
            if slot['timing']=='OFF':proof['T_DD']=None
            return proof
        cls.collection.execute=off_clock
        cls.result=cls.collection.run(allow_new=True)
        assert cls.result.get('failure') is None
        cls.root=cls.collection.root

    @classmethod
    def tearDownClass(cls):cls.f.doCleanups()

    def read(self):
        return read_inventory(self.root,self.f.card,self.f.context,[1.]*36,
            dict(path_seconds=10.,FIT_score_seconds=2.,overhead_seconds=.1),
            cpu_validation=True,maximum_elapsed_seconds=self.runtime.clock+1)

    @contextlib.contextmanager
    def changed(self,path,transform):
        original=path.read_bytes()
        value=json.loads(original)
        transform(value)
        path.write_text(json.dumps(value))
        try:yield
        finally:path.write_bytes(original)

    def test_full146_aliases_and_whole_original_cost_inventory_read_without_callbacks(self):
        before=(len(self.runtime.calls),len(self.runtime.scores))
        loaded=self.read()
        self.assertEqual(loaded['semantic_denominator'],146)
        self.assertEqual(len(loaded['physical']),len(self.runtime.calls))
        self.assertEqual(len(loaded['resolved']),146)
        self.assertEqual(before,(len(self.runtime.calls),len(self.runtime.scores)))
        self.assertEqual(loaded['original_generation_or_score_callbacks'],0)
        self.assertFalse(loaded['scientific_accepted'])
        self.assertEqual(sum(p['value']['proof']['T_DD'] is None for p in loaded['physical'].values()),4)

    def test_missing_or_replaced_semantic_position_cannot_shrink_denominator(self):
        summary=self.root/'algorithm-summary.json'
        with self.changed(summary,lambda s:s['semantic_positions'].pop()):
            with self.assertRaisesRegex(ValueError,'146'):self.read()

    def test_changed_physical_video_or_latent_is_refused(self):
        loaded=self.read()
        proof=next(iter(loaded['physical'].values()))['value']['proof']
        for artifact in (proof['video'],proof['final_latent']):
            path=Path(artifact['path']);raw=path.read_bytes();path.write_bytes(raw+b'changed')
            try:
                with self.subTest(path=path.name),self.assertRaisesRegex(ValueError,'bytes'):self.read()
            finally:path.write_bytes(raw)

    def test_torn_or_changed_operation_return_cannot_be_replayed(self):
        summary=self.root/'algorithm-summary.json'
        name=next(iter(self.result['operations']))
        path=self.root/'operations'/name/'return.json'
        with self.changed(path,lambda r:r.update(after_seconds=r['after_seconds']+.1)):
            with self.assertRaisesRegex(ValueError,'operation bytes'):self.read()
        extra=self.root/'operations'/'UNRECORDED'
        extra.mkdir()
        try:
            with self.assertRaisesRegex(ValueError,'unaccounted'):self.read()
        finally:extra.rmdir()

    def test_changing_clean_alias_to_another_physical_input_is_refused(self):
        summary=self.root/'algorithm-summary.json'
        original=read_record(summary)
        alias=next(p for p in original['semantic_positions'] if p['status']=='QUALITY_AND_CLEAN_SAMPLE_ALIAS')
        wrong=next(p['original_operation'] for p in original['semantic_positions']
                   if p['status']=='COMPLETE' and p['original_operation']!=alias['original_operation'])
        def replace(s):next(p for p in s['semantic_positions'] if p['id']==alias['id']).update(original_operation=wrong)
        with self.changed(summary,replace):
            with self.assertRaisesRegex(ValueError,'aliased'):self.read()

    def test_new_winner_or_old_rgb_mse_reselection_is_refused(self):
        summary=self.root/'algorithm-summary.json'
        def wrong_winner(s):
            selected=s['FIT_selected'];key=next(iter(selected))
            selected[key]=dict(selected[key],proxy_cost=selected[key]['proxy_cost']+1)
        with self.changed(summary,wrong_winner):
            with self.assertRaisesRegex(ValueError,'selection'):self.read()
        with self.changed(summary,lambda s:s.update(original_RGB_MSE_search_reselected=True)):
            with self.assertRaisesRegex(ValueError,'algorithm success'):self.read()

    def test_budget_stop_keeps146_positions_and_does_not_claim_hc_finished(self):
        runtime=fixture.SyntheticRequests(self.f.context,self.f.labels,scalar_seconds=14.)
        collection,_=self.f.collection('new-reader-budget-stop',runtime=runtime)
        execute=runtime.execute
        def off_clock(slot,output):
            proof=execute(slot,output)
            if slot['timing']=='OFF':proof['T_DD']=None
            return proof
        collection.execute=off_clock
        result=collection.run(allow_new=True)
        self.assertIsNone(result.get('failure'))
        loaded=read_inventory(collection.root,self.f.card,self.f.context,[1.]*36,
            dict(path_seconds=10.,FIT_score_seconds=2.,overhead_seconds=.1),
            cpu_validation=True,maximum_elapsed_seconds=runtime.clock+1)
        self.assertEqual(len(loaded['semantic_positions']),146)
        self.assertLess(len(loaded['resolved']),146)
        for search in result['fair_searches'].values():
            if not search['configured_search_finished']:
                self.assertLess(search['HC_iterations_completed'],1)


if __name__=='__main__':unittest.main()
