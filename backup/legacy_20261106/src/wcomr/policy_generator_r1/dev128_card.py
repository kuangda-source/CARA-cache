"""Immutable six-role held-out DEV card; preparation never grants GPU permission."""
import json,hashlib
from pathlib import Path
from .continuation_preparation import require
RUN='cara-shared25-dev128-r1'
MANIFEST='manifests/cara_DEV128_scope_r1_20261026.json'
CONFIG='dev-config.json'
REQUESTS='configs/cara_DEV128_requests_r1_20261026.json'
read=lambda p:json.loads(Path(p).read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
FROZEN_SHA='76f96fff4965b6b4508ae95299e53b0f861c6fd6f6e4e72bc431117e04986913'
COUNTS={'total_paths': 128, 'DEV': 16, 'seeds': [0], 'roles': 6, 'quality_paths': 96, 'timing_repeat_paths': 24, 'warm_paths': 6, 'diagnostic_paths': 2, 'guided_pairs': 4419, 'CFG_calls': 8838, 'loads': 1, 'LPIPS_pairs': 80, 'LPIPS_frames': 7440, 'independent_quality_videos': 96, 'independent_quality_positions': 288}
def check_card(card):
 require(digest(card)==FROZEN_SHA,'Frozen DEV scope/alpha/input/order changed')
 require(card['scope']==COUNTS and len(card['matrix'])==128,'Full128 required')
 require(len({s['id'] for s in card['matrix']})==128,'Duplicate physical slot')
 return card

def validate(project,stage):
 stage=Path(stage);project=Path(project);reg=read(stage/'registration.json')
 require(reg['namespace']=='CARA_SHARED25_DEV128_CPU_R1' and reg['stage']==str(stage),'Wrong new DEV stage')
 for n,h in reg['payload_sha256'].items():
  p=stage/n;require(not p.is_symlink() and p.resolve().is_relative_to(stage.resolve()) and sha(p)==h,'Payload changed: '+n)
 for n,h in reg['runtime_source_sha256'].items():require(sha(project/'runtime'/n)==h,'Runtime changed')
 card=check_card(read(stage/MANIFEST))
 for n,h in {**card['source_bindings'],**card['input_bindings']}.items():require(sha(stage/n)==h,'Frozen source/input changed')
 c=read(stage/CONFIG);require(c['scope_counts']==COUNTS and c['matrix']==card['matrix'],'Config differs')
 require(c['GPU_dispatch_authorized'] is False,'Preparation grants no dispatch')
 return c,reg,card
