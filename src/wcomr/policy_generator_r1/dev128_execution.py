"""Host-specific execution binding; never turns a CPU stage into launch authority."""
from pathlib import Path
from .dev128_card import RUN,COUNTS,CONFIG,MANIFEST,REQUESTS,read,sha,check_card
from .continuation_preparation import require
CPU_PROOF='DEV128-lifecycle-CPU.json'
QUOTE='manifests/cara_DEV128_dual_host_whole_quote_r1_20261026.json'
QUOTE_SHA='7c59a76a271b8ce01bdaf1d09348fe19862edd45afe388cf3df00528e5def9a4'

def execution_quote(card,host,quote_path=None):
 check_card(card);require(host in ('four_card','two_card'),'Unknown host')
 p=Path(quote_path) if quote_path else Path(__file__).resolve().parents[3]/QUOTE
 require(sha(p)==QUOTE_SHA,'Original whole quote changed')
 whole=read(p);q=whole['quotes'][host]
 generation=sum(q['arm_seconds'][s['role']] for s in card['matrix'])/3600
 require(abs(generation-q['components']['all128_generation_GPUh'])<1e-12,'128 price denominator differs')
 require(abs(sum(q['components'].values())*(1+q['uncertainty_margin'])-q['forecast_GPUh'])<1e-12,'Quote arithmetic differs')
 require(q['proposed_limit_GPUh']==12 and whole['cumulative_cap_GPUh']==226 and whole['scope']==COUNTS,'Budget/scope changed')
 require(whole['deployment_budget']==dict(cumulative_GPUh=226,absolute_seconds=257.7712338712067,relative_native=.8),'Deployment budget changed')
 require(whole['post_release_CPU']['wall_limit_hours']==10 and whole['post_release_CPU']['cpus']==2 and whole['post_release_CPU']['memory_GiB']==8,'CPU resource envelope changed')
 return dict(q,post_release_CPU=whole['post_release_CPU'],quote_source_sha256=QUOTE_SHA)

def validate(project,stage):
 stage=Path(stage);project=Path(project);reg=read(stage/'registration.json')
 require(reg['namespace']=='CARA_DEV128_EXECUTION_R1' and reg['stage']==str(stage),'No execution-stage binding; CPU preparation is not authority')
 for n,h in reg['payload_sha256'].items():
  p=stage/n;require(not p.is_symlink() and p.resolve().is_relative_to(stage.resolve()) and sha(p)==h,'Execution payload changed: '+n)
 for n,h in reg['runtime_source_sha256'].items():require(sha(project/'runtime'/n)==h,'Runtime changed')
 card=check_card(read(stage/MANIFEST))
 for n,h in {**card['source_bindings'],**card['input_bindings']}.items():require(sha(stage/n)==h,'Frozen input/source changed')
 c=read(stage/CONFIG);q=execution_quote(card,c['host'],stage/QUOTE)
 require(c['host']==reg['host'] and c['run_id']==RUN and c['scope_counts']==COUNTS and c['matrix']==card['matrix'],'Execution host/scope changed')
 require(c['compute_capability']==q['compute_capability'] and c['billed_limit_GPUh']==12 and c['forecast_complete_GPUh']==q['forecast_GPUh'],'Host quote changed')
 require(0<c['forecast_complete_GPUh']<=c['billed_limit_GPUh'],'Host complete quote exceeds unchanged limit')
 require(c['GPU_dispatch_authorized'] is True and c['storage_contract_required'] is True,'No explicit execution/storage authority')
 require(read(stage/'pg-whole-quote.json')==q,'Bound quote changed')
 auth=read(stage/'pg-GPU-authorization.json')
 require(auth['host']==c['host'] and auth['source_revision']==reg['source_revision'] and auth['registration_sha256']==sha(stage/'registration.json') and auth['config_sha256']==sha(stage/CONFIG) and auth['scope_counts']==COUNTS and auth['billed_limit_GPUh']==12,'Exact launch authority differs')
 cpu=read(stage/'pg-independent-CPU-acceptance.json')
 require(cpu['host']==c['host'] and cpu['production_CPU_accepted'] and cpu['full_GPU_lifecycle_CPU_accepted'] and cpu['independent_quality_models_CPU_accepted'] and auth['independent_CPU_acceptance_sha256']==sha(stage/'pg-independent-CPU-acceptance.json'),'Full host CPU not bound')
 if c['host']=='two_card':
  envelope=read(stage/'central-envelope.json');job=envelope['job']
  require(envelope['central_reservation_verified'] and envelope['same_money_not_two_reservations'],'No central reservation')
  for k in ('run_id','launch_id','source_revision','gpu_uuid','stage','billed_limit_GPUh'):require(job[k]==auth[k],'External envelope identity differs')
  require(job['status']=='RESERVED_OR_RUNNING','External envelope no longer reserved')
 return c,reg,card
