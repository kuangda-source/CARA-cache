#!/usr/bin/env python3
"""Freeze the whole affected three-method CPU fixture, not a real GPU card."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--attempt',choices=('r1','r2'),default='r1')
    args=p.parse_args()
    prior_ref='manifests/wc_ra_calibration_sampling_cpu_r1_preregistration_20261010.json'
    prior=json.loads(Path(prior_ref).read_text())
    audit_ref='reports/wc_ra_calibration_sampling_cpu_r1_terminal_20261010_capture_and_independent_audit.json'
    result_ref='reports/wc_ra_calibration_sampling_cpu_r1_terminal_20261010_result.json.native.gz'
    audit=json.loads(Path(audit_ref).read_text())
    assert audit['exit_code']==0 and audit['full_guarded_batch_complete_scope_reconstructed']
    assert audit['actual_parent_guided_reloaded']==288 and audit['actual_child_tensors_reloaded']==96
    assert {n:sha(n) for n in prior['payload_sha256']}==prior['payload_sha256']
    files=set(prior['payload_sha256'])|{prior_ref,audit_ref,result_ref,
        'src/wcomr/cfg_ra_baseline.py','src/wcomr/cfg_ra_baseline_sampling.py',
        'tests/check_cfg_ra_baseline_sampling_cpu.py',
        'scripts/prepare_wc_ra_baseline_sampling_cpu.py','scripts/check_wc_ra_baseline_sampling_cpu.py',
        'scripts/supervise_wc_ra_baseline_sampling_cpu.py','scripts/deploy_wc_ra_baseline_sampling_cpu.py',
        'scripts/capture_wc_ra_baseline_sampling_cpu.py'}
    for name in files:
        if name.endswith('.py'):
            raw=Path(name).read_bytes()
            ast.parse(raw)
            compile(raw,name,'exec')
    scope={'flows':[False,True],'methods':['WC','JOINT_NATIVE','RA'],
        'scenarios':['complete','last_vector_writer_failure'],
        'complete_executed_paths':24,'successful_paths':12,'solver_updates':864,'net_calls':1728,
        'guided_tensors_reloaded':432,'final_latents_reloaded':12,
        'semantic_mutation_refusals':12,'actual_last_method_truncation_refusals':2,
        'last_method_writer_failure_controls':2,'retained_Toy_tensor_files':22,'GPU_submissions':0}
    reg={'card':'WC-RA-BASELINE-SAMPLING-CPU-'+args.attempt.upper()+'-20261010-A',
        'registered_unix':time.time(),'CPU_scope':scope,
        'hypothesis':'Three actual full36 guarded trajectories preserve input/conditions/RNG and execute their registered WC, simple-joint-native and calibrated-RA actions; complete actual vectors and late failure denominators are retained.',
        'threshold_rule':'MEDIAN_EIGHT_COMPLETE_SHARED_D6_INTERVAL_PAID_RISKS',
        'threshold_role':'Initial proxy operating point; not equal actual time or dense calls, no endpoint-quality selection.',
        'calibration_batch_CPU_audit_ref':audit_ref,'calibration_batch_CPU_result_ref':result_ref,
        'prior_actual_Toy_data_role':'Actual accepted six-origin Toy correlations/gains and observed parent paid features; not Cosmos calibration or fabricated rho/gain.',
        'payload_sha256':{n:sha(n) for n in sorted(files)},
        'runtime_source_sha256':prior['runtime_source_sha256'],
        'reuse_unchanged_prior_CPU_proofs_not_rerun':True,
        'real_GPU_calibration_remains_required_for_real_policy':True,
        'model_weights_or_CUDA_or_real_videos_or_quality_or_speed_claim':False,
        'GPU_submissions':0,'ledger_written':False}
    ref=Path('manifests/wc_ra_baseline_sampling_cpu_'+args.attempt+'_preregistration_20261010.json')
    assert not ref.exists()
    ref.write_text(json.dumps(reg,indent=2)+'\n')
    print(json.dumps({'status':'RA_BASELINE_COMPLETE_CPU_REGISTERED_NOT_EXECUTED',
        'payload_files':len(reg['payload_sha256']),'scope':scope,'GPU_submissions':0}))


if __name__=='__main__':
    main()
