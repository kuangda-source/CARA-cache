"""Bind the actual production selector on every frozen S policy's causal slots."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def build(scope,contract):
    import torch
    from wcomr.policy_generator_r1.production_sampling import PolicyOwner,validate_policy
    from wcomr.sq_s_risk_post_r3 import domain,C_policy
    from wcomr.sq_s_data_terminal_r2 import require
    profile,candidates,baselines=domain(scope,contract)
    sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    require(sha(ROOT/'src/wcomr/policy_generator_r1/production_sampling.py')==contract['legacy_source_sha256']['production_sampling'],
        'Original production selector source differs')
    policies={policy['fingerprint']:policy for policy in baselines.values()}
    policies.update({row['policy_fingerprint']:C_policy(profile,row['dense']) for row in candidates})
    selected_histories=set();pairs=0
    for policy in policies.values():
        validate_policy(profile,policy)
        owner=SimpleNamespace(force_dense=False,policy=policy,profile=profile,fallback_reason=None,
            readout=SimpleNamespace(completed=0,calibrators=[SimpleNamespace(anchors=[]) for _ in (0,1)]))
        for step,action in enumerate(policy['actions'],1):
            owner.readout.completed=step-1
            actual=PolicyOwner._choose(owner,None);pairs+=1
            require(actual==('DD' if action=='D' else 'CC') and owner.fallback_reason is None,
                'Original production selector lacks true-D slots for a frozen S policy')
            if action=='D':
                for branch in owner.readout.calibrators:branch.anchors=(branch.anchors+[SimpleNamespace(step=step)])[-2:]
            else:
                past=[anchor.step for anchor in owner.readout.calibrators[0].anchors]
                require(len(past)==2 and past[-1]<step
                    and all([anchor.step for anchor in branch.anchors]==past for branch in owner.readout.calibrators),
                    'Both branches require the same strictly causal true-D slots')
                selected_histories.add((step,*past))
    require(not torch.cuda.is_initialized(),'Selector/history preparation must never initialize CUDA')
    expected=sorted({tuple(value) for row in candidates for value in row['history']})
    require(set(expected)<=selected_histories,'Original candidate history coverage missing')
    return dict(schema='S_FROZEN_PRODUCTION_SELECTOR_HISTORY_CPU_R3',status='S_SELECTOR_HISTORY_SLOTS_CPU_PASS',
        rule_sha256=contract['rule_sha256'],production_source_sha256=contract['legacy_source_sha256']['production_sampling'],
        producer_sha256=sha(Path(__file__)),candidate_policy_fingerprints=[row['policy_fingerprint'] for row in candidates],
        supported_C_histories=[list(row) for row in sorted(selected_histories)],checked_distinct_policies=len(policies),
        checked_policy_fingerprints=sorted(policies),
        checked_selector_pairs=pairs,history_slots_are_controlled_CPU_objects=True,
        actual_model_forward_calls=0,CUDA_initialized=False,free_running_or_endpoint_acceptance=False,
        GPU_submissions=0,ledger_writes=0)


def main():
    p=argparse.ArgumentParser()
    for name in ('scope','contract','output'):p.add_argument('--'+name,type=Path,required=True)
    args=p.parse_args()
    if args.output.exists():raise FileExistsError('Preserve original S history-support preparation')
    if os.environ.get('CUDA_VISIBLE_DEVICES')!='' or os.environ.get('NVIDIA_VISIBLE_DEVICES')!='void':
        raise ValueError('S selector/history preparation must hide all GPUs')
    result=build(json.loads(args.scope.read_text()),json.loads(args.contract.read_text()))
    with args.output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({key:result[key] for key in ('status','checked_distinct_policies','checked_selector_pairs')}))


if __name__=='__main__':main()
