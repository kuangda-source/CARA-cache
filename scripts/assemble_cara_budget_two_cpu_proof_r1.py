"""Compose existing complete CPU evidence for one unchanged published payload.

No remote access, production authority, ledger write, or GPU execution occurs.
GPU hardware and Docker device behavior remain fresh-dispatch boundaries.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'src'), str(ROOT/'scripts')]
from accept_cara_budget_calibration_cpu_r3 import accept as accept_r4, encoded_sha, require
from accept_cara_budget_private_rgb_cpu_r1 import accept as accept_rgb
from wcomr.cara_budget_host_policy_r1 import POLICY, POLICY_SHA256
from wcomr.cara_budget_prepare_r1 import EXTRA
from wcomr.cara_budget_dispatch_r1 import REQUIRED as DISPATCH_REQUIRED
from wcomr.cara_budget_runner_binding_r1 import REQUIRED, SPEC
from wcomr.immutable_stage_payload_r1 import git_archive, overlay_bytes

REVISION = 'cc5f38a1233d565158783e3152c06c58516d633b'
R4 = 'reports/cara_budget_current_CPU_two_R4_accepted_r1_20261031.json'
POLICY_ACCEPTED = 'reports/cara_budget_two_card_policy_CPU_accepted_r1_20261031.json'
CHILD = 'reports/cara_budget_dispatch_child_CPU_accepted_r1_20261031.json'
RGB = 'reports/cara_budget_private_RGB_CPU_accepted_r1_20261031.json'
STORAGE = 'reports/cara_budget_two_card_private_storage_accepted_r1_20261031.json'
CLEANUP = 'reports/cara_budget_private_RGB_fixture_cleanup_r1_20261031.json'


def read(name):
    return json.loads((ROOT/name).read_text())


def sha(name):
    return hashlib.sha256((ROOT/name).read_bytes()).hexdigest()


def compose():
    r4 = read(R4)
    package = ROOT/'.sync/cara-budget-two-R4-published-source-20261031'
    rebuilt = accept_r4(read(r4['capture_ref'])['result'], read(r4['original_launch_ref'])['result'],
        json.loads((package/'source-plan.json').read_text()),
        json.loads((package/'base-registration.json').read_text()), r4['source_revision'],
        published_bytes=lambda name: subprocess.check_output(['git', 'show', r4['source_revision']+':'+name], cwd=ROOT),
        package_receipt=read('reports/cara_budget_two_R4_published_source_r1_20261031.json'))
    require(all(r4[k] == value for k, value in rebuilt.items() if k != 'observed_unix'), 'R4 acceptance changed')
    require(sha(r4['capture_ref']) == r4['capture_sha256'] and
            sha(r4['original_launch_ref']) == r4['original_launch_sha256'], 'R4 receipt bytes changed')
    # Re-run only offline acceptance over original captures, never the remote tests.
    for ref, script in [(POLICY_ACCEPTED, 'accept_cara_budget_two_card_policy_cpu_r1.py'),
                        (CHILD, 'accept_cara_budget_dispatch_child_cpu_r1.py')]:
        saved = read(ref)
        require(sha(saved['capture_ref']) == saved['capture_sha256'] and
                sha(saved['launch_ref']) == saved['launch_sha256'], 'Original component receipt bytes changed')
        require(sha('scripts/'+script) == saved['acceptor_sha256'], 'Original component acceptor changed')
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary)/'accepted.json'
            subprocess.run([sys.executable, str(ROOT/'scripts'/script), '--capture', saved['capture_ref'],
                '--launch', saved['launch_ref'], '--output', str(target)], cwd=ROOT,
                check=True, capture_output=True, env={**__import__('os').environ, 'PYTHONPATH': str(ROOT/'src')})
            result = json.loads(target.read_text())
        require(all(saved[k] == v for k, v in result.items() if k != 'observed_unix'), 'Original component acceptance changed')
    policy = read(POLICY_ACCEPTED)
    cap = read(policy['capture_ref'])['result']
    reg = cap['registration']
    require(reg['parent_git_revision'] == REVISION and encoded_sha(reg) == cap['registration_sha256'], 'Final registration changed')
    payload = reg['payload_sha256']
    require(all(sha(n) == h for n, h in payload.items()), 'Accepted final payload changed')
    require(set(REQUIRED)|set(DISPATCH_REQUIRED)|set(EXTRA) <= set(payload), 'Whole production closure incomplete')
    require(payload[POLICY] == POLICY_SHA256, 'Two-card restriction changed')
    changed = {n for n,h in r4['payload_sha256'].items() if payload.get(n) != h}
    require(changed <= set(policy['overlay_sha256']), 'Unaccepted production source delta')
    require(all(payload[n] == h for n,h in policy['overlay_sha256'].items()), 'Affected policy source changed')
    card = read(SPEC)
    require(card['scope_sha256'] == r4['scope_sha256'], 'Full112/51 scope changed')
    io = read(RGB)
    require(sha(io['capture_ref']) == io['capture_sha256'], 'IO capture changed')
    io_rebuilt = accept_rgb(read(io['capture_ref']))
    require(all(io[k] == v for k,v in io_rebuilt.items() if k != 'observed_unix'), 'IO acceptance changed')
    storage, cleanup = read(STORAGE), read(CLEANUP)
    require(storage['actual_storage_accepted'] and storage['storage_contract'] == io['storage_contract']
            and storage['provision_sha256'] == io['provision_sha256'], 'Actual private storage differs')
    require(cleanup['exit_code'] == 0 and cleanup['result']['output_empty'] and cleanup['result']['journal_pristine']
            and cleanup['result']['proof_sha256'] == io['CPU_proof_sha256'], 'Accepted synthetic IO cleanup incomplete')
    refs = [R4, POLICY_ACCEPTED, CHILD, RGB, STORAGE, CLEANUP]
    evidence = {ref: sha(ref) for ref in refs}
    proof = dict(status='COMPOSED_TWO_CARD_WHOLE_CPU_ACCEPTED_NOT_GPU_AUTHORIZED', observed_unix=time.time(),
        passed=True, whole_card_CPU_accepted=True, host='two_card', source_revision=REVISION,
        scope_sha256=card['scope_sha256'], payload_sha256=payload,
        runtime_source_sha256=reg['runtime_source_sha256'], required_host_whole_card_CPU_accepted=True,
        execution_host_policy_sha256=POLICY_SHA256, required_hosts=['two_card'],
        host_receipts={'two_card': dict(whole_card_CPU_accepted=True, scope_sha256=card['scope_sha256'],
            payload_sha256=payload, evidence_sha256=evidence)}, evidence_sha256=evidence,
        complete_design_paths=224, complete_two_FIT_objectives=102, original_execution_controls=134,
        original_spec_controls=3, affected_policy_and_real_child_controls=43,
        actual_64GiB_storage_exercised=True, full93_private_RGB_IO_accepted=True,
        dispatcher_child_spawn_exercised=True, real_Docker_GPU_lifecycle_exercised=False,
        GPU_model_execution_exercised=False, CPU_numeric_geometry='FULL93_FRAMES_SMALL_SPATIAL_SYNTHETIC_MODEL',
        IO_geometry=[3,93,432,768], acceptance_mode='ORIGINAL_COMPLETE_MATRIX_PLUS_EXACT_AFFECTED_DELTA_NO_RERUN',
        GPU_dispatch_ready=False, execution_authorized=False, GPU_submissions=0, ledger_written=False,
        four_card_contacted=False,
        fresh_dispatch_boundaries=['Current GPU/runtime/assets and sole-runner exclusivity',
            'Remount/storage identity and empty original output', 'Single authoritative central ledger and all original intents',
            'Direct single14GPUh approval and whole quote binding'])
    plan = dict(status='CALIBRATION_SOURCE_PLAN_NO_GPU_AUTHORITY', overlay_sha256=payload,
        base_registration_sha256=cap['registration_sha256'], base_source_revision=REVISION,
        base_revision_field='parent_git_revision', GPU_submissions=0, execution_authorized=False)
    archive = git_archive(ROOT, plan, REVISION)
    require(set(overlay_bytes(archive, plan)) == set(payload), 'Frozen Git payload incomplete')
    return proof, plan, reg, archive


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--package', type=Path, required=True)
    args = parser.parse_args()
    require(not args.output.exists() and not args.package.exists(), 'Fresh local package and proof required')
    proof, plan, reg, archive = compose()
    args.package.mkdir(mode=0o700)
    for name, value in [('source-plan.json', plan), ('base-registration.json', reg)]:
        (args.package/name).write_text(json.dumps(value, indent=2)+'\n')
    (args.package/'source.tar.gz').write_bytes(archive)
    proof.update(package_ref=str(args.package), package_plan_sha256=encoded_sha(plan),
        package_archive_sha256=hashlib.sha256(archive).hexdigest(),
        assembler_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    with args.output.open('x') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=proof['status'], source_revision=REVISION, payload_files=len(proof['payload_sha256']))))


if __name__ == '__main__':
    main()
