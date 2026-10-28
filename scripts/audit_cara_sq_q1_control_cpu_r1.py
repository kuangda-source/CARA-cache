"""Reuse core acceptance and independently require every affected wrapper test."""
import copy
import hashlib
import json

from audit_cara_sq_q1_execution_cpu_r1 import accept as accept_core


def accept(capture,host):
    def require(value,message):
        if not value:raise ValueError(message)
    result=capture['result']
    require(hashlib.sha256((json.dumps(result,indent=2,allow_nan=False)+'\n').encode()).hexdigest()
            ==capture['result_sha256'],'Original wrapper CPU bytes differ')
    require(result['status']=='SQ_Q1_CONTROL_CPU_PASS_BOUND_WRAPPERS_NOT_REAL_CUDA',
            'Original wrapper CPU status differs')
    core=copy.deepcopy(capture);core['result']=result['core_result'];core['result_sha256']=result['core_result_sha256']
    accepted=accept_core(core,host);checks=result['wrapper_checks']
    require(checks['tests']==11 and checks['errors']==checks['failures']==checks['skipped']==0
            and checks['real_Linux_stub_handoff_and_post_CLI'] is True
            and checks['actual_GPU_guardian_started'] is False,'Complete GPU-free wrapper control cohort required')
    require(result['CUDA_initialized'] is False and all(result[k]==0 for k in ('GPU_submissions','new_GPUh','ledger_writes')),
            'Wrapper tests exceeded their CPU boundary')
    require(0<result['wall_seconds']<1800 and 0<result['total_process_CPU_seconds']<3600
            and 0<result['peak_RSS_KiB']<8*2**20,'Wrapper CPU resource bound exceeded')
    return dict(accepted,wrapper_tests=11,total_tests=45,result_sha256=capture['result_sha256'],
        worker_wall_seconds=result['wall_seconds'],CPU_seconds=result['CPU_seconds'],
        child_CPU_seconds=result['child_CPU_seconds'],total_process_CPU_seconds=result['total_process_CPU_seconds'],
        peak_RSS_GiB=result['peak_RSS_KiB']/2**20,prospective_control_wrappers_CPU_accepted=True)
