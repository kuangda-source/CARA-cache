"""Streaming readout assets with unique true anchors and exact tensor hashes.

No pipeline checkpoint claim. Large unused sampler checkpoints are represented
by identity hashes; all tensors required for actual head/RF replay are stored.
"""
import copy
import hashlib
import json
from pathlib import Path

import torch

from .mid_coverage import tree_digest


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024**2),b''):h.update(block)
    return h.hexdigest()


class GainAssetStore:
    def __init__(self, root, *, byte_limit, check_space):
        self.root=Path(root);self.limit=byte_limit;self.check_space=check_space
        if self.root.exists():raise FileExistsError('Original gain asset store cannot be replayed')
        if type(byte_limit) is not int or byte_limit <= 0:raise ValueError('Explicit storage bound required')
        self.root.mkdir(parents=True);self.used=0;self.anchors={};self.states=[]

    def _write(self, name, value):
        self.check_space()
        path=self.root/name
        # Sum serialized tensor bytes conservatively before opening; final
        # file size is checked as well. Keep any failed original as evidence.
        from .partial_mlp_deployment_state import tensor_bytes
        if self.used+tensor_bytes(value)+1024**2>self.limit:
            raise OSError('Registered gain asset capacity would be exceeded')
        with path.open('xb') as f:torch.save(value,f)
        self.used+=path.stat().st_size
        if self.used>self.limit:raise OSError('Serialized gain asset exceeds registered storage bound')
        return dict(name=name,sha256=sha(path),bytes=path.stat().st_size)

    def save(self, payload):
        prompt=payload['context'][0];step=payload['step']
        key=hashlib.sha256(prompt.encode()).hexdigest()[:16]
        if any(r['prompt']==prompt and r['step']==step for r in self.states):
            raise ValueError('Duplicate registered gain state')
        refs=[]
        for branch,pair in enumerate(payload['anchors']):
            refs.append([])
            for anchor in pair:
                identity=(prompt,branch,anchor['step'])
                digest=tree_digest(anchor)
                if identity not in self.anchors:
                    record=self._write('anchor_%s_%d_%d.pt'%(key,branch,anchor['step']),anchor)
                    record['tensor_identity']=digest;self.anchors[identity]=record
                record=self.anchors[identity]
                if record['tensor_identity']!=digest:raise ValueError('True D anchor changed under same identity')
                refs[-1].append(record)
        # Copies only Python topology. Never duplicate large CPU tensors here.
        compact=dict(payload)
        checkpoint=compact.pop('pre_pair_checkpoint')
        compact['pre_pair_checkpoint_identity']=tree_digest(checkpoint)
        compact['serialized_pipeline_resume_supported']=False
        compact['anchors']=refs
        compact['current']=[{k:v for k,v in row.items() if k in ('original','probe','embedding','adaln')}
                            for row in compact['current']]
        dense=compact.pop('teacher_features')
        compact['teacher_hidden']=[dense[b]['hidden'] for b in (0,1)]
        compact['teacher_features_identity']={b:tree_digest(v) for b,v in dense.items()}
        record=self._write('state_%s_%d.pt'%(key,step),compact)
        self.states.append(dict(prompt=prompt,step=step,artifact=record,moments=payload['gain_moments']))
        manifest=dict(schema='CARA_IG_STREAMED_ASSETS_R1',states=self.states,
                      unique_anchors=list(self.anchors.values()),written_bytes=self.used,byte_limit=self.limit)
        from .gpu_budget_pool_v2 import atomic_json
        atomic_json(self.root/'manifest.json',manifest)
        return record


def load_state(root, record):
    root=Path(root).resolve()
    def read(ref):
        path=(root/ref['name']).resolve()
        if path.parent!=root or path.stat().st_size!=ref['bytes'] or sha(path)!=ref['sha256']:
            raise ValueError('Gain asset path/bytes/SHA mismatch')
        return torch.load(path,map_location='cpu',weights_only=True)
    value=read(record)
    value['anchors']=tuple(tuple(read(ref) for ref in pair) for pair in value['anchors'])
    return value
