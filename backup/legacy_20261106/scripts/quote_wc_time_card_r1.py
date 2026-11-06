"""Whole 73-path engineering quote from saved real timings; no GPU calls."""
import collections,hashlib,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'plans/cara_wc_time_protocol_r1_20261027'
def read(p):return json.loads((ROOT/p).read_text())
def sha(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def main():
 card=read('plans/cara_wc_time_protocol_p0_20261027/CONTROL_IDENTITY_MATRIX.yaml')
 timing=read('reports/cara_latency_boundary_audit_r1_20261027.json')['cards']
 old=read('reports/wc_clean_speed20_live_or_terminal_capture_20261012.json')
 refs=['reports/cara_latency_boundary_audit_r1_20261027.json','reports/wc_clean_speed20_live_or_terminal_capture_20261012.json','reports/cara_CAL66_A6000_terminal_20261026_0930.json','reports/cara_DEV128_A6000_terminal_20261027_0400.json']
 observed={}
 for method in ('NATIVE','WC','RA'):
  vals=[sum(r[k] for k in ('method_install_seconds','guarded_pipeline_without_write_seconds','video_write_seconds','method_cleanup_seconds')) for r in old['final']['rows'] if r['section']=='TIMED' and r['method']==method]
  observed[method]=dict(host='two_card',n=len(vals),mean=sum(vals)/len(vals),max=max(vals),source=refs[1],new_T_DD=None)
 quality=[]
 for p in refs[2:]:
  x=read(p);q=json.loads(x['files']['quality_progress']['raw_utf8']);quality.append(dict(source=p,videos=len(q['rows'])//3,positions=len(q['rows']),CPU_seconds=q['ended_unix']-q['started_unix'],cores=2))
 hosts={}
 for host,source,native_role in [('two_card','CAL66','NATIVE35'),('four_card','C112','NATIVE')]:
  hist=timing[source];native=hist['groups'][native_role]['means']['full_request_seconds'];N=max(r['full_request_seconds'] for r in hist['rows'] if r['role']==native_role)
  # All cache roles budgeted as full Native plus20% probe/online allowance.
  # This is deliberately an engineering estimate, not a measured new latency.
  unit={role:N*(1.2 if role!='NATIVE_U36' else 1.0) for role in card['roles']}
  unit.update({'TAU_0.04':N*1.2,'TAU_0.06':N*1.2})
  phases={};positions=[]
  for s in card['physical_matrix']:
   factor=1.5 if 'DIAGNOSTIC' in s['section'] else 1.0
   positions.append(dict(id=s['id'],role=s['role'],phase=s['section'][0],section=s['section'],request_allowance_seconds=unit[s['role']],diagnostic_multiplier=factor,forecast_seconds=unit[s['role']]*factor,new_measured_seconds=None))
  for phase in 'AB':
   paths=[p for p in positions if p['phase']==phase];request=sum(p['forecast_seconds'] for p in paths)
   overhead=dict(model_load=max(300,hist['load_seconds']*1.5),source_checks_and_context=180,reset_hash_save_decode_checks=300 if phase=='A' else 240,thermal_wait=300,stop_release_settlement=120)
   before=request+sum(overhead.values());forecast=before*1.15
   phases[phase]=dict(paths=len(paths),request_seconds=request,overhead_seconds=overhead,contingency_factor=1.15,forecast_GPUh=forecast/3600,proposed_hard_GPUh=5 if phase=='A' else 7,stop_before_hard_seconds=120)
  total=sum(v['forecast_GPUh'] for v in phases.values())
  hosts[host]=dict(reference_native_mean=native,reference_native_max=N,reference_card=source,role_unit_allowances=unit,positions=positions,phases=phases,forecast_complete_GPUh=total,proposed_whole_hard_GPUh=12,actual_new_GPUh=None,whole_wall_excluding_queue_hours=[total+2,total+4],sequential_worst_bound_hours=19,price_type='HISTORICAL_ANCHORED_FULL_SCOPE_ENGINEERING_QUOTE_NOT_MEASURED_NEW_RATES')
 result=dict(scope_sha256=card['scope_sha256'],counts=card['scope'],source_sha256={p:sha(p) for p in refs},historical_method_observations=observed,quality_CPU_observations=quality,hosts=hosts,
 CPU=dict(phase_A=dict(cores=4,memory_GiB=12,wall_cap_hours=1,Alex_pairs=4),phase_B=dict(cores=4,memory_GiB=12,wall_cap_hours=6,Alex_pairs=24,VGG_pairs=24,quality_gate_positions=84,dynamic_degree_positions=28),allocated_vCPUh_cap=28,forecast_wall_hours=[2,4],actual_current_GPU_model_scoring=0),
 overhead_policy='All warm, diagnostics, rejected tau, reload, writes, checks, held idle, failure and termination included; CPU selection after release. No automatic retry or added calibration.',
 budget=dict(central_cap=226,available_snapshot=37.234225285801614,uncertainty_hold=16.5,proposed_whole_envelope=12,final_confirmation_planning_earmark=16,remaining_after_both=9.234225285801614,earmark_is_not_ledger_reservation=True,increase_applied=False,permission_increment=24),
 billing='One physical GPU chosen for both phases; A and B actual costs add into one envelope, no second-host credit; hard stop retains failures and denominators.',
 uncertainty='No new real GPU sample collected. Historical cache observations are disclosed only; all cache roles use conservative full-Native+20% planning. No guaranteed runtime bound or new T_DD inferred.',GPU_authorized=False)
 (OUT/'WHOLE_QUOTE.json').write_text(json.dumps(result,indent=2)+'\n')
 print({h:dict(forecast_GPUh=round(v['forecast_complete_GPUh'],3),hard_GPUh=12,wall_hours=v['whole_wall_excluding_queue_hours']) for h,v in hosts.items()})
if __name__=='__main__':main()
