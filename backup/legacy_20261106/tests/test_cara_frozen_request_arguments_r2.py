"""Local structural regression; actual Cosmos class is separately tested remotely."""
import copy
import sys
import types
import unittest
from unittest.mock import patch
from wcomr.policy_generator_r1.frozen_request_arguments import request_variant
from wcomr.policy_generator_r1.exploration_requests import Requests

class Frozen:
    model_config={'frozen':True}
    def __init__(self, data):object.__setattr__(self,'data',copy.deepcopy(data))
    def __getattr__(self,key):return self.data[key]
    def __setattr__(self,*args):raise ValueError('frozen_instance')
    def model_dump(self,**kw):return copy.deepcopy(self.data)
    @classmethod
    def model_validate(cls,data):
        if data['num_steps']<=0:raise ValueError('positive')
        return cls(data)

class FrozenRequests(unittest.TestCase):
    def setUp(self):
        self.base=Frozen(dict(name='fixture',seed=0,num_steps=35,prompt='same',negative_prompt='negative',guidance=7,num_output_frames=93,resolution='432,768',nested={'x':[1]}))
        self.roles={'N':dict(kind='native',requested_steps=26),'P':dict(kind='policy',requested_steps=35,policy={'fingerprint':'fixed','shared_alpha':[.5,1.]})}
        self.a=Requests(inference=None,samples={'fixture':self.base},profile='profile',roles=self.roles,schedules=[dict(requested_steps=n,actual_updates=n+1) for n in (26,35)],common={})
        self.slot=dict(id='a',member='fixture',role='N',seed=0,actual_updates=27)
    def test_legacy_assignment_fails(self):
        with self.assertRaisesRegex(ValueError,'frozen'):self.base.seed=0
    def test_reconstruction_preserves_all_other_fields(self):
        before=self.base.model_dump();r=request_variant(self.base,seed=19,num_steps=26)
        self.assertEqual(r.model_dump(),dict(before,seed=19,num_steps=26));self.assertEqual(self.base.model_dump(),before)
        with self.assertRaises(ValueError):r.seed=0
        r.data['nested']['x'].append(2);self.assertEqual(self.base.data['nested']['x'],[1])
    def test_invalid_override_rejected(self):
        for seed,n in [(True,26),('0',26),(0,0),(0,False),(0,26.)]:
            with self.subTest(seed=seed,n=n),self.assertRaises(ValueError):request_variant(self.base,seed=seed,num_steps=n)
    def test_mutable_fixtures_rejected(self):
        with self.assertRaises(TypeError):request_variant(types.SimpleNamespace(seed=0),seed=0,num_steps=26)
        class Mutable(Frozen):model_config={'frozen':False}
        with self.assertRaises(TypeError):request_variant(Mutable(self.base.data),seed=0,num_steps=26)
    def test_validator_side_effect_detected(self):
        class Bad(Frozen):
            @classmethod
            def model_validate(cls,data):data['prompt']='changed';return cls(data)
        with self.assertRaises(ValueError):request_variant(Bad(self.base.data),seed=0,num_steps=26)
    def test_preload_validation_does_not_attempt_or_execute(self):
        self.assertEqual(self.a.validate_slots([self.slot])[0].num_steps,26);self.assertFalse(self.a.seen)
        with self.assertRaises(ValueError):self.a.validate_slots([self.slot,self.slot])
    def test_native_and_policy_dispatch_preserve_identity(self):
        calls=[]
        def execute(inference,sample,**kw):calls.append((sample,kw));return 'ok'
        modules={f'wcomr.policy_generator_r1.{name}':types.SimpleNamespace(execute=execute) for name in ('p2_native_sampling','production_sampling')}
        with patch.dict(sys.modules,modules):
            self.assertEqual(self.a(self.slot,'unused'),'ok')
            self.assertEqual(self.a(dict(self.slot,id='b',role='P',actual_updates=36),'unused'),'ok')
            with self.assertRaises(ValueError):self.a(self.slot,'unused')
        self.assertEqual([c[0].num_steps for c in calls],[26,35]);self.assertIs(calls[1][1]['policy'],self.roles['P']['policy'])
        self.assertEqual(self.base.num_steps,35)
    def test_failed_attempt_cannot_replay(self):
        slot=dict(self.slot,actual_updates=99)
        with self.assertRaises(ValueError):self.a(slot,'unused')
        with self.assertRaisesRegex(ValueError,'already attempted'):self.a(self.slot,'unused')
    def test_engine_error_retained(self):
        def fail(*a,**kw):raise OSError('injected writer')
        with patch.dict(sys.modules,{'wcomr.policy_generator_r1.p2_native_sampling':types.SimpleNamespace(execute=fail)}):
            with self.assertRaisesRegex(OSError,'writer'):self.a(self.slot,'unused')
        with self.assertRaisesRegex(ValueError,'already attempted'):self.a(self.slot,'unused')
    def test_unknown_role_or_schedule_not_silently_substituted(self):
        for slot in [dict(self.slot,role='missing'),dict(self.slot,member='missing')]:
            with self.assertRaises(KeyError):self.a.prepare(slot)
        self.roles['N']['kind']='unknown'
        with self.assertRaises(ValueError):self.a.prepare(self.slot)

if __name__=='__main__':unittest.main()
