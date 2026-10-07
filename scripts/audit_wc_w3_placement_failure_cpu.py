#!/usr/bin/env python3
"""Audit the immutable incomplete R1 receipt; never grant full-card acceptance."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys


def audit(root):
    read = lambda name: json.loads((root/name).read_text())
    capture = read('reports/wc_w3_placement_failed_native_capture_20261007.json')
    supervisor = read('reports/wc_w3_placement_failed_supervisor_native_20261007.json')
    config = read('configs/wc_w3_placement_approved_r1_20261007.json')
    raw = gzip.decompress((root/'reports/wc_w3_placement_failed_runner_native_20261007.json.gz').read_bytes())
    receipt = json.loads(raw)
    budget = read('reports/budget.json')
    sys.path.insert(0, str(root/'src'))
    from wcomr.rv0_placement_execution import reserve_budget, settle_budget, audit_settlement
    from wcomr.rv0_fixed_plan import FixedMaskPlan, cfg_full_counts
    for item in capture['local_artifacts'].values():
        path = root/item['local_path']
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == item['local_sha256']
        native = gzip.decompress(data) if path.suffix == '.gz' else data
        assert hashlib.sha256(native).hexdigest() == item['native_sha256']
        assert len(native) == item['native_bytes']
    assert capture['payload_sha256'] == capture['expected_payload_sha256'] == config['payload_sha256']
    assert hashlib.sha256((root/'configs/wc_w3_placement_approved_r1_20261007.json').read_bytes()).hexdigest() == capture['local_artifacts']['config']['native_sha256']
    assert receipt['scope'] == config == supervisor['config']
    assert supervisor['status'] == 'TECH_BLOCKED' and supervisor['exit_code'] == 1
    assert receipt['status'] == 'TECH_BLOCKED_PLACEMENT_2_PARENT_16_SUFFIX_10_OUTPUT_DENOMINATOR_PRESERVED'
    assert receipt['source_revision'] == supervisor['source_revision'] == 'de24070522000a5d17ad64ca0651ac102e9eddc3'
    assert receipt['pid'] == supervisor['child_pid'] and 'cleanup_error' not in receipt and 'settlement_error' not in supervisor
    assert [receipt[k] for k in ['planned_parent_phases','planned_suffix_controls','planned_encoded_outputs']] == [2,16,10]
    assert len(receipt['requests']) == 1
    row = receipt['requests'][0]
    assert len(row['inputs']) == len(row['outputs']) == 44 and len(row['solver_outputs']) == 22
    children = row['children']
    assert [c['label'] for c in children] == ['OFF1','OFF2','BASE1','SWAP0_first']
    off1, off2, base, swap = children
    trace = ['inputs','outputs','deep','banks','solver_outputs','final_latent_sha256']
    assert all(off1[k] == off2[k] == base[k] for k in trace)
    assert off1['record']['final_state_components'] == off2['record']['final_state_components'] == base['record']['final_state_components']
    assert off1['record']['action_report'] == off2['record']['action_report']
    for child in children:
        assert child['record']['parent_restored'] is True
    for child in children[:3]:
        assert child['status'] == 'COMPLETE_PLACEMENT_SUFFIX_NOT_RV_LABEL'
        assert [len(child[k]) for k in trace[:5]] == [28,28,28,28,14]
        assert child['record']['action_report']['per_CFG_full_counts'] == [18,17]
    assert swap['error'] == receipt['error'] == 'Protected native action differs; swap infeasible without fallback'
    assert swap['status'] == 'TECH_BLOCKED' and swap['swap_calls'] == [47,49]
    lengths = {k:len(swap[k]) for k in trace[:5]}
    assert list(lengths.values()) == [26,25,25,25,12]
    failure_call = 44 + len(swap['inputs'])
    assert failure_call == 70 and len(swap['outputs']) == len(swap['inputs'])-1
    scene = config['scope']['scenes'][0]
    mask = tuple(scene['parent_action_mask'])
    plan = FixedMaskPlan(mask, (47,49)); plan.validate()
    expected = plan.action_mask()
    completed_actions = tuple('C' if d == 0 else 'D' for d in swap['deep'])
    assert completed_actions == expected[44:69]
    assert [i+45 for i,(a,b) in enumerate(zip(base['deep'],swap['deep'])) if a != b] == [47,49]
    assert swap['inputs'][:3] == base['inputs'][:3]
    assert expected[69] == 'C' and cfg_full_counts(expected) == cfg_full_counts(mask) == (18,17)
    # The failure predicate has two actions. C was planned, hence D was proposed.
    # This is an inference from source and coverage, not a saved pending event.
    assert supervisor['budget_after'] == budget
    reserved = reserve_budget(supervisor['budget_before'], config, supervisor['pid'])
    assert settle_budget(reserved, supervisor['budget_before'], config, supervisor['wall_seconds'], supervisor['pid']) == budget
    assert not any(k.endswith('_inflight') for k in budget) and budget['gpu_jobs_launched'] == 50
    assert budget['cap_gpu_hours'] == 24 and budget['used_gpu_hours'] < 24
    assert supervisor['cumulative_budget_exceeded'] is False
    assert capture['original_pids_absent'] and capture['global_lock_free']
    assert not supervisor['release']['pids'] and supervisor['release']['memory_used_mib'] == 24
    assert supervisor['release']['uuid'] == config['gpu_uuid']
    assert config['gpu_uuid'] not in capture['compute_apps']
    assert len(row['decoded_children']) == len(capture['videos']) == 2
    reference = config['references'][row['sample_name']]['official_WC']
    assert all(v['sha256'] == reference['sha256'] and v['bytes'] == reference['bytes'] for v in capture['videos'].values())
    for child in row['decoded_children']:
        assert child['status'] == 'ORIGINAL_TAIL_GUARDED_ENCODED_COMPLETE'
        assert child['artifact']['sha256'] == reference['sha256']
    monitors = [json.loads(line) for line in gzip.decompress((root/'reports/wc_w3_placement_failed_monitor_native_20261007.jsonl.gz').read_bytes()).decode().splitlines()]
    assert monitors and all(m['uuid'] == config['gpu_uuid'] and set(m['pids']).issubset({supervisor['pid'],supervisor['child_pid']}) for m in monitors)
    try:
        audit_settlement(supervisor, receipt, config, budget, supervisor['source_revision'])
    except ValueError:
        success_auditor_rejected = True
    else:
        raise AssertionError('An incomplete card must not pass the success auditor')
    return {'status':'R1_INCOMPLETE_COST_RELEASE_CONTROLS_AND_FAILURE_LOCATION_AUDIT_PASS_NOT_PLACEMENT_RESULT',
        'source_revision':supervisor['source_revision'], 'GPU_submissions':0,
        'planned_denominator':{'parents':2,'suffixes':16,'videos':10,'swaps':4},
        'actual':{'parents_started':1,'parents_complete':0,'suffixes_started':4,'suffixes_complete':3,'videos':2,'science_swaps_complete':0},
        'failure':{'call':failure_call,'CFG_slot':1,'solver_step':35,'planned_action':'C',
            'native_proposal_inferred_from_predicate':'D','pending_event_saved':False,
            'completed_actions_differ_only_at':[47,49],'failure_after_exact_planned_partial_mask':True},
        'controls':{'OFF_repeat_exact':True,'BASE_OFF_trajectory_exact':True,'actual_full_CFG_counts':[18,17],'historical_video_byte_identity':True},
        'cost':{'wall_seconds':supervisor['wall_seconds'],'GPUh':supervisor['wall_seconds']/3600,
            'used_GPUh':budget['used_gpu_hours'],'remaining_GPUh':24-budget['used_gpu_hours'],'job_count':50,
            'actual_cost_reconstruction':True,'inflight':False},
        'original_pids_absent':True,'shared_lock_free':True,'target_gpu_released':True,
        'stage_source_payloads_unchanged':len(config['payload_sha256']),
        'monitor_rows':len(monitors),'monitor_peak_mib':max(m['memory_used_mib'] for m in monitors),
        'normal_success_auditor_rejected':success_auditor_rejected,
        'full_card_acceptance':False,'LPIPS_swap_labels':0,'direction_refuted':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); result=audit(args.root)
    if args.output.exists(): raise ValueError('Preserve prior failure audit')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
