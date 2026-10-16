"""Full40 adapter/archival tests; inference/video/CUDA observations are synthetic.

The original complete102 numerical observer proof is reused, not repeated here.
Small real CPU tensors exercise only the new out-of-clock artifact boundary.
"""
from contextlib import contextmanager
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import torch

from test_balanced_repeat_execution_r1 import FakeArguments, response as original_response
from wcomr import runtime_profile40_execution_r1 as M

ROOT=Path(__file__).resolve().parents[1]


def fixture():
    scope=json.loads((ROOT/'manifests/wc_paper_N09_runtime_profile40_scope_r1_20261016.json').read_text())
    protocol=json.loads((ROOT/'manifests/wc_paper_N08_balanced_repeat40_protocol_r1_20261016.json').read_text())
    freeze=json.loads((ROOT/'manifests/wc_paper_N07_N08_method_freeze_r1_20261016.json').read_text())
    bound=M.bind(scope,protocol,freeze)
    return scope,protocol,freeze,bound,M.prepare_samples(bound,FakeArguments)


def response(planned,sample):
    mapped={**planned,'section':'WARMUP' if planned['audit_guided'] else 'TIMED'}
    return original_response(mapped,sample)


class RuntimeProfile40Controls(unittest.TestCase):
    def test_registered40_keeps_all_three_modes_and_original_five_workpoints(self):
        scope,protocol,freeze,bound,samples=fixture()
        self.assertEqual(bound['execution_plan'],scope['complete_matrix'])
        self.assertEqual(len(samples),10);self.assertEqual(len(bound['execution_plan']),40)
        self.assertEqual(sum(p['component_profile'] for p in bound['execution_plan']),20)
        self.assertEqual(sum(p['audit_guided'] for p in bound['execution_plan']),30)
        self.assertEqual(sum(p['actual_solver_updates'] for p in bound['execution_plan']),1440)
        self.assertEqual(bound['bindings'],freeze['repeat_timing_bindings'])
        self.assertEqual(bound['requests'],protocol['requests']);self.assertFalse(bound['clean_repeated_latency_claim'])

    def test_changed_role_mode_input_or_reduced_matrix_refused(self):
        for mode in ('method','input','matrix','profile','freeze'):
            with self.subTest(mode=mode):
                scope,protocol,freeze,_,_=fixture()
                if mode=='method':scope['method_bindings']['RA_CFG_CACHE']='RA_DOUBLE'
                elif mode=='input':scope['requests'][0]['seed']=17
                elif mode=='matrix':scope['complete_matrix'].pop()
                elif mode=='profile':scope['complete_matrix'][-1]['component_profile']=False
                else:freeze['repeat_timing_bindings']['GCR_EFFICIENT']='TABLE_PHASE_H1'
                with self.assertRaises(ValueError):M.bind(scope,protocol,freeze)

    def test_full40_fake_outcomes_retain_actual_section_and_no_clean_repeat_summary(self):
        _,_,_,bound,samples=fixture();before=copy.deepcopy(bound)
        result=M.run_registered_batch(bound,samples,response)
        self.assertEqual(len(result['runs']),40);self.assertEqual(bound,before)
        self.assertEqual(sum(p['section']=='PROFILE_CONTROL' for p in result['runs']),30)
        audits=[p for p in result['runs'] if p['mode']=='PROFILE_AUDIT']
        self.assertEqual(len(audits),10);self.assertTrue(all(p['in_timing_guided_copies']==36 for p in audits))
        lean=[p for p in result['runs'] if p['mode']=='PROFILE_LEAN']
        self.assertTrue(all(p['in_timing_guided_copies']==0 for p in lean))
        self.assertTrue(result['status'].endswith('CPU_AUDIT_PENDING'))

    def test_new_entry_delegates_all40_modes_and_preserves_original_execution(self):
        _,_,_,bound,samples=fixture();called=[];restored=[];profile_calls=[]
        def restore():
            restored.append(True)
            return dict(original_state_sha256='a'*64,restored_state_sha256='a'*64,shared_eval_verified=True)
        @contextmanager
        def observer(inference,**kwargs):
            profile_calls.append(kwargs)
            with M.RequestProfile(device='cpu') as p:
                with p.span('SYNTHETIC_REQUEST_COMPONENT'):yield p
        current=[]
        def execute(inference,sample,method,**kwargs):
            planned=current[-1];called.append((method,kwargs['audit']))
            return response(planned,sample)
        with patch.object(M,'execute',side_effect=execute),patch.object(M,'profile_execution',side_effect=observer):
            for planned in bound['execution_plan']:
                current.append(planned)
                result=M.execute_one(object(),samples[(planned['scene'],planned['slot'])],planned,bound,
                    restore_request_state=restore,inference_module=object(),device='cpu',settings={'probe_depth':2})
                memory=result['request_memory_observation']
                self.assertIsNone(memory['memory_after']['peak_allocated_bytes'])
                self.assertEqual(result['component_profile_summary'] is not None,planned['component_profile'])
                self.assertFalse(result['clean_repeated_latency_claim'])
        self.assertEqual(len(called),40);self.assertEqual(len(restored),40);self.assertEqual(len(profile_calls),20)
        self.assertEqual([a for m,a in called],[p['audit_guided'] for p in bound['execution_plan']])
        self.assertTrue(all(p['probe_depth']==2 and p['device']=='cpu' for p in profile_calls))

    def test_restore_failure_and_illegal_lean_copies_fail_before_or_after_original_call(self):
        _,_,_,bound,samples=fixture();planned=next(p for p in bound['execution_plan'] if p['mode']=='PROFILE_LEAN')
        sample=samples[(planned['scene'],planned['slot'])]
        with patch.object(M,'execute') as called:
            with self.assertRaises(ValueError):M.execute_one(object(),sample,planned,bound,
                restore_request_state=lambda:dict(original_state_sha256='a'*64,restored_state_sha256='b'*64,shared_eval_verified=True),
                inference_module=object(),device='cpu',settings={'probe_depth':2})
            called.assert_not_called()
        row={**planned,**response(planned,sample)};row['in_timing_guided_copies']=36
        with self.assertRaises(ValueError):M.audit_row(row,planned,bound)
        original=copy.deepcopy(row);row=original;row['in_timing_guided_copies']=0
        row['frozen_input_identity']['installed_contexts'][0][2]='frozen-input-seed17'
        with self.assertRaises(ValueError):M.audit_row(row,planned,bound)

    def test_rejection_continues_and_technical_failure_retains_complete40(self):
        _,_,_,bound,samples=fixture();reject=bound['execution_plan'][5]['id']
        def one(planned,sample):
            return dict(status='TEXT_REJECTED',solver_steps=0,guided_pairs=0) if planned['id']==reject else response(planned,sample)
        done=M.run_registered_batch(bound,samples,one)
        self.assertEqual(len(done['runs']),40);self.assertEqual(done['runs'][5]['status'],'TEXT_REJECTED')
        snapshots=[];count=[0]
        def bad(planned,sample):
            count[0]+=1
            if count[0]==9:raise RuntimeError('SYNTHETIC_PROFILE_FAILURE_NO_RETRY')
            return response(planned,sample)
        with self.assertRaisesRegex(RuntimeError,'SYNTHETIC_PROFILE'):
            M.run_registered_batch(bound,samples,bad,save=lambda r:snapshots.append(copy.deepcopy(r)))
        rows=M.full_rows(snapshots[-1]['runs'],bound)
        self.assertEqual(len(rows),40);self.assertEqual(count[0],9)
        self.assertEqual(sum(r['status']=='TECH_FAILED' for r in rows),1)
        self.assertEqual(sum(r['status']=='NOT_REACHED' for r in rows),31)

    def test_real_small_CPU_artifacts_retain_all36_only_in_registered_audit_modes(self):
        _,_,_,bound,_=fixture();shape=(1,2,3)
        for mode in M.MODES.values():
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as folder:
                planned=next(p for p in bound['execution_plan'] if p['mode']==mode)
                root=Path(folder).resolve();directory=root/planned['id'];directory.mkdir()
                video=directory/'SYNTHETIC_NOT_REAL_VIDEO.mp4';video.write_bytes(b'EXPLICIT_SYNTHETIC_VIDEO_NOT_DECODED')
                final=torch.ones(shape);guided=[final.clone() for _ in range(36)] if planned['audit_guided'] else None
                summary=None
                if planned['component_profile']:
                    with M.RequestProfile(device='cpu') as p:
                        with p.span('SYNTHETIC_COMPONENT'):pass
                    summary=p.summary
                result=dict(status='COMPLETE',final_latent=final,guided=guided,
                    component_profile_summary=summary,video_path=str(video))
                actual=M.archive_output(result,planned,directory,root,expected_shape=shape)
                self.assertEqual('guided_artifact' in actual,planned['audit_guided'])
                self.assertEqual('component_profile_artifact' in actual,planned['component_profile'])
                self.assertTrue(torch.equal(torch.load(actual['final_artifact']['path'],weights_only=True)['final_latent'],final))
                if guided is not None:
                    self.assertEqual(len(torch.load(actual['guided_artifact']['path'],weights_only=True)['guided']),36)
                self.assertNotIn('final_latent',actual);self.assertNotIn('guided',actual)
                with self.assertRaises(FileExistsError):M.archive_output(result,planned,directory,root,expected_shape=shape)

    def test_bad_tensor_wrong_profile_record_and_foreign_artifact_path_are_refused(self):
        _,_,_,bound,_=fixture();planned=next(p for p in bound['execution_plan'] if p['mode']=='PROFILE_LEAN')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder).resolve();final=torch.ones(1,2,3)
            value=dict(status='COMPLETE',final_latent=final,guided=None,component_profile_summary=None)
            with self.assertRaisesRegex(ValueError,'scalar record'):
                M.archive_output(value,planned,root/'one',root,expected_shape=(1,2,3))
            value['component_profile_summary']={'components':{}}
            value['final_latent']=torch.full((1,2,3),float('nan'))
            with self.assertRaises(ValueError):M.archive_output(value,planned,root/'two',root,expected_shape=(1,2,3))
            with self.assertRaises(ValueError):M.archive_output(value,planned,root.parent/'foreign',root,expected_shape=(1,2,3))


if __name__=='__main__':unittest.main()
