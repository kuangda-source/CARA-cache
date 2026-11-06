"""After the original supervisor exits, audit its config-derived output path."""
import argparse,json,os,subprocess,sys,time
from pathlib import Path


def paths(stage,project):
    from wcomr.drop1_full18_r1 import CONFIG,validate_contract
    c=json.loads((stage/CONFIG).read_text());validate_contract(c)
    output=project/'outputs'/c['run_id']
    command=[sys.executable,str(stage/'scripts/postprocess_wc_drop1_full18_r1.py'),
        '--project',str(project),'--stage',str(stage)]
    return output,command


def main():
    p=argparse.ArgumentParser();p.add_argument('--supervisor-pid',type=int,required=True)
    for name in ('project','stage'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();assert a.supervisor_pid>0
    os.environ['CUDA_VISIBLE_DEVICES']='';sys.path.insert(0,str(a.stage/'src'))
    output,command=paths(a.stage,a.project)
    from wcomr.gpu_budget_pool_v2 import process_identity
    while process_identity(a.supervisor_pid)['state'] not in (None,'Z','X'):time.sleep(10)
    receipt={'GPU_submissions':0,'ledger_written':False,'output':str(output),'command':command}
    try:
        sup=json.loads((output/'supervisor.json').read_text())
        assert sup['pid']==a.supervisor_pid and sup['status']=='DROP1_GPU_EXITED_REQUIRES_RAW_CPU_AUDIT'
        with (a.stage/'post-CPU.log').open('x') as log:
            receipt['exit_code']=subprocess.call(command,stdout=log,stderr=subprocess.STDOUT,
                env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
    except BaseException as error:
        receipt.update(exit_code=1,error_type=type(error).__name__,error=str(error))
        raise
    finally:
        receipt['status']='DROP1_FULL_POST_CPU_TERMINAL'
        receipt['ended_unix']=time.time()
        (a.stage/'post-CPU-exit.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':main()
