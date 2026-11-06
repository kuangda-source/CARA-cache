"""Full-scope failure preservation and real Python-cycle cleanup; no model/GPU."""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wcomr import action_price12_execution_r1 as E

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    scope=json.loads((ROOT/'manifests/wc_paper_N09_action16_prices_scope_r2_20261016.json').read_text())
    row=scope['complete_parent_matrix'][0]
    sample=SimpleNamespace(name=row['scene'],seed=0,num_steps=35)
    inf=SimpleNamespace(rank0=True,text_guardrail_runner=object(),video_guardrail_runner=object())
    restore=lambda:dict(original_state_sha256='a'*64,restored_state_sha256='a'*64,shared_eval_verified=True)
    return scope,row,sample,inf,dict(scope=scope,parameters=dict(gamma=row['gamma']),
        checkpoint_reserves={},restore_request_state=restore,output=Path('NEVER_CREATED'))


class BatchExecutionControls(unittest.TestCase):
    def test_full12_denominator_with_actual_rejections_kept(self):
        scope,*_=fixture();samples={r['name']:object() for r in scope['requests']}
        called=[]
        def run(p,s):
            called.append(p['id']);return dict(status='TEXT_REJECTED' if len(called)==4 else 'COMPLETE')
        state=E.run_registered_batch(scope,samples,run)
        self.assertEqual(len(state['runs']),12);self.assertEqual(state['runs'][3]['status'],'TEXT_REJECTED')
        self.assertEqual(len(E.full_rows(state['runs'],scope)),12)
        self.assertFalse(state['new_prices_deployed'])

    def test_original_failure_prefix_and_all_unreached_positions_retained_no_retry(self):
        scope,*_=fixture();samples={r['name']:object() for r in scope['requests']};calls=[]
        def run(p,s):
            calls.append(p['id'])
            if len(calls)==2:raise E.RequestFailure(OSError('ORIGINAL_WRITER'),dict(diagnostic_points=[{'retained':True}],actual_pair_computations=9))
            return dict(status='COMPLETE')
        state=E.run_registered_batch(scope,samples,run);rows=E.full_rows(state['runs'],scope)
        self.assertEqual(len(calls),2);self.assertEqual(len(rows),12)
        self.assertEqual(rows[1]['error_type'],'OSError');self.assertEqual(rows[1]['actual_pair_computations'],9)
        self.assertTrue(rows[1]['diagnostic_points'][0]['retained'])
        self.assertTrue(all(r['status']=='NOT_REACHED' for r in rows[2:]))

    def test_callback_cannot_relabel_original_parent_position(self):
        scope,*_=fixture();samples={r['name']:object() for r in scope['requests']}
        state=E.run_registered_batch(scope,samples,lambda p,s:dict(status='COMPLETE',id='OTHER'))
        rows=E.full_rows(state['runs'],scope)
        self.assertEqual(rows[0]['id'],scope['complete_parent_matrix'][0]['id'])
        self.assertEqual(rows[0]['callback_identity_error'],dict(id='OTHER'))
        self.assertEqual(rows[0]['status'],'TECH_FAILED')

    def test_unguarded_parent_refused_before_restore_collection_or_algorithm(self):
        scope,row,sample,inf,kw=fixture();inf.video_guardrail_runner=None
        with patch.object(E,'collect_boundary') as gc,patch.object(E,'original_parent') as parent:
            with self.assertRaisesRegex(ValueError,'Ordinary guardrails'):E.execute_one(inf,sample,row,**kw)
        gc.assert_not_called();parent.assert_not_called()

    def test_real_unreachable_cycle_collected_and_reachable_leak_refused(self):
        scope,row,sample,inf,kw=fixture()
        class Owner:pass
        for retain in (False,True):
            held=[]
            def install(*a,**k):
                owner=Owner();owner.cycle=owner
                if retain:held.append(owner)
                return (None,owner,None,None)
            def parent(*a,**k):
                E.clean.install()
                return dict(status='TEXT_REJECTED',solver_steps=0,guided_pairs=0),None
            with self.subTest(retain=retain),patch.object(E.clean,'install',side_effect=install), \
                    patch.object(E,'original_parent',side_effect=parent):
                if retain:
                    with self.assertRaisesRegex(ValueError,'reachable'):E.execute_one(inf,sample,row,**kw)
                else:
                    result=E.execute_one(inf,sample,row,**kw)
                    self.assertEqual(result['request_memory_lifecycle']['observed_components'],1)
                    self.assertEqual(result['request_memory_lifecycle']['components_alive_after'],0)

    def test_failed_diagnostic_keeps_completed_points_and_original_error(self):
        scope,row,sample,inf,kw=fixture();row=scope['complete_parent_matrix'][1]
        @contextmanager
        def install(clean,scheduler,states,config,writer,parameters,holder):
            holder['owner']=SimpleNamespace(records=[dict(original_point=7)],actual_pair_computations=8)
            yield
        inf.pipe=SimpleNamespace(model=SimpleNamespace(sample_scheduler=object()))
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            kw['output']=Path(folder)/'original'
            with patch.object(E,'price16_install',install),patch.object(E.clean,'execute',side_effect=ValueError('ORIGINAL_P0')):
                with self.assertRaises(E.RequestFailure) as caught:E.execute_one(inf,sample,row,**kw)
        self.assertEqual(caught.exception.original_type,'ValueError')
        self.assertEqual(caught.exception.receipt['diagnostic_points'],[dict(original_point=7)])
        self.assertEqual(caught.exception.receipt['actual_pair_computations'],8)

    def test_guarded_pipeline_owns_directory_creation_before_first_state_artifact(self):
        scope,row,sample,inf,kw=fixture();row=scope['complete_parent_matrix'][1]
        @contextmanager
        def install(*a):yield
        inf.pipe=SimpleNamespace(model=SimpleNamespace(sample_scheduler=object()))
        def text_reject(*a,**k):
            self.assertFalse(Path(k['output']).exists())
            return dict(status='TEXT_REJECTED',solver_steps=0,guided_pairs=0)
        import tempfile
        with tempfile.TemporaryDirectory() as folder:
            kw['output']=Path(folder)/'must_not_be_precreated'
            with patch.object(E,'price16_install',install),patch.object(E.clean,'execute',side_effect=text_reject):
                value=E.execute_one(inf,sample,row,**kw)
            self.assertEqual(value['status'],'TEXT_REJECTED');self.assertFalse(kw['output'].exists())


if __name__=='__main__':unittest.main()
