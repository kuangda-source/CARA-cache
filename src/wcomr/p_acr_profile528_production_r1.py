"""Actual PA12 stage/resources and original H1 execution inputs, read-only."""
import json
from pathlib import Path

from .p_acr_profile528_contract_r1 import *
from .math_n1_production_r1 import MODE_REF
from .math_n1_production_r2 import current_window_original_inputs

CONFIG='configs/wc_p_acr_local12_profile528_production_r1_20261015.json'
CPU_STATUS='PA_LOCAL12_PROFILE528_ACTUAL_PRODUCTION_CPU_ACCEPTED'


def write(path,value):
    path=Path(path);temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n');temporary.replace(path)


def matrix(c):
    validate_contract(c)
    return [{'id':str(i)+'_'+kind,'scene':sample['name'],'kind':kind,'status':'NOT_RUN',
        'planned_ordinary_pairs':36,'planned_diagnostic_pairs':60 if kind=='DIAGNOSTIC' else 0}
        for i,sample in enumerate(c['requests']) for kind in ('BASELINE','DIAGNOSTIC')]


def validate(project,stage):
    project,stage=Path(project),Path(stage)
    reg=json.loads((stage/'registration.json').read_text());c=json.loads((stage/CONFIG).read_text())
    values=validate_local_bindings(stage,c)
    for name,digest in reg['payload_sha256'].items():
        if sha(stage/name)!=digest:raise ValueError('Changed immutable PA production payload: '+name)
    for name,digest in reg['runtime_source_sha256'].items():
        if sha(project/'runtime'/name)!=digest:raise ValueError('Changed pinned PA runtime: '+name)
    # The actual CPU capture binds the tested physical/core files. New entry
    # glue has a separate CPU proof; it cannot replace the numerical scope.
    import gzip
    proof=values['profile_CPU'];capture=stage/proof['capture_ref']
    if sha(capture)!=proof['capture_sha256']:raise ValueError('Profile numerical terminal capture changed')
    numeric=json.loads(gzip.decompress(capture.read_bytes()))['capture']['result']['jobs'][0]['result']
    if numeric['actual_CPU_paths']!=48 or numeric['GPU_submissions'] or numeric['CUDA_initialized']:
        raise ValueError('Full profile numerical CPU required')
    for name,digest in numeric['payload_sha256'].items():
        if name.startswith('src/wcomr/') and reg['payload_sha256'].get(name)!=digest:
            raise ValueError('Actual core differs from numerical CPU: '+name)
    for parameters in (values['H1'],values['previous']):
        for name,digest in parameters['sources'].items():
            if sha(stage/name)!=digest:raise ValueError('Frozen H1 parameter evidence changed: '+name)
    for name,digest in values['coefficients']['inputs_sha256'].items():
        if sha(stage/name)!=digest:raise ValueError('Frozen developer coefficient evidence changed: '+name)
    baseline=values['baseline']
    if (baseline['middle_parameters_fingerprint']!=H1_FP or len(baseline['rows'])!=4
            or {r['scene'] for r in baseline['rows']}!={r['name'] for r in c['requests']}):
        raise ValueError('All original H1 reference identities required')
    for row in baseline['rows']:
        if row['method']!='TABLE_PHASE_H1':raise ValueError('Original H1 reference method changed')
        for key in ('video_artifact','final_artifact'):
            asset=row[key];path=Path(asset['path'])
            if sha(path)!=asset['sha256'] or path.stat().st_size!=asset['bytes']:
                raise ValueError('Original H1 reference file changed')
    _,_,old,inputs=current_window_original_inputs(project,project/c['original_input_stage'])
    if old['preregistration']['requests']!=c['requests'] or old['expected_real_shape']!=c['expected_real_shape']:
        raise ValueError('Original physical model inputs/geometry changed')
    specs=inputs[1][c['strategy']];prior=values['previous'];table=values['H1'];prices=specs['A_CPD_BETA1_ONE_PHASE']['costs']
    if (specs['SOURCE_RA']['threshold']!=prior['original_RA_threshold']
            or (prices.C,prices.P,prices.D)!=(table['source_A_cost_seconds']['D'],prior['cost_seconds']['P'],prior['cost_seconds']['D'])):
        raise ValueError('Original H1 physical root/controller costs changed')
    return c,reg,old,inputs,values


def validate_parent(row,planned):
    if row['scene']!=planned['scene'] or row['kind']!=planned['kind']:
        raise ValueError('Parent identity changed')
    if row['status'] not in ('COMPLETE','VIDEO_REJECTED','TEXT_REJECTED'):
        raise ValueError('Parent terminal status missing')
    if row['status']=='TEXT_REJECTED':
        if row['solver_steps'] or row['guided_pairs'] or row.get('parent_vectors'):
            raise ValueError('Text rejection cannot have model outputs')
        return
    if (row['solver_steps']!=36 or row['guided_pairs']!=36 or len(row['guided_sha256'])!=36
            or row['method_fingerprint']!=H1_FP or not row['parent_vectors']):
        raise ValueError('All ordinary36 outputs required even for video rejection')
    if planned['kind']=='BASELINE':
        if row['actual_pair_computations']!=36:raise ValueError('Original full H1 parent count changed')
    else:
        if row['actual_pair_computations']!=96 or len(row['diagnostic_points'])!=3:
            raise ValueError('All three profile20 origins and original full36 required')
        if not row['all36_guided_final_actions_equal_to_resident_baseline']:
            raise ValueError('Noncommitting diagnostic changed the actual H1 parent')
