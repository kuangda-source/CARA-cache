"""Same current-birth method; CPU-backed additional checkpoint state only.

The original physical pre-snapshot two-copy gate remains. After its snapshot
exists, guards account for the next copy in this serial restoration sequence.
No GPU root cause or end-to-end saving follows from importing this module.
"""
import torch

from . import source_aware_current_birth_sampling_r2 as original
from .source_aware_phase_sampling import bind_globals
from .cpu_owned_state_snapshot import CPUDeploymentRoundtrip,storage_inventory


def next_copy_requirement(physical_gate,inventory,stage):
    if (physical_gate['transient_copy_factor']!=2 or physical_gate['workspace_reserve_bytes']<=0
            or physical_gate['required_GPU_headroom_bytes']!=2*physical_gate['GPU_logical_copy_bytes']+physical_gate['workspace_reserve_bytes']
            or stage not in ('physical_restore','owned_restore')):
        raise ValueError('Original physical gate and registered serial restore stage required')
    extra=physical_gate['GPU_logical_copy_bytes'] if stage=='physical_restore' else inventory['unique_GPU_storage_bytes']
    return {'next_copy_GPU_bytes':extra,'workspace_reserve_bytes':physical_gate['workspace_reserve_bytes'],
        'required_free_GPU_bytes':extra+physical_gate['workspace_reserve_bytes'],
        'stage':stage,'original_pre_snapshot_two_copy_gate_unchanged':True,
        'saved_CPU_owned_image_additional_GPU_residency_bytes':0}


def admit_next_copy(gate,inventory,stage):
    required=next_copy_requirement(gate,inventory,stage)
    GPU=bool(gate['GPU_logical_copy_bytes'] or inventory['unique_GPU_storage_bytes'])
    if GPU:
        if not torch.cuda.is_initialized():raise ValueError('Cannot initialize CUDA for checkpoint observation')
        free,total=torch.cuda.mem_get_info()
        observation={'free_bytes':free,'total_bytes':total,'allocated_bytes':torch.cuda.memory_allocated(),
            'reserved_bytes':torch.cuda.memory_reserved(),'max_allocated_bytes':torch.cuda.max_memory_allocated(),
            'max_reserved_bytes':torch.cuda.max_memory_reserved()}
        if free<required['required_free_GPU_bytes']:
            raise ValueError('CPU-owned checkpoint next-copy GPU headroom unavailable: '+stage)
    else:observation={'status':'CPU_STATE_NO_CUDA_INITIALIZATION'}
    return {**required,'actual_observation':observation,'GPU_measurement':GPU}


class CPUStorageSamplingOwner(original.CurrentBirthSamplingOwner):
    def installation(self):
        return super().installation()+('CPU_OWNED_STORAGE_SERIAL_RESTORE_R1',)

    def checkpoint(self,physical,gate,config):
        self.check_healthy()
        remaining=config['logical_copy_cap_bytes']-gate['logical_tensor_copy_bytes']
        live_inventory=storage_inventory(self.own_state())
        if remaining<=0 or live_inventory['logical_tensor_bytes_aliases_counted']>remaining:
            raise ValueError('Original combined logical copy cap exceeded')
        # CPU cap bounds complete backing storages, even where views expose
        # fewer logical elements. No change to physical capture or buffers.
        own=CPUDeploymentRoundtrip(self,logical_copy_cap_bytes=remaining,
            CPU_storage_cap_bytes=config['logical_copy_cap_bytes'])
        before=physical.fingerprint()
        if config.get('CPU_mutate_owned_state_before_restore',False):
            self.controller.creation_floor=999.;self.controller.accumulated=999.
            self.controller.working_step=-99;self.controller.consecutive_P=-99
            self.controller.history.clear()
            self.deployment.readout.completed=-99;self.deployment.readout.history.clear()
            self.deployment.working=[None,None];self.deployment.opportunities=-99
            self.head_calls.append({'injected_checkpoint_only':True})
        physical_guard=admit_next_copy(gate,live_inventory,'physical_restore')
        physical.restore()
        owned_guard=admit_next_copy(gate,live_inventory,'owned_restore')
        own.restore()
        if physical.fingerprint()!=before:
            raise ValueError('CPU-owned serial physical state restore differs')
        return {'additional_state_bytes':own.bytes,'complete_additional_state_restored':True,
            'physical_state_restored':True,'fingerprint':own.origin,
            'checkpoint_perturbation_executed':bool(config.get('CPU_mutate_owned_state_before_restore',False)),
            'source_controller_and_A_history_perturbation_restored':True,
            'arbitrary_failed_pair_recovery_claim':False,'CPU_owned_storage_version':'R1',
            'owned_storage_inventory':live_inventory,'original_logical_cap_unchanged':True,
            'serial_next_copy_guards':[physical_guard,owned_guard]}


METHODS=original.METHODS
STRATEGIES=original.STRATEGIES
valid_P_interval=original.valid_P_interval
CURRENT_BIRTH_RULE=original.CURRENT_BIRTH_RULE
CurrentBirthDeployment=original.CurrentBirthDeployment
CurrentBirthSamplingOwner=CPUStorageSamplingOwner
verify_batch=original.verify_batch
derive=original.derive
audit_vectors=original.audit_vectors
run_batch=bind_globals(original.run_batch,{'DynamicSamplingOwner':CPUStorageSamplingOwner})
DERIVATION_PROOFS={**original.DERIVATION_PROOFS,'additional_state_checkpoint_storage_only_new_owner':True,
    'original_physical_pre_snapshot_gate_unchanged':True,'original_verifier_and_vector_audit_unchanged':True,
    'source_RA_owner_unchanged':True,'policy_and_readout_bytecode_unchanged':True}
