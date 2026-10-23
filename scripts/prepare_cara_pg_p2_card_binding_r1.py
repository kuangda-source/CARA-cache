#!/usr/bin/env python3
"""Recheck P1 and P2 CPU originals, then prepare dedup; never quote/dispatch."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'scripts')]
from prepare_cara_pg_p2_after_p1_r1 import checked,roles_from_batch,accept_p1,accept_cpu,accept_combination
from wcomr.policy_generator_r1.production_terminal import record
from wcomr.policy_generator_r1.p2_card_binding import binding_blueprint
from wcomr.policy_generator_r1.continuation_preparation import require


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('p1-capture','p1-acceptance','cpu-capture','cpu-acceptance','combination-capture',
              'combination-acceptance','quality-readiness','manifest','output'):
        p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();require(not a.output.exists(),'Preserve original binding')
    p1,pa=checked(a.p1_capture,a.p1_acceptance,accept_p1)
    require(pa['PG_P2_input_ready'] is True,'No accepted P1 policy, no P2 binding')
    _,ca=checked(a.cpu_capture,a.cpu_acceptance,accept_cpu)
    _,co=checked(a.combination_capture,a.combination_acceptance,accept_combination)
    require(ca['production_entry_CPU_accepted'],'Actual Native/history CPU missing')
    refs=[a.p1_capture,a.p1_acceptance,a.cpu_capture,a.cpu_acceptance,a.combination_capture,a.combination_acceptance,a.quality_readiness,a.manifest]
    bindings=[dict(ref=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in refs]
    original=dict(status='P2_ORIGINAL_P1_POLICY_AND_NATIVE_HISTORY_CPU_BOUND_NOT_DISPATCH',
        P1_selected_policy_frozen=True,roles=roles_from_batch(record(p1,'runner')['batch']),source_bindings=bindings)
    quality=json.loads(a.quality_readiness.read_text())
    # Local packet readiness cannot grant real-model CPU acceptance.
    require(quality.get('four_card_real_model_CPU_accepted') is False,'Real-model acceptance must be independently bound by the final stage controller')
    result=binding_blueprint(json.loads(a.manifest.read_text()),P1_binding=original,combination_acceptance=co,quality_readiness=quality)
    result.update(source_bindings=bindings,unverified_input_manifest_or_model_resources_cannot_dispatch=True)
    with a.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ('status','final_budget_determined','GPU_dispatch_ready')}))
if __name__=='__main__':main()
