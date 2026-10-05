"""Four signed joint-swap diagnostics from six complete Native losses, no Torch."""
import math

LABELS = ('BASE1', 'SWAP0_first', 'SWAP1_first')
POLICY = {'benefit': 'J_FIXED_BASE_MINUS_J_TWO_POSITION_SWAP_NEGATIVE_VALUES_RETAINED',
          'comparison': 'OFFLINE_SAME_CFG_TWO_POSITION_ACTION_SWAP',
          'per_CFG_refresh_quota_matched': True, 'equal_runtime': False,
          'single_action_RV_training_label': False, 'online_policy': False,
          'exposed_CAL_not_CONF': True, 'physics_or_quality_noninferiority': False}


def signed_placement_diagnostics(pairs, config):
    scenes = config['scope']['scenes']
    if len(scenes) != 2 or len(pairs) != 6:
        raise ValueError('Two frozen scenes and all six Native-relative losses required')
    expected = [(s['scene'], label) for s in scenes for label in LABELS]
    if [(p['scene'], p['label']) for p in pairs] != expected:
        raise ValueError('Placement score identity/order/denominator differs')
    by = {}
    for pair in pairs:
        score = pair['score']; name = pair['scene']; label = pair['label']
        expected_slot = None if label == 'BASE1' else int(label[4])
        values = score['frame_distances']
        if (pair['CFG_slot'] != expected_slot or score['frames'] != 93
                or len(score['pts']) != 93 or len(values) != 93
                or pair['reference'] != config['references'][name]['Native35']
                or score['reference_sha256'] != pair['reference']['sha256']
                or score['candidate_sha256'] != pair['candidate']['sha256']
                or any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
                or type(score['mean_LPIPS']) not in (int, float) or not math.isfinite(score['mean_LPIPS'])
                or not math.isclose(score['mean_LPIPS'], sum(values)/93, rel_tol=1e-12, abs_tol=1e-12)):
            raise ValueError('Complete placement frame loss/reference/candidate binding differs')
        by[name, label] = score
    results = []
    for scene in scenes:
        name = scene['scene']; base = by[name, 'BASE1']
        for slot in (0, 1):
            swap = by[name, 'SWAP'+str(slot)+'_first']
            if base['pts'] != swap['pts'] or base['reference_sha256'] != swap['reference_sha256']:
                raise ValueError('Placement baseline/swap full timestamps or Native reference differ')
            results.append({'scene': name, 'CFG_slot': slot,
                'swap_calls': list(scene['swaps'][slot]['calls']),
                'LPIPS_BASE': base['mean_LPIPS'], 'LPIPS_SWAP': swap['mean_LPIPS'],
                'LPIPS_BASE_minus_SWAP': base['mean_LPIPS']-swap['mean_LPIPS'],
                'policy_protocol': POLICY.copy(), 'signed_negative_retained': True,
                'formal_RV_training_label': False, 'clean_speed_or_new_online_method_gain': False})
    return results
