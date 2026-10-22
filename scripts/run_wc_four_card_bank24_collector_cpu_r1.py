#!/usr/bin/env python3
"""GPU-hidden, host-PID-bound original post or physical-artifact collection."""
import argparse
import copy
import os
from pathlib import Path
import runpy
import sys
import traceback

from four_card_bank24_container_transport_r1 import atomic,identity,alive,receive,socket_path
from four_card_bank24_execution_tools_r1 import verify_registration,post_conditions,read,sha,ROOT,CONFIG


def collect(snapshot,stage):
    """The registered raw audit shape expected by original offline acceptance."""
    stage=Path(stage);project=Path(snapshot['launch']['project']);L=snapshot['launch'];out=project/'outputs'/L['run_id']
    require_no_live=[]
    for key,expected in snapshot['expected_original_handles'].items():
        if alive(expected):require_no_live.append(key)
    assert not require_no_live and not any(snapshot['original_live_handles'].values())
    reg=verify_registration(stage)
    value=dict(snapshot,registration=reg,payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},
        runtime_actual_sha256={n:sha(Path(ROOT)/'runtime'/n) for n in reg['runtime_source_sha256']},
        entry_registration=reg,entry_registration_sha256=sha(stage/'registration.json'),
        entry_payload_actual_sha256={n:sha(stage/n) for n in reg['payload_sha256']},
        entry_config_file_sha256=sha(stage/'inputs'/CONFIG),original_artifacts={})
    mapping={'supervisor':out/'supervisor.json','runner':out/'runner.json','billing':out/'billing.json',
        'final':stage/'CPU-final-results.json','post_exit':stage/'post-CPU-exit.json',
        'production_CPU':stage/'scout-lifecycle-CPU-proof.json','CPU_independent':stage/'scout-lifecycle-CPU-independent-acceptance.json',
        'authorization':stage/'scout-GPU-authorization.json','dependency':stage/'host-lifecycle-dependency.json',
        'config':stage/'inputs'/CONFIG}
    for key,path in mapping.items():
        if path.is_file():value[key]=read(path);value[key+'_sha256']=sha(path)
    runner=value.get('runner') or {};final=value.get('final') or {}
    for row in final.get('rows',[])+runner.get('runs',[])+final.get('Native_reference_bindings',[]):
        for key in ['final_artifact','warm_guided_artifact','scout_vectors_artifact','video_artifact']:
            if key not in row:continue
            info=row[key];path=Path(info['path']);resolved=path.resolve()
            assert not path.is_symlink() and (project/'outputs').resolve() in resolved.parents
            if info['path'] not in value['original_artifacts']:
                value['original_artifacts'][info['path']]=dict(sha256=sha(path),bytes=path.stat().st_size) if path.is_file() else dict(missing=True)
    for key,path in [('GPU',out/'GPU.log'),('supervisor',stage/'supervisor.log'),('post',stage/'post-CPU.log')]:
        if path.is_file():
            with path.open('rb') as f:f.seek(0,2);n=f.tell();f.seek(max(0,n-18000));body=f.read().decode(errors='replace')
            value[key+'_log_tail']=body
    value['scientific_partial_read']=False
    if (stage/'CPU-TEST-ONLY.json').is_file():value['CPU_FIXTURE_ONLY_NOT_SCIENTIFIC_CAPTURE']=True
    return value


def post(stage,snapshot):
    stage=Path(stage);L=snapshot['launch'];project=Path(L['project'])
    post_conditions(project,stage,L,snapshot['GPU_container_state'])
    budget=project/'reports/gpu-budget-v2.json';budget_lock=project/'.sync/gpu-budget-v2.lock'
    def physical_record(path):
        st=path.stat()
        return dict(sha256=sha(path),bytes=st.st_size,inode=st.st_ino,mtime_ns=st.st_mtime_ns)
    before=dict(pool=physical_record(budget),lock=physical_record(budget_lock))
    sys.path[:0]=[str(stage),str(stage/'inputs/src')];os.environ['WC_SCOUT_KIND']='BANK24'
    import torch
    def forbidden(*a,**k):raise RuntimeError('CPU post cannot initialize CUDA or download')
    torch.cuda._lazy_init=forbidden;torch.hub.download_url_to_file=forbidden
    if (stage/'CPU-TEST-ONLY.json').is_file():
        # Explicit zero-neural-output fixture, only for the CPU deployment card.
        # It cannot pass production GPU namespace/authority validation.
        import bank24_fourcard_lifecycle_r1 as contract
        config=read(stage/'inputs'/CONFIG);reg=read(stage/'registration.json')
        contract.bound_dependency=lambda *args:(dict(entry_source_revision=reg['source_revision'],
            entry_registration_sha256=sha(stage/'registration.json')),config,reg,None,None)
        torch.load=forbidden
    sys.argv=['original-post','--project',str(project),'--stage',str(stage)]
    runpy.run_path(str(stage/'bank24-fourcard-post.py'),run_name='__main__')
    assert not torch.cuda.is_initialized()
    after=dict(pool=physical_record(budget),lock=physical_record(budget_lock))
    assert before==after,'CPU post must not write or replace the budget or its existing lock'
    return dict(status='ORIGINAL_FULL24_CPU_POST_EXITED',final_result_sha256=sha(stage/'CPU-final-results.json'),
        exit_code=0,CUDA_initialized=False,GPU_submissions=0,ledger_written=False,
        readonly_budget_and_lock_verified=True,readonly_budget_before=before,readonly_budget_after=after)


def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',required=True,type=Path);a=p.parse_args()
    m=read(a.manifest);stage=Path(m['stage']);observation=Path(m['observation'])
    assert sha(observation/'host-snapshot.json')==m['host_snapshot_sha256']
    assert not list(Path('/dev').glob('nvidia*'))
    fd,receipt=receive(socket_path(observation),m['nonce'],sha(a.manifest))
    value=dict(actual_CPU_identity=identity(os.getpid()),original_observation_FD=receipt,
        original_host_PID_namespace=os.readlink('/proc/self/ns/pid'),GPU_hidden=True,CUDA_initialized=False,GPU_submissions=0,ledger_written=False)
    code=1
    try:
        assert receipt['peer_identity']['pid']==os.getpid() and receipt['container_actual_pid_mode']=='host'
        assert receipt['container_actual_readonly_root'] is True and not receipt['container_devices'] and not receipt['container_device_requests']
        snapshot=read(observation/'host-snapshot.json')
        verify_registration(stage)
        if m['mode']=='post':value['post']=post(stage,snapshot)
        elif m['mode']=='collect':
            value['capture']=collect(snapshot,stage)
            if (stage/'CPU-TEST-ONLY.json').is_file():
                from four_card_bank24_gpu_port_r1 import accept_capture
                import torch
                torch.cuda._lazy_init=lambda *a,**k:(_ for _ in ()).throw(RuntimeError('CPU collector forbids CUDA'))
                actual=value['capture'];function_input=copy.deepcopy(actual);function_launch=copy.deepcopy(actual['launch'])
                function_launch['next_check_not_before_unix']=actual['observed_unix'];function_input['launch']=function_launch
                function_input['CPU_FIXTURE_ETA_OVERRIDE_FOR_PURE_FUNCTION_ONLY']=True
                atomic(observation/'CPU-offline-acceptance-function-input.json',function_input)
                decision=accept_capture(function_input,function_launch,stage/'inputs')
                assert decision['registered_paths']==24 and decision['formal_denominator']==18 and decision['full_protocol_accepted'] is False
                assert len(decision['all_paths'])==24 and all(r['status']=='NOT_REACHED_RETAINED' for r in decision['all_paths'])
                assert not torch.cuda.is_initialized()
                value['fixture_offline_control']=dict(registered_paths=24,formal_denominator=18,all24_missing_retained=True,
                    scored_formal_paths=0,full_protocol_accepted=False,finance_formula_verified=decision['finance']['finance_accepted'],
                    actual_GPUh_charged=0,actual_observation_time_preserved=True,
                    pure_function_input_sha256=sha(observation/'CPU-offline-acceptance-function-input.json'))
        else:raise ValueError('Only registered post/collect modes allowed')
        value['status']='HOST_BOUND_CPU_POST_OR_COLLECT_PASS';code=0
    except BaseException as error:
        value.update(status='HOST_BOUND_CPU_POST_OR_COLLECT_FAILURE_RETAINED',error_type=type(error).__name__)
        (observation/'failure.log').write_text(traceback.format_exc())
    finally:
        os.close(fd);value['observation_FD_closed']=True;atomic(observation/'cpu-result.json',value)
    return code


if __name__=='__main__':raise SystemExit(main())
