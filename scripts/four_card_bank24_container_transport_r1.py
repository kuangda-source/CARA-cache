"""Owned Unix FD handoff across Docker, without copying or inventing a lease.

Host and container use --pid=host explicitly. The host retains the original
flock description until the owned container exits. The inner supervisor then
passes a duplicate of that *same* description to the actual runner.
"""
import array
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import threading
import time


def socket_path(job):
    # Linux sun_path is only 108 bytes. Research job names exceed that limit.
    # A short, owned filesystem socket crosses an offline Docker network
    # namespace; an abstract socket would not cross that boundary.
    key=hashlib.sha256(str(Path(job).resolve()).encode()).hexdigest()[:20]
    return Path('/tmp/wc-bank24-fd-'+key)/'lease.sock'


def atomic(path, value):
    path=Path(path);tmp=path.with_name(path.name+'.tmp')
    with tmp.open('x') as out:json.dump(value,out,indent=2,allow_nan=False);out.write('\n')
    os.replace(tmp,path)


def identity(pid):
    try:
        value=Path('/proc/%d/stat'%pid).read_text().rsplit(')',1)[1].split()
        return dict(pid=pid,start_ticks=int(value[19]),state=value[0])
    except FileNotFoundError:return None


def alive(expected):
    current=identity(expected['pid']) if expected else None
    return bool(current and current['start_ticks']==expected['start_ticks'] and current['state'] not in ('Z','X'))


def receive(sock_path, nonce, manifest_sha256):
    connection=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);connection.settimeout(60)
    connection.connect(str(sock_path))
    connection.sendall((json.dumps(dict(nonce=nonce,manifest_sha256=manifest_sha256,
        pid=os.getpid(),uid=os.getuid(),pid_namespace=os.readlink('/proc/self/ns/pid')))+'\n').encode())
    data,ancillary,flags,address=connection.recvmsg(4096,socket.CMSG_SPACE(array.array('i').itemsize))
    fds=[]
    for level,kind,body in ancillary:
        if level==socket.SOL_SOCKET and kind==socket.SCM_RIGHTS:
            values=array.array('i');values.frombytes(body[:len(body)-(len(body)%values.itemsize)]);fds.extend(values)
    if len(fds)!=1 or flags & (socket.MSG_CTRUNC|socket.MSG_TRUNC):
        connection.close()
        for fd in fds:os.close(fd)
        raise ValueError('Exactly one complete original lease descriptor required')
    fd=fds[0]
    try:
        while not data.endswith(b'\n'):
            more=connection.recv(4096-len(data))
            if not more or len(data)+len(more)>4096:raise ValueError('Incomplete original FD receipt')
            data+=more
        connection.close();receipt=json.loads(data);stat=os.fstat(fd)
        assert receipt['status']=='OWNED_ORIGINAL_LEASE_FD_TRANSFERRED'
        assert receipt['device']==stat.st_dev and receipt['inode']==stat.st_ino
        assert Path('/proc/self/fd/%d'%fd).resolve()==Path(receipt['path']).resolve()
        assert receipt['host_pid_namespace']==os.readlink('/proc/self/ns/pid')
        # A new open description must fail while the inherited description owns
        # the flock. Calling flock on fd itself would not prove this.
        with Path(receipt['path']).open('r') as independent:
            try:fcntl.flock(independent,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:pass
            else:raise ValueError('Passed descriptor did not retain the original UUID lease')
        return fd,receipt
    except BaseException:connection.close();os.close(fd);raise


class LeaseBroker:
    def __init__(self, job, fd, path, nonce, manifest_sha256, container, inspect=subprocess.run):
        self.job=Path(job);self.fd=fd;self.path=Path(path).resolve();self.nonce=nonce
        self.manifest_sha256=manifest_sha256;self.container=container;self.inspect=inspect
        self.socket_path=socket_path(self.job);self.ipc_directory=self.socket_path.parent
        self.ipc_directory.mkdir(mode=0o700)
        self.record=None;self.failure=None
        self.listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM)
        self.listener.bind(str(self.socket_path));os.chmod(self.socket_path,0o600)
        self.listener.listen(1);self.listener.settimeout(80)
        self.thread=threading.Thread(target=self._serve,name='owned-lease-broker',daemon=True)

    def start(self):self.thread.start()

    def _serve(self):
        try:
            connection,_=self.listener.accept();connection.settimeout(20)
            with connection:
                peer_pid,peer_uid,peer_gid=struct.unpack('3i',connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
                raw=bytearray()
                while not raw.endswith(b'\n'):
                    part=connection.recv(4096)
                    if not part or len(raw)+len(part)>4096:raise ValueError('Bounded handoff identity required')
                    raw.extend(part)
                hello=json.loads(raw)
                assert peer_uid==os.getuid() and hello['pid']==peer_pid and hello['uid']==peer_uid
                assert hello['nonce']==self.nonce and hello['manifest_sha256']==self.manifest_sha256
                assert hello['pid_namespace']==os.readlink('/proc/self/ns/pid')
                check=self.inspect(['docker','inspect',self.container],capture_output=True,text=True,timeout=20)
                assert check.returncode==0
                container=json.loads(check.stdout)[0]
                assert container['State']['Running'] is True and container['State']['Pid']==peer_pid
                assert container['Config']['Labels']['wcomr.manifest']==self.manifest_sha256
                assert container['HostConfig']['PidMode']=='host'
                stat=os.fstat(self.fd)
                receipt=dict(status='OWNED_ORIGINAL_LEASE_FD_TRANSFERRED',host_identity=identity(os.getpid()),
                    peer_identity=identity(peer_pid),peer_uid=peer_uid,path=str(self.path),
                    device=stat.st_dev,inode=stat.st_ino,host_pid_namespace=os.readlink('/proc/self/ns/pid'),
                    manifest_sha256=self.manifest_sha256,container=self.container,
                    container_actual_running=True,container_actual_readonly_root=container['HostConfig']['ReadonlyRootfs'],
                    container_actual_pid_mode=container['HostConfig']['PidMode'],
                    container_devices=container['HostConfig'].get('Devices') or [],
                    container_device_requests=container['HostConfig'].get('DeviceRequests') or [],
                    socket_peer_PID_matches_actual_Docker_PID=True,original_fd_held_by_host=True)
                encoded=(json.dumps(receipt)+'\n').encode()
                sent=connection.sendmsg([encoded],[(socket.SOL_SOCKET,socket.SCM_RIGHTS,array.array('i',[self.fd]))])
                if sent<len(encoded):connection.sendall(encoded[sent:])
                self.record=receipt;atomic(self.job/'host-FD-handoff.json',receipt)
        except BaseException as error:
            self.failure=dict(error_type=type(error).__name__,error=str(error))
            atomic(self.job/'host-FD-handoff-failure.json',self.failure)

    def close(self):
        self.listener.close();self.thread.join(timeout=2)
        if self.socket_path.exists():self.socket_path.unlink()
        if self.ipc_directory.is_dir():self.ipc_directory.rmdir()


def stop_owned(child, grace=5):
    if child is None or child.poll() is not None:return
    # A process group created by this supervisor, never a foreign PID.
    os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=grace)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait(timeout=grace)


def run_inherited(command, fd, env, timeout, log, on_started=None):
    """Shared actual launch/timeout path used by GPU and CPU transport checks."""
    start=time.monotonic();started=time.time();child=None;result={}
    try:
        child=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            env=dict(env,WC_SUPERVISOR_PID=str(os.getpid()),WC_LOCK_FD=str(fd)),
            pass_fds=(fd,),start_new_session=True)
        result.update(child_identity=identity(child.pid),started_unix=started)
        if on_started is not None:on_started(dict(result))
        try:result['exit_code']=child.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            result['owned_timeout_stop']=True;stop_owned(child);result['exit_code']=child.returncode
    finally:
        stop_owned(child)
        result.update(ended_unix=time.time(),wall_seconds=time.monotonic()-start,
                      child_exited=child is None or child.poll() is not None)
    return result


def retain_full_rows(planned, actual):
    by_id={r['id']:r for r in actual}
    if len(by_id)!=len(actual) or not set(by_id)<={r['id'] for r in planned}:
        raise ValueError('Duplicate or foreign registered path')
    rows=[by_id.get(r['id'],dict(r,status='NOT_REACHED_RETAINED')) for r in planned]
    assert len(rows)==24
    return rows
