"""Re-run only the original complete CPU post with private codec library paths.

The original stage, failed post receipts, GPU outputs and budget are read-only.
Only the post output path and collector result paths move to a fresh directory.
"""
import argparse
import inspect
import json
import os
from pathlib import Path
import sys
import time
import traceback


def replace_once(body, old, new):
    assert body.count(old) == 1, old
    return body.replace(old, new)


def codec_environment(original, project, caches):
    value = original(project, caches)
    libs = Path(project)/'system-libs-r1/usr/lib/x86_64-linux-gnu'
    extra = [libs/name for name in ('blas', 'lapack', 'pulseaudio')]
    assert all(p.is_dir() for p in extra)
    value['LD_LIBRARY_PATH'] = ':'.join(map(str, extra))+':'+value['LD_LIBRARY_PATH']
    return value


def worker(manifest):
    from four_card_bank24_container_transport_r1 import atomic, identity, receive, socket_path
    from four_card_bank24_execution_tools_r1 import read, sha, verify_registration
    import run_wc_four_card_bank24_collector_cpu_r1 as collector
    m=read(manifest);stage=Path(m['stage']);job=Path(m['observation']);root=Path(m['project'])
    assert sha(job/'host-snapshot.json') == m['host_snapshot_sha256']
    assert not list(Path('/dev').glob('nvidia*'))
    fd, receipt=receive(socket_path(job),m['nonce'],sha(manifest))
    result=dict(actual_CPU_identity=identity(os.getpid()),original_observation_FD=receipt,
        GPU_hidden=True,CUDA_initialized=False,GPU_submissions=0,ledger_written=False)
    started=time.time()
    try:
        verify_registration(stage)
        preserved=[stage/'CPU-final-results.json',stage/'post-CPU-exit.json',root/'reports/gpu-budget-v2.json',root/'.sync/gpu-budget-v2.lock']
        before={str(p):dict(sha256=sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in preserved}
        import subprocess
        codecs={}
        for name in ('ffprobe','ffmpeg'):
            q=subprocess.run([name,'-version'],check=True,capture_output=True,text=True,timeout=30)
            codecs[name]=q.stdout.splitlines()[0]
        import torch
        torch.cuda._lazy_init=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('CPU recovery forbids CUDA'))
        torch.hub.download_url_to_file=lambda *a,**k: (_ for _ in ()).throw(RuntimeError('CPU recovery forbids download'))
        source=(stage/'bank24-fourcard-post.py').read_text()
        body=replace_once(source,"target = a.stage/'CPU-final-results.json'",'target = Path('+repr(str(job/'CPU-final-results.json'))+')')
        sys.argv=['original-full24-post','--project',str(root),'--stage',str(stage)]
        exec(compile(body,str(job/'original-post-output-only.py'),'exec'),{'__name__':'__main__'})
        assert not torch.cuda.is_initialized()
        after={str(p):dict(sha256=sha(p),bytes=p.stat().st_size,mtime_ns=p.stat().st_mtime_ns) for p in preserved}
        assert before==after
        post=dict(status='ORIGINAL_FULL24_CPU_POST_RECOVERED_IN_SEPARATE_DIRECTORY',exit_code=0,
            final_result_sha256=sha(job/'CPU-final-results.json'),original_post_source_sha256=sha(stage/'bank24-fourcard-post.py'),
            output_path_only_substitution=True,codec_versions=codecs,preserved_before=before,preserved_after=after,
            started_unix=started,ended_unix=time.time(),GPU_submissions=0,ledger_written=False,CUDA_initialized=False)
        atomic(job/'post-CPU-exit.json',post)
        body=inspect.getsource(collector.collect)
        body=replace_once(body,"'final':stage/'CPU-final-results.json','post_exit':stage/'post-CPU-exit.json'",
            "'final':Path("+repr(str(job/'CPU-final-results.json'))+"),'post_exit':Path("+repr(str(job/'post-CPU-exit.json'))+")")
        namespace=dict(collector.__dict__)
        exec(compile(body,'<original-collector-independent-post-paths>','exec'),namespace)
        result['capture']=namespace['collect'](read(job/'host-snapshot.json'),stage)
        result['capture']['CPU_post_recovery']=post
        result['capture']['CPU_post_recovery_job']=str(job)
        result['status']='HOST_BOUND_CPU_POST_RECOVERY_AND_COLLECT_PASS'
        code=0
    except BaseException as error:
        result.update(status='CPU_POST_RECOVERY_FAILURE_RETAINED',error_type=type(error).__name__,error=str(error))
        (job/'failure.log').write_text(traceback.format_exc());code=1
    finally:
        os.close(fd);result['observation_FD_closed']=True;atomic(job/'cpu-result.json',result)
    return code


def supervise(stage, job):
    import four_card_bank24_execution_tools_r1 as original
    from four_card_bank24_container_transport_r1 import atomic
    original.verify_registration(stage);launch=original.read(stage/'scout-GPU-launch.json')
    snapshot=original.capture_host(Path(launch['project']),stage,launch,'terminal',original.gpu_telemetry)
    original.post_conditions(Path(launch['project']),stage,launch,snapshot['GPU_container_state'])
    atomic(job/'host-snapshot.json',snapshot)
    body=inspect.getsource(original.cpu_container)
    body=replace_once(body,"str(stage/'run_wc_four_card_bank24_collector_cpu_r1.py')",'str(observation/\'recovery.py\')')
    body=replace_once(body,"'--manifest',str(observation/'cpu-manifest.json')","'worker','--manifest',str(observation/'cpu-manifest.json')")
    # Original stage is read-only even though the legacy container wrapper
    # allowed writes; only the new observation directory remains writable.
    body=replace_once(body,"str(stage)+':'+str(stage)+':rw'","str(stage)+':'+str(stage)+':ro'")
    namespace=dict(original.__dict__,process_environment=lambda p,c:codec_environment(original.process_environment,p,c))
    exec(compile(body,'<original-CPU-transport-recovery-entry-and-readonly-stage>','exec'),namespace)
    try:
        meta=original.read(stage/'host-lifecycle-dependency.json')
        result=namespace['cpu_container'](Path(launch['project']),stage,job,'post',meta['container_image_id'],timeout=7200)
        value=result['capture'];value['CPU_collector_binding']={k:v for k,v in result.items() if k!='capture'}
        atomic(job/'complete-capture.json',value)
        atomic(job/'supervisor-result.json',dict(status='COMPLETE_CPU_RECOVERY_COLLECTED',capture_sha256=original.sha(job/'complete-capture.json'),ended_unix=time.time(),GPU_submissions=0))
        return 0
    except BaseException as error:
        (job/'supervisor-failure.log').write_text(traceback.format_exc())
        atomic(job/'supervisor-result.json',dict(status='CPU_RECOVERY_FAILED_RETAINED',error_type=type(error).__name__,error=str(error),ended_unix=time.time(),GPU_submissions=0))
        return 1


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['worker','supervise']);p.add_argument('--manifest',type=Path);p.add_argument('--stage',type=Path);p.add_argument('--job',type=Path)
    a=p.parse_args()
    stage=a.stage if a.stage else Path(json.loads(a.manifest.read_text())['stage'])
    sys.path.insert(0,str(stage))
    return worker(a.manifest) if a.mode=='worker' else supervise(stage,a.job)


if __name__=='__main__':raise SystemExit(main())
