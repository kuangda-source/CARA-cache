"""Audit original S metadata for V1 source coverage; no fitting or GPU access."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path

from wcomr.sq_s_sources_r1 import PARENTS


ROOT = Path(__file__).resolve().parents[1]


def audit(metadata, manifest):
    raw = Path(metadata).read_bytes();packet = json.loads(raw)
    original = json.loads((ROOT/packet['source_ref']).read_text())
    assert hashlib.sha256((ROOT/packet['source_ref']).read_bytes()).hexdigest() == packet['source_sha256']
    assert packet['exit_code'] == 0 and packet['GPU_submissions'] == 0 and not packet['ledger_written']
    expected = {r['path']:r for r in original['artifact_acceptance']['files'] if '/streaming/row-' in r['path']}
    files = packet['result']['files']
    assert len(files) == 108 and {r['path'] for r in files} == set(expected)
    card = json.loads(Path(manifest).read_text());sigmas = card['schedule']['sigmas']
    rows = []
    for item in files:
        encoded = item['raw_utf8'].encode();value = json.loads(encoded);source = value['source']
        assert len(encoded) == expected[item['path']]['bytes']
        assert hashlib.sha256(encoded).hexdigest() == item['sha256'] == expected[item['path']]['sha256']
        t = value['step'];parent = value['parent'];a,b = source['source_anchor_steps']
        assert parent in PARENTS and value['prompt'] in card['FIT'] and 1 <= a < b < t <= 36
        assert [s for s in PARENTS[parent] if s < t][-2:] == [a,b]
        assert source['parent'] == parent and source['step'] == t and source['context'] == value['context']
        assert source['source_captured_before_parent_pair'] and not source['current_D_in_source']
        assert source['native_window_lengths'] == [3,3] and source['consumed_anchor_slots'] == 2
        assert source['complete_shadow_transaction_accepted'] and value['parent_roundtrip_equal']
        assert value['paid_prefix_equal'] and value['teacher_writes_parent'] is False
        assert value['sigma'] == sigmas[t-1] and all(math.isfinite(value['moments'][k]) for k in ('C','U','K','CFG'))
        action = 'D' if t in PARENTS[parent] else 'C'
        assert value['planned_parent_action'] == action
        assert value['actual_D_teacher_reused'] == (action == 'D')
        assert value['extra_Dense_teacher_pairs'] == (1 if action == 'C' else 0)
        rows.append(dict(member=value['prompt'], parent=parent, t=t, a=a, b=b, parent_action=action,
            sigma_t=sigmas[t-1], current_sigma_age=abs(sigmas[t-1]-sigmas[b-1]),
            previous_sigma_gap=abs(sigmas[b-1]-sigmas[a-1]), source_step_age=t-b, source_step_gap=b-a,
            raw_guided_moment=value['moments']['CFG'], existing_risk_normalization='teacher_energy_normalized_in_S_only',
            row_sha256=item['sha256']))
    identities = [(r['member'],r['parent'],r['t']) for r in rows]
    assert len(set(identities)) == 108

    def summary(part):
        grouped = defaultdict(set)
        for r in part:
            grouped[(r['t'],r['b'])].add(r['a'])
        varied = [dict(t=t,b=b,previous_a=sorted(values)) for (t,b),values in sorted(grouped.items()) if len(values)>1]
        return dict(rows=len(part), unique_t_a_b=len({(r['t'],r['a'],r['b']) for r in part}),
            exact_stage_and_current_age_with_different_previous_gap=varied,
            source_step_age_range=[min(r['source_step_age'] for r in part),max(r['source_step_age'] for r in part)],
            source_step_gap_range=[min(r['source_step_gap'] for r in part),max(r['source_step_gap'] for r in part)])

    return dict(schema='CARA_SOURCE_LIFECYCLE_OLD108_COVERAGE_R1',
        status='ORIGINAL108_SOURCE_METADATA_VERIFIED_NEW_COVERAGE_REQUIRED_BEFORE_V1_FIT',
        metadata_ref=str(metadata), metadata_sha256=hashlib.sha256(raw).hexdigest(),
        original_accepted_ref=packet['source_ref'], manifest_ref=str(manifest),
        same_state_source_identity_accepted=True, all_rows=summary(rows),
        actual_C_shadow_D_rows=summary([r for r in rows if r['parent_action']=='C']),
        D_parent_counterfactual_rows=52, actual_C_shadow_D_count=56,
        counts_by_parent_action={parent+'|'+action:count for (parent,action),count in
            sorted(Counter((r['parent'],r['parent_action']) for r in rows).items())},
        source_parent_masks={k:list(v) for k,v in PARENTS.items()},
        parent_mask_validation_groups=2, trajectory_validation_groups=4,
        split_rule='leave_one_parent_mask_out_across_both_FIT; never_random_adjacent_rows',
        random_row_split_allowed=False, arbitrary_source_combinations_calibrated=False,
        new_19D_22D_source_span_coverage_needed=True, old_labels_fitted=False,
        old_S_mask_or_scores_changed=False, rows=sorted(rows,key=lambda r:(r['member'],r['parent'],r['t'])),
        new_GPU_submissions=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata', type=Path, required=True)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = audit(args.metadata,args.manifest)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({k:result[k] for k in ('status','all_rows','actual_C_shadow_D_rows')}))


if __name__ == '__main__':
    main()
