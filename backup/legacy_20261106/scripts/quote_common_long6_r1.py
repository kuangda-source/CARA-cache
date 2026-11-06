"""Reproducible whole six-path planning quote, not a measured new GPU price."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build():
 ref=ROOT/'reports/cara_IG_B1_R2_central_settlement_20261027.json';r=json.loads(ref.read_text());actual=r['job']['actual_GPUh']
 assert r['job']['status']=='SETTLED' and r['job']['scope_counts']['parent_paths']==4
 m=json.loads((ROOT/'manifests/cara_common_long_newstates_scope_quote_r1_20261027.json').read_text())
 assert m['scope']['total_full_paths']==6 and m['scope']['readout_positions']==84
 snapshots={h:json.loads((ROOT/f'reports/cara_common_long_{h}_exposure_resource_20261027.json').read_text()) for h in ('four_card','two_card')}
 central=snapshots['four_card']['ledger']['totals'];assert central['cap_gpu_hours']==226 and central['reserved_gpu_hours']>=16.5
 forecast=actual*6/4*2;assert forecast<3<=central['available_gpu_hours']
 return dict(status='COMPLETE_SCOPE_PLANNING_QUOTE_NOT_NEW_GPU_MEASUREMENT',reference=dict(path=str(ref.relative_to(ROOT)),sha256=hashlib.sha256(ref.read_bytes()).hexdigest(),actual_GPUh=actual),
 scope=m['scope'],formula='prior complete4 actual * (6/4) * 2 engineering margin',forecast_GPUh=forecast,proposed_hard_GPUh=3,
 hosts={h:dict(forecast_GPUh=forecast,hard_GPUh=3,actual_GPU_price_measured=False) for h in snapshots},
 CPU_post=dict(cores=2,memory_GiB=8,wall_hours=1,GPU_held=False),
 includes=m['quote']['included'],central_totals_snapshot=central,local_mirror_is_authoritative=False,
 two_card_mirror_delta_used_GPUh=central['used_gpu_hours']-snapshots['two_card']['ledger']['totals']['used_gpu_hours'],
 central_reservation_needed_before_dispatch=True,unknown_reserve_preserved=16.5,
 new_scope_parent_same_state_not_new_videos=True,GPU_submissions=0,ledger_written=False)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists();v=build();a.output.write_text(json.dumps(v,indent=2)+'\n');print(json.dumps({k:v[k] for k in ('status','forecast_GPUh','proposed_hard_GPUh','central_totals_snapshot','two_card_mirror_delta_used_GPUh')}))
