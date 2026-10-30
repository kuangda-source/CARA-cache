import unittest
from unittest.mock import patch
from wcomr import cara_budget_original_handles_r1 as reader


class HandleTests(unittest.TestCase):
    def setUp(self):
        self.view=dict(boot_id='12345678-1234-1234-1234-123456789abc',pid_namespace_inode=42)
        self.handle=dict(pid=100,start_ticks=1000,host_view=self.view)
        self.current=dict(pid=100,state='S',start_ticks=1000,command='original')

    def observe(self):
        with patch.object(reader,'host_view',return_value=self.view),patch.object(reader,'process_identity',return_value=self.current):
            return reader.observe_original_process(self.handle)

    def test_same_original_live_and_no_permissions(self):
        for state in ('R','S','D','T'):
            self.current['state']=state;result=self.observe();self.assertTrue(result['original_live'])
            self.assertFalse(result['dispatch_allowed']);self.assertFalse(result['scientific_read_allowed'])
            self.assertFalse(result['financial_settlement_allowed'])

    def test_absent_zombie_and_reused_PID_are_original_not_live(self):
        for state,ticks,reason in [(None,None,'ORIGINAL_PROC_ABSENT'),('Z',1000,'ORIGINAL_PROCESS_ZOMBIE_OR_DEAD'),
                                  ('S',1001,'PID_REUSED_ORIGINAL_PROCESS_EXITED')]:
            self.current.update(state=state,start_ticks=ticks);result=self.observe()
            self.assertFalse(result['original_live']);self.assertEqual(result['reason'],reason)

    def test_wrong_boot_or_namespace_never_reads_pid(self):
        for key,value in [('boot_id','22345678-1234-1234-1234-123456789abc'),('pid_namespace_inode',43)]:
            view={**self.view,key:value}
            with patch.object(reader,'host_view',return_value=view),patch.object(reader,'process_identity') as observe:
                result=reader.observe_original_process(self.handle)
                self.assertIsNone(result['original_live']);observe.assert_not_called()

    def test_observation_errors_and_incomplete_stat_remain_unknown(self):
        for error in (PermissionError('denied'),ValueError('invalid proc stat'),FileNotFoundError('unavailable proc mount')):
            with patch.object(reader,'host_view',side_effect=error):
                self.assertIsNone(reader.observe_original_process(self.handle)['original_live'])
        with patch.object(reader,'host_view',return_value=self.view),patch.object(reader,'process_identity',side_effect=PermissionError('denied')):
            self.assertIsNone(reader.observe_original_process(self.handle)['original_live'])
        self.current.update(state=None,start_ticks=1000);self.assertIsNone(self.observe()['original_live'])

    def test_missing_roles_and_duplicate_handles_refused(self):
        with self.assertRaises(ValueError):reader.observe_original_handles({'guardian':self.handle})
        with self.assertRaises(ValueError):reader.observe_original_handles({role:self.handle for role in reader.ROLES})
        result=reader.observe_original_handles({role:None for role in reader.ROLES})
        self.assertEqual(result['unresolved_handles'],list(reader.ROLES));self.assertFalse(result['all_original_handles_not_live'])

    def test_malformed_original_binding_refused(self):
        for change in ({'pid':True},{'pid':-1},{'start_ticks':None},{'start_ticks':0},{'host_view':{}}):
            with self.subTest(change=change),self.assertRaises(ValueError):reader.observe_original_process({**self.handle,**change})

    def test_all_originals_ended_still_grants_no_billing_or_dispatch(self):
        handles={role:{**self.handle,'pid':100+i} for i,role in enumerate(reader.ROLES)}
        with patch.object(reader,'host_view',return_value=self.view),patch.object(reader,'process_identity',side_effect=lambda pid:dict(pid=pid,state=None,start_ticks=None)):
            result=reader.observe_original_handles(handles)
        self.assertTrue(result['all_original_handles_not_live']);self.assertFalse(result['dispatch_allowed'])
        self.assertFalse(result['financial_settlement_allowed']);self.assertFalse(result['scientific_read_allowed'])


if __name__=='__main__':unittest.main()
