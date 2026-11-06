"""Accept a registered complete-calibration CPU host, without a GPU readiness claim."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import time

from cara_budget_calibration_cpu_hosts_r1 import NEW_FILES, PARENTS, STAGES, HOST_CONFIG

ROOT=Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def accept(paths, *, source_revision=None):
    if source_revision is not None and not re.fullmatch(r"[0-9a-f]{40}", source_revision):
        raise ValueError("Historical evidence requires an immutable full commit SHA")
    def bound_sha(name):
        if source_revision is None:return sha(ROOT/name)
        try:
            raw=subprocess.check_output(['git','show',source_revision+':'+name],cwd=ROOT,stderr=subprocess.PIPE)
        except subprocess.CalledProcessError as error:
            raise ValueError(f'Cannot read historical source {source_revision}:{name}') from error
        return hashlib.sha256(raw).hexdigest()
    if len(paths)!=1: raise ValueError('One original four-card CPU capture required')
    receipts=[]
    for host,path in zip(('four_card',),paths):
        capture=json.loads(Path(path).read_text())
        state,proof,registration=(capture[k] for k in ('container_state','CPU_proof','registration'))
        original_launch=json.loads((ROOT/'reports/cara_budget_calibration_four_card_CPU_launch_r1_20261030.json').read_text())
        if (capture['launch']!=original_launch or registration['stage']!=original_launch['stage']
                or registration['host']!=host or original_launch['registration_sha256']!=capture['registration_sha256']):
            raise ValueError('Original launch, source registration and host must match')
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
        expected=HOST_CONFIG
        if registration.get('expected_host_config')!=expected:
            raise ValueError('R2 prospectively registered CPU limits required')
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
            if registration['payload_sha256'][name]!=bound_sha(name):
                raise ValueError('Affected endpoint source changed: '+name)
        intent=json.loads((ROOT/'plans/cara_next_stage_20261028/mainline/r2/BUDGET_CALIBRATION_CPU_FRAGMENT_R1.json').read_text())
        for name,expected_sha in intent['source_sha256'].items():
            if bound_sha(name)!=expected_sha:
                raise ValueError('Original CPU scope source changed: '+name)
        if (proof['status']!='COMPLETE_CALIBRATION_ROUTES_CPU_NOT_GPU' or proof['spec_tests']!=3
                or proof['calibration_lifecycle_tests']!=21
                or proof['resource_bound']!=dict(cpus=1,memory_GiB=4,work_seconds=2400,exit_seconds=60)):
            raise ValueError('Complete registered calibration worker required')
        numeric=proof['numeric']
        if [r['flow'] for r in numeric['checks']]!=[False,True] or numeric['cuda_initialized']:
            raise ValueError('Both actual CPU sampler modes required')
        for row in numeric['checks']:
            if (row['validation']!='FULL112_CALIBRATION_PRODUCTION_ROUTES_CPU'
                    or row['complete_design_paths']!=112 or row['complete_two_FIT_queries']!=51
                    or row['SA_iterations']!=30 or row['HC_iterations']!=1 or row['HC_neighbors']!=20
                    or row['successful_physical_paths']!=133 or row['declared_failure_attempts']!=3
                    or row['total_physical_attempts']!=136
                    or row['Cosmos_model_weights_loaded'] or row['real_GPU_executed'] or row['whole_GPU_card_accepted']
                    or not all(row[k] for k in ('complete93_frame_RGB','Native_allD_timing_RGB_and_CPU_RNG_equal',
                        'original_complete_recovery_without_generation','hooks_restored'))
                    or row['failures']!=[dict(kind=k,physical_attempts=n,no_replay=True) for k,n in (
                        ('first_writer',1),('second_FIT_refusal',12),('policy_fallback',11))]):
                raise ValueError('Complete112-path scope and original failure/recovery controls required')
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
    return dict(status='FOUR_CARD_COMPLETE_CALIBRATION_CPU_ACCEPTED_NOT_DUAL_HOST_OR_GPU',
        observed_unix=time.time(),receipts=receipts,source_sha256={p:bound_sha(p) for p in NEW_FILES},
        verified_source_revision=source_revision,
        acceptor_source_sha256=sha(__file__),complete_design_paths=224,complete_two_FIT_objectives=102,
        successful_physical_paths=266,declared_failure_attempts=6,total_physical_attempts=272,
        local_calibration_and_lifecycle_tests=21,original_62_B36_sources_unchanged=True,
        dual_host_accepted=False,actual_GPU_query_cap_frozen=False,whole_GPU_quote_frozen=False,
        GPU_dispatch_ready=False,real_model_quality_or_speed_result=False,GPU_submissions=0,
        new_reserved_GPUh=0,ledger_written=False)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--four-card',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--source-revision',help='Explicit immutable published source for historical CPU evidence')
    args=parser.parse_args()
    if args.output.exists(): raise ValueError('Fresh acceptance receipt required')
    result=accept([args.four_card],source_revision=args.source_revision)
    with args.output.open('x') as stream:
        json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps(dict(status=result['status'],hosts=1,GPU_submissions=0)))


if __name__=='__main__': main()
