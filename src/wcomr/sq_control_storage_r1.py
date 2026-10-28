"""S/Q control records inside the unchanged 48MiB production journal.

The original six slots keep their on-disk format. S/Q's additional logical
records share the accounting slot as a named packet, under one separate lock
across its complete read/merge/write. Original control files are still written
only after the independent journal is durable.
"""
import fcntl
import hashlib
import json
import os
from pathlib import Path

from .history104_storage_r2 import FixedJournal,StorageGuard,KEYS,SLOT_BYTES

EXTRA_KEYS=('allocation_release','pending_release','supervisor_billing_diagnostic',
            'supervisor_release_diagnostic','accounting')
SCHEMA='SQ_CONTROL_JOURNAL_PACKET_R1'


def require(value,message):
    if not value:raise ValueError(message)


class ControlJournal:
    def __init__(self,original,run_id,lock_root):
        self.original=original;self.path=original.path;self.run_id=run_id
        require(type(run_id) is str and bool(run_id),'Bound S/Q run identity required')
        identity=hashlib.sha256(str(self.path.resolve()).encode()).hexdigest()
        self.lock_path=Path(lock_root)/('sq-control-journal-'+identity+'.lock')

    def _empty_accounting(self):
        fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
        try:
            for slot in (0,1):
                offset=(KEYS.index('accounting')*2+slot)*SLOT_BYTES
                if os.pread(fd,SLOT_BYTES,offset)!=bytes(SLOT_BYTES):return False
            return True
        finally:os.close(fd)

    def _packet(self,allow_empty):
        try:packet=self.original.read('accounting')
        except (ValueError,TypeError,KeyError):
            if allow_empty and self._empty_accounting():
                return dict(schema=SCHEMA,run_id=self.run_id,records={})
            raise ValueError('S/Q accounting journal is absent or corrupt; recover original records only')
        require(isinstance(packet,dict) and packet.get('schema')==SCHEMA and packet.get('run_id')==self.run_id
            and isinstance(packet.get('records'),dict) and set(packet['records'])<=set(EXTRA_KEYS),
            'Foreign S/Q accounting packet; preserve original journal')
        return packet

    def write(self,key,value):
        require(key in set(KEYS)|set(EXTRA_KEYS),'Unregistered S/Q control record key')
        if key not in EXTRA_KEYS:return self.original.write(key,value)
        self.lock_path.parent.mkdir(parents=True,exist_ok=True)
        descriptor=os.open(self.lock_path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(descriptor,fcntl.LOCK_EX)
            packet=self._packet(allow_empty=True)
            packet['records'][key]=value
            self.original.write('accounting',packet)
        finally:os.close(descriptor)

    def read(self,key):
        require(key in set(KEYS)|set(EXTRA_KEYS),'Unregistered S/Q control record key')
        if key not in EXTRA_KEYS:return self.original.read(key)
        packet=self._packet(allow_empty=False)
        require(key in packet['records'],'No durable S/Q control record: '+key)
        return packet['records'][key]


class SQStorageGuard:
    def __init__(self,config,lock_root):
        self.original=StorageGuard(config);self.config=self.original.config;self.output=self.original.output
        self.journal=ControlJournal(self.original.journal,config['run_id'],lock_root)

    def check(self):return self.original.check()

    def persist(self,key,path,value,writer):
        self.journal.write(key,value)
        writer(path,value)


def storage_for(stage):
    stage=Path(stage)
    require(stage.parent.name=='.sync','Registered S/Q stage required')
    config=json.loads((stage/'history104-storage.json').read_text())
    return SQStorageGuard(config,stage.parent/'gpu-locks')
