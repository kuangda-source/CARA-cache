#!/usr/bin/env python3
"""CPU-only full-video metric probe from the accepted original model stage."""
import argparse,base64,hashlib,json,sys,subprocess
from pathlib import Path
from wc_four_card_cara_cal66_quality_cpu_r1 import ssh,accept as accept_models,BASE
from wc_four_card_policy_assets_r1 import REPO,read,write
sys.path.insert(0,str(REPO/'src'))
from wcomr.policy_generator_r1.p2_quality_entry import evaluator_identity

WRAPPER='''import os,resource,runpy,signal,sys
assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
signal.alarm(21600)
entry=sys.argv.pop(1);sys.argv[0]=entry
runpy.run_path(entry,run_name='__main__')
'''

DEPLOY=r'''
import json,pathlib,hashlib,os,sys,subprocess,time
p=json.load(sys.stdin);root=pathlib.Path('/data20t/gaokuangda/worldcache_workspace');stage=root/'.sync'/p['stage_name']
assert stage.parent==root/'.sync' and stage.name.startswith('cara-cal66-quality-video-CPU-') and not stage.exists()
b=p['binding'];model=pathlib.Path(b['registration']['stage']);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
assert json.loads((model/'registration.json').read_text())==b['registration']
for n,h in b['registration']['payload_sha256'].items():assert sha(model/n)==h
overlay=pathlib.Path(b['dependency_overlay']);lock=overlay.parent/'dependency-overlay-manifest.json'
assert sha(lock)==b['dependency_overlay_manifest_sha256']
for n,h in json.loads(lock.read_text())['files'].items():
 rel=pathlib.PurePosixPath(n);assert not rel.is_absolute() and '..' not in rel.parts
 assert not (overlay/n).is_symlink() and sha(overlay/n)==h
stage.mkdir(mode=0o700)
(stage/'binding.json').write_text(json.dumps(b,indent=2)+'\n');(stage/'wrapper.py').write_text(p['wrapper'])
reg=dict(binding_sha256=sha(stage/'binding.json'),wrapper_sha256=sha(stage/'wrapper.py'),model_registration_sha256=b['acceptance']['registration_sha256'],controller_source_revision=p['source_revision'],controller_source_sha256=p['source_sha256'])
(stage/'registration.json').write_text(json.dumps(reg,indent=2)+'\n')
sys.path.insert(0,p['base']+'/scripts');from four_card_policy_assets_port_r1 import container_command
sys.path.insert(0,str(root/'.sync/wc-bank24-fourcard-full-execution-r3-20261022'))
from four_card_bank24_execution_tools_r1 import process_environment
env=process_environment(root,stage/'CPU-caches');env.update(MPLCONFIGDIR=str(stage/'mpl'),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
cmd=container_command(root,stage,'cpu-worker',sha(stage/'registration.json'),env,os.getuid(),os.getgid());cmd[cmd.index('--memory')+1]='8g'
for i,v in enumerate(cmd):
 if v.startswith('PYTHONPATH='):cmd[i]='PYTHONPATH='+str(model/'scripts')+':'+str(model/'src')+':'+str(overlay)
i=cmd.index(str(stage/'scripts/wc_policy_interval_assets_lifecycle_r1.py'))
cmd[i:]=[str(stage/'wrapper.py'),str(model/'scripts/score_cara_cal66_quality_cpu_r1.py'),'--binding',str(stage/'binding.json'),'--output',str(stage/'output'),'--declared-synthetic-CPU-probe']
with (stage/'probe.log').open('x') as log:child=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
launch=dict(status='CAL66_REAL_93_FRAME_METRIC_CPU_DISPATCHED',stage=str(stage),container=stage.name+'-cpu',pid=child.pid,start_ticks=int((pathlib.Path('/proc')/str(child.pid)/'stat').read_text().split(') ',1)[1].split()[19]),started_unix=time.time(),registration_sha256=sha(stage/'registration.json'),GPU_submissions=0,ledger_written=False)
(stage/'CPU-probe-launch.json').write_text(json.dumps(launch,indent=2)+'\n');print(json.dumps(launch))
'''

CAPTURE=r'''
import json,pathlib,hashlib,sys,subprocess,time,base64,gzip
L=json.load(sys.stdin);s=pathlib.Path(L['stage']);assert s.parent==pathlib.Path('/data20t/gaokuangda/worldcache_workspace/.sync') and s.name.startswith('cara-cal66-quality-video-CPU-')
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert sha(s/'registration.json')==L['registration_sha256'];reg=json.loads((s/'registration.json').read_text())
assert sha(s/'binding.json')==reg['binding_sha256'] and sha(s/'wrapper.py')==reg['wrapper_sha256']
c=json.loads(subprocess.check_output(['docker','inspect',L['container']],text=True))[0];assert c['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
files={}
for f in sorted((s/'output').glob('*.json')):
 raw=f.read_bytes();files[f.name]=dict(sha256=hashlib.sha256(raw).hexdigest(),raw_base64=base64.b64encode(raw).decode(),data=json.loads(raw))
v=dict(status='CAL66_REAL_METRIC_CPU_CAPTURE',observed_unix=time.time(),launch=L,registration=reg,binding=json.loads((s/'binding.json').read_text()),files=files,container=dict(state=c['State'],readonly_root=c['HostConfig']['ReadonlyRootfs'],network=c['HostConfig']['NetworkMode'],nano_cpus=c['HostConfig']['NanoCpus'],memory=c['HostConfig']['Memory'],devices=c['HostConfig'].get('Devices') or [],device_requests=c['HostConfig'].get('DeviceRequests') or []),log_tail=(s/'probe.log').read_text(errors='replace')[-12000:],GPU_submissions=0,ledger_written=False)
print(json.dumps(dict(compressed_original=base64.b64encode(gzip.compress(json.dumps(v).encode())).decode())))
'''

def accept(v):
 from wcomr.policy_generator_r1.p2_quality_entry import validate_sources_and_decoder
 from wcomr.policy_generator_r1.shared66_quality import DIMENSIONS,digest
 from wcomr.automatic_quality_batch_r1 import validate_result
 from wcomr.automatic_quality_r1 import sampling_spec,text_sha
 c=v['container'];s=c['state'];assert not s['Running'] and s['ExitCode']==0 and not s['OOMKilled']
 assert c['readonly_root'] and c['network']=='none' and c['nano_cpus']==2*10**9 and c['memory']==8*2**30 and not c['devices'] and not c['device_requests']
 for r in v['files'].values():
  raw=base64.b64decode(r['raw_base64'],validate=True);assert hashlib.sha256(raw).hexdigest()==r['sha256'] and json.loads(raw)==r['data']
 proof=v['files']['result.json']['data'];assert proof['status']=='CAL66_REAL_THREE_METRIC_93_FRAME_CPU_PROBE_PASS' and proof['frames']==93 and proof['geometry']==[432,768] and not proof['scientific_quality_result'] and not proof['GPU_submissions']
 assert [r['dimension'] for r in proof['rows']]==list(DIMENSIONS)
 for r in proof['rows']:
  raw=v['files'][r['dimension']+'.raw.json'];assert r['result_sha256']==raw['sha256']
  result=raw['data'];validate_sources_and_decoder(v['binding']['identity'],result)
  row=dict(case_id='DECLARED_SYNTHETIC_CPU',method='CPU93',dimension=r['dimension'],seed=0,prompt='Synthetic gray CPU fixture',prompt_sha256=text_sha('Synthetic gray CPU fixture'),video_path=str(Path(v['launch']['stage'])/'output/fixture93.mp4'),video_sha256=result['video_sha256'],scorer_fingerprint=digest(v['binding']['identity']),expected_sampling=sampling_spec(r['dimension']),input_status='READY_TO_SCORE')
  validate_result(row,result)
 estimate=52*sum(r['score_seconds'] for r in proof['rows'])+sum(r['load_seconds'] for r in proof['rows'])
 return dict(status='CAL66_REAL_THREE_METRIC_93_FRAME_CPU_ACCEPTED_NOT_SCIENCE',CPU_accepted=True,proof=proof,full52_quality_only_extrapolated_seconds=estimate,extrapolation_is_not_full_cohort_acceptance=True,LPIPS_and_IO_not_included=True,CPU_limits=dict(cpus=2,memory_bytes=8*2**30,wall_seconds=21600),GPU_submissions=0,ledger_written=False)

def main():
 p=argparse.ArgumentParser();p.add_argument('command',choices=['deploy','capture','accept'])
 for n in ('model-capture','model-acceptance','overlay-acceptance','launch-ref','capture','output'):p.add_argument('--'+n,type=Path,required=n=='output')
 p.add_argument('--stage-name');a=p.parse_args();assert not a.output.exists()
 if a.command=='deploy':
  c=read(a.model_capture);accepted=read(a.model_acceptance);check=accept_models(c)
  assert all(accepted[k]==value for k,value in check.items())
  assert accepted['capture_sha256']==hashlib.sha256(a.model_capture.read_bytes()).hexdigest()
  overlay=read(a.overlay_acceptance);assert overlay['status']=='CAL66_OFFLINE_OVERLAY_CPU_IMPORT_ACCEPTED'
  resources=c['files']['model-resources.json']['data']['resources']
  identity=evaluator_identity(c['registration'],accepted,resources,c['registration_sha256'])
  b=dict(registration=c['registration'],acceptance=accepted,resources=resources,identity=identity,dependency_overlay=overlay['overlay'],dependency_overlay_manifest_sha256=overlay['overlay_manifest_sha256'])
  from wcomr.automatic_quality_r1 import text_sha
  from wcomr.policy_generator_r1.shared66_card import check_card
  card=check_card(read(REPO/'manifests/cara_shared_CAL66_scope_quote_r1_20261025.json'))
  requests=read(REPO/'configs/wc_policy_interval_assets_full1624_r1_20261020.json')['requests']
  assert {r['name'] for r in requests}=={s['member'] for s in card['matrix']}
  b['members']={r['name']:dict(prompt=r['prompt'],prompt_sha256=text_sha(r['prompt'])) for r in requests}
  rev=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();raw=Path(__file__).read_bytes();name=str(Path(__file__).resolve().relative_to(REPO));assert subprocess.check_output(['git','show',rev+':'+name])==raw
  v=ssh(DEPLOY,dict(binding=b,wrapper=WRAPPER,stage_name=a.stage_name,base=BASE,source_revision=rev,source_sha256=hashlib.sha256(raw).hexdigest()))
 elif a.command=='capture':
  v=ssh(CAPTURE,read(a.launch_ref))
  if 'compressed_original' in v:v=json.loads(__import__('gzip').decompress(base64.b64decode(v['compressed_original'])))
 else:
  v=accept(read(a.capture));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest())
 write(a.output,v);print(json.dumps({k:v.get(k) for k in ('status','CPU_accepted','GPU_submissions')}))
if __name__=='__main__':main()
