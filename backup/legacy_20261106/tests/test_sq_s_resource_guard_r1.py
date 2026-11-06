"""Pre-snapshot storage/schema refusals and original-entry restoration."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import torch

from wcomr.sq_s_batch_r1 import Requests,digest
from wcomr.sq_s_resource_guard_r1 import ResourceGuard,ResourceCheckedRequests,checked_collector
from wcomr.sq_s_resources_r1 import inventory

ROOT=Path(__file__).resolve().parents[1]


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.contract=json.loads((ROOT/'plans/cara_next_stage_20261028/sq/S_RESOURCE_GUARD_CPU_CONTRACT_R1.json').read_text())
        self.report=json.loads((ROOT/'tests/fixtures/sq_s_resource_guard_tiny_metadata_r1.json').read_text())

    def guard(self,change=None):
        contract=copy.deepcopy(self.contract)
        if change:change(contract)
        contract['contract_sha256']=digest({k:v for k,v in contract.items() if k!='contract_sha256'})
        return ResourceGuard(contract)

    def test_original_complete_metadata_has_no_value_reads_or_GPU_admission(self):
        result=self.guard().check_metadata(self.report,[])
        self.assertTrue(result['all_eight_groups_checked'])
        self.assertFalse(result['tensor_values_read']);self.assertEqual(result['tensor_copies_performed'],0)
        self.assertFalse(result['GPU_admission'])

    def test_contract_byte_change_refuses(self):
        self.contract['limits']['logical_copy_guard_bytes']+=1
        with self.assertRaisesRegex(ValueError,'bytes changed'):ResourceGuard(self.contract)

    def test_unknown_tensor_field_refuses(self):
        self.report['group_inventories']['native']['tensors'][0]['path']='root/new_tensor_field'
        with self.assertRaisesRegex(ValueError,'tensor schema'):self.guard().check_metadata(self.report,[])

    def test_view_backing_cap_refuses_even_when_logical_bytes_fit(self):
        backing=torch.zeros(2**18);view=backing[:4096].reshape(1,2,16,16,8)
        group=inventory(dict(residual_cache=[view]))
        self.assertEqual(group['logical_tensor_bytes'],16384)
        self.assertEqual(group['backing_storage_bytes_by_device'],{'cpu':2**20})
        self.report['group_inventories']['native']=group
        groups=self.report['group_inventories'].values()
        self.report['logical_copy_guard_bytes']=8*sum(g['logical_tensor_bytes'] for g in groups)
        self.report['backing_storage_bytes_by_device']={'cpu':sum(
            g['backing_storage_bytes_by_device'].get('cpu',0) for g in groups)}
        guard=self.guard(lambda c:c['limits'].update(backing_copy_guard_bytes=4*2**20))
        self.assertLess(self.report['logical_copy_guard_bytes'],self.contract['limits']['logical_copy_guard_bytes'])
        with self.assertRaisesRegex(ValueError,'backing-storage copy cap'):guard.check_metadata(self.report,[])

    def test_logical_live_storage_and_buffer_caps_refuse(self):
        for kind in ('logical','live','buffers'):
            report=copy.deepcopy(self.report)
            if kind=='logical':report['logical_copy_guard_bytes']=129*2**20
            elif kind=='live':report['backing_storage_bytes_by_device']={'cpu':17*2**20}
            else:report['group_inventories']['buffers']['logical_tensor_bytes']=1
            with self.subTest(kind=kind),self.assertRaises(ValueError):self.guard().check_metadata(report,[])

    def test_unregistered_numpy_storage_refuses(self):
        self.report['numpy_backing_bytes']=8
        with self.assertRaisesRegex(ValueError,'NumPy'):self.guard().check_metadata(self.report,[])

    def test_meta_inventory_never_admits_real_snapshots(self):
        self.report['any_meta_tensors']=True
        with self.assertRaisesRegex(ValueError,'meta inventory'):self.guard().check_metadata(self.report,[])

    def test_shape_dtype_and_grad_changes_refuse(self):
        for key,value in [('shape',[1]),('dtype','torch.float64'),('requires_grad',True)]:
            report=copy.deepcopy(self.report);report['group_inventories']['native']['tensors'][0][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'tensor schema'):
                self.guard().check_metadata(report,[])

    def test_complete_native_solver_and_buffer_name_sets_required(self):
        for key in ('native_field_names','solver_field_names','buffer_names'):
            report=copy.deepcopy(self.report);buffers=[]
            if key=='buffer_names':buffers=['new_buffer']
            else:report[key].append('new_field')
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'fields changed'):
                self.guard().check_metadata(report,buffers)

    def test_guard_runs_before_original_budget_and_preserves_its_return(self):
        order=[]
        class Base:
            def copy_budget(self,inputs):order.append('original');return 8
        class Guard:
            def before_pair(self,*args):order.append('guard');return dict(original_logical_copy_guard_bytes=8)
        cls=checked_collector(Base,Guard(),lambda row:order.append(('record',row['step'])))
        collector=cls();collector.owner=SimpleNamespace(readout=SimpleNamespace(completed=7))
        self.assertEqual(collector.copy_budget(None),8)
        self.assertEqual(order,['guard','original',('record',8)])

    def test_guard_refusal_prevents_original_budget_and_snapshot_entry(self):
        order=[]
        class Base:
            def copy_budget(self,inputs):order.append('original');raise AssertionError('Must not enter')
        class Guard:
            def before_pair(self,*args):raise ValueError('resource refused before snapshot')
        cls=checked_collector(Base,Guard(),lambda row:order.append('record'))
        collector=cls();collector.owner=None
        with self.assertRaisesRegex(ValueError,'before snapshot'):collector.copy_budget(None)
        self.assertEqual(order,[])

    def test_original_collection_global_restored_after_request_failure(self):
        from wcomr import sq_s_collection_r1 as collection
        original=collection.execute
        request=ResourceCheckedRequests.__new__(ResourceCheckedRequests)
        request.resource_guard=None;request.resource_checks=[];request.resource_observer=None
        def failed(*args):
            self.assertIsNot(collection.execute,original)
            raise RuntimeError('controlled request failure')
        with patch.object(Requests,'__call__',failed):
            with self.assertRaisesRegex(RuntimeError,'controlled request failure'):
                request(dict(id='x',prompt='p',parent='F19-C',enabled=True),None)
        self.assertIs(collection.execute,original)

    def test_CPU_fixture_cannot_select_real_contract(self):
        real=json.loads((ROOT/'plans/cara_next_stage_20261028/sq/S_RESOURCE_GUARD_REAL_CONTRACT_R1.json').read_text())
        def initialized(request,**kwargs):
            request.scope=dict(CPU_fixture_only=True);request.copy_cap=real['limits']['logical_copy_guard_bytes']
        with patch.object(Requests,'__init__',initialized):
            with self.assertRaisesRegex(ValueError,'CPU/real resource scope'):
                ResourceCheckedRequests(resource_contract=real)


if __name__=='__main__':unittest.main()
