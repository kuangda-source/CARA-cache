"""Complete-state P/D birth C4 diagnostics; no online controller revision."""
import copy
import functools
import time

import torch

from . import source_aware_current_birth_sampling_r2 as original
from .source_aware_CPU_storage_sampling_r1 import CPUStorageSamplingOwner, admit_next_copy
from .source_aware_phase_sampling import bind_globals
from .cpu_owned_state_snapshot import CPUDeploymentRoundtrip, storage_inventory
from .e4c_offline_intervention_control_r1 import OfflineInterventionController, VERSION
from .full_sampling import CompleteStateRoundtrip
from .rv0_restore import capture_inventory, capture_gate
from .rv0_fork import object_state
from .cfg_guided_w1_collection import signature
from .mid_coverage import tree_digest
from .light_sampling import synchronize
from .cfg_guided_w1_outputs import guided_velocity_moments


class DiagnosticSnapshot:
    """The original two-copy gate plus the accepted CPU-owned serial restore."""
    def __init__(self, owner, latent, noise, velocity, generator, config):
        owner.check_healthy()
        inventory = capture_inventory(owner.net, owner.model.sample_scheduler, latent, noise, velocity)
        self.gate = capture_gate(inventory,
            logical_copy_cap_bytes=config['logical_copy_cap_bytes'], transient_copy_factor=2,
            workspace_reserve_bytes=config['workspace_reserve_bytes'] + config['paired_prefix_reserve_bytes'],
            available_gpu_bytes=torch.cuda.mem_get_info()[0] if latent.is_cuda else None)
        self.owned_inventory = storage_inventory(owner.own_state())
        remaining = config['logical_copy_cap_bytes'] - self.gate['logical_tensor_copy_bytes']
        if remaining <= 0 or self.owned_inventory['logical_tensor_bytes_aliases_counted'] > remaining:
            raise ValueError('Original combined physical and owned logical cap exceeded')
        self.physical = CompleteStateRoundtrip(owner.net, owner.model.sample_scheduler, latent, [generator])
        self.owned = CPUDeploymentRoundtrip(owner, logical_copy_cap_bytes=remaining,
                                           CPU_storage_cap_bytes=config['logical_copy_cap_bytes'])
        self.owner = owner
        self.parent_latent = latent
        self.latent_sha = tree_digest(latent)
        self.physical_sha = self.physical.fingerprint()
        self.condition_objects = tuple(inspect_conditions(velocity))
        self.condition_identity = signature([object_state(c) for c in self.condition_objects])
        self.condition_sha = tree_digest([object_state(c) for c in self.condition_objects])
        self.restores = []

    def restore(self):
        self.owner.check_healthy()
        # Conditions are frozen inputs. Replacing them with equal clones would
        # violate the original deployment's id/version contract. A mutation is
        # a failed branch, never a license to rewrite that contract.
        if (signature([object_state(c) for c in self.condition_objects]) != self.condition_identity
                or tree_digest([object_state(c) for c in self.condition_objects]) != self.condition_sha):
            raise ValueError('Frozen original condition identity/version/content changed')
        a = admit_next_copy(self.gate, self.owned_inventory, 'physical_restore')
        latent = self.physical.restore()
        b = admit_next_copy(self.gate, self.owned_inventory, 'owned_restore')
        self.owned.restore()
        if (self.physical.fingerprint() != self.physical_sha
                or tree_digest(self.parent_latent) != self.latent_sha
                or signature([object_state(c) for c in self.condition_objects]) != self.condition_identity
                or tree_digest([object_state(c) for c in self.condition_objects]) != self.condition_sha):
            raise ValueError('Physical sampler, live parent latent or conditions failed restoration')
        self.restores.append([a, b])
        return latent


def inspect_conditions(velocity):
    import inspect
    cells = inspect.getclosurevars(velocity).nonlocals
    if set(cells) != {'self', 'condition', 'uncondition', 'guidance'} or cells['guidance'] != 7:
        raise ValueError('Exact live CFG7 condition closure required')
    return cells['condition'], cells['uncondition']


class MatchedSourceAgeOwner(CPUStorageSamplingOwner):
    def __init__(self, model, *, method, context, runtime, wc, rf, calibration, spec,
                 events, enabled, config, writer):
        if (method != 'A_CPD_W1_ONE_PHASE' or type(enabled) is not bool
                or [e['phase'] for e in events] != ['early', 'late']
                or any(e['source_method'] != method for e in events)
                or spec['working_epoch_strategy'] != 'WORKING_P_AGE_KEEP_INTERVAL'):
            raise ValueError('Exact complete two-phase offline diagnostic owner required')
        constructor = bind_globals(original.CurrentBirthSamplingOwner.__init__, {
            'WorkingEpochCPDController': functools.partial(OfflineInterventionController,
                registered_birth_steps=tuple(e['birth_step'] for e in events))})
        constructor(self, model, method=method, context=context, runtime=runtime,
                    wc=wc, rf=rf, calibration=calibration, spec=spec)
        self.events, self.enabled, self.config, self.writer = events, enabled, config, writer
        self.event_records = []
        self.active_suffix = None
        self.active_velocity = None
        self.active_generator = None

    def installation(self):
        return super().installation() + (VERSION, self.controller.registered_birth_steps)

    def pair(self, noise, latent, timestep, conditions, choose):
        step = len(self.history) + 1
        active = self.active_suffix
        age = step - active['birth_step'] if active else None
        teacher = None
        if active and active['source'] in ('P', 'D') and age in (1, 2, 4):
            before = DiagnosticSnapshot(self, latent, noise, self.active_velocity,
                                         self.active_generator, self.config)
            before_state = self.controller._state()
            input_sha = tree_digest((noise, latent, timestep))
            beta_stats = [copy.deepcopy(c.receipt()) for c in self.deployment.dense]
            anchors = [list(c.receipt()['anchor_steps']) for c in self.deployment.dense]
            raw_beta = [(c.numerator/(c.denominator+c.ridge)
                         if c.pairs and c.denominator > c.min_energy else None)
                        for c in self.deployment.dense]
            clipped_beta = [None if v is None else max(-c.clip, min(c.clip, v))
                           for c, v in zip(self.deployment.dense, raw_beta)]
            try:
                synchronize(); started = time.perf_counter()
                with self.controller.same_state_teacher(step):
                    teacher = super().pair(noise, latent, timestep, conditions, choose)
                synchronize(); teacher_seconds = time.perf_counter() - started
                teacher = tuple(v.detach().clone() for v in teacher)
            finally:
                before.restore()
            if (self.controller._state() != before_state
                    or tree_digest((noise, latent, timestep)) != input_sha):
                raise ValueError('Teacher changed the actual candidate state')
        synchronize(); started = time.perf_counter()
        actual = super().pair(noise, latent, timestep, conditions, choose)
        synchronize(); action_seconds = time.perf_counter() - started
        if active:
            guided = actual[0] + 7*(actual[0]-actual[1])
            active['guided'].append(guided.detach().cpu().clone())
            active['actions'].append(self.history[-1]['action'])
            active['realized_full_pair_wall_seconds'].append(action_seconds)
        if teacher is not None:
            h = copy.deepcopy(self.history[-1])
            if (h['action'] != 'CC' or any(s['kind'] != active['source']
                    or s['created_step'] != active['birth_step'] for s in h['working_sources'])
                    or h['working_source_ages'] != [age, age]
                    or h['true_D_before'] != h['true_D_after']
                    or tree_digest((noise, latent, timestep)) != input_sha):
                raise ValueError('Actual C did not read its own matched birth source')
            status = h['A_readout']['branch_status']
            effective_beta = [b if s == 'scalar' else None for s, b in zip(status, clipped_beta)]
            scheduler = self.model.sample_scheduler
            index = scheduler._step_index
            sigma = scheduler.sigmas[index]
            payload = {'C': tuple(v.detach().cpu().clone() for v in actual),
                'DENSE_SAME_STATE': tuple(v.detach().cpu().clone() for v in teacher),
                'candidate_latent': latent.detach().cpu().clone(),
                'timestep': timestep.detach().cpu().clone()}
            artifact = self.writer(active['event_id'], active['source'], age, payload)
            record = {'event_id': active['event_id'], 'source': active['source'], 'age': age,
                'step': step, 'sigma_index': index, 'sigma': float(sigma),
                'timestep': timestep.detach().cpu().tolist(), 'input_sha256': input_sha,
                'candidate_latent_sha256': tree_digest(payload['candidate_latent']),
                'true_D_steps_before': anchors, 'D_statistics_before_C': beta_stats,
                'fitted_beta_from_actual_D_statistics': clipped_beta,
                'effective_scalar_beta': effective_beta, 'A_status': status,
                'actual_shared_alpha': h['A_readout']['shared_alpha'],
                'actual_source_and_decision_history': h,
                'same_state_guided_moments': guided_velocity_moments(
                    scene=self.context[0], state=active['event_id']+'-'+active['source']+'-age'+str(age),
                    original=actual, proposed=actual, dense=teacher),
                'actual_C_full_pair_seconds': action_seconds, 'research_teacher_full_pair_seconds': teacher_seconds,
                'cost_boundary': 'FULL_PAIR_WITH_BOTH_PROBES_AND_ACTUAL_A_HEADS_NOT_POST_PROBE_OR_CLEAN_VIDEO',
                'teacher_state_restored_before_actual_C': True,
                'teacher_updates_final_deployment_anchors': False,
                'birth_source_P_not_promoted_to_D': True,
                'complete_gate': before.gate, 'serial_restore_guards': before.restores,
                'artifact': artifact}
            active['age_points'].append(record)
        return actual

    @torch.no_grad()
    def run_event(self, event, latent, noise, generator, velocity, suffix):
        if (not self.enabled or self.active_suffix is not None
                or self.model.sample_scheduler._step_index != event['fork_after_update']
                or len(self.history) != event['fork_after_update']):
            raise ValueError('Complete bound parent boundary before the registered event required')
        parent = DiagnosticSnapshot(self, latent, noise, velocity, generator, self.config)
        self.active_velocity, self.active_generator = velocity, generator
        row = {'event': event, 'branches': [], 'status': 'STARTED',
            'parent_physical_sha256': parent.physical_sha, 'parent_owned_sha256': parent.owned.origin}
        self.event_records.append(row)
        try:
            for label in ('POLICY_REPEAT1', 'POLICY_REPEAT2', 'P_BIRTH_C4', 'D_BIRTH_C4'):
                origin = parent.restore()
                source = label[0] if label in ('P_BIRTH_C4', 'D_BIRTH_C4') else None
                branch = {'label': label, 'source': source, 'birth_step': event['birth_step'],
                    'event_id': event['id'], 'guided': [], 'actions': [],
                    'age_points': [], 'realized_full_pair_wall_seconds': [], 'status': 'STARTED'}
                row['branches'].append(branch); self.active_suffix = branch
                start = time.perf_counter()
                try:
                    grid = self.model.sample_scheduler.timesteps[event['fork_after_update']:event['last_diagnostic_update']]
                    if len(grid) != 5:
                        raise ValueError('Complete five-update diagnostic grid required')
                    if source:
                        with self.controller.intervention(event['birth_step'], source):
                            result = suffix(self.model, noise, origin, velocity, generator, grid)
                            branch['owned_state_sha256'] = self.fingerprint()
                    else:
                        result = suffix(self.model, noise, origin, velocity, generator, grid)
                        branch['owned_state_sha256'] = self.fingerprint()
                    if (self.model.sample_scheduler._step_index != event['last_diagnostic_update']
                            or len(branch['guided']) != 5 or len(branch['actions']) != 5
                            or source and (branch['actions'] != [source*2]+['CC']*4
                                or [p['age'] for p in branch['age_points']] != [1, 2, 4])):
                        raise ValueError('Complete matched branch or all age points missing')
                    if not source and branch['actions'][0] != 'PP':
                        raise ValueError('The registered natural parent P event was not reproduced')
                    branch['final_latent'] = result.detach().cpu().clone()
                    branch['final_latent_sha256'] = tree_digest(branch['final_latent'])
                    branch['physical_state_sha256'] = parent.physical.fingerprint()
                    branch['status'] = 'COMPLETE5_UPDATES_NOT_ENDPOINT_VIDEO_OR_ONLINE_POLICY'
                finally:
                    branch['inclusive_research_wall_seconds'] = time.perf_counter()-start
                    self.active_suffix = None
                    parent.restore()
            first, second = row['branches'][:2]
            if (first['actions'] != second['actions'] or first['owned_state_sha256'] != second['owned_state_sha256']
                    or first['physical_state_sha256'] != second['physical_state_sha256']
                    or not all(torch.equal(a, b) for a, b in zip(
                        first['guided']+[first['final_latent']], second['guided']+[second['final_latent']]))):
                raise ValueError('Original-policy repeated suffix is not numerically equivalent')
            for branch in row['branches']:
                branch['guided_sha256'] = [tree_digest(v) for v in branch['guided']]
                branch['vector_artifact'] = self.writer(event['id'], branch['label'], 'suffix', {
                    'guided': branch.pop('guided'), 'final_latent': branch.pop('final_latent')})
            row['status'] = 'COMPLETE4_BRANCHES_6_AGE_POINTS_NOT_ENDPOINT_QUALITY'
        finally:
            self.active_suffix = None
            parent.restore()
            self.active_velocity = self.active_generator = None
            row['parent_restored'] = True
            row['serial_restore_guards'] = parent.restores
        return row
