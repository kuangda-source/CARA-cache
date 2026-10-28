"""Capture S's two true-D sources strictly before the current parent pair.

Calibrator anchors already own cloned true-D p/r. Retain those old objects
when the parent appends its current D; do not borrow the post-D anchor list.
Full shadow transactions, tensor ownership inventory and OFF/ON acceptance
remain the production collector's responsibilities.
"""
from dataclasses import dataclass

import torch

from .sq_risk_r1 import F19, TARGETS
from .sq_q1_readout_r1 import source_from_anchors

SHARED25 = tuple(range(1,22))+(24,27,30,36)
PARENTS = {'Shared25-C':SHARED25,'F19-C':F19}


@dataclass(frozen=True)
class PastSources:
    parent: str
    context: tuple
    step: int
    anchor_steps: tuple
    anchors: tuple
    versions: tuple
    native_window_lengths: tuple

    def source(self):
        for value,version in self.versions:
            if version is not None and value._version != version:
                raise ValueError('Captured true-D source was mutated after the pre-pair boundary')
        return source_from_anchors(self.anchors)

    def metadata(self):
        return dict(parent=self.parent,context=list(self.context),step=self.step,
            source_anchor_steps=list(self.anchor_steps),source_captured_before_parent_pair=True,
            current_D_in_source=False,native_window_lengths=list(self.native_window_lengths),
            consumed_anchor_slots=2,inference_tensors_without_version=sum(v is None for _,v in self.versions),
            complete_shadow_transaction_accepted=False,deployment_memory_measured=False)


def capture_before_pair(owner, *, parent, step):
    """Read only at a healthy quiescent production-owner boundary."""
    if parent not in PARENTS or type(step) is not int or step not in TARGETS:
        raise ValueError('Registered S parent and target step required')
    readout,net,policy = owner.readout,owner.net,owner.policy
    if (readout.current is not None or readout.completed != step-1
            or len(owner.history) != step-1 or net.cnt != 2*(step-1)%70
            or net.worldcache_num_steps != 70 or readout.poisoned or owner.executor.poisoned):
        raise ValueError('S source capture must occur before the current parent pair')
    if (owner.model.net is not net or readout.net is not net or readout.policy is not policy
            or readout.context[-1] != policy['fingerprint']
            or tuple(t for t,is_dense in enumerate(policy['dense_mask'],1) if is_dense) != PARENTS[parent]
            or any(a not in ('D','C') for a in policy['actions'])):
        raise ValueError('S parent/context/policy binding differs')
    expected = tuple(t for t in PARENTS[parent] if t<step)[-2:]
    anchors = tuple(tuple(c.anchors) for c in readout.calibrators)
    if len(anchors) != 2 or any(len(pair)!=2 or tuple(a.step for a in pair)!=expected for pair in anchors):
        raise ValueError('Exactly the two strictly past true-D anchors required')
    versions, lengths = [],[]
    for branch,(calibrator,pair) in enumerate(zip(readout.calibrators,anchors)):
        if calibrator.context != readout.context:
            raise ValueError('Source calibrator belongs to a different request/model/policy')
        physical_r,physical_p = net.residual_window[branch],net.probe_residual_window[branch]
        if len(physical_r)<2 or len(physical_p)!=len(physical_r):
            raise ValueError('Two complete native p/r window slots required')
        lengths.append(len(physical_r))
        for index,anchor in enumerate(pair):
            for value,physical in ((anchor.residual,physical_r[-2+index]),(anchor.probe,physical_p[-2+index])):
                if value.dtype!=physical.dtype or value.device!=physical.device or not torch.equal(value,physical):
                    raise ValueError('Calibrator source differs from the actual native true-D window')
                versions.append((value,None if torch.is_inference(value) else value._version))
    return PastSources(parent,readout.context,step,expected,anchors,tuple(versions),tuple(lengths))
