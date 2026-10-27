"""Independent evidence acceptance, finance distinct from local science."""
import math
from .common_long_card_r1 import COUNTS,RUN,require,matrix,MANIFEST,CONFIG
from .common_long_finance_r1 import audit_settlement
from .policy_price_terminal_r1 import record,monitor

def accept(v):
 L=v['launch'];require(L['run_id']==RUN and L['scope_counts']==COUNTS and L['billed_limit_GPUh']==3,'identity/scope')
 reg=record(v,'registration');config=record(v,'config');auth=record(v,'authorization');card=record(v,'card')
 require(reg['source_revision']==L['source_revision'] and reg['stage']==L['stage'],'registered identity')
 require(v['files']['registration']['sha256']==L['registration_sha256'],'registration hash')
 require(v['payload_actual_sha256']==reg['payload_sha256'] and v['runtime_actual_sha256']==reg['runtime_source_sha256'],'source/runtime')
 for key,name in [('card',MANIFEST),('config',CONFIG)]:require(v['files'][key]['sha256']==reg['payload_sha256'][name],'registered '+key)
 require(config['scope_counts']==COUNTS and config['matrix']==matrix(card),'exact registered matrix')
 require(card['alpha']=={'step_lt_25':1.,'step_ge_25':.5},'original alpha')
 for k in ('run_id','launch_id','source_revision','gpu_uuid','scope_counts','billed_limit_GPUh'):require(auth[k]==L[k],'authorization '+k)
 require(v['files']['authorization']['sha256']==L['authorization_sha256'],'authorization SHA')
 finance=audit_settlement(v)
 require(finance['actual_GPUh']<=3,'hard limit exceeded; retain financial settlement only')
 require(not any(v['original_live_handles'].values()) and v['own_UUID_lock_free'],'live original')
 bill=record(v,'billing');release=record(v,'monitor_final')
 monitor(v,L,release['runner'],bill['wall_seconds'])
 state=record(v,'supervisor');postexit=record(v,'post_exit');post=record(v,'post');collection=record(v,'collection')
 require(state['child_exit_code']==state['post_exit_code']==postexit['exit_code']==0,'nonzero original exit')
 require(postexit['CPU_only_after_UUID_release'] and postexit['final_result_sha256']==v['files']['post']['sha256'],'post identity')
 require(post['billing_sha256']==v['files']['billing']['sha256'] and post['collection_sha256']==v['files']['collection']['sha256'],'post originals')
 require(post['states']==12 and post['readout_positions']==84 and post['CPU_only'] and not post['video_quality_claim'],'score scope')
 require(len(collection['rows'])==6 and len(collection['states'])==12 and all(r['status']=='COMPLETE' for r in collection['rows']),'collection scope')
 require(collection['matrix']==matrix(card),'collection matrix')
 for r,slot in zip(collection['rows'],matrix(card)):
  require(all(r[k]==x for k,x in slot.items()),'slot identity')
  require(math.isfinite(r['full_request_seconds']) and 0<r['paper_denoise_decode_seconds']<=r['full_request_seconds'] and r['timing_is_diagnostic'],'two clocks')
 expected={(r['name'],t) for r in card['requests'] for t in card['states']}
 require({(r['prompt'],r['step']) for r in collection['states']}==expected,'exact state identities')
 require(len(post['values'])==12 and {(r['prompt'],r['step']) for r in post['values']}==expected,'score identities')
 from .scout_common_long_r1 import ALL_LABELS
 for r in post['values']:
  require(set(r['scores'])==set(ALL_LABELS),'score labels')
  require(all(math.isfinite(s['MSE']) and s['MSE']>=0 for s in r['scores'].values()),'score finite')
 off={r['prompt']:r['fingerprint'] for r in collection['rows'] if r['section']=='OFF'}
 for r in collection['rows']:
  if r['section']=='ON':require(r['fingerprint']==off[r['prompt']],'all36/final/video control')
 require(v['CPU_resources']==dict(cores=2,memory_bytes=8*2**30,timeout_seconds=3600),'CPU resources')
 require(v['source_and_asset_SHA_verified'] and v['storage_and_cross_disk_journal_verified'],'bound source/storage')
 return dict(status='COMMON_LONG6_TECHNICAL_FINANCIAL_ACCEPTED_PENDING_FROZEN_ANALYSIS',finance=finance,
  science_promoted=False,GPU_repeat_authorized=False)
