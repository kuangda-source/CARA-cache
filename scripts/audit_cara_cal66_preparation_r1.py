#!/usr/bin/env python3
"""Replay all separate CAL66 CPU proofs and the full quote; never dispatch."""
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from audit_cara_cal66_entry_cpu_r1 import accept as entry_accept
from audit_cara_shared66_cpu_r1 import accept as combination_accept
from wc_four_card_cara_cal66_quality_cpu_r1 import accept as model_accept
from wc_four_card_cara_cal66_quality_probe_r1 import accept as video_accept
from wcomr.policy_generator_r1.shared66_card import MANIFEST,quote_audit,read
from wcomr.policy_generator_r1.p2_quality_entry import evaluator_identity
from wcomr.automatic_quality_r1 import text_sha
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def audit():
 proofs={};sources={};originals={}
 for role,cap,accepted,callback in [
  ('entry','cara_CAL66_entry_CPU_exited_r1_20261025.json','cara_CAL66_entry_CPU_accepted_r1_20261025.json',entry_accept),
  ('combination','cara_CAL66_combination_CPU_exited_r3_20261025.json','cara_CAL66_combination_CPU_accepted_r3_20261025.json',combination_accept),
  ('models','cara_CAL66_quality_models_CPU_terminal_r1_20261025.json','cara_CAL66_quality_models_CPU_accepted_r1_20261025.json',model_accept),
  ('video','cara_CAL66_quality_video_CPU_terminal_r1_20261025.json','cara_CAL66_quality_video_CPU_accepted_r1_20261025.json',video_accept)]:
  cp=ROOT/'reports'/cap;ap=ROOT/'reports'/accepted;c=read(cp);a=read(ap);replay=callback(c)
  assert all(a[k]==v for k,v in replay.items()) and a['capture_sha256']==sha(cp)
  sources[role]=dict(capture_ref=str(cp.relative_to(ROOT)),capture_sha256=sha(cp),acceptance_ref=str(ap.relative_to(ROOT)),acceptance_sha256=sha(ap))
  originals[role]=c;proofs[role]=a
 assert originals['combination']['proof']['data']['reused_entry']==entry_accept(originals['entry'])
 binding=originals['video']['binding'];models=originals['models']
 assert binding['registration']==models['registration'] and binding['acceptance']==proofs['models']
 assert binding['resources']==models['files']['model-resources.json']['data']['resources']
 assert binding['identity']==evaluator_identity(binding['registration'],binding['acceptance'],binding['resources'],models['registration_sha256'])
 requests=read(ROOT/'configs/wc_policy_interval_assets_full1624_r1_20261020.json')['requests']
 assert binding['members']=={r['name']:dict(prompt=r['prompt'],prompt_sha256=text_sha(r['prompt'])) for r in requests}
 overlay=read(ROOT/'reports/cara_CAL66_quality_overlay_CPU_accepted_r3_complete_20261025.json')
 assert binding['dependency_overlay_manifest_sha256']==overlay['overlay_manifest_sha256'] and not overlay['base_environment_modified']
 raw=(json.dumps(binding,indent=2)+'\n').encode();assert hashlib.sha256(raw).hexdigest()==originals['video']['registration']['binding_sha256']
 quote=quote_audit(read(ROOT/MANIFEST))
 oldref='reports/cara_history104_R2_terminal_20261024_2315.json';old=read(ROOT/oldref)
 olda=read(ROOT/'reports/cara_history104_R2_accepted_20261024_2315.json')
 assert olda['full_protocol_accepted'] and olda['capture_sha256']==sha(ROOT/oldref)
 score=json.loads(old['files']['score_progress']['raw_utf8'])
 assert score['status']=='CPU_SCORE_COMPLETE72' and score['completed_pairs']==score['planned_pairs']==72
 assert hashlib.sha256(old['files']['score_progress']['raw_utf8'].encode()).hexdigest()==old['files']['score_progress']['sha256']
 old_seconds=score['ended_unix']-score['started_unix'];lpips_estimate=old_seconds*48/72
 quality_estimate=proofs['video']['full52_quality_only_extrapolated_seconds']
 planning=(quality_estimate+lpips_estimate)*1.5+600
 value=dict(status='CAL66_ALL_CPU_PREPARATION_INDEPENDENTLY_REPLAYED_NO_GPU',observed_unix=time.time(),CPU_preparation_accepted=True,
  source_receipts=sources,production_sampling_CPU_paths=60,registered_paths=66,original_historical_roles=['S26_C','SHARED26_C','NATIVE35'],
  lifecycle_scenarios=10,storage_scenarios=6,LPIPS_pairs=48,LPIPS_frames=4464,quality_positions=156,
  combination_endpoints_and_all_position_scores_are_declared_fixtures=True,real_LPIPS93=True,
  real_original_models_accepted=5,real_video_metric_probes=3,probe_frames=93,synthetic_probe_is_not_scientific_quality=True,
  binding_sha256=hashlib.sha256(raw).hexdigest(),quote=quote,
  CPU_planning=dict(quality52_seconds=quality_estimate,LPIPS48_seconds=lpips_estimate,LPIPS_source_ref=oldref,
   LPIPS_source_sha256=sha(ROOT/oldref),original72_LPIPS_seconds=old_seconds,margin_factor=1.5,setup_IO_allowance_seconds=600,
   planning_seconds=planning,hard_limit_seconds=21600,within_original_CPU_envelope=planning<21600,
   single_synthetic_video_extrapolation_and_historical_LPIPS_not_full_cohort_runtime=True),
  GPU_authorized=False,GPU_dispatch_ready=False,GPU_submissions=0,ledger_written=False,new_GPUh_reserved=0,
  pending=['explicit_GPU_execution_instruction','fresh_GPU_exclusive_storage_ledger_admission_and_source_bound_stage'])
 assert planning<21600,'Keep original CPU limit; review quote before any GPU admission'
 return value,raw

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--binding-output',type=Path,required=True);a=p.parse_args()
 assert not a.output.exists() and not a.binding_output.exists();v,b=audit()
 a.binding_output.write_bytes(b);v['binding_ref']=str(a.binding_output)
 a.output.write_text(json.dumps(v,indent=2)+'\n')
 print(json.dumps({k:v[k] for k in ('status','CPU_preparation_accepted','GPU_submissions','CPU_planning')}))
if __name__=='__main__':main()
