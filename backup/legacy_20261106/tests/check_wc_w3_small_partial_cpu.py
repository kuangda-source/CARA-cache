"""CPU raw-receipt partial-analysis controls; does not accept the failed card."""
import ast
import copy
import gzip
import json
from pathlib import Path
from wcomr.rv0_small_partial import partial_plan


def run(root):
    config = json.loads((root/'configs/wc_w3_small_cd_approved_r1_20261005.json').read_text())
    raw = json.loads(gzip.decompress((root/'reports/wc_w3_small_cd_runner_20261005.json.gz').read_bytes()))
    plan = partial_plan(raw, config)
    assert len(plan['matrix']) == 2 and len(plan['pairs']) == 2 and len(plan['files']) == 4 and len(plan['references']) == 1
    assert plan['original_denominator'] == {'parents':2,'suffixes':12,'new_outputs':8,'Native_relative_losses':4,'signed_diagnostics':2}
    assert plan['matrix'][1]['status'] == 'UNFINISHED_OR_TECH_BLOCKED' and plan['full_card_accepted'] is False
    source = ast.parse((root/'src/wcomr/rv0_small_evaluation.py').read_text())
    full = next(n for n in source.body if isinstance(n,ast.FunctionDef) and n.name=='audit_trajectories')
    body = next(n for n in full.body if isinstance(n,ast.For)).body
    partial = ast.parse((root/'src/wcomr/rv0_small_partial.py').read_text())
    one = next(n for n in partial.body if isinstance(n,ast.FunctionDef) and n.name=='validate_complete_row')
    assert [ast.dump(n) for n in body] == [ast.dump(n) for n in one.body[:-1]]
    refused = []
    mutations = [('shrunken_original_scope',lambda r:r.update(planned_suffix_controls=6)),
        ('CPU_not_real_GPU',lambda r:r.update(CUDA_initialized=False)),
        ('toy_not_real_GPU',lambda r:r.update(toy_fixture=True)),
        ('lost_repeat',lambda r:r['requests'][0]['children'].pop()),
        ('truncated_trajectory',lambda r:r['requests'][0]['children'][2]['solver_outputs'].pop()),
        ('current_truth_leak',lambda r:r['requests'][0]['children'][2]['record']['action_report']['suffix_events'][0].update(current_deep_truth_used=True)),
        ('failed_history_bridge',lambda r:r['requests'][0].update(historical_WC_encoded_bridge_pass=False)),
        ('paid_probe_missing',lambda r:r['requests'][0]['children'][2]['record']['action_report']['suffix_events'][0].update(paid_probe=False)),
        ('repeat_value_changed',lambda r:r['requests'][0]['children'][5]['outputs'].__setitem__(0,'f'*64))]
    for name, mutate in mutations:
        broken=copy.deepcopy(raw);mutate(broken)
        try:partial_plan(broken,config)
        except (ValueError,KeyError):refused.append(name)
        else:raise AssertionError('Invalid completed row accepted: '+name)
    missing=copy.deepcopy(raw);missing['requests'].pop();p=partial_plan(missing,config)
    assert len(p['matrix'])==2 and p['matrix'][1]['status']=='UNFINISHED_OR_TECH_BLOCKED'
    return {'status':'PARTIAL_FAILED_CARD_CPU_RAW_CONTROLS_PASS_NOT_FULL_CARD_OR_METRIC',
        'strict_row_checks_AST_identical_to_frozen_full_audit':True,'refusals':refused,
        'refusal_count':len(refused),'original_two_scene_denominator_retained':True,'GPU_submissions':0}


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(a.root)))
