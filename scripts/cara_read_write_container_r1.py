"""Build the exact full14 M1 container command without executing it."""
from pathlib import Path
import re

from cara_fast_host_guardian_r2 import container_arguments as original_container_arguments
from wcomr.cara_read_write_runner_binding_r1 import PROFILE, validate_profile

WORKER = 'scripts/cara_read_write_supervisor_worker_r1.py'


def container_arguments(*, project, stage, storage, registration_sha, profile, host, run_id, uuid, uid, gid):
    project, stage = Path(project), Path(stage)
    if (not project.is_absolute() or stage.parent != project/'.sync'
            or not stage.name.startswith('cara-read-write-M1-GPU-')
            or not re.fullmatch('cara-read-write-M1-[a-z0-9-]+', run_id)
            or not re.fullmatch('[0-9a-f]{64}', registration_sha)
            or uuid != 'GPU-cebf7119-cf03-23b9-e192-cd196332b704' or host != 'two_card'
            or type(uid) is not int or uid <= 0 or type(gid) is not int or gid <= 0):
        raise ValueError('Original M1 absolute stage, two-card UUID and non-root owner required')
    validate_profile(profile, profile['scope_sha256'])
    config, limits = storage.config, profile['storage']
    if (storage.output != project/'outputs'/run_id or config['output_mount'] != str(storage.output)
            or config['image_bytes'] != limits['output_image_bytes']
            or config['journal_bytes'] != limits['independent_journal_bytes']
            or config['journal_path'] != str(storage.journal.path)
            or any(config[k] < limits[k] for k in
                ('minimum_output_free_bytes', 'minimum_host_free_bytes', 'minimum_free_inodes'))):
        raise ValueError('Original16GiB M1 output and independent48MiB journal contract differs')
    paths = (project, stage, storage.output, storage.journal.path, Path(config['image_path']))
    if any(not p.is_absolute() or '..' in p.parts or ':' in str(p) or '\n' in str(p) for p in paths):
        raise ValueError('Exact absolute bind-mount paths required')
    resources = profile['GPU_container']
    command = original_container_arguments(project, stage, storage, registration_sha,
        profile['hosts'][host]['cpuset_cpus'], uid, gid, uuid, resources['memory_GiB'])
    entry = command.index('--entrypoint')
    if command[entry+2] != resources['image']:
        raise ValueError('Original pinned container image differs')
    worker = command.index(str(stage/'scripts/cara_fast_worker_r2.py'))
    if command[worker+1] != 'supervise':
        raise ValueError('Original supervisor command shape differs')
    command[worker:worker+2] = [str(stage/WORKER)]
    command[entry:entry] = ['--cidfile', str(stage/'container.cid'),
        '-v', str(stage/'src')+':'+str(stage/'src')+':ro',
        '-v', str(stage/'scripts')+':'+str(stage/'scripts')+':ro']
    return command
