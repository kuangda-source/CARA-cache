"""Whole-matrix metadata controls; fake requests do not run a model."""
import copy
import ast
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from wcomr.policy_generator_r1.interval_grammar import Profile
from wcomr.sq_s_batch_r1 import (COUNTS, Requests, VIDEO_HELPER_PATH, VIDEO_HELPER_SHA,
                               collect, digest, make_scope, rgb_signature, validate_scope)
from wcomr.sq_risk_r1 import TARGETS
from wcomr.sq_s_sources_r1 import PARENTS


def profile():
    return Profile(horizon=36, protected_dense=tuple(range(1,8))+(36,),
        max_source_age=28, min_C_anchors=2, min_A_anchors=1,
        alpha_candidates=(.5,1.), identity='CPU_BATCH_UNIT_ONLY')


class Store:
    def __init__(self):self.finished=False
    def finish(self):
        self.finished=True
        return dict(measured_rows=108, raw_states=8, unique_anchor_files=24, CPU_FIXTURE_ONLY=True)


class Adapter:
    def __init__(self, mutate=None):
        self.scope=make_scope(profile(), ('P0_CPU','P1_CPU'), cpu_fixture=True)
        self.calls=[];self.mutate=mutate

    def __call__(self, slot, output):
        self.calls.append(slot['id'])
        rows=[dict(prompt=slot['prompt'],parent=slot['parent'],step=t,
            parent_roundtrip_equal=True,teacher_writes_parent=False,
            source=dict(source_captured_before_parent_pair=True,current_D_in_source=False),
            extra_Dense_teacher_pairs=int(t not in PARENTS[slot['parent']]),
            extra_C_readout_pairs=int(t in PARENTS[slot['parent']]),
            extra_Dense_hidden_replay_heads=0) for t in TARGETS] if slot['enabled'] else []
        key=digest([slot['prompt'],slot['parent']])
        value=dict(status='COMPLETE',solver_steps=36,CPU_fixture=True,
            policy_fingerprint=self.scope['policies'][slot['parent']]['fingerprint'],
            guided=[dict(sha256=key) for _ in range(36)],final_latent=dict(sha256=key),
            RGB=dict(shape=[93,2,2,3],sha256=key),
            semantic_actions=self.scope['policies'][slot['parent']]['actions'],S_rows=rows)
        if self.mutate:self.mutate(slot,value)
        return value


class BatchTests(unittest.TestCase):
    def test_pixels_match_actual_pinned_writer_for_float_bfloat16_and_uint8(self):
        import numpy as np
        import torch
        from einops import rearrange
        from types import SimpleNamespace
        path=Path(__file__).resolve().parents[1]/'cache/runtime'/VIDEO_HELPER_PATH
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),VIDEO_HELPER_SHA)
        node=next(n for n in ast.parse(path.read_text()).body
                  if isinstance(n,ast.FunctionDef) and n.name=='save_img_or_video')
        node.returns=None
        for arg in node.args.args:arg.annotation=None
        captured=[]
        namespace=dict(torch=torch,np=np,rearrange=rearrange,
            easy_io=SimpleNamespace(dump=lambda value,*a,**kw:captured.append(value.copy())))
        exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),str(path),'exec'),namespace)
        values=torch.linspace(-.1,1.1,3*93*2*2).reshape(3,93,2,2)
        byte_values=torch.arange(values.numel()).remainder(256).to(torch.uint8).reshape(values.shape)
        for video in (values,values.bfloat16(),byte_values):
            namespace['save_img_or_video'](video,'DECLARED_NO_ENCODING')
            pixels=np.ascontiguousarray(captured.pop())
            self.assertEqual(rgb_signature(video),dict(shape=list(pixels.shape),dtype=str(pixels.dtype),
                sha256=hashlib.sha256(memoryview(pixels)).hexdigest()))

    def test_complete_json_roundtrip_and_both_observer_orders(self):
        adapter=Adapter();scope=json.loads(json.dumps(adapter.scope));validate_scope(scope)
        self.assertEqual(scope['counts'],COUNTS)
        self.assertEqual(COUNTS['total_pairs'],468)
        self.assertEqual(COUNTS['total_branch_readouts'],936)
        controls=[r['enabled'] for r in scope['slots'] if r['purpose']=='CONTROL']
        self.assertEqual(controls,[False,True,True,False,True,False,False,True])
        with tempfile.TemporaryDirectory() as directory:
            store=Store();snapshots=[]
            value=collect(adapter,Path(directory)/'whole',before_request=lambda s:None,
                storage=store,save=lambda v:snapshots.append(copy.deepcopy(v)))
            self.assertEqual(len(adapter.calls),10)
            self.assertEqual(len(value['OFF_ON_controls']),4)
            self.assertTrue(store.finished)
            self.assertFalse(value['scientific_labels_accepted'])

    def test_altered_complete_scope_and_denominator_rejected(self):
        for field in ('slots','counts'):
            scope=Adapter().scope
            if field=='slots':scope['slots'].pop()
            else:scope['counts']['paths']=9
            scope['scope_sha256']=digest({k:v for k,v in scope.items() if k!='scope_sha256'})
            with self.assertRaises(ValueError):validate_scope(scope)

    def test_RGB_mismatch_retains_failure_and_cannot_restart(self):
        def bad(slot,value):
            if slot['id']=='p1-F19-C-ON':value['RGB']['sha256']='changed'
        adapter=Adapter(bad);store=Store();snapshots=[]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError,'OFF-ON mismatch'):
                collect(adapter,Path(directory)/'failed',before_request=lambda s:None,
                    storage=store,save=lambda v:snapshots.append(copy.deepcopy(v)))
            self.assertEqual(snapshots[-1]['status'],'FAILED_RETAINED_NO_RETRY')
            self.assertFalse(store.finished)
            with self.assertRaisesRegex(ValueError,'already attempted'):
                collect(adapter,Path(directory)/'retry',before_request=lambda s:None,
                    storage=store,save=lambda v:None)
            self.assertFalse((Path(directory)/'retry').exists())

    def test_first_resource_failure_also_consumes_whole_attempt(self):
        adapter=Adapter();seen=[]
        def refuse(slot):raise OSError('declared resource refusal')
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(OSError):
                collect(adapter,Path(directory)/'first',before_request=refuse,
                    storage=Store(),save=lambda v:seen.append(copy.deepcopy(v)))
            self.assertEqual(adapter.calls,[])
            self.assertEqual(seen[-1]['status'],'FAILED_RETAINED_NO_RETRY')
            with self.assertRaises(ValueError):
                collect(adapter,Path(directory)/'second',before_request=lambda s:None,
                    storage=Store(),save=lambda v:None)

    def test_missing_rows_or_CPU_substitution_stop_before_finish(self):
        for kind in ('missing_rows','GPU_claim','short_guided'):
            def bad(slot,value):
                if kind=='missing_rows' and slot['enabled']:value['S_rows'].pop()
                if kind=='GPU_claim':value['CPU_fixture']=False
                if kind=='short_guided':value['guided'].pop()
            adapter=Adapter(bad);store=Store()
            with tempfile.TemporaryDirectory() as directory:
                with self.assertRaises(ValueError):
                    collect(adapter,Path(directory)/'bad',before_request=lambda s:None,
                        storage=store,save=lambda v:None)
                self.assertFalse(store.finished)

    def test_Q1_or_missing_authority_cannot_enter_real_S_requests(self):
        p=profile();scope=make_scope(p)
        for context in (None,dict(scope_sha256=scope['scope_sha256'],
                authorizes_S_collection=False,launch_id='CPU',gpu_uuid='CPU',source_revision='CPU')):
            with self.assertRaisesRegex(ValueError,'separately authorized'):
                Requests(scope=scope,inference=None,samples={},profile=p,common={},sink=lambda *a:None,
                    logical_copy_cap_bytes=1,cpu_validation=False,production_context=context)


if __name__=='__main__':unittest.main()
