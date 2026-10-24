"""Private output filesystem and preallocated, double-buffered control journal.

All checks and reservation work run outside the measured request boundary.
No CUDA, sudo, mode change, launch or dataset operation is performed here.
"""
import hashlib,json,os
from pathlib import Path

KEYS=('supervisor','billing','guardian','telemetry','failure','accounting')
SLOT_BYTES=4*1024*1024
HEADER=80

class FixedJournal:
    def __init__(self,path):self.path=Path(path)
    def create(self):
        fd=os.open(self.path,os.O_CREAT|os.O_EXCL|os.O_RDWR,0o600)
        try:
            os.posix_fallocate(fd,0,2*len(KEYS)*SLOT_BYTES);os.fsync(fd)
            if os.fstat(fd).st_blocks*512<2*len(KEYS)*SLOT_BYTES:raise OSError('Sparse journal rejected')
        finally:os.close(fd)
    def _records(self,fd,key):
        values=[]
        for slot in (0,1):
            offset=(KEYS.index(key)*2+slot)*SLOT_BYTES
            try:
                header=os.pread(fd,HEADER,offset);size=int(header[:16]);digest=header[16:].decode()
                if not 0<size<SLOT_BYTES-HEADER:continue
                raw=os.pread(fd,size,offset+HEADER)
                if hashlib.sha256(raw).hexdigest()!=digest:continue
                value=json.loads(raw);values.append((value['generation'],slot,value['value']))
            except (ValueError,UnicodeDecodeError,KeyError):pass
        return sorted(values)
    def read(self,key):
        fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            records=self._records(fd,key)
            if not records:raise ValueError('No valid durable journal record: '+key)
            return records[-1][2]
        finally:os.close(fd)
    def write(self,key,value):
        import fcntl
        fd=os.open(self.path,os.O_RDWR|os.O_NOFOLLOW)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX)
            if os.fstat(fd).st_size!=2*len(KEYS)*SLOT_BYTES:raise ValueError('Journal size changed')
            records=self._records(fd,key);generation=records[-1][0]+1 if records else 1;slot=1-records[-1][1] if records else 0
            raw=json.dumps(dict(generation=generation,value=value),allow_nan=False,sort_keys=True).encode()
            if len(raw)>=SLOT_BYTES-HEADER:raise ValueError('Journal record too large')
            offset=(KEYS.index(key)*2+slot)*SLOT_BYTES
            if os.pwrite(fd,raw,offset+HEADER)!=len(raw):raise OSError('Short journal payload write')
            os.fsync(fd)
            header=('%016d'%len(raw)).encode()+hashlib.sha256(raw).hexdigest().encode()
            if os.pwrite(fd,header,offset)!=HEADER:raise OSError('Short journal header write')
            os.fsync(fd)
        finally:os.close(fd)


class StorageGuard:
    def __init__(self,config):
        self.config=config;self.output=Path(config['output_mount']);self.journal=FixedJournal(config['journal_path'])
    def check(self):
        c=self.config;out=self.output;image=Path(c['image_path']);journal=self.journal.path
        if not os.path.ismount(out) or out.is_symlink():raise ValueError('Dedicated output filesystem is not mounted')
        if out.stat().st_dev==out.parent.stat().st_dev:raise ValueError('Output still on shared filesystem')
        if out.stat().st_dev!=c['output_device'] or image.stat().st_ino!=c['image_inode']:raise ValueError('Storage identity changed')
        if image.stat().st_size!=c['image_bytes'] or image.stat().st_blocks*512<c['image_bytes']:raise ValueError('Output image is sparse or changed')
        if journal.stat().st_dev in (out.stat().st_dev,image.stat().st_dev):raise ValueError('Control journal must be on an independent filesystem')
        if journal.stat().st_size!=2*len(KEYS)*SLOT_BYTES or journal.stat().st_blocks*512<journal.stat().st_size:raise ValueError('Control journal not fully reserved')
        s=os.statvfs(out);host=os.statvfs(image.parent)
        if s.f_bavail*s.f_frsize<c['minimum_output_free_bytes'] or s.f_favail<c['minimum_free_inodes']:raise OSError(28,'Private output low water; stop before next request')
        if host.f_bavail*host.f_frsize<c['minimum_host_free_bytes']:raise OSError(28,'Host control filesystem low water')
        return dict(output_available=s.f_bavail*s.f_frsize,host_available=host.f_bavail*host.f_frsize,free_inodes=s.f_favail)
    def persist(self,key,path,value,writer):
        # Independent durability first; original names are preserved on success.
        self.journal.write(key,value)
        writer(path,value)


def storage_for(stage):
    path=Path(stage)/'history104-storage.json'
    if not path.exists():raise ValueError('Recovery104 requires dedicated storage contract')
    return StorageGuard(json.loads(path.read_text()))

