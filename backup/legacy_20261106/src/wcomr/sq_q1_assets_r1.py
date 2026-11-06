"""Strict immutable B1 reader for Q1; no sampling or new model assets."""
import hashlib
import json
from pathlib import Path

import torch

from .sq_q1_spec_r1 import MANIFEST_SHA,STATE_KEYS


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8*1024**2),b''):h.update(block)
    return h.hexdigest()


class B1Reader:
    def __init__(self,root):
        self.root=Path(root).resolve()
        if file_sha(self.root/'manifest.json') != MANIFEST_SHA:
            raise ValueError('Immutable original B1 manifest SHA differs')
        self.manifest=json.loads((self.root/'manifest.json').read_text())
        self.records=self.manifest['states']
        keys=[(row['prompt'],row['step']) for row in self.records]
        if len(keys)!=len(set(keys)) or set(keys)!=set(STATE_KEYS):
            raise ValueError('Complete original twelve-state B1 cohort required')
        self.references={ref['name']:ref for ref in self.manifest['unique_anchors']+
            [row['artifact'] for row in self.records]}
        if len(self.references)!=32:
            raise ValueError('Exactly the 32 immutable original B1 files required')
        self.verified=set()
        self.identities={}

    @staticmethod
    def _identity(path):
        value=path.stat()
        return (value.st_dev,value.st_ino,value.st_size,value.st_mtime_ns,value.st_ctime_ns)

    def _path(self,ref):
        path=self.root/ref['name']
        if (self.references.get(ref['name'])!=ref or path.is_symlink()
                or path.resolve().parent!=self.root or path.stat().st_size!=ref['bytes']):
            raise ValueError('Original B1 path/reference/bytes differ')
        if ref['name'] in self.verified and self._identity(path)!=self.identities[ref['name']]:
            raise ValueError('Verified original B1 file changed before use')
        return path

    def verify_files(self,progress):
        for ref in self.references.values():
            path=self._path(ref);before=self._identity(path)
            if file_sha(path) != ref['sha256'] or self._identity(path)!=before:
                raise ValueError('Original B1 artifact SHA differs: '+ref['name'])
            self.identities[ref['name']]=before
            self.verified.add(ref['name'])
            progress(len(self.verified),32)

    def load(self,record):
        if len(self.verified)!=32:
            raise ValueError('Verify all original B1 files before Q1 reads')
        if record not in self.records:
            raise ValueError('Foreign original B1 state record')
        def load(ref):
            return torch.load(self._path(ref),map_location='cpu',weights_only=True,mmap=True)
        value=load(record['artifact'])
        value['anchors']=tuple(tuple(load(ref) for ref in pair) for pair in value['anchors'])
        if ((value['context'][0],value['step'])!=(record['prompt'],record['step'])
                or value['context'][1]!='Cosmos-Predict2.5-2B-post-trained'):
            raise ValueError('Original state/model/manifest identity differs')
        return value


def real_geometry(value):
    """Reject a CPU stand-in tensor geometry before a production device copy."""
    feature=(1,24,27,48,2048);output=(1,16,24,54,96)
    expected=[]
    for row in value['current']:
        expected += [(row[k],feature,torch.bfloat16) for k in ('original','probe')]
        expected += [(row['embedding'],(1,24,2048),torch.float32),
                     (row['adaln'],(1,24,6144),torch.float32)]
    expected += [(x,feature,torch.bfloat16) for x in value['teacher_hidden']]
    for key in ('teacher',):expected += [(x,output,torch.float32) for x in value[key]]
    expected += [(x,output,torch.float32) for x in value['readouts']['WC_C']['outputs']]
    expected += [(value['pair_inputs'][key],output,torch.float32) for key in ('noise','latent')]
    for pair in value['anchors']:
        for anchor in pair:
            expected += [(anchor[key],feature,torch.bfloat16) for key in ('probe','residual')]
    if any(not isinstance(x,torch.Tensor) or tuple(x.shape)!=shape or x.dtype!=dtype
           or x.device.type!='cpu' for x,shape,dtype in expected):
        raise ValueError('Original full-geometry CPU B1 tensor shape/dtype/device differs')
