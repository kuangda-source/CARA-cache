"""Resident-model request adapter shared by P2 timing/history batch engines.

Source/stage, P1 acceptance, whole budget and exclusivity are external admission
requirements. This adapter never creates a CUDA context or launches a worker.
"""
import copy,json
from pathlib import Path
from .p2_native_sampling import execute as native_execute
from .p2_history_sampling import execute as history_execute
from .production_sampling import execute as policy_execute,validate_policy
from .production_evidence import artifact
from .continuation_preparation import require


class Requests:
    def __init__(self,*,inference,samples,profile,CARA,schedules,output,common):
        validate_policy(profile,CARA)
        self.inference=inference;self.samples=samples;self.profile=profile;self.CARA=CARA
        self.schedules={r['requested_steps']:r for r in schedules};self.output=Path(output);self.common=dict(common)
        require(set(self.schedules)==set(range(18,36)),'Complete accepted scheduler grid required')
    def __call__(self,slot,policy=None):
        import torch
        sample=copy.copy(self.samples[slot['member']]);require(sample.seed==slot['seed'],'Original registered seed differs')
        identifier=slot['id'];require(Path(identifier).name==identifier and identifier not in ('.','..'),'Safe original slot required')
        directory=self.output/identifier;require(not directory.exists(),'No retry or overwrite of original request')
        common=dict(self.common,output=directory)
        if policy is not None:
            validate_policy(self.profile,policy);sample.num_steps=35
            result=history_execute(self.inference,sample,profile=self.profile,policy=policy,**common)
        elif slot['method']=='CARA':
            sample.num_steps=35;result=policy_execute(self.inference,sample,profile=self.profile,policy=self.CARA,**common)
        else:
            require(slot['method'].startswith('NATIVE'),'Unknown timing method')
            n=int(slot['method'][6:]);require(n in self.schedules,'Unregistered Native count')
            sample.num_steps=n;result=native_execute(self.inference,sample,schedule=self.schedules[n],**common)
        # In CPU parity tests only, guided vectors exist. Their transport is an
        # audit artifact, never a JSON metadata value or production timing copy.
        guided=result.pop('guided',None);latent=result.pop('final_latent',None)
        if latent is not None:
            path=directory/'final-latent.pt'
            with path.open('xb') as f:torch.save(dict(final_latent=latent),f)
            result['final_latent_artifact']=artifact(path,self.output)
        if guided is not None:
            path=directory/'CPU-guided-audit.pt'
            with path.open('xb') as f:torch.save(dict(guided=guided),f)
            result['CPU_guided_artifact']=artifact(path,self.output)
        if result['status']=='COMPLETE':
            require(latent is not None,'Complete request missing final latent')
            result['video_artifact']=artifact(result['video_path'],self.output)
        path=directory/'request.json'
        with path.open('x') as f:json.dump(dict(slot=slot,policy=policy,result=result),f,indent=2,allow_nan=False);f.write('\n')
        result['request_artifact']=artifact(path,self.output)
        return result
