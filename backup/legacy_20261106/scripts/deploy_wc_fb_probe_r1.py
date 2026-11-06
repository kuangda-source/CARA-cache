#!/usr/bin/env python3
"""Deploy an isolated immutable F/B stage; actual CPU first, then one launch."""
import argparse,hashlib,io,json,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HOST=['ssh','-o','BatchMode=yes','-o','ConnectTimeout=15','-o','ClearAllForwardings=yes','gkd_minchen']
SERVER='/home/gaokuangda/data/gkd/worldcache_omr'
CONFIG='configs/wc_fb_probe_r1_20261013.json'
DEFAULT_STAGE='wc-fb-probe-cpu-r1-20261013'
BASE='wc-teacher-first-velocity-production-r1-20261013'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()


def remote(code):
    compile(code,'fb-deployment-wrapper','exec')
    return subprocess.check_output(HOST+['python3 -'],input=code,text=True)


def names():
    c=json.loads((ROOT/CONFIG).read_text());params=json.loads((ROOT/c['parameters_ref']).read_text())
    values=[CONFIG,c['authority_ref']]+[c[k+'_ref'] for k in ('selection','parameters','cost','baseline','labels','F_analysis_parameters','old_labels_capture')]+list(params['sources'])
    for pattern in ('src/wcomr/*fb_probe*.py','src/wcomr/block_probe_r1.py','src/wcomr/spectral_probe_r1.py',
                    'scripts/*fb_probe*.py','scripts/analyze_wc_spectral_probe_r1.py',
                    'tests/*fb_probe*.py','tests/*block_probe*.py','tests/*spectral_probe*.py'):
        values += [str(p.relative_to(ROOT)) for p in ROOT.glob(pattern)]
    required=['scripts/check_wc_fb_probe_cpu_r1.py','scripts/postprocess_wc_fb_probe_cpu_r1.py',
        'src/wcomr/fb_probe_r1.py','tests/check_fb_probe_sampling_cpu_r1.py']
    assert all(n in values and (ROOT/n).is_file() for n in required)
    return list(dict.fromkeys(values))


def main():
    p=argparse.ArgumentParser();p.add_argument('--launch',action='store_true')
    p.add_argument('--stage-name',default=DEFAULT_STAGE);a=p.parse_args()
    if '/' in a.stage_name or not a.stage_name.startswith('wc-fb-probe-'):raise ValueError('Explicit isolated stage name required')
    stage=SERVER+'/.sync/'+a.stage_name
    packet={'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'new_payload':{n:sha(ROOT/n) for n in names()}}
    for n, digest in packet['new_payload'].items():
        committed=subprocess.check_output(['git','show',packet['source_revision']+':'+n],cwd=ROOT)
        assert hashlib.sha256(committed).hexdigest()==digest, 'Commit complete payload before deployment: '+n
    if not a.launch:
        buffer=io.BytesIO()
        with tarfile.open(fileobj=buffer,mode='w:gz') as archive:
            for n in packet['new_payload']:archive.add(ROOT/n,arcname=n)
        code='BASE='+repr(SERVER+'/.sync/'+BASE)+'\nSTAGE='+repr(stage)+'\n'+r'''import pathlib,json,hashlib,shutil
base=pathlib.Path(BASE);stage=pathlib.Path(STAGE);assert not stage.exists()
reg=json.loads((base/'registration.json').read_text());proof=json.loads((base/'production-CPU-result.json').read_text())
assert proof['status']=='TEACHER_FIRST_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['exit_code']==0
assert proof['registration_sha256']==hashlib.sha256((base/'registration.json').read_bytes()).hexdigest()
stage.mkdir()
for name,digest in reg['payload_sha256'].items():
 source=base/name;assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
 target=stage/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
(stage/'base-registration.json').write_text(json.dumps(reg,indent=2)+'\n')
print(json.dumps({'status':'FB_PRIOR_HELPERS_COPIED_NOT_NEW_CPU_ACCEPTANCE','files':len(reg['payload_sha256'])}))
'''
        print(remote(code).strip())
        subprocess.run(HOST+['tar -xzf - -C '+stage],input=buffer.getvalue(),check=True)
        code='P='+repr(packet)+'\nSTAGE='+repr(stage)+'\nROOT='+repr(SERVER)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);base=json.loads((stage/'base-registration.json').read_text())
reg={'source_revision':P['source_revision'],'payload_sha256':dict(base['payload_sha256']),
 'runtime_source_sha256':base['runtime_source_sha256'],'new_payload_sha256':P['new_payload'],
 'base_helper_source_revision':base['source_revision'],'base_CPU_not_new_FB_proof':True}
for name,digest in P['new_payload'].items():
 assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
 if name in reg['payload_sha256']:assert reg['payload_sha256'][name]==digest
 reg['payload_sha256'][name]=digest
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/run_wc_fb_probe_r1.py'),
 '--project',str(root),'--stage',str(stage),'--cpu-check']
with (stage/'production-CPU.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,
  env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2'))
r={'status':'FB_PROBE_ACTUAL_TWO_FLOW_AND_PRODUCTION_CPU_STARTED_NOT_GPU','pid':child.pid,'command':command,
 'stage':str(stage),'source_revision':reg['source_revision'],'payload_files':len(reg['payload_sha256']),
 'started_unix':time.time(),'GPU_submissions':0,'ledger_written':False}
(stage/'CPU-launch.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''
        result=json.loads(remote(code))
        (ROOT/'reports'/('wc_fb_probe_'+a.stage_name+'_CPU_launch.json')).write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result));return
    code='P='+repr(packet)+'\nSTAGE='+repr(stage)+'\nROOT='+repr(SERVER)+'\n'+r'''import pathlib,json,hashlib,subprocess,os,time
stage=pathlib.Path(STAGE);root=pathlib.Path(ROOT);reg=json.loads((stage/'registration.json').read_text())
proof=json.loads((stage/'production-CPU-result.json').read_text())
assert proof['status']=='FB_PROBE_ACTUAL_PRODUCTION_CPU_PASS_NOT_GPU' and proof['exit_code']==0
assert proof['registration_sha256']==hashlib.sha256((stage/'registration.json').read_bytes()).hexdigest()
assert P['new_payload']==reg['new_payload_sha256']
for name,digest in reg['payload_sha256'].items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
teacher=root/'.sync/wc-teacher-first-velocity-production-r1-20261013'
t=json.loads((teacher/'CPU-final-results.json').read_text());post=json.loads((teacher/'post-CPU-exit.json').read_text())
assert t['status']=='TEACHER_FIRST_ALL4_PARENTS8_SUFFIXES4_TEACHERS12_OUTPUTS_AUDITED_ALL93_SCORED'
assert t['accepted_videos']==t['scored_videos']==12 and post['exit_code']==0
ts=json.loads((root/'outputs/wc-teacher-first-velocity-full270-r1/supervisor.json').read_text())
assert ts['child_exit_code']==0 and not pathlib.Path('/proc/'+str(ts['child_pid'])).exists()
assert not (stage/'GPU-launch.json').exists() and not (root/'outputs/wc-fb-probe-full432-r1').exists()
command=['/home/gaokuangda/data/gkd/cosmos/cosmos-predict2.5/.venv/bin/python','-u',str(stage/'scripts/supervise_wc_fb_probe_r1.py'),
 '--project',str(root),'--stage',str(stage),'--source-revision',reg['source_revision']]
with (stage/'GPU-supervisor.log').open('x') as log:
 child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
r={'status':'FB_PROBE_COMPLETE432_DISPATCHED_ADMISSION_PENDING','supervisor_pid':child.pid,
 'command':command,'stage':str(stage),'source_revision':reg['source_revision'],'started_unix':time.time(),
 'automatic_CPU_post_on_supervisor_completion':True}
(stage/'GPU-launch.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
'''
    result=json.loads(remote(code))
    (ROOT/'reports'/('wc_fb_probe_'+a.stage_name+'_GPU_launch.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
