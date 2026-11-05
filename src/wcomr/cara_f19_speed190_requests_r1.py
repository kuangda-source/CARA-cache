"""Already-admitted loaded-model request routing; no launch or reservation."""
import copy
from pathlib import Path

from . import clean_speed20_r1 as clean
from .cara_fast_spec_r1 import profile_from
from .cara_f19_profile_r1 import profile_policy_owner
from .cara_f19_speed190_sampling_r1 import SpeedOwner
from .paper_latency_r1 import execute_with_timing
from .policy_generator_r1 import production_sampling,p2_native_sampling
from .policy_generator_r1.frozen_request_arguments import request_variant
from .source_aware_phase_sampling import bind_globals
from .wc_time_protocol_p0 import compile_wc_adapter


class Requests:
    def __init__(self,inference,samples,card,common,*,cpu_validation=False):
        self.inference,self.samples,self.card,self.common=inference,samples,card,common
        self.cpu_validation=cpu_validation;self.seen=set();self.profile=profile_from(card['profile'])
        self.wc_port=compile_wc_adapter(common['runtime'],common['wc'],paper_port=True)[0]
        self.allD=compile_wc_adapter(common['runtime'],common['wc'],force_full=True)[0]

    def __call__(self,slot,output):
        if slot not in self.card['matrix'] or slot['id'] in self.seen:raise ValueError('Unregistered or repeated physical CAL request')
        self.seen.add(slot['id']);role=self.card['roles'][slot['role']]
        sample=request_variant(self.samples[slot['member']],seed=0,num_steps=35)
        runner,args,extra,module=production_sampling.execute,(),{},self.common['wc']
        settings=copy.deepcopy(self.card['settings']);diagnostic={}
        if role['kind']=='native':runner=p2_native_sampling.execute;extra['schedule']=self.card['schedule']
        elif role['kind']=='wc':
            runner=clean.execute;args=('WC',);settings=copy.deepcopy(role['settings']);module=self.wc_port
        elif role['kind']=='allD':runner=clean.execute;args=('WC',);module=self.allD
        else:
            extra.update(profile=self.profile,policy=role['policy'])
            if role['kind']=='speed_policy':
                factory=lambda model,**kw:SpeedOwner(model,light_C=role['light_C'],partial_updates=tuple(role['partial_updates']),**kw)
                runner=bind_globals(production_sampling.execute,dict(PolicyOwner=factory))
            elif role['kind']=='sparse_policy':
                from .cara_sparse_refresh_probe_r1 import SparseOwner
                factory=lambda model,**kw:SparseOwner(model,light_C=True,partial_updates=tuple(role['partial_updates']),sync_residual=role['sync_residual'],**kw)
                runner=bind_globals(production_sampling.execute,dict(PolicyOwner=factory))
            elif role['kind']=='profile_policy':
                from .policy_generator_r1.production_sampling import PolicyOwner
                class DiagnosticOwner(PolicyOwner):
                    def __init__(self,model,**kw):
                        super().__init__(model,**kw)
                        device=next(model.net.parameters()).device
                        self.measurement=profile_policy_owner(self,model.sample_scheduler,device=device)
                        self.observer=self.measurement.__enter__()
                        self.observer.bind(model,'decode','VAE_decode')
                    def close(self):
                        if self.measurement is not None:
                            self.measurement.__exit__(None,None,None);self.measurement=None
                            diagnostic.update(self.observer.summary)
                        super().close()
                runner=bind_globals(production_sampling.execute,dict(PolicyOwner=DiagnosticOwner))
            elif role['kind']!='policy':raise ValueError('Unknown CAL role')
        result=execute_with_timing(runner,self.inference,sample,*args,host='two_card',expected_updates=36,
            cpu_validation=self.cpu_validation,diagnostic=not slot['eligible_clean_time'],
            **{**self.common,'wc':module,'settings':settings,'calibration':None,'specs':{},
               'output':Path(output),'audit':slot['audit'],**extra})
        result.update(slot_id=slot['id'],role=slot['role'],scope_sha256=self.card['scope_sha256'],
            T_DD=result.get('paper_denoise_decode_seconds'),T_request=result.get('full_request_seconds'),
            CPU_fixture=self.cpu_validation,eligible_clean_time=slot['eligible_clean_time'])
        if diagnostic:result['component_profile']=diagnostic
        return result
