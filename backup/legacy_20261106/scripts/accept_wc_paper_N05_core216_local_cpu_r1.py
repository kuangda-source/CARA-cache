#!/usr/bin/env python3
"""Independent finite-grid/default controls acceptance; no model or server."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def accept(c):
    assert c['status']=='N05_LOCAL_CORE216_ORIGINAL_ONCE_CAPTURE'
    launch=c['launch']
    assert c['at_unix']>=launch['first_collection_not_before_unix']
    assert not c['original_handle_confirmed_live_now'] and all(c['payload_verified'].values())
    end=c['files'][launch['exit_ref']];result=c['files'][launch['result_ref']]
    assert end['exists'] and result['exists']
    e,v=end['data'],result['data']
    assert e['pid']==launch['pid'] and e['exit_code']==0 and e['result_sha256']==result['sha256']
    assert e['source_sha256']==v['source_sha256']
    assert all(sha(ROOT/n)==h for n,h in e['source_sha256'].items())
    assert v['status']=='N05_CORE_GRID_FULL216_LOCAL_TOY_CPU_PASS_NOT_PRODUCTION'
    assert v['actual_CPU_paths']==216 and v['ordinary_pairs']==7360 and v['CFG_calls']==14720
    assert not v['production_CPU_accepted'] and not v['real_video_quality_or_speed_claim']
    assert not v['CUDA_initialized']
    assert v['weights_loaded']==v['real_videos_generated']==v['GPU_submissions']==v['SSH_queries']==0
    assert not v['ledger_written']
    core=json.loads((ROOT/'manifests/wc_paper_N05_core66_preregistration_r1_20261016.json').read_text())
    grid={r['id']:r for r in core['methods']}
    methods=list(grid);scenes=['AV28_CPU','Human_CPU','misc_CPU','AV51_CPU']
    defaults=['NATIVE35','WC_DEFAULT','RA_DEFAULT','A_NO_P','TABLE_PHASE_H1']
    times={int(k):n for k,n in core['actual_native_updates'].items()}
    assert len(v['checks'])==2 and {r['flow'] for r in v['checks']}=={False,True}
    steps=[]
    for flow in v['checks']:
        assert flow['complete_CPU_paths']==108 and flow['ordinary_pairs']==3680 and flow['CFG_calls']==7360
        assert flow['all_audit_lean_and_default_controls_equal'] and flow['all_components_released']
        rows=flow['method_pair_checks'];bridges=flow['default_method_bridges']
        assert len(rows)==44 and {(r['scene'],r['method']) for r in rows}=={(s,m) for s in scenes for m in methods}
        assert len(bridges)==20 and {(r['scene'],r['method']) for r in bridges}=={(s,m) for s in scenes for m in defaults}
        for row in rows:
            spec=grid[row['method']];expected=times[spec['requested_steps']] if spec['family']=='NATIVE' else 36
            assert row['requested_steps']==spec['requested_steps'] and row['actual_updates']==expected
            assert row['audit_lean_final_actions_Ahistory_mock_equal'] and row['components_released']
            actual=row['installed_thresholds'];assert len(actual)==1
            if spec['family']=='NATIVE':
                assert set(row['native_block_CFG_counts'].values())=={2*expected}
                steps.append(dict(flow=flow['flow'],scene=row['scene'],method=row['method'],actual_updates=expected,CFG_calls=2*expected))
            elif spec['family']=='WC':
                assert actual[0]['net_WC_threshold']==row['actual_threshold']==spec['worldcache_rel_l1_thresh']
            elif spec['family']=='RA':
                assert actual[0]['controller_RA_threshold']==row['actual_threshold']==spec['RA_threshold']
        assert all(r['all36_guided_final_actions_Ahistory_mock_equal'] for r in bridges)
    artifacts={r['path']:r for r in c['mock_outputs']}
    assert len(artifacts)==len(c['mock_outputs'])==216
    for name,r in artifacts.items():
        assert r['error'] is None and r['data']['CPU_MOCK_WRITER_NOT_VIDEO']
        assert r['data']['value']['shape']==[3,93,16,16] and sha(ROOT/name)==r['sha256']
    def one(folder):
        found=[r for name,r in artifacts.items() if Path(name).is_relative_to(folder)]
        assert len(found)==1
        return found[0]
    pairs=bridges=0
    for flow in ('False','True'):
        for i in range(4):
            parent=Path(launch['artifacts_ref'])/flow/str(i)
            for m in methods:
                assert one(parent/(m+'True'))['sha256']==one(parent/(m+'False'))['sha256'];pairs+=1
            for m in defaults:
                assert one(parent/(m+'True'))['sha256']==one(parent/('old_'+m))['sha256'];bridges+=1
    assert pairs==88 and bridges==40 and len(steps)==24
    return dict(status='N05_CORE216_LOCAL_CPU_MATRIX_PARAMETER_PATHS_AND_MOCKS_INDEPENDENTLY_ACCEPTED',
        actual_CPU_paths=216,ordinary_pairs=7360,CFG_calls=14720,
        audit_lean_mock_pairs=pairs,default_full36_guided_and_mock_bridges=bridges,
        mock_files=216,native_grid_controls=steps,actual_installed_WC_RA_thresholds_checked=True,
        production_CPU_accepted=False,real_video_quality_or_speed_claim=False,
        GPU_submissions=0,SSH_queries=0,ledger_written=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();v=accept(json.loads(gzip.decompress(a.capture.read_bytes())))
    v.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture))
    a.output.write_text(json.dumps(v,indent=2)+'\n')
    print(json.dumps({k:x for k,x in v.items() if k!='native_grid_controls'}))

if __name__=='__main__':main()
