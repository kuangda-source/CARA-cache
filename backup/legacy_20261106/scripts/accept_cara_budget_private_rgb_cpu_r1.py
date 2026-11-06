"""Accept one original private-volume RGB CPU probe, never a GPU quote."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def accept(capture):
    assert capture['exit_code'] == 0 and capture['host'] == 'two_card'
    r = capture['result']
    state = r['container_state']
    assert state['Status'] == 'exited' and state['ExitCode'] == 0
    assert not any(state[k] for k in ('Running', 'OOMKilled', 'Dead', 'Restarting'))
    assert r['payload_intact'] and r['runtime_intact']
    assert r['host_config'] == dict(NanoCpus=10**9, Memory=4*2**30, MemorySwap=4*2**30,
        CpusetCpus='', DeviceRequests=None, NetworkMode='none', ReadonlyRootfs=True)
    reg = r['registration']
    reg_sha = hashlib.sha256((json.dumps(reg, indent=2)+'\n').encode()).hexdigest()
    assert reg_sha == r['registration_sha256'] == r['launch']['registration_sha256']
    assert reg['parent_git_revision'] == capture['source_revision']
    worker = 'scripts/check_cara_budget_private_RGB_io_r1.py'
    raw = subprocess.check_output(['git', 'show', capture['source_revision']+':'+worker], cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest() == reg['payload_sha256'][worker]
    proof = r['CPU_proof']
    assert hashlib.sha256((json.dumps(proof, indent=2)+'\n').encode()).hexdigest() == r['CPU_proof_sha256']
    assert proof['status'] == 'PRIVATE64_FULL93_RGB_CACHE_CONTROLLED_CPU_COMPLETE_NOT_GPU'
    assert proof['registration_sha256'] == reg_sha and proof['source_revision'] == capture['source_revision']
    storage = json.loads((ROOT/'reports/cara_budget_two_card_private_storage_accepted_r1_20261031.json').read_text())
    assert proof['provision_sha256'] == storage['provision_sha256']
    assert proof['storage_contract'] == storage['storage_contract']
    c = proof['storage_contract']
    mounts = {row['Destination']: row for row in r['container_mounts']}
    for path, writable in [(c['output_mount'], True), (str(Path(c['image_path']).parent), False),
                           (str(Path(c['journal_path']).parent), False)]:
        assert mounts[path]['Type'] == 'bind' and mounts[path]['RW'] == writable
    assert proof['RGB_shape'] == [3, 93, 432, 768] and proof['retained_NPY_bytes'] == 740524288
    assert proof['synthetic_RGB_MSE'] == .25**2/(3*93*432*768)
    assert len(proof['NPY_residency_before_cold_read']) == 2
    assert all(v['resident_pages'] == 0 and v['total_pages'] > 0 for v in proof['NPY_residency_before_cold_read'].values())
    assert proof['cold_file_pages_established'] and proof['private_file_cache_eviction_only']
    assert not any(proof[k] for k in ('universal_cold_disk_bound_established', 'real_model_output',
        'GPU_to_CPU_copy_measured', 'GPU_submissions', 'ledger_written', 'whole_GPU_quote_accepted'))
    assert proof['ended_unix']-proof['started_unix'] < 180 and proof['peak_RSS_bytes'] < 4*2**30
    return dict(status='TWO_CARD_PRIVATE64_FULL93_RGB_CPU_IO_ACCEPTED', observed_unix=time.time(),
        source_revision=capture['source_revision'], launch=r['launch'], container_state=state,
        host_config=r['host_config'], container_mounts=r['container_mounts'],
        CPU_proof_sha256=r['CPU_proof_sha256'], storage_contract=c,
        provision_sha256=proof['provision_sha256'], measurement=proof,
        actual_private_storage_accepted=True, private_full_RGB_IO_accepted=True,
        universal_cold_disk_bound_established=False, GPU_to_CPU_copy_measured=False,
        whole_GPU_quote_accepted=False, GPU_dispatch_ready=False, GPU_submissions=0, ledger_written=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    raw = args.capture.read_bytes()
    result = accept(json.loads(raw))
    result.update(capture_ref=str(args.capture), capture_sha256=hashlib.sha256(raw).hexdigest())
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(status=result['status'], measurement={k:v for k,v in result['measurement'].items() if k.endswith('_seconds')})))


if __name__ == '__main__':
    main()
