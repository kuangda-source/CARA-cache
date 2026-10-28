"""Exclusive streaming S artifacts with shared true-anchor deduplication.

This writes caller-supplied CPU data. It neither validates real-model outputs
nor proves physical deployment memory. Failed stages retain partial files and
cannot resume or overwrite an original attempt.
"""
import errno
import hashlib
import json
import os
from pathlib import Path

import torch

from .mid_coverage import tree_digest
from .sq_risk_r1 import TARGETS,coverage
from .sq_s_sources_r1 import PARENTS

RAW_STEPS=(9,22,33,35)


def require(value,message):
    if not value:raise ValueError(message)


def cpu_data(value):
    if isinstance(value,torch.Tensor):
        require(value.device.type=='cpu' and not value.requires_grad,'Only detached CPU artifact tensors may be written')
    elif isinstance(value,dict):
        require(all(type(k) in (str,int) for k in value),'S artifact dictionary keys must be data')
        for item in value.values():cpu_data(item)
    elif isinstance(value,(list,tuple)):
        for item in value:cpu_data(item)
    else:require(value is None or type(value) in (str,int,float,bool),'Only registered CPU data may be serialized')


class SCollectionStore:
    def __init__(self,root,*,prompts,maximum_total_bytes,maximum_file_bytes,minimum_free_bytes):
        require(len(prompts)==2 and len(set(prompts))==2 and all(type(p) is str and p for p in prompts),
                'Exactly two distinct frozen FIT or declared CPU fixture identities required')
        require(all(type(v) is int and v>0 for v in (maximum_total_bytes,maximum_file_bytes,minimum_free_bytes))
                and maximum_file_bytes<=maximum_total_bytes,'Explicit positive S storage limits required')
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=False)
        self.prompts=tuple(prompts);self.total_cap=maximum_total_bytes;self.file_cap=maximum_file_bytes
        self.lowwater=minimum_free_bytes;self.written=0;self.failed=False;self.finished=False
        self.rows=[];self.anchors={};self.raw=[];self.contexts={}

    def _write(self,name,payload,*,tensor):
        require(not self.failed and not self.finished,'Failed or completed S storage cannot resume')
        require(Path(name).name==name and not name.startswith('.'),'Registered local artifact basename required')
        partial=self.root/(name+'.partial');target=self.root/name;start=self.written;store=self
        class Counted:
            def __init__(self,stream):self.stream=stream
            def __getattr__(self,key):return getattr(self.stream,key)
            def write(self,value):
                requested=len(value);space=os.statvfs(store.root)
                if (store.written+requested>store.total_cap or store.written-start+requested>store.file_cap
                        or space.f_bavail*space.f_frsize<store.lowwater+requested):
                    raise OSError(errno.ENOSPC,'Frozen S artifact byte cap or free-space boundary')
                actual=self.stream.write(value);store.written+=actual;return actual
        try:
            with partial.open('xb') as stream:
                bounded=Counted(stream)
                if tensor:
                    cpu_data(payload);torch.save(payload,bounded)
                else:bounded.write((json.dumps(payload,indent=2,allow_nan=False)+'\n').encode())
                stream.flush();os.fsync(stream.fileno())
            # Same-directory hard link publishes without replacing an original.
            os.link(partial,target);partial.unlink()
            fd=os.open(self.root,os.O_RDONLY)
            try:os.fsync(fd)
            finally:os.close(fd)
            digest=hashlib.sha256()
            with target.open('rb') as stream:
                for chunk in iter(lambda:stream.read(8*2**20),b''):digest.update(chunk)
            return dict(name=name,bytes=target.stat().st_size,sha256=digest.hexdigest())
        except BaseException:
            self.failed=True
            raise

    def _raw(self,row,raw):
        require(raw['schema']=='SQ_S_F19_RAW_CPU_DATA_R2' and raw['prompt']==row['prompt']
                and raw['parent']==row['parent']=='F19-C' and raw['step']==row['step'] in RAW_STEPS
                and tuple(raw['context'])==tuple(row['context']),'S raw identity differs from its measured row')
        expected=tuple(t for t in PARENTS['F19-C'] if t<row['step'])[-2:]
        require(len(raw['anchors'])==2 and all(tuple(a['step'] for a in pair)==expected for pair in raw['anchors']),
                'S raw requires the exact two strictly past true-D anchors in both branches')
        require(all(tuple(a['context'])==tuple(raw['context']) and a['branch']==b
                for b,pair in enumerate(raw['anchors']) for a in pair),
                'S raw anchor request/branch identity differs')
        require(raw['P1_Dense_hidden_head_replay_accepted'] is False
                and raw['serialized_whole_pipeline_resume_accepted'] is False,
                'S storage cannot add unmeasured hidden-head or pipeline-resume acceptance')
        cpu_data(raw);refs=[]
        for branch,pair in enumerate(raw['anchors']):
            branch_refs=[]
            for anchor in pair:
                key=hashlib.sha256(json.dumps([list(raw['context']),branch,anchor['step']],separators=(',',':')).encode()).hexdigest()
                payload=dict(anchor,context=list(raw['context']),branch=branch)
                content=tree_digest(payload)
                if key in self.anchors:
                    require(self.anchors[key]['content_sha256']==content,'Same S source identity has different true-anchor bytes')
                else:
                    artifact=self._write('anchor-'+key+'.pt',payload,tensor=True)
                    self.anchors[key]=dict(artifact=artifact,content_sha256=content,
                        prompt=row['prompt'],parent=row['parent'],branch=branch,step=anchor['step'])
                branch_refs.append(dict(self.anchors[key]['artifact']))
            refs.append(branch_refs)
        payload={k:v for k,v in raw.items() if k!='anchors'};payload['anchor_refs']=refs
        key=hashlib.sha256(json.dumps([row['prompt'],row['parent'],row['step']]).encode()).hexdigest()
        artifact=self._write('state-'+key+'.pt',payload,tensor=True)
        self.raw.append(dict(prompt=row['prompt'],parent=row['parent'],step=row['step'],artifact=artifact))
        return artifact

    def __call__(self,row,raw):
        require(not self.failed and not self.finished,'Failed or completed S storage cannot resume')
        try:
            key=(row['prompt'],row['parent'],row['step'])
            require(key[0] in self.prompts and key[1] in PARENTS and key[2] in TARGETS
                    and key not in {(r['prompt'],r['parent'],r['step']) for r in self.rows},
                    'Duplicate or foreign S measured row')
            context=tuple(row['context']);parent_key=key[:2]
            require(context and tuple(row['source']['context'])==context
                    and row['source']['parent']==row['parent'] and row['source']['step']==row['step']
                    and not row['source']['current_D_in_source']
                    and row['source']['source_captured_before_parent_pair'],
                    'S row source/context identity differs')
            if parent_key in self.contexts:require(self.contexts[parent_key]==context,'S parent context changed inside one request')
            else:self.contexts[parent_key]=context
            expected=tuple(t for t in PARENTS[row['parent']] if t<row['step'])[-2:]
            require(tuple(row['source']['source_anchor_steps'])==expected,'S measured row borrowed its current D or a foreign source')
            selected=row['parent']=='F19-C' and row['step'] in RAW_STEPS
            require((raw is not None)==selected and row['raw_state_selected']==selected,'S raw scope differs from the frozen eight states')
            receipt=self._raw(row,raw) if raw is not None else None
            key_hash=hashlib.sha256(json.dumps(list(key)).encode()).hexdigest()
            artifact=self._write('row-'+key_hash+'.json',dict(row,raw_artifact=receipt),tensor=False)
            self.rows.append(dict(prompt=key[0],parent=key[1],step=key[2],artifact=artifact))
        except BaseException:
            self.failed=True
            raise

    def finish(self):
        require(not self.failed and not self.finished,'Failed or completed S storage cannot resume')
        try:
            require(coverage(self.rows,self.prompts,tuple(PARENTS))['complete'] and len(self.rows)==108
                    and len(self.raw)==8 and len(self.anchors)==24,'Complete108/eight-state/24-anchor S storage cohort required')
        except BaseException:
            self.failed=True
            raise
        manifest=dict(schema='SQ_S_STREAMING_STORAGE_DATA_ONLY_R1',prompts=list(self.prompts),
            rows=self.rows,raw_states=self.raw,anchors=list(self.anchors.values()),
            status='COMPLETE_CPU_DATA_ARTIFACTS_NOT_SCIENTIFIC_ACCEPTANCE',
            payload_bytes_before_manifest=self.written,maximum_total_bytes=self.total_cap,
            maximum_file_bytes=self.file_cap,minimum_free_bytes=self.lowwater,
            actual_Cosmos_weights_accepted=False,scientific_S_labels_accepted=False,
            deployment_memory_or_speed_accepted=False,GPU_submissions=0)
        artifact=self._write('manifest.json',manifest,tensor=False);self.finished=True
        return dict(manifest=artifact,measured_rows=108,raw_states=8,unique_anchor_files=24,
            actual_stored_bytes=self.written,CPU_data_storage_only=True)
