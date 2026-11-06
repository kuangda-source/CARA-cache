"""Successor-only authority/proof and persistent original-ledger operator cache."""
import cara_source_lifecycle_p1_control_r1 as control

control.AUTH='plans/cara_next_stage_20261101/source_lifecycle/V1_P1_SUCCESSOR_SINGLE19_AUTHORIZATION_R2.json'
control.PROOF='reports/cara_v1_P1_successor_whole_CPU_accepted_r2_20261102.json'
control.PREPARED='reports/cara_v1_P1_successor_source_accepted_r2_20261102.json'
control.CENTRAL=control.CENTRAL.replace("pathlib.Path('/tmp')", "(root/'.sync')")

if __name__=='__main__':control.main()
