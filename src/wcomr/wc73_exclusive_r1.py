"""WC73-only observer: vanished non-GPU /proc comm entries are not MPS.

Preserves permission/unknown GPU identity failures and every exclusivity gate.
Historical observer and completed runs are unchanged.
"""
import json
import os
from pathlib import Path
import subprocess
import time
from .gpu_budget_pool_v2 import atomic_json, process_identity
from .policy_asset_price_review_r1 import exclusive_gate


def observe(gpu_uuid):
    def query(columns, kind):
        out=subprocess.check_output(['/usr/bin/nvidia-smi','-i',gpu_uuid,'--query-'+kind+'='+columns,
            '--format=csv,noheader,nounits'],text=True,timeout=15)
        return [[x.strip() for x in line.split(',')] for line in out.splitlines() if line.strip()]
    gpu=query('uuid,compute_mode','gpu')
    if len(gpu)!=1 or gpu[0][0]!=gpu_uuid:raise ValueError('Wrong physical GPU')
    apps=[]
    for uuid,pid,memory in query('gpu_uuid,pid,used_gpu_memory','compute-apps'):
        path=Path('/proc')/pid
        try:
            ident=process_identity(int(pid))
            apps.append(dict(gpu_uuid=uuid,pid=int(pid),start_ticks=ident['start_ticks'],uid=path.stat().st_uid,
                memory_MiB=memory))
        except OSError:apps.append(dict(pid=int(pid),identity_unknown=True))
    mps=[]
    for path in Path('/proc').iterdir():
        if not path.name.isdigit():continue
        try:
            if (path/'comm').read_text().strip().startswith('nvidia-cuda-mps'):mps.append(int(path.name))
        except (FileNotFoundError, ProcessLookupError):pass
        except PermissionError:mps=None;break
    return dict(gpu_uuid=gpu_uuid,compute_mode=gpu[0][1],compute_apps=apps,
                mps_processes=mps,observed_unix=time.time())


def verify(snapshot, gpu_uuid, runner=None):
    gate=exclusive_gate(snapshot,gpu_uuid=gpu_uuid,phase='active' if runner else 'idle',
        runner=runner,now=time.time())
    if not gate['observation_passed']:raise ValueError('Hardware exclusive gate: '+','.join(gate['reasons']))
    return gate


def runner_context_gate(project, stage, gpu_uuid):
    import torch
    verify(observe(gpu_uuid),gpu_uuid)
    # Retain an actual allocation throughout the process so the exclusive
    # context cannot lapse between the admission check and model load.
    context=torch.zeros(1,device='cuda');torch.cuda.synchronize()
    ident={k:process_identity(os.getpid())[k] for k in ('pid','start_ticks')};ident['uid']=os.getuid()
    snapshot=observe(gpu_uuid);verify(snapshot,gpu_uuid,ident)
    stage=Path(stage)
    atomic_json(stage/'pg-runner-context-ready.json',dict(identity=ident,snapshot=snapshot,
        GPU_context_held=True,source_revision=json.loads((stage/'registration.json').read_text())['source_revision']))
    deadline=time.monotonic()+90
    while not (stage/'pg-runner-context-granted.json').exists():
        if time.monotonic()>deadline:raise TimeoutError('No exact supervisor context grant')
        time.sleep(.1)
    grant=json.loads((stage/'pg-runner-context-granted.json').read_text())
    if grant['runner']!=ident or grant['gpu_uuid']!=gpu_uuid:raise ValueError('Wrong exact context grant')
    verify(observe(gpu_uuid),gpu_uuid,ident)
    return context
