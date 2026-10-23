import copy,unittest
from wcomr.policy_generator_r1.production_contract import matrix,COUNTS,complete_quote
from wcomr.policy_generator_r1.production_sampling import validate_policy,complete_request_seconds
from wcomr.policy_generator_r1.production_batch import run
from wcomr.policy_generator_r1.continuation_preparation import TIME_BOUNDARY
from test_policy_generator_r1 import fixture
from check_cara_pg_production_sampling_cpu_r1 import plans

class ProductionTests(unittest.TestCase):
    def test_full64_denominators(self):
        rows=matrix();self.assertEqual(len(rows),len({r['id'] for r in rows}));self.assertEqual(len(rows),64)
        self.assertEqual(sum(r['kind']=='NATIVE' for r in rows),8)
        self.assertEqual(sum(r['split']=='WARM' for r in rows),18)
        self.assertEqual(sum(r['split']=='CAL_SELECT' and r['kind']=='POLICY' for r in rows),8)
        self.assertEqual(COUNTS['maximum_CFG_calls'],4608)
    def test_arbitrary_mask_and_tampering(self):
        p,policies=plans()
        for policy in policies.values():validate_policy(p,policy)
        for field,value in [('actions',['D']*36),('shared_alpha',[1.]*36),('fingerprint','x'),('source_before',[0]*36)]:
            changed=copy.deepcopy(policies['MIXED']);changed[field]=value
            with self.assertRaises(ValueError):validate_policy(p,changed)
    def test_timing_boundary(self):
        r=dict(method_install_seconds=2.,guarded_pipeline_without_write_seconds=10.,video_write_seconds=3.,method_cleanup_seconds=1.,core_seconds=9.)
        self.assertEqual(complete_request_seconds(r),16.)
        for v in (-1.,float('nan'),float('inf')):
            with self.assertRaises(ValueError):complete_request_seconds(dict(r,video_write_seconds=v))
        with self.assertRaises(ValueError):complete_request_seconds(dict(r,core_seconds=20.))
    def test_whole_quote_does_not_credit_acceleration_or_dedup(self):
        bank={'runner':{'load_seconds':100.,'runs':[dict(status='COMPLETE',started_unix=0,ended_unix=300.) for _ in range(24)]}}
        v=complete_quote(bank);self.assertEqual(v['terms_seconds']['all64_full_paths'],19200.)
        self.assertEqual(v['physical_dedup_credit_seconds'],0);self.assertGreater(v['billed_limit_GPUh'],v['forecast_complete_GPUh'])
        bank['runner']['runs'].pop()
        with self.assertRaises(ValueError):complete_quote(bank)
    def engine(self,fail=None,exposure=True):
        profile,costs,stats,_=fixture(6);fit=['a','b','c','d'];select=['e','f'];events=[];saved=[]
        from dataclasses import asdict
        data=dict(profile=asdict(profile),costs=asdict(costs),statistics=[dict(member=m,source=s,update=t,e2=v.e2,ed=v.ed,d2=v.d2,fusion_contract=v.fusion_contract) for m in fit for (_,s,t),v in stats.items() if _=='cal-a'],CAL_FIT_members=fit,weights=[1.]*6,label_basis='SYNTHETIC_UNIT_FIXTURE',statistic_profile_identity=profile.identity,budget_seconds=22.,quantum_seconds=.5,paths_per_state=4,maximum_final_paths=32,Q=8,provenance={'fixture':True})
        def endpoint(slot,policy=None,reference=None):
            events.append(slot['id'])
            if slot['id']==fail:raise RuntimeError('Injected original failure')
            return dict(status='COMPLETE',timing_boundary=TIME_BOUNDARY,full_request_seconds=20.,core_seconds=19.,solver_steps=36,guided_pairs=36,**({'LPIPS':.05} if policy and slot['split']!='WARM' else {}))
        state=run(fit_members=fit,select_members=select,native=endpoint,evaluate=endpoint,build_consumer=lambda clock:data,
            accept_native_clock=lambda rows:{'accepted':len(rows)==4},calibration_cap_GPUh=10.5,elapsed_GPUh=lambda:0.,save=lambda s:saved.append(copy.deepcopy(s)),exposure_recheck=lambda:{'passed':exposure})
        return state,events,saved
    def test_complete_adaptive_card_closes_search_before_SELECT(self):
        s,events,history=self.engine();self.assertEqual(s['status'],'PG_P1_CAL_SELECTION_COMPLETE');self.assertLessEqual(s['query_attempts'],8)
        self.assertLessEqual(len(events),64);self.assertEqual(events[:6],['native_warm_1','native_warm_2']+['native_fit_'+str(i) for i in range(4)])
        first_select=next(i for i,e in enumerate(events) if e.startswith('native_select'))
        self.assertFalse(any(e.startswith('q') for e in events[first_select:]));self.assertIsNotNone(s['selection_frozen'])
        self.assertEqual(len(s['rows']),64);self.assertFalse(s['TEST_used'])
    def test_failure_and_exposed_SELECT_stop_without_replacement(self):
        with self.assertRaises(RuntimeError):self.engine(fail='native_fit_1')
        with self.assertRaises(ValueError):self.engine(exposure=False)

if __name__=='__main__':unittest.main()
