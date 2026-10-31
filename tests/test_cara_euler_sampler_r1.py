import copy
import unittest
from types import SimpleNamespace
import torch
from wcomr.cara_euler_protocol_r1 import reconstructed_grid
from wcomr.cara_euler_sampler_r1 import CosmosEuler35,installed_euler35

class EulerSampler(unittest.TestCase):
    def test_analytic_constant_velocity_and_exact_count(self):
        grid=reconstructed_grid();s=CosmosEuler35(grid);s.set_timesteps(35,device='cpu')
        x=torch.tensor([1.,2.],dtype=torch.float64);initial=x.clone()
        for t in s.timesteps:x=s.step(torch.full_like(x,2),t,x)[0]
        self.assertTrue(torch.allclose(x,initial-2*grid['sigmas'][0],atol=1e-12,rtol=0))
        with self.assertRaises(ValueError):s.step(x,s.timesteps[-1],x)
        with self.assertRaises(ValueError):s.set_timesteps(35,device='cpu')
    def test_changed_grid_or_sampler_options_refused(self):
        grid=reconstructed_grid();grid['sigmas'][3]-=.001
        with self.assertRaises(ValueError):CosmosEuler35(grid)
        for options in [dict(num_steps=36),dict(num_steps=35,shift=1),dict(num_steps=35,use_kerras_sigma=False)]:
            with self.assertRaises(ValueError):CosmosEuler35(reconstructed_grid()).set_timesteps(device='cpu',**options)
    def test_original_ordered_scalar_view_required(self):
        s=CosmosEuler35(reconstructed_grid());s.set_timesteps(35,device='cpu');x=torch.ones(1)
        for wrong in [s.timesteps[1],s.timesteps[0].clone(),s.timesteps[:1]]:
            with self.assertRaises(ValueError):s.step(x,wrong,x)
        self.assertEqual(s._step_index,0)
        s.step(x,s.timesteps[0],x)
        with self.assertRaises(ValueError):s.step(x,s.timesteps[0],x)
    def test_incompatible_tensor_or_return_mode_refused_before_update(self):
        s=CosmosEuler35(reconstructed_grid());s.set_timesteps(35,device='cpu');x=torch.ones(1)
        for velocity in [torch.ones(2),x.double()]:
            with self.assertRaises(ValueError):s.step(velocity,s.timesteps[0],x)
        with self.assertRaises(ValueError):s.step(x,s.timesteps[0],x,return_dict=True)
        self.assertEqual(s._step_index,0)
    def test_scope_restores_original_and_refuses_nesting(self):
        original=object();m=SimpleNamespace(sample_scheduler=original)
        with installed_euler35(m,reconstructed_grid()) as s:
            self.assertIs(m.sample_scheduler,s)
            with self.assertRaises(ValueError):
                with installed_euler35(m,reconstructed_grid()):pass
        self.assertIs(m.sample_scheduler,original)
        with self.assertRaises(RuntimeError):
            with installed_euler35(m,reconstructed_grid()):raise RuntimeError('injected request failure')
        self.assertIs(m.sample_scheduler,original)

if __name__=='__main__':unittest.main()
