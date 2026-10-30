"""Provision the frozen private S filesystem; no GPU authority or dispatch."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser()
    for name in ('project', 'stage'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--registration-sha256', required=True)
    parser.add_argument('--worker-sha256', required=True)
    args = parser.parse_args()
    secret = json.load(sys.stdin)['sudo_password']
    sys.path[:0] = [str(args.stage / 'src'), str(args.stage / 'scripts')]
    from wcomr.gpu_budget_pool_v2 import process_identity, sha
    from wcomr.history104_storage_r2 import FixedJournal, StorageGuard
    from wcomr.sq_s_execution_r2 import assets_current, require, validate_source
    from wcomr.sq_s_spec_r2 import RUN
    from wcomr.sq_s_stage_r2 import create

    require(sys.platform == 'linux' and os.environ.get('CUDA_VISIBLE_DEVICES') == ''
        and os.environ.get('NVIDIA_VISIBLE_DEVICES') == 'void', 'Native GPU-hidden preparation required')
    require(sha(__file__) == args.worker_sha256 and sha(args.stage / 'registration.json') == args.registration_sha256,
        'Published storage worker and original S registration required')
    bundle, registration = validate_source(args.project, args.stage)
    assets_current(args.project, args.stage)
    profile = bundle['execution_profile']
    host = profile['hosts'][registration['host']]
    image, output, journal = (Path(host[key]) for key in ('image_path', 'output_mount', 'journal_path'))
    contract_path = args.stage / 'history104-storage.json'
    require(not any((args.stage / name).exists() for name in
        ('GPU-intent.json', 'GPU-launch.json', 'GPU-dispatch-consumed.json')), 'Recover any original GPU handle first')
    if contract_path.exists():
        contract = json.loads(contract_path.read_text())
        require(contract['run_id'] == RUN and contract['image_path'] == str(image)
            and contract['output_mount'] == str(output) and contract['journal_path'] == str(journal),
            'Recover original S storage only')
        print(json.dumps(dict(status='S_ORIGINAL_STORAGE_RECOVERED_NO_GPU',
            check=StorageGuard(contract).check(), storage_contract_sha256=sha(contract_path), GPU_submissions=0)))
        return
    require(not (args.stage / 'S-storage-CPU-request.json').exists(), 'Partial original storage: recover without recreating')
    require(not any(path.exists() or path.is_symlink() for path in (image, output, journal)),
        'Existing storage paths require original recovery')
    require(image.name == RUN + '.img' and output == args.project / 'outputs' / RUN
        and journal == args.project / 'reports' / (RUN + '.control.journal'), 'Frozen private S storage paths required')
    require(image.parent.parent.is_dir() and output.parent.is_dir() and journal.parent.is_dir()
        and not image.parent.is_symlink() and not output.parent.is_symlink() and not journal.parent.is_symlink(),
        'Original owned storage parents required')
    image_bytes = profile['output_image_GiB'] * 2**30
    journal_bytes = profile['control_journal_MiB'] * 2**20
    host_margin = profile['minimum_storage_host_free_GiB'] * 2**30
    image_parent = image.parent if image.parent.exists() else image.parent.parent
    require(image_bytes == 32 * 2**30 and journal_bytes == 48 * 2**20
        and shutil.disk_usage(image_parent).free >= image_bytes + host_margin
        and shutil.disk_usage(journal.parent).free >= journal_bytes + host_margin
        and image_parent.stat().st_dev != journal.parent.stat().st_dev, 'Whole private storage and independent journal margin required')
    require({4, 5} <= os.sched_getaffinity(0), 'Original preparation CPU cores required')
    os.sched_setaffinity(0, {4, 5})
    os.nice(10)
    resource.setrlimit(resource.RLIMIT_AS, (2 * 2**30, 2 * 2**30))
    resource.setrlimit(resource.RLIMIT_CPU, (1800, 1800))
    resource.setrlimit(resource.RLIMIT_FSIZE, (image_bytes, image_bytes))
    def timed_out(signum, frame):
        raise TimeoutError('Original S storage preparation reached its 1800 second wall limit')
    signal.signal(signal.SIGALRM, timed_out)
    signal.alarm(1800)
    state = dict(status='S_STORAGE_CPU_RUNNING_NO_GPU', identity=process_identity(os.getpid()),
        started_unix=time.time(), host=registration['host'], stage=str(args.stage),
        registration_sha256=args.registration_sha256, worker_sha256=args.worker_sha256,
        image_path=str(image), output_mount=str(output), journal_path=str(journal),
        resources=dict(cpus=[4, 5], address_space_GiB=2, wall_seconds=1800, CPU_seconds=1800),
        GPU_submissions=0, ledger_writes=0, authorizes_retry=False)
    create(args.stage / 'S-storage-CPU-request.json', state)
    started = time.monotonic()
    try:
        image.parent.mkdir(mode=0o700, exist_ok=True)
        output.mkdir(mode=0o700)
        descriptor = os.open(image, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        try:
            os.posix_fallocate(descriptor, 0, image_bytes)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        subprocess.run(['/usr/sbin/mkfs.ext4', '-q', '-F', '-E',
            'nodiscard,lazy_itable_init=0,lazy_journal_init=0', '-m', '0', str(image)],
            capture_output=True, check=True, timeout=120)
        # mkfs can punch holes; restore the full reserved image before mounting.
        descriptor = os.open(image, os.O_RDWR)
        try:
            os.posix_fallocate(descriptor, 0, image_bytes)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        for command in (
            ['/usr/bin/mount', '-o', 'loop,nodev,nosuid,noexec', str(image), str(output)],
            ['/usr/bin/chown', str(os.getuid()) + ':' + str(os.getgid()), str(output)],
            ['/usr/bin/rmdir', str(output / 'lost+found')]):
            result = subprocess.run(['sudo', '-S', '-p', ''] + command, input=secret + '\n',
                capture_output=True, text=True, timeout=60)
            require(result.returncode == 0, 'Private S storage command failed: ' + command[0]
                + ': ' + result.stderr.replace(secret, '[REDACTED]')[-500:])
        FixedJournal(journal).create()
        contract = dict(version='HISTORY104_PRIVATE_STORAGE_R2', run_id=RUN, output_mount=str(output),
            output_device=output.stat().st_dev, image_path=str(image), image_inode=image.stat().st_ino,
            image_bytes=image_bytes, journal_path=str(journal), journal_bytes=journal_bytes,
            minimum_output_free_bytes=profile['minimum_output_free_MiB'] * 2**20,
            minimum_free_inodes=1024, minimum_host_free_bytes=host_margin,
            shared_disk_reserve_ratio_modified=False, reboot_remount_must_be_reverified=True)
        check = StorageGuard(contract).check()
        create(contract_path, contract)
        state.update(status='S_PRIVATE_STORAGE_CPU_PREPARED_NO_GPU', exit_code=0,
            storage_contract_sha256=sha(contract_path), storage_contract=contract, check=check)
    except BaseException as error:
        state.update(status='S_STORAGE_CPU_FAILED_PRESERVE_ORIGINAL_PATHS', exit_code=1,
            error_type=type(error).__name__, error=str(error).replace(secret, '[REDACTED]'))
        raise
    finally:
        state.update(wall_seconds=time.monotonic() - started, ended_unix=time.time())
        create(args.stage / 'S-storage-CPU-exit.json', state)
    print(json.dumps(state))


if __name__ == '__main__':
    main()
