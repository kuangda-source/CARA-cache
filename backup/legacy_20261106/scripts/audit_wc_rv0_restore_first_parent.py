#!/usr/bin/env python3
"""Read-only first-parent partial audit; the two-scene denominator stays intact."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


def audit(root,stage):
    path=root/'outputs/wc-rv0-restore-r1/diagnostic/receipt.json'
    raw=path.read_bytes();r=json.loads(raw);c=json.loads((stage/'mid-config.json').read_text())
    assert r['run_card']==c['card'] and r['scope']==c
    assert r['planned_parent_phases']==2 and r['planned_suffix_controls']==4 and r['planned_parent_outputs']==2
    assert r['RV_labels']==r['action_interventions']==0 and r['complete_RV0_acceptance'] is False
    row=r['requests'][0];assert row['sample_name']==c['sample_names'][0]
    assert row['status']=='RESTORE_CONTROLS_AND_ORDINARY_PARENT_CONTINUATION_PASS'
    assert row['prepare_calls']==1 and len(row['inputs'])==len(row['outputs'])==len(row['deep'])==72
    assert len(row['solver_outputs'])==36 and [v['label'] for v in row['controls']]==['A','B']
    assert row['flags_before']==row['flags_after']
    assert row['decode_policy']=='SCOPED_CUDNN_BENCHMARK_FALSE_DETERMINISTIC_TRUE'
    assert all(v['frozen_dataclass'] is True for v in row['condition_classes'].values())
    assert row['sample_return_sha256']==row['final_latent_sha256']
    for child in row['controls']:
        assert child['status']=='UNCHANGED_SUFFIX_COMPLETE_NOT_ACTION_LABEL'
        for key in ['inputs','outputs','deep']:assert child[key]==row[key][44:]
        assert len(child['inputs'])==28 and child['solver_outputs']==row['solver_outputs'][22:]
        assert child['final_latent_sha256']==row['final_latent_sha256']
        record=child['record'];assert record['completed_updates']==22 and record['planned_remaining_updates']==14
        assert record['parent_restored'] is True and record['status']=='UNCHANGED_SUFFIX_COMPLETE_NOT_RV_LABEL'
        assert record['current_action_intervention'] is False and record['counterfactual_label'] is False
        assert record['final_state_components']==row['final_components']
    gate=row['capture_gate'];assert gate['logical_tensor_copy_bytes']<=c['logical_copy_cap_bytes']
    assert gate['GPU_free_bytes']>=gate['required_GPU_headroom_bytes']==2*gate['GPU_logical_copy_bytes']+4*(1<<30)
    for key in ['memory_before_snapshot','memory_after_snapshot','memory_after_parent']:
        memory=row[key];assert memory['GPU_measurement'] is True and memory['max_allocated_bytes']>=memory['allocated_bytes']
    artifact=Path(row['artifact']['path']);video=artifact.read_bytes()
    assert len(video)==row['artifact']['bytes'] and hashlib.sha256(video).hexdigest()==row['artifact']['sha256']==c['expected_parent_video_sha256'][row['sample_name']]
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate','-of','json',str(artifact)],text=True))['streams']
    assert len(probe)==1 and (probe[0]['width'],probe[0]['height'],probe[0]['r_frame_rate'])==(768,432,'16/1')
    decoded=subprocess.run(['ffmpeg','-v','error','-i',str(artifact),'-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,timeout=90)
    assert decoded.returncode==0 and len(decoded.stdout)==93*768*432*3
    snapshot_sha=hashlib.sha256(raw).hexdigest()
    destination=root/'.sync/wc-rv0-independent-analysis';destination.mkdir(exist_ok=True)
    snapshot=destination/('first-parent-'+snapshot_sha+'.json')
    if snapshot.exists():assert snapshot.read_bytes()==raw
    else:snapshot.write_bytes(raw)
    result={'status':'FIRST_PARENT_TWO_UNCHANGED_SUFFIXES_INDEPENDENT_PARTIAL_AUDIT_PASS',
        'observed_unix':time.time(),'runner_snapshot_sha256':snapshot_sha,'snapshot_path':str(snapshot),
        'sample':row['sample_name'],'completed_parent_phases':1,'planned_parent_phases':2,
        'completed_suffixes_audited':2,'planned_suffixes':4,'completed_videos_audited':1,'planned_outputs':2,
        'every_CFG_input_output_deep_solver_and_final_state_equal':True,'full_decode_frames':93,
        'video_sha256':row['artifact']['sha256'],'capture_gate':gate,'snapshot_wall_seconds':row['snapshot_and_validation_wall_seconds'],
        'parent_pipeline_diagnostic_wall_seconds':row['parent_pipeline_including_diagnostics_wall_seconds'],
        'suffix_wall_seconds':[v['inclusive_wall_seconds'] for v in row['controls']],
        'condition_classes':row['condition_classes'],'memory_after_parent':row['memory_after_parent'],
        'GPU_submissions':0,'RV_labels':0,'complete_card_or_full_RV0_accepted':False,
        'limits':'Partial current first-parent evidence only. Other scene, terminal source/cost/release and full causal C/D controls remain incomplete; no quality or clean speed claim.'}
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['project','stage']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();r=audit(a.project,a.stage)
    r['auditor_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();print(json.dumps(r))
