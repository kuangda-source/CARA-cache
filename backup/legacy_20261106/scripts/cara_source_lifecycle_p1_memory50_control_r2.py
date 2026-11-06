"""Select the versioned memory50 proof/authority; retain original RPC checks."""
import cara_source_lifecycle_p1_control_r1 as control

control.AUTH = 'plans/cara_next_stage_20261101/source_lifecycle/V1_P1_MEMORY50_AUTHORIZATION_R2.json'
control.PROOF = 'reports/cara_v1_P1_whole_CPU_memory50_accepted_r2_20261102.json'
control.PREPARED = 'reports/cara_v1_P1_source_memory50_amended_r2_20261102.json'

if __name__ == '__main__':
    control.main()
