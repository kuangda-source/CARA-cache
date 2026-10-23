"""Declared synthetic controls; no real model acceptance or quality claim."""
import copy,json,tempfile,unittest
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from wcomr.policy_generator_r1.p2_quality_entry import execute,audit,validate_sources_and_decoder,build_plan
from wcomr.policy_generator_r1.p2_combination import DIMENSIONS,digest
from wcomr.policy_generator_r1.p2_card_binding import deduplicate_requests,binding_blueprint
from wcomr.automatic_quality_r1 import sampling_spec


def plan_and_scores():
    identity=dict(metric_stage='/CPU_FIXTURE',constructor_sources={'metric.py':'a'*64})
    planned=[];scored=[]
    for dim in DIMENSIONS:
        sampling=sampling_spec(dim)
        p=dict(case_id='c',method='physical',roles=['CARA','FRONT_A'],dimension=dim,input_status='READY_TO_SCORE',
               video_sha256='b'*64,prompt_sha256='c'*64,scorer_fingerprint=digest(identity),expected_sampling=sampling)
        r=dict(case_id='c',method='physical',dimension=dim,status='SCORED',value=.5,video_sha256='b'*64,
               prompt_sha256='c'*64,scorer_fingerprint=digest(identity),observed_sampling=sampling,
               metric_source_sha256={'/CPU_FIXTURE/metric.py':'a'*64},unweighted_original_per_video_result=True)
        if dim=='MUSIQ_LONGER512':
            r.update(frame_scores=[.5]*93,pts=[[i,'1/16'] for i in range(93)],
                decoder_evidence=dict(backend='ORIGINAL_FFMPEG_READER',model_input_shapes=[[1,3,288,512]]*93))
        else:
            decord=dim in ('subject_consistency','overall_consistency')
            r['decoder_evidence']=dict(readers=[dict(backend='DECORD' if decord else 'OPENCV',source_frames=93,source_fps=16,released=True)],
              batches=[sampling['frame_indices']] if decord else [],
              selections=[] if decord else [sampling['frame_indices'],sampling['target_indices']] if dim=='motion_smoothness' else [sampling['frame_indices']],
              decoder_pixels_or_preprocessing_not_replaced=True,metric_decoder_not_assumed_byte_equal_to_N07_RGB_backend=True)
        if dim=='dynamic_degree':r['value']=False
        planned.append(p);scored.append(r)
    plan=dict(evaluator_identity=identity,rows=planned);plan['sha256']=digest(plan)
    return plan,scored


class Quality(unittest.TestCase):
    def setUp(self):self.plan,self.scores=plan_and_scores();self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
    def run_quality(self,scores=None,fail=None):
        chosen=scores or self.scores
        @contextmanager
        def factory(dim):
            if dim==fail:raise RuntimeError('DECLARED_MODEL_LOAD_FAILURE')
            yield SimpleNamespace(dimension=dim,scorer_fingerprint=digest(self.plan['evaluator_identity']),
                score=lambda p:copy.deepcopy(chosen[list(DIMENSIONS).index(dim)]))
        return execute(self.plan,factory,Path(self.temp.name)/'journal.jsonl')
    def test_five_physical_positions_keep_aliases(self):
        state=self.run_quality();self.assertEqual(audit(self.plan,state)['positions'],5)
        self.assertEqual(state['rows'][0]['planned']['roles'],['CARA','FRONT_A'])
    def test_model_failure_keeps_full_denominator(self):
        with self.assertRaises(RuntimeError):self.run_quality(fail='motion_smoothness')
        terminal=json.loads((Path(self.temp.name)/'journal.jsonl').read_text().splitlines()[-1])['state']
        self.assertEqual(len(terminal['rows']),5);self.assertEqual(terminal['rows'][-1]['status'],'NOT_REACHED')
    def test_bad_raw_score_saved_before_rejection(self):
        self.scores[0]['value']=True
        with self.assertRaises(ValueError):self.run_quality()
        events=[json.loads(s) for s in (Path(self.temp.name)/'journal.jsonl').read_text().splitlines()]
        self.assertTrue(any(e['kind']=='RAW_RESULT' for e in events))
    def test_no_overwrite_original_journal(self):
        self.run_quality()
        with self.assertRaises(FileExistsError):self.run_quality()
    def test_bad_source_rejected(self):
        r=copy.deepcopy(self.scores[0]);r['metric_source_sha256']={'/outside/metric.py':'a'*64}
        with self.assertRaises(ValueError):validate_sources_and_decoder(self.plan['evaluator_identity'],r)
    def test_bad_decoder_rejected(self):
        r=copy.deepcopy(self.scores[0]);r['decoder_evidence']['readers'][0]['source_frames']=92
        with self.assertRaises(ValueError):validate_sources_and_decoder(self.plan['evaluator_identity'],r)
    def test_musiq_all_frame_shapes(self):
        r=copy.deepcopy(self.scores[-1]);r['decoder_evidence']['model_input_shapes'].pop()
        with self.assertRaises(ValueError):validate_sources_and_decoder(self.plan['evaluator_identity'],r)
    def test_terminal_requires_all_models_released(self):
        s=self.run_quality();s['model_lifecycle'].pop()
        with self.assertRaises(ValueError):audit(self.plan,s)
    def test_alias_tampering_rejected(self):
        s=self.run_quality();s['rows'][0]['planned']['roles'].pop()
        with self.assertRaises(ValueError):audit(self.plan,s)
    def test_missing_score_rejected(self):
        s=self.run_quality();s['rows'].pop()
        with self.assertRaises(ValueError):audit(self.plan,s)


def request(identifier,role):
    return dict(id=identifier,roles=[role],method=role,member='m',seed=0,block='new_dev',reference_id=None,
        expected_updates=36,input_sha256='a'*64,repeat_id=0,query_id=None,
        execution_signature=dict(source_sha256='b'*64,policy_fingerprint='p',requested_steps=35,actual_updates=36,
            sampler_config_sha256='c'*64,diagnostic_mode='OFF'))


class Dedup(unittest.TestCase):
    def test_same_policy_aliases_only(self):
        d=deduplicate_requests([request('a','CARA'),request('b','FRONT_A')])
        self.assertEqual(d['physical_paths'],1);self.assertEqual(d['rows'][0]['roles'],['CARA','FRONT_A'])
        self.assertFalse(d['budget_determined'])
    def test_repeat_seed_query_input_policy_do_not_collapse(self):
        for field,value in [('repeat_id',1),('seed',1),('query_id',2),('input_sha256','d'*64),('block','timing')]:
            a=request('a','CARA');b=request('b','FRONT_A');b[field]=value
            self.assertEqual(deduplicate_requests([a,b])['physical_paths'],2)
        a=request('a','CARA');b=request('b','FRONT_A');b['execution_signature']['policy_fingerprint']='different'
        self.assertEqual(deduplicate_requests([a,b])['physical_paths'],2)
    def test_missing_repeat_identity_rejected(self):
        r=request('a','CARA');del r['repeat_id']
        with self.assertRaises(ValueError):deduplicate_requests([r])
    def test_duplicate_role_rejected(self):
        with self.assertRaises(ValueError):deduplicate_requests([request('a','CARA'),request('b','CARA')])
    def test_reference_rewrites_only_to_original_alias(self):
        rows=[request('a','NATIVE35'),request('b','OTHER_NATIVE'),request('c','CARA')]
        rows[2]['reference_id']='b';d=deduplicate_requests(rows)
        self.assertEqual(d['rows'][-1]['reference_id'],'a')
    def test_unknown_reference_rejected(self):
        a=request('a','CARA');a['reference_id']='missing'
        with self.assertRaises(ValueError):deduplicate_requests([a])
    def test_shadow_mode_distinct(self):
        a=request('a','CARA');b=request('b','FRONT_A');b['execution_signature']['diagnostic_mode']='SHADOW'
        self.assertEqual(deduplicate_requests([a,b])['physical_paths'],2)
    def test_actual_solver_mismatch(self):
        a=request('a','CARA');a['expected_updates']=26
        with self.assertRaises(ValueError):deduplicate_requests([a])


def small_manifest():
    from wcomr.policy_generator_r1.p2_combination import BLOCK_MAX
    rows=[]
    for block in BLOCK_MAX:
        r=request(block,'CARA');r.update(block=block,quality_dimensions=list(DIMENSIONS) if block=='new_dev' else [],lpips=False,shadow_D_pairs=0)
        rows.append(r)
    m=dict(rows=rows,block_counts={b:1 for b in BLOCK_MAX});m['sha256']=digest(m)
    return m


class OriginalBinding(unittest.TestCase):
    def test_blueprint_preserves_all_blocks_and_no_budget(self):
        m=small_manifest();p=dict(status='P2_ORIGINAL_P1_POLICY_AND_NATIVE_HISTORY_CPU_BOUND_NOT_DISPATCH',P1_selected_policy_frozen=True,roles={'CARA':{'fingerprint':'p'}})
        c=dict(production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True)
        b=binding_blueprint(m,P1_binding=p,combination_acceptance=c,quality_readiness={'four_card_real_model_CPU_accepted':False})
        self.assertEqual(b['deduplication']['physical_paths'],6);self.assertFalse(b['GPU_dispatch_ready']);self.assertIsNone(b['whole_quote'])
        for field in ('P1_selected_policy_frozen',):
            p[field]=False
            with self.assertRaises(ValueError):binding_blueprint(m,P1_binding=p,combination_acceptance=c,quality_readiness={})
    def test_policy_cannot_change_after_p1(self):
        p=dict(status='P2_ORIGINAL_P1_POLICY_AND_NATIVE_HISTORY_CPU_BOUND_NOT_DISPATCH',P1_selected_policy_frozen=True,roles={'CARA':{'fingerprint':'different'}})
        with self.assertRaises(ValueError):binding_blueprint(small_manifest(),P1_binding=p,combination_acceptance=dict(production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True),quality_readiness={})
    def test_plan_reads_real_serialized_request_and_rejects_changed_video(self):
        from wcomr.policy_generator_r1.production_evidence import artifact
        from wcomr.automatic_quality_r1 import text_sha
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);m=small_manifest();rows=[]
            for slot in m['rows']:
                result={}
                if slot['block']=='new_dev':
                    v=root/'synthetic.mp4';v.write_bytes(b'DECLARED_CPU_SYNTHETIC_BYTES_NOT_A_VIDEO')
                    result={'video_artifact':artifact(v,root)}
                    r=root/'request.json';r.write_text(json.dumps(dict(slot=slot,result=result)))
                    result['request_artifact']=artifact(r,root)
                rows.append(dict(slot=slot,status='COMPLETE',result=result))
            state=dict(manifest_sha256=m['sha256'],status='COMPLETE_ORIGINALS_REQUIRE_INDEPENDENT_AUDIT',rows=rows)
            members={'m':dict(prompt='Synthetic only',prompt_id='synthetic',prompt_sha256=text_sha('Synthetic only'))}
            p=build_plan(m,state,members,{},root);self.assertEqual(len(p['rows']),5)
            v.write_bytes(b'changed')
            with self.assertRaises(ValueError):build_plan(m,state,members,{},root)
if __name__=='__main__':unittest.main()
