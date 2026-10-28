"""Exact B1 CPU-only copy through a pinned read-only SFTP source.

No tensors are decoded, no new model output is produced, and no GPU or ledger
interface is used. A completed target is published only after full SHA checks.
The caller owns the once-only process handle and CPU resource limits.
"""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import socket
import stat
import time

MANIFEST_SHA='5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa'
TOTAL_BYTES=20795567276
ASSETS='outputs/cara-ig-b1-r2-20261027/assets'
PROJECT='/data20t/gaokuangda/worldcache_workspace'
FILES=32
CHUNK=8*2**20

SOURCE_WRAPPER=r'''
import json,os,pathlib,resource,subprocess,sys
os.environ.update(CUDA_VISIBLE_DEVICES='',NVIDIA_VISIBLE_DEVICES='void')
assert {4,5}<=os.sched_getaffinity(0)
os.sched_setaffinity(0,{4,5});os.nice(10)
resource.setrlimit(resource.RLIMIT_AS,(2*2**30,2*2**30))
resource.setrlimit(resource.RLIMIT_CPU,(7200,7200))
subprocess.run(['/usr/bin/ionice','-c','3','-p',str(os.getpid())],check=True)
fields=pathlib.Path('/proc/self/stat').read_text().split(') ',1)[1].split()
sys.stderr.write(json.dumps(dict(status='SQ_B1_READONLY_SOURCE_SERVER',pid=os.getpid(),
 start_ticks=int(fields[19]),CPUs=[4,5],address_space_bytes=2*2**30,
 CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'],source_readonly=True))+'\n')
sys.stderr.flush()
os.execv('/usr/lib/openssh/sftp-server',['sftp-server','-R'])
'''


def require(value,message):
    if not value:raise ValueError(message)


@contextmanager
def readonly_source(endpoint,pins,password,*,wall_seconds=7200):
    import paramiko
    transport=paramiko.Transport(socket.create_connection((endpoint['hostname'],int(endpoint['port'])),timeout=15))
    transport.banner_timeout=15;transport.auth_timeout=15
    transport.get_security_options().key_types=tuple(pins)
    channel=sftp=None
    try:
        transport.start_client(timeout=15);key=transport.get_remote_server_key()
        require(pins.get(key.get_name())==key.get_base64(),'Source SSH key differs from the existing verified Mac pin')
        transport.auth_password(endpoint['user'],password);password=None
        channel=transport.open_session(timeout=30);channel.settimeout(60)
        require(type(wall_seconds) is int and 0<wall_seconds<=7200,'Original CPU transfer deadline required')
        command='/usr/bin/timeout --signal=TERM --kill-after=10s '+str(wall_seconds)+' /usr/bin/python3 -u -c '+shlex.quote(SOURCE_WRAPPER)
        channel.exec_command(command)
        banner=json.loads(channel.makefile_stderr('rb').readline(8192))
        require(banner['status']=='SQ_B1_READONLY_SOURCE_SERVER' and banner['source_readonly'] is True
                and banner['CPUs']==[4,5] and banner['address_space_bytes']==2*2**30
                and banner['CUDA_VISIBLE_DEVICES']=='','Source CPU/read-only boundary differs')
        sftp=paramiko.SFTPClient(channel);sftp.get_channel().settimeout(60)
        yield sftp,banner
    finally:
        if sftp is not None:sftp.close()
        elif channel is not None:channel.close()
        transport.close()


def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(CHUNK),b''):digest.update(block)
    return digest.hexdigest()


def local_identity(path):
    value=Path(path).stat()
    return [value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns]


def source_identity(value):
    return dict(size=value.st_size,mtime=value.st_mtime,mode=value.st_mode,
                uid=value.st_uid,gid=value.st_gid)


def directory_sync(path):
    fd=os.open(str(path),os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def stream_blocks(reader,size,readv_requests):
    require(readv_requests in (0,32),'Only the serial original or bounded32 transport is registered')
    if not readv_requests:
        left=size
        while left:
            block=reader.read(min(CHUNK,left))
            require(bool(block) and len(block)<=left,'Original B1 stream ended early or exceeded its declared size')
            left-=len(block);yield block
        return
    # Paramiko2.6 readv schedules only these chunks. Consume every response
    # before starting the next batch: <=32 requests and <=1MiB prefetched.
    step=32768
    for base in range(0,size,readv_requests*step):
        chunks=[(offset,min(step,size-offset)) for offset in range(base,min(size,base+readv_requests*step),step)]
        values=iter(reader.readv(chunks))
        for _,length in chunks:
            block=next(values,None)
            require(block is not None and len(block)==length,'Bounded B1 readv response size/order differs')
            yield block
        require(next(values,None) is None,'Bounded B1 readv returned an unregistered block')


def copy_assets(sftp,source_root,target,*,expected_manifest_sha=MANIFEST_SHA,
                expected_total_bytes=TOTAL_BYTES,minimum_free_bytes=4*2**30,
                readv_requests=0,incoming_name='.sq-b1-port-cpu-r1-20261029',
                save=lambda value:None,free_bytes=lambda path:shutil.disk_usage(path).free):
    """Stream exactly 32 declared leaves; preserve originals on every failure."""
    with sftp.open(source_root+'/manifest.json','rb') as stream:manifest_raw=stream.read(2**20+1)
    require(len(manifest_raw)<=2**20 and hashlib.sha256(manifest_raw).hexdigest()==expected_manifest_sha,
            'Original B1 manifest bytes differ')
    manifest=json.loads(manifest_raw)
    refs=manifest['unique_anchors']+[r['artifact'] for r in manifest['states']]
    require(len(refs)==FILES and len({r['name'] for r in refs})==FILES
            and sum(r['bytes'] for r in refs)==expected_total_bytes,'Exact32 B1 byte cohort differs')
    require(all(type(r['bytes']) is int and r['bytes']>0 and Path(r['name']).name==r['name']
                and not r['name'].startswith('.') and r['name']!='manifest.json'
                and len(r['sha256'])==64 and all(c in '0123456789abcdef' for c in r['sha256']) for r in refs),
            'Registered positive-size local artifact leaves required')
    target=Path(target);target.mkdir(parents=True,exist_ok=True)
    require(not target.is_symlink(),'B1 target directory cannot be a symlink')
    existing=target/'manifest.json'
    if existing.exists():require(not existing.is_symlink() and sha(existing)==expected_manifest_sha,'Preserve foreign target manifest')
    require(incoming_name in ('.sq-b1-port-cpu-r1-20261029','.sq-b1-port-cpu-r2-20261029'),
            'Registered private transfer attempt directory required')
    incoming=target/incoming_name;incoming.mkdir(mode=0o700,exist_ok=False)
    missing=sum(r['bytes'] for r in refs if not (target/r['name']).exists())
    require(free_bytes(target)>=missing+minimum_free_bytes,'Insufficient target capacity for the full B1 cohort')
    state=dict(status='B1_CPU_PORT_RUNNING',planned_files=FILES,planned_bytes=expected_total_bytes,
        transferred_bytes=0,verified_target_bytes=0,files=[],started_unix=time.time(),
        readv_requests=readv_requests,maximum_prefetch_bytes=readv_requests*32768,
        GPU_submissions=0,ledger_writes=0)
    last=[0.]
    def progress(force=False):
        now=time.monotonic()
        if force or now-last[0]>=1:save(state);last[0]=now
    progress(True)
    for ref in refs:
        source=source_root+'/'+ref['name'];destination=target/ref['name']
        require(not destination.is_symlink(),'Preserve original target symlink')
        before=sftp.lstat(source);original=source_identity(before)
        require(stat.S_ISREG(before.st_mode) and before.st_size==ref['bytes'],'Original source is not the registered regular file')
        state['current_file']=ref['name'];progress(True)
        if destination.exists():
            require(not destination.is_symlink() and destination.stat().st_size==ref['bytes'],'Preserve original target path/size mismatch')
            identity=local_identity(destination)
            require(sha(destination)==ref['sha256'] and local_identity(destination)==identity,'Preserve original target SHA/identity mismatch')
            method='EXISTING_TARGET_SHA_ONLY_SOURCE_NOT_REREAD'
        else:
            partial=incoming/(ref['name']+'.partial');digest=hashlib.sha256();remaining=ref['bytes']
            with sftp.open(source,'rb') as reader,partial.open('xb') as writer:
                for block in stream_blocks(reader,ref['bytes'],readv_requests):
                    require(free_bytes(target)>=minimum_free_bytes+len(block),'Target free-space low water during B1 copy')
                    require(bool(block) and len(block)<=remaining,'Original B1 stream ended early or exceeded its declared size')
                    writer.write(block);digest.update(block);remaining-=len(block)
                    state['transferred_bytes']+=len(block);progress()
                require(remaining==0,'Original B1 transfer byte denominator differs')
                require(not reader.read(1),'Original B1 stream exceeded its declared size')
                writer.flush();os.fsync(writer.fileno())
            require(source_identity(sftp.lstat(source))==original,'Original B1 source attributes changed during copy')
            require(digest.hexdigest()==ref['sha256'] and partial.stat().st_size==ref['bytes']
                    and sha(partial)==ref['sha256'],'B1 received/write-readback SHA differs; preserve partial')
            os.link(partial,destination);partial.unlink();directory_sync(target)
            identity=local_identity(destination);method='DIRECT_SOURCE_STREAM_AND_TARGET_READBACK_SHA'
        state['verified_target_bytes']+=ref['bytes']
        state['files'].append(dict(name=ref['name'],bytes=ref['bytes'],sha256=ref['sha256'],
            method=method,source_attributes=original,target_identity=identity))
        progress(True)
    require(len(state['files'])==FILES and state['verified_target_bytes']==expected_total_bytes,'Complete B1 target cohort required')
    if not existing.exists():
        partial=incoming/'manifest.json.partial'
        with partial.open('xb') as stream:stream.write(manifest_raw);stream.flush();os.fsync(stream.fileno())
        os.link(partial,existing);partial.unlink();directory_sync(target)
    require(sha(existing)==expected_manifest_sha,'Final original B1 manifest differs')
    incoming.rmdir();directory_sync(target)
    state.update(status='B1_32_CPU_PORT_COMPLETE_NO_GPU',manifest_sha256=expected_manifest_sha,
        ended_unix=time.time(),copied_files=sum(r['method']=='DIRECT_SOURCE_STREAM_AND_TARGET_READBACK_SHA' for r in state['files']),
        source_SFTP_attributes_have_no_inode_or_nanosecond_proof=True,
        stronger_Q1_host_asset_verification_still_required=True,scientific_or_GPU_acceptance=False)
    progress(True);return state
