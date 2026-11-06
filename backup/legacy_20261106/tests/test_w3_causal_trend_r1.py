from dataclasses import replace
import unittest

import numpy as np

from wcomr.w3_causal_trend_r1 import CausalHistory, Observation, SameStateLabel, RidgeRisk, coherent_scores, local_regret


def observation(prompt, step, *, seed=0, sigma=True):
    protected = step <= 7 or step == 36
    birth = step-1 if step <= 25 else 24 if step <= 31 else 31
    supported = not protected and step != 31
    return Observation(prompt, seed, step, f'{prompt}:{seed}:{step}', 1-step/40 if sigma else None,
        'D', f'D:{birth}', max(0, step-birth), 0., .02*step, .021*step,
        .03*step if supported else None, .5 if supported else None, protected, supported)


def dataset(prompt):
    h = CausalHistory(prompt, 0, window=4); result = []
    for step in range(1,37):
        features = h.push(observation(prompt, step))
        if step in (10,16,23,25,29,30,32,35):
            # Declared synthetic interface targets, not Cosmos/LPIPS evidence.
            label = SameStateLabel(prompt,0,step,features['T1'].observation.state_id,
                .4 + .01*step, .25 + .008*step, 'SYNTHETIC_CPU_INTERFACE')
            result.append((features, label))
    return result


class TestCausalHistory(unittest.TestCase):
    def test_future_observations_do_not_rewrite_past_features(self):
        h=CausalHistory('p',0); old=None
        for step in range(1,37):
            if step==16: old=h.push(observation('p',step))['T2']; before=old.values
            else: h.push(observation('p',step))
        self.assertEqual(old.values,before); self.assertEqual(old.prefix_steps,(13,14,15,16))
        self.assertNotIn(17,old.prefix_steps)

    def test_cross_prompt_seed_gaps_or_reversed_noise_are_rejected(self):
        h=CausalHistory('p',0); h.push(observation('p',1))
        for bad in (observation('other',2),observation('p',2,seed=1),observation('p',3),
                    replace(observation('p',2),sigma=2.)):
            with self.assertRaises(ValueError):h.push(bad)
        self.assertEqual(len(h.rows),1)

    def test_window_reset_count_uses_actual_preceding_source(self):
        h=CausalHistory('p',0)
        for step in range(1,31):features=h.push(observation('p',step))
        f=features['T2']; i=f.names.index('window_source_resets')
        self.assertEqual(f.prefix_steps,(27,28,29,30)); self.assertEqual(f.values[i],0.)

    def test_teacher_or_post_action_fields_are_not_observation_arguments(self):
        with self.assertRaises(TypeError):Observation(**{**vars(observation('p',10)),'q_A':.1})
        with self.assertRaises(TypeError):Observation(**{**vars(observation('p',10)),'future_action':'D'})

    def test_D31_domain_is_not_relaxed_by_new_features(self):
        o=observation('p',31)
        result=coherent_scores(np.array([0.,0.]),o,costs={'C':1.,'A':2.,'D':10.},lam=1.)
        self.assertEqual(result['action'],'D');self.assertIsNone(result['scores'])
        with self.assertRaises(ValueError):replace(o,calibration_supported=True,gain=1.,local_proxy=1.).validate()


class TestLabelsAndChoice(unittest.TestCase):
    def test_actual_state_identity_is_required(self):
        f,label=dataset('p')[0];label=replace(label,state_id='same-step-another-trajectory')
        with self.assertRaises(ValueError):label.target(f['T1'])

    def test_weighted_gain_is_applied_exactly_once(self):
        f,label=dataset('p')[0];feature=replace(f['T1'],observation=replace(f['T1'].observation,gain=2.))
        label=replace(label,q_C=3.,q_A=1.)
        y=label.target(feature);self.assertTrue(np.array_equal(y,[4.,8.]))
        d=coherent_scores(y,feature.observation,costs={'C':1.,'A':2.,'D':10.},lam=.5)
        self.assertEqual(d['action'],'A');self.assertEqual(d['scores']['A'],4.)
        self.assertEqual(local_regret(d,feature,label,costs={'C':1.,'A':2.,'D':10.},lam=.5),0.)

    def test_negative_A_benefit_and_risk_repair_recompute_margins(self):
        f,_=dataset('p')[0];o=f['T1'].observation
        d=coherent_scores([3.,-5.],o,costs={'C':1.,'A':2.,'D':10.},lam=1.)
        self.assertTrue(d['repair']);self.assertEqual(d['effective_delta_CA'],-3.)
        self.assertEqual(d['margin_CA'],-4.);self.assertEqual(d['action'],'C')
        self.assertEqual(d['scores']['C'],1.)

    def test_missing_sigma_is_not_timestep_conversion_or_training_label(self):
        h=CausalHistory('p',0)
        for step in range(1,11):f=h.push(observation('p',step,sigma=False))
        self.assertFalse(f['T2'].actual_sigma_available)
        _,label=dataset('p')[0]
        with self.assertRaises(ValueError):label.target(f['T1'])


class TestGroupedRidge(unittest.TestCase):
    def test_prompt_group_and_training_only_scaling(self):
        train=[(fs['T2'],label) for p in ('a','b','c') for fs,label in dataset(p)]
        test=[(fs['T2'],label) for fs,label in dataset('held')]
        model=RidgeRisk(model='T2').fit(train,forbidden_prompts=('held',))
        before=(model.mean.copy(),model.std.copy(),model.weights.copy())
        for feature,label in test:
            model.predict(feature);replace(label,q_C=1000.,q_A=500.).target(feature)
        self.assertTrue(np.array_equal(model.mean,before[0]));self.assertTrue(np.array_equal(model.std,before[1]))
        self.assertTrue(np.array_equal(model.weights,before[2]));self.assertNotIn('held',model.training_prompts)
        with self.assertRaises(ValueError):RidgeRisk(model='T2').fit(train+test,forbidden_prompts=('held',))

    def test_T1_T2_schema_and_current_only_bridge_are_distinct(self):
        rows=dataset('p'); a=RidgeRisk(model='T1').fit([(f['T1'],l) for f,l in rows])
        b=RidgeRisk(model='T2').fit([(f['T2'],l) for f,l in rows])
        self.assertEqual(len(a.names),13);self.assertEqual(len(b.names),27)
        with self.assertRaises(ValueError):a.predict(rows[0][0]['T2'])


if __name__=='__main__':unittest.main()
