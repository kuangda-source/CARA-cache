#!/usr/bin/env python3
"""Post-result exploration of the complete fixed-quota card. No new rollout or fit."""
import gzip
import hashlib
import json
import math
from pathlib import Path

REG = 'manifests/wc_w3_cfg_budget_followup_cpu_preregistration_20261009.json'
CELLS = ('BASE', 'CFG0', 'CFG1', 'PAIRED')


def main():
    reg = json.loads(Path(REG).read_text())
    for name, digest in reg['input_sha256'].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == digest, name
    runner = json.loads(gzip.decompress(Path(reg['runner_ref']).read_bytes()))
    score = json.loads(gzip.decompress(Path(reg['score_ref']).read_bytes()))
    audit = json.loads(Path(reg['complete_audit_ref']).read_text())
    assert audit['all_masks_independently_reconstructed']
    row = runner['cases'][0]['WC']['requests'][0]
    cells = {n: next(x for x in row['children'] if x['label'] == n + '_first') for n in CELLS}
    base = cells['BASE']
    losses = score['losses']
    records = {}
    for name, cell in cells.items():
        events = cell['record']['action_report']['suffix_events']
        records[name] = {
            'current_and_donor_events': events[:4],
            'actual_full_calls': [e['call'] for e in events if e['actual_action'] == 'D'],
            'native_adaptive_proposal_disagreements': [e['call'] for e in events
                if e['paid_probe'] and (e['actual_action'] == 'C') != e['native_skip']],
            'first_model_input_difference_vs_BASE': next((45 + i for i, (a, b) in
                enumerate(zip(base['inputs'], cell['inputs'])) if a != b), None),
            'first_model_output_difference_vs_BASE': next((45 + i for i, (a, b) in
                enumerate(zip(base['outputs'], cell['outputs'])) if a != b), None),
            'first_solver_update_difference_vs_BASE': next((23 + i for i, (a, b) in
                enumerate(zip(base['solver_outputs'], cell['solver_outputs'])) if a != b), None),
            'pre46_own_history': cell['pre46']['own_history'],
        }
        assert cell['inputs'][:2] == base['inputs'][:2]
        assert cell['record']['action_report']['per_CFG_full_counts'] == [18, 17]
    pairs = [('CFG0_given_CFG1_C', 'BASE', 'CFG0'),
             ('CFG0_given_CFG1_D', 'CFG1', 'PAIRED'),
             ('CFG1_given_CFG0_C', 'BASE', 'CFG1'),
             ('CFG1_given_CFG0_D', 'CFG0', 'PAIRED')]
    conditional = []
    for name, left, right in pairs:
        changes = [a - b for a, b in zip(losses[left]['frame_distances'], losses[right]['frame_distances'])]
        signed = math.fsum(changes) / 93
        conditional.append({'context': name, 'comparison': right + '_vs_' + left,
            'signed_quality': signed,
            'relative_fidelity_improvement_percent': 100 * signed / losses[left]['mean_LPIPS'],
            'improved_frames': sum(x > 0 for x in changes),
            'worse_frames': sum(x < 0 for x in changes),
            'three_equal31_frame_mean_changes': [math.fsum(changes[i:i+31]) / 31 for i in (0,31,62)],
            'whole_full_saved': 0, 'single_action_RV_label': False})
    changed = [k for k in sorted(base['pre46']['components']) if
               base['pre46']['components'][k] != cells['CFG0']['pre46']['components'][k]]
    out = {
        'status': 'EXPOSED_FIXED_CFG_QUOTA_CONTEXT_CPU_DIAGNOSIS_COMPLETE_NOT_MEDIATION_NOT_CONF',
        'preregistration_ref': REG, 'input_hashes_verified': True,
        'estimand': 'total effect of registered fixed-mask position exchange at per-CFG quota 18/17',
        'all_four_current_input_pairs_equal': True,
        'CFG0_D45_output_equal_given_CFG1_C_or_D': cells['CFG0']['outputs'][0] == cells['PAIRED']['outputs'][0],
        'CFG1_D46_output_equal_given_CFG0_C_or_D': cells['CFG1']['outputs'][1] == cells['PAIRED']['outputs'][1],
        'CFG1_C46_output_equal_given_CFG0_C_or_D': cells['BASE']['outputs'][1] == cells['CFG0']['outputs'][1],
        'pre46_changed_component_names_after_CFG0_D': changed,
        'pre46_current_latent_equal': base['pre46']['components']['output'] == cells['CFG0']['pre46']['components']['output'],
        'pre46_solver_components_equal': all(base['pre46']['components'][k] == cells['CFG0']['pre46']['components'][k]
            for k in base['pre46']['components'] if k.startswith('solver.')),
        'conditional_position_exchange_effects': conditional, 'recorded_routes_and_divergence': records,
        'shared_factorial_helper_metadata_warning': {
            'native_helper_status': score['factorial_summary']['status'],
            'native_interaction_interpretation': score['factorial_summary']['interaction']['interpretation'],
            'explanation': 'Legacy adaptive wording is inherited from a pure arithmetic helper; actual current routing is fixed mask. Original bytes are retained. No adaptive continuation or single-action labels are inferred here.'},
        'missing_for_guided_error_cancellation_attribution': [
            'paired signed velocity/residual error vectors on identical actual states',
            'guided error inner products and norms', 'separate donor-step intervention holding other mechanisms fixed'],
        'vector_magnitude_or_unique_causal_mediation_inferred': False,
        'all_four_cell_and_all93_frame_denominators_retained': True,
        'new_comparisons_post_result_exploratory': True,
        'formal_RV_training_labels': False, 'fit_or_new_generation': False,
        'CUDA_initialized': False, 'GPU_submissions': 0,
    }
    dest = Path('reports/wc_w3_cfg_budget_context_cpu_results_20261009.json')
    with dest.open('x') as f:
        f.write(json.dumps(out, indent=2, allow_nan=False) + '\n')
    print(json.dumps({k: out[k] for k in ('status', 'conditional_position_exchange_effects',
        'CFG0_D45_output_equal_given_CFG1_C_or_D', 'CFG1_D46_output_equal_given_CFG0_C_or_D',
        'CFG1_C46_output_equal_given_CFG0_C_or_D', 'pre46_changed_component_names_after_CFG0_D')}))


if __name__ == '__main__':
    main()
