#!/usr/bin/env python3
"""Read accepted CAL scalars only; no dispatch, training, or policy selection."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics as st

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
ACTIONS = ('C', 'A_HALF', 'A_ONE')
CAPTURE = 'reports/wc_policy_assets_full1624_fourcard_GPU_terminal_20261023_0826.json'
ACCEPTED = 'reports/wc_policy_assets_full1624_fourcard_GPU_accepted_20261023_0826.json'
CONFIG = 'configs/wc_policy_interval_assets_full1624_r1_20261020.json'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def validate_rows(rows, scenes, grid):
    require(len(rows) == len(scenes) == 4 and {r['scene'] for r in rows} == set(scenes),
            'Exactly four original CAL scenes required')
    result = []
    for scene in scenes:
        row = next(r for r in rows if r['scene'] == scene)
        points = row['interval_cells']
        require(row['status'] == 'COMPLETE' and len(points) == len(grid) == 406
                and {(p['source'], p['target']) for p in points} == set(grid),
                'Complete unique original 406-cell domain required')
        indexed = {(p['source'], p['target']): p for p in points}
        values = []
        for s, t in grid:
            p = indexed[s, t]
            require(p['label_basis'] == 'TEACHER_CONDITIONED_PROPOSAL'
                    and p['free_policy_history_truth'] is False
                    and p['source_anchor_steps'] == [s - 1, s]
                    and p['actual_parent_action'] == 'DD', 'Teacher provenance changed')
            v = p['statistics']
            q = [v['e2'], v['actual_half_MSE'], v['e2'] + 2*v['ed'] + v['d2']]
            require(all(math.isfinite(x) and x > 0 for x in q),
                    'Positive finite log-labels required; no silent epsilon/clipping')
            values.append(q)
        result.append(values)
    return result


def load():
    cap, acc, config = (read(ROOT / p) for p in (CAPTURE, ACCEPTED, CONFIG))
    require(acc['status'] == 'POLICY_INTERVAL_ASSETS_FULL_ORIGINALS_AND_FINANCE_ACCEPTED'
            and acc['full_protocol_accepted'] is True and acc['formal_source_time_cells'] == 1624
            and acc['registered_paths'] == 14 and acc['missing_or_rejected_paths'] == []
            and acc['container_binding_accepted'] is True
            and acc['capture_ref'] == CAPTURE and acc['capture_sha256'] == sha(ROOT / CAPTURE)
            and acc['source_revision'] == cap['launch']['source_revision']
            and acc['registration_sha256'] == cap['registration_sha256'],
            'Saved independent acceptance must bind original completed capture')
    require(all(r['seed'] == 0 for r in config['requests']), 'Original seed0 required')
    scenes = [r['name'] for r in config['requests']]
    grid = [(s, t) for t in range(8, 36) for s in range(7, t)]
    rows = [r for r in cap['runner']['runs'] if r['section'] == 'FORMAL' and r['mode'] == 'COLLECT']
    return validate_rows(rows, scenes, grid), scenes, grid


def additive_fit(y, grid):
    """OLS categorical target + age on the triangular domain by backfitting."""
    groups_t = {t: [j for j, (_, u) in enumerate(grid) if u == t] for t in {t for _, t in grid}}
    groups_a = {a: [j for j, (s, t) in enumerate(grid) if t-s == a] for a in {t-s for s, t in grid}}
    f, g = {t: 0. for t in groups_t}, {a: 0. for a in groups_a}
    for iteration in range(1000):
        old = [f[t] + g[t-s] for s, t in grid]
        for t, ii in groups_t.items():
            f[t] = st.mean(y[j] - g[grid[j][1]-grid[j][0]] for j in ii)
        for a, ii in groups_a.items():
            g[a] = st.mean(y[j] - f[grid[j][1]] for j in ii)
        fit = [f[t] + g[t-s] for s, t in grid]
        if max(abs(a-b) for a, b in zip(old, fit)) < 1e-12:
            return fit, iteration + 1
    raise ValueError('Descriptive additive fit did not converge')


def decompose(y, grid):
    """Balanced scene x cell decomposition on natural-log local MSE."""
    n, m = len(y), len(grid)
    require(n > 1 and m > 1 and all(len(row) == m for row in y), 'Balanced matrix required')
    mu = st.mean(v for row in y for v in row)
    pm = [st.mean(row) for row in y]
    cm = [st.mean(y[i][j] for i in range(n)) for j in range(m)]
    total = math.fsum((v-mu)**2 for row in y for v in row)
    cell = n * math.fsum((v-mu)**2 for v in cm)
    prompt = m * math.fsum((v-mu)**2 for v in pm)
    interaction = math.fsum((y[i][j]-pm[i]-cm[j]+mu)**2 for i in range(n) for j in range(m))
    require(math.isclose(total, cell+prompt+interaction, rel_tol=1e-11, abs_tol=1e-11), 'SS identity failed')
    fit, iterations = additive_fit([v-mu for v in cm], grid)
    sse = math.fsum((y[i][j]-mu-fit[j])**2 for i in range(n) for j in range(m))
    return dict(total_SS=total, cell_SS=cell, prompt_SS=prompt, interaction_SS=interaction,
                joint_cell_fraction=cell/total if total else None,
                prompt_fraction=prompt/total if total else None,
                interaction_fraction=interaction/total if total else None,
                additive_time_age_R2=1-sse/total if total else None,
                additive_iterations=iterations, held_out=False,
                residual_is_scene_cell_interaction_not_independent_noise=True)


def loo_actions(values, scenes):
    """Unbudgeted cellwise diagnostic, not a legal schedule or adaptive bound."""
    rows = []
    for i, scene in enumerate(scenes):
        chosen, oracle, intersections, regrets, widths = [], [], [], [], []
        for j, actual in enumerate(values[i]):
            predicted = [st.mean(values[k][j][a] for k in range(len(scenes)) if k != i) for a in range(3)]
            winners = [a for a in range(3) if predicted[a] == min(predicted)]
            best = {a for a in range(3) if actual[a] == min(actual)}
            # Declared order C, A_HALF, A_ONE only resolves exact predictor ties.
            chosen.append(actual[winners[0]])
            oracle.append(min(actual))
            intersections.append(bool(set(winners) & best))
            regrets.append([min(actual[a] for a in winners)-min(actual),
                            max(actual[a] for a in winners)-min(actual)])
            widths.append(len(winners))
        shared, own = st.mean(chosen), st.mean(oracle)
        rows.append(dict(scene=scene, cells=len(chosen), shared_local_MSE=shared,
                         privileged_cellwise_oracle_local_MSE=own,
                         oracle_reduction_vs_shared=1-own/shared,
                         best_set_overlap_fraction=st.mean(intersections),
                         exact_prediction_ties=sum(w > 1 for w in widths),
                         mean_tied_choice_regret_range=[st.mean(r[k] for r in regrets) for k in (0, 1)]))
    return dict(rows=rows, equal_scene_shared_local_MSE=st.mean(r['shared_local_MSE'] for r in rows),
                equal_scene_oracle_local_MSE=st.mean(r['privileged_cellwise_oracle_local_MSE'] for r in rows),
                budget_matched=False, executable_trajectory=False, endpoint_upper_bound=False,
                split='EXPLORATORY_OLD_CAL_LEAVE_ONE_SCENE_OUT', prices_used=False)


def analyze():
    values, scenes, grid = load()
    decomposition = {action: decompose([[math.log(v[a]) for v in row] for row in values], grid)
                     for a, action in enumerate(ACTIONS)}
    refs = (CAPTURE, ACCEPTED, CONFIG)
    return dict(status='COMPLETED_CPU_DESCRIPTIVE_ANALYSIS_ONLY', scenes=scenes, seeds=[0],
                formal_cells=1624, independent_prompt_count=4, actions=list(ACTIONS),
                label_definition='C=e2; A_HALF=actual_half_MSE; A_ONE=e2+2ed+d2',
                log_definition='natural log of guided local MSE, no epsilon',
                decomposition=decomposition, leave_one_scene_out=loo_actions(values, scenes),
                source_bindings=[dict(ref=p, sha256=sha(ROOT/p)) for p in refs],
                analysis_source_sha256=sha(__file__),
                decision_contract_sha256=sha(HERE/'decision_contract.json'),
                GPU_submissions=0, remote_calls=0, ledger_written=False,
                policy_exported=False, scheduler_trained=False,
                own_trajectory_diagnostic_completed=False, endpoint_quality_result=False,
                automatic_reopening_of_closed_probe_line=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists(), 'Preserve original output; use a fresh path')
    result = analyze()
    with args.output.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(dict(status=result['status'], output=str(args.output), GPU_submissions=0)))
