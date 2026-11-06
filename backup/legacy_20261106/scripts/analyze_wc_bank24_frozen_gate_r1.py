"""Six-DEV frozen one-decision gate and all same-D-quota offline comparators."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
from statistics import mean


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(capture, accepted, gate):
    assert accepted['full_protocol_accepted'] and accepted['scored_nonNative_formal']==12
    assert gate['DEV_used_for_fit'] is False and gate['direction']=='LARGER_Z_KEEP_D'
    rows=[r for r in capture['final']['rows'] if r['section']=='TIMED']
    scenes=list(dict.fromkeys(r['scene'] for r in rows));assert len(scenes)==6 and len(rows)==18
    pairs=[]
    for scene in scenes:
        group={r['method']:r for r in rows if r['scene']==scene};assert set(group)=={'D21','A21','NATIVE35'}
        d,a,n=(group[k] for k in ('D21','A21','NATIVE35'))
        assert d['scout_observation']['pre_action_input_sha256']==a['scout_observation']['pre_action_input_sha256']
        assert d['visible_probe_delta']==a['visible_probe_delta']
        z=d['visible_probe_delta']['guided_probe_delta_RMS']/(gate['mu_RMS']+gate['epsilon'])
        pair=dict(scene=scene,z=z,gate_method='D21' if z>=gate['threshold'] else 'A21',
            D_LPIPS=d['LPIPS']['mean_LPIPS'],A_LPIPS=a['LPIPS']['mean_LPIPS'],
            delta_A_minus_D=a['LPIPS']['mean_LPIPS']-d['LPIPS']['mean_LPIPS'],
            D_core_seconds=d['core_seconds'],A_core_seconds=a['core_seconds'],Native_core_seconds=n['core_seconds'],
            D_whole_seconds=d['ended_unix']-d['started_unix'],A_whole_seconds=a['ended_unix']-a['started_unix'],
            Native_whole_seconds=n['ended_unix']-n['started_unix'],
            visible_root_proxy=a['source_history'][20]['source_policy']['decision']['local_proxy'])
        pair['gate_LPIPS']=pair['D_LPIPS'] if pair['gate_method']=='D21' else pair['A_LPIPS']
        pair['gate_regret_to_endpoint_oracle']=pair['gate_LPIPS']-min(pair['D_LPIPS'],pair['A_LPIPS'])
        pairs.append(pair)
    def policy(mask):
        return dict(D_scenes=[p['scene'] for p,use in zip(pairs,mask) if use],D_count=sum(mask),
            mean_LPIPS=mean(p['D_LPIPS'] if use else p['A_LPIPS'] for p,use in zip(pairs,mask)),
            sum_core_seconds=sum(p['D_core_seconds'] if use else p['A_core_seconds'] for p,use in zip(pairs,mask)),
            sum_whole_seconds=sum(p['D_whole_seconds'] if use else p['A_whole_seconds'] for p,use in zip(pairs,mask)))
    masks=list(itertools.product((False,True),repeat=6));all_policies=[policy(mask) for mask in masks]
    selected=policy([p['gate_method']=='D21' for p in pairs]);k=selected['D_count']
    quota=[p for p in all_policies if p['D_count']==k]
    assert len(quota)==math.comb(6,k)
    oracle=policy([p['D_LPIPS']<=p['A_LPIPS'] for p in pairs])
    same_quality=[p for p in all_policies if p['mean_LPIPS']<=selected['mean_LPIPS']+1e-12]
    same_time=[p for p in all_policies if p['sum_core_seconds']<=selected['sum_core_seconds']+1e-9]
    return dict(status='BANK24_FROZEN_GATE_AND_EXHAUSTIVE_QUOTA_ANALYSIS',scenes=6,formal_denominator=18,
        scored_D_A_pairs=6,frozen_gate=gate,per_scene=pairs,all_D=policy([True]*6),all_A=policy([False]*6),
        frozen_z_gate=selected,diagnostic_endpoint_oracle=oracle,
        same_D_quota=dict(D_count=k,combinations=len(quota),random_mixture_expected_LPIPS=mean(p['mean_LPIPS'] for p in quota),
            best_LPIPS=min(p['mean_LPIPS'] for p in quota),worst_LPIPS=max(p['mean_LPIPS'] for p in quota),
            strictly_better_than_gate=sum(p['mean_LPIPS']<selected['mean_LPIPS']-1e-12 for p in quota),
            gate_minus_random_expected_LPIPS=selected['mean_LPIPS']-mean(p['mean_LPIPS'] for p in quota),policies=quota),
        fastest_at_gate_quality=min(same_quality,key=lambda p:p['sum_core_seconds']),
        best_quality_at_gate_observed_time=min(same_time,key=lambda p:p['mean_LPIPS']),
        all64_combinations=all_policies,
        worst_gate_degradation_vs_all_D=max(p['gate_LPIPS']-p['D_LPIPS'] for p in pairs),
        mean_native_core_seconds=mean(p['Native_core_seconds'] for p in pairs),
        DEV_refit=False,online_gate_executed=False,calibration_generated_joint_policy_test=False,
        timing='Existing single-pass diagnostic clocks include observer overhead; not clean repeated latency',
        actual_GPUh=accepted['actual_GPUh'],new_GPU_submissions=0)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',required=True,type=Path);p.add_argument('--accepted',required=True,type=Path)
    p.add_argument('--gate',type=Path,default=Path('reports/wc_scout_CAL12_fourCAL_frozen_gate_20261019.json'));p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();assert not a.output.exists()
    read=lambda p:json.loads(p.read_text());accepted=read(a.accepted)
    assert accepted['capture_sha256']==sha(a.capture)
    result=analyze(read(a.capture),accepted,read(a.gate))
    result['bindings']={k:dict(ref=str(v),sha256=sha(v)) for k,v in vars(a).items() if k!='output'}
    a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('all_D','all_A','frozen_z_gate','same_D_quota')})[:2500])


if __name__=='__main__':main()
