"""Streaming terminal VJP controls; declared toy metric, no pretrained claim."""
import unittest

import torch

from wcomr.cara_read_write_terminal_r1 import StreamingAlexTerminal, float_rgb
from wcomr.cara_read_write_vae_r1 import FunctionalWan21Decode
from test_cara_read_write_vae_r1 import fixture, RUNTIME

METRICS = {}


class TinyFeatureLoss(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.scale = torch.nn.Parameter(torch.tensor(.7), requires_grad=False)

    def forward(self, candidate, reference):
        return ((candidate.sin()-reference.sin()).square()*self.scale).mean(dim=(1,2,3), keepdim=True)


def direct(alex, candidate, reference):
    return sum(alex(float_rgb(candidate[:, :, i])*2-1,
                    float_rgb(reference[:, :, i])*2-1).reshape(-1).mean().double()
               for i in range(93))/93


class Terminal(unittest.TestCase):
    def videos(self):
        value = torch.linspace(-.8, .9, 3*93*4*5, dtype=torch.float64).reshape(1,3,93,4,5)
        return value, value*.8-.03

    def test_complete93_value_and_gradient_match_direct_graph(self):
        alex = TinyFeatureLoss().eval()
        objective = StreamingAlexTerminal(alex, geometry=(4,5))
        x, native = self.videos();x.requires_grad_()
        loss = objective.loss(x, native)
        gradient = torch.autograd.grad(loss, x)[0]
        expected = direct(alex, x, native)
        reference_gradient = torch.autograd.grad(expected, x)[0]
        self.assertEqual(float(loss), float(expected))
        self.assertTrue(torch.equal(gradient, reference_gradient))
        METRICS['full93_stream_equals_direct'] = dict(value=float(loss), gradient_max_error=0.,
            actual_Alex_weights=False, active_metric_graph_frames=1)

    def test_clipped_pixels_have_zero_gradient_and_complete_direction_matches_FD(self):
        objective = StreamingAlexTerminal(TinyFeatureLoss().eval(), geometry=(4,5))
        x, native = self.videos();x[:, :, :, 0, 0] = 1.3;x.requires_grad_()
        loss = objective.loss(x, native);gradient = torch.autograd.grad(loss, x)[0]
        self.assertEqual(float(gradient[:, :, :, 0, 0].abs().sum()), 0.)
        direction = torch.full_like(x, .02)
        epsilon = .01
        with torch.no_grad():
            high = direct(objective.alex, x+epsilon*direction, native)
            low = direct(objective.alex, x-epsilon*direction, native)
        numerical = float((high-low)/(2*epsilon));predicted = float((gradient*direction).sum())
        self.assertAlmostEqual(predicted, numerical, delta=2e-6)
        METRICS['terminal_direction'] = dict(predicted=predicted, central_FD=numerical,
            absolute_error=abs(predicted-numerical), epsilon=epsilon, clipped_pixel_gradient_zero=True)

    def test_causal_VAE_to_streamed_terminal_chain_matches_direct(self):
        adapter = FunctionalWan21Decode(fixture(), runtime=RUNTIME)
        alex = TinyFeatureLoss().eval();objective = StreamingAlexTerminal(alex, geometry=(16,24))
        x = torch.linspace(-.1, .1, 16*24*2*3, dtype=torch.float64).reshape(1,16,24,2,3).requires_grad_()
        with torch.no_grad():native = adapter.decode(x*.9-.01)
        video = adapter.decode(x)
        loss = objective.loss(video, native)
        gradient = torch.autograd.grad(loss, x)[0]
        expected = direct(alex, adapter.decode(x), native)
        reference_gradient = torch.autograd.grad(expected, x)[0]
        self.assertEqual(float(loss), float(expected))
        self.assertTrue(torch.equal(gradient, reference_gradient))
        METRICS['causal_VAE_terminal_chain'] = dict(full_frames=93, gradient_max_error=0.,
            actual_pretrained_VAE=False, actual_Alex_weights=False)

    def test_partial_video_trainable_metric_or_reference_gradient_refused(self):
        alex = TinyFeatureLoss().eval();objective = StreamingAlexTerminal(alex, geometry=(4,5))
        x, native = self.videos()
        with self.assertRaisesRegex(ValueError, 'Complete same-geometry'):
            objective.value_and_vjp(x[:, :, :92], native[:, :, :92])
        with self.assertRaisesRegex(ValueError, 'constant Native'):
            objective.value_and_vjp(x, native.requires_grad_())
        alex.scale.requires_grad_()
        with self.assertRaisesRegex(ValueError, 'Frozen eval'):
            objective.value_and_vjp(x, native.detach())


if __name__ == '__main__':
    torch.set_num_threads(2)
    unittest.main()
