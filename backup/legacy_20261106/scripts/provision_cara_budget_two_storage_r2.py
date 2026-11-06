"""One private two-card volume and independent journal; no GPU or ledger access."""
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import time

ROOT = Path('/data20t/gaokuangda/worldcache_workspace')
CONTROL = ROOT/'.sync/cara-budget-storage-provision-two-r3-20261031'
BASE = ROOT/'.sync/storage-reservations/budget-calibration-r2'
RUN = 'cara-budget-calibration-14gpuh-r2-20261031'
OUTPUT = ROOT/'outputs'/RUN
IMAGE = BASE/'output.ext4'
JOURNAL_DIR = Path('/home/gaokuangda/cara_control/budget-calibration-r2')
JOURNAL = JOURNAL_DIR/'control.journal'
CPU_STAGE = ROOT/'.sync/cara-budget-two-card-policy-CPU-a6000-r1-20261031'
HELPER = CPU_STAGE/'src/wcomr/history104_storage_r2.py'
HELPER_SHA = '90636ca74f1ae88db5ed1b8478f6aef8f83fd57db827db04da2e4d58a48c1361'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_state(value):
    target = CONTROL/'state.json'
    temporary = CONTROL/'state.tmp'
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, target)


def preflight():
    assert all(not p.exists() and not p.is_symlink() for p in (BASE, OUTPUT, JOURNAL_DIR))
    assert BASE.parent.is_dir() and OUTPUT.parent.is_dir() and JOURNAL_DIR.parent.is_dir()
    assert all(not p.is_symlink() and p.stat().st_uid == os.getuid()
               for p in (BASE.parent, OUTPUT.parent, JOURNAL_DIR.parent))
    assert ROOT.stat().st_dev != JOURNAL_DIR.parent.stat().st_dev
    assert shutil.disk_usage(ROOT).free >= 80*2**30
    assert shutil.disk_usage(JOURNAL_DIR.parent).free >= 2*2**30
    memory = int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines()
                      if l.startswith('MemAvailable:')))*1024
    assert memory >= 4*2**30
    return dict(data_free_bytes=shutil.disk_usage(ROOT).free,
        journal_free_bytes=shutil.disk_usage(JOURNAL_DIR.parent).free, MemAvailable_bytes=memory,
        data_device=ROOT.stat().st_dev, journal_device=JOURNAL_DIR.parent.stat().st_dev)


def main():
    assert os.getuid() != 0 and Path('/proc/self').exists()
    registration = json.loads((CONTROL/'registration.json').read_text())
    assert registration['operator_sha256'] == sha(__file__) and sha(HELPER) == HELPER_SHA
    assert not (CONTROL/'state.json').exists(), 'Original provisioning exists; capture, never replay'
    sys.path.insert(0, str(CPU_STAGE/'src'))
    from wcomr.history104_storage_r2 import FixedJournal, StorageGuard
    from wcomr.cara_budget_original_handles_r1 import bind_original_process
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('Provisioning wall limit')))
    signal.alarm(300)
    resource.setrlimit(resource.RLIMIT_AS, (2*2**30, 2*2**30))
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    os.nice(10)
    state = dict(status='TWO_CARD_PRIVATE_STORAGE_PREPARING_NO_GPU', started_unix=time.time(),
        identity=bind_original_process(os.getpid()), source_revision=registration['source_revision'],
        operator_sha256=registration['operator_sha256'], helper_sha256=HELPER_SHA,
        steps=[], GPU_submissions=0, ledger_written=False)
    write_state(state)
    password = None
    try:
        incoming = json.load(sys.stdin)
        password = incoming['sudo_password']
        assert isinstance(password, str) and password
        launch = json.loads((CONTROL/'launch.json').read_text())
        assert launch['identity'] == state['identity'], 'Only the original launched process may provision'
        state['fresh_resources'] = preflight()

        def step(name):
            state['steps'].append(dict(name=name, unix=time.time()))
            write_state(state)

        def sudo(arguments):
            result = subprocess.run(['sudo', '-S', '-p', '']+arguments, input=password+'\n',
                                    text=True, capture_output=True, timeout=45)
            if result.returncode:
                raise RuntimeError('Private storage operation failed: '+arguments[0])

        BASE.mkdir(mode=0o700)
        OUTPUT.mkdir(mode=0o700)
        JOURNAL_DIR.mkdir(mode=0o700)
        step('PRIVATE_DIRECTORIES_CREATED')
        fd = os.open(IMAGE, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            os.posix_fallocate(fd, 0, 64*2**30)
            os.fsync(fd)
        finally:
            os.close(fd)
        step('FULL64_GIB_BACKING_RESERVED')
        subprocess.run(['/usr/sbin/mkfs.ext4', '-q', '-F', '-E',
            'nodiscard,lazy_itable_init=0,lazy_journal_init=0', '-m', '0', str(IMAGE)],
            check=True, capture_output=True, timeout=90)
        # Retain physical reservation after filesystem creation.
        fd = os.open(IMAGE, os.O_RDWR | os.O_NOFOLLOW)
        try:
            os.posix_fallocate(fd, 0, 64*2**30)
            os.fsync(fd)
        finally:
            os.close(fd)
        step('EXT4_FORMATTED_AND_RESERVATION_VERIFIED')
        sudo(['/usr/bin/mount', '-o', 'loop,nodev,nosuid,noexec', str(IMAGE), str(OUTPUT)])
        sudo(['/usr/bin/chown', str(os.getuid())+':'+str(os.getgid()), str(OUTPUT)])
        sudo(['/usr/bin/rmdir', str(OUTPUT/'lost+found')])
        step('PRIVATE_FILESYSTEM_MOUNTED')
        FixedJournal(JOURNAL).create()
        config = dict(version='HISTORY104_PRIVATE_STORAGE_R2', run_id=RUN,
            output_mount=str(OUTPUT), output_device=OUTPUT.stat().st_dev,
            image_path=str(IMAGE), image_inode=IMAGE.stat().st_ino, image_bytes=64*2**30,
            journal_path=str(JOURNAL), journal_bytes=48*2**20,
            minimum_output_free_bytes=4*2**30, minimum_free_inodes=1024,
            minimum_host_free_bytes=128*2**20, shared_disk_reserve_ratio_modified=False,
            reboot_remount_must_be_reverified=True)
        probe = OUTPUT/'.CPU-storage-admission-probe'
        content = bytes(range(256))*4096
        expected = hashlib.sha256(content).hexdigest()
        with probe.open('xb') as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        assert sha(probe) == expected
        probe.unlink()
        assert list(OUTPUT.iterdir()) == []
        checked = StorageGuard(config).check()
        with JOURNAL.open('rb') as stream:
            assert all(block == bytes(len(block)) for block in iter(lambda: stream.read(2**20), b''))
        result = dict(status='TWO_CARD_PRIVATE64_STORAGE_PROVISIONED_NO_GPU',
            observed_unix=time.time(), storage_contract=config, check=checked,
            journal_pristine=True, persistence_probe_bytes=len(content), persistence_probe_sha256=expected, persistence_probe_removed=True, image_allocated_bytes=IMAGE.stat().st_blocks*512,
            journal_allocated_bytes=JOURNAL.stat().st_blocks*512,
            findmnt=json.loads(subprocess.check_output(['findmnt', '-J', str(OUTPUT)], text=True)),
            source_revision=registration['source_revision'], operator_sha256=sha(__file__),
            helper_sha256=HELPER_SHA, GPU_submissions=0, ledger_written=False)
        with (BASE/'provision.json').open('x') as stream:
            json.dump(result, stream, indent=2)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        step('STORAGE_GUARD_AND_PRISTINE_JOURNAL_ACCEPTED')
        state.update(status=result['status'], result=result)
    except BaseException as error:
        state.update(status='TWO_CARD_PRIVATE_STORAGE_ORIGINAL_FAILURE_NO_REPLAY',
                     error_type=type(error).__name__, error=str(error))
        raise
    finally:
        password = None
        state['ended_unix'] = time.time()
        write_state(state)
        signal.alarm(0)


if __name__ == '__main__':
    main()
