"""Fixed V1 scalar/selection controls; synthetic targets, no video efficacy."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

from wcomr.cara_fast_spec_r1 import digest
from wcomr.cara_source_lifecycle_estimation_r1 import (
    Estimator, FAMILIES, RIDGE, complete_samples, coordinates, features,
    fit, fit_validate_plan, select_complete_FIT)

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT/'plans/cara_next_stage_20261101/source_lifecycle/V1_CALIBRATION64_DESIGN_R1.json'
MANIFEST = ROOT/'plans/cara_next_stage_20261101/e1/ENDPOINT7_46_MANIFEST_R1.json'
METRICS = {}


def fixture_packet():
    design = json.loads(DESIGN.read_text())
    manifest = json.loads(MANIFEST.read_text())
    rows = []
    for index, member in enumerate(design['FIT']):
        for parent in design['parents']:
            for state in parent['states']:
                t, a, b = (state[k] for k in ('t', 'a', 'b'))
                sigma, age, gap = coordinates(manifest['schedule']['sigmas'], t, a, b)
                target = .1+.2*sigma+.3*age+2.*gap+.5*gap*gap+(2*index-1)*.001
                identity = member+'/'+parent['id']+'/'+str(t)
                rows.append(dict(member=member, parent_id=parent['id'],
                                 parent_fingerprint=parent['policy']['fingerprint'],
                                 t=t, a=a, b=b, source_steps_by_CFG=[[a, b], [a, b]],
                                 C_input_state_id=identity, shadow_D_input_state_id=identity,
                                 parent_before_shadow_id=identity, parent_after_shadow_id=identity,
                                 sum_squared_error_fp64=target*4096, element_count=4096))
    packet = dict(schema='CARA_V1_SAME_STATE_SCALAR_LABELS_R1', status='COMPLETE',
                  input_kind='SYNTHETIC_CPU', design_scope_sha256=design['scope_sha256'],
                  schedule_sha256=digest(manifest['schedule']), rows=rows,
                  provenance=dict(teacher='candidate_own_current_state_shadow_D',
                                  teacher_writes_parent=False, target_normalized=False,
                                  target='FP64_MSE_OF_ACTUAL_SAME_STATE_FP32_CFG'))
    return packet, design, manifest


class Estimation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet, cls.design, cls.manifest = fixture_packet()
        cls.samples = complete_samples(cls.packet, cls.design, cls.manifest['schedule'])
        # Deliberately synthetic weights; original UniPC weights need their own
        # source/grid-bound production export, never infer them from this control.
        cls.weights = [1.+.01*i for i in range(36)]
        cls.pipeline = fit_validate_plan(cls.samples, cls.design, cls.manifest, cls.weights)

    def test_complete64_sources_and_raw_target_moments(self):
        self.assertEqual(len(self.samples), 64)
        for sample in self.samples:
            row = next(r for r in self.packet['rows'] if (r['member'], r['parent_id'], r['t']) ==
                       (sample.member, sample.parent, sample.t))
            self.assertEqual(sample.target, row['sum_squared_error_fp64']/row['element_count'])
            self.assertLess(sample.a, sample.b)
            self.assertLess(sample.b, sample.t)
        METRICS['complete_design'] = dict(rows=64, parents=4, members=2, synthetic_labels=True)

    def test_individually_metered_family_preserves_all_original_fixed_outputs(self):
        separate = [fit_validate_plan(self.samples, self.design, self.manifest, self.weights,
                    families=(family,))['families'][0] for family in FAMILIES]
        self.assertEqual(separate, self.pipeline['families'])

    def test_partial_duplicate_foreign_and_wrong_source_rows_refused(self):
        mutations = [lambda p: p['rows'].pop(),
                     lambda p: p['rows'].__setitem__(0, deepcopy(p['rows'][1])),
                     lambda p: p['rows'][0].update(member='OLD_CHECK_FORBIDDEN'),
                     lambda p: p['rows'][0].update(a=p['rows'][0]['a']+1),
                     lambda p: p['rows'][0].update(parent_fingerprint='foreign'),
                     lambda p: p['rows'][0].update(sum_squared_error_fp64=float('nan'))]
        for mutation in mutations:
            changed = deepcopy(self.packet)
            mutation(changed)
            with self.assertRaises(ValueError):
                complete_samples(changed, self.design, self.manifest['schedule'])

    def test_native_teacher_normalized_target_state_mismatch_and_parent_write_refused(self):
        mutations = [lambda p: p['provenance'].update(teacher='Native_other_trajectory'),
                     lambda p: p['provenance'].update(target_normalized=True),
                     lambda p: p['provenance'].update(teacher_writes_parent=True),
                     lambda p: p['rows'][0].update(shadow_D_input_state_id='other-state'),
                     lambda p: p['rows'][0].update(parent_after_shadow_id='mutated-parent'),
                     lambda p: p['rows'][0].update(source_steps_by_CFG=[[1, 2], [3, 4]])]
        for mutation in mutations:
            changed = deepcopy(self.packet)
            mutation(changed)
            with self.assertRaises(ValueError):
                complete_samples(changed, self.design, self.manifest['schedule'])

    def test_fixed_ridge_solution_satisfies_independent_normal_equation(self):
        model = fit(self.samples, 'stage_age_previous_gap')
        x = np.asarray([features(s.coordinates, model.family) for s in self.samples])
        y = np.asarray([s.target for s in self.samples])
        penalty = np.diag([0.]+[RIDGE]*9)
        gradient = x.T@(x@np.asarray(model.coefficients)-y)/len(y)+penalty@model.coefficients
        self.assertLess(float(np.max(np.abs(gradient))), 1e-12)
        self.assertEqual(model.record()['ridge'], 1e-4)
        self.assertFalse(model.record()['intercept_penalized'])
        METRICS['ridge_stationarity_max_error'] = float(np.max(np.abs(gradient)))

    def test_input_equal_fit_is_unchanged_by_one_members_duplicate_rows(self):
        model = fit(self.samples, 'stage_age_previous_gap')
        member = self.samples[0].member
        duplicated = self.samples+tuple(s for s in self.samples if s.member == member)
        other = fit(duplicated, model.family)
        self.assertLess(max(abs(a-b) for a, b in zip(model.coefficients, other.coefficients)), 1e-11)

    def test_entire_parent_holdout_both_members_and_nested_gap_signal(self):
        losses = []
        for result in self.pipeline['families']:
            self.assertEqual(len(result['whole_parent_folds']), 4)
            for fold in result['whole_parent_folds']:
                self.assertNotIn(fold['held_out_parent'], fold['train_parents'])
                self.assertEqual(len(fold['train_parents']), 3)
                self.assertEqual(fold['train_rows'], 48)
                self.assertEqual(fold['diagnostic']['rows'], 16)
                self.assertEqual(set(fold['held_out_members']), set(self.design['FIT']))
            losses.append(result['held_out_input_equal_MSE'])
        self.assertLess(losses[2], losses[1])
        self.assertFalse(self.pipeline['adjacent_random_split'])
        METRICS['synthetic_whole_parent_MSE'] = dict(zip(FAMILIES, losses))

    def test_same_t_b_different_previous_source_affects_only_full_family(self):
        contrast = self.design['exact_stage_age_gap_contrasts'][0]
        t, b = contrast['t'], contrast['b']
        left, right = (coordinates(self.manifest['schedule']['sigmas'], t, a, b)
                       for a in contrast['previous_a'][:2])
        for family in FAMILIES[:2]:
            model = fit(self.samples, family)
            self.assertEqual(model.predict(left), model.predict(right))
        model = fit(self.samples, FAMILIES[2])
        self.assertGreater(abs(model.predict(left)-model.predict(right)), 1e-5)
        negative = Estimator('stage', (-1., 0., 0.), ((0., 1.),)*3, frozenset(), 1)
        self.assertEqual(negative.predict(left), 0.)

    def test_all_three_models_generate_exact19_and22_top3_under_same_dp(self):
        for result in self.pipeline['families']:
            self.assertEqual(set(result['candidates']), {'19', '22'})
            for budget, value in result['candidates'].items():
                masks = [tuple(row['dense_steps']) for row in value['plans']]
                self.assertEqual(len(masks), len(set(masks)))
                self.assertEqual(len(masks), 3)
                for row in value['plans']:
                    self.assertEqual(len(row['dense_steps']), int(budget))
                    self.assertEqual(row['policy']['counts']['A'], 0)
                    self.assertTrue(set(self.manifest['profile']['protected_dense']) <= set(row['dense_steps']))
        self.assertFalse(self.pipeline['GPU_dispatch_ready'])
        self.assertFalse(self.pipeline['whole_collection_provenance_accepted'])
        METRICS['synthetic_plan_positions'] = dict(families=3, budgets=[19, 22], top_k=3,
                                                 total=18, real_video_efficacy=False)

    def test_full93_fit_selection_ties_and_failure_denominators(self):
        candidates = self.pipeline['families'][2]['candidates']['19']['plans']
        scores = [dict(candidate_id=c['policy']['fingerprint'], member=m, status='COMPLETE',
                       Alex_curve=[.2]*93) for c in candidates for m in self.design['FIT']]
        selected = select_complete_FIT(candidates, scores, self.design['FIT'])
        self.assertEqual(selected['candidate_id'], min(candidates, key=lambda c:
            (c['proxy_cost'], c['dense_steps']))['policy']['fingerprint'])
        changed = deepcopy(scores)
        changed[0]['Alex_curve'] = [.01]*93
        changed[1]['Alex_curve'] = [.01]*93
        self.assertEqual(select_complete_FIT(candidates, changed, self.design['FIT'])['candidate_id'],
                         candidates[0]['policy']['fingerprint'])
        self.assertFalse(selected['CHECK_used'])
        tied = deepcopy(candidates)
        for row in tied:
            row['proxy_cost'] = 1.
        self.assertEqual(select_complete_FIT(tied, scores, self.design['FIT'])['candidate_id'],
                         min(tied, key=lambda r: r['dense_steps'])['policy']['fingerprint'])
        mutations = [lambda x: x.pop(), lambda x: x[0].update(member='OLD_CHECK'),
                     lambda x: x[0].update(status='TECH_FAILED'),
                     lambda x: x[0].update(Alex_curve=[.2]*92)]
        for mutation in mutations:
            changed = deepcopy(scores)
            mutation(changed)
            with self.assertRaises(ValueError):
                select_complete_FIT(candidates, changed, self.design['FIT'])
        METRICS['selection_controls'] = dict(frames=93, input_equal=True, CHECK_refused=True,
                                            missing_failure_partial_refused=True)

    def test_original_weights_reject_foreign_grid_partial_or_terminal_substitution(self):
        from fit_cara_source_lifecycle_v1_r1 import frozen_weights
        contract = json.loads((DESIGN.parent/'V1_FIXED_ESTIMATION_COMPONENT_CONTRACT_R1.json').read_text())
        schedule = self.manifest['schedule']
        record = dict(schedule, schema='CARA_SOURCE_LIFECYCLE_FROZEN_UNIPC_SCALE_R1',
                      coefficients=[1.]*36, weights=[1.]*36)
        record.update(original_UniPC_source_sha256=contract['original_UniPC_source_sha256'],
                      current_corrector_and_predictor_included=True, terminal_sensitivity=False)
        self.assertEqual(frozen_weights(record, schedule, contract, False), [1.]*36)
        self.assertEqual(frozen_weights(record, schedule, contract, True), [1.]*36)
        mutations = [lambda r: r.update(terminal_sensitivity=True),
                     lambda r: r['weights'].pop(),
                     lambda r: r.update(original_UniPC_source_sha256='foreign'),
                     lambda r: r.update(sigmas=[1.]*37),
                     lambda r: r.update(weights=[2.]*36)]
        for mutation in mutations:
            changed = deepcopy(record)
            mutation(changed)
            with self.assertRaises(ValueError):
                frozen_weights(changed, schedule, contract, False)

    def test_complete_scalar_to_candidate_cli_and_explicit_fixture_boundary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            labels, weights, output = (directory/name for name in ('labels.json', 'weights.json', 'output.json'))
            labels.write_text(json.dumps(self.packet))
            scale = dict(self.manifest['schedule'], schema='CARA_SOURCE_LIFECYCLE_SYNTHETIC_SCALE_CPU_R1',
                         coefficients=[1.]*36, weights=[1.]*36)
            weights.write_text(json.dumps(scale))
            command = [sys.executable, str(ROOT/'scripts/fit_cara_source_lifecycle_v1_r1.py'),
                       '--labels', str(labels), '--weights', str(weights), '--output', str(output)]
            refused = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(refused.returncode, 0)
            self.assertFalse(output.exists())
            accepted = subprocess.run(command+['--fixture-only'], capture_output=True, text=True)
            self.assertEqual(accepted.returncode, 0, accepted.stderr)
            report = json.loads(output.read_text())
            self.assertTrue(report['CPU_fixture_only'])
            self.assertEqual(report['samples'], 64)
            self.assertEqual(len(report['families']), 3)
            self.assertFalse(report['endpoint_selection_performed'])
            self.assertFalse(report['whole_collection_provenance_accepted'])
            self.assertEqual(report['GPU_submissions'], 0)
            repeated = subprocess.run(command+['--fixture-only'], capture_output=True, text=True)
            self.assertNotEqual(repeated.returncode, 0)
            METRICS['complete_CLI'] = dict(rows=64, candidates=18, fixture_flag_required=True,
                                         original_output_overwrite_refused=True, GPU_submissions=0)


if __name__ == '__main__':
    unittest.main()
