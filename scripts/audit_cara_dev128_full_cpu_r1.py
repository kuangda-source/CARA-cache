"""Independent complete CPU acceptance. Does not authorize GPU execution."""
import argparse,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.policy_generator_r1.dev128_card import COUNTS,check_card
from wcomr.policy_generator_r1.dev128_execution import execution_quote

def accept(c):
 L=c['launch'];p=c['proof'];reg=c['registration'];con=c['container']
 assert p['status']=='DEV128_FULL_LIFECYCLE_RELEASE_SCORE_FINANCE_CPU_COMPLETE'
 assert p['host']==L['host']==reg['host'] and p['scope']==COUNTS
 assert p['registration_sha256']==L['registration_sha256']==c['registration_sha256'] and p['source_revision']==L['source_revision']==reg['source_revision']
 assert c['payload_actual_sha256']==reg['payload_sha256'] and c['runtime_actual_sha256']==reg['runtime_source_sha256']
 assert not con['State']['Running'] and con['State']['ExitCode']==0 and not con['State']['OOMKilled']
 assert con['HostConfig']['ReadonlyRootfs'] and con['HostConfig']['NanoCpus']==2*10**9 and con['HostConfig']['Memory']==8*2**30 and not con['HostConfig']['DeviceRequests']
 env=dict(x.split('=',1) for x in con['Config']['Env']);assert env['CUDA_VISIBLE_DEVICES']=='' and env['NVIDIA_VISIBLE_DEVICES']=='void'
 assert con['Config']['Labels']['wcomr.manifest']==L['registration_sha256']
 r=p['reused_production_binding'];assert r['prior_GPU_hidden'] and r['prior_exited_zero'] and r['acceptance']['host']==L['host'] and r['acceptance']['production_entry_CPU_accepted'] and r['acceptance']['quality_models_CPU_accepted']
 assert r['proof_sha256']==reg['payload_sha256']['prior-production-proof.json']==r['acceptance']['proof_sha256']
 assert all(reg['payload_sha256'][n]==h for n,h in r['payload_sha256'].items() if n!='scripts/run_cara_dev128_r1.py')
 life=p['lifecycle'];storage=p['storage']
 assert len(life['checks'])==10 and all(x['status']=='PASS' and x['GPU_submissions']==x['actual_sudo_calls']==x['actual_nvidia_smi_calls']==0 for x in life['checks'])
 assert len(storage['checks'])==6 and storage['actual_tmpfs_ENOSPC'] and all(x['status']=='PASS' for x in storage['checks'])
 assert life['production_supervisor_sha256']==reg['payload_sha256']['scripts/wc_cara_dev128_worker_r1.py'] and life['production_host_guardian_sha256']==reg['payload_sha256']['scripts/wc_cara_dev128_host_guardian_r1.py']
 assert all(reg['payload_sha256'][n]==h for n,h in storage['source_sha256'].items())
 assert p['terminal_tests']>=61 and p['full_GPU_supervisor_financial_terminal_binding_CPU_accepted']
 assert not any(p[k] for k in ('actual_CUDA','real_nvidia_smi_calls','real_sudo_calls','authoritative_ledger_written','GPU_submissions','new_DEV_inference','GPU_dispatch_ready'))
 from wcomr.policy_generator_r1.dev128_card import MANIFEST
 card=json.loads((Path(__file__).resolve().parents[1]/MANIFEST).read_text());check_card(card)
 assert p['quotes']=={h:execution_quote(card,h) for h in ('four_card','two_card')}
 return dict(status='DEV128_COMPLETE_CPU_COMBINATION_ACCEPTED_NOT_GPU',host=L['host'],source_revision=L['source_revision'],registration_sha256=L['registration_sha256'],proof_sha256=c['proof_sha256'],observed_unix=c['observed_unix'],scope=COUNTS,
  production_CPU_accepted=True,full_GPU_lifecycle_CPU_accepted=True,independent_quality_models_CPU_accepted=True,full_GPU_supervisor_financial_terminal_binding_accepted=True,
  lifecycle_cases=10,real_ENOSPC_storage_cases=6,terminal_tests=p['terminal_tests'],reused_production_acceptance=r['acceptance'],host_quote=p['quotes'][L['host']],
  GPU_submissions=0,ledger_written=False,new_DEV_inference=False,GPU_dispatch_ready=False,hardware_exclusive_verified=False,execution_authorized=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
 v=accept(json.loads(a.capture.read_text()));v.update(capture_ref=str(a.capture),capture_sha256=hashlib.sha256(a.capture.read_bytes()).hexdigest());a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v[k] for k in ('status','host','lifecycle_cases','real_ENOSPC_storage_cases','terminal_tests','GPU_dispatch_ready')}))
