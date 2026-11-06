"""Construct the original full P1 command and scoped caches; never execute it."""
from pathlib import Path
import re

from cara_fast_host_guardian_r2 import container_arguments as original_container_arguments
from wcomr.cara_source_lifecycle_p1_runner_binding_r1 import RUN_ID,STAGE_NAME,GPU,validate_profile

SOURCE='scripts/cara_source_lifecycle_p1_container_r1.py'
WORKER='scripts/cara_source_lifecycle_p1_supervisor_worker_r1.py'


def container_arguments(*,project,stage,storage,registration_sha,profile,host,run_id,uuid,uid,gid):
    project,stage=Path(project),Path(stage)
    if (not project.is_absolute() or stage.parent!=project/'.sync' or stage.name!=STAGE_NAME
            or run_id!=RUN_ID or host!='two_card' or uuid!=GPU
            or not re.fullmatch('[0-9a-f]{64}',registration_sha)
            or type(uid) is not int or uid<=0 or type(gid) is not int or gid<=0):
        raise ValueError('Exact original full146 P1 two-card stage/UUID/non-root owner required')
    validate_profile(profile,profile['scope_sha256'])
    config,limits=storage.config,profile['storage']
    if (storage.output!=project/'outputs'/RUN_ID or config['output_mount']!=str(storage.output)
            or config['image_bytes']!=limits['output_image_bytes']
            or config['journal_bytes']!=limits['independent_journal_bytes']
            or config['journal_path']!=str(storage.journal.path)
            or any(config[k]<limits[k] for k in ('minimum_output_free_bytes','minimum_host_free_bytes','minimum_free_inodes'))):
        raise ValueError('Whole64GiB output/independent48MiB journal and original margins required')
    mounts=(project,stage,storage.output,storage.journal.path,Path(config['image_path']))
    if any(not p.is_absolute() or '..' in p.parts or any(c in str(p) for c in (':','\n')) for p in mounts):
        raise ValueError('Exact isolated absolute P1 bind mounts required')
    resources=profile['GPU_container']
    command=original_container_arguments(project,stage,storage,registration_sha,
        profile['hosts'][host]['cpuset_cpus'],uid,gid,uuid,resources['memory_GiB'])
    entry=command.index('--entrypoint')
    if command[entry+2]!=resources['image']:
        raise ValueError('Original pinned container image differs')
    worker=command.index(str(stage/'scripts/cara_fast_worker_r2.py'))
    if command[worker+1]!='supervise':raise ValueError('Original supervisor command shape differs')
    command[worker:worker+2]=[str(stage/WORKER)]
    command[entry:entry]=['--cidfile',str(stage/'container.cid'),
        '-v',str(stage/'src')+':'+str(stage/'src')+':ro',
        '-v',str(stage/'scripts')+':'+str(stage/'scripts')+':ro']
    return command
