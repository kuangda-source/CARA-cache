"""Frozen CAL66 scope and whole quote, independent of permission to launch."""
import hashlib,json,math
from pathlib import Path
from collections import Counter
from .production_evidence import sha
from .continuation_preparation import require
RUN='cara-shared-cal66-ada-r2'
VERSION='CARA_SHARED66_RECOVERY_R2'
CONFIG='pg-config.json'
CPU_PROOF='shared66-recovery-CPU.json'
MANIFEST='manifests/cara_shared_CAL66_scope_quote_r1_20261025.json'
# The whole previously registered matrix, roles, phase alpha and quote are immutable.
FROZEN_SHA='10fd7536bc7486d9326b179f01eb10e3f992be3b59fa0635856815a9c81da7e0'
COUNTS={'formal_roles': 13, 'total_role_identities': 15, 'CAL': 4, 'seeds': [0], 'quality_paths': 52, 'timing_repeat_paths': 6, 'warm_paths': 6, 'historical_bridge_paths': 2, 'total_paths': 66, 'guided_pairs': 2296, 'CFG_calls': 4592, 'loads': 1, 'LPIPS_pairs': 48, 'LPIPS_frames': 4464, 'independent_quality_videos': 52, 'independent_quality_positions': 156, 'SELECT_paths': 0, 'DEV_paths': 0, 'TEST_paths': 0}
read=lambda p:json.loads(Path(p).read_text())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def check_card(card):
 require(digest(card)==FROZEN_SHA,'Original66 scope/alpha/quote changed')
 require(card['scope']==COUNTS and len(card['matrix'])==66,'Whole66 denominator')
 require(len({s['id'] for s in card['matrix']})==66,'Duplicate physical slot')
 q=card['quote'];generation=sum(q['arm_seconds'][s['role']] for s in card['matrix'])/3600
 require(abs(generation-q['components']['generation_GPUh'])<1e-12,'Quote denominator mismatch')
 forecast=sum(q['components'].values())*(1+q['uncertainty_margin'])
 require(abs(forecast-q['forecast_GPUh'])<1e-12 and forecast<=q['proposed_limit_GPUh']==8.0 and q['cumulative_cap_GPUh']==226,'Quote changed')
 require(q['post_release_CPU']['wall_limit_hours']==6 and q['post_release_CPU']['cpus']==2 and q['post_release_CPU']['memory_GiB']==8,'CPU envelope changed')
 return card

def quote_audit(card):
 check_card(card);q=card['quote']
 return dict(status='CAL66_COMPLETE_QUOTE_RECOMPUTED',scope=COUNTS,manifest_digest=digest(card),
  roles=Counter(s['role'] for s in card['matrix']),sections=Counter(s['section'] for s in card['matrix']),
  forecast_GPUh=q['forecast_GPUh'],proposed_limit_GPUh=8.0,cumulative_cap_GPUh=226,
  generation_GPUh=sum(q['arm_seconds'][s['role']] for s in card['matrix'])/3600,
  post_release_CPU=q['post_release_CPU'],GPU_submissions=0,ledger_written=False,GPU_authorized=False)

RECOVERY_QUOTE='manifests/cara_CAL66_full_recovery_quote_r2_20261025.json'
RECOVERY_QUOTE_SHA='ea6f015803d15385e9903077617a3d3f52618551df771443e00f7c19260c7018'
def execution_quote(card, recovery_path=None):
 check_card(card)
 path=Path(recovery_path) if recovery_path else Path(__file__).resolve().parents[3]/RECOVERY_QUOTE
 require(sha(path)==RECOVERY_QUOTE_SHA,'Frozen recovery quote changed')
 q=read(path)
 require(q['scope']==COUNTS and q['matrix_sha256']==digest(card['matrix']) and q['roles_sha256']==digest(card['roles']),'Recovery changed scientific scope')
 require(q['arm_seconds']==card['quote']['arm_seconds'] and q['billed_limit_GPUh']==8 and q['cumulative_cap_GPUh']==226,'Recovery prices/limits changed')
 require(q['deployment_absolute_seconds']==257.7712338712067 and q['deployment_native_ratio']==.8,'Deployment limit changed')
 expected=sum(q['components'].values())*(1+q['uncertainty_margin'])
 require(abs(expected-q['forecast_GPUh'])<1e-12 and expected<=8,'Recovery whole quote mismatch')
 result=dict(card['quote'])
 result.update(basis='Original full66 arm prices plus accepted failed-run startup allowance',
  components=dict(generation_GPUh=q['components']['all66_generation_GPUh'],model_load_GPUh=q['components']['startup_allowance_GPUh'],artifact_save_release_GPUh=q['components']['artifact_save_release_GPUh']),
  forecast_GPUh=q['forecast_GPUh'],recovery_quote_sha256=RECOVERY_QUOTE_SHA)
 return result

def validate(project,stage):
 stage=Path(stage);project=Path(project);reg=read(stage/'registration.json')
 require(reg['namespace']==VERSION and reg['stage']==str(stage),'Wrong66 stage')
 for n,h in reg['payload_sha256'].items():
  p=stage/n;require(not p.is_symlink() and p.resolve().is_relative_to(stage.resolve()) and sha(p)==h,'Payload changed: '+n)
 for n,h in reg['runtime_source_sha256'].items():require(sha(project/'runtime'/n)==h,'Runtime changed')
 card=check_card(read(stage/MANIFEST));c=read(stage/CONFIG)
 require(c['run_id']==RUN and c['scope_counts']==COUNTS and c['matrix']==card['matrix'],'Config scope changed')
 q=execution_quote(card,stage/RECOVERY_QUOTE)
 require(c['billed_limit_GPUh']==8.0 and c['forecast_complete_GPUh']==q['forecast_GPUh'],'Config quote changed')
 require(read(stage/'pg-whole-quote.json')==q,'Quote bytes mismatch')
 return c,reg,card
