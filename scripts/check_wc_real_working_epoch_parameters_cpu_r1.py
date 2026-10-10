#!/usr/bin/env python3
"""Complete real-parameter wiring against saved D6 packets, never a rollout."""
import copy
from dataclasses import asdict, replace
import gzip
import hashlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wcomr.action_cost_ranking import BOUNDARY, build_ranking
from wcomr.cfg_ra_joint_control import Calibration, JointCDController
from wcomr.real_working_epoch_parameters_r1 import build_parameters, METHODS, FINGERPRINT
from wcomr.source_aware_working_epoch_control_r2 import WorkingEpochCPDController, STRATEGIES
from build_wc_action_cost_ranking_real_r1 import PROOF, DEST, read_native

REG = Path('manifests/wc_real_working_epoch_parameters_cpu_r1_preregistration_20261010.json')


def serial_decision(decision):
    value = asdict(decision); value.pop('owner', None)
    return value


def main():
    started = time.perf_counter(); reg = json.loads(REG.read_text())
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    before = sha('reports/budget.json')
    for name, digest in reg['source_sha256'].items():
        if sha(name) != digest:
            raise ValueError('Registered parameter source changed: ' + name)
    proof, bound = [json.loads(p.read_text()) for p in (PROOF, DEST)]
    if (not proof['independent_checks']['success'] or proof['GPU_exit_code'] != 0
            or proof['CPU_exit_code'] != 0 or bound['source_proof_sha256'] != sha(PROOF)):
        raise ValueError('Complete independent cost proof required')
    native, runner = [read_native(proof, k) for k in ('calibration_table', 'runner')]
    ranking = build_ranking(native['all_group_cost_seconds'], boundary=BOUNDARY,
        source_kind='INDEPENDENTLY_CAPTURED_REAL_FULL_ACTION_COST_CARD',
        source_sha256=proof['files']['calibration_table']['sha256'])
    if json.loads(json.dumps(asdict(ranking))) != bound['ranking']:
        raise ValueError('Complete all144 cost reconstruction differs')
    ra = json.loads(gzip.decompress(Path(reg['RA_calibration_table_ref']).read_bytes()))
    base = dict(ra); fingerprint = base.pop('fingerprint')
    if (hashlib.sha256(json.dumps(base, sort_keys=True, allow_nan=False).encode()).hexdigest()
            != fingerprint or fingerprint != FINGERPRINT):
        raise ValueError('Actual original RA calibration changed')
    calibration = Calibration(fingerprint,
        {(v['anchor'], v['step']): v['rho'] for v in ra['rho_at']},
        {int(k): v for k, v in ra['gains'].items()})
    floor_path = Path(reg['creation_floor_ref']); floors = json.loads(floor_path.read_text())
    if floors['source_proof_sha256'] != sha(PROOF):
        raise ValueError('Creation prior belongs to another cost source')
    paths = []; bindings = []; restores = 0; P_pairs = 0
    for strategy in STRATEGIES:
        specs, evidence = build_parameters(calibration, ranking, floors,
            strategy=strategy, floor_source_sha256=sha(floor_path))
        bindings.append(evidence)
        for request in runner['batch']['requests']:
            parent = next(p for p in request['paths'] if p['collect'] is True)
            if parent['status'] != 'COMPLETE_PARENT_PATH' or len(parent['own_history']) != 36:
                raise ValueError('Complete saved D6 packet parent required')
            actual = {}
            for method in METHODS:
                spec = specs[method]
                controller = JointCDController(calibration, spec['threshold']) if method == 'SOURCE_RA' else \
                    WorkingEpochCPDController(calibration, spec['threshold'], spec['costs'],
                        spec['partial_prior'], strategy=strategy)
                actions = []; decisions = []; states = []
                for row in parent['own_history']:
                    step = row['step']; protected = step <= 7 or step == 36
                    packets = [SimpleNamespace(**{k: p[k] for k in ('slot', 'counter', 'delta_y')})
                        for p in row['paid_probes']]
                    if protected:
                        controller.commit_protected_dense(step,
                            actual_action='DD' if method == 'SOURCE_RA' else 'D', pair_completed=True)
                        decision = controller.history[-1]
                    else:
                        kwargs = {'both_sources_ready': True}
                        if method != 'SOURCE_RA': kwargs['partial_ready'] = spec['partial_prior'] is not None
                        decision = controller.decide(step, packets, **kwargs)
                        controller.commit(decision, actual_action=decision.action, pair_completed=True)
                    action = decision.action[0]; actions.append(action)
                    decisions.append(serial_decision(decision))
                    states.append({'anchor': controller.anchor, 'accumulated': controller.accumulated})
                    if action == 'P':
                        P_pairs += 1
                        if (controller.creation_floor != spec['partial_prior'].creation_floor_at(step)
                                or controller.creation_floor <= 0 or controller.consecutive_P > 2):
                            raise ValueError('Positive phase birth prior or consecutive protection differs')
                    if step in reg['state_steps']:
                        if method == 'SOURCE_RA':
                            keys = ('anchor', 'accumulated', 'last_completed_step', 'generation', 'history', 'poisoned')
                            snapshot = copy.deepcopy({k: getattr(controller, k) for k in keys})
                            controller.anchor = None; controller.accumulated = -1.
                            for k, v in snapshot.items(): setattr(controller, k, copy.deepcopy(v))
                            if {k: getattr(controller, k) for k in keys} != snapshot:
                                raise ValueError('Original RA reference state roundtrip failed')
                        else:
                            snapshot = controller.state_dict()
                            controller.creation_floor = -1.; controller.accumulated = -1.
                            controller.restore(snapshot)
                            if controller.state_dict() != snapshot:
                                raise ValueError('Working-source full healthy history roundtrip failed')
                        restores += 1
                if len(actions) != 36 or actions[:7] != ['D']*7 or actions[-1] != 'D':
                    raise ValueError('Complete protected full36 script scope required')
                actual[method] = {'actions': actions, 'decisions': decisions, 'states': states}
                paths.append({'strategy': strategy, 'scene': request['sample_name'], 'method': method,
                    'source_packet_role': 'FIXED_D6_PACKETS_SCRIPTED_WIRING_NOT_CLOSED_LOOP_ROLLOUT',
                    **actual[method]})
            if (actual['SOURCE_RA']['actions'] != actual['DYNAMIC_NO_P']['actions']
                    or actual['SOURCE_RA']['states'] != actual['DYNAMIC_NO_P']['states']
                    or actual['CPD'] != actual['REF_CPD'] or actual['CPD'] != actual['A_CPD_OFF']
                    or actual['DENSE_CONTROL']['actions'] != ['D']*36):
                raise ValueError('Complete no-P, OFF, reference or dense controls differ')
    refusals = []
    for fault in reg['mutation_controls']:
        cal, rank, f, strategy, digest0 = calibration, ranking, copy.deepcopy(floors), STRATEGIES[0], sha(floor_path)
        if fault == 'foreign_RA_fingerprint': cal = replace(calibration, fingerprint='FOREIGN')
        elif fault == 'synthetic_cost_role': rank = replace(ranking, source_kind='SYNTHETIC_INTERFACE_CONTROL')
        elif fault == 'wrong_cost_boundary': rank = replace(ranking, boundary='FULL_PAIR_NOT_MEASURED')
        elif fault == 'false_P_future_drift': f['P_future_drift_empirically_calibrated'] = True
        elif fault == 'wrong_phase_boundary': f['creation_phase_boundary'] = 24
        elif fault == 'missing_creation_origin': f['phase_priors']['12']['all_four_origins'].pop()
        elif fault == 'zero_early_floor': f['phase_priors']['12']['median_creation_floor_proxy'] = 0.
        elif fault == 'nonfinite_late_floor': f['phase_priors']['30']['median_creation_floor_proxy'] = float('inf')
        elif fault == 'changed_P_mode': f['fixed_P_mode'] = 'RANDOM_050'
        elif fault == 'changed_transfer_ratio': f['borrowed_D_drift_ratio_assumption'] = .5
        elif fault == 'missing_cost_denominator': f['original_timed_values'] = 141
        elif fault == 'claimed_installed_prior': f['model_or_controller_installed'] = True
        elif fault == 'foreign_working_strategy': strategy = 'UNREGISTERED_ZERO_RESET'
        elif fault == 'missing_source_fingerprint': digest0 = ''
        else: raise ValueError('Unknown registered mutation')
        try: build_parameters(cal, rank, f, strategy=strategy, floor_source_sha256=digest0)
        except ValueError: refusals.append(fault)
        else: raise AssertionError('Foreign production parameter accepted: ' + fault)
    if len(paths) != 64 or sum(len(p['actions']) for p in paths) != 2304 or restores != 256:
        raise ValueError('Whole real-parameter wiring denominator changed')
    if sha('reports/budget.json') != before:
        raise ValueError('Pure parameter CPU must not change budget')
    result = {'status': 'REAL_PARAMETER_FULL64_SCRIPTED_CPU_PASS_NOT_COSMOS_ROLLOUT',
        'registration_ref': str(REG), 'registration_sha256': sha(REG),
        'source_sha256': reg['source_sha256'], 'parameter_bindings': bindings, 'paths': paths,
        'complete_scripted_full36_paths': 64, 'complete_scripted_decisions': 2304,
        'healthy_state_roundtrips': restores, 'scripted_P_actions_not_real_P_calls': P_pairs,
        'mutation_refusals': refusals, 'complete_actual_cost_rows': 48, 'actual_timed_values': 144,
        'saved_D6_packet_inputs_not_new_adaptive_trajectory': True,
        'model_or_controller_installed': False, 'CUDA_initialized': False,
        'GPU_submissions': 0, 'ledger_written': False,
        'budget_before_sha256': before, 'budget_after_sha256': sha('reports/budget.json'),
        'CPU_wall_seconds': time.perf_counter()-started}
    dest = Path(reg['output'])
    if dest.exists(): raise ValueError('Preserve first complete parameter result')
    dest.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({k: result[k] for k in ('status', 'complete_scripted_full36_paths',
        'complete_scripted_decisions', 'healthy_state_roundtrips', 'CPU_wall_seconds', 'GPU_submissions')}))


if __name__ == '__main__': main()
