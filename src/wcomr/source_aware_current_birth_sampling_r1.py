"""Current-P creation loss in the unchanged ordinary physical execution."""
from . import source_aware_working_epoch_sampling_r1 as working
from .source_aware_phase_sampling import bind_globals
from .source_aware_current_birth_control_r1 import CurrentBirthCPDController, CURRENT_BIRTH_RULE

METHODS = working.METHODS
STRATEGIES = working.STRATEGIES


class CurrentBirthDeployment(working.WorkingEpochDeployment):
    def finish(self):
        result = super().finish()
        result['current_P_birth_rule'] = CURRENT_BIRTH_RULE
        return result


class CurrentBirthSamplingOwner(working.WorkingEpochSamplingOwner):
    def installation(self):
        return super().installation() + (CURRENT_BIRTH_RULE,)


CurrentBirthSamplingOwner.__init__ = bind_globals(working.WorkingEpochSamplingOwner.__init__, {
    'WorkingEpochCPDController': CurrentBirthCPDController,
    'WorkingEpochDeployment': CurrentBirthDeployment})


def verify_batch(state):
    result = working.verify_batch(state)
    P_creations = C_reads = 0
    for request in state['requests']:
        for row in request['paths']:
            deployment = row['collection_complete'].get('deployment')
            if deployment is None: continue
            if deployment.get('current_P_birth_rule') != CURRENT_BIRTH_RULE:
                raise ValueError('Current P error target is not bound to the actual deployment')
            for entry in deployment['history']:
                decision = entry['source_policy']['decision']
                if entry['action'] == 'PP':
                    if (decision['predicted_creation_floor'] <= 0
                            or decision['added_risk'] != decision['gain']*decision['predicted_creation_floor']):
                        raise ValueError('Current P must pay its positive creation error only')
                    P_creations += 1
                elif entry['action'] == 'CC':
                    floor = decision['state_before'][3]
                    if decision['added_risk'] != decision['gain']*(floor+decision['local_proxy']):
                        raise ValueError('C after P must retain source floor plus borrowed drift')
                    C_reads += 1
    return {**result, 'current_P_birth_rule': CURRENT_BIRTH_RULE,
        'current_P_creation_scores_verified': P_creations,
        'C_source_floor_and_drift_scores_verified': C_reads,
        'physical_sampler_bytecode_changed': False}


derive = bind_globals(working.derive, {'verify_batch': verify_batch})
run_batch = bind_globals(working.run_batch, {
    'DynamicSamplingOwner': CurrentBirthSamplingOwner, 'derive': derive})
audit_vectors = bind_globals(working.audit_vectors, {'verify_batch': verify_batch})
DERIVATION_PROOFS = {**working.DERIVATION_PROOFS,
    'current_P_creation_target': CURRENT_BIRTH_RULE,
    'constructor_bytecode_preserved_with_current_controller_and_deployment_bindings': True,
    'original_full_batch_and_vector_audit_bytecode_preserved': True,
    'current_rule_in_installation_and_state_snapshot_binding': True,
    'new_current_birth_and_retained_C_drift_verifier_checks': True}
