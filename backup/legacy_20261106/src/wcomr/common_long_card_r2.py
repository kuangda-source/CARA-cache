"""Frozen six-path common-long card; no dispatch or implicit authorization."""
import json,hashlib
from pathlib import Path
RUN='cara-common-long-newstates6-r2'
CONFIG='common-config.json'
CPU_PROOF='common-combination-CPU.json'
MANIFEST='manifests/cara_common_long_newstates_scope_quote_r1_20261027.json'
COUNTS=dict(total_paths=6,warm_paths=2,formal_paths=4,states=12,readout_positions=84,
 guided_pairs=228,CFG_calls=456,extra_head_pairs=186,loads=1)
def read(p):return json.loads(Path(p).read_text())
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024**2),b''):h.update(b)
 return h.hexdigest()
def require(ok,msg):
 if not ok:raise ValueError(msg)
def matrix(m):
 names=[r['name'] for r in m['requests']]
 require(len(set(names))==2,'two registered old CAL inputs')
 return [dict(id=f'{section}_{i}',prompt=n,enabled=section=='ON',section=section) for section in ('WARM','OFF','ON') for i,n in enumerate(names)]
def validate(project,stage):
 stage=Path(stage);project=Path(project);reg=read(stage/'registration.json');c=read(stage/CONFIG)
 require(reg['namespace']=='CARA_COMMON_LONG6_R1' and reg['stage']==str(stage),'stage identity')
 for n,h in reg['payload_sha256'].items():
  p=stage/n;require(not p.is_symlink() and p.resolve().is_relative_to(stage.resolve()) and sha(p)==h,'source '+n)
 for n,h in reg['runtime_source_sha256'].items():require(sha(project/'runtime'/n)==h,'runtime '+n)
 m=read(stage/MANIFEST);q=read(stage/'pg-whole-quote.json')
 require(c['run_id']==RUN and c['scope_counts']==COUNTS and c['matrix']==matrix(m),'scope')
 require(c['billed_limit_GPUh']==3 and c['forecast_complete_GPUh']==q['forecast_GPUh'] and 0<q['forecast_GPUh']<=3,'quote')
 require(c['host'] in ('four_card','two_card') and c['compute_capability']==({'four_card':[8,9],'two_card':[8,6]}[c['host']]),'host')
 require(c['storage_contract_required'] is True,'dedicated storage mandatory')
 require(c['post_CPU_limit_seconds']==3600 and c['post_CPU_memory_bytes']==8*2**30,'CPU bound')
 require(m['alpha']=={'step_lt_25':1.,'step_ge_25':.5} and m['states']==[22,23,25,33,34,35],'science changed')
 require(m['quote']['cumulative_cap_GPUh']==226 and q['scope_counts']==COUNTS,'budget/scope')
 proof=read(stage/CPU_PROOF);require(proof['status']=='COMMON_LONG_COMBINATION_CPU_ACCEPTED_NOT_GPU','new combination CPU')
 for n,h in proof['source_sha256'].items():require(reg['payload_sha256'].get(n)==h,'CPU closure '+n)
 return c,reg,m
