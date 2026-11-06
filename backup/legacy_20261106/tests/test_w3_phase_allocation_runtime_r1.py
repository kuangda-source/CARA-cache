"""Frozen feature parity, full36 controller replay and source-domain controls."""
import copy, gzip, json, math, unittest
from dataclasses import replace
from pathlib import Path
from wcomr.cfg_ra_joint_control import Calibration
from wcomr.source_aware_cpd_control import Costs
from wcomr.source_aware_phase_control import CreationPhasePrior
from wcomr.source_phase_absolute_h1_control_r1 import SourcePhaseH1Controller, fingerprint
from wcomr.w3_causal_trend_r1 import Observation
from wcomr.w3_phase_allocation_runtime_r1 import PhaseAllocationController, METHODS, online_feature, validate_T1
ROOT = Path(__file__).resolve().parents[1]

def resources(table=None):
    p = json.loads((ROOT/'manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json').read_text()) if table is None else copy.deepcopy(table)
    frozen = json.loads((ROOT/'manifests/wc_w3_T1_primary6_ridge1_window4_frozen_candidate_20261016.json').read_text())
    calibration = Calibration('DECLARED_CPU_AGE6', {(a, n): .99 for a in range(1, 36) for n in range(a+1, min(a+6, 36)+1)}, {n: 1. for n in range(1, 37)})
    costs = Costs('DECLARED_CPU_H1_QUOTES', p['source_A_cost_seconds']['D'], p['cost_seconds']['D'], p['cost_seconds']['P'])
    prior = CreationPhasePrior('DECLARED_CPU_POSITIVE_ROOT', .005, .3, early_creation_floor=.005, late_creation_floor=.02)
    kw = dict(strategy='WORKING_P_AGE_NONZERO_REBASE', table_parameters=p,
        math_parameters={'fingerprint':'CPU_DECLARED_OLD_GAMMA','gamma':p['gamma']}, horizon=1, sigma_at=lambda n: 1.-n/40)
    return calibration, costs, prior, kw, frozen

def controller(method, table=None):
    cal, costs, prior, kw, frozen = resources(table)
    return PhaseAllocationController(cal, 2., costs, prior, **kw, allocation_method=method,
        frozen_T1=frozen, request_identity=('CPU_request', 17))

def choose(c, step, delta=.5, partial=True):
    protected = step <= 7 or step == 36
    packets = () if protected else ((0, 2*(step-1)%70, delta), (1, 2*(step-1)%70+1, delta))
    return c._choice(step, packets, not protected, partial and not protected, protected=protected)

class RuntimeTests(unittest.TestCase):
    def test_all_saved_ordinary_T1_features_match_without_labels(self):
        p = ROOT/'reports/wc_w3_label64_full864_collection_20261016_0100.json.gz'
        raw = json.loads(gzip.decompress(p.read_bytes()))['capture']['receipts']
        runs = next(v['data']['runs'] for k, v in raw.items() if k.endswith('/runner.json'))
        checked = 0
        for run in runs:
            previous = None
            for row in run.get('feature_rows', []):
                o = Observation(**row['observation']); f = online_feature(o, previous); saved = row['features']['T1']
                self.assertEqual(list(f.names), saved['names']); self.assertEqual(list(f.prefix_steps), saved['prefix_steps'])
                for a, b in zip(f.values, saved['values']): self.assertLessEqual(abs(a-b), 8*2.220446049250313e-16*max(1.,abs(a),abs(b)))
                previous = o.source_id; checked += 1
        self.assertEqual(checked, 288)

    def test_wrapper_OFF_is_original_H1_for_all36_steps_and_exact_restore(self):
        cal, costs, prior, kw, _ = resources()
        original = SourcePhaseH1Controller(cal, 2., costs, prior, **kw)
        wrapped = controller('H1_ORIGINAL')
        for n in range(1, 37):
            a, b = choose(original, n, .5 if n<25 else .001), choose(wrapped, n, .5 if n<25 else .001)
            self.assertEqual(a, replace(b, owner=id(original)))
            original.commit(a, actual_action=a.action, pair_completed=True); wrapped.commit(b, actual_action=b.action, pair_completed=True)
        self.assertEqual(original._state(), wrapped._state())
        snap = wrapped.state_dict(); wrapped.accumulated = 123.; wrapped.restore(snap); self.assertEqual(wrapped.state_dict(), snap)

    def test_step23_changes_real_C_readout_root_source_without_dense_write(self):
        c = controller('STEP23_A_ONLY')
        for n in range(1, 23):
            d = choose(c, n, delta=1., partial=False); c.commit(d, actual_action=d.action, pair_completed=True)
        d = choose(c, 23, delta=1., partial=False)
        self.assertEqual((d.action, d.reason.rsplit(':',1)[-1]), ('C','A'))
        before = c._state(); c.commit(d, actual_action='C', pair_completed=True)
        self.assertEqual(c._state()[:4], before[:4]); self.assertGreater(c.accumulated, before[4])
        trace = c.query_basis(d); self.assertEqual(trace['actual_semantic_action'], 'A')
        self.assertFalse(trace['absolute_error_written_into_root_accumulator'])
        snap = c.state_dict(); c.accumulated += 9; c.restore(snap); self.assertEqual(c.state_dict(), snap)

    def test_T1_full36_pure_choice_actual_scores_and_restore(self):
        c = controller('T1_CAD'); observed = 0
        for n in range(1, 37):
            d = choose(c, n, delta=.01 if n%2 else .2); state = c.state_dict()
            self.assertEqual(d, choose(c, n, delta=.01 if n%2 else .2)); self.assertEqual(state, c.state_dict())
            self.assertNotEqual(d.action, 'P')
            if n<=7 or n==36:self.assertEqual(d.reason, 'actual_protected_dense')
            c.commit(d, actual_action=d.action, pair_completed=True)
            event = c.query_basis(d); trace = event['allocation_trace']
            if trace['decision'] is not None:
                observed += 1; scores = trace['decision']['scores']; name = min(scores,key=lambda a:(scores[a],{'C':0,'A':1,'D':2}[a]))
                self.assertEqual(event['actual_semantic_action'],name)
                self.assertEqual({a:v['score'] for a,v in event['candidate_risk_and_price'].items()},scores)
                self.assertEqual(set(a[0] for a in d.candidates),{'C','A','D'})
        self.assertGreater(observed,0); snap=c.state_dict();c.accumulated=999.;c.restore(snap);self.assertEqual(c.state_dict(),snap)
        bad=copy.deepcopy(snap);bad['binding']=bad['binding'][:-1]+(('foreign',0),)
        with self.assertRaises(ValueError):c.restore(bad)

    def test_original_P0_and_CAD_bridge_include_UNKNOWN_fallback(self):
        _,_,_,kw,_=resources();p=kw['table_parameters'];p['cost_seconds']['P']=.01
        for cell in p['table_model']['cells'].values():cell.update(C_scale=1e6,A_ratios={'FUSION_A':1.},actual_NEW_P_birth_mean=.0001)
        p['fingerprint']=fingerprint(p)
        for unknown in (False,True):
            table=copy.deepcopy(p)
            if unknown:table['table_model']['cells']['D_EARLY']['status']='UNKNOWN_ZERO_FEATURE_OR_C_TARGET';table['fingerprint']=fingerprint(table)
            for method in METHODS:
                c=controller(method,table)
                for n in range(1,8):c.commit_protected_dense(n,actual_action='D',pair_completed=True)
                d=choose(c,8,delta=1.,partial=True)
                if method in ('H1_ORIGINAL','STEP23_A_ONLY'):self.assertEqual(d.action,'P')
                else:self.assertNotEqual(d.action,'P')

    def test_corrupt_frozen_weights_and_missing_support_are_not_used(self):
        *_,frozen=resources();bad=copy.deepcopy(frozen);bad['weights'][0][0]+=1
        with self.assertRaises(ValueError):validate_T1(bad)
        c=controller('T1_CAD')
        c.calibration=Calibration('DECLARED_CPU_MISSING_CALIBRATION',{}, {n:1. for n in range(1,37)})
        for n in range(1,8):c.commit_protected_dense(n,actual_action='D',pair_completed=True)
        def forbidden(n):raise AssertionError('Unsupported state evaluated predictor')
        c.sigma_at=forbidden;d=choose(c,8)
        self.assertEqual(d.action,'D');self.assertEqual(d.reason,'missing_current_calibration')

if __name__=='__main__':unittest.main()
