"""Pre-D causality controls using real calibrators and compiled CPU policies."""
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

import torch

from wcomr.calibration import ResidualCalibrator
from wcomr.policy_generator_r1.interval_grammar import Profile, Edge, compile_policy
from wcomr.sq_s_sources_r1 import PARENTS, capture_before_pair

ROOT = Path(__file__).resolve().parents[1]


def fixture(parent='F19-C',step=8):
    data=json.loads((ROOT/'manifests/cara_DEV128_scope_r1_20261026.json').read_text())['profile']
    data['protected_dense']=tuple(data['protected_dense']);data['alpha_candidates']=tuple(data['alpha_candidates'])
    profile=Profile(**data);dense=PARENTS[parent];bounds=dense+(37,)
    policy=compile_policy(profile,[Edge(a,b) for a,b in zip(bounds,bounds[1:])])
    context=('EXPLICIT_CPU_PROMPT','DECLARED_CPU_WEIGHTS',policy['fingerprint'])
    calibrators=[]
    for branch in (0,1):
        c=ResidualCalibrator();c.reset(context)
        for t in [v for v in dense if v<step][-2:]:
            c.observe_full(context=context,step=t,probe=torch.full((1,2,2,2,4),float(t+branch)),
                           residual=torch.full((1,2,2,2,4),float(2*t+branch)))
        calibrators.append(c)
    net=SimpleNamespace(cnt=2*(step-1)%70,worldcache_num_steps=70,
        residual_window=[[torch.zeros(1)]+[a.residual.clone() for a in c.anchors] for c in calibrators],
        probe_residual_window=[[torch.zeros(1)]+[a.probe.clone() for a in c.anchors] for c in calibrators])
    readout=SimpleNamespace(net=net,policy=policy,context=context,completed=step-1,current=None,
        poisoned=False,calibrators=calibrators)
    return SimpleNamespace(net=net,model=SimpleNamespace(net=net),readout=readout,
        policy=policy,history=[None]*(step-1),executor=SimpleNamespace(poisoned=False))


class SourceTests(unittest.TestCase):
    def test_current_D_cannot_enter_pre_pair_sources(self):
        owner=fixture();past=capture_before_pair(owner,parent='F19-C',step=8)
        for c in owner.readout.calibrators:
            c.observe_full(context=c.context,step=8,probe=torch.full_like(c.anchors[-1].probe,100.),
                           residual=torch.full_like(c.anchors[-1].residual,200.))
        source=past.source()
        self.assertEqual(past.anchor_steps,(6,7))
        self.assertEqual([a.step for a in owner.readout.calibrators[0].anchors],[7,8])
        self.assertEqual(float(source[0]['residual'].mean()),14.)
        self.assertIs(source[0]['residual'],source[0]['residual_window'][-1])
        self.assertEqual(past.metadata()['native_window_lengths'],[3,3])
        self.assertFalse(past.metadata()['current_D_in_source'])

    def test_capture_after_current_D_is_refused(self):
        owner=fixture();owner.readout.completed=8;owner.net.cnt=16;owner.history.append(None)
        with self.assertRaisesRegex(ValueError,'before the current parent pair'):
            capture_before_pair(owner,parent='F19-C',step=8)

    def test_parent_context_or_physical_window_mismatch_is_refused(self):
        for issue in ('parent','context','physical'):
            owner=fixture()
            if issue=='context':owner.readout.calibrators[0].context=('WRONG_CONTEXT',)
            if issue=='physical':owner.net.residual_window[0][-1].add_(1)
            with self.assertRaises(ValueError):
                capture_before_pair(owner,parent='Shared25-C' if issue=='parent' else 'F19-C',step=8)

    def test_captured_source_mutation_is_refused(self):
        owner=fixture();past=capture_before_pair(owner,parent='F19-C',step=8)
        past.anchors[0][-1].residual.add_(1)
        with self.assertRaisesRegex(ValueError,'mutated after the pre-pair boundary'):past.source()

    def test_both_parents_have_their_actual_past_history_at_C_targets(self):
        for parent,step,expected in [('Shared25-C',22,(20,21)),('F19-C',9,(7,8)),('F19-C',33,(27,30))]:
            owner=fixture(parent,step)
            value=capture_before_pair(owner,parent=parent,step=step)
            self.assertEqual(value.anchor_steps,expected)
            self.assertEqual(value.step,step)


if __name__=='__main__':unittest.main()
