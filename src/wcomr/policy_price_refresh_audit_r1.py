"""Reject incomplete prices; bind replacement costs to immutable old labels."""
import copy
import math
import statistics
from .policy_interval_assets_r1 import cells, ROUNDS, SCENES
from .policy_price_refresh_contract_r1 import matrix, COUNTS, VERSION

PROVENANCE = ('source', 'target', 'source_anchor_steps', 'source_sha256', 'older_source_sha256', 'input_sha256')


def audit_price_cells(rows, original):
    if [(r['source'], r['target']) for r in rows] != cells() or len(original) != 406:
        raise ValueError('Complete ordered 406-cell domain required')
    expected = [(r, a) for r, order in ROUNDS for a in order]
    for row, old in zip(rows, original):
        if any(row[k] != old[k] for k in PROVENANCE) or row['original_parent_hashes_equal'] is not True:
            raise ValueError('Original parent provenance differs')
        if row['source_shadow_writes_parent'] or row['extra_deep_teacher_pairs'] or row['new_error_labels'] or row['raw_interval_tensors_written']:
            raise ValueError('Price-only no-write boundary differs')
        if [(t['round'], t['action']) for t in row['price_trials']] != expected:
            raise ValueError('All three balanced formal repeats required at every cell')
        for t in row['price_trials']:
            if (not math.isfinite(t['seconds']) or t['seconds'] <= 0 or not t['repeated_output_equal']
                    or t['shared_prefix_included'] or t['restore_copy_hash_write_included']
                    or t['boundary'] != 'AFTER_ALREADY_PAID_PROBES_THROUGH_WC_HEAD_RF_AND_SHARED_FUSION'):
                raise ValueError('Changed or invalid action timing boundary')
    return dict(accepted=True, cells=406, readout_trials=4872, new_error_labels=0)


def make_repriced_bundle(rows, original_rows, old_bundle, *, original_bundle_sha256, prices_sha256,
                         profile_identity, exclusive_accepted, parity_accepted):
    if not exclusive_accepted or not parity_accepted:
        raise ValueError('Full exclusive monitoring and old Native parity required')
    if len(rows) != 10 or any(any(r[k] != p[k] for k in p) or r['status'] != 'COMPLETE'
                              for r, p in zip(rows, matrix())):
        raise ValueError('All ten registered complete paths required')
    old = {r['scene']: r for r in original_rows if r['mode']=='COLLECT' and r['section']=='FORMAL'}
    if set(old) != set(SCENES): raise ValueError('All original four CAL labels required')
    for row in rows:
        clocks = row['action_clocks']
        if len(clocks) != 36 or [c['step'] for c in clocks] != list(range(1, 37)):
            raise ValueError('All36 new D and shared-prefix prices required')
        for c in clocks:
            if (c['boundary'] != 'SHARED_PREFIX_PLUS_NONOVERLAPPING_POST_PROBE_D' or c['diagnostics_included']
                    or any(not math.isfinite(c[k]) or c[k] < 0 for k in ('D_action_seconds','shared_prefix_seconds','whole_pair_seconds'))
                    or c['D_action_seconds'] <= 0 or c['whole_pair_seconds'] <= 0):
                raise ValueError('Invalid D/shared timing boundary')
        if row['mode']=='PRICE': audit_price_cells(row['price_cells'], old[row['scene']]['interval_cells'])
    # Reuse the accepted aggregation unchanged, substituting new clocks only.
    from .policy_interval_assets_audit_r1 import make_generator_bundle
    formal = []
    for row in rows:
        if row['section'] != 'FORMAL': continue
        r = copy.deepcopy(row)
        if r['mode']=='PRICE':
            r['mode']='COLLECT'
            r['interval_cells']=copy.deepcopy(old[r['scene']]['interval_cells'])
            for point, price in zip(r['interval_cells'], row['price_cells']):
                point['price_trials']=price['price_trials']
        formal.append(r)
    result = make_generator_bundle(formal, profile_identity)
    if result['statistics'] != old_bundle['statistics'] or result['profile'] != old_bundle['profile']:
        raise ValueError('Replacement price bundle changed frozen labels/profile')
    result.update(status='COMPLETE_OLD_LABELS_WITH_NEW_EXCLUSIVE_PRICES', version=VERSION,
        original_label_bundle_sha256=original_bundle_sha256, replacement_prices_sha256=prices_sha256,
        clean_action_prices_accepted=True, scope_counts=COUNTS,
        exclusive_monitoring_accepted=True, old_Native_parity_accepted=True,
        original_bundle_unchanged=True)
    return result
