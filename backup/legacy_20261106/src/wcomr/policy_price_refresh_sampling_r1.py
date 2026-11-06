"""Full-domain price-only collector on the accepted all-D parent trajectory."""
import copy
import json
import time
import sys
import weakref
from pathlib import Path
import torch

from . import clean_speed20_r1 as clean
from .simple26d_memory_r2 import collect_boundary
from .source_phase_fixed_mask_r1 import FixedMaskH1Owner
from .policy_interval_assets_sampling_r1 import IntervalAssetsOwner
from .policy_interval_assets_r1 import cells, ROUNDS
from .policy_interval_readout_r1 import ReadoutKernel
from .post_probe_action_clock_r1 import observe_post_probe_action
from .light_sampling import synchronize
from .mid_coverage import tree_digest
from .partial_mlp_deployment_state import plain
from .gpu_budget_pool_v2 import atomic_json

PROVENANCE = ('source', 'target', 'source_anchor_steps', 'source_sha256',
              'older_source_sha256', 'input_sha256')


def reference_cells(rows):
    if [(r['source'], r['target']) for r in rows] != cells():
        raise ValueError('All 406 accepted parent cells required')
    return {(r['source'], r['target']): {k: r[k] for k in PROVENANCE} for r in rows}


class PriceRefreshOwner(IntervalAssetsOwner):
    def __init__(self, *args, accepted_cells, **kwargs):
        super().__init__(*args, **kwargs)
        self.accepted_cells = reference_cells(accepted_cells) if self.collector_enabled else {}

    @torch.no_grad()
    def pair(self, noise, latent, timestep, conditions, choose):
        step = len(self.history) + 1
        self._current_features = {}
        synchronize(); begin = time.perf_counter()
        with observe_post_probe_action(self, synchronize=synchronize) as timer:
            # Use the identical ordinary D parent, without the label collector.
            actual = FixedMaskH1Owner.pair(self, noise, latent, timestep, conditions, choose)
            action = timer.finish() if timer.start is not None else None
        synchronize(); ended = time.perf_counter()
        if self.history[-1]['action'] != 'DD' or set(self._current_features) != {0, 1}:
            raise ValueError('Both actual D branches required')
        self.action_clocks.append(dict(step=step, protected=action is None,
            shared_prefix_seconds=0. if action is None else timer.start-begin,
            D_action_seconds=ended-begin if action is None else action['synchronized_wall_seconds'],
            whole_pair_seconds=ended-begin, boundary='SHARED_PREFIX_PLUS_NONOVERLAPPING_POST_PROBE_D',
            diagnostics_included=False))
        if not self.collector_enabled:
            self._current_features.clear()
            return actual
        if self._kernel is None:
            self._kernel = ReadoutKernel(self.model, self._runtime, self._wc, self._rf, self.deployment.warp)
        inputs = (noise, latent, timestep, conditions)
        input_sha = tree_digest((noise, latent, timestep))
        before = tree_digest(plain((self.deployment.working, [vars(c) for c in self.deployment.dense])))
        self.directory.mkdir(parents=True, exist_ok=True)
        for s in self.by_target[step]:
            provenance = dict(source=s, target=step, source_anchor_steps=[s-1, s],
                source_sha256=tree_digest(self.bank[s]), older_source_sha256=tree_digest(self.bank[s-1]),
                input_sha256=input_sha)
            if provenance != self.accepted_cells[s, step]:
                raise ValueError('Original accepted source/input/older-anchor hash differs')
            source = self._source(s, latent.device)
            trials, references = [], {}
            for round_name, order in ROUNDS:
                for label in order:
                    synchronize(); start = time.perf_counter()
                    returned, c, phi = self._kernel.run(label, source=source,
                        current=self._current_features, pair_inputs=inputs)
                    synchronize(); seconds = time.perf_counter()-start
                    if label not in references:
                        if any(not torch.isfinite(v).all() for v in returned):
                            raise ValueError('Nonfinite readout')
                        references[label] = tuple(v.detach().clone() for v in returned)
                    elif any(not torch.equal(x, y) for x, y in zip(references[label], returned)):
                        raise ValueError('Independent same-state repetition differs')
                    if label == 'A_ONE' and any(not torch.equal(x, y) for x, y in zip(returned, phi)):
                        raise ValueError('Actual alpha1 differs from Phi endpoint')
                    trials.append(dict(round=round_name, action=label, seconds=seconds,
                        boundary='AFTER_ALREADY_PAID_PROBES_THROUGH_WC_HEAD_RF_AND_SHARED_FUSION',
                        shared_prefix_included=False, restore_copy_hash_write_included=False,
                        repeated_output_equal=True))
            row = dict(**provenance, price_trials=trials, original_parent_hashes_equal=True,
                source_shadow_writes_parent=False, extra_deep_teacher_pairs=0,
                new_error_labels=0, raw_interval_tensors_written=0)
            with (self.directory/'cells.jsonl').open('a') as f:
                f.write(json.dumps(row, allow_nan=False)+'\n')
            self.points.append(row)
            atomic_json(self.directory/'technical-progress.json', dict(stage='PRICE_REFRESH',
                completed_source_time_cells=len(self.points), registered_source_time_cells=406,
                current_target=step, current_source=s, errors=0))
            del source, references, returned, c, phi
        if (tree_digest((noise, latent, timestep)) != input_sha
                or tree_digest(plain((self.deployment.working, [vars(c) for c in self.deployment.dense]))) != before):
            raise ValueError('Price diagnostic changed parent state')
        self.bank[step] = [dict(probe=self._current_features[b]['anchor_probe'].detach().cpu().clone(),
            residual=self._current_features[b]['residual'].detach().cpu().clone()) for b in (0, 1)]
        self._current_features.clear()
        return actual

    def close(self):
        self.accepted_cells.clear()
        return super().close()


def execute(inference, sample, mode, *, table_parameters, previous_parameters, accepted_cells, **kw):
    if inference.text_guardrail_runner is None or inference.video_guardrail_runner is None:
        raise ValueError('Ordinary guardrails required')
    if mode not in ('CONTROL', 'PRICE'):
        raise ValueError('New price card contains only CONTROL and PRICE')
    before = collect_boundary(); holder = {}; refs = []
    def factory(*args, **kwargs):
        owner = PriceRefreshOwner(*args, collector_enabled=mode=='PRICE', accepted_cells=accepted_cells,
            collector_output=Path(kw['output'])/'price-raw', table_parameters=table_parameters['SOURCE_PHASE'],
            math_parameters=previous_parameters, horizon=1, source_mode='FUSION', **kwargs)
        owner._runtime, owner._wc, owner._rf = kw['runtime'], kw['wc'], kw['rf']
        holder['owner'] = owner; refs.append(weakref.ref(owner))
        return owner
    try:
        with clean.patched(clean, 'CurrentBirthSamplingOwner', factory):
            result = clean.execute(inference, sample, 'KEEP_A_P', **kw)
        owner = holder['owner']
        result.update(price_cells=copy.deepcopy(owner.points), action_clocks=copy.deepcopy(owner.action_clocks),
            reference_parent_all_D=True, collector_enabled=mode=='PRICE')
        del owner
        if result['status'] in ('COMPLETE', 'VIDEO_REJECTED'):
            if result['guided_pairs'] != 36 or result['solver_steps'] != 36 or result['actions'] != ['DD']*36:
                raise ValueError('All 36 real D updates required')
            if mode == 'PRICE' and [(r['source'], r['target']) for r in result['price_cells']] != cells():
                raise ValueError('All 406 original cells required')
        return result
    finally:
        holder.clear(); after = collect_boundary()
        if sys.exc_info()[0] is None:
            if any(ref() is not None for ref in refs):
                raise ValueError('Completed request retained a price collector')
        elif any(ref() is not None and (ref().bank or ref()._current_features or ref()._kernel is not None) for ref in refs):
            raise ValueError('Failed request did not clear its retained anchors and kernel')
        if 'result' in locals():
            result['request_memory_lifecycle'] = dict(before=before, after=after,
                observed_owners=len(refs), owners_alive_after=0)
