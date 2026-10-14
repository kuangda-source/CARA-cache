"""Freeze source/phase scalars from all previously exposed CAL16 only.

This supplies developer coefficients for PA, not held-out evaluation. The old
LOPO result is kept separate; new PA teachers never choose or fit these gains.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INPUT='reports/wc_p_acr_e0_16state_raw_oracles_20261014.json'
H1='manifests/wc_source_phase_absolute_h1_parameters_r1_20261013.json'


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    data=json.loads((ROOT/INPUT).read_text());h1=json.loads((ROOT/H1).read_text())
    rows=[r for r in data['families'] if r['readout']=='FUSION_A']
    assert data['status']=='E0_16_PI0_STATES48_OFFLINE_READOUT_FAMILIES_ANALYZED' and len(rows)==16
    cells={}
    for source in ('D','P'):
        for phase in ('EARLY','LATE'):
            group=[r for r in rows if r['source']==source and r['phase']==phase]
            assert len(group)==4 and len({r['scene'] for r in group})==4
            mc=sum(r['moments']['mc'] for r in group);mu=sum(r['moments']['mu'] for r in group);cross=sum(r['moments']['cross'] for r in group)
            assert mc>0 and mu>0
            cells[source+'_'+phase]={'Pc_eta':cross/mc,'Pu_zeta':cross/mu,
                'training_prompts':sorted({r['scene'] for r in group}),'states':4,
                'parent_source_identity':'TRUE_D' if source=='D' else 'LEGACY_P0_MLP_NOT_ACR_REFRESH'}
    value={'version':'P_ACR_FROZEN_DEVELOPMENT_SOURCE_PHASE_SCALARS_R1','cells':cells,
        'inputs_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in (INPUT,H1)},
        'A_gamma':h1['gamma'],'A_method':'BETA1_ONE_PHASE','phase_boundary_step':25,
        'fitted_before_new_PA_teacher_or_endpoint':True,'all_CAL_used':True,'independent_test':False,
        'current_omitted_teacher_online':False,'direction_chosen_by_current_teacher':False,
        'new_P_price_measured':False,'GPU_submissions':0,'mainline_modified':False}
    value['fingerprint']=hashlib.sha256(json.dumps(value,sort_keys=True,allow_nan=False).encode()).hexdigest()
    with a.output.open('x') as out:json.dump(value,out,indent=2,allow_nan=False);out.write('\n')
    print(json.dumps({'fingerprint':value['fingerprint'],'coefficients':{k:{n:v[n] for n in ('Pc_eta','Pu_zeta')} for k,v in cells.items()}}))


if __name__=='__main__':main()
