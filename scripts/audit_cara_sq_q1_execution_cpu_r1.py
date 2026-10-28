"""Accept dual-host execution controls without upgrading fixtures to CUDA."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def accept(capture,host):
    def require(value,message):
        if not value:raise ValueError(message)
    state,result=capture['container_state'],capture['result']
    require(hashlib.sha256((json.dumps(result,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
            ==capture['result_sha256'],'Captured original CPU result bytes differ')
    require(state['Status']=='exited' and not state['Running'] and state['ExitCode']==0
            and not state['OOMKilled'] and not state['Error'],'Original CPU container is not cleanly terminal')
    require(capture['source_hashes_equal'] and capture['runtime_hashes_equal'],
            'Original CPU source/runtime differs')
    require(capture['host_config']==dict(DeviceRequests=None,NanoCpus=2_000_000_000,
        Memory=8*2**30,MemorySwap=8*2**30,CpusetCpus='4,5',NetworkMode='none',ReadonlyRootfs=True),
        'Original CPU resource boundary differs')
    require(capture['image']=='sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d',
            'Original CPU image differs')
    require(result['status']=='SQ_Q1_EXECUTION_CPU_PASS_FIXTURES_NOT_REAL_CUDA' and result['profile']==host
            and result['tests']==34 and result['errors']==result['failures']==result['skipped']==0
            and result['real_Linux_subprocess_control'] is True,'Complete Linux control cohort required')
    require(result['subprocess_scenarios']==['complete','numeric_failure','runner_failure','thermal','timeout'],
            'A required original-process lifecycle scenario is absent')
    require(result['fixture_head_calls']=={key:dict(started=n,completed=n)
            for key,n in (('warm',4),('controls',26),('formal',192))},'Whole Q1 fixture denominator differs')
    for key in ('fixture_is_GPU_evidence','actual_B1_replay','actual_model_weights','CUDA_initialized',
                'original_C_CUDA_parity_accepted','GPU_ready','actual_GPU_runner_entry_accepted',
                'actual_financial_settlement_performed'):
        require(result[key] is False,'CPU controls overstated as actual evidence: '+key)
    require(result['temporary_fixture_ledger_only'] is True and result['synthetic_authority_only'] is True,
            'CPU fixture ledger or authority boundary differs')
    for key in ('GPU_submissions','new_GPUh','ledger_writes'):
        require(result[key]==0 and capture.get(key,0)==0,'CPU proof changed GPU or budget state')
    revision=capture['launch']['source_revision']
    from wcomr.sq_q1_spec_r1 import EXECUTION_CRITICAL,SCOPE
    require(set(result['critical_source_sha256'])==set(EXECUTION_CRITICAL),'Incomplete affected source proof')
    for name,digest in result['critical_source_sha256'].items():
        raw=subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)
        require(hashlib.sha256(raw).hexdigest()==digest,'Original published source differs: '+name)
    require(result['scope']==json.loads(subprocess.check_output(['git','show',revision+':'+SCOPE],cwd=ROOT)),
            'Original frozen scope differs')
    require(result['actual_platform']['system']=='Linux' and result['actual_platform']['machine']=='x86_64'
            and result['torch_version']=='2.7.1+cu128' and 1<=result['torch_threads']<=2,
            'Original Linux/runtime/CPU binding differs')
    require(result['raw_ru_maxrss_unit']=='KiB' and result['peak_RSS_KiB']==result['raw_ru_maxrss']
            and 0<result['peak_RSS_KiB']<8*2**20 and 0<result['wall_seconds']<1800
            and 0<result['total_process_CPU_seconds']<3600
            and result['child_CPU_seconds']>0,'Original CPU resource accounting differs')
    return dict(host=host,source_revision=revision,result_sha256=capture['result_sha256'],
        tests=34,skipped=0,real_Linux_lifecycle_controls=5,
        worker_wall_seconds=result['wall_seconds'],CPU_seconds=result['CPU_seconds'],
        child_CPU_seconds=result['child_CPU_seconds'],total_process_CPU_seconds=result['total_process_CPU_seconds'],
        peak_RSS_GiB=result['peak_RSS_KiB']/2**20,
        terminal_torch_threads=result['torch_threads'],
        execution_and_terminal_controls_CPU_accepted=True,actual_GPU_or_science_accepted=False)
