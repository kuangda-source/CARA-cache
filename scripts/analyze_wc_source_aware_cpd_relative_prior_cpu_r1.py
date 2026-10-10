"""All eight exposed P0 origins: dimensionless ratios, not RA-unit floors."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import statistics


def main():
    reg_path=Path('manifests/wc_source_aware_cpd_cpu_r1_preregistration_20261010.json')
    reg=json.loads(reg_path.read_text())
    for n,expected in reg['payload_sha256'].items():
        assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==expected,n
    x=json.loads(Path(reg['analysis_input']).read_text())
    raw=gzip.decompress(Path(x['source_table_native_ref']).read_bytes())
    assert hashlib.sha256(raw).hexdigest()==x['source_table_sha256']
    assert x['complete_rows']==48 and x['actual_same_state_origins']==8
    assert x['actual_group_timing_values']==144
    proof=json.loads(Path(x['source_proof_ref']).read_text())
    assert hashlib.sha256(Path(x['source_proof_ref']).read_bytes()).hexdigest()==x['source_proof_sha256']
    assert proof['independent_source_complete_results_and_actual_artifact_hashes_verified']
    modes=reg['complete_P_modes'];rows=[];summaries=[]
    origins={(r['scene'],r['step']) for r in x['per_origin_mode']}
    assert len(origins)==8 and len(x['per_origin_mode'])==48
    for mode in modes:
        selected=[r for r in x['per_origin_mode'] if r['mode']==mode]
        assert len(selected)==8 and {(r['scene'],r['step']) for r in selected}==origins
        values=[]
        for row in selected:
            a=row['base_C_guided_MSE'];b=row['full_strength_guided_MSE_from_FP64_moments']
            assert math.isfinite(a) and a>0 and math.isfinite(b) and b>0
            ratio=math.sqrt(b/a);values.append(ratio)
            rows.append({'scene':row['scene'],'step':row['step'],'mode':mode,
                'same_state_C_guided_MSE':a,'same_state_P_guided_MSE':b,
                'relative_guided_error_norm_ratio':ratio})
        summaries.append({'mode':mode,'complete_origins':8,
            'median_relative_guided_error_norm_ratio':statistics.median(values),
            'range_relative_guided_error_norm_ratio':[min(values),max(values)],
            'absolute_WC_PAID_DELTA_Y_creation_floor':None})
    out={'status':'COMPLETE_EXPOSED_P0_RELATIVE_PRIOR_ANALYSIS_NOT_PRODUCTION_CALIBRATION',
        'preregistration_ref':str(reg_path),'preregistration_sha256':hashlib.sha256(reg_path.read_bytes()).hexdigest(),
        'source_analysis_sha256':reg['payload_sha256'][reg['analysis_input']],
        'complete_input_rows':48,'complete_origins':8,'original_timing_values_retained':144,
        'complete_P_relative_ratio_rows':32,'per_origin_mode':rows,'complete_mode_summaries':summaries,
        'selected_production_P_mode':None,'production_proxy_floor_generated':False,
        'clean_action_costs_generated':False,'new_policy_installed':False,'GPU_submissions':0,
        'old_descriptive_protocol_unchanged':True,'already_exposed_CAL_not_confirmation':True}
    dest=Path(reg['relative_prior_output']);assert not dest.exists()
    dest.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='per_origin_mode'}))


if __name__=='__main__':main()
