"""Declared synthetic full518 composition. No real policy, timing or quality."""
import copy,unittest
from wcomr.policy_generator_r1.p2_combination import *
from wcomr.automatic_quality_r1 import sampling_spec


def fixture():
    rows=[]
    for block,count in BLOCK_MAX.items():
        for i in range(count):
            rows.append(dict(id=f'{block}_{i}',block=block,member='CPU_SYNTHETIC_MEMBER',seed=0,roles=[f'CPU_ROLE_{i}'],expected_updates=27 if block=='timing' else 36,
                reference_id='timing_0' if block in ('simple_cal','fixed_cal','new_dev') else None,
                lpips=(block=='simple_cal' and i<40) or (block=='fixed_cal' and i<18) or (block=='new_dev' and i<288),
                quality_dimensions=list(DIMENSIONS) if block=='new_dev' else [],shadow_D_pairs=6 if block=='history' else 0))
    manifest=dict(CPU_FIXTURE_ONLY=True,block_counts=BLOCK_MAX,rows=rows);manifest['sha256']=digest(manifest)
    requests={};scores={};saved=[];metric={'CPU_FIXTURE_ONLY':True}
    def ref(name):return dict(path='/CPU_FIXTURE/'+name,bytes=1,sha256=digest(name))
    def execute(slot):
        result=dict(status='COMPLETE',solver_steps=slot['expected_updates'],guided_pairs=slot['expected_updates'],timing_boundary=TIME_BOUNDARY,
            full_request_seconds=None if slot['block']=='history' else 1.,video_artifact=ref(slot['id']+'/video'),final_latent_artifact=ref(slot['id']+'/latent'))
        if slot['block']=='history':result.update(clean_deployment_timing=False,shadow_D_pairs=6,history_originals_audited=True,P1_OFF_reference_parity=True)
        requests[slot['id']]=dict(slot=copy.deepcopy(slot),result=copy.deepcopy(result));result['request_artifact']=ref(slot['id']+'/request');return result
    def score(slot,result,reference):
        if not slot['lpips']:return {}
        values=[.05]*93
        scores[slot['id']]=dict(reference_sha256=reference['video_artifact']['sha256'],candidate_sha256=result['video_artifact']['sha256'],
            frame_distances=values,pts=[[i,'1/16'] for i in range(93)],frames=93,mean_LPIPS=sum(values)/93,metric_identity=metric,
            geometry=[432,768,3],resize_crop_subsample=False,device='cpu')
        return dict(LPIPS=sum(values)/93,score_artifact=ref(slot['id']+'/score'))
    state=run_registered(manifest,execute,score,lambda s:saved.__setitem__(slice(None),[s]))
    return dict(manifest=manifest,state=state,request_records=requests,score_records=scores,metric_identity=metric),execute,score,saved


def quality_fixture():
    planned=[];results=[]
    for i in range(320):
        for d in DIMENSIONS:
            p=dict(case_id=f'cpu_{i}',method='CPU_ROLE',dimension=d,input_status='READY_TO_SCORE',video_sha256=digest(i),prompt_sha256=digest('prompt'),
                scorer_fingerprint=digest('metric'),expected_sampling=sampling_spec(d))
            r=dict(case_id=p['case_id'],method=p['method'],dimension=d,status='SCORED',video_sha256=p['video_sha256'],prompt_sha256=p['prompt_sha256'],scorer_fingerprint=p['scorer_fingerprint'],
                observed_sampling=p['expected_sampling'],unweighted_original_per_video_result=True,metric_source_sha256={'CPU':digest('source')},decoder_evidence={'CPU_FIXTURE_ONLY':True},value=1.)
            if d=='MUSIQ_LONGER512':r['frame_scores']=[1.]*93
            planned.append(p);results.append(r)
    return planned,results

class Composition(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.template=fixture()[0]
    def setUp(self):self.v=copy.deepcopy(self.template)
    def audit(self):return audit_registered(self.v['manifest'],self.v['state'],self.v['request_records'],self.v['score_records'],self.v['metric_identity'],lambda r:None)
    def test_whole518_346scores_36shadow(self):
        a=self.audit();self.assertEqual((a['physical_paths'],a['LPIPS_pairs'],a['shadow_D_pairs']),(518,346,36))
    def test_missing_path(self):
        self.v['state']['rows'].pop()
        with self.assertRaises(ValueError):self.audit()
    def test_alias_changed(self):
        self.v['state']['rows'][0]['slot']['roles']=['changed']
        with self.assertRaises(ValueError):self.audit()
    def test_extra_score(self):
        self.v['score_records']['extra']=next(iter(self.v['score_records'].values()))
        with self.assertRaises(ValueError):self.audit()
    def test_nan_frame(self):
        next(iter(self.v['score_records'].values()))['frame_distances'][0]=float('nan')
        with self.assertRaises(ValueError):self.audit()
    def test_scalar_override(self):
        next(r for r in self.v['state']['rows'] if r['score'])['score']['LPIPS']=0.
        with self.assertRaises(ValueError):self.audit()
    def test_request_original_changed(self):
        self.v['request_records']['timing_0']['result']['full_request_seconds']=2.
        with self.assertRaises(ValueError):self.audit()
    def test_raw_artifact_changed(self):
        with self.assertRaises(ValueError):audit_registered(self.v['manifest'],self.v['state'],self.v['request_records'],self.v['score_records'],self.v['metric_identity'],lambda r:(_ for _ in ()).throw(ValueError('SHA changed')))
    def test_native_actual_steps(self):
        self.v['state']['rows'][0]['result']['guided_pairs']=36
        with self.assertRaises(ValueError):self.audit()
    def test_history_clock_contamination(self):
        row=next(r for r in self.v['state']['rows'] if r['slot']['block']=='history');row['result']['full_request_seconds']=1.
        with self.assertRaises(ValueError):self.audit()
    def test_history_audit_missing(self):
        row=next(r for r in self.v['state']['rows'] if r['slot']['block']=='history');row['result']['history_originals_audited']=False
        with self.assertRaises(ValueError):self.audit()
    def test_refused_preserves_full_denominator(self):
        calls=[];saved=[]
        def execute(s):calls.append(s);return dict(status='REFUSED')
        with self.assertRaises(ValueError):run_registered(self.v['manifest'],execute,lambda *a:{},saved.append)
        self.assertEqual(len(calls),1);self.assertEqual(len(saved[-1]['rows']),518);self.assertEqual(saved[-1]['rows'][0]['status'],'TECH_FAILED')
    def test_score_failure_keeps_raw_and_remaining(self):
        v,execute,score,_=fixture();saved=[]
        def fail(*a):raise RuntimeError('CPU_METRIC_FAILED')
        with self.assertRaises(RuntimeError):run_registered(v['manifest'],execute,fail,saved.append)
        self.assertIn('result',saved[-1]['rows'][0]);self.assertEqual(len(saved[-1]['rows']),518)
    def test_final_admission_remains_closed(self):
        from wcomr.policy_generator_r1.p2_combination_stage import validate
        with self.assertRaisesRegex(ValueError,'P2 admission closed'):validate(None,None)

class Quality(unittest.TestCase):
    def setUp(self):self.p,self.r=quality_fixture()
    def test_all1600_positions(self):self.assertEqual(audit_quality(self.p,self.r)['positions'],1600)
    def test_missing_dimension_position(self):
        self.r.pop()
        with self.assertRaises(ValueError):audit_quality(self.p,self.r)
    def test_musiq_requires_all93(self):
        self.r[4]['frame_scores'].pop()
        with self.assertRaises(ValueError):audit_quality(self.p,self.r)
    def test_wrong_video(self):
        self.r[0]['video_sha256']=digest('wrong')
        with self.assertRaises(ValueError):audit_quality(self.p,self.r)
    def test_metric_failure_not_NA(self):
        self.r[0].update(status='METRIC_FAILED',value=None)
        with self.assertRaises(ValueError):audit_quality(self.p,self.r)
    def test_registered_NA_preserved(self):
        p=self.p[0];p.update(input_status='NOT_APPLICABLE_PRE_REGISTERED',NA_reason='CPU declared only')
        self.r[0]={k:p[k] for k in ('case_id','method','dimension','NA_reason')};self.r[0].update(status='NOT_APPLICABLE_PRE_REGISTERED',value=None)
        self.assertEqual(audit_quality(self.p,self.r)['status_counts']['NOT_APPLICABLE_PRE_REGISTERED'],1)
    def test_dynamic_descriptive_binary(self):
        self.r[3]['value']=.5
        with self.assertRaises(ValueError):audit_quality(self.p,self.r)
    def test_implicit_NA_rejected(self):
        self.p[0]['input_status']='VIDEO_UNAVAILABLE'
        with self.assertRaises(ValueError):audit_quality(self.p,self.r)
if __name__=='__main__':unittest.main()
