#!/usr/bin/env python3
"""Two-card C1 CPU-only preparation/capture, sourced from one pinned commit.

No GPU dispatch, ledger, old process recovery or service/network modification.
Run as the existing user with docker group access; never mount its socket.
"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time
import urllib.request

ROOT = Path('/data20t/gaokuangda/worldcache_workspace')
STAGE = ROOT/'.sync/cara-source-coverage-C1-CPU-r1-20261103'
NAME = 'cara-source-coverage-C1-CPU-r1-20261103'
IMAGE = 'sha256:1e81ac62ee68ca1a6ef655515096a1d84579b01aa4986810c9b18d4f6c4c552d'
TEMPLATE = 'plans/cara_next_stage_20261103/source_coverage/c1/C1_CPU_SOURCE_REGISTRATION_R1.json'
BASE = ROOT/'.sync/cara-source-lifecycle-V1-P1-GPU-a6000-full146-r2-20261102'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_new(path,value):
    with path.open('x') as out:
        out.write(json.dumps(value,sort_keys=True,indent=2)+'\n')


def download(revision,name):
    url = 'https://raw.githubusercontent.com/kuangda-source/CARA-cache/'+revision+'/'+name
    with urllib.request.urlopen(url,timeout=30) as response:
        return response.read()


def inspect():
    result = subprocess.run(['docker','inspect',NAME],capture_output=True,text=True)
    if result.returncode:
        if 'No such object' in result.stderr:
            return None
        raise RuntimeError(result.stderr[-600:])
    value = json.loads(result.stdout)[0]
    return value


def capture():
    intent = STAGE/'CPU-intent.json'
    if not intent.exists():
        return dict(status='NO_C1_CPU_INTENT',stage=str(STAGE),GPU_submissions=0)
    expected = json.loads(intent.read_bytes())
    registered=(STAGE/'registration.json').read_bytes()
    if sha(registered) != expected['registration_sha256']:
        raise ValueError('Original CPU source registration differs')
    mapping=json.loads(registered)
    for name,expected_sha in mapping['payload_sha256'].items():
        if sha((STAGE/name).read_bytes()) != expected_sha:
            raise ValueError('Original CPU source bytes changed: '+name)
    value = inspect()
    if value is None:
        return dict(status='ORIGINAL_C1_CPU_INTENT_CONTAINER_UNKNOWN_NO_RETRY',intent=expected)
    host,config,state = value['HostConfig'],value['Config'],value['State']
    if (value['Image'] != IMAGE or value['Name'] != '/'+NAME
            or config['Labels']['cara.C1.registration'] != expected['registration_sha256']
            or host.get('DeviceRequests') or host['Memory'] != 8*2**30
            or host['MemorySwap'] != 8*2**30 or host['NanoCpus'] != 2_000_000_000
            or host['CpusetCpus'] != '26,27' or host['NetworkMode'] != 'none'
            or not host['ReadonlyRootfs']):
        raise ValueError('Original C1 CPU identity or resource isolation differs')
    result = dict(status='ORIGINAL_C1_CPU_ACTIVE' if state['Running'] else 'ORIGINAL_C1_CPU_TERMINAL',
        container_id=value['Id'],image=value['Image'],state=state,host_config=host,intent=expected,
        registration_raw_base64=base64.b64encode(registered).decode(),
        GPU_submissions=0,ledger_written=False)
    target=STAGE/'linux-results-r1/C1_CPU_PROOF_R1.json'
    if not state['Running'] and target.exists():
        raw=target.read_bytes();result.update(proof_sha256=sha(raw),proof_raw_base64=base64.b64encode(raw).decode())
    if not state['Running'] and state['ExitCode'] != 0:
        log=subprocess.run(['docker','logs',NAME],capture_output=True,text=True)
        result['terminal_log_tail']=(log.stdout+log.stderr)[-6000:]
    return result


def prepare(revision,template_sha):
    if (STAGE/'CPU-intent.json').exists():
        return capture()
    if inspect() is not None:
        raise RuntimeError('C1 CPU container exists without this intent; inspect original, never launch')
    raw=download(revision,TEMPLATE)
    if sha(raw) != template_sha:
        raise ValueError('Pinned CPU registration template SHA differs')
    registration=json.loads(raw)
    STAGE.mkdir(mode=0o700,exist_ok=True)
    def source(item):
        name,expected=item;rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Project-relative source required')
        target=STAGE/rel
        if target.exists():
            if sha(target.read_bytes()) != expected:
                raise ValueError('Existing C1 source changed: '+name)
            return
        bases=[BASE/rel]
        if name=='reports/cara_v1_P1_successor_original_algorithm_summary_r1_20261103.json':
            bases.append(ROOT/'outputs/cara-source-lifecycle-V1-P1-full146-r2-20261102/algorithm/algorithm-summary.json')
        content=next((p.read_bytes() for p in bases if p.is_file() and sha(p.read_bytes())==expected),None)
        if content is None:
            content=download(revision,name)
        if sha(content) != expected:
            raise ValueError('Pinned source SHA differs: '+name)
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(source,registration['payload_sha256'].items()))
    for name,expected in registration['runtime_source_sha256'].items():
        if sha((ROOT/'runtime'/name).read_bytes()) != expected:
            raise ValueError('Pinned CPU runtime changed: '+name)
    registration['published_source_revision']=revision
    reg_raw=(json.dumps(registration,sort_keys=True,indent=2)+'\n').encode()
    path=STAGE/'registration.json'
    if path.exists() and path.read_bytes()!=reg_raw:
        raise ValueError('Existing C1 registration differs')
    if not path.exists():
        path.write_bytes(reg_raw)
    mem={line.split(':')[0]:line.split(':')[1].strip() for line in Path('/proc/meminfo').read_text().splitlines()}
    available=int(mem['MemAvailable'].split()[0])*1024
    if available < 12*2**30:
        return dict(status='C1_CPU_RESOURCE_REFUSAL_NO_INTENT',MemAvailable_bytes=available)
    subprocess.run(['docker','image','inspect',IMAGE],check=True,stdout=subprocess.DEVNULL)
    (STAGE/'scratch').mkdir(exist_ok=True)
    registration_sha=sha(reg_raw)
    intent=dict(kind='C1_PREPARATION_CPU_ONLY',created_unix=time.time(),image=IMAGE,container=NAME,
        stage=str(STAGE),registration_sha256=registration_sha,published_source_revision=revision,
        source_files=len(registration['payload_sha256']),scope_sha256=registration['scope_sha256'],
        MemAvailable_bytes=available,GPU_submissions=0,ledger_written=False)
    write_new(STAGE/'CPU-intent.json',intent)
    command=['docker','run','--detach','--name',NAME,'--label','cara.C1.registration='+registration_sha,
        '--cpus','2','--cpuset-cpus','26,27','--memory','8g','--memory-swap','8g','--pids-limit','512',
        '--network','none','--read-only','--user',str(os.getuid())+':'+str(os.getgid()),
        '-e','CUDA_VISIBLE_DEVICES=','-e','NVIDIA_VISIBLE_DEVICES=void','-e','PYTHONDONTWRITEBYTECODE=1',
        '-e','OMP_NUM_THREADS=2','-e','OPENBLAS_NUM_THREADS=2','-e','TMPDIR=/workspace/scratch',
        '-e','CARA_READ_WRITE_RUNTIME=/runtime','-e','PYTHONPATH=/workspace/src:/workspace/tests:/workspace/scripts',
        '-v',str(STAGE)+':/workspace:rw','-v',str(ROOT/'runtime')+':/runtime:ro','-w','/workspace',
        IMAGE,'timeout','300','python','scripts/prepare_cara_source_coverage_c1_r1.py',
        '--output-directory','/workspace/linux-results-r1']
    run=subprocess.run(command,capture_output=True,text=True)
    write_new(STAGE/'CPU-launch.json',dict(exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr))
    if run.returncode:
        return dict(status='C1_CPU_LAUNCH_FAILED_NO_RETRY',intent=intent,error=run.stderr[-1000:])
    return capture()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','capture'))
    parser.add_argument('--source-revision')
    parser.add_argument('--expected-template-sha256')
    args=parser.parse_args()
    if args.action=='prepare':
        if not re.fullmatch('[0-9a-f]{40}',args.source_revision or ''):
            raise ValueError('Published full source revision required')
        result=prepare(args.source_revision,args.expected_template_sha256)
    else:
        result=capture()
    result['operator_source_sha256']=sha(Path(__file__).read_bytes())
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':
    main()
