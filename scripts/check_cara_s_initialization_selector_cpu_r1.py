"""Original production selector on the two fixed initialization domains, CPU only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time
from types import SimpleNamespace

CONTRACT = 'plans/cara_next_stage_20261028/mainline/r2/S_INITIALIZATION_SELECTOR_CPU_R1_20261031.json'


def main():
    parser = argparse.ArgumentParser()
    for name in ('runtime', 'stage', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--host', required=True)
    args = parser.parse_args()
    assert args.host == 'two_card' and not args.output.exists()
    assert os.environ['CUDA_VISIBLE_DEVICES'] == '' and os.environ['NVIDIA_VISIBLE_DEVICES'] == 'void'
    assert os.sched_getaffinity(0) == {26}
    signal.alarm(180)
    started = time.time()
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    registration = json.loads((args.stage/'registration.json').read_text())
    assert all(sha(args.stage/p) == h for p,h in registration['payload_sha256'].items())
    assert all(sha(args.runtime/p) == h for p,h in registration['runtime_source_sha256'].items())
    contract = json.loads((args.stage/CONTRACT).read_text())
    assert args.stage.name == contract['stage_name']
    assert all(sha(args.stage/p) == h for p,h in contract['production_source_sha256'].items())
    sys.path[:0] = [str(args.stage/'src'), str(args.runtime), str(args.runtime/'packages/cosmos-oss'),
                   str(args.runtime/'packages/cosmos-cuda')]
    from wcomr.cara_s_initialization_audit_r1 import audit
    from wcomr.cara_fast_spec_r1 import digest, profile_from, policy_from_mask
    risk = {j:{int(k):v for k,v in rows.items()} for j,rows in contract['risk'].items()}
    diagnostic = audit(contract['profile'], contract['baselines'], risk,
                       contract['original_choices'], contract['original_candidate_count'])
    assert digest(diagnostic) == contract['expected_audit_digest']
    import torch
    torch.set_num_threads(1)

    def forbidden(*args, **kwargs):
        raise AssertionError('No CUDA initialization or model weight loading in selector CPU check')

    torch.cuda.init = forbidden
    torch.cuda._lazy_init = forbidden
    torch.load = forbidden
    from wcomr.policy_generator_r1.production_sampling import PolicyOwner, validate_policy
    profile = profile_from(contract['profile'])
    policies = {}
    for origin in diagnostic['origins'].values():
        for dense in [origin['initial_dense']] + [row['dense'] for row in origin['candidates']]:
            policy = policy_from_mask(profile, dense)
            policies[policy['fingerprint']] = policy
    supported, pairs, branch_checks = set(), 0, 0
    for policy in policies.values():
        validate_policy(profile, policy)
        owner = SimpleNamespace(force_dense=False, policy=policy, profile=profile, fallback_reason=None,
            readout=SimpleNamespace(completed=0, calibrators=[SimpleNamespace(anchors=[]) for _ in (0,1)]))
        for step, action in enumerate(policy['actions'], 1):
            owner.readout.completed = step-1
            actual = PolicyOwner._choose(owner, None)
            pairs += 1
            assert actual == ('DD' if action == 'D' else 'CC') and owner.fallback_reason is None
            if action == 'D':
                for branch in owner.readout.calibrators:
                    branch.anchors = (branch.anchors+[SimpleNamespace(step=step)])[-2:]
            else:
                past = [a.step for a in owner.readout.calibrators[0].anchors]
                assert len(past) == 2 and past[0] < past[1] < step
                assert all([a.step for a in branch.anchors] == past for branch in owner.readout.calibrators)
                assert step-past[-1] <= profile.max_source_age
                supported.add((step, *past))
                branch_checks += 2
    assert set(map(tuple, contract['expected_additional_histories'])) <= supported
    assert len(contract['expected_additional_histories']) == 138
    # The real selector must reject a missing/future anchor in either branch.
    policy = policy_from_mask(profile, contract['baselines']['Uniform19_C'])
    step = next(i for i,a in enumerate(policy['actions'],1) if a == 'C')
    refused = []
    for branch in (0,1):
        for reason in ('missing', 'future'):
            anchors = [[SimpleNamespace(step=6), SimpleNamespace(step=7)] for _ in (0,1)]
            anchors[branch] = anchors[branch][:1] if reason == 'missing' else [SimpleNamespace(step=6), SimpleNamespace(step=step)]
            owner = SimpleNamespace(force_dense=False, policy=policy, profile=profile, fallback_reason=None,
                readout=SimpleNamespace(completed=step-1, calibrators=[SimpleNamespace(anchors=a) for a in anchors]))
            assert PolicyOwner._choose(owner,None) == 'DD' and owner.fallback_reason == 'INSUFFICIENT_TRUE_D_ANCHORS'
            refused.append(dict(branch=branch, reason=reason))
    owner.force_dense = True
    owner.fallback_reason = None
    assert PolicyOwner._choose(owner,None) == 'DD'
    assert not torch.cuda.is_initialized()
    proof = dict(status='S_TWO_INITIALIZATIONS_PRODUCTION_SELECTOR_CPU_COMPLETE_NOT_ENDPOINT', host=args.host,
        started_unix=started, ended_unix=time.time(), registration_sha256=sha(args.stage/'registration.json'),
        source_revision=registration['parent_git_revision'], contract_sha256=sha(args.stage/CONTRACT),
        diagnostic_digest=digest(diagnostic), production_source_sha256=contract['production_source_sha256'],
        checked_distinct_policies=len(policies), checked_policy_fingerprints=sorted(policies),
        checked_selector_pairs=pairs, checked_C_branch_histories=branch_checks,
        supported_C_histories=[list(row) for row in sorted(supported)],
        additional_histories_verified=contract['expected_additional_histories'],
        anchor_mutations_refused=refused, forced_dense_verified=True,
        actual_CPU_affinity=sorted(os.sched_getaffinity(0)), torch_version=torch.__version__,
        CUDA_initialized=False, controlled_CPU_anchor_objects=True, actual_model_forward_calls=0,
        original_S_freeze_changed=False, free_running_or_endpoint_acceptance=False,
        GPU_submissions=0, ledger_written=False)
    with args.output.open('x') as stream:
        json.dump(proof, stream, indent=2, allow_nan=False)
        stream.write('\n')
    signal.alarm(30)
    print(json.dumps({k:proof[k] for k in ('status','checked_distinct_policies','checked_selector_pairs')}), flush=True)


if __name__ == '__main__':
    main()
