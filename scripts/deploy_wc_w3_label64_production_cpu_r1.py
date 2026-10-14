"""Create one fresh project-owned CPU stage. No GPU or shared runtime writes."""
import argparse
import hashlib
import io
import json
import re
from pathlib import Path
import shlex
import subprocess
import tarfile
import time

ROOT=Path(__file__).resolve().parents[1]
STAGE='.sync/wc-w3-label64-production-cpu-r1-20261015'
REMOTE_PY='/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python'
PROJECT='/home/gaokuangda/data/gkd/worldcache_omr'
SCRIPTS=tuple(str(p.relative_to(ROOT)) for p in sorted((ROOT/'scripts').glob('*.py')))
PREREG='configs/wc_p_acr_local12_profile528_production_r1_20261015.json'


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,required=True);ap.add_argument('--launch-cpu',action='store_true');ap.add_argument('--stage-suffix',default='r1');a=ap.parse_args()
    if a.output.exists():raise ValueError('New launch receipt required')
    if not re.fullmatch(r'r[1-9][0-9]*',a.stage_suffix):raise ValueError('Fresh named CPU revision only')
    stage_name=STAGE.replace('cpu-r1-','cpu-'+a.stage_suffix+'-')
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    names=sorted(str(p.relative_to(ROOT)) for directory in ('src/wcomr','tests') for p in (ROOT/directory).glob('*.py'))+list(SCRIPTS)+[PREREG]
    config=json.loads((ROOT/PREREG).read_text())
    references=[x['ref'] for x in config['references'].values()]
    for role in ('H1','previous'):
        references+=list(json.loads((ROOT/config['references'][role]['ref']).read_text())['sources'])
    coeff=json.loads((ROOT/config['references']['coefficients']['ref']).read_text())
    references+=list(coeff['inputs_sha256'])
    proof=json.loads((ROOT/config['references']['profile_CPU']['ref']).read_text())
    references += [proof['capture_ref'],'manifests/wc_p_acr_local12_production_cpu_prereg_20261015.json','manifests/wc_h0_eval_mode_contract_20261003.json',
        'manifests/wc_source_phase_h1_four_controls_bindings_r1_20261013.json',
        'manifests/wc_p_acr_local12_launch_cpu_prereg_r2_20261015.json']
    # Original PA configuration is used only for unchanged H1 resource and
    # physical-input validation. This CPU stage never executes a PA profile.
    w3_scope='manifests/wc_w3_label64_parent18_full864_scope_r1_20261015.json'
    w3_inputs='manifests/wc_w3_expl_dev8_inputs_r1_20261015.json'
    collector='reports/wc_w3_label64_h1_collector_CPU_r3_independent_acceptance_20261015.json'
    accepted=json.loads((ROOT/collector).read_text())
    assert accepted['status']=='W3_FULL72_288_ORIGINS3456_PAIRS_INDEPENDENT_CPU_ACCEPTED_NOT_REAL_LABELS'
    references += [w3_scope,w3_inputs,collector,accepted['capture_ref'],
        'configs/wc_w3_expl_dev8_requests_r1_20261015.jsonl',
        'manifests/wc_w3_label64_full864_provisional_cost_r1_20261015.json']
    references += list(json.loads((ROOT/w3_scope).read_text())['clock_sources'])
    references += [s['path'] for s in json.loads((ROOT/w3_inputs).read_text())['selected_sources']]
    names=sorted(set(names+references))
    payload={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}
    for name in names:
        blob=subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)
        if hashlib.sha256(blob).hexdigest()!=payload[name]:raise ValueError('CPU payload must be fully committed: '+name)
    reg={'source_revision':revision,'payload_sha256':payload,'CPU_scopes':['ACTUAL_W3_FULL18_864_PRODUCTION_CPU_NOT_MODEL'],'GPU_submissions':0,'shared_runtime_written':False,'stage':stage_name}
    if not a.launch_cpu:print(json.dumps({'status':'PACKET_READY_NOT_LAUNCHED','files':len(payload),'source_revision':revision,'GPU_submissions':0}));return
    buffer=io.BytesIO()
    with tarfile.open(fileobj=buffer,mode='w:gz') as tar:
        for name in names:tar.add(ROOT/name,arcname=name,recursive=False)
        raw=json.dumps(reg,indent=2).encode();entry=tarfile.TarInfo('registration.json');entry.size=len(raw);tar.addfile(entry,io.BytesIO(raw))
    code="""import pathlib,tarfile,io,sys,json,subprocess,hashlib,time,os
root=pathlib.Path(PROJECT).resolve();stage=root/STAGE
assert not stage.exists(),'Fresh stage required; never duplicate original CPU launch'
stage.mkdir(parents=True)
archive=tarfile.open(fileobj=io.BytesIO(sys.stdin.buffer.read()),mode='r:gz')
for member in archive:
 assert member.isfile() and '..' not in pathlib.PurePosixPath(member.name).parts and not pathlib.PurePosixPath(member.name).is_absolute()
 path=stage/member.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(archive.extractfile(member).read())
reg=json.loads((stage/'registration.json').read_text())
assert all(hashlib.sha256((stage/name).read_bytes()).hexdigest()==h for name,h in reg['payload_sha256'].items())
prior=root/'.sync/wc-source-phase-absolute-h1-cpu-r4-20261013/registration.json'
previous=json.loads(prior.read_text());assert previous['source_revision']=='d661cf521c6af0951f2967dd74e8693c23cc9e29'
reg['runtime_source_sha256']=previous['runtime_source_sha256']
reg['runtime_binding_origin']={'path':str(prior),'sha256':hashlib.sha256(prior.read_bytes()).hexdigest(),'source_revision':previous['source_revision']}
assert all(hashlib.sha256((root/'runtime'/n).read_bytes()).hexdigest()==h for n,h in reg['runtime_source_sha256'].items())
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\\n')
command=[sys.executable,str(stage/'scripts/run_wc_w3_label64_production_cpu_bundle_r1.py'),'--stage',str(stage),'--project',str(root),'--runtime',str(root/'runtime')]
log=(stage/'CPU-bundle.log').open('xb')
job=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'CUDA_VISIBLE_DEVICES':''})
receipt={'pid':job.pid,'source_revision':reg['source_revision'],'stage':str(stage),'command':command,'launched_unix':time.time(),'registration_sha256':hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest(),'GPU_submissions':0,'estimated_collect_after_seconds':300}
(stage/'launch.json').write_text(json.dumps(receipt,indent=2)+'\\n');print(json.dumps(receipt))
"""
    code='PROJECT='+repr(PROJECT)+'\nSTAGE='+repr(stage_name)+'\n'+code
    command=REMOTE_PY+' -c '+shlex.quote(code)
    started=time.time();p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen',command],input=buffer.getvalue(),capture_output=True,timeout=120)
    result={'transport_exit_code':p.returncode,'started_unix':started,'ended_unix':time.time(),'source_revision':revision,'stderr':p.stderr.decode(),'GPU_submissions':0}
    try:result['launch']=json.loads(p.stdout)
    except json.JSONDecodeError:result['unparsed_stdout']=p.stdout.decode()
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result))
    if p.returncode:raise SystemExit(p.returncode)


if __name__=='__main__':main()
