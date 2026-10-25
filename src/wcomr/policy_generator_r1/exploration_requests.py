"""Shared CAL production request adapter; reuses accepted Native and PG engines."""
import copy
from .p2_native_sampling import execute as native_execute
from .production_sampling import execute as policy_execute

class Requests:
    def __init__(self,*,inference,samples,profile,roles,schedules,common):
        self.inference=inference;self.samples=samples;self.profile=profile
        self.roles=roles;self.schedules={r['requested_steps']:r for r in schedules}
        self.common=common;self.seen=set()

    def __call__(self,slot,output):
        if slot['id'] in self.seen: raise ValueError('Physical slot already attempted')
        self.seen.add(slot['id'])
        role=self.roles[slot['role']];sample=copy.deepcopy(self.samples[slot['member']])
        sample.seed=slot['seed'];sample.num_steps=role['requested_steps']
        kw=dict(self.common,output=output)
        if role['kind']=='native':
            return native_execute(self.inference,sample,schedule=self.schedules[sample.num_steps],**kw)
        return policy_execute(self.inference,sample,profile=self.profile,policy=role['policy'],**kw)
