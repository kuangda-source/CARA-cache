"""Views/aliases, complete native fields and strict resource refusal on CPU."""
from types import SimpleNamespace
import unittest

import numpy as np
import torch

from wcomr.sq_s_resources_r1 import inventory,before_pair_inventory,check_limits,registered_experiment,explicit_meta_constructor


class ResourceTests(unittest.TestCase):
    def test_explicit_meta_device_preserves_original_class_and_restores_constructor(self):
        class DeviceRequired(torch.nn.Module):
            def __init__(self,n,*,device=None):
                super().__init__()
                if device is None:raise RuntimeError('This original default would request CUDA')
                self.weight=torch.nn.Parameter(torch.empty(n,device=device))
        original=DeviceRequired.__init__
        with explicit_meta_constructor(DeviceRequired) as state:
            module=DeviceRequired(128)
            self.assertIs(type(module),DeviceRequired)
            self.assertEqual(module.weight.device.type,'meta')
            with self.assertRaises(ValueError):DeviceRequired(128,device='cpu')
        self.assertIs(DeviceRequired.__init__,original)
        self.assertTrue(state['restored']);self.assertEqual(state['calls'],1)
        with self.assertRaises(RuntimeError):DeviceRequired(128)

    def test_experiment_lookup_never_resolves_checkpoint_path(self):
        class Checkpoint:
            experiment='FROZEN_CPU_EXPERIMENT'
            @property
            def path(self):raise AssertionError('Checkpoint path/download must not be resolved')
        kwargs=dict(expected_model='CPU_MODEL',expected_experiment='FROZEN_CPU_EXPERIMENT')
        self.assertEqual(registered_experiment('CPU_MODEL',{'CPU_MODEL':'k'},{'k':Checkpoint()},**kwargs),
            'FROZEN_CPU_EXPERIMENT')
        with self.assertRaises(ValueError):registered_experiment('OTHER',{}, {},**kwargs)

    def test_references_objects_and_full_backing_storage_are_distinct(self):
        value=torch.zeros(16);view=value[2:5]
        report=inventory(dict(original=value,alias=value,view=view))
        self.assertEqual(report['logical_tensor_bytes'],(16+16+3)*4)
        self.assertEqual(report['unique_tensor_objects'],2)
        self.assertEqual(report['unique_tensor_storages'],1)
        self.assertEqual(report['backing_storage_bytes_by_device'],{'cpu':64})
        self.assertEqual(report['tensors'][2]['storage_offset'],2)
        self.assertFalse(report['tensor_values_read'])

    def test_meta_inventory_records_virtual_bytes_without_admitting_real_execution(self):
        value=torch.empty(1,24,27,48,2048,device='meta',dtype=torch.bfloat16)
        report=inventory(value)
        self.assertEqual(report['logical_tensor_bytes'],127401984)
        self.assertTrue(report['any_meta_tensors'])
        with self.assertRaisesRegex(ValueError,'meta inventory'):check_limits(report,{})

    def test_all_copy_groups_reconcile_and_unknown_types_refuse(self):
        x=torch.zeros(2,3);net=torch.nn.Linear(3,3)
        net.residual_window=[[x,x],[x,x]];net.previous_output=[x,x]
        net.affline_emb=x;net.crossattn_emb=x;net.affline_scale_log_info={'t_embedding_B_T_D':x}
        scheduler=SimpleNamespace(model_outputs=[x],sigmas=torch.ones(3),cache=np.arange(4),method=lambda:None)
        owner=SimpleNamespace(net=net,model=SimpleNamespace(sample_scheduler=scheduler),history=[],
            readout=SimpleNamespace(history=[],completed=7,calibrators=[SimpleNamespace(anchors=[x])]))
        condition=SimpleNamespace(crossattn_emb=x)
        report=before_pair_inventory(owner,(x,x,torch.zeros(1),[condition]))
        self.assertIn('previous_output',report['native_field_names'])
        self.assertIn('affline_emb',report['native_field_names'])
        self.assertIn('cache',report['solver_field_names'])
        self.assertEqual(report['numpy_backing_bytes'],32)
        self.assertEqual(report['logical_copy_guard_bytes'],8*report['logical_tensor_bytes'])
        self.assertEqual(inventory((torch.device('cpu'),torch.float32,np.bool_(True)))['logical_tensor_bytes'],0)
        with self.assertRaises(TypeError):inventory(dict(unregistered=object()))

    def test_numpy_views_are_counted_once_separately_from_torch_logical_bytes(self):
        x=np.zeros(128,dtype=np.float32)
        report=inventory((x,x[1:4]))
        self.assertEqual(report['numpy_backing_bytes'],512)
        self.assertEqual(report['logical_tensor_bytes'],0)

    def test_registered_limits_refuse_before_snapshot_and_do_not_read_values(self):
        report=dict(any_meta_tensors=False,logical_copy_guard_bytes=1024,
            group_inventories=dict(buffers=dict(logical_tensor_bytes=8)),
            backing_storage_bytes_by_device={'cpu':256})
        limits=dict(logical_copy_guard_bytes=1024,mutable_buffer_bytes=8,
            live_backing_storage_bytes_by_device_kind={'cpu':256})
        self.assertTrue(check_limits(report,limits)['accepted'])
        for key in ('logical_copy_guard_bytes','mutable_buffer_bytes','live_backing_storage_bytes_by_device_kind'):
            bad=dict(limits);bad[key]={'cpu':255} if key.endswith('device_kind') else limits[key]-1
            with self.assertRaises(ValueError):check_limits(report,bad)

    def test_no_finite_scan_or_clone_is_hidden_in_the_inventory(self):
        value=torch.tensor([float('nan')])
        report=inventory(value)
        self.assertEqual(report['logical_tensor_bytes'],4)
        self.assertFalse(report['tensor_values_read'])
        self.assertEqual(report['tensor_copies_performed'],0)


if __name__=='__main__':unittest.main()
