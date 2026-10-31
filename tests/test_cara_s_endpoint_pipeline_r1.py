"""Local pipeline boundary controls; no model, metrics, GPU or central ledger."""
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from wcomr import cara_s_endpoint_pipeline_r1 as pipeline
from wcomr.cara_budget_search_journal_r1 import read_record


class Pipeline(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.out=Path(self.temp.name)
        self.adapter=SimpleNamespace(card=dict(scope_sha256='a'*64,physical_matrix=list(range(32)),endpoint_binding_sha256='b'*64),cpu_validation=True)
        self.context=dict(scope_sha256='a'*64,physical_paths=32,endpoint_binding_sha256='b'*64,CPU_fixture_only=True)

    def collect(self):
        return pipeline.collect(self.adapter,self.out,self.context,before_request=lambda slot:None,precision={})

    def test_all16_original_historical_routes(self):
        from check_cara_s_endpoint_pipeline_fixture_r1 import historical_slot
        from wcomr.cara_fast_binding_r2 import load_card
        base=load_card(Path(__file__).resolve().parents[1],'plans/cara_next_stage_20261028/mainline/r2/RUN_SPEC.json')
        slots=[historical_slot(base,member,role) for member in base['FIT']+base['CHECK']
               for role in ('NATIVE35','F19_C','UNIFORM19_C','F19_A1')]
        self.assertEqual(len({s['id'] for s in slots}),16)
        self.assertEqual(sum(s['section']=='A_ANCHOR' for s in slots),2)

    def test_wrong_scope_before_intent(self):
        self.context['scope_sha256']='c'*64
        with self.assertRaises(ValueError):self.collect()
        self.assertFalse((self.out/'endpoint-runner-intent.json').exists())

    def test_fixture_cannot_be_production(self):
        self.context['CPU_fixture_only']=False
        with self.assertRaises(ValueError):self.collect()

    def test_failure_persists_once_intent(self):
        with patch.object(pipeline,'execute',side_effect=RuntimeError('original failure')):
            with self.assertRaises(RuntimeError):self.collect()
        self.assertEqual(read_record(self.out/pipeline.RUNNER)['status'],'FAILED_NO_REPLAY')
        with patch.object(pipeline,'execute',side_effect=AssertionError('must not replay')):
            with self.assertRaises(FileExistsError):self.collect()

    def test_complete_collection_is_not_release(self):
        with patch.object(pipeline,'execute',return_value={'rows':[]}):self.collect()
        state=read_record(self.out/pipeline.RUNNER)
        self.assertEqual(state['status'],'COMPLETE_COLLECTION_NOT_RELEASED')
        self.assertFalse(state['scientific_accepted'])

    def test_no_artifact_read_before_release(self):
        with patch.object(pipeline,'released_lifecycle',side_effect=ValueError('still live')),patch.object(pipeline,'captured_file',side_effect=AssertionError('opened early')):
            with self.assertRaises(ValueError):pipeline.released_artifacts({},'',{})

    def test_failed_release_cannot_read_artifacts(self):
        with patch.object(pipeline,'released_lifecycle',return_value={'container_exit_success':False}),patch.object(pipeline,'record',side_effect=AssertionError('opened early')):
            with self.assertRaises(ValueError):pipeline.released_artifacts({},'',{})


if __name__=='__main__':unittest.main()
