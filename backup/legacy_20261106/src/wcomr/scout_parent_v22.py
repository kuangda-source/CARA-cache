"""Isolated E1 sparse-parent observer. Preparation only; no card dispatcher.

The original Shared25-C action/controller owns the free-running trajectory.
A separate pinned dense executor is a same-state oracle, never a source anchor.
"""
import copy
import hashlib
import json
import math
import sys
import time
import numpy as np
from enum import Enum
import weakref

import torch

from . import clean_speed20_r1 as clean
from .cfg_guided_w1_forward import compile_collection
from .cfg_paired_probe_forward import PairedProbeExecutor
from .full_sampling import CompleteStateRoundtrip
from .mid_coverage import tree_digest, WC_FIELDS
from .partial_mlp_deployment_state import plain, tensor_bytes, DeploymentRoundtrip
from .scout_readout_v22 import (Anchor, D_STEPS, STATE_STEPS, LABELS,
    PARENT_FINGERPRINT, ScoutReadoutKernel, UnsupportedReadout, actual_guided_error)
from .source_phase_fixed_mask_r1 import FixedMaskH1Owner
from .simple26d_memory_r2 import collect_boundary
from .light_sampling import synchronize

# Frozen CAL66 requested35/actual36 schedule; independent of E1 outputs.
GRID_SHA256 = '420d3bb2c4190a4d462df61623e71e0a2fd08216c505872ba15c68318be7e734'
PLAN = tuple('D' if s in D_STEPS else 'C' for s in range(1, 37))


def tensor_record(value):
    """Data-only artifact tree; never pickle live condition/model objects."""
    value = plain(value)
    if isinstance(value, np.ndarray):
        return dict(numpy_dtype=str(value.dtype), numpy_shape=list(value.shape), values=value.tolist())
    if isinstance(value, np.generic): return value.item()
    if isinstance(value, Enum): return tensor_record(value.value)
    if isinstance(value, torch.Tensor): return value.detach().cpu().clone()
    if isinstance(value, dict): return {k:tensor_record(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return type(value)(tensor_record(v) for v in value)
    if value is None or type(value) in (str,int,float,bool): return value
    raise TypeError('Unregistered artifact field: '+type(value).__name__)


def noise_coordinates(scheduler, step, timestep):
    sigmas = [float(v) for v in scheduler.sigmas]
    times = scheduler.timesteps
    if (len(sigmas) != 37 or len(times) != 36 or not 1 <= step <= 36
            or any(not math.isfinite(v) for v in sigmas)
            or sigmas[-1] != 0 or any(a <= b for a, b in zip(sigmas, sigmas[1:]))):
        raise ValueError('Exact full36 descending sigma grid and terminal zero required')
    grid = dict(sigmas=sigmas,timesteps=[int(v) for v in times])
    if hashlib.sha256(json.dumps(grid,sort_keys=True,separators=(',',':')).encode()).hexdigest()!=GRID_SHA256:
        raise ValueError('Actual grid differs from frozen CAL66 grid')
    # Sampler presents the registered timestep, not an inferred step number.
    expected = torch.as_tensor(times[step-1], device=timestep.device, dtype=timestep.dtype)
    if not torch.equal(timestep, expected.expand_as(timestep)):
        raise ValueError('Actual paired timestep differs from scheduler step')
    return [(sigmas[0]-s)/(sigmas[0]-sigmas[-1]) for s in sigmas], sigmas


class DenseObserver:
    def __init__(self): self.features = {}
    def prewarp(self, *args): pass
    def output(self, *args): pass
    def hidden(self, net, skipped, branch, original, probe, hidden, kwargs, embedding, adaln):
        if skipped or branch in self.features:
            raise ValueError('Exactly one actual dense observation per branch required')
        self.features[branch] = dict(original=original.detach().clone(), probe=probe.detach().clone(),
            hidden=hidden.detach().clone(), embedding=embedding.detach().clone(),
            adaln=copy.deepcopy(adaln))


class ScoutParentOwner(FixedMaskH1Owner):
    def __init__(self, *args, scout_enabled, scout_context, scout_sink,
                 scout_copy_cap, scout_fault=None, **kwargs):
        if (len(scout_context) != 3 or scout_context[-1] != PARENT_FINGERPRINT
                or not callable(scout_sink) or type(scout_copy_cap) is not int or scout_copy_cap <= 0):
            raise ValueError('Explicit context, artifact sink and copy budget required')
        super().__init__(*args, replay_plan=PLAN, **kwargs)
        self.enabled, self.scout_context, self.sink = scout_enabled, scout_context, scout_sink
        self.copy_cap, self.fault = scout_copy_cap, scout_fault
        self.bank, self.rows, self.features = {}, [], {}
        self.old_hidden = self.deployment.readout.semantic_hidden
        self.deployment.readout.semantic_hidden = self.capture_hidden
        self.kernel = None

    def capture_hidden(self, net, skipped, branch, original, probe, hidden, kwargs, embedding, adaln):
        if self.enabled:
            step = len(self.history)+1
            # Reference views are consumed before the next real parent pair.
            if step in STATE_STEPS or step in {20, 21, 24, 27, 30}:
                if branch in self.features or skipped != (step not in D_STEPS):
                    raise ValueError('Actual parent action/observation identity mismatch')
                self.features[branch] = dict(original=original, probe=probe,
                    embedding=embedding, adaln=adaln,
                    anchor_probe=net.probe_residual_cache[branch], residual=net.residual_cache[branch])
        return self.old_hidden(net, skipped, branch, original, probe, hidden, kwargs, embedding, adaln)

    def copy_budget(self, pair_inputs):
        value = plain(({k:getattr(self.model.net,k) for k in WC_FIELDS if hasattr(self.model.net,k)},
            {k:v for k,v in vars(self.model.sample_scheduler).items() if not callable(v)},
            list(self.model.net.buffers()), self.own_state(), pair_inputs[:3], [vars(c) for c in pair_inputs[3]], self.bank))
        # Two snapshots plus teacher/input copies are simultaneous. Conservative
        # logical bound, explicitly not a device peak or full-model memory quote.
        logical = 4*tensor_bytes(value)
        if logical > self.copy_cap:
            raise ValueError('Parent diagnostic copy budget exceeded before snapshots')
        return logical

    @torch.no_grad()
    def pair(self, noise, latent, timestep, conditions, choose):
        step = len(self.history)+1
        self.features = {}
        inputs = (noise, latent, timestep, conditions)
        if not self.enabled:
            return super().pair(*inputs, choose)
        xis, sigmas = noise_coordinates(self.model.sample_scheduler, step, timestep)
        selected = step in STATE_STEPS
        if selected:
            self.copy_budget(inputs)
            pre = CompleteStateRoundtrip(self.model.net, self.model.sample_scheduler, latent)
        actual = super().pair(*inputs, choose)
        if self.history[-1]['action'] != ('DD' if step in D_STEPS else 'CC'):
            raise ValueError('Parent deviated from Shared25-C')
        if step in {20, 21, 24, 27, 30}:
            self.bank[step] = tuple(Anchor(self.scout_context, b, step, xis[step-1],
                self.features[b]['anchor_probe'].detach().clone(),
                self.features[b]['residual'].detach().clone()) for b in (0, 1))
        if selected:
            self._observe(step, xis, sigmas, inputs, actual, pre)
        self.features.clear()
        return actual

    def _observe(self, step, xis, sigmas, inputs, actual, pre):
        synchronize(); diagnostic_start=time.perf_counter()
        net, scheduler = self.model.net, self.model.sample_scheduler
        post = CompleteStateRoundtrip(net, scheduler, inputs[1])
        own = DeploymentRoundtrip(self, logical_copy_cap_bytes=self.copy_cap)
        state_before, owner_before = post.fingerprint(), own.origin
        input_before = tree_digest(plain((inputs[:3], [vars(c) for c in inputs[3]])))
        versions = [(p, p._version) for p in net.parameters()]
        current = [copy.deepcopy(self.features[b]) for b in (0, 1)]
        older, latest = [s for s in D_STEPS if s < step][-2:]
        anchors = tuple((self.bank[older][b], self.bank[latest][b]) for b in (0, 1))
        payload = None
        try:
            pre.restore()
            observer = DenseObserver()
            _, denoise, proof = compile_collection(self._runtime, self._wc, self._rf, observer)
            executor = PairedProbeExecutor(self.model, denoise, torch)
            with self.deployment.core.readonly():
                dense = executor.pair(*copy.deepcopy(inputs), lambda _: 'DD')
            dense = tuple(v.detach().clone() for v in dense)
            if set(observer.features) != {0, 1}: raise ValueError('Missing teacher branch')
            if self.fault: self.fault('after_teacher', step, self)
            # P1: the actual dense hidden is replayed through its native head/RF.
            replay = []
            for b in (0, 1):
                row = observer.features[b]
                head = net.unpatchify(net.final_layer(row['hidden'], row['embedding'], adaln_lora_B_T_3D=row['adaln']))
                replay.append(observer.to_velocity(self.model, *inputs[:3], inputs[3][b], _supplied_net_output=head))
            if any(not torch.equal(a,b) for a,b in zip(dense,replay)):
                raise ValueError('Dense hidden/head/RF replay mismatch')
            # Paid prefix must match the same input on the C parent exactly.
            if any(not torch.equal(current[b][key], observer.features[b][key])
                   for b in (0, 1) for key in ('original', 'probe')):
                raise ValueError('Teacher is not on the same paid input/prefix')
            post.restore(); own.restore()
            if self.kernel is None:
                self.kernel = ScoutReadoutKernel(self.model,self._runtime,self._wc,self._rf,
                    self.deployment.warp,max_logical_copy_bytes=self.copy_cap)
            readouts, summaries = {}, {}
            for label in LABELS:
                try:
                    value = self.kernel.evaluate(label,context=self.scout_context,step=step,xi=xis[step-1],
                        anchors=anchors,current=current,pair_inputs=inputs)
                    if label == 'WC_C' and any(not torch.equal(a,b) for a,b in zip(value['outputs'],actual)):
                        raise ValueError('Reconstructed C differs from paid parent output')
                    readouts[label] = value
                    summaries[label] = dict(status='SUPPORTED', **actual_guided_error(value['outputs'],dense))
                except UnsupportedReadout as exc:
                    if label == 'WC_C': raise
                    summaries[label] = dict(status='UNSUPPORTED', reason=str(exc), retained_in_denominator=True)
            payload = dict(context=self.scout_context, step=step,
                pre_pair_checkpoint=dict(WC_cache=pre.net_state,solver=pre.solver_state,
                    python_rng=pre.python_rng,numpy_rng=pre.numpy_rng,torch_cpu_rng=pre.cpu_rng,
                    torch_cuda_rng=pre.cuda_rng,buffers={k:v[1] for k,v in pre.buffers.items()},
                    modes={k:v[1] for k,v in pre.modes.items()},
                    serialized_whole_pipeline_resume_accepted=False), xi=xis[step-1], sigma=sigmas[step-1],
                source_anchor_steps=[older,latest], anchors=anchors,current=current,
                pair_inputs=dict(noise=inputs[0],latent=inputs[1],timestep=inputs[2],
                    conditions=[dict(class_name=type(c).__qualname__,fields=vars(c)) for c in inputs[3]]),
                teacher=dense,teacher_features=observer.features,
                readouts=readouts,summary=summaries,
                state_basis='C_POLICY_STATE_SAME_STATE_COUNTERFACTUAL', teacher_writes_parent=False,
                P0_actual_dense=True,P1_dense_head_RF_equal=True,P2_C_actual_parent_equal=True,
                teacher_pairs=1,extra_replay_head_pairs=1,readout_head_pairs=11,
                source_proof=dict(proof))
        finally:
            post.restore(); own.restore()
            if (post.fingerprint()!=state_before or self.fingerprint()!=owner_before
                    or tree_digest(plain((inputs[:3],[vars(c) for c in inputs[3]])))!=input_before):
                raise RuntimeError('Shadow changed parent state, owner history or conditioning')
            if any(p._version!=v for p,v in versions):
                raise RuntimeError('Shadow mutated model weights')
        # The sink is outside trajectory clocks. Its failure aborts this attempt.
        try:
            self.sink(tensor_record(payload))
        finally:
            post.restore(); own.restore()
            if post.fingerprint()!=state_before or self.fingerprint()!=owner_before:
                raise RuntimeError('Artifact sink changed the parent state')
        synchronize(); diagnostic_seconds=time.perf_counter()-diagnostic_start
        self.rows.append(dict(step=step,source_anchor_steps=[older,latest],
            labels={k:v['status'] for k,v in summaries.items()},
            P0_actual_dense=True,P1_dense_head_RF_equal=True,P2_C_actual_parent_equal=True,
            parent_roundtrip_equal=True,teacher_writes_parent=False,
            diagnostic_seconds_including_teacher_readouts_copy_hash_sink=diagnostic_seconds,
            diagnostic_clock_excludes_pre_pair_snapshot=True))

    def close(self):
        self.deployment.readout.semantic_hidden = self.old_hidden
        self.bank.clear(); self.features.clear(); self.kernel=None
        return super().close()


def execute(inference, sample, *, enabled, context, sink, copy_cap,
            table_parameters, previous_parameters, fault=None, **kw):
    if inference.text_guardrail_runner is None or inference.video_guardrail_runner is None:
        raise ValueError('Ordinary production guardrail entry required')
    before=collect_boundary(); holder={}; refs=[]
    def factory(*args, **kwargs):
        owner=ScoutParentOwner(*args,scout_enabled=enabled,scout_context=context,scout_sink=sink,
            scout_copy_cap=copy_cap,scout_fault=fault,
            table_parameters=table_parameters['SOURCE_PHASE'],math_parameters=previous_parameters,
            horizon=1,source_mode='FUSION',**kwargs)
        owner._runtime,owner._wc,owner._rf=kw['runtime'],kw['wc'],kw['rf']
        holder['owner']=owner;refs.append(weakref.ref(owner));return owner
    try:
        with clean.patched(clean,'CurrentBirthSamplingOwner',factory):
            result=clean.execute(inference,sample,'KEEP_A_P',**kw)
        owner=holder['owner']
        result.update(scout_states=copy.deepcopy(owner.rows),parent_policy_fingerprint=PARENT_FINGERPRINT,
            scout_enabled=enabled,real_weights_accepted=False)
        if result['status']=='COMPLETE':
            if result['guided_pairs']!=36 or result['solver_steps']!=36:
                raise ValueError('Complete36 required')
            if enabled and [r['step'] for r in result['scout_states']]!=list(STATE_STEPS):
                raise ValueError('Six states including unsupported rows required')
        del owner
        return result
    finally:
        holder.clear();after=collect_boundary()
        # An active exception traceback intentionally retains its owner frames.
        # Do not mask the causal failure with a false leak classification.
        if sys.exc_info()[0] is None and any(r() is not None for r in refs):
            raise ValueError('Scout owner leaked')
        if 'result' in locals():result['scout_lifecycle']=dict(before=before,after=after,owners_alive_after=0)
