#!/usr/bin/env python3
"""Independent CPU receipt/matrix/mock-artifact acceptance; no model or SSH."""
import argparse, collections, gzip, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
METHODS=('H1_ORIGINAL','H1_CAD','STEP23_A_ONLY','T1_CAD')
SCENES=('AV28_CPU','Human_CPU','misc_CPU','AV51_CPU')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def accept(c):
    launch=c['launch'];assert c['status']=='W3_LOCAL_FULL72_CPU_ONCE_CAPTURE'
    assert not c['original_handle_confirmed_live_now'] and all(c['payload_verified'].values())
    assert c['at_unix']>=launch['first_collection_not_before_unix']
    end=c['files'][launch['exit_ref']];result=c['files'][launch['result_ref']]
    assert end['exists'] and result['exists']
    e,v=end['data'],result['data']
    assert e['exit_code']==0 and e['pid']==launch['pid'] and e['result_sha256']==result['sha256']
    assert e['source_sha256']==v['source_sha256'] and all(sha(ROOT/p)==s for p,s in e['source_sha256'].items())
    assert v['status']=='W3_PHASE_T1_FULL72_LOCAL_TOY_SAMPLING_CPU_PASS_NOT_PRODUCTION_CPU'
    assert v['actual_CPU_paths']==72 and v['ordinary_pairs']==2592 and v['CFG_calls']==5184
    assert v['weights_loaded']==v['real_videos_generated']==v['GPU_submissions']==v['SSH_queries']==0
    assert not v['CUDA_initialized'] and not v['production_CPU_accepted'] and not v['ledger_written']
    assert not v['new_policy_quality_or_speed_claim']
    assert len(v['checks'])==2 and {r['flow'] for r in v['checks']}=={False,True}
    totals=collections.Counter();step23=[]
    for flow in v['checks']:
        assert flow['complete_CPU_paths']==36 and flow['ordinary_pairs']==1296
        assert len(flow['method_pair_checks'])==16 and len(flow['original_H1_controls'])==4
        assert flow['all36_audit_lean_controls'] and flow['all_owners_released']
        assert {(r['scene'],r['method']) for r in flow['method_pair_checks']}=={(s,m) for s in SCENES for m in METHODS}
        assert {r['scene'] for r in flow['original_H1_controls']}==set(SCENES)
        for r in flow['method_pair_checks']:
            assert r['audit_lean_final_actions_Ahistory_mock_output_equal'] and r['boundary_owner_release']
            assert r['ordinary_pairs']==72 and len(r['semantic_actions'])==36
            assert all(a in ('C','A','P','D') for a in r['semantic_actions'])
            assert r['semantic_actions'][:7]==['D']*7 and r['semantic_actions'][-1]=='D'
            if r['method'] in ('H1_CAD','T1_CAD'):assert 'P' not in r['semantic_actions']
            totals['new_paths']+=2;totals['ordinary_pairs']+=72
        for r in flow['original_H1_controls']:
            assert r['all36_guided_final_actions_Ahistory_mock_output_equal']
            totals['old_paths']+=1;totals['ordinary_pairs']+=36
        for scene in SCENES:
            index={r['method']:r for r in flow['method_pair_checks'] if r['scene']==scene}
            step23.append(dict(flow=flow['flow'],scene=scene,
                original=index['H1_ORIGINAL']['semantic_actions'][22],phase=index['STEP23_A_ONLY']['semantic_actions'][22],
                T1=index['T1_CAD']['semantic_actions'][22]))
    assert totals['new_paths']==64 and totals['old_paths']==8 and totals['ordinary_pairs']==2592
    mock=c['mock_outputs'];assert len(mock)==72
    paths={r['path']:r for r in mock};assert len(paths)==72
    # These are JSON mock writer files, not real decoded videos.
    for r in mock:
        assert r['error'] is None and r['data']['CPU_MOCK_WRITER_NOT_VIDEO'] is True
        # Pinned inference removes batch dimension before the guarded writer.
        assert r['data']['value']['shape']==[3,93,16,16]
        assert sha(ROOT/r['path'])==r['sha256']
    artifacts=Path(launch['runtime_ref']).parent/'artifacts'
    pairs=0;old_pairs=0
    def one(folder):
        found=[r for path,r in paths.items() if Path(path).is_relative_to(folder)]
        assert len(found)==1
        return found[0]
    for flow in ('False','True'):
        for i in range(4):
            parent=artifacts/flow/str(i)
            for method in METHODS:
                a,b=one(parent/(method+'True')),one(parent/(method+'False'))
                assert a['sha256']==b['sha256'];pairs+=1
            assert one(parent/'H1_ORIGINALTrue')['sha256']==one(parent/'ORIGINAL_H1_CONTROL')['sha256'];old_pairs+=1
    assert pairs==32 and old_pairs==8
    return dict(status='W3_LOCAL_FULL72_CPU_MATRIX_AND_MOCK_ARTIFACTS_INDEPENDENTLY_ACCEPTED',
        actual_paths=72,ordinary_pairs=2592,CFG_calls=5184,method_audit_lean_mock_hash_pairs=32,
        original_H1_mock_hash_pairs=8,programmatic_full36_guided_controls=8,
        step23_CPU_coverage=step23,physical_D_to_A_step23_exercised=any(r['original']=='D' and r['phase']=='A' for r in step23),
        offline_T1_parameters_refit=False,production_CPU_accepted=False,new_GPU_submissions=0,
        real_video_quality_or_speed_claim=False)

def main():
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    assert not a.output.exists();out=accept(json.loads(gzip.decompress(a.capture.read_bytes())))
    out.update(capture_ref=str(a.capture),capture_sha256=sha(a.capture))
    a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))

if __name__=='__main__':main()
