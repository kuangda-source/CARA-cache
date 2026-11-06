#!/usr/bin/env python3
"""Complete exposed P0 origins mapped to a source-bound WC/RA probe prior."""
import gzip
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wcomr.source_aware_proxy_mapping import map_creation_error, summarize_modes


def main():
    ref=Path('manifests/wc_source_aware_proxy_mapping_cpu_r1_preregistration_20261010.json')
    reg=json.loads(ref.read_text())
    for n,h in reg['payload_sha256'].items():
        assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h,n
    availability=json.loads(Path(reg['paid_probe_availability_ref']).read_text())
    raw=gzip.decompress(Path(reg['raw_runner_ref']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==availability['native_source_sha256']
    runner=json.loads(raw)
    analysis=json.loads(Path(reg['same_state_analysis_ref']).read_text())
    proof=json.loads(Path(analysis['source_proof_ref']).read_text())
    assert hashlib.sha256(Path(analysis['source_proof_ref']).read_bytes()).hexdigest()==analysis['source_proof_sha256']
    assert proof['independent_source_complete_results_and_actual_artifact_hashes_verified']
    table=json.loads(gzip.decompress(Path(reg['RA_calibration_table_ref']).read_bytes()))
    base=dict(table);fingerprint=base.pop('fingerprint')
    assert hashlib.sha256(json.dumps(base,sort_keys=True,allow_nan=False).encode()).hexdigest()==fingerprint
    assert fingerprint==reg['RA_calibration_fingerprint']
    assert table['protocol']=='COSMOS_SHARED_D6_COARSE_CAL_R1' and not table['toy_only_not_Cosmos_calibration']
    assert table['paid_proxy_definition']=='WC_PAID_DELTA_Y' and table['guided_weights']==[8,-7]
    rho={(v['anchor'],v['step']):v['rho'] for v in table['rho_at']}
    expected={(s,t) for s in reg['scenes'] for t in reg['steps']}
    assert analysis['complete_rows']==48 and analysis['actual_same_state_origins']==8
    assert analysis['actual_group_timing_values']==144 and len(analysis['per_origin_mode'])==48
    records={}
    for request in runner['batch']['requests']:
        paths=[p for p in request['paths'] if p['collect'] is True]
        assert len(paths)==1
        path=paths[0];assert path['status']=='COMPLETE_PARENT_PATH'
        assert path['parameter_versions_unchanged'] and path['all_modules_eval']
        assert len(path['own_history'])==36
        for t in reg['steps']:
            row=path['own_history'][t-1]
            assert row['step']==t and row['anchor_before']==reg['true_D_anchors'][str(t)]
            assert len(row['paid_probes'])==2
            key=(request['sample_name'],t);assert key not in records;records[key]=row
    assert set(records)==expected
    rows=[];controls=[]
    for original in analysis['per_origin_mode']:
        key=(original['scene'],original['step']);history=records[key]
        row=map_creation_error(scene=key[0],step=key[1],anchor=history['anchor_before'],
            packets=history['paid_probes'],rho=rho[(history['anchor_before'],key[1])],
            C_guided_MSE=original['base_C_guided_MSE'],
            P_guided_MSE=original['full_strength_guided_MSE_from_FP64_moments'],mode=original['mode'])
        (rows if original['mode'] in reg['P_modes'] else controls).append(row)
    assert len(rows)==32 and len(controls)==16
    summaries=summarize_modes(rows,modes=reg['P_modes'],origins=sorted(expected))
    out={'status':'COMPLETE_EXPOSED_P0_EMPIRICAL_PROXY_SCALE_MAPPING_NOT_ENDPOINT_BOUND',
        'preregistration_ref':str(ref),'preregistration_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),
        'source_payload_sha256':reg['payload_sha256'],'RA_calibration_fingerprint':fingerprint,
        'complete_original_origins':8,'complete_original_modes_rows':48,'partial_mapping_rows':32,
        'original_control_mapping_rows':16,'original_group_timing_denominator_retained':144,
        'per_origin_mode':rows,'complete_original_control_rows':controls,'complete_mode_summaries':summaries,
        'creation_prior_mapping':reg['mapping'],'propagation_gain_not_folded_into_creation_floor':True,
        'selected_P_mode':None,'installed_policy':False,'P_source_future_drift_measured':False,
        'clean_C_A_P_D_costs':None,'new_GPU_submissions':0,'already_exposed_CAL_not_confirmation':True,
        'RF_to_hidden_error_bound_or_endpoint_quality_or_clean_speed_claim':False}
    dest=Path(reg['output']);assert not dest.exists()
    dest.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:out[k] for k in ['status','complete_original_origins','partial_mapping_rows','complete_mode_summaries']}))


if __name__=='__main__':main()
