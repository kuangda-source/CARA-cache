"""Join host-specific CPU proofs only when the production sources agree."""
import argparse
import hashlib
import json
from pathlib import Path

from audit_cara_sq_s_physical_cpu_r1 import accept, instant

ROOT=Path(__file__).resolve().parents[1]
DEST='plans/cara_next_stage_20261028/sq/'


def read(name):
    return json.loads((ROOT/name).read_text())


def sha(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise FileExistsError('Retain the original dual physical CPU receipt')
    configs=dict(two_card=('r2','reports/cara_sq_s_physical_two_card_cpu_accepted_r2_20261029.json'),
                 four_card=('r1','reports/cara_sq_s_physical_four_card_cpu_accepted_r1_20261029.json'))
    hosts={};proofs={};refs=[]
    for host,(attempt,name) in configs.items():
        proof=read(name);capture=read(proof['capture_ref'])
        if sha(proof['capture_ref'])!=proof['capture_sha256'] or not proof['passed']:
            raise ValueError('Original complete accepted CPU source differs: '+host)
        cpu_scope=DEST+'S_PHYSICAL_CPU_'+attempt.upper()+'.json'
        result=accept(capture,read(cpu_scope),proof['source_revision'],host,attempt)
        if result['resources']!=proof['resources'] or len(proof['rejection_controls'])!=8 or not all(proof['rejection_controls'].values()):
            raise ValueError('Independent terminal/cost/rejection acceptance differs: '+host)
        physical=read(DEST+'S_PHYSICAL_'+host.upper()+'_R1.json')
        if (proof['actual_heads_per_flow']!=physical['counts']['branch_readouts']
                or proof['actual_deep_blocks_per_flow']!=physical['counts']['deep_block_calls']):
            raise ValueError('The CPU matrix does not cover the registered host physical counts')
        hosts[host]=dict(accepted_ref=name,source_revision=proof['source_revision'],
            matrix_new_CPU_paths=proof['new_CPU_paths'],
            source_preparation_CPU_paths=proof['separately_prepared_tiny_OFF_source_paths'],
            imported_tiny_OFF_roles=proof['imported_tiny_OFF_roles'],
            actual_matrix_heads_per_flow=proof['actual_heads_per_flow'],
            extra_source_heads_per_flow=proof['source_fixture_head_calls_per_flow'],
            resources=proof['resources'],CPU_unit_controls=9,rejection_controls=8,
            synthetic_full93_MP4_decode=True,streamed_file_reloads=280)
        proofs[host]=proof;refs.extend([name,proof['capture_ref'],cpu_scope])
    shared={}
    for name,value in proofs['two_card']['critical_source_sha256'].items():
        production=name.startswith('src/') or name in [DEST+n for n in (
            'S_EXECUTION_IDENTITY_R1.json','S_RETAINED_OFF_WITNESS_R1.json',
            'S_PHYSICAL_TWO_CARD_R1.json','S_PHYSICAL_FOUR_CARD_R1.json','S_SUPPORT_RECONCILIATION_R2.json')]
        if production:
            if value!=proofs['four_card']['critical_source_sha256'].get(name) or value!=sha(name):
                raise ValueError('Common production source/binding differs: '+name)
            shared[name]=value
    old_failure='reports/cara_sq_s_physical_two_card_cpu_capture1_r1_20261029.json'
    failed_state=read(old_failure)['container_state']
    failed_wall=(instant(failed_state['FinishedAt'])-instant(failed_state['StartedAt'])).total_seconds()
    refs += [old_failure,'reports/cara_sq_s_tiny_fixture_qualification_r1_20261029.json',
        'reports/cara_sq_s_resource_native_copy_floor_r3_20261029.json',
        'reports/cara_sq_s_physical_two_card_status_read_recovery_r2_20261029.json']
    value=dict(status='S_PHYSICAL_DUAL_CPU_PREPARATION_ACCEPTED_REAL_GPU_CARD_INCOMPLETE',
        hosts=hosts,common_production_source_sha256=shared,
        original_A6000_R1_failure_retained=True,old_unbound_tiny_weights_not_reused=True,
        prior_A6000_R1_failure_resources=dict(container_wall_seconds=failed_wall,
            allocated_vCPU_seconds_upper_bound=2*failed_wall,worker_CPU_unmetered=True),
        combined_CPU_container_wall_seconds=failed_wall+sum(h['resources']['container_wall_seconds'] for h in hosts.values()),
        new_tiny_model_checkpoint_save_reload_and_value_digest_accepted=True,
        actual_real_retained_OFF_ref='reports/cara_sq_s_reuse_two_card_cpu_accepted_r2_20261029.json',
        real_OFF_ON_equivalence_accepted=False,complete_S_GPU_card_accepted=False,
        real_S_labels=0,S_mask=None,GPU_submissions=0,ledger_writes=0,
        evaluation_boundary='CPU implementation and synthetic decoder evidence only; no real video quality/speed/memory result',
        pending=['Fresh auxiliary model/request/runtime/backend asset binding and admission',
            'Remaining WC output/embedding, solver and buffer bounds; physical peak and complete copy/hash accounting',
            'Full GPU staging/lifecycle/once-only intent, storage and shared-budget terminal accounting',
            'Complete host-specific whole-card quotes and separate GPU authorization',
            'Real complete108-label collection and actual new-ON/original-OFF equivalence before S rule selection'],
        Q1_direct_human_approval_received=False,
        evidence_sha256={name:sha(name) for name in refs})
    with args.output.open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=value['status'],common_production_files=len(shared),
        actual_new_CPU_paths={h:r['matrix_new_CPU_paths'] for h,r in hosts.items()})))


if __name__=='__main__':main()
