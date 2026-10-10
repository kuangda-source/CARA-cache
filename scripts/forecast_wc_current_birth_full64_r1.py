#!/usr/bin/env python3
"""Conservative whole64 forecast from accepted Native and action-cost receipts."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    proof_ref=Path('reports/wc_ra_plus_a_r1_terminal_20261010_capture_and_independent_audit.json')
    ranking_ref=Path('reports/wc_action_cost_real_r1_bound_ranking_inputs_20261010.json')
    sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
    proof=json.loads(proof_ref.read_text());assert proof['independent_checks']['success']
    item=proof['files']['runner'];raw=gzip.decompress(Path(item['local_path']).read_bytes())
    assert len(raw)==item['bytes'] and hashlib.sha256(raw).hexdigest()==item['sha256']
    runner=json.loads(raw);refs=runner['comparison']['references']
    assert len(refs)==4 and all(r['outcome']=='ACCEPTED' and r['solver_steps']==36 and r['CFG_calls']==72 for r in refs)
    costs=json.loads(ranking_ref.read_text());assert (costs['registered_cost_rows'],costs['timed_values'])==(48,144)
    mean=dict(costs['ranking']['global_means'])
    native=max(r['pipeline_wall_seconds'] for r in refs)
    reuse=max(mean['C'],mean['A_W1_ONE_PHASE'],mean['A_BETA1_ONE_PHASE'])
    maintenance=max(0.,mean['DENSE_WITH_P0']-mean['DENSE_REFERENCE'])
    # Deliberately charge all64 paths as slowest complete Native, with extra
    # A heads and dense projection maintenance on all36 pairs of every path.
    # The 1.35 factor covers new state/JSON/vector IO and hardware variation;
    # it is a planning envelope, never a speed result or runtime guarantee.
    base=64*native+64*36*(reuse+maintenance)+runner['load_seconds']
    seconds=base*1.35+120.
    value={'status':'COMPLETE64_CONSERVATIVE_PLANNING_ENVELOPE_NOT_SPEED_RESULT',
        'complete_paths':64,'solver_updates':2304,'net_calls':4608,
        'native_all_four_pipeline_seconds':[r['pipeline_wall_seconds'] for r in refs],
        'slowest_accepted_native_pipeline_seconds':native,'parent_model_load_seconds':runner['load_seconds'],
        'all36_extra_reuse_action_seconds_per_pair':reuse,'all36_dense_maintenance_extra_seconds_per_pair':maintenance,
        'unmargined_full_scope_seconds':base,'whole_scope_margin_multiplier':1.35,'shutdown_flush_reserve_seconds':120.,
        'forecast_complete_seconds':seconds,'forecast_complete_GPUh':seconds/3600.,
        'not_a_hard_runtime_limit_or_claimed_speed':True,'old_card_authorization_not_reused':True,
        'source_sha256':{str(proof_ref):sha(proof_ref),str(ranking_ref):sha(ranking_ref),
            item['local_path']:sha(item['local_path']),str(Path(__file__).resolve().relative_to(Path.cwd().resolve())):sha(__file__)},'GPU_submissions':0,'budget_written':False}
    dest=Path('reports/wc_current_birth_full64_whole_cost_20261010.json');assert not dest.exists()
    dest.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:value[k] for k in ('status','complete_paths','forecast_complete_GPUh','GPU_submissions')}))


if __name__=='__main__':main()
