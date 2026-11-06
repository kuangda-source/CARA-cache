import copy
import unittest
from wcomr.policy_price_mode_guard_r1 import ModeGuard
from wcomr.policy_asset_price_review_r1 import exclusive_gate


class ModeGuardTest(unittest.TestCase):
    def setUp(self):
        self.s=dict(gpu_uuid='GPU-test',compute_mode='Default',compute_apps=[],mps_processes=[],observed_unix=5)
        self.calls=[]
    def query(self,u):self.assertEqual(u,'GPU-test');return copy.deepcopy(self.s)
    def change(self,u,m):
        self.calls.append((u,m));self.s['compute_mode']={'EXCLUSIVE_PROCESS':'Exclusive_Process','DEFAULT':'Default'}[m]
    def guard(self):return ModeGuard('GPU-test',self.query,self.change,lambda:5)
    def test_only_selected_idle_mode_then_safe_restore(self):
        g=self.guard();self.assertTrue(g.acquire()['changed']);self.assertTrue(g.restore()['restored'])
        self.assertEqual(self.calls,[('GPU-test','EXCLUSIVE_PROCESS'),('GPU-test','DEFAULT')])
    def test_busy_or_MPS_or_stale_never_mutates(self):
        for key,value in [('compute_apps',[{'pid':123}]),('mps_processes',[123]),('observed_unix',-100)]:
            old=self.s[key];self.s[key]=value
            with self.assertRaises(ValueError):self.guard().acquire()
            self.s[key]=old
        self.assertEqual(self.calls,[])
    def test_foreign_arrival_blocks_restoration_without_touching_it(self):
        g=self.guard();g.acquire();self.s['compute_apps']=[{'pid':123}]
        self.assertFalse(g.restore()['restored']);self.assertEqual(len(self.calls),1)
    def test_unsupported_hardware_never_passes(self):
        g=ModeGuard('GPU-test',self.query,lambda *a:None,lambda:5)
        with self.assertRaises(ValueError):g.acquire()
    def test_prior_exclusive_is_preserved(self):
        self.s['compute_mode']='Exclusive_Process';g=self.guard();g.acquire();g.restore()
        self.assertEqual(self.calls,[])
    def test_exact_runner_not_same_uid_or_pid_alone(self):
        self.s.update(compute_mode='Exclusive_Process',compute_apps=[dict(pid=42,uid=1000,start_ticks=99)])
        for runner in [dict(pid=43,uid=1000,start_ticks=99),dict(pid=42,uid=1000,start_ticks=98)]:
            self.assertFalse(exclusive_gate(self.s,gpu_uuid='GPU-test',phase='active',runner=runner,now=5)['observation_passed'])
        self.assertTrue(exclusive_gate(self.s,gpu_uuid='GPU-test',phase='active',runner=self.s['compute_apps'][0],now=5)['observation_passed'])

if __name__=='__main__':unittest.main()
