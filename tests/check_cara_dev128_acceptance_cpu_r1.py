"""Reject damaged independent CPU evidence without running a remote workload."""
import copy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from audit_cara_dev128_cpu_r1 import accept

def check(path):
 original=json.loads(path.read_text());accept(original)
 mutations={
 'GPU_visible':lambda c:c['container']['HostConfig'].update(DeviceRequests=[{'Count':1}]),
 'container_running':lambda c:c['container']['State'].update(Running=True),
 'nonzero_exit':lambda c:c['container']['State'].update(ExitCode=1),
 'wrong_scope':lambda c:c['proof']['scope'].update(total_paths=127),
 'score_missing':lambda c:c['proof']['outputs']['combination']['collection'].update(score_frames=7439),
 'model_missing':lambda c:c['proof']['outputs']['quality']['rows'].pop(),
 'source_changed':lambda c:c['payload_actual_sha256'].update({'injected.py':'0'*64}),
 'DEV_inference':lambda c:c['proof'].update(new_DEV_inference_executed=True),
 'unsafe_reuse':lambda c:c['proof']['reuse'].update(prior_GPU_hidden=False),
 }
 for name,mutate in mutations.items():
  bad=copy.deepcopy(original);mutate(bad)
  try:accept(bad)
  except (AssertionError,KeyError,ValueError):continue
  raise AssertionError('Accepted damaged evidence: '+name)
 return dict(host=original['launch']['host'],accepted_original=True,rejected=list(mutations))
if __name__=='__main__':
 print(json.dumps({'local_only':True,'GPU_submissions':0,'checks':[check(Path(p)) for p in sys.argv[1:]]},indent=2))
