"""Fixed two-scale innovation proposals through the existing isolated adapter.

No teacher selection, anchor writes, scheduler changes or dispatch. Hidden
features use the pinned production B,T,H,W,D layout, not the synthetic
attachment's channels-first layout. Gain endpoints execute the existing
FULL/DEEP expressions to preserve their floating-point operation order.
"""
import math
from types import SimpleNamespace

import torch
import torch.nn.functional as F

from .cfg_guided_w1_outputs import shared_output_fusion
from .policy_interval_readout_r1 import ReadoutKernel
from .scout_readout_v22 import ScoutReadoutKernel, UnsupportedReadout, _tensors, proposal


def gains_checked(gains):
    if len(gains) != 2 or any(type(k) not in (float, int) or not math.isfinite(k)
                             or not 0 <= k <= 1 for k in gains):
        raise UnsupportedReadout('R1 requires two finite shared gains in [0,1]')
    return tuple(float(k) for k in gains)


@torch.no_grad()
def project_spatial_blocks(x):
    """Disjoint 2x2 mean/replication; real partial edge area, BTHWD only."""
    _tensors(x)
    if x.ndim != 5:
        raise UnsupportedReadout('Actual B,T,H,W,D token grid required')
    b, t, h, w, d = x.shape
    # Move feature channels out of the spatial pool. No temporal mixing.
    work = x.permute(0, 1, 4, 2, 3).reshape(b*t, d, h, w)
    accumulation = work.double() if x.dtype == torch.float64 else work.float()
    low = F.avg_pool2d(accumulation, 2, 2, ceil_mode=True, count_include_pad=False)
    low = low.repeat_interleave(2, -2).repeat_interleave(2, -1)[..., :h, :w]
    return low.reshape(b, t, d, h, w).permute(0, 1, 3, 4, 2).to(x.dtype).contiguous()


@torch.no_grad()
def gain_proposal(current_probe, older, latest, *, ratio, gains, age):
    low_gain, high_gain = gains_checked(gains)
    full, _ = proposal('FULL', current_probe, older, latest, kappa=ratio, age=age)
    if (low_gain, high_gain) == (0., 0.):
        return full
    if (low_gain, high_gain) == (1., 1.):
        return proposal('R4_GLOBAL', current_probe, older, latest, kappa=ratio, age=age)[0]
    predicted_probe = latest.probe + ratio*(latest.probe-older.probe)
    innovation = current_probe-predicted_probe
    result = full + high_gain*innovation
    if low_gain != high_gain:
        result = result+(low_gain-high_gain)*project_spatial_blocks(innovation)
    if not bool(torch.isfinite(result).all()):
        raise UnsupportedReadout('Nonfinite innovation proposal')
    return result


class InnovationGainKernel(ScoutReadoutKernel):
    """One immutable coefficient pair; reuse the accepted isolation wrapper.

The wrapper's FULL label is only its validation/transaction entry. This class
replaces its numerical implementation, and returns its distinct IG identity.
It is never installed into an already registered E1 card implicitly.
"""
    def __init__(self, *args, gains, **kwargs):
        super().__init__(*args, **kwargs)
        self.gains = gains_checked(gains)

    def evaluate_gain(self, **kwargs):
        value = super().evaluate('FULL', **kwargs)
        value.update(candidate='IG_SCALAR' if self.gains[0] == self.gains[1] else 'IG_BAND',
                     gains=list(self.gains), gain_shared_CFG=True,
                     projection='DISJOINT_2X2_BTHWD_REAL_BOUNDARY_AREA')
        return value

    def _evaluate(self, label, spans, anchors, current, pair_inputs):
        if self.gains in ((0., 0.), (1., 1.)):
            return super()._evaluate('FULL' if self.gains == (0., 0.) else 'R4_GLOBAL',
                                     spans, anchors, current, pair_inputs)
        source = [dict(probe=b.probe, residual=b.residual,
                       residual_window=[o.residual, b.residual], probe_window=[o.probe, b.probe])
                  for o, b in anchors]
        cached, _, _ = ReadoutKernel.run(self, 'C', source=source, current=current, pair_inputs=pair_inputs)
        noise, latent, timestep, conditions = pair_inputs
        outputs = []
        for branch, (older, latest) in enumerate(anchors):
            row = current[branch]
            residual = gain_proposal(row['probe']-row['original'], older, latest,
                                     ratio=spans['kappa'], gains=self.gains, age=spans['age'])
            proxy = SimpleNamespace(cnt=branch, previous_input=[None, None],
                previous_internal_states=[None, None], worldcache_flow_enabled=self.net.worldcache_flow_enabled,
                worldcache_flow_scale=self.net.worldcache_flow_scale)
            proxy.previous_input[branch] = row['original']
            proxy.previous_internal_states[branch] = row['probe']
            hidden = self.warp(proxy, row['original']+residual, latest.residual, row['original'].shape[1])
            head = self.net.unpatchify(self.net.final_layer(hidden, row['embedding'], adaln_lora_B_T_3D=row['adaln']))
            outputs.append(self.to_velocity(self.model, noise, latent, timestep, conditions[branch],
                                            _supplied_net_output=head))
        outputs = tuple(outputs)
        return dict(outputs=shared_output_fusion(cached, outputs, spans['alpha']),
                    component_outputs=outputs, alpha=spans['alpha'],
                    formulas=[dict(raw_formula='FULL+kH*nu+(kL-kH)*P_L(nu)',
                                   ratio_h_over_H=spans['kappa'], gains=list(self.gains)) for _ in (0, 1)])
