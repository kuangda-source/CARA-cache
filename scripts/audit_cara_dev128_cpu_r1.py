"""Independent host/source/count acceptance; never GPU or scientific acceptance."""
import argparse,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.policy_generator_r1.dev128_card import COUNTS

def accept(cap):
 L=cap['launch'];reg=cap['registration'];p=cap['proof'];con=cap['container']
 assert p and p['status']=='DEV128_DUAL_HOST_PRODUCTION_CPU_COMPLETE_NOT_GPU'
 assert cap['registration_sha256']==L['registration_sha256']==p['registration_sha256']
 assert cap['payload_actual_sha256']==reg['payload_sha256']==p['execution_source_sha256']
 assert cap['runtime_actual_sha256']==reg['runtime_source_sha256']
 assert reg['source_revision']==L['source_revision']==p['source_revision']
 assert p['host']==L['host']==reg['host'] and p['scope']==COUNTS
 assert not con['State']['Running'] and con['State']['ExitCode']==0 and not con['State']['OOMKilled']
 assert con['HostConfig']['ReadonlyRootfs'] and con['HostConfig']['NanoCpus']==2*10**9 and con['HostConfig']['Memory']==8*2**30
 assert not con['HostConfig']['DeviceRequests']
 env=dict(x.split('=',1) for x in con['Config']['Env']);assert env['CUDA_VISIBLE_DEVICES']=='' and env['NVIDIA_VISIBLE_DEVICES']=='void'
 assert con['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
 if p.get('reuse'):
  reuse=p['reuse'];old=reuse['parent_registration']
  assert reuse['prior_container_exited'] and reuse['prior_GPU_hidden'] and old['runtime_source_sha256']==reg['runtime_source_sha256']
  allowed={'scripts/wc_dual_host_cara_dev128_cpu_r1.py','scripts/check_cara_dev128_cpu_r1.py','scripts/score_cara_dev128_quality_cpu_r1.py','scripts/audit_cara_dev128_cpu_r1.py'}
  assert set(reuse['allowed_changed_files'])==allowed
  assert all(reg['payload_sha256'].get(n)==h for n,h in old['payload_sha256'].items() if n not in allowed)
  assert all(reg['payload_sha256'][n]==h for n,h in reuse['section_files'].items())
  for key in ('entry','combination'):
   prior=p['outputs'][key];assert prior['registration_sha256']==reuse['parent_launch']['registration_sha256'] and prior['source_revision']==old['source_revision']
 else:
  assert all(p['outputs'][k]['registration_sha256']==L['registration_sha256'] for k in ('entry','combination'))
 e=p['outputs']['entry'];b=e['frozen_boundary'];combo=p['outputs']['combination'];q=p['outputs']['quality']
 assert e['actual_request_count']==e['guard_refusal_controls']==102
 assert b['preload_validated_slots']==128 and b['failed128_original_denominator_retained'] and b['failed128_unreached']==127
 assert b['old_bug_reproduced'] and b['original_requests_unchanged'] and e['actual_SetupArguments']
 assert {r['flow'] for r in e['numeric']['checks']}=={False,True}
 assert all(r['all6_production_roles'] and r['complete_paths']==12 and r['original_alpha_and_D_preserved'] and r['failed_slot_replay_refused'] for r in e['numeric']['checks'])
 expected=dict(paths=128,controls=26,requests_serialized=128,score_pairs=80,score_frames=7440,quality_videos=96,quality_positions=288,synthetic_endpoints_and_scores=True,score_resume_without_GPU_replay=True,quality_resume_without_GPU_replay=True,pre_release_score_refused=True,same_slot_replay_refused=True)
 assert combo['collection']==expected and combo['full_video_metric']['real_LPIPS93']
 assert q['models_really_loaded'] and q['frames']==93 and {r['dimension'] for r in q['rows']}=={'MUSIQ_LONGER512','subject_consistency','motion_smoothness'}
 assert not any(p[k] for k in ('GPU_submissions','ledger_written','CUDA_initialized','new_DEV_inference_executed','GPU_supervisor_financial_terminal_CPU_accepted'))
 for v in (e,combo,q):assert v['GPU_submissions']==0 and not v['CUDA_initialized']
 quote=p['quote'];assert quote['manifest_sha256']==reg['payload_sha256']['manifests/cara_DEV128_scope_r1_20261026.json']
 prices=quote['quotes'][L['host']];assert abs(sum(prices['components'].values())*(1+prices['uncertainty_margin'])-prices['forecast_GPUh'])<1e-10
 return dict(status='DEV128_AFFECTED_PRODUCTION_CPU_ACCEPTED_NOT_GPU',host=L['host'],production_entry_CPU_accepted=True,collection_release_score_CPU_accepted=True,quality_models_CPU_accepted=True,
  source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],proof_sha256=cap['proof_sha256'],scope=COUNTS,observed_unix=cap['observed_unix'],GPU_submissions=0,ledger_written=False,new_DEV_inference_executed=False,
  full_GPU_supervisor_financial_terminal_binding_accepted=False,GPU_dispatch_ready=False,host_forecast_GPUh=prices['forecast_GPUh'],forecast_fits_12_GPUh=prices['forecast_fits_subpool'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 v=accept(json.loads(a.capture.read_text()));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest());a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps(v))
