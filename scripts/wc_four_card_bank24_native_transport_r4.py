"""Native private-Python control around the source-bound independent retry tools."""
import argparse,hashlib,json,subprocess
from pathlib import Path
import wc_four_card_bank24_execution_r2 as original
from wc_four_card_resource_cpu_r4 import ssh as base_ssh,write

RUNTIME_REF='reports/wc_four_card_BANK24_native_control_python_CPU_R1_20261022.json'
def bridge(code,runtime):
    if runtime.get('status')!='NATIVE_CONTROL_PYTHON_CPU_PASS' or runtime.get('exit_code')!=0:
        raise ValueError('Actual native-control interpreter CPU proof required')
    prefix="""import hashlib,json,os,subprocess,sys\nfrom pathlib import Path\nraw=sys.stdin.read();p=json.loads(raw) if raw.strip() else None\nruntime=RUNTIME\njob=Path(runtime['job'])\nfor name,key in [('bin/python3','wrapper_sha256'),('usr-local/bin/python3.10','python_sha256'),('lib/ld-linux-x86-64.so.2','loader_sha256')]:\n assert hashlib.sha256((job/name).read_bytes()).hexdigest()==runtime[key]\nassert hashlib.sha256((job/'manifest.json').read_bytes()).hexdigest()==runtime['manifest_sha256']\nassert json.loads((job/'result.json').read_text())['status']=='NATIVE_CONTROL_PYTHON_CPU_PASS'\nenv=dict(os.environ,PATH=str(job/'bin')+':'+os.environ['PATH'],CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')\nq=subprocess.run([str(job/'bin/python3'),'-c',CODE],input=json.dumps(p).encode(),env=env,capture_output=True,timeout=160)\nsys.stdout.buffer.write(q.stdout);sys.stderr.buffer.write(q.stderr);sys.exit(q.returncode)\n"""
    return prefix.replace('runtime=RUNTIME','runtime='+repr(runtime)).replace("'-c',CODE","'-c',"+repr(code))

def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    q=s.add_parser('launch-gpu')
    for name in ['CPU-launch-ref','CPU-capture','CPU-acceptance','unique-handoff','upstream-capture','upstream-acceptance','frozen-gate','output']:q.add_argument('--'+name,required=True,type=Path)
    q.add_argument('--gpu-uuid',required=True)
    q=s.add_parser('capture');q.add_argument('--launch-ref',required=True,type=Path);q.add_argument('--mode',choices=['admission','halfway','terminal'],required=True);q.add_argument('--output',required=True,type=Path);q.add_argument('--human-advanced-terminal',action='store_true')
    q=s.add_parser('accept');q.add_argument('--launch-ref',required=True,type=Path);q.add_argument('--capture',required=True,type=Path);q.add_argument('--output',required=True,type=Path)
    a=p.parse_args();runtime=json.loads(Path(RUNTIME_REF).read_text())
    original.ssh=lambda code,data=None,timeout=180:base_ssh(bridge(code,runtime),data,timeout=timeout)
    if a.command=='launch-gpu':
        value=original.launch_gpu(a)
    elif a.command=='capture':
        if a.human_advanced_terminal:
            from wc_four_card_bank24_advance_terminal_r1 import capture
            value=capture(a)
        else:value=original.capture(a)
    else:
        from wc_four_card_bank24_advance_terminal_r1 import accept_gpu
        value=accept_gpu(a)
    print(json.dumps(value))
if __name__=='__main__':main()
