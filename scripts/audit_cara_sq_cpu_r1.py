"""Independent receipt/byte arithmetic acceptance of scoped S/Q CPU work."""
import argparse
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def audit(capture, original):
    state=capture['container_state'];h=capture['host_config'];r=capture['result']
    assert state['Status']=='exited' and state['ExitCode']==0 and not state['OOMKilled'] and not state['Error']
    assert capture['source_hashes_equal'] and capture['runtime_hashes_equal']
    assert not h['DeviceRequests'] and h['NetworkMode']=='none' and h['ReadonlyRootfs']
    assert h['NanoCpus']==2*10**9 and h['Memory']==h['MemorySwap']==8*2**30 and h['CpusetCpus']=='4,5'
    assets='/data20t/gaokuangda/worldcache_workspace/outputs/cara-ig-b1-r2-20261027'
    assert any(m['Destination']==assets and not m['RW'] for m in capture['mounts'])
    expected=original['manifest'];refs=expected['unique_anchors']+[row['artifact'] for row in expected['states']]
    assert {x['name']:(x['sha256'],x['bytes']) for x in r['verified']}=={x['name']:(x['sha256'],x['bytes']) for x in refs}
    assert len(r['verified'])==32 and r['original_asset_bytes']==20795567276
    assert r['manifest_sha256']==original['manifest_sha256']=='5487f8db32d45a5d0f3304333bf362d9d6ec46fb3181c735d7267b78a6e398fa'
    assert not r['CUDA_initialized'] and not r['new_GPU_submissions'] and not r['new_GPUh'] and not r['ledger_writes']
    t=r['source_bound_small_tensor'];assert t['tests']==8 and t['failures']==t['errors']==0 and not t['real_model']
    s=r['S'];assert len(s['local_rows'])==12 and s['coverage']['present']==12 and s['coverage']['expected']==108
    assert not s['coverage']['complete'] and len(s['coverage']['missing'])==96 and s['generated_S_mask'] is None
    assert s['structural_candidates']==158 and s['fully_witnessed_candidates']==0 and not s['production_candidate_support_accepted']
    for row in s['local_rows']:
        m=row['moments'];assert m['identity_abs_error']<=m['identity_tolerance'] and m['reduction_dtype']=='FP64'
        assert math.isclose(m['DIAG'],64*m['C']+49*m['U'],rel_tol=1e-14)
        assert math.isclose(m['CFG_formula'],m['DIAG']-112*m['K'],rel_tol=1e-12,abs_tol=1e-12)
        assert m['teacher_branch_energy']>0
        assert all(math.isclose(m['normalized'][k],m[k]/m['teacher_branch_energy'],rel_tol=1e-14) for k in ('BR','DIAG','CFG'))
    q=r['Q'];assert len(q['codecs'])==60 and len(q['transform_roundtrip'])==10
    assert not q['actual_model_C_replay'] and not q['global_direction_selected']
    assert all(q[k] is None for k in ('persistent_deployment_bytes','peak_allocated','peak_reserved','clean_speed'))
    rates={};groups={};totals={}
    for row in q['codecs']:
        p=row['packed'];assert p['basis']==row['basis'] and row['basis'] in ('I','M')
        assert row['bits'] in ([8,8],[4,8],[8,4]) and not row['actual_C_output_measured']
        actual=p['pair_header_bytes'];assert actual==64
        for component,bits in zip(p['components'],row['bits']):
            shape=component['shape'];tokens=math.prod(shape[:-1]);channels=shape[-1]
            n=tokens*((channels+127)//128)
            scale=4*n;payload=n*128*bits//8
            pad=lambda n:(n+63)//64*64
            assert component['bits']==bits and component['group_channels']==128
            assert component['group_count']==n and component['scale_bytes']==scale and component['payload_bytes']==payload
            assert component['tail_channels_per_token']==(-channels)%128
            assert component['actual_bytes']==64+pad(scale)+pad(payload)
            assert component['padding_bytes']==pad(scale)+pad(payload)-scale-payload
            actual+=component['actual_bytes']
        assert actual==p['actual_bytes']
        key=(row['prompt'],row['step'],row['rate'])
        groups.setdefault(key,[]).append(row)
        rates.setdefault(row['rate'],set()).add(actual)
        totals.setdefault((row['basis'],tuple(row['bits'])),dict(raw=0,packed=0))
        totals[(row['basis'],tuple(row['bits']))]['raw']+=row['raw_r_bytes']
        totals[(row['basis'],tuple(row['bits']))]['packed']+=actual
        assert all(math.isfinite(e['MSE']) and e['MSE']>=0 and math.isfinite(e['max_abs']) for e in row['raw_reconstruction'])
    assert len(groups)==20
    for key,rows in groups.items():
        assert len(rows)==(2 if key[2]=='R16' else 4) and len({row['packed']['actual_bytes'] for row in rows})==1
    assert r['CPU_wall_seconds']<1800 and 0<r['CPU_seconds']<=2*r['CPU_wall_seconds']+10
    assert r['peak_RSS_KiB']<8*2**20
    # Docker emits nanoseconds; the local Python 3.9 parser accepts microseconds.
    # Truncate only the local accounting view, preserving original receipt text.
    parse=lambda t:datetime.fromisoformat(re.sub(r'(\.\d{6})\d+(?=Z$)',r'\1',t).replace('Z','+00:00'))
    wall=(parse(state['FinishedAt'])-parse(state['StartedAt'])).total_seconds()
    assert 0<wall<=1810
    return dict(status='SQ_CPU_PREPARATION_ACCEPTED_SCOPED_NOT_GPU_READY',
                manifest_sha256=r['manifest_sha256'],verified_original_files=32,verified_original_bytes=r['original_asset_bytes'],
                S=dict(FP64_local_states=12,expected_labels=108,missing_labels=96,
                       structural_exchange_candidates=158,fully_witnessed_candidates=0,S_mask=None),
                Q=dict(real_anchor_pairs=10,real_packed_pairs=60,same_bytes_within_all_rates=True,
                       tensor_shape_dtype=q['anchor_schema'][0]['residual'],
                       packed_pair_bytes_by_rate={k:sorted(v) for k,v in rates.items()},
                       corpus_bytes_by_codec={str(k):v for k,v in totals.items()},
                       raw_error_does_not_choose_codec=True,actual_model_C_replay=False,
                       source_bound_C_warp_head_RF_fixture=True,deployed_peak_or_speed_measured=False),
                resources=dict(container_wall_seconds=wall,worker_wall_seconds=r['CPU_wall_seconds'],
                    actual_process_CPU_seconds=r['CPU_seconds'],actual_process_CPUh=r['CPU_seconds']/3600,
                    allocated_vCPUh_upper_bound=2*wall/3600,worker_peak_RSS_GiB=r['peak_RSS_KiB']/2**20,
                    hash_wall_seconds=r['hash_wall_seconds'],GPUh=0,new_budget_reserved_GPUh=0,ledger_writes=0,
                    local_edit_transport_and_git_CPU_metered=False),
                source_revision=capture['launch']['source_revision'],container=capture['launch']['container'],
                image=capture['image'],GPU_ready=False,scientific_benefit_established=False)


def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();assert not a.output.exists()
    original=ROOT/'reports/cara_sq_resource_audit_20261028.json'
    value=audit(json.loads(a.capture.read_text()),json.loads(original.read_text()))
    value['evidence_sha256']={str(x.relative_to(ROOT) if x.is_absolute() else x):sha(x) for x in (a.capture,original,Path(__file__))}
    with a.output.open('x') as f:json.dump(value,f,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps(value,indent=2))


if __name__=='__main__':main()
