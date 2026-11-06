"""Fail-closed production binding. There is deliberately no GPU dispatch here."""
from pathlib import Path
from .production_stage import accepted_assets,read,sha
from .p1_repair_contract import VERSION,RUN,COUNTS,MANIFEST,matrix,timing_gate
from .cost112_card import MANIFEST as COST_MANIFEST
CONFIG='pg-config.json'

def validate(project,stage):
 stage=Path(stage);reg=read(stage/'registration.json')
 if reg['namespace']!=VERSION or reg['stage']!=str(stage):raise ValueError('Wrong P1 repair stage')
 for n,h in reg['payload_sha256'].items():
  p=stage/n
  if p.is_symlink() or not p.resolve().is_relative_to(stage.resolve()) or sha(p)!=h:raise ValueError('Changed immutable source/asset')
 for n,h in reg['runtime_source_sha256'].items():
  if sha(Path(project)/'runtime'/n)!=h:raise ValueError('Runtime changed')
 from .cost112_terminal import accept
 capture=read(stage/'p1-COST112-terminal.json');accepted=accept(capture)
 if accepted!=read(stage/'p1-COST112-accepted-recomputed.json'):raise ValueError('Independent timing replay differs')
 card=read(stage/COST_MANIFEST);timing_gate(accepted,card)
 if capture['launch']['launch_id']!='35150ebb-41a4-4db7-b8fb-45f6ef49297f' or capture['files']['card']['sha256']!=sha(stage/COST_MANIFEST):raise ValueError('Wrong prerequisite launch/card')
 c=read(stage/CONFIG);q=read(stage/MANIFEST)
 if c['run_id']!=RUN or c['scope_counts']!=COUNTS or c['matrix']!=matrix() or c['billed_limit_GPUh']!=q['billed_limit_GPUh'] or c['forecast_complete_GPUh']!=q['forecast_complete_GPUh']:raise ValueError('Whole quote/config mismatch')
 # The concrete >12GPUh quote is not covered by older 10.5/11.9 GPUh cards.
 authorization=read(stage/'pg-GPU-authorization.json')
 if q['specific_whole_card_approval_required'] and authorization.get('specific_quote_sha256')!=sha(stage/MANIFEST):raise ValueError('Specific whole-card quote authorization missing')
 return c,reg,accepted_assets(stage),card,accepted
