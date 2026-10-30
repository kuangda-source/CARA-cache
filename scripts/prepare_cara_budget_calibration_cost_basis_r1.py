"""Source-bound request and RGB cost components; never a whole-card quote."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from wcomr.cara_budget_cpu_resources_r2 import HOST_CONFIG
from wcomr.cara_budget_search_r1 import FIT_MEMBERS


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(analysis,capture):
    if (analysis['status']!='COMPLETE_ACCEPTED_B36_ANALYSIS' or analysis['CPU_fixture_only']
            or analysis['formal_logical_positions']!=32):
        raise ValueError('Original complete accepted B36 timing source required')
    state,proof,reg=(capture[k] for k in ('container_state','CPU_proof','registration'))
    if (state['Status']!='exited' or state['Running'] or state['Pid'] or state['ExitCode']
            or state['OOMKilled'] or proof is None or capture['host_config']!=HOST_CONFIG
            or not capture['payload_intact'] or not capture['runtime_intact']):
        raise ValueError('Original completed bounded RGB CPU measurement required')
    if (proof['status']!='FULL_RESOLUTION_RGB_CPU_IO_COST_COMPONENT_COMPLETE_NOT_GPU'
            or proof['RGB_shape']!=[3,93,432,768] or proof['retained_NPY_bytes']!=740524288
            or proof['GPU_submissions'] or proof['ledger_written'] or proof['real_model_output']
            or proof['cold_disk_bound_established'] or proof['GPU_to_CPU_copy_measured']
            or proof['whole_GPU_quote_accepted']):
        raise ValueError('Same full geometry and explicit CPU-only cost boundary required')
    if (hashlib.sha256((json.dumps(proof,indent=2,allow_nan=False)+'\n').encode()).hexdigest()!=capture['CPU_proof_sha256']
            or hashlib.sha256((json.dumps(reg,indent=2)+'\n').encode()).hexdigest()!=capture['registration_sha256']
            or proof['registration_sha256']!=capture['registration_sha256']
            or proof['source_sha256']!=reg['payload_sha256']):
        raise ValueError('Original cost proof digest differs')
    sources=[];native=[];candidate=[]
    for member in FIT_MEMBERS:
        rows=[r for r in analysis['per_member'] if r['member']==member and r['role'] in ('NATIVE35','F19_C','UNIFORM19_C')]
        if len(rows)!=3 or any(r['partition']!='FIT' for r in rows):
            raise ValueError('All three original FIT timing roles required')
        for row in rows:
            samples=[float(s['T_request']) for s in row['timing_samples']]
            if not samples or any(not 0<t<10000 for t in samples):raise ValueError('Finite positive full request timing required')
            sources.append(dict(member=member,role=row['role'],samples=row['timing_samples'],maximum_seconds=max(samples)))
        native.append(next(r['maximum_seconds'] for r in sources if r['member']==member and r['role']=='NATIVE35'))
        candidate.append(max(r['maximum_seconds'] for r in sources if r['member']==member and r['role'] in ('F19_C','UNIFORM19_C')))
    queries=301
    save=max(proof['native_save_fsync_and_hash_seconds'],proof['candidate_save_fsync_and_hash_seconds'])
    extra=2*save+2*proof['read_hash_validate_two_arrays_seconds']+2*proof['full_MSE_validate_and_compute_seconds']
    return dict(status='CALIBRATION_REQUEST_AND_FULL_RGB_COST_COMPONENTS_NOT_WHOLE_QUOTE',
        observed_unix=time.time(),timing_source_host=analysis['host'],timing_source_GPU=analysis['gpu_uuid'],
        FIT_timing_samples=sources,two_native_teacher_request_seconds=sum(native),
        two_FIT_query_request_proxy_seconds=sum(candidate),default_candidate_queries=queries,
        default_teacher_plus_candidate_paths=2+2*queries,
        default_pipeline_request_proxy_GPUh=(sum(native)+queries*sum(candidate))/3600,
        proxy_assumption='Future19D requests resemble saved F19/Uniform19 full-request clocks; not a measured future price or upper bound',
        default_all_native_request_allowance_GPUh=((2+2*queries)*max(native))/3600,
        all_native_allowance_is_proven_upper_bound=False,
        RGB_CPU_host=proof['host'],full_RGB_CPU_proof_sha256=capture['CPU_proof_sha256'],
        RGB_CPU_measurement={k:proof[k] for k in ('native_save_fsync_and_hash_seconds','candidate_save_fsync_and_hash_seconds',
            'read_hash_validate_two_arrays_seconds','full_MSE_validate_and_compute_seconds','peak_RSS_bytes','cache_state')},
        prospective_two_FIT_RGB_CPU_seconds_at_observed_cost=extra,
        cross_host_measurements_pooled_as_GPU_quote=False,
        omitted_whole_card_items=['warm paths','numerical and timing controls','cold model/auxiliary loading',
            'GPU-to-CPU copy','cold disk and device contention','allocation/release/failure overhead',
            'complete CPU evaluation while GPU held','dedicated disk quota and reserve'],
        candidate_query_cap_frozen=False,search_iteration_allocation_frozen=False,whole_GPU_quote_accepted=False,
        proposed_hard_GPUh=None,GPU_submissions=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    if args.output.exists():raise ValueError('Fresh cost basis receipt required')
    a=ROOT/'reports/cara_fast_B36_complete_analysis_r1_20261029.json'
    c=ROOT/'reports/cara_budget_full_RGB_cost_four_card_CPU_capture_r1_20261030.json'
    result=build(json.loads(a.read_text()),json.loads(c.read_text()))
    result['input_sha256']={str(p.relative_to(ROOT)):sha(p) for p in (a,c)}
    result['calculator_source_sha256']=sha(__file__)
    with args.output.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({k:result[k] for k in ['status','default_pipeline_request_proxy_GPUh','default_all_native_request_allowance_GPUh','prospective_two_FIT_RGB_CPU_seconds_at_observed_cost']}))


if __name__=='__main__':main()
