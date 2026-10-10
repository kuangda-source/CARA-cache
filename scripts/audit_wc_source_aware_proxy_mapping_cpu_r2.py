#!/usr/bin/env python3
"""Independently reconstruct every mapped row directly from saved sources."""
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import median


def main():
    regref=Path('manifests/wc_source_aware_proxy_mapping_cpu_r2_preregistration_20261010.json')
    reg=json.loads(regref.read_text())
    for p,h in reg['payload_sha256'].items():
        assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
    output=Path(reg['output']);actual=json.loads(output.read_text())
    raw=json.loads(gzip.decompress(Path(reg['raw_runner_ref']).read_bytes()))
    table=json.loads(gzip.decompress(Path(reg['RA_calibration_table_ref']).read_bytes()))
    source=json.loads(Path(reg['same_state_analysis_ref']).read_text())
    probes={(r['sample_name'],h['step']):h for r in raw['batch']['requests']
        for p in r['paths'] if p['collect'] is True for h in p['own_history'] if h['step'] in reg['steps']}
    rho={(r['anchor'],r['step']):r['rho'] for r in table['rho_at']}
    input_rows={(r['scene'],r['step'],r['mode']):r for r in source['per_origin_mode']}
    output_rows=actual['per_origin_mode']+actual['complete_original_control_rows']
    assert len(probes)==8 and len(input_rows)==48 and len(output_rows)==48
    assert {(r['scene'],r['step'],r['mode']) for r in output_rows}==set(input_rows)
    rebuilt=[]
    for row in output_rows:
        key=(row['scene'],row['step'],row['mode']);saved=input_rows[key]
        h=probes[key[:2]];ec,eu=[p['delta_y'] for p in h['paid_probes']]
        correlation=rho[(h['anchor_before'],h['step'])]
        energy=64*ec*ec+49*eu*eu-112*correlation*ec*eu
        assert energy>=0
        q=math.sqrt(energy)
        ratio=math.sqrt(saved['full_strength_guided_MSE_from_FP64_moments']/saved['base_C_guided_MSE'])
        floor=q*ratio
        assert row['defined'] and row['anchor_before']==h['anchor_before']
        assert row['actual_C_guided_MSE']==saved['base_C_guided_MSE']
        assert row['actual_P_guided_MSE']==saved['full_strength_guided_MSE_from_FP64_moments']
        assert math.isclose(row['C_local_WC_PAID_DELTA_Y_proxy'],q,rel_tol=1e-10,abs_tol=1e-12)
        assert math.isclose(row['empirically_mapped_creation_floor_proxy'],floor,rel_tol=1e-10,abs_tol=1e-12)
        rebuilt.append({'scene':key[0],'step':key[1],'mode':key[2],'floor':floor})
    summaries=[]
    for mode,saved in zip(reg['P_modes'],actual['complete_mode_summaries']):
        rows=[r for r in rebuilt if r['mode']==mode]
        assert len(rows)==8 and saved['mode']==mode and saved['defined_origins']==8
        value=median(r['floor'] for r in rows)
        assert math.isclose(saved['median_mapped_creation_floor_proxy'],value,rel_tol=1e-10,abs_tol=1e-12)
        early=median(r['floor'] for r in rows if r['step']==12)
        late=median(r['floor'] for r in rows if r['step']==30)
        g12,g30=[table['gains'][str(t)] for t in (12,30)]
        summaries.append({'mode':mode,'independently_reconstructed_global_floor':value,
            'descriptive_early_floor_median':early,'descriptive_late_floor_median':late,
            'descriptive_late_over_early_proxy_floor_ratio':late/early,
            'bound_RA_gain_at_12':g12,'bound_RA_gain_at_30':g30,
            'gain_weighted_early_floor':g12*early,'gain_weighted_late_floor':g30*late,
            'stage_pattern_does_not_alone_prove_future_P_error_or_endpoint_quality':True})
    assert not actual['installed_policy'] and actual['selected_P_mode'] is None
    result={'status':'ALL48_PROXY_MAPPING_ROWS_INDEPENDENTLY_RECONSTRUCTED_FROM_SAVED_PROBES_AND_MSE',
        'results_ref':str(output),'results_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
        'registration_sha256':hashlib.sha256(regref.read_bytes()).hexdigest(),
        'original_origins':8,'partial_mapping_rows':32,'original_dense_control_rows':16,
        'all_original_rows_independently_reconstructed':48,'original_timing_values_retained':144,
        'independent_alternative_CFG_energy_formula':True,'all_mode_summaries':summaries,
        'new_GPU_submissions':0,'future_P_drift_or_clean_cost_fitted':False,
        'new_phase_model_fitted_or_selected':False,'new_heldout_confirmation_or_video_claim':False}
    dest=Path('reports/wc_source_aware_proxy_mapping_cpu_r2_independent_audit_20261010.json')
    assert not dest.exists();dest.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps(result))


if __name__=='__main__':main()
