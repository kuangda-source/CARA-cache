"""Immutable complete112 scope; no search or post-hoc scope changes."""
import json
from pathlib import Path
from .production_evidence import sha
from .continuation_preparation import require
RUN='cara-cost-validation112-cal4-ada-r1'
VERSION='CARA_COST_VALIDATION112_R1'
CONFIG='pg-config.json'
CPU_PROOF='cost112-combination-CPU.json'
CPU_BUNDLE=CPU_PROOF
MANIFEST='manifests/cara_cost112_scope_quote_r1_20261025.json'
COUNTS={'roles': 11, 'CAL_FIT': 4, 'seeds': [0], 'formal_repeats': 2, 'formal_paths': 80, 'warm_paths': 20, 'diagnostic_paths': 4, 'total_paths': 112, 'guided_pairs': 4032, 'CFG_calls': 8064, 'loads': 1, 'post_CPU_score_pairs': 72, 'post_CPU_frames': 6696, 'SELECT_paths': 0, 'DEV_paths': 0, 'TEST_paths': 0, 'clock_anchor_paths': 8}
read=lambda p:json.loads(Path(p).read_text())

def check_card(card):
 require(card['cost_model']['version']=='CARA_PRECEDING_FULLD_CLOCK_MODEL_R1' and card['cost_model']['training_rows']==64 and not card['cost_model']['new_card_refit'],'Frozen independent timing contract')
 require(card['scope']==COUNTS and len(card['matrix'])==112,'Whole112 denominator')
 require(len({r['id'] for r in card['matrix']})==112,'Duplicate slot')
 require(card['budget']['deployment_seconds']==257.7712338712067 and card['budget']['relative_native']==.8 and not card['budget']['relaxed'],'Deployment budget changed')
 q=card['quote'];require(q['cumulative_cap_GPUh']==226 and q['billed_limit_GPUh']==11.9 and 0<q['forecast_GPUh']<=11.9<12,'Whole quote changed')
 require(q['post_GPU_release_CPU']['GPU_held'] is False and q['post_GPU_release_CPU']['wall_limit_hours']==1.5,'CPU post budget changed')
 for s in card['matrix']:
  require(Path(s['id']).name==s['id'] and s['member'] in card['CAL_FIT_members'] and s['seed']==0,'Unregistered input')
 return card

def validate(project,stage):
 stage=Path(stage);project=Path(project);reg=read(stage/'registration.json')
 require(reg['namespace']==VERSION and reg['stage']==str(stage),'Wrong cost112 stage')
 for n,h in reg['payload_sha256'].items():
  p=stage/n;require(not p.is_symlink() and p.resolve().is_relative_to(stage.resolve()) and sha(p)==h,'Frozen payload changed: '+n)
 for n,h in reg['runtime_source_sha256'].items():require(sha(project/'runtime'/n)==h,'Runtime changed')
 card=check_card(read(stage/MANIFEST));c=read(stage/CONFIG);q=read(stage/'pg-whole-quote.json')
 require(q==card['quote'] and c['run_id']==RUN and c['scope_counts']==COUNTS and c['matrix']==card['matrix'],'Config/quote scope changed')
 require(c['billed_limit_GPUh']==q['billed_limit_GPUh'] and c['forecast_complete_GPUh']==q['forecast_GPUh'],'Config quote changed')
 return c,reg,card
