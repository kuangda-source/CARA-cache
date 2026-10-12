#!/usr/bin/env python3
"""Analyze only the complete raw-audited cal16 receipt with frozen gamma."""
import argparse,hashlib,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'src'))
from wcomr.source_phase_table_fit_r1 import analyze


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,default=R/'reports/wc_source_phase16_live_or_terminal_capture_20261012.json')
    p.add_argument('--output',type=Path,default=R/'reports/wc_source_phase16_complete_scalar_and_cell_analysis_20261012.json');a=p.parse_args()
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    data=json.loads(a.input.read_text());v=data['final'];sup=data['supervisor']
    assert v['status']=='SOURCE_PHASE16_ALL8_PARENTS16_POINTS64_LABELS368_PAIRS192_TENSORS_CPU_AUDITED'
    assert data['post_exit']['exit_code']==sup['child_exit_code']==0 and not any(data['original_processes'].values())
    assert data['kernel_lock_free'] and all(data['payload_verified'].values())
    assert v['raw_files']==16 and v['raw_tensors']==192 and len(v['parents'])==8 and all(n==4 for n in v['source_phase_cells'].values())
    assert sum(x['actual_pair_computations'] for x in v['parents'])==368
    assert all(x['old_final_actions_and93RGB_equal'] and x['all36_guided_final_actions_equal_to_new_baseline'] for x in v['parents'])
    assert all(x['all_candidate_and_teacher_tensors_read'] for x in v['points'])
    assert v['budget_before_sha256']==v['budget_after_sha256']==data['ledger_sha256']
    params=R/'manifests/wc_math_n2_frozen_parameters_r1_20261012.json';parameters=json.loads(params.read_text())
    analysis=analyze(v['points'],parameters)
    rows=[]
    for point in v['points']:
        s=point['selection'];loss=point['losses'];energy=point['teacher_guided_energy']
        for name,q in loss.items():
            assert abs(q['absolute_guided_MSE']-q['normalized_guided_MSE']*max(energy,1e-12))<=1e-10*max(1.,q['absolute_guided_MSE'])
        rows.append({'selection':s,'losses':loss,'teacher_guided_energy':energy,
            'parent_continues':point['parent_continues'],'raw_artifact':point['raw_artifact']})
    energies=[p['teacher_guided_energy'] for p in v['points']]
    result={'status':'SOURCE_PHASE16_COMPLETE64_LABELS_CELL_LOSO_INTERVAL_COST_UNITS_CPU_ANALYZED_NOT_NEW_POLICY',
        'raw_checked_receipt_ref':str(a.input),'raw_checked_receipt_sha256':sha(a.input),
        'parameters_sha256':sha(params),'scope_points':16,'readout_labels':64,
        'source_revision':data['source_revision'],'all8_parent_controls_pass':True,
        'energy_min':min(energies),'energy_max':max(energies),'energy_ratio':max(energies)/min(energies) if min(energies)>0 else None,
        'points':rows,'analysis':analysis,'GPU_cost_hours':sup['wall_seconds']/3600,
        'ledger_used':data['ledger']['used_gpu_hours'],'remaining_GPUh':data['ledger']['cap_gpu_hours']-data['ledger']['used_gpu_hours'],
        'GPU_submissions':0,'ledger_written':False}
    assert not a.output.exists();a.output.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({k:result[k] for k in ('status','energy_ratio','GPU_cost_hours','remaining_GPUh')}))
    print(json.dumps(analysis['cell_summaries']))


if __name__=='__main__':main()
