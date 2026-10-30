"""Accept both original bounded endpoint CPU workers, never a GPU search card."""
import argparse
import hashlib
import json
from pathlib import Path
import time

from cara_budget_endpoint_cpu_hosts_r1 import NEW_FILES, PARENTS, STAGES

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def accept(paths):
    if len(paths)!=2: raise ValueError('Both registered host captures required')
    receipts=[]
    for host,path in zip(('four_card','two_card'),paths):
        capture=json.loads(Path(path).read_text())
        state,proof,registration=(capture[k] for k in ('container_state','CPU_proof','registration'))
        if (state['Status']!='exited' or state['Running'] or state['Pid']!=0 or state['ExitCode']!=0
                or state['OOMKilled'] or proof is None):
            raise ValueError('Original CPU worker must exit normally with complete proof: '+host)
        proof_sha=hashlib.sha256((json.dumps(proof,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
        registration_sha=hashlib.sha256((json.dumps(registration,indent=2)+'\n').encode()).hexdigest()
        if (proof_sha!=capture['CPU_proof_sha256'] or registration_sha!=capture['registration_sha256']
                or proof['registration_sha256']!=registration_sha
                or proof['payload_sha256']!=registration['payload_sha256']
                or proof['runtime_source_sha256']!=registration['runtime_source_sha256']):
            raise ValueError('Original source/proof identity differs')
        expected=dict(NanoCpus=10**9,Memory=4*2**30,MemorySwap=4*2**30,CpusetCpus='26',
            DeviceRequests=None,NetworkMode='none',ReadonlyRootfs=True)
        if (capture['host_config']!=expected or not capture['payload_intact'] or not capture['runtime_intact']
                or capture['launch']['host']!=host or proof['host']!=host
                or Path(capture['launch']['stage']).name!=STAGES[host]
                or proof['CUDA_initialized'] or proof['Cosmos_model_weights_loaded'] or proof['GPU_submissions']
                or proof['ledger_written'] or proof['whole_GPU_card_accepted']
                or proof['actual_compile_threads']!=1 or proof['compile_pools']):
            raise ValueError('Exact GPU-hidden CPU resource/runtime boundary required')
        parent=json.loads((ROOT/PARENTS[host]).read_text())
        if registration['base_registration_sha256']!=parent['registration_sha256']:
            raise ValueError('Original accepted parent CPU changed')
        for name in NEW_FILES:
            if registration['payload_sha256'][name]!=sha(ROOT/name):
                raise ValueError('Affected endpoint source changed: '+name)
        numeric=proof['numeric']
        if numeric['budget_component_unit_controls']!=31 or [r['flow'] for r in numeric['checks']]!=[False,True]:
            raise ValueError('All component controls and both original flow modes required')
        for row in numeric['checks']:
            if (row['validation']!='BUDGET_ENDPOINT_AFFECTED_PRODUCTION_CPU'
                    or row['successful_tiny_paths']!=27 or row['declared_failure_attempts']!=4
                    or row['complete_two_FIT_objectives']!=6
                    or set(row['failures'])!={'refusal','decode','writer','fallback'}
                    or row['Cosmos_weights_loaded'] or row['real_video_quality_or_speed_result']
                    or row['whole_GPU_card_accepted'] or not all(row[k] for k in (
                        'full36_and_exact19D','full93_preencoding_RGB','ON_OFF_RGB_RNG_objectives_exact',
                        'original_teacher_reuse_without_generation','completed_query_replay_without_generation',
                        'partial_cohort_never_scored','nonfinite_fallback_invalidates_fixed_budget',
                        'hooks_restored','unbound_GPU_entry_refused'))):
                raise ValueError('Complete endpoint affected-path matrix required')
        receipts.append(dict(host=host,path=str(path),sha256=sha(path),launch=capture['launch'],
            container_state=state,host_config=expected,CPU_proof_sha256=proof_sha,
            CPU_process_seconds=proof['CPU_process_seconds'],
            worker_wall_seconds=proof['ended_unix']-proof['started_unix']))
    for filename,count in [('reports/cara_fast_B36_dispatch_CPU_acceptance_r2_20261029.json',52),
            ('reports/cara_fast_B36_analysis_CPU_acceptance_r1_20261029.json',4),
            ('reports/cara_fast_B36_figures_CPU_acceptance_r2_20261029.json',6)]:
        original=json.loads((ROOT/filename).read_text())['critical_source_sha256']
        if len(original)!=count or any(sha(ROOT/p)!=h for p,h in original.items()):
            raise ValueError('Original accepted B36 source changed')
    return dict(status='BUDGET_ENDPOINT_AFFECTED_PRODUCTION_CPU_DUAL_HOST_ACCEPTED_NOT_GPU',
        observed_unix=time.time(),receipts=receipts,source_sha256={p:sha(ROOT/p) for p in NEW_FILES},
        acceptor_source_sha256=sha(__file__),successful_tiny_paths_per_host=54,
        declared_failure_attempts_per_host=8,complete_two_FIT_objectives_per_host=12,
        component_unit_controls_per_host=31,original_62_B36_sources_unchanged=True,
        original_unknown_physical_process_reader_accepted=False,dedicated_GPU_storage_accepted=False,
        actual_GPU_query_cap_frozen=False,whole_GPU_quote_frozen=False,GPU_dispatch_ready=False,
        real_model_quality_or_speed_result=False,GPU_submissions=0,new_reserved_GPUh=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--four-card',type=Path,required=True)
    parser.add_argument('--two-card',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('Fresh acceptance receipt required')
    result=accept([args.four_card,args.two_card])
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=result['status'],hosts=2,GPU_submissions=0)))


if __name__=='__main__': main()
