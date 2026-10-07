"""Fresh-seed causal checks, including original-D no-op and complete inventories."""
from .mid_coverage import tree_digest
from .rv0_causal import TRACE_KEYS

LABELS = ['OFF1','OFF2','BASE_first','REFRESH_second','REFRESH_first','BASE_second']
ENCODED = ['OFF1','BASE_first','REFRESH_first']
PIPELINE = ['decode_input','decode_output','guardrail_input','guardrail_output','save_input']


def require(ok, message):
    if not ok: raise ValueError(message)


def state_components(value, inventory, *, fingerprint=None, output=None):
    require(isinstance(value, dict) and bool(value) and set(value) == inventory
            and all(type(v) is str and len(v) == 64 and all(c in '0123456789abcdef' for c in v) for v in value.values()),
            'Complete finite state hash inventory differs')
    if fingerprint is not None: require(tree_digest(value) == fingerprint, 'State fingerprint differs')
    if output is not None: require(value['output'] == output, 'State output binding differs')


def verify_seed_row(row, deep_count):
    require(row['target_call'] == 46 and row['slot'] == 1 and row['prepare_calls'] == 1
            and row['flags_before'] == row['flags_after']
            and row['sample_return_sha256'] == row['final_latent_sha256'], 'Seed parent context differs')
    require(all(len(row[k]) == (36 if k == 'solver_outputs' else 72) for k in TRACE_KEYS), 'Complete seed parent required')
    require([e['stage'] for e in row['pipeline']] == PIPELINE, 'Parent output pipeline differs')
    inventory = set(row['final_components'])
    require({'output','cpu_rng','python_rng','numpy_rng','cuda_rng','explicit_generators','net.cnt','solver._step_index'} <= inventory,
            'Complete state families missing')
    state_components(row['final_components'], inventory, output=row['final_latent_sha256'])
    by = {c['label']:c for c in row['children']}
    require(list(by) == LABELS and len(row['children']) == 6, 'Six ordered suffix controls required')
    parent_tail = {k: row[k][22 if k == 'solver_outputs' else 44:] for k in TRACE_KEYS}
    for label in ['OFF1','OFF2','BASE_first','BASE_second']:
        child = by[label]
        require(all(child[k] == parent_tail[k] for k in TRACE_KEYS)
                and child['final_latent_sha256'] == row['final_latent_sha256']
                and child['record']['final_state_components'] == row['final_components'], 'Adaptive BASE/OFF differs from parent')
    for first, second in [('OFF1','OFF2'),('BASE_first','BASE_second'),('REFRESH_first','REFRESH_second')]:
        a,b = by[first],by[second]
        require(all(a[k] == b[k] for k in TRACE_KEYS+['final_latent_sha256','pre46'])
                and a['record']['final_state_components'] == b['record']['final_state_components']
                and a['record']['action_report'] == b['record']['action_report'], 'Strict seed repeat differs')
    base, refresh = by['BASE_first'], by['REFRESH_first']
    require(base['pre46'] == refresh['pre46'] and base['inputs'][:2] == refresh['inputs'][:2]
            and all(base[k][:1] == refresh[k][:1] for k in ('outputs','deep','banks')), 'Pre46 same-state/current input differs')
    for label, child in by.items():
        rec = child['record']; report = rec['action_report']; events = report['suffix_events']
        state_components(rec['final_state_components'], inventory, fingerprint=rec['final_state_sha256'], output=child['final_latent_sha256'])
        state_components(child['pre46']['components'], inventory, fingerprint=child['pre46']['fingerprint'])
        require(child['pre46']['own_history'][1] and rec['parent_restored']
                and rec['completed_updates'] == 22 and rec['planned_remaining_updates'] == 14
                and all(len(child[k]) == (14 if k == 'solver_outputs' else 28) for k in TRACE_KEYS)
                and [e['call'] for e in events] == list(range(45,73))
                and not report['budget_matched'] and report['remaining_policy'] == 'ORIGINAL_WC_ADAPTIVE'
                and not any(e['current_deep_truth_used'] for e in events), 'Full seed causal suffix required')
        expected = 'D' if label.startswith('REFRESH') else 'OFF'
        require(child['action'] == expected and report['plan']['action'] == expected
                and report['plan']['target_call'] == 46 and report['decision_interventions'] == int(expected == 'D'),
                'Only one registered D46 instruction allowed')
        require(all(d in (0,deep_count) for d in child['deep'])
                and ['C' if d == 0 else 'D' for d in child['deep']] == [e['actual_action'] for e in events], 'Deep execution/actions disagree')
        require(events[-3]['native_cycle_reset'] and child['deep'][-2:] == [deep_count,deep_count], 'Terminal WC reset differs')
        for e in events:
            if e['call'] != 46 or expected == 'OFF':
                require(e['requested'] is None and e['selected_skip'] == e['native_skip'] if e['paid_probe'] else e['requested'] is None,
                        'Native suffix policy changed outside D46')
        if expected == 'D':
            target = events[1]
            require(target['requested'] == 'D' and target['paid_probe'] and target['cfg_slot'] == 1
                    and target['actual_action'] == 'D' and 1 <= target['age_solver_steps'] <= 32,
                    'D46 legal paid own-CFG decision missing')
    native_skip = base['record']['action_report']['suffix_events'][1]['native_skip']
    require(native_skip == refresh['record']['action_report']['suffix_events'][1]['native_skip'], 'Paired paid native proposal differs')
    if not native_skip:
        require(all(base[k] == refresh[k] for k in TRACE_KEYS+['final_latent_sha256'])
                and base['record']['final_state_components'] == refresh['record']['final_state_components'], 'Original-D no-op changed actual trajectory')
    decoded = {c['label']:c for c in row['decoded_children']}
    require(list(decoded) == ENCODED, 'Three child encodings required')
    for child in decoded.values():
        require(child['status'] == 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
                and child['flags_before'] == child['flags_after']
                and [e['stage'] for e in child['pipeline']] == PIPELINE, 'Full child output pipeline missing')
    require(decoded['OFF1']['pipeline'] == decoded['BASE_first']['pipeline'] == row['pipeline']
            and decoded['OFF1']['artifact']['sha256'] == decoded['BASE_first']['artifact']['sha256'] == row['artifact']['sha256'],
            'Fresh parent/OFF/BASE byte bridge differs')
    if not native_skip:
        require(decoded['REFRESH_first']['artifact']['sha256'] == row['artifact']['sha256'], 'No-op encoded output differs')
    return {'eligible_original_C46': bool(native_skip), 'original_D46_noop': not native_skip,
            'suffix_full_counts': {label:[sum(e['actual_action']=='D' for e in c['record']['action_report']['suffix_events'][slot::2]) for slot in (0,1)] for label,c in by.items()},
            'current_truth_used': False, 'RV_label': False}
