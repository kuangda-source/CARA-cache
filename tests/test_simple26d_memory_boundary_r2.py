"""Lifecycle, immutable scope, exception cleanup and RNG controls."""
import copy,gc,json,unittest,weakref
from pathlib import Path
from unittest.mock import patch
import torch
from wcomr import simple26d_memory_r2 as new

class BoundaryTests(unittest.TestCase):
    def fake_install(self,*args,**kw):
        class Owner:pass
        owner=Owner();owner.cycle=owner;owner.tensor=torch.ones(256)
        self.refs.append(weakref.ref(owner));return None,owner,None,None
    def setUp(self):self.refs=[]
    def test_complete_cycles_released_without_changing_result(self):
        marker={'final':torch.arange(8),'actions':['DD']*36}
        def request(*a,**kw):new.clean.install();return marker
        rng=torch.get_rng_state().clone();held=torch.ones(32)
        with patch.object(new.clean,'install',self.fake_install),patch.object(new.legacy,'execute',request):
            result=new.execute()
        self.assertIs(result,marker);self.assertTrue(torch.equal(held,torch.ones(32)))
        self.assertTrue(torch.equal(rng,torch.get_rng_state()))
        self.assertEqual(result['request_memory_lifecycle']['owners_alive_after'],0)
        self.assertIsNone(self.refs[0]());self.assertFalse(torch.cuda.is_initialized())
    def test_original_exception_preserved_and_unreachable_cycle_collected(self):
        def request(*a,**kw):new.clean.install();raise RuntimeError('original guarded failure')
        with patch.object(new.clean,'install',self.fake_install),patch.object(new.legacy,'execute',request):
            with self.assertRaisesRegex(RuntimeError,'original guarded failure'):new.execute()
        gc.collect();self.assertIsNone(self.refs[0]())
    def test_actual_live_owner_rejected(self):
        live=[]
        def request(*a,**kw):live.append(new.clean.install()[1]);return {}
        with patch.object(new.clean,'install',self.fake_install),patch.object(new.legacy,'execute',request):
            with self.assertRaisesRegex(ValueError,'remains reachable'):new.execute()
        self.assertTrue(torch.equal(live[0].tensor,torch.ones(256)))
    def test_complete_frozen_scope_and_negative_changes(self):
        root=Path(__file__).resolve().parents[1];c=json.loads((root/new.CONFIG).read_text());new.validate_contract(c)
        for key,value in [('memory_policy','CLEAR_LIVE_CACHE'),('old28_reference_count',16),('P_enabled',True),('billed_limit_GPUh',12),('methods',c['methods'][:-1]),('requests',c['requests'][:-1])]:
            bad=copy.deepcopy(c);bad[key]=value
            with self.assertRaises((ValueError,AssertionError)):new.validate_contract(bad)

if __name__=='__main__':unittest.main()
