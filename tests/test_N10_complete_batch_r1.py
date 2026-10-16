"""Full160/six-dimension960 scheduling, failure and interruption controls.

Scorers and all video/metric observations in these tests are synthetic. No
codec, checkpoint, GPU, SSH, paper video or actual quality model is used.
"""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from test_automatic_quality_r1 import fixture
from wcomr.automatic_quality_r1 import DIMENSIONS, build_inputs, fingerprint
from wcomr.automatic_quality_batch_r1 import (
    JsonlSink, JournalWriteError, ResourceUnavailable, execute, key, read_journal, reconstruct,
)


def inputs(rejected=False):
    cases, methods, generation, evaluator, _, scores = fixture()
    for case in cases: case['static_eligible'] = False
    if rejected:
        generation[0].update(status='TEXT_REJECTED', endpoint_audit=None, video_artifact=None)
    bundle = build_inputs(cases, methods, generation, list(DIMENSIONS), evaluator)
    raw = {key(row): copy.deepcopy(row) for row in scores}
    for row in raw.values():
        if row['status'] == 'SCORED':
            row.update(unweighted_original_per_video_result=True,
                metric_source_sha256={'SYNTHETIC_DECLARED_SOURCE': 'e'*64},
                decoder_evidence={'SYNTHETIC_NOT_REAL_DECODER': True})
    return bundle, raw, [(methods[1], methods[0])]


class Scorers:
    def __init__(self, bundle, raw, *, effect=None, unavailable=None, close_error=None):
        self.bundle, self.raw, self.effect = bundle, raw, effect
        self.unavailable, self.close_error = unavailable, close_error
        self.entered, self.closed, self.seen = [], [], []
        self.active = 0

    @contextmanager
    def __call__(self, dimension):
        if self.active: raise AssertionError('Never load scoring models concurrently')
        self.active += 1; self.entered.append(dimension)
        def score(planned):
            self.seen.append(key(planned)); value = copy.deepcopy(self.raw[key(planned)])
            if self.effect: self.effect(planned,value)
            return value
        try:
            if dimension == self.unavailable: raise ResourceUnavailable('SYNTHETIC_MISSING_FIXED_RESOURCE')
            yield SimpleNamespace(dimension=dimension,scorer_fingerprint=self.bundle['scorer_fingerprint'],score=score)
        finally:
            self.active -= 1; self.closed.append(dimension)
            if dimension == self.close_error: raise RuntimeError('SYNTHETIC_CONTEXT_RELEASE_FAILURE')


class FullAutomaticQualityBatchControls(unittest.TestCase):
    def test_actual_full_matrix_order_and_readonly_jsonl_reconstruction(self):
        bundle, raw, contrasts = inputs(); scorers = Scorers(bundle,raw)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'original.jsonl'; sink=JsonlSink(path)
            try: result=execute(bundle,contrasts,scorers,sink,bootstrap_repetitions=8)
            finally: sink.close()
            events=[json.loads(line) for line in path.read_text().splitlines()]
            recovered=reconstruct(bundle,events)
            with self.assertRaises(FileExistsError): JsonlSink(path)
        self.assertEqual(result['metric_status_counts'],{'SCORED':800,'NOT_APPLICABLE_STATIC_SCOPE':160})
        self.assertEqual(len(result['rows']),960); self.assertTrue(result['all_ready_positions_scored'])
        self.assertEqual(scorers.entered,list(DIMENSIONS[:-1])); self.assertEqual(scorers.closed,scorers.entered)
        self.assertEqual(len(scorers.seen),800); self.assertEqual(scorers.active,0)
        self.assertEqual(recovered['final'],result); self.assertFalse(recovered['new_work_started'])
        self.assertIsNone(result['summary']['methods'][-1]['full_eligible_prompt_mean'])

    def test_original_rejection_and_one_metric_failure_retain_all_positions(self):
        bundle, raw, contrasts=inputs(rejected=True); target=('case1_seed43',bundle['methods'][1],'overall_consistency')
        def effect(planned,value):
            if key(planned)==target: raise ValueError('SYNTHETIC_BAD_CONTAINER')
        scorers=Scorers(bundle,raw,effect=effect); events=[]
        result=execute(bundle,contrasts,scorers,events.append,bootstrap_repetitions=8)
        self.assertEqual(result['metric_status_counts'],dict(SCORED=794,VIDEO_UNAVAILABLE=5,
            NOT_APPLICABLE_STATIC_SCOPE=160,METRIC_FAILED=1))
        self.assertFalse(result['all_ready_positions_scored']); self.assertEqual(len(result['rows']),960)
        self.assertEqual(len(scorers.seen),795); self.assertEqual(scorers.active,0)
        self.assertEqual(reconstruct(bundle,events)['final'],result)
        contrast=next(r for r in result['summary']['comparisons'] if r['dimension']=='overall_consistency')
        self.assertIn('prompt1',contrast['missing_eligible_prompt_ids'])

    def test_one_missing_model_is_not_replaced_or_called_and_later_roles_continue(self):
        bundle,raw,contrasts=inputs(); scorers=Scorers(bundle,raw,unavailable='dynamic_degree'); events=[]
        result=execute(bundle,contrasts,scorers,events.append,bootstrap_repetitions=3)
        self.assertEqual(result['metric_status_counts'],dict(SCORED=640,RESOURCE_UNAVAILABLE=160,NOT_APPLICABLE_STATIC_SCOPE=160))
        self.assertEqual(scorers.entered,list(DIMENSIONS[:-1])); self.assertEqual(scorers.active,0)
        self.assertFalse(any(r[2]=='dynamic_degree' for r in scorers.seen))
        self.assertTrue(any(r[2]=='MUSIQ_LONGER512' for r in scorers.seen))
        self.assertEqual(reconstruct(bundle,events)['final'],result)

    def test_wrong_identity_sampling_or_nonfinite_return_is_isolated(self):
        bundle,raw,contrasts=inputs(); case='case0_seed17'; method=bundle['methods'][0]
        def effect(planned,value):
            if planned['case_id']!=case or planned['method']!=method: return
            if planned['dimension']=='subject_consistency': value['video_sha256']='f'*64
            elif planned['dimension']=='motion_smoothness': value['observed_sampling']['frame_indices']=[0]
            elif planned['dimension']=='overall_consistency': planned['prompt']='MUTATED'
            elif planned['dimension']=='dynamic_degree': value['value']=.5
            elif planned['dimension']=='MUSIQ_LONGER512': value['frame_scores']=[float('nan')]*93
        events=[]; result=execute(bundle,contrasts,Scorers(bundle,raw,effect=effect),events.append,bootstrap_repetitions=2)
        self.assertEqual(result['metric_status_counts']['METRIC_FAILED'],5)
        self.assertEqual(result['metric_status_counts']['SCORED'],795)
        failed=[r for r in result['rows'] if r['status']=='METRIC_FAILED']
        self.assertTrue(all(r['value'] is None and r['error_type']=='ValueError' for r in failed))
        self.assertEqual(reconstruct(bundle,events)['final'],result)

    def test_keyboard_interrupt_preserves_complete_initial_matrix_and_releases_context(self):
        bundle,raw,contrasts=inputs(); count=[0]
        def effect(planned,value):
            count[0]+=1
            if count[0]==4: raise KeyboardInterrupt('SYNTHETIC_ORIGINAL_PROCESS_INTERRUPT')
        scorers=Scorers(bundle,raw,effect=effect); events=[]
        with self.assertRaises(KeyboardInterrupt): execute(bundle,contrasts,scorers,events.append,bootstrap_repetitions=2)
        partial=reconstruct(bundle,events)
        self.assertEqual(partial['status'],'ORIGINAL_INTERRUPTED_JOURNAL_REBUILT_NOT_RESUMED')
        self.assertEqual(partial['metric_status_counts'],dict(SCORED=3,NOT_REACHED=797,NOT_APPLICABLE_STATIC_SCOPE=160))
        self.assertEqual(scorers.active,0); self.assertEqual(scorers.entered,['subject_consistency'])
        self.assertFalse(partial['new_work_started']); self.assertIsNone(partial['final'])

    def test_durable_write_failure_stops_without_loading_another_model(self):
        bundle,raw,contrasts=inputs(); events=[]; scorer=Scorers(bundle,raw)
        def emit(event):
            if event['kind']=='ROW' and len([e for e in events if e['kind']=='ROW'])==2:
                raise OSError('SYNTHETIC_DISK_FAILURE')
            events.append(copy.deepcopy(event))
        with self.assertRaises(JournalWriteError): execute(bundle,contrasts,scorer,emit,bootstrap_repetitions=2)
        partial=reconstruct(bundle,events)
        self.assertEqual(partial['metric_status_counts']['SCORED'],2)
        self.assertEqual(partial['metric_status_counts']['NOT_REACHED'],798)
        self.assertEqual(scorer.active,0); self.assertEqual(scorer.entered,['subject_consistency'])

    def test_cleanup_failure_keeps_scores_and_stops_the_remaining_models(self):
        bundle,raw,contrasts=inputs(); events=[]; scorer=Scorers(bundle,raw,close_error='subject_consistency')
        with self.assertRaisesRegex(RuntimeError,'CONTEXT_RELEASE_FAILURE'):
            execute(bundle,contrasts,scorer,events.append,bootstrap_repetitions=2)
        partial=reconstruct(bundle,events)
        self.assertEqual(partial['metric_status_counts'],dict(SCORED=160,NOT_REACHED=640,NOT_APPLICABLE_STATIC_SCOPE=160))
        self.assertEqual(partial['lifecycle'][0]['status'],'CONTEXT_RELEASE_FAILURE')
        self.assertEqual(scorer.entered,['subject_consistency']); self.assertIsNone(partial['final'])

    def test_wrong_loaded_scorer_is_released_and_cannot_start_later_models(self):
        bundle,raw,contrasts=inputs(); events=[]; opened=[]; closed=[]
        @contextmanager
        def factory(dimension):
            opened.append(dimension)
            try: yield SimpleNamespace(dimension='FOREIGN',scorer_fingerprint=bundle['scorer_fingerprint'])
            finally: closed.append(dimension)
        with self.assertRaisesRegex(ValueError,'another dimension'):
            execute(bundle,contrasts,factory,events.append,bootstrap_repetitions=2)
        self.assertEqual(opened,['subject_consistency']); self.assertEqual(closed,opened)
        recovered=reconstruct(bundle,events)
        self.assertEqual(recovered['metric_status_counts']['NOT_REACHED'],800)
        self.assertEqual(recovered['lifecycle'][0]['status'],'SCORER_IDENTITY_FAILURE')

    def test_incomplete_resealed_scope_or_invalid_statistics_cannot_enter_models(self):
        original,raw,contrasts=inputs()
        for change in ('drop','duplicate','dimension','prompt','seed','static','bootstrap'):
            with self.subTest(change=change):
                bundle=copy.deepcopy(original); events=[]; scorers=Scorers(bundle,raw)
                if change=='drop': bundle['rows'].pop()
                elif change=='duplicate': bundle['rows'][0]=copy.deepcopy(bundle['rows'][1])
                elif change=='dimension': bundle['dimensions']=bundle['dimensions'][:-1]
                elif change=='prompt': bundle['rows'][0]['prompt']='SUBSTITUTED'
                elif change=='seed': bundle['cases'][0]['seed']=43
                elif change=='static': bundle['cases'][0]['static_eligible']=True
                bundle['fingerprint']=fingerprint({k:v for k,v in bundle.items() if k!='fingerprint'})
                with self.assertRaises(ValueError):
                    execute(bundle,contrasts,scorers,events.append,bootstrap_repetitions=0 if change=='bootstrap' else 2)
                self.assertFalse(events); self.assertFalse(scorers.entered)

    def test_independent_journal_rejects_duplicate_foreign_and_fabricated_final(self):
        bundle,raw,contrasts=inputs(); events=[]
        execute(bundle,contrasts,Scorers(bundle,raw),events.append,bootstrap_repetitions=2)
        for change in ('duplicate','foreign','summary','counts','missing_scope'):
            with self.subTest(change=change):
                changed=copy.deepcopy(events)
                if change=='duplicate': changed[2]['row']=copy.deepcopy(changed[1]['row'])
                elif change=='foreign': changed[1]['input_bundle_fingerprint']='0'*64
                elif change=='summary': changed[-1]['result']['summary']['methods'][0]['available_complete_prompt_mean']=99.
                elif change=='counts': changed[-1]['result']['metric_status_counts']['SCORED']=960
                else: changed=changed[1:]
                with self.assertRaises(ValueError): reconstruct(bundle,changed)

    def test_trailing_incomplete_write_is_retained_without_repair_or_resume(self):
        bundle,raw,contrasts=inputs(); events=[]
        execute(bundle,contrasts,Scorers(bundle,raw),events.append,bootstrap_repetitions=2)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'original_interrupted.jsonl'
            prefix=b''.join((json.dumps(event)+'\n').encode() for event in events[:3])
            original=prefix+b'{"kind":"ROW","row":'
            path.write_bytes(original); captured=read_journal(path)
            self.assertEqual(path.read_bytes(),original); self.assertIsNotNone(captured['incomplete_original_tail'])
            rebuilt=reconstruct(bundle,captured['events'])
            self.assertEqual(rebuilt['metric_status_counts']['SCORED'],2)
            self.assertEqual(rebuilt['metric_status_counts']['NOT_REACHED'],798)
            self.assertFalse(captured['original_file_modified']); self.assertFalse(rebuilt['new_work_started'])
            path.write_bytes(prefix+b'{INVALID COMPLETE LINE}\n')
            with self.assertRaisesRegex(ValueError,'corrupt'): read_journal(path)


if __name__=='__main__': unittest.main()
