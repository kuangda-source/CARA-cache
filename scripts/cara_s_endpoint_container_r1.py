"""Build the prospective endpoint command; never execute or reserve a GPU."""
from pathlib import Path
import re

from cara_fast_host_guardian_r2 import container_arguments as original_container_arguments

PROFILE='configs/cara_endpoint_container_profile.json'
WORKER='scripts/cara_s_endpoint_supervisor_worker_r1.py'


def container_arguments(*,project,stage,storage,registration_sha,profile,host,run_id,uuid,uid,gid):
    project,stage=Path(project),Path(stage)
    if (not project.is_absolute() or stage.parent!=project/'.sync'
            or not stage.name.startswith('cara-S-endpoint-GPU-')
            or not re.fullmatch('cara-S-endpoint-[a-z0-9-]+',run_id)
            or not re.fullmatch('[0-9a-f]{64}',registration_sha)
            or not re.fullmatch('GPU-[0-9a-f-]{36}',uuid)
            or type(uid) is not int or uid<=0 or type(gid) is not int or gid<=0):
        raise ValueError('Original absolute stage, manifest, UUID and non-root owner required')
    resources=profile['GPU_container'];limits=profile['storage']
    if (profile['schema']!='CARA_ENDPOINT_CONTAINER_PROFILE_R1'
            or host!='two_card'
            or not (profile['hard_GPUh']>600/3600 and (profile['physical_paths'],profile['new_scoring_pairs']) in (((46,16),) if profile.get('endpoint7') else ((32,12),(25,8))))
            or (resources['cpus'],resources['memory_GiB'],resources['memory_swap_GiB'])!=(2,40,40)
            or resources['pid_namespace']!='host' or resources['network']!='none'
            or resources['readonly_rootfs'] is not True or resources['supervisor_CUDA_visible'] is not False
            or resources['only_exact_runner_CUDA_visible'] is not True
            or profile['hosts'][host]['cpuset_cpus']!='24,25'
            or (limits['output_image_bytes'],limits['independent_journal_bytes'])!=(64*2**30,48*2**20)):
        raise ValueError('Registered whole container and storage geometry required')
    if profile.get('endpoint7') and (limits['minimum_output_free_bytes']!=8*2**30
            or limits['minimum_host_free_bytes']!=16*2**30
            or limits['minimum_host_free_before_provision_bytes']!=80*2**30):
        raise ValueError('Selected46 storage floors differ from complete quote')
    config=storage.config
    if (storage.output!=project/'outputs'/run_id or config['output_mount']!=str(storage.output)
            or config['image_bytes']!=limits['output_image_bytes']
            or config['journal_bytes']!=limits['independent_journal_bytes']
            or config['journal_path']!=str(storage.journal.path)
            or any(config[k]<limits[k] for k in ('minimum_output_free_bytes','minimum_host_free_bytes','minimum_free_inodes'))):
        raise ValueError('Original private output and independent journal contract differs')
    paths=(project,stage,storage.output,storage.journal.path,Path(config['image_path']))
    if any(not p.is_absolute() or '..' in p.parts or ':' in str(p) or '\n' in str(p) for p in paths):
        raise ValueError('Exact absolute bind-mount paths required')
    command=original_container_arguments(project,stage,storage,registration_sha,
        profile['hosts'][host]['cpuset_cpus'],uid,gid,uuid,resources['memory_GiB'])
    entry=command.index('--entrypoint')
    if command[entry+2]!=resources['image']:raise ValueError('Original pinned container image differs')
    worker=command.index(str(stage/'scripts/cara_fast_worker_r2.py'))
    if command[worker+1]!='supervise':raise ValueError('Original supervisor command shape differs')
    command[worker:worker+2]=[str(stage/WORKER)]
    # Preserve the daemon's creation ID and prevent the worker changing its code.
    command[entry:entry]=['--cidfile',str(stage/'container.cid'),
        '-v',str(stage/'src')+':'+str(stage/'src')+':ro',
        '-v',str(stage/'scripts')+':'+str(stage/'scripts')+':ro']
    return command
